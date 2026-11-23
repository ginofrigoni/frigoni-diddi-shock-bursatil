# Guion de la presentación · versión 6.0

Presentación: `Presentación Tesina — versión 6.0.pptx` (y su copia en PDF), en esta misma carpeta. Son 29 diapositivas y los números coinciden con el informe.

**Duración prevista: 25 minutos** (a confirmar con la cátedra). Nicolás habla unos 11 minutos y Gino unos 14. Si hay que recortar, ver el final.

**Reglas para los dos:**
- Decir **«sentimiento»**, nunca «tono».
- Cada resultado se dice con su número y su comparación: «0,678 contra 0,526», no «da bien».
- Ante una pregunta que no sabemos: «Eso no lo medimos; lo que sí medimos es…».

---

## Parte 1 · El problema (Nicolás, ~6 min)

| # | Diapositiva | Tiempo | Qué decir (ideas clave, no para leer) |
|---|---|---|---|
| 1 | Portada | 0:30 | Saludo y presentación. «Es una **metodología de ciencia de datos**, organizada con CRISP-DM.» |
| 2 | Separador 1 | 0:10 | — |
| 3 | El problema | 0:50 | Los días de noticias fuertes son días de mercado fuerte, pero eso no dice quién va primero. Ejemplo: «El Merval subió 5 %» es una nota positiva **causada** por el precio. |
| 4 | Relevancia | 0:40 | No existían ni un corpus, ni un modelo de sentimiento para prensa económica en español, ni un VIX argentino. Hubo que construir cada pieza. |
| 5 | Hipótesis | 1:10 | Leer H1 en simple: se pone a prueba **la metodología**. H0 es su negación exacta. El criterio tiene **dos partes** que se cumplen a la vez, medir y relacionar, y **se fijó antes** de ver los datos. |
| 6 | Objetivos | 0:40 | Cuatro objetivos escritos como resultados. «Al final volvemos a cada uno.» |
| 7 | Metodología | 0:50 | Las seis fases de CRISP-DM. Cada fase es una carpeta del proyecto y un capítulo del informe. La fase 5 es donde se pone a prueba la hipótesis. |
| 8 | Pipeline | 0:50 | Arriba, las noticias (lado de Gino); abajo, el mercado (lado de Nicolás). Se juntan en un dataset de 17 × 244. **Pasar la palabra a Gino.** |

## Parte 2 · Los datos (Gino, ~5 min; Nicolás cierra con el VIX)

| # | Diapositiva | Tiempo | Qué decir |
|---|---|---|---|
| 9 | Separador 2 | 0:10 | — |
| 10 | Corpus | 0:50 | 14.012 notas de 7 portales, recolectadas con la Wayback Machine y los mapas del sitio. Cinco problemas de calidad; el más importante, las plantillas tipo «Dólar hoy». **Por qué no usamos la cantidad de notas:** depende de qué capturó el archivo web (abril de 2026 no tiene iProfesional). |
| 11 | Regla de las 17:00 | 0:40 | Una nota del martes a las 20 h la puede usar el mercado recién el miércoles. 59,8 % se queda en su día; el resto pasa a la rueda siguiente. Es la clave para que nada «mire al futuro». |
| 12 | Etiquetado | 1:20 | **Lo que pidió el profesor.** Los cuatro pasos y una razón escrita por cada oración. Leer los dos ejemplos. Decirlo claro: **no hubo revisión humana**; el F1 mide el acuerdo con Gemma. |
| 13 | Fórmulas | 1:00 | Recorrer las cinco fórmulas. Ejemplo del inesperado: hoy +10, promedio +6, inesperado +4. «¿Por qué 20 ruedas? Un mes de mercado, el horizonte del VIX de Cboe y de Corsi (2009). Probamos 10 y 60 en la robustez.» **Pasar a Nicolás.** |
| 14 | VIX | 1:00 | (Nicolás) Sin opciones líquidas, se usa la volatilidad realizada. La fórmula. Escala por **terciles**: bajo hasta 33,8 %, alto más de 39,6 %. «Los umbrales de EE. UU. no sirven: acá el promedio es 41,9 %.» **Devolver a Gino.** |

## Parte 3 · Preparación y modelado (Gino ~4 min, Nicolás ~3 min)

| # | Diapositiva | Tiempo | Qué decir |
|---|---|---|---|
| 15 | Separador 3 | 0:10 | — |
| 16 | FinBETO | 1:00 | Dos pasos: aprende el idioma y después a clasificar. El ejemplo de «inflación». **MIXTO → NEU:** aportaban lo mismo al sentimiento neto; ahora la escala es ordenada. Se usaron exactamente las mismas oraciones. |
| 17 | Evaluación de FinBETO | 1:10 | **0,697 contra 0,542: +15,5 puntos.** El de referencia dice «neutra» en 493 de 786. En la matriz, casi nunca confunde positivo con negativo. «Dividimos por **noticia**, no por oración: si no, el F1 sale inflado.» **Primera parte del criterio: cumplida.** |
| 18 | Sentimiento | 0:50 | 413.515 oraciones clasificadas. El inesperado es igual para todas las acciones del día; el propio compara una empresa contra el mercado. `hubo_noticia` distingue «se habló igual» de «no se habló». **Pasar a Nicolás.** |
| 19 | El experimento | 1:20 | (Nicolás) El mismo modelo con y sin la información del otro lado, **en las dos direcciones**. Leer A y B de cada lado. Regresión logística (interpretable) y random forest (confirma). Afuera quedan la cantidad de notas y el régimen. |
| 20 | Corte temporal | 1:00 | Entrenar con el pasado, evaluar con el futuro: corte el 01/02/2026, test de 58 ruedas **usado una sola vez**. ΔAUC con bootstrap por bloques de ruedas. **Pasar a Gino.** |

## Parte 4 · Evaluación y cierre (Gino ~6 min, Nicolás ~2 min)

| # | Diapositiva | Tiempo | Qué decir |
|---|---|---|---|
| 21 | Separador 4 | 0:10 | — |
| 22 | Noticias → precio | 1:10 | «El momento de la verdad.» AUC 0,533 contra 0,521: **ΔAUC −0,012**, el intervalo incluye el 0. El random forest dice lo mismo. Las noticias no agregan nada a lo que ya dicen los retornos, el volumen y el VIX. |
| 23 | Precio → sentimiento | 1:20 | **Al revés sí: 0,526 → 0,678, ΔAUC +0,152**, el intervalo excluye el 0. El random forest confirma. Granger: 14 de 17 empresas contra 0 de 17. **Segunda parte del criterio: cumplida.** |
| 24 | Variables | 0:50 | Lo que más pesa es **el retorno del Merval de hoy**. Explicación: las notas publicadas después del cierre cuentan para la rueda siguiente, y son las que cuentan cómo cerró el mercado. |
| 25 | Robustez | 1:00 | Una decisión por vez, nueve variantes. Noticias → precio: nunca. Precio → sentimiento: positivo en las 9, significativo en 6. «Lo decimos: con el ajuste por portal se achica.» |
| 26 | Discusión | 1:20 | **Lo pidió el profesor: los desaciertos.** Cuatro corregidos y cuatro límites. El más importante: **el test es un período calmo** (58 ruedas, todas en régimen Calmo). **Pasar a Nicolás.** |
| 27 | Conclusiones | 1:00 | (Nicolás) Se rechaza H0. Recorrer los cuatro objetivos con su resultado y las líneas futuras. |
| 28 | Cierre | 0:30 | (Nicolás) Leer la frase: «los medios siguieron al mercado, no al revés». Agradecer y abrir a preguntas. |
| 29 | Anexo | — | No se expone. Se muestra la ficha que corresponda si hay preguntas. |

---

## Preguntas probables y respuestas cortas

| Pregunta | Respuesta (≈ 30 segundos) | Quién |
|---|---|---|
| ¿Por qué etiquetó Gemma y no personas? | No había un conjunto público ni presupuesto para anotadores, y la literatura muestra que un modelo de lenguaje puede igualarlos (Gilardi et al., 2023). Es una limitación declarada: el F1 mide el acuerdo con Gemma. La línea futura es etiquetar una muestra a mano. | Gino |
| ¿Por qué juntaron MIXTO con NEU? | Porque en el sentimiento neto ya valían lo mismo, 0. No había forma de justificar dos clases que se tratan igual, y así la escala queda ordenada. Se usaron las mismas oraciones, y FinBETO no empeoró (0,731 contra 0,724 en las oraciones comparables). | Gino |
| ¿Por qué 20 ruedas? | Un mes de mercado, el horizonte del VIX de Cboe (30 días ≈ 21 ruedas) y del componente mensual de Corsi (2009). No se eligió con los datos: probamos 10 y 60, siguiendo a Tetlock (2007). | Gino |
| ¿No es chico el test? | Sí: 58 ruedas. Por eso el intervalo se calcula con bootstrap por bloques de ruedas, y el resultado se repitió con otros dos cortes del test (enero y marzo): se mantiene. | Nicolás |
| ¿Un AUC de 0,678 no es bajo? | Lo que importa es la **diferencia**: con solo el pasado de las noticias el AUC es 0,526, casi el azar; al agregar el mercado sube a 0,678. Predecir el sentimiento de un día es difícil; el mercado agrega información real. | Gino |
| ¿Hay fuga de información? | Se cuidó en cuatro lugares: la regla de las 17:00, la estandarización con datos solo del entrenamiento, el K del sentimiento propio estimado solo con el entrenamiento y la validación temporal. Además, el test se usó una sola vez. | Nicolás |
| ¿Es causalidad? | No. Es **anticipación**: el precio de hoy mejora la predicción del sentimiento de mañana. Es causalidad en el sentido de Granger, no una causa demostrada. | Nicolás |
| ¿Por qué se achica con el ajuste por portal? | Puede ser que parte del efecto venga de qué portales publican cada día, por ejemplo los que hacen la crónica del cierre. No lo verificamos: es una línea futura. | Gino |
| ¿Por qué solo 17 empresas? | Para medir el sentimiento propio hace falta que la empresa tenga noticias en buena parte de las ruedas. Con un corte de 90 de 244 quedan 17; el resto tiene pocas menciones o ninguna. | Gino |
| ¿Qué pasó con los regímenes y el clustering? | El régimen sale del mismo VIX que ya está en el modelo; agregarlo era duplicar. Se usa solo en la robustez y no cambia nada. El clustering no encontró familias más allá de la liquidez, así que no aportaba al modelo. | Nicolás |
| ¿Por qué dejaron VAR y Granger? | Como verificación. Siguiendo la devolución de la cátedra, la prueba principal pasó a ser el modelo predictivo con métricas de ciencia de datos, y los dos métodos dicen lo mismo. | Nicolás |
| ¿Sirve para otros períodos? | El test es un período calmo. Garcia (2013) encontró que el sentimiento anticipa al mercado en recesiones; probarlo necesita varios años de datos. Es la principal línea futura. | Gino |

## Si hay que recortar a 15 minutos

Saltar estas diapositivas: relevancia (4), objetivos (6, se mencionan en conclusiones), pipeline (8), regla de las 17:00 (11, se nombra en el experimento), sentimiento (18) y variables (24, se dice en una frase en la 23). Los separadores se pasan sin hablar.
