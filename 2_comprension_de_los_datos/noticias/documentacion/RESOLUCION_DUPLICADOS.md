# Resolución de duplicados — noticias

Fecha: 2026-09-13
Continúa: [AUDITORIA_CORPUS.md](AUDITORIA_CORPUS.md) (hallazgos 4.1, 4.2, 5.1)
Esta vez sí se modificó código y datos — todo lo de abajo vive en `tesis 3.0/`, la copia en `tesis version 2.0/` queda intacta.

> **Nota (2026-10-18):** este documento se escribió cuando la carpeta de trabajo era `tesis 3.0`. Esa carpeta quedó corrompida por una copia masiva desde la 2.0, y la base vigente es `tesis 4.0`, que contiene estos mismos archivos revisados. Las menciones a `tesis 3.0` describen dónde estaba el trabajo en ese momento.

## Qué se hizo

### 1. Deduplicación exacta por URL (hallazgo 4.1)

`dedup_utils.py` (nuevo) → función `deduplicar_entre_archivos()`. Compara los 9 `.jsonl` de `resultados/` y, cuando la misma URL aparece en más de uno, se queda con la copia del archivo "directo" (sitemap.py) y borra la del archivo vía Wayback (`noticias_historico_v3.py`), por orden de prioridad `clarin_sitemap → eleconomista_sitemap → iprofesional_sitemap → resto`.

Resultado: **`clarin_economia.jsonl`: 500 → 295** (205 duplicados exactos eliminados). Ningún otro archivo tenía overlap exacto de URL.

### 2. Deduplicación semántica (hallazgo 4.2) — con Qwen local

Un simple match de título no alcanza: hay columnas recurrentes con título idéntico semana a semana ("¿cuánto paga esta billetera hoy?", "dólar hoy: a cuánto cotiza este viernes...") que **no** son duplicados, tienen contenido distinto cada vez.

`dedup_semantico_qwen.py` (nuevo) resuelve esto en dos pasos:

1. Agrupa por título normalizado, y dentro de cada grupo arma sub-clusters de artículos publicados a **menos de 48hs** de diferencia. Los que están más separados en el tiempo se descartan automáticamente como "feature recurrente" — **sin gastar una sola consulta al modelo**.
   - De 208 grupos con título repetido, **175 se descartaron así** (recurrentes, no duplicados).
2. Los **33 grupos candidatos restantes** (68 artículos) se mandan a `qwen3.8` corriendo local vía Ollama (RTX 3090), con el contenido de cada artículo, pidiéndole que juzgue si es la misma nota republicada o no.

Resultado: **14 de los 33 grupos** confirmados como duplicado real (mismo contenido, minutos de diferencia, IDs de artículo consecutivos, cross-posteado a dos secciones del mismo sitio). Los otros 19 eran genuinamente distintos (mismo tema del día, dos medios distintos, o la misma columna en una fecha diferente) — el modelo explicó cada decisión, ver `analisis_duplicados/reporte_dedup_semantico.json` para el detalle completo (los 33 veredictos con su razón).

Ejemplo de falso positivo bien descartado por el modelo: dos notas tituladas "dólar hoy: a cuánto cotiza este viernes 31 de octubre", una de El Economista (explica el esquema cambiario) y otra de Ámbito (cotizaciones del día) — mismo título, mismo día, **contenido y enfoque completamente distintos**. Un dedup por título ciego las habría borrado por error.

### 3. Checkpoint de FinBERT y serie diaria regenerados

`checkpoint_finetuned.jsonl` (04_modeling/sentimiento_finbert/) tenía las 205 filas duplicadas exactas desde antes de esta limpieza (14.667 filas, 410 involucradas en duplicados). Se limpió con la misma lógica (exacto + semántico) y se regeneraron `finetuned_articulos.csv` y `finetuned_serie_diaria.csv` a partir del checkpoint ya limpio — **sin volver a correr el modelo** (esto es solo reagregación, no inferencia).

`serie_completa_finetuned.py` también se actualizó: `cargar_corpus()` ahora deduplica por URL y excluye los duplicados semánticos ya detectados (lee `analisis_duplicados/reporte_dedup_semantico.json`), para que un re-run desde cero no vuelva a introducir el problema.

### 4. Prevención a futuro en los 3 scrapers activos

`noticias_historico_v3.py`, `noticias_sitemap.py` y `noticias_diario.py` ahora chequean, antes de bajar una URL, contra **todos** los `.jsonl` de `resultados/` (vía `dedup_utils.cargar_urls_ya_scrapeadas()`), no solo contra su propio checkpoint. Así ningún scraper vuelve a bajar una nota que otro ya bajó hacia otro archivo.

### 5. Credenciales fuera del código

`noticias_historico_v3.py` ya no tiene `IA_S3_KEY`/`IA_S3_SECRET` hardcodeadas — las lee de `../.env` (`env_utils.py`, loader manual sin dependencias nuevas). Si `.env` no existe, el script avisa y sigue sin autenticación (rate limit más bajo, no falla). Ver `.env.example` para el formato.

### 6. Scripts obsoletos

`noticias_historico.py`, `noticias_historico_v2.py` no se copiaron a `tesis 3.0` (siguen existiendo en `tesis version 2.0`, intactos). `diagnostico_ambito.py` sí se copió, con el docstring actualizado (ya no menciona v2).

## Números finales

| | Antes | Después |
|---|---:|---:|
| Artículos totales | 14.667 | **14.448** |
| Duplicados exactos (URL) | 205 | 0 |
| Duplicados semánticos (cross-posting) | 14 (de 33 candidatos evaluados) | 0 |
| Grupos de título repetido evaluados con LLM | — | 33 |
| Grupos descartados sin consulta (features recurrentes) | — | 175 |

## Qué queda pendiente (no se tocó en esta pasada)

- **Hallazgo 4.3** (páginas de sección de El Economista coladas como artículo) — no se filtró todavía.
- **Hallazgo 4.4** (artículo de Clarín con fecha de publicación real de 2014) — sigue en el corpus. Ahora que `finetuned_serie_diaria.csv` se regeneró, este artículo determina el extremo inferior del rango de fechas de la serie: **el CSV tiene 4.186 días de rango pero solo 381 con datos reales** — casi todo ese rango es relleno vacío por culpa de este único artículo. Vale la pena resolverlo pronto si se va a usar `finetuned_serie_diaria.csv` tal cual (filtrar por fecha antes de usarlo, o excluir directamente ese artículo).
- Ampliar el límite de 500 artículos por fuente en `noticias_historico_v3.py` (no se tocó).

## Seguimiento (2026-10-10)

> Los puntos de esta lista que figuraban como pendientes se resolvieron en [DEPURACION_CALIDAD.md](DEPURACION_CALIDAD.md): el dedup semántico ya **no es un paso manual** (es incremental y los scrapers lo llaman al terminar), y los hallazgos 4.3 y 4.4 de la auditoría (páginas de sección, artículos con fecha vieja) quedaron resueltos. Los números de esta página (14.448 artículos) son los de esa fecha; el corpus actual tiene **14.431**.
