# noticias

Scraping de noticias económicas: 7 portales (9 fuentes), **14.012 artículos** (2025-01-02 → 2026-05-03) recolectados vía Wayback Machine y sitemaps, deduplicados y depurados (ver `RESOLUCION_DUPLICADOS.md` y `DEPURACION_CALIDAD.md`).

## Contenido

- `scripts/` — 4 scripts activos + utilitarios:
  - `noticias_historico_v3.py` **(recomendado)** — checkpoint en JSONL, multihilo, fallback sitio original → Wayback. `--dias N` (default 14).
  - `noticias_diario.py` — pensado para correr periódicamente (`--dias 1` por defecto), vía sitemap.
  - `noticias_sitemap.py` — alternativa sin Wayback, solo 3 portales.
  - `diagnostico_ambito.py` — utilitario manual, corre si falla el scraping de Ámbito Financiero.
  - `dedup_utils.py` — deduplicación por URL (dentro y entre archivos), usada por los 3 scripts de arriba.
  - `env_utils.py` — loader de `.env` sin dependencias externas.
  - `dedup_semantico_qwen.py` — detección de cross-posting (duplicado con URL distinta) vía LLM local (Ollama). Incremental; los 3 scrapers lo llaman al terminar y lo omiten con un aviso si Ollama / el modelo no están disponibles.
  - `calidad_utils.py` — controles de calidad compartidos: patrón de URL de artículo por fuente, detección de paywall, filtro por fecha de publicación, parseo de JSON-LD tolerante a caracteres de control.
  - `depurar_corpus.py` — depuración única del corpus ya recolectado (`--aplicar` elimina y escribe el reporte en `analisis_calidad/`).
  - `depurar_plantillas.py` — elimina contenido repetido por plantilla (cuerpo de relleno, notas republicadas); reporte en `analisis_calidad/depuracion_plantillas_<fecha>.json`.
  - `recuperar_metadatos.py` — vuelve a bajar los artículos sin fecha/autor y completa los campos que faltan.
- `resultados/` — el corpus: un `.json` + `.jsonl` por fuente (9 fuentes, 7 portales).
- `analisis_duplicados/` — reporte acumulado del dedup semántico (`reporte_dedup_semantico.json`: veredictos + URLs descartadas).
- `analisis_calidad/` — reporte de la depuración (`depuracion_<fecha>.json`: cada URL eliminada y su motivo).
- `.env` / `.env.example` — credenciales de Internet Archive (no versionar `.env`).
- `AUDITORIA_CORPUS.md` — diagnóstico original (duplicados, credenciales hardcodeadas, calidad de datos).
- `RESOLUCION_DUPLICADOS.md` — qué se corrigió y cómo (duplicados).
- `DEPURACION_CALIDAD.md` — causa raíz del bug de JSON-LD, páginas índice, paywall, fechas fuera de ventana, dedup semántico automatizado, y lo que sigue sin resolver.
- `SECCION_TESIS.md` — borrador en prosa para la tesina, listo para copiar/adaptar.

`noticias_historico.py` y `noticias_historico_v2.py` (versiones obsoletas, reemplazadas por v3) no se trajeron a esta copia — siguen existiendo en `tesis version 2.0/` si hace falta consultarlas.

## Cómo correrlo

Los scripts escriben en `../resultados` (relativo a `scripts/`, no al directorio de trabajo). Pararse en `scripts/` y correr, por ejemplo:

```bash
python noticias_diario.py --dias 1
```

Antes de la primera corrida: copiar `.env.example` a `.env` (en `noticias/`, un nivel arriba de `scripts/`) y completar las credenciales de Internet Archive, o dejarlo vacío — corre igual, con menos rate limit.

## Nota

Estos scripts hacen requests en vivo (Wayback Machine / sitios) — no son 100% reproducibles bit a bit (el corpus crece con el tiempo). `resultados/` acá es el corpus tal como quedó después de la limpieza de duplicados documentada en `RESOLUCION_DUPLICADOS.md`.
