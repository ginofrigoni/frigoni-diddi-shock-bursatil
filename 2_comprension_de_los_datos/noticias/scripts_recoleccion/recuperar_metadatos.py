# -*- coding: utf-8 -*-
"""
Recupera fecha de publicacion, autor, tags y fecha de modificacion de los
articulos de un .jsonl que quedaron sin fecha_publicacion por el bug del
JSON-LD (caracteres de control -> json.loads estricto fallaba, ver
calidad_utils.py). Vuelve a bajar solo esos articulos y completa los campos
que faltan; no pisa ningun dato ya existente ni toca el contenido.

Uso (desde scripts/):
    python recuperar_metadatos.py                       # eleconomista_sitemap
    python recuperar_metadatos.py --archivo iprofesional_sitemap --solo-sin-autor
"""

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from calidad_utils import PATRON_ARTICULO, metadata_jsonld, sincronizar_json, url_es_articulo

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CARPETA = "../resultados"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; EconomiaScraper/1.0)"}
HILOS = 5
PAUSA = 1.0


def sesion():
    s = requests.Session()
    r = Retry(total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
    s.mount("https://", HTTPAdapter(max_retries=r))
    return s


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--archivo", default="eleconomista_sitemap")
    ap.add_argument("--solo-sin-autor", action="store_true",
                    help="en vez de 'sin fecha', recuperar los que no tienen autor")
    args = ap.parse_args()

    ruta = os.path.join(CARPETA, args.archivo + ".jsonl")
    patron = PATRON_ARTICULO[args.archivo]
    with open(ruta, "r", encoding="utf-8") as f:
        arts = [json.loads(l) for l in f if l.strip()]

    campo = "autor" if args.solo_sin_autor else "fecha_publicacion"
    pendientes = [i for i, a in enumerate(arts) if not a.get(campo) and url_es_articulo(a["url"], patron)]
    print(f"{args.archivo}: {len(arts)} articulos, {len(pendientes)} sin '{campo}' con URL de articulo")

    s = sesion()

    def bajar(i):
        url = arts[i]["url"]
        try:
            r = s.get(url, headers=HEADERS, timeout=45)
            r.raise_for_status()
            meta = metadata_jsonld(r.text)
            if not meta.get("fecha_publicacion"):
                m = re.search(r'datePublished"\s*:\s*"([^"]+)"', r.text)
                if m:
                    meta["fecha_publicacion"] = m.group(1)
            time.sleep(PAUSA)
            return i, meta, None
        except Exception as e:
            time.sleep(PAUSA)
            return i, {}, str(e)[:80]

    recuperados = {"fecha_publicacion": 0, "autor": 0, "tags": 0, "fecha_modificacion": 0}
    errores = []
    with ThreadPoolExecutor(max_workers=HILOS) as ex:
        futuros = [ex.submit(bajar, i) for i in pendientes]
        for n, fut in enumerate(as_completed(futuros), 1):
            i, meta, err = fut.result()
            if err:
                errores.append((arts[i]["url"], err))
                continue
            for k in ("fecha_publicacion", "fecha_modificacion", "autor", "tags"):
                if meta.get(k) and not arts[i].get(k):
                    arts[i][k] = meta[k]
                    recuperados[k] += 1
            if n % 25 == 0 or n == len(pendientes):
                print(f"  [{n}/{len(pendientes)}] recuperados={recuperados} errores={len(errores)}")

    tmp = ruta + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        for a in arts:
            f.write(json.dumps(a, ensure_ascii=False) + "\n")
    os.replace(tmp, ruta)
    sincronizar_json(ruta)

    sin = sum(1 for a in arts if not a.get("fecha_publicacion"))
    print(f"\nListo. Recuperados: {recuperados} | errores: {len(errores)} | sin fecha_publicacion tras recuperar: {sin}")
    for u, e in errores[:10]:
        print("  ERR", u[-70:], e)


if __name__ == "__main__":
    main()
