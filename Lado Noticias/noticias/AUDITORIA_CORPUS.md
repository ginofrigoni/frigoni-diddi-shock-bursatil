# Auditoría del corpus de noticias

Fecha de la auditoría: 2026-09-13
Alcance: carpeta de noticias del pipeline (scripts de scraping + `resultados/`) — en `tesis version 2.0/` vivía en `pipeline_productivo/02_data_understanding/noticias/`; en `tesis 3.0/` es simplemente `noticias/` (ver reorganización en README raíz).
Estado: **solo diagnóstico** — no se modificó ningún script ni archivo de `resultados/` para producir este documento.

> **Actualización 2026-10-10.** Esta auditoría se revisó al resolver los hallazgos 4.3–4.5 (ver `DEPURACION_CALIDAD.md`). Tres cosas cambiaron respecto del texto original, marcadas con "ACTUALIZACIÓN" / "CORRECCIÓN" en cada sección: (1) 4.3 — las páginas de sección eran 2, no "varias"; el resto de los "sin fecha" eran artículos reales afectados por un bug de parseo; (2) 4.4 — los artículos fuera de ventana eran 5 (+1), no 1; (3) 4.5 — mi afirmación de que iProfesional "no publica autor ni tags" era **incorrecta**: era el mismo bug de parseo. Además aparecieron dos hallazgos nuevos: stubs de paywall de La Nación (9) y contenido repetido por plantilla (ver `DEPURACION_CALIDAD.md`, sección "No resuelto"). Las cifras de las secciones 1–3 corresponden al corpus original de 14.667 artículos y no se actualizaron.

Este documento tiene dos lectores en mente: (a) vos mismo escribiendo la sección de Comprensión de los Datos de la tesina, y (b) referencia técnica para decidir qué tocar y en qué orden más adelante.

---

## 1. Resumen ejecutivo

- **14.667 artículos** recolectados de **9 fuentes** (7 portales, 2 de ellos con 2 categorías separadas: Ámbito economía/finanzas).
- **~65.0 millones de caracteres** de contenido, ~4.431 caracteres promedio por artículo.
- Ventana temporal cubierta: mayoritariamente **mayo 2025 → mayo 2026** (con una excepción puntual, ver hallazgo 4.4).
- Tres estrategias de recolección distintas conviven en el mismo corpus (Wayback Machine, sitemap directo, e sitemap diario incremental) — no es un único método uniforme.
- Se encontraron **5 hallazgos de calidad de datos** y **3 hallazgos de seguridad/mantenibilidad** (detalle en §4 y §5). El más relevante: **205 artículos duplicados (Clarín, mismo `url` bajado por dos scripts distintos) confirmados pesando el doble** en la serie diaria de sentimiento que ya se usó para todo el modelado (§4.1, §6). Ninguno es bloqueante para seguir trabajando, pero todos son relevantes para la sección metodológica/limitaciones de la tesina y para decidir si conviene re-ejecutar el scraping antes de re-correr el resto del pipeline.

---

## 2. Arquitectura de recolección

Hay 3 estrategias distintas, implementadas en 5 scripts (+ 1 utilitario de diagnóstico):

| Script | Estrategia | Portales que cubre | Estado |
|---|---|---|---|
| `noticias_historico_v3.py` | Wayback Machine (CDX API → snapshots → HTML archivado) | Ámbito (economía+finanzas), La Nación, Clarín, TN, Infobae | Activo — generó 5 de los 9 archivos actuales |
| `noticias_sitemap.py` | Sitemap XML directo del sitio, sin Wayback | Clarín, El Economista, iProfesional | Activo — generó los otros 3 archivos (más `clarin_sitemap`, que se solapa con Clarín vía v3, ver §4.1) |
| `noticias_diario.py` | Sitemap de noticias (`sitemap-news.xml`), pensado para correr periódicamente, `--dias 1` por defecto | los 7 portales | Diseñado para mantenimiento incremental — no está claro (no verificado en esta auditoría) si ya se usó para generar parte del corpus actual o si todavía no corrió en producción |
| `noticias_historico.py`, `noticias_historico_v2.py` | Versiones previas de la estrategia Wayback | — | Obsoletos, reemplazados por v3, siguen presentes en la carpeta |
| `diagnostico_ambito.py` | Utilitario manual (consulta CDX API y lista snapshots) | Ámbito | Herramienta de debugging, pensada para correr "antes de usar `noticias_historico_v2.py`" (según su propio docstring) — atada a una versión ya obsoleta |

**Punto clave:** el corpus actual en `resultados/` no viene de un único pipeline consistente — es la unión de dos corridas con estrategias distintas (`v3` vía Wayback + `sitemap.py` directo), corridas en algún momento antes de esta migración. Eso por sí solo ya explica varios de los hallazgos de abajo.

---

## 3. Estadísticas del corpus por fuente

| Archivo | Artículos | Rango de fechas | Sin fecha_publicación | Sin autor |
|---|---:|---|---:|---:|
| `ambito_economia.jsonl` | 500 | 2025-01-02 → 2026-04-10 | 0 | 0 |
| `ambito_finanzas.jsonl` | 257 | 2025-06-15 → 2026-03-02 | 0 | 0 |
| `clarin_economia.jsonl` | 500 | 2025-05-09 → 2026-04-18 | 0 | 0 |
| `clarin_sitemap.jsonl` | 3.748 | 2014-11-17 → 2026-05-03 | 0 | 0 |
| `eleconomista_sitemap.jsonl` | 3.055 | 2025-05-01 → 2026-05-02 | 194 (6,4%) | 194 (6,4%) |
| `infobae_economia.jsonl` | 500 | 2025-05-05 → 2026-05-02 | 0 | 0 |
| `iprofesional_sitemap.jsonl` | 5.504 | 2025-05-04 → 2026-04-15 | 0 | **5.504 (100%)** |
| `lanacion_economia.jsonl` | 500 | 2025-05-06 → 2026-05-02 | 9 (1,8%) | 9 (1,8%) |
| `tn_economia.jsonl` | 103 | 2025-08-14 → 2026-05-02 | 0 | 0 |
| **Total** | **14.667** | | | |

Nota sobre las fechas "futuras" (2026-xx): no son un error — hoy es 2026-09-13, así que esas fechas están dentro del último año.

De los 9 archivos, **4 tocan el techo de `limite_articulos: 500`** de `noticias_historico_v3.py` (ámbito economía, ámbito finanzas nunca llega pero está cerca, Clarín economía, Infobae, La Nación): eso quiere decir que **hay más artículos disponibles en Wayback de los que se bajaron** — el corpus de esas 4-5 fuentes está artificialmente acotado, no es "todo lo que había".

Contenido: no se encontraron artículos con `contenido` nulo o vacío en ningún archivo, y los artículos sospechosamente cortos (<300 caracteres) son marginales (<0,2% en los dos únicos archivos donde aparecen). La extracción de texto (JSON-LD → OG → Trafilatura → BeautifulSoup) funciona bien en general.

---

## 4. Hallazgos de calidad de datos

### 4.1 Duplicación entre Clarín-Wayback y Clarín-sitemap (205 artículos, 41%)

`clarin_economia.jsonl` (vía `noticias_historico_v3.py`, Wayback) y `clarin_sitemap.jsonl` (vía `noticias_sitemap.py`, directo) comparten **205 de las 500 URLs** de `clarin_economia.jsonl` — es decir, el 41% de ese archivo está duplicado en el otro. Son la misma nota, el mismo `url`, bajada dos veces por dos scripts con dos estrategias distintas.

**Confirmado que esto llega hasta el final, sin filtrarse en ningún paso intermedio.** El archivo que agrega sentimiento por día no es `construir_dataset_unificado.py` (ese solo lee el CSV ya agregado) sino `04_modeling/sentimiento_finbert/serie_completa_finetuned.py`, que:

1. Lee los 9 `.jsonl` y los concatena en una sola lista (`cargar_corpus()`).
2. Filtra contra su propio checkpoint (`checkpoint_finetuned.jsonl`) para no volver a correr inferencia sobre algo ya procesado en una corrida *anterior* — pero no deduplica *dentro* de la lista que acaba de cargar. Si la misma URL aparece dos veces en los 9 archivos y ninguna copia está todavía en el checkpoint, corre inferencia sobre **las dos**.
3. `exportar_articulos()` y `generar_serie()` leen el checkpoint línea por línea y promedian por fecha sin deduplicar por `url` en ningún punto.

Verificación directa sobre `checkpoint_finetuned.jsonl`: **14.667 filas, mismo total que el corpus, pero solo 14.462 URLs únicas — 205 URLs duplicadas, 410 filas involucradas.** Coincide exactamente con el solapamiento Clarín-Wayback/Clarín-sitemap encontrado arriba: esas 205 notas están pesando **el doble** en `sent_neto`/`pct_pos`/etc. de los días en que se publicaron, y por lo tanto también en `finetuned_serie_diaria.csv` y `dataset_unificado.csv` río abajo.

### 4.2 Artículos con título duplicado, URL distinta (posible re-publicación cruzada)

En `eleconomista_sitemap.jsonl`: **39 títulos** se repiten, involucrando **210 artículos** (6,9% del archivo). Ejemplo verificado:

- `.../economia/el-riesgo-pais-651-puntos-basicos-n84784` (2025-05-15 18:09)
- `.../finanzas/el-riesgo-pais-651-puntos-basicos-n84783` (2025-05-15 18:04)

Mismo título, mismo contenido, publicado 5 minutos aparte bajo `/economia/` y `/finanzas/` con IDs de nota consecutivos (`n84783`/`n84784`) — es el sitio cross-posteando la misma nota a dos secciones, no un bug del scraper. El efecto downstream es el mismo que en 4.1: doble conteo en el sentimiento agregado.

Este patrón también aparece, en menor escala, en `iprofesional_sitemap.jsonl` (14 títulos / 36 artículos), `lanacion_economia.jsonl`, `clarin_sitemap.jsonl` y `ambito_finanzas.jsonl`. No los revisé uno por uno — algunos títulos duplicados podrían ser coincidencia genuina (ej. dos actualizaciones del "dólar hoy" con exactamente el mismo título) y no cross-posting; queda como pendiente de revisión manual si se quiere depurar a fondo.

### 4.3 Páginas de sección coladas como si fueran artículos

> **ACTUALIZACIÓN (2026-10-10).** Se verificaron los 194 casos sin fecha de `eleconomista_sitemap.jsonl`, y la hipótesis de abajo ("probablemente varios sean de este tipo") **era falsa**: solo **2** son páginas de índice de sección. Los otros **192 son artículos reales** a los que les faltaban fecha, autor y tags por un bug de parseo del JSON-LD (caracteres de control crudos → `json.loads` estricto falla en silencio; ver 4.5). Se recuperaron las 192 fechas re-descargando esas páginas (`recuperar_metadatos.py`, 0 errores). Detalle en `DEPURACION_CALIDAD.md`.

Los dos casos sin `fecha_publicación`/`autor` de `eleconomista_sitemap.jsonl` que inspeccioné no son notas: son las páginas de índice `eleconomista.com.ar/economia/` y `/finanzas/` — el listado de tapa de la sección, no una noticia individual. El filtro de categoría de `noticias_sitemap.py` (`"/economia/" in url`) es demasiado laxo: acepta cualquier URL que contenga el string, incluida la propia URL de la sección.

Esto contamina el corpus con contenido que no es una noticia (texto de navegación/resumen de sección) y le mete ruido al sentimiento si esas filas llegan a `construir_dataset_unificado.py`.

### 4.4 Artículo con fecha de publicación real muy vieja (2014) colado por `lastmod`

> **ACTUALIZACIÓN (2026-10-10).** No era un único caso: hay **5** artículos de `clarin_sitemap.jsonl` con fecha de publicación real anterior a 2025 (2014-11-17, 2024-05-05, 2024-10-15 ×2, 2024-10-17), todos con `lastmod` de 2025 en el sitemap. Además, al recuperar las fechas faltantes de El Economista apareció un sexto caso del mismo tipo (nota con id muy antiguo que el sitio re-fechó en agosto de 2026, posterior al fin de la recolección). Los 6 se eliminaron del corpus (ver `DEPURACION_CALIDAD.md`).

Un artículo de Clarín (`clarin_sitemap.jsonl`) tiene `fecha_publicacion: 2014-11-17` pero `fecha_sitemap` (el `lastmod` del sitemap): `2025-11-05` — la nota original es de 2014 pero fue editada/republicada en 2025, y el sitemap sólo expone la fecha de última modificación. Como `noticias_sitemap.py` filtra por `lastmod` (no por fecha de publicación real) para decidir si un artículo entra en la ventana de "últimos N días", este tipo de nota vieja-pero-reeditada puede colarse. Si el pipeline usa `fecha_publicacion` para alinear sentimiento con el mercado, esta nota terminaría "flotando" en 2014 en vez de aportar señal a 2025 (de hecho estiraba el rango de `finetuned_serie_diaria.csv` a 4.186 días, de los cuales solo 381 tenían datos); si en cambio usa `fecha_sitemap`/`fecha_descarga`, aporta señal a la fecha equivocada de todas formas.

### 4.5 `iProfesional`: autor y tags faltantes en el 100% de los artículos

> **CORRECCIÓN (2026-10-10).** La versión original de esta sección decía que no era un bug del parser y que el sitio no publicaba autor ni tags. **Era incorrecto**: lo afirmé sin haber inspeccionado el HTML. Al revisarlo, el JSON-LD de iProfesional sí trae `author` y `keywords` (además de `article:author` / `article:tag` en las metaetiquetas), pero el bloque contiene caracteres de control crudos dentro de strings, `json.loads()` estricto lanzaba "Invalid control character" y `except Exception: continue` lo descartaba en silencio. Es el mismo bug que dejó sin fecha a 192 artículos de El Economista (ver 4.3). Corregido en el extractor (`strict=False`); el corpus actual de iProfesional **no** se re-extrajo (autor y tags no se usan en el análisis, y implicaba ~5.500 requests): sigue sin esos campos. Las fechas de iProfesional no están afectadas (vienen del `news:publication_date` del sitemap).

---

## 5. Hallazgos de seguridad / mantenibilidad

### 5.1 Credenciales de Internet Archive en texto plano

`noticias_historico_v3.py` tiene hardcodeado un par de credenciales S3-like de Internet Archive (`IA_S3_KEY` / `IA_S3_SECRET`) directamente en el código fuente (línea ~125-126), usadas para autenticar contra la Wayback Machine con rate limits más altos ("LOW" tier). Al estar en el `.py`, viajan con cualquier copia del repo/zip del proyecto.

### 5.2 Conteo de errores no es confiable

Los `meta.total_errores` de casi todos los archivos dan `0` (o `1` en un solo caso) incluso en corridas de miles de artículos. Mirando el código: el contador de errores (`n_error`) se inicializa en `0` al arrancar `procesar_sitio()` en cada corrida — como el checkpoint excluye las URLs ya procesadas exitosamente, pero **no** recuerda errores de corridas anteriores, cada corrida nueva sólo reporta los errores *de esa corrida*, y el JSON final pisa el `meta` anterior. Si una URL falló en la corrida 1 y nunca se reintentó a propósito, ese error se "pierde" del reporte a partir de la corrida 2. En la práctica esto significa que **no hay forma de saber, mirando el `meta` actual, cuántos artículos se intentaron y fallaron en total** a lo largo de toda la vida del corpus.

### 5.3 Scripts obsoletos sin eliminar

`noticias_historico.py`, `noticias_historico_v2.py` y `diagnostico_ambito.py` (atado a v2) siguen en la carpeta pese a estar reemplazados por v3 según el propio README. No rompen nada, pero son ruido para cualquiera (vos en 6 meses, un jurado que mire el repo) que trate de entender cuál es el script "real".

---

## 6. Impacto en el resto del pipeline

El flujo real es: `resultados/*.jsonl` → `serie_completa_finetuned.py` (FinBERT, agrega por día) → `finetuned_serie_diaria.csv` → `construir_dataset_unificado.py` → `dataset_unificado.csv` / `dataset_panel_acciones.csv` → HMM / VAR / Granger / event study.

Confirmado en §4.1: los 205 duplicados exactos de URL (Clarín) **ya están pesando el doble** en `sent_neto` y el resto de las métricas diarias de `finetuned_serie_diaria.csv`, y por lo tanto en todo lo que se calculó a partir de ahí (HMM de régimen — indirectamente, vía `dataset_unificado.csv` —, VAR, Granger, event study, shocks). Los duplicados de título con URL distinta de §4.2 (~210 artículos adicionales de cross-posting, no capturados por el chequeo de URL) probablemente tienen el mismo efecto, aunque no se verificó caso por caso. En conjunto son ~415 de 14.667 artículos (~2,8%) con peso duplicado — una fracción chica del corpus total, pero concentrada en notas de alto perfil (dólar, riesgo país), que son justamente las que más pesan en el análisis de shocks de sentimiento.

Esto **no invalida los resultados existentes** (2,8% de peso duplicado no alcanza para cambiar conclusiones cualitativas), pero sí es una limitación real y concreta para documentar en la sección de limitaciones de la tesina, y un candidato claro si se decide re-ejecutar el pipeline. Quedó definido que **se puede considerar re-ejecutar todo el pipeline** si se decide corregir estos puntos — pero no se tocó nada todavía; esta auditoría es sólo diagnóstico.

---

## 7. Preguntas abiertas / pendientes de decisión

- ¿`noticias_diario.py` corrió alguna vez en producción, o el corpus actual es 100% de corridas manuales de `v3` + `sitemap.py`? No se pudo determinar solo con los datos de `resultados/`.
- Los duplicados de título de 4.2 en las otras fuentes (La Nación, Clarín-sitemap, Ámbito finanzas) no se revisaron caso por caso — falta confirmar cuántos son cross-posting real vs. coincidencia de título genérico.
- Alcance del `limite_articulos: 500` (§3): decidir si vale la pena sacarlo y volver a bajar el resto del histórico disponible en Wayback para esas 4-5 fuentes.
- Si se decide corregir la duplicación (§4.1/§4.2), el lugar correcto es `serie_completa_finetuned.py::cargar_corpus()` (deduplicar por `url` antes de correr inferencia) — no `construir_dataset_unificado.py`, que ya recibe los datos agregados y nunca ve las URLs individuales.
