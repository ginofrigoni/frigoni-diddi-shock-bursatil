# Unión

Une el lado bursátil (`../Lado Bursatil`, Nicolás) con el lado de noticias (`../Lado Noticias`, Gino) y responde la pregunta de la tesis: **¿las noticias económicas anticipan al mercado, o el mercado anticipa a las noticias?**

**Resultado:** los medios siguen al mercado. En las notas de la misma noche, después del cierre, cuentan la suba o la baja con un tono que la acompaña. Ni el tono ni la cantidad de noticias anticipan los precios o el volumen. Con la definición de shock del plan (muchas más notas que lo habitual), la acción de la empresa se opera más ese mismo día, sin una dirección en el precio. El detalle está en `09_entrega_final/Documentacion_Entrega_Final.pdf`.

Ningún paso modifica los archivos de los dos lados: los lee y escribe sus resultados en su propia carpeta.

## Carpetas

| Carpeta | Paso | Qué hace |
|---|---|---|
| `00_pipeline_union` | — | Pipeline, diagnóstico del cruce, inventario de la versión 2.0 contra la 3.0 y mensajes para Gino |
| `01_alineacion_noticias_ruedas` | U1 | Asigna cada noticia a la rueda en la que el mercado pudo reaccionar (regla de las 17:00) |
| `02_sentimiento_por_rueda` | U2 | Tono y atención de los medios por rueda; ruedas de tono extremo |
| `03_sentimiento_por_empresa` | U3 | Tono de cada empresa por rueda (cruce de entidades y sentimiento de Gino) |
| `04_dataset_unificado` | U4 | Las dos tablas finales (mercado y panel) y el diccionario de variables |
| `05_adf_union` | U5 | Estacionariedad de cada serie en las 244 ruedas |
| `06_var_granger` | U6 | VAR, Granger e impulso-respuesta en las dos direcciones |
| `06b_noticias_preapertura` | U6b | Notas publicadas con el mercado cerrado → apertura (especificación fijada de antemano) |
| `07_event_study` | U7 | Precio y volumen alrededor de las ruedas de noticias extremas |
| `07b_shock_volumen_noticias` | U7b | Event study del shock de cantidad de noticias tal como lo define el plan (especificación fijada de antemano, con prueba pre-apertura) |
| `08_robustez` | U8 | Los resultados con 12 variantes, una decisión por vez |
| `09_entrega_final` | U9 | Documento final, mapa de la tesis y reproducibilidad |
| `10_papers_union` | — | Papers relacionados con cada prueba y sus referencias (`referencias_papers.md`, `.bib` y `Referencias_Papers_Union.pdf`) |
| `11_papers_lado_noticias` | — | Papers relacionados con el lado de noticias (corpus, sentimiento, NER); está acá para no modificar `Lado Noticias` |
| `99_generadores_documentacion` | — | Los generadores de los PDF (Node + docx; reutilizan el estilo del lado bursátil) |

Cada carpeta tiene su script, sus CSV, un `verificaciones.csv` con los controles automáticos y su PDF.

## Cómo reproducir todo

Desde `09_entrega_final`:

```bash
python correr_todo.py
```

El script corre los pasos en orden (unos 2 minutos y medio), verifica que pasen todos los controles y compara la huella de cada archivo de resultados con la corrida anterior (`reproducibilidad.csv`).

Para regenerar un PDF, desde `99_generadores_documentacion`:

```bash
node build_doc_u6.js
```

Después hay que convertir el `.docx` a PDF con LibreOffice:

```bash
soffice --headless --convert-to pdf Documentacion_U6_VAR_Granger.docx
```

## Requisitos

- **Python 3:** pandas, numpy, statsmodels, scipy y matplotlib.
- **Node:** el paquete `docx`, que ya está instalado en `../Lado Bursatil/99_generadores_documentacion/node_modules`.
- **LibreOffice:** para pasar los Word a PDF.

U3, U6b y U8 importan las funciones del cruce de Gino desde `../Lado Noticias/ner_entidades/cruce_ner_sentimiento.py`.
