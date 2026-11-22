"""
Anexo · verificación clásica con VAR y Granger — tesis versión 6.0
Fase 5 de CRISP-DM (evaluación).

En la 6.0 la prueba de la hipótesis es el modelo predictivo (4_modelado). Esto es una verificación con
la econometría clásica de la 5.0, ya con FinBETO de 3 clases: ¿los dos métodos dicen lo mismo?

Diferencias con la 5.0 (U6), siguiendo el feedback del docente:
  - se usan solo las variables del modelo predictivo: sentimiento inesperado, sentimiento propio,
    retorno y volumen anormal (no la atención ni el monto operado);
  - solo las 17 empresas con cobertura, más el nivel mercado (no los sectores ni las 47 empresas);
  - sin la corrección de Benjamini-Hochberg ni las pruebas de control adicionales: se informa el p y,
    en el nivel empresa, cuántas empresas dan p < 0,05 contra las que se esperan por azar (5 %).

Niveles (las 224 ruedas con sentimiento inesperado, del 02/06/2025 al 30/04/2026):
  mercado  VAR(sentimiento inesperado, retorno del Merval)
  empresa  para cada una de las 17: VAR(sentimiento inesperado, sentimiento propio, retorno, volumen anormal)
Rezagos: elegidos por AIC entre 1 y 5. Granger: test F de que los rezagos de la causa no aportan para
predecir el efecto. Impulso-respuesta del mercado ortogonalizado, con las noticias primero.

Entradas: dataset_unificado/salidas/dataset_mercado.csv y dataset_panel.csv
Salidas: salidas/granger_resultados.csv, rezagos_var.csv, irf_mercado.csv, var_granger.png; metricas_var_granger.csv

Uso:  python var_granger.py
"""

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")

AQUI = Path(__file__).resolve().parent
DATASET = AQUI.parent.parent / "3_preparacion_de_los_datos" / "dataset_unificado" / "salidas"
SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)
MAX_REZAGOS, ALFA, HORIZONTE = 5, 0.05, 10
NOMBRE = {"sentimiento_inesperado": "sentimiento inesperado", "sentimiento_propio": "sentimiento propio",
          "ret_merval": "retorno", "retorno": "retorno", "vol_anormal": "volumen"}
NOTICIAS = {"sentimiento_inesperado", "sentimiento_propio"}

mercado = pd.read_csv(DATASET / "dataset_mercado.csv").dropna(subset=["sentimiento_inesperado"]).reset_index(drop=True)
panel = pd.read_csv(DATASET / "dataset_panel.csv")
panel = panel[panel["rueda"].isin(mercado["rueda"])].sort_values(["ticker", "rueda"])

filas, rezagos = [], []


def correr(nivel, unidad, datos, pares):
    modelo = VAR(datos)
    k = int(min(max(modelo.select_order(maxlags=MAX_REZAGOS).aic, 1), MAX_REZAGOS))
    res = modelo.fit(k)
    rezagos.append({"nivel": nivel, "unidad": unidad, "rezagos": k, "estable": bool(res.is_stable()), "n": int(res.nobs)})
    for causa, efecto in pares:
        t = res.test_causality(efecto, [causa], kind="f")
        suma = sum(res.params.loc[f"L{l}.{causa}", efecto] for l in range(1, k + 1))
        filas.append({"nivel": nivel, "unidad": unidad, "prueba": f"{NOMBRE[causa]} → {NOMBRE[efecto]}",
                      "direccion": "noticias → mercado" if causa in NOTICIAS else "mercado → noticias",
                      "rezagos": k, "F": round(float(t.test_statistic), 4), "p": float(t.pvalue),
                      "efecto_desvios": round(suma * datos[causa].std() / datos[efecto].std(), 4)})
    return res


# ── Mercado ──────────────────────────────────────────────────────────────
VARS_M = ["sentimiento_inesperado", "ret_merval"]
res_m = correr("mercado", "Merval", mercado[VARS_M],
               [("sentimiento_inesperado", "ret_merval"), ("ret_merval", "sentimiento_inesperado")])
irf = res_m.irf(HORIZONTE)
se = irf.stderr(orth=True)
irf_df = pd.DataFrame([{"impulso": imp, "respuesta": resp, "horizonte": h, "irf": irf.orth_irfs[h, j, i],
                        "banda_baja": irf.orth_irfs[h, j, i] - 1.96 * se[h, j, i], "banda_alta": irf.orth_irfs[h, j, i] + 1.96 * se[h, j, i]}
                       for i, imp in enumerate(VARS_M) for j, resp in enumerate(VARS_M) for h in range(HORIZONTE + 1)])
irf_df.to_csv(SALIDAS / "irf_mercado.csv", index=False, encoding="utf-8")

# ── Empresas (17) ────────────────────────────────────────────────────────
pares_e = [("sentimiento_inesperado", "retorno"), ("retorno", "sentimiento_inesperado"),
           ("sentimiento_propio", "retorno"), ("retorno", "sentimiento_propio")]
for t, g in panel.groupby("ticker"):
    correr("empresa", t, g[["sentimiento_inesperado", "sentimiento_propio", "retorno", "vol_anormal"]].reset_index(drop=True), pares_e)

gr = pd.DataFrame(filas)
gr["p_menor_005"] = gr["p"] < ALFA
gr.to_csv(SALIDAS / "granger_resultados.csv", index=False, encoding="utf-8")
rz = pd.DataFrame(rezagos)
rz.to_csv(SALIDAS / "rezagos_var.csv", index=False, encoding="utf-8")

# ── Métricas ─────────────────────────────────────────────────────────────
r = [{"metrica": "ruedas", "valor": len(mercado), "detalle": f"{mercado['rueda'].iloc[0]} a {mercado['rueda'].iloc[-1]}"},
     {"metrica": "modelos_var", "valor": len(rz)}, {"metrica": "tests_granger", "valor": len(gr)},
     {"metrica": "var_estables", "valor": f"{int(rz['estable'].sum())} de {len(rz)}"},
     {"metrica": "rezagos_mercado", "valor": int(rz.loc[rz["nivel"] == "mercado", "rezagos"].iloc[0])}]
for _, x in gr[gr["nivel"] == "mercado"].iterrows():
    r.append({"metrica": f"mercado {x['prueba']}: p", "valor": float(f"{x['p']:.3g}"), "detalle": f"F={x['F']}; efecto {x['efecto_desvios']} desvíos"})
emp = gr[gr["nivel"] == "empresa"]
for prueba, g in emp.groupby("prueba", sort=False):
    sig = g[g["p_menor_005"]]
    r.append({"metrica": f"empresas {prueba}: p < 0,05", "valor": f"{len(sig)} de {len(g)}",
              "detalle": f"por azar se esperan {ALFA * len(g):.1f}; positivas {int((sig['efecto_desvios'] > 0).sum())}"})
for imp, resp in (("ret_merval", "sentimiento_inesperado"), ("sentimiento_inesperado", "ret_merval")):
    for h in (0, 1, 2):
        x = irf_df.query("impulso == @imp and respuesta == @resp and horizonte == @h").iloc[0]
        r.append({"metrica": f"irf {NOMBRE[imp]} → {NOMBRE[resp]} h{h}", "valor": round(x["irf"], 3),
                  "detalle": f"banda {x['banda_baja']:.3f} a {x['banda_alta']:.3f}"})
pd.DataFrame(r).to_csv(AQUI / "metricas_var_granger.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
fig, axs = plt.subplots(1, 3, figsize=(14, 4.2), gridspec_kw={"width_ratios": [1, 1, 1.2]})
for ax, (imp, resp, tit) in zip(axs[:2], (("ret_merval", "sentimiento_inesperado", "Retorno del Merval → sentimiento"),
                                          ("sentimiento_inesperado", "ret_merval", "Sentimiento → retorno del Merval"))):
    s = irf_df.query("impulso == @imp and respuesta == @resp")
    ax.fill_between(s["horizonte"], s["banda_baja"], s["banda_alta"], color="#7CC3EE", alpha=0.35)
    ax.plot(s["horizonte"], s["irf"], color="#1F6FA3", lw=1.8, marker="o", ms=3)
    ax.axhline(0, color="#999", lw=0.8)
    ax.set_title(tit, loc="left", fontsize=10.5, fontweight="bold"); ax.set_xlabel("Ruedas después del golpe")
    ax.spines[["top", "right"]].set_visible(False)
conteo = emp.groupby("prueba", sort=False)["p_menor_005"].sum()
axs[2].barh(conteo.index[::-1], conteo.values[::-1], color=["#B5700F" if "retorno →" in p else "#1F6FA3" for p in conteo.index[::-1]])
axs[2].axvline(ALFA * 17, color="#13202F", ls="--", lw=1)
axs[2].text(ALFA * 17 + 0.2, -0.4, "esperado por azar", fontsize=8.5)
axs[2].set_xlabel("Empresas con p < 0,05 (de 17)")
axs[2].set_title("Granger por empresa", loc="left", fontsize=10.5, fontweight="bold")
axs[2].spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(SALIDAS / "var_granger.png", dpi=160, facecolor="white")

print(pd.DataFrame(r).to_string(index=False))
