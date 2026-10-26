"""
U2 · Series de mercado por rueda — tesis version 3.0 (Unión)

Arma, para cada una de las 244 ruedas de la ventana de la unión:
  - el sentimiento de las noticias (promedio del sent_neto de las notas de la rueda, igual peso por nota,
    la misma definición que la serie diaria de Gino) y su versión ajustada por portal;
  - la atención de los medios: cuántas notas recibió la rueda, comparado con lo habitual (decisión D2);
  - los shocks de sentimiento, con una regla elegida comparándola contra el azar.

Cómo se elige la regla de shocks
  Se prueban dos familias de reglas sobre la serie por rueda:
    "desvío de los días previos": el día es shock si se aparta de la media de las W ruedas previas más de
        k desvíos de esas mismas ruedas (la de Gino es W=7, incluyendo el propio día, k=1,5);
    "por muestreo": el día es shock si se aparta de la media de las W ruedas previas más de k veces el error
        que se espera solo por la cantidad de notas del día (desvío de una nota / raíz de la cantidad de notas).
  El "azar" se obtiene mezclando las notas entre ruedas (cada rueda conserva su cantidad de notas) y
  contando cuántos shocks marca cada regla: si las marca igual con las notas mezcladas, no detecta nada.
  Criterio fijado de antemano: ventana de 20 ruedas (la misma del VIX y la volatilidad del lado bursátil),
  serie ajustada por portal, y el umbral que más shocks detecta con a lo sumo 20% de falsos esperados.
  Decisión del 24/10/2026 (opción A): como el promedio diario varía en todos los días más de lo que predice
  la cantidad de notas (las notas de un mismo día hablan de los mismos temas), los shocks se interpretan como
  las ruedas de tono más extremo del período, no como días estadísticamente excepcionales. En U8 se repite
  con umbral 3.

Solo lee. Entradas:
  ../01_alineacion_noticias_ruedas/nota_a_rueda.csv          rueda de cada nota (U1)
  Lado Noticias/sentimiento_finbert/finetuned_articulos.csv  sentimiento de cada nota (versión congelada, D1)
  Lado Noticias/sentimiento_finbert/finetuned_serie_diaria.csv  control: la serie diaria de Gino
  Lado Bursatil/03_vix_argentino/vix_arg.csv                 calendario (días que cubre cada rueda)

Salidas (en esta carpeta):
  sentimiento_mercado_rueda.csv  una fila por rueda: sentimiento, atención y shock
  shocks_rueda.csv               los shocks elegidos, agrupados en eventos
  reglas_shock.csv               todas las reglas probadas contra el azar
  resumen_u2.csv, verificaciones.csv, u2_serie.png, u2_reglas.png

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
RAIZ = AQUI.parent.parent
U1 = AQUI.parent / "01_alineacion_noticias_ruedas"
SENT = RAIZ / "Lado Noticias" / "sentimiento_finbert"

VENTANA = 20                 # ruedas previas que definen "lo habitual" (fijada de antemano)
MAX_FALSOS = 0.20            # a lo sumo 20% de shocks esperables por azar
N_PERMUTACIONES = 300
SEMILLA = 42
DIAS_ELECTORALES = {"2025-09-08": "elecciones bonaerenses (07/09)", "2025-10-27": "elecciones legislativas (26/10)"}
ventanas_prueba, umbrales_desvio, umbrales_muestreo = (7, 10, 20, 30), (1.5, 2.0, 2.5, 3.0), (2.0, 2.5, 3.0, 3.5)

# ── 1. Notas de la ventana con su rueda y su sentimiento ─────────────────
nr = pd.read_csv(U1 / "nota_a_rueda.csv")
art = pd.read_csv(SENT / "finetuned_articulos.csv")
d = art.merge(nr[["url", "rueda", "en_ventana_union", "hora_sospechosa"]], on="url")
d = d[d["en_ventana_union"]].copy()
# Ajuste por portal: a cada nota se le resta el promedio de su portal en la ventana. Así un día con
# muchas notas de un portal "optimista" (TN promedia +30) no parece un día optimista.
d["sent_portal"] = d["sent_neto"] - d.groupby("fuente")["sent_neto"].transform("mean")

ruedas = sorted(d["rueda"].unique())
pos = d["rueda"].map({r: i for i, r in enumerate(ruedas)}).to_numpy()
n = np.bincount(pos, minlength=len(ruedas))


def media_por_rueda(valores):
    return np.bincount(pos, weights=np.asarray(valores, dtype=float), minlength=len(ruedas)) / n


# ── 2. Serie por rueda ───────────────────────────────────────────────────
s = pd.DataFrame({"rueda": ruedas, "n_notas": n})
s["sent_neto"] = media_por_rueda(d["sent_neto"])
s["sent_neto_portal"] = media_por_rueda(d["sent_portal"])
for c in ("pct_pos", "pct_neg", "pct_neu", "pct_mixto"):
    s[c] = media_por_rueda(d[c])

# Días que cubre cada rueda: 1 un día normal, 3 un lunes, 4 o más tras un feriado.
cal = pd.read_csv(RAIZ / "Lado Bursatil" / "03_vix_argentino" / "vix_arg.csv", parse_dates=["fecha"])["fecha"]
anterior = dict(zip(cal.dt.strftime("%Y-%m-%d").iloc[1:], cal.iloc[:-1]))
s["dias_cubiertos"] = [(pd.Timestamp(r) - anterior[r]).days for r in ruedas]

# Atención anormal (log): primero se descuenta cuántos días junta la rueda (mediana de notas de las ruedas
# que cubren la misma cantidad de días), después el nivel de las 20 ruedas previas (cambios lentos, como
# el hueco de iProfesional en abril de 2026). 0 = lo habitual; +0,69 = el doble de notas; −0,69 = la mitad.
tipo = s["dias_cubiertos"].clip(upper=4)
r1 = np.log(s["n_notas"]) - np.log(s.groupby(tipo)["n_notas"].transform("median"))
s["atencion_anormal"] = r1 - r1.shift(1).rolling(VENTANA, min_periods=VENTANA).mean()

# ── 3. Reglas de shock contra el azar ────────────────────────────────────
def contar(serie, sd_nota):
    x = pd.Series(serie)
    out = {}
    for w in ventanas_prueba:
        previa = x.shift(1)
        media = previa.rolling(w, min_periods=w).mean()
        z_desv = (x - media) / previa.rolling(w, min_periods=w).std()
        z_mues = (x - media) / (sd_nota / np.sqrt(n))
        for k in umbrales_desvio:
            out[("desvío de los días previos", w, k)] = int((z_desv.abs() > k).sum())
        for k in umbrales_muestreo:
            out[("por muestreo", w, k)] = int((z_mues.abs() > k).sum())
    # La regla original de Gino, aplicada a la serie por rueda (7 días incluyendo el propio, 1,5σ).
    z_gino = (x - x.rolling(7, min_periods=7).mean()) / x.rolling(7, min_periods=7).std()
    out[("Gino (incluye el día)", 7, 1.5)] = int((z_gino.abs() > 1.5).sum())
    return out


rng = np.random.default_rng(SEMILLA)
tablas = []
for serie_nombre, col in (("simple", "sent_neto"), ("ajustada por portal", "sent_portal")):
    valores = d[col].to_numpy()
    sd_nota = valores.std()
    real = contar(media_por_rueda(valores), sd_nota)
    azar = pd.DataFrame([contar(media_por_rueda(rng.permutation(valores)), sd_nota) for _ in range(N_PERMUTACIONES)])
    for (familia, w, k), v in real.items():
        a = azar[(familia, w, k)]
        tablas.append({"serie": serie_nombre, "familia": familia, "ventana": w, "umbral": k, "shocks": v,
                       "azar_promedio": round(a.mean(), 1), "p_valor": round(((a >= v).sum() + 1) / (N_PERMUTACIONES + 1), 4),
                       "falsos_esperados_pct": round(100 * a.mean() / max(v, 1), 1)})
reglas = pd.DataFrame(tablas)
candidatas = reglas[(reglas["serie"] == "ajustada por portal") & (reglas["familia"] == "por muestreo") &
                    (reglas["ventana"] == VENTANA) & (reglas["falsos_esperados_pct"] <= 100 * MAX_FALSOS)]
elegida = candidatas.sort_values(["shocks", "umbral"], ascending=[False, True]).iloc[0]
reglas["elegida"] = ((reglas["serie"] == elegida["serie"]) & (reglas["familia"] == elegida["familia"]) &
                     (reglas["ventana"] == elegida["ventana"]) & (reglas["umbral"] == elegida["umbral"]))
reglas.to_csv(AQUI / "reglas_shock.csv", index=False, encoding="utf-8")
UMBRAL = float(elegida["umbral"])

# ── 4. Shocks con la regla elegida ───────────────────────────────────────
sd_nota = d["sent_portal"].std(ddof=0)
media_previa = s["sent_neto_portal"].shift(1).rolling(VENTANA, min_periods=VENTANA).mean()
s["z_shock"] = (s["sent_neto_portal"] - media_previa) / (sd_nota / np.sqrt(s["n_notas"]))
s["shock_pos"] = s["z_shock"] > UMBRAL
s["shock_neg"] = s["z_shock"] < -UMBRAL
s["shock"] = s["shock_pos"] | s["shock_neg"]
s["evaluable"] = media_previa.notna()
# Shocks del mismo signo en ruedas seguidas forman un solo evento (fecha = la primera rueda).
signo = np.where(s["shock_pos"], 1, np.where(s["shock_neg"], -1, 0))
nuevo = (signo != 0) & ((signo != np.roll(signo, 1)) | (np.arange(len(s)) == 0))
s["evento_id"] = np.where(signo != 0, np.cumsum(nuevo), 0)
s["dia_electoral"] = s["rueda"].map(DIAS_ELECTORALES).fillna("")

cols = ["rueda", "n_notas", "dias_cubiertos", "atencion_anormal", "sent_neto", "sent_neto_portal",
        "pct_pos", "pct_neg", "pct_neu", "pct_mixto", "z_shock", "evaluable", "shock", "shock_pos", "shock_neg",
        "evento_id", "dia_electoral"]
s[cols].round(4).to_csv(AQUI / "sentimiento_mercado_rueda.csv", index=False, encoding="utf-8")

# Shocks y su relación con la serie de Gino (por fecha calendario).
gino = pd.read_csv(SENT / "finetuned_serie_diaria.csv")
shocks_gino = set(gino.loc[gino["shock"] == True, "fecha"])
notas_rueda = nr[nr["en_ventana_union"]].groupby("rueda")["fecha_ar"].apply(set)
sh = s[s["shock"]].copy()
sh["tipo"] = np.where(sh["shock_pos"], "positivo", "negativo")
sh["fechas_que_junta"] = sh["rueda"].map(lambda r: ", ".join(sorted(notas_rueda[r])))
sh["coincide_con_shock_gino"] = sh["rueda"].map(lambda r: bool(notas_rueda[r] & shocks_gino))
sh[["evento_id", "rueda", "tipo", "z_shock", "n_notas", "sent_neto", "sent_neto_portal", "atencion_anormal",
    "dia_electoral", "coincide_con_shock_gino", "fechas_que_junta"]].round(3).to_csv(AQUI / "shocks_rueda.csv", index=False, encoding="utf-8")

# ── 5. Controles ─────────────────────────────────────────────────────────
u1 = pd.read_csv(U1 / "notas_por_rueda.csv")
cal_gino = art.groupby("fecha")["sent_neto"].mean()
g = gino.dropna(subset=["sent_neto"]).set_index("fecha")["sent_neto"]
comunes = g.index.intersection(cal_gino.index)
controles = [
    ("La serie tiene las 244 ruedas, sin huecos", len(s) == 244 and s["sent_neto"].notna().all()),
    ("Las notas por rueda coinciden con U1", s.set_index("rueda")["n_notas"].equals(u1.set_index("rueda")["n_notas"])),
    ("Promediando por fecha calendario se reproduce la serie diaria de Gino",
     bool(np.allclose(cal_gino[comunes], g[comunes], atol=1e-3))),
    ("El ajuste por portal deja en 0 el promedio de cada portal",
     bool((d.groupby("fuente")["sent_portal"].mean().abs() < 1e-9).all())),
    ("Solo hay shocks en ruedas con 20 ruedas previas de referencia", not (s["shock"] & ~s["evaluable"]).any()),
    ("La regla elegida tiene a lo sumo 20% de falsos esperados", elegida["falsos_esperados_pct"] <= 100 * MAX_FALSOS),
    ("La regla elegida marca más shocks que con las notas mezcladas al azar (p < 0,05)", elegida["p_valor"] < 0.05),
]

# Sobredispersión: las notas de un mismo día hablan de los mismos temas, así que el promedio diario varía
# más de lo que predice la cantidad de notas. Si esa variación extra es pareja en todos los días, z se
# comporta como una normal con desvío mayor que 1, y los "shocks" son sus puntas normales.
from scipy import stats
z = s["z_shock"].dropna()
sd_robusto = 1.4826 * np.median(np.abs(z - z.median()))
esperados_sobredisp = len(z) * 2 * stats.norm.sf(UMBRAL / sd_robusto)
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── 6. Resumen ───────────────────────────────────────────────────────────
res = []
def m(clave, valor, detalle=""):
    res.append({"metrica": clave, "valor": valor, "detalle": detalle})

m("ruedas", len(s)); m("notas", int(s["n_notas"].sum()))
m("ruedas_evaluables_shock", int(s["evaluable"].sum()), f"desde {s.loc[s['evaluable'], 'rueda'].iloc[0]}")
m("sent_neto_media", round(s["sent_neto"].mean(), 2)); m("sent_neto_desvio", round(s["sent_neto"].std(), 2))
m("sent_neto_min", round(s["sent_neto"].min(), 2), s.loc[s["sent_neto"].idxmin(), "rueda"])
m("sent_neto_max", round(s["sent_neto"].max(), 2), s.loc[s["sent_neto"].idxmax(), "rueda"])
m("correlacion_simple_vs_portal", round(s["sent_neto"].corr(s["sent_neto_portal"]), 3))
m("autocorrelacion_sentimiento", round(s["sent_neto"].autocorr(1), 2))
m("sd_nota_ajustada", round(sd_nota, 1), "desvío del sentimiento de una nota")
for fuente, g in d.groupby("fuente")["sent_neto"]:
    m(f"portal_{fuente}", round(g.mean(), 1), str(len(g)))
m("notas_mediana_por_dias_cubiertos", "; ".join(f"{k}: {int(v)}" for k, v in s.groupby(tipo)["n_notas"].median().items()))
m("atencion_max", round(s["atencion_anormal"].max(), 2), s.loc[s["atencion_anormal"].idxmax(), "rueda"])
m("atencion_min", round(s["atencion_anormal"].min(), 2), s.loc[s["atencion_anormal"].idxmin(), "rueda"])
m("regla_elegida", f"por muestreo, {VENTANA} ruedas, {UMBRAL:g}", "serie ajustada por portal")
m("shocks", int(s["shock"].sum()), f"azar: {elegida['azar_promedio']}")
m("shocks_pos", int(s["shock_pos"].sum())); m("shocks_neg", int(s["shock_neg"].sum()))
m("eventos", int(s["evento_id"].max()))
m("falsos_esperados_pct", float(elegida["falsos_esperados_pct"])); m("p_valor_regla", float(elegida["p_valor"]))
m("desvio_z", round(z.std(), 2), "1 si los días solo variaran por la cantidad de notas")
m("desvio_robusto_z", round(sd_robusto, 2), "desvío sin dejarse llevar por los extremos (MAD)")
m("shocks_esperados_sobredispersion", round(esperados_sobredisp, 1), "si z fuera normal con el desvío robusto")
m("curtosis_z", round(stats.kurtosis(z), 2), "0 en una normal")
m("shocks_coinciden_gino", int(sh["coincide_con_shock_gino"].sum()), f"de {len(sh)}")
m("shocks_dia_electoral", int((sh["dia_electoral"] != "").sum()), "; ".join(sh.loc[sh["dia_electoral"] != "", "rueda"]))
gr = reglas[(reglas["familia"].str.startswith("Gino"))]
for _, x in gr.iterrows():
    m(f"gino_rueda_{'portal' if 'portal' in x['serie'] else 'simple'}", int(x["shocks"]), f"azar: {x['azar_promedio']}; falsos {x['falsos_esperados_pct']}%")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(res).to_csv(AQUI / "resumen_u2.csv", index=False, encoding="utf-8")

# ── 7. Figuras ───────────────────────────────────────────────────────────
x = pd.to_datetime(s["rueda"])
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
a1.plot(x, s["sent_neto_portal"], color="#4A90C8", lw=1.1, label="Sentimiento ajustado por portal")
a1.plot(x, media_previa, color="#5C6B7A", lw=1.4, ls="--", label=f"Media de las {VENTANA} ruedas previas")
a1.scatter(x[s["shock_pos"]], s.loc[s["shock_pos"], "sent_neto_portal"], color="#2E8B57", s=46, zorder=3, label="Shock positivo")
a1.scatter(x[s["shock_neg"]], s.loc[s["shock_neg"], "sent_neto_portal"], color="#D7301F", s=46, zorder=3, label="Shock negativo")
for (f, txt), alto in zip(DIAS_ELECTORALES.items(), (1.0, 0.93)):
    a1.axvline(pd.Timestamp(f), color="#C26A00", lw=1, ls=":")
    y0, y1 = a1.get_ylim()
    a1.text(pd.Timestamp(f), y0 + (y1 - y0) * alto, " " + txt.split(" (")[0], fontsize=8, color="#C26A00", va="top")
a1.axhline(0, color="#999", lw=0.6)
a1.set_ylabel("Sentimiento neto (puntos)")
a1.set_title("Sentimiento de las noticias por rueda y shocks elegidos", loc="left", fontsize=12, fontweight="bold")
a1.legend(loc="lower left", frameon=False, fontsize=8.5, ncol=2)
a2.bar(x, s["atencion_anormal"], width=1, color=np.where(s["atencion_anormal"] > 0, "#F2A900", "#8C6BB1"))
a2.axhline(0, color="#999", lw=0.6)
a2.set_ylabel("Atención anormal (log)")
a2.set_title("Atención de los medios: notas de la rueda comparadas con lo habitual", loc="left", fontsize=12, fontweight="bold")
for ax in (a1, a2):
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(AQUI / "u2_serie.png", dpi=160, facecolor="white")

fig, axs = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
for ax, fam, umbs in ((axs[0], "desvío de los días previos", umbrales_desvio), (axs[1], "por muestreo", umbrales_muestreo)):
    t = reglas[(reglas["serie"] == "ajustada por portal") & (reglas["familia"] == fam) & (reglas["ventana"] == VENTANA)]
    xs = np.arange(len(t))
    ax.bar(xs - 0.2, t["shocks"], 0.4, color="#4A90C8", label="Noticias reales")
    ax.bar(xs + 0.2, t["azar_promedio"], 0.4, color="#BBBBBB", label="Notas mezcladas al azar")
    ax.set_xticks(xs, [f"{k:g}" for k in t["umbral"]])
    ax.set_xlabel("Umbral")
    ax.set_title(f"Regla \"{fam}\" ({VENTANA} ruedas)", fontsize=10.5, fontweight="bold", loc="left")
    ax.spines[["top", "right"]].set_visible(False)
    if fam == "por muestreo":
        i = list(t["umbral"]).index(UMBRAL)
        ax.annotate("elegida", (i - 0.2, t["shocks"].iloc[i]), xytext=(i + 0.4, t["shocks"].iloc[i] + 8),
                    arrowprops=dict(arrowstyle="->", color="#12263A"), fontsize=9)
axs[0].set_ylabel("Ruedas marcadas como shock")
axs[0].legend(frameon=False, fontsize=9)
fig.tight_layout()
fig.savefig(AQUI / "u2_reglas.png", dpi=160, facecolor="white")

print(pd.DataFrame(res).to_string(index=False))
print()
print(verif.to_string(index=False))
print()
print(sh[["evento_id", "rueda", "tipo", "z_shock", "n_notas", "dia_electoral", "coincide_con_shock_gino"]].round(2).to_string(index=False))
