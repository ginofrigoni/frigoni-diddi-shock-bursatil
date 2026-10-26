# Análisis de sentimiento

> Borrador para la tesina, en tono de tesis, para copiar o adaptar. Las cifras salen de los archivos de esta carpeta (ver `README.md`, que documenta la procedencia de cada archivo y cada paso). Lo que proviene de los cuadernos de la versión anterior del proyecto, que no están en `tesis 4.0`, se indica en el texto.

## 1. Objetivo y enfoque

El objetivo de esta etapa es asignar a cada artículo del corpus una medida de sentimiento y agregarla en una serie diaria, sobre la cual identificar los días en que el tono de la cobertura se aparta de lo habitual (shocks de sentimiento).

Para ello se adaptó al dominio un modelo de lenguaje en español. Se partió de BETO (`dccuchile/bert-base-spanish-wwm-cased`), un modelo BERT preentrenado en español, y se lo ajustó en dos pasos: continuación del preentrenamiento sobre el texto del propio corpus y ajuste fino para clasificar el sentimiento de oraciones. El modelo resultante se denomina aquí FinBETO. Se trabajó con cuatro clases —positiva (POS), negativa (NEG), neutra (NEU) y mixta (MIXTO)—, porque una parte de las oraciones de la prensa económica combina señales de ambos signos (por ejemplo, un dato de actividad que mejora mientras la inflación se acelera), y forzarlas a una sola clase habría sido arbitrario.

## 2. Construcción del conjunto etiquetado

No existe un conjunto público de oraciones de prensa económica argentina etiquetadas por sentimiento. Se construyó uno usando como etiquetador un modelo de lenguaje ejecutado localmente: Gemma (`gemma4:26b`, servido con Ollama), con temperatura 0,1.

El etiquetado se hizo en dos pasos por noticia. Primero, el modelo leyó el título, la bajada y los primeros 3.000 caracteres del artículo, y produjo un análisis de contexto con cuatro campos: tema central, encuadre, actores principales y tono general. Luego etiquetó cada oración del artículo de al menos 30 caracteres, recibiendo ese contexto como referencia. Las instrucciones indicaban que el sentimiento debía surgir de lo que la oración expresa por sí misma, y que el contexto solo debía usarse para resolver ambigüedades. Las clases se definieron así: POS, algo favorable dentro del encuadre de la noticia; NEG, algo desfavorable; NEU, descriptiva y sin carga valorativa (datos, cifras, definiciones); MIXTO, combina señales positivas y negativas. El criterio es, entonces, relativo al encuadre de cada nota y no a un punto de vista fijo (por ejemplo, el del mercado).

Para cubrir todas las fuentes desde el comienzo, se tomó un artículo de cada uno de los nueve archivos del corpus por lote. El resultado fue de 408 noticias (45 o 46 por fuente) y 11.605 filas etiquetadas, que corresponden a 11.283 oraciones distintas:

| Clase | Filas | % |
|---|---:|---:|
| NEU | 5.390 | 46,4 |
| POS | 2.763 | 23,8 |
| NEG | 2.416 | 20,8 |
| MIXTO | 1.036 | 8,9 |

## 3. Entrenamiento del modelo

**Conjunto de entrenamiento.** Para que la clase neutra no dominara el aprendizaje, se tomó una muestra balanceada de hasta 2.400 oraciones por clase, con todas las de MIXTO por ser la clase escasa. Esa muestra se dividió en 80% para entrenamiento, 10% para validación y 10% para prueba, estratificando por clase: 6.588, 824 y 824 oraciones. En total se usaron para entrenar el 57% de las filas etiquetadas (el 36% de las neutras y entre el 70% y el 80% de las demás clases). La pérdida se ponderó por la raíz cuadrada de la frecuencia inversa de cada clase.

**Preentrenamiento continuado.** Según el cuaderno de la versión anterior, BETO se siguió entrenando con la tarea de enmascarar palabras (15% de los tokens) sobre el texto de los 14.667 artículos del corpus de entonces: 3 épocas, segmentos de 128 tokens, tasa de aprendizaje 2·10⁻⁵. La pérdida de evaluación bajó de 1,233 a 1,121, y ante la frase "La [MASK] llegó al 3% mensual según el INDEC" el modelo propuso "inflación" con probabilidad 0,81.

**Ajuste fino.** Sobre ese modelo se entrenó un clasificador de cuatro clases: textos de hasta 128 tokens, 5 épocas, lotes de 32, tasa de aprendizaje 2·10⁻⁵ con 10% de calentamiento, decaimiento de pesos 0,01, y selección de la mejor época por F1 macro en validación.

## 4. Evaluación

### 4.1 Evaluación original y sus problemas

La evaluación original informó un F1 macro de 0,7296 en las cuatro clases, frente a 0,6201 de un modelo de sentimiento público sin ajuste a este dominio (`finiteautomata/beto-sentiment-analysis`, un BETO ajustado con unos 5.000 tuits del corpus TASS 2020, de tres clases). Al revisar el conjunto etiquetado y la división se encontraron tres problemas:

- **La división se hizo por oración, no por noticia.** Las oraciones de una misma nota quedaron repartidas entre entrenamiento, validación y prueba. Las 824 oraciones de prueba provenían de 337 noticias, y las 337 aportaban también oraciones al entrenamiento: el modelo nunca se evaluó sobre una noticia que no hubiera visto, aunque fuera en parte. En el uso real, en cambio, el 97% de los artículos del corpus no participó del entrenamiento.
- **Había textos repetidos.** Dieciocho noticias se procesaron dos veces, lo que dejó 318 oraciones etiquetadas más de una vez; en 35 de ellas, Gemma asignó etiquetas distintas en cada pasada. Además, varios párrafos fijos de los sitios se repetían en distintas noticias. Por eso 41 oraciones del conjunto de prueba (5%) estaban también, textualmente, en el de entrenamiento.
- **Había texto que no es una oración de noticia.** Restos del scraping como "PUBLICIDAD PUBLICIDAD PUBLICIDAD" o "Sobre la firma Newsletter Clarín" se etiquetaron como neutros. En Infobae, además, muchas oraciones reales traían la marca "PUBLICIDAD" pegada al principio.

### 4.2 Corrección y nueva medición

Sin modificar el modelo en uso, se rehízo la evaluación en tres pasos:

1. **Limpieza del conjunto etiquetado.** Se quitaron las marcas de relleno pegadas a las oraciones y se descartaron 750 filas: 73 de relleno puro, 72 oraciones etiquetadas dos veces con etiquetas distintas, 281 copias de oraciones etiquetadas dos veces con la misma etiqueta, 36 textos repetidos con etiquetas distintas y 288 copias de textos repetidos. Quedaron 10.855 oraciones de las mismas 408 noticias, sin repeticiones.
2. **Nueva división por noticia.** Con el mismo criterio de balanceo y la misma proporción 80/10/10, se sortearon noticias en lugar de oraciones, estratificando por fuente: 330 noticias para entrenamiento, 39 para validación y 39 para prueba, sin ninguna noticia ni ningún texto compartido entre conjuntos.
3. **Reentrenamiento solo para medir.** Se reentrenó el modelo con la misma configuración sobre las dos divisiones, la original y la nueva, con tres semillas cada una. El código reproduce el resultado original: 0,732 de F1 con la división original, frente al 0,7296 informado.

| F1 en el conjunto de prueba (media de 3 semillas) | División original (por oración) | División por noticia |
|---|---:|---:|
| **F1 macro, 4 clases** | 0,732 ± 0,012 | **0,685 ± 0,009** |
| Exactitud | 0,743 | 0,691 |
| F1 POS / NEG / NEU / MIXTO | 0,752 / 0,760 / 0,754 / 0,663 | 0,694 / 0,677 / 0,725 / 0,645 |

Quitar del test original las 41 oraciones repetidas baja el F1 solo 0,7 puntos. Dividir por noticia lo baja unos 4,7 puntos, sobre todo en la clase negativa. **La estimación que corresponde informar es la de la división por noticia: F1 macro de 0,685 en cuatro clases.**

### 4.3 Comparación con el modelo de referencia

Para comparar en igualdad de condiciones, los dos modelos se midieron en la misma tarea de tres clases. Se usaron solo las oraciones cuya etiqueta es POS, NEG o NEU, y se contó como error cada vez que FinBETO predijo MIXTO.

| F1 macro, 3 clases | Test original (720 oraciones) | Test por noticia (662 oraciones) |
|---|---:|---:|
| Modelo de referencia | 0,620 | **0,546** |
| FinBETO | 0,773 | **0,724** |
| Diferencia | +15,3 puntos | **+17,7 puntos** |

El modelo de referencia reproduce el 0,6201 de la evaluación original, lo que confirma que se aplicó del mismo modo. Medidos en la misma tarea, la ventaja original de FinBETO era de 15 puntos, no de 11: el valor original comparaba su F1 de cuatro clases con el de tres clases del modelo de referencia. Sobre noticias no vistas, ambos modelos bajan —el de referencia también, aunque no se entrenó con estos datos, lo que indica que el nuevo conjunto de prueba es más exigente—, pero la ventaja de FinBETO se mantiene: **0,724 frente a 0,546**. El modelo de referencia, entrenado con tuits, tiende a clasificar como neutras la mayoría de las oraciones (411 de 662) y tiene su peor desempeño en la clase positiva.

## 5. Aplicación al corpus y serie diaria

El modelo se aplicó a todas las oraciones del corpus, incluido el título de cada nota, con oraciones de entre 30 y 600 caracteres. Antes de agregar se excluyeron 2.438 oraciones de relleno que el scraping había dejado dentro del texto, sobre todo el bloque de firma y suscripción al final de las notas de Clarín y las marcas de publicidad de Infobae, que el modelo clasificaba como neutras. Quedaron 399.803 oraciones de los 14.012 artículos: 36,7% neutras, 27,1% positivas, 24,1% negativas y 12,1% mixtas. Para cada artículo se calcularon los porcentajes de cada clase y el sentimiento neto, definido como la diferencia entre el porcentaje de oraciones positivas y el de negativas (las mixtas y las neutras no suman ni restan). La misma clasificación por oración se usa para el sentimiento por empresa e indicador (capítulo de reconocimiento de entidades), de modo que ambas medidas provienen de una única aplicación del modelo.

La serie diaria es el promedio del sentimiento neto de los artículos publicados cada día, con igual peso por artículo. Un día es un shock positivo (negativo) cuando su sentimiento neto supera (queda por debajo de) la media de los últimos siete días con datos en más de 1,5 desvíos estándar, siempre que tenga al menos cinco artículos. La ventana de siete días incluye al propio día evaluado, lo que acota el desvío máximo alcanzable a (7−1)/√7 ≈ 2,27 desvíos; la etapa de unión con las variables financieras redefine la banda excluyendo ese día. Con el corpus depurado de 14.012 artículos, la serie abarca 487 días, de los cuales 377 tienen datos, y contiene 36 shocks: 17 positivos y 19 negativos. Como 14.001 de los 14.012 artículos son de mayo de 2025 en adelante, la serie es prácticamente vacía entre enero y abril de 2025.

## 6. Limitaciones

- **Las etiquetas provienen de un modelo, no de personas.** El F1 mide el acuerdo de FinBETO con Gemma, no con un criterio humano, y no se realizó una validación con anotadores. Las conclusiones que se apoyan en la serie de sentimiento heredan esta limitación.
- **El contexto del etiquetado se armó con los primeros 3.000 caracteres de cada nota.** El 39% de las oraciones etiquetadas está más allá de ese punto, y su efecto solo puede medirse con la validación humana.
- **El modelo en uso se entrenó con la división original**, que contenía relleno y repeticiones. La corrección se aplicó a la medición de su calidad, no al modelo, para no tener que reprocesar toda la cadena antes de la validación humana.
- **Oraciones con marcas de relleno pegadas.** Las oraciones reales que el scraping dejó precedidas por "PUBLICIDAD" se clasificaron con esa marca incluida; se conservan con su etiqueta, porque reclasificarlas requeriría volver a correr el modelo.
- **Tamaño del conjunto de prueba.** Con 39 noticias por conjunto, las clases quedan algo desparejas (por ejemplo, 182 oraciones negativas en el test por noticia) y la estimación tiene un desvío de casi un punto entre semillas.
- **El preentrenamiento continuado usó el texto de todos los artículos,** incluidos los del conjunto de prueba. No usa etiquetas, por lo que no filtra la respuesta, pero el modelo estuvo expuesto al vocabulario de esas notas.
- **El criterio de sentimiento es relativo al encuadre de cada noticia,** lo que debe tenerse en cuenta al interpretar la serie: una misma noticia puede ser favorable para un actor y desfavorable para otro.
