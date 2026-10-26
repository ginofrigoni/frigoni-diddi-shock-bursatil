"""
U7 · Event study — tesis version 3.0 (Unión)

¿Qué pasa con los precios y el volumen alrededor de las ruedas de noticias extremas? Ventana del evento:
de 3 ruedas antes a 5 después ([−3, +5]); la rueda 0 es la del evento. Se separa en antes [−3, −1], el día
[0] y después [+1, +5]: si el mercado se mueve ANTES del evento, las noticias reflejan lo que ya pasó (U6).

Dos partes:
  A. Ruedas de tono extremo del MERCADO (los shocks de U2). Son noticias generales: si mueven precios, mueven
     al Merval entero. Un modelo de mercado por acción restaría justamente ese movimiento, así que se mide el
     Merval mismo, contra su retorno promedio en la ventana de estimación [−25, −4] (modelo de media constante).
     También el monto operado anormal del mercado. Los días electorales (08/09 y 27/10) no entran al promedio
     habitual, y los eventos cuya ventana incluye uno se analizan aparte: su retorno lo domina la elección.
  B. Ruedas de tono PROPIO extremo de cada una de las 17 empresas (|tono propio| > 2,5 desvíos de su serie).
     Acá sí se usa el modelo de mercado por acción, estimado en [−25, −4] sin los días electorales: retorno anormal
     = retorno − (α + β × retorno del Merval). Mide si ESA acción se movió distinto del mercado. También su volumen
     anormal. Se descartan los eventos cuya ventana incluye un día electoral.

Eventos solapados: dos eventos cuyas ventanas se superponen comparten retornos. Se informan y, como control,
se repite el resultado dejando solo el primero de cada grupo de eventos solapados.

Significancia: test t y test de signo sobre los eventos, y comparación contra fechas al azar (mismas cantidades
de eventos, 5.000 sorteos entre las ruedas con ventana completa): p = proporción de sorteos con un promedio al
menos tan extremo como el observado.

Solo lee. Entradas: ../02_sentimiento_por_rueda/shocks_rueda.csv, ../04_dataset_unificado/dataset_panel.csv,
Lado Bursatil/03_vix_argentino/vix_arg.csv y Lado Bursatil/01_scraping_acciones/precios_diarios_47_acciones.csv
(retornos desde antes de la ventana, para estimar los modelos de los primeros eventos).
Uso:  python event_study.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).parent
UNION = AQUI.parent
BURSATIL = UNION.parent / "Lado Bursatil"
EST_INI, EST_FIN = -25, -4          # ventana de estimación
EV_INI, EV_FIN = -3, 5              # ventana del evento
UMBRAL_PROPIO = 2.5                 # |tono propio| en desvíos de la serie de la empresa
N_SORTEOS = 5000
SEMILLA = 42
ELECTORALES = ["2025-09-08", "2025-10-27"]   # ruedas posteriores a las elecciones: saltos de +21% y −13% del Merval
VENTANAS = {"antes [−3, −1]": (-3, -1), "día [0]": (0, 0), "después [+1, +5]": (1, 5), "total [−3, +5]": (-3, 5)}

# ── Datos ────────────────────────────────────────────────────────────────
vix = pd.read_csv(BURSATIL / "03_vix_argentino" / "vix_arg.csv")
merv = vix.set_index("fecha")["retorno_diario"]
calendario = list(merv.index)
pos = {f: i for i, f in enumerate(calendario)}
panel = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_panel.csv")
mercado = pd.read_csv(UNION / "04_dataset_unificado" / "dataset_mercado.csv").set_index("rueda")
precios = pd.read_csv(BURSATIL / "01_scraping_acciones" / "precios_diarios_47_acciones.csv").sort_values(["ticker", "Date"])
precios["retorno"] = precios.groupby("ticker")["Close"].pct_change()
ret_acc = precios.pivot(index="Date", columns="ticker", values="retorno").reindex(calendario)
shocks = pd.read_csv(UNION / "02_sentimiento_por_rueda" / "shocks_rueda.csv")
ruedas_union = list(mercado.index)


def media_estimacion(fecha):
    """Retorno promedio del Merval en [−25, −4], sin los días electorales (un salto de +21% inflaría lo "habitual")."""
    dias = [d for d in ventana(fecha, EST_INI, EST_FIN) if d not in ELECTORALES]
    return merv.loc[dias].mean()


def ventana(fecha, a, b):
    i = pos[fecha]
    return calendario[i + a: i + b + 1] if i + a >= 0 and i + b < len(calendario) else None


def resumir(car, esperado=None):
    """t, signo y promedio de un vector de CAR por evento."""
    car = np.asarray(car, dtype=float)
    n = len(car)
    t, p_t = stats.ttest_1samp(car, 0) if n > 1 else (np.nan, np.nan)
    positivos = int((car > 0).sum())
    p_signo = stats.binomtest(positivos, n, 0.5).pvalue if n else np.nan
    return {"n": n, "car_medio_pct": 100 * car.mean(), "positivos": positivos, "t": t, "p_t": p_t, "p_signo": p_signo}


# ── A. Ruedas de tono extremo del mercado ────────────────────────────────
eventos = shocks.sort_values("rueda").groupby("evento_id").first().reset_index()
filas = []
for _, e in eventos.iterrows():
    est, ev = ventana(e["rueda"], EST_INI, EST_FIN), ventana(e["rueda"], EV_INI, EV_FIN)
    ar = merv.loc[ev] - media_estimacion(e["rueda"])
    fila = {"evento_id": e["evento_id"], "rueda": e["rueda"], "tipo": e["tipo"], "dia_electoral": e["dia_electoral"] if isinstance(e["dia_electoral"], str) else "",
            "z_shock": e["z_shock"]}
    for nombre, (a, b) in VENTANAS.items():
        fila[f"car_{nombre}"] = ar.iloc[a - EV_INI: b - EV_INI + 1].sum()
        dias = ventana(e["rueda"], a, b)
        fila[f"vol_{nombre}"] = mercado.reindex(dias)["monto_anormal"].mean()
    fila["ar_diario"] = list(ar.values)
    filas.append(fila)
ev_m = pd.DataFrame(filas)
# Solapamientos: la ventana [−3, +5] de un evento se superpone con la del anterior.
idx = ev_m["rueda"].map(pos)
ev_m["solapa_con_anterior"] = idx.diff().fillna(99) <= (EV_FIN - EV_INI)
ev_m["dia_electoral"] = ev_m["dia_electoral"].fillna("")
# Eventos cuya ventana [−3, +5] incluye un día electoral: su retorno lo domina la elección, no el tono.
ev_m["ventana_con_eleccion"] = ev_m["rueda"].map(lambda f: any(d in ELECTORALES for d in ventana(f, EV_INI, EV_FIN)))

# Días electorales: con su propio CAR, sean o no shock de tono.
elect = []
for f, nombre in (("2025-09-08", "elecciones bonaerenses (07/09)"), ("2025-10-27", "elecciones legislativas (26/10)")):
    est, ev = ventana(f, EST_INI, EST_FIN), ventana(f, EV_INI, EV_FIN)
    ar = merv.loc[ev] - media_estimacion(f)
    elect.append({"rueda": f, "evento": nombre, "es_shock_de_tono": f in set(shocks["rueda"]),
                  **{f"car_{k}": 100 * ar.iloc[a - EV_INI: b - EV_INI + 1].sum() for k, (a, b) in VENTANAS.items()},
                  "tono_anormal": mercado.loc[f, "sent_anormal"]})
pd.DataFrame(elect).round(3).to_csv(AQUI / "dias_electorales.csv", index=False, encoding="utf-8")

# Sorteo de fechas al azar entre las ruedas de la unión con ventanas completas.
validas = [f for f in ruedas_union if ventana(f, EST_INI, EST_FIN) and ventana(f, EV_INI, EV_FIN)
          and not any(d in ELECTORALES for d in ventana(f, EV_INI, EV_FIN))]   # el azar, con la misma exclusión
car_azar = {}
for f in validas:
    est, ev = ventana(f, EST_INI, EST_FIN), ventana(f, EV_INI, EV_FIN)
    ar = merv.loc[ev] - media_estimacion(f)
    car_azar[f] = {k: ar.iloc[a - EV_INI: b - EV_INI + 1].sum() for k, (a, b) in VENTANAS.items()}
    car_azar[f].update({f"vol_{k}": mercado.reindex(ventana(f, a, b))["monto_anormal"].mean() for k, (a, b) in VENTANAS.items()})
car_azar = pd.DataFrame(car_azar).T
rng = np.random.default_rng(SEMILLA)


def p_azar(valores, columna):
    n = len(valores)
    # Solo fechas con dato: el volumen anormal no existe antes del 05/05/2025, y un hueco anularía la comparación.
    pool = car_azar[columna].dropna().to_numpy()
    medias = np.array([pool[rng.choice(len(pool), n, replace=False)].mean() for _ in range(N_SORTEOS)])
    obs = np.mean(valores)
    return float((np.abs(medias - medias.mean()) >= abs(obs - medias.mean())).mean())


res_m = []
principal = ev_m[~ev_m["ventana_con_eleccion"]]
for grupo, sel in (("positivos", principal["tipo"] == "positivo"), ("negativos", principal["tipo"] == "negativo")):
    for muestra, filtro in (("todos", sel), ("sin solapados", sel & ~principal["solapa_con_anterior"])):
        g = principal[filtro]
        for nombre in VENTANAS:
            s = resumir(g[f"car_{nombre}"])
            vol = g[f"vol_{nombre}"]
            res_m.append({"eventos": grupo, "muestra": muestra, "ventana": nombre, **s, "p_azar": p_azar(g[f"car_{nombre}"], nombre),
                          "monto_anormal_medio": vol.mean(), "p_vol_t": stats.ttest_1samp(vol, 0).pvalue if len(vol) > 1 else np.nan,
                          "p_vol_azar": p_azar(vol, f"vol_{nombre}")})
res_m = pd.DataFrame(res_m)
res_m.round(4).to_csv(AQUI / "resultados_mercado.csv", index=False, encoding="utf-8")
ev_m.drop(columns="ar_diario").round(5).to_csv(AQUI / "eventos_mercado.csv", index=False, encoding="utf-8")

# Camino promedio del CAR (−3 a +5) por tipo, para la figura.
camino = {}
for tipo in ("positivo", "negativo"):
    g = principal[principal["tipo"] == tipo]
    camino[tipo] = 100 * np.cumsum(np.mean(np.vstack(g["ar_diario"].to_list()), axis=0))

# ── B. Ruedas de tono propio extremo de cada empresa ─────────────────────
propias = sorted(panel.loc[panel["sentimiento_propio"] == 1, "ticker"].unique())
filas_b = []
descartados_eleccion = 0
for t in propias:
    g = panel[panel["ticker"] == t].set_index("rueda")
    tp = g["tono_propio"]
    z = tp / tp.std()
    candidatos = [f for f in z.index[z.abs() > UMBRAL_PROPIO] if ventana(f, EST_INI, EST_FIN) and ventana(f, EV_INI, EV_FIN)]
    con_eleccion = [f for f in candidatos if any(d in ELECTORALES for d in ventana(f, EV_INI, EV_FIN))]
    descartados_eleccion += len(con_eleccion)
    candidatos = [f for f in candidatos if f not in con_eleccion]   # mismo criterio que en el mercado
    ultimo = -99
    for f in candidatos:
        if pos[f] - ultimo <= EV_FIN - EV_INI:      # solapado con el evento anterior de la misma empresa: se descarta
            continue
        ultimo = pos[f]
        ev = ventana(f, EV_INI, EV_FIN)
        est = [d for d in ventana(f, EST_INI, EST_FIN) if d not in ELECTORALES]
        y, x = ret_acc.loc[est, t], merv.loc[est]
        ok = y.notna() & x.notna()
        beta, alfa = np.polyfit(x[ok], y[ok], 1)
        ar = ret_acc.loc[ev, t] - (alfa + beta * merv.loc[ev])
        fila = {"ticker": t, "rueda": f, "tipo": "positivo" if z[f] > 0 else "negativo", "z_tono_propio": z[f],
                "oraciones": g.loc[f, "n_oraciones_empresa"], "beta": beta}
        for nombre, (a, b) in VENTANAS.items():
            fila[f"car_{nombre}"] = ar.iloc[a - EV_INI: b - EV_INI + 1].sum()
            dias = [d for d in ventana(f, a, b) if d in g.index]
            fila[f"vol_{nombre}"] = g.loc[dias, "vol_anormal"].mean() if dias else np.nan
        filas_b.append(fila)
ev_b = pd.DataFrame(filas_b)
ev_b.round(5).to_csv(AQUI / "eventos_empresa.csv", index=False, encoding="utf-8")
res_b = []
for grupo in ("positivo", "negativo"):
    g = ev_b[ev_b["tipo"] == grupo]
    for nombre in VENTANAS:
        s = resumir(g[f"car_{nombre}"])
        vol = g[f"vol_{nombre}"].dropna()
        res_b.append({"eventos": grupo + "s", "ventana": nombre, **s, "vol_anormal_medio": vol.mean(),
                      "p_vol": stats.ttest_1samp(vol, 0).pvalue if len(vol) > 1 else np.nan})
res_b = pd.DataFrame(res_b)
res_b.round(4).to_csv(AQUI / "resultados_empresa.csv", index=False, encoding="utf-8")

# ── Controles ────────────────────────────────────────────────────────────
controles = [
    ("Todos los eventos del mercado tienen ventana de estimación y de evento completas",
     all(ventana(f, EST_INI, EST_FIN) and ventana(f, EV_INI, EV_FIN) for f in ev_m["rueda"])),
    ("Se usan los 18 eventos de U2 (shocks del mismo signo en ruedas seguidas = un evento)", len(ev_m) == shocks["evento_id"].nunique()),
    ("Ningún evento por empresa se solapa con el anterior de la misma empresa",
     bool(ev_b.groupby("ticker")["rueda"].apply(lambda s: (s.map(pos).diff().dropna() > EV_FIN - EV_INI).all()).all())),
    ("El sorteo de fechas al azar usa solo ruedas con ventanas completas", len(car_azar) == len(validas)),
    ("Retornos anormales de una fecha al azar promedian cerca de 0 (control del modelo)",
     abs(car_azar["total [−3, +5]"].mean()) < 0.01),
]
verif = pd.DataFrame(controles, columns=["control", "pasa"])
verif.to_csv(AQUI / "verificaciones.csv", index=False, encoding="utf-8")

# ── Resumen ──────────────────────────────────────────────────────────────
r = []
def m(clave, valor, detalle=""):
    r.append({"metrica": clave, "valor": valor, "detalle": detalle})

m("eventos_mercado", len(ev_m)); m("eventos_mercado_principal", len(principal))
m("eventos_con_eleccion", int(ev_m["ventana_con_eleccion"].sum()), ", ".join(ev_m.loc[ev_m["ventana_con_eleccion"], "rueda"]))
m("eventos_pos", int((principal["tipo"] == "positivo").sum())); m("eventos_neg", int((principal["tipo"] == "negativo").sum()))
m("eventos_solapados", int(principal["solapa_con_anterior"].sum()), ", ".join(principal.loc[principal["solapa_con_anterior"], "rueda"]))
m("ruedas_para_sorteo", len(validas))
for _, x in res_m[res_m["muestra"] == "todos"].iterrows():
    m(f"mercado_{x['eventos']}_{x['ventana']}", round(x["car_medio_pct"], 3),
      f"t p={x['p_t']:.3f}; signo {x['positivos']}/{x['n']} p={x['p_signo']:.3f}; azar p={x['p_azar']:.3f}")
    m(f"volumen_{x['eventos']}_{x['ventana']}", round(x["monto_anormal_medio"], 3), f"t p={x['p_vol_t']:.3f}; azar p={x['p_vol_azar']:.3f}")
m("eventos_empresa", len(ev_b), f"{ev_b['ticker'].nunique()} empresas")
m("eventos_empresa_con_eleccion", descartados_eleccion, "excluidos: su ventana incluye un día electoral")
m("eventos_empresa_pos", int((ev_b["tipo"] == "positivo").sum())); m("eventos_empresa_neg", int((ev_b["tipo"] == "negativo").sum()))
for _, x in res_b.iterrows():
    m(f"empresa_{x['eventos']}_{x['ventana']}", round(x["car_medio_pct"], 3),
      f"t p={x['p_t']:.3f}; signo {x['positivos']}/{x['n']} p={x['p_signo']:.3f}; vol {x['vol_anormal_medio']:.3f} p={x['p_vol']:.3f}")
m("controles_ok", int(verif["pasa"].sum()), f"de {len(verif)}")
pd.DataFrame(r).to_csv(AQUI / "resumen_u7.csv", index=False, encoding="utf-8")

# ── Figuras ──────────────────────────────────────────────────────────────
dias = list(range(EV_INI, EV_FIN + 1))
fig, axs = plt.subplots(1, 2, figsize=(11, 4.4), sharey=True)
for ax, tipo, color in ((axs[0], "positivo", "#2E8B57"), (axs[1], "negativo", "#D7301F")):
    n = int((principal["tipo"] == tipo).sum())
    sorteos = np.array([100 * np.cumsum(np.mean(np.vstack([
        (merv.loc[ventana(f, EV_INI, EV_FIN)] - media_estimacion(f)).values
        for f in rng.choice(validas, n, replace=False)]), axis=0)) for _ in range(1000)])
    ax.fill_between(dias, np.percentile(sorteos, 2.5, axis=0), np.percentile(sorteos, 97.5, axis=0), color="#BBBBBB", alpha=0.45,
                    label="95% de fechas al azar")
    ax.plot(dias, camino[tipo], color=color, lw=2.2, marker="o", label=f"Ruedas de tono extremo {tipo} (n={n})")
    ax.axvline(0, color="#12263A", lw=1, ls="--"); ax.axhline(0, color="#999", lw=0.7)
    ax.set_xticks(dias); ax.set_xlabel("Ruedas respecto del evento")
    ax.set_title(f"Tono extremo {tipo}", loc="left", fontsize=11, fontweight="bold")
    ax.legend(frameon=False, fontsize=8.5, loc="upper left"); ax.spines[["top", "right"]].set_visible(False)
axs[0].set_ylabel("Retorno anormal acumulado del Merval (%)")
fig.tight_layout(); fig.savefig(AQUI / "u7_mercado.png", dpi=160, facecolor="white")

fig, ax = plt.subplots(figsize=(8, 4.2))
for tipo, color in (("positivo", "#2E8B57"), ("negativo", "#D7301F")):
    g = ev_b[ev_b["tipo"] == tipo]
    vals = [100 * g[f"car_{k}"].mean() for k in VENTANAS]
    errs = [100 * 1.96 * g[f"car_{k}"].std() / np.sqrt(len(g)) for k in VENTANAS]
    xs = np.arange(len(VENTANAS)) + (-0.18 if tipo == "positivo" else 0.18)
    ax.bar(xs, vals, 0.36, yerr=errs, color=color, alpha=0.8, capsize=3, label=f"Tono propio extremo {tipo} (n={len(g)})")
ax.axhline(0, color="#999", lw=0.7); ax.set_xticks(range(len(VENTANAS)), list(VENTANAS))
ax.set_ylabel("Retorno anormal acumulado (%)"); ax.legend(frameon=False, fontsize=9); ax.spines[["top", "right"]].set_visible(False)
ax.set_title("Empresas: retorno anormal alrededor de su tono propio extremo (barras: 95%)", loc="left", fontsize=11, fontweight="bold")
fig.tight_layout(); fig.savefig(AQUI / "u7_empresa.png", dpi=160, facecolor="white")

for _, x in pd.DataFrame(r).iterrows():
    print(f"{x['metrica']:45s} {str(x['valor']):10s} {str(x['detalle'])[:120]}")
print(); print(verif.to_string(index=False)); print(); print(pd.DataFrame(elect).round(2).to_string(index=False))
