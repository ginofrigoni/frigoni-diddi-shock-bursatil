# -*- coding: utf-8 -*-
"""
FinBETO de 3 clases contra el modelo de referencia, en la MISMA tarea y el MISMO test (tesis versión 6.0).
Fase 3 de CRISP-DM (preparación): evaluación del modelo que construye la variable de sentimiento.

Modelo de referencia: finiteautomata/beto-sentiment-analysis (BETO ajustado con ~5.000 tuits del corpus
TASS 2020; 3 clases POS/NEG/NEU), en modelos/baseline_finiteautomata/
(revision 9384c7f339a6d62c9e2e1d686f225f92e3a3353b).

Con 3 clases los dos modelos resuelven exactamente la misma tarea: ya no hace falta contar como error
una prediccion MIXTO. Se informan dos tests:
  completo     las 786 oraciones del test (las que eran MIXTO cuentan como NEU)
  como_la_5.0  solo las oraciones que ya eran POS, NEG o NEU (mismo subconjunto que la 5.0: 662)
FinBETO: media y desvio de las 3 semillas (matrices guardadas por fase3_reentrenar_para_medir.py).

Salidas: salidas/entrenamiento/comparacion_baseline.json y .csv

Uso:  python comparar_baseline.py
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score
from transformers import pipeline

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(AQUI, "modelos", "baseline_finiteautomata")
TEST = os.path.join(AQUI, "salidas", "dataset_3clases", "test.csv")
OUT = os.path.join(AQUI, "salidas", "entrenamiento")
MAPA = {"POS": 0, "NEG": 1, "NEU": 2}        # mismos ids que LABEL_MAP de FinBETO
CLASES = [0, 1, 2]


def resumen(y, p):
    f1c = f1_score(y, p, average=None, labels=CLASES)
    return {"f1_macro": round(float(f1_score(y, p, average="macro", labels=CLASES)), 4),
            "accuracy": round(float(accuracy_score(y, p)), 4),
            "f1_POS": round(float(f1c[0]), 4), "f1_NEG": round(float(f1c[1]), 4), "f1_NEU": round(float(f1c[2]), 4),
            "predicciones": {k: int((p == v).sum()) for k, v in MAPA.items()},
            "matriz_confusion": confusion_matrix(y, p, labels=CLASES).tolist()}


def main():
    device = 0 if torch.cuda.is_available() else -1
    clf = pipeline("text-classification", model=REF, tokenizer=REF, device=device, truncation=True, max_length=128)
    te = pd.read_csv(TEST)
    y_all = te["label"].map(MAPA).values
    p_ref_all = np.array([MAPA.get(r["label"].upper(), 2) for r in clf(te["texto"].tolist(), batch_size=64)])

    # FinBETO: en el test completo, media de las 3 semillas; en el subconjunto, las predicciones guardadas
    # de la semilla 42 (la del modelo final), porque de las otras semillas solo quedan las matrices
    semillas = {}
    for f in sorted(glob.glob(os.path.join(OUT, "seed*.json"))):
        r = json.load(open(f, encoding="utf-8"))
        semillas[r["seed"]] = r
    pred42 = pd.read_csv(os.path.join(OUT, "predicciones_test_seed42.csv"))

    filas, detalle = [], {}
    for nombre, mascara in (("completo", np.ones(len(te), bool)),
                            ("como_la_5.0", (te["label_original"] != "MIXTO").values)):
        y, p_ref = y_all[mascara], p_ref_all[mascara]
        ref = resumen(y, p_ref)
        if nombre == "completo":
            f1s = [r["test"]["f1_macro"] for r in semillas.values()]
            accs = [r["test"]["accuracy"] for r in semillas.values()]
        else:
            f1s = [None]; accs = [None]
        p42 = pred42.loc[mascara, "pred"].map(MAPA).values
        fin42 = resumen(y, p42)
        fin = {"f1_macro_por_semilla": {int(s): r["test"]["f1_macro"] for s, r in semillas.items()} if nombre == "completo" else None,
               "f1_macro_media": round(float(np.mean(f1s)), 4) if f1s[0] is not None else fin42["f1_macro"],
               "f1_macro_desvio": round(float(np.std(f1s, ddof=1)), 4) if f1s[0] is not None and len(f1s) > 1 else None,
               "accuracy_media": round(float(np.mean(accs)), 4) if accs[0] is not None else fin42["accuracy"],
               "semilla_42": fin42}
        detalle[nombre] = {"n_oraciones": int(mascara.sum()), "clases": te.loc[mascara, "label"].value_counts().to_dict(),
                           "referencia": ref, "finbeto": fin}
        filas.append({"test": nombre, "n": int(mascara.sum()),
                      "referencia_f1_macro": ref["f1_macro"], "referencia_accuracy": ref["accuracy"],
                      "referencia_dice_neutro": ref["predicciones"]["NEU"],
                      "finbeto_f1_macro": fin["f1_macro_media"], "finbeto_desvio": fin["f1_macro_desvio"],
                      "finbeto_accuracy": fin["accuracy_media"],
                      "ventaja_puntos": round(100 * (fin["f1_macro_media"] - ref["f1_macro"]), 1),
                      "nota": "media de 3 semillas" if nombre == "completo" else "semilla 42 (la del modelo final)"})
    json.dump(detalle, open(os.path.join(OUT, "comparacion_baseline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    R = pd.DataFrame(filas)
    R.to_csv(os.path.join(OUT, "comparacion_baseline.csv"), index=False)
    print(R.to_string(index=False))


if __name__ == "__main__":
    main()
