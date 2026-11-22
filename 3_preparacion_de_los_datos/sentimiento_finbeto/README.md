# sentimiento_finbeto

Convierte el texto de las noticias en sentimiento. MIXTO pasa a NEU, se reentrena FinBETO con 3 clases (POS, NEG, NEU) y se clasifican todas las oraciones del corpus.

**Fase de CRISP-DM:** 3, preparación de los datos (construir atributos derivados). Este paso tiene su propia evaluación porque FinBETO es un modelo.

## Pasos, en orden

| # | Script | Qué hace | Estado |
|---|---|---|---|
| 1 | `limpiar_etiquetado.py` | Limpia las etiquetas de Gemma: de 11.605 oraciones quedan 10.855 | Copiado de la 5.0 |
| 2 | `preparar_dataset_v2.py` | Divide por noticia en train, val y test; **MIXTO → NEU**, con las mismas oraciones que la 5.0 | ✅ 10/10 controles |
| 3 | `fase3_reentrenar_para_medir.py` | Entrena con 3 semillas y guarda el modelo de la semilla 42 | ✅ |
| 4 | `comparar_baseline.py` | FinBETO contra el modelo de referencia, en el mismo test | ✅ |
| 5 | `clasificar_oraciones.py` | Clasifica las 413.515 oraciones del corpus | ⏳ falta la entrada `datos/oraciones_corpus.csv` |

## Resultados (test: 786 oraciones de 39 noticias no vistas)

| | F1 macro | Accuracy |
|---|---|---|
| FinBETO 3 clases (media de 3 semillas) | **0,697 ± 0,012** | 0,703 |
| Modelo de referencia | 0,542 | 0,570 |
| **Ventaja** | **+15,5 puntos** | |

- **Mismo subconjunto que la 5.0** (662 oraciones que ya eran POS, NEG o NEU): FinBETO saca 0,731 contra 0,546 de la referencia. En la 5.0 eran 0,724 contra 0,546. La referencia da exactamente lo mismo que antes, lo que confirma que el test es el mismo.
- **La referencia dice "neutro" a 493 de 786 oraciones.**
- **Las 124 oraciones que eran MIXTO:** el modelo clasifica 78 como NEU, 27 como NEG y 19 como POS.

Matriz de confusión del modelo final (semilla 42). Filas = etiqueta de Gemma, columnas = predicción:

| | POS | NEG | NEU |
|---|---|---|---|
| **POS** | 172 | 20 | 48 |
| **NEG** | 14 | 136 | 32 |
| **NEU** | 56 | 55 | 253 |

## Recibe / entrega

- **Recibe:**
  - `etiquetado_gemma/checkpoint_limpio.jsonl`, las etiquetas de Gemma;
  - `modelos/beto_further_pretrained/`, BETO con preentrenamiento adicional en noticias;
  - `modelos/baseline_finiteautomata/`, el modelo de referencia.
- **Entrega:**
  - `salidas/dataset_3clases/`;
  - `salidas/entrenamiento/` (métricas, matrices, predicciones del test);
  - `modelos/beto_finetuned_3clases/`;
  - `salidas/beto_oraciones_finetuned.csv`.
- **Entorno:** `tesis 4.0/.venv`, que tiene torch con CUDA; se usó una RTX 3090.
