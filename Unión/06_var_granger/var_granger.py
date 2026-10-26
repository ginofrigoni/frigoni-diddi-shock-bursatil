"""
U6 · VAR, Granger e impulso-respuesta — tesis version 3.0 (Unión)

La pregunta central de la tesis: ¿las noticias anticipan al mercado (precio y volumen), o el mercado anticipa
a las noticias? Se responde con modelos VAR y tests de causalidad de Granger, siempre en las dos direcciones.

Niveles (todos sobre las 224 ruedas con tono anormal y atención, del 02/06/2025 al 30/04/2026):
  mercado     VAR(tono anormal, atención anormal, retorno del Merval, monto operado anormal)
  empresa     para cada una de las 47 acciones: VAR(tono anormal del mercado, retorno, volumen anormal)
  propio      para las 17 con sentimiento propio: VAR(tono anormal, tono propio, retorno, volumen anormal)
  sector      para cada sector: VAR(tono anormal, retorno promedio del sector, volumen anormal promedio)
  régimen     ¿el efecto cambia en los días Tenso? Regresión con todos los días y una marca de día Tenso
              (no se cortan los días de cada régimen: eso pegaría días no consecutivos). Calmo vs. Tenso.

Rezagos: elegidos por AIC entre 1 y 5 para cada modelo. Granger: test F de que los rezagos de la causa no
aportan para predecir el efecto. Corrección por pruebas múltiples: Benjamini-Hochberg dentro de cada nivel.
Impulso-respuesta: ortogonalizado, con las noticias primero (una nota asignada a la rueda puede mover el precio
de ese día; el precio de ese día no puede cambiar una nota ya publicada); bandas del 95% asintóticas.
Control de calibración: se repite el Granger por empresa con el tono mezclado al azar (placebo); si el test
está bien calibrado, alrededor del 5% de los placebos da p < 0,05.

Solo lee ../04_dataset_unificado/. Escribe en esta carpeta: granger_resultados.csv, regimen_resultados.csv,
rezagos.csv, irf_mercado.csv, resumen_u6.csv, verificaciones.csv, u6_irf_mercado.png, u6_empresas.png.
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
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.api import VAR

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*frequency.*")

AQUI = Path(__file__).parent
U4 = AQUI.parent / "04_dataset_unificado"
MAX_REZAGOS = 5
ALFA = 0.05
HORIZONTE_IRF = 10
SEMILLA = 42
N_PLACEBO = 20

mercado = pd.read_csv(U4 / "dataset_mercado.csv")
panel = pd.read_csv(U4 / "dataset_panel.csv")
mercado = mercado.dropna(subset=["sent_anormal", "atencion_anormal"]).reset_index(drop=True)
RUEDAS = mercado["rueda"].tolist()
panel = panel[panel["rueda"].isin(RUEDAS)].sort_values(["ticker", "rueda"])

NOMBRE = {"sent_anormal": "tono", "atencion_anormal": "atención", "ret_merval": "retorno", "monto_anormal": "volumen",
          "retorno": "retorno", "vol_anormal": "volumen", "tono_propio": "tono propio", "ret_sector": "retorno", "vol_sector": "volumen"}
NOTICIAS = {"sent_anormal", "atencion_anormal", "tono_propio"}


def ajustar(datos):
    modelo = VAR(datos)
    k = modelo.select_order(maxlags=MAX_REZAGOS).aic
    k = int(min(max(k, 1), MAX_REZAGOS))
    return modelo.fit(k), k


def granger(res, causa, efecto):
    t = res.test_causality(efecto, [causa], kind="f")
    return float(t.test_statistic), float(t.pvalue)


filas, rezagos = [], []


def correr(nivel, unidad, datos, pares):
    res, k = ajustar(datos)
    rezagos.append({"nivel": nivel, "unidad": unidad, "rezagos": k, "estable": bool(res.is_stable()), "n": res.nobs})
    for causa, efecto in pares:
        f, pv = granger(res, causa, efecto)
        # Signo: suma de los coeficientes de los rezagos de la causa en la ecuación del efecto, en desvíos
        # (cuántos desvíos del efecto cambia ante una suba de un desvío de la causa, sumando los rezagos).
        suma = sum(res.params.loc[f"L{l}.{causa}", efecto] for l in range(1, k + 1))
        efecto_sd = suma * datos[causa].std() / datos[efecto].std()
        filas.append({"nivel": nivel, "unidad": unidad, "causa": causa, "efecto": efecto,
                      "direccion": "noticias → mercado" if causa in NOTICIAS else "mercado → noticias",
                      "prueba": f"{NOMBRE[causa]} → {NOMBRE[efecto]}", "rezagos": k, "F": round(f, 4), "p": pv,
                      "efecto_desvios": round(efecto_sd, 4), "signo": "+" if efecto_sd > 0 else "−"})
    return res


# ── 1. Mercado ───────────────────────────────────────────────────────────
VARS_M = ["sent_anormal", "atencion_anormal", "ret_merval", "monto_anormal"]
pares_m = [("sent_anormal", "ret_merval"), ("ret_merval", "sent_anormal"), ("sent_anormal", "monto_anormal"), ("monto_anormal", "sent_anormal"),
           ("atencion_anormal", "ret_merval"), ("ret_merval", "atencion_anormal"), ("atencion_anormal", "monto_anormal"), ("monto_anormal", "atencion_anormal")]
res_m = correr("mercado", "Merval", mercado[VARS_M], pares_m)

# Impulso-respuesta del mercado, con bandas del 95% por simulación.
irf = res_m.irf(HORIZONTE_IRF)
# Bandas asintóticas (estimación ± 1,96 errores estándar), las que usa por defecto statsmodels al graficar.
# No se usan las de simulación (errband_mc): en statsmodels 0.14.6 devuelven el límite inferior igual al superior.
se_irf = irf.stderr(orth=True)
bajo, alto = irf.orth_irfs - 1.96 * se_irf, irf.orth_irfs + 1.96 * se_irf
irf_filas = []
for i_imp, imp in enumerate(VARS_M):
    for i_resp, resp in enumerate(VARS_M):
        for h in range(HORIZONTE_IRF + 1):
            irf_filas.append({"impulso": imp, "respuesta": resp, "horizonte": h, "irf": irf.orth_irfs[h, i_resp, i_imp],
                              "banda_baja": bajo[h, i_resp, i_imp], "banda_alta": alto[h, i_resp, i_imp]})
irf_df = pd.DataFrame(irf_filas)
irf_df.to_csv(AQUI / "irf_mercado.csv", index=False, encoding="utf-8")
corr_resid = pd.DataFrame(res_m.resid, columns=VARS_M).corr()

# ── 2. Empresas (las 47, con el tono del mercado) y 3. tono propio (17) ──
pares_e = [("sent_anormal", "retorno"), ("sent_anormal", "vol_anormal"), ("retorno", "sent_anormal"), ("vol_anormal", "sent_anormal")]
pares_p = [("tono_propio", "retorno"), ("tono_propio", "vol_anormal"), ("retorno", "tono_propio"), ("vol_anormal", "tono_propio")]
tickers = sorted(panel["ticker"].unique())
for t in tickers:
    g = panel[panel["ticker"] == t].reset_index(drop=True)
    correr("empresa", t, g[["sent_anormal", "retorno", "vol_anormal"]], pares_e)
    if g["sentimiento_propio"].iloc[0] == 1:
        correr("propio", t, g[["sent_anormal", "tono_propio", "retorno", "vol_anormal"]], pares_p)

# ── 4. Sectores ──────────────────────────────────────────────────────────
pares_s = [("sent_anormal", "ret_sector"), ("sent_anormal", "vol_sector"), ("ret_sector", "sent_anormal"), ("vol_sector", "sent_anormal")]
sectores = panel.groupby(["sector", "rueda"]).agg(ret_sector=("retorno", "mean"), vol_sector=("vol_anormal", "mean"),
                                                   n_acciones=("ticker", "nunique")).reset_index()
for sec, g in sectores.groupby("sector"):
    g = g.merge(mercado[["rueda", "sent_anormal"]], on="rueda").sort_values("rueda").reset_index(drop=True)
    correr("sector", f"{sec} ({g['n_acciones'].iloc[0]})", g[["sent_anormal", "ret_sector", "vol_sector"]], pares_s)

# ── 5. Corrección por pruebas múltiples (Benjamini-Hochberg, dentro de cada nivel) ─
gr = pd.DataFrame(filas)
gr["p_bh"] = np.nan
for nivel, idx in gr.groupby("nivel").groups.items():
    gr.loc[idx, "p_bh"] = multipletests(gr.loc[idx, "p"], method="fdr_bh")[1]
gr["signif_sin_corregir"] = gr["p"] < ALFA
gr["signif_bh"] = gr["p_bh"] < ALFA
gr.to_csv(AQUI / "granger_resultados.csv", index=False, encoding="utf-8")
rz = pd.DataFrame(rezagos)
rz.to_csv(AQUI / "rezagos.csv", index=False, encoding="utf-8")

# ── 6. Régimen: ¿el efecto cambia en los días Tenso? ─────────────────────
k_m = int(rz.loc[rz["nivel"] == "mercado", "rezagos"].iloc[0])
reg_filas = []
for causa, efecto in [("sent_anormal", "ret_merval"), ("sent_anormal", "monto_anormal"), ("ret_merval", "sent_anormal"), ("monto_anormal", "sent_anormal")]:
    d = mercado[["rueda", "regimen", causa, efecto]].copy()
    X = pd.DataFrame({"const": 1.0, "tenso": (d["regimen"] == "Tenso").astype(float)})
    for l in range(1, k_m + 1):
        X[f"y_l{l}"] = d[efecto].shift(l)
        X[f"x_l{l}"] = d[causa].shift(l)
        X[f"x_l{l}_tenso"] = d[causa].shift(l) * X["tenso"]
    usar = X.notna().all(axis=1) & d["regimen"].isin(["Calmo", "Tenso"])   # los días Moderado no se usan como efecto
    ols = sm.OLS(d.loc[usar, efecto], X[usar]).fit(cov_type="HC3")
    nombres = list(X.columns)
    def wald(restr):
        R = np.zeros((len(restr), len(nombres)))
        for i, comb in enumerate(restr):
            for nombre, coef in comb:
                R[i, nombres.index(nombre)] = coef
        w = ols.wald_test(R, use_f=True, scalar=True)
        return float(w.statistic), float(w.pvalue)
    pruebas = {
        "en días Calmo": [[(f"x_l{l}", 1)] for l in range(1, k_m + 1)],
        "en días Tenso": [[(f"x_l{l}", 1), (f"x_l{l}_tenso", 1)] for l in range(1, k_m + 1)],
        "diferencia Tenso − Calmo": [[(f"x_l{l}_tenso", 1)] for l in range(1, k_m + 1)],
    }
    for nombre_p, restr in pruebas.items():
        f, pv = wald(restr)
        reg_filas.append({"causa": causa, "efecto": efecto, "prueba": f"{NOMBRE[causa]} → {NOMBRE[efecto]}",
                          "direccion": "noticias → mercado" if causa in NOTICIAS else "mercado → noticias",
                          "cuando": nombre_p, "rezagos": k_m, "n": int(usar.sum()),
                          "n_tenso": int((usar & (d["regimen"] == "Tenso")).sum()), "F": round(f, 4), "p": pv})
rg = pd.DataFrame(reg_filas)
rg["p_bh"] = multipletests(rg["p"], method="fdr_bh")[1]
rg["signif_bh"] = rg["p_bh"] < ALFA
rg.to_csv(AQUI / "regimen_resultados.csv", index=False, encoding="utf-8")

# ── 7. Placebo: Granger por empresa con el tono mezclado al azar ─────────
rng = np.random.default_rng(SEMILLA)
placebo = []
for _ in range(N_PLACEBO):
    falso = rng.permutation(mercado["sent_anormal"].to_numpy())
    for t in tickers:
        g = panel[panel["ticker"] == t].reset_index(drop=True)
        datos = pd.DataFrame({"sent_anormal": falso, "retorno": g["retorno"].to_numpy(), "vol_anormal": g["vol_anormal"].to_numpy()})
        res, _ = ajustar(datos)
        placebo += [granger(res, "sent_anormal", "retorno")[1], granger(res, "sent_anormal", "vol_anormal")[1]]
placebo = np.array(placebo)

# ── 8. Controles ─────────────────────────────────────────────────────────
n_prop = int(panel.groupby("ticker")["sentimiento_propio"].first().sum())
n_sec = panel["sector"].nunique()
controles = [
    ("Todos los modelos usan las 224 ruedas, sin valores faltantes",
     len(mercado) == 224 and not mercado[VARS_M].isna().any().any() and not panel[["retorno", "vol_anormal", "tono_propio"]].isna().any().any()),
    ("Se corrieron todos los tests previstos",
     len(gr) == len(pares_m) + 47 * 4 + n_prop * 4 + n_sec * 4 and len(rg) == 12),
    ("Todos los VAR son estables (raíces dentro del círculo unitario)", bool(rz["estable"].all())),
    ("Rezagos entre 1 y 5 en todos los modelos", bool(rz["rezagos"].between(1, MAX_REZAGOS).all())),
    ("La corrección BH nunca achica un p-valor", bool((gr["p_bh"] >= gr["p"] - 1e-12).all())),
    (f"El test está calibrado: con el tono mezclado al azar, entre 2% y 9% de p < 0,05 (dio {100 * (placebo < ALFA).mean():.1f}%)",
     0.02 <= (placebo < ALFA).mean() <= 0.09),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── 9. Resumen ───────────────────────────────────────────────────────────
r = []
def m(clave, valor, detalle=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle})

m("ruedas", len(mercado), f"{RUEDAS[0]} a {RUEDAS[-1]}")
m("tests_granger", len(gr)); m("tests_regimen", len(rg)); m("modelos_var", len(rz))
m("rezagos_mercado", k_m)
m("rezagos_empresas_mediana", int(rz.loc[rz["nivel"] == "empresa", "rezagos"].median()))
for nivel in ("mercado", "empresa", "propio", "sector"):
    g = gr[gr["nivel"] == nivel]
    for d_ in ("noticias → mercado", "mercado → noticias"):
        gd = g[g["direccion"] == d_]
        clave = "nm" if d_.startswith("noticias") else "mn"
        sig = gd[gd["signif_bh"]]
        m(f"{nivel}_{clave}_tests", len(gd))
        m(f"{nivel}_{clave}_sin_corregir", int(gd["signif_sin_corregir"].sum()))
        m(f"{nivel}_{clave}_bh", int(gd["signif_bh"].sum()),
          "; ".join(f"{u.replace('.BA', '')}: {pr} (p_bh={pb:.3f})" for u, pr, pb in zip(sig["unidad"], sig["prueba"], sig["p_bh"])))
for nivel in ("mercado", "empresa", "propio", "sector"):
    sig = gr[(gr["nivel"] == nivel) & gr["signif_bh"]]
    for prueba_, g_ in sig.groupby("prueba"):
        m(f"signo_{nivel}_{prueba_}", f"{(g_['signo'] == '+').sum()}+ / {(g_['signo'] == '−').sum()}−",
          f"mediana {g_['efecto_desvios'].median():.3f} desvíos")
m("placebo_pct_p05", round(100 * (placebo < ALFA).mean(), 1), f"{len(placebo)} tests con el tono mezclado al azar")
m("esperados_por_azar_empresa", round(ALFA * len(gr[gr["nivel"] == "empresa"]), 1), "5% de los tests por empresa")
for _, x in gr[gr["nivel"] == "mercado"].iterrows():
    m(f"mercado_{x['causa']}__{x['efecto']}", round(x["p"], 4), f"F={x['F']}; p_bh={x['p_bh']:.4f}")
m("sd_ret_merval", round(100 * mercado["ret_merval"].std(), 2), "un desvío del retorno del Merval, en %")
m("sd_sent_anormal", round(mercado["sent_anormal"].std(), 2), "un desvío del tono anormal, en puntos")
for imp, resp in (("ret_merval", "sent_anormal"), ("sent_anormal", "ret_merval"), ("sent_anormal", "monto_anormal")):
    for h in (0, 1, 2, 3):
        x = irf_df[(irf_df["impulso"] == imp) & (irf_df["respuesta"] == resp) & (irf_df["horizonte"] == h)].iloc[0]
        fuera = x["banda_baja"] > 0 or x["banda_alta"] < 0
        m(f"irf_{imp}__{resp}__h{h}", round(x["irf"], 4), f"banda {x['banda_baja']:.4f} a {x['banda_alta']:.4f}; {'distinto de 0' if fuera else 'incluye 0'}")
m("corr_mismo_dia_tono_retorno", round(corr_resid.loc["sent_anormal", "ret_merval"], 3), "correlación de las sorpresas del mismo día (residuos del VAR)")
m("corr_mismo_dia_tono_volumen", round(corr_resid.loc["sent_anormal", "monto_anormal"], 3))
m("corr_mismo_dia_atencion_volumen", round(corr_resid.loc["atencion_anormal", "monto_anormal"], 3))
m("corr_mismo_dia_atencion_retorno", round(corr_resid.loc["atencion_anormal", "ret_merval"], 3))
for _, x in rg.iterrows():
    m(f"regimen_{x['causa']}__{x['efecto']}__{x['cuando']}", round(x["p"], 4), f"p_bh={x['p_bh']:.4f}")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u6.csv", index=False, encoding="utf-8")

# ── 10. Figuras ──────────────────────────────────────────────────────────
pares_fig = [("sent_anormal", "ret_merval", "Tono → retorno del Merval"), ("sent_anormal", "monto_anormal", "Tono → volumen operado"),
             ("ret_merval", "sent_anormal", "Retorno del Merval → tono"), ("monto_anormal", "sent_anormal", "Volumen operado → tono"),
             ("atencion_anormal", "monto_anormal", "Atención → volumen operado"), ("ret_merval", "atencion_anormal", "Retorno del Merval → atención")]
fig, axs = plt.subplots(2, 3, figsize=(11, 6.2))
for ax, (imp, resp, tit) in zip(axs.flat, pares_fig):
    s = irf_df[(irf_df["impulso"] == imp) & (irf_df["respuesta"] == resp)]
    ax.fill_between(s["horizonte"], s["banda_baja"], s["banda_alta"], color="#4A90C8", alpha=0.2)
    ax.plot(s["horizonte"], s["irf"], color="#2C5F8A", lw=1.8, marker="o", ms=3)
    ax.axhline(0, color="#999", lw=0.8)
    ax.set_title(tit, fontsize=10, fontweight="bold", loc="left")
    ax.set_xlabel("Ruedas después del golpe", fontsize=8.5)
    ax.tick_params(labelsize=8)
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Impulso-respuesta del mercado (golpe de un desvío; banda: 95%)", x=0.01, ha="left", fontsize=12, fontweight="bold")
fig.tight_layout()
fig.savefig(AQUI / "u6_irf_mercado.png", dpi=160, facecolor="white")

emp = gr[gr["nivel"] == "empresa"].copy()
emp["t"] = emp["unidad"].str.replace(".BA", "", regex=False)
mat = emp.pivot(index="t", columns="prueba", values="p")
orden_cols = ["tono → retorno", "tono → volumen", "retorno → tono", "volumen → tono"]
mat = mat[orden_cols]
sig = emp.pivot(index="t", columns="prueba", values="signif_bh")[orden_cols]
fig, ax = plt.subplots(figsize=(7.5, 11))
im = ax.imshow(-np.log10(np.clip(mat.to_numpy(dtype=float), 1e-3, 1)), aspect="auto", cmap="Blues", vmin=0, vmax=3)   # piso 0,001: más chico = máximo color
for i in range(mat.shape[0]):
    for j in range(mat.shape[1]):
        pv = mat.iloc[i, j]
        if pv < ALFA:
            ax.text(j, i, "●" if sig.iloc[i, j] else "○", ha="center", va="center", fontsize=9, color="#D7301F" if sig.iloc[i, j] else "#12263A")
ax.set_xticks(range(4), ["Tono →\nretorno", "Tono →\nvolumen", "Retorno →\ntono", "Volumen →\ntono"], fontsize=9)
ax.set_yticks(range(mat.shape[0]), mat.index, fontsize=7.5)
ax.set_title("Granger por empresa (○ p < 0,05 sin corregir · ● significativo con BH)", loc="left", fontsize=10.5, fontweight="bold")
fig.colorbar(im, ax=ax, fraction=0.04, pad=0.02, label="−log10(p): más oscuro = p más chico")
fig.tight_layout()
fig.savefig(AQUI / "u6_empresas.png", dpi=160, facecolor="white")

print(pd.DataFrame(r).to_string(index=False)); print(); print(verif.to_string(index=False))
print(); print(gr[gr["nivel"].isin(["mercado", "sector"])][["nivel", "unidad", "prueba", "rezagos", "F", "p", "p_bh"]].to_string(index=False))
print(); print(rg[["prueba", "cuando", "n", "n_tenso", "F", "p", "p_bh"]].to_string(index=False))
