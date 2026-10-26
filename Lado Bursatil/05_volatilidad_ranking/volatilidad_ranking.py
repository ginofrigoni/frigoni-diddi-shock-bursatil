"""
Volatilidad por acción y ranking — panel de 47 acciones — tesis version 3.0
Tesina: Impacto de shocks informativos en empresas argentinas

Mismo cálculo que el VIX argentino (03_vix_argentino) pero por acción en vez
de por el índice: desvío estándar rodante de 20 días de los retornos
diarios, anualizado. Compara cada acción contra el VIX de mercado.

VENTANA: se lee directamente de ../03_vix_argentino/vix_arg.csv (no se
repite la fecha a mano) -- es la ventana del corpus de noticias del
compañero, y así ADF, VIX y esta volatilidad quedan siempre alineados
aunque esa ventana cambie más adelante. Tanto el retorno como el desvío
rodante de 20 días se calculan sobre la serie completa de precios y recién
después se recorta a la ventana -- igual que el VIX, que usa los días
previos como "calentamiento". Si el desvío rodante se calculara después de
recortar, se perderían los primeros 19 días de la ventana.

Input:  ../01_scraping_acciones/precios_diarios_47_acciones.csv
        ../03_vix_argentino/vix_arg.csv           (ventana + referencia de mercado)
Output: volatilidad_acciones.csv   (una columna por acción, una fila por día)
        ranking_volatilidad.png    (barras horizontales, coloreadas por sector)
        volatilidad_por_sector.png (una fila de panel por sector)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

VENTANA = 20

# ── 1. Ventana — tomada de vix_arg.csv ───────────────────────────────────────
vix = pd.read_csv("../03_vix_argentino/vix_arg.csv", parse_dates=["fecha"], index_col="fecha")
FECHA_INICIO, FECHA_FIN = vix.index.min(), vix.index.max()
vix_prom = vix["vix_arg"].mean()
print(f"Ventana (tomada de vix_arg.csv): {FECHA_INICIO.date()} -> {FECHA_FIN.date()}")

# ── 2. Cargar datos y calcular retorno ANTES de recortar la ventana ─────────
precios = pd.read_csv("../01_scraping_acciones/precios_diarios_47_acciones.csv", parse_dates=["Date"])
precios = precios.rename(columns={"Date": "fecha"})
precios = precios.sort_values(["ticker", "fecha"])
precios["retorno"] = precios.groupby("ticker")["Close"].pct_change()

meta = precios[["ticker", "empresa", "sector"]].drop_duplicates().set_index("ticker")
print(f"Acciones: {precios['ticker'].nunique()}")

# ── 3. Volatilidad realizada rodante (20 días, anualizada) ──────────────────
# Se calcula sobre la serie completa y DESPUÉS se recorta a la ventana.
def volatilidad_realizada(serie, ventana=VENTANA):
    return serie.rolling(window=ventana).std() * np.sqrt(252) * 100

vol_lista = []
for ticker, grupo in precios.groupby("ticker"):
    grupo = grupo.set_index("fecha").sort_index()
    vol = volatilidad_realizada(grupo["retorno"])
    vol = vol[(vol.index >= FECHA_INICIO) & (vol.index <= FECHA_FIN)]
    vol_df = vol.rename("volatilidad").to_frame()
    vol_df["ticker"] = ticker
    vol_lista.append(vol_df)

vol_all = pd.concat(vol_lista).dropna()
vol_all = vol_all.join(meta, on="ticker")

# ── 4. Guardar en formato wide (una columna por acción) ──────────────────────
vol_wide = vol_all.reset_index().pivot(index="fecha", columns="ticker", values="volatilidad")
vol_wide.to_csv("volatilidad_acciones.csv")
print(f"\nGuardado: volatilidad_acciones.csv")
print(f"Shape: {vol_wide.shape[0]} días x {vol_wide.shape[1]} acciones")

# ── 5. Ranking promedio por acción ───────────────────────────────────────────
ranking = (
    vol_all.groupby(["ticker", "empresa", "sector"])["volatilidad"]
    .mean().rename("vol_prom").reset_index()
    .sort_values("vol_prom")
)
ranking.to_csv("ranking_volatilidad.csv", index=False)
print(f"Guardado: ranking_volatilidad.csv")
print()
print(ranking.to_string(index=False))

# ── 5b. Picos propios — la acción muy por encima del mercado con el mercado tranquilo ──
# Día "propio": volatilidad de la acción > VIX + 60 puntos, con VIX < 50%.
# Se agrupan en episodios de días consecutivos (de 3 días o más).
EXCESO_MIN, VIX_TRANQUILO, DIAS_MIN = 60, 50, 3
vol_wide_al = vol_wide.reindex(vix.index)
propio = (vol_wide_al.sub(vix["vix_arg"], axis=0) > EXCESO_MIN) & (vix["vix_arg"] < VIX_TRANQUILO).values[:, None]
episodios = []
for ticker in vol_wide_al.columns:
    e = propio[ticker]
    bloques = (e != e.shift()).cumsum()[e]
    for _, idx in bloques.groupby(bloques).groups.items():
        if len(idx) < DIAS_MIN:
            continue
        tramo = vol_wide_al.loc[idx, ticker]
        f_pico = tramo.idxmax()
        episodios.append({
            "ticker": ticker, "sector": meta.loc[ticker, "sector"],
            "desde": idx.min().date(), "hasta": idx.max().date(), "dias": len(idx),
            "pico_vol": round(tramo.max(), 1), "fecha_pico": f_pico.date(),
            "vix_en_pico": round(vix.loc[f_pico, "vix_arg"], 1),
            "dias_propios_total": int(e.sum()),
        })
picos = pd.DataFrame(episodios).sort_values(["dias_propios_total", "ticker", "desde"], ascending=[False, True, True])

# Marca de "eco de ventana": el episodio arranca dentro de las 5 ruedas
# siguientes a una caída del VIX de más de 10 puntos en un día. Esas caídas son
# el día grande del mercado saliendo de la ventana de 20 ruedas -- el VIX se
# "calma" de golpe mientras la acción todavía tiene sus propios días grandes en
# su ventana. En esos casos el pico no es necesariamente propio de la empresa.
caidas_vix = vix.index[vix["vix_arg"].diff() < -10]
pos = {f: i for i, f in enumerate(vix.index)}
def tras_caida(desde):
    i = pos[pd.Timestamp(desde)]
    return any(0 <= i - pos[c] <= 5 for c in caidas_vix)
picos["tras_caida_vix"] = picos["desde"].map(tras_caida)
print("Caídas del VIX > 10 puntos en un día:", [str(c.date()) for c in caidas_vix])
picos.to_csv("picos_propios.csv", index=False)
print(f"Guardado: picos_propios.csv  ({len(picos)} episodios, {picos.ticker.nunique()} acciones)")

print(f"\nVIX de mercado (promedio, mismo período): {vix_prom:.1f}%")
print(f"Volatilidad promedio del panel de 47: {ranking['vol_prom'].mean():.1f}%")

# ── 6. Gráfico — ranking horizontal, coloreado por sector ───────────────────
paleta_sector = {
    "Energía": "#e07b39", "Utilities": "#5aa86f", "Financiero": "#4a7fc1",
    "Materiales": "#a87bc1", "Comunicaciones": "#c1a84a", "Real Estate": "#c15a5a",
    "Consumo": "#5ac1b8", "Industrial": "#7b8fa1", "Conglomerado": "#c17b9e",
    "Tecnología": "#3d4f8a",
}
colores = ranking["sector"].map(paleta_sector).fillna("#aaaaaa")

fig, ax = plt.subplots(figsize=(10, 12))
bars = ax.barh(ranking["ticker"].str.replace(".BA", ""), ranking["vol_prom"],
                color=colores, edgecolor="white", linewidth=0.5, height=0.7)
for bar, val in zip(bars, ranking["vol_prom"]):
    ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
            f"{val:.1f}%", va="center", ha="left", fontsize=8, color="#333333")
ax.axvline(vix_prom, color="black", linewidth=1.2, linestyle="--")
ax.set_xlabel("Volatilidad promedio anualizada (%)")
ax.set_title(f"Ranking de volatilidad por acción — panel de 47\nVIX de mercado: {vix_prom:.1f}%",
             fontsize=12, fontweight="bold")
ax.set_xlim(0, ranking["vol_prom"].max() + 15)
ax.grid(axis="x", alpha=0.3)

leyenda = [mpatches.Patch(color=c, label=s) for s, c in paleta_sector.items() if s in ranking.sector.unique()]
leyenda.append(mpatches.Patch(color="black", label=f"VIX mercado: {vix_prom:.1f}%"))
ax.legend(handles=leyenda, loc="lower right", fontsize=8, title="Sector", framealpha=0.9)

plt.tight_layout()
plt.savefig("ranking_volatilidad.png", dpi=150, bbox_inches="tight")
plt.close()
print("\nGráfico guardado: ranking_volatilidad.png")

# ── 7. Gráfico — volatilidad por sector vs. VIX de mercado ──────────────────
sectores = sorted(vol_all["sector"].unique())
n = len(sectores)
fig, axes = plt.subplots(n, 1, figsize=(13, 2.6 * n), sharex=True)
if n == 1:
    axes = [axes]

for ax, sector in zip(axes, sectores):
    df_s = vol_all[vol_all["sector"] == sector]
    for ticker in df_s["ticker"].unique():
        serie = df_s[df_s["ticker"] == ticker]["volatilidad"]
        ax.plot(serie.index, serie.values, linewidth=1, alpha=0.8, label=ticker.replace(".BA", ""))
    ax.plot(vix.index, vix["vix_arg"], color="black", linewidth=1.2, linestyle="--", alpha=0.5, label="VIX mercado")
    ax.set_title(f"Sector: {sector}", fontsize=10, fontweight="bold")
    ax.set_ylabel("Vol. (%)", fontsize=9)
    ax.legend(fontsize=7, loc="upper right", ncol=6)
    ax.grid(alpha=0.3)

plt.suptitle("Volatilidad realizada por acción vs. mercado (ventana 20 días)", fontsize=13, y=1.005)
plt.tight_layout()
plt.savefig("volatilidad_por_sector.png", dpi=150, bbox_inches="tight")
plt.close()
print("Gráfico guardado: volatilidad_por_sector.png")
