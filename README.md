# Impacto de shocks informativos en el comportamiento bursátil de empresas argentinas

Trabajo Final de Grado de la Licenciatura en Ciencia de Datos (Universidad del Gran Rosario), de **Gino Frigoni** y **Nicolás Diddi**: *un enfoque basado en análisis de sentimiento y modelos de series temporales*.

La tesina estudia si las noticias económicas de los medios digitales argentinos anticipan el precio y el volumen de las acciones de BYMA, o si reflejan lo que el mercado ya hizo. Resultado principal: el tono de las noticias no anticipa al mercado; el retorno del S&P Merval sí anticipa el tono de las notas siguientes, sobre todo el de las publicadas la misma noche, después del cierre.

## El documento

| Archivo | Qué es |
|---|---|
| [`Informe Final/Tesina_Reducida.pdf`](Informe%20Final/Tesina_Reducida.pdf) | **Versión de entrega** (46 páginas) |
| [`Informe Final/Tesina_Final.pdf`](Informe%20Final/Tesina_Final.pdf) | Versión completa (92 páginas), con todas las tablas de detalle |

En los PDF, debajo de cada referencia de la bibliografía está la ruta del paper dentro de este repositorio; con un lector de escritorio, la ruta abre el archivo.

## Organización

El trabajo tiene tres partes que no se modifican entre sí. Cada paso es una carpeta con su script, sus resultados, sus controles automáticos y su documentación en PDF.

| Carpeta | Contenido | Responsable |
|---|---|---|
| [`Lado Noticias/`](Lado%20Noticias/) | Corpus de 14.012 notas (Wayback Machine y mapas del sitio), FinBETO y reconocimiento de entidades | Gino Frigoni |
| [`Lado Bursatil/`](Lado%20Bursatil/) | Panel de 47 acciones, clustering, VIX argentino, estacionariedad, volatilidad y regímenes (HMM) | Nicolás Diddi |
| [`Unión/`](Unión/) | Cada nota a su rueda, datasets unificados, VAR y Granger, estudios de eventos y robustez | Ambos |
| [`Informe Final/`](Informe%20Final/) | La tesina en LaTeX y los scripts que la compilan | Ambos |

Cada carpeta tiene su propio README con el detalle.

## Cómo se reproduce

- **Lado de noticias:** entorno Python 3.13 desde `Lado Noticias/requirements.txt` (ver `Lado Noticias/README.md`). La recolección usa credenciales de Internet Archive en `Lado Noticias/noticias/.env`, que no se sube: copiar `.env.example` y completarlo.
- **Lado bursátil:** cada carpeta tiene un script de Python; los PDF de documentación se generan con Node desde `Lado Bursatil/99_generadores_documentacion` (`npm install`).
- **Unión:** desde `Unión/09_entrega_final`, `python correr_todo.py` rehace todos los pasos, verifica los 66 controles automáticos y compara los 64 archivos de resultados con la corrida anterior.
- **Tesina:** desde `Informe Final`, `python compilar_reducida.py` (versión de entrega) o `python compilar_tesina.py` (versión completa). Usan [tectonic](https://tectonic-typesetting.github.io/), en `~/tools/tectonic/tectonic.exe`.

## Archivos que no están en el repositorio

GitHub no acepta archivos de más de 100 MB. Estos cinco quedaron afuera por su tamaño:

| Archivo | Tamaño | Cómo se obtiene |
|---|---:|---|
| `Lado Noticias/sentimiento_finbert/beto_further_pretrained/model.safetensors` | 419 MB | Pesos de BETO con preentrenamiento continuado sobre el corpus; copia de los autores (sha256 `b4ff46aa…`). Solo lo usa la medición de calidad (Fase 3) |
| `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/pytorch_model.bin` | 419 MB | Modelo de referencia, de Hugging Face: [`finiteautomata/beto-sentiment-analysis`](https://huggingface.co/finiteautomata/beto-sentiment-analysis), revisión `9384c7f3…` |
| `Lado Noticias/sentimiento_finbert/beto_oraciones_finetuned.csv` | 169 MB | Sentimiento FinBETO de las 408.939 oraciones del corpus; copia de los autores (sha256 `f4b9c10f…`). Lo leen el cruce con el NER y la unión |
| `Lado Noticias/ner_entidades/resultados_ner/ner_oraciones.csv` | 221 MB | Se regenera con `Lado Noticias/ner_entidades/ner_analisis.ipynb` |
| `Lado Noticias/ner_entidades/resultados_ner/ner_articulos.csv` | 79 MB | Ídem |

Tampoco se suben los entornos (`.venv/`, `node_modules/`), que se reinstalan, ni el archivo de credenciales `.env`.
