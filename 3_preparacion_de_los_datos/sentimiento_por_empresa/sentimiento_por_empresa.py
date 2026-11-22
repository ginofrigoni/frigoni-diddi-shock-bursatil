"""
Sentimiento por empresa y por rueda — tesis versión 6.0
Fase 3 de CRISP-DM (preparación de los datos): construir atributos derivados.

Hace el cruce entidad × oración (cruce_ner_sentimiento.py, en esta carpeta) agrupando por RUEDA (la que
le asignó la regla de las 17:00 a cada nota). Se importan sus funciones (normalización del texto,
equivalencias de indicadores, sentimiento neto), se une cada mención con el sentimiento de su oración por
(url, número de oración) exigiendo que el texto coincida, y cada oración cuenta una sola vez por entidad.

Después arma el panel de las 47 acciones × 244 ruedas: si en una rueda no hubo noticias de la empresa,
el sentimiento queda vacío y hubo_noticia = 0 (no se rellena con 0, que significaría "sentimiento neutro").
La marca empresa_con_cobertura = 1 indica las empresas con noticias en al menos 90 ruedas (en la 5.0 esta
columna se llamaba sentimiento_propio; se renombró para que ese nombre quede para el valor, decisión D4).

Cambios de la 6.0: rutas nuevas, 3 clases, el renombre de la marca, y los controles se hacen contra la
salida del cruce de esta misma carpeta (antes, contra la del lado de noticias).

Entradas:
  datos/ner_oraciones.csv                                     menciones por oración
  datos/cobertura_por_ticker.csv                              diagnóstico de cobertura de la 5.0 (control)
  ../sentimiento_finbeto/salidas/beto_oraciones_finetuned.csv sentimiento por oración (FinBETO 3 clases)
  salidas/ner_sentimiento_diario.csv, ner_sentimiento_reporte.json   salida del cruce (control)
  ../regla_17/salidas/nota_a_rueda.csv                        rueda de cada nota
  2_comprension_de_los_datos/mercado/datos/panel_acciones_final.csv  las 47 acciones
Salidas (salidas/):
  sentimiento_entidad_rueda.csv  una fila por rueda × entidad (empresas e indicadores) con sentimiento
  panel_empresas_rueda.csv       47 acciones × 244 ruedas, con hubo_noticia y empresa_con_cobertura
  cobertura_empresas.csv         ruedas con noticias de cada acción
  verificaciones.csv, cobertura_empresas.png;  ../metricas.csv

Uso:  python cruce_ner_sentimiento.py  y después  python sentimiento_por_empresa.py
"""

import collections
import csv
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")
csv.field_size_limit(10 ** 9)

AQUI = Path(__file__).resolve().parent
PREP = AQUI.parent
RAIZ = PREP.parent
SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)
REF_50 = RAIZ.parent / "tesis version 5.0" / "Unión" / "03_sentimiento_por_empresa"
sys.path.insert(0, str(AQUI))
import cruce_ner_sentimiento as gino   # noqa: E402  (mismas funciones que el cruce)

MIN_RUEDAS_PROPIO = 90       # decisión U0 (95), bajada a 90 el 24/10 para que entre ALUA (94 ruedas exactas)
CLASES = gino.CLASES
TIPOS = gino.TIPOS_DIARIOS   # EMP_MERVAL e IND_ECO

# ── 1. Rueda de cada nota (U1) ───────────────────────────────────────────
u1 = pd.read_csv(PREP / "regla_17" / "salidas" / "nota_a_rueda.csv",
                 usecols=["url", "rueda", "en_ventana_union"])
rueda_de = dict(zip(u1["url"], u1["rueda"]))
en_ventana = set(u1.loc[u1["en_ventana_union"], "url"])
ruedas = sorted(u1.loc[u1["en_ventana_union"], "rueda"].unique())

# ── 2. Cruce, igual al de Gino, acumulando por fecha (control) y por rueda ─
print("Leyendo sentimiento por oración...")
sent = {}
with open(PREP / "sentimiento_finbeto" / "salidas" / "beto_oraciones_finetuned.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        sent[(r["url"], r["or_idx"])] = (gino.norm(r["oracion"]), r["label"])

print("Cruzando con ner_oraciones.csv...")
vistos, oraciones_ner, unidas, sin_idx, texto_distinto = set(), set(), set(), set(), set()
por_fecha = collections.defaultdict(collections.Counter); arts_fecha = collections.defaultdict(set)
por_rueda = collections.defaultdict(collections.Counter); arts_rueda = collections.defaultdict(set)
sin_rueda = set()
oraciones_en_ventana = 0     # control: menciones de notas de la ventana, contadas antes de agrupar
with open(AQUI / "datos" / "ner_oraciones.csv", encoding="utf-8", newline="") as f:
    for r in csv.DictReader(f):
        k = (r["url"], r["oracion_idx"])
        oraciones_ner.add(k)
        s = sent.get(k)
        if s is None:
            sin_idx.add(k); continue
        if s[0] != gino.norm(r["oracion"]):
            texto_distinto.add(k); continue
        unidas.add(k)
        ent = gino.canonico(r["entidad"].strip().lower(), r["tipo"])
        v = (k, ent, r["tipo"])
        if v in vistos:
            continue
        vistos.add(v)
        if r["tipo"] not in TIPOS:
            continue
        kf = (r["fecha"], ent, r["tipo"], r["subtipo"])
        por_fecha[kf][s[1]] += 1; arts_fecha[kf].add(r["url"])
        if r["url"] not in en_ventana:
            sin_rueda.add(r["url"]); continue
        oraciones_en_ventana += 1
        kr =(rueda_de[r["url"]], ent, r["tipo"], r["subtipo"])
        por_rueda[kr][s[1]] += 1; arts_rueda[kr].add(r["url"])


def tabla(acum, arts, nombre_fecha):
    filas = [{nombre_fecha: fe, "entidad": e, "tipo": t, "subtipo": su, "n_articulos": len(arts[(fe, e, t, su)]),
              **gino.fila_resumen(a)} for (fe, e, t, su), a in acum.items()]
    return pd.DataFrame(filas).sort_values([nombre_fecha, "tipo", "entidad"]).reset_index(drop=True)


diario = tabla(por_fecha, arts_fecha, "fecha")
por_r = tabla(por_rueda, arts_rueda, "rueda")
por_r.to_csv(SALIDAS / "sentimiento_entidad_rueda.csv", index=False, encoding="utf-8")

# ── 3. Panel 47 acciones × 244 ruedas ────────────────────────────────────
panel_acc = pd.read_csv(RAIZ / "2_comprension_de_los_datos" / "mercado" / "datos" / "panel_acciones_final.csv")
panel_acc["entidad"] = panel_acc["ticker"].str.replace(".BA", "", regex=False).str.lower()
emp = por_r[por_r["tipo"] == "EMP_MERVAL"].rename(columns={"sent_neto": "sent_neto_empresa"})
grilla = pd.MultiIndex.from_product([panel_acc["ticker"], ruedas], names=["ticker", "rueda"]).to_frame(index=False)
grilla = grilla.merge(panel_acc[["ticker", "entidad", "empresa", "sector"]], on="ticker")
cols = (["n_articulos", "n_oraciones"] + ["n_" + c.lower() for c in CLASES] + ["pct_" + c.lower() for c in CLASES]
        + ["sent_neto_empresa"])
panel = grilla.merge(emp[["rueda", "entidad"] + cols], on=["rueda", "entidad"], how="left")
panel["hubo_noticia"] = panel["n_articulos"].notna().astype(int)
for c in ["n_articulos", "n_oraciones"] + ["n_" + c.lower() for c in CLASES]:
    panel[c] = panel[c].fillna(0).astype(int)         # cantidades: 0 es correcto (no hubo menciones)
# pct_* y sent_neto_empresa quedan vacíos: sin noticias no hay tono que medir.
cob = panel.groupby("ticker").agg(ruedas_con_noticias=("hubo_noticia", "sum"), articulos=("n_articulos", "sum"),
                                  oraciones=("n_oraciones", "sum"), n_pos=("n_pos", "sum"), n_neg=("n_neg", "sum")).reset_index()
# Tono total de la empresa en la ventana, con la misma fórmula de Gino: (positivas − negativas) / oraciones.
cob["sent_neto_total"] = (100 * (cob["n_pos"] - cob["n_neg"]) / cob["oraciones"].replace(0, np.nan)).round(1)
cob = cob.drop(columns=["n_pos", "n_neg"])
cob = panel_acc[["ticker", "empresa", "sector", "oficial"]].merge(cob, on="ticker")
cob["pct_ruedas"] = (100 * cob["ruedas_con_noticias"] / len(ruedas)).round(1)
cob["empresa_con_cobertura"] = cob["ruedas_con_noticias"] >= MIN_RUEDAS_PROPIO
cob = cob.sort_values("ruedas_con_noticias", ascending=False).reset_index(drop=True)
diag = pd.read_csv(AQUI / "datos" / "cobertura_por_ticker.csv")
cob = cob.merge(diag[["ticker", "ruedas_con_noticias"]].rename(columns={"ruedas_con_noticias": "ruedas_diagnostico"}), on="ticker")
cob.to_csv(SALIDAS / "cobertura_empresas.csv", index=False, encoding="utf-8")
propias = set(cob.loc[cob["empresa_con_cobertura"], "ticker"])
panel["empresa_con_cobertura"] = panel["ticker"].isin(propias)
panel = panel[["ticker", "empresa", "sector", "rueda", "hubo_noticia", "empresa_con_cobertura"] + cols]
panel.to_csv(SALIDAS / "panel_empresas_rueda.csv", index=False, encoding="utf-8")

# ── 4. Controles ─────────────────────────────────────────────────────────
original = pd.read_csv(SALIDAS / "ner_sentimiento_diario.csv")
clave = ["fecha", "entidad", "tipo", "subtipo"]
comp = original.merge(diario, on=clave, how="outer", suffixes=("_gino", "_u3"), indicator=True)
num = ["n_articulos", "n_oraciones"] + ["n_" + c.lower() for c in CLASES] + ["sent_neto"]
iguales = (comp["_merge"] == "both").all() and all(np.allclose(comp[c + "_gino"], comp[c + "_u3"]) for c in num)
rep = json.loads((SALIDAS / "ner_sentimiento_reporte.json").read_text(encoding="utf-8"))
p50 = pd.read_csv(REF_50 / "panel_empresas_rueda.csv") if (REF_50 / "panel_empresas_rueda.csv").exists() else None
controles = [
    ("Agrupando por fecha se reproduce ner_sentimiento_diario.csv del cruce, fila por fila", bool(iguales)),
    ("La cobertura del cruce coincide con su reporte",
     len(oraciones_ner) == rep["oraciones_ner"] and len(unidas) == rep["unidas"] and len(texto_distinto) == rep["texto_distinto"]),
    ("Todas las notas con menciones están en U1", all(u in rueda_de for u in sin_rueda)),
    ("Ninguna oración se pierde al pasar de fecha a rueda (mismas notas de la ventana)",
     int(por_r["n_oraciones"].sum()) == oraciones_en_ventana),
    ("El panel tiene 47 acciones × 244 ruedas sin repetidos",
     len(panel) == 47 * len(ruedas) and not panel.duplicated(["ticker", "rueda"]).any()),
    ("Sin noticia ⇔ sentimiento vacío", bool(((panel["hubo_noticia"] == 0) == panel["sent_neto_empresa"].isna()).all())),
    ("Todos los tickers de las menciones están entre las 47 acciones",
     set(emp["entidad"]) <= set(panel_acc["entidad"])),
    ("Las empresas con cobertura son las mismas 17 de la 5.0",
     p50 is not None and propias == set(p50.loc[p50["sentimiento_propio"], "ticker"]) and len(propias) == 17),
    ("hubo_noticia es igual al de la 5.0 en cada acción y rueda (no depende de la etiqueta)",
     p50 is not None and panel.set_index(["ticker", "rueda"])["hubo_noticia"].equals(p50.set_index(["ticker", "rueda"])["hubo_noticia"])),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(SALIDAS / "verificaciones.csv", index=False, encoding="utf-8")

# ── 5. Resumen ───────────────────────────────────────────────────────────
res = []
def m(clave_, valor, detalle=""):
    res.append({"metrica": clave_, "valor": valor, "detalle": detalle})

m("oraciones_con_entidades", len(oraciones_ner)); m("oraciones_unidas", len(unidas))
m("cobertura_cruce_pct", round(100 * len(unidas) / len(oraciones_ner), 2))
m("filas_entidad_rueda", len(por_r)); m("filas_empresa_rueda", int(panel["hubo_noticia"].sum()))
m("notas_con_mencion_fuera_de_ventana", len(sin_rueda))
m("ruedas", len(ruedas))
m("empresas_con_cobertura", len(propias), f"al menos {MIN_RUEDAS_PROPIO} ruedas con noticias")
m("empresas_sin_mencion", int((cob["ruedas_con_noticias"] == 0).sum()), ", ".join(cob.loc[cob["ruedas_con_noticias"] == 0, "ticker"].str.replace(".BA", "")))
m("empresas_menos_10_ruedas", int((cob["ruedas_con_noticias"] < 10).sum()))
dif = cob[cob["ruedas_con_noticias"] != cob["ruedas_diagnostico"]]
m("empresas_con_cobertura_distinta_al_diagnostico", len(dif),
  "; ".join(f"{t.replace('.BA', '')} {int(a)}→{int(b)}" for t, a, b in zip(dif["ticker"], dif["ruedas_diagnostico"], dif["ruedas_con_noticias"])))
diag_prop = set(diag.loc[diag["var_propio"], "ticker"])
m("cambio_lista_empresas_con_cobertura", "no" if diag_prop == propias else "sí",
  f"entran: {sorted(propias - diag_prop)} · salen: {sorted(diag_prop - propias)}")
for _, x in cob.head(5).iterrows():
    m(f"top_{x['ticker'].replace('.BA', '')}", int(x["ruedas_con_noticias"]), str(int(x["articulos"])))
prop = panel[panel["empresa_con_cobertura"] & (panel["hubo_noticia"] == 1)]
med = prop.groupby("ticker")["sent_neto_empresa"].mean().sort_values()
m("sent_empresa_mas_negativa", round(med.iloc[0], 1), med.index[0].replace(".BA", ""))
m("sent_empresa_mas_positiva", round(med.iloc[-1], 1), med.index[-1].replace(".BA", ""))
m("mediana_oraciones_por_rueda_empresa", int(prop["n_oraciones"].median()), "en ruedas con noticia, empresas con cobertura")
m("pct_ruedas_empresa_una_oracion", round(100 * (prop["n_oraciones"] == 1).mean(), 1), "en esas ruedas, una sola oración menciona a la empresa")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(res).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")

# ── 6. Figura ────────────────────────────────────────────────────────────
fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 9.5), gridspec_kw={"height_ratios": [1, 1.1]})
c = cob.iloc[::-1]
a1.barh(c["ticker"].str.replace(".BA", ""), c["ruedas_con_noticias"],
        color=np.where(c["empresa_con_cobertura"], "#2C5F8A", "#B8C4CF"), height=0.75)
a1.axvline(MIN_RUEDAS_PROPIO, color="#D7301F", ls="--", lw=1.3)
a1.text(MIN_RUEDAS_PROPIO + 2, 2, f"corte: {MIN_RUEDAS_PROPIO} ruedas", color="#D7301F", fontsize=9)
a1.set_xlabel(f"Ruedas con al menos una noticia de la empresa (de {len(ruedas)})")
a1.tick_params(axis="y", labelsize=6.5)
a1.set_title("¿Cuántas ruedas tienen noticias de cada empresa?  (azul = con cobertura suficiente)", loc="left", fontsize=12, fontweight="bold")
orden = cob.loc[cob["empresa_con_cobertura"], "ticker"].tolist()
mat = panel[panel["ticker"].isin(orden)].pivot(index="ticker", columns="rueda", values="sent_neto_empresa").loc[orden]
mapa = plt.get_cmap("RdYlGn").copy()
mapa.set_bad("#D9D9D9")      # sin noticias: gris, para no confundirlo con el amarillo del sentimiento neutro
im = a2.imshow(np.ma.masked_invalid(mat.to_numpy(dtype=float)), aspect="auto", cmap=mapa, vmin=-60, vmax=60, interpolation="nearest")
a2.set_yticks(range(len(orden)), [t.replace(".BA", "") for t in orden], fontsize=8)
meses = pd.to_datetime(pd.Series(mat.columns))
marcas = [i for i in range(len(meses)) if i == 0 or meses[i].month != meses[i - 1].month]
a2.set_xticks(marcas, [meses[i].strftime("%m/%y") for i in marcas], fontsize=8)
a2.set_title("Sentimiento de cada empresa por rueda (gris = sin noticias de la empresa)", loc="left", fontsize=12, fontweight="bold")
fig.colorbar(im, ax=a2, fraction=0.025, pad=0.01, label="Sentimiento neto")
for ax in (a1,):
    ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(SALIDAS / "cobertura_empresas.png", dpi=160, facecolor="white")

print(pd.DataFrame(res).to_string(index=False))
print()
print(verif.to_string(index=False))
print()
print(cob.head(20).to_string(index=False))
