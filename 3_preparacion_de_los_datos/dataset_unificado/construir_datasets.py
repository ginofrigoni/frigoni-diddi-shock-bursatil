"""
Dataset unificado — tesis versión 6.0
Fase 3 de CRISP-DM (preparación de los datos): integrar datos.

Junta el mercado con las series de noticias en las dos tablas que usan los modelos:

  dataset_panel.csv    una fila por acción y rueda: 17 empresas con cobertura × 244 ruedas = 4.148 filas.
  dataset_mercado.csv  una fila por rueda (244): Merval, VIX, régimen y sentimiento de las noticias
                       (para el modelo de la dirección inversa).

Definiciones (las mismas de la 5.0):
  - retorno = variación porcentual del cierre (pct_change), calculada sobre la serie completa desde 2023
    y recién después recortada a la ventana;
  - vol_anormal = log(1 + volumen del día) − promedio de log(1 + volumen) de las 20 ruedas previas
    (0 = lo habitual; +0,69 ≈ el doble), también sobre la serie completa;
  - sentimiento_inesperado: viene de sentimiento_por_rueda (rueda − promedio de las 20 anteriores);
  - sentimiento_propio = peso × (sentimiento de la empresa − sentimiento del mercado) si hubo noticia de la
    empresa, y 0 si no hubo. peso = n / (n + K), con n = oraciones que mencionan a la empresa ese día.
    K sale de los datos (estimación empírica de Bayes): varianza de una oración suelta ÷ varianza real del
    sentimiento relativo entre días.

Cambio de la 6.0 en K: en la 5.0 se estimaba con las 244 ruedas. Para que el período de test no influya
en ninguna variable del modelo, ahora K se estima SOLO con las ruedas de entrenamiento (antes de
CORTE_TEST). Se informa también el K con todas las ruedas, para mostrar cuánto cambia.

Cambios de la 6.0: solo las 17 empresas con cobertura; renombres (D4): tono_propio → sentimiento_propio,
peso_tono_propio → peso_sentimiento_propio, sent_anormal → sentimiento_inesperado, marca 0/1
sentimiento_propio → empresa_con_cobertura (ya no hace falta: son todas). Se sacan las columnas del
clustering, la atención, los shocks y el monto operado, que no se usan.

Entradas:
  2_comprension_de_los_datos/mercado/datos/precios_diarios_47_acciones.csv, panel_acciones_final.csv
  ../regimen_hmm/salidas/hmm_regimen_mercado.csv (Merval, VIX y régimen por rueda)
  ../vix_argentino/salidas/vix_arg.csv (control)
  ../sentimiento_por_rueda/salidas/sentimiento_por_rueda.csv
  ../sentimiento_por_empresa/salidas/panel_empresas_rueda.csv
Salidas: salidas/dataset_panel.csv, dataset_mercado.csv, diccionario_variables.csv, descriptivos.csv,
         verificaciones.csv, panorama.png;  metricas.csv

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
PREP = AQUI.parent
RAIZ = PREP.parent
MERCADO = RAIZ / "2_comprension_de_los_datos" / "mercado" / "datos"
SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)
REF_50 = RAIZ.parent / "tesis version 5.0" / "Unión" / "04_dataset_unificado"

VENTANA_VOL = 20
INICIO = "2025-05-05"
CORTE_TEST = "2026-02-01"      # primera fecha del período de test (decisión pendiente de confirmar; ver PLAN)
ECO = 20                       # ruedas en que un salto del día electoral sigue dentro de la ventana del VIX

# ── 1. Mercado ───────────────────────────────────────────────────────────
precios = pd.read_csv(MERCADO / "precios_diarios_47_acciones.csv", parse_dates=["Date"])
precios = precios.rename(columns={"Date": "fecha"}).sort_values(["ticker", "fecha"])
g = precios.groupby("ticker")
precios["retorno"] = g["Close"].pct_change()
precios["log_vol"] = np.log1p(precios["Volume"])
precios["vol_anormal"] = precios["log_vol"] - g["log_vol"].transform(
    lambda x: x.shift(1).rolling(VENTANA_VOL, min_periods=VENTANA_VOL).mean())
precios["sin_operar"] = (precios["Volume"] == 0).astype(int)
precios["precio_quieto"] = (g["Close"].diff() == 0).astype(int)

hmm = pd.read_csv(PREP / "regimen_hmm" / "salidas" / "hmm_regimen_mercado.csv", parse_dates=["fecha"])
acciones = pd.read_csv(MERCADO / "panel_acciones_final.csv")[["ticker", "empresa", "sector", "oficial"]]

# ── 2. Noticias ──────────────────────────────────────────────────────────
u_rueda = pd.read_csv(PREP / "sentimiento_por_rueda" / "salidas" / "sentimiento_por_rueda.csv", parse_dates=["rueda"])
u_emp = pd.read_csv(PREP / "sentimiento_por_empresa" / "salidas" / "panel_empresas_rueda.csv", parse_dates=["rueda"])

# ── 3. Dataset de mercado (una fila por rueda) ───────────────────────────
m = hmm[hmm["fecha"] >= INICIO][["fecha", "merv_cierre", "retorno_diario", "vix_arg", "regimen_nombre",
                                  "regimen_filtrado_nombre", "prob_suavizada_Tenso", "prob_filtrada_Tenso"]].rename(columns={
    "fecha": "rueda", "retorno_diario": "ret_merval", "regimen_nombre": "regimen", "regimen_filtrado_nombre": "regimen_filtrado",
    "prob_suavizada_Tenso": "prob_tenso", "prob_filtrada_Tenso": "prob_tenso_filtrada"})
noticias = u_rueda[["rueda", "n_notas", "dias_cubiertos", "sent_neto", "sent_neto_portal", "pct_pos", "pct_neg", "pct_neu",
                    "sentimiento_inesperado", "sentimiento_inesperado_portal", "dia_electoral"]]
m = m.merge(noticias, on="rueda", how="left").sort_values("rueda").reset_index(drop=True)
m["dia_electoral"] = m["dia_electoral"].fillna("")
m["eco_electoral"] = 0
for i in m.index[m["dia_electoral"] != ""]:
    m.loc[i:i + ECO - 1, "eco_electoral"] = 1
m["abril_2026"] = ((m["rueda"] >= "2026-04-01") & (m["rueda"] <= "2026-04-30")).astype(int)
m["periodo"] = np.where(m["rueda"] < CORTE_TEST, "entrenamiento", "test")
m_out = m.copy(); m_out["rueda"] = m_out["rueda"].dt.strftime("%Y-%m-%d")
m_out.round(6).to_csv(SALIDAS / "dataset_mercado.csv", index=False, encoding="utf-8")

# ── 4. Dataset panel: 17 empresas con cobertura × 244 ruedas ─────────────
emp = u_emp[u_emp["empresa_con_cobertura"]][["ticker", "rueda", "hubo_noticia", "n_articulos", "n_oraciones", "n_pos", "n_neg",
                                             "sent_neto_empresa"]].rename(
    columns={"n_articulos": "n_articulos_empresa", "n_oraciones": "n_oraciones_empresa"})
tickers = sorted(emp["ticker"].unique())
p = precios[(precios["fecha"] >= INICIO) & precios["ticker"].isin(tickers)][
    ["ticker", "fecha", "Close", "retorno", "Volume", "vol_anormal", "sin_operar", "precio_quieto"]]
p = p.rename(columns={"fecha": "rueda", "Close": "cierre", "Volume": "volumen"}).merge(acciones, on="ticker")
p = p.merge(emp, on=["ticker", "rueda"], how="left")
de_mercado = ["rueda", "ret_merval", "vix_arg", "regimen", "regimen_filtrado", "prob_tenso", "sent_neto", "sent_neto_portal",
              "sentimiento_inesperado", "sentimiento_inesperado_portal", "n_notas", "dia_electoral", "eco_electoral",
              "abril_2026", "periodo"]
p = p.merge(m[de_mercado], on="rueda", how="left").sort_values(["ticker", "rueda"]).reset_index(drop=True)


def estimar_k(d):
    """K de la estimación empírica de Bayes, con las filas de d (empresa con noticia)."""
    con = d[d["hubo_noticia"] == 1]
    relativo = con["sent_neto_empresa"] - con["sent_neto"]
    pp, pn = con["n_pos"].sum() / con["n_oraciones_empresa"].sum(), con["n_neg"].sum() / con["n_oraciones_empresa"].sum()
    var_oracion = 1e4 * (pp + pn - (pp - pn) ** 2)
    var_entre_dias = relativo.var() - (var_oracion / con["n_oraciones_empresa"]).mean()
    return var_oracion / var_entre_dias, var_oracion, var_entre_dias


K_PESO, VAR_ORACION, VAR_ENTRE_DIAS = estimar_k(p[p["periodo"] == "entrenamiento"])
K_TODAS, _, _ = estimar_k(p)
peso = p["n_oraciones_empresa"] / (p["n_oraciones_empresa"] + K_PESO)
p["peso_sentimiento_propio"] = peso.round(4)
p["sentimiento_propio"] = np.where(p["hubo_noticia"] == 1, peso * (p["sent_neto_empresa"] - p["sent_neto"]), 0.0)
p["sentimiento_propio_k_todas"] = np.where(
    p["hubo_noticia"] == 1, p["n_oraciones_empresa"] / (p["n_oraciones_empresa"] + K_TODAS) * (p["sent_neto_empresa"] - p["sent_neto"]), 0.0)
orden = ["ticker", "empresa", "sector", "oficial", "rueda", "periodo", "cierre", "retorno", "volumen", "vol_anormal", "sin_operar",
         "precio_quieto", "hubo_noticia", "n_articulos_empresa", "n_oraciones_empresa", "sent_neto_empresa",
         "peso_sentimiento_propio", "sentimiento_propio", "sentimiento_propio_k_todas"] + [c for c in de_mercado[1:] if c != "periodo"]
p = p[orden]
p_out = p.copy(); p_out["rueda"] = p_out["rueda"].dt.strftime("%Y-%m-%d")
p_out.round(6).to_csv(SALIDAS / "dataset_panel.csv", index=False, encoding="utf-8")

# ── 5. Diccionario de variables ──────────────────────────────────────────
D = [
    ("rueda", "ambos", "Día de bolsa (BYMA)", "fecha", "vix_argentino (calendario del Merval)"),
    ("periodo", "ambos", f"entrenamiento (antes del {CORTE_TEST}) o test (desde esa fecha)", "texto", "dataset_unificado"),
    ("merv_cierre", "mercado", "Cierre del índice Merval", "puntos", "vix_argentino"),
    ("ret_merval", "ambos", "Retorno diario del Merval", "proporción (0,01 = 1%)", "vix_argentino"),
    ("vix_arg", "ambos", "VIX argentino: volatilidad realizada de 20 ruedas, anualizada", "%", "vix_argentino"),
    ("regimen", "ambos", "Régimen de mercado (HMM, probabilidades suavizadas): Calmo, Moderado o Tenso. Solo anexo", "categoría", "regimen_hmm"),
    ("regimen_filtrado", "ambos", "Régimen con probabilidades filtradas (solo usa información hasta ese día). Solo anexo", "categoría", "regimen_hmm"),
    ("prob_tenso", "ambos", "Probabilidad suavizada del régimen Tenso", "0 a 1", "regimen_hmm"),
    ("prob_tenso_filtrada", "mercado", "Probabilidad filtrada del régimen Tenso", "0 a 1", "regimen_hmm"),
    ("n_notas", "ambos", "Notas que recibe la rueda (regla de las 17:00). Descriptivo, no entra al modelo", "notas", "regla_17"),
    ("dias_cubiertos", "mercado", "Días de calendario que junta la rueda (1 normal, 3 un lunes, 4+ tras feriado)", "días", "sentimiento_por_rueda"),
    ("sent_neto", "ambos", "Sentimiento de las noticias: promedio del sentimiento neto (% POS − % NEG) de las notas de la rueda", "puntos (−100 a +100)", "sentimiento_por_rueda"),
    ("sent_neto_portal", "ambos", "Sentimiento ajustado por portal (a cada nota se le resta el promedio de su portal)", "puntos", "sentimiento_por_rueda"),
    ("sentimiento_inesperado", "ambos", "Sentimiento de la rueda − promedio de las 20 ruedas anteriores. Variable de noticias del modelo B", "puntos (0 = habitual)", "sentimiento_por_rueda"),
    ("sentimiento_inesperado_portal", "ambos", "Lo mismo con el sentimiento ajustado por portal (anexo)", "puntos (0 = habitual)", "sentimiento_por_rueda"),
    ("pct_pos, pct_neg, pct_neu", "mercado", "Porcentaje promedio de oraciones de cada clase en las notas de la rueda", "%", "sentimiento_por_rueda"),
    ("dia_electoral", "ambos", "Rueda posterior a una elección (08/09/2025 y 27/10/2025)", "texto", "sentimiento_por_rueda"),
    ("eco_electoral", "ambos", "Rueda dentro de las 20 posteriores a un día electoral (eco en el VIX)", "0/1", "dataset_unificado"),
    ("abril_2026", "ambos", "Rueda de abril de 2026 (hueco de iProfesional en el corpus)", "0/1", "dataset_unificado"),
    ("ticker, empresa, sector, oficial", "panel", "Identificación de la acción; oficial = está en el S&P Merval", "texto", "mercado"),
    ("cierre", "panel", "Precio de cierre ajustado", "pesos", "mercado"),
    ("retorno", "panel", "Retorno diario de la acción (pct_change sobre la serie completa)", "proporción", "dataset_unificado"),
    ("volumen", "panel", "Acciones operadas en la rueda", "acciones", "mercado"),
    ("vol_anormal", "panel", "log(1 + volumen) − promedio de log(1 + volumen) de las 20 ruedas previas", "log (0 = habitual)", "dataset_unificado"),
    ("sin_operar", "panel", "La acción no operó (volumen 0)", "0/1", "dataset_unificado"),
    ("precio_quieto", "panel", "El cierre es igual al de la rueda anterior", "0/1", "dataset_unificado"),
    ("hubo_noticia", "panel", "Al menos una oración de las notas de la rueda menciona a la empresa", "0/1", "sentimiento_por_empresa"),
    ("n_articulos_empresa, n_oraciones_empresa", "panel", "Notas y oraciones de la rueda que mencionan a la empresa", "cantidad", "sentimiento_por_empresa"),
    ("sent_neto_empresa", "panel", "Sentimiento de las oraciones que mencionan a la empresa; vacío si no hubo noticia", "puntos", "sentimiento_por_empresa"),
    ("peso_sentimiento_propio", "panel", "Cuánto se confía en las oraciones de la empresa: n / (n + K), K estimado con el período de entrenamiento", "0 a 1", "dataset_unificado"),
    ("sentimiento_propio", "panel", "peso × (sentimiento de la empresa − sentimiento del mercado); 0 si no hubo noticia. Variable de empresa del modelo B", "puntos (0 = como el mercado)", "dataset_unificado"),
    ("sentimiento_propio_k_todas", "panel", "Lo mismo con K estimado con las 244 ruedas, como en la 5.0 (control)", "puntos", "dataset_unificado"),
]
dic = pd.DataFrame(D, columns=["variable", "dataset", "descripcion", "unidad", "origen"])
dic.to_csv(SALIDAS / "diccionario_variables.csv", index=False, encoding="utf-8")
documentadas = {c.strip() for v in dic["variable"] for c in v.split(",")}

# ── 6. Descriptivos ──────────────────────────────────────────────────────
desc_m = m[["ret_merval", "vix_arg", "sent_neto", "sentimiento_inesperado", "n_notas"]].describe().T
desc_p = p[["retorno", "vol_anormal", "sent_neto_empresa", "n_oraciones_empresa", "sentimiento_propio"]].describe().T
desc = pd.concat([desc_m.assign(dataset="mercado"), desc_p.assign(dataset="panel")])
desc = desc.rename(columns={"count": "n", "mean": "media", "std": "desvio", "min": "minimo", "50%": "mediana", "max": "maximo"})
desc[["dataset", "n", "media", "desvio", "minimo", "mediana", "maximo"]].round(4).to_csv(SALIDAS / "descriptivos.csv", encoding="utf-8", index_label="variable")

# ── 7. Controles ─────────────────────────────────────────────────────────
vix = pd.read_csv(PREP / "vix_argentino" / "salidas" / "vix_arg.csv", parse_dates=["fecha"])
vix = vix[vix["fecha"] >= INICIO].reset_index(drop=True)
controles = [
    ("Mercado: 244 ruedas, sin repetidas, las mismas del calendario bursátil",
     len(m) == 244 and m["rueda"].is_unique and m["rueda"].equals(vix["fecha"])),
    ("Merval, retorno y VIX idénticos a vix_argentino",
     bool(np.allclose(m["ret_merval"], vix["retorno_diario"]) and np.allclose(m["vix_arg"], vix["vix_arg"]))),
    ("Panel: 17 empresas × 244 ruedas = 4.148 filas, sin repetidos",
     len(p) == 17 * 244 == 4148 and not p.duplicated(["ticker", "rueda"]).any()),
    ("Sin faltantes en retorno, volumen anormal, VIX, sentimiento propio y hubo_noticia",
     bool(p[["retorno", "vol_anormal", "vix_arg", "sentimiento_propio", "hubo_noticia"]].notna().all().all())),
    ("El sentimiento inesperado falta solo en las primeras 20 ruedas",
     int(m["sentimiento_inesperado"].isna().sum()) == 20 and m["sentimiento_inesperado"].iloc[:20].isna().all()),
    ("Las notas suman lo mismo que en la regla de las 17:00", int(m["n_notas"].sum()) == 13925),
    ("Sentimiento de la empresa presente ⇔ hubo noticia", bool((p["sent_neto_empresa"].notna() == (p["hubo_noticia"] == 1)).all())),
    ("Cada rueda del panel tiene el mismo sentimiento de mercado que el dataset de mercado",
     bool(p.merge(m[["rueda", "sent_neto"]], on="rueda", suffixes=("", "_m")).eval("sent_neto == sent_neto_m").all())),
    ("K se estimó solo con ruedas de entrenamiento", bool((p.loc[p["periodo"] == "entrenamiento", "rueda"] < CORTE_TEST).all())),
    ("Todas las columnas de los dos datasets están en el diccionario", set(m_out.columns) | set(p_out.columns) <= documentadas),
]
if (REF_50 / "dataset_panel.csv").exists():
    v50 = pd.read_csv(REF_50 / "dataset_panel.csv", parse_dates=["rueda"])
    v50 = v50[v50["ticker"].isin(tickers)].sort_values(["ticker", "rueda"]).reset_index(drop=True)
    controles += [
        ("Retorno, volumen anormal y VIX idénticos a los de la 5.0 en las 17 empresas",
         # la 5.0 guarda los valores redondeados a 6 decimales: se compara con esa tolerancia
         bool(np.allclose(p["retorno"], v50["retorno"], atol=1e-6) and np.allclose(p["vol_anormal"], v50["vol_anormal"], atol=1e-6)
              and np.allclose(p["vix_arg"], v50["vix_arg"], atol=1e-6))),
        ("hubo_noticia idéntico al de la 5.0", bool((p["hubo_noticia"].values == v50["hubo_noticia"].values).all())),
    ]
    corr_propio = round(float(np.corrcoef(p["sentimiento_propio"], v50["tono_propio"])[0, 1]), 3)
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(SALIDAS / "verificaciones.csv", index=False, encoding="utf-8")

# ── 8. Métricas ──────────────────────────────────────────────────────────
res = []
def r(clave, valor, detalle=""):
    res.append({"metrica": clave, "valor": valor, "detalle": detalle})

r("ruedas", len(m)); r("filas_panel", len(p)); r("empresas", len(tickers), ", ".join(t.replace(".BA", "") for t in tickers))
r("columnas_panel", p_out.shape[1]); r("columnas_mercado", m_out.shape[1])
r("corte_test", CORTE_TEST)
r("ruedas_entrenamiento", int((m["periodo"] == "entrenamiento").sum())); r("ruedas_test", int((m["periodo"] == "test").sum()))
for reg in ("Calmo", "Moderado", "Tenso"):
    r(f"ruedas_{reg.lower()}", int((m["regimen"] == reg).sum()))
r("ruedas_eco_electoral", int(m["eco_electoral"].sum())); r("ruedas_abril_2026", int(m["abril_2026"].sum()))
r("filas_con_noticia", int(p["hubo_noticia"].sum()), f"de {len(p)}")
r("pct_filas_con_noticia", round(100 * p["hubo_noticia"].mean(), 1))
r("k_peso_entrenamiento", round(K_PESO, 2), f"varianza de una oración {VAR_ORACION:.0f} / varianza entre días {VAR_ENTRE_DIAS:.0f}")
r("k_peso_todas_las_ruedas", round(K_TODAS, 2), "como en la 5.0")
r("correlacion_sentimiento_propio_k_entrenamiento_vs_k_todas", round(p["sentimiento_propio"].corr(p["sentimiento_propio_k_todas"]), 4))
for n_or in (1, 2, 5, 10, 30):
    r(f"peso_con_{n_or}_oraciones", round(n_or / (n_or + K_PESO), 3))
if (REF_50 / "dataset_panel.csv").exists():
    r("correlacion_sentimiento_propio_con_tono_propio_5.0", corr_propio)
r("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(res).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")

# ── 9. Figura panorama ───────────────────────────────────────────────────
COL = {"Calmo": "#4A90C8", "Moderado": "#F2A900", "Tenso": "#D7301F"}
fig, ax = plt.subplots(3, 1, figsize=(11, 8.5), sharex=True, gridspec_kw={"height_ratios": [1.3, 1, 1]})
x = m["rueda"]
for a in ax:
    a.axvspan(pd.Timestamp(CORTE_TEST), x.max(), color="#999", alpha=0.10, lw=0)
ax[0].plot(x, m["merv_cierre"] / 1e6, color="#12263A", lw=1.2); ax[0].set_ylabel("Merval (millones)")
ax[0].set_title("Panorama de la ventana (gris: período de test)", loc="left", fontsize=12, fontweight="bold")
ax[1].plot(x, m["vix_arg"], color="#C26A00", lw=1.1); ax[1].set_ylabel("VIX argentino (%)")
ax[2].bar(x, m["sentimiento_inesperado"], width=1, color=np.where(m["sentimiento_inesperado"] > 0, "#2E8B57", "#D7301F"))
ax[2].axhline(0, color="#999", lw=0.6); ax[2].set_ylabel("Sentimiento\ninesperado")
for a in ax:
    a.spines[["top", "right"]].set_visible(False)
    for f in m.loc[m["dia_electoral"] != "", "rueda"]:
        a.axvline(f, color="#C26A00", lw=0.9, ls=":")
fig.tight_layout()
fig.savefig(SALIDAS / "panorama.png", dpi=160, facecolor="white")

print(pd.DataFrame(res).to_string(index=False)); print(); print(verif.to_string(index=False))
