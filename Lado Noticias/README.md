# tesis 4.0

Base de trabajo vigente del lado de noticias de la tesina: corpus de noticias económicas, análisis de sentimiento (FinBETO) y reconocimiento de entidades (NER). Desde el 2026-10-18 es el único punto en que cada archivo fue revisado y controlado:

- **`tesis 3.0`** quedó corrompida por una copia masiva de archivos de `tesis version 2.0`, y no se usa como fuente. `tesis 4.0` partió de su estado al 12/10, antes de esa copia.
- **`tesis version 2.0`** se conserva intacta como referencia.
- **Nada entra a 4.0 desde la 3.0 o la 2.0 sin una decisión explícita.** Cada archivo traído desde afuera está registrado, con su origen y su hash, en el README de la carpeta donde quedó.

El lado bursátil y la unión de ambas partes (VAR, Granger, event study) se trabajan aparte.

## Convención

**Estructura plana por tema:** cada tema es una única carpeta en la raíz, con todo adentro: scripts, datos, documentos de auditoría y corrección, y el borrador de tesis (`SECCION_TESIS.md`). No hay subcarpetas intermedias que obliguen a subir y bajar directorios.

## Temas

### [`noticias/`](noticias/)

Corpus de noticias económicas: 7 portales (9 fuentes) y **14.012 artículos**, del 2025-01-02 al 2026-05-03. En la práctica el corpus empieza en mayo de 2025: el 99,9% de los artículos es posterior al 1/5/2025. Se recolectó vía Wayback Machine y mapas del sitio, y se depuró de duplicados exactos y semánticos, páginas índice, paywall, notas fuera de ventana y contenido de plantilla. Documentos:
- `AUDITORIA_CORPUS.md`: diagnóstico inicial.
- `RESOLUCION_DUPLICADOS.md`: duplicados y credenciales.
- `DEPURACION_CALIDAD.md`: metadatos, paywall, fechas y plantillas, más lo que queda sin resolver (hueco de iProfesional en abril de 2026, marcas horarias).
- `SECCION_TESIS.md`: borrador de tesis.

### [`sentimiento_finbert/`](sentimiento_finbert/)

Sentimiento con FinBETO, un BETO ajustado con etiquetas de Gemma, en 4 clases. Contiene:
- El **etiquetado** (11.605 filas de 408 noticias) y su corrección: limpieza, división por noticia y reentrenamiento para medir.
- La **calidad sobre noticias no vistas:** F1 macro **0,685** en 4 clases, y **0,724** frente a **0,546** del modelo de referencia en 3 clases.
- La **serie diaria** (487 días, 377 con datos, **36 shocks**), armada desde la misma clasificación por oración que usa el cruce con el NER y sin las oraciones de relleno.

No incluye los pesos del modelo en uso (`beto_finetuned/`, en `tesis version 2.0`), que solo hacen falta para volver a clasificar el corpus. Documentos: `README.md` (registro técnico) y `SECCION_TESIS.md` (borrador de tesis).

### [`ner_entidades/`](ner_entidades/)

NER híbrido: spaCy `es_core_news_lg` más un gazetteer de 47 empresas del panel Merval, canonicalizadas por ticker y sector, y 160 indicadores económicos. Incluye:
- El filtrado de ruido de spaCy.
- El bloqueo del relleno del scraping y de las autorreferencias de cada medio.
- El cruce con el sentimiento por oración, con indicadores sinónimos unificados (`equivalencias_indicadores.py`), que genera la serie diaria por empresa e indicador (`ner_sentimiento_diario.csv`).

Documentos: `README.md` y `SECCION_TESIS.md`.

## Entorno

`tesis 4.0/.venv` es un entorno Python 3.13 propio de esta carpeta, creado desde `requirements.txt`. Tiene el modelo `es_core_news_lg` de spaCy y torch con CUDA, que se usó para la medición de calidad de FinBETO. El kernel de Jupyter `tesis4-venv` apunta ahí. En este equipo `pip` se cuelga al escribir su caché: instalar siempre con `--no-cache-dir`.

## Orden de ejecución

1. **Entorno:** crear el venv e instalar `requirements.txt` con `--no-cache-dir`. Los comandos de torch, spaCy, nltk y del kernel `tesis4-venv` están en ese archivo.
2. **Noticias** (`noticias/scripts/`): copiar `.env.example` a `.env` y correr, por ejemplo, `python noticias_diario.py --dias 1`. El dedup semántico corre al final si Ollama está activo con `qwen3.8`. Para depurar un corpus ya recolectado están `python depurar_corpus.py` y `python depurar_plantillas.py`: sin `--aplicar` solo informan.
3. **NER** (`ner_entidades/`): `jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=tesis4-venv --ExecutePreprocessor.timeout=3600 ner_analisis.ipynb`, unos 25 minutos. La última celda corre el cruce con el sentimiento; también se puede correr solo con `python cruce_ner_sentimiento.py`.
4. **Sentimiento** (`sentimiento_finbert/`): `python serie_completa_finetuned.py --desde-oraciones` regenera el sentimiento por artículo y la serie diaria, sin el modelo.
