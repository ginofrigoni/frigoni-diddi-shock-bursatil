# dataset_unificado

Junta mercado y noticias en las tablas que usan los modelos.

**Fase de CRISP-DM:** 3, preparación de los datos (integrar datos).

- `salidas/dataset_panel.csv`: **17 empresas × 244 ruedas = 4.148 filas**.
  - Mercado: retorno, vol_anormal y vix_arg.
  - Noticias: sentimiento_inesperado, sentimiento_propio y hubo_noticia.
  - Marcas: periodo (entrenamiento o test), dia_electoral, eco_electoral, abril_2026 y regimen (solo para el anexo).
- `salidas/dataset_mercado.csv`: una fila por rueda (244). Es para la dirección inversa.
- `salidas/diccionario_variables.csv`, `descriptivos.csv`, `verificaciones.csv` y `panorama.png`.
- `metricas.csv`.

**Script:** `python construir_datasets.py`

**Estado:** ✅ 12/12 controles. Retorno, volumen anormal, VIX y hubo_noticia son idénticos a la 5.0 en las 17 empresas.

## Decisiones de este paso

- **Corte temporal:** el test empieza el **01/02/2026** (febrero, marzo y abril de 2026). Quedan 185 ruedas de entrenamiento y 59 de test. *Falta confirmarlo antes de modelar.*
- **K del sentimiento propio:** se estima **solo con las ruedas de entrenamiento**, para que el test no influya en ninguna variable. Da 8,85; con todas las ruedas, como en la 5.0, daba 10,4. Las dos versiones correlacionan 0,9996.
- **Sentimiento propio comparado con el `tono_propio` de la 5.0:** correlación 0,889. Cambia porque las etiquetas ahora tienen 3 clases.
- **Renombres (D4):**
  - `tono_propio` → `sentimiento_propio`;
  - `peso_tono_propio` → `peso_sentimiento_propio`;
  - `sent_anormal` → `sentimiento_inesperado`.
- **Columnas que salen:** clustering, atención, shocks y monto operado.
