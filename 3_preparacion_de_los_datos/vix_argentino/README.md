# vix_argentino

VIX argentino: la volatilidad realizada del S&P Merval en las últimas 20 ruedas, anualizada. **Fase de CRISP-DM:** 3, preparación (construir atributos derivados).

- `salidas/vix_arg.csv`: el VIX por rueda (del 02/01/2025 al 30/04/2026). Lo calculó el lado bursátil con `calcular_vix_arg.py`, que es documentación y no se vuelve a correr.
- `escala_vix.py`:
  - verifica que la fórmula reproduce el VIX;
  - define la **escala por terciles** de las 244 ruedas: bajo hasta 33,8 %, medio de 33,8 % a 39,6 %, alto más de 39,6 %;
  - hace la figura `salidas/vix_arg.png`.
- **Entrega:** `salidas/escala_vix.csv` y `metricas.csv`.
- **Lo usan:** `regla_17` (como calendario de ruedas), `sentimiento_por_rueda` y `dataset_unificado`.
