# -*- coding: utf-8 -*-
"""
Dataset de FinBETO con 3 clases (tesis versión 6.0): division train / validacion / test POR NOTICIA.
Fase 3 de CRISP-DM (preparación de los datos).

Entrada: etiquetado_gemma/checkpoint_limpio.jsonl (limpiar_etiquetado.py).

CAMBIO DE LA 6.0: MIXTO pasa a NEU. Decision: se usan EXACTAMENTE las mismas oraciones que la 5.0
(mismo sorteo y mismo tope, hecho con las 4 etiquetas originales) y recien despues se cambia la
etiqueta. Asi lo unico que cambia respecto de la 5.0 es la union de MIXTO con NEU.
Justificacion: las oraciones mixtas ya aportaban 0 al sentimiento neto, igual que las neutras.

Diferencias con 02_preparar_dataset.ipynb (division original):
  * parte del conjunto limpio (sin relleno ni textos repetidos);
  * sortea NOTICIAS, no oraciones: todas las oraciones de una noticia van al mismo conjunto, de modo
    que el test mide al modelo sobre noticias que no vio al entrenar;
  * el sorteo de noticias se estratifica por fuente (cada fuente reparte 80/10/10 sus noticias).
Se mantiene: proporcion 80/10/10, tope por clase (2.400 en total para POS, NEG y NEU, repartido
1.920 / 240 / 240), todas las MIXTO, semilla 42, columnas texto / label / label_id.
El texto es `oracion_limpia` (sin las marcas de relleno del scraping); se guarda tambien el original.

Salidas (salidas/dataset_3clases/):
  train.csv, val.csv, test.csv   texto, label, label_id, label_original, url, fuente, or_idx, texto_original
  class_weights.json             raiz de la frecuencia inversa en train (como 02_preparar_dataset);
                                 en json porque el venv no tiene torch: convertir a tensor al entrenar
  reporte.json                   conteos y verificaciones (sin noticias ni textos compartidos)

Uso:  python preparar_dataset_v2.py
"""

import json
import os
import sys

import numpy as np
import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "etiquetado_gemma", "checkpoint_limpio.jsonl")
SALIDA = os.path.join(AQUI, "salidas", "dataset_3clases")
REF_50 = os.path.join(AQUI, "..", "..", "..", "tesis version 5.0", "Lado Noticias", "sentimiento_finbert", "dataset_v2")
SEED = 42
PROPORCION = {"train": 0.8, "val": 0.1, "test": 0.1}
TOPE_TOTAL = 2400                      # por clase, salvo MIXTO (todas)
LABELS_SELECCION = ["POS", "NEG", "NEU", "MIXTO"]   # el sorteo y el tope se hacen como en la 5.0
UNION = {"MIXTO": "NEU"}                           # 6.0: MIXTO pasa a NEU
LABEL_MAP = {"POS": 0, "NEG": 1, "NEU": 2}


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
        for label in LABELS_SELECCION:
            s = sub[sub["label"] == label]
            if label == "MIXTO":
                partes.append(s)
                continue
            tope = int(round(TOPE_TOTAL * prop))
            if len(s) < tope:
                faltantes[f"{conj}/{label}"] = {"pedidas": tope, "disponibles": int(len(s))}
            partes.append(s.sample(n=min(tope, len(s)), random_state=SEED))
    sel = pd.concat(partes)
    sel = sel.assign(label_original=sel["label"])
    sel["label"] = sel["label"].replace(UNION)
    sel = sel.assign(texto=sel["oracion_limpia"], texto_original=sel["oracion"], label_id=sel["label"].map(LABEL_MAP))

    os.makedirs(SALIDA, exist_ok=True)
    cols = ["texto", "label", "label_id", "label_original", "url", "fuente", "or_idx", "texto_original"]
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
    # controles de la 6.0
    controles = {
        "no_queda_ninguna_MIXTO": all((v["label"] != "MIXTO").all() for v in out.values()),
        "solo_3_clases": all(set(v["label"]) <= set(LABEL_MAP) for v in out.values()),
        "sin_label_id_vacios": all(v["label_id"].notna().all() for v in out.values()),
        "entrada_10855_oraciones": len(df) == 10855,
    }
    if os.path.isdir(REF_50):
        for k, v in out.items():
            r = pd.read_csv(os.path.join(REF_50, f"{k}.csv"), dtype={"or_idx": str})
            controles[f"{k}_mismas_oraciones_que_5.0"] = (
                set(zip(r["url"], r["or_idx"].astype(str))) == set(zip(v["url"], v["or_idx"].astype(str))))
            m = v.merge(r[["url", "or_idx", "label"]].astype({"or_idx": str}), on=["url", "or_idx"], suffixes=("", "_50"))
            controles[f"{k}_etiqueta_original_igual_5.0"] = bool((m["label_original"] == m["label_50"]).all())
    rep["controles"] = controles
    rep["controles_ok"] = f"{sum(controles.values())} de {len(controles)}"
    pd.DataFrame([{"metrica": f"oraciones_{k}", "valor": len(v)} for k, v in out.items()]
                 + [{"metrica": f"{k}_{lab}", "valor": int((v["label"] == lab).sum())} for k, v in out.items() for lab in LABEL_MAP]
                 + [{"metrica": "mixto_pasadas_a_neu", "valor": int(sum((v["label_original"] == "MIXTO").sum() for v in out.values()))},
                    {"metrica": "controles_dataset_ok", "valor": rep["controles_ok"]}]
                 ).to_csv(os.path.join(AQUI, "metricas_dataset.csv"), index=False, encoding="utf-8")
    with open(os.path.join(SALIDA, "reporte.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
