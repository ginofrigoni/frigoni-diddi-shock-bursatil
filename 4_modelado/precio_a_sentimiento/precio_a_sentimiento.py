"""
Precio → sentimiento — tesis versión 6.0. Fase 4 de CRISP-DM (modelado).

Pregunta: ¿el mercado ayuda a predecir el sentimiento de las noticias de la rueda siguiente?

Unidad: una rueda (dataset de mercado). Objetivo (decisión D9): 1 si el sentimiento inesperado de la
rueda t+1 es > 0 (las noticias de mañana son más positivas que lo habitual).

  Modelo A (solo noticias): sentimiento inesperado en t, t−1, t−2, t−3 y t−4.
  Modelo B (A + mercado):   A + retorno del Merval en t, t−1, t−2, t−3 y t−4 + VIX en t.

Cuándo se conoce cada dato: el retorno del Merval de t se conoce al cierre de t (17:00). La rueda t+1
junta las notas publicadas desde las 17:00 de t hasta las 17:00 de t+1, así que una nota que comenta el
cierre de t cae en t+1. Las variables de t no usan nada de t+1.

Diseño, algoritmos, corte y bootstrap: 4_modelado/README.md (fijado antes de ver resultados).

Entrada:  3_preparacion_de_los_datos/dataset_unificado/salidas/dataset_mercado.csv
Salidas (salidas/): metricas_test.csv, delta_auc.csv, hiperparametros.csv, importancias.csv,
                    predicciones_test.csv, verificaciones.csv, precio_a_sentimiento.png;  metricas.csv

Uso:  python precio_a_sentimiento.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import modelado_comun as mc   # noqa: E402

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = AQUI.parent.parent
SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)
REZAGOS = 5

d = pd.read_csv(RAIZ / "3_preparacion_de_los_datos" / "dataset_unificado" / "salidas" / "dataset_mercado.csv")
d = d.sort_values("rueda").reset_index(drop=True)
for k in range(REZAGOS):
    d[f"inesperado_t{k}"] = d["sentimiento_inesperado"].shift(k)
    d[f"ret_merval_t{k}"] = d["ret_merval"].shift(k)
d["inesperado_siguiente"] = d["sentimiento_inesperado"].shift(-1)
d["sentimiento_sube"] = (d["inesperado_siguiente"] > 0).astype(int)
VARS_A = [f"inesperado_t{k}" for k in range(REZAGOS)]
VARS_MERCADO = [f"ret_merval_t{k}" for k in range(REZAGOS)] + ["vix_arg"]
VARS_B = VARS_A + VARS_MERCADO
completas = d[VARS_B + ["inesperado_siguiente"]].notna().all(axis=1)
datos = d[completas].reset_index(drop=True)

metr, delta, hiper, imps, preds, info = mc.correr_comparacion(datos, "sentimiento_sube", VARS_A, VARS_B)
metr.round(4).to_csv(SALIDAS / "metricas_test.csv", index=False, encoding="utf-8")
delta.round(4).to_csv(SALIDAS / "delta_auc.csv", index=False, encoding="utf-8")
hiper.round(4).to_csv(SALIDAS / "hiperparametros.csv", index=False, encoding="utf-8")
imps.round(4).to_csv(SALIDAS / "importancias.csv", index=False, encoding="utf-8")
# redondeo a 10 decimales: el random forest suma en paralelo y el último decimal varía entre corridas (~1e-16)
preds.round(10).to_csv(SALIDAS / "predicciones_test.csv", index=False, encoding="utf-8")

# ── Controles ────────────────────────────────────────────────────────────
alt = d["ret_merval"].copy(); alt.iloc[100] += 1
controles = [
    ("Los rezagos usan solo ruedas anteriores",
     all(np.allclose(alt.shift(k).iloc[:100].fillna(0), d[f"ret_merval_t{k}"].iloc[:100].fillna(0)) for k in range(REZAGOS))),
    ("El objetivo es el sentimiento inesperado de la rueda siguiente",
     bool(np.allclose(datos["inesperado_siguiente"].iloc[:-1].to_numpy(), datos["inesperado_t0"].iloc[1:].to_numpy()))),
    ("Entrenamiento y test no comparten ruedas", info["ultima_rueda_entrenamiento"] < info["primera_rueda_test"]),
    ("El test empieza en febrero de 2026", info["primera_rueda_test"] >= mc.CORTE_TEST),
    ("Sin faltantes en las variables de los modelos", bool(datos[VARS_B].notna().all().all())),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(SALIDAS / "verificaciones.csv", index=False, encoding="utf-8")

# ── Métricas para el informe ─────────────────────────────────────────────
res = [{"metrica": k, "valor": v} for k, v in info.items()]
for _, x in metr.iterrows():
    for c in ("auc", "balanced_accuracy", "f1", "accuracy"):
        res.append({"metrica": f"{x['algoritmo']}_{x['modelo']}_{c}".replace(" ", "_"), "valor": round(x[c], 4)})
for _, x in delta.iterrows():
    for c in ("delta_auc", "ic95_inf", "ic95_sup", "p_unilateral"):
        res.append({"metrica": f"{x['algoritmo']}_{c}", "valor": round(x[c], 4)})
dl = delta.set_index("algoritmo").loc["logistica"]
res.append({"metrica": "mercado_aporta_segun_criterio", "valor": "sí" if dl["ic95_inf"] > 0 else "no"})
res.append({"metrica": "controles_ok", "valor": f"{int(verif['pasa'].sum())} de {len(verif)}"})
pd.DataFrame(res).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
fig, axs = plt.subplots(1, 3, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1.2, 1, 1]})
y = preds["y"].to_numpy()
for nombre, color in (("A", "#5C6B7A"), ("B", "#B5700F")):
    fpr, tpr, _ = roc_curve(y, preds[f"logistica_{nombre}"])
    auc = metr.query("algoritmo == 'logistica' and modelo == @nombre")["auc"].iloc[0]
    axs[0].plot(fpr, tpr, color=color, lw=1.8, label=f"{'A · solo noticias' if nombre == 'A' else 'B · noticias + mercado'} (AUC {auc:.3f})")
axs[0].plot([0, 1], [0, 1], color="#999", ls="--", lw=1)
axs[0].set_xlabel("Falsos positivos"); axs[0].set_ylabel("Verdaderos positivos")
axs[0].set_title("Curva ROC en el test (regresión logística)", loc="left", fontsize=11, fontweight="bold")
axs[0].legend(loc="lower right", frameon=False, fontsize=8.5)
for ax, nombre in zip(axs[1:], ("A", "B")):
    x = metr.query("algoritmo == 'logistica' and modelo == @nombre").iloc[0]
    mat = np.array([[x["tn"], x["fp"]], [x["fn"], x["tp"]]])
    ax.imshow(mat, cmap="Oranges")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, int(mat[i, j]), ha="center", va="center", fontsize=12,
                    color="white" if mat[i, j] > mat.max() / 2 else "#13202F")
    ax.set_xticks([0, 1], ["predice ≤ habitual", "predice > habitual"]); ax.set_yticks([0, 1], ["fue ≤ habitual", "fue > habitual"])
    ax.set_title(f"Matriz de confusión · modelo {nombre}", loc="left", fontsize=11, fontweight="bold")
fig.tight_layout()
fig.savefig(SALIDAS / "precio_a_sentimiento.png", dpi=160, facecolor="white")

print(pd.Series(info).to_string()); print()
print(metr[["algoritmo", "modelo", "auc", "balanced_accuracy", "f1", "accuracy", "pct_clase_1_predicha"]].round(4).to_string(index=False)); print()
print(delta.round(4).to_string(index=False)); print()
print(hiper.round(4).to_string(index=False)); print()
print(imps[imps["algoritmo"] == "logistica"].round(3).to_string(index=False)); print()
print(verif.to_string(index=False))
