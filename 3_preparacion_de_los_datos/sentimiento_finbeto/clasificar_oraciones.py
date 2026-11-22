# -*- coding: utf-8 -*-
"""
Clasifica con FinBETO de 3 clases todas las oraciones del corpus (tesis versión 6.0).
Fase 3 de CRISP-DM (preparación): construye la variable de sentimiento de cada oración.

Las oraciones son EXACTAMENTE las mismas que en la 5.0 (misma división en oraciones, mismo or_idx),
para que el cruce con las entidades (ner_oraciones.csv, que usa esos mismos índices) siga valiendo.
Solo cambia la etiqueta: la pone el modelo nuevo.

Misma inferencia que 06_inferencia.ipynb (2.0): máximo 128 tokens, softmax, etiqueta = argmax,
score = probabilidad de esa etiqueta.

Entrada:
  datos/oraciones_corpus.csv            fuente, url, fecha, autor, titulo, or_idx, oracion
  modelos/beto_finetuned_3clases/       el modelo guardado por fase3_reentrenar_para_medir.py
Salida:
  salidas/beto_oraciones_finetuned.csv  las mismas columnas + label, score (no va a GitHub: > 100 MB)
  metricas_clasificacion.csv

Uso:  python clasificar_oraciones.py [--batch-size 256]
"""

import argparse
import csv
import os
import sys
import time

import numpy as np
import pandas as pd
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
ENTRADA = os.path.join(AQUI, "datos", "oraciones_corpus.csv")
MODELO = os.path.join(AQUI, "modelos", "beto_finetuned_3clases")
SALIDA = os.path.join(AQUI, "salidas", "beto_oraciones_finetuned.csv")
MAX_LEN = 128
CAMPOS = ["fuente", "url", "fecha", "autor", "titulo", "or_idx", "oracion", "label", "score"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch-size", type=int, default=256)
    a = ap.parse_args()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODELO)
    model = AutoModelForSequenceClassification.from_pretrained(MODELO).to(device).eval()
    if device == "cuda":
        model = model.half()
    id2label = {int(k): v for k, v in model.config.id2label.items()}
    assert set(id2label.values()) == {"POS", "NEG", "NEU"}, id2label

    df = pd.read_csv(ENTRADA, dtype=str, keep_default_na=False)
    textos = df["oracion"].tolist()
    # ordenar por largo acelera mucho el relleno por lote; despues se vuelve al orden original
    orden = np.argsort([len(t) for t in textos])
    labels = np.empty(len(textos), dtype=object)
    scores = np.empty(len(textos), dtype=float)
    t0 = time.time()
    with torch.no_grad():
        for i in range(0, len(orden), a.batch_size):
            idx = orden[i:i + a.batch_size]
            enc = tok([textos[j] for j in idx], truncation=True, max_length=MAX_LEN, padding=True, return_tensors="pt").to(device)
            probs = torch.softmax(model(**enc).logits.float(), dim=-1).cpu().numpy()
            pred = probs.argmax(-1)
            labels[idx] = [id2label[p] for p in pred]
            scores[idx] = probs[np.arange(len(pred)), pred]
            if (i // a.batch_size) % 200 == 0:
                print(f"  {i + len(idx):>7}/{len(orden)}  ({time.time() - t0:.0f} s)", flush=True)
    df["label"] = labels
    df["score"] = np.round(scores, 4)
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    df[CAMPOS].to_csv(SALIDA, index=False, encoding="utf-8", quoting=csv.QUOTE_MINIMAL)

    v = df["label"].value_counts()
    filas = [{"metrica": "oraciones_clasificadas", "valor": len(df)},
             {"metrica": "noticias", "valor": df["url"].nunique()},
             *({"metrica": f"oraciones_{k}", "valor": int(v.get(k, 0))} for k in ("POS", "NEG", "NEU")),
             *({"metrica": f"pct_{k}", "valor": round(100 * v.get(k, 0) / len(df), 1)} for k in ("POS", "NEG", "NEU")),
             {"metrica": "minutos", "valor": round((time.time() - t0) / 60, 1)}]
    pd.DataFrame(filas).to_csv(os.path.join(AQUI, "metricas_clasificacion.csv"), index=False, encoding="utf-8")
    print(pd.DataFrame(filas).to_string(index=False))


if __name__ == "__main__":
    main()
