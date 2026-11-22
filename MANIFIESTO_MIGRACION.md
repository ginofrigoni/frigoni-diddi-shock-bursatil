# Manifiesto de migración 5.0 → 6.0

Estado: **borrador para aprobar**. Todavía no se copió nada. Origen: `tesis version 5.0`, que se usa solo para leer.

Total: **89 archivos, 1 GB**.

En la columna "Qué se hace": *tal cual* = se copia sin cambios; *adaptar* = se copia y se modifica; *documentación* = se copia para mostrar cómo se hizo, pero no se vuelve a correr.

## 2_comprension_de_los_datos

| # | Destino en la 6.0 | Origen en la 5.0 | Qué se hace | Tamaño |
|---|---|---|---|---|
| 1 | `2_comprension_de_los_datos/noticias/datos/ambito_economia.jsonl` | `Lado Noticias/noticias/resultados/ambito_economia.jsonl` | tal cual | 2 MB |
| 2 | `2_comprension_de_los_datos/noticias/datos/ambito_finanzas.jsonl` | `Lado Noticias/noticias/resultados/ambito_finanzas.jsonl` | tal cual | 870 KB |
| 3 | `2_comprension_de_los_datos/noticias/datos/clarin_economia.jsonl` | `Lado Noticias/noticias/resultados/clarin_economia.jsonl` | tal cual | 1 MB |
| 4 | `2_comprension_de_los_datos/noticias/datos/clarin_sitemap.jsonl` | `Lado Noticias/noticias/resultados/clarin_sitemap.jsonl` | tal cual | 16 MB |
| 5 | `2_comprension_de_los_datos/noticias/datos/eleconomista_sitemap.jsonl` | `Lado Noticias/noticias/resultados/eleconomista_sitemap.jsonl` | tal cual | 13 MB |
| 6 | `2_comprension_de_los_datos/noticias/datos/infobae_economia.jsonl` | `Lado Noticias/noticias/resultados/infobae_economia.jsonl` | tal cual | 3 MB |
| 7 | `2_comprension_de_los_datos/noticias/datos/iprofesional_sitemap.jsonl` | `Lado Noticias/noticias/resultados/iprofesional_sitemap.jsonl` | tal cual | 33 MB |
| 8 | `2_comprension_de_los_datos/noticias/datos/lanacion_economia.jsonl` | `Lado Noticias/noticias/resultados/lanacion_economia.jsonl` | tal cual | 3 MB |
| 9 | `2_comprension_de_los_datos/noticias/datos/tn_economia.jsonl` | `Lado Noticias/noticias/resultados/tn_economia.jsonl` | tal cual | 660 KB |
| 10 | `2_comprension_de_los_datos/noticias/datos/reporte_dedup_semantico.json` | `Lado Noticias/noticias/analisis_duplicados/reporte_dedup_semantico.json` | tal cual (lo usa la regla de las 17:00) | 35 KB |
| 11 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/noticias_historico_v3.py` | `Lado Noticias/noticias/scripts/noticias_historico_v3.py` | documentación (no se corre) | 26 KB |
| 12 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/noticias_sitemap.py` | `Lado Noticias/noticias/scripts/noticias_sitemap.py` | documentación (no se corre) | 22 KB |
| 13 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/noticias_diario.py` | `Lado Noticias/noticias/scripts/noticias_diario.py` | documentación (no se corre) | 23 KB |
| 14 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/recuperar_metadatos.py` | `Lado Noticias/noticias/scripts/recuperar_metadatos.py` | documentación (no se corre) | 4 KB |
| 15 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/depurar_corpus.py` | `Lado Noticias/noticias/scripts/depurar_corpus.py` | documentación (no se corre) | 5 KB |
| 16 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/depurar_plantillas.py` | `Lado Noticias/noticias/scripts/depurar_plantillas.py` | documentación (no se corre) | 5 KB |
| 17 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/dedup_semantico_qwen.py` | `Lado Noticias/noticias/scripts/dedup_semantico_qwen.py` | documentación (no se corre) | 14 KB |
| 18 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/dedup_utils.py` | `Lado Noticias/noticias/scripts/dedup_utils.py` | documentación (no se corre) | 6 KB |
| 19 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/calidad_utils.py` | `Lado Noticias/noticias/scripts/calidad_utils.py` | documentación (no se corre) | 6 KB |
| 20 | `2_comprension_de_los_datos/noticias/scripts_recoleccion/env_utils.py` | `Lado Noticias/noticias/scripts/env_utils.py` | documentación (no se corre) | 2 KB |
| 21 | `2_comprension_de_los_datos/noticias/.env.example` | `Lado Noticias/noticias/.env.example` | tal cual (plantilla sin claves) | 175 B |
| 22 | `2_comprension_de_los_datos/noticias/documentacion/AUDITORIA_CORPUS.md` | `Lado Noticias/noticias/AUDITORIA_CORPUS.md` | documentación | 16 KB |
| 23 | `2_comprension_de_los_datos/noticias/documentacion/DEPURACION_CALIDAD.md` | `Lado Noticias/noticias/DEPURACION_CALIDAD.md` | documentación | 12 KB |
| 24 | `2_comprension_de_los_datos/noticias/documentacion/RESOLUCION_DUPLICADOS.md` | `Lado Noticias/noticias/RESOLUCION_DUPLICADOS.md` | documentación | 6 KB |
| 25 | `2_comprension_de_los_datos/mercado/datos/precios_diarios_47_acciones.csv` | `Lado Bursatil/01_scraping_acciones/precios_diarios_47_acciones.csv` | tal cual | 4 MB |
| 26 | `2_comprension_de_los_datos/mercado/datos/panel_acciones_final.csv` | `Lado Bursatil/01_scraping_acciones/panel_acciones_final.csv` | tal cual | 4 KB |
| 27 | `2_comprension_de_los_datos/mercado/datos/cobertura_53_candidatas.csv` | `Lado Bursatil/01_scraping_acciones/cobertura_53_candidatas.csv` | tal cual | 5 KB |
| 28 | `2_comprension_de_los_datos/mercado/datos/descartadas_por_cobertura.csv` | `Lado Bursatil/01_scraping_acciones/descartadas_por_cobertura.csv` | tal cual | 581 B |
| 29 | `2_comprension_de_los_datos/mercado/scraping_acciones.py` | `Lado Bursatil/01_scraping_acciones/scraping_acciones.py` | documentación (no se corre) | 19 KB |

## 3_preparacion_de_los_datos

| # | Destino en la 6.0 | Origen en la 5.0 | Qué se hace | Tamaño |
|---|---|---|---|---|
| 1 | `3_preparacion_de_los_datos/regla_17/alinear_noticias_ruedas.py` | `Unión/01_alineacion_noticias_ruedas/alinear_noticias_ruedas.py` | adaptar rutas; quitar el control contra 00_pipeline_union | 13 KB |
| 2 | `3_preparacion_de_los_datos/sentimiento_finbeto/etiquetado_gemma/checkpoint.jsonl` | `Lado Noticias/sentimiento_finbert/dataset_etiquetado/checkpoint.jsonl` | tal cual | 14 MB |
| 3 | `3_preparacion_de_los_datos/sentimiento_finbeto/etiquetado_gemma/checkpoint_limpio.jsonl` | `Lado Noticias/sentimiento_finbert/dataset_etiquetado/checkpoint_limpio.jsonl` | tal cual | 15 MB |
| 4 | `3_preparacion_de_los_datos/sentimiento_finbeto/etiquetado_gemma/limpieza_reporte.json` | `Lado Noticias/sentimiento_finbert/dataset_etiquetado/limpieza_reporte.json` | tal cual | 1 KB |
| 5 | `3_preparacion_de_los_datos/sentimiento_finbeto/etiquetado_gemma/limpieza_filas_eliminadas.csv` | `Lado Noticias/sentimiento_finbert/dataset_etiquetado/limpieza_filas_eliminadas.csv` | tal cual | 335 KB |
| 6 | `3_preparacion_de_los_datos/sentimiento_finbeto/etiquetado_gemma/indice_procesados.json` | `Lado Noticias/sentimiento_finbert/dataset_etiquetado/indice_procesados.json` | tal cual | 50 KB |
| 7 | `3_preparacion_de_los_datos/sentimiento_finbeto/etiquetado_gemma/etiquetado_gemma.ipynb` | `Lado Noticias/sentimiento_finbert/etiquetado_gemma.ipynb` | documentación (no se corre) | 472 KB |
| 8 | `3_preparacion_de_los_datos/sentimiento_finbeto/limpiar_etiquetado.py` | `Lado Noticias/sentimiento_finbert/limpiar_etiquetado.py` | tal cual | 6 KB |
| 9 | `3_preparacion_de_los_datos/sentimiento_finbeto/preparar_dataset_v2.py` | `Lado Noticias/sentimiento_finbert/preparar_dataset_v2.py` | adaptar: MIXTO → NEU y balanceo con 3 clases | 5 KB |
| 10 | `3_preparacion_de_los_datos/sentimiento_finbeto/fase3_reentrenar_para_medir.py` | `Lado Noticias/sentimiento_finbert/fase3_reentrenar_para_medir.py` | adaptar: 3 clases y guardar el modelo final | 8 KB |
| 11 | `3_preparacion_de_los_datos/sentimiento_finbeto/comparar_baseline.py` | `Lado Noticias/sentimiento_finbert/comparar_baseline.py` | adaptar: 3 contra 3 | 5 KB |
| 12 | `3_preparacion_de_los_datos/sentimiento_finbeto/serie_completa_finetuned.py` | `Lado Noticias/sentimiento_finbert/serie_completa_finetuned.py` | adaptar rutas y clases | 26 KB |
| 13 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/config.json` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/config.json` | tal cual | 734 B |
| 14 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/generation_config.json` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/generation_config.json` | tal cual | 95 B |
| 15 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/model.safetensors` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/model.safetensors` | tal cual; **no va a GitHub** (> 100 MB) | 419 MB |
| 16 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/special_tokens_map.json` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/special_tokens_map.json` | tal cual | 732 B |
| 17 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/tokenizer.json` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/tokenizer.json` | tal cual | 713 KB |
| 18 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/tokenizer_config.json` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/tokenizer_config.json` | tal cual | 1 KB |
| 19 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/vocab.txt` | `Lado Noticias/sentimiento_finbert/beto_further_pretrained/vocab.txt` | tal cual | 236 KB |
| 20 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/README.md` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/README.md` | tal cual | 2 KB |
| 21 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/added_tokens.json` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/added_tokens.json` | tal cual | 67 B |
| 22 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/config.json` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/config.json` | tal cual | 841 B |
| 23 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/pytorch_model.bin` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/pytorch_model.bin` | tal cual; **no va a GitHub** (> 100 MB) | 419 MB |
| 24 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/special_tokens_map.json` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/special_tokens_map.json` | tal cual | 112 B |
| 25 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/tokenizer.json` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/tokenizer.json` | tal cual | 469 KB |
| 26 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/tokenizer_config.json` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/tokenizer_config.json` | tal cual | 528 B |
| 27 | `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/baseline_finiteautomata/vocab.txt` | `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/vocab.txt` | tal cual | 236 KB |
| 28 | `3_preparacion_de_los_datos/sentimiento_por_rueda/sentimiento_por_rueda.py` | `Unión/02_sentimiento_por_rueda/sentimiento_por_rueda.py` | adaptar: solo sentimiento inesperado (sin atención ni shocks) y renombres | 18 KB |
| 29 | `3_preparacion_de_los_datos/sentimiento_por_empresa/datos/ner_oraciones.csv` | `Lado Noticias/ner_entidades/resultados_ner/ner_oraciones.csv` | tal cual (entrada del cruce); **no va a GitHub** (> 100 MB) | 221 MB |
| 30 | `3_preparacion_de_los_datos/sentimiento_por_empresa/ner_analisis.ipynb` | `Lado Noticias/ner_entidades/ner_analisis.ipynb` | documentación (cómo se generó ner_oraciones.csv) | 935 KB |
| 31 | `3_preparacion_de_los_datos/sentimiento_por_empresa/cruce_ner_sentimiento.py` | `Lado Noticias/ner_entidades/cruce_ner_sentimiento.py` | adaptar: 3 clases | 7 KB |
| 32 | `3_preparacion_de_los_datos/sentimiento_por_empresa/equivalencias_indicadores.py` | `Lado Noticias/ner_entidades/equivalencias_indicadores.py` | tal cual (lo importa el cruce) | 3 KB |
| 33 | `3_preparacion_de_los_datos/sentimiento_por_empresa/sentimiento_por_empresa.py` | `Unión/03_sentimiento_por_empresa/sentimiento_por_empresa.py` | adaptar rutas y renombres | 14 KB |
| 34 | `3_preparacion_de_los_datos/sentimiento_por_empresa/datos/cobertura_por_ticker.csv` | `Unión/00_pipeline_union/cobertura_por_ticker.csv` | tal cual (lo lee el script) | 3 KB |
| 35 | `3_preparacion_de_los_datos/vix_argentino/calcular_vix_arg.py` | `Lado Bursatil/03_vix_argentino/calcular_vix_arg.py` | documentación (no se vuelve a correr) | 6 KB |
| 36 | `3_preparacion_de_los_datos/vix_argentino/salidas/vix_arg.csv` | `Lado Bursatil/03_vix_argentino/vix_arg.csv` | tal cual | 19 KB |
| 37 | `3_preparacion_de_los_datos/regimen_hmm/hmm_regimen_mercado.py` | `Lado Bursatil/06_hmm_regimen_mercado/hmm_regimen_mercado.py` | documentación (no se reentrena) | 13 KB |
| 38 | `3_preparacion_de_los_datos/regimen_hmm/salidas/hmm_regimen_mercado.csv` | `Lado Bursatil/06_hmm_regimen_mercado/hmm_regimen_mercado.csv` | tal cual | 33 KB |
| 39 | `3_preparacion_de_los_datos/regimen_hmm/salidas/bic_por_k.csv` | `Lado Bursatil/06_hmm_regimen_mercado/bic_por_k.csv` | tal cual | 421 B |
| 40 | `3_preparacion_de_los_datos/regimen_hmm/salidas/matriz_transicion.csv` | `Lado Bursatil/06_hmm_regimen_mercado/matriz_transicion.csv` | tal cual | 86 B |
| 41 | `3_preparacion_de_los_datos/dataset_unificado/construir_datasets.py` | `Unión/04_dataset_unificado/construir_datasets.py` | adaptar: 17 empresas, renombres, sin clustering ni atención | 22 KB |

## 5_evaluacion

| # | Destino en la 6.0 | Origen en la 5.0 | Qué se hace | Tamaño |
|---|---|---|---|---|
| 1 | `5_evaluacion/anexo/var_granger.py` | `Unión/06_var_granger/var_granger.py` | adaptar a las columnas nuevas | 19 KB |

## 6_despliegue

| # | Destino en la 6.0 | Origen en la 5.0 | Qué se hace | Tamaño |
|---|---|---|---|---|
| 1 | `6_despliegue/informe/Informe_Final_NicolasDiddi-GinoFrigoni.tex` | `Informe Final/Informe_Final_NicolasDiddi-GinoFrigoni.tex` | tal cual (base) | 13 KB |
| 2 | `6_despliegue/informe/bibliografia.tex` | `Informe Final/bibliografia.tex` | tal cual (base) | 23 KB |
| 3 | `6_despliegue/informe/logo_ugr.png` | `Informe Final/logo_ugr.png` | tal cual (base) | 21 KB |
| 4 | `6_despliegue/informe/compilar_tesina.py` | `Informe Final/compilar_tesina.py` | tal cual (base) | 4 KB |
| 5 | `6_despliegue/informe/figuras.py` | `Informe Final/figuras.py` | tal cual (base) | 9 KB |
| 6 | `6_despliegue/informe/capitulos/01_introduccion.tex` | `Informe Final/capitulos/01_introduccion.tex` | base para reescribir | 9 KB |
| 7 | `6_despliegue/informe/capitulos/02_marco_teorico.tex` | `Informe Final/capitulos/02_marco_teorico.tex` | base para reescribir | 4 KB |
| 8 | `6_despliegue/informe/capitulos/03_corpus.tex` | `Informe Final/capitulos/03_corpus.tex` | base para reescribir | 10 KB |
| 9 | `6_despliegue/informe/capitulos/04_finbeto.tex` | `Informe Final/capitulos/04_finbeto.tex` | base para reescribir | 14 KB |
| 10 | `6_despliegue/informe/capitulos/05_vix.tex` | `Informe Final/capitulos/05_vix.tex` | base para reescribir | 11 KB |
| 11 | `6_despliegue/informe/capitulos/06_hmm.tex` | `Informe Final/capitulos/06_hmm.tex` | base para reescribir | 7 KB |
| 12 | `6_despliegue/informe/capitulos/07_var_granger.tex` | `Informe Final/capitulos/07_var_granger.tex` | base para reescribir | 20 KB |
| 13 | `6_despliegue/informe/capitulos/08_conclusiones.tex` | `Informe Final/capitulos/08_conclusiones.tex` | base para reescribir | 5 KB |
| 14 | `6_despliegue/informe/capitulos/09_anexo.tex` | `Informe Final/capitulos/09_anexo.tex` | base para reescribir | 4 KB |
| 15 | `6_despliegue/presentacion/SIMULACION_PRESENTACION.md` | `Informe Final/SIMULACION_PRESENTACION.md` | base para actualizar | 17 KB |

## (raíz)

| # | Destino en la 6.0 | Origen en la 5.0 | Qué se hace | Tamaño |
|---|---|---|---|---|
| 1 | `(raíz)/correr_todo.py` | `Unión/09_entrega_final/correr_todo.py` | reescribir con el orden nuevo | 3 KB |
| 2 | `(raíz)/requirements.txt` | `Lado Noticias/requirements.txt` | revisar y sumar scikit-learn | 1 KB |
| 3 | `(raíz)/.gitignore` | `.gitignore` | adaptar rutas | 718 B |

## No entra (queda en la 5.0)

| Qué | Por qué |
|---|---|
| `Lado Noticias/noticias/.env` | Tiene claves. **Nunca se copia.** |
| Corpus en `.json` (9 archivos) | Es el mismo corpus que los `.jsonl`, en otro formato. |
| `_backup_pre_unescape/`, `analisis_calidad/`, el resto de `analisis_duplicados/` | Pasos intermedios ya resueltos. |
| `sentimiento_finbert/dataset/` (división por oración) | La 6.0 usa solo la división por noticia. |
| `dataset_v2/`, `resultados_fase3/`, `beto_oraciones_finetuned.csv*`, `finetuned_*.csv`, `checkpoint_finetuned.jsonl` | Se regeneran con FinBETO de 3 clases. Para comparar con la 5.0, se leen de ahí. |
| `ner_articulos.csv`, `ner_resumen.csv`, `ner_sentimiento*.csv` | Los dos primeros no los usa el pipeline; los otros se regeneran. |
| `Lado Bursatil/00`, `02`, `04`, `05`, `99` | Quedan afuera (D3). |
| `Unión/00` (salvo `cobertura_por_ticker.csv`), `05`, `06b`, `07`, `07b`, `08`, `99` | Quedan afuera (D3). |
| Salidas de `Unión/01` a `04` y `06` | Se regeneran. |
| `Documentacion_*.pdf/.docx` de cada paso y carpetas `papers/` | Pendiente: entran solo los papers citados en `bibliografia.tex`. |
| `Informe Final/_tools`, `mapeo_referencias*`, el PDF y las figuras de la 5.0 | Herramientas y salidas de la 5.0. |
| Presentación de Maricel | Es de otra persona; queda como referencia en la 5.0. |

## A tener en cuenta

- **El modelo FinBETO final no está guardado en la 5.0**: la carpeta `beto_finetuned/` no existe. Como se reentrena igual, no es un problema, pero el entrenamiento nuevo tiene que guardarlo.
- **`construir_datasets.py` lee el clustering** (`comparacion_grupo_no_degenerado.csv`). Como el clustering queda afuera, hay que sacar esa columna.
- **El balanceo de clases** de `preparar_dataset_v2.py` limita NEU a 1.920 oraciones de entrenamiento. Con MIXTO → NEU hay que decidir si se mantiene ese tope.
- **El cruce NER se hace por oración.** Hay que verificar que la clasificación nueva divide las oraciones igual que `ner_oraciones.csv`.

## Agregado después de aprobar el manifiesto (22/11/2026)

| # | Destino en la 6.0 | Origen en la 5.0 | Qué se hace | Tamaño |
|---|---|---|---|---|
| 1 | `3_preparacion_de_los_datos/sentimiento_finbeto/datos/oraciones_corpus.csv` | `Lado Noticias/sentimiento_finbert/beto_oraciones_finetuned.csv` | se copian las columnas fuente, url, fecha, autor, titulo, or_idx y oracion, **sin la etiqueta vieja**: mismas oraciones que usa el NER; **no va a GitHub** (> 100 MB) | ver registro |
| 2 | ~~`3_preparacion_de_los_datos/sentimiento_finbeto/serie_completa_finetuned.py`~~ | — | **se sacó**: lo reemplaza `sentimiento_por_nota.py`, que hace el mismo cálculo (reproduce la 5.0 exacto) sin la parte de inferencia vieja | — |
| 3 | `6_despliegue/informe/papers/` (35 PDF) | los papers citados en `bibliografia.tex`, de `Unión/10_papers_union`, `Unión/11_papers_lado_noticias` y `Lado Bursatil/*/papers` | tal cual (verificados con MD5); solo los que cita el informe | 36.5 MB |
