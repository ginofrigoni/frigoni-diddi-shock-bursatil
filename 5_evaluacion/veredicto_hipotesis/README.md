# veredicto_hipotesis

Aplica el criterio de aceptación de H1, fijado antes de ver los resultados, a los resultados de las otras carpetas. No calcula nada nuevo.

**Fase de CRISP-DM:** 5, evaluación (los resultados contra el criterio de éxito).

- **H1:** es posible construir una metodología de ciencia de datos que mida el sentimiento de las noticias económicas y lo relacione con el comportamiento de las acciones argentinas.
- **H0:** no es posible.

| Parte del criterio | Resultado | ¿Cumple? |
|---|---|---|
| 1. FinBETO supera a la referencia | F1 macro 0,697 contra 0,542 (+15,5 puntos) | ✅ |
| 2a. Noticias → precio | ΔAUC −0,012 [−0,054; +0,036] | ❌ |
| 2b. Precio → sentimiento | ΔAUC **+0,152 [+0,074; +0,267]** | ✅ |
| 2. Al menos una dirección | precio → sentimiento | ✅ |
| **Veredicto** | **Se rechaza H0: se acepta H1** | |

**Contexto para la discusión:**
- precio → sentimiento aporta en 6 de 9 variantes de robustez; el ΔAUC es positivo en las 9;
- noticias → precio no aporta en ninguna de las 9;
- Granger da retorno → sentimiento en 14 de 17 empresas, y sentimiento → retorno en 0 de 17.

**Lectura para el informe:** la metodología **mide** el sentimiento de la prensa económica mejor que un modelo genérico, y lo **relaciona** con el mercado. La relación va del mercado hacia las noticias: **los medios siguen al mercado; no lo anticipan.**

- **Script:** `python veredicto.py`
- **Entrega:** `salidas/veredicto.csv` y `metricas.csv`.
