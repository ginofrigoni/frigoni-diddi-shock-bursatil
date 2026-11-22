"""
Acuerdo entre la clasificación de FinBETO de 3 clases (6.0) y la de 4 clases (5.0), oración por oración.

Las oraciones son las mismas (mismo url y or_idx, en el mismo orden). Para comparar, en la 5.0 se
cuenta MIXTO como NEU. Necesita la carpeta de la 5.0 al lado; si no está, no escribe nada.

Salidas: salidas/acuerdo_con_5.csv (tabla cruzada), metricas_acuerdo.csv

Uso:  python acuerdo_con_5.py
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
REF = AQUI.parent.parent.parent / "tesis version 5.0" / "Lado Noticias" / "sentimiento_finbert" / "beto_oraciones_finetuned.csv"
if not REF.exists():
    sys.exit("No está la 5.0 al lado: no se calcula el acuerdo.")
a = pd.read_csv(REF, usecols=["url", "or_idx", "label"], dtype=str)
b = pd.read_csv(AQUI / "salidas" / "beto_oraciones_finetuned.csv", usecols=["url", "or_idx", "label"], dtype=str)
assert (a["url"].values == b["url"].values).all() and (a["or_idx"].values == b["or_idx"].values).all()
t = pd.crosstab(a["label"], b["label"], rownames=["5.0"], colnames=["6.0"])
t.to_csv(AQUI / "salidas" / "acuerdo_con_5.csv", encoding="utf-8")
viejo = a["label"].replace({"MIXTO": "NEU"})
mx = a["label"] == "MIXTO"
filas = [("oraciones_comparadas", len(a)),
         ("acuerdo_pct", round(100 * (viejo == b["label"]).mean(), 1)),
         ("mixto_5_0", int(mx.sum()))]
for c in ("NEU", "NEG", "POS"):
    filas.append((f"mixto_pasan_a_{c}_pct", round(100 * (b.loc[mx, "label"] == c).mean(), 1)))
pd.DataFrame(filas, columns=["metrica", "valor"]).to_csv(AQUI / "metricas_acuerdo.csv", index=False, encoding="utf-8")
print(t); print(pd.DataFrame(filas, columns=["metrica", "valor"]).to_string(index=False))
