# ner_entidades

Reconocimiento de entidades nombradas (NER) híbrido sobre el corpus de noticias: spaCy `es_core_news_lg` (PER/ORG/LOC/MISC) + gazetteer propio (indicadores económicos + empresas Merval).

**Estado: paso 3 completo.** `resultados_ner/` refleja el corpus depurado de `../noticias/` (14.012 artículos) con canonicalización de empresas, filtrado de ruido y gazetteer auditado contra falsos positivos.

## Qué se hizo

### Paso 1 — Ampliación del panel

- `ner_analisis.ipynb` copiado desde `tesis version 2.0/analisis_complementarios/ner_entidades/` (que queda intacta).
- Ruta de entrada actualizada a la estructura plana de `tesis 3.0` (`../noticias/resultados`), la misma de `tesis 4.0`, que es hoy la base vigente: la 3.0 quedó corrompida por una copia masiva desde la 2.0.
- **Panel de empresas Merval ampliado de 20 a 47 tickers**, con la lista provista por el usuario (2 pasadas — la segunda agregó `RIGO.BA` Rigolleau), organizada por sector.

### Paso 2 — Canonicalización, filtrado de ruido y re-corrida

- **Canonicalización**: el gazetteer de Merval pasó de listas planas de alias a `{ticker, sector, aliases}` por empresa. El NER ahora emite el **ticker** como entidad (`GGAL`, no "Banco Galicia"/"Grupo Financiero Galicia"/"GGAL" por separado) y el **sector** como subtipo — resuelve la fragmentación de entidades del hallazgo original.
- **Alias ambiguo excluido** del matching por texto libre: "San Miguel" (SAMI) colisiona con topónimos — el ticker sigue funcionando si aparece literal en el texto, pero no el nombre genérico.
- **Filtrado de ruido de spaCy** (el gazetteer no se toca, se confía en él aunque una entidad aparezca una sola vez):
  - **Relleno de Clarín y autorreferencias (2026-10-18):** el bloque "Sobre la firma / Mirá también / Newsletter Clarín" que cierra casi todas las notas de Clarín aparecía como entidad ("newsletter clarín" en 2.134 artículos, "mirá" en 1.004), y el nombre de cada medio aparecía en sus propias notas ("iprofesional" en 1.062 artículos de iProfesional, "clarín" en 560 de Clarín). Se agregaron "newsletter" y "mira" a la blocklist por palabra, y una regla que descarta el nombre del medio **solo en las notas de ese mismo medio** (`AUTORREFERENCIAS`). Si otro medio lo cita, se conserva. Para La Nación se descarta solo la marca sin tilde, "la nacion", porque "la Nación" con tilde puede ser el Estado nacional. Salieron 15 entidades, todas relleno o autorreferencias; empresas e indicadores no cambian.
  - Blocklist por palabra (no match exacto) — "PUBLICIDAD" aparecía pegada a otras palabras en el texto scrapeado ("publicidad a", "bloomberg publicidad") por contaminación de contenido publicitario; un blocklist de match exacto no alcanzaba a cazar esas variantes.
  - Heurística de forma válida — rechaza fragmentos de solo números/símbolos (`"75%/4%"`) o de más de 6 palabras (fragmentos de oración, no entidades).
  - Frecuencia mínima de 2 artículos distintos, solo para entidades de spaCy.
  - Reconciliación de tipo: cuando spaCy etiquetó la misma cadena como LOC en un artículo y ORG en otro, se unifica al tipo con más menciones totales.
- **Rendimiento**: el loop original llamaba `nlp(oracion)` una por una; se restructuró para juntar todas las oraciones del corpus y mandarlas juntas a `nlp.pipe(..., batch_size=500)` — ~1,5x más rápido. Se probó también multiproceso (`n_process=4` y `8`): **más lento**, no más rápido — con oraciones cortas y un modelo no-transformer, el overhead de IPC entre procesos supera la ganancia. Se agregó barra de progreso (`tqdm`) a las dos fases del loop.

### Paso 3 — Auditoría del gazetteer y re-corrida sobre el corpus depurado

- **Corpus**: 14.012 artículos (antes 14.449, que arrastraba una inconsistencia `.json`/`.jsonl`; la depuración de calidad eliminó 17 y la de plantillas 419; ver `../noticias/DEPURACION_CALIDAD.md`).
- **Falso positivo de `AGRO`**: el alias `AGRO` matcheaba la palabra común "agro" en 920 artículos. Ahora `AGRO.BA` (**Agrometal S.A.I.**, no "AgroIndustria") tiene solo el alias "Agrometal" y aparece en 2 artículos. Fuentes: [Simply Wall St](https://simplywall.st/stocks/ar/capital-goods/base-agro/agrometali-shares/information), [Snowball](https://snowball-analytics.com/public/asset/AGRO.BA.ARS), [EODHD](https://eodhd.com/financial-summary/AGRO.BA).
- **Alias en MAYÚSCULAS case-sensitive**: tickers y siglas (`LOMA`, `COME`, `LONG`, `SEMI`…) se buscan respetando mayúsculas, porque en minúscula son palabras comunes. Excepción: `IRSA` y `BYMA`, que el texto escribe como nombre propio.
- **Alias genéricos eliminados**: "Hipotecario", "Celulosa", "Molinos", "Capex" (crédito hipotecario, molinos harineros, gasto de capital).
- **Sin doble conteo**: las entidades de spaCy cuyo texto coincide con un término del gazetteer se descartan en el post-procesamiento.
- **Conciliación con la lista vigente de 47 tickers** — sectores corregidos: COME y CRES → Conglomerado, AGRO y OEST → Industrial, GCDI → Real Estate, BOLT → Tecnología. Alias corregidos: OEST era "Petrolera del Conosur" (otra empresa) → Grupo Concesionario del Oeste; SEMI era "Semillas Selectas" → Molinos Juan Semino; GCDI suma "TGLT" (nombre anterior); GBAN suma "Naturgy BAN".

### Paso 4 — Cruce NER × sentimiento

`cruce_ner_sentimiento.py` une `resultados_ner/ner_oraciones.csv` con el sentimiento FinBETO por oración (`../sentimiento_finbert/beto_oraciones_finetuned.csv`, 177 MB, copiado sin cambios de `tesis version 2.0/analisis_complementarios/finetuning_evaluacion/` el 2026-10-18; el script lo usa por defecto). Se une por `(url, oración)` **y se exige que el texto coincida**. Cobertura: **243.265 de 244.809 oraciones con entidades (99,37%)**; 1.466 tienen texto distinto (distinta segmentación) y 78 no tienen sentimiento, y se descartan.

- No se usó el baseline sin fine-tuning (`baseline_beto_sin_finetuning/`), como hacía la celda original del notebook: su índice de oración (`or_idx`) no incluye el título y queda **corrido en 1** respecto de este NER, así que el cruce habría asignado a cada entidad el sentimiento de la oración vecina.
- **Indicadores unificados (2026-10-18):** el gazetteer de indicadores no estaba canonicalizado, de modo que sinónimos como "ccl" y "contado con liquidacion" salían como dos indicadores. `equivalencias_indicadores.py` une 24 variantes en su nombre más frecuente (por ejemplo, "contado con liquidacion" y "contado con liqui" → "ccl"; "pib" y "producto bruto interno" → "pbi"; "indice de precios al consumidor" → "ipc"; "dolar bolsa" → "dolar mep"), y el cruce lo aplica antes de contar. Una oración que menciona dos variantes cuenta una sola vez: antes se contaba doble (por ejemplo, 899 oraciones con "contado con liquidación (CCL)"). Indicadores con al menos 5 oraciones: 153 → 130. No se unen términos relacionados pero distintos, como la inflación mensual, anual e interanual; la lista completa está en el encabezado del script. Las salidas del notebook (`ner_articulos.csv`, `ner_oraciones.csv`, `ner_resumen.csv`) conservan los términos originales.
- Salidas en `resultados_ner/`: `ner_sentimiento.csv` (una fila por entidad con al menos 5 oraciones: 7.570), `ner_sentimiento_diario.csv` (22.513 filas fecha × entidad, solo `EMP_MERVAL` e `IND_ECO`, pensado para unir con precios) y `ner_sentimiento_reporte.json`.
- `sent_neto = (n_pos − n_neg) / n_oraciones × 100` sobre las 4 clases (POS, NEG, NEU, MIXTO), la misma definición del `sent_neto` por artículo de la serie diaria.
- Ejemplos (sent_neto): GGAL +28,9, BMA +25,0, YPFD +17,4, BBAR +11,3, SUPV +1,4, EDN +0,9; inflación +1,9, tipo de cambio −3,6, riesgo país +10,8; Milei −7,5, Trump −12,6, Congreso −14,9.

## Resultado final

| | Antes (corpus sin deduplicar, sin filtrar) | Después |
|---|---:|---:|
| Artículos procesados | 14.667 | 14.012 (14.005 con al menos una entidad) |
| Entidades únicas totales | 65.352 | **17.894** (-73%) |
| "PUBLICIDAD" como entidad | #1, 2.258 menciones | 0 |
| Relleno de Clarín ("newsletter clarín", "mirá") y autorreferencias ("iprofesional") | 2.134, 1.004 y 1.062 artículos | 0 |
| Empresas Merval en el gazetteer | 20 (fragmentadas en variantes) | 47 (canonicalizadas por ticker) |
| Tickers Merval con menciones reales | — | 44 de 47 (sin menciones: `CAPX`, `FIPL`, `LONG`; verificado con búsqueda directa en el texto) |
| Falso positivo `AGRO` (palabra "agro") | 920 artículos | 0 (Agrometal: 2 artículos) |
| Filas `ner_articulos.csv` | ~395.000 (sin filtrar) | 312.785 |
| Filas `ner_oraciones.csv` | ~581.000 (sin filtrar) | 486.450 |
| Tiempo de corrida (spaCy) | ~44 min (loop sin batch) | ~25 min (batch) |

Tickers con más artículos: YPFD (1.040), BBAR (687), SUPV (634), EDN (461), GGAL (421), BMA (408), CEPU (363), TGSU2 (360), PAMP (349), IRSA (302).

## Pendiente / limitaciones conocidas

- **Entidades HTML en títulos**: resuelto. Los 435 títulos con `&quot;` y similares se decodificaron (`html.unescape`) en el corpus y en los scrapers antes de la última corrida; las entidades que contienen `&` hoy son legítimas (S&P, C&T, H&M).
- **"Galicia" como LOC**: spaCy etiqueta "Galicia" como lugar en 422 artículos y solo 111 comparten artículo con el ticker `GGAL`; el resto es la región o texto parcial. No se tocó.
- **El sentimiento es por oración, no hacia la entidad.** Una oración con "inflación" y sentimiento positivo suele describir una baja de la inflación; y las notas de cotización ("dólar blue", CCL) son mayormente neutras, por lo que su `sent_neto` ronda 0. Es una medida de tono del contexto, no de opinión sobre la entidad.
- `beto_oraciones_finetuned.csv` corresponde al corpus anterior a la depuración: cubre las 14.012 URLs actuales, pero incluye también oraciones de artículos ya eliminados (no afectan: el cruce parte de `ner_oraciones.csv`).
- No se auditó la calidad de las entidades PER/ORG/LOC/MISC que sí pasaron el filtro (ej. "gobierno" como LOC es discutible) — el objetivo de esta pasada fue eliminar el ruido evidente (fragmentos, contaminación), no lograr NER perfecto.

## Requisitos para correr

```bash
pip install spacy nltk pandas tqdm jupyter nbconvert ipykernel
python -m spacy download es_core_news_lg
python -m nltk.downloader punkt punkt_tab
python -m ipykernel install --user --name tesis4-venv --display-name "Tesis 4.0 venv"
```

Para correr el notebook completo (~25 min) sin abrir Jupyter:

```bash
jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=tesis4-venv --ExecutePreprocessor.timeout=3600 ner_analisis.ipynb
```

## Input

Corpus depurado de `../noticias/resultados/` (9 fuentes, 14.012 artículos — ver `../noticias/RESOLUCION_DUPLICADOS.md` y `../noticias/DEPURACION_CALIDAD.md`). Opcionalmente `../baseline_beto_sin_finetuning/beto_oraciones.csv` para la celda de cruce con sentimiento (todavía no curada en `tesis 3.0`).
