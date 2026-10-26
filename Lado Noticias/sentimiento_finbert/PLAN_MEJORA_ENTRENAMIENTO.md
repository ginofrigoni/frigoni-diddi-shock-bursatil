# Plan de mejora del entrenamiento de FinBETO

Fecha: 2026-10-18. Punto de partida: lo hecho en las fases 1 a 3 (ver `README.md` de esta carpeta).

## Dónde estamos

| | Valor |
|---|---|
| Modelo en uso (el que clasificó el corpus) | FinBETO de la versión 2.0, entrenado con la división original por oración. **No se cambió.** |
| Calidad medida sobre noticias no vistas, 4 clases | F1 macro **0,685 ± 0,009** (Fase 3, división por noticia, 3 semillas) |
| Ídem, 3 clases (sin MIXTO) | **0,724** frente a **0,546** del modelo de referencia `finiteautomata/beto-sentiment-analysis` |
| Etiquetas | Generadas por Gemma (`gemma4:26b`); **sin validación humana** |
| Decisión tomada | Se mantienen las 4 clases (POS, NEG, NEU, MIXTO) |

Lo que limita hoy la calidad, de mayor a menor peso:

1. Las etiquetas no fueron validadas por personas: no se sabe si Gemma etiqueta como lo haría un lector experto.
2. El contexto que Gemma usó para etiquetar se armó con los primeros 3.000 caracteres de cada nota, y el 39% de las frases etiquetadas está más allá de ese punto.
3. El modelo en uso se entrenó con la división original y con datos sin limpiar (relleno, repetidos).
4. El sentimiento de cada artículo incluye frases de relleno que el modelo clasifica como neutras, lo que diluye el promedio.
5. Hay pocos datos de la clase MIXTO (995 tras la limpieza), que es la de peor F1 (~0,64).

## Pasos

Cada paso tiene un criterio de decisión: si el resultado es bueno, el paso siguiente puede no hacer falta.

### Paso 1. Validación humana del etiquetado (Fase 4) — **descartado**

> **Decisión del 2026-10-18: no se hace.** Las etiquetas de Gemma se toman como válidas y la falta de validación humana queda como limitación declarada en la tesis (`SECCION_TESIS.md`, sección 6). El diseño se conserva abajo por si se retoma.

**Objetivo:** saber si las etiquetas de Gemma, y por lo tanto FinBETO, coinciden con el criterio de una persona.

**Diseño:**
- **Muestra:** 400 frases tomadas de noticias del corpus que **no** estén entre las 408 etiquetadas por Gemma. Así la muestra sirve a la vez como test independiente. Se estratifica por fuente y se sobrerrepresentan las frases que FinBETO clasifica como POS, NEG o MIXTO, para que no quede casi todo neutro.
- **Anotadores:** al menos dos personas que etiqueten a ciegas, sin ver la etiqueta de Gemma ni la de FinBETO, y por separado.
- **Guía:** las mismas definiciones del prompt de Gemma ("favorable / desfavorable dentro del encuadre de la noticia", NEU descriptiva, MIXTO con señales de ambos signos), con ejemplos. Hay que agregar una opción "no es una frase de noticia" para el relleno.
- **Contexto:** a cada frase se le muestra la noticia completa, porque el criterio depende del encuadre.

**Qué se mide:**
- Acuerdo entre las dos personas (kappa de Cohen). Es el techo realista: ningún modelo puede superar el acuerdo humano.
- Acuerdo de cada persona con Gemma y con FinBETO (kappa y F1 macro, tomando la etiqueta humana consensuada como referencia).
- Ese mismo acuerdo separado entre frases del principio de la nota y frases posteriores al carácter 3.000. Responde si el corte de contexto afectó.

**Criterio de decisión:**
- Si el acuerdo Gemma–humanos es comparable al acuerdo entre humanos, las etiquetas son válidas. Se reporta y **no hace falta reetiquetar** (se saltea el paso 3).
- Si es claramente menor, o si las frases posteriores al carácter 3.000 tienen peor acuerdo, se pasa al paso 3.

**Costo:** unas 4 a 6 horas de trabajo humano por anotador. Para mí: preparar la muestra, la planilla y el script de métricas.

### Paso 2. Reentrenar el modelo de producción con los datos limpios

**Objetivo:** que el modelo en uso se entrene con el conjunto limpio y la división por noticia, y no con los datos con relleno y repetidos.

**Cómo:** mismo script de la Fase 3, sobre `dataset_v2/` y guardando el modelo. Conviene elegir la semilla con mejor F1 en **validación**, nunca en test.

**Cuándo:** solo junto con el paso 5. Reentrenar implica volver a clasificar el corpus y regenerar la serie diaria, los shocks, el cruce NER × sentimiento y los modelos econométricos. Si el paso 1 lleva a reetiquetar, este paso se hace una sola vez, después del paso 3.

**Costo:** minutos de GPU para entrenar; el costo real está en el reproceso posterior.

### Paso 3. Reetiquetar con un prompt corregido (solo si el paso 1 sale mal)

**Cambios al prompt y al procedimiento:**
- Pasarle a Gemma el artículo completo para armar el contexto, o armar un contexto por tramo en las notas largas, en lugar de cortar en 3.000 caracteres.
- Agregar una salida `NO_ORACION` para el relleno.
- Filtrar el relleno y los repetidos **antes** de etiquetar, con las reglas de `limpiar_etiquetado.py`.
- Si el paso 1 mostró desacuerdos sistemáticos (por ejemplo, frases de cotizaciones), agregar ejemplos de esos casos al prompt.
- Etiquetar cada noticia una sola vez, controlando con el índice, para no repetir el reproceso de 18 noticias.

**Cobertura:** sumar noticias, no solo frases, para ganar variedad. Conviene apuntar a más ejemplos de MIXTO.

**Costo:** alto. Gemma tarda del orden de minutos por frase, así que unas 10.000 frases son días de cómputo.

### Paso 4. Más datos para la clase MIXTO

La curva de aprendizaje original se estabilizó en ~0,72 con unas 1.500 frases por clase, pero MIXTO tiene menos de 1.000. Opciones, de más barata a más cara:
- Seleccionar para etiquetar las frases que el modelo actual clasifica como MIXTO o con baja confianza (muestreo dirigido).
- Reetiquetar con más noticias (paso 3).

Criterio: vale la pena si el F1 de MIXTO sigue siendo el más bajo después del paso 1.

### Paso 5. Corregir el sentimiento por artículo

**Objetivo:** que el relleno no diluya el sentimiento de cada noticia.

**Cómo:** recalcular el sentimiento neto de cada artículo excluyendo las frases de relleno (mismas marcas que `limpiar_etiquetado.py`) y quitando "PUBLICIDAD" de las frases que la traen pegada. No hace falta el modelo: se puede hacer desde el sentimiento por oración.

**Cuándo:** junto con el paso 2, porque los dos obligan a regenerar todo lo de abajo.

### Paso 6. Reproducibilidad

Lo que hay que dejar fijo para que todo lo anterior sea verificable:
- Guardar las predicciones por oración de cada evaluación, no solo las métricas.
- Fijar las versiones de las bibliotecas (`requirements.txt`) y registrar la semilla de cada corrida.
- Guardar el modelo de producción con su hash, junto con el de la división con que se entrenó.

## Orden recomendado

Sin validación humana (paso 1 descartado), el paso 3 deja de tener un criterio para activarse y queda fuera de alcance. Lo que sigue en pie:

1. **Pasos 2 y 5 juntos** (reentrenar el modelo de producción con los datos limpios y sacar el relleno del sentimiento por artículo), con un solo reproceso de la cadena completa. **Conviene decidirlo antes de que la unión use la serie**: si se hace después, hay que rehacer la unión.
2. **Paso 4** (más datos de MIXTO): solo si se decide reetiquetar en algún momento.
3. **Paso 6** en todos los casos.
