# -*- coding: utf-8 -*-
"""
Comparacion FinBETO vs. modelo de referencia sin ajuste a este dominio, en la MISMA tarea y el MISMO test.

Modelo de referencia: finiteautomata/beto-sentiment-analysis (BETO ajustado con ~5.000 tuits del corpus
TASS 2020; 3 clases POS/NEG/NEU), descargado de Hugging Face en baseline_finiteautomata/
(revision 9384c7f339a6d62c9e2e1d686f225f92e3a3353b).

Tarea comun: 3 clases. Se usan solo las oraciones cuya etiqueta (Gemma) es POS, NEG o NEU; las MIXTO se
excluyen, porque el modelo de referencia no puede predecirlas. Igual que 05_evaluacion.ipynb (tesis 2.0).
  - referencia: se clasifica cada oracion (max 128 tokens, como en la 2.0).
  - FinBETO: se toman las matrices de confusion guardadas por la Fase 3 (3 semillas por division); si
    FinBETO predice MIXTO para una oracion POS/NEG/NEU, cuenta como error.

Tests:
  dataset/test.csv     division original (control: la referencia deberia dar el 0,6201 de la 2.0)
  dataset_v2/test.csv  division por noticia (noticias no vistas al entrenar FinBETO)

Salidas: resultados_fase3/comparacion_baseline.json y .csv

Uso (desde sentimiento_finbert/):  python comparar_baseline.py
"""

import glob
import json
import os
import sys

import numpy as np
import pandas as pd
import torch
from sklearn.metrics import accuracy_score, f1_score
from transformers import pipeline

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(AQUI, "baseline_finiteautomata")
OUT = os.path.join(AQUI, "resultados_fase3")
MAPA = {"POS": 0, "NEG": 1, "NEU": 2}        # mismos ids que LABEL_MAP de FinBETO


def f1_3_desde_matriz(cm):
    """F1 macro de 3 clases sobre las filas POS/NEG/NEU; la columna MIXTO cuenta como error."""
    cm = np.array(cm)
    f = []
    for c in range(3):
        tp = cm[c, c]
        fn = cm[c, :].sum() - tp
        fp = cm[:3, c].sum() - tp
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f.append(2 * p * r / (p + r) if p + r else 0.0)
    return float(np.mean(f)), float(np.trace(cm[:3, :3]) / cm[:3, :].sum()), [round(x, 4) for x in f]


def main():
    device = 0 if torch.cuda.is_available() else -1
    clf = pipeline("text-classification", model=REF, tokenizer=REF, device=device, truncation=True, max_length=128)
    filas, detalle = [], {}
    for division in ("dataset", "dataset_v2"):
        te = pd.read_csv(os.path.join(AQUI, division, "test.csv"))
        te = te[te["label"] != "MIXTO"].reset_index(drop=True)
        y = te["label"].map(MAPA).values
        preds = [MAPA.get(r["label"].upper(), 2) for r in clf(te["texto"].tolist(), batch_size=64)]
        p = np.array(preds)
        f1c = f1_score(y, p, average=None, labels=[0, 1, 2])
        ref = {"f1_macro": round(float(f1_score(y, p, average="macro", labels=[0, 1, 2])), 4),
               "accuracy": round(float(accuracy_score(y, p)), 4),
               "f1_POS": round(float(f1c[0]), 4), "f1_NEG": round(float(f1c[1]), 4), "f1_NEU": round(float(f1c[2]), 4),
               "predicciones": {k: int((p == v).sum()) for k, v in MAPA.items()}}
        fb = [f1_3_desde_matriz(json.load(open(f, encoding="utf-8"))["matriz_confusion"])
              for f in sorted(glob.glob(os.path.join(OUT, f"{division}_seed*.json")))]
        fin = {"f1_macro_por_semilla": [round(x[0], 4) for x in fb],
               "f1_macro_media": round(float(np.mean([x[0] for x in fb])), 4),
               "f1_macro_desvio": round(float(np.std([x[0] for x in fb], ddof=1)), 4),
               "accuracy_media": round(float(np.mean([x[1] for x in fb])), 4),
               "f1_por_clase_media": [round(float(np.mean([x[2][i] for x in fb])), 4) for i in range(3)]}
        detalle[division] = {"n_oraciones": int(len(te)), "clases": te["label"].value_counts().to_dict(),
                             "referencia": ref, "finbeto": fin}
        filas.append({"test": division, "n": len(te),
                      "referencia_f1_macro": ref["f1_macro"], "referencia_accuracy": ref["accuracy"],
                      "finbeto_f1_macro": fin["f1_macro_media"], "finbeto_desvio": fin["f1_macro_desvio"],
                      "finbeto_accuracy": fin["accuracy_media"],
                      "ventaja_puntos": round(100 * (fin["f1_macro_media"] - ref["f1_macro"]), 1)})
    json.dump(detalle, open(os.path.join(OUT, "comparacion_baseline.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    R = pd.DataFrame(filas)
    R.to_csv(os.path.join(OUT, "comparacion_baseline.csv"), index=False)
    print(json.dumps(detalle, ensure_ascii=False, indent=2))
    print("\n", R.to_string(index=False))


if __name__ == "__main__":
    main()
