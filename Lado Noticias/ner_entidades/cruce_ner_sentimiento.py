# -*- coding: utf-8 -*-
"""
Cruce NER x sentimiento: para cada entidad, el sentimiento (FinBETO) de las
oraciones donde aparece.

Entradas
  resultados_ner/ner_oraciones.csv         una fila por mencion (url, oracion_idx, entidad, tipo, subtipo)
  beto_oraciones_finetuned.csv             sentimiento FinBETO por oracion (url, or_idx, oracion, label, score).
                                           Copia en ../sentimiento_finbert/ (177 MB, traida de tesis version 2.0,
                                           finetuning_evaluacion/, sin cambios; sha256 f4b9c10f...).

Se une por (url, oracion_idx == or_idx) y se EXIGE que el texto de la oracion coincida
(normalizado); las oraciones que no coinciden se descartan y se cuentan en el reporte.
No se usa el baseline sin fine-tuning: su or_idx no incluye el titulo y queda corrido en 1
respecto de ner_oraciones.

Salidas (resultados_ner/)
  ner_sentimiento.csv          una fila por (entidad, tipo, subtipo)
  ner_sentimiento_diario.csv   una fila por (fecha, entidad) para EMP_MERVAL e IND_ECO
  ner_sentimiento_reporte.json cobertura del cruce

Los indicadores (IND_ECO) se unifican con equivalencias_indicadores.py antes de contar: una oracion
que menciona "ccl" y "contado con liquidacion" cuenta una sola vez para "ccl".

sent_neto = (n_pos - n_neg) / n_oraciones * 100, igual que el sent_neto por articulo de la
serie diaria (la proporcion se calcula sobre las 4 clases: POS, NEG, NEU, MIXTO).

Uso (desde ner_entidades/):
    python cruce_ner_sentimiento.py
    python cruce_ner_sentimiento.py --oraciones otra/ruta.csv   # para usar otro archivo
"""

import argparse
import collections
import csv
import json
import re
import sys
from pathlib import Path

from equivalencias_indicadores import EQUIVALENCIAS_IND_ECO, canonico

csv.field_size_limit(10 ** 9)
if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SALIDA = Path("resultados_ner")
CLASES = ("POS", "NEG", "NEU", "MIXTO")
TIPOS_DIARIOS = ("EMP_MERVAL", "IND_ECO")


def norm(texto):
    return re.sub(r"\s+", " ", (texto or "").strip().rstrip(".").strip().lower())


def fila_resumen(acum):
    n = sum(acum[c] for c in CLASES)
    fila = {"n_oraciones": n}
    for c in CLASES:
        fila["n_" + c.lower()] = acum[c]
    for c in CLASES:
        fila["pct_" + c.lower()] = round(100 * acum[c] / n, 2)
    fila["sent_neto"] = round(100 * (acum["POS"] - acum["NEG"]) / n, 2)
    return fila


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--oraciones", default=str(Path(__file__).resolve().parent.parent / "sentimiento_finbert" / "beto_oraciones_finetuned.csv"),
                    help="sentimiento FinBETO por oracion (default: ../sentimiento_finbert/beto_oraciones_finetuned.csv)")
    ap.add_argument("--min-oraciones", type=int, default=5,
                    help="minimo de oraciones para listar una entidad en ner_sentimiento.csv (default 5)")
    args = ap.parse_args()

    print("Leyendo sentimiento por oracion...")
    sent = {}
    with open(args.oraciones, "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            sent[(r["url"], r["or_idx"])] = (norm(r["oracion"]), r["label"])
    print(f"  {len(sent):,} oraciones con sentimiento")

    print("Cruzando con ner_oraciones.csv...")
    vistos = set()          # (url, idx, entidad, tipo): una oracion cuenta una vez por entidad
    oraciones_ner = set()
    oraciones_unidas = set()
    sin_match_idx = set()
    sin_match_texto = set()
    por_entidad = collections.defaultdict(lambda: collections.Counter())
    arts_entidad = collections.defaultdict(set)
    por_dia = collections.defaultdict(lambda: collections.Counter())
    arts_dia = collections.defaultdict(set)

    with open(SALIDA / "ner_oraciones.csv", "r", encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            k = (r["url"], r["oracion_idx"])
            oraciones_ner.add(k)
            s = sent.get(k)
            if s is None:
                sin_match_idx.add(k)
                continue
            if s[0] != norm(r["oracion"]):
                sin_match_texto.add(k)
                continue
            oraciones_unidas.add(k)
            ent = canonico(r["entidad"].strip().lower(), r["tipo"])
            clave = (ent, r["tipo"], r["subtipo"])
            v = (k, ent, r["tipo"])
            if v in vistos:
                continue
            vistos.add(v)
            por_entidad[clave][s[1]] += 1
            arts_entidad[clave].add(r["url"])
            if r["tipo"] in TIPOS_DIARIOS:
                kd = (r["fecha"], ent, r["tipo"], r["subtipo"])
                por_dia[kd][s[1]] += 1
                arts_dia[kd].add(r["url"])

    # ner_sentimiento.csv
    filas = []
    for (ent, tipo, sub), acum in por_entidad.items():
        fila = fila_resumen(acum)
        if fila["n_oraciones"] < args.min_oraciones:
            continue
        filas.append({"entidad": ent, "tipo": tipo, "subtipo": sub,
                      "n_articulos": len(arts_entidad[(ent, tipo, sub)]), **fila})
    filas.sort(key=lambda x: -x["n_oraciones"])
    campos = ["entidad", "tipo", "subtipo", "n_articulos", "n_oraciones",
              "n_pos", "n_neg", "n_neu", "n_mixto", "pct_pos", "pct_neg", "pct_neu", "pct_mixto", "sent_neto"]
    with open(SALIDA / "ner_sentimiento.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)

    # ner_sentimiento_diario.csv
    diario = []
    for (fecha, ent, tipo, sub), acum in por_dia.items():
        diario.append({"fecha": fecha, "entidad": ent, "tipo": tipo, "subtipo": sub,
                       "n_articulos": len(arts_dia[(fecha, ent, tipo, sub)]), **fila_resumen(acum)})
    diario.sort(key=lambda x: (x["fecha"], x["tipo"], x["entidad"]))
    campos_d = ["fecha", "entidad", "tipo", "subtipo", "n_articulos", "n_oraciones",
                "n_pos", "n_neg", "n_neu", "n_mixto", "pct_pos", "pct_neg", "pct_neu", "pct_mixto", "sent_neto"]
    with open(SALIDA / "ner_sentimiento_diario.csv", "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos_d)
        w.writeheader()
        w.writerows(diario)

    reporte = {
        "equivalencias_ind_eco_aplicadas": len(EQUIVALENCIAS_IND_ECO),
        "oraciones_ner": len(oraciones_ner),
        "unidas": len(oraciones_unidas),
        "sin_sentimiento_para_url_idx": len(sin_match_idx),
        "texto_distinto": len(sin_match_texto),
        "cobertura_pct": round(100 * len(oraciones_unidas) / len(oraciones_ner), 2),
        "entidades_en_ner_sentimiento": len(filas),
        "filas_diario": len(diario),
        "min_oraciones": args.min_oraciones,
    }
    with open(SALIDA / "ner_sentimiento_reporte.json", "w", encoding="utf-8") as f:
        json.dump(reporte, f, ensure_ascii=False, indent=2)

    print(json.dumps(reporte, ensure_ascii=False, indent=2))
    for tipo in ("EMP_MERVAL", "IND_ECO", "ORG", "PER"):
        top = [x for x in filas if x["tipo"] == tipo][:8]
        print(f"\n--- {tipo} (top 8 por oraciones) ---")
        for x in top:
            print(f"  {x['entidad']:28s} oraciones:{x['n_oraciones']:6d}  sent_neto:{x['sent_neto']:7.2f}  "
                  f"pos:{x['pct_pos']:5.1f}%  neg:{x['pct_neg']:5.1f}%")


if __name__ == "__main__":
    main()
