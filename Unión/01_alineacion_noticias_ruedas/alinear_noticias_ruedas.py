"""
U1 · Cada noticia a su rueda — tesis version 3.0 (Unión)

Asigna cada nota del corpus a la rueda de BYMA en la que el mercado pudo reaccionar a ella:
  - la hora de publicación se pasa a hora argentina (Clarín, Infobae y La Nación la traen en UTC);
  - si la nota salió antes de las 17:00 de un día con rueda, cuenta para esa rueda;
  - si salió a las 17:00 o después, o en un día sin rueda (fin de semana, feriado), cuenta para la
    primera rueda posterior.
Además marca las notas con "hora sospechosa": una hora que concentra más del 3% de las notas de su
portal (Clarín 07:00/07:08, Ámbito 00:00, TN 05:55...), que no puede ser la hora real de cada nota.

Solo lee. Entradas:
  Lado Noticias/noticias/resultados/*.jsonl                 corpus (url, fecha_publicacion)
  Lado Noticias/noticias/analisis_duplicados/...json        duplicados semánticos (se excluyen, como hace Gino)
  Lado Noticias/sentimiento_finbert/finetuned_articulos.csv control: mismas URLs y misma fecha
  Lado Bursatil/03_vix_argentino/vix_arg.csv                calendario de ruedas (02/01/2025 → 30/04/2026)

Salidas (en esta carpeta):
  nota_a_rueda.csv     una fila por nota: hora argentina, rueda, si salió tras el cierre, si la hora es sospechosa
  notas_por_rueda.csv  una fila por rueda de la ventana de la unión: cantidad de notas (variable de atención, D2)
  resumen_u1.csv       cifras del paso (las usa el PDF)
  verificaciones.csv   los controles automáticos y si pasaron
  u1_alineacion.png    figura del paso

Uso:  python alinear_noticias_ruedas.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).parent
RAIZ = AQUI.parent.parent
NOTICIAS = RAIZ / "Lado Noticias"
BURSATIL = RAIZ / "Lado Bursatil"

CIERRE_BYMA = 17                 # hora de cierre de la rueda (hora argentina); 17:00 en punto ya es "después"
INICIO_UNION = "2025-05-05"      # primera rueda de la ventana de la unión (decisión U0)
UMBRAL_HORA_SOSPECHOSA = 0.03    # una hora que junta más del 3% de las notas de su portal
# Mismo orden que serie_completa_finetuned.py: ante una URL repetida manda la primera aparición,
# así el portal de cada nota coincide con el de finetuned_articulos.csv.
ARCHIVOS = ["ambito_economia", "ambito_finanzas", "clarin_economia", "clarin_sitemap", "eleconomista_sitemap",
            "infobae_economia", "iprofesional_sitemap", "lanacion_economia", "tn_economia"]


# ── 1. Corpus ────────────────────────────────────────────────────────────
reporte = NOTICIAS / "noticias" / "analisis_duplicados" / "reporte_dedup_semantico.json"
excluir = set(json.loads(reporte.read_text(encoding="utf-8")).get("urls_a_eliminar", [])) if reporte.exists() else set()

filas, vistas = [], set()
for archivo in ARCHIVOS:
    for linea in open(NOTICIAS / "noticias" / "resultados" / f"{archivo}.jsonl", encoding="utf-8"):
        if not linea.strip():
            continue
        a = json.loads(linea)
        url = a.get("url")
        if not url or url in excluir or url in vistas:
            continue
        vistas.add(url)
        filas.append({"url": url, "portal": archivo, "fecha_publicacion": a.get("fecha_publicacion") or ""})
notas = pd.DataFrame(filas)

# ── 2. Hora argentina ────────────────────────────────────────────────────
hora_ar = (pd.to_datetime(notas["fecha_publicacion"], utc=True, format="mixed")
           .dt.tz_convert("America/Argentina/Buenos_Aires").dt.tz_localize(None))
notas["hora_ar"] = hora_ar.dt.strftime("%Y-%m-%d %H:%M")
notas["fecha_ar"] = hora_ar.dt.strftime("%Y-%m-%d")
notas["fecha_texto"] = notas["fecha_publicacion"].str[:10]          # la fecha que usa la serie de Gino
notas["cambia_por_huso"] = notas["fecha_ar"] != notas["fecha_texto"]
notas["tras_cierre"] = hora_ar.dt.hour >= CIERRE_BYMA

hhmm = hora_ar.dt.strftime("%H:%M")
frecuencia = hhmm.groupby(notas["portal"]).value_counts(normalize=True)
sospechosas = set(frecuencia[frecuencia > UMBRAL_HORA_SOSPECHOSA].index)
notas["hora_sospechosa"] = [(p, h) in sospechosas for p, h in zip(notas["portal"], hhmm)]

# ── 3. Rueda ─────────────────────────────────────────────────────────────
vix = pd.read_csv(BURSATIL / "03_vix_argentino" / "vix_arg.csv", parse_dates=["fecha"])
ruedas = pd.DatetimeIndex(vix["fecha"])
dia = hora_ar.dt.normalize()
notas["dia_con_rueda"] = dia.isin(ruedas)
desde = dia + pd.to_timedelta(notas["tras_cierre"].astype(int), unit="D")   # primer día en que pudo operarse
pos = ruedas.searchsorted(desde)
tiene = pos < len(ruedas)
rueda = pd.Series(pd.NaT, index=notas.index, dtype="datetime64[ns]")
rueda[tiene] = ruedas[pos[tiene]]
notas["rueda"] = rueda.dt.strftime("%Y-%m-%d")
notas["dias_hasta_rueda"] = (rueda - dia).dt.days
notas["motivo"] = "rueda_del_dia"
notas.loc[tiene & (rueda != dia) & notas["tras_cierre"] & notas["dia_con_rueda"], "motivo"] = "tras_el_cierre"
notas.loc[tiene & (rueda != dia) & ~notas["dia_con_rueda"], "motivo"] = "dia_sin_rueda"
notas.loc[~tiene, "motivo"] = "despues_del_calendario"
notas["en_ventana_union"] = tiene & (rueda >= pd.Timestamp(INICIO_UNION))
notas.loc[tiene & (rueda < pd.Timestamp(INICIO_UNION)), "motivo"] += "|antes_de_la_ventana"

columnas = ["url", "portal", "fecha_publicacion", "hora_ar", "fecha_ar", "fecha_texto", "cambia_por_huso",
            "tras_cierre", "dia_con_rueda", "rueda", "dias_hasta_rueda", "motivo", "en_ventana_union", "hora_sospechosa"]
notas[columnas].to_csv(AQUI / "nota_a_rueda.csv", index=False, encoding="utf-8")

# ── 4. Notas por rueda (variable de atención de los medios) ──────────────
en = notas[notas["en_ventana_union"]]
comun = ruedas[ruedas >= pd.Timestamp(INICIO_UNION)].strftime("%Y-%m-%d")
por_rueda = pd.DataFrame(index=pd.Index(comun, name="rueda"))
por_rueda["n_notas"] = en.groupby("rueda").size()
por_rueda["n_mismo_dia"] = en[en["motivo"] == "rueda_del_dia"].groupby("rueda").size()
por_rueda["n_tras_cierre"] = en[en["motivo"] == "tras_el_cierre"].groupby("rueda").size()
por_rueda["n_dia_sin_rueda"] = en[en["motivo"] == "dia_sin_rueda"].groupby("rueda").size()
por_rueda["n_hora_sospechosa"] = en[en["hora_sospechosa"]].groupby("rueda").size()
for archivo in ARCHIVOS:
    por_rueda[f"n_{archivo}"] = en[en["portal"] == archivo].groupby("rueda").size()
por_rueda = por_rueda.fillna(0).astype(int)
por_rueda.to_csv(AQUI / "notas_por_rueda.csv", encoding="utf-8")

# ── 5. Controles ─────────────────────────────────────────────────────────
art = pd.read_csv(NOTICIAS / "sentimiento_finbert" / "finetuned_articulos.csv", usecols=["url", "fuente", "fecha"])
cruce = notas.merge(art, on="url", how="outer", indicator=True)
diag = pd.read_csv(AQUI.parent / "00_pipeline_union" / "diagnostico_resumen.csv").set_index("metrica")["valor"]
con_rueda = notas[notas["rueda"].notna()]
controles = [
    ("Cada nota tiene una rueda o un motivo para no tenerla", notas["motivo"].notna().all() and
     (notas["rueda"].notna() | (notas["motivo"] == "despues_del_calendario")).all()),
    ("Ninguna nota va a una rueda anterior a su publicación", (con_rueda["dias_hasta_rueda"] >= 0).all()),
    ("Ninguna nota publicada tras el cierre queda en la rueda del mismo día",
     not ((notas["tras_cierre"]) & (notas["dias_hasta_rueda"] == 0)).any()),
    ("Las URLs coinciden una a una con finetuned_articulos.csv", (cruce["_merge"] == "both").all()),
    ("El portal coincide con finetuned_articulos.csv", (cruce["portal"] == cruce["fuente"]).all()),
    ("La fecha sin convertir reproduce la fecha de Gino", (cruce["fecha_texto"] == cruce["fecha"]).all()),
    ("Todas las ruedas de la ventana tienen noticias", (por_rueda["n_notas"] > 0).all()),
    ("Cantidad de ruedas igual al diagnóstico", len(por_rueda) == diag["ruedas_ventana_comun"]),
    ("Mínimo y mediana de notas por rueda iguales al diagnóstico",
     por_rueda["n_notas"].min() == diag["articulos_por_rueda_min"] and por_rueda["n_notas"].median() == diag["articulos_por_rueda_mediana"]),
    ("Notas con hora sospechosa iguales al diagnóstico", notas["hora_sospechosa"].sum() == diag["articulos_hora_por_defecto"]),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── 6. Resumen ───────────────────────────────────────────────────────────
r = []
def m(clave, valor, detalle=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle})

m("notas", len(notas))
m("notas_en_ventana_union", int(notas["en_ventana_union"].sum()), f"ruedas {comun[0]} a {comun[-1]}")
m("notas_antes_de_la_ventana", int(notas["motivo"].str.contains("antes_de_la_ventana").sum()), "ruedas de enero a abril de 2025")
m("notas_despues_del_calendario", int((notas["motivo"] == "despues_del_calendario").sum()), "después del cierre del 30/04/2026")
for motivo in ("rueda_del_dia", "tras_el_cierre", "dia_sin_rueda"):
    m(f"en_ventana_{motivo}", int((en["motivo"] == motivo).sum()))
m("pct_en_ventana_cambia_de_dia", round(100 * (en["motivo"] != "rueda_del_dia").mean(), 1))
m("notas_cambia_por_huso", int(notas["cambia_por_huso"].sum()), "UTC → hora argentina cambia la fecha")
m("notas_hora_sospechosa", int(notas["hora_sospechosa"].sum()),
  "; ".join(sorted({f"{p.split('_')[0]} {h}" for p, h in sospechosas})))
m("pct_hora_sospechosa", round(100 * notas["hora_sospechosa"].mean(), 1))
m("ruedas_ventana", len(por_rueda))
for k, f in (("min", "min"), ("mediana", "median"), ("max", "max")):
    m(f"notas_por_rueda_{k}", int(getattr(por_rueda["n_notas"], f)()))
m("rueda_mas_notas", por_rueda["n_notas"].idxmax(), str(int(por_rueda["n_notas"].max())))
lunes = pd.to_datetime(por_rueda.index).dayofweek == 0
m("notas_mediana_lunes", int(por_rueda.loc[lunes, "n_notas"].median()), "los lunes reciben el fin de semana")
m("notas_mediana_resto", int(por_rueda.loc[~lunes, "n_notas"].median()))
m("max_dias_hasta_rueda", int(en["dias_hasta_rueda"].max()), en.loc[en["dias_hasta_rueda"].idxmax(), "fecha_ar"])
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u1.csv", index=False, encoding="utf-8")

# ── 7. Figura ────────────────────────────────────────────────────────────
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8.2), gridspec_kw={"height_ratios": [1, 1.15]})
horas = hora_ar.dt.hour + hora_ar.dt.minute / 60
a1.hist(horas[~notas["hora_sospechosa"]], bins=96, range=(0, 24), color="#4A90C8", label="Hora real")
a1.hist(horas[notas["hora_sospechosa"]], bins=96, range=(0, 24), color="#D7301F", label="Hora sospechosa (repetida)")
a1.axvline(CIERRE_BYMA, color="#12263A", lw=1.6, ls="--")
a1.axvspan(11, CIERRE_BYMA, color="#2E8B57", alpha=0.08)
a1.text(14, a1.get_ylim()[1] * 0.92, "Rueda abierta\n(11 a 17 h)", ha="center", va="top", fontsize=9, color="#2E8B57")
a1.text(CIERRE_BYMA + 0.2, a1.get_ylim()[1] * 0.92, "17:00 · cierre: lo que sale\ndespués va a la rueda siguiente",
        va="top", fontsize=9, color="#12263A")
a1.set_xlim(0, 24); a1.set_xticks(range(0, 25, 2)); a1.set_xlabel("Hora de publicación (hora argentina)")
a1.set_ylabel("Notas (cada 15 min)"); a1.legend(loc="upper left", frameon=False, fontsize=9)
a1.set_title("¿A qué hora salen las notas?", loc="left", fontsize=12, fontweight="bold")

x = pd.to_datetime(por_rueda.index)
a2.bar(x, por_rueda["n_mismo_dia"], width=1, color="#4A90C8", label="Publicadas ese día antes de las 17:00")
a2.bar(x, por_rueda["n_tras_cierre"], width=1, bottom=por_rueda["n_mismo_dia"], color="#F2A900", label="Publicadas la rueda anterior después del cierre")
a2.bar(x, por_rueda["n_dia_sin_rueda"], width=1, bottom=por_rueda["n_mismo_dia"] + por_rueda["n_tras_cierre"],
       color="#8C6BB1", label="Publicadas en un día sin rueda")
a2.axvspan(pd.Timestamp("2026-04-01"), pd.Timestamp("2026-04-30"), color="#D7301F", alpha=0.07)
a2.text(pd.Timestamp("2026-04-15"), a2.get_ylim()[1] * 0.97, "abril 2026:\nsin iProfesional", ha="center", va="top", fontsize=8.5, color="#D7301F")
a2.set_ylabel("Notas por rueda"); a2.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=1)
a2.set_title("Cantidad de notas que recibe cada rueda", loc="left", fontsize=12, fontweight="bold")
for ax in (a1, a2):
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(AQUI / "u1_alineacion.png", dpi=160, facecolor="white")

print(pd.DataFrame(r).to_string(index=False))
print()
print(verif.to_string(index=False))
