"""
Ejemplos del etiquetado de Gemma y de las predicciones de FinBETO — tesis versión 6.0
Fase 3 de CRISP-DM (preparación). Responde al pedido del docente de explicar el etiquetado con ejemplos.

Toma oraciones del TEST (noticias que FinBETO no vio al entrenar), con la etiqueta de Gemma, la razón
que Gemma escribió al etiquetarla y la predicción de FinBETO (semilla 42, el modelo final):
  - un acierto por cada clase original (POS, NEG, NEU y una que era MIXTO y ahora es NEU);
  - dos errores, para mostrar dónde se equivoca.
La selección es al azar con semilla fija, entre oraciones de 70 a 220 caracteres, para que se lean en
una tabla. No se elige "a mano".

Entradas: salidas/entrenamiento/predicciones_test_seed42.csv, etiquetado_gemma/checkpoint_limpio.jsonl
Salida:   salidas/ejemplos_etiquetado.csv

Uso:  python ejemplos_etiquetado.py
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
SEMILLA = 42

pred = pd.read_csv(AQUI / "salidas" / "entrenamiento" / "predicciones_test_seed42.csv", dtype={"or_idx": str})
gem = pd.read_json(AQUI / "etiquetado_gemma" / "checkpoint_limpio.jsonl", lines=True, dtype={"or_idx": str})
d = pred.merge(gem[["url", "or_idx", "razon", "fuente"]], on=["url", "or_idx"], how="left")
d = d[d["texto"].str.len().between(70, 220) & d["razon"].notna()]

casos = [("Acierto", "POS", lambda x: (x["label_original"] == "POS") & (x["pred"] == "POS")),
         ("Acierto", "NEG", lambda x: (x["label_original"] == "NEG") & (x["pred"] == "NEG")),
         ("Acierto", "NEU", lambda x: (x["label_original"] == "NEU") & (x["pred"] == "NEU")),
         ("Acierto (era MIXTO)", "NEU", lambda x: (x["label_original"] == "MIXTO") & (x["pred"] == "NEU")),
         ("Error", "POS", lambda x: (x["label_original"] == "POS") & (x["pred"] == "NEU")),
         ("Error", "NEU", lambda x: (x["label_original"] == "NEU") & (x["pred"] == "NEG"))]
filas = []
for tipo, etiqueta, cond in casos:
    x = d[cond(d)].sample(1, random_state=SEMILLA).iloc[0]
    filas.append({"tipo": tipo, "oracion": x["texto"], "etiqueta_gemma_original": x["label_original"],
                  "etiqueta_3_clases": x["label"], "prediccion_finbeto": x["pred"], "razon_gemma": x["razon"],
                  "fuente": x["fuente"], "url": x["url"]})
E = pd.DataFrame(filas)
E.to_csv(AQUI / "salidas" / "ejemplos_etiquetado.csv", index=False, encoding="utf-8")
for _, x in E.iterrows():
    print(f"[{x['tipo']}] Gemma {x['etiqueta_gemma_original']} → FinBETO {x['prediccion_finbeto']}\n  {x['oracion']}\n  razón: {x['razon_gemma'][:200]}\n")
