# -*- coding: utf-8 -*-
"""
Depuracion unica del corpus ya recolectado. Aplica las mismas reglas que los
scrapers ahora aplican al recolectar (calidad_utils.py) sobre resultados/*.jsonl:

  1. no_articulo            URL que no tiene forma de articulo (paginas indice de seccion)
  2. paywall                stub "Suscribite a LA NACION..." en lugar del articulo
  3. fecha_fuera_de_ventana fecha de PUBLICACION real anterior a --desde (default 2025-01-01)
  4. fecha_posterior_a_recoleccion  fecha posterior a --hasta (fin de la recoleccion, default 2026-05-03)

Escribe un reporte con cada URL eliminada y su motivo en
../analisis_calidad/depuracion_<fecha>.json y deja .json y .jsonl consistentes.

Uso (desde scripts/):
    python depurar_corpus.py            # solo informa
    python depurar_corpus.py --aplicar  # elimina y escribe el reporte
"""

import argparse
import json
import os
import sys
from datetime import datetime

from calidad_utils import (PATRON_ARTICULO, es_paywall, fecha_fuera_de_ventana,
                           fecha_posterior_a_recoleccion, sincronizar_json, url_es_articulo)

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CARPETA = "../resultados"
CARPETA_REPORTE = "../analisis_calidad"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--desde", default="2025-01-01", help="inicio de la ventana del corpus (YYYY-MM-DD)")
    ap.add_argument("--hasta", default="2026-05-03", help="fecha en que termino la recoleccion (YYYY-MM-DD)")
    args = ap.parse_args()
    desde_dt = datetime.strptime(args.desde, "%Y-%m-%d")
    hasta_dt = datetime.strptime(args.hasta, "%Y-%m-%d")

    eliminadas = []
    resumen = {}
    for nombre in sorted(os.listdir(CARPETA)):
        if not nombre.endswith(".jsonl"):
            continue
        base = nombre[:-6]
        ruta = os.path.join(CARPETA, nombre)
        with open(ruta, "r", encoding="utf-8") as f:
            arts = [json.loads(l) for l in f if l.strip()]

        quedan, fuera = [], []
        for a in arts:
            if not url_es_articulo(a["url"], PATRON_ARTICULO[base]):
                motivo = "no_articulo"
            elif es_paywall(a):
                motivo = "paywall"
            elif fecha_fuera_de_ventana(a, desde_dt):
                motivo = "fecha_fuera_de_ventana"
            elif fecha_posterior_a_recoleccion(a, hasta_dt):
                motivo = "fecha_posterior_a_recoleccion"
            else:
                motivo = None
            if motivo:
                fuera.append({"archivo": nombre, "url": a["url"], "motivo": motivo,
                              "titulo": a.get("titulo"), "fecha_publicacion": a.get("fecha_publicacion")})
            else:
                quedan.append(a)

        resumen[nombre] = {"antes": len(arts), "despues": len(quedan), "eliminadas": len(fuera)}
        eliminadas += fuera
        if fuera:
            print(f"{nombre}: {len(arts)} -> {len(quedan)}  ({len(fuera)} a eliminar)")
            for e in fuera:
                print("    ", e["motivo"], "|", (e["fecha_publicacion"] or "")[:10], "|", e["url"][-70:])
        if fuera and args.aplicar:
            tmp = ruta + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for a in quedan:
                    f.write(json.dumps(a, ensure_ascii=False) + "\n")
            os.replace(tmp, ruta)
            sincronizar_json(ruta)

    total_antes = sum(v["antes"] for v in resumen.values())
    total_despues = sum(v["despues"] for v in resumen.values())
    print(f"\nTotal: {total_antes} -> {total_despues} ({len(eliminadas)} eliminadas)")

    if args.aplicar and eliminadas:
        os.makedirs(CARPETA_REPORTE, exist_ok=True)
        ruta_rep = os.path.join(CARPETA_REPORTE, "depuracion_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        if os.path.exists(ruta_rep):
            # varias corridas el mismo dia: acumular en vez de pisar el reporte anterior
            with open(ruta_rep, "r", encoding="utf-8") as f:
                prev = json.load(f)
            eliminadas = prev["eliminadas"] + eliminadas
            for k, v in prev["resumen"].items():
                if k in resumen:
                    resumen[k] = {"antes": v["antes"], "despues": resumen[k]["despues"],
                                  "eliminadas": v["antes"] - resumen[k]["despues"]}
        with open(ruta_rep, "w", encoding="utf-8") as f:
            json.dump({"ventana_desde": args.desde, "ventana_hasta": args.hasta,
                       "resumen": resumen, "eliminadas": eliminadas},
                      f, ensure_ascii=False, indent=2)
        print("Reporte:", ruta_rep)
    elif not args.aplicar:
        print("(solo informe; correr con --aplicar para eliminar)")


if __name__ == "__main__":
    main()
