"""
VIX argentino: verificación de la fórmula y escala bajo / medio / alto — tesis versión 6.0
Fase 3 de CRISP-DM (preparación de los datos).

El VIX argentino (vix_arg.csv) lo calculó el lado bursátil con calcular_vix_arg.py y no se vuelve a
calcular. Este script:
  1. verifica la fórmula: σ_t = √252 · desvío(r_{t−19}, …, r_t) · 100, con r_t el retorno diario del
     S&P Merval, reproduce la columna vix_arg;
  2. define la escala pedida por el docente, por TERCILES del VIX en las 244 ruedas de la ventana
     (decisión del 22/11/2026: no se usan los regímenes del HMM): bajo = el tercio de ruedas con menor
     VIX, medio = el tercio del medio, alto = el tercio con mayor VIX;
  3. hace la figura del capítulo.

Entradas: salidas/vix_arg.csv
Salidas: salidas/escala_vix.csv (una fila por rueda con su nivel), salidas/vix_arg.png, metricas.csv

Uso:  python escala_vix.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
SALIDAS = AQUI / "salidas"
INICIO = "2025-05-05"
VENTANA = 20
EVENTOS = {"2025-04-14": "salida del cepo", "2025-09-08": "elecciones bonaerenses", "2025-10-27": "elecciones legislativas"}

v = pd.read_csv(SALIDAS / "vix_arg.csv", parse_dates=["fecha"])
recalc = np.sqrt(252) * v["retorno_diario"].rolling(VENTANA, min_periods=VENTANA).std() * 100
comparables = recalc.notna() & v["vix_arg"].notna()
formula_ok = bool(np.allclose(recalc[comparables], v.loc[comparables, "vix_arg"], atol=1e-6))

w = v[v["fecha"] >= INICIO].copy().reset_index(drop=True)
t1, t2 = w["vix_arg"].quantile([1 / 3, 2 / 3])
w["nivel_vix"] = np.where(w["vix_arg"] <= t1, "bajo", np.where(w["vix_arg"] <= t2, "medio", "alto"))
w.assign(fecha=w["fecha"].dt.strftime("%Y-%m-%d"))[["fecha", "vix_arg", "nivel_vix"]].round(4).to_csv(
    SALIDAS / "escala_vix.csv", index=False, encoding="utf-8")

res = [("formula_reproduce_vix", "sí" if formula_ok else "no"),
       ("ruedas_ventana", len(w)), ("vix_media", round(w["vix_arg"].mean(), 1)),
       ("vix_mediana", round(w["vix_arg"].median(), 1)),
       ("vix_min", round(w["vix_arg"].min(), 1)), ("vix_min_fecha", w.loc[w["vix_arg"].idxmin(), "fecha"].strftime("%d/%m/%Y")),
       ("vix_max", round(w["vix_arg"].max(), 1)), ("vix_max_fecha", w.loc[w["vix_arg"].idxmax(), "fecha"].strftime("%d/%m/%Y")),
       ("tercil_1", round(t1, 1)), ("tercil_2", round(t2, 1))]
for n in ("bajo", "medio", "alto"):
    s = w.loc[w["nivel_vix"] == n, "vix_arg"]
    res += [(f"ruedas_{n}", len(s)), (f"vix_media_{n}", round(s.mean(), 1))]
test = w[w["fecha"] >= "2026-02-01"]
for n in ("bajo", "medio", "alto"):
    res.append((f"ruedas_test_{n}", int((test["nivel_vix"] == n).sum())))
res.append(("vix_media_test", round(test["vix_arg"].mean(), 1)))
res.append(("vix_media_entrenamiento", round(w.loc[w["fecha"] < "2026-02-01", "vix_arg"].mean(), 1)))
pd.DataFrame(res, columns=["metrica", "valor"]).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.8), sharex=True, gridspec_kw={"height_ratios": [1, 1.25]})
a1.plot(v["fecha"], v["merv_cierre"] / 1e6, color="#13202F", lw=1.2)
a1.set_ylabel("S&P Merval (millones de pesos)")
a1.set_title("S&P Merval y VIX argentino", loc="left", fontsize=12, fontweight="bold")
a2.axhspan(0, t1, color="#2E8B57", alpha=0.10, lw=0)
a2.axhspan(t1, t2, color="#F2A900", alpha=0.12, lw=0)
a2.axhspan(t2, max(100, v["vix_arg"].max() + 5), color="#D7301F", alpha=0.10, lw=0)
a2.plot(v["fecha"], v["vix_arg"], color="#B5700F", lw=1.3)
a2.text(v["fecha"].iloc[-1], t1 / 2, " bajo", va="center", fontsize=9, color="#2E8B57")
a2.text(v["fecha"].iloc[-1], (t1 + t2) / 2, " medio", va="center", fontsize=9, color="#B5700F")
a2.text(v["fecha"].iloc[-1], t2 + 8, " alto", va="center", fontsize=9, color="#D7301F")
a2.axvspan(pd.Timestamp("2026-02-01"), v["fecha"].iloc[-1], color="#999", alpha=0.12, lw=0)
a2.text(pd.Timestamp("2026-03-15"), 92, "test", ha="center", fontsize=9, color="#555")
a2.set_ylabel("VIX argentino (%)"); a2.set_ylim(0, max(100, v["vix_arg"].max() + 5))
for f, txt in EVENTOS.items():
    for ax in (a1, a2):
        ax.axvline(pd.Timestamp(f), color="#C26A00", lw=0.9, ls=":")
    a1.text(pd.Timestamp(f), a1.get_ylim()[1], " " + txt, fontsize=8, color="#C26A00", va="top", rotation=90)
a2.axvline(pd.Timestamp(INICIO), color="#555", lw=0.8, ls="--")
for ax in (a1, a2):
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(SALIDAS / "vix_arg.png", dpi=160, facecolor="white")
print(pd.DataFrame(res, columns=["metrica", "valor"]).to_string(index=False))
