# -*- coding: utf-8 -*-
"""
Elimina contenido repetido por plantilla del corpus ya recolectado
(ver DEPURACION_CALIDAD.md, seccion "Contenido repetido por plantilla").

Agrupa los articulos de una misma fuente cuyo texto empieza igual (primeros
--prefijo caracteres, normalizado) y aplica dos reglas:

  contenido_duplicado   en cada grupo de 2 o mas se conserva la nota mas antigua
                        (fecha_publicacion, luego url) y se eliminan las demas.
  contenido_plantilla   si el grupo tiene --grupo-plantilla o mas notas, el cuerpo
                        es relleno fijo (cotizacion del dia, promo, bloque de
                        navegacion extraido en lugar de la nota): se eliminan TODAS,
                        incluida la mas antigua.

Escribe un reporte con cada URL eliminada, su motivo y el tamano del grupo en
../analisis_calidad/depuracion_plantillas_<fecha>.json; dedup_utils lo lee para
que los scrapers no vuelvan a bajar esas URLs. Deja .json y .jsonl consistentes.

Uso (desde scripts/):
    python depurar_plantillas.py            # solo informa
    python depurar_plantillas.py --aplicar  # elimina y escribe el reporte
"""

import argparse
import collections
import json
import os
import re
import sys
from datetime import datetime

from calidad_utils import sincronizar_json

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CARPETA = "../resultados"
CARPETA_REPORTE = "../analisis_calidad"


def normalizar(texto):
    return re.sub(r"\s+", " ", (texto or "").strip().lower())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    ap.add_argument("--prefijo", type=int, default=160,
                    help="caracteres iniciales que definen el grupo (default 160)")
    ap.add_argument("--grupo-plantilla", type=int, default=11,
                    help="tamano de grupo desde el cual se elimina TODO el grupo (default 11)")
    args = ap.parse_args()

    corpus = {}
    for nombre in sorted(os.listdir(CARPETA)):
        if nombre.endswith(".jsonl"):
            with open(os.path.join(CARPETA, nombre), "r", encoding="utf-8") as f:
                corpus[nombre] = [json.loads(l) for l in f if l.strip()]

    grupos = collections.defaultdict(list)
    for nombre, arts in corpus.items():
        for a in arts:
            c = normalizar(a.get("contenido"))
            if len(c) >= args.prefijo:
                grupos[(nombre, c[:args.prefijo])].append(a)

    eliminar = {}  # url -> registro del reporte
    for (nombre, _), miembros in grupos.items():
        if len(miembros) < 2:
            continue
        miembros = sorted(miembros, key=lambda a: ((a.get("fecha_publicacion") or ""), a["url"]))
        plantilla = len(miembros) >= args.grupo_plantilla
        for i, a in enumerate(miembros):
            if i == 0 and not plantilla:
                continue
            eliminar[a["url"]] = {
                "archivo": nombre, "url": a["url"],
                "motivo": "contenido_plantilla" if plantilla else "contenido_duplicado",
                "tamano_grupo": len(miembros), "titulo": a.get("titulo"),
                "fecha_publicacion": a.get("fecha_publicacion"),
            }

    resumen = {}
    for nombre, arts in corpus.items():
        quedan = [a for a in arts if a["url"] not in eliminar]
        resumen[nombre] = {"antes": len(arts), "despues": len(quedan), "eliminadas": len(arts) - len(quedan)}
        print(f"{nombre}: {len(arts)} -> {len(quedan)}  ({len(arts) - len(quedan)} a eliminar)")
        if args.aplicar and len(quedan) != len(arts):
            ruta = os.path.join(CARPETA, nombre)
            tmp = ruta + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                for a in quedan:
                    f.write(json.dumps(a, ensure_ascii=False) + "\n")
            os.replace(tmp, ruta)
            sincronizar_json(ruta)

    por_motivo = collections.Counter(e["motivo"] for e in eliminar.values())
    print(f"\nTotal: {sum(v['antes'] for v in resumen.values())} -> "
          f"{sum(v['despues'] for v in resumen.values())} ({len(eliminar)} eliminadas: {dict(por_motivo)})")

    if args.aplicar and eliminar:
        os.makedirs(CARPETA_REPORTE, exist_ok=True)
        ruta_rep = os.path.join(CARPETA_REPORTE,
                                "depuracion_plantillas_" + datetime.now().strftime("%Y-%m-%d") + ".json")
        eliminadas = list(eliminar.values())
        if os.path.exists(ruta_rep):
            with open(ruta_rep, "r", encoding="utf-8") as f:
                prev = json.load(f)
            eliminadas = prev["eliminadas"] + eliminadas
            for k, v in prev["resumen"].items():
                if k in resumen:
                    resumen[k] = {"antes": v["antes"], "despues": resumen[k]["despues"],
                                  "eliminadas": v["antes"] - resumen[k]["despues"]}
        with open(ruta_rep, "w", encoding="utf-8") as f:
            json.dump({"prefijo": args.prefijo, "grupo_plantilla": args.grupo_plantilla,
                       "resumen": resumen, "eliminadas": eliminadas}, f, ensure_ascii=False, indent=2)
        print("Reporte:", ruta_rep)
    elif not args.aplicar:
        print("(solo informe; correr con --aplicar para eliminar)")


if __name__ == "__main__":
    main()
