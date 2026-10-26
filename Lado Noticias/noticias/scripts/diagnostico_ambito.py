# -*- coding: utf-8 -*-
"""
Diagnostico: verifica snapshots y patrones de URL para ambito.com en la
Wayback Machine (CDX API). Util para debuggear noticias_historico_v3.py
cuando el scraping de Ambito no encuentra snapshots o falla el parseo:
corre esto primero para confirmar que existen snapshots en el rango de
fechas esperado antes de asumir que el problema esta en el parser.
"""

import requests
import re
import json
from datetime import datetime, timedelta

HOY       = datetime.now()
UN_SEMANA = (HOY - timedelta(days=7)).strftime("%Y%m%d")
UN_MES    = (HOY - timedelta(days=30)).strftime("%Y%m%d")
HASTA_HOY = HOY.strftime("%Y%m%d")
CDX_API   = "https://web.archive.org/cdx/search/cdx"
HEADERS   = {"User-Agent": "Mozilla/5.0 (compatible; EconomiaScraper/1.0)"}

def consultar_cdx(url_categoria, fecha_desde, fecha_hasta, etiqueta):
    params = {
        "url":      url_categoria,
        "output":   "json",
        "fl":       "timestamp,original",
        "from":     fecha_desde,
        "to":       fecha_hasta,
        "filter":   "statuscode:200",
        "collapse": "timestamp:8",
        "limit":    "3",
    }
    try:
        r = requests.get(CDX_API, params=params, headers=HEADERS, timeout=30)
        r.raise_for_status()
        data = r.json()
        n = max(0, len(data) - 1)
        print(f"  [{etiqueta}]  url='{url_categoria}'  rango={fecha_desde}-{fecha_hasta}  snapshots={n}")
        if n > 0:
            for fila in data[1:]:
                print(f"    -> ts={fila[0]}  original={fila[1]}")
        return n
    except Exception as e:
        print(f"  [{etiqueta}]  ERROR: {e}")
        return 0


print("=" * 65)
print("DIAGNOSTICO 1: snapshots de la pagina de categoria")
print("=" * 65)

variantes = [
    ("sin-www  / 7d",  "ambito.com/economia/",      UN_SEMANA, HASTA_HOY),
    ("con-www  / 7d",  "www.ambito.com/economia/",  UN_SEMANA, HASTA_HOY),
    ("sin-www  / 30d", "ambito.com/economia/",      UN_MES,    HASTA_HOY),
    ("con-www  / 30d", "www.ambito.com/economia/",  UN_MES,    HASTA_HOY),
]

url_correcta = None
for etiqueta, url, f_desde, f_hasta in variantes:
    n = consultar_cdx(url, f_desde, f_hasta, etiqueta)
    if n > 0 and url_correcta is None:
        url_correcta = url

print()
if url_correcta:
    print(f"[OK] URL que funciona: '{url_correcta}'")
else:
    print("[!!] Ninguna variante devolvio snapshots. Quiza la pagina no esta archivada.")


# ----------------------------------------------------------------
print()
print("=" * 65)
print("DIAGNOSTICO 2: patron de articulos en un snapshot real")
print("=" * 65)

if url_correcta:
    # Buscar un snapshot reciente de la categoria
    params_snap = {
        "url":      url_correcta,
        "output":   "json",
        "fl":       "timestamp,original",
        "from":     UN_MES,
        "to":       HASTA_HOY,
        "filter":   "statuscode:200",
        "collapse": "timestamp:8",
        "limit":    "1",
    }
    try:
        r = requests.get(CDX_API, params=params_snap, headers=HEADERS, timeout=30)
        data = r.json()
        if len(data) > 1:
            ts, orig = data[1][0], data[1][1]
            url_wb = f"https://web.archive.org/web/{ts}if_/{orig}"
            print(f"  Descargando snapshot: {ts} -> {orig}")
            html_resp = requests.get(url_wb, headers=HEADERS, timeout=45)
            html_resp.encoding = html_resp.apparent_encoding
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_resp.text, "html.parser")
            todos_hrefs = [a["href"] for a in soup.find_all("a", href=True)]

            patron_nid  = re.compile(r"ambito\.com/economia/.+-nid\d+")
            patron_n    = re.compile(r"ambito\.com/economia/.+-n\d+")
            patron_gen  = re.compile(r"ambito\.com/economia/[^\"'\s]+")

            matches_nid = [h for h in todos_hrefs if patron_nid.search(h)]
            matches_n   = [h for h in todos_hrefs if patron_n.search(h)]
            matches_gen = [h for h in todos_hrefs if patron_gen.search(h)]

            print(f"\n  patron '-nid\\d+'  (el que esta en el script) : {len(matches_nid)} matches")
            print(f"  patron '-n\\d+'    (sin 'id')                  : {len(matches_n)} matches")
            print(f"  patron generico   (cualquier /economia/...)    : {len(matches_gen)} matches")

            if matches_gen:
                print(f"\n  Ejemplos de URLs encontradas en el HTML:")
                for href in matches_gen[:5]:
                    print(f"    {href}")
        else:
            print("  No se encontro ningun snapshot para testear el patron.")
    except Exception as e:
        print(f"  ERROR al descargar snapshot: {e}")
else:
    print("  (saltado porque no se encontraron snapshots en diagnostico 1)")

print()
print("=" * 65)
print("CONCLUSION Y CORRECCIONES SUGERIDAS")
print("=" * 65)
print("""
Si diagnostico 1 muestra que 'www.ambito.com/economia/' funciona
pero 'ambito.com/economia/' no -> cambiar url_categoria a:
    "url_categoria": "www.ambito.com/economia/"

Si diagnostico 2 muestra que '-n\\d+' tiene mas matches que '-nid\\d+' -> cambiar patron a:
    "patron_articulo": r"ambito\\.com/economia/.+-n\\d+"

Si ningun patron encuentra articulos -> ver los ejemplos de URLs
y ajustar el patron segun ese formato real.
""")
