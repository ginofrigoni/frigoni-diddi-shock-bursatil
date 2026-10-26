// Genera Documentacion_U6b_Noticias_Preapertura.docx dentro de ../06b_noticias_preapertura/
// Uso:  node build_doc_u6b.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, miles, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "06b_noticias_preapertura");
const r = leerResumen(path.join(CARPETA, "resumen_u6b.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const pr = leerCsv(path.join(CARPETA, "resultados_principales.csv"));
const det = leerCsv(path.join(CARPETA, "resultados_empresas.csv"));
const serie = leerCsv(path.join(CARPETA, "serie_preapertura.csv"));
const v = k => Number(r[k].valor);
const pv = x => Number(x) < 0.0001 ? "< 0,0001" : coma(x, 3);
const fila = (muestra, nivel, ret) => pr.find(x => x.muestra === muestra && x.nivel.startsWith(nivel) && x.retorno === ret);
const mA = fila("todas las ruedas", "mercado", "ret_apertura"), pA = fila("todas las ruedas", "panel", "ret_apertura");
const mAs = fila("sin días electorales", "mercado", "ret_apertura"), pAs = fila("sin días electorales", "panel", "ret_apertura");
const algunaSig = pr.filter(x => x.muestra === "todas las ruedas" && x.retorno === "ret_apertura").some(x => Number(x.p) < 0.05);
const elect = serie.filter(x => x.electoral === "1");
const NOMBRE_ELEC = { "2025-09-08": "08/09/2025 (tras las bonaerenses)", "2025-10-27": "27/10/2025 (tras las legislativas)" };

const doc = u.documentoUnion({
  titulo: "U6b · Noticias publicadas con el mercado cerrado",
  subtitulo: "La prueba más directa de la hipótesis principal: ¿el tono de la noche anticipa la apertura?",
  encabezado: "U6b · Noticias pre-apertura — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\06b_noticias_preapertura\\"),
    plain(". Script: "), code("noticias_preapertura.py"), plain(". Especificación previa: "), code("especificacion_previa.md"), plain(".")],
  children: [
    refBox("En una frase", [
      `El tono de las ${miles(v("notas_preapertura"))} notas publicadas con el mercado cerrado va en la dirección de la hipótesis (notas más positivas, apertura más alta), ` +
      `pero no llega a ser significativo (p = ${pv(mA.p)} en el mercado y ${pv(pA.p)} en las empresas), y sin los dos días electorales se achica a menos de la mitad. ` +
      "La hipótesis de que el tono de las noticias anticipa al mercado no encuentra apoyo, ni siquiera con la prueba más favorable.",
    ]),

    h1("1. Por qué esta prueba"),
    p("En U6 el tono no anticipó los precios. Pero quedaba una duda: dentro de una misma rueda, el tono y el retorno se mueven juntos, y con datos diarios no se sabe quién movió a quién. " +
      "Esta prueba resuelve esa duda usando la hora de cada nota."),
    p("Las notas publicadas entre el cierre de la rueda anterior (17:00) y la apertura (11:00) salen antes de cualquier operación de la rueda. El precio de esa rueda no puede haberlas causado. " +
      "Si su tono anticipa el salto de apertura, eso es noticias → mercado sin ambigüedad. Es la prueba más favorable posible para la hipótesis principal."),
    p([bold("Ejemplo. "), plain("A las 21:00 sale una nota muy positiva. Al día siguiente, ¿el mercado abre más arriba de lo que cerró? Si eso pasa en general, las noticias movieron el precio, " +
      "porque la nota existió antes que cualquier operación de esa rueda.")]),

    h1("2. Fijada antes de ver los resultados"),
    p("Para que el resultado valga, sea cual sea, la especificación se escribió y se guardó antes de correr ningún cálculo (especificacion_previa.md). " +
      "Define qué notas se usan, qué variables, qué modelos y qué cuenta como evidencia. La única agregación posterior, todavía antes de correr, fue informar también el resultado sin los dos días electorales."),
    bullet([bold("Notas: "), plain(`las asignadas a la rueda que no se publicaron durante la sesión (11:00 a 17:00), sin las de hora sospechosa: ${miles(v("notas_preapertura"))} notas. ` +
      `${r.notas_preapertura.detalle.split("; ")[1]}. Todas las ruedas tienen notas de este tipo (mínimo ${v("notas_pre_por_rueda_min")}, mediana ${v("notas_pre_por_rueda_mediana")}).`)]),
    bullet([bold("Tono: "), plain("el tono anormal de esas notas (comparado con las 20 ruedas previas, como en U5) y, para las 17 empresas, su tono propio con solo esas notas.")]),
    bullet([bold("Retornos: "), plain("de apertura (de cierre de ayer a apertura de hoy) y de la sesión (de apertura a cierre). El mercado es el promedio de las 47 acciones, porque los datos no traen la apertura del Merval.")]),
    bullet([bold("Controles: "), plain("el retorno del día anterior, porque muchas notas de la noche cuentan cómo cerró el mercado, y si la rueda viene de un día sin mercado.")]),
    bullet([bold("Evidencia a favor: "), plain("que el tono anticipe el retorno de apertura con signo positivo y p < 0,05, con la corrección por pruebas múltiples.")]),

    h1("3. Resultado"),
    simpleTable(["Muestra", "Nivel", "Retorno", "Efecto por desvío del tono", "p", "p corregido"],
      pr.map(x => [x.muestra, x.nivel.replace(" (promedio de las 47)", ""), x.retorno === "ret_apertura" ? "Apertura" : "Sesión",
        `${Number(x.efecto_por_desvio_pct) > 0 ? "+" : ""}${coma(x.efecto_por_desvio_pct, 3)}%`, pv(x.p), pv(x.p_bh)]), [20, 22, 12, 18, 13, 15]),
    nota(`Efecto por desvío: cuánto cambia el retorno promedio cuando el tono de la noche sube un desvío. Para dimensionarlo: el retorno de apertura del promedio de las 47 varía ` +
      `${coma(v("sd_ret_apertura_pct"))}% de un día a otro (un desvío), y el de la sesión ${coma(v("sd_ret_sesion_pct"))}%.`),
    figure(path.join(CARPETA, "u6b_preapertura.png"), 590),
    nota("Cada punto es una rueda. Horizontal: tono anormal de las notas publicadas con el mercado cerrado. Vertical: retorno promedio de las 47 acciones."),
    p(`El signo va en la dirección de la hipótesis: con notas de la noche más positivas, el mercado abre algo más arriba (${coma(mA.efecto_por_desvio_pct, 2)}% por desvío del tono). ` +
      `Pero ${algunaSig ? "solo una prueba" : "ninguna prueba"} llega al 5% (mercado p = ${pv(mA.p)}; empresas p = ${pv(pA.p)}). ` +
      `Sin los dos días electorales, el efecto del mercado se achica a ${coma(mAs.efecto_por_desvio_pct, 2)}% (p = ${pv(mAs.p)}) y el de las empresas a ${coma(pAs.efecto_por_desvio_pct, 2)}% (p = ${pv(pAs.p)}). ` +
      "Durante la sesión no hay nada."),
    p(`Por empresa, ${v("empresas_p05_sin_corregir")} de 34 pruebas da p < 0,05 sin corregir y ${v("empresas_bh")} después de la corrección: lo esperable por casualidad.`),

    h1("4. Los días electorales"),
    simpleTable(["Rueda", "Notas de la noche", "Tono anormal", "Retorno de apertura", "Retorno de la sesión"],
      elect.map(x => [NOMBRE_ELEC[x.rueda], x.n_notas_pre, coma(x.tono_pre_anormal, 1), `${coma(100 * Number(x.ret_apertura), 1)}%`, `${coma(100 * Number(x.ret_sesion), 1)}%`]),
      [32, 16, 16, 18, 18]),
    p("Los dos días electorales son exactamente el caso que plantea la hipótesis: noticias de la noche muy positivas o muy negativas, y una apertura que salta en la misma dirección. " +
      "Pero lo que mueve al mercado ahí es el resultado de la elección, no el tono con que los medios lo cuentan. Fuera de esos dos días, el tono de la noche casi no se relaciona con la apertura."),

    h1("5. La otra dirección, otra vez"),
    p(`El tono de las notas de la noche se relaciona fuerte con cómo cerró el mercado ese mismo día (correlación ${coma(v("corr_tono_pre_ret_anterior"), 2)}): ` +
      "después de una rueda buena, las notas de la noche son más positivas. Es el mismo resultado de U6 visto desde otro lado: los medios cuentan lo que hizo el mercado. " +
      "Por eso el modelo descuenta el retorno del día anterior; si no, ese reflejo se confundiría con un efecto de las noticias."),

    h1("6. Conclusión"),
    bullet([bold("La hipótesis principal no encuentra apoyo. "), plain("Ni con la prueba más favorable, que usa el orden real en el tiempo, el tono de las noticias anticipa los precios a un nivel significativo.")]),
    bullet([bold("Hay un indicio débil, del signo esperado. "), plain("Se apoya en buena parte en los días electorales, donde la noticia es el hecho mismo.")]),
    bullet([bold("Encaja con un mercado que incorpora la información rápido. "), plain("Los hechos grandes (las elecciones) se reflejan de inmediato en la apertura. El tono habitual de la cobertura no agrega información que el precio no tenga ya, " +
      "y en cambio sí refleja lo que el precio ya hizo.")]),

    h1("7. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),

    h1("8. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("especificacion_previa.md")], "La especificación, escrita antes de correr el análisis"],
      [[code("serie_preapertura.csv")], "Por rueda: notas pre-apertura, tono y tono anormal, retornos de apertura, de la sesión y del día anterior"],
      [[code("panel_preapertura.csv")], "Por empresa y rueda: oraciones pre-apertura que la mencionan, su tono y el tono propio pre-apertura"],
      [[code("resultados_principales.csv")], "Las 8 pruebas principales (mercado y panel, apertura y sesión, con y sin días electorales)"],
      [[code("resultados_empresas.csv")], "Las 34 pruebas por empresa"],
      [[code("resumen_u6b.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u6b_preapertura.png")], "La figura de la sección 3"],
    ], [34, 66]),

    h1("9. Limitaciones"),
    bullet("Los precios de apertura vienen de Yahoo Finance; en algunos días la apertura puede no reflejar la primera operación real."),
    bullet("El mercado es el promedio simple de las 47 acciones, no el Merval (que pondera por tamaño)."),
    bullet("Se excluyen las notas con hora sospechosa; si eran pre-apertura, la prueba pierde esa información."),
    bullet("Un año de datos: un efecto chico podría existir y no detectarse. El indicio de esta prueba (p ≈ 0,1) es compatible con un efecto chico o con ninguno."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U6b_Noticias_Preapertura.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
