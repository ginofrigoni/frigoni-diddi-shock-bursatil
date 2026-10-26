"""
U4 · Datasets unificados — tesis version 3.0 (Unión)

Junta el lado bursátil con las series de noticias de U2 y U3 en las dos tablas que usan los modelos:

  dataset_mercado.csv  una fila por rueda (244): Merval, VIX, régimen, monto operado, tono de las noticias,
                       atención de los medios, ruedas de tono extremo y marcas de días especiales.
  dataset_panel.csv    una fila por acción y rueda (47 × 244): precio, retorno, volumen y volumen anormal,
                       liquidez, sector, sentimiento propio de la empresa y las variables de mercado.

Definiciones (las mismas del lado bursátil):
  - retorno = variación porcentual del cierre (pct_change), calculada sobre la serie completa desde 2023
    y recién después recortada a la ventana, como en las carpetas 02, 04 y 05;
  - volumen anormal = log(1 + volumen del día) − promedio de log(1 + volumen) de las 20 ruedas previas
    (0 = lo habitual; +0,69 ≈ el doble), también calculado sobre la serie completa (decisión D2);
  - monto operado = cierre × volumen, sumado sobre las 47 acciones (el volumen total en pesos del panel).

Solo lee. Escribe en esta carpeta: dataset_mercado.csv, dataset_panel.csv, diccionario_variables.csv,
descriptivos.csv, resumen_u4.csv, verificaciones.csv y u4_panorama.png.

Uso:  python construir_datasets.py
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

AQUI = Path(__file__).parent
UNION = AQUI.parent
BURSATIL = UNION.parent / "Lado Bursatil"
VENTANA_VOL = 20               # ruedas previas para el volumen anormal (igual que el VIX y la atención)
INICIO = "2025-05-05"
CUATRO_ILIQUIDAS = ["GCDI.BA", "RIGO.BA", "GRIM.BA", "GARO.BA"]   # más días sin operar (carpeta 02, prueba C)
ECO = 20                       # ruedas en que un salto del día electoral sigue dentro de la ventana del VIX

# ── 1. Lado bursátil ─────────────────────────────────────────────────────
precios = pd.read_csv(BURSATIL / "01_scraping_acciones" / "precios_diarios_47_acciones.csv", parse_dates=["Date"])
precios = precios.rename(columns={"Date": "fecha"}).sort_values(["ticker", "fecha"])
g = precios.groupby("ticker")
precios["retorno"] = g["Close"].pct_change()
precios["log_vol"] = np.log1p(precios["Volume"])
precios["vol_anormal"] = precios["log_vol"] - g["log_vol"].transform(
    lambda x: x.shift(1).rolling(VENTANA_VOL, min_periods=VENTANA_VOL).mean())
precios["monto"] = precios["Close"] * precios["Volume"]
precios["sin_operar"] = (precios["Volume"] == 0).astype(int)
precios["precio_quieto"] = (g["Close"].diff() == 0).astype(int)

monto = precios.groupby("fecha")["monto"].sum().rename("monto_operado").to_frame()
monto["log_monto"] = np.log(monto["monto_operado"])
monto["monto_anormal"] = monto["log_monto"] - monto["log_monto"].shift(1).rolling(VENTANA_VOL, min_periods=VENTANA_VOL).mean()

hmm = pd.read_csv(BURSATIL / "06_hmm_regimen_mercado" / "hmm_regimen_mercado.csv", parse_dates=["fecha"])
acciones = pd.read_csv(BURSATIL / "01_scraping_acciones" / "panel_acciones_final.csv")[["ticker", "empresa", "sector", "oficial"]]
liq = pd.read_csv(BURSATIL / "02_clustering_acciones" / "comparacion_grupo_no_degenerado.csv")[["label", "dias_sin_operar", "en_grupo"]]
liq["ticker"] = liq["label"] + ".BA"

# ── 2. Series de noticias (U2 y U3) ──────────────────────────────────────
u2 = pd.read_csv(UNION / "02_sentimiento_por_rueda" / "sentimiento_mercado_rueda.csv", parse_dates=["rueda"])
u3 = pd.read_csv(UNION / "03_sentimiento_por_empresa" / "panel_empresas_rueda.csv", parse_dates=["rueda"])

# ── 3. Dataset de mercado ────────────────────────────────────────────────
m = hmm[hmm["fecha"] >= INICIO][["fecha", "merv_cierre", "retorno_diario", "vix_arg", "regimen_nombre", "regimen_filtrado_nombre",
                                  "prob_suavizada_Tenso", "prob_filtrada_Tenso"]].rename(columns={
    "fecha": "rueda", "retorno_diario": "ret_merval", "regimen_nombre": "regimen", "regimen_filtrado_nombre": "regimen_filtrado",
    "prob_suavizada_Tenso": "prob_tenso", "prob_filtrada_Tenso": "prob_tenso_filtrada"})
m = m.merge(monto[["monto_operado", "monto_anormal"]], left_on="rueda", right_index=True, how="left")
noticias = u2[["rueda", "n_notas", "dias_cubiertos", "atencion_anormal", "sent_neto", "sent_neto_portal", "pct_pos", "pct_neg",
               "pct_neu", "pct_mixto", "z_shock", "shock", "shock_pos", "shock_neg", "evento_id", "dia_electoral"]]
m = m.merge(noticias, on="rueda", how="left")
m = m.sort_values("rueda").reset_index(drop=True)
# Tono anormal (decisión de U5, 24/10): el tono de la rueda comparado con el promedio de las 20 ruedas previas.
# El tono en nivel dio "inconcluso" en el ADF (cambia en ciclos de meses); el tono anormal es estable y usa
# la misma lógica que la atención y el volumen anormales. Es la variable de tono del VAR; el nivel va a robustez.
for col, nuevo in (("sent_neto", "sent_anormal"), ("sent_neto_portal", "sent_portal_anormal")):
    m[nuevo] = m[col] - m[col].shift(1).rolling(VENTANA_VOL, min_periods=VENTANA_VOL).mean()
m["dia_electoral"] = m["dia_electoral"].fillna("")
pos_elec = m.index[m["dia_electoral"] != ""]
m["eco_electoral"] = 0
for i in pos_elec:
    m.loc[i:i + ECO - 1, "eco_electoral"] = 1
m["abril_2026"] = ((m["rueda"] >= "2026-04-01") & (m["rueda"] <= "2026-04-30")).astype(int)
for c in ("shock", "shock_pos", "shock_neg"):
    m[c] = m[c].astype(int)
m = m.sort_values("rueda").reset_index(drop=True)
m_out = m.copy(); m_out["rueda"] = m_out["rueda"].dt.strftime("%Y-%m-%d")
m_out.round(6).to_csv(AQUI / "dataset_mercado.csv", index=False, encoding="utf-8")

# ── 4. Dataset panel (acción × rueda) ────────────────────────────────────
p = precios[precios["fecha"] >= INICIO][["ticker", "fecha", "Close", "retorno", "Volume", "monto", "vol_anormal", "sin_operar", "precio_quieto"]]
p = p.rename(columns={"fecha": "rueda", "Close": "cierre", "Volume": "volumen"})
p = p.merge(acciones, on="ticker").merge(liq[["ticker", "en_grupo"]].rename(columns={"en_grupo": "grupo_baja_liquidez"}), on="ticker")
p["grupo_baja_liquidez"] = p["grupo_baja_liquidez"].astype(int)
p["cuatro_iliquidas"] = p["ticker"].isin(CUATRO_ILIQUIDAS).astype(int)
emp = u3[["ticker", "rueda", "hubo_noticia", "sentimiento_propio", "n_articulos", "n_oraciones", "sent_neto_empresa"]].rename(
    columns={"n_articulos": "n_articulos_empresa", "n_oraciones": "n_oraciones_empresa"})
emp["sentimiento_propio"] = emp["sentimiento_propio"].astype(int)
p = p.merge(emp, on=["ticker", "rueda"], how="left")
de_mercado = ["rueda", "ret_merval", "vix_arg", "regimen", "regimen_filtrado", "prob_tenso", "sent_neto", "sent_neto_portal",
              "sent_anormal", "sent_portal_anormal", "n_notas", "atencion_anormal", "shock", "shock_pos", "shock_neg", "evento_id", "dia_electoral", "eco_electoral", "abril_2026"]
p = p.merge(m[de_mercado], on="rueda", how="left")
orden = ["ticker", "empresa", "sector", "oficial", "grupo_baja_liquidez", "cuatro_iliquidas", "rueda", "cierre", "retorno", "volumen",
         "monto", "vol_anormal", "sin_operar", "precio_quieto", "hubo_noticia", "sentimiento_propio", "n_articulos_empresa",
         "n_oraciones_empresa", "sent_neto_empresa"] + de_mercado[1:]
p = p[orden].sort_values(["ticker", "rueda"]).reset_index(drop=True)

# Tono propio (decisión de U6, 24/10): cuánto mejor o peor se habla de la empresa que del mercado ese día,
# con más peso cuantas más oraciones la mencionan. peso = n / (n + K). Sin noticias de la empresa vale 0.
# K sale de los datos (estimación empírica de Bayes, sobre las 17 empresas con sentimiento propio):
#   varianza de una oración suelta (valores +100 / 0 / −100)  ÷  varianza real del tono relativo entre días.
con = p[(p["sentimiento_propio"] == 1) & (p["hubo_noticia"] == 1)]
relativo = con["sent_neto_empresa"] - con["sent_neto"]
cuenta = pd.read_csv(UNION / "03_sentimiento_por_empresa" / "panel_empresas_rueda.csv", usecols=["ticker", "n_pos", "n_neg", "n_oraciones", "sentimiento_propio"])
cuenta = cuenta[cuenta["sentimiento_propio"]]
pp, pn = cuenta["n_pos"].sum() / cuenta["n_oraciones"].sum(), cuenta["n_neg"].sum() / cuenta["n_oraciones"].sum()
VAR_ORACION = 1e4 * (pp + pn - (pp - pn) ** 2)
VAR_ENTRE_DIAS = relativo.var() - (VAR_ORACION / con["n_oraciones_empresa"]).mean()
K_PESO = VAR_ORACION / VAR_ENTRE_DIAS
peso = p["n_oraciones_empresa"] / (p["n_oraciones_empresa"] + K_PESO)
p["peso_tono_propio"] = peso.round(4)
p["tono_propio"] = np.where(p["hubo_noticia"] == 1, peso * (p["sent_neto_empresa"] - p["sent_neto"]), 0.0)
p_out = p.copy(); p_out["rueda"] = p_out["rueda"].dt.strftime("%Y-%m-%d")
p_out.round(6).to_csv(AQUI / "dataset_panel.csv", index=False, encoding="utf-8")

# ── 5. Diccionario de variables ──────────────────────────────────────────
D = [
    # (variable, dataset, descripción, unidad, origen)
    ("rueda", "ambos", "Día de bolsa (BYMA)", "fecha", "Lado Bursatil/03_vix_argentino (calendario de ^MERV)"),
    ("merv_cierre", "mercado", "Cierre del índice Merval", "puntos", "Lado Bursatil/03_vix_argentino"),
    ("ret_merval", "ambos", "Retorno diario del Merval", "proporción (0,01 = 1%)", "Lado Bursatil/03_vix_argentino"),
    ("vix_arg", "ambos", "VIX argentino: volatilidad realizada de 20 ruedas, anualizada", "%", "Lado Bursatil/03_vix_argentino"),
    ("regimen", "ambos", "Régimen de mercado (HMM, probabilidades suavizadas): Calmo, Moderado o Tenso", "categoría", "Lado Bursatil/06_hmm_regimen_mercado"),
    ("regimen_filtrado", "ambos", "Régimen con probabilidades filtradas (solo usa información hasta ese día)", "categoría", "Lado Bursatil/06_hmm_regimen_mercado"),
    ("prob_tenso", "ambos", "Probabilidad suavizada del régimen Tenso", "0 a 1", "Lado Bursatil/06_hmm_regimen_mercado"),
    ("prob_tenso_filtrada", "mercado", "Probabilidad filtrada del régimen Tenso", "0 a 1", "Lado Bursatil/06_hmm_regimen_mercado"),
    ("monto_operado", "mercado", "Cierre × volumen, sumado sobre las 47 acciones", "pesos", "Lado Bursatil/01_scraping_acciones (U4)"),
    ("monto_anormal", "mercado", "log(monto) − promedio de log(monto) de las 20 ruedas previas", "log (0 = habitual)", "U4"),
    ("n_notas", "ambos", "Notas que recibe la rueda (regla de las 17:00)", "notas", "U1"),
    ("dias_cubiertos", "mercado", "Días de calendario que junta la rueda (1 normal, 3 un lunes, 4+ tras feriado)", "días", "U2"),
    ("atencion_anormal", "ambos", "Atención de los medios: notas comparadas con lo habitual para ese tipo de rueda y las 20 previas", "log (0 = habitual)", "U2"),
    ("sent_neto", "ambos", "Tono de las noticias: promedio del sentimiento neto de las notas de la rueda", "puntos (−100 a +100)", "U2 (sentimiento de Gino)"),
    ("sent_neto_portal", "ambos", "Tono ajustado por portal (a cada nota se le resta el promedio de su portal)", "puntos", "U2"),
    ("sent_anormal", "ambos", "Tono anormal: tono de la rueda − promedio del tono de las 20 ruedas previas. Variable de tono del VAR", "puntos (0 = habitual)", "U4 (decisión de U5)"),
    ("sent_portal_anormal", "ambos", "Lo mismo con el tono ajustado por portal", "puntos (0 = habitual)", "U4 (decisión de U5)"),
    ("pct_pos, pct_neg, pct_neu, pct_mixto", "mercado", "Porcentaje promedio de oraciones de cada clase en las notas de la rueda", "%", "U2"),
    ("z_shock", "mercado", "Distancia del tono a lo habitual, en veces el error esperable por la cantidad de notas", "veces", "U2"),
    ("shock, shock_pos, shock_neg", "ambos", "Rueda de tono extremo (|z| > 2,5), total, positiva y negativa", "0/1", "U2"),
    ("evento_id", "ambos", "Número de evento (shocks del mismo signo en ruedas seguidas = un evento); 0 si no hay", "número", "U2"),
    ("dia_electoral", "ambos", "Rueda posterior a una elección (08/09/2025 y 27/10/2025)", "texto", "U2"),
    ("eco_electoral", "ambos", "Rueda dentro de las 20 posteriores a un día electoral (eco en el VIX y el régimen)", "0/1", "U4"),
    ("abril_2026", "ambos", "Rueda de abril de 2026 (hueco de iProfesional en el corpus)", "0/1", "U4"),
    ("ticker, empresa, sector, oficial", "panel", "Identificación de la acción; oficial = está en el S&P Merval", "texto", "Lado Bursatil/01_scraping_acciones"),
    ("grupo_baja_liquidez", "panel", "Integra el grupo de 8 del clustering, explicado por baja liquidez", "0/1", "Lado Bursatil/02_clustering_acciones"),
    ("cuatro_iliquidas", "panel", "Es una de las 4 acciones con más días sin operar (GCDI, RIGO, GRIM, GARO)", "0/1", "Lado Bursatil/02_clustering_acciones"),
    ("cierre", "panel", "Precio de cierre ajustado", "pesos", "Lado Bursatil/01_scraping_acciones"),
    ("retorno", "panel", "Retorno diario de la acción (pct_change sobre la serie completa)", "proporción", "U4 (misma definición que la carpeta 04)"),
    ("volumen", "panel", "Acciones operadas en la rueda", "acciones", "Lado Bursatil/01_scraping_acciones"),
    ("monto", "panel", "Cierre × volumen", "pesos", "U4"),
    ("vol_anormal", "panel", "log(1 + volumen) − promedio de log(1 + volumen) de las 20 ruedas previas", "log (0 = habitual)", "U4"),
    ("sin_operar", "panel", "La acción no operó (volumen 0)", "0/1", "U4"),
    ("precio_quieto", "panel", "El cierre es igual al de la rueda anterior", "0/1", "U4"),
    ("hubo_noticia", "panel", "Al menos una oración de las notas de la rueda menciona a la empresa", "0/1", "U3"),
    ("sentimiento_propio", "panel", "La empresa tiene noticias en al menos 90 ruedas y usa su propio sentimiento", "0/1", "U3"),
    ("n_articulos_empresa, n_oraciones_empresa", "panel", "Notas y oraciones de la rueda que mencionan a la empresa", "cantidad", "U3"),
    ("sent_neto_empresa", "panel", "Tono de las oraciones que mencionan a la empresa; vacío si no hubo noticia", "puntos", "U3 (cruce de Gino)"),
    ("peso_tono_propio", "panel", "Cuánto se confía en las oraciones de la empresa: n / (n + K), con K estimado de los datos", "0 a 1", "U4 (decisión de U6)"),
    ("tono_propio", "panel", "Tono propio: peso × (tono de la empresa − tono del mercado); 0 si no hubo noticia. Variable de empresa del VAR", "puntos (0 = como el mercado)", "U4 (decisión de U6)"),
]
dic = pd.DataFrame(D, columns=["variable", "dataset", "descripcion", "unidad", "origen"])
dic.to_csv(AQUI / "diccionario_variables.csv", index=False, encoding="utf-8")
documentadas = {c.strip() for v in dic["variable"] for c in v.split(",")}

# ── 6. Descriptivos ──────────────────────────────────────────────────────
desc_m = m[["ret_merval", "vix_arg", "monto_anormal", "sent_neto", "sent_neto_portal", "sent_anormal", "n_notas", "atencion_anormal"]].describe().T
desc_p = p[["retorno", "vol_anormal", "sent_neto_empresa", "n_oraciones_empresa"]].describe().T
desc_p = pd.concat([desc_p, p.loc[p["sentimiento_propio"] == 1, ["tono_propio"]].describe().T])
desc = pd.concat([desc_m.assign(dataset="mercado"), desc_p.assign(dataset="panel")])
desc = desc.rename(columns={"count": "n", "mean": "media", "std": "desvio", "min": "minimo", "50%": "mediana", "max": "maximo"})
desc[["dataset", "n", "media", "desvio", "minimo", "mediana", "maximo"]].round(4).to_csv(AQUI / "descriptivos.csv", encoding="utf-8", index_label="variable")

# ── 7. Controles ─────────────────────────────────────────────────────────
vix = pd.read_csv(BURSATIL / "03_vix_argentino" / "vix_arg.csv", parse_dates=["fecha"])
vix = vix[vix["fecha"] >= INICIO].reset_index(drop=True)
nucleo_m = ["merv_cierre", "ret_merval", "vix_arg", "regimen", "monto_operado", "monto_anormal", "n_notas", "sent_neto", "sent_neto_portal"]
nucleo_p = ["cierre", "retorno", "volumen", "vol_anormal", "hubo_noticia", "sentimiento_propio", "ret_merval", "sent_neto"]
controles = [
    ("Mercado: 244 ruedas, sin repetidas, las mismas del calendario bursátil",
     len(m) == 244 and m["rueda"].is_unique and m["rueda"].equals(vix["fecha"])),
    ("Merval, retorno y VIX idénticos a la carpeta 03",
     bool(np.allclose(m["ret_merval"], vix["retorno_diario"]) and np.allclose(m["vix_arg"], vix["vix_arg"]))),
    ("Panel: 47 acciones × 244 ruedas, sin repetidos", len(p) == 47 * 244 and not p.duplicated(["ticker", "rueda"]).any()),
    ("Sin valores faltantes en las variables principales (salvo atención en las 20 primeras ruedas)",
     bool(m[nucleo_m].notna().all().all() and p[nucleo_p].notna().all().all())),
    ("Las notas suman lo mismo que en U1", int(m["n_notas"].sum()) == 13925),
    ("Sentimiento de la empresa presente ⇔ hubo noticia", bool((p["sent_neto_empresa"].notna() == (p["hubo_noticia"] == 1)).all())),
    ("Cada rueda del panel tiene el mismo tono de mercado que el dataset de mercado",
     bool(p.merge(m[["rueda", "sent_neto"]], on="rueda", suffixes=("", "_m")).eval("sent_neto == sent_neto_m").all())),
    ("Todas las columnas de los dos datasets están en el diccionario",
     set(m_out.columns) | set(p_out.columns) <= documentadas),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── 8. Resumen ───────────────────────────────────────────────────────────
res = []
def r(clave, valor, detalle=""):
    res.append({"metrica": clave, "valor": valor, "detalle": detalle})

r("ruedas", len(m)); r("filas_panel", len(p)); r("columnas_mercado", m_out.shape[1]); r("columnas_panel", p_out.shape[1])
r("variables_diccionario", len(dic))
for reg in ("Calmo", "Moderado", "Tenso"):
    r(f"ruedas_{reg.lower()}", int((m["regimen"] == reg).sum()))
r("ruedas_eco_electoral", int(m["eco_electoral"].sum())); r("ruedas_abril_2026", int(m["abril_2026"].sum()))
r("ruedas_atencion_vacia", int(m["atencion_anormal"].isna().sum()), "primeras 20 ruedas, sin referencia previa")
r("ruedas_tono_anormal_vacio", int(m["sent_anormal"].isna().sum()), "primeras 20 ruedas, sin referencia previa")
r("ruedas_shock", int(m["shock"].sum()))
ili = p[p["cuatro_iliquidas"] == 1].groupby("ticker")[["sin_operar", "precio_quieto"]].sum()
r("cuatro_iliquidas_sin_operar", int(ili["sin_operar"].sum()), "; ".join(f"{t.replace('.BA', '')} {int(v)}" for t, v in ili["sin_operar"].items()))
r("cuatro_iliquidas_precio_quieto", int(ili["precio_quieto"].sum()), "; ".join(f"{t.replace('.BA', '')} {int(v)}" for t, v in ili["precio_quieto"].items()))
liq_total = liq.set_index("ticker").loc[CUATRO_ILIQUIDAS, "dias_sin_operar"]
r("cuatro_iliquidas_sin_operar_3anos", int(liq_total.sum()), "; ".join(f"{t.replace('.BA', '')} {int(v)}" for t, v in liq_total.items()))
quieto = p.groupby("ticker")["precio_quieto"].sum().sort_values(ascending=False)
r("precio_quieto_max", int(quieto.iloc[0]), quieto.index[0].replace(".BA", ""))
r("precio_quieto_mediana", int(quieto.median()))
r("filas_con_noticia", int(p["hubo_noticia"].sum()))
r("k_peso_tono_propio", round(K_PESO, 2), f"varianza de una oración {VAR_ORACION:.0f} / varianza entre días {VAR_ENTRE_DIAS:.0f}")
for n_or in (1, 2, 5, 10, 30):
    r(f"peso_con_{n_or}_oraciones", round(n_or / (n_or + K_PESO), 3))
r("filas_sentimiento_propio_con_noticia", int(((p["sentimiento_propio"] == 1) & (p["hubo_noticia"] == 1)).sum()),
  f"de {int((p['sentimiento_propio'] == 1).sum())}")
r("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(res).to_csv(AQUI / "resumen_u4.csv", index=False, encoding="utf-8")

# ── 9. Figura panorama ───────────────────────────────────────────────────
COL = {"Calmo": "#4A90C8", "Moderado": "#F2A900", "Tenso": "#D7301F"}
fig, ax = plt.subplots(4, 1, figsize=(11, 10), sharex=True, gridspec_kw={"height_ratios": [1.3, 1, 1, 0.9]})
x = m["rueda"]
for a in ax:
    for reg, color in COL.items():
        sel = m["regimen"] == reg
        a.fill_between(x, 0, 1, where=sel, transform=a.get_xaxis_transform(), color=color, alpha=0.10, step="mid", lw=0)
ax[0].plot(x, m["merv_cierre"] / 1e6, color="#12263A", lw=1.2)
ax[0].set_ylabel("Merval (millones)")
ax[0].set_title("Panorama de la ventana de la unión (fondo: régimen del HMM)", loc="left", fontsize=12, fontweight="bold")
for reg, color in COL.items():
    ax[0].plot([], [], color=color, lw=8, alpha=0.3, label=reg)
ax[0].legend(loc="upper left", frameon=False, fontsize=8.5, ncol=3)
ax[1].plot(x, m["sent_neto"], color="#2E8B57", lw=1)
ax[1].scatter(x[m["shock"] == 1], m.loc[m["shock"] == 1, "sent_neto"], color="#12263A", s=14, zorder=3, label="Rueda de tono extremo")
ax[1].axhline(0, color="#999", lw=0.6); ax[1].set_ylabel("Tono de\nlas noticias"); ax[1].legend(loc="lower left", frameon=False, fontsize=8.5)
ax[2].bar(x, m["atencion_anormal"], width=1, color="#8C6BB1"); ax[2].axhline(0, color="#999", lw=0.6)
ax[2].set_ylabel("Atención\nanormal")
ax[3].bar(x, m["monto_anormal"], width=1, color="#C26A00"); ax[3].axhline(0, color="#999", lw=0.6)
ax[3].set_ylabel("Monto operado\nanormal")
for a in ax:
    a.spines[["top", "right"]].set_visible(False)
for f in m.loc[m["dia_electoral"] != "", "rueda"]:
    for a in ax:
        a.axvline(f, color="#C26A00", lw=0.9, ls=":")
fig.tight_layout()
fig.savefig(AQUI / "u4_panorama.png", dpi=160, facecolor="white")

print(pd.DataFrame(res).to_string(index=False)); print(); print(verif.to_string(index=False))
print(); print(desc[["dataset", "n", "media", "desvio", "minimo", "maximo"]].round(3).to_string())
