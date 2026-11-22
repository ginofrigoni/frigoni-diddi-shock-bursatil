# Tesina · versión 6.0

**«Impacto de shocks informativos en el comportamiento bursátil de empresas argentinas»**
Gino Frigoni (lado de noticias) y Nicolás Diego Diddi (lado bursátil) · Licenciatura en Ciencia de Datos, Universidad del Gran Rosario · 2026

Se construye y evalúa una metodología de ciencia de datos que **mide el sentimiento** de las noticias económicas argentinas y lo **relaciona** con las acciones de BYMA. Cuatro resultados:
- un corpus de 14.012 notas;
- FinBETO, el modelo de sentimiento;
- variables por acción y rueda;
- un modelo predictivo, evaluado en ruedas que no vio.

## Resultado

| Criterio de aceptación de H1 | Resultado | ¿Cumple? |
|---|---|---|
| FinBETO supera a un modelo de sentimiento existente | F1 macro 0,697 contra 0,542 | ✅ |
| Noticias → precio | ΔAUC −0,012 [−0,054; +0,036] | ❌ |
| Precio → sentimiento | ΔAUC **+0,152** [+0,074; +0,267] | ✅ |

**Se rechaza H0.** En el período estudiado, los medios económicos argentinos **siguieron al mercado**: no lo anticiparon.

## Organización: las fases de CRISP-DM

Cada fase es una carpeta, y adentro hay una subcarpeta por tema. Cada subcarpeta tiene:
- `README.md`: qué hace, qué recibe y qué entrega;
- su script;
- `salidas/`, con los resultados;
- `metricas.csv`, con los números que usan el informe y la presentación.

| Fase | Carpeta | Qué hay |
|---|---|---|
| 1. Comprensión del problema | `1_comprension_del_problema/` | Hipótesis, criterio y objetivos |
| 2. Comprensión de los datos | `2_comprension_de_los_datos/` | `noticias/` (el corpus) y `mercado/` (los precios) |
| 3. Preparación de los datos | `3_preparacion_de_los_datos/` | Regla de las 17:00 · FinBETO · sentimiento por rueda y por empresa · VIX · régimen (anexo) · dataset unificado |
| 4. Modelado | `4_modelado/` | Modelo A contra B: noticias → precio y precio → sentimiento |
| 5. Evaluación | `5_evaluacion/` | Veredicto sobre la hipótesis · anexo de robustez y VAR/Granger |
| 6. Despliegue | `6_despliegue/` | `informe/` (la tesina en LaTeX) y `presentacion/` (el deck) |

## Cómo se reproduce

```
python correr_todo.py
```

- Corre todos los pasos en orden, en unos 2 minutos.
- Verifica los **56 controles automáticos** y compara la huella de cada resultado con la corrida anterior. Hoy los 82 archivos salen idénticos.
- Escribe `controles.csv` y `reproducibilidad.csv`.
- Opciones:
  - `--con-robustez`: corre las 9 variantes de robustez (unos 25 minutos).
  - `--con-informe`: compila el PDF.
  - `--con-gpu`: reentrena FinBETO y vuelve a clasificar el corpus. Necesita torch con CUDA y usa el entorno de la tesis 4.0.
- Requisitos: `requirements.txt`.

## Archivos que no están en git (más de 100 MB)

| Archivo | Cómo se obtiene |
|---|---|
| `3_preparacion_de_los_datos/sentimiento_finbeto/modelos/beto_further_pretrained/model.safetensors` | Copia de la 5.0 (BETO con preentrenamiento continuado) |
| `…/modelos/baseline_finiteautomata/pytorch_model.bin` | Copia de la 5.0, o Hugging Face: `finiteautomata/beto-sentiment-analysis` |
| `…/modelos/beto_finetuned_3clases/` | Se genera con `fase3_reentrenar_para_medir.py` |
| `…/datos/oraciones_corpus.csv` y `…/salidas/beto_oraciones_finetuned.csv` | La lista de oraciones sale de la 5.0; la clasificación, de `clasificar_oraciones.py` |
| `3_preparacion_de_los_datos/sentimiento_por_empresa/datos/ner_oraciones.csv` | Copia de la 5.0 (salida del NER) |

## Documentos de la migración

- `MANIFIESTO_MIGRACION.md`: qué se copió de la 5.0, archivo por archivo, y qué quedó afuera.
- `registro_copia.csv`: la verificación MD5 de cada copia.
- El plan y las decisiones de la versión 6.0 están en `../PLAN_VERSION_6.md`.
- La 5.0 quedó intacta. Algunos controles la **leen**, si está al lado, para verificar que la 6.0 reproduce sus resultados cuando recibe las mismas entradas.
