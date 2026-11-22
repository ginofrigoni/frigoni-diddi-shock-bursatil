# mercado

Precios y volumen diarios de las acciones de BYMA (Yahoo Finance, tres años). **Fase de CRISP-DM:** 2, comprensión de los datos.

- `datos/precios_diarios_47_acciones.csv`: precios de las 47 acciones del panel.
- `datos/panel_acciones_final.csv`: las 47 acciones, con su sector y si integran el S&P Merval.
- `datos/cobertura_53_candidatas.csv` y `descartadas_por_cobertura.csv`: cómo se eligieron (cobertura completa y al menos 90 % de días con volumen).
- `scraping_acciones.py`: la descarga. Es **documentación** y no se vuelve a correr.
- **Lo usan:** `sentimiento_por_empresa` y `dataset_unificado`.
