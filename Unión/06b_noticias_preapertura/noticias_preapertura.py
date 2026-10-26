"""
U6b · Noticias publicadas con el mercado cerrado → precio de la rueda siguiente — tesis version 3.0 (Unión)

Implementa EXACTAMENTE la especificación fijada antes de ver los resultados (especificacion_previa.md).
Las notas publicadas entre el cierre de la rueda anterior y la apertura (11:00) salen antes de cualquier
operación de la rueda: la rueda no puede haberlas causado. Si su tono anticipa el retorno de apertura,
es noticias → mercado sin ambigüedad.

Solo lee. Entradas: U1 (nota_a_rueda.csv), U3 (las funciones del cruce de Gino), U4 (K del tono propio y
datasets), el sentimiento por nota y por oración de Lado Noticias y los precios (apertura y cierre) de Lado Bursatil.
Uso:  python noticias_preapertura.py
"""

import collections
import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
csv.field_size_limit(10 ** 9)

AQUI = Path(__file__).parent
UNION = AQUI.parent
RAIZ = UNION.parent
NER = RAIZ / "Lado Noticias" / "ner_entidades"
sys.path.insert(0, str(NER))
import cruce_ner_sentimiento as gino   # noqa: E402

VENTANA = 20
ALFA = 0.05
SEMILLA = 42
N_PLACEBO = 300
ELECTORALES = ["2025-09-08", "2025-10-27"]
INICIO = "2025-05-05"

# ── 1. Notas pre-apertura ────────────────────────────────────────────────
nr = pd.read_csv(UNION / "01_alineacion_noticias_ruedas" / "nota_a_rueda.csv")
nr = nr[nr["en_ventana_union"]].copy()
hora = pd.to_datetime(nr["hora_ar"])
en_sesion = (nr["fecha_ar"] == nr["rueda"]) & (hora.dt.hour >= 11) & (hora.dt.hour < 17)
nr["pre_apertura"] = ~en_sesion
pre = nr[nr["pre_apertura"] & ~nr["hora_sospechosa"]]
art = pd.read_csv(RAIZ / "Lado Noticias" / "sentimiento_finbert" / "finetuned_articulos.csv", usecols=["url", "sent_neto"])
pre = pre.merge(art, on="url")

mercado = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_mercado.csv")
ruedas = mercado["rueda"].tolist()
serie = pre.groupby("rueda").agg(n_notas_pre=("url", "size"), tono_pre=("sent_neto", "mean")).reindex(ruedas)
serie["tono_pre_anormal"] = serie["tono_pre"] - serie["tono_pre"].shift(1).rolling(VENTANA, min_periods=VENTANA).mean()

# ── 2. Retornos de apertura y de la sesión ───────────────────────────────
pr = pd.read_csv(RAIZ / "Lado Bursatil" / "01_scraping_acciones" / "precios_diarios_47_acciones.csv").sort_values(["ticker", "Date"])
cierre_ant = pr.groupby("ticker")["Close"].shift(1)
pr["ret_apertura"] = pr["Open"] / cierre_ant - 1
pr["ret_sesion"] = pr["Close"] / pr["Open"] - 1
pr["ret_cc"] = pr["Close"] / cierre_ant - 1
pr["ret_cc_ant"] = pr.groupby("ticker")["ret_cc"].shift(1)
pr = pr.rename(columns={"Date": "rueda"})
prom = pr.groupby("rueda")[["ret_apertura", "ret_sesion", "ret_cc"]].mean()
prom["ret_cc_ant"] = prom["ret_cc"].shift(1)
serie = serie.join(prom, how="left")
serie["tras_dia_sin_mercado"] = (mercado.set_index("rueda")["dias_cubiertos"] > 1).astype(int)
serie["electoral"] = serie.index.isin(ELECTORALES).astype(int)
serie.index.name = "rueda"
serie.round(6).to_csv(AQUI / "serie_preapertura.csv", encoding="utf-8")

# ── 3. Tono propio pre-apertura de las 17 empresas ───────────────────────
r4 = pd.read_csv(UNION / "04_dataset_unificado" / "resumen_u4.csv").set_index("metrica")["valor"]
K = float(r4["k_peso_tono_propio"])
panel4 = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_panel.csv", usecols=["ticker", "rueda", "sentimiento_propio"])
propias = sorted(panel4.loc[panel4["sentimiento_propio"] == 1, "ticker"].unique())
entidad = {t.replace(".BA", "").lower(): t for t in propias}
urls_pre = set(pre["url"])
rueda_de = dict(zip(pre["url"], pre["rueda"]))
sent = {}
with open(RAIZ / "Lado Noticias" / "sentimiento_finbert" / "beto_oraciones_finetuned.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["url"] in urls_pre:
            sent[(r["url"], r["or_idx"])] = (gino.norm(r["oracion"]), r["label"])
acum, vistos = collections.defaultdict(collections.Counter), set()
with open(NER / "resultados_ner" / "ner_oraciones.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["url"] not in urls_pre or r["tipo"] != "EMP_MERVAL":
            continue
        ent = r["entidad"].strip().lower()
        if ent not in entidad:
            continue
        k = (r["url"], r["oracion_idx"])
        s = sent.get(k)
        if s is None or s[0] != gino.norm(r["oracion"]) or (k, ent) in vistos:
            continue
        vistos.add((k, ent))
        acum[(rueda_de[r["url"]], entidad[ent])][s[1]] += 1
filas = []
for (rd, t), c in acum.items():
    n = sum(c[x] for x in gino.CLASES)
    filas.append({"rueda": rd, "ticker": t, "n_oraciones_pre": n, "sent_emp_pre": 100 * (c["POS"] - c["NEG"]) / n})
emp = pd.DataFrame(filas)
grilla = pd.MultiIndex.from_product([propias, ruedas], names=["ticker", "rueda"]).to_frame(index=False)
emp = grilla.merge(emp, on=["ticker", "rueda"], how="left").merge(serie[["tono_pre", "tono_pre_anormal", "tras_dia_sin_mercado", "electoral"]].reset_index(), on="rueda")
emp["n_oraciones_pre"] = emp["n_oraciones_pre"].fillna(0)
peso = emp["n_oraciones_pre"] / (emp["n_oraciones_pre"] + K)
emp["tono_propio_pre"] = np.where(emp["n_oraciones_pre"] > 0, peso * (emp["sent_emp_pre"] - emp["tono_pre"]), 0.0)
emp = emp.merge(pr[["ticker", "rueda", "ret_apertura", "ret_sesion", "ret_cc_ant"]], on=["ticker", "rueda"], how="left")
emp.round(6).to_csv(AQUI / "panel_preapertura.csv", index=False, encoding="utf-8")

# ── 4. Modelos ───────────────────────────────────────────────────────────
def mercado_ols(datos, y, tono="tono_pre_anormal"):
    d = datos.dropna(subset=[y, tono, "ret_cc_ant"])
    X = sm.add_constant(d[[tono, "ret_cc_ant", "tras_dia_sin_mercado"]])
    return sm.OLS(d[y], X).fit(cov_type="HC3"), len(d)


def panel_ols(datos, y, tono="tono_propio_pre"):
    d = datos.dropna(subset=[y, tono, "tono_pre_anormal", "ret_cc_ant"]).copy()
    X = pd.concat([d[[tono, "tono_pre_anormal", "ret_cc_ant", "tras_dia_sin_mercado"]],
                   pd.get_dummies(d["ticker"], drop_first=True, dtype=float)], axis=1)
    X = sm.add_constant(X)
    grupos = pd.factorize(d["rueda"])[0]
    return sm.OLS(d[y], X).fit(cov_type="cluster", cov_kwds={"groups": grupos}), len(d)


principales = []
for muestra, sel in (("todas las ruedas", lambda x: x), ("sin días electorales", lambda x: x[x["electoral"] == 0])):
    for y in ("ret_apertura", "ret_sesion"):
        res, n = mercado_ols(sel(serie), y)
        principales.append({"muestra": muestra, "nivel": "mercado (promedio de las 47)", "retorno": y, "variable": "tono pre-apertura anormal",
                            "b": res.params["tono_pre_anormal"], "error": res.bse["tono_pre_anormal"], "p": res.pvalues["tono_pre_anormal"],
                            "control_ret_anterior": res.params["ret_cc_ant"], "p_ret_anterior": res.pvalues["ret_cc_ant"], "n": n})
        res, n = panel_ols(sel(emp), y)
        principales.append({"muestra": muestra, "nivel": "panel de las 17 empresas", "retorno": y, "variable": "tono propio pre-apertura",
                            "b": res.params["tono_propio_pre"], "error": res.bse["tono_propio_pre"], "p": res.pvalues["tono_propio_pre"],
                            "control_ret_anterior": res.params["ret_cc_ant"], "p_ret_anterior": res.pvalues["ret_cc_ant"], "n": n,
                            "b_tono_mercado": res.params["tono_pre_anormal"], "p_tono_mercado": res.pvalues["tono_pre_anormal"]})
pr_df = pd.DataFrame(principales)
pr_df["p_bh"] = np.nan
for muestra, idx in pr_df.groupby("muestra").groups.items():
    pr_df.loc[idx, "p_bh"] = multipletests(pr_df.loc[idx, "p"], method="fdr_bh")[1]
# Efecto en unidades simples: cuánto cambia el retorno (en %) por un desvío del tono.
sd_tono = {"tono pre-apertura anormal": serie["tono_pre_anormal"].std(), "tono propio pre-apertura": emp["tono_propio_pre"].std()}
pr_df["efecto_por_desvio_pct"] = 100 * pr_df["b"] * pr_df["variable"].map(sd_tono)
pr_df.to_csv(AQUI / "resultados_principales.csv", index=False, encoding="utf-8")

detalle = []
for t in propias:
    g = emp[emp["ticker"] == t]
    for y in ("ret_apertura", "ret_sesion"):
        d = g.dropna(subset=[y, "tono_propio_pre", "tono_pre_anormal", "ret_cc_ant"])
        X = sm.add_constant(d[["tono_propio_pre", "tono_pre_anormal", "ret_cc_ant", "tras_dia_sin_mercado"]])
        res = sm.OLS(d[y], X).fit(cov_type="HC3")
        detalle.append({"ticker": t, "retorno": y, "b": res.params["tono_propio_pre"], "p": res.pvalues["tono_propio_pre"],
                        "ruedas_con_mencion_pre": int((d["n_oraciones_pre"] > 0).sum()), "n": len(d)})
det = pd.DataFrame(detalle)
det["p_bh"] = multipletests(det["p"], method="fdr_bh")[1]
det.to_csv(AQUI / "resultados_empresas.csv", index=False, encoding="utf-8")

# ── 5. Control de calibración (tono mezclado al azar) ────────────────────
rng = np.random.default_rng(SEMILLA)
placebo = []
for _ in range(N_PLACEBO):
    falso = serie.copy()
    falso["tono_pre_anormal"] = rng.permutation(falso["tono_pre_anormal"].to_numpy())
    for y in ("ret_apertura", "ret_sesion"):
        placebo.append(mercado_ols(falso, y)[0].pvalues["tono_pre_anormal"])
placebo = np.array(placebo)
# Control de dirección: el tono de la noche refleja cómo cerró el mercado.
dirc = serie.dropna(subset=["tono_pre_anormal", "ret_cc_ant"])
corr_dir = dirc["tono_pre_anormal"].corr(dirc["ret_cc_ant"])

# ── 6. Controles ─────────────────────────────────────────────────────────
pre_n = pre.groupby("rueda").size().reindex(ruedas)
controles = [
    ("Ninguna nota pre-apertura se publicó durante la sesión de su rueda (11:00 a 17:00)",
     not ((pre["fecha_ar"] == pre["rueda"]) & pd.to_datetime(pre["hora_ar"]).dt.hour.between(11, 16)).any()),
    ("Ninguna nota pre-apertura tiene hora sospechosa", not pre["hora_sospechosa"].any()),
    ("Todas las ruedas tienen notas pre-apertura", bool(pre_n.notna().all())),
    ("Los modelos principales usan 224 ruedas (mercado) con todas las ruedas", int(pr_df.loc[(pr_df["muestra"] == "todas las ruedas") & pr_df["nivel"].str.startswith("mercado"), "n"].min()) == 224),
    ("El panel tiene las 17 empresas", emp["ticker"].nunique() == 17),
    (f"Calibración: con el tono mezclado al azar, entre 2% y 9% de p < 0,05 (dio {100 * (placebo < ALFA).mean():.1f}%)", 0.02 <= (placebo < ALFA).mean() <= 0.09),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── 7. Resumen ───────────────────────────────────────────────────────────
r = []
def m(clave, valor, detalle_=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle_})

m("notas_preapertura", len(pre), f"de {len(nr)} notas de la ventana; {int((nr['pre_apertura'] & nr['hora_sospechosa']).sum())} pre-apertura excluidas por hora sospechosa")
m("notas_pre_por_rueda_min", int(pre_n.min())); m("notas_pre_por_rueda_mediana", int(pre_n.median()))
m("sd_tono_pre_anormal", round(serie["tono_pre_anormal"].std(), 2))
m("sd_ret_apertura_pct", round(100 * serie["ret_apertura"].std(), 2)); m("sd_ret_sesion_pct", round(100 * serie["ret_sesion"].std(), 2))
m("corr_tono_pre_ret_anterior", round(corr_dir, 3), "el tono de la noche refleja el cierre del día")
for _, x in pr_df.iterrows():
    m(f"{x['muestra']}|{x['nivel']}|{x['retorno']}", round(x["b"], 6),
      f"p={x['p']:.4f}; p_bh={x['p_bh']:.4f}; efecto por desvío {x['efecto_por_desvio_pct']:.3f}%; n={x['n']}")
m("empresas_p05_sin_corregir", int((det["p"] < ALFA).sum()), f"de {len(det)}")
m("empresas_bh", int((det["p_bh"] < ALFA).sum()), "; ".join(f"{a.replace('.BA', '')} {b}" for a, b in zip(det.loc[det['p_bh'] < ALFA, 'ticker'], det.loc[det['p_bh'] < ALFA, 'retorno'])))
m("placebo_pct_p05", round(100 * (placebo < ALFA).mean(), 1), f"{len(placebo)} pruebas")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u6b.csv", index=False, encoding="utf-8")

# ── 8. Figura ────────────────────────────────────────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(11, 4.6))
d = serie.dropna(subset=["tono_pre_anormal", "ret_apertura"])
for ax, y, tit in ((axs[0], "ret_apertura", "Retorno de apertura (cierre de ayer → apertura)"), (axs[1], "ret_sesion", "Retorno de la sesión (apertura → cierre)")):
    normal = d[d["electoral"] == 0]
    ax.scatter(normal["tono_pre_anormal"], 100 * normal[y], s=14, color="#4A90C8", alpha=0.7, label="Ruedas")
    el = d[d["electoral"] == 1]
    ax.scatter(el["tono_pre_anormal"], 100 * el[y], s=40, color="#C26A00", marker="D", label="Días electorales")
    res, _ = mercado_ols(serie, y)
    xs = np.linspace(d["tono_pre_anormal"].min(), d["tono_pre_anormal"].max(), 50)
    ax.plot(xs, 100 * (res.params["const"] + res.params["tono_pre_anormal"] * xs), color="#12263A", lw=1.5,
            label=f"Recta (p = {res.pvalues['tono_pre_anormal']:.3f})")
    ax.axhline(0, color="#999", lw=0.6); ax.axvline(0, color="#999", lw=0.6)
    ax.set_xlabel("Tono anormal de las notas publicadas con el mercado cerrado")
    ax.set_title(tit, loc="left", fontsize=10.5, fontweight="bold")
    ax.legend(frameon=False, fontsize=8); ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("Retorno promedio de las 47 acciones (%)")
fig.tight_layout(); fig.savefig(AQUI / "u6b_preapertura.png", dpi=160, facecolor="white")

for _, x in pd.DataFrame(r).iterrows():
    print(f"{x['metrica']:72s} {str(x['valor']):12s} {str(x['detalle'])[:110]}")
print(); print(verif.to_string(index=False))
