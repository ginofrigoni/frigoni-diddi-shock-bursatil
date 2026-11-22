"""
Noticias → precio — tesis versión 6.0. Fase 4 de CRISP-DM (modelado).

Pregunta: ¿las noticias ayudan a predecir si la acción sube en la rueda siguiente?

Unidad: una acción en una rueda (17 empresas con cobertura). Objetivo: sube = 1 si el retorno de la
acción en la rueda t+1 es > 0 (un retorno de exactamente 0 cuenta como "no sube").

  Modelo A (solo mercado): retornos de la acción en t, t−1, t−2, t−3 y t−4; volumen anormal en t; VIX en t.
  Modelo B (A + noticias): A + sentimiento inesperado en t + sentimiento propio de la empresa en t +
                           hubo_noticia en t.

Todas las variables de la rueda t se conocen al cierre de t. Diseño, algoritmos, corte y bootstrap:
4_modelado/README.md (fijado antes de ver resultados) y 4_modelado/modelado_comun.py.

Entrada:  3_preparacion_de_los_datos/dataset_unificado/salidas/dataset_panel.csv
Salidas (salidas/): metricas_test.csv, delta_auc.csv, hiperparametros.csv, importancias.csv,
                    predicciones_test.csv, verificaciones.csv, noticias_a_precio.png;  metricas.csv

Uso:  python noticias_a_precio.py
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

d = pd.read_csv(RAIZ / "3_preparacion_de_los_datos" / "dataset_unificado" / "salidas" / "dataset_panel.csv")
d = d.sort_values(["ticker", "rueda"]).reset_index(drop=True)
g = d.groupby("ticker")
for k in range(REZAGOS):
    d[f"retorno_t{k}"] = g["retorno"].shift(k)
d["retorno_siguiente"] = g["retorno"].shift(-1)
d["sube"] = (d["retorno_siguiente"] > 0).astype(int)
VARS_A = [f"retorno_t{k}" for k in range(REZAGOS)] + ["vol_anormal", "vix_arg"]
VARS_NOTICIAS = ["sentimiento_inesperado", "sentimiento_propio", "hubo_noticia"]
VARS_B = VARS_A + VARS_NOTICIAS
completas = d[VARS_B + ["retorno_siguiente"]].notna().all(axis=1)
datos = d[completas].reset_index(drop=True)

metr, delta, hiper, imps, preds, info = mc.correr_comparacion(datos, "sube", VARS_A, VARS_B)
metr.round(4).to_csv(SALIDAS / "metricas_test.csv", index=False, encoding="utf-8")
delta.round(4).to_csv(SALIDAS / "delta_auc.csv", index=False, encoding="utf-8")
hiper.round(4).to_csv(SALIDAS / "hiperparametros.csv", index=False, encoding="utf-8")
imps.round(4).to_csv(SALIDAS / "importancias.csv", index=False, encoding="utf-8")
# redondeo a 10 decimales: el random forest suma en paralelo y el último decimal varía entre corridas (~1e-16)
preds.round(10).to_csv(SALIDAS / "predicciones_test.csv", index=False, encoding="utf-8")

# ── Controles ────────────────────────────────────────────────────────────
alt = d.copy(); alt.loc[alt.index[100], "retorno"] += 1   # cambiar un retorno no cambia rezagos de filas anteriores
ga = alt.groupby("ticker")
controles = [
    ("Los rezagos usan solo ruedas anteriores de la misma acción",
     all(np.allclose(ga["retorno"].shift(k).iloc[:100].fillna(0), d[f"retorno_t{k}"].iloc[:100].fillna(0)) for k in range(REZAGOS))),
    ("El objetivo de cada fila es el retorno de la rueda siguiente de la misma acción",
     bool((datos.groupby("ticker")["rueda"].shift(-1).dropna() > datos.groupby("ticker")["rueda"].shift(0)[datos.groupby("ticker")["rueda"].shift(-1).notna()]).all())),
    ("Entrenamiento y test no comparten ruedas", info["ultima_rueda_entrenamiento"] < info["primera_rueda_test"]),
    ("El test empieza en febrero de 2026", info["primera_rueda_test"] >= mc.CORTE_TEST),
    ("17 empresas en entrenamiento y en test",
     datos.loc[datos["rueda"] < mc.CORTE_TEST, "ticker"].nunique() == 17 and datos.loc[datos["rueda"] >= mc.CORTE_TEST, "ticker"].nunique() == 17),
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
res.append({"metrica": "noticias_aportan_segun_criterio", "valor": "sí" if dl["ic95_inf"] > 0 else "no"})
res.append({"metrica": "controles_ok", "valor": f"{int(verif['pasa'].sum())} de {len(verif)}"})
pd.DataFrame(res).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
fig, axs = plt.subplots(1, 3, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1.2, 1, 1]})
y = preds["y"].to_numpy()
for nombre, color in (("A", "#5C6B7A"), ("B", "#1F6FA3")):
    fpr, tpr, _ = roc_curve(y, preds[f"logistica_{nombre}"])
    auc = metr.query("algoritmo == 'logistica' and modelo == @nombre")["auc"].iloc[0]
    axs[0].plot(fpr, tpr, color=color, lw=1.8, label=f"{'A · solo mercado' if nombre == 'A' else 'B · mercado + noticias'} (AUC {auc:.3f})")
axs[0].plot([0, 1], [0, 1], color="#999", ls="--", lw=1)
axs[0].set_xlabel("Falsos positivos"); axs[0].set_ylabel("Verdaderos positivos")
axs[0].set_title("Curva ROC en el test (regresión logística)", loc="left", fontsize=11, fontweight="bold")
axs[0].legend(loc="lower right", frameon=False, fontsize=8.5)
for ax, nombre in zip(axs[1:], ("A", "B")):
    x = metr.query("algoritmo == 'logistica' and modelo == @nombre").iloc[0]
    mat = np.array([[x["tn"], x["fp"]], [x["fn"], x["tp"]]])
    ax.imshow(mat, cmap="Blues")
    for i in range(2):
        for j in range(2):
            ax.text(j, i, int(mat[i, j]), ha="center", va="center", fontsize=12,
                    color="white" if mat[i, j] > mat.max() / 2 else "#13202F")
    ax.set_xticks([0, 1], ["predice no sube", "predice sube"]); ax.set_yticks([0, 1], ["no subió", "subió"])
    ax.set_title(f"Matriz de confusión · modelo {nombre}", loc="left", fontsize=11, fontweight="bold")
fig.tight_layout()
fig.savefig(SALIDAS / "noticias_a_precio.png", dpi=160, facecolor="white")

print(pd.Series(info).to_string()); print()
print(metr[["algoritmo", "modelo", "auc", "balanced_accuracy", "f1", "accuracy", "pct_clase_1_predicha"]].round(4).to_string(index=False)); print()
print(delta.round(4).to_string(index=False)); print()
print(hiper.round(4).to_string(index=False)); print()
print(verif.to_string(index=False))
