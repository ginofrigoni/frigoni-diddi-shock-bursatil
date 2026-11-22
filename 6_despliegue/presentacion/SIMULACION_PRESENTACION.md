# Simulación de la presentación (guion diapositiva por diapositiva)

> **Para qué es este documento.** Es un ensayo de cómo debería verse la presentación si se aplican las correcciones del docente (reunión de devolución) con el orden de la presentación de Maricel Martinez. Funciona como **plan de trabajo**: cada diapositiva dice de dónde sale su contenido y qué falta hacer.
>
> **Marcas:** ✅ ya existe en la 5.0 · ✏️ existe, pero hay que reescribirlo · 🆕 [a calcular] hay que producirlo · ❓ [a decidir] lo deciden ustedes.
>
> **Reglas que sigue todo el guion** (del docente y de la presentación de Maricel):
> 1. El trabajo es una **metodología de ciencia de datos**: se evalúa con métricas de ciencia de datos (matriz de confusión, F1, AUC), no con pruebas de significación.
> 2. **Las definiciones van antes que los resultados** (VIX, escala, regímenes, tono anormal), con su fórmula.
> 3. Cada diapositiva tiene un **título que afirma algo**, una bajada de una línea y un gráfico o un número grande. Diagramas con pasos y flechas en lugar de texto.
> 4. Cada gráfico o tabla **cita su lugar en el informe** ("Figura X del informe").
> 5. Las conclusiones **responden a cada objetivo**.

---

## Estructura

| Bloque | Diapositivas | Qué resuelve |
|---|---|---|
| Portada | 1 | Título técnico y subtítulo llano |
| **Parte 1 · El problema** | 2–5 | Pregunta, hipótesis, objetivos, metodología |
| **Parte 2 · Los datos** | 6–10 | Corpus, alineación con las ruedas, etiquetado, definiciones |
| **Parte 3 · Preparación y modelado** | 11–17 | FinBETO, tono por rueda y empresa, mercado, modelo predictivo |
| **Parte 4 · Evaluación y cierre** | 18–23 | Resultados en datos no vistos, discusión, conclusiones |
| **Anexo** | A1–A10 | El detalle que puede preguntar el tribunal |

Cada parte abre con una diapositiva separadora ("Parte 2 de 4 · Los datos · ¿Qué medimos y cómo?") con la barra de las 4 partes. Las separadoras no se cuentan en la numeración de arriba.

---

## Portada

### 1 · Portada — ✏️
- **Título:** *Una metodología de ciencia de datos para medir el tono de las noticias económicas argentinas y evaluar su relación con el mercado bursátil*.
- **Subtítulo:** *¿Las noticias anticipan a las acciones, o las acciones a las noticias?*
- Autores, carrera, universidad, fecha.
- **Cambio:** el subtítulo actual ("análisis de sentimiento y modelos de series temporales") pone el foco en la técnica. El docente pidió que el foco sea la metodología.

---

## Parte 1 · El problema

### 2 · "Los días de noticias fuertes son días de mercado fuerte, pero ¿quién va primero?" — ✅ (actual 2)
- Las dos direcciones posibles: noticias → mercado y mercado → noticias.
- El ejemplo «El Merval subió 5 %»: una nota de tono positivo cuya causa es el precio.
- **Visual:** dos flechas opuestas entre un ícono de diario y uno de gráfico bursátil.
- **Presenta:** Nicolás.

### 3 · "Por qué importa: en Argentina no existía con qué medirlo" — 🆕 (nueva)
- Relevancia, como la diapositiva 4 de Maricel: no hay un corpus de prensa económica argentina, ni un modelo de tono en español para finanzas, ni un VIX local.
- La literatura (Fang y Peress 2009, Engelberg y Parsons 2011, Dougal et al. 2012) trabaja con prensa en inglés y mercados desarrollados.
- **Visual:** tres casilleros vacíos ("corpus", "termómetro de tono", "termómetro de mercado") que el trabajo llena.

### 4 · Hipótesis y objetivos — ✏️ (actual 3, reescrita)
- **Hipótesis (H1):** ❓ [a decidir la redacción final]. Propuesta, en el formato de Maricel y del docente:
  > *Es posible construir una metodología de ciencia de datos que mida el tono de las noticias económicas argentinas y lo relacione con el comportamiento bursátil, con un desempeño evaluable con métricas de clasificación.*
- **H0:** *No es posible construir esa metodología.* (Exactamente la negación de H1.)
- **Objetivo general:** construir y evaluar una metodología de ciencia de datos que relacione el tono de las noticias económicas con el comportamiento de las acciones argentinas.
- **Objetivos específicos (4, como resultados y no como técnicas):**
  1. Construir un corpus depurado de noticias económicas argentinas.
  2. Desarrollar un modelo que clasifique el tono de las noticias.
  3. Caracterizar el mercado y agrupar las empresas con aprendizaje no supervisado.
  4. Construir y evaluar un modelo que prediga el comportamiento de las acciones con y sin el tono de las noticias.
- **Cambio:** se sacan "5 de 6 cumplidos" y Twitter. Twitter pasa a la discusión como algo que no se hizo.

### 5 · "La metodología en cuatro etapas" — 🆕 (reemplaza a la actual 4)
- **Visual:** diagrama con flechas, una caja por etapa, cada una con su **pregunta guía** y el objetivo que responde:
  1. **Datos** → ¿Qué se publicó y cuándo? (Obj. 1) · scraping, auditoría, regla de las 17:00.
  2. **Tono** → ¿Con qué tono? (Obj. 2) · etiquetado con Gemma, FinBETO, NER.
  3. **Mercado** → ¿Cómo estaba el mercado? (Obj. 3) · VIX argentino, regímenes, clustering.
  4. **Modelo y evaluación** → ¿El tono ayuda a predecir? (Obj. 4) · regresión logística y random forest, corte temporal, matriz de confusión y AUC.
- **Presenta:** Nicolás.

---

## Parte 2 · Los datos

### 6 · "14.012 notas de 7 portales, depuradas" — ✅ (actual 5)
- Números grandes: 14.012 notas · 7 portales en 9 fuentes · 419 notas de plantilla eliminadas.
- Cómo se recolectó: Wayback Machine y mapas del sitio.
- Cinco problemas de calidad y su solución, con el ejemplo de «Dólar hoy».
- **Fuente:** cap. 3 del informe. **Presenta:** Gino.

### 7 · "Cada nota a su rueda: la regla de las 17:00" — ✅ (actual 6)
- 59,8 % cuenta para su mismo día · 24,8 % pasa a la rueda siguiente (salió después del cierre) · 15,4 % pasa a la rueda siguiente (día sin rueda).
- Es una decisión metodológica que el docente valoró; se mantiene igual.
- **Presenta:** Gino.

### 8 · "Cómo se etiquetaron 11.605 oraciones" — 🆕 (nueva; es la principal crítica del docente)
- **Visual:** diagrama de flujo en dos pasos.
  1. Gemma lee la noticia (título, bajada y primeros 3.000 caracteres) y escribe un análisis de contexto: tema, encuadre, actores y tono general.
  2. Con ese contexto, etiqueta cada oración en POS, NEG, NEU o MIXTO.
- **Dos o tres ejemplos reales** de oraciones con la etiqueta y la razón que dio Gemma (de `dataset_etiquetado/checkpoint.jsonl`, que guarda la razón de cada etiqueta). 🆕 [elegir ejemplos].
- **Datos:** 408 noticias (45 o 46 por fuente) · 11.605 oraciones · 46,4 % NEU, 23,8 % POS, 20,8 % NEG, 8,9 % MIXTO · temperatura 0,1.
- **Auditoría humana:** ❓ [a decidir]. Hoy no hay ninguna revisión manual. Si se hace (ver pregunta 2), acá va el resultado: "revisamos N oraciones al azar y coincidimos con Gemma en X %".
- **Presenta:** Gino.

### 9 · "Las fórmulas de lo que medimos" — 🆕 (nueva; pedido explícito del docente)
- Una fórmula por variable, cada una con un ejemplo numérico:
  - **Retorno:** r_t = (cierre_t − cierre_t−1) / cierre_t−1
  - **Sentimiento neto de una nota:** %POS − %NEG
  - **Tono de la rueda:** promedio del sentimiento neto de las notas asignadas a la rueda
  - **Tono anormal:** tono_t − promedio del tono de las 20 ruedas anteriores. Ejemplo: si hoy es +10 y el promedio fue +6, el tono anormal es +4.
  - **Atención anormal:** cantidad de notas comparada con lo habitual (0 = habitual, +0,69 = el doble)
  - **Tono propio de una empresa:** tono de las oraciones que la nombran − tono de la rueda
- **Fuente:** sección 4.4 del informe y `Unión/04_dataset_unificado/diccionario_variables.csv`. **Presenta:** Gino.

### 10 · "El VIX argentino y su escala, definidos antes de mirar los datos" — ✏️ (actual 9, movida y ampliada)
- **Qué es:** el VIX de Chicago mide la volatilidad esperada del S&P 500 a partir de opciones. En Argentina no hay opciones líquidas, así que se usa la volatilidad realizada del Merval.
- **Fórmula:** VIX_arg = desvío estándar de los retornos de las últimas 20 ruedas × √252 × 100.
- **Cómo se lee:** un VIX de 44 % significa que, al ritmo del último mes, el índice se movería ±44 % en un año.
- **Escala:** ❓ [a decidir]. El docente pidió bajo, medio y alto definidos antes. Propuesta: "a los fines de este trabajo, la escala la define el modelo de regímenes (sección 4.6)", con los tres estados Calmo, Moderado y Tenso como categorías. Las cifras de cada régimen recién se muestran en la diapositiva 15.
- **Presenta:** Nicolás.

---

## Parte 3 · Preparación y modelado

### 11 · "FinBETO: un modelo que aprendió el idioma de la prensa económica" — ✏️ (parte de la actual 7)
- **Visual:** diagrama BETO → preentrenamiento con el corpus → ajuste fino con las 11.605 oraciones → FinBETO.
- La prueba del idioma: «La [MASK] llegó al 3 % mensual» → «inflación» (0,81).
- **Presenta:** Gino.

### 12 · "FinBETO acierta el tono de noticias que nunca vio" — 🆕 (nueva; métricas de ciencia de datos)
- **Visual:** **matriz de confusión** de FinBETO en la división por noticia. 🆕 [a generar: el informe tiene el F1 por clase, falta la matriz como figura].
- Números grandes: F1 macro 0,685 (4 clases) · 0,724 contra 0,546 del modelo de referencia (3 clases).
- Una línea honesta: la primera medición daba 0,7296 porque dividía por oración; dividiendo por noticia, que es lo correcto, da 0,685.
- **Fuente:** tabla de calidad de FinBETO del cap. 4 del informe. **Presenta:** Gino.

### 13 · "El tono de cada rueda y de cada empresa" — ✅ (actual 8, con la fórmula ya definida en la 9)
- Tono medio +3,9 · 19 ruedas de tono extremo (10 positivas y 9 negativas) · 17 empresas con noticias suficientes para un tono propio.
- **Visual:** serie del tono por rueda (Figura u2 del informe).
- **Presenta:** Gino, y pasa la palabra a Nicolás.

### 14 · "47 acciones, y no hay familias de comportamiento" — ✅ (actual 10)
- Responde el objetivo 3 (agrupar con aprendizaje no supervisado).
- Volatilidad de una acción 55,1 % contra la del índice 44,0 %.
- 18 combinaciones de clustering. El único grupo real (silueta 0,406) era de acciones poco líquidas, y sin las 4 que menos operan se deshace (0,219). Por eso el modelo trabaja acción por acción.
- **Presenta:** Nicolás.

### 15 · "Los tres estados del mercado" — ✅ (actual 11, ya con la escala definida)
- Calmo (VIX 33,0 %, 177 días) · Moderado (46,6 %, 81) · Tenso (70,8 %, 65).
- Al estrés se entra de golpe y se sale de a poco.
- **Visual:** Merval coloreado por régimen (Figura del cap. 6).
- **Presenta:** Nicolás.

### 16 · "El experimento: el mismo modelo, con y sin noticias" — 🆕 (nueva; reemplaza a Granger)
- **Pregunta:** ¿saber lo que dicen las noticias ayuda a predecir si una acción sube o baja en la rueda siguiente?
- **Visual:** dos cajas lado a lado.
  - **Modelo A (sin noticias):** retornos de las ruedas anteriores, volumen, VIX y régimen.
  - **Modelo B (con noticias):** lo mismo, más tono anormal, tono propio y atención anormal.
- **Qué se predice:** si el retorno de la acción en la rueda siguiente es positivo o negativo.
- **Datos:** el panel de 47 acciones × 244 ruedas (`Unión/04_dataset_unificado/dataset_panel.csv`).
- **Modelos:** regresión logística (interpretable) y random forest (captura combinaciones como "el tono importa solo en régimen Tenso").
- **Presenta:** Nicolás.

### 17 · "Entrenar con el pasado, evaluar con el futuro" — 🆕 (nueva; como la diapositiva 12 de Maricel)
- **Visual:** línea de tiempo con el corte: entrenamiento de mayo de 2025 a enero de 2026 y prueba de febrero a abril de 2026. ❓ [a decidir el corte exacto; propuesta 75 % / 25 %].
- Dentro del entrenamiento, la validación respeta el orden del tiempo, para elegir hiperparámetros.
- La prueba se usa **una sola vez**.
- **Métricas, definidas acá y antes de los resultados:** exactitud balanceada, F1, AUC y la diferencia de AUC entre B y A con su intervalo de confianza.
- **Presenta:** Nicolás.

---

## Parte 4 · Evaluación y cierre

### 18 · "En las ruedas que nunca vio, las noticias no mejoran la predicción" — 🆕 [a calcular]
- El título es el resultado **esperado** según lo que ya mostró Granger. Si el número da otra cosa, se cambia.
- **Visual:** dos matrices de confusión (A y B) y el AUC de cada una. [a calcular]
- Números grandes: AUC A = [x] · AUC B = [y] · diferencia = [y − x] (IC 95 % [a, b]). [a calcular]
- Comparación con la clase más frecuente ("siempre sube").
- **Presenta:** Gino.

### 19 · "Al revés sí funciona: el mercado anticipa a las noticias" — 🆕 [a calcular] (conserva el hallazgo de la actual 13)
- El mismo experimento invertido: predecir si el tono de la rueda siguiente es más positivo o más negativo, con y sin el retorno de hoy.
- Números grandes: AUC sin retorno = [x] · AUC con retorno = [y]. [a calcular]
- Respaldo: es coherente con Granger (39 de 47 empresas), que pasa al anexo.
- **Presenta:** Gino.

### 20 · "Qué variables usó el modelo" — 🆕 [a calcular] (opcional, como la de interpretabilidad de Maricel)
- Coeficientes de la regresión logística o importancia de variables del random forest.
- Muestra si el tono pesa o no dentro del modelo.

### 21 · Discusión — 🆕 (reemplaza a "Limitaciones y líneas futuras")
- **Punto fuerte:** cuatro instrumentos que no existían para el mercado argentino, y una metodología reproducible de punta a punta.
- **Desaciertos, dichos con precisión:**
  - El etiquetado lo hizo un modelo y no se validó con personas, así que el F1 mide el acuerdo con Gemma (salvo que se haga la auditoría de la pregunta 2).
  - La clase MIXTO no tiene lugar en una escala de −1 a +1, por lo que el tono se trató como variable nominal. En una próxima versión conviene definir las clases con orden.
  - La primera evaluación de FinBETO estaba inflada (0,7296) porque dividía por oración; se corrigió a 0,685.
  - Un año de datos diarios: un efecto chico podría no verse.
  - El 13,4 % de las notas tiene hora por defecto.
  - El objetivo de Twitter no se llegó a hacer.
- **Presenta:** Gino.

### 22 · Conclusiones — ✏️ (actual 16, reescrita por objetivo)
- **Respuesta a la hipótesis:** sí, es posible construir la metodología. Se construyó, se evaluó con métricas de ciencia de datos y mostró que [el tono no mejora la predicción del precio; el precio sí anticipa el tono]. [completar con los resultados]
- **Un renglón por objetivo:**
  1. Corpus: ✓ 14.012 notas depuradas.
  2. Tono: ✓ FinBETO, F1 0,685 sobre noticias no vistas.
  3. Mercado: ✓ VIX, 3 regímenes, sin familias de acciones.
  4. Modelo: ✓ evaluado con y sin noticias. [completar]
- **Líneas futuras:** reentrenar FinBETO con más noticias y clases ordenadas, etiquetar con revisión humana, sumar varios años y precios intradiarios.
- **Presenta:** Nicolás.

### 23 · Cierre en una frase y ¿Preguntas? — ✏️ (actual 18)
- *"Se construyó una metodología de ciencia de datos que mide el tono de la prensa económica argentina: los medios siguieron al mercado, no al revés."* [ajustar según el resultado]
- **Presentan:** ambos.

---

## Anexo (no se expone; sirve para responder preguntas)

| N.º | Contenido | Origen en la 5.0 |
|---|---|---|
| A1 | Detalle de la depuración del corpus (cinco problemas) | cap. 3 |
| A2 | Tabla de ejemplos de etiquetado, con la razón de Gemma | `dataset_etiquetado/checkpoint.jsonl` |
| A3 | Preentrenamiento y ajuste fino: hiperparámetros | cap. 4 |
| A4 | F1 por clase, división por oración contra por noticia | tabla de calidad de FinBETO, cap. 4 |
| A5 | VIX: los tres picos y el eco de 20 ruedas | cap. 5 (actual 9) |
| A6 | Volatilidad por acción y ranking | `Lado Bursatil/05_volatilidad_ranking` |
| A7 | Régimen: BIC y matriz de transición | cap. 6 |
| A8 | **Verificación con un método econométrico clásico:** VAR y Granger (304 pruebas, Benjamini–Hochberg), con su resultado coincidente | cap. 7 (actuales 12–14) |
| A9 | Hiperparámetros del modelo predictivo y validación temporal | 🆕 [a calcular] |
| A10 | Robustez del modelo predictivo: otro corte temporal y sin los días de elecciones | 🆕 [a calcular] |

**Qué sale:** las cuatro pruebas de control de la actual 15 ("lo hubieran volado", según el docente) y el efecto de las notas de la noche (actual 14) como diapositiva propia. Si se quiere conservar este último, va como una línea en A8.

---

## Lo que falta producir (resumen para el plan de trabajo)

| Qué | Para qué diapositiva | Esfuerzo |
|---|---|---|
| Modelo predictivo A contra B (regresión logística + random forest), con corte temporal | 16–18, 20, A9, A10 | Alto |
| Modelo invertido (mercado → tono) | 19 | Medio, reutiliza lo anterior |
| Matriz de confusión de FinBETO por noticia | 12 | Bajo |
| Ejemplos de etiquetado | 8, A2 | Bajo |
| Auditoría humana del etiquetado | 8, 21 | ❓ Medio, si se hace |
| Fórmulas y escala del VIX | 9, 10 | Bajo (redacción) |
| Reescribir hipótesis, objetivos, discusión y conclusiones en el informe | 4, 21, 22 | Medio |
