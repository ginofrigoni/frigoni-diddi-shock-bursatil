# -*- coding: utf-8 -*-
"""
Sentimiento de cada nota a partir del sentimiento de sus oraciones (tesis versión 6.0).
Fase 3 de CRISP-DM (preparación).

Reproduce la función registros_desde_oraciones() de serie_completa_finetuned.py (5.0, opción
--desde-oraciones), que es la que usaba el pipeline:
  - el corpus se carga de los 9 .jsonl en el mismo orden; ante una URL repetida manda la primera
    aparición, y se excluyen los duplicados semánticos;
  - de cada nota se toman sus oraciones (título + cuerpo) de beto_oraciones_finetuned.csv; si un
    or_idx aparece dos veces manda el primero;
  - se excluyen las oraciones de relleno del scraping ("Sobre la firma", "PUBLICIDAD"...), con las
    mismas reglas que limpiar_etiquetado.py;
  - sentimiento neto de la nota = % de oraciones POS − % de oraciones NEG (NEU aporta 0).

Control: con --control-5.0 se corre con las etiquetas de la 5.0 y se compara contra el
finetuned_articulos.csv de la 5.0. Tiene que dar idéntico: así se sabe que el cálculo es el mismo y
que lo único que cambia en la 6.0 es la etiqueta de cada oración.

Entradas:
  2_comprension_de_los_datos/noticias/datos/*.jsonl y reporte_dedup_semantico.json
  salidas/beto_oraciones_finetuned.csv
Salidas:
  salidas/sentimiento_por_nota.csv   una fila por nota (14.012)
  metricas_por_nota.csv

Uso:  python sentimiento_por_nota.py [--control-5.0]
"""

import argparse
import csv
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from limpiar_etiquetado import MIN_LETRAS, limpiar

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).parent
RAIZ = AQUI.parent.parent
DATOS = RAIZ / "2_comprension_de_los_datos" / "noticias" / "datos"
ORACIONES = AQUI / "salidas" / "beto_oraciones_finetuned.csv"
SALIDA = AQUI / "salidas" / "sentimiento_por_nota.csv"
REF_50 = RAIZ.parent / "tesis version 5.0" / "Lado Noticias" / "sentimiento_finbert"
ARCHIVOS = ["ambito_economia", "ambito_finanzas", "clarin_economia", "clarin_sitemap", "eleconomista_sitemap",
            "infobae_economia", "iprofesional_sitemap", "lanacion_economia", "tn_economia"]


def cargar_corpus():
    excluir = set(json.loads((DATOS / "reporte_dedup_semantico.json").read_text(encoding="utf-8")).get("urls_a_eliminar", []))
    arts, vistas = [], set()
    for archivo in ARCHIVOS:
        for linea in open(DATOS / f"{archivo}.jsonl", encoding="utf-8"):
            linea = linea.strip()
            if not linea:
                continue
            a = json.loads(linea)
            url = a.get("url")
            if url in excluir or (url and url in vistas):
                continue
            if url:
                vistas.add(url)
            a["_fuente"] = archivo
            arts.append(a)
    return arts


def agregar(preds, clases):
    labels = [p["label"] for p in preds]
    conteo = Counter(labels)
    total = len(labels)
    pct = {c: round(conteo.get(c, 0) / total * 100, 2) for c in clases}
    r = {"n_oraciones": total, "label_dominante": conteo.most_common(1)[0][0]}
    r.update({f"pct_{c.lower()}": pct[c] for c in clases})
    r["sent_neto"] = round(pct["POS"] - pct["NEG"], 2)
    r.update({f"n_{c.lower()}": conteo.get(c, 0) for c in clases})
    r["score_promedio"] = round(sum(p["score"] for p in preds) / total, 4)
    return r


def sentimiento_por_nota(ruta_oraciones, clases):
    arts = cargar_corpus()
    por_url = {a["url"]: a for a in arts}
    oraciones, n_relleno = {}, 0
    with open(ruta_oraciones, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            url = r["url"]
            if url not in por_url:
                continue
            d = oraciones.setdefault(url, {})
            if r["or_idx"] in d:
                continue
            texto = r["oracion"].strip()
            sin_marca = limpiar(texto)
            letras = len(re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]", sin_marca))
            if sin_marca != texto and letras < MIN_LETRAS:
                n_relleno += 1
                d[r["or_idx"]] = None
                continue
            d[r["or_idx"]] = {"label": r["label"], "score": float(r["score"])}
    filas, sin_oraciones = [], 0
    for url, a in por_url.items():
        preds = [p for p in oraciones.get(url, {}).values() if p is not None]
        if not preds:
            sin_oraciones += 1
            continue
        filas.append({"url": url, "fuente": a["_fuente"], "fecha": (a.get("fecha_publicacion") or "")[:10],
                      "titulo": a.get("titulo", ""), **agregar(preds, clases)})
    usadas = sum(len(d) for d in oraciones.values()) - n_relleno
    return pd.DataFrame(filas), {"notas_corpus": len(por_url), "notas_con_sentimiento": len(filas),
                                 "notas_sin_oraciones": sin_oraciones, "oraciones_relleno_excluidas": n_relleno,
                                 "oraciones_usadas": usadas}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--control-5.0", dest="control", action="store_true")
    a = ap.parse_args()
    if a.control:
        d, info = sentimiento_por_nota(REF_50 / "beto_oraciones_finetuned.csv", ["POS", "NEG", "NEU", "MIXTO"])
        ref = pd.read_csv(REF_50 / "finetuned_articulos.csv", dtype=str, keep_default_na=False)
        nuevo = pd.read_csv(pd.io.common.StringIO(d.to_csv(index=False)), dtype=str, keep_default_na=False)
        print("Control con las etiquetas de la 5.0:", info)
        print("Idéntico a finetuned_articulos.csv de la 5.0:", ref.equals(nuevo[ref.columns]))
        return
    d, info = sentimiento_por_nota(ORACIONES, ["POS", "NEG", "NEU"])
    d.to_csv(SALIDA, index=False, encoding="utf-8")
    filas = [{"metrica": k, "valor": v} for k, v in info.items()]
    filas += [{"metrica": "sent_neto_nota_media", "valor": round(d["sent_neto"].mean(), 2)},
              {"metrica": "sent_neto_nota_desvio", "valor": round(d["sent_neto"].std(), 2)}]
    pd.DataFrame(filas).to_csv(AQUI / "metricas_por_nota.csv", index=False, encoding="utf-8")
    print(pd.DataFrame(filas).to_string(index=False))


if __name__ == "__main__":
    main()
