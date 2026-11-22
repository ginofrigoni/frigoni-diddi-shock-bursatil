# noticias_a_precio

¿Las noticias ayudan a predecir si la acción sube en la rueda siguiente?

**Fase de CRISP-DM:** 4, modelado. El diseño está en `../README.md` y se fijó antes de ver resultados.

- **Recibe:** `3_preparacion_de_los_datos/dataset_unificado/salidas/dataset_panel.csv`.
- **Unidad:** una acción en una rueda (17 empresas).
- **Objetivo:** 1 si el retorno de la rueda siguiente es mayor que 0.
- **Modelo A:** retornos de t a t−4, volumen anormal y VIX.
- **Modelo B:** A más sentimiento inesperado, sentimiento propio y hubo_noticia.
- **Datos:**
  - entrenamiento: 2.805 filas (165 ruedas, del 02/06/2025 al 30/01/2026);
  - test: 986 filas (58 ruedas, del 02/02/2026 al 29/04/2026).
- **Entrega:** `salidas/metricas_test.csv`, `delta_auc.csv`, `hiperparametros.csv`, `importancias.csv`, `predicciones_test.csv`, `verificaciones.csv` y `noticias_a_precio.png`; `metricas.csv`.
- **Script:** `python noticias_a_precio.py`
- **Estado:** ✅ 6/6 controles.

## Resultado (test)

| | AUC | Balanced accuracy | F1 |
|---|---|---|---|
| Línea base (siempre "no sube") | 0,500 | 0,500 | 0,000 |
| Logística A | 0,533 | 0,529 | 0,472 |
| Logística B | 0,521 | 0,516 | 0,499 |
| Random forest A | 0,533 | 0,525 | 0,502 |
| Random forest B | 0,497 | 0,483 | 0,505 |

**ΔAUC (B − A):**
- Logística: −0,012, con IC 95 % [−0,055; +0,037].
- Random forest: −0,037, con IC 95 % [−0,089; +0,024].

**Las noticias no mejoran la predicción del precio.** Los dos modelos quedan apenas por encima del azar.
