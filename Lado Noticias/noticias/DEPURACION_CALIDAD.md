# Depuración de calidad — noticias

Fecha: 2026-10-10
Continúa: [AUDITORIA_CORPUS.md](AUDITORIA_CORPUS.md) (hallazgos 4.3, 4.4, 4.5) y [RESOLUCION_DUPLICADOS.md](RESOLUCION_DUPLICADOS.md) (pendiente: dedup semántico no automatizado).
Todo vive en `tesis 3.0/`; `tesis version 2.0/` queda intacta.

> **Nota (2026-10-18):** este documento se escribió cuando la carpeta de trabajo era `tesis 3.0`. Esa carpeta quedó corrompida por una copia masiva desde la 2.0, y la base vigente es `tesis 4.0`, que contiene estos mismos archivos revisados. Las menciones a `tesis 3.0` describen dónde estaba el trabajo en ese momento.

## Resumen

| | Antes | Después |
|---|---:|---:|
| Artículos en `resultados/` | 14.448 | **14.431** (14.012 tras la sección 8) |
| Artículos sin `fecha_publicacion` | 194 (El Economista) + 9 (La Nación, stubs) | **0** |
| Rango de `fecha_publicacion` | 2014-11-17 → 2026-05-03 | **2025-01-02 → 2026-05-03** |
| `finetuned_serie_diaria.csv` | 4.186 días de rango, 381 con datos | 487 días, 377 con datos |

## 1. Causa raíz: JSON-LD con caracteres de control

El extractor de metadatos de los scrapers hacía `json.loads(bloque_jsonld)` y, ante cualquier excepción, `continue`. Los bloques JSON-LD de El Economista e iProfesional traen **caracteres de control crudos dentro de strings** (ej. saltos de línea literales en `articleBody`), y el parseo estricto de Python falla con `Invalid control character at: line 28 column 368`. El error se tragaba en silencio y el scraper seguía con los fallbacks (OG, `<h1>`, fecha del sitemap), perdiendo **fecha de publicación, autor, tags y fecha de modificación**.

Efectos medidos sobre el corpus:

- **El Economista**: 194 artículos sin fecha/autor/tags. No eran "páginas de sección" como se había supuesto (hallazgo 4.3 original): solo **2** eran páginas índice; los otros **192 eran artículos reales** (190 dentro de la ventana, ids ≥ 84360).
- **iProfesional**: 5.497 artículos (100%) sin autor, tags ni fecha de modificación. La auditoría original **había atribuido esto a una limitación del sitio, y era incorrecto** (ver corrección en 4.5 de la auditoría). Las fechas de iProfesional no se vieron afectadas: vienen del `news:publication_date` del sitemap (5.481 de 5.497 coinciden exactamente con `fecha_sitemap`).

**Corrección**: `json.loads(..., strict=False)` en `extraer_metadata_jsonld` de los tres scrapers, y una versión sin dependencias (`calidad_utils.metadata_jsonld`) para el script de recuperación.

## 2. Recuperación de metadatos de El Economista

`scripts/recuperar_metadatos.py` volvió a bajar solo los artículos sin fecha y completó los campos faltantes sin pisar nada existente ni tocar el contenido. Resultado: **192 de 192 fechas recuperadas, 0 errores** (también 190 autores, 188 tags, 190 fechas de modificación).

## 3. Depuración del corpus existente

`scripts/depurar_corpus.py` (idempotente; con `--aplicar` elimina y escribe el reporte acumulado en `analisis_calidad/depuracion_2026-10-10.json`, con cada URL eliminada y su motivo):

| Motivo | Artículos | Detalle |
|---|---:|---|
| `no_articulo` | 2 | `eleconomista.com.ar/economia/` y `/finanzas/` (páginas índice de sección) |
| `paywall` | 9 | La Nación: stub "Suscribite a LA NACION y disfrutá del acceso digital" (527 caracteres de relleno en lugar del artículo) |
| `fecha_fuera_de_ventana` | 5 | Clarín (vía sitemap): fecha real de publicación 2014-11-17, 2024-05-05, 2024-10-15 (×2), 2024-10-17; el sitemap las listaba por `lastmod` de 2025 |
| `fecha_posterior_a_recoleccion` | 1 | El Economista: nota con id muy antiguo (n59754) que el sitio re-fechó en agosto de 2026, después del fin de la recolección — la fecha recuperada ya no describía el contenido guardado |
| **Total** | **17** | 14.448 → 14.431 |

Ventana del corpus: `--desde 2025-01-01`, `--hasta 2026-05-03` (fecha en que terminó la recolección).

## 4. Prevención en los scrapers

Los tres scrapers activos ahora:

- **Exigen forma de URL de artículo** (`calidad_utils.PATRON_ARTICULO`, por fuente) además de la categoría. Cada patrón se validó contra el corpus existente: no rechaza ningún artículo legítimo. El de iProfesional tolera el prefijo `/index.php/` (47 artículos lo traen; no hay gemelos con la URL sin prefijo).
- **Descartan stubs de paywall** (título "Suscribite a LA NACION…").
- **Filtran por fecha de publicación real**, no solo por `lastmod` (`noticias_sitemap.py` y `noticias_diario.py`; v3 no, porque su ventana la define el snapshot de Wayback).
- Registran `total_descartadas` en el meta, separado de `total_errores`, y muestran `[SKIP]` en vez de `[ERR]`.

## 5. Dedup semántico automatizado

`dedup_semantico_qwen.py` quedó **incremental e integrado**:

- Guarda los veredictos en `analisis_duplicados/reporte_dedup_semantico.json` y los reutiliza: una corrida repetida solo consulta al modelo los grupos nuevos (verificado: con el corpus actual, 19 grupos candidatos, 19 con veredicto previo, 0 consultas).
- Los tres scrapers lo llaman al terminar (`post_scraping()`). **Si Ollama o el modelo no están disponibles, se omite con un aviso** — el scraping nunca falla por esto. (Ojo: en esta sesión Ollama no estaba corriendo y hubo que levantarlo antes de poder probar.)
- Las URLs descartadas como duplicado se leen desde `dedup_utils.cargar_urls_ya_scrapeadas()`, para que el sitemap — que las sigue listando — no las vuelva a bajar.
- Al eliminar, sincroniza el `.json` hermano de cada `.jsonl` modificado (`calidad_utils.sincronizar_json`).
- Probado con una consulta real tras actualizar el modelo (`qwen3.8` se había actualizado desde la sesión anterior): veredicto correcto.

## 6. Impacto en el resto del pipeline

- `sentimiento_finbert/serie_completa_finetuned.py` ganó `sincronizar_checkpoint_con_corpus()` (corre en el paso 3 de `main()`, también con `--solo-serie`): descarta del checkpoint las URLs que ya no están en el corpus y refresca `fecha` desde el corpus, **sin volver a correr el modelo**. En esta pasada: −17 filas, 191 fechas actualizadas (las 190 recuperadas de El Economista pasaron a sumar a la serie diaria), 14.431 filas finales.
- **La serie cambió**: `finetuned_serie_diaria.csv` pasó de 33 a **35 shocks** (17 positivos, 18 negativos), y su rango de 4.186 días a 487. Los resultados de HMM/VAR/Granger/event study que están en `tesis version 2.0/` se calcularon sobre la serie anterior; si se adopta esta, hay que regenerarlos.
- **Inconsistencia corregida**: `clarin_economia.json` tenía 295 noticias y su `.jsonl` 294 (no se había regenerado tras el dedup semántico de la sesión anterior). Por eso NER había procesado 14.449 artículos en vez de 14.448. Ahora todos los `.json` se sincronizan desde su `.jsonl` y hay una verificación de consistencia en la depuración.

## 7. No resuelto (decisión pendiente o fuera de alcance)

- **Contenido repetido por plantilla** *(resuelto el 2026-10-12, ver sección 8; el texto que sigue describe el hallazgo original)*. 20 grupos de artículos con texto *completo* idéntico bajo URLs/fechas distintas (53 artículos, 33 redundantes, 0,23% del corpus; el grupo más grande son 11 notas de El Economista del 2026-04-02 al 04-30). Aparte, 7 inicios de texto (primeros 160 caracteres) se repiten en 348 artículos (2,4%), casi todos de El Economista: "Dólar hoy: a cuánto cotiza este jueves 29 de mayo" (147), la nota de Pix (76 + 31), etc. — el cuerpo cambia (cotizaciones del día) pero arrancan con el mismo párrafo. No se tocó: depende de si una nota republicada con otra fecha cuenta como un evento o como ruido para la serie de sentimiento.
- **Entidades HTML en títulos** (`&quot;`, etc.): **resuelto** (2026-10-12). 435 títulos (431 El Economista, 4 iProfesional) se decodificaron con `html.unescape` en el corpus, y los tres scrapers lo aplican al extraer el título. Queda sin decodificar el campo `bajada` de 290 notas de El Economista (no lo usa NER ni sentimiento). Copia previa al cambio: `_backup_pre_unescape/`.
- **iProfesional**: autor, tags y fecha de modificación siguen sin re-extraerse (implicaría ~5.500 requests; no se usan en el análisis). Las corridas nuevas sí los traen.
- **Hueco de iProfesional en abril de 2026** (detectado el 2026-10-18): 512 notas en marzo y solo 3 en abril (la última del 15/04), contra unas 500 por mes en los meses anteriores. La corrida del scraper fue el 03/05/2026, con ventana 03/05/2025 → 03/05/2026, así que no es un problema de ventana; la causa no se verificó. Como iProfesional es el 39% del corpus, abril de 2026 queda con unas 670 notas contra 1.100–1.400 en los otros meses y con otra composición por fuente. No se volvió a recolectar.
- **Marcas horarias** (detectado el 2026-10-18): Clarín, Infobae y La Nación traen `fecha_publicacion` en UTC ("Z") y el resto en hora argentina. Como la fecha se toma con los primeros 10 caracteres, 95 notas publicadas de noche (0,7%) quedan con el día siguiente. Además, varias fuentes tienen horas por defecto: el 20% de Clarín por sitemap figura a las 07:00 o 07:08, el 3,8% de iProfesional a las 07:00 y el 7–9% de Ámbito a las 00:00. No se corrigió en el corpus; la unión con el lado bursátil convierte todo a hora argentina.
- No hay normalización de URLs (`/index.php/`, `www.`, query strings) en el chequeo de duplicados: hoy no hay gemelos, pero sería la defensa correcta si aparecen.

## 8. Depuración de contenido repetido por plantilla (2026-10-12)

`scripts/depurar_plantillas.py` (idempotente; `--aplicar` elimina y escribe `analisis_calidad/depuracion_plantillas_2026-10-12.json` con cada URL, su motivo y el tamaño de su grupo). Agrupa por fuente y por los primeros 160 caracteres normalizados del contenido:

| Motivo | Artículos | Regla |
|---|---:|---|
| `contenido_duplicado` | 83 | grupos de 2 a 10 notas: se conserva la más antigua |
| `contenido_plantilla` | 336 | grupos de 11 o más: relleno fijo, se eliminan todas |
| **Total** | **419** | 14.431 → **14.012** (2,9%) |

Por fuente: El Economista −356 (3.051 → 2.695), iProfesional −42, Ámbito Finanzas −16, Ámbito Economía −2, Clarín sitemap −2, TN −1.

Qué eran los grupos grandes (todos de El Economista):

| Grupo | Notas | Sentimiento neto (desvío) |
|---|---:|---|
| "Dólar hoy" (esquema sin cepo, may-2025 a ene-2026) | 147 | 0,0 (0) |
| "Dólar hoy" (bandas, 2026) | 71 | 18,2 (0) |
| Pix en Brasil, versión A (jul-nov 2025) | 76 | 52,2 (0) |
| Pix en Brasil, versión B (ene-feb 2026) | 31 | 63,6 (0) |
| Bloque de navegación extraído en lugar de la nota (abril 2026) | 11 | — (error de extracción) |

Los títulos y el texto de las notas "Dólar hoy" son distintos (fecha y cotizaciones), pero el modelo asigna el mismo valor a todas: depende de la parte fija del texto. En los 11 casos de navegación el contenido guardado (555 caracteres) no es la nota.

**Decisión**: eliminar en lugar de marcar (decisión del usuario; ~3% del corpus). Se eliminaron también las notas más antiguas de los cinco grupos grandes, que de haberse conservado dejarían un único artículo de relleno por grupo.

**Efecto** (verificado recalculando antes de aplicar): 377 de 487 días con datos (igual que antes); shocks 35 → **33** (15 positivos, 18 negativos); 29 de los 35 shocks previos se mantienen, 6 desaparecen y 4 aparecen. Entre los shocks previos, el peso de notas redundantes en el día era de 0% a 20% (típicamente <10%), por lo que la serie es bastante robusta.

**Prevención**: `dedup_utils.cargar_urls_ya_scrapeadas()` también lee las URLs eliminadas de `analisis_calidad/depuracion_*.json`, de modo que el sitemap, que las sigue listando, no las vuelve a bajar (14.462 URLs excluidas = 14.012 del corpus + 14 duplicados semánticos + 17 depuración de calidad + 419 plantillas). Las plantillas nuevas que aparezcan en corridas futuras no se filtran al recolectar: hay que volver a correr `depurar_plantillas.py`.

**Limitaciones**: el criterio mira sólo el inicio del texto; una nota con relleno al final o con otro inicio no se detecta. Las 290 `bajada` de El Economista con `&quot;` no se tocaron.

## Entorno

El `.venv` original de `C:\Proyectos\Tesis` quedó inutilizable: su intérprete base (Python 3.10) ya no existe. Se creó **`tesis 3.0/.venv`** con Python 3.13 (spaCy, nltk, tqdm, nbconvert, ipykernel, requests, beautifulsoup4, trafilatura y el modelo `es_core_news_lg`); el kernel de Jupyter `tesis3-venv` apunta ahí. El `.venv` viejo no se tocó.
