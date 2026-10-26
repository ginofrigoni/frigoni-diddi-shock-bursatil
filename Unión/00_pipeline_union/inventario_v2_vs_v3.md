# Inventario: tesis version 2.0 → tesis version 3.0

Generado por `inventario_v2_vs_v3.py`. 230 archivos de la 2.0 (sin entornos virtuales ni cachés; cada carpeta de pesos del modelo cuenta como una fila).

**Estados:** *No pasó* = no está en la 3.0 · *Rehacer en la unión* = se reconstruye en un paso del pipeline · *Reemplazado en 3.0* = hay una versión nueva · *Pasó* = está en la 3.0 (actualizado).

## Resumen

| Grupo | No pasó | Rehacer en la unión | Reemplazado | Pasó | Total |
|---|---:|---:|---:|---:|---:|
| A. Modelo de sentimiento | 24 | · | · | 4 | 28 |
| B. Sentimiento por empresa (versión vieja) | · | · | 2 | · | 2 |
| C. Corpus de noticias | 8 | · | · | 22 | 30 |
| D. NER (entidades) | · | · | · | 5 | 5 |
| E. Lado bursátil | · | · | 23 | · | 23 |
| F. HMM por sector y por acción | 10 | · | · | · | 10 |
| G. Unión de la versión anterior | · | 36 | · | · | 36 |
| H. Plan y documentación | 9 | · | 4 | · | 13 |
| I. Presentación de avance e infografías | 53 | · | · | · | 53 |
| J. Estructura vieja (README) | · | · | 21 | · | 21 |
| K. Bibliografía general | 9 | · | · | · | 9 |

## A. Modelo de sentimiento

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/analisis_beto.ipynb` | 452 KB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/analisis_beto.py` | 9 KB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/beto_articulos.csv` | 601 KB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/beto_oraciones.csv` | 24.3 MB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/beto_serie_diaria.csv` | 59 KB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/muestra_prueba.json` | 326 KB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/baseline_beto_sin_finetuning/serie_temporal_sentimiento.png` | 496 KB | — | Para la tesis (comparación sin ajuste) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/04_learning_curve.ipynb` | 66 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/05_evaluacion.ipynb` | 52 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/06_inferencia.ipynb` | 12 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/beto_oraciones_finetuned.csv` | 169.1 MB | — | Sí (paso U3 de la unión) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/confusion_matrix.png` | 49 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/learning_curve.csv` | 0 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/learning_curve.png` | 49 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/metricas.csv` | 0 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `analisis_complementarios/finetuning_evaluacion/reporte.txt` | 1 KB | — | Para la tesis (métricas del modelo) | Gino |
| No pasó | `pipeline_productivo/03_data_preparation/sentimiento/02_preparar_dataset.ipynb` | 9 KB | — | Para la tesis (de dónde salieron las etiquetas) | Gino |
| No pasó | `pipeline_productivo/03_data_preparation/sentimiento/dataset_etiquetado/checkpoint.jsonl` | 14.4 MB | — | Para la tesis (de dónde salieron las etiquetas) | Gino |
| No pasó | `pipeline_productivo/03_data_preparation/sentimiento/dataset_etiquetado/indice_procesados.json` | 50 KB | — | Para la tesis (de dónde salieron las etiquetas) | Gino |
| No pasó | `pipeline_productivo/03_data_preparation/sentimiento/etiquetado_gemma.ipynb` | 467 KB | — | Para la tesis (de dónde salieron las etiquetas) | Gino |
| No pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/01_further_pretraining.ipynb` | 25 KB | — | Para la tesis (cómo se entrenó) | Gino |
| No pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/03_finetuning.ipynb` | 24 KB | — | Para la tesis (cómo se entrenó) | Gino |
| No pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/beto_finetuned/ (6 archivos)` | 420.0 MB | — | Solo para analizar noticias nuevas | Gino |
| No pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/beto_further_pretrained/ (7 archivos)` | 420.1 MB | — | No (paso intermedio del entrenamiento) | Gino |
| Pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/checkpoint_finetuned.jsonl` | 7.0 MB | Lado Noticias/sentimiento_finbert/ (actualizado) | — | Gino |
| Pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/finetuned_articulos.csv` | 4.0 MB | Lado Noticias/sentimiento_finbert/ (actualizado) | — | Gino |
| Pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/finetuned_serie_diaria.csv` | 186 KB | Lado Noticias/sentimiento_finbert/ (actualizado) | — | Gino |
| Pasó | `pipeline_productivo/04_modeling/sentimiento_finbert/serie_completa_finetuned.py` | 18 KB | Lado Noticias/sentimiento_finbert/ (actualizado) | — | Gino |

## B. Sentimiento por empresa (versión vieja)

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| Reemplazado en 3.0 | `pipeline_productivo/03_data_preparation/construccion_dataset/sentimiento_por_empresa.csv` | 208 KB | Lado Noticias/ner_entidades/resultados_ner/ner_sentimiento_diario.csv | No | Gino |
| Reemplazado en 3.0 | `pipeline_productivo/03_data_preparation/sentimiento/construir_sentimiento_empresa.py` | 8 KB | Lado Noticias/ner_entidades/ (47 empresas, por oración) | No | Gino |

## C. Corpus de noticias

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| No pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/circulo_resultado.png` | 6 KB | — | No (imágenes de formas geométricas sin uso; parecen de otro trabajo) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/circulo_ruido_resultado.png` | 451 KB | — | No (imágenes de formas geométricas sin uso; parecen de otro trabajo) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/cuadrado_resultado.png` | 6 KB | — | No (imágenes de formas geométricas sin uso; parecen de otro trabajo) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/multiple_resultado.png` | 10 KB | — | No (imágenes de formas geométricas sin uso; parecen de otro trabajo) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/rectangulo_resultado.png` | 5 KB | — | No (imágenes de formas geométricas sin uso; parecen de otro trabajo) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/triangulo_resultado.png` | 8 KB | — | No (imágenes de formas geométricas sin uso; parecen de otro trabajo) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/scraping_noticias/noticias_historico.py` | 20 KB | — | No (versión obsoleta, reemplazada por v3) | Gino |
| No pasó | `pipeline_productivo/02_data_understanding/noticias/scraping_noticias/noticias_historico_v2.py` | 20 KB | — | No (versión obsoleta, reemplazada por v3) | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/ambito_economia.json` | 2.2 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/ambito_economia.jsonl` | 2.2 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/ambito_finanzas.json` | 942 KB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/ambito_finanzas.jsonl` | 909 KB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/clarin_economia.json` | 2.2 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/clarin_economia.jsonl` | 2.1 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/clarin_sitemap.json` | 16.8 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/clarin_sitemap.jsonl` | 16.0 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/eleconomista_sitemap.json` | 13.9 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/eleconomista_sitemap.jsonl` | 13.5 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/infobae_economia.json` | 3.2 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/infobae_economia.jsonl` | 3.1 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/iprofesional_sitemap.json` | 33.4 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/iprofesional_sitemap.jsonl` | 32.9 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/lanacion_economia.json` | 2.7 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/lanacion_economia.jsonl` | 2.7 MB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/tn_economia.json` | 676 KB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/resultados/tn_economia.jsonl` | 665 KB | Lado Noticias/noticias/resultados/ (depurado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/scraping_noticias/diagnostico_ambito.py` | 5 KB | Lado Noticias/noticias/scripts/ (actualizado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/scraping_noticias/noticias_diario.py` | 21 KB | Lado Noticias/noticias/scripts/ (actualizado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/scraping_noticias/noticias_historico_v3.py` | 23 KB | Lado Noticias/noticias/scripts/ (actualizado) | — | Gino |
| Pasó | `pipeline_productivo/02_data_understanding/noticias/scraping_noticias/noticias_sitemap.py` | 20 KB | Lado Noticias/noticias/scripts/ (actualizado) | — | Gino |

## D. NER (entidades)

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| Pasó | `analisis_complementarios/ner_entidades/ner_analisis.ipynb` | 22 KB | Lado Noticias/ner_entidades/ (rehecho, 47 empresas) | — | Gino |
| Pasó | `analisis_complementarios/ner_entidades/resultados_ner/ner_articulos.csv` | 99.1 MB | Lado Noticias/ner_entidades/ (rehecho, 47 empresas) | — | Gino |
| Pasó | `analisis_complementarios/ner_entidades/resultados_ner/ner_oraciones.csv` | 260.0 MB | Lado Noticias/ner_entidades/ (rehecho, 47 empresas) | — | Gino |
| Pasó | `analisis_complementarios/ner_entidades/resultados_ner/ner_resumen.csv` | 1.8 MB | Lado Noticias/ner_entidades/ (rehecho, 47 empresas) | — | Gino |
| Pasó | `analisis_complementarios/ner_entidades/resultados_ner/ner_sentimiento.csv` | 695 KB | Lado Noticias/ner_entidades/ (rehecho, 47 empresas) | — | Gino |

## E. Lado bursátil

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| Reemplazado en 3.0 | `analisis_complementarios/clustering_acciones/clustering_merval.ipynb` | 1.3 MB | Lado Bursatil/02_clustering_acciones/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/clustering_acciones/merval_precios.csv` | 3.5 MB | Lado Bursatil/02_clustering_acciones/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/clustering_acciones/resumen_clustering_final.csv` | 13 KB | Lado Bursatil/02_clustering_acciones/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/adf_resultados.csv` | 2 KB | Lado Bursatil/04_adf/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/adf_resultados.png` | 94 KB | Lado Bursatil/04_adf/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/adf_test.py` | 6 KB | Lado Bursatil/04_adf/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/merval_precios.csv` | 3.5 MB | Lado Bursatil/01_scraping_acciones/ (copia repetida) | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/ranking_volatilidad.png` | 147 KB | Lado Bursatil/05_volatilidad_ranking/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/ranking_volatilidad.py` | 4 KB | Lado Bursatil/05_volatilidad_ranking/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/vix_arg.csv` | 14 KB | Lado Bursatil/03_vix_argentino/ (copia repetida) | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/volatilidad_acciones.csv` | 81 KB | Lado Bursatil/05_volatilidad_ranking/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/volatilidad_acciones.png` | 830 KB | Lado Bursatil/05_volatilidad_ranking/ | No | Nicolás |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/volatilidad_por_accion.py` | 6 KB | Lado Bursatil/05_volatilidad_ranking/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/bursatil/calcular_vix_arg.py` | 4 KB | Lado Bursatil/03_vix_argentino/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/bursatil/descargar_merval.py` | 6 KB | Lado Bursatil/01_scraping_acciones/scraping_acciones.py | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/bursatil/merval_precios.csv` | 1.6 MB | Lado Bursatil/01_scraping_acciones/precios_diarios_47_acciones.csv | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/bursatil/merval_resumen.csv` | 2 KB | Lado Bursatil/01_scraping_acciones/panel_acciones_final.csv | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/bursatil/vix_arg.csv` | 14 KB | Lado Bursatil/03_vix_argentino/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/hmm_regimen_mercado/Cadenas_Markov_HMM.docx` | 11 KB | Lado Bursatil/06_hmm_regimen_mercado/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/hmm_regimen_mercado/Cadenas_Markov_HMM.md` | 5 KB | Lado Bursatil/06_hmm_regimen_mercado/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/hmm_regimen_mercado/hmm_mercado_general.csv` | 16 KB | Lado Bursatil/06_hmm_regimen_mercado/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/hmm_regimen_mercado/hmm_mercado_general.png` | 243 KB | Lado Bursatil/06_hmm_regimen_mercado/ | No | Nicolás |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/hmm_regimen_mercado/hmm_nivel1_mercado.py` | 7 KB | Lado Bursatil/06_hmm_regimen_mercado/ | No | Nicolás |

## F. HMM por sector y por acción

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_acciones.csv` | 451 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_acciones.png` | 1.8 MB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_acciones_resumen_dias.csv` | 1 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_bic_curva.png` | 44 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_nivel2_sectores.py` | 7 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_nivel3_acciones.py` | 8 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_sectores.csv` | 117 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/hmm_sectores.png` | 670 KB | — | Decidir: dejar afuera o rehacer | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/merval_precios.csv` | 3.5 MB | — | No (copia repetida de precios) | Nicolás |
| No pasó | `analisis_complementarios/hmm_sectores_acciones/vix_arg.csv` | 14 KB | — | No (copia repetida del VIX) | Nicolás |

## G. Unión de la versión anterior

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| Rehacer en la unión | `pipeline_productivo/03_data_preparation/construccion_dataset/construir_dataset_unificado.py` | 6 KB | Unión — paso U4 (datasets) | No (se rehace con las reglas nuevas) | Ambos |
| Rehacer en la unión | `pipeline_productivo/03_data_preparation/construccion_dataset/dataset_panel_acciones.csv` | 1.2 MB | Unión — paso U4 (datasets) | No (se rehace con las reglas nuevas) | Ambos |
| Rehacer en la unión | `pipeline_productivo/03_data_preparation/construccion_dataset/dataset_unificado.csv` | 34 KB | Unión — paso U4 (datasets) | No (se rehace con las reglas nuevas) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/event_study_comparativa.png` | 152 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/event_study_heatmap.png` | 111 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/event_study_resultados.csv` | 2 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_ALUA_BA.png` | 87 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_COME_BA.png` | 73 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_CVH_BA.png` | 104 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_GGAL_BA.png` | 79 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_PAMP_BA.png` | 75 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_TGNO4_BA.png` | 75 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_empresa_VALO_BA.png` | 81 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_general.png` | 91 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_general_completo.png` | 243 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_regimen_calmo.png` | 101 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_regimen_moderado.png` | 77 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_regimen_tenso.png` | 86 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/irf_sector_comunicaciones.png` | 79 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/resultados_adf.csv` | 3 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/var_empresas_granger.csv` | 4 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/var_general_coeficientes.csv` | 1 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/var_general_granger.csv` | 1 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/var_regimenes_granger.csv` | 1 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/resultados/var_sectores_granger.csv` | 2 KB | Unión — pasos U5 a U7 | No (resultados viejos) | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/script1_adf.py` | 4 KB | Unión — paso U5 (ADF) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/script2_var_general.py` | 4 KB | Unión — paso U6 (VAR, Granger, IRF) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/script3_var_empresas.py` | 6 KB | Unión — paso U6 (VAR, Granger, IRF) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/script4_var_regimenes.py` | 5 KB | Unión — paso U6 (VAR, Granger, IRF) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/script4_var_sectores.py` | 7 KB | Unión — paso U6 (VAR, Granger, IRF) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/04_modeling/var_econometria/script5_event_study.py` | 11 KB | Unión — paso U7 (event study) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/05_evaluation/exploracion_resultados/colab_visualizar_shocks.py` | 6 KB | Unión — pasos U2 y U9 (gráficos de shocks) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/05_evaluation/exploracion_resultados/eda_var_empresas.ipynb` | 2.5 MB | Unión — pasos U2 y U9 (gráficos de shocks) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/05_evaluation/exploracion_resultados/explorar_shocks.ipynb` | 9 KB | Unión — pasos U2 y U9 (gráficos de shocks) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/05_evaluation/exploracion_resultados/shocks_noticias.png` | 476 KB | Unión — pasos U2 y U9 (gráficos de shocks) | Como referencia | Ambos |
| Rehacer en la unión | `pipeline_productivo/05_evaluation/exploracion_resultados/shocks_por_mes.png` | 56 KB | Unión — pasos U2 y U9 (gráficos de shocks) | Como referencia | Ambos |

## H. Plan y documentación

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| No pasó | `00_documentacion/InformeFinal-GaunaPasinato.pdf` | 4.0 MB | — | Como referencia (tesis de ejemplo de otros autores) | Ambos |
| No pasó | `00_documentacion/MEMORIA.md` | 23 KB | — | No (desactualizada) | Ambos |
| No pasó | `00_documentacion/TesinaIdeasyConceptos.txt` | 9 KB | — | Como referencia | Ambos |
| No pasó | `pipeline_productivo/01_business_understanding/PlandeTesis-GaunaPasinato (1).pdf` | 453 KB | — | Como referencia (tesis de ejemplo de otros autores) | Ambos |
| No pasó | `pipeline_productivo/01_business_understanding/diccionario_variables.docx` | 13 KB | — | Sí (rehacer con las variables de la unión) | Ambos |
| No pasó | `pipeline_productivo/01_business_understanding/notas.txt` | 1 KB | — | Como referencia (ideas iniciales) | Ambos |
| No pasó | `pipeline_productivo/01_business_understanding/plan_de_trabajo_v2.pdf` | 388 KB | — | Sí (objetivos de la tesis; corregir apellido "Didi") | Ambos |
| No pasó | `pipeline_productivo/01_business_understanding/resumen_metodologico.docx` | 13 KB | — | Revisar (dice "etiquetado manual": fue Gemma) | Ambos |
| No pasó | `pipeline_productivo/01_business_understanding/~$an_de_trabajo_v2.docx` | 0 KB | — | No (archivo de bloqueo de Word) | Ambos |
| Reemplazado en 3.0 | `00_documentacion/Documentacion_Detallada_Lado_Bursatil.docx` | 17 KB | Lado Bursatil/ (un PDF por carpeta) | No | Nicolás |
| Reemplazado en 3.0 | `00_documentacion/Documentacion_Detallada_Lado_Bursatil.pdf` | 177 KB | Lado Bursatil/ (un PDF por carpeta) | No | Nicolás |
| Reemplazado en 3.0 | `00_documentacion/MAPA_PIPELINE.md` | 21 KB | Lado Bursatil/00_mapa_lado_bursatil/ + Unión/00_pipeline_union/ | No | Ambos |
| Reemplazado en 3.0 | `00_documentacion/Mapa_Pipeline_Tesina.docx` | 14 KB | Lado Bursatil/00_mapa_lado_bursatil/ + Unión/00_pipeline_union/ | No | Ambos |

## I. Presentación de avance e infografías

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| No pasó | `00_infografias/01_business_understanding.png` | 168 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/01_business_understanding.svg` | 102 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/02_data_understanding.png` | 183 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/02_data_understanding.svg` | 102 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/03_data_preparation.png` | 208 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/03_data_preparation.svg` | 122 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/04_modeling.png` | 216 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/04_modeling.svg` | 128 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/05_evaluation.png` | 161 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/05_evaluation.svg` | 92 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/06_deployment.png` | 113 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/06_deployment.svg` | 74 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/07_analisis_complementarios.png` | 193 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/07_analisis_complementarios.svg` | 110 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/Infografias_Pipeline_Tesina.pdf` | 2.7 MB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R00_portada.png` | 65 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R00_portada.svg` | 29 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R01_hmm_regimen.png` | 251 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R01_hmm_regimen.svg` | 236 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R02_finbert_confusion.png` | 188 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R02_finbert_confusion.svg` | 158 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R03_shocks.png` | 293 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R03_shocks.svg` | 285 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R04_irf_general.png` | 261 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R04_irf_general.svg` | 238 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R05_granger_empresa.png` | 176 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R05_granger_empresa.svg` | 136 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R06_event_study.png` | 218 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R06_event_study.svg` | 190 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R07_hmm_sectores.png` | 291 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R07_hmm_sectores.svg` | 276 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R08_ranking_volatilidad.png` | 190 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/R08_ranking_volatilidad.svg` | 171 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/build_infografias.py` | 14 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `00_infografias/build_resultados.py` | 10 KB | — | Rehacer con resultados nuevos (R05 cuenta mal las empresas) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Guion_Presentacion_Avance.docx` | 27 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Guion_Presentacion_Avance.pdf` | 236 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Mapa_Lado_Bursatil.html` | 28 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Mapa_Lado_Bursatil.pdf` | 331 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Presentacion_Avance_Resumida.pdf` | 1.0 MB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Presentacion_Avance_Resumida.pptx` | 1.1 MB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Presentacion_Avance_Tesina.pdf` | 347 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Presentacion_Avance_Tesina.pptx` | 620 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Punteo_Proyecto.docx` | 16 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/Punteo_Proyecto.pdf` | 173 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/build_deck.js` | 54 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/build_deck_corto.js` | 21 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/build_guion.js` | 44 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/build_punteo.js` | 20 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/diagrama_flujo_datos.html` | 795 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/figuras/hmm_recortado.png` | 149 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/figuras/shocks_recortado.png` | 439 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |
| No pasó | `pipeline_productivo/06_deployment/presentacion_avance/mapa_archivos.html` | 46 KB | — | Para la presentación final (rehacer con resultados nuevos) | Ambos |

## J. Estructura vieja (README)

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| Reemplazado en 3.0 | `00_infografias/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `README.md` | 3 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/README.md` | 3 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/baseline_beto_sin_finetuning/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/clustering_acciones/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/finetuning_evaluacion/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/hmm_sectores_acciones/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/ner_entidades/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `analisis_complementarios/volatilidad_ranking/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/01_business_understanding/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/bursatil/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/02_data_understanding/noticias/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/03_data_preparation/construccion_dataset/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/03_data_preparation/sentimiento/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/hmm_regimen_mercado/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/sentimiento_finbert/README.md` | 2 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/04_modeling/var_econometria/README.md` | 3 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/05_evaluation/exploracion_resultados/README.md` | 1 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/06_deployment/README.md` | 0 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/06_deployment/presentacion_avance/README.md` | 3 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |
| Reemplazado en 3.0 | `pipeline_productivo/README.md` | 3 KB | Cada carpeta 3.0 tiene su propio README o PDF | No | Ambos |

## K. Bibliografía general

| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |
|---|---|---:|---|---|---|
| No pasó | `00_bibliografia/Clasificación temporal del dengue en Argentina_ informe analítico.pdf` | 684 KB | — | Revisar (tema dengue: ¿antecedente metodológico?) | Ambos |
| No pasó | `00_bibliografia/FinBERT Financial Sentiment Analysis.pdf` | 868 KB | — | Sí (papers de noticias y bolsa para la unión) | Ambos |
| No pasó | `00_bibliografia/Journalists and the Stock Market -- Dougal, Casey (author);Engelberg, Joseph (author);García, -- Review of Financial Studies, #3, 25, pages 639-679, -- doi 10_1093_rfs_hhr133 -- dcf03f7d14c2d6605d241edd9971becc -- Anna’s.pdf` | 363 KB | — | Sí (papers de noticias y bolsa para la unión) | Ambos |
| No pasó | `00_bibliografia/Media Coverage and the Cross-section of Stock Returns -- LILY FANG; JOEL PERESS -- The Journal of Finance, #5, 64, pages 2023-2052, 2009 sep 28 -- doi 10_1111_j_1540-6261_2009_014.pdf` | 179 KB | — | Sí (papers de noticias y bolsa para la unión) | Ambos |
| No pasó | `00_bibliografia/Procesamiento del Lenguaje Natural en las Finanzas con FinBERT _ by Wiston Adrián Risso Charquero _ Medium.pdf` | 791 KB | — | Revisar (artículo de Medium, no académico) | Ambos |
| No pasó | `00_bibliografia/Spillover between investor sentiment and volatility The role of.pdf` | 2.0 MB | — | Sí (papers de noticias y bolsa para la unión) | Ambos |
| No pasó | `00_bibliografia/Tendencias sociales y variables bursátiles_ ¿Paralelos con la propagación del dengue_.pdf` | 52 KB | — | Revisar (tema dengue: ¿antecedente metodológico?) | Ambos |
| No pasó | `00_bibliografia/The Causal Impact of Media in Financial Markets_ -- JOSEPH E_ ENGELBERG;CHRISTOPHER A_ PARSONS(Engelberg and -- The Journal of Finance, #1, 66, pages -- doi 10_1111_j_1540-6261_2010_01626_x -- 8ba113a2c9f14652d33a527b823.pdf` | 199 KB | — | Sí (papers de noticias y bolsa para la unión) | Ambos |
| No pasó | `00_bibliografia/conversacion chat gpt.pdf` | 503 KB | — | No (no es una fuente citable) | Ambos |
