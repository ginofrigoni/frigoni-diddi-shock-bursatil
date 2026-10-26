"""
Test ADF (Augmented Dickey-Fuller) — panel de 47 acciones — tesis version 3.0
Tesina: Impacto de shocks informativos en empresas argentinas

El VAR y el test de Granger exigen series estacionarias (media y varianza
estables en el tiempo). Si se usan precios -- que tienen tendencia -- los
resultados salen espurios. Este test decide si hay que trabajar con precios
o con retornos.

Hipótesis nula: la serie NO es estacionaria. Si p < 0.05, se rechaza la
nula y la serie SÍ es estacionaria.

ESPECIFICACIÓN: cada serie se testea con la variante que corresponde a su
forma. Los precios (en pesos nominales, con tendencia de fondo por la
inflación) van con constante + tendencia (regression="ct"); los retornos,
que oscilan alrededor de una media sin tendencia, van solo con constante
(regression="c").

VENTANA: se lee directamente de ../03_vix_argentino/vix_arg.csv (no se
repite la fecha a mano) -- es la ventana del corpus de noticias del
compañero (2025-01-02 -> 2026-05-03 según lo que va a usar el análisis
final), y así ADF, VIX y volatilidad quedan siempre alineados aunque esa
ventana cambie más adelante. El retorno se calcula sobre la serie completa
de precios y recién después se recorta a la ventana, para no perder el
primer día por falta del precio anterior.

Input:  ../01_scraping_acciones/precios_diarios_47_acciones.csv
        ../03_vix_argentino/vix_arg.csv   (solo para tomar la ventana)
Output: resultados_adf_47.csv   (una fila por ticker x tipo de serie)
        resumen_adf.png         (barras: cuántas estacionarias, precio vs retorno)
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import matplotlib.pyplot as plt
from statsmodels.tsa.stattools import adfuller

# ── Ventana — tomada de vix_arg.csv, no hardcodeada ─────────────────────────
vix = pd.read_csv("../03_vix_argentino/vix_arg.csv", parse_dates=["fecha"])
FECHA_INICIO, FECHA_FIN = vix["fecha"].min(), vix["fecha"].max()
print(f"Ventana (tomada de vix_arg.csv): {FECHA_INICIO.date()} -> {FECHA_FIN.date()}")

# ── 1. Cargar datos y calcular retorno ANTES de recortar la ventana ─────────
precios = pd.read_csv("../01_scraping_acciones/precios_diarios_47_acciones.csv", parse_dates=["Date"])
precios = precios.rename(columns={"Date": "fecha"})
precios = precios.sort_values(["ticker", "fecha"])
precios["retorno"] = precios.groupby("ticker")["Close"].pct_change()

# ── 2. Recortar a la ventana ─────────────────────────────────────────────────
precios = precios[(precios["fecha"] >= FECHA_INICIO) & (precios["fecha"] <= FECHA_FIN)]
tickers = sorted(precios["ticker"].unique())
print(f"Corriendo ADF sobre {len(tickers)} acciones...")


REGRESION = {"precio": "ct", "retorno": "c"}   # ver ESPECIFICACIÓN en el encabezado


def test_adf(serie, nombre, regresion):
    resultado = adfuller(serie.dropna(), autolag="AIC", regression=regresion)
    stat, p_valor = resultado[0], resultado[1]
    es_est = "Estacionaria" if p_valor < 0.05 else "NO estacionaria"
    return {"serie": nombre, "regresion": regresion, "estadistico": round(stat, 3),
            "p_valor": round(p_valor, 4), "resultado": es_est}


# ── 3. Correr ADF sobre precio y retorno, por acción ────────────────────────
filas = []
for ticker in tickers:
    df_t = precios[precios["ticker"] == ticker].set_index("fecha").sort_index()

    r_precio = test_adf(df_t["Close"], f"{ticker} precio", REGRESION["precio"])
    r_precio["ticker"], r_precio["tipo"] = ticker, "precio"
    filas.append(r_precio)

    r_retorno = test_adf(df_t["retorno"], f"{ticker} retorno", REGRESION["retorno"])
    r_retorno["ticker"], r_retorno["tipo"] = ticker, "retorno"
    filas.append(r_retorno)

    print(f"  {ticker:8s} | precio: {r_precio['resultado']:16s} (p={r_precio['p_valor']:.4f})"
          f" | retorno: {r_retorno['resultado']:16s} (p={r_retorno['p_valor']:.4f})")

resultados = pd.DataFrame(filas)[["serie", "ticker", "tipo", "regresion", "estadistico", "p_valor", "resultado"]]
resultados.to_csv("resultados_adf_47.csv", index=False)

# ── 4. Resumen ───────────────────────────────────────────────────────────────
print()
print("=" * 60)
resumen = resultados.groupby(["tipo", "resultado"]).size().unstack(fill_value=0)
print(resumen.to_string())
print(f"\nGuardado: resultados_adf_47.csv  ({len(resultados)} filas)")

n_precio_est = ((resultados.tipo == "precio") & (resultados.resultado == "Estacionaria")).sum()
n_retorno_est = ((resultados.tipo == "retorno") & (resultados.resultado == "Estacionaria")).sum()
print(f"\nPrecios estacionarios:  {n_precio_est} de {len(tickers)}")
print(f"Retornos estacionarios: {n_retorno_est} de {len(tickers)}")

# ── 5. Gráfico resumen ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7, 4.5))
tipos = ["precio", "retorno"]
estacionarias = [((resultados.tipo == t) & (resultados.resultado == "Estacionaria")).sum() for t in tipos]
no_estacionarias = [len(tickers) - e for e in estacionarias]

x = range(len(tipos))
ax.bar(x, estacionarias, label="Estacionaria", color="#2E7D5B")
ax.bar(x, no_estacionarias, bottom=estacionarias, label="NO estacionaria", color="#C1272D")
ax.set_xticks(list(x))
ax.set_xticklabels(["Precio (Close)", "Retorno diario"])
ax.set_ylabel(f"Cantidad de acciones (de {len(tickers)})")
ax.set_title("Test ADF — estacionariedad por tipo de serie (panel de 47)")
ax.legend()
for i, (e, n) in enumerate(zip(estacionarias, no_estacionarias)):
    ax.text(i, e / 2, str(e), ha="center", va="center", color="white", fontweight="bold")
    if n > 0:
        ax.text(i, e + n / 2, str(n), ha="center", va="center", color="white", fontweight="bold")
plt.tight_layout()
plt.savefig("resumen_adf.png", dpi=150)
plt.close()
print("Gráfico guardado: resumen_adf.png")
