# sentimiento_finbert

Serie diaria de sentimiento del corpus de noticias, generada con el modelo FinBETO (BETO con pre-entrenamiento continuado sobre el corpus y ajuste fino con etiquetas de Gemma). Calidad estimada sobre noticias no vistas al entrenar: **F1 macro 0,685 en 4 clases** y **0,724 en 3 clases (POS/NEG/NEU), frente a 0,546 del modelo de referencia** `finiteautomata/beto-sentiment-analysis` en el mismo test. La evaluación original de la 2.0 (0,7296 contra 0,6201) usaba una división por oración en la que el test compartía noticias con el entrenamiento; ver la sección Fase 3.

Esta carpeta **no es todavía el proyecto de modelado completo**. Contiene la serie diaria y lo necesario para que refleje el corpus curado de `../noticias/`, y el **etiquetado** con el que se construyó el conjunto de entrenamiento (ver más abajo). Tiene además el modelo de partida del ajuste fino (`beto_further_pretrained/`) y la Fase 3 de medición. Faltan los cuadernos de entrenamiento y evaluación originales (`01_further_pretraining`, `03_finetuning`, `04`–`06`) y los pesos del modelo que usa el pipeline (`beto_finetuned/`, ~420 MB); para volver a correr inferencia desde cero hay que usarlos desde `tesis version 2.0/`.

## Contenido

| Archivo | Qué es |
|---|---|
| `SECCION_TESIS.md` | Borrador en prosa de tesis de todo el análisis de sentimiento: etiquetado, entrenamiento, evaluación original y corregida, comparación con el modelo de referencia, serie diaria y limitaciones. |
| `PLAN_MEJORA_ENTRENAMIENTO.md` | Pasos a seguir para mejorar el entrenamiento (validación humana, reentrenamiento, reetiquetado, MIXTO, relleno), con criterios de decisión y orden recomendado. |
| `serie_completa_finetuned.py` | Arma el sentimiento por artículo y la serie diaria con detección de shocks (±1,5σ sobre media móvil de 7 días, mínimo 5 artículos/día). **Modo vigente: `--desde-oraciones`**, que arma el sentimiento de cada artículo desde `beto_oraciones_finetuned.csv` (título + cuerpo) sin las oraciones de relleno y sin usar el modelo. Los otros modos (inferencia completa y `--solo-serie`, desde el checkpoint) se conservan. |
| `checkpoint_finetuned.jsonl` | Resultado de la corrida original por artículo, que clasificó **solo el cuerpo** de cada nota (14.012 filas, una por URL). Desde el 2026-10-18 **ya no alimenta la serie**; se conserva como registro. |
| `finetuned_articulos.csv` | Una fila por artículo con las métricas agregadas. |
| `finetuned_serie_diaria.csv` | Serie diaria (487 días, 377 con datos, **36 shocks: 17 positivos y 19 negativos**), generada con `--desde-oraciones`. |
| `etiquetado_gemma.ipynb` | Etiquetado de oraciones con Gemma (Ollama), en dos pasos: análisis de contexto del artículo y etiqueta por oración (POS/NEG/NEU/MIXTO). Contiene los prompts y los parámetros. |
| `dataset_etiquetado/checkpoint.jsonl` | Las etiquetas: 11.605 filas de 408 artículos (~45 por fuente), con oración, etiqueta, confianza declarada, razón y contexto. |
| `dataset_etiquetado/indice_procesados.json` | Artículos ya procesados (lo usa el cuaderno para no repetir). |
| `02_preparar_dataset.ipynb` | Balanceo (hasta 2.400 por clase, todas las MIXTO) y división estratificada 80/10/10, más los pesos por clase. |
| `dataset/` | `train.csv` (6.588), `val.csv` (824), `test.csv` (824) y `class_weights.pt`: las divisiones con las que se entrenó y evaluó el modelo (F1 0,7296 sobre `test.csv`). |
| `limpiar_etiquetado.py` | Fase 1 de la corrección: limpia `checkpoint.jsonl` (relleno, oraciones etiquetadas dos veces, textos repetidos) y genera `dataset_etiquetado/checkpoint_limpio.jsonl`, `limpieza_filas_eliminadas.csv` y `limpieza_reporte.json`. |
| `preparar_dataset_v2.py` | Fase 2: nueva división train/val/test **por noticia** a partir del conjunto limpio. Genera `dataset_v2/` (no reemplaza a `dataset/`). |
| `fase3_reentrenar_para_medir.py` | Fase 3: reentrena FinBETO con la configuración original sobre `dataset/` y `dataset_v2/` (3 semillas cada uno) solo para medir. No guarda modelos. Resultados en `resultados_fase3/`. |
| `beto_further_pretrained/` | Modelo de partida del ajuste fino (BETO con pre-entrenamiento continuado sobre el corpus, 420 MB). Copiado sin cambios de `tesis version 2.0/pipeline_productivo/04_modeling/sentimiento_finbert/` el 2026-10-18 (7 archivos, hashes iguales; `model.safetensors` sha256 `b4ff46aa…`). Lo usa la Fase 3. |
| `comparar_baseline.py` | Compara FinBETO con el modelo de referencia en la misma tarea (3 clases, sin MIXTO) y el mismo test, en las dos divisiones. Resultados en `resultados_fase3/comparacion_baseline.*`. |
| `baseline_finiteautomata/` | Modelo de referencia `finiteautomata/beto-sentiment-analysis` (BETO ajustado con ~5.000 tuits del corpus TASS 2020; 3 clases), descargado de Hugging Face el 2026-10-18, revisión `9384c7f3…` (`pytorch_model.bin`, 440 MB, sha256 `6301fc83…`). Su ficha avisa que será retirado y recomienda `pysentimiento/robertuito-sentiment-analysis`. |
| `beto_oraciones_finetuned.csv` | Sentimiento FinBETO por oración (408.939 oraciones). Copiado sin cambios de `tesis version 2.0/analisis_complementarios/finetuning_evaluacion/` (sha256 `f4b9c10f…`). Lo usa `../ner_entidades/cruce_ner_sentimiento.py`. Corresponde al corpus previo a la depuración: incluye oraciones de artículos ya eliminados, que el cruce ignora. |

## Etiquetado (conjunto de entrenamiento)

**Procedencia.** Copiados sin cambios el 2026-10-18, verificados por sha256:

| En 4.0 | Origen | sha256 |
|---|---|---|
| `etiquetado_gemma.ipynb` | `tesis version 2.0/pipeline_productivo/03_data_preparation/sentimiento/` | `3a916c38…` (antes del ajuste de ruta) |
| `02_preparar_dataset.ipynb` | ídem | `739eca61…` |
| `dataset_etiquetado/checkpoint.jsonl` | ídem, `dataset_etiquetado/` | `37ecd7fa…` |
| `dataset_etiquetado/indice_procesados.json` | ídem | `ae3771c0…` |
| `dataset/train.csv`, `val.csv`, `test.csv`, `class_weights.pt` | `lado_noticias/finetune_beto/dataset/` (no estaban en la 2.0) | `27acfa12…`, `4d56bd09…`, `82b38c51…`, `94af986b…` |

**Único cambio:** en `etiquetado_gemma.ipynb` (celda de rutas) `BASE_DIR` pasó de `../../02_data_understanding/noticias/resultados` a `../noticias/resultados`. Las rutas de `02_preparar_dataset.ipynb` ya eran relativas a esta carpeta.

**Se conservan como documentación, no para volver a correr.** El etiquetado tarda horas con Gemma, y sobre el corpus actual (depurado) elegiría otros artículos. `02_preparar_dataset.ipynb` necesita scikit-learn y torch, que no están en `../.venv`. La última celda de `etiquetado_gemma.ipynb` exporta una versión antigua de las divisiones dentro de `dataset_etiquetado/`; las que se usaron para entrenar son las de `dataset/`, generadas por `02_preparar_dataset.ipynb`.

**Lo que se encontró al revisarlos** (para analizar aparte; según ese análisis se decidirá si corregir):

- **Oraciones etiquetadas dos veces:** 318 oraciones (de 18 artículos procesados de nuevo) aparecen dos o tres veces en `checkpoint.jsonl`. Gemma les dio la misma etiqueta en el 89% de los casos.
- **Solapamiento entre entrenamiento y prueba:** 41 de las 824 oraciones de `test.csv` (5%) están textualmente también en `train.csv`. Eso infla el F1 de prueba en una magnitud no medida.
- **Artículos eliminados del corpus:** 8 de los 408 artículos etiquetados (110 oraciones) se eliminaron después del corpus (5 por contenido duplicado y 3 por plantilla). El modelo ya se entrenó con ellos; no se tocaron.
- **Menores:** `indice_procesados.json` lista 405 artículos y el checkpoint tiene 408; 104 filas no tienen fecha; el cuaderno imprime "500 oraciones por clase", pero el código exige 2.500.
- **Las etiquetas son de un modelo, no de personas:** el F1 mide el acuerdo con Gemma, no con un criterio humano.

## Corrección del conjunto etiquetado (fases 1 y 2, 2026-10-18)

Responde a lo encontrado en la sección anterior. **No toca** `checkpoint.jsonl`, `dataset/` ni el modelo: genera archivos nuevos al lado. Sirve de base para medir el modelo de forma limpia (fase 3, pendiente de decisión).

**Fase 1: `limpiar_etiquetado.py`** → `dataset_etiquetado/checkpoint_limpio.jsonl`

Primero quita de cada oración las marcas que el scraping dejó pegadas: "PUBLICIDAD", "Sobre la firma", "Mirá también", "Newsletter Clarín", "Tags relacionados" y la promoción de la cobertura de Clarín. Afecta a 361 filas, casi todas de Infobae, que traen oraciones reales precedidas por "PUBLICIDAD". El texto limpio queda en `oracion_limpia` y el original en `oracion`. Después aplica cinco reglas:

| Motivo | Filas | Regla |
|---|---:|---|
| `relleno` | 73 | Tenía marcas y, al quitarlas, no queda una oración (17 textos distintos: "PUBLICIDAD PUBLICIDAD PUBLICIDAD", firmas y newsletter de Clarín). |
| `reproceso_conflicto` | 72 | La misma oración etiquetada más de una vez con etiquetas distintas: se descartan todas las copias. |
| `reproceso_mismo_label` | 281 | La misma oración etiquetada más de una vez con la misma etiqueta: queda una copia. |
| `texto_repetido_conflicto` | 36 | El mismo texto en noticias distintas con etiquetas distintas: se descartan todas las copias. |
| `texto_repetido` | 288 | El mismo texto en noticias distintas (párrafos fijos de los sitios) con la misma etiqueta: queda la primera aparición. |
| **Total eliminado** | **750** | 11.605 → **10.855** filas, de las mismas 408 noticias, sin textos repetidos. |

Las oraciones cortas sin marcas, como los ítems de listas con cifras, se conservan. Clases: NEU 5.390 → 4.861, POS 2.763 → 2.684, NEG 2.416 → 2.315, MIXTO 1.036 → 995. Cada fila eliminada y su motivo están en `limpieza_filas_eliminadas.csv`.

**Fase 2: `preparar_dataset_v2.py`** → `dataset_v2/`

Mismo criterio que `02_preparar_dataset.ipynb` (80/10/10; tope de 2.400 por clase repartido 1.920/240/240; todas las MIXTO; semilla 42), con dos diferencias: parte del conjunto limpio y **sortea noticias, no oraciones**, estratificando por fuente.

| | Noticias | Oraciones | POS | NEG | NEU | MIXTO |
|---|---:|---:|---:|---:|---:|---:|
| train | 330 | 6.528 | 1.920 | 1.892 | 1.920 | 796 |
| val | 39 | 754 | 199 | 240 | 240 | 75 |
| test | 39 | 786 | 240 | 182 | 240 | 124 |

- **Verificado:** ninguna noticia ni ningún texto se comparte entre conjuntos, y no hay textos repetidos dentro de cada uno. En `dataset/`, en cambio, el 100% del test venía de noticias vistas en el entrenamiento y 41 oraciones del test estaban también en train.
- **Costo de dividir por noticia:** las clases quedan algo menos parejas en val y test (NEG 182 en test, POS 199 en val, MIXTO entre 75 y 124), porque cada conjunto tiene solo 39 noticias. Se mantuvo la semilla 42 de la división original y no se probó otra para equilibrar, para no elegir la división según el resultado.
- Los pesos por clase quedan en `class_weights.json`, porque el venv no tiene torch. Hay que convertirlos a tensor al entrenar.
- Las columnas son las de `dataset/` (`texto`, `label`, `label_id`) más `url`, `fuente`, `or_idx` y `texto_original`, para trazabilidad.

## Fase 3: reentrenar solo para medir (2026-10-18)

`fase3_reentrenar_para_medir.py` reentrena FinBETO desde `beto_further_pretrained/` con la misma configuración de `03_finetuning.ipynb`: 5 épocas, lote 32, lr 2·10⁻⁵, 10% de calentamiento, weight decay 0,01, pérdida ponderada por clase, mejor época por F1 macro en validación y fp16. Se corre con **el mismo código** sobre las dos divisiones y con 3 semillas (42, 1, 2), para que la diferencia se deba a la división y no al azar. **No reemplaza al modelo del pipeline** ni guarda los modelos entrenados: solo las métricas (`resultados_fase3/*.json`, `resumen.csv`). Cada corrida tarda ~1,4 minutos en la RTX 3090.

| F1 en test (media ± desvío, 3 semillas) | División original `dataset/` | División por noticia `dataset_v2/` |
|---|---:|---:|
| **F1 macro** | **0,732 ± 0,012** | **0,685 ± 0,009** |
| Exactitud | 0,743 ± 0,010 | 0,691 ± 0,008 |
| F1 POS | 0,752 | 0,694 |
| F1 NEG | 0,760 | 0,677 |
| F1 NEU | 0,754 | 0,725 |
| F1 MIXTO | 0,663 | 0,645 |
| F1 macro sin las 41 oraciones del test que están en train | 0,725 ± 0,011 | — (no hay) |

Lectura:
- **El script reproduce el resultado original.** Con la división original da 0,732, frente al 0,7296 informado.
- **Las 41 oraciones repetidas explican poco:** sacarlas baja el F1 0,7 puntos (0,732 → 0,725).
- **Dividir por noticia baja el F1 unos 4,7 puntos** (0,732 → 0,685), y lo más afectado es NEG (−8 puntos). Esta es la estimación honesta de la calidad del modelo sobre noticias que no vio, que es la situación de uso real: el 97% de las noticias del corpus nunca se vio al entrenar.
- Los dos tests no son idénticos (distintas oraciones y proporciones de clase; el de `dataset_v2` no tiene relleno ni repetidos). Por eso la diferencia combina el efecto de la superposición de noticias con el de un test algo más difícil.
**Comparación con el modelo de referencia (`comparar_baseline.py`).** Se miden los dos modelos en la misma tarea: 3 clases, solo oraciones POS/NEG/NEU. Si FinBETO predice MIXTO, cuenta como error.

| F1 macro, 3 clases | Test original (720 oraciones) | Test por noticia (662 oraciones) |
|---|---:|---:|
| Referencia `finiteautomata/beto-sentiment-analysis` | 0,620 | **0,546** |
| FinBETO (media de 3 semillas) | 0,773 ± 0,009 | **0,724 ± 0,009** |
| Ventaja de FinBETO | +15,3 puntos | **+17,7 puntos** |

- **Control:** la referencia da exactamente el 0,6201 y 0,6208 de `05_evaluacion.ipynb` sobre el test original, así que se corre igual que en la 2.0.
- **Corrección de una afirmación previa:** la comparación de la 2.0 no favorecía a FinBETO por incluir MIXTO, porque ya excluía esas oraciones para la referencia. Lo que estaba desparejo es que comparaba el F1 de FinBETO en 4 clases (0,7296) con el de la referencia en 3 (0,6201). Medidos en la misma tarea, la ventaja era mayor: 15 puntos en lugar de 11.
- **El test por noticia es más difícil para cualquier modelo,** no solo para FinBETO: la referencia, que no se entrenó con estos datos y no puede beneficiarse de la superposición, también baja (0,620 → 0,546). Por eso la caída de FinBETO no puede atribuirse entera a la superposición de noticias.
- **La ventaja de FinBETO se mantiene, e incluso crece, sobre noticias no vistas:** 0,724 contra 0,546. La referencia, entrenada con tuits, sobrepredice la clase neutra (411 de 662 predicciones) y es floja en POS (F1 0,43).

Entorno: torch 2.11.0+cu128, transformers 5.20.1, accelerate 1.15.0 y scikit-learn 1.9.1, instalados en `../.venv`. El script se adapta a transformers 5.x, que renombró algunos parámetros (`eval_strategy`, `warmup_steps` como fracción, `processing_class`).

## Una sola clasificación para la serie y el cruce con el NER (2026-10-18)

Al revisar 4.0 se vio que el modelo se había corrido dos veces sobre el corpus, con criterios distintos:

| | Qué clasificó | Usado por |
|---|---|---|
| `checkpoint_finetuned.jsonl` (`serie_completa_finetuned.py`) | Solo el **cuerpo** de la nota; oraciones de 30 caracteres o más | La serie diaria, hasta el 2026-10-18 |
| `beto_oraciones_finetuned.csv` (`06_inferencia.ipynb`, versión 2.0) | **Título + cuerpo**; oraciones de 30 a 600 caracteres | El cruce NER × sentimiento |

Solo 1.040 de los 14.012 artículos tenían la misma cantidad de oraciones en ambas, y el sentimiento neto por artículo difería en promedio 2,2 puntos. Además, las dos incluían el **relleno que el scraping dejó dentro del texto**: el bloque "Sobre la firma / Mirá también / Newsletter Clarín" al final de casi todas las notas de Clarín (4.028) y "PUBLICIDAD" en las de Infobae (485).

**Corrección:** `serie_completa_finetuned.py --desde-oraciones` arma el sentimiento de cada artículo desde `beto_oraciones_finetuned.csv`, el mismo archivo del cruce, y excluye las oraciones de relleno con las reglas de `limpiar_etiquetado.py`: 2.438 oraciones, casi todas NEU, el 2,4% de las de Clarín y el 1,2% de las de Infobae. Las oraciones reales que traen una marca pegada ("PUBLICIDAD El ministro…") se conservan con su etiqueta. Quedan 399.803 oraciones de los 14.012 artículos: 27,1% POS, 24,1% NEG, 36,7% NEU y 12,1% MIXTO.

**Efecto en la serie:** la correlación del sentimiento neto diario entre la versión anterior y la nueva es 0,996, y la diferencia media es de 0,55 puntos. Los shocks pasan de 33 a 36. Se mantienen 31 de los 33, todos con el mismo signo e incluidos los dos días electorales (2025-09-08 y 2025-10-27). Salen el 2025-07-31 y el 2025-08-16; entran el 2025-05-09, 2025-11-09, 2025-12-19, 2026-02-11 y 2026-02-23.

**Regla de shocks (precisión):** la media y el desvío de 7 días **incluyen el propio día evaluado**, lo que limita el z máximo posible a (7−1)/√7 ≈ 2,27. Se dejó así en esta carpeta; la unión con el lado bursátil la redefine (banda sin el día evaluado).

## Cómo se mantiene consistente con el corpus

`serie_completa_finetuned.py` hace dos cosas para que el corpus mande sobre el checkpoint:

- `cargar_corpus()` deduplica por URL y excluye los duplicados semánticos ya detectados (`../noticias/analisis_duplicados/reporte_dedup_semantico.json`).
- `sincronizar_checkpoint_con_corpus()` (paso 3 de `main()`, también con `--solo-serie`) descarta del checkpoint las URLs que ya no están en el corpus y refresca la `fecha` desde `fecha_publicacion`, **sin volver a correr el modelo**. Se agregó cuando la depuración eliminó 17 artículos y recuperó 192 fechas de El Economista: sin esto, los eliminados seguían sumando a la serie y los recuperados quedaban fuera de ella.

Regenerar la serie tras cualquier cambio del corpus:

```bash
python serie_completa_finetuned.py --desde-oraciones
```

(`--solo-serie` regenera la versión anterior, desde el checkpoint.)

## Historial de cambios en la serie

| Momento | Artículos | Rango | Días con datos | Shocks |
|---|---:|---|---:|---:|
| `tesis version 2.0` (corpus original) | 14.667 | 2014-11-17 → 2026-05-03 (4.186 días) | 381 | 33 |
| Tras dedup exacto + semántico | 14.448 | 2014-11-17 → 2026-05-03 | 381 | 33 |
| Tras depuración de calidad (2026-10-10) | 14.431 | 2025-01-02 → 2026-05-03 (487 días) | 377 | 35 |
| Tras depuración de plantillas (2026-10-12) | 14.012 | 2025-01-02 → 2026-05-03 (487 días) | 377 | 33 (15 positivos, 18 negativos) |
| Desde el archivo por oración, sin relleno (2026-10-18) | **14.012** | **2025-01-02 → 2026-05-03 (487 días)** | 377 | **36** (17 positivos, 19 negativos) |

El rango de 4.186 días se debía a una sola nota de 2014 que el sitemap había expuesto con `lastmod` reciente (ver `../noticias/DEPURACION_CALIDAD.md`).

## Impacto sobre el resto del análisis

Los resultados de HMM, VAR, Granger y event study que están en `tesis version 2.0/` se calcularon sobre la serie original (33 shocks, pero no necesariamente los mismos días). Si se adopta esta versión de la serie, hay que regenerar `dataset_unificado.csv` y todo lo que depende de él.
