# U7b · Especificación fijada antes de ver los resultados

Escrita el 24/10/2026, antes de calcular ningún resultado de este paso. No se modifica después de ver los resultados.
Si algo hubiera que cambiar, se agrega abajo como "cambio posterior", con la fecha y el motivo, y se informan las dos versiones.

Lo único que se miró antes fue **cuántos** eventos habría en el mercado, no qué pasa con los precios en esos eventos.
Con una versión preliminar de la regla (logaritmo de la cantidad de notas, 30 ruedas, umbral 2) salían 8 eventos.
Se miró para saber si la prueba era factible.

## Pregunta

El plan de trabajo (sección 4.4) define así el shock informativo: un aumento anormal de la **cantidad** de noticias.
- La medida es un z-score: la cantidad de noticias del día comparada con la media móvil de los 30 días previos.
- Un z-score por encima de un umbral marca un evento de shock.

La hipótesis H1 del plan dice que ese shock tiene un impacto medible sobre el precio y/o el volumen de transacciones.

U7 hizo el event study con las ruedas de **tono** extremo. Este paso lo hace con la definición literal del plan: las ruedas con **cantidad** anormal de noticias.

## Cómo se marca un shock

- **Unidad de tiempo:** la rueda. Cada nota cuenta para la rueda en la que el mercado pudo reaccionar a ella (regla de las 17:00 de U1).
  Así, la rueda 0 es la primera en la que el precio pudo responder a la noticia.
- **Mercado:** la cantidad de notas de la rueda (`n_notas`).
- **Cada empresa:** la cantidad de artículos que la mencionan en la rueda (`n_articulos_empresa`); vale 0 si no hubo ninguno.
  - Es la variable "volumen noticioso diario por entidad" del plan.
  - Se usan las 17 empresas con tono propio, porque son las que tienen noticias seguido. En las demás, casi todas las ruedas valen 0 y el z-score no está definido.
- **z-score:** (cantidad de la rueda − promedio de las 30 ruedas previas) / desvío de esas 30 ruedas.
  - Se necesitan al menos 20 de las 30 ruedas previas con dato.
  - Si el desvío es 0, el z-score no se calcula.
- **Versión principal:** la cantidad tal cual viene (es la definición del plan) y umbral **z > 2**.
- **Empresas:** además se exige al menos **3 artículos** en la rueda. Así se evita que un solo artículo cuente como shock en una empresa que casi nunca aparece.
- **Ruedas seguidas con shock:** cuentan como un solo evento, y la rueda 0 es la primera.

## Medición (igual que U7)

- **Ventanas:** estimación [−25, −4] y evento [−3, +5], partido en antes [−3, −1], día [0] y después [+1, +5].
- **Mercado:**
  - El retorno anormal del Merval se mide con el modelo de media constante, igual que U7. El modelo de mercado por acción restaría justamente el efecto de una noticia general.
  - También se mide el monto operado anormal.
- **Empresas:**
  - El retorno anormal se mide con el modelo de mercado por acción (retorno − α − β · retorno del Merval), estimado en [−25, −4].
  - También se mide el volumen anormal de la acción.
- **Días electorales** (08/09 y 27/10): quedan fuera de la estimación. Los eventos cuya ventana incluye uno se informan aparte y no entran al resultado principal.
- **Eventos de una misma empresa que se solapan:** se queda el primero.

## Qué se mide

Un shock de cantidad no tiene signo: muchas notas pueden ser buenas o malas. Por eso se miden tres cosas:

1. **Tamaño del movimiento del precio el día del shock:** el retorno anormal en valor absoluto, |RA| en [0]. Si las noticias mueven el precio, en ese día se mueve más que en un día cualquiera, para un lado o para el otro.
2. **Volumen anormal** en antes, día y después.
3. **Retorno anormal acumulado (CAR)** con signo, en antes, día y después.

Como análisis secundario, se separan los eventos según el tono de esa rueda: tono anormal > 0 o < 0 en el mercado, y tono propio > 0 o < 0 en las empresas.

## Significancia

- **Prueba principal:** la comparación contra fechas al azar, con 5.000 sorteos de la misma cantidad de eventos.
  - **Mercado:** se sortean ruedas con ventanas completas y sin día electoral.
  - **Empresas:** se sortean pares (empresa, rueda) de las mismas 17 empresas, con el mismo filtro.
  - El p es la proporción de sorteos con un promedio al menos tan extremo como el observado.
- **También se informan** el test t y el test de signo.
- **Corrección por pruebas múltiples:** Benjamini-Hochberg sobre las pruebas principales.
  - Son 2 niveles (mercado y empresas) × 7 medidas: |RA| del día y, para el volumen anormal y el CAR, antes, día y después.

## Qué cuenta como evidencia

- **La hipótesis H1 se apoya** si, después de la corrección, el |RA| del día [0], el volumen anormal del día o de después, o el CAR de después son significativos (p < 0,05). Basta con el mercado o con las empresas.
- **Si solo aparece movimiento "antes",** el precio se movió antes de que creciera la cantidad de noticias. Eso es lo mismo que mercado → noticias (U6 y U7), no un apoyo a H1.

## Robustez (también fijada ahora)

- Umbral z > 2,5.
- z-score sobre log(1 + cantidad) en lugar de la cantidad tal cual.
- Con los eventos cuya ventana incluye un día electoral.

## Lo que se informa pase lo que pase

Todos los eventos, todos los p-valores y la conclusión, sea a favor o en contra de la hipótesis.

---

## Cambio posterior 1 (24/10/2026, después de ver los resultados de la versión original)

**Qué se encontró.** Los 13 eventos del mercado de la versión original caen en la primera rueda después de un día sin mercado: 11 lunes y 2 ruedas post-feriado.
- Por la regla de las 17:00, esa rueda acumula las notas de 3 o 4 días de calendario.
- Comparada con las 30 ruedas previas, casi siempre "tiene muchas más notas".
- Es decir, la regla original marca fines de semana, no aumentos de noticias.
- En las empresas pasa lo mismo, pero menos: 51 de los 105 eventos caen en esas ruedas, que son el 23% del período (56 de 244).

**Qué se cambia.**
- La cantidad se mide **por día de calendario**: la cantidad de la rueda dividida por los días que cubre (`dias_cubiertos` de U4).
- Es lo más fiel al plan, que habla del volumen *diario* de noticias.
- Todo lo demás queda igual: 30 ruedas previas, z > 2, al menos 3 artículos en las empresas, las mismas medidas, el mismo sorteo y la misma corrección.
- Se informan las dos versiones: la corregida pasa a ser la principal, y la original queda como "especificación original".

## Agregado posterior 2 (24/10/2026, antes de correrlo): prueba pre-apertura

**Por qué.** La rueda 0 incluye notas publicadas durante esa misma sesión, que pueden estar contando la suba o la baja del día. Por eso, "el precio se mueve más el día del shock" no dice qué vino primero.

**Cómo se mide.**
- **Notas que se cuentan:** solo las pre-apertura, con el mismo criterio de U6b.
  - Son las asignadas a la rueda t que no se publicaron entre las 11:00 y las 17:00 del día t.
  - Se excluyen las de hora sospechosa.
  - En las empresas se cuentan los artículos pre-apertura que mencionan a la empresa, con el mismo cruce entidad-sentimiento de U3 y U6b.
- **Shock:** la misma regla corregida. Cantidad pre-apertura por día de calendario, z contra las 30 ruedas previas, z > 2, y en las empresas al menos 3 artículos.
- **Medidas:** se usan precios de apertura y cierre, porque no hay hora a hora.
  - **Salto de apertura anormal**, en valor absoluto.
    - Mercado: el retorno de apertura del promedio de las 47 acciones (apertura de t / cierre de t−1 − 1), menos su promedio en [−25, −4] sin los días electorales.
    - Empresa: su retorno de apertura menos el del promedio de las 47.
    - Es la medida central: es el único precio que se forma después de las notas pre-apertura y antes de las notas de la sesión.
  - **|retorno anormal| del día [0]**, de cierre a cierre, igual que en la prueba principal.
  - **Volumen anormal del día [0].**
- **Significancia:** contra fechas al azar (5.000 sorteos), con Benjamini-Hochberg sobre estas 6 pruebas (2 niveles × 3 medidas).
- **Qué cuenta como evidencia de noticias → mercado:** un salto de apertura anormal mayor que el de un día cualquiera, significativo tras la corrección.

## Agregado posterior 3 (24/10/2026, después de ver los resultados): sensibilidad

El salto de apertura del mercado salió significativo con solo 5 eventos.
- Como análisis **descriptivo**, se repite la comparación sacando un evento por vez (`sensibilidad_preapertura.csv`).
- No cambia la regla de evidencia. Sirve para saber si el resultado depende de un solo día.
