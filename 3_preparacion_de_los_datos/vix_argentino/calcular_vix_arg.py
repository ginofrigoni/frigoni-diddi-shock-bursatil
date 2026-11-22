"""
VIX argentino casero — tesis version 3.0
Tesina: Impacto de shocks informativos en empresas argentinas

El VIX de Chicago Board se calcula con precios de opciones sobre el S&P 500:
mide volatilidad IMPLÍCITA (lo que el mercado espera). En Argentina no hay
mercado de opciones con la liquidez necesaria para eso, así que se construye
un análogo con volatilidad REALIZADA: qué tan dispersos fueron los retornos
del índice Merval en los últimos 20 días, anualizado.

Nota importante: este cálculo usa el índice ^MERV directamente, no depende
de qué acciones estén en el panel de 01_scraping_acciones — es una medida
de mercado general, no de las empresas individuales.

CÓMO LEERLO -- EL ECO DE LA VENTANA DE 20 DÍAS: un único día con un
movimiento extremo (en cualquier dirección, suba o baja) queda adentro de
la ventana durante exactamente 20 ruedas: el VIX salta el día que entra y
cae de golpe el día que sale, sin que el mercado haya hecho nada especial
ese día. Ej.: 27/10/2025 (+21,8%) -> VIX de 30% a 80% ese día, y de 91% a
52% el 25/11/2025, cuando ese día sale de la ventana.

VENTANA FINAL: 2025-01-02 -> 2026-05-03. Es la ventana real del corpus de
noticias del compañero (lado de sentimiento) — la fecha que va a definir el
dataset final combinado, así que es la que se usa acá y de la que después
toman fecha ADF (04_adf) y volatilidad por acción (05_volatilidad_ranking):
ambos leen el rango directamente de vix_arg.csv, no repiten la fecha a mano,
para que no se puedan desalinear entre ellos.

Se descarga desde antes (2024-11-15) solo para tener los 20 días previos
que necesita la ventana rodante -- esos días de "calentamiento" no quedan
en el vix_arg.csv final, se recortan al guardar.

Input:  ninguno (descarga ^MERV en vivo de Yahoo Finance)
Output: vix_arg.csv   (fecha, merv_cierre, retorno_diario, vix_arg) -- 2025-01-02 -> 2026-05-03
        vix_arg.png   (Merval + VIX argentino, dos paneles)
"""

import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt

# ── Ventana de descarga (con margen para la ventana rodante de 20 días) ─────
DESCARGA_INICIO = "2024-11-15"
DESCARGA_FIN    = "2026-05-04"   # exclusivo en yfinance -> último día real: 2026-05-03

# ── Ventana final -- la del corpus de noticias del compañero ────────────────
FECHA_INICIO = "2025-01-02"
FECHA_FIN    = "2026-05-03"

# ── Descarga del índice Merval ───────────────────────────────────────────────
print(f"Descargando ^MERV ({DESCARGA_INICIO} -> {DESCARGA_FIN}, incluye margen para la ventana rodante)...")
merv = yf.download("^MERV", start=DESCARGA_INICIO, end=DESCARGA_FIN, progress=False, auto_adjust=True)
if isinstance(merv.columns, pd.MultiIndex):
    merv.columns = merv.columns.get_level_values(0)
print(f"Días descargados: {len(merv)}")

# ── Retorno diario ────────────────────────────────────────────────────────────
merv["retorno_diario"] = merv["Close"].pct_change()

# ── VIX argentino: desvío estándar rodante de 20 días, anualizado ───────────
VENTANA = 20
merv["vix_arg"] = merv["retorno_diario"].rolling(window=VENTANA).std() * (252 ** 0.5) * 100

# ── Recortar a la ventana final y guardar ───────────────────────────────────
resultado = merv[["Close", "retorno_diario", "vix_arg"]].copy()
resultado.columns = ["merv_cierre", "retorno_diario", "vix_arg"]
resultado.index.name = "fecha"
resultado = resultado.dropna()
resultado = resultado[(resultado.index >= FECHA_INICIO) & (resultado.index <= FECHA_FIN)]

resultado.to_csv("vix_arg.csv")
print(f"\nGuardado: vix_arg.csv ({len(resultado)} filas)")

# ── Estadísticas básicas ──────────────────────────────────────────────────────
print("\n── Estadísticas del vix_arg ──")
print(f"  Promedio : {resultado['vix_arg'].mean():.1f}%")
print(f"  Mínimo   : {resultado['vix_arg'].min():.1f}%  (mercado más calmo, {resultado['vix_arg'].idxmin().date()})")
print(f"  Máximo   : {resultado['vix_arg'].max():.1f}%  (mercado más nervioso, {resultado['vix_arg'].idxmax().date()})")
print(f"  Rango de fechas: {resultado.index.min().date()} -> {resultado.index.max().date()}")

# ── Gráfico ────────────────────────────────────────────────────────────────
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7), sharex=True)

ax1.plot(resultado.index, resultado["merv_cierre"], color="steelblue", linewidth=1.2)
ax1.set_title(f"Índice Merval ({FECHA_INICIO} – {FECHA_FIN})", fontsize=13)
ax1.set_ylabel("Puntos")
ax1.grid(alpha=0.3)

ax2.plot(resultado.index, resultado["vix_arg"], color="firebrick", linewidth=1.2)
ax2.axhline(resultado["vix_arg"].mean(), color="gray", linestyle="--", linewidth=1,
            label=f"Promedio: {resultado['vix_arg'].mean():.1f}%")
ax2.fill_between(resultado.index, resultado["vix_arg"], resultado["vix_arg"].mean(),
                  where=resultado["vix_arg"] > resultado["vix_arg"].mean(),
                  alpha=0.2, color="firebrick", label="Por encima del promedio (nervioso)")
ax2.set_title(f"VIX Argentina — volatilidad realizada (ventana {VENTANA} días, anualizada)", fontsize=13)
ax2.set_ylabel("Volatilidad (%)")
ax2.legend()
ax2.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("vix_arg.png", dpi=150)
plt.close()
print("\nGráfico guardado: vix_arg.png")
