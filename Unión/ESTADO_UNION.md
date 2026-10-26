# Estado de la unión

Actualizado: 24/10/2026

## Decisiones tomadas

- **Ventana:** 05/05/2025 → 30/04/2026 (244 ruedas).
- **Regla de las 17:00:** una nota publicada después del cierre, o en un día sin mercado, cuenta para la rueda siguiente.
- **HMM:** se usa tal cual está, sin reentrenar.
- **Moderado:** el VAR por régimen compara Calmo contra Tenso.
- **Sentimiento:** queda congelado. Los datos actuales de Gino son los finales.
- **Variables:** se analizan precio y volumen, con tono, cantidad de notas y menciones por empresa.
- **Sentimiento propio:** solo para las 17 empresas con al menos 90 ruedas con noticias (el corte bajó de 95 a 90 para que entre ALUA, que tiene 94 exactas). Las demás usan el sentimiento general.
- **Shocks:** son las "ruedas de tono extremo" (opción A).
- **Tono en el VAR:** se usa el tono anormal, que es el tono comparado con las 20 ruedas previas. El tono en nivel queda como prueba de robustez.
- **Tono propio de cada empresa:** es cuánto mejor o peor se habla de ella que del mercado, ponderado por la cantidad de oraciones (con 1 oración pesa el 8%; con 10, el 48%). Si no hay noticias de la empresa, vale 0.

## Resultado principal (U6)

- **Mercado → noticias:**
  - cuando el Merval sube, el tono de las noticias de las 2 ruedas siguientes es más positivo;
  - pasa en 39 de las 47 empresas y en 9 de los 10 sectores;
  - en **15 de las 17** empresas con tono propio, después de que la acción sube se habla de ella mejor que del resto del mercado.
- **Noticias → mercado:** no aparece nada consistente en el mercado, las empresas, los sectores ni los regímenes.
- **Cuándo lo siguen (U8):**
  - el efecto está en las notas publicadas entre las 17 y las 24 h del día del retorno: un desvío del retorno sube su tono +4,8 puntos;
  - a la mañana siguiente ya no queda;
  - el resultado "noticias → mercado" no aparece en ninguna variante.
- **Prueba más directa (U6b):**
  - el tono de las notas publicadas con el mercado cerrado no anticipa la apertura a un nivel significativo;
  - los días electorales sí se reflejan en la apertura, pero lo que mueve al mercado es la elección y no el tono de los medios.
- **Event study (U7):**
  - en las ruedas de tono extremo positivo, el Merval sube +2,0% ese día (7 de 7 eventos) y ya venía subiendo +3,2% en las 3 ruedas previas; después no pasa nada;
  - cuando se habla de una empresa de forma muy positiva, su acción ya había subido +1,2% más que el mercado en las 3 ruedas previas;
  - los días electorales se excluyeron, porque contaminaban la comparación.
- **Fuera del análisis:** dólares y DLM quedan como trabajo futuro, Twitter queda documentado sin usarse y el HMM por sector no se rehace.

## Hecho ✅

| Paso | Qué | Resultado |
|---|---|---|
| 00 | Pipeline, diagnóstico e inventario 2.0 → 3.0 | PDF del pipeline |
| U1 | Cada noticia a su rueda | 13.925 notas en 244 ruedas · 10/10 controles |
| U2 | Tono, atención y shocks por rueda | 19 ruedas de tono extremo · 7/7 controles |
| U3 | Sentimiento por empresa por rueda | Panel de 47 × 244 · 17 empresas con sentimiento propio · 7/7 controles |
| U4 | Datasets finales + diccionario de variables | dataset_mercado (244 × 29) y dataset_panel (11.468 × 37) · 8/8 controles |
| U5 | ADF + KPSS en las 244 ruedas | 156 series · el tono del VAR es el **tono anormal** (el tono en nivel dio inconcluso) · 5/5 controles |
| U6 | VAR + Granger + IRF (precio y volumen) | **El mercado anticipa a las noticias, no al revés** · 304 tests + 12 por régimen · 6/6 controles |
| U6b | Notas publicadas con el mercado cerrado → apertura (regla fijada antes de ver los resultados) | El signo va a favor de la hipótesis, pero **no es significativo** (p ≈ 0,1) y se apoya en los días electorales · 6/6 controles |
| U7 | Event study: ruedas de tono extremo del mercado y de cada empresa | El precio y el volumen se mueven **antes o junto** con las noticias extremas, no después · 5/5 controles |
| U7b | Shock de cantidad de noticias como lo define el plan (z > 2 contra 30 ruedas, por día de calendario; regla fijada de antemano, con un cambio posterior documentado) | Empresas: **se operan más el día del shock** (p corregido 0,017), sin dirección en el precio; contando solo las notas de la noche, la apertura no se mueve más. Mercado: nada (el salto de apertura depende del 24/09, el anuncio del Tesoro de EE. UU.) · 7/7 controles |
| U8 | Robustez: 12 variantes, una decisión por vez | 93 de 106 comparaciones se mantienen; el efecto "mercado → noticias" está en las **notas de la misma noche, después del cierre** · 5/5 controles |
| U9 | Entrega final | Documento final, mapa de la tesis, README y `correr_todo.py`: 64 de 64 archivos idénticos y 66 de 66 controles |
| 10 | Papers relacionados (`10_papers_union`) | 29 PDF agrupados por prueba (U1 a U8), en español, inglés y portugués, más 11 clásicos citados · referencias en `.md`, `.bib` y PDF de 7 páginas |
| — | Correcciones de la revisión general (24/10) | Plan de trabajo v3 corregido (`09_entrega_final/Plan_de_Trabajo_v3.pdf`), PDF del pipeline sin referencias a otras versiones, documento final con las carpetas 10 y 11, y Rabiner (1989) y Yang et al. (2024) en la bibliografía |
| 11 | Papers del lado de noticias (`11_papers_lado_noticias`) | 23 PDF sobre recolección del corpus, FinBETO y NER, más 8 citados · referencias en `.md`, `.bib` y PDF de 6 páginas · está en Unión para no tocar `Lado Noticias` |

## Falta ⏳

| Qué | Estado |
|---|---|
| Documento de la tesina | Versión final en `Informe Final/Informe_Final_NicolasDiddi-GinoFrigoni.pdf` (46 págs.). Falta completar la fecha de la portada |
| Presentación con los resultados | Falta definir el formato |
| Papers de PeerJ (Pan et al. 2023) e IEEE Access (García-Díaz et al. 2023) | De acceso abierto, pero hay que bajarlos a mano (bloquean la descarga automática) |
| Disertación de la UFPB (Brasil) | No se pudo bajar porque el servidor estaba caído (error 502); el link está en `10_papers_union/referencias_papers.md` |

## Pendiente con Gino

- Qué nombre lleva la carpeta: "tesis 3.0" o "tesis 4.0".
- Mandarle `00_pipeline_union/mensaje_para_gino_2.md`.
- Avisarle que tiene papers de su lado en `Unión/11_papers_lado_noticias/`, por si los quiere copiar a su carpeta.
- Avisarle que su borrador de NER (`ner_entidades/SECCION_TESIS.md`) dice que el NER "no alimenta `dataset_unificado.csv`", pero ahora U3 usa su cruce entidad-sentimiento para el tono de cada empresa.
