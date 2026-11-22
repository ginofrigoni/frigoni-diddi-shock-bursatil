"""
Sentimiento por rueda y sentimiento inesperado — tesis versión 6.0
Fase 3 de CRISP-DM (preparación de los datos): construir atributos derivados.

Para cada una de las 244 ruedas:
  - sent_neto: promedio del sentimiento neto de las notas de la rueda (cada nota pesa lo mismo);
  - sent_neto_portal: lo mismo, restando antes a cada nota el promedio de su portal (un día con
    muchas notas de un portal "optimista" no parece un día optimista);
  - sentimiento_inesperado = sent_neto − promedio de sent_neto de las 20 ruedas anteriores
    (0 = lo habitual). Es la variable de noticias del mercado en el modelo B. Las primeras 20
    ruedas quedan vacías porque no tienen 20 ruedas previas.
  - dia_electoral: rueda posterior a una elección (para la prueba del anexo sin días electorales).

Ventana de 20 ruedas: un mes de mercado, el horizonte del VIX (Cboe, 30 días ≈ 21 ruedas) y del
componente mensual de Corsi (2009); siguiendo a Tetlock (2007), el anexo prueba 10 y 60 ruedas.

Cambios respecto de la 5.0 (U2): ya no se calculan los shocks ni la atención de los medios, que no
entran al modelo. El sentimiento inesperado antes se calculaba en U4 (con el nombre sent_anormal);
ahora se calcula acá, con la misma fórmula.

Entradas:
  ../regla_17/salidas/nota_a_rueda.csv                 rueda de cada nota
  ../sentimiento_finbeto/salidas/sentimiento_por_nota.csv   sentimiento de cada nota
  ../vix_argentino/salidas/vix_arg.csv                 calendario (días que cubre cada rueda)
Salidas:
  salidas/sentimiento_por_rueda.csv, salidas/verificaciones.csv, salidas/sentimiento_por_rueda.png
  metricas.csv

Uso:  python sentimiento_por_rueda.py
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
SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)
REF_50 = PREP.parent.parent / "tesis version 5.0"

VENTANA = 20
CLASES = ("pos", "neg", "neu")
DIAS_ELECTORALES = {"2025-09-08": "elecciones bonaerenses (07/09)", "2025-10-27": "elecciones legislativas (26/10)"}


def serie_por_rueda(nota_a_rueda, por_nota, clases):
    d = por_nota.merge(nota_a_rueda[["url", "rueda", "en_ventana_union"]], on="url")
    d = d[d["en_ventana_union"]].copy()
    d["sent_portal"] = d["sent_neto"] - d.groupby("fuente")["sent_neto"].transform("mean")
    g = d.groupby("rueda")
    s = pd.DataFrame({"n_notas": g.size(), "sent_neto": g["sent_neto"].mean(), "sent_neto_portal": g["sent_portal"].mean()})
    for c in clases:
        s[f"pct_{c}"] = g[f"pct_{c}"].mean()
    s = s.reset_index()
    for col, nuevo in (("sent_neto", "sentimiento_inesperado"), ("sent_neto_portal", "sentimiento_inesperado_portal")):
        s[nuevo] = s[col] - s[col].shift(1).rolling(VENTANA, min_periods=VENTANA).mean()
    return s, d


nr = pd.read_csv(PREP / "regla_17" / "salidas" / "nota_a_rueda.csv")
art = pd.read_csv(PREP / "sentimiento_finbeto" / "salidas" / "sentimiento_por_nota.csv")
s, d = serie_por_rueda(nr, art, CLASES)

cal = pd.read_csv(PREP / "vix_argentino" / "salidas" / "vix_arg.csv", parse_dates=["fecha"])["fecha"]
anterior = dict(zip(cal.dt.strftime("%Y-%m-%d").iloc[1:], cal.iloc[:-1]))
s["dias_cubiertos"] = [(pd.Timestamp(r) - anterior[r]).days for r in s["rueda"]]
s["dia_electoral"] = s["rueda"].map(DIAS_ELECTORALES).fillna("")
cols = ["rueda", "n_notas", "dias_cubiertos", "sent_neto", "sent_neto_portal", "pct_pos", "pct_neg", "pct_neu",
        "sentimiento_inesperado", "sentimiento_inesperado_portal", "dia_electoral"]
s[cols].round(4).to_csv(SALIDAS / "sentimiento_por_rueda.csv", index=False, encoding="utf-8")

# ── Controles ────────────────────────────────────────────────────────────
u1 = pd.read_csv(PREP / "regla_17" / "salidas" / "notas_por_rueda.csv")
controles = [
    ("La serie tiene las 244 ruedas, sin huecos", len(s) == 244 and s["sent_neto"].notna().all()),
    ("Las notas por rueda coinciden con la regla de las 17:00",
     s.set_index("rueda")["n_notas"].equals(u1.set_index("rueda")["n_notas"])),
    ("El ajuste por portal deja en 0 el promedio de cada portal",
     bool((d.groupby("fuente")["sent_portal"].mean().abs() < 1e-9).all())),
    ("El sentimiento inesperado está vacío solo en las primeras 20 ruedas",
     bool(s["sentimiento_inesperado"].iloc[:VENTANA].isna().all() and s["sentimiento_inesperado"].iloc[VENTANA:].notna().all())),
    ("El sentimiento inesperado usa solo ruedas anteriores (cambiar la rueda t no cambia el valor de t−1)", True),
]
# control de "no mirar al futuro": se altera el sentimiento de una rueda y se verifica que no cambian las anteriores
alt = s["sent_neto"].copy(); k = 100; alt.iloc[k] += 50
ines_alt = alt - alt.shift(1).rolling(VENTANA, min_periods=VENTANA).mean()
controles[-1] = (controles[-1][0], bool(np.allclose(ines_alt.iloc[:k].fillna(0), s["sentimiento_inesperado"].iloc[:k].fillna(0))))

hay_50 = (REF_50 / "Unión" / "02_sentimiento_por_rueda" / "sentimiento_mercado_rueda.csv").exists()
if hay_50:
    # mismo cálculo con las etiquetas de la 5.0 → tiene que dar la serie de la 5.0
    nr50 = pd.read_csv(REF_50 / "Unión" / "01_alineacion_noticias_ruedas" / "nota_a_rueda.csv")
    art50 = pd.read_csv(REF_50 / "Lado Noticias" / "sentimiento_finbert" / "finetuned_articulos.csv")
    s50, _ = serie_por_rueda(nr50, art50, CLASES + ("mixto",))
    u2_50 = pd.read_csv(REF_50 / "Unión" / "02_sentimiento_por_rueda" / "sentimiento_mercado_rueda.csv")
    d4_50 = pd.read_csv(REF_50 / "Unión" / "04_dataset_unificado" / "dataset_mercado.csv")
    controles += [
        ("Con las etiquetas de la 5.0 se reproduce el sentimiento por rueda de la 5.0",
         bool(np.allclose(s50["sent_neto"], u2_50["sent_neto"], atol=1e-4))),
        ("Con las etiquetas de la 5.0 se reproduce el sent_anormal de la 5.0",
         bool(np.allclose(s50["sentimiento_inesperado"].fillna(0), d4_50["sent_anormal"].fillna(0), atol=1e-3))),
    ]
    corr_nivel = round(s["sent_neto"].corr(u2_50["sent_neto"]), 3)
    corr_ines = round(s["sentimiento_inesperado"].corr(d4_50["sent_anormal"]), 3)
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(SALIDAS / "verificaciones.csv", index=False, encoding="utf-8")

# ── Métricas ─────────────────────────────────────────────────────────────
res = []
def m(clave, valor, detalle=""):
    res.append({"metrica": clave, "valor": valor, "detalle": detalle})

m("ruedas", len(s)); m("notas", int(s["n_notas"].sum()))
m("sent_neto_media", round(s["sent_neto"].mean(), 2)); m("sent_neto_desvio", round(s["sent_neto"].std(), 2))
m("sent_neto_min", round(s["sent_neto"].min(), 2), s.loc[s["sent_neto"].idxmin(), "rueda"])
m("sent_neto_max", round(s["sent_neto"].max(), 2), s.loc[s["sent_neto"].idxmax(), "rueda"])
m("inesperado_desvio", round(s["sentimiento_inesperado"].std(), 2))
m("inesperado_min", round(s["sentimiento_inesperado"].min(), 2), s.loc[s["sentimiento_inesperado"].idxmin(), "rueda"])
m("inesperado_max", round(s["sentimiento_inesperado"].max(), 2), s.loc[s["sentimiento_inesperado"].idxmax(), "rueda"])
m("ruedas_con_inesperado", int(s["sentimiento_inesperado"].notna().sum()), f"desde {s.loc[VENTANA, 'rueda']}")
m("autocorrelacion_sentimiento", round(s["sent_neto"].autocorr(1), 2))
for c in CLASES:
    m(f"pct_{c}_media", round(s[f"pct_{c}"].mean(), 1))
for fuente, g in d.groupby("fuente")["sent_neto"]:
    m(f"portal_{fuente}", round(g.mean(), 1), f"{len(g)} notas")
if hay_50:
    m("correlacion_con_5.0_sent_neto", corr_nivel, "misma serie con FinBETO de 4 clases")
    m("correlacion_con_5.0_inesperado", corr_ines)
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(res).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")

# ── Figura ───────────────────────────────────────────────────────────────
x = pd.to_datetime(s["rueda"])
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 7.5), sharex=True)
a1.plot(x, s["sent_neto"], color="#4A90C8", lw=1.1, label="Sentimiento de la rueda")
a1.plot(x, s["sent_neto"].shift(1).rolling(VENTANA, min_periods=VENTANA).mean(), color="#5C6B7A", lw=1.4, ls="--",
        label=f"Promedio de las {VENTANA} ruedas anteriores")
a1.axhline(0, color="#999", lw=0.6); a1.set_ylabel("Sentimiento neto (puntos)")
a1.set_title("Sentimiento de las noticias por rueda", loc="left", fontsize=12, fontweight="bold")
a1.legend(loc="lower left", frameon=False, fontsize=9)
a2.bar(x, s["sentimiento_inesperado"], width=1, color=np.where(s["sentimiento_inesperado"] > 0, "#2E8B57", "#D7301F"))
a2.axhline(0, color="#999", lw=0.6); a2.set_ylabel("Puntos (0 = lo habitual)")
a2.set_title("Sentimiento inesperado: la rueda contra las 20 anteriores", loc="left", fontsize=12, fontweight="bold")
for f in DIAS_ELECTORALES:
    for ax in (a1, a2):
        ax.axvline(pd.Timestamp(f), color="#C26A00", lw=1, ls=":")
for ax in (a1, a2):
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(SALIDAS / "sentimiento_por_rueda.png", dpi=160, facecolor="white")

print(pd.DataFrame(res).to_string(index=False))
print()
print(verif.to_string(index=False))
