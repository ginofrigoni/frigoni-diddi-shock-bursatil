"""
Regímenes de mercado vía Hidden Markov Model (Markov-Switching).

Modela el VIX argentino como una serie generada por un número finito de
estados ocultos (regímenes de volatilidad) que se alternan según una cadena
de Markov. Cada día se le asigna, vía probabilidades suavizadas, el régimen
más probable.

Modelo: statsmodels.tsa.regime_switching.markov_regression.MarkovRegression
(Markov-Switching de media y varianza — no es un HMM discreto clásico, pero
se lo suele llamar "HMM" en la literatura de regímenes de mercado).

El número de regímenes k NO se fija a mano: se barre k=2..6, se calcula el
BIC de cada ajuste y se elige el k de menor BIC entre los que convergen sin
producir un régimen degenerado (menos de 5 días).

Input:  ../03_vix_argentino/vix_arg.csv   (fecha, merv_cierre, retorno_diario, vix_arg)
Output: hmm_regimen_mercado.csv           (1 fila por día: régimen asignado)
        matriz_transicion.csv             (P(pasar de régimen A a B al día siguiente))
        bic_por_k.csv                     (BIC de cada k barrido)
        bic_curva.png
        hmm_regimen_mercado.png           (Merval / VIX / probabilidades, coloreados por régimen)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
np.random.seed(42)  # search_reps arranca desde puntos aleatorios -> se fija la semilla para que el script sea reproducible

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.cm as cm

from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

# ─────────────────────────────────────────
# PASO 1: Cargar datos
# ─────────────────────────────────────────
df = pd.read_csv("../03_vix_argentino/vix_arg.csv", parse_dates=["fecha"], index_col="fecha")
print(f"Días cargados: {len(df)}  ({df.index.min().date()} -> {df.index.max().date()})")

# ─────────────────────────────────────────
# PASO 2: Barrido de k -> BIC real (no fijado a mano)
#
# Se prueban k=2..6 regímenes. El optimizador por defecto (BFGS) es inestable
# en esta serie (con em_iter>=3 el SVD interno del EM no converge). Se usa
# Nelder-Mead (method="nm"), que converge de forma estable y reproducible en
# k=3 (mismo resultado con 10 semillas distintas).
#
# Para k>=4 el "régimen extra" es siempre degenerado: un estado con varianza
# casi nula pegado a un único día (con k=4: el 01/12/2025, VIX 40,3%, un día
# de transición mientras el VIX bajaba después de las elecciones), mientras
# los otros 3 regímenes quedan iguales a los de k=3. Una varianza que tiende
# a cero hace explotar la verosimilitud en ese punto y "mejora" el BIC de
# forma artificial — es la singularidad clásica de los modelos de mezcla, no
# un régimen real.
#
# Regla de selección (transparente, no manual): de los k que (a) convergen
# (mle_retvals["converged"]==True) y (b) no producen ningún régimen
# degenerado (mínimo de días por régimen >= UMBRAL_DIAS_MIN_REGIMEN), se
# elige el que minimiza el BIC.
# ─────────────────────────────────────────
K_RANGO = range(2, 7)
UMBRAL_DIAS_MIN_REGIMEN = 5
resultados_k = []
modelos = {}

print("\n── Barrido de k (BIC) ──")
for k in K_RANGO:
    mod_k = MarkovRegression(df["vix_arg"], k_regimes=k, trend="c", switching_variance=True)
    res_k = None
    for reps in (20, 10, 5, 1, 0):
        try:
            res_k = mod_k.fit(search_reps=reps, em_iter=2, method="nm", maxiter=5000, maxfun=5000, disp=False)
            break
        except (np.linalg.LinAlgError, ValueError):
            continue
    if res_k is None:
        print(f"  k={k}:  no convergió con ningún número de arranques -> se descarta del barrido")
        continue

    prob_k = np.asarray(res_k.smoothed_marginal_probabilities)
    regimen_k = prob_k.argmax(axis=1)
    dias_por_regimen = pd.Series(regimen_k).value_counts()
    min_dias = int(dias_por_regimen.min())
    convergio = bool(res_k.mle_retvals.get("converged", False))
    degenerado = min_dias < UMBRAL_DIAS_MIN_REGIMEN

    resultados_k.append({
        "k": k, "aic": res_k.aic, "bic": res_k.bic, "loglik": res_k.llf,
        "convergio": convergio, "min_dias_regimen": min_dias, "degenerado": degenerado,
    })
    modelos[k] = res_k
    flag = "" if (convergio and not degenerado) else "  <- descartado (no converge o régimen degenerado)"
    print(f"  k={k}:  AIC={res_k.aic:.1f}   BIC={res_k.bic:.1f}   logL={res_k.llf:.1f}   "
          f"min_días/régimen={min_dias}   convergió={convergio}{flag}")

bic_df = pd.DataFrame(resultados_k)
bic_df.to_csv("bic_por_k.csv", index=False)

candidatos = bic_df[(bic_df["convergio"]) & (~bic_df["degenerado"])]
if candidatos.empty:
    raise RuntimeError("Ningún k convergió sin degenerar — revisar el barrido.")
MEJOR_K = int(candidatos.loc[candidatos["bic"].idxmin(), "k"])
res = modelos[MEJOR_K]
print(f"\nk elegido (mínimo BIC entre los que convergen sin degenerar): {MEJOR_K}")

plt.figure(figsize=(7, 4.5))
plt.plot(bic_df["k"], bic_df["bic"], color="#1C3A5C", linewidth=1.4, zorder=1)
descartados = bic_df[(~bic_df["convergio"]) | (bic_df["degenerado"])]
validos = bic_df[(bic_df["convergio"]) & (~bic_df["degenerado"])]
plt.scatter(validos["k"], validos["bic"], color="#1C3A5C", zorder=3, s=55, label="Converge, sin régimen degenerado")
plt.scatter(descartados["k"], descartados["bic"], color="#9AA7B0", zorder=3, s=55, marker="x",
            label="No converge o régimen degenerado (< 5 días)")
plt.scatter([MEJOR_K], [bic_df.loc[bic_df["k"] == MEJOR_K, "bic"].values[0]],
            color="#C1272D", zorder=5, s=90, label=f"k elegido = {MEJOR_K}")
plt.xlabel("k (número de regímenes)")
plt.ylabel("BIC")
plt.title("Selección de k por BIC — Markov-Switching sobre VIX argentino")
plt.xticks(list(K_RANGO))
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig("bic_curva.png", dpi=150)
plt.close()
print("Gráfico guardado: bic_curva.png")

# ─────────────────────────────────────────
# PASO 3: Extraer el régimen más probable por día
# (probabilidades suavizadas -> argmax)
# ─────────────────────────────────────────
prob = res.smoothed_marginal_probabilities
df["regimen"] = prob.values.argmax(axis=1)

# ─────────────────────────────────────────
# PASO 4: Interpretar regímenes
# Se ordenan por vix_arg promedio: el más bajo = "Muy calmo", el más alto = "Crisis"/"Pánico"
# ─────────────────────────────────────────
vix_por_regimen = df.groupby("regimen")["vix_arg"].mean().sort_values()

# Nombres según cuántos regímenes haya: el más volátil siempre es "Tenso" o
# más. (Cortar una lista fija con [:k] hacía que, con k=3, el régimen de VIX
# promedio ~70% quedara llamado "Moderado".)
ETIQUETAS_POR_K = {
    2: ["Calmo", "Tenso"],
    3: ["Calmo", "Moderado", "Tenso"],
    4: ["Muy calmo", "Calmo", "Moderado", "Tenso"],
    5: ["Muy calmo", "Calmo", "Moderado", "Tenso", "Crisis"],
    6: ["Muy calmo", "Calmo", "Moderado", "Tenso", "Crisis", "Pánico"],
}
etiquetas = ETIQUETAS_POR_K[MEJOR_K]
nombres = {reg: etiquetas[i] for i, (reg, _) in enumerate(vix_por_regimen.items())}
df["regimen_nombre"] = df["regimen"].map(nombres)

# ─────────────────────────────────────────
# PASO 5: Características de cada régimen
# ─────────────────────────────────────────
print("\n── Características de cada régimen ──")
resumen = df.groupby("regimen_nombre").agg(
    retorno_prom=("retorno_diario", "mean"),
    vix_prom=("vix_arg", "mean"),
    dias=("vix_arg", "count"),
).reindex(etiquetas)

resumen["retorno_prom"] = (resumen["retorno_prom"] * 100).round(3)
resumen["vix_prom"] = resumen["vix_prom"].round(1)
resumen["pct_dias"] = (resumen["dias"] / len(df) * 100).round(1)

print(resumen.rename(columns={
    "retorno_prom": "Retorno prom (%)",
    "vix_prom": "VIX prom (%)",
    "dias": "Días",
    "pct_dias": "% del período",
}).to_string())

# ─────────────────────────────────────────
# PASO 6: Matriz de transición -> SE GUARDA A CSV
# P(ir de estado A -> estado B al día siguiente)
#
# statsmodels devuelve regime_transition[i, j] = P(pasar a régimen i | venía
# de régimen j) -- el régimen DESTINO está en la fila y el ORIGEN en la
# columna (matriz left-stochastic: las COLUMNAS suman 100). Se transpone acá
# para mostrarla en la convención habitual "fila = origen, columna = destino"
# (right-stochastic, las FILAS suman 100), que es como se lee en el texto.
# ─────────────────────────────────────────
print("\n── Matriz de transición (%) — fila = régimen hoy, columna = régimen mañana ──")
trans_raw = res.regime_transition
if trans_raw.ndim == 3:
    trans_raw = trans_raw.mean(axis=2)
trans_raw = trans_raw.T  # fila=origen, columna=destino

trans = pd.DataFrame(
    trans_raw * 100,
    index=[nombres[i] for i in range(MEJOR_K)],
    columns=[nombres[i] for i in range(MEJOR_K)],
).round(1)
trans = trans.reindex(index=etiquetas, columns=etiquetas)  # ordenado de menor a mayor volatilidad
print(trans.to_string())
trans.to_csv("matriz_transicion.csv")
print("\nGuardado: matriz_transicion.csv")

# ─────────────────────────────────────────
# PASO 7: Guardar CSV con el régimen día a día
#
# regimen / regimen_nombre usan las probabilidades SUAVIZADAS: para cada día
# miran toda la serie, incluidos los días posteriores. Sirven para describir
# el período, pero no para anticipar nada (usarían información del futuro).
# Se guardan también las probabilidades FILTRADAS, que en cada día solo usan
# la información hasta ese día: son las que corresponden si el régimen se usa
# para pronosticar o para condicionar un análisis "en tiempo real".
# ─────────────────────────────────────────
prob_filt = res.filtered_marginal_probabilities
for i in range(MEJOR_K):
    df[f"prob_suavizada_{nombres[i]}"] = prob.iloc[:, i].values.round(4)
for i in range(MEJOR_K):
    df[f"prob_filtrada_{nombres[i]}"] = prob_filt.iloc[:, i].values.round(4)
df["regimen_filtrado_nombre"] = pd.Series(prob_filt.values.argmax(axis=1), index=df.index).map(nombres)
coincide = (df["regimen_filtrado_nombre"] == df["regimen_nombre"]).mean() * 100
print(f"\nRégimen filtrado vs. suavizado: coinciden en {coincide:.1f}% de los días")

df.to_csv("hmm_regimen_mercado.csv")
print("Guardado: hmm_regimen_mercado.csv")

# ─────────────────────────────────────────
# PASO 8: Graficar
# ─────────────────────────────────────────
# Colores fijos por nombre de régimen. (El centro del mapa RdYlBu_r es un
# amarillo casi blanco que, con el sombreado al 30%, no se distinguía.)
COLOR_REGIMEN = {
    "Muy calmo": "#2C5F8A",
    "Calmo":     "#4A90C8",
    "Moderado":  "#F2A900",   # ámbar, bien visible tanto sombreado como en línea
    "Tenso":     "#D7301F",
    "Crisis":    "#8B0000",
    "Pánico":    "#4B0030",
}
colores = {nombre: COLOR_REGIMEN[nombre] for nombre in etiquetas}

fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)

ax = axes[0]
for reg_name in etiquetas:
    mask = df["regimen_nombre"] == reg_name
    ax.fill_between(df.index, 0, 1, where=mask, transform=ax.get_xaxis_transform(),
                     alpha=0.3, color=colores[reg_name], label=reg_name)
ax.plot(df.index, df["merv_cierre"], color="black", linewidth=1.2)
ax.set_title("Índice Merval — coloreado por régimen detectado", fontsize=12)
ax.set_ylabel("Puntos")
ax.legend(loc="upper left", fontsize=8)
ax.grid(alpha=0.3)

ax = axes[1]
for reg_name in etiquetas:
    mask = df["regimen_nombre"] == reg_name
    ax.fill_between(df.index, 0, 1, where=mask, transform=ax.get_xaxis_transform(),
                     alpha=0.3, color=colores[reg_name])
ax.plot(df.index, df["vix_arg"], color="firebrick", linewidth=1.2)
ax.set_title("VIX Argentina — coloreado por régimen detectado", fontsize=12)
ax.set_ylabel("Volatilidad (%)")
ax.grid(alpha=0.3)

ax = axes[2]
for i, reg_name in enumerate(etiquetas):
    reg_num = [k for k, v in nombres.items() if v == reg_name][0]
    ax.plot(df.index, prob.iloc[:, reg_num], color=colores[reg_name], linewidth=1.2, label=reg_name)
ax.set_title("Probabilidad de cada régimen por día (curvas suavizadas)", fontsize=12)
ax.set_ylabel("Probabilidad")
ax.set_ylim(0, 1)
ax.legend(fontsize=8)
ax.grid(alpha=0.3)

plt.tight_layout()
plt.savefig("hmm_regimen_mercado.png", dpi=150)
plt.close()
print("Gráfico guardado: hmm_regimen_mercado.png")
