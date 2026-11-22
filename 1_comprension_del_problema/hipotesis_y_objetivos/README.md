# hipotesis_y_objetivos

**Fase de CRISP-DM:** 1, comprensión del problema.

## Hipótesis

- **H1:** es posible construir una metodología de ciencia de datos que mida el sentimiento de las noticias económicas argentinas y lo relacione con el comportamiento de las acciones de BYMA.
- **H0:** no es posible: o el sentimiento no se mide mejor que con un modelo genérico, o no se relaciona con las acciones en ninguna dirección.

## Criterio de aceptación (fijado antes de ver los resultados)

1. **Medir:** FinBETO supera a un modelo de sentimiento en español ya existente en noticias no vistas, medido con el F1 macro.
2. **Relacionar:** en al menos una dirección (noticias → precio o precio → sentimiento), el modelo con la información del otro lado supera al modelo sin ella. Esto quiere decir que el límite inferior del IC 95 % de ΔAUC es mayor que 0, con regresión logística.

## Objetivos específicos (escritos como resultados)

1. Un corpus de noticias económicas depurado, con cada nota asignada a su rueda.
2. Un modelo de sentimiento para la prensa económica, evaluado en noticias no vistas y comparado con uno existente.
3. Las variables por acción y por rueda: sentimiento inesperado, sentimiento propio, retorno, volumen anormal y VIX.
4. Un modelo predictivo evaluado en ruedas no vistas que indique en qué dirección va la relación.

El veredicto está en `5_evaluacion/veredicto_hipotesis/`.
