"""
U5 · Estacionariedad en la ventana de la unión — tesis version 3.0 (Unión)

El VAR exige series estables (estacionarias) en el tramo exacto que usa. La carpeta 04 del lado bursátil
justificó trabajar con retornos usando 3 años de precios; este paso lo confirma en las 244 ruedas de la
unión y lo extiende a las series de noticias y de volumen.

Especificación (la misma de la carpeta 04 para retornos): ADF con constante (regression="c"), rezagos
elegidos por AIC. Como confirmación se agrega KPSS con constante, que plantea la pregunta al revés
(hipótesis nula: la serie ES estacionaria). Conclusión:
  - "Estacionaria"          ADF rechaza (p < 0,05) y KPSS no rechaza (p ≥ 0,05);
  - "Estacionaria (ADF)"    ADF rechaza pero KPSS también rechaza: estable, con algo de persistencia;
  - "Inconclusa"            ninguno de los dos rechaza: los datos no alcanzan para decidir (serie persistente);
  - "No estacionaria"       ADF no rechaza y KPSS rechaza.

Para el tono de las noticias del mercado se prueban además dos transformaciones candidatas para el VAR:
  tono anormal      = tono de la rueda − promedio del tono de las 20 ruedas previas (misma lógica que la
                      atención y el volumen anormales). ELEGIDA el 24/10 como variable de tono del VAR:
                      está en los datasets de U4 (sent_anormal, sent_portal_anormal);
  cambio de tono    = tono de la rueda − tono de la rueda anterior (alternativa, solo para comparar).

Series:
  mercado  ret_merval, monto_anormal, sent_neto, sent_neto_portal, n_notas, atencion_anormal, vix_arg
  panel    retorno y vol_anormal de las 47 acciones;
           tono_propio de las 17 con sentimiento propio (la variable de empresa del VAR, decisión de U6);
           sent_neto_empresa de esas 17, de dos formas:
             "completada": los días sin noticias de la empresa toman el tono general del mercado;
             "solo días con noticia": la secuencia de los días con noticias, sin los huecos.

Solo lee ../04_dataset_unificado/. Escribe: resultados_adf_union.csv, resumen_u5.csv, verificaciones.csv, u5_resumen.png.
Uso:  python adf_union.py
"""

import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import adfuller, kpss

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
warnings.simplefilter("ignore", InterpolationWarning)   # KPSS avisa cuando el p-valor cae fuera de su tabla (<0,01 o >0,10)

AQUI = Path(__file__).parent
U4 = AQUI.parent / "04_dataset_unificado"
ALFA = 0.05

mercado = pd.read_csv(U4 / "dataset_mercado.csv")
panel = pd.read_csv(U4 / "dataset_panel.csv")


def probar(serie, nombre, ambito, ticker="", forma=""):
    x = pd.Series(serie).dropna().to_numpy(dtype=float)
    adf = adfuller(x, autolag="AIC", regression="c")
    kp = kpss(x, regression="c", nlags="auto")
    adf_ok, kpss_ok = adf[1] < ALFA, kp[1] >= ALFA
    if adf_ok:
        conclusion = "Estacionaria" if kpss_ok else "Estacionaria (ADF)"
    else:
        conclusion = "Inconclusa" if kpss_ok else "No estacionaria"
    return {"ambito": ambito, "serie": nombre, "forma": forma, "ticker": ticker, "n": len(x),
            "adf_estadistico": round(adf[0], 4), "adf_p": round(adf[1], 6), "adf_rezagos": adf[2],
            "kpss_estadistico": round(kp[0], 4), "kpss_p": round(kp[1], 4), "conclusion": conclusion}


filas = []
for col in ("ret_merval", "monto_anormal", "sent_neto", "sent_neto_portal", "n_notas", "atencion_anormal", "vix_arg"):
    filas.append(probar(mercado[col], col, "mercado"))
# Tono anormal: la variable que eligió esta etapa (decisión del 24/10), tomada del dataset de U4.
for col in ("sent_anormal", "sent_portal_anormal"):
    filas.append(probar(mercado[col], col, "mercado"))
# Cambio de tono: alternativa descartada, se prueba solo para documentar la comparación.
for col in ("sent_neto", "sent_neto_portal"):
    filas.append(probar(mercado[col].diff(), col, "mercado", forma="cambio de tono"))

for ticker, g in panel.groupby("ticker"):
    g = g.sort_values("rueda")
    filas.append(probar(g["retorno"], "retorno", "panel", ticker))
    filas.append(probar(g["vol_anormal"], "vol_anormal", "panel", ticker))
    if g["sentimiento_propio"].iloc[0] == 1:
        completada = g["sent_neto_empresa"].fillna(g["sent_neto"])
        filas.append(probar(completada, "sent_neto_empresa", "panel", ticker, "completada"))
        filas.append(probar(g["sent_neto_empresa"], "sent_neto_empresa", "panel", ticker, "solo días con noticia"))
        filas.append(probar(g["tono_propio"], "tono_propio", "panel", ticker))   # variable de empresa del VAR (decisión de U6)

res = pd.DataFrame(filas)
res.to_csv(AQUI / "resultados_adf_union.csv", index=False, encoding="utf-8")

# ── Resumen ──────────────────────────────────────────────────────────────
tabla = (res.assign(grupo=res["serie"] + np.where(res["forma"] != "", " (" + res["forma"] + ")", ""))
         .groupby(["ambito", "grupo"])["conclusion"].value_counts().unstack(fill_value=0))
CATS = ["Estacionaria", "Estacionaria (ADF)", "Inconclusa", "No estacionaria"]
for c in CATS:
    if c not in tabla.columns:
        tabla[c] = 0
tabla = tabla[CATS]
tabla["total"] = tabla.sum(axis=1)
tabla.to_csv(AQUI / "resumen_por_serie.csv", encoding="utf-8")

r = []
def m(clave, valor, detalle=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle})

m("series_probadas", len(res))
for cat, clave in (("No estacionaria", "no_estacionarias"), ("Inconclusa", "inconclusas")):
    sel = res[res["conclusion"] == cat]
    m(clave, len(sel), "; ".join(f"{s}{' ' + t if t else ''}{' (' + f + ')' if f else ''}" for s, t, f in zip(sel["serie"], sel["ticker"], sel["forma"])))
solo_adf = res[res["conclusion"] == "Estacionaria (ADF)"]
m("estacionarias_solo_adf", len(solo_adf), "; ".join(f"{s}{' ' + t if t else ''}{' (' + f + ')' if f else ''}" for s, t, f in zip(solo_adf["serie"], solo_adf["ticker"], solo_adf["forma"])))
m("adf_p_max_retornos", float(res.loc[res["serie"] == "retorno", "adf_p"].max()),
  res.loc[res["serie"] == "retorno"].sort_values("adf_p").iloc[-1]["ticker"])
for col in ("ret_merval", "monto_anormal", "sent_neto", "sent_neto_portal", "n_notas", "atencion_anormal", "vix_arg"):
    x = res[(res["ambito"] == "mercado") & (res["serie"] == col)].iloc[0]
    m(f"mercado_{col}", x["conclusion"], f"ADF p={x['adf_p']:.4f}; KPSS p={x['kpss_p']:.3f}")
adf04 = pd.read_csv(AQUI.parent.parent / "Lado Bursatil" / "04_adf" / "resultados_adf_47.csv")
ret04 = adf04[adf04["tipo"] == "retorno"]
x = res[res["serie"] == "sent_anormal"].iloc[0]
m("mercado_sent_anormal", x["conclusion"], f"ADF p={x['adf_p']:.6f}; KPSS p={x['kpss_p']:.3f}")
m("carpeta04_retornos_estacionarios", int((ret04["resultado"] == "Estacionaria").sum()), "de 47, con 3 años")

# ── Controles ────────────────────────────────────────────────────────────
CON_20_PREVIAS = ["atencion_anormal", "sent_anormal", "sent_portal_anormal"]
esperadas = 7 + 4 + 47 * 2 + int(panel.groupby("ticker")["sentimiento_propio"].first().sum()) * 3
controles = [
    ("Se probaron todas las series previstas", len(res) == esperadas),
    ("Las series de mercado tienen 244 datos (224 la atención y el tono anormal, sin sus 20 primeras ruedas)",
     bool(res.loc[(res["ambito"] == "mercado") & (res["forma"] == "") & ~res["serie"].isin(CON_20_PREVIAS), "n"].eq(244).all()
          and res.loc[res["serie"].isin(CON_20_PREVIAS), "n"].eq(224).all())),
    ("Retornos y volumen anormal de cada acción tienen 244 datos",
     bool(res.loc[res["serie"].isin(["retorno", "vol_anormal"]), "n"].eq(244).all())),
    ("La versión completada del sentimiento por empresa no tiene huecos",
     bool(res.loc[res["forma"] == "completada", "n"].eq(244).all())),
    ("Misma especificación que la carpeta 04 para retornos (ADF con constante, rezagos por AIC)",
     set(adf04.loc[adf04["tipo"] == "retorno", "regresion"]) == {"c"}),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u5.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
t = tabla.reset_index()
etq = {"ret_merval": "Retorno Merval", "monto_anormal": "Monto operado anormal", "sent_neto": "Tono de las noticias",
       "sent_neto_portal": "Tono ajustado por portal", "n_notas": "Notas por rueda", "atencion_anormal": "Atención anormal",
       "vix_arg": "VIX argentino", "sent_anormal": "Tono anormal (variable del VAR)",
       "sent_neto (cambio de tono)": "Cambio de tono (vs. rueda anterior)", "sent_portal_anormal": "Tono por portal, anormal",
       "sent_neto_portal (cambio de tono)": "Tono por portal, cambio", "retorno": "Retorno (47 acciones)", "vol_anormal": "Volumen anormal (47 acciones)",
       "sent_neto_empresa (completada)": "Tono de la empresa, completada (17)",
       "sent_neto_empresa (solo días con noticia)": "Tono de la empresa, solo días con noticia (17)",
       "tono_propio": "Tono propio de la empresa (17, variable del VAR)"}
t["etiqueta"] = t["grupo"].map(etq)
t = t.iloc[::-1]
fig, ax = plt.subplots(figsize=(10, 6.2))
izq = np.zeros(len(t))
for c, color in (("Estacionaria", "#2E8B57"), ("Estacionaria (ADF)", "#9CCB86"), ("Inconclusa", "#F2A900"), ("No estacionaria", "#D7301F")):
    pct = 100 * t[c] / t["total"]
    ax.barh(t["etiqueta"], pct, left=izq, color=color, label=c, height=0.65)
    izq += pct.to_numpy()
ax.set_xlim(0, 100); ax.set_xlabel("% de las series")
ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=4, frameon=False, fontsize=9)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(AQUI / "u5_resumen.png", dpi=160, facecolor="white")

print(pd.DataFrame(r).to_string(index=False)); print(); print(tabla.to_string()); print(); print(verif.to_string(index=False))
