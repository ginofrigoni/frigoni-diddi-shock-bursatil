"""
U7b · Event study del shock de CANTIDAD de noticias — tesis version 3.0 (Unión)

El plan de trabajo (4.4) define el shock informativo como un aumento anormal de la cantidad de noticias: z-score de
la cantidad del día contra la media móvil de los 30 días previos, por encima de un umbral. U7 usó las ruedas de tono
extremo; este paso usa esa definición. La especificación se fijó antes de ver los resultados (especificacion_previa.md),
con un cambio posterior documentado allí:

  · Versión original: cantidad de la rueda. Marcaba casi solo lunes y post-feriados (la rueda junta las notas de varios
    días por la regla de las 17:00). Se informa como "especificación original".
  · Versión principal (cambio posterior 1): cantidad por día de calendario = cantidad de la rueda / días que cubre.
  · Prueba pre-apertura (agregado posterior 2): solo las notas publicadas con el mercado cerrado (criterio de U6b) y,
    como medida central, el salto de apertura: el único precio que se forma después de esas notas y antes de las de la sesión.

Mercado: notas de la rueda → Merval con modelo de media constante y monto anormal. Empresas (las 17 con tono propio):
artículos que mencionan a la empresa, con al menos 3 en la rueda → modelo de mercado por acción y volumen anormal.
z = (cantidad − media de las 30 ruedas previas) / su desvío, con al menos 20 previas; z > 2; ruedas seguidas = un evento.
Un shock de cantidad no tiene signo: se mide el tamaño del movimiento (|retorno anormal| y |salto de apertura anormal|),
el volumen anormal y el CAR. Significancia contra fechas al azar (5.000 sorteos) con Benjamini-Hochberg por familia.

Solo lee. Entradas: U1 (nota_a_rueda.csv), U4 (datasets), U6b (serie_preapertura.csv), el cruce NER-sentimiento de
Lado Noticias y los precios (apertura y cierre) y el Merval de Lado Bursatil.
Uso:  python shock_volumen_noticias.py
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
from scipy import stats
from statsmodels.stats.multitest import multipletests

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
csv.field_size_limit(10 ** 9)

AQUI = Path(__file__).parent
UNION = AQUI.parent
RAIZ = UNION.parent
BURSATIL = RAIZ / "Lado Bursatil"
NER = RAIZ / "Lado Noticias" / "ner_entidades"
sys.path.insert(0, str(NER))
import cruce_ner_sentimiento as gino   # noqa: E402

EST_INI, EST_FIN = -25, -4          # ventana de estimación (igual que U7)
EV_INI, EV_FIN = -3, 5              # ventana del evento
VENTANA_Z, MIN_PREVIAS = 30, 20     # media móvil de los 30 días previos (plan, 4.4)
UMBRAL, UMBRAL_ROBUSTO = 2.0, 2.5
MIN_ARTICULOS = 3                   # empresas: un solo artículo no es un shock
N_SORTEOS = 5000
SEMILLA = 42
ELECTORALES = ["2025-09-08", "2025-10-27"]
VENTANAS = {"antes [−3, −1]": (-3, -1), "día [0]": (0, 0), "después [+1, +5]": (1, 5)}
MEDIDAS = ["abs_ra_dia"] + [f"vol_{k}" for k in VENTANAS] + [f"car_{k}" for k in VENTANAS]
MEDIDAS_PRE = ["abs_salto", "abs_ra_dia", "vol_día [0]"]
NOMBRE_MEDIDA = {"abs_ra_dia": "|retorno anormal| del día [0]", "abs_salto": "|salto de apertura anormal|",
                 **{f"vol_{k}": f"volumen anormal {k}" for k in VENTANAS}, **{f"car_{k}": f"CAR {k}" for k in VENTANAS}}
EN_VALOR_ABSOLUTO = ("abs_ra_dia", "abs_salto")   # se comparan contra el promedio de un día cualquiera, no contra 0

# ── Datos ────────────────────────────────────────────────────────────────
vix = pd.read_csv(BURSATIL / "03_vix_argentino" / "vix_arg.csv")
merv = vix.set_index("fecha")["retorno_diario"]
calendario = list(merv.index)
pos = {f: i for i, f in enumerate(calendario)}
mercado = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_mercado.csv").set_index("rueda")
panel = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_panel.csv")
precios = pd.read_csv(BURSATIL / "01_scraping_acciones" / "precios_diarios_47_acciones.csv").sort_values(["ticker", "Date"])
cierre_ant = precios.groupby("ticker")["Close"].shift(1)
precios["retorno"] = precios["Close"] / cierre_ant - 1
precios["salto"] = precios["Open"] / cierre_ant - 1
ret_acc = precios.pivot(index="Date", columns="ticker", values="retorno").reindex(calendario)
salto_acc = precios.pivot(index="Date", columns="ticker", values="salto").reindex(calendario)
salto_merc = salto_acc.mean(axis=1)                 # no hay apertura del Merval: promedio de las 47 (igual que U6b)
ruedas_union = list(mercado.index)
dias = mercado["dias_cubiertos"]
propias = sorted(panel.loc[panel["sentimiento_propio"] == 1, "ticker"].unique())
paneles = {t: panel[panel["ticker"] == t].set_index("rueda") for t in propias}

# ── Notas pre-apertura (mismo criterio que U6b) ──────────────────────────
pre_merc = pd.read_csv(UNION / "06b_noticias_preapertura" / "serie_preapertura.csv").set_index("rueda")["n_notas_pre"].reindex(ruedas_union).fillna(0)
nr = pd.read_csv(UNION / "01_alineacion_noticias_ruedas" / "nota_a_rueda.csv")
nr = nr[nr["en_ventana_union"]].copy()
hora = pd.to_datetime(nr["hora_ar"])
en_sesion = (nr["fecha_ar"] == nr["rueda"]) & (hora.dt.hour >= 11) & (hora.dt.hour < 17)
pre = nr[~en_sesion & ~nr["hora_sospechosa"]]
art = pd.read_csv(RAIZ / "Lado Noticias" / "sentimiento_finbert" / "finetuned_articulos.csv", usecols=["url"])
pre = pre[pre["url"].isin(set(art["url"]))]
urls_pre, rueda_de = set(pre["url"]), dict(zip(pre["url"], pre["rueda"]))
entidad = {t.replace(".BA", "").lower(): t for t in propias}
sent = {}
with open(RAIZ / "Lado Noticias" / "sentimiento_finbert" / "beto_oraciones_finetuned.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["url"] in urls_pre:
            sent[(r["url"], r["or_idx"])] = gino.norm(r["oracion"])
articulos_pre = collections.defaultdict(set)      # (rueda, ticker) → urls pre-apertura que mencionan a la empresa
with open(NER / "resultados_ner" / "ner_oraciones.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        if r["url"] not in urls_pre or r["tipo"] != "EMP_MERVAL":
            continue
        ent = r["entidad"].strip().lower()
        if ent in entidad and sent.get((r["url"], r["oracion_idx"])) == gino.norm(r["oracion"]):
            articulos_pre[(rueda_de[r["url"]], entidad[ent])].add(r["url"])


def ventana(fecha, a, b):
    i = pos[fecha]
    return calendario[i + a: i + b + 1] if i + a >= 0 and i + b < len(calendario) else None


def con_eleccion(fecha):
    return any(d in ELECTORALES for d in ventana(fecha, EV_INI, EV_FIN))


def completa(fecha):
    return bool(ventana(fecha, EST_INI, EST_FIN)) and bool(ventana(fecha, EV_INI, EV_FIN))


def estimacion(fecha):
    return [d for d in ventana(fecha, EST_INI, EST_FIN) if d not in ELECTORALES]


def zscore(cantidad, log=False):
    """z de la cantidad contra las 30 ruedas PREVIAS (shift: la propia rueda no entra en su referencia)."""
    x = np.log1p(cantidad) if log else cantidad.astype(float)
    previas = x.shift(1).rolling(VENTANA_Z, min_periods=MIN_PREVIAS)
    media, desvio = previas.mean(), previas.std()
    return ((x - media) / desvio).where(desvio > 0)


def primeras(marca):
    """Ruedas seguidas con shock = un evento; la rueda 0 es la primera."""
    marca = marca.fillna(False).astype(bool)
    return list(marca.index[marca & ~marca.shift(1, fill_value=False)])


def medidas_mercado(f):
    ar = merv.loc[ventana(f, EV_INI, EV_FIN)] - merv.loc[estimacion(f)].mean()
    fila = {"abs_ra_dia": abs(ar.iloc[-EV_INI]), "abs_salto": abs(salto_merc[f] - salto_merc.loc[estimacion(f)].mean()),
            "ar_diario": list(ar.values)}
    for k, (a, b) in VENTANAS.items():
        fila[f"car_{k}"] = ar.iloc[a - EV_INI: b - EV_INI + 1].sum()
        fila[f"vol_{k}"] = mercado.reindex(ventana(f, a, b))["monto_anormal"].mean()
    return fila


def medidas_empresa(t, f):
    est = estimacion(f)
    y, x = ret_acc.loc[est, t], merv.loc[est]
    ok = y.notna() & x.notna()
    if ok.sum() < 10:
        return None
    beta, alfa = np.polyfit(x[ok], y[ok], 1)
    ev = ventana(f, EV_INI, EV_FIN)
    ar = ret_acc.loc[ev, t] - (alfa + beta * merv.loc[ev])
    if pd.isna(ar.iloc[-EV_INI]):
        return None
    g = paneles[t]
    fila = {"abs_ra_dia": abs(ar.iloc[-EV_INI]), "abs_salto": abs(salto_acc.loc[f, t] - salto_merc[f]), "beta": beta}
    for k, (a, b) in VENTANAS.items():
        fila[f"car_{k}"] = ar.iloc[a - EV_INI: b - EV_INI + 1].sum()
        en_panel = [d for d in ventana(f, a, b) if d in g.index]
        fila[f"vol_{k}"] = g.loc[en_panel, "vol_anormal"].mean() if en_panel else np.nan
    return fila


# ── Cantidades: original (por rueda), principal (por día de calendario) y pre-apertura ──
art_emp = {t: paneles[t]["n_articulos_empresa"].reindex(ruedas_union).fillna(0) for t in propias}
art_emp_pre = {t: pd.Series([len(articulos_pre.get((r, t), ())) for r in ruedas_union], index=ruedas_union, dtype=float) for t in propias}
CANTIDADES = {
    "original": (mercado["n_notas"], {t: (art_emp[t], art_emp[t]) for t in propias}),
    "principal": (mercado["n_notas"] / dias, {t: (art_emp[t] / dias, art_emp[t]) for t in propias}),
    "pre-apertura": (pre_merc / dias, {t: (art_emp_pre[t] / dias, art_emp_pre[t]) for t in propias}),
}

# ── Fechas al azar (mismo filtro que los eventos: ventanas completas, sin elección) ──
validas = [f for f in ruedas_union if completa(f) and not con_eleccion(f)]
azar_m = pd.DataFrame({f: medidas_mercado(f) for f in validas}).T.drop(columns="ar_diario").astype(float)
pares = {(t, f): medidas_empresa(t, f) for t in propias for f in validas}
azar_e = pd.DataFrame({k: v for k, v in pares.items() if v is not None}).T.astype(float)
rng = np.random.default_rng(SEMILLA)


def p_azar(valores, pool):
    valores = pd.Series(valores, dtype=float).dropna()
    pool = pool.dropna().to_numpy()
    n = len(valores)
    if n == 0 or n > len(pool):
        return np.nan
    medias = np.array([pool[rng.choice(len(pool), n, replace=False)].mean() for _ in range(N_SORTEOS)])
    centro = medias.mean()
    return float((np.abs(medias - centro) >= abs(valores.mean() - centro)).mean())


def resumir(nivel, ev, pool, medidas=MEDIDAS):
    filas = []
    for med in medidas:
        v = ev[med].dropna() if len(ev) else pd.Series(dtype=float)
        n = len(v)
        ref = pool[med].mean()
        base = ref if med in EN_VALOR_ABSOLUTO else 0
        mayores = int((v > base).sum())
        filas.append({"nivel": nivel, "medida": NOMBRE_MEDIDA[med], "clave": med, "n": n,
                      "promedio_eventos": v.mean() if n else np.nan, "promedio_dia_cualquiera": ref, "por_encima": mayores,
                      "p_t": stats.ttest_1samp(v - base, 0).pvalue if n > 1 else np.nan,
                      "p_signo": stats.binomtest(mayores, n, 0.5).pvalue if n else np.nan, "p_azar": p_azar(v, pool[med])})
    return filas


def con_bh(filas):
    tabla = pd.DataFrame(filas)
    ok = tabla["p_azar"].notna()
    tabla["p_bh"] = np.nan
    tabla.loc[ok, "p_bh"] = multipletests(tabla.loc[ok, "p_azar"], method="fdr_bh")[1]
    tabla["significativo_bh"] = tabla["p_bh"] < 0.05
    return tabla


# ── Eventos ──────────────────────────────────────────────────────────────
def eventos_mercado(version, umbral=UMBRAL, log=False, incluir_eleccion=False):
    cantidad = CANTIDADES[version][0]
    z = zscore(cantidad, log)
    filas = [{"rueda": f, "cantidad": cantidad[f], "dias_cubiertos": int(dias[f]), "z": z[f], "tono_anormal": mercado.loc[f, "sent_anormal"],
              "ventana_con_eleccion": con_eleccion(f), **medidas_mercado(f)} for f in primeras(z > umbral) if completa(f)]
    ev = pd.DataFrame(filas)
    return ev if incluir_eleccion or ev.empty else ev[~ev["ventana_con_eleccion"]]


def eventos_empresa(version, umbral=UMBRAL, log=False, incluir_eleccion=False):
    filas = []
    for t in propias:
        cantidad, en_rueda = CANTIDADES[version][1][t]
        z = zscore(cantidad, log)
        ultimo = -99
        for f in primeras((z > umbral) & (en_rueda >= MIN_ARTICULOS)):
            if not completa(f) or (con_eleccion(f) and not incluir_eleccion):
                continue
            if pos[f] - ultimo <= EV_FIN - EV_INI:      # solapado con el evento anterior de la misma empresa
                continue
            m = medidas_empresa(t, f)
            if m is None:
                continue
            ultimo = pos[f]
            filas.append({"ticker": t, "rueda": f, "articulos": int(en_rueda[f]), "dias_cubiertos": int(dias[f]), "z": z[f],
                          "tono_propio": paneles[t].loc[f, "tono_propio"], "ventana_con_eleccion": con_eleccion(f), **m})
    return pd.DataFrame(filas)


ev = {v: (eventos_mercado(v, incluir_eleccion=True), eventos_empresa(v)) for v in CANTIDADES}
for v, (em, ee) in ev.items():
    sufijo = {"principal": "", "original": "_original", "pre-apertura": "_preapertura"}[v]
    em.drop(columns="ar_diario").round(5).to_csv(AQUI / f"eventos_mercado{sufijo}.csv", index=False, encoding="utf-8")
    ee.round(5).to_csv(AQUI / f"eventos_empresa{sufijo}.csv", index=False, encoding="utf-8")
ev_m_todos, ev_e = ev["principal"]
ev_m = ev_m_todos[~ev_m_todos["ventana_con_eleccion"]]

# ── Resultados: principal y original (14 pruebas cada una) y pre-apertura (6) ──
tablas = []
for v in ("principal", "original"):
    em, ee = ev[v]
    em = em[~em["ventana_con_eleccion"]]
    t = con_bh(resumir("mercado", em, azar_m) + resumir("empresas", ee, azar_e))
    t.insert(0, "version", "principal (por día de calendario)" if v == "principal" else "especificación original (por rueda)")
    tablas.append(t)
princ = pd.concat(tablas, ignore_index=True)
princ.round(5).to_csv(AQUI / "resultados_principales.csv", index=False, encoding="utf-8")
p_principal = princ[princ["version"].str.startswith("principal")]

em_pre, ee_pre = ev["pre-apertura"]
em_pre = em_pre[~em_pre["ventana_con_eleccion"]]
pre_res = con_bh(resumir("mercado", em_pre, azar_m, MEDIDAS_PRE) + resumir("empresas", ee_pre, azar_e, MEDIDAS_PRE))
pre_res.round(5).to_csv(AQUI / "resultados_preapertura.csv", index=False, encoding="utf-8")

# Sensibilidad descriptiva (agregado 3): el salto de apertura del mercado sacando un evento por vez.
sens = []
for f in em_pre["rueda"]:
    resto = em_pre[em_pre["rueda"] != f]["abs_salto"]
    sens.append({"sin_evento": f, "n": len(resto), "promedio_eventos": resto.mean(), "promedio_dia_cualquiera": azar_m["abs_salto"].mean(),
                 "p_azar": p_azar(resto, azar_m["abs_salto"])})
sens = pd.DataFrame(sens)
sens.round(5).to_csv(AQUI / "sensibilidad_preapertura.csv", index=False, encoding="utf-8")

# Lo que cuenta como evidencia para H1 (especificación): |RA| del día, volumen del día o de después, CAR de después.
CLAVES_H1 = ["abs_ra_dia", "vol_día [0]", "vol_después [+1, +5]", "car_después [+1, +5]"]
apoyo_h1 = p_principal[p_principal["clave"].isin(CLAVES_H1) & p_principal["significativo_bh"]]
solo_antes = p_principal[p_principal["clave"].str.contains("antes") & p_principal["significativo_bh"]]
salto_sig = pre_res[(pre_res["clave"] == "abs_salto") & pre_res["significativo_bh"]]

# ── Secundario (versión principal): por tono de la rueda, y robustez ─────
sec = []
for nivel, e, pool, col in (("mercado", ev_m, azar_m, "tono_anormal"), ("empresas", ev_e, azar_e, "tono_propio")):
    for signo, sel in (("tono > 0", e[col] > 0), ("tono < 0", e[col] < 0)):
        sec += [{"analisis": f"según el tono ({signo})", **x} for x in resumir(nivel, e[sel], pool)]
for nombre, kw in (("umbral z > 2,5", {"umbral": UMBRAL_ROBUSTO}), ("z sobre log(1 + cantidad)", {"log": True}),
                   ("con eventos de ventana electoral", {"incluir_eleccion": True})):
    filas = resumir("mercado", eventos_mercado("principal", **kw), azar_m) + resumir("empresas", eventos_empresa("principal", **kw), azar_e)
    sec += [{"analisis": f"robustez: {nombre}", **x} for x in filas]
pd.DataFrame(sec).round(5).to_csv(AQUI / "resultados_secundarios.csv", index=False, encoding="utf-8")

# ── Controles ────────────────────────────────────────────────────────────
f_ctrl = ruedas_union[60]
x = mercado["n_notas"] / dias
previas = x.loc[ruedas_union[30:60]]
z_manual = (x[f_ctrl] - previas.mean()) / previas.std()
todos_eventos = pd.concat([pd.concat([em, ee]) for em, ee in ev.values()])
controles = [
    ("El z de una rueda usa solo las 30 ruedas previas (recalculado a mano)", bool(np.isclose(z_manual, zscore(x)[f_ctrl]))),
    ("Todos los eventos tienen ventanas de estimación y de evento completas", all(completa(f) for f in todos_eventos["rueda"])),
    ("Ruedas seguidas con shock cuentan como un solo evento (mercado, versión principal)",
     not any((zscore(x) > UMBRAL).shift(1, fill_value=False).loc[ev_m_todos["rueda"]])),
    ("Ningún evento de empresa se solapa con el anterior de la misma empresa",
     all(bool(ee.groupby("ticker")["rueda"].apply(lambda s: (s.map(pos).diff().dropna() > EV_FIN - EV_INI).all()).all())
         for _, ee in ev.values() if len(ee))),
    ("Todos los eventos de empresa tienen al menos 3 artículos en la rueda",
     all(bool((ee["articulos"] >= MIN_ARTICULOS).all()) for _, ee in ev.values() if len(ee))),
    ("Las notas pre-apertura nunca superan a las de la rueda (mercado y cada empresa)",
     bool((pre_merc <= mercado["n_notas"]).all()) and all(bool((art_emp_pre[t] <= art_emp[t]).all()) for t in propias)),
    ("Retornos anormales de fechas al azar promedian cerca de 0 (mercado y empresas)",
     abs(azar_m["car_después [+1, +5]"].mean()) < 0.01 and abs(azar_e["car_después [+1, +5]"].mean()) < 0.01),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── Resumen ──────────────────────────────────────────────────────────────
r = []
def m(clave, valor, detalle=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle})

for v, (em, ee) in ev.items():
    tras = int((em["dias_cubiertos"] > 1).sum()) if len(em) else 0
    m(f"eventos_mercado_{v}", int((~em["ventana_con_eleccion"]).sum()) if len(em) else 0,
      f"{len(em)} en total, {int(em['ventana_con_eleccion'].sum()) if len(em) else 0} con elección en la ventana; {tras} tras un día sin mercado")
    m(f"eventos_empresa_{v}", len(ee), f"{ee['ticker'].nunique() if len(ee) else 0} empresas; {int((ee['dias_cubiertos'] > 1).sum()) if len(ee) else 0} tras un día sin mercado")
m("ruedas_tras_dia_sin_mercado", int((dias > 1).sum()), f"de {len(dias)} ruedas")
m("ruedas_para_sorteo", len(validas)); m("pares_para_sorteo", len(azar_e))
for _, x in princ.iterrows():
    v = "principal" if x["version"].startswith("principal") else "original"
    m(f"{v}_{x['nivel']}_{x['clave']}", round(x["promedio_eventos"], 5),
      f"día cualquiera {x['promedio_dia_cualquiera']:.5f}; azar p={x['p_azar']:.3f}; p BH={x['p_bh']:.3f}; n={x['n']}")
for _, x in pre_res.iterrows():
    m(f"preapertura_{x['nivel']}_{x['clave']}", round(x["promedio_eventos"], 5),
      f"día cualquiera {x['promedio_dia_cualquiera']:.5f}; azar p={x['p_azar']:.3f}; p BH={x['p_bh']:.3f}; n={x['n']}")
m("apoya_h1", int(len(apoyo_h1) > 0), "; ".join(apoyo_h1["nivel"] + ": " + apoyo_h1["medida"]) or "ninguna prueba de H1 significativa tras BH")
m("significativo_solo_antes", len(solo_antes), "; ".join(solo_antes["nivel"] + ": " + solo_antes["medida"]))
m("salto_apertura_significativo", len(salto_sig), "; ".join(salto_sig["nivel"]) or "ninguno")
peor = sens.loc[sens["p_azar"].idxmax()]
m("sensibilidad_salto_mercado", round(peor["promedio_eventos"], 5),
  f"sin {peor['sin_evento']}: azar p={peor['p_azar']:.3f}; el máximo p sacando un evento por vez")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u7b.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
dias_ev = list(range(EV_INI, EV_FIN + 1))
fig, axs = plt.subplots(1, 3, figsize=(15, 4.4))
ax = axs[0]
n = len(ev_m)
if n:
    sorteos = np.array([100 * np.cumsum(np.mean(np.vstack([medidas_mercado(f)["ar_diario"] for f in rng.choice(validas, n, replace=False)]), axis=0))
                        for _ in range(1000)])
    ax.fill_between(dias_ev, np.percentile(sorteos, 2.5, axis=0), np.percentile(sorteos, 97.5, axis=0), color="#BBBBBB", alpha=0.45,
                    label="95% de fechas al azar")
    ax.plot(dias_ev, 100 * np.cumsum(np.mean(np.vstack(ev_m["ar_diario"].to_list()), axis=0)), color="#2C5F8A", lw=2.2, marker="o",
            label=f"Shocks de cantidad de notas (n={n})")
ax.axvline(0, color="#12263A", lw=1, ls="--"); ax.axhline(0, color="#999", lw=0.7)
ax.set_xticks(dias_ev); ax.set_xlabel("Ruedas respecto del shock"); ax.set_ylabel("Retorno anormal acumulado del Merval (%)")
ax.set_title("A. Mercado: retorno alrededor del shock", loc="left", fontsize=11, fontweight="bold")
ax.legend(frameon=False, fontsize=8.5, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)


def barras(ax, tabla, clave, titulo, ylabel):
    filas = tabla[tabla["clave"] == clave].set_index("nivel")
    xs = np.arange(2)
    ref = [100 * filas.loc[k, "promedio_dia_cualquiera"] for k in ("mercado", "empresas")]
    obs = [100 * filas.loc[k, "promedio_eventos"] for k in ("mercado", "empresas")]
    ax.bar(xs - 0.18, ref, 0.36, color="#BBBBBB", label="Día cualquiera")
    ax.bar(xs + 0.18, obs, 0.36, color="#2C5F8A", label="Día del shock")
    for i, k in enumerate(("mercado", "empresas")):
        if pd.notna(obs[i]):
            ax.text(i + 0.18, obs[i], f"p BH = {filas.loc[k, 'p_bh']:.3f}", ha="center", va="bottom", fontsize=8.5)
    ax.set_xticks(xs, [f"{k.capitalize()}\n(n={int(filas.loc[k, 'n'])})" for k in ("mercado", "empresas")])
    ax.set_ylabel(ylabel); ax.legend(frameon=False, fontsize=8.5)
    ax.set_title(titulo, loc="left", fontsize=11, fontweight="bold"); ax.spines[["top", "right"]].set_visible(False)


barras(axs[1], p_principal, "abs_ra_dia", "B. Tamaño del movimiento del día", "|retorno anormal| del día [0] (%)")
barras(axs[2], pre_res, "abs_salto", "C. Notas pre-apertura: salto de apertura", "|salto de apertura anormal| (%)")
fig.tight_layout(); fig.savefig(AQUI / "u7b_shock_volumen.png", dpi=160, facecolor="white")

for _, x in pd.DataFrame(r).iterrows():
    print(f"{x['metrica']:48s} {str(x['valor']):10s} {str(x['detalle'])[:120]}")
print(); print(verif.to_string(index=False))
