# Reconocimiento de entidades nombradas (NER) sobre el corpus de noticias

> Borrador para la sección de análisis complementarios de la tesina (este análisis no alimenta `dataset_unificado.csv` — es un resultado propio, citable por separado). Redactado en tono de tesis — copiar/adaptar directamente al documento final.

## 1. Objetivo y enfoque

Como complemento al análisis de sentimiento, se realizó un reconocimiento de entidades nombradas (Named Entity Recognition, NER) sobre el corpus completo de noticias económicas, con el objetivo de identificar qué actores (personas, organizaciones, empresas) y qué conceptos económicos concentran la cobertura periodística, y de qué manera se distribuyen en el tiempo. Este análisis no forma parte de la cadena de construcción de `dataset_unificado.csv`; se preserva como un resultado independiente, citable en la tesina sin condicionar el pipeline principal.

Se adoptó un enfoque **híbrido**, combinando dos estrategias complementarias:

- **Modelo estadístico general** (`spaCy es_core_news_lg`, en español): detecta entidades de tipo persona (PER), organización (ORG), lugar (LOC) y misceláneas (MISC) sin necesidad de una lista predefinida, a costa de una tasa de error mayor en textos informales o con formato irregular.
- **Gazetteer curado**: un diccionario de términos construido a mano para dos categorías que un modelo general no cubre de forma confiable: indicadores económicos argentinos (inflación, tipo de cambio, tasas de interés, etc.) y empresas del panel Merval, identificadas por su ticker bursátil.

## 2. Gazetteer: indicadores económicos y panel de empresas

El gazetteer de indicadores económicos agrupa 160 términos en seis categorías temáticas: macroeconomía, política monetaria, política fiscal, mercado financiero, mercado laboral y precios/pobreza. Cada término se matchea por expresión regular sobre el texto normalizado (sin tildes, insensible a mayúsculas), lo que permite capturar variantes de escritura sin necesidad de listarlas todas por separado.

El panel de empresas Merval se amplió de 20 a **47 tickers**, cubriendo los sectores Comunicaciones, Conglomerado, Consumo, Energía, Financiero, Industrial, Materiales, Real Estate y Utilities. A diferencia del gazetteer de indicadores, el de empresas está **canonicalizado**: cada alias de superficie de una misma empresa (razón social completa, nombre comercial, ticker) se resuelve a un único identificador — el ticker — en el resultado final. Esto evita que una misma empresa aparezca fragmentada en el conteo (por ejemplo, "Banco Galicia", "Grupo Financiero Galicia" y "GGAL" contando como tres entidades distintas en vez de una).

La lista de empresas se concilió con la nómina vigente del panel (razón social y sector por ticker), lo que corrigió seis sectores y tres denominaciones del gazetteer inicial; por ejemplo, `AGRO.BA` corresponde a Agrometal S.A.I. (sector Industrial), no a la "AgroIndustria" con que figuraba originalmente, y `OEST.BA` a Grupo Concesionario del Oeste.

Para limitar los falsos positivos se adoptaron tres criterios. Primero, los alias escritos en mayúsculas (tickers y siglas) se buscan respetando mayúsculas, ya que en minúscula varios coinciden con palabras comunes: sin esta regla, el alias `AGRO` coincidía con la palabra "agro" (sector agropecuario) en 920 artículos, y el único "AGRO" en mayúsculas del corpus corresponde a Adecoagro, otra sociedad. Se exceptuaron `IRSA` y `BYMA`, que el texto escribe como nombres propios. Segundo, se excluyeron alias genéricos que son expresiones comunes ("Hipotecario", "Celulosa", "Molinos", "Capex") y el nombre "San Miguel" (topónimo), de modo que el ticker `SAMI` solo se reconoce si aparece literalmente. Tercero, las entidades que el modelo estadístico detecta con el mismo texto que un término del gazetteer se descartan, para no contar dos veces una misma mención.

## 3. Problemas detectados y soluciones implementadas

### 3.1 Fragmentación de entidades sin canonicalización

En una primera corrida sobre el gazetteer original (20 empresas, sin canonicalizar), se observó que una misma empresa podía aparecer bajo más de 40 variantes de superficie distintas en el ranking de entidades — el caso más extremo, "Banco Galicia", incluía desde razones sociales completas hasta errores de formato ("Banco Galicia-"). La solución fue reestructurar el gazetteer de empresas de una lista plana de alias a una estructura `{ticker, sector, alias}` por empresa, de modo que el resultado final identifica cada mención por su ticker, no por el alias que la originó.

### 3.2 Contaminación de contenido scrapeado

Se detectó que la cadena "PUBLICIDAD" figuraba como la entidad de tipo organización más mencionada del corpus (2.258 menciones), producto de texto publicitario de relleno que quedó embebido dentro del contenido extraído de algunos artículos, sin una separación clara del texto periodístico circundante. Un filtro de exclusión exacto resultó insuficiente, porque el bloque publicitario aparecía pegado a palabras adyacentes ("publicidad a", "bloomberg publicidad"); se resolvió excluyendo cualquier entidad que contuviera la palabra como token completo, no solo como cadena exacta.

El mismo problema apareció con el bloque de firma y suscripción que cierra casi todas las notas de Clarín ("Sobre la firma", "Mirá también", "Newsletter Clarín"): "newsletter clarín" figuraba como entidad en 2.134 artículos y "mirá" en 1.004. Se trató con el mismo criterio de exclusión por palabra. Además, el nombre de cada medio aparecía como entidad en sus propias notas ("iprofesional" en 1.062 artículos de iProfesional, "clarín" en 560 de Clarín), por firmas y remisiones internas. Se descartó el nombre del medio solo dentro de sus propias notas, conservando las menciones en las que un medio cita a otro.

### 3.3 Ruido general del modelo estadístico

Sobre el corpus sin filtrar, el modelo detectó 65.352 entidades únicas, de las cuales el 67,5% aparecía en un único artículo — en su mayoría fragmentos sin valor informativo (secuencias numéricas, fragmentos de oración cortados) más que entidades reales. Se aplicaron tres criterios de limpieza, exclusivos para las entidades detectadas por el modelo estadístico (el gazetteer, al ser curado a mano, no se sometió a este filtrado):

- Forma inválida: cadenas compuestas solo por números y símbolos, o de más de seis palabras.
- Frecuencia mínima: al menos dos artículos distintos deben mencionar la entidad.
- Reconciliación de tipo: cuando la misma cadena fue etiquetada con más de un tipo (por ejemplo, persona en un artículo y organización en otro), se unificó al tipo con mayor número de menciones totales, evitando que una misma entidad quede dispersa bajo etiquetas distintas.

## 4. Resultado

| | Antes del filtrado | Después |
|---|---:|---:|
| Artículos procesados | 14.667 (corpus sin deduplicar) | 14.012 (corpus depurado; 14.005 con al menos una entidad) |
| Entidades únicas totales | 65.352 | **17.894** |
| Menciones de "PUBLICIDAD" como entidad | 2.258 (ranking #1) | 0 |
| Relleno de Clarín y autorreferencias de los medios | "newsletter clarín" en 2.134 artículos | 0 |
| Empresas del panel Merval | 20, fragmentadas en variantes | 47, canonicalizadas por ticker |
| Tickers con menciones reales en el corpus | — | 44 de 47 |
| Falsos positivos del alias `AGRO` | 920 artículos | 0 |

Los tres tickers sin menciones (`CAPX`, `FIPL`, `LONG`) se verificaron con una búsqueda directa en el texto del corpus: no aparecen ni por ticker ni por nombre. Entre las empresas, las más mencionadas son YPF (1.040 artículos), BBVA (687), Supervielle (634), Edenor (461) y Galicia (421).

Entre las entidades más mencionadas se destacan, sin sorpresas frente a la coyuntura del período cubierto: el Banco Central (BCRA), el FMI y el Tesoro entre las organizaciones; el presidente y el ministro de Economía entre las personas; inflación, tipo de cambio y dólar (oficial, blue, MEP) entre los indicadores económicos.

## 5. Cruce con el sentimiento

Para vincular las entidades con el análisis de sentimiento, se unió cada mención con el sentimiento de la oración que la contiene, obtenido con el modelo FinBETO (BETO ajustado a dominio financiero). La unión se hizo por artículo y número de oración, exigiendo además que el texto de la oración coincidiera en ambas etapas; se cruzaron así 243.265 de las 244.809 oraciones con entidades (99,37%). Se descartó el uso de la versión sin ajuste fino del modelo, porque su numeración de oraciones no incluye el título del artículo y habría asignado a cada entidad el sentimiento de la oración contigua.

Para cada entidad se calcula la proporción de oraciones positivas, negativas, neutras y mixtas, y un sentimiento neto (diferencia entre positivas y negativas, en puntos porcentuales de las oraciones), con la misma definición que el sentimiento neto por artículo de la serie diaria. Antes de agregar, los indicadores económicos se unificaron con una tabla de equivalencias. A diferencia del de empresas, el gazetteer de indicadores no estaba canonicalizado, y sinónimos como "CCL" y "contado con liquidación" figuraban como indicadores distintos. Se unieron 24 variantes en la forma más frecuente de cada indicador (por ejemplo, "PIB" y "producto bruto interno" en "PBI"), conservando separados los términos relacionados pero distintos, como la inflación mensual, anual e interanual. Una oración que menciona dos variantes del mismo indicador cuenta una sola vez. Se generaron: un resumen por entidad (7.570 entidades con al menos cinco oraciones) y una serie diaria por empresa del panel Merval e indicador económico (22.513 observaciones fecha × entidad), pensada para combinarse con los precios bursátiles. A modo ilustrativo, entre las empresas con más menciones el sentimiento neto fue de +28,9 para Galicia, +25,0 para Macro y +17,4 para YPF, frente a valores cercanos a cero para Supervielle (+1,4) y Edenor (+0,9); entre los actores políticos, negativo para Milei (−7,5), Trump (−12,6) y el Congreso (−14,9).

## 6. Limitaciones

- Los términos del gazetteer de indicadores se buscan de forma independiente, por lo que un término contenido en otro se cuenta para ambos: una oración con "inflación mensual" suma también para "inflación", y una con "índice Merval" sumaba para "índice Merval" y "Merval" (este caso quedó resuelto al unificar sinónimos). Para indicadores relacionados pero distintos, como las variantes de inflación, la superposición se mantiene.
- La clasificación sectorial proviene de la nómina del panel, no de una taxonomía externa (ICB/GICS); por ejemplo, Agrometal figura como Industrial y Cresud/Comercial del Plata como Conglomerado.
- spaCy etiqueta "Galicia" como lugar en 422 artículos, de los cuales solo 111 coinciden con menciones del ticker `GGAL`; la entidad de empresa es la canonicalizada y el lugar se mantiene como entidad aparte.
- El filtrado de ruido se aplicó únicamente sobre las entidades detectadas por el modelo estadístico (PER/ORG/LOC/MISC); no se auditó exhaustivamente la precisión de las que sí superaron el filtro (por ejemplo, "gobierno" quedó etiquetado como lugar, una clasificación discutible). El objetivo de esta etapa fue eliminar el ruido evidente, no alcanzar una precisión de NER exhaustiva.
- El sentimiento asociado a una entidad es el de las oraciones donde aparece, no una medida de opinión sobre la entidad: una oración con "inflación" y tono positivo suele describir una baja, y las notas de cotización (dólar blue, CCL) son mayormente neutras. Debe interpretarse como tono del contexto.
- Un 0,63% de las oraciones con entidades (1.544 de 244.809) quedó sin sentimiento por diferencias de segmentación u omisión entre la etapa de NER y la de sentimiento.
