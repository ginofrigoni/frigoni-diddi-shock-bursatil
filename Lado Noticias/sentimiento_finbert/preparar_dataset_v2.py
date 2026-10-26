# -*- coding: utf-8 -*-
"""
Fase 2 de la correccion del conjunto etiquetado: nueva division train / validacion / test POR NOTICIA.

Entrada: dataset_etiquetado/checkpoint_limpio.jsonl (limpiar_etiquetado.py).
No reemplaza a dataset/ (la division original, con la que se entreno el modelo actual).

Diferencias con 02_preparar_dataset.ipynb (division original):
  * parte del conjunto limpio (sin relleno ni textos repetidos);
  * sortea NOTICIAS, no oraciones: todas las oraciones de una noticia van al mismo conjunto, de modo
    que el test mide al modelo sobre noticias que no vio al entrenar;
  * el sorteo de noticias se estratifica por fuente (cada fuente reparte 80/10/10 sus noticias).
Se mantiene: proporcion 80/10/10, tope por clase (2.400 en total para POS, NEG y NEU, repartido
1.920 / 240 / 240), todas las MIXTO, semilla 42, columnas texto / label / label_id.
El texto es `oracion_limpia` (sin las marcas de relleno del scraping); se guarda tambien el original.

Salidas (dataset_v2/):
  train.csv, val.csv, test.csv   texto, label, label_id, url, fuente, or_idx, texto_original
  class_weights.json             raiz de la frecuencia inversa en train (como 02_preparar_dataset);
                                 en json porque el venv no tiene torch: convertir a tensor al entrenar
  reporte.json                   conteos y verificaciones (sin noticias ni textos compartidos)

Uso (desde sentimiento_finbert/):  python preparar_dataset_v2.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "dataset_etiquetado", "checkpoint_limpio.jsonl")
SALIDA = os.path.join(AQUI, "dataset_v2")
SEED = 42
PROPORCION = {"train": 0.8, "val": 0.1, "test": 0.1}
TOPE_TOTAL = 2400                      # por clase, salvo MIXTO (todas)
LABEL_MAP = {"POS": 0, "NEG": 1, "NEU": 2, "MIXTO": 3}


def main():
    df = pd.read_json(ENTRADA, lines=True, dtype={"or_idx": str})
    rng = np.random.default_rng(SEED)

    # 1. sorteo de noticias, estratificado por fuente
    asignacion = {}
    for fuente, g in df.groupby("fuente"):
        urls = sorted(g["url"].unique())
        rng.shuffle(urls)
        n = len(urls)
        n_val = int(round(n * PROPORCION["val"]))
        n_test = int(round(n * PROPORCION["test"]))
        for i, u in enumerate(urls):
            asignacion[u] = "test" if i < n_test else ("val" if i < n_test + n_val else "train")
    df["conjunto"] = df["url"].map(asignacion)

    # 2. tope por clase dentro de cada conjunto
    partes = []
    faltantes = {}
    for conj, prop in PROPORCION.items():
        sub = df[df["conjunto"] == conj]
        for label in LABEL_MAP:
            s = sub[sub["label"] == label]
            if label == "MIXTO":
                partes.append(s)
                continue
            tope = int(round(TOPE_TOTAL * prop))
            if len(s) < tope:
                faltantes[f"{conj}/{label}"] = {"pedidas": tope, "disponibles": int(len(s))}
            partes.append(s.sample(n=min(tope, len(s)), random_state=SEED))
    sel = pd.concat(partes)
    sel = sel.assign(texto=sel["oracion_limpia"], texto_original=sel["oracion"], label_id=sel["label"].map(LABEL_MAP))

    os.makedirs(SALIDA, exist_ok=True)
    cols = ["texto", "label", "label_id", "url", "fuente", "or_idx", "texto_original"]
    out = {}
    for conj in PROPORCION:
        x = sel[sel["conjunto"] == conj].sample(frac=1, random_state=SEED)[cols]
        x.to_csv(os.path.join(SALIDA, f"{conj}.csv"), index=False, encoding="utf-8")
        out[conj] = x

    # pesos por clase: raiz de la frecuencia inversa en train
    cont = out["train"]["label"].value_counts()
    total = len(out["train"])
    pesos = {lab: round(float((total / cont[lab]) ** 0.5), 4) for lab in LABEL_MAP}
    with open(os.path.join(SALIDA, "class_weights.json"), "w", encoding="utf-8") as f:
        json.dump({"orden_label_id": list(LABEL_MAP), "pesos": pesos}, f, ensure_ascii=False, indent=2)

    # verificaciones
    urls = {k: set(v["url"]) for k, v in out.items()}
    textos = {k: set(v["texto"]) for k, v in out.items()}
    pares = [("train", "val"), ("train", "test"), ("val", "test")]
    rep = {
        "entrada_filas": int(len(df)),
        "entrada_noticias": int(df["url"].nunique()),
        "noticias_por_conjunto": {k: int(df.loc[df["conjunto"] == k, "url"].nunique()) for k in PROPORCION},
        "oraciones_disponibles_por_conjunto": {k: int((df["conjunto"] == k).sum()) for k in PROPORCION},
        "oraciones_seleccionadas": {k: int(len(v)) for k, v in out.items()},
        "clases_por_conjunto": {k: v["label"].value_counts().to_dict() for k, v in out.items()},
        "fuentes_en_test": out["test"]["fuente"].value_counts().to_dict(),
        "clases_con_menos_de_lo_pedido": faltantes,
        "noticias_compartidas": {f"{a}-{b}": len(urls[a] & urls[b]) for a, b in pares},
        "textos_compartidos": {f"{a}-{b}": len(textos[a] & textos[b]) for a, b in pares},
        "textos_repetidos_dentro": {k: int(v["texto"].duplicated().sum()) for k, v in out.items()},
        "class_weights": pesos,
        "seed": SEED,
    }
    with open(os.path.join(SALIDA, "reporte.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
