# 4_modelado

Fase 4 de CRISP-DM: los modelos, el diseño de la prueba (el corte temporal) y las métricas de cada modelo.

| Subcarpeta | Pregunta |
|---|---|
| `noticias_a_precio/` | ¿Las noticias ayudan a predecir si la acción sube mañana? |
| `precio_a_sentimiento/` | ¿El mercado ayuda a predecir el sentimiento de las noticias de mañana? |

`modelado_comun.py` tiene lo que comparten las dos: el ajuste de los modelos, las métricas y el bootstrap.

## Diseño fijado ANTES de ver resultados (22/11/2026)

**Comparación:** en cada dirección se entrena un modelo A, sin la información del otro lado, y un modelo B, que es A más esa información. Se evalúan los dos en el mismo test.

**Algoritmos:**
- **Regresión logística (principal):** penalización L2; las variables se estandarizan con la media y el desvío del entrenamiento; C ∈ {0,001; 0,01; 0,1; 1; 10}.
- **Random forest (confirmatorio):** 500 árboles; profundidad ∈ {3, 5, 8}; mínimo de filas por hoja ∈ {20, 50, 100}; `max_features = sqrt`.
- Los hiperparámetros se eligen **solo con el entrenamiento**, por validación cruzada temporal: 5 cortes que se van extendiendo, separados por fecha, maximizando el AUC.

**Corte temporal:** entrenamiento hasta el 30/01/2026 y test desde el 01/02/2026 (febrero a abril de 2026). **El test se usa una sola vez.**

**Métricas en el test:**
- AUC, balanced accuracy, F1 de la clase 1, accuracy y matriz de confusión, con umbral 0,5.
- **Línea base:** predecir siempre la clase más frecuente en el entrenamiento.

**Prueba de la hipótesis:** ΔAUC = AUC(B) − AUC(A), con intervalo de confianza del 95 %.
- Se calcula con un bootstrap por bloques de 5 ruedas del test: 2.000 repeticiones y semilla 42.
- Se remuestrean **ruedas** y no filas, porque las acciones de un mismo día se mueven juntas.
- Las noticias **aportan** en una dirección si el límite inferior del intervalo de la regresión logística es mayor que 0. El random forest confirma.

**Cuándo se conoce cada dato:** las variables de la rueda t se conocen al cierre de t (17:00). La regla de las 17:00 manda las notas publicadas después del cierre a la rueda siguiente, así que ninguna variable usa información posterior al cierre de t.
