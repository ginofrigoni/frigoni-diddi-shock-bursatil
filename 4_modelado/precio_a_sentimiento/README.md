# precio_a_sentimiento

¿El mercado ayuda a predecir el sentimiento de las noticias de la rueda siguiente?

**Fase de CRISP-DM:** 4, modelado. El diseño está en `../README.md` y se fijó antes de ver resultados.

- **Recibe:** `3_preparacion_de_los_datos/dataset_unificado/salidas/dataset_mercado.csv`.
- **Unidad:** una rueda.
- **Objetivo (D9):** 1 si el sentimiento inesperado de la rueda siguiente es mayor que 0.
- **Modelo A:** sentimiento inesperado de t a t−4.
- **Modelo B:** A más el retorno del Merval de t a t−4 y el VIX.
- **Datos:**
  - entrenamiento: 161 ruedas (del 06/06/2025 al 30/01/2026);
  - test: 58 ruedas (del 02/02/2026 al 29/04/2026).
- **Entrega:** lo mismo que `noticias_a_precio/`.
- **Script:** `python precio_a_sentimiento.py`
- **Estado:** ✅ 5/5 controles.

## Resultado (test)

| | AUC | Balanced accuracy | F1 |
|---|---|---|---|
| Línea base (siempre "> habitual") | 0,500 | 0,500 | 0,532 |
| Logística A | 0,526 | 0,545 | 0,378 |
| **Logística B** | **0,678** | **0,623** | 0,471 |
| Random forest A | 0,497 | 0,545 | 0,378 |
| **Random forest B** | **0,655** | **0,620** | 0,487 |

**ΔAUC (B − A):**
- Logística: **+0,152**, con IC 95 % [+0,074; +0,267] y p = 0,001.
- Random forest: **+0,158**, con IC 95 % [+0,059; +0,323] y p = 0,005.

**El mercado sí mejora la predicción del sentimiento de las noticias.** La variable que más pesa en el modelo B es el retorno del Merval del mismo día (coeficiente estandarizado 0,51), seguida por el retorno del día anterior (0,23). Coincide con lo que encontró Granger en la 5.0: los medios siguen al mercado.

**Cuidado:** el test tiene solo 58 ruedas, por eso el intervalo es ancho. Además, abril de 2026, que no tiene iProfesional, queda dentro del test. Las dos cosas se revisan en el anexo.
