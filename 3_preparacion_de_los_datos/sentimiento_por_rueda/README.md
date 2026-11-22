# sentimiento_por_rueda

Calcula el sentimiento de las noticias en cada una de las 244 ruedas y el **sentimiento inesperado**: el de la rueda menos el promedio de las 20 ruedas anteriores (0 = lo habitual).

**Fase de CRISP-DM:** 3, preparación de los datos (construir atributos derivados).

- **Recibe:**
  - `../regla_17/salidas/nota_a_rueda.csv`;
  - `../sentimiento_finbeto/salidas/sentimiento_por_nota.csv`;
  - `../vix_argentino/salidas/vix_arg.csv`.
- **Entrega:**
  - `salidas/sentimiento_por_rueda.csv`, con sent_neto, sent_neto_portal, sentimiento_inesperado y dia_electoral;
  - `salidas/verificaciones.csv` y `salidas/sentimiento_por_rueda.png`;
  - `metricas.csv`.
- **Script:** `python sentimiento_por_rueda.py`
- **Estado:** ✅ 7/7 controles.
  - Con las etiquetas de la 5.0, este cálculo reproduce exactamente la serie de la 5.0.
  - Con FinBETO de 3 clases, la serie correlaciona 0,976 con la de la 5.0, y el sentimiento inesperado 0,970.
  - El promedio bajó de +3,9 a +1,2 porque el modelo nuevo clasifica más oraciones como negativas. Al sentimiento inesperado no le afecta, porque compara contra las ruedas anteriores.
- **Cambios respecto de la 5.0:**
  - ya no se calculan los shocks ni la atención de los medios;
  - el sentimiento inesperado (antes `sent_anormal`) se calcula acá y no en el dataset.
