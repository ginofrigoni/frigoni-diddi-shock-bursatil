"""
Diagnóstico previo a la unión — tesis version 3.0

Cruza el lado bursátil con el lado de noticias SIN modificar ninguno de los dos
y mide lo que condiciona la unión: ventana común, alineación de cada noticia
con una rueda de BYMA, shocks que caen en días sin mercado, composición de
fuentes, cobertura del sentimiento por empresa y días por régimen.

Solo lee. Escribe en esta carpeta:
  diagnostico_resumen.csv      una fila por métrica (la usa el PDF del pipeline)
  cobertura_por_ticker.csv     ruedas con noticias de cada una de las 47 acciones
  shocks_serie_actual.csv      los shocks de la serie de noticias y si cayeron en rueda
  fuentes_por_mes.csv          artículos por portal y mes

Uso:  python diagnostico_union.py
"""

import json
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
RAIZ = AQUI.parent.parent
BURSATIL = RAIZ / "Lado Bursatil"
NOTICIAS = RAIZ / "Lado Noticias"

CIERRE_BYMA = 17          # hora de cierre de la rueda (hora argentina)
MIN_RUEDAS_TICKER = 90    # ruedas con noticias para que un ticker tenga VAR propio (decisión del 24/10)
MIN_DIAS_REGIMEN = 20     # mismo umbral que el VAR por régimen

metricas = []
def m(clave, valor, detalle=""):
    metricas.append({"metrica": clave, "valor": valor, "detalle": detalle})


# ── 1. Calendario de ruedas (lado bursátil) ──────────────────────────────
vix = pd.read_csv(BURSATIL / "03_vix_argentino" / "vix_arg.csv", parse_dates=["fecha"])
ruedas = pd.DatetimeIndex(vix["fecha"])
m("ruedas_ventana_bursatil", len(ruedas), f"{ruedas.min().date()} a {ruedas.max().date()}")

# ── 2. Corpus con hora de publicación ────────────────────────────────────
filas = []
for f in sorted((NOTICIAS / "noticias" / "resultados").glob("*.jsonl")):
    for linea in open(f, encoding="utf-8"):
        if linea.strip():
            a = json.loads(linea)
            filas.append((a["url"], a.get("fecha_publicacion") or "", f.stem))
corpus = pd.DataFrame(filas, columns=["url", "fecha_publicacion", "archivo"]).drop_duplicates("url")
m("articulos_corpus", len(corpus))

# Clarín, Infobae y La Nación publican la hora en UTC ("Z"); el resto en -03:00.
ts = pd.to_datetime(corpus["fecha_publicacion"], utc=True, format="mixed")
ts_ar = ts.dt.tz_convert("America/Argentina/Buenos_Aires").dt.tz_localize(None)
fecha_texto = pd.to_datetime(corpus["fecha_publicacion"].str[:10])
m("articulos_fecha_cambia_por_huso", int((fecha_texto != ts_ar.dt.normalize()).sum()),
  "fecha tomada de los primeros 10 caracteres vs. fecha en hora argentina")
m("pct_publicadas_tras_cierre", round(100 * (ts_ar.dt.hour >= CIERRE_BYMA).mean(), 1),
  f"publicadas a las {CIERRE_BYMA}:00 o más tarde")

# Rueda a la que llega cada noticia: si sale después del cierre, a la rueda siguiente;
# si sale un fin de semana o feriado, a la primera rueda posterior.
base = ts_ar.dt.normalize() + pd.to_timedelta((ts_ar.dt.hour >= CIERRE_BYMA).astype(int), unit="D")
pos = ruedas.searchsorted(base)
dentro = pos < len(ruedas)
corpus["rueda"] = pd.NaT
corpus.loc[dentro, "rueda"] = ruedas[pos[dentro]]
mueven = (corpus.loc[dentro, "rueda"] != ts_ar[dentro].dt.normalize()).sum()
m("articulos_cambian_de_dia_al_alinear", int(mueven), "fecha de rueda distinta de la fecha calendario")
m("pct_cambian_de_dia_al_alinear", round(100 * mueven / dentro.sum(), 1))

# Horas "por defecto": una misma hora que concentra más del 3% de las notas de una fuente
# (Clarín 07:00/07:08, Ámbito 00:00, TN 05:55...). Esa hora no es la real, así que la regla
# de las 17:00 no la puede usar bien: en U1 se marcan y en U8 se prueba sin ellas.
hora = ts_ar.dt.strftime("%H:%M")
defecto = set()
for archivo, horas in hora.groupby(corpus["archivo"]):
    for h, p in horas.value_counts(normalize=True).items():
        if p > 0.03:
            defecto.add((archivo, h))
corpus["hora_defecto"] = [(a, h) in defecto for a, h in zip(corpus["archivo"], hora)]
m("articulos_hora_por_defecto", int(corpus["hora_defecto"].sum()),
  "; ".join(sorted({f"{a.split('_')[0]} {h}" for a, h in defecto})))
m("pct_hora_por_defecto", round(100 * corpus["hora_defecto"].mean(), 1))

# ── 3. Ventana común ─────────────────────────────────────────────────────
ts_mes = ts_ar.dt.to_period("M")
m("articulos_ene_abr_2025", int((ts_ar < "2025-05-01").sum()), "cobertura casi nula antes de mayo 2025")
desde = pd.Timestamp("2025-05-01")
comun = ruedas[ruedas >= desde]
por_rueda = corpus[corpus["rueda"] >= desde].groupby("rueda").size().reindex(comun, fill_value=0)
m("ruedas_ventana_comun", len(comun), f"{comun.min().date()} a {comun.max().date()}")
m("ruedas_comun_sin_noticias", int((por_rueda == 0).sum()))
m("articulos_por_rueda_min", int(por_rueda.min()))
m("articulos_por_rueda_mediana", int(por_rueda.median()))
m("articulos_por_rueda_max", int(por_rueda.max()))

# ── 4. Shocks de la serie actual (calendario, no ruedas) ─────────────────
serie = pd.read_csv(NOTICIAS / "sentimiento_finbert" / "finetuned_serie_diaria.csv", parse_dates=["fecha"])
sh = serie[serie["shock"] == True].copy()
sh["es_rueda"] = sh["fecha"].isin(ruedas)
sh["tipo"] = sh["shock_pos"].map({True: "positivo", False: "negativo"})
sh[["fecha", "tipo", "n_articulos", "sent_neto", "es_rueda"]].to_csv(AQUI / "shocks_serie_actual.csv", index=False)
m("shocks_serie_actual", len(sh))
m("shocks_en_rueda", int(sh["es_rueda"].sum()))
m("shocks_en_dia_sin_mercado", int((~sh["es_rueda"]).sum()))
m("shocks_sin_mercado_min_articulos", int(sh.loc[~sh["es_rueda"], "n_articulos"].min()))
m("dias_sin_mercado_con_noticias", int((~serie["fecha"].isin(ruedas) & serie["n_articulos"].notna()).sum()))

# ── 5. Composición de fuentes ────────────────────────────────────────────
art = pd.read_csv(NOTICIAS / "sentimiento_finbert" / "finetuned_articulos.csv")
por_fuente = art.groupby("fuente")["sent_neto"].mean()
m("sent_neto_medio_fuente_min", round(por_fuente.min(), 1), por_fuente.idxmin())
m("sent_neto_medio_fuente_max", round(por_fuente.max(), 1), por_fuente.idxmax())
tabla = pd.crosstab(ts_mes, corpus["archivo"])
tabla.index = tabla.index.astype(str)
tabla.to_csv(AQUI / "fuentes_por_mes.csv")
m("iprofesional_mar_2026", int(tabla.loc["2026-03", "iprofesional_sitemap"]))
m("iprofesional_abr_2026", int(tabla.loc["2026-04", "iprofesional_sitemap"]))

# ── 6. Sentimiento por empresa ───────────────────────────────────────────
panel = pd.read_csv(BURSATIL / "01_scraping_acciones" / "panel_acciones_final.csv")
emp = pd.read_csv(NOTICIAS / "ner_entidades" / "resultados_ner" / "ner_sentimiento_diario.csv", parse_dates=["fecha"])
emp = emp[emp["tipo"] == "EMP_MERVAL"]
# Aproximación: la serie por empresa solo trae fecha (sin hora); se cuenta la rueda siguiente
# si la fecha no es rueda. El conteo exacto sale de rehacer el cruce con la hora (paso U3).
pos = ruedas.searchsorted(emp["fecha"])
emp = emp[pos < len(ruedas)].assign(rueda=ruedas[pos[pos < len(ruedas)]])
emp = emp[emp["rueda"] >= desde]
cob = emp.groupby("entidad").agg(ruedas_con_noticias=("rueda", "nunique"), articulos=("n_articulos", "sum"))
panel["entidad"] = panel["ticker"].str.replace(".BA", "", regex=False).str.lower()
cob = panel[["ticker", "empresa", "sector", "oficial", "entidad"]].merge(cob, left_on="entidad", right_index=True, how="left")
cob = cob.fillna({"ruedas_con_noticias": 0, "articulos": 0}).drop(columns="entidad")
cob["pct_ruedas"] = (100 * cob["ruedas_con_noticias"] / len(comun)).round(1)
cob["var_propio"] = cob["ruedas_con_noticias"] >= MIN_RUEDAS_TICKER
cob.sort_values("ruedas_con_noticias", ascending=False).to_csv(AQUI / "cobertura_por_ticker.csv", index=False)
m("tickers_con_var_propio", int(cob["var_propio"].sum()), f"al menos {MIN_RUEDAS_TICKER} ruedas con noticias")
m("tickers_sin_ninguna_mencion", int((cob["ruedas_con_noticias"] == 0).sum()))
m("tickers_menos_de_10_ruedas", int((cob["ruedas_con_noticias"] < 10).sum()))

# ── 7. Regímenes del HMM dentro de la ventana común ──────────────────────
hmm = pd.read_csv(BURSATIL / "06_hmm_regimen_mercado" / "hmm_regimen_mercado.csv", parse_dates=["fecha"])
w = hmm[hmm["fecha"] >= desde]
for reg in ("Calmo", "Moderado", "Tenso"):
    n = int((w["regimen_nombre"] == reg).sum())
    m(f"dias_{reg.lower()}_ventana_comun", n, "alcanza para VAR" if n >= MIN_DIAS_REGIMEN else "NO alcanza para VAR (n<20)")
fuera = hmm[hmm["fecha"] < desde]["regimen_nombre"].value_counts()
m("dias_tenso_perdidos_ene_abr", int(fuera.get("Tenso", 0)), "Tenso de abril 2025 queda fuera de la ventana común")

# ── 8. ¿La regla de shocks se distingue del azar? (serie por rueda) ───────
# Vista previa de U2: sentimiento promedio por rueda (regla de las 17:00) y cuántas ruedas marca
# como shock cada regla, contra lo que marcaría una serie de números al azar (misma regla, 30
# simulaciones, semilla fija). Si la proporción es parecida, la regla no separa evento de ruido.
import numpy as np

d = art.merge(corpus[["url", "rueda"]], on="url")
serie_rueda = d[d["rueda"] >= desde].groupby("rueda")["sent_neto"].mean()
rng = np.random.default_rng(42)


def pct_shocks(x, ventana, umbral, incluye_dia):
    x = pd.Series(np.asarray(x, dtype=float))
    base = x if incluye_dia else x.shift(1)
    media = base.rolling(ventana, min_periods=ventana).mean()
    desvio = base.rolling(ventana, min_periods=ventana).std()
    z = ((x - media) / desvio).dropna()
    return 100 * (z.abs() > umbral).mean()


for ventana, umbral, incluye, nombre in [(7, 1.5, True, "regla_gino"), (7, 2.0, False, "sin_dia_7d_2s"),
                                         (20, 2.0, False, "sin_dia_20d_2s")]:
    datos = pct_shocks(serie_rueda, ventana, umbral, incluye)
    azar = np.mean([pct_shocks(rng.normal(size=3000), ventana, umbral, incluye) for _ in range(30)])
    m(f"shocks_rueda_{nombre}_pct", round(datos, 1), f"azar: {azar:.1f}%")
m("autocorrelacion_sentimiento_rueda", round(serie_rueda.autocorr(1), 2), "rezago de 1 rueda")

pd.DataFrame(metricas).to_csv(AQUI / "diagnostico_resumen.csv", index=False)
print(pd.DataFrame(metricas).to_string(index=False))
