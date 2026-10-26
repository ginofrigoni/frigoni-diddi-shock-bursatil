# Recolección del corpus de noticias

> Borrador para la sección de Comprensión de los Datos (CRISP-DM, fase 02) de la tesina. Redactado en tono de tesis — copiar/adaptar directamente al documento final.

## 1. Fuentes y métodos de recolección

El corpus de noticias económicas se construyó a partir de **siete portales** de prensa económica argentina, combinando **dos métodos de recolección** según la disponibilidad de cada fuente:

- **Vía Wayback Machine (Internet Archive)**: se consultó la CDX API de Internet Archive para obtener snapshots históricos de cada portal dentro de la categoría de economía, y se descargó el HTML archivado de cada artículo. Este método permite reconstruir una ventana histórica más amplia que la que exponen los propios sitios, a costa de depender de la cobertura y disponibilidad de snapshots de un tercero.
- **Vía sitemap XML directo**: se recorrió el sitemap XML publicado por el propio sitio (`sitemap.xml` / `sitemap-news.xml`) y se descargó el HTML directamente del portal en vivo. Este método es más simple y no depende de un tercero, pero está limitado a la ventana de retención del sitemap del sitio (habitualmente días o semanas para sitemaps de noticias).

En ambos casos, la extracción del contenido de cada artículo siguió la misma estrategia en capas: metadatos estructurados (JSON-LD) como fuente principal, con reintentos sucesivos vía metaetiquetas Open Graph, el encabezado `<h1>`, la librería `trafilatura` y, como último recurso, heurísticas sobre el HTML con BeautifulSoup.

Un mismo portal (Clarín) se cubrió con ambos métodos: la ventana histórica más profunda vía Wayback Machine, y las notas más recientes/no cubiertas por Wayback vía sitemap directo — con el consecuente riesgo de duplicación entre ambas fuentes, tratado en la sección 3.

## 2. Corpus resultante

| Portal | Método | Artículos |
|---|---|---:|
| Ámbito Financiero — sección Economía | Wayback Machine | 498 |
| Ámbito Financiero — sección Finanzas | Wayback Machine | 240 |
| Clarín — sección Economía | Wayback Machine | 294 |
| Clarín | Sitemap directo | 3.737 |
| El Economista | Sitemap directo | 2.695 |
| iProfesional | Sitemap directo | 5.455 |
| La Nación — sección Economía | Wayback Machine | 491 |
| TN — sección Economía | Wayback Machine | 102 |
| Infobae — sección Economía | Wayback Machine | 500 |
| **Total** | | **14.012** |

El corpus final abarca aproximadamente 63 millones de caracteres de contenido (~4.500 caracteres promedio por artículo), con fechas de publicación entre enero de 2025 y mayo de 2026. En la práctica, el corpus comienza en mayo de 2025: 14.001 de los 14.012 artículos (99,9%) son del 1 de mayo de 2025 en adelante, y los 11 anteriores (10 de Clarín y 1 de Ámbito) no alcanzan para cubrir enero a abril. No se investigó la causa; es probable que se deba a la ventana de retención de los mapas del sitio y a la cobertura de capturas de Wayback Machine, ambas concentradas en los meses más recientes.

## 3. Problemas detectados y soluciones implementadas

### 3.1 Duplicación exacta entre métodos de recolección

Al cubrir un mismo portal (Clarín) con dos métodos de recolección independientes, se detectó que **205 artículos** habían sido descargados dos veces: una vez vía Wayback Machine y otra vez vía sitemap directo, con idéntica URL de origen en ambos casos. Esta duplicación no fue advertida por ninguno de los dos scripts de recolección, ya que cada uno solo verificaba su propio historial de descargas antes de procesar una URL, sin considerar lo ya descargado por otras fuentes.

**Solución implementada**: se desarrolló una rutina de deduplicación por URL que compara el contenido de todas las fuentes entre sí y conserva una única copia por artículo (priorizando la versión obtenida directamente del sitio por sobre la versión archivada). Adicionalmente, se modificó la lógica de los tres scripts de recolección activos para que, antes de descargar un artículo, verifiquen su URL contra el conjunto de artículos ya recolectados por **cualquier** fuente — no solo la propia —, previniendo la reaparición de este tipo de duplicación en corridas futuras.

### 3.2 Duplicación semántica (publicación cruzada de una misma nota)

Un segundo tipo de duplicación, más difícil de detectar, corresponde a notas que un mismo portal publica dos veces bajo URLs distintas — típicamente al distribuir una misma noticia en dos secciones del sitio (por ejemplo, "Economía" y "Finanzas") con minutos de diferencia. Un criterio de detección basado únicamente en el título del artículo resultó insuficiente: varios portales publican columnas recurrentes con título idéntico o casi idéntico en cada edición (por ejemplo, reportes diarios de cotización del dólar), que **no** constituyen una duplicación real pese a compartir título, ya que su contenido cambia día a día.

**Solución implementada**: se diseñó un procedimiento de verificación en dos etapas. Primero, los artículos se agruparon por título normalizado y, dentro de cada grupo, se identificaron subconjuntos de artículos publicados dentro de una ventana de 48 horas entre sí — los artículos del mismo título pero separados por más tiempo se descartaron automáticamente como columnas recurrentes, sin necesidad de análisis adicional. De 208 grupos de título repetido detectados, 175 se resolvieron de esta forma. Los 33 grupos restantes (68 artículos), donde la coincidencia de título y proximidad temporal sí sugería una posible republicación, se sometieron a verificación semántica mediante un modelo de lenguaje de código abierto (Qwen3, ejecutado localmente), al que se le presentó el contenido completo de cada artículo del grupo y se le solicitó un juicio explícito sobre si se trataba de la misma noticia republicada o de notas genuinamente distintas. Este procedimiento confirmó **14 casos** de publicación cruzada real (mismo contenido, minutos de diferencia, identificadores de artículo consecutivos), y descartó correctamente los 19 casos restantes como coincidencias de título sobre contenido distinto — incluyendo, en varios casos, la misma fecha y tema cubiertos por dos medios distintos con enfoques diferentes. El procedimiento es **incremental** y quedó integrado al final de cada corrida de recolección: conserva los veredictos previos, de modo que solo consulta al modelo los grupos nuevos, y registra las URLs descartadas para que los scrapers no las vuelvan a descargar; si el modelo local no está disponible, el paso se omite con un aviso sin interrumpir la recolección.

### 3.3 Metadatos faltantes por un error de parseo del extractor

Dos fuentes presentaban metadatos sistemáticamente incompletos: el 100% de los artículos de **iProfesional** carecía de autor, palabras clave y fecha de modificación, y el 6,4% de los de **El Economista** (194 artículos) carecía de fecha de publicación, autor y palabras clave. Una primera lectura atribuyó el caso de iProfesional a una limitación del sitio; la inspección del HTML mostró que **era un error del extractor**: ambos sitios publican los metadatos como JSON-LD (datos estructurados embebidos en la página), pero el bloque contiene caracteres de control sin escapar dentro de cadenas de texto, y el parseo estricto de JSON fallaba. El extractor capturaba la excepción sin registrarla y continuaba con fuentes alternativas menos completas, de modo que el fallo pasaba inadvertido.

**Solución implementada**: se pasó a un parseo tolerante a esos caracteres en los tres scripts de recolección, y se volvieron a descargar los 192 artículos reales de El Economista que habían quedado sin fecha (los otros dos casos eran páginas de índice, ver 3.4), recuperando el 100% de las fechas de publicación. En iProfesional las fechas no estaban afectadas (provienen del mapa del sitio, que informa la fecha de publicación), y no se re-extrajeron autor ni palabras clave por no utilizarse en el análisis; las corridas nuevas sí los incorporan.

### 3.4 Contenido que no es una noticia dentro de la ventana de estudio

Una depuración final eliminó 17 registros que no correspondían a artículos del período analizado:

- **2 páginas índice de sección** de El Economista, que el filtro de categoría por URL dejaba pasar. Los recolectores ahora exigen, además de la categoría, una forma de URL propia de artículo, validada contra el corpus existente.
- **9 páginas de acceso por suscripción** de La Nación: el sitio devolvía un texto de invitación a suscribirse (527 caracteres idénticos) en lugar de la nota. Se descartan al recolectar.
- **6 notas fuera de la ventana temporal**: el mapa del sitio informa la fecha de *última modificación*, no la de publicación, por lo que notas antiguas reeditadas (publicadas en 2014 y 2024) ingresaban como si fueran recientes; en un caso, el propio sitio había vuelto a fechar una nota antigua con posterioridad a la recolección. Los recolectores ahora filtran por la fecha de publicación efectiva.

El efecto no era menor: una sola nota de 2014 extendía el rango de la serie diaria de sentimiento a 4.186 días, de los cuales solo 381 tenían datos; tras la depuración la serie abarca 487 días (377 con datos).

### 3.5 Contenido repetido por plantilla

La última auditoría detectó que parte del corpus no son noticias distintas sino **plantillas**: notas con fecha y título propios cuyo cuerpo es un texto fijo. Se agrupó a los artículos de una misma fuente por sus primeros 160 caracteres normalizados y se encontraron 65 grupos (479 artículos). Dos tipos de casos:

- **Cuerpo de relleno invariable.** Cuatro plantillas de El Economista concentran 325 notas: el reporte diario "Dólar hoy" (147 notas con el esquema cambiario sin cepo y 71 con el de bandas) y dos versiones de la nota sobre Pix para argentinos que viajan a Brasil (76 y 31 notas). Cada nota tiene fecha y cotizaciones propias, pero el modelo de sentimiento les asigna siempre el mismo valor (0,0; 18,2; 52,2 y 63,6 de sentimiento neto, respectivamente, con desvío cero), es decir, el valor depende de la parte fija del texto y no de la información del día. Un quinto grupo de 11 notas de El Economista es un **error de extracción**: el extractor tomó un bloque de navegación ("últimas noticias…") de 555 caracteres en lugar de la nota.
- **Notas republicadas.** Los 60 grupos restantes (2 a 7 notas) corresponden a la misma nota reeditada en otra fecha, promociones recurrentes o textos de agencia.

**Criterio adoptado**: en los grupos de menos de 11 notas se conserva la más antigua y se eliminan las demás (83 notas); en los de 11 o más, cuyo cuerpo es relleno, se eliminan todas (336 notas). En total se eliminaron **419 artículos (2,9%)**, 356 de ellos de El Economista; el corpus pasó de 14.431 a **14.012**. Se prefirió eliminar a conservar con una marca porque estas notas aportan un valor de sentimiento constante que no refleja información, y ese valor, replicado durante meses (las notas de Pix, por ejemplo, de julio de 2025 a febrero de 2026), sesga hacia arriba el promedio diario.

**Efecto sobre la serie**: los días con datos se mantienen (377 de 487), y los shocks pasan de 35 (17 positivos y 18 negativos) a **33** (15 positivos y 18 negativos). La mayoría de los shocks previos se apoyaba poco en estas notas (típicamente entre 0% y 10% de los artículos del día, con un máximo de 20%). La depuración queda registrada con cada URL eliminada y su motivo, y los recolectores no vuelven a descargarlas.

### 3.6 Reproducibilidad y gestión de credenciales

El acceso autenticado a la API de Internet Archive (necesario para obtener un límite de tasa de consulta más alto) dependía de credenciales incluidas directamente en el código fuente del script de recolección. Se migraron a un archivo de configuración externo no versionado, desacoplando las credenciales del código y evitando su exposición en copias o distribuciones del proyecto.

## 4. Limitaciones conocidas

- **Plantillas.** El criterio de agrupación (primeros 160 caracteres) sólo detecta repeticiones al inicio del texto: una nota con relleno fijo en el medio o al final, o con un inicio distinto, no se detecta. Las notas diarias "Dólar hoy" eliminadas son informativas en principio (traen la cotización del día); se descartaron porque el valor de sentimiento constante que reciben (desvío cero entre decenas de notas con cotizaciones distintas) indica que el modelo responde a la parte fija del texto y no a la cotización. Corridas futuras de recolección pueden volver a traer plantillas: `depurar_plantillas.py` es idempotente y se puede volver a correr.
- En 290 notas de El Economista el campo `bajada` conserva entidades HTML (`&quot;`); no se utiliza en el análisis.
- De iProfesional no se recuperaron autor, palabras clave ni fecha de modificación del corpus ya recolectado.
- **Hueco de recolección en iProfesional en abril de 2026:** el portal tiene 3 notas ese mes, contra unas 500 en cada uno de los anteriores. Como aporta el 39% del corpus, abril de 2026 tiene menos cobertura y otra composición por fuente; los análisis que usen ese mes deben tenerlo en cuenta.
- **Marcas horarias heterogéneas:** tres fuentes informan la hora de publicación en UTC y el resto en hora argentina, y varias usan horas por defecto (por ejemplo, 07:00 en una de cada cinco notas de Clarín por mapa del sitio). Al tomar la fecha calendario sin convertir de huso horario, 95 notas (0,7%) quedan asignadas al día siguiente.
- El dedup semántico requiere que el modelo local esté disponible; si no lo está, queda pendiente hasta la próxima corrida.
- La serie diaria de sentimiento cambió respecto de la versión previa (36 shocks en la versión vigente, armada desde la clasificación por oración sin relleno; 33 tras la depuración de plantillas; 35 antes de ella y 33 en la serie original de tesis 2.0); los resultados econométricos calculados sobre la serie anterior deben regenerarse si se adopta esta versión del corpus.
