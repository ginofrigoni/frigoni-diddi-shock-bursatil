# U6b · Especificación fijada antes de ver los resultados

Escrita el 24/10/2026, antes de correr ningún cálculo de este paso. No se modifica después de ver los resultados.
Si algo hubiera que cambiar, se agrega abajo como "cambio posterior", con la fecha y el motivo, y se informan las dos versiones.

## Pregunta

¿El tono de las noticias publicadas con el mercado cerrado anticipa el precio de la rueda siguiente?
Esas notas salen antes de cualquier operación de la rueda, así que la rueda no puede haberlas causado.
Es la prueba más directa de la hipótesis principal (noticias → mercado).

## Notas que se usan

- **Notas pre-apertura de la rueda t:** las que U1 asignó a la rueda t y **no** se publicaron entre las 11:00 y las 17:00 del día t.
  Es decir, las que salieron después del cierre de la rueda anterior, en días sin rueda o en la madrugada y mañana de t, antes de las 11:00.
- **Se excluyen las notas con hora sospechosa (U1)**, porque no se sabe si salieron antes o después de la apertura.
- **Ventana:** las 244 ruedas de la unión. La variable principal necesita 20 ruedas previas, así que quedan 224.

## Variables

- **Tono pre-apertura del mercado:** promedio del sentimiento neto de las notas pre-apertura de la rueda.
  - **Variable principal:** su versión **anormal**, es decir, menos el promedio de las 20 ruedas previas. Es el mismo criterio que U5.
- **Tono propio pre-apertura de cada empresa (las 17 con tono propio):** se usa la misma fórmula de U4, pero solo con las oraciones de las notas pre-apertura.
  - Fórmula: peso × (tono de la empresa − tono pre-apertura del mercado), con peso = n / (n + K) y el mismo K de U4.
  - Si no hay menciones pre-apertura de la empresa, vale 0.
- **Retorno de apertura** de la rueda t: apertura de t / cierre de t−1 − 1.
- **Retorno de la sesión** de la rueda t: cierre de t / apertura de t − 1.
- **Mercado:** promedio simple de las 47 acciones, porque no hay apertura del Merval en los datos.

## Modelos (MCO, errores robustos HC3)

**Mercado.** Retorno (de apertura o de la sesión) del promedio de las 47 = a + b · tono pre-apertura anormal + c · retorno del día anterior (cierre a cierre) + d · rueda que viene de un día sin mercado (0/1).

**Empresas (prueba principal).** Panel de las 17 empresas: retorno de la empresa = efecto fijo de la empresa + b · tono propio pre-apertura + c · tono pre-apertura anormal del mercado + e · retorno de la empresa del día anterior + d · rueda tras día sin mercado. Errores agrupados por rueda.

**Empresas (detalle).** El mismo modelo para cada una de las 17, por separado, sin efecto fijo.

## Qué cuenta como evidencia

- **La hipótesis se apoya si b > 0 y es significativo (p < 0,05)** en el modelo del mercado o en el panel de empresas, para el **retorno de apertura**. Esa es la prueba central.
- El retorno de la sesión es secundario: dentro de la sesión pueden publicarse otras notas.
- **Corrección por pruebas múltiples:** Benjamini-Hochberg dentro de cada grupo.
  - Grupo 1: las 4 pruebas principales (mercado y panel, apertura y sesión).
  - Grupo 2: las 34 pruebas por empresa.
- **Control de calibración:** se repite con el tono mezclado al azar entre ruedas. Si el modelo está bien, alrededor del 5% de los p da menos de 0,05.
- **Control de dirección:** se informa la relación entre el tono pre-apertura y el retorno del día anterior. Se espera positiva, porque muchas notas de la noche cuentan cómo cerró el mercado. Por eso ese retorno entra como control.

## Robustez (agregada el 24/10/2026, todavía antes de correr)

- **Sin los dos días electorales** (08/09 y 27/10). Son los mayores saltos de apertura del período, y su noticia es la elección misma.
  Un solo punto así puede dominar una regresión. Por eso se informa el resultado con ellos (principal) y sin ellos.

## Lo que se informa pase lo que pase

Todos los coeficientes, p-valores y la conclusión, sea a favor o en contra de la hipótesis.
