# regla_17

Asigna cada nota a la rueda en la que el mercado pudo reaccionar a ella:
- la hora de publicación se pasa a hora argentina;
- si la nota salió antes de las 17:00 de un día con rueda, cuenta para ese día;
- si salió a las 17:00 o más tarde, o en un día sin rueda, cuenta para la rueda siguiente.

**Fase de CRISP-DM:** 3, preparación de los datos (integrar datos).

- **Recibe:**
  - `2_comprension_de_los_datos/noticias/datos/*.jsonl`, el corpus;
  - `reporte_dedup_semantico.json`, los duplicados que se excluyen;
  - `3_preparacion_de_los_datos/vix_argentino/salidas/vix_arg.csv`, el calendario de ruedas.
- **Entrega:**
  - `salidas/nota_a_rueda.csv`: cada nota con su rueda, si salió después del cierre y si su hora es sospechosa;
  - `salidas/notas_por_rueda.csv`: cuántas notas tiene cada rueda (es descriptivo, no entra al modelo);
  - `salidas/verificaciones.csv` y `salidas/regla_17.png`;
  - `metricas.csv`: las cifras que usan el informe y la presentación.
- **Script:** `python alinear_noticias_ruedas.py`
- **Estado:** ✅ 7/7 controles. Las salidas son idénticas a las de la 5.0.
