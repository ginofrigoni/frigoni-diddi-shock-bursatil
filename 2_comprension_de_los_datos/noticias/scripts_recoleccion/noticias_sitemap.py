# -*- coding: utf-8 -*-
"""
Scraper multi-sitio via Sitemap XML
Portales: Clarin, El Economista, iProfesional
Categorias: /economia/, /finanzas/

Flujo por sitio:
  1. Sitemap XML (raiz + sub-sitemaps) -> URLs filtradas por categoria y fecha
  2. Deduplicar URLs con checkpoint
  3. Por cada URL: intentar sitio original, fallback Wayback Machine
  4. Parsear articulo (JSON-LD -> OG -> Trafilatura -> BS)
  5. Guardar progresivamente en JSONL

Instalacion:
    pip install requests beautifulsoup4 trafilatura

Uso:
    python noticias_sitemap.py                  (default: 365 dias)
    python noticias_sitemap.py --dias 180
    python noticias_sitemap.py --dias 730
"""

import requests
import json
import time
import re
import html
import sys
import os
import gzip
import argparse
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import trafilatura

from dedup_utils import cargar_urls_ya_scrapeadas
from calidad_utils import PATRON_ARTICULO, url_es_articulo, motivo_descarte

# Nota: este scraper obtiene el contenido directamente del sitio original.
# No usa Wayback Machine.

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# =============================================================
# ARGUMENTO --dias
# =============================================================

parser = argparse.ArgumentParser(description="Scraper de noticias via Sitemap XML")
parser.add_argument("--dias", type=int, default=365, help="Ventana de dias hacia atras (default: 365)")
ARGS = parser.parse_args()

# =============================================================
# CONFIGURACION DE SITIOS
# =============================================================

HOY       = datetime.now()
HASTA_HOY = HOY.strftime("%Y%m%d")
DESDE     = (HOY - timedelta(days=ARGS.dias)).strftime("%Y%m%d")
DESDE_DT  = HOY - timedelta(days=ARGS.dias)   # datetime para comparar con fechas del sitemap

SITIOS = [
    {
        "nombre":           "Clarin economia",
        "sitemap_url":      "https://www.clarin.com/sitemaps/index_news.xml",
        "categorias":       ["/economia/"],
        "patron_articulo":  PATRON_ARTICULO["clarin_sitemap"],
        "archivo_json":     "clarin_sitemap.json",
        "limite_articulos": 0,   # 0 = sin limite
    },
    {
        "nombre":           "El Economista",
        "sitemap_url":      "https://eleconomista.com.ar/sitemap.xml",
        "categorias":       ["/economia/", "/finanzas/"],
        "patron_articulo":  PATRON_ARTICULO["eleconomista_sitemap"],
        "archivo_json":     "eleconomista_sitemap.json",
        "limite_articulos": 0,
    },
    {
        "nombre":           "iProfesional",
        "sitemap_url":      "https://www.iprofesional.com/sitemap-index.xml",
        "categorias":       ["/economia/", "/finanzas/"],
        "patron_articulo":  PATRON_ARTICULO["iprofesional_sitemap"],
        "archivo_json":     "iprofesional_sitemap.json",
        "limite_articulos": 0,
    },
]

# =============================================================
# OPCIONES GLOBALES
# =============================================================

PAUSA_SITEMAP   = 1.5   # pausa entre sub-sitemaps
PAUSA_ARTICULO  = 1.0   # pausa entre articulos (por hilo)
HILOS           = 5     # hilos paralelos para descargar articulos
CARPETA_OUT     = "../resultados"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EconomiaScraper/1.0)",
}


# =============================================================
# SESION CON REINTENTOS
# =============================================================

def crear_sesion():
    sesion = requests.Session()
    reintentos = Retry(
        total=5,
        backoff_factor=2,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=reintentos)
    sesion.mount("https://", adapter)
    sesion.mount("http://", adapter)
    return sesion


# =============================================================
# UTILIDADES XML
# =============================================================

def strip_ns(tag):
    """Quita el namespace de un tag XML: {http://...}urlset -> urlset"""
    return re.sub(r"\{[^}]+\}", "", tag)


def find_text(elem, tag):
    """Busca el texto de un hijo directo ignorando namespaces."""
    for child in elem:
        if strip_ns(child.tag) == tag:
            return (child.text or "").strip()
    return None


def descargar_xml(sesion, url):
    """
    Descarga un XML de sitemap (soporta .xml y .xml.gz).
    Retorna el elemento raiz de ElementTree.
    """
    resp = sesion.get(url, headers=HEADERS, timeout=45)
    resp.raise_for_status()

    contenido = resp.content
    # Descomprimir gzip si corresponde
    if url.endswith(".gz") or resp.headers.get("Content-Type", "").startswith("application/x-gzip"):
        contenido = gzip.decompress(contenido)

    return ET.fromstring(contenido)


def parsear_fecha_sitemap(fecha_str):
    """
    Parsea una fecha de sitemap a datetime naive.
    Acepta: '2024-01-15', '2024-01-15T10:00:00-03:00', '2024-01-15T10:00:00Z'
    """
    if not fecha_str:
        return None
    # Tomar solo los primeros 10 caracteres (YYYY-MM-DD) para comparacion de fecha
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d")
    except ValueError:
        return None


# =============================================================
# PASO 1: Obtener URLs desde el sitemap
# =============================================================

def obtener_urls_sitemap(sesion, sitio):
    """
    Recorre el sitemap raiz del sitio (y todos sus sub-sitemaps).
    Retorna un dict { url_articulo: fecha_iso_str } filtrado por:
      - categorias del sitio
      - fecha >= DESDE_DT
    """
    categorias  = sitio["categorias"]
    urls_result = {}   # url -> fecha_str

    patron_articulo = sitio.get("patron_articulo")

    def es_de_categoria(url):
        # Ademas de la categoria exige forma de URL de articulo: sin esto entraban
        # paginas indice de seccion (ej. eleconomista.com.ar/economia/).
        return any(cat in url for cat in categorias) and (
            patron_articulo is None or url_es_articulo(url, patron_articulo)
        )

    def procesar_urlset(root):
        """Extrae URLs de un <urlset> y las agrega a urls_result."""
        for url_elem in root:
            if strip_ns(url_elem.tag) != "url":
                continue

            loc = find_text(url_elem, "loc")
            if not loc or not es_de_categoria(loc):
                continue

            # Fecha: preferir news:publication_date, luego lastmod
            fecha_str = None
            for child in url_elem:
                if strip_ns(child.tag) == "news":
                    for subchild in child:
                        if strip_ns(subchild.tag) == "publication_date":
                            fecha_str = (subchild.text or "").strip()
                            break
                    break

            if not fecha_str:
                fecha_str = find_text(url_elem, "lastmod")

            # Filtrar por fecha si esta disponible
            if fecha_str:
                fecha_dt = parsear_fecha_sitemap(fecha_str)
                if fecha_dt and fecha_dt < DESDE_DT:
                    continue

            urls_result[loc] = fecha_str or ""

    def procesar_sitemapindex(root):
        """Itera sub-sitemaps de un <sitemapindex>, descartando los muy viejos."""
        sub_sitemaps = []
        for sm_elem in root:
            if strip_ns(sm_elem.tag) != "sitemap":
                continue
            loc     = find_text(sm_elem, "loc")
            lastmod = find_text(sm_elem, "lastmod")
            if not loc:
                continue

            # Si tiene lastmod y es anterior al rango, saltear
            if lastmod:
                fecha_dt = parsear_fecha_sitemap(lastmod)
                if fecha_dt and fecha_dt < DESDE_DT:
                    continue

            sub_sitemaps.append(loc)

        print("  Sub-sitemaps dentro del rango: " + str(len(sub_sitemaps)))

        for i, sub_url in enumerate(sub_sitemaps, 1):
            print("  [" + str(i) + "/" + str(len(sub_sitemaps)) + "] " + sub_url[-70:])
            try:
                sub_root = descargar_xml(sesion, sub_url)
                tag = strip_ns(sub_root.tag)
                if tag == "sitemapindex":
                    procesar_sitemapindex(sub_root)
                else:
                    procesar_urlset(sub_root)
            except Exception as e:
                print("    [ERR] " + str(e)[:70])
            time.sleep(PAUSA_SITEMAP)

    # ── Arrancar desde el sitemap raiz ──
    print("  Descargando sitemap raiz...")
    root = descargar_xml(sesion, sitio["sitemap_url"])
    tag  = strip_ns(root.tag)

    if tag == "sitemapindex":
        procesar_sitemapindex(root)
    else:
        procesar_urlset(root)

    return urls_result


# =============================================================
# PASO 3: Parsear articulo
# Estrategia en capas:
#   1. JSON-LD  -> titulo, fecha, autor, bajada, tags
#   2. Meta OG  -> fallback de titulo, bajada, fecha
#   3. H1       -> fallback de titulo
#   4. Trafilatura -> contenido principal
#   5. BeautifulSoup -> fallback de contenido
# =============================================================

def extraer_metadata_jsonld(soup):
    meta = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            # strict=False: el JSON-LD de El Economista / iProfesional trae
            # caracteres de control crudos y el parseo estricto fallaba en silencio
            # (se perdian fecha, autor y tags).
            data = json.loads(script.string or "", strict=False)
            if isinstance(data, list):
                data = next((d for d in data if "Article" in str(d.get("@type", ""))), {})
            tipos = data.get("@type", "")
            if isinstance(tipos, list):
                tipos = " ".join(tipos)
            if "Article" not in tipos:
                continue
            meta["titulo"]             = data.get("headline")
            meta["bajada"]             = data.get("description")
            meta["fecha_publicacion"]  = data.get("datePublished")
            meta["fecha_modificacion"] = data.get("dateModified")
            autor = data.get("author")
            if isinstance(autor, dict):
                meta["autor"] = autor.get("name")
            elif isinstance(autor, list) and autor:
                meta["autor"] = autor[0].get("name") if isinstance(autor[0], dict) else str(autor[0])
            elif isinstance(autor, str):
                meta["autor"] = autor
            kw = data.get("keywords", "")
            meta["tags"] = [t.strip() for t in kw.split(",")] if isinstance(kw, str) else (kw or [])
            break
        except Exception:
            continue
    return meta


def extraer_metadata_og(soup):
    meta = {}
    og_title = soup.find("meta", property="og:title")
    if og_title:
        meta["titulo"] = og_title.get("content", "").strip()
    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        meta["bajada"] = og_desc.get("content", "").strip()
    pub_time = soup.find("meta", property="article:published_time")
    if pub_time:
        meta["fecha_publicacion"] = pub_time.get("content", "")
    return meta


def extraer_contenido_bs(soup):
    selectores = [
        ".article-body", ".body-nota", ".article-content",
        ".content-nota", ".story-body", ".article__body", "article",
    ]
    for sel in selectores:
        cuerpo = soup.select_one(sel)
        if cuerpo:
            partes = [
                tag.get_text(separator=" ", strip=True)
                for tag in cuerpo.find_all(["p", "h2", "h3", "blockquote"])
                if len(tag.get_text(strip=True)) > 20
            ]
            if partes:
                return "\n\n".join(partes)
    partes = [
        p.get_text(separator=" ", strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 40
    ]
    return "\n\n".join(partes) if partes else None


def parsear_articulo(html, url, timestamp, nombre_sitio, fecha_sitemap=None):
    soup = BeautifulSoup(html, "html.parser")

    art = {
        "sitio":              nombre_sitio,
        "url":                url,
        "timestamp_descarga":  timestamp,
        "fecha_descarga":      datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S"),
        "fecha_sitemap":      fecha_sitemap or None,
        "titulo":             None,
        "fecha_publicacion":  None,
        "fecha_modificacion": None,
        "autor":              None,
        "bajada":             None,
        "contenido":          None,
        "tags":               [],
    }

    jsonld = extraer_metadata_jsonld(soup)
    art.update({k: v for k, v in jsonld.items() if v})

    og = extraer_metadata_og(soup)
    if not art["titulo"]:
        art["titulo"] = og.get("titulo")
    if not art["bajada"]:
        art["bajada"] = og.get("bajada")
    if not art["fecha_publicacion"]:
        art["fecha_publicacion"] = og.get("fecha_publicacion")

    if not art["titulo"]:
        h1 = soup.find("h1")
        if h1:
            art["titulo"] = h1.get_text(strip=True)

    # Los titulos pueden llegar con entidades HTML (&quot; &amp; &#...): decodificarlas.
    if isinstance(art["titulo"], str):
        art["titulo"] = html.unescape(art["titulo"])

    # Usar fecha_sitemap como fallback de fecha_publicacion
    if not art["fecha_publicacion"] and fecha_sitemap:
        art["fecha_publicacion"] = fecha_sitemap

    contenido_trafilatura = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        favor_precision=True,
    )
    if contenido_trafilatura and len(contenido_trafilatura) > 100:
        art["contenido"] = contenido_trafilatura
    else:
        art["contenido"] = extraer_contenido_bs(soup)

    return art


# =============================================================
# CHECKPOINT / JSONL
# =============================================================

def cargar_checkpoint(archivo_jsonl):
    urls_procesadas = set()
    if not os.path.exists(archivo_jsonl):
        return urls_procesadas
    with open(archivo_jsonl, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                art = json.loads(linea)
                if art.get("url"):
                    urls_procesadas.add(art["url"])
            except Exception:
                continue
    return urls_procesadas


def jsonl_a_json(archivo_jsonl, archivo_json, meta):
    noticias = []
    with open(archivo_jsonl, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                try:
                    noticias.append(json.loads(linea))
                except Exception:
                    continue
    resultado = {"meta": meta, "noticias": noticias}
    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)


# =============================================================
# PROCESAR UN SITIO
# =============================================================

def procesar_sitio(sesion, sitio):
    nombre        = sitio["nombre"]
    archivo_json  = os.path.join(CARPETA_OUT, sitio["archivo_json"])
    archivo_jsonl = archivo_json.replace(".json", ".jsonl")

    print("")
    print("=" * 60)
    print("SITIO:  " + nombre)
    print("URL:    " + sitio["sitemap_url"])
    print("Cats:   " + ", ".join(sitio["categorias"]))
    print("Rango:  " + DESDE + " -> " + HASTA_HOY)
    print("=" * 60)

    # ── Checkpoint: propio + todos los .jsonl de resultados/ (cross-fuente,
    # ver AUDITORIA_CORPUS.md hallazgo 4.1) ──
    urls_ya_procesadas = cargar_checkpoint(archivo_jsonl) | cargar_urls_ya_scrapeadas(CARPETA_OUT)
    if urls_ya_procesadas:
        print("Retomando: " + str(len(urls_ya_procesadas)) + " articulos ya procesados (este archivo + otras fuentes)")

    # ── PASO 1: Obtener URLs del sitemap ──
    print("")
    print("Recorriendo sitemap...")
    try:
        urls_dict = obtener_urls_sitemap(sesion, sitio)
    except Exception as e:
        print("[ERR] No se pudo procesar el sitemap: " + str(e))
        return {"sitio": nombre, "noticias": 0, "errores": 1}

    print("")
    print("URLs encontradas en sitemap: " + str(len(urls_dict)))

    # ── Excluir ya procesadas ──
    urls_pendientes = [(url, fecha) for url, fecha in urls_dict.items()
                       if url not in urls_ya_procesadas]

    print("Ya procesadas (checkpoint):  " + str(len(urls_ya_procesadas)))
    print("Pendientes esta sesion:      " + str(len(urls_pendientes)))

    limite = sitio.get("limite_articulos", 0)
    if limite and len(urls_pendientes) > limite:
        urls_pendientes = urls_pendientes[:limite]
        print("Limite aplicado: " + str(limite) + " articulos")

    if not urls_pendientes:
        print("Nada nuevo para procesar.")
        return {"sitio": nombre, "noticias": len(urls_ya_procesadas), "errores": 0}

    # ── PASO 2 y 3: Descargar y parsear con multihilo ──
    total   = len(urls_pendientes)
    n_ok    = len(urls_ya_procesadas)
    n_error = 0
    n_descartadas = 0
    lock    = threading.Lock()

    print("")
    print("Descargando " + str(total) + " articulos con " + str(HILOS) + " hilos...")
    print("Guardando en: " + archivo_jsonl)
    print("")

    def procesar_articulo(idx_url_fecha):
        idx, url, fecha_sitemap = idx_url_fecha
        ts = HOY.strftime("%Y%m%d%H%M%S")

        try:
            resp = sesion.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            noticia = parsear_articulo(resp.text, url, ts, nombre, fecha_sitemap)
            time.sleep(PAUSA_ARTICULO)
            # el sitemap filtra por lastmod: aca se filtra por fecha de PUBLICACION real
            motivo = motivo_descarte(noticia, desde_dt=DESDE_DT)
            if motivo:
                return (idx, url, None, "DESCARTADA:" + motivo)
            return (idx, url, noticia, None)
        except Exception as e:
            time.sleep(PAUSA_ARTICULO)
            return (idx, url, None, str(e)[:80])

    with open(archivo_jsonl, "a", encoding="utf-8") as jsonl_f:
        with ThreadPoolExecutor(max_workers=HILOS) as executor:
            futuros = {
                executor.submit(procesar_articulo, (i, url, fecha)): i
                for i, (url, fecha) in enumerate(urls_pendientes, 1)
            }
            for futuro in as_completed(futuros):
                idx, url, noticia, error = futuro.result()
                prefijo = "[" + str(idx) + "/" + str(total) + "] "
                with lock:
                    if noticia:
                        jsonl_f.write(json.dumps(noticia, ensure_ascii=False) + "\n")
                        jsonl_f.flush()
                        n_ok += 1
                        titulo = noticia.get("titulo") or "(sin titulo)"
                        print(prefijo + "[OK] " + titulo[:60])
                    elif str(error).startswith("DESCARTADA:"):
                        n_descartadas += 1
                        print(prefijo + "[SKIP] " + str(error)[11:] + " - " + url[-60:])
                    else:
                        n_error += 1
                        print(prefijo + "[ERR] " + str(error)[:70])

    # ── Generar JSON final ──
    meta = {
        "sitio":          nombre,
        "sitemap_url":    sitio["sitemap_url"],
        "categorias":     sitio["categorias"],
        "fecha_desde":    DESDE,
        "fecha_hasta":    HASTA_HOY,
        "total_noticias": n_ok,
        "total_errores":  n_error,
        "total_descartadas": n_descartadas,
        "generado_en":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    jsonl_a_json(archivo_jsonl, archivo_json, meta)

    print("")
    print("[OK] " + nombre + ": " + str(n_ok) + " noticias totales, " + str(n_error) + " errores")
    print("     JSONL: " + archivo_jsonl)
    print("     JSON:  " + archivo_json)
    return {"sitio": nombre, "noticias": n_ok, "errores": n_error}


# =============================================================
# MAIN
# =============================================================

def main():
    print("=" * 60)
    print("Scraper via Sitemap XML - Noticias de economia")
    print("Sitios: " + str(len(SITIOS)))
    print("Ventana: ultimos " + str(ARGS.dias) + " dias (" + DESDE + " -> " + HASTA_HOY + ")")
    print("=" * 60)

    os.makedirs(CARPETA_OUT, exist_ok=True)
    sesion  = crear_sesion()
    resumen = []

    for sitio in SITIOS:
        resultado = procesar_sitio(sesion, sitio)
        resumen.append(resultado)

    print("")
    print("=" * 60)
    print("RESUMEN FINAL")
    print("=" * 60)
    total_n = 0
    total_e = 0
    for r in resumen:
        print("  " + r["sitio"] + ": " + str(r["noticias"]) + " noticias, " + str(r["errores"]) + " errores")
        total_n += r["noticias"]
        total_e += r["errores"]
    print("  " + "-" * 40)
    print("  TOTAL: " + str(total_n) + " noticias, " + str(total_e) + " errores")
    print("  Archivos en: " + os.path.abspath(CARPETA_OUT))
    print("=" * 60)

    # Dedup semantico (cross-posting con URL distinta) via LLM local: incremental,
    # se omite con un aviso si Ollama / el modelo no estan disponibles.
    try:
        from dedup_semantico_qwen import post_scraping
        post_scraping()
    except Exception as e:
        print("[AVISO] dedup semantico omitido: " + str(e))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("")
        print("[ERROR INESPERADO] " + str(e))
    finally:
        input("\nPresiona Enter para cerrar...")
