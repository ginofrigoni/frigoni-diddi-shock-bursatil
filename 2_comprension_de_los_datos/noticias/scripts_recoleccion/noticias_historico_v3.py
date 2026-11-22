# -*- coding: utf-8 -*-
"""
Scraper multi-sitio de noticias de economia via Wayback Machine
Portales: La Nacion, Clarin, TN, Infobae

Flujo por sitio:
  1. CDX API -> snapshots de la categoria (orden descendente, hasta 1 anio atras)
  2. Por cada snapshot -> extraer URLs de articulos
  3. Deduplicar URLs con un set
  4. Por cada articulo unico -> descargar y parsear
  5. Escribir JSON en tiempo real

Instalacion:
    pip install requests beautifulsoup4 trafilatura

Uso:
    python noticias_economia.py
Uso:
    python noticias_economia.py              (default: 14 dias)
    python noticias_economia.py --dias 7
    python noticias_economia.py --dias 30
    python noticias_economia.py --dias 365
"""

import requests
import json
import time
import re
import html
import sys
import os
import argparse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import trafilatura

from env_utils import cargar_env
from dedup_utils import cargar_urls_ya_scrapeadas
from calidad_utils import motivo_descarte

cargar_env()  # carga ../.env (IA_S3_KEY, IA_S3_SECRET) a os.environ si existe

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# =============================================================
# ARGUMENTO --dias
# =============================================================

parser = argparse.ArgumentParser(description="Scraper de noticias de economia via Wayback Machine")
parser.add_argument("--dias", type=int, default=14, help="Ventana de dias hacia atras (default: 14)")
ARGS = parser.parse_args()

# =============================================================
# CONFIGURACION DE SITIOS
# =============================================================

HOY       = datetime.now()
HASTA_HOY = HOY.strftime("%Y%m%d")
DESDE     = (HOY - timedelta(days=ARGS.dias)).strftime("%Y%m%d")

SITIOS = [
    {
        "nombre":           "ambito economia",
        "url_categoria":    "www.ambito.com/economia/",
        "fecha_desde":      DESDE,
        "fecha_hasta":      HASTA_HOY,
        "patron_articulo":  r"ambito\.com/economia/.+-n\d+",
        "archivo_json":     "ambito_economia.json",
        "limite_articulos": 500,
    },
    {
        "nombre":           "ambito finanzas",
        "url_categoria":    "www.ambito.com/finanzas/",
        "fecha_desde":      DESDE,
        "fecha_hasta":      HASTA_HOY,
        "patron_articulo":  r"ambito\.com/finanzas/.+-n\d+",
        "archivo_json":     "ambito_finanzas.json",
        "limite_articulos": 500,
    },
    {
        "nombre":           "La Nacion economia",
        "url_categoria":    "lanacion.com.ar/economia/",
        "fecha_desde":      DESDE,
        "fecha_hasta":      HASTA_HOY,
        "patron_articulo":  r"lanacion\.com\.ar/economia/.+-nid\d+",
        "archivo_json":     "lanacion_economia.json",
        "limite_articulos": 500,
    },
    {
        "nombre":           "Clarin economia",
        "url_categoria":    "clarin.com/economia/",
        "fecha_desde":      DESDE,
        "fecha_hasta":      HASTA_HOY,
        "patron_articulo":  r"clarin\.com/economia/.+_0_[A-Za-z0-9]+\.html",
        "archivo_json":     "clarin_economia.json",
        "limite_articulos": 500,
    },
    {
        "nombre":           "TN economia",
        "url_categoria":    "tn.com.ar/economia/",
        "fecha_desde":      DESDE,
        "fecha_hasta":      HASTA_HOY,
        "patron_articulo":  r"tn\.com\.ar/economia/.+/\d{4}/\d{2}/\d{2}/.+",
        "archivo_json":     "tn_economia.json",
        "limite_articulos": 500,
    },
    {
        "nombre":           "Infobae economia",
        "url_categoria":    "infobae.com/economia/",
        "fecha_desde":      DESDE,
        "fecha_hasta":      HASTA_HOY,
        "patron_articulo":  r"infobae\.com/economia/\d{4}/\d{2}/\d{2}/.+",
        "archivo_json":     "infobae_economia.json",
        "limite_articulos": 500,
    },
]

# =============================================================
# OPCIONES GLOBALES
# =============================================================

PAUSA_CATEGORIA  = 2.0   # pausa entre snapshots de categoria
PAUSA_ARTICULO   = 1.0   # pausa entre articulos (por hilo)
HILOS            = 5     # hilos paralelos para descargar articulos
CARPETA_OUT      = "../resultados"

IA_S3_KEY    = os.environ.get("IA_S3_KEY", "")
IA_S3_SECRET = os.environ.get("IA_S3_SECRET", "")

if not IA_S3_KEY or not IA_S3_SECRET:
    print("[AVISO] IA_S3_KEY / IA_S3_SECRET no encontradas en ../.env -- las requests")
    print("        a Wayback van a ir sin autenticacion (rate limit mas bajo).")
    print("        Copiar ../.env.example a ../.env y completar las credenciales.")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EconomiaScraper/1.0)",
}
if IA_S3_KEY and IA_S3_SECRET:
    HEADERS["Authorization"] = "LOW " + IA_S3_KEY + ":" + IA_S3_SECRET

CDX_API      = "https://web.archive.org/cdx/search/cdx"
WAYBACK_BASE = "https://web.archive.org/web"


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
# PASO 1: Snapshots de la categoria (descendente)
# =============================================================

def obtener_snapshots_categoria(sesion, sitio):
    """
    Retorna lista de snapshots de la pagina de categoria,
    un snapshot por dia, ordenados de mas reciente a mas viejo.
    """
    print("  Consultando CDX para categoria (puede tardar)...")

    params = {
        "url":      sitio["url_categoria"],
        "output":   "json",
        "fl":       "timestamp,original",
        "from":     sitio["fecha_desde"],
        "to":       sitio["fecha_hasta"],
        "filter":   "statuscode:200",
        "collapse": "timestamp:8",   # un snapshot por dia
        "limit":    "365",
    }

    resp = sesion.get(CDX_API, params=params, headers=HEADERS, timeout=120)
    resp.raise_for_status()

    datos = resp.json()
    if not datos or len(datos) <= 1:
        print("  Sin snapshots encontrados.")
        return []

    columnas  = datos[0]
    snapshots = [dict(zip(columnas, fila)) for fila in datos[1:]]

    # Invertir: de mas reciente a mas viejo
    snapshots = snapshots[::-1]

    print("  Snapshots de categoria encontrados: " + str(len(snapshots)))
    print("  Desde: " + snapshots[0]["timestamp"][:8] +
          "  Hasta: " + snapshots[-1]["timestamp"][:8])
    return snapshots


# =============================================================
# PASO 2: Extraer URLs de articulos de un snapshot
# =============================================================

def extraer_urls_articulos(sesion, snapshot, patron_articulo):
    """
    Descarga el HTML del snapshot de la categoria y
    extrae todos los links que coincidan con el patron de articulo.
    """
    ts  = snapshot["timestamp"]
    url = snapshot["original"]
    url_wb = WAYBACK_BASE + "/" + ts + "if_/" + url

    resp = sesion.get(url_wb, headers=HEADERS, timeout=45)
    resp.raise_for_status()
    resp.encoding = resp.apparent_encoding

    soup = BeautifulSoup(resp.text, "html.parser")
    patron = re.compile(patron_articulo)

    urls = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]

        # Normalizar URL relativa
        if href.startswith("/"):
            dominio = re.match(r"https?://[^/]+", url)
            if dominio:
                href = dominio.group(0) + href

        # Limpiar URLs de Wayback embebidas
        # Ej: https://lanacion.com.ar/web/20260416001433/https://lanacion.com.ar/economia/nota-nid123
        # o:  https://web.archive.org/web/20260416001433/https://lanacion.com.ar/economia/nota-nid123
        match_wb = re.search(r'/web/\d{14}[a-z_]*/(.+)', href)
        if match_wb:
            href = match_wb.group(1)
            # Asegurar que empiece con https://
            if not href.startswith("http"):
                href = "https://" + href

        # Limpiar parametros de query y anchors
        href = href.split("?")[0].split("#")[0]

        if patron.search(href):
            urls.add(href)

    return urls


# =============================================================
# PASO 3: Buscar el mejor snapshot de un articulo en CDX
# =============================================================

def obtener_snapshot_articulo(sesion, url_articulo, fecha_desde, fecha_hasta):
    """
    Busca en CDX el snapshot mas antiguo disponible del articulo
    dentro del rango de fechas (el mas cercano a su publicacion real).
    """
    params = {
        "url":    url_articulo,
        "output": "json",
        "fl":     "timestamp,original",
        "from":   fecha_desde,
        "to":     fecha_hasta,
        "filter": "statuscode:200",
        "limit":  "1",   # solo el primero (mas antiguo)
    }

    resp = sesion.get(CDX_API, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    datos = resp.json()
    if not datos or len(datos) <= 1:
        return None

    return dict(zip(datos[0], datos[1]))


# =============================================================
# PASO 4: Parsear articulo
# Estrategia en capas:
#   1. JSON-LD  -> titulo, fecha, autor, bajada, tags  (estructurado)
#   2. Meta OG  -> fallback de titulo, bajada, fecha
#   3. Trafilatura -> contenido del articulo            (automatico, robusto)
#   4. BeautifulSoup -> fallback de contenido si trafilatura no extrae nada
# =============================================================

def extraer_metadata_jsonld(soup):
    """Extrae titulo, fecha, autor, bajada y tags del bloque JSON-LD."""
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
    """Fallback: extrae titulo, bajada y fecha de meta tags OG."""
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
    """Fallback de contenido: BeautifulSoup con selectores comunes."""
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
    # ultimo recurso: todos los <p>
    partes = [
        p.get_text(separator=" ", strip=True)
        for p in soup.find_all("p")
        if len(p.get_text(strip=True)) > 40
    ]
    return "\n\n".join(partes) if partes else None


def parsear_articulo(html, url, timestamp, nombre_sitio):
    soup = BeautifulSoup(html, "html.parser")

    art = {
        "sitio":              nombre_sitio,
        "url":                url,
        "timestamp_descarga":  timestamp,
        "fecha_descarga":      datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S"),
        "titulo":             None,
        "fecha_publicacion":  None,
        "fecha_modificacion": None,
        "autor":              None,
        "bajada":             None,
        "contenido":          None,
        "tags":               [],
    }

    # ── Capa 1: JSON-LD (fuente mas confiable) ──
    jsonld = extraer_metadata_jsonld(soup)
    art.update({k: v for k, v in jsonld.items() if v})

    # ── Capa 2: Meta OG como fallback de metadata ──
    og = extraer_metadata_og(soup)
    if not art["titulo"]:
        art["titulo"] = og.get("titulo")
    if not art["bajada"]:
        art["bajada"] = og.get("bajada")
    if not art["fecha_publicacion"]:
        art["fecha_publicacion"] = og.get("fecha_publicacion")

    # ── Capa 3: H1 si aun no hay titulo ──
    if not art["titulo"]:
        h1 = soup.find("h1")
        if h1:
            art["titulo"] = h1.get_text(strip=True)

    # Los titulos pueden llegar con entidades HTML (&quot; &amp; &#...): decodificarlas.
    if isinstance(art["titulo"], str):
        art["titulo"] = html.unescape(art["titulo"])

    # ── Capa 4: Trafilatura para el cuerpo del articulo ──
    # Trafilatura esta disenada para extraer el texto principal
    # de articulos de noticias, descartando menus, ads y footer
    contenido_trafilatura = trafilatura.extract(
        html,
        include_comments=False,
        include_tables=False,
        no_fallback=False,
        favor_precision=True,   # prioriza precision sobre cobertura
    )
    if contenido_trafilatura and len(contenido_trafilatura) > 100:
        art["contenido"] = contenido_trafilatura
    else:
        # ── Capa 5: BeautifulSoup como fallback de contenido ──
        art["contenido"] = extraer_contenido_bs(soup)

    return art


# =============================================================
# PROCESAR UN SITIO
# Guarda progresivamente en JSONL + checkpoint para poder retomar
# =============================================================

def cargar_checkpoint(archivo_jsonl):
    """
    Lee el JSONL existente y retorna el set de URLs ya procesadas.
    Si el archivo no existe, retorna set vacio (inicio desde cero).
    """
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
    """
    Convierte el JSONL a un JSON final legible con estructura completa.
    Se puede llamar en cualquier momento para ver el estado actual.
    """
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


def procesar_sitio(sesion, sitio):
    nombre        = sitio["nombre"]
    archivo_json  = os.path.join(CARPETA_OUT, sitio["archivo_json"])
    archivo_jsonl = archivo_json.replace(".json", ".jsonl")  # progresivo
    patron        = sitio["patron_articulo"]
    f_desde       = sitio["fecha_desde"]
    f_hasta       = sitio["fecha_hasta"]

    print("")
    print("=" * 60)
    print("SITIO:  " + nombre)
    print("URL:    " + sitio["url_categoria"])
    print("Rango:  " + f_desde + " -> " + f_hasta)
    print("=" * 60)

    # ── Cargar checkpoint: URLs ya procesadas en ejecuciones anteriores.
    # Se une con las URLs de TODOS los .jsonl de resultados/ (no solo el
    # propio) para no volver a bajar una nota que otro scraper ya bajo
    # hacia otro archivo -- ver AUDITORIA_CORPUS.md, hallazgo 4.1.
    urls_ya_procesadas = cargar_checkpoint(archivo_jsonl) | cargar_urls_ya_scrapeadas(CARPETA_OUT)
    if urls_ya_procesadas:
        print("Retomando: " + str(len(urls_ya_procesadas)) + " articulos ya procesados (este archivo + otras fuentes)")

    # ── PASO 1: snapshots de la categoria ──
    snapshots = obtener_snapshots_categoria(sesion, sitio)
    if not snapshots:
        return {"sitio": nombre, "noticias": 0, "errores": 0}

    # ── PASO 2: recolectar URLs, excluyendo las ya procesadas ──
    print("")
    print("Recolectando URLs de articulos...")
    urls_vistas = set()

    for i, snap in enumerate(snapshots, 1):
        fecha = snap["timestamp"][:8]
        print("  [" + str(i) + "/" + str(len(snapshots)) + "] snapshot " + fecha, end="")
        try:
            nuevas = extraer_urls_articulos(sesion, snap, patron)
            nuevas_unicas = nuevas - urls_vistas
            urls_vistas.update(nuevas)
            print(" -> " + str(len(nuevas)) + " links, " +
                  str(len(nuevas_unicas)) + " nuevos (total: " + str(len(urls_vistas)) + ")")
        except Exception as e:
            print(" -> [ERR] " + str(e)[:60])
        time.sleep(PAUSA_CATEGORIA)

    # Excluir URLs ya procesadas (checkpoint)
    urls_pendientes = [u for u in urls_vistas if u not in urls_ya_procesadas]
    print("")
    print("Total URLs encontradas:   " + str(len(urls_vistas)))
    print("Ya procesadas (checkpoint): " + str(len(urls_ya_procesadas)))
    print("Pendientes esta sesion:   " + str(len(urls_pendientes)))

    # Aplicar limite sobre las pendientes
    limite = sitio.get("limite_articulos")
    if limite and len(urls_pendientes) > limite:
        urls_pendientes = urls_pendientes[:limite]
        print("Limite aplicado: procesando " + str(limite) + " articulos")

    if not urls_pendientes:
        print("Nada nuevo para procesar.")
        return {"sitio": nombre, "noticias": len(urls_ya_procesadas), "errores": 0}

    # ── PASO 3 y 4: descargar con multihilo, guardar en JSONL ──
    total   = len(urls_pendientes)
    n_ok    = len(urls_ya_procesadas)   # contar los anteriores tambien
    n_error = 0
    n_descartadas = 0
    lock    = threading.Lock()

    print("Descargando " + str(total) + " articulos con " + str(HILOS) + " hilos...")
    print("Guardando progresivamente en: " + archivo_jsonl)
    print("")

    def procesar_articulo(idx_url):
        idx, url = idx_url
        html   = None
        fuente = None
        ts     = HOY.strftime("%Y%m%d%H%M%S")

        # Fuente 1: sitio original
        try:
            resp = sesion.get(url, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding
            html   = resp.text
            fuente = "original"
        except Exception:
            pass

        # Fuente 2: Wayback Machine
        if not html:
            try:
                snap_art = obtener_snapshot_articulo(sesion, url, f_desde, f_hasta)
                if snap_art:
                    ts     = snap_art["timestamp"]
                    url_wb = WAYBACK_BASE + "/" + ts + "if_/" + url
                    resp   = sesion.get(url_wb, headers=HEADERS, timeout=45)
                    resp.raise_for_status()
                    resp.encoding = resp.apparent_encoding
                    html   = resp.text
                    fuente = "wayback"
            except Exception:
                pass

        if not html:
            time.sleep(PAUSA_ARTICULO)
            return (idx, url, None, "Sin contenido (original y wayback fallaron)")

        try:
            noticia = parsear_articulo(html, url, ts, nombre)
            noticia["fuente"] = fuente
            time.sleep(PAUSA_ARTICULO)
            # La Nacion devuelve un stub de paywall en vez del articulo (ver calidad_utils.py).
            # No se filtra por fecha: la ventana de v3 la define el snapshot de Wayback.
            motivo = motivo_descarte(noticia)
            if motivo:
                return (idx, url, None, "DESCARTADA:" + motivo)
            return (idx, url, noticia, None)
        except Exception as e:
            time.sleep(PAUSA_ARTICULO)
            return (idx, url, None, "Error parseando: " + str(e))

    # Abrir JSONL en modo append para no perder lo anterior
    with open(archivo_jsonl, "a", encoding="utf-8") as jsonl_f:

        with ThreadPoolExecutor(max_workers=HILOS) as executor:
            futuros = {
                executor.submit(procesar_articulo, (i, url)): i
                for i, url in enumerate(urls_pendientes, 1)
            }

            for futuro in as_completed(futuros):
                idx, url, noticia, error = futuro.result()
                prefijo = "[" + str(idx) + "/" + str(total) + "] "

                with lock:
                    if noticia:
                        # Escribir linea JSONL inmediatamente
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

    # Generar JSON final a partir del JSONL completo
    meta = {
        "sitio":          nombre,
        "url":            sitio["url_categoria"],
        "fecha_desde":    f_desde,
        "fecha_hasta":    f_hasta,
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
    print("Scraper multi-sitio - Noticias de economia")
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
