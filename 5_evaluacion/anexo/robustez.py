"""
Anexo · pruebas de robustez del modelo predictivo — tesis versión 6.0
Fase 5 de CRISP-DM (evaluación).

Se repite la comparación A contra B en las dos direcciones cambiando UNA decisión por vez, para ver si
el resultado principal depende de ella. Las variantes se fijaron antes de ver los resultados del modelo
principal (PLAN_VERSION_6.md, sección 2), salvo "sin abril de 2026", que se agregó al ver que abril
(el mes sin iProfesional) cae dentro del test.

  principal                    el modelo de 4_modelado (control: tiene que dar lo mismo)
  con_regimen                  se agrega el régimen del HMM a A y a B (0 = Calmo, 1 = Moderado, 2 = Tenso).
                               Se usa el régimen FILTRADO, que solo usa información hasta ese día; el
                               suavizado usa toda la muestra y filtraría el futuro.
  ventana_10, ventana_60       sentimiento inesperado y volumen anormal con 10 o 60 ruedas en lugar de 20
                               (el VIX queda con 20, la definición del lado bursátil)
  corte_2026_01, corte_2026_03 el test empieza el 01/01/2026 o el 01/03/2026 en lugar del 01/02/2026
  sin_dias_electorales         se sacan las filas cuya rueda o rueda siguiente es un día electoral
  sin_abril_2026               se saca abril de 2026 (sin iProfesional en el corpus)
  sentimiento_por_portal       se usa el sentimiento ajustado por portal (a cada nota se le resta el
                               promedio de su portal), que no depende de qué portales hay cada día

Entradas: dataset_unificado/salidas/dataset_panel.csv y dataset_mercado.csv, y los precios completos
          (2_comprension_de_los_datos/mercado/datos/precios_diarios_47_acciones.csv) para recalcular el
          volumen anormal con otras ventanas.
Salidas: salidas/robustez.csv, salidas/robustez.png, metricas.csv

Uso:  python robustez.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
sys.path.insert(0, str(RAIZ / "4_modelado"))
import modelado_comun as mc   # noqa: E402

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)
DATASET = RAIZ / "3_preparacion_de_los_datos" / "dataset_unificado" / "salidas"
PRECIOS = RAIZ / "2_comprension_de_los_datos" / "mercado" / "datos" / "precios_diarios_47_acciones.csv"
REZAGOS = 5
CORTE_PRINCIPAL = mc.CORTE_TEST
REGIMEN = {"Calmo": 0, "Moderado": 1, "Tenso": 2}
ELECTORALES = {"2025-09-08", "2025-10-27"}

panel0 = pd.read_csv(DATASET / "dataset_panel.csv")
mercado0 = pd.read_csv(DATASET / "dataset_mercado.csv")
precios = pd.read_csv(PRECIOS, parse_dates=["Date"]).sort_values(["ticker", "Date"])
precios["log_vol"] = np.log1p(precios["Volume"])


def inesperado(serie, w):
    return serie - serie.shift(1).rolling(w, min_periods=w).mean()


def vol_anormal(w):
    v = precios.copy()
    v["vol_anormal_w"] = v["log_vol"] - v.groupby("ticker")["log_vol"].transform(lambda x: x.shift(1).rolling(w, min_periods=w).mean())
    v["rueda"] = v["Date"].dt.strftime("%Y-%m-%d")
    return v[["ticker", "rueda", "vol_anormal_w"]]


def armar_panel(ventana=20, portal=False, regimen=False):
    m = mercado0.sort_values("rueda").copy()
    col = "sent_neto_portal" if portal else "sent_neto"
    m["ines"] = inesperado(m[col], ventana)
    d = panel0.drop(columns=["sentimiento_inesperado"]).merge(m[["rueda", "ines"]], on="rueda")
    if ventana != 20:
        d = d.drop(columns=["vol_anormal"]).merge(vol_anormal(ventana).rename(columns={"vol_anormal_w": "vol_anormal"}),
                                                  on=["ticker", "rueda"], how="left")
    d = d.sort_values(["ticker", "rueda"]).reset_index(drop=True)
    g = d.groupby("ticker")
    for k in range(REZAGOS):
        d[f"retorno_t{k}"] = g["retorno"].shift(k)
    d["rueda_siguiente"] = g["rueda"].shift(-1)
    d["retorno_siguiente"] = g["retorno"].shift(-1)
    d["sube"] = (d["retorno_siguiente"] > 0).astype(int)
    d["regimen_num"] = d["regimen_filtrado"].map(REGIMEN)
    va = [f"retorno_t{k}" for k in range(REZAGOS)] + ["vol_anormal", "vix_arg"] + (["regimen_num"] if regimen else [])
    vb = va + ["ines", "sentimiento_propio", "hubo_noticia"]
    d = d[d[vb + ["retorno_siguiente"]].notna().all(axis=1)].reset_index(drop=True)
    return d, "sube", va, vb


def armar_mercado(ventana=20, portal=False, regimen=False):
    d = mercado0.sort_values("rueda").reset_index(drop=True).copy()
    col = "sent_neto_portal" if portal else "sent_neto"
    d["ines"] = inesperado(d[col], ventana)
    for k in range(REZAGOS):
        d[f"ines_t{k}"] = d["ines"].shift(k)
        d[f"ret_merval_t{k}"] = d["ret_merval"].shift(k)
    d["rueda_siguiente"] = d["rueda"].shift(-1)
    d["ines_siguiente"] = d["ines"].shift(-1)
    d["sentimiento_sube"] = (d["ines_siguiente"] > 0).astype(int)
    d["regimen_num"] = d["regimen_filtrado"].map(REGIMEN)
    va = [f"ines_t{k}" for k in range(REZAGOS)] + (["regimen_num"] if regimen else [])
    vb = va + [f"ret_merval_t{k}" for k in range(REZAGOS)] + ["vix_arg"]
    d = d[d[vb + ["ines_siguiente"]].notna().all(axis=1)].reset_index(drop=True)
    return d, "sentimiento_sube", va, vb


VARIANTES = [
    ("principal", {}, None, None),
    ("con_regimen", {"regimen": True}, None, None),
    ("ventana_10", {"ventana": 10}, None, None),
    ("ventana_60", {"ventana": 60}, None, None),
    ("corte_2026_01", {}, "2026-01-01", None),
    ("corte_2026_03", {}, "2026-03-01", None),
    ("sin_dias_electorales", {}, None, "electorales"),
    ("sin_abril_2026", {}, None, "abril"),
    ("sentimiento_por_portal", {"portal": True}, None, None),
]

filas = []
for nombre, kw, corte, filtro in VARIANTES:
    for direccion, armar in (("noticias → precio", armar_panel), ("precio → sentimiento", armar_mercado)):
        d, obj, va, vb = armar(**kw)
        if filtro == "electorales":
            d = d[~d["rueda"].isin(ELECTORALES) & ~d["rueda_siguiente"].isin(ELECTORALES)]
        if filtro == "abril":
            d = d[~((d["rueda"] >= "2026-04-01") & (d["rueda"] <= "2026-04-30"))]
        d = d.reset_index(drop=True)
        mc.CORTE_TEST = corte or CORTE_PRINCIPAL
        metr, delta, _, _, _, info = mc.correr_comparacion(d, obj, va, vb)
        for alg in ("logistica", "random_forest"):
            a = metr.query("algoritmo == @alg and modelo == 'A'").iloc[0]
            b = metr.query("algoritmo == @alg and modelo == 'B'").iloc[0]
            x = delta.set_index("algoritmo").loc[alg]
            filas.append({"variante": nombre, "direccion": direccion, "algoritmo": alg,
                          "auc_A": a["auc"], "auc_B": b["auc"], "delta_auc": x["delta_auc"],
                          "ic95_inf": x["ic95_inf"], "ic95_sup": x["ic95_sup"], "p_unilateral": x["p_unilateral"],
                          "aporta": bool(x["ic95_inf"] > 0), "filas_entrenamiento": info["filas_entrenamiento"],
                          "filas_test": info["filas_test"], "ruedas_test": info["ruedas_test"],
                          "primera_rueda_test": info["primera_rueda_test"]})
        print(f"{nombre:24s} {direccion:22s} ΔAUC logística {filas[-2]['delta_auc']:+.3f} "
              f"[{filas[-2]['ic95_inf']:+.3f}; {filas[-2]['ic95_sup']:+.3f}]", flush=True)
mc.CORTE_TEST = CORTE_PRINCIPAL

R = pd.DataFrame(filas)
R.round(4).to_csv(SALIDAS / "robustez.csv", index=False, encoding="utf-8")

# ── Control y métricas ───────────────────────────────────────────────────
ppal = {}
for sub, archivo in (("noticias_a_precio", "noticias → precio"), ("precio_a_sentimiento", "precio → sentimiento")):
    ref = pd.read_csv(RAIZ / "4_modelado" / sub / "salidas" / "delta_auc.csv").set_index("algoritmo")
    rep = R[(R["variante"] == "principal") & (R["direccion"] == archivo)].set_index("algoritmo")
    ppal[archivo] = bool(np.allclose(ref.loc[["logistica", "random_forest"], "delta_auc"], rep["delta_auc"], atol=1e-3))
res = [{"metrica": "principal_reproduce_4_modelado", "valor": "sí" if all(ppal.values()) else "no"}]
for direccion in R["direccion"].unique():
    t = R[(R["direccion"] == direccion) & (R["algoritmo"] == "logistica")]
    clave = "noticias_a_precio" if direccion.startswith("noticias") else "precio_a_sentimiento"
    res.append({"metrica": f"{clave}_variantes_que_aportan_logistica", "valor": f"{int(t['aporta'].sum())} de {len(t)}"})
    t2 = R[(R["direccion"] == direccion) & (R["algoritmo"] == "random_forest")]
    res.append({"metrica": f"{clave}_variantes_que_aportan_rf", "valor": f"{int(t2['aporta'].sum())} de {len(t2)}"})
    res.append({"metrica": f"{clave}_delta_auc_min_logistica", "valor": round(t["delta_auc"].min(), 4),
                "detalle": t.loc[t["delta_auc"].idxmin(), "variante"]})
    res.append({"metrica": f"{clave}_delta_auc_max_logistica", "valor": round(t["delta_auc"].max(), 4),
                "detalle": t.loc[t["delta_auc"].idxmax(), "variante"]})
pd.DataFrame(res).to_csv(AQUI / "metricas_robustez.csv", index=False, encoding="utf-8")

# ── Figura: ΔAUC con su intervalo, por variante ──────────────────────────
fig, axs = plt.subplots(1, 2, figsize=(13, 5.2), sharey=True)
orden = [v[0] for v in VARIANTES]
for ax, direccion, color in zip(axs, ("noticias → precio", "precio → sentimiento"), ("#1F6FA3", "#B5700F")):
    t = R[(R["direccion"] == direccion) & (R["algoritmo"] == "logistica")].set_index("variante").loc[orden]
    y = np.arange(len(orden))[::-1]
    ax.errorbar(t["delta_auc"], y, xerr=[t["delta_auc"] - t["ic95_inf"], t["ic95_sup"] - t["delta_auc"]],
                fmt="o", color=color, ecolor=color, capsize=3, lw=1.4)
    ax.axvline(0, color="#999", lw=1, ls="--")
    ax.set_yticks(y, [o.replace("_", " ") for o in orden])
    ax.set_xlabel("ΔAUC = AUC(B) − AUC(A), con IC 95 %")
    ax.set_title(direccion, loc="left", fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
fig.suptitle("Robustez: cada fila cambia una sola decisión (regresión logística)", x=0.01, ha="left", fontsize=12)
fig.tight_layout()
fig.savefig(SALIDAS / "robustez.png", dpi=160, facecolor="white")

print()
print(R[R["algoritmo"] == "logistica"][["variante", "direccion", "auc_A", "auc_B", "delta_auc", "ic95_inf", "ic95_sup", "aporta",
                                         "filas_entrenamiento", "ruedas_test"]].round(3).to_string(index=False))
print()
print(pd.DataFrame(res).to_string(index=False))
