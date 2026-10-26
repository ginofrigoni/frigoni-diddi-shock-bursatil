# -*- coding: utf-8 -*-
"""
Scraper DIARIO via Sitemap XML - Todos los portales
Obtiene las noticias de hoy (o los ultimos N dias) para las categorias
de economia/finanzas y las agrega a los JSONL historicos existentes.

El checkpoint por URL garantiza que nunca se duplique una noticia ya guardada.

Portales y sitemaps:
  Ambito          https://www.ambito.com/sitemap.xml
  La Nacion       https://www.lanacion.com.ar/sitemap-news.xml
  Clarin          https://www.clarin.com/sitemaps/index_news.xml
  TN              https://tn.com.ar/arc/outboundfeeds/sitemap/?outputType=xml
  Infobae         https://www.infobae.com/arc/outboundfeeds/news-sitemap2/
  El Economista   https://eleconomista.com.ar/sitemapNews.xml
  iProfesional    https://www.iprofesional.com/sitemap-news.xml

Instalacion:
    pip install requests beautifulsoup4 trafilatura

Uso:
    python noticias_diario.py              (default: solo hoy)
    python noticias_diario.py --dias 3     (ultimos 3 dias)
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

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# =============================================================
# ARGUMENTO --dias
# =============================================================

parser = argparse.ArgumentParser(description="Scraper diario de noticias via Sitemap XML")
parser.add_argument(
    "--dias", type=int, default=1,
    help="Cuantos dias hacia atras incluir (default: 1 = solo hoy)"
)
ARGS = parser.parse_args()

# =============================================================
# FECHAS
# =============================================================

HOY      = datetime.now()
# DESDE_DT: inicio del dia mas viejo a incluir (00:00:00)
# --dias 1 = solo hoy | --dias 3 = hoy + 2 dias anteriores
DESDE_DT = (HOY - timedelta(days=ARGS.dias - 1)).replace(
    hour=0, minute=0, second=0, microsecond=0
)
DESDE    = DESDE_DT.strftime("%Y%m%d")
HASTA    = HOY.strftime("%Y%m%d")

# =============================================================
# CONFIGURACION DE SITIOS
# Cada entrada apunta al JSONL existente creado por los scripts
# historicos, para que las noticias de hoy se acumulen ahi.
# =============================================================

SITIOS = [
    # ── Ambito ─────────────────────────────────────────────────
    {
        "nombre":       "Ambito economia",
        "sitemap_url":  "https://www.ambito.com/sitemap.xml",
        "categorias":   ["/economia/"],
        "archivo_json": "ambito_economia.json",   # creado por v3
    },
    {
        "nombre":       "Ambito finanzas",
        "sitemap_url":  "https://www.ambito.com/sitemap.xml",
        "categorias":   ["/finanzas/"],
        "archivo_json": "ambito_finanzas.json",   # creado por v3
    },
    # ── La Nacion ───────────────────────────────────────────────
    {
        "nombre":       "La Nacion economia",
        "sitemap_url":  "https://www.lanacion.com.ar/sitemap-news.xml",
        "categorias":   ["/economia/"],
        "archivo_json": "lanacion_economia.json", # creado por v3
    },
    # ── Clarin ──────────────────────────────────────────────────
    {
        "nombre":       "Clarin economia",
        "sitemap_url":  "https://www.clarin.com/sitemaps/index_news.xml",
        "categorias":   ["/economia/"],
        "archivo_json": "clarin_economia.json",   # creado por v3
    },
    # ── TN ──────────────────────────────────────────────────────
    {
        "nombre":       "TN economia",
        "sitemap_url":  "https://tn.com.ar/arc/outboundfeeds/sitemap/?outputType=xml",
        "categorias":   ["/economia/"],
        "archivo_json": "tn_economia.json",       # creado por v3
    },
    # ── Infobae ─────────────────────────────────────────────────
    {
        "nombre":       "Infobae economia",
        "sitemap_url":  "https://www.infobae.com/arc/outboundfeeds/news-sitemap2/",
        "categorias":   ["/economia/"],
        "archivo_json": "infobae_economia.json",  # creado por v3
    },
    # ── El Economista ───────────────────────────────────────────
    {
        "nombre":       "El Economista",
        "sitemap_url":  "https://eleconomista.com.ar/sitemapNews.xml",
        "categorias":   ["/economia/", "/finanzas/"],
        "archivo_json": "eleconomista_sitemap.json", # creado por sitemap.py
    },
    # ── iProfesional ────────────────────────────────────────────
    {
        "nombre":       "iProfesional",
        "sitemap_url":  "https://www.iprofesional.com/sitemap-news.xml",
        "categorias":   ["/economia/", "/finanzas/"],
        "archivo_json": "iprofesional_sitemap.json", # creado por sitemap.py
    },
]

# Forma de URL de articulo por fuente (clave = nombre del archivo sin .json):
# evita que entren paginas indice de seccion (ver calidad_utils.py).
for _s in SITIOS:
    _s["patron_articulo"] = PATRON_ARTICULO[_s["archivo_json"][:-5]]

# =============================================================
# OPCIONES GLOBALES
# =============================================================

PAUSA_SITEMAP  = 1.0   # pausa entre sub-sitemaps
PAUSA_ARTICULO = 1.0   # pausa entre articulos (por hilo)
HILOS          = 5     # hilos paralelos para descargar articulos
CARPETA_OUT    = "../resultados"

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
    """Descarga y parsea un sitemap XML (soporta .gz)."""
    resp = sesion.get(url, headers=HEADERS, timeout=45)
    resp.raise_for_status()
    contenido = resp.content
    if url.endswith(".gz") or resp.headers.get("Content-Type", "").startswith("application/x-gzip"):
        contenido = gzip.decompress(contenido)
    return ET.fromstring(contenido)


def parsear_fecha_sitemap(fecha_str):
    """
    Parsea fecha de sitemap a datetime naive (solo parte YYYY-MM-DD).
    Acepta: '2024-01-15', '2024-01-15T10:00:00-03:00', '2024-01-15T10:00:00Z'
    """
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d")
    except ValueError:
        return None


# =============================================================
# OBTENER URLs DESDE SITEMAP
# =============================================================

def obtener_urls_sitemap(sesion, sitio):
    """
    Recorre el sitemap del sitio y retorna dict { url: fecha_str }
    filtrando por categoria y por fecha >= DESDE_DT.
    """
    categorias  = sitio["categorias"]
    urls_result = {}

    patron_articulo = sitio.get("patron_articulo")

    def es_de_categoria(url):
        return any(cat in url for cat in categorias) and (
            patron_articulo is None or url_es_articulo(url, patron_articulo)
        )

    def procesar_urlset(root):
        for url_elem in root:
            if strip_ns(url_elem.tag) != "url":
                continue
            loc = find_text(url_elem, "loc")
            if not loc or not es_de_categoria(loc):
                continue

            # Fecha: news:publication_date > lastmod
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

            if fecha_str:
                fecha_dt = parsear_fecha_sitemap(fecha_str)
                if fecha_dt and fecha_dt < DESDE_DT:
                    continue

            urls_result[loc] = fecha_str or ""

    def procesar_sitemapindex(root):
        sub_sitemaps = []
        for sm_elem in root:
            if strip_ns(sm_elem.tag) != "sitemap":
                continue
            loc     = find_text(sm_elem, "loc")
            lastmod = find_text(sm_elem, "lastmod")
            if not loc:
                continue
            # Saltar sub-sitemaps anteriores al rango
            if lastmod:
                fecha_dt = parsear_fecha_sitemap(lastmod)
                if fecha_dt and fecha_dt < DESDE_DT:
                    continue
            sub_sitemaps.append(loc)

        print("  Sub-sitemaps en rango: " + str(len(sub_sitemaps)))
        for i, sub_url in enumerate(sub_sitemaps, 1):
            print("  [" + str(i) + "/" + str(len(sub_sitemaps)) + "] " + sub_url[-70:])
            try:
                sub_root = descargar_xml(sesion, sub_url)
                if strip_ns(sub_root.tag) == "sitemapindex":
                    procesar_sitemapindex(sub_root)
                else:
                    procesar_urlset(sub_root)
            except Exception as e:
                print("    [ERR] " + str(e)[:70])
            time.sleep(PAUSA_SITEMAP)

    print("  Descargando sitemap...")
    root = descargar_xml(sesion, sitio["sitemap_url"])
    if strip_ns(root.tag) == "sitemapindex":
        procesar_sitemapindex(root)
    else:
        procesar_urlset(root)

    return urls_result


# =============================================================
# PARSEAR ARTICULO
# =============================================================

def extraer_metadata_jsonld(soup):
    meta = {}
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            # strict=False: JSON-LD con caracteres de control crudos (ver calidad_utils.py)
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
        "timestamp_descarga": timestamp,
        "fecha_descarga":     datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S"),
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
    if not art["titulo"]:        art["titulo"] = og.get("titulo")
    if not art["bajada"]:        art["bajada"] = og.get("bajada")
    if not art["fecha_publicacion"]: art["fecha_publicacion"] = og.get("fecha_publicacion")

    if not art["titulo"]:
        h1 = soup.find("h1")
        if h1:
            art["titulo"] = h1.get_text(strip=True)

    # Los titulos pueden llegar con entidades HTML (&quot; &amp; &#...): decodificarlas.
    if isinstance(art["titulo"], str):
        art["titulo"] = html.unescape(art["titulo"])

    if not art["fecha_publicacion"] and fecha_sitemap:
        art["fecha_publicacion"] = fecha_sitemap

    contenido_traf = trafilatura.extract(
        html, include_comments=False, include_tables=False,
        no_fallback=False, favor_precision=True,
    )
    art["contenido"] = contenido_traf if (contenido_traf and len(contenido_traf) > 100) \
                       else extraer_contenido_bs(soup)

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
    with open(archivo_json, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "noticias": noticias}, f, ensure_ascii=False, indent=2)


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
    print("Rango:  " + DESDE + " -> " + HASTA)
    print("=" * 60)

    # Propio + todos los .jsonl de resultados/ (cross-fuente,
    # ver AUDITORIA_CORPUS.md hallazgo 4.1)
    urls_ya_procesadas = cargar_checkpoint(archivo_jsonl) | cargar_urls_ya_scrapeadas(CARPETA_OUT)
    if urls_ya_procesadas:
        print("Checkpoint: " + str(len(urls_ya_procesadas)) + " URLs ya procesadas (este archivo + otras fuentes)")

    print("")
    print("Recorriendo sitemap...")
    try:
        urls_dict = obtener_urls_sitemap(sesion, sitio)
    except Exception as e:
        print("[ERR] No se pudo procesar el sitemap: " + str(e))
        return {"sitio": nombre, "noticias": 0, "errores": 1}

    urls_pendientes = [(url, fecha) for url, fecha in urls_dict.items()
                       if url not in urls_ya_procesadas]

    print("")
    print("Encontradas en sitemap:  " + str(len(urls_dict)))
    print("Ya en JSONL (skip):      " + str(len(urls_ya_procesadas & urls_dict.keys())))
    print("Nuevas a descargar:      " + str(len(urls_pendientes)))

    if not urls_pendientes:
        print("Nada nuevo para hoy.")
        return {"sitio": nombre, "noticias": len(urls_ya_procesadas), "errores": 0}

    total   = len(urls_pendientes)
    n_ok    = len(urls_ya_procesadas)
    n_error = 0
    n_descartadas = 0
    lock    = threading.Lock()

    print("")
    print("Descargando " + str(total) + " articulos con " + str(HILOS) + " hilos...")
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

    meta = {
        "sitio":          nombre,
        "sitemap_url":    sitio["sitemap_url"],
        "categorias":     sitio["categorias"],
        "fecha_desde":    DESDE,
        "fecha_hasta":    HASTA,
        "total_noticias": n_ok,
        "total_errores":  n_error,
        "total_descartadas": n_descartadas,
        "generado_en":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    jsonl_a_json(archivo_jsonl, archivo_json, meta)

    print("")
    print("[OK] " + nombre + ": +" + str(total - n_error - n_descartadas) + " nuevas, " +
          str(n_ok) + " totales, " + str(n_error) + " errores")
    return {"sitio": nombre, "noticias": n_ok, "errores": n_error}


# =============================================================
# MAIN
# =============================================================

def main():
    etiqueta = "solo hoy" if ARGS.dias == 1 else "ultimos " + str(ARGS.dias) + " dias"
    print("=" * 60)
    print("Scraper DIARIO via Sitemap XML")
    print("Sitios: " + str(len(SITIOS)))
    print("Rango:  " + etiqueta + " (" + DESDE + " -> " + HASTA + ")")
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
        print("  " + r["sitio"] + ": " + str(r["noticias"]) + " noticias, " +
              str(r["errores"]) + " errores")
        total_n += r["noticias"]
        total_e += r["errores"]
    print("  " + "-" * 40)
    print("  TOTAL: " + str(total_n) + " noticias acumuladas, " + str(total_e) + " errores")
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
