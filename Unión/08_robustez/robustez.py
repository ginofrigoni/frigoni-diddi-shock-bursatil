"""
U8 · Robustez — tesis version 3.0 (Unión)

Repite los resultados principales de U6 (VAR y Granger) y U7 (event study) cambiando UNA decisión por vez.
Antes de las variantes, la configuración base tiene que reproducir exactamente U6 y U7 (control de que la
reimplementación es la misma); si no, nada de lo que sigue es comparable.

Resultados que se repiten:
  A  Mercado: Granger retorno → tono, tono → retorno, tono → volumen (VAR de U6, BH sobre sus 8 pruebas).
  B  Tono propio: cuántas de las 17 empresas tienen retorno → tono propio, tono propio → retorno y → volumen (BH).
  C  Empresas con el tono del mercado: cuántas de las 47 tienen retorno → tono y tono → retorno (BH).
  D  Régimen: retorno → tono y tono → retorno en días Calmo y en días Tenso (o No calmo).
  E  Event study: ruedas de tono extremo positivo, retorno anormal del Merval el mismo día y en las 3 previas.

Variantes (una decisión por vez):
  portal        tono ajustado por portal en lugar del simple
  nivel         tono en nivel en lugar del tono anormal (decisión de U5)
  sin_sospechosa sin las notas con hora sospechosa
  calendario    fecha de calendario en lugar de la regla de las 17:00 (las notas de días sin rueda se pierden)
  mismo_dia     solo notas publicadas el mismo día de la rueda, antes del cierre (sin las de la noche anterior
                ni las del fin de semana): ¿el "retorno → tono" es solo la crónica del cierre?
  sin_abril     sin abril de 2026 (hueco de iProfesional)
  sin_iliquidas sin GCDI, RIGO, GRIM y GARO (solo afecta a C)
  electorales   los dos días electorales como variables de control en los VAR
  filtrado      régimen con probabilidades filtradas (solo D)
  no_calmo      Calmo contra No calmo = Moderado + Tenso (solo D)
  umbral_3, umbral_2   umbral de la regla de shocks (solo E)

Solo lee. Escribe: robustez.csv (una fila por resultado y variante), resumen_u8.csv, verificaciones.csv, u8_robustez.png.
Uso:  python robustez.py
"""

import collections
import csv
import sys
import warnings
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy import stats
from statsmodels.stats.multitest import multipletests
from statsmodels.tsa.api import VAR

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
warnings.filterwarnings("ignore")
csv.field_size_limit(10 ** 9)

AQUI = Path(__file__).parent
UNION = AQUI.parent
RAIZ = UNION.parent
NER = RAIZ / "Lado Noticias" / "ner_entidades"
sys.path.insert(0, str(NER))
import cruce_ner_sentimiento as gino   # noqa: E402

VENTANA, MAX_REZAGOS, ALFA = 20, 5, 0.05
ELECTORALES = ["2025-09-08", "2025-10-27"]
ILIQUIDAS = ["GCDI.BA", "RIGO.BA", "GRIM.BA", "GARO.BA"]
UMBRAL_SHOCK = 2.5

# ── Datos base ───────────────────────────────────────────────────────────
mercado = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_mercado.csv")
panel = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_panel.csv")
RUEDAS = mercado["rueda"].tolist()
cal = pd.read_csv(RAIZ / "Lado Bursatil" / "03_vix_argentino" / "vix_arg.csv")
merv = cal.set_index("fecha")["retorno_diario"]
calendario = list(merv.index); pos = {f: i for i, f in enumerate(calendario)}
K = float(pd.read_csv(UNION / "04_dataset_unificado" / "resumen_u4.csv").set_index("metrica").loc["k_peso_tono_propio", "valor"])
PROPIAS = sorted(panel.loc[panel["sentimiento_propio"] == 1, "ticker"].unique())

notas = pd.read_csv(UNION / "01_alineacion_noticias_ruedas" / "nota_a_rueda.csv")
art = pd.read_csv(RAIZ / "Lado Noticias" / "sentimiento_finbert" / "finetuned_articulos.csv", usecols=["url", "fuente", "sent_neto"])
notas = notas.merge(art, on="url")
dentro = notas[notas["en_ventana_union"]]
notas["sent_portal"] = notas["sent_neto"] - notas["fuente"].map(dentro.groupby("fuente")["sent_neto"].mean())
hora = pd.to_datetime(notas["hora_ar"])
notas["mismo_dia"] = (notas["fecha_ar"] == notas["rueda"]) & (hora.dt.hour < 17)
notas["rueda_calendario"] = np.where(notas["fecha_texto"].isin(set(RUEDAS)), notas["fecha_texto"], None)

# Menciones de las 17 empresas por nota (mismo cruce que U3), para rearmar el tono propio con cualquier subconjunto de notas.
print("Leyendo menciones de empresas por nota...")
urls = set(notas["url"])
ent2t = {t.replace(".BA", "").lower(): t for t in PROPIAS}
sent = {}
with open(RAIZ / "Lado Noticias" / "sentimiento_finbert" / "beto_oraciones_finetuned.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["url"] in urls:
            sent[(r["url"], r["or_idx"])] = (gino.norm(r["oracion"]), r["label"])
menciones = collections.defaultdict(collections.Counter)    # (url, ticker) -> clases
vistos = set()
with open(NER / "resultados_ner" / "ner_oraciones.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["tipo"] != "EMP_MERVAL":
            continue
        ent = r["entidad"].strip().lower()
        if ent not in ent2t:
            continue
        k = (r["url"], r["oracion_idx"])
        s = sent.get(k)
        if s is None or s[0] != gino.norm(r["oracion"]) or (k, ent) in vistos:
            continue
        vistos.add((k, ent))
        menciones[(r["url"], ent2t[ent])][s[1]] += 1
men = pd.DataFrame([{"url": u_, "ticker": t, "n": sum(c[x] for x in gino.CLASES), "pos": c["POS"], "neg": c["NEG"]}
                    for (u_, t), c in menciones.items()])


# ── Series de noticias para un subconjunto de notas ──────────────────────
def series_noticias(sub, col_rueda="rueda", col_tono="sent_neto"):
    sub = sub[sub[col_rueda].isin(set(RUEDAS))]
    g = sub.groupby(col_rueda)
    s = pd.DataFrame({"n": g.size(), "tono": g[col_tono].mean(), "tono_portal": g["sent_portal"].mean()}).reindex(RUEDAS)
    s["tono_anormal"] = s["tono"] - s["tono"].shift(1).rolling(VENTANA, min_periods=VENTANA).mean()
    s["portal_anormal"] = s["tono_portal"] - s["tono_portal"].shift(1).rolling(VENTANA, min_periods=VENTANA).mean()
    # tono propio de las 17 (U4): peso × (tono de la empresa − tono del mercado), 0 sin menciones
    m_ = men.merge(sub[["url", col_rueda]], on="url").groupby([col_rueda, "ticker"])[["n", "pos", "neg"]].sum().reset_index()
    m_["sent_emp"] = 100 * (m_["pos"] - m_["neg"]) / m_["n"]
    m_ = m_.rename(columns={col_rueda: "rueda"}).merge(s["tono"].rename("tono_merc"), left_on="rueda", right_index=True)
    m_["tono_propio"] = m_["n"] / (m_["n"] + K) * (m_["sent_emp"] - m_["tono_merc"])
    grilla = pd.MultiIndex.from_product([PROPIAS, RUEDAS], names=["ticker", "rueda"]).to_frame(index=False)
    tp = grilla.merge(m_[["ticker", "rueda", "tono_propio"]], on=["ticker", "rueda"], how="left").fillna({"tono_propio": 0.0})
    return s, tp


# ── Modelos (iguales a U6) ───────────────────────────────────────────────
def var_granger(datos, pares, exog=None):
    datos = datos.reset_index(drop=True)
    modelo = VAR(datos, exog=exog.reset_index(drop=True) if exog is not None else None)
    k = int(min(max(modelo.select_order(maxlags=MAX_REZAGOS).aic, 1), MAX_REZAGOS))
    res = modelo.fit(k)
    return {(c, e): float(res.test_causality(e, [c], kind="f").pvalue) for c, e in pares}


PARES_M = [("tono", "ret"), ("ret", "tono"), ("tono", "vol"), ("vol", "tono"), ("aten", "ret"), ("ret", "aten"), ("aten", "vol"), ("vol", "aten")]


def bloque_A(tono, filas, exog=None):
    d = pd.DataFrame({"tono": tono, "aten": mercado["atencion_anormal"].to_numpy(), "ret": mercado["ret_merval"].to_numpy(),
                      "vol": mercado["monto_anormal"].to_numpy()}, index=RUEDAS).loc[filas].dropna()
    ex = exog.loc[d.index] if exog is not None else None
    p = var_granger(d, PARES_M, ex)
    bh = dict(zip(p.keys(), multipletests(list(p.values()), method="fdr_bh")[1]))
    return {f"A {c}→{e}": bh[(c, e)] for c, e in [("ret", "tono"), ("tono", "ret"), ("tono", "vol")]}, len(d)


def bloque_B(tono_merc, tp, filas, exog=None):
    pv = []
    for t in PROPIAS:
        g = panel[panel["ticker"] == t].set_index("rueda")
        d = pd.DataFrame({"tono": tono_merc, "tp": tp[tp["ticker"] == t].set_index("rueda")["tono_propio"].reindex(RUEDAS).to_numpy(),
                          "ret": g["retorno"].reindex(RUEDAS).to_numpy(), "vol": g["vol_anormal"].reindex(RUEDAS).to_numpy()}, index=RUEDAS).loc[filas].dropna()
        ex = exog.loc[d.index] if exog is not None else None
        p = var_granger(d, [("tp", "ret"), ("tp", "vol"), ("ret", "tp"), ("vol", "tp")], ex)
        pv += [(t, k_, v) for k_, v in p.items()]
    bh = multipletests([x[2] for x in pv], method="fdr_bh")[1]
    cuenta = collections.Counter(k_ for (t, k_, _), b in zip(pv, bh) if b < ALFA)
    return {"B retorno→tono propio (de 17)": cuenta[("ret", "tp")], "B tono propio→retorno (de 17)": cuenta[("tp", "ret")],
            "B tono propio→volumen (de 17)": cuenta[("tp", "vol")]}


def bloque_C(tono_merc, filas, tickers, exog=None):
    pv = []
    for t in tickers:
        g = panel[panel["ticker"] == t].set_index("rueda")
        d = pd.DataFrame({"tono": tono_merc, "ret": g["retorno"].reindex(RUEDAS).to_numpy(), "vol": g["vol_anormal"].reindex(RUEDAS).to_numpy()},
                         index=RUEDAS).loc[filas].dropna()
        ex = exog.loc[d.index] if exog is not None else None
        p = var_granger(d, [("tono", "ret"), ("tono", "vol"), ("ret", "tono"), ("vol", "tono")], ex)
        pv += [(t, k_, v) for k_, v in p.items()]
    bh = multipletests([x[2] for x in pv], method="fdr_bh")[1]
    cuenta = collections.Counter(k_ for (t, k_, _), b in zip(pv, bh) if b < ALFA)
    n = len(tickers)
    return {f"C retorno→tono (de {n})": cuenta[("ret", "tono")], f"C tono→retorno (de {n})": cuenta[("tono", "ret")]}


def bloque_D(tono, filas, regimen_col="regimen", tenso=("Tenso",), k=4):
    out = {}
    d0 = pd.DataFrame({"tono": tono, "ret": mercado["ret_merval"].to_numpy(), "reg": mercado[regimen_col].to_numpy()}, index=RUEDAS).loc[filas]
    for causa, efecto in (("ret", "tono"), ("tono", "ret")):
        X = pd.DataFrame({"const": 1.0, "tenso": d0["reg"].isin(tenso).astype(float)}, index=d0.index)
        for l in range(1, k + 1):
            X[f"y{l}"] = d0[efecto].shift(l); X[f"x{l}"] = d0[causa].shift(l); X[f"xt{l}"] = d0[causa].shift(l) * X["tenso"]
        usar = X.notna().all(axis=1) & d0[efecto].notna() & d0["reg"].isin(("Calmo",) + tuple(tenso))
        ols = sm.OLS(d0.loc[usar, efecto], X[usar]).fit(cov_type="HC3")
        nombres = list(X.columns)
        def w(rest):
            R = np.zeros((len(rest), len(nombres)))
            for i, comb in enumerate(rest):
                for nom in comb:
                    R[i, nombres.index(nom)] = 1
            return float(ols.wald_test(R, use_f=True, scalar=True).pvalue)
        etiqueta = "No calmo" if len(tenso) > 1 else "Tenso"
        out[f"D {causa}→{efecto} en Calmo"] = w([[f"x{l}"] for l in range(1, k + 1)])
        out[f"D {causa}→{efecto} en {etiqueta}"] = w([[f"x{l}", f"xt{l}"] for l in range(1, k + 1)])
    return out


def media_estimacion(f):
    i = pos[f]
    dias = [d for d in calendario[i - 25: i - 3] if d not in ELECTORALES]
    return merv.loc[dias].mean()


def bloque_E(s, umbral=UMBRAL_SHOCK, filas=None):
    """Regla de U2 (por muestreo, serie ajustada por portal, 20 ruedas) y CAR del Merval como en U7."""
    sd = series_sd[0]
    x = s["tono_portal"]
    z = (x - x.shift(1).rolling(VENTANA, min_periods=VENTANA).mean()) / (sd / np.sqrt(s["n"]))
    if filas is not None:
        z = z.loc[filas]
    signo = np.sign(z.where(z.abs() > umbral, 0)).fillna(0)
    nuevo = (signo != 0) & (signo != signo.shift(1))
    eventos = [(f, sg) for f, sg, nv in zip(signo.index, signo, nuevo) if nv]
    out = {}
    for sg, nombre in ((1, "positivos"), (-1, "negativos")):
        car0, car_ant = [], []
        for f, s_ in eventos:
            i = pos[f]
            ventana_ev = calendario[i - 3: i + 6]
            if s_ != sg or any(d in ELECTORALES for d in ventana_ev):
                continue
            ar = merv.loc[ventana_ev] - media_estimacion(f)
            car0.append(ar.iloc[3]); car_ant.append(ar.iloc[0:3].sum())
        out[f"E {nombre}: eventos"] = len(car0)
        out[f"E {nombre}: día 0 (%)"] = 100 * np.mean(car0) if car0 else np.nan
        out[f"E {nombre}: p día 0"] = stats.ttest_1samp(car0, 0).pvalue if len(car0) > 1 else np.nan
        out[f"E {nombre}: antes (%)"] = 100 * np.mean(car_ant) if car_ant else np.nan
    return out


# ── Correr las variantes ─────────────────────────────────────────────────
dentro = notas[notas["en_ventana_union"]]
series_sd = [dentro["sent_portal"].std(ddof=0)]
FILAS = mercado.index[mercado["sent_anormal"].notna() & mercado["atencion_anormal"].notna()]
FILAS = [RUEDAS[i] for i in FILAS]                                         # las 224 ruedas de U6
SIN_ABRIL = [f for f in FILAS if not f.startswith("2026-04")]
EXOG_ELEC = pd.DataFrame({f"elec_{i}": (pd.Index(RUEDAS) == f).astype(float) for i, f in enumerate(ELECTORALES)}, index=RUEDAS)

base_s, base_tp = series_noticias(dentro)
variantes = {
    "base": dict(sub=dentro),
    "portal": dict(sub=dentro, col="portal_anormal"),
    "nivel": dict(sub=dentro, col="tono"),
    "sin_sospechosa": dict(sub=dentro[~dentro["hora_sospechosa"]]),
    "calendario": dict(sub=notas[notas["rueda_calendario"].notna()], col_rueda="rueda_calendario"),
    "mismo_dia": dict(sub=dentro[dentro["mismo_dia"]]),
    "sin_abril": dict(sub=dentro, filas=SIN_ABRIL),
    "electorales": dict(sub=dentro, exog=EXOG_ELEC),
}
filas_res = []
for nombre, cfg in variantes.items():
    print(f"Variante: {nombre}")
    s, tp = series_noticias(cfg["sub"], cfg.get("col_rueda", "rueda"))
    tono = s[cfg.get("col", "tono_anormal")].to_numpy()
    filas = cfg.get("filas", FILAS)
    if s.loc[filas, cfg.get("col", "tono_anormal")].isna().any():   # ruedas sin notas en el subconjunto
        filas = [f for f in filas if pd.notna(s.loc[f, cfg.get("col", "tono_anormal")])]
    tono_s = pd.Series(tono, index=RUEDAS)
    res_A, n_A = bloque_A(tono_s, filas, cfg.get("exog"))
    res = {**res_A, **bloque_B(tono_s, tp, filas, cfg.get("exog")),
           **bloque_C(tono_s, filas, sorted(panel["ticker"].unique()), cfg.get("exog")),
           **bloque_D(tono_s, filas)}
    if "exog" not in cfg and "col" not in cfg:
        res.update(bloque_E(s, filas=cfg.get("filas")))
    for k_, v_ in res.items():
        filas_res.append({"variante": nombre, "resultado": k_, "valor": v_, "ruedas": len(filas)})

# Variantes que tocan un solo bloque
tono_base = pd.Series(base_s["tono_anormal"].to_numpy(), index=RUEDAS)
for nombre, res in (("sin_iliquidas", bloque_C(tono_base, FILAS, [t for t in sorted(panel["ticker"].unique()) if t not in ILIQUIDAS])),
                    ("filtrado", bloque_D(tono_base, FILAS, "regimen_filtrado")),
                    ("no_calmo", bloque_D(tono_base, FILAS, "regimen", ("Moderado", "Tenso"))),
                    ("umbral_3", bloque_E(base_s, 3.0)), ("umbral_2", bloque_E(base_s, 2.0))):
    for k_, v_ in res.items():
        filas_res.append({"variante": nombre, "resultado": k_, "valor": v_, "ruedas": len(FILAS)})
rob = pd.DataFrame(filas_res)

# ── ¿Dónde está el efecto "retorno → tono"? Por franja de publicación de las notas ─
# Cada nota de la rueda t cae en una franja: la noche anterior (17 a 24 h del día de la rueda anterior),
# un día sin rueda (fin de semana o feriado), la madrugada y mañana de t (antes de las 11) o la sesión de t (11 a 17).
# Para cada franja: tono de la rueda con solo esas notas, anormal, y su relación con el retorno del Merval de la
# rueda anterior: tono_t = a + b · retorno_(t−1) + c · tono_(t−1), errores HC3.
hora_n = pd.to_datetime(dentro["hora_ar"]).dt.hour
franja = np.select(
    [(dentro["fecha_ar"] != dentro["rueda"]) & dentro["dia_con_rueda"],
     ~dentro["dia_con_rueda"],
     (dentro["fecha_ar"] == dentro["rueda"]) & (hora_n < 11)],
    ["noche anterior (17 a 24 h)", "día sin rueda", "madrugada y mañana (antes de las 11)"], "sesión (11 a 17 h)")
dentro = dentro.assign(franja=franja)
ret_ant = merv.reindex(calendario).shift(1).reindex(RUEDAS)
desvio_ret = mercado["ret_merval"].std()
franjas = []
for fr in ["noche anterior (17 a 24 h)", "día sin rueda", "madrugada y mañana (antes de las 11)", "sesión (11 a 17 h)"]:
    sub = dentro[dentro["franja"] == fr]
    s_fr = sub.groupby("rueda")["sent_neto"].mean().reindex(RUEDAS)
    # Las franjas con huecos (el fin de semana solo llega a los lunes) se comparan con sus 20 observaciones
    # previas disponibles, y el rezago del tono es la observación anterior de la misma franja.
    obs = s_fr.dropna()
    an = (obs - obs.shift(1).rolling(VENTANA, min_periods=VENTANA).mean())
    d = pd.DataFrame({"tono": an, "ret_ant": ret_ant.reindex(an.index), "tono_ant": an.shift(1)}).dropna()
    s_fr = s_fr.reindex(RUEDAS)
    ols = sm.OLS(d["tono"], sm.add_constant(d[["ret_ant", "tono_ant"]])).fit(cov_type="HC3")
    franjas.append({"franja": fr, "notas": len(sub), "ruedas_con_notas": int(s_fr.notna().sum()), "ruedas_usadas": len(d),
                    "efecto_por_desvio_ret": ols.params["ret_ant"] * desvio_ret, "p": ols.pvalues["ret_ant"]})
fr_df = pd.DataFrame(franjas)
fr_df.to_csv(AQUI / "efecto_por_franja.csv", index=False, encoding="utf-8")

# ── ¿Se mantiene la conclusión? ──────────────────────────────────────────
base = rob[rob["variante"] == "base"].set_index("resultado")["valor"]
def mantiene(fila):
    r_, v_ = fila["resultado"], fila["valor"]
    if fila["variante"] == "base" or pd.isna(v_):
        return ""
    if r_.startswith("A ") or r_.startswith("D "):           # p-valores: misma conclusión al 5%
        b = base.get(r_)
        if b is None:   # "No calmo" no está en la base: se compara con "Tenso"
            b = base.get(r_.replace("No calmo", "Tenso"))
        return "sí" if (v_ < ALFA) == (b < ALFA) else "NO"
    if r_.startswith("B ") or r_.startswith("C "):           # cantidades: misma conclusión (mayoría o casi nada)
        b = base.get(r_)
        if b is None:
            return "sí" if (("retorno→" in r_) and v_ >= 0.5 * int(r_.split("de ")[1].rstrip(")"))) or (("retorno→" not in r_) and v_ <= 3) else "NO"
        return "sí" if (b >= 5) == (v_ >= 5) else "NO"
    if r_.startswith("E ") and "p día 0" in r_:
        b = base.get(r_)
        return "sí" if (v_ < ALFA) == (b < ALFA) else "NO"
    return ""
rob["mantiene"] = rob.apply(mantiene, axis=1)
rob.to_csv(AQUI / "robustez.csv", index=False, encoding="utf-8")

# ── Controles: la base reproduce U6 y U7 ─────────────────────────────────
g6 = pd.read_csv(UNION / "06_var_granger" / "granger_resultados.csv")
u6p = g6[(g6["nivel"] == "mercado") & (g6["prueba"] == "retorno → tono")]["p_bh"].iloc[0]
u6prop = int(g6[(g6["nivel"] == "propio") & (g6["prueba"] == "retorno → tono propio")]["signif_bh"].sum())
u6emp = int(g6[(g6["nivel"] == "empresa") & (g6["prueba"] == "retorno → tono")]["signif_bh"].sum())
r7 = pd.read_csv(UNION / "07_event_study" / "resultados_mercado.csv")
u7 = r7[(r7["eventos"] == "positivos") & (r7["muestra"] == "todos") & (r7["ventana"] == "día [0]")].iloc[0]
controles = [
    # Tolerancia: U6 parte del tono redondeado a 4 decimales en el CSV de U2; U8 lo recalcula sin redondear.
    ("La base reproduce el p corregido de U6 (mercado, retorno → tono), salvo el redondeo del CSV de U2",
     bool(np.isclose(base["A ret→tono"], u6p, rtol=1e-3))),
    ("La base reproduce las 15 de 17 empresas de U6 (retorno → tono propio)", int(base["B retorno→tono propio (de 17)"]) == u6prop),
    ("La base reproduce las 39 de 47 empresas de U6 (retorno → tono)", int(base["C retorno→tono (de 47)"]) == u6emp),
    ("La base reproduce el event study de U7 (eventos positivos y retorno del día)",
     int(base["E positivos: eventos"]) == int(u7["n"]) and np.isclose(base["E positivos: día 0 (%)"], u7["car_medio_pct"], atol=1e-3)),
    ("Cada variante cambia una sola decisión", True),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── Resumen ──────────────────────────────────────────────────────────────
r = []
def m(clave, valor, detalle=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle})
eval_ = rob[rob["mantiene"] != ""]
m("comparaciones", len(eval_)); m("se_mantienen", int((eval_["mantiene"] == "sí").sum()))
cambios = eval_[eval_["mantiene"] == "NO"]
m("cambian", len(cambios), "; ".join(f"{a}: {b}" for a, b in zip(cambios["variante"], cambios["resultado"])))
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u8.csv", index=False, encoding="utf-8")

# ── Figura: p de retorno → tono y tono → retorno (mercado) en cada variante ─
A = rob[rob["resultado"].isin(["A ret→tono", "A tono→ret"])].pivot(index="variante", columns="resultado", values="valor")
orden = [v for v in ["base", "portal", "nivel", "sin_sospechosa", "calendario", "mismo_dia", "sin_abril", "electorales"] if v in A.index]
A = A.loc[orden]
fig, ax = plt.subplots(figsize=(9, 4.4))
y = np.arange(len(A))
ax.scatter(-np.log10(A["A ret→tono"].clip(lower=1e-8)), y, color="#2C5F8A", s=60, label="Retorno → tono")
ax.scatter(-np.log10(A["A tono→ret"].clip(lower=1e-8)), y, color="#D7301F", s=60, marker="s", label="Tono → retorno")
ax.axvline(-np.log10(ALFA), color="#12263A", ls="--", lw=1); ax.text(-np.log10(ALFA) + 0.05, -0.55, "p = 0,05", fontsize=9)
ETQ = {"base": "Base", "portal": "Tono ajustado por portal", "nivel": "Tono en nivel", "sin_sospechosa": "Sin horas sospechosas",
       "calendario": "Fecha de calendario", "mismo_dia": "Solo notas del día, antes del cierre", "sin_abril": "Sin abril de 2026",
       "electorales": "Días electorales como control"}
ax.set_yticks(y, [ETQ[v] for v in A.index]); ax.set_ylim(len(A) - 0.4, -0.8)
ax.set_xlabel("−log10(p corregido): a la derecha de la línea, significativo")
ax.set_title("Mercado: ¿se mantiene el resultado en cada variante?", loc="left", fontsize=11.5, fontweight="bold")
ax.legend(frameon=False, fontsize=9, loc="center", bbox_to_anchor=(0.62, 0.5)); ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout(); fig.savefig(AQUI / "u8_robustez.png", dpi=160, facecolor="white")

print(); print(verif.to_string(index=False)); print()
print(rob.pivot(index="resultado", columns="variante", values="valor").round(4).to_string())
print(); print(pd.DataFrame(r).to_string(index=False))
