"""
Mapa del lado bursátil — tesis version 3.0
Tesina: Impacto de shocks informativos en empresas argentinas

Dibuja el flujo completo del lado bursátil (de Yahoo Finance hasta la etapa
que se une con las noticias), con los resultados clave de cada carpeta.

Todos los números se leen de los CSV de cada carpeta (01 a 06) -- no hay
ningún valor escrito a mano. Si se vuelve a correr alguna carpeta, alcanza
con volver a correr este script para que el mapa quede al día.

Input:  los CSV de 01_scraping_acciones ... 06_hmm_regimen_mercado
Output: mapa_lado_bursatil.png
        resumen_mapa.csv   (los números que aparecen en el mapa, uno por fila)
"""

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Circle

R = ".."
plt.rcParams["font.family"] = "Calibri"

# ════════════════════════════════════════════════════════════════════════
# 1. Números, leídos de cada carpeta
# ════════════════════════════════════════════════════════════════════════
cob = pd.read_csv(f"{R}/01_scraping_acciones/cobertura_53_candidatas.csv")
panel = pd.read_csv(f"{R}/01_scraping_acciones/panel_acciones_final.csv")
precios = pd.read_csv(f"{R}/01_scraping_acciones/precios_diarios_47_acciones.csv", usecols=["Date"], parse_dates=["Date"])
vix = pd.read_csv(f"{R}/03_vix_argentino/vix_arg.csv", parse_dates=["fecha"])
clu = pd.read_csv(f"{R}/02_clustering_acciones/resumen_clustering_47.csv")
adf = pd.read_csv(f"{R}/04_adf/resultados_adf_47.csv")
rank = pd.read_csv(f"{R}/05_volatilidad_ranking/ranking_volatilidad.csv")
picos = pd.read_csv(f"{R}/05_volatilidad_ranking/picos_propios.csv")
hmm = pd.read_csv(f"{R}/06_hmm_regimen_mercado/hmm_regimen_mercado.csv")

f = lambda d: d.strftime("%d/%m/%Y")
coma = lambda x, n=1: f"{x:.{n}f}".replace(".", ",")

N = len(panel)
n_cand = len(cob)
n_sect = panel["sector"].nunique()
dias_3a = precios["Date"].nunique()
ini_3a, fin_3a = precios["Date"].min(), precios["Date"].max()
n_vix = len(vix)
ini_v, fin_v = vix["fecha"].min(), vix["fecha"].max()
vmax = vix.loc[vix.vix_arg.idxmax()]

km = clu[(clu.Analisis == "13 features") & (clu.Periodo == "3 anos") & (clu.Metodo == "K-Means")]
grupo = km.loc[km.N_empresas.idxmin()]
combos = clu.groupby(["Analisis", "Periodo", "Metodo"]).N_empresas.min()
n_deg = int((combos <= 2).sum())

est_p = int(((adf.tipo == "precio") & (adf.resultado == "Estacionaria")).sum())
est_r = int(((adf.tipo == "retorno") & (adf.resultado == "Estacionaria")).sum())

gen = picos[~picos.tras_caida_vix]
reg = hmm.regimen_nombre.value_counts()

resumen = {
    "candidatas": n_cand, "panel": N, "sectores": n_sect, "ruedas_3_anos": dias_3a,
    "ruedas_ventana_noticias": n_vix, "vix_promedio": round(vix.vix_arg.mean(), 1),
    "vix_maximo": round(vmax.vix_arg, 1), "grupo_clustering": int(grupo.N_empresas),
    "silueta_grupo": grupo.Silueta, "combinaciones_degeneradas": n_deg, "combinaciones": len(combos),
    "precios_estacionarios": est_p, "retornos_estacionarios": est_r,
    "vol_promedio_panel": round(rank.vol_prom.mean(), 1), "picos_propios_genuinos": len(gen),
    **{f"dias_{k.lower()}": int(v) for k, v in reg.items()},
}
pd.Series(resumen, name="valor").to_csv("resumen_mapa.csv", header=True)

# ════════════════════════════════════════════════════════════════════════
# 2. Estilo
# ════════════════════════════════════════════════════════════════════════
INK, INK2, ACC, LINE = "#12263A", "#1C3A5C", "#40798C", "#C9D3DC"
GRIS, NOTI = "#8A97A3", "#7B5EA7"
C_FUENTE, C_BASE, C_ANAL, C_PEND = "#5C6B7A", "#1C3A5C", "#40798C", "#9AA7B0"

fig = plt.figure(figsize=(17, 11.5), dpi=150)
ax = fig.add_axes([0, 0, 1, 1])
ax.set_xlim(0, 100); ax.set_ylim(0, 74); ax.axis("off")
fig.patch.set_facecolor("white")


def etiqueta_ventana(b, texto, color):
    """Chip chico arriba a la derecha de una caja: qué ventana de fechas usa."""
    # Segoe UI: con matplotlib 3.11, Calibri/Cambria dentro de un recuadro de color a veces no se dibujan
    ax.text(b["x"] + b["w"] - 1.0, b["y"] + b["h"] - 2.3, texto, ha="right", va="center", fontsize=9,
            color="white", fontweight="bold", family="Segoe UI", zorder=6,
            bbox=dict(boxstyle="round,pad=0.35,rounding_size=0.6", facecolor=color, edgecolor="none"))


def caja(x, y, w, h, num, titulo, lineas, color, pendiente=False, borde=None):
    estilo = dict(boxstyle="round,pad=0,rounding_size=1.1", linewidth=1.6,
                  edgecolor=borde or color, facecolor="#FAFBFC" if pendiente else "white",
                  linestyle=(0, (4, 3)) if pendiente else "-", zorder=2)
    ax.add_patch(FancyBboxPatch((x, y), w, h, **estilo))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.55), w, 0.55, boxstyle="round,pad=0,rounding_size=0.25",
                                facecolor=color, edgecolor="none", zorder=3, alpha=0.5 if pendiente else 1))
    tx = x + 1.2
    if num:
        ax.add_patch(Circle((x + 2.1, y + h - 2.3), 1.35, facecolor=color, edgecolor="none", zorder=4))
        ax.text(x + 2.1, y + h - 2.33, num, ha="center", va="center", color="white", fontsize=11.5,
                fontweight="bold", family="Cambria", zorder=5)
        tx = x + 4.1
    ax.text(tx, y + h - 2.3, titulo, ha="left", va="center", fontsize=13.5, fontweight="bold",
            family="Cambria", color=GRIS if pendiente else INK, zorder=5)
    yy = y + h - 4.6
    for l in lineas:
        negrita = l.startswith("**")
        ax.text(x + 1.3, yy, l.strip("*"), ha="left", va="top", fontsize=10.8, zorder=5,
                color=GRIS if pendiente else ("#1F2D3A" if not negrita else INK2),
                fontweight="bold" if negrita else "normal")
        yy -= 1.95
    return dict(x=x, y=y, w=w, h=h)


def flecha(p0, p1, color=INK2, estilo="-", rad=0.0, etiqueta=None, dx=0, dy=0.7, ancho=1.6):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=15, color=color, linewidth=ancho,
                                 linestyle=estilo, connectionstyle=f"arc3,rad={rad}", zorder=1, shrinkA=2, shrinkB=2))
    if etiqueta:
        mx, my = (p0[0] + p1[0]) / 2 + dx, (p0[1] + p1[1]) / 2 + dy
        ax.text(mx, my, etiqueta, ha="center", va="bottom", fontsize=9.5, color=color, style="italic",
                bbox=dict(facecolor="white", edgecolor="none", pad=0.6), zorder=6)

der = lambda b, fy=0.5: (b["x"] + b["w"], b["y"] + b["h"] * fy)
izq = lambda b, fy=0.5: (b["x"], b["y"] + b["h"] * fy)
arr = lambda b, fx=0.5: (b["x"] + b["w"] * fx, b["y"] + b["h"])
aba = lambda b, fx=0.5: (b["x"] + b["w"] * fx, b["y"])

# ════════════════════════════════════════════════════════════════════════
# 3. Título y encabezados de columna
# ════════════════════════════════════════════════════════════════════════
ax.text(1, 72.2, "Lado bursátil — mapa del pipeline", fontsize=24, fontweight="bold", family="Cambria", color=INK, va="center")
ax.text(1, 69.9, "Tesina: impacto de shocks informativos en acciones argentinas (BYMA / S&P Merval) · tesis version 3.0",
        fontsize=12, color=GRIS, va="center", style="italic")
for x, w, t in [(1, 13, "FUENTE"), (18, 21, "DATOS BASE"), (45, 25, "ANÁLISIS"), (76, 23, "PRÓXIMA ETAPA — CON NOTICIAS")]:
    ax.text(x, 67.3, t, fontsize=10.5, fontweight="bold", color=ACC, va="center")
    ax.plot([x, x + w], [66.4, 66.4], color=LINE, lw=1.2)

# ════════════════════════════════════════════════════════════════════════
# 4. Cajas
# ════════════════════════════════════════════════════════════════════════
merv = caja(1, 54, 13, 10, None, "^MERV", ["Índice S&P Merval", "Yahoo Finance"], C_FUENTE)
tick = caja(1, 24, 13, 12, None, f"{n_cand} tickers", ["Panel General y", "Líderes de BYMA", "Yahoo Finance"], C_FUENTE)

v03 = caja(18, 48, 21, 16, "03", "VIX argentino",
           ["Volatilidad realizada del ^MERV", "(desvío 20 días, anualizado)",
            f"**{n_vix} ruedas · prom. {coma(vix.vix_arg.mean())}%",
            f"Máx. {coma(vmax.vix_arg)}% ({f(vmax.fecha)})", "Fija la ventana de noticias"], C_BASE)
s01 = caja(18, 15, 21, 27, "01", "Scraping",
           [f"{n_cand} tickers → {N} acciones", "Criterio: 100% de las ruedas",
            "y ≥ 90% de días con volumen", f"**{N} acciones · {n_sect} sectores",
            f"{dias_3a} ruedas (3 años)", "Calendario real = días de ^MERV",
            "2 eventos corporativos corregidos", "(SEMI 16/12/24 · AGRO hasta 11/23)"], C_BASE)

h06 = caja(45, 54, 25, 11, "06", "HMM — régimen de mercado",
           ["Markov-Switching sobre el VIX, k = 3",
            f"**Calmo {reg.get('Calmo', 0)} · Moderado {reg.get('Moderado', 0)} · Tenso {reg.get('Tenso', 0)} días",
            "Ojo: hereda el eco de 20 días"], C_ANAL)
a04 = caja(45, 41, 25, 11, "04", "Test ADF",
           [f"Precios: {N - est_p} de {N} NO estacionarios",
            f"Retornos: {est_r} de {N} estacionarios",
            "**→ el VAR se hace con retornos"], C_ANAL)
c02 = caja(45, 28, 25, 11, "02", "Clustering",
           [f"{n_deg} de {len(combos)} combinaciones: 1-2 outliers",
            f"Grupo de {int(grupo.N_empresas)} (sil. {coma(grupo.Silueta, 3)}): baja liquidez",
            "**→ sin familias claras: por acción"], C_ANAL)
o05 = caja(45, 15, 25, 11, "05", "Volatilidad por acción",
           [f"Panel {coma(rank.vol_prom.mean())}% vs. VIX {coma(vix.vix_arg.mean())}%",
            f"{rank.iloc[0].ticker[:-3]} {coma(rank.iloc[0].vol_prom)}% → {rank.iloc[-1].ticker[:-3]} {coma(rank.iloc[-1].vol_prom)}%",
            f"**{len(gen)} picos propios en {gen.ticker.nunique()} acciones"], C_ANAL)

noti = caja(76, 56, 23, 8.5, None, "Corpus de noticias", ["Sentimiento diario (FinBETO)", "— lado de Gino —"], NOTI, borde=NOTI)
dset = caja(76, 41.5, 23, 11, None, "Dataset unificado",
            ["Mercado + sentimiento + shocks", f"{n_vix} días, {N} acciones", "Pendiente: sentimiento por empresa"],
            C_PEND, pendiente=True)
var = caja(76, 28, 23, 10.5, None, "VAR + Granger + IRF",
           ["General · por empresa", "por régimen · por sector", "¿Quién anticipa a quién?"], C_PEND, pendiente=True)
evs = caja(76, 15, 23, 10, None, "Event study",
           ["Precios alrededor de los", "shocks de noticias"], C_PEND, pendiente=True)

# ════════════════════════════════════════════════════════════════════════
# 5. Flechas
# ════════════════════════════════════════════════════════════════════════
flecha(der(merv), izq(v03, 0.62), etiqueta="cierres")
flecha(der(tick), izq(s01, 0.55), etiqueta="OHLCV")
flecha(aba(merv, 0.5), arr(tick, 0.5), color=GRIS, estilo=(0, (3, 2)), etiqueta="calendario real", dx=0, dy=-0.5)

flecha(der(v03, 0.62), izq(h06, 0.5), etiqueta="serie VIX", dy=0.4)
for destino, salida in [(a04, 0.80), (c02, 0.52), (o05, 0.22)]:   # salida = altura relativa en Scraping
    flecha(der(s01, salida), izq(destino, 0.5))
ax.text(42.0, der(s01, 0.66)[1], f"precios\nde las {N}", fontsize=9.5, color=INK2, style="italic", ha="center",
        va="center", bbox=dict(facecolor="white", edgecolor="none", pad=0.3), zorder=6)

# Qué ventana de fechas usa cada caja (detalle completo en la línea de tiempo de abajo)
for b in (v03, h06, a04, o05):
    etiqueta_ventana(b, f"{n_vix} días", ACC)
etiqueta_ventana(s01, f"{dias_3a} días", C_BASE)
etiqueta_ventana(c02, f"{dias_3a} y {n_vix} días", ACC)

flecha(aba(noti), arr(dset), color=NOTI, etiqueta="sentimiento", dx=3.2, dy=-0.9)
flecha(der(h06, 0.4), izq(dset, 0.78), etiqueta="régimen diario", color=INK2, dy=0.3)
flecha(der(a04, 0.5), izq(dset, 0.3), etiqueta="retornos", color=INK2, dy=-1.9)
flecha(aba(dset), arr(var), color=C_PEND)
flecha(aba(var), arr(evs), color=C_PEND)
flecha(der(c02, 0.5), izq(var, 0.5), color=GRIS, estilo=(0, (3, 2)), etiqueta="análisis por acción", dy=0.3)
flecha(der(o05, 0.5), izq(evs, 0.5), color=GRIS, estilo=(0, (3, 2)), etiqueta="picos a cruzar", dy=0.3)

# ════════════════════════════════════════════════════════════════════════
# 6. Línea de tiempo de las dos ventanas
# ════════════════════════════════════════════════════════════════════════
t0, t1 = pd.Timestamp("2023-04-01"), pd.Timestamp("2026-06-01")
X0, X1 = 3, 97
tx = lambda d: X0 + (d - t0) / (t1 - t0) * (X1 - X0)
ax.text(1, 11.6, "LAS DOS VENTANAS DE FECHAS", fontsize=10.5, fontweight="bold", color=ACC, va="center")
ax.plot([1, 99], [10.7, 10.7], color=LINE, lw=1.2)
for anio in range(2024, 2027):
    xa = tx(pd.Timestamp(f"{anio}-01-01"))
    ax.plot([xa, xa], [1.3, 9.6], color=LINE, lw=0.9, zorder=0)
    ax.text(xa, 0.6, str(anio), ha="center", fontsize=9.5, color=GRIS)
for y, a, b, c, txt in [
    (7.3, ini_3a, fin_3a, C_BASE, f"3 años · {f(ini_3a)} → {f(fin_3a)} · {dias_3a} ruedas · carpetas 01 y 02 (3 años)"),
    (3.6, ini_v, fin_v, ACC, f"Ventana noticias · {f(ini_v)} → {f(fin_v)} · {n_vix} ruedas · 02 (1 año), 03, 04, 05, 06"),
]:
    ax.add_patch(FancyBboxPatch((tx(a), y - 1.15), tx(b) - tx(a), 2.3, boxstyle="round,pad=0,rounding_size=0.6",
                                facecolor=c, edgecolor="none", zorder=2))
    ax.text(tx(b) - 0.8, y, txt, ha="right", va="center", fontsize=10.5, color="white", fontweight="bold", zorder=3)

# Leyenda (abajo de la columna Fuente, que tiene lugar libre)
lx, ly = 1, 20.5
ax.text(lx, ly + 1, "Referencias", fontsize=10, fontweight="bold", color=INK)
for i, (c, t, est) in enumerate([(INK2, "flujo de datos", "-"), (GRIS, "insumo / relación", (0, (3, 2))),
                                  (C_PEND, "pendiente", (0, (4, 3)))]):
    yy = ly - 1.4 - i * 1.9
    ax.plot([lx, lx + 2.6], [yy, yy], color=c, lw=1.8, ls=est)
    ax.text(lx + 3.1, yy, t, fontsize=9.5, color="#333", va="center")

plt.savefig("mapa_lado_bursatil.png", dpi=150, facecolor="white")
plt.close()
print("Guardado: mapa_lado_bursatil.png")
print("Guardado: resumen_mapa.csv")
print(pd.Series(resumen).to_string())
