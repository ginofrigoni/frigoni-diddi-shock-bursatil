// Genera Documentacion_U7b_Shock_Volumen_Noticias.docx dentro de ../07b_shock_volumen_noticias/
// Uso:  node build_doc_u7b.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "07b_shock_volumen_noticias");
const r = leerResumen(path.join(CARPETA, "resumen_u7b.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const res = leerCsv(path.join(CARPETA, "resultados_principales.csv"));
const pre = leerCsv(path.join(CARPETA, "resultados_preapertura.csv"));
const sens = leerCsv(path.join(CARPETA, "sensibilidad_preapertura.csv"));
const sec = leerCsv(path.join(CARPETA, "resultados_secundarios.csv"));
const v = k => Number(r[k].valor);
const det = k => r[k].detalle;
const pv = x => x === "" || x === undefined ? "—" : Number(x) < 0.001 ? "< 0,001" : coma(x, 3);
const ABS = ["abs_ra_dia", "abs_salto"];
const valor = (clave, x) => x === "" ? "—" : clave.startsWith("vol_") ? coma(x, 3) : `${coma(100 * Number(x), 2)}%`;
const fecha = s => s.split("-").reverse().join("/");
const principal = res.filter(x => x.version.startsWith("principal"));
const original = res.filter(x => x.version.startsWith("especificación"));
const de = (tabla, nivel, clave) => tabla.find(x => x.nivel === nivel && x.clave === clave);
const eRa = de(principal, "empresas", "abs_ra_dia"), eVol = de(principal, "empresas", "vol_día [0]");
const mSalto = de(pre, "mercado", "abs_salto"), eSalto = de(pre, "empresas", "abs_salto"), eVolPre = de(pre, "empresas", "vol_día [0]");
const sinUno = sens.reduce((a, b) => (Number(b.p_azar) > Number(a.p_azar) ? b : a));
const filaTabla = x => [x.nivel === "mercado" ? "Mercado" : "Empresas", x.medida.charAt(0).toUpperCase() + x.medida.slice(1), x.n,
  valor(x.clave, x.promedio_eventos), valor(x.clave, x.promedio_dia_cualquiera), pv(x.p_azar), pv(x.p_bh)];
const CAB = ["Nivel", "Medida", "Eventos", "En los shocks", "Día cualquiera", "p (azar)", "p corregido"];
const ANCHOS = [11, 29, 9, 13, 13, 11, 14];
const nEv = k => det(k).split(";")[0];
// Análisis secundarios de empresas: en cuáles el |RA| y el volumen del día dan p < 0,05.
const secEmp = [...new Set(sec.map(x => x.analisis))].map(a => {
  const g = c => Number(sec.find(x => x.analisis === a && x.nivel === "empresas" && x.clave === c).p_azar);
  const nombre = a.replace("robustez: ", "").replace("según el tono (tono > 0)", "los días de tono positivo").replace("según el tono (tono < 0)", "los días de tono negativo");
  return { nombre, ok: g("abs_ra_dia") < 0.05 && g("vol_día [0]") < 0.05 };
});
const seMantiene = secEmp.filter(x => x.ok).map(x => x.nombre), noSeMantiene = secEmp.filter(x => !x.ok).map(x => x.nombre);

const doc = u.documentoUnion({
  titulo: "U7b · Shock de cantidad de noticias",
  subtitulo: "El event study con la definición de shock del plan de trabajo: muchas más notas que lo habitual",
  encabezado: "U7b · Shock de cantidad de noticias — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\07b_shock_volumen_noticias\\"),
    plain(". Script: "), code("shock_volumen_noticias.py"), plain(". Especificación previa: "), code("especificacion_previa.md"), plain(".")],
  children: [
    refBox("En una frase", [
      `Cuando una empresa aparece en muchas más notas que lo habitual, ese mismo día su acción se opera más (volumen anormal ${coma(eVol.promedio_eventos, 2)} contra ` +
      `${coma(eVol.promedio_dia_cualquiera, 2)} de un día cualquiera; p corregido ${pv(eVol.p_bh)}) y su precio se mueve algo más, para un lado o para el otro. ` +
      "No hay una dirección ni un efecto en los días siguientes, y en el mercado en su conjunto no aparece nada. " +
      "Contando solo las notas publicadas con el mercado cerrado, el precio de apertura de las empresas no se mueve más que en un día cualquiera.",
    ]),

    h1("1. Por qué esta prueba"),
    p("El plan de trabajo (sección 4.4) define el shock informativo como un aumento anormal de la cantidad de noticias: la cantidad del día comparada con " +
      "la media de los 30 días previos, medida con un z-score. Si el z-score supera un umbral, hay un evento de shock. La hipótesis H1 del plan dice que ese shock " +
      "tiene un impacto medible sobre el precio o el volumen."),
    p("U7 hizo el event study con las ruedas de tono extremo, y el VAR de U6 usó la cantidad de notas como una variable continua (la atención anormal). " +
      "Faltaba la prueba con la definición literal del plan: tomar los días de muchas más notas que lo habitual y mirar qué pasa con el precio y el volumen alrededor."),
    p([bold("Ejemplo. "), plain("Si una empresa suele aparecer en 2 notas por día y un día aparece en 12, ese día es un shock. " +
      "La pregunta es si ese día (o los siguientes) su acción se mueve o se opera más que en un día cualquiera.")]),

    h1("2. Fijada antes de ver los resultados, con un cambio documentado"),
    p("La especificación se escribió antes de calcular ningún resultado (especificacion_previa.md). Define cómo se marca un shock, qué se mide, cómo se compara " +
      "contra el azar y qué cuenta como evidencia. Un shock de cantidad no tiene signo (muchas notas pueden ser buenas o malas), así que la medida central es " +
      "el tamaño del movimiento del precio el día del shock, para un lado o para el otro, además del volumen."),
    bullet([bold("Shock: "), plain("z-score de la cantidad contra las 30 ruedas previas, mayor que 2. Mercado: notas de la rueda. Empresas (las 17 con tono propio): " +
      "artículos que la mencionan, con al menos 3 en la rueda. Ruedas seguidas con shock cuentan como un solo evento.")]),
    bullet([bold("Medición: "), plain("igual que U7. Merval con modelo de media constante; cada acción con modelo de mercado; ventana de estimación [−25, −4] " +
      "sin los días electorales; los eventos con una elección en su ventana se dejan aparte.")]),
    bullet([bold("Significancia: "), plain("contra fechas al azar (5.000 sorteos) con la corrección de Benjamini-Hochberg sobre las 14 pruebas principales.")]),
    p([bold("El cambio posterior. "), plain(`Con la versión original, los ${parseInt(nEv("eventos_mercado_original"))} eventos del mercado caían todos ` +
      "en la primera rueda después de un día sin mercado (lunes o post-feriado). Por la regla de las 17:00, esa rueda junta las notas de 3 o 4 días: " +
      "comparada con las ruedas previas, casi siempre \"tiene muchas más notas\". La regla marcaba fines de semana, no noticias. " +
      "Se corrigió midiendo la cantidad por día de calendario (la cantidad de la rueda dividida por los días que cubre), que es lo más fiel al \"volumen diario\" del plan. " +
      "El cambio está registrado en la especificación con su fecha y su motivo, y la versión original se informa en la sección 6.")]),
    simpleTable(["Versión", "Eventos del mercado", "Eventos de empresas"], [
      ["Original (por rueda)", det("eventos_mercado_original").split("; ")[1], det("eventos_empresa_original").split("; ")[1]],
      ["Principal (por día de calendario)", det("eventos_mercado_principal").split("; ")[1], det("eventos_empresa_principal").split("; ")[1]],
    ], [34, 33, 33]),
    nota(`Referencia: ${v("ruedas_tras_dia_sin_mercado")} de las ${det("ruedas_tras_dia_sin_mercado").replace("de ", "")} del período vienen después de un día sin mercado.`),

    h1("3. Resultado principal"),
    simpleTable(CAB, principal.map(filaTabla), ANCHOS),
    nota("Retornos en %, volumen en logaritmo (0 = lo habitual). Las medidas en valor absoluto se comparan contra un día cualquiera; las demás, contra 0. " +
      "p (azar): proporción de sorteos de fechas al azar con un promedio al menos tan extremo. p corregido: Benjamini-Hochberg sobre las 14 pruebas."),
    figure(path.join(CARPETA, "u7b_shock_volumen.png"), 600),
    nota("A: retorno anormal acumulado del Merval alrededor de los shocks del mercado, contra el 95% de fechas al azar. B y C: tamaño del movimiento en los shocks " +
      "contra un día cualquiera; C cuenta solo las notas publicadas con el mercado cerrado."),
    bullet([bold("Mercado: "), plain(`con la definición corregida hay ${v("eventos_mercado_principal")} eventos y en ninguna medida se distinguen de un día cualquiera.`)]),
    bullet([bold("Empresas: "), plain(`en los ${eVol.n} shocks de empresa, el volumen anormal del día es claramente mayor (p corregido ${pv(eVol.p_bh)}). ` +
      `El precio se mueve algo más (${valor("abs_ra_dia", eRa.promedio_eventos)} contra ${valor("abs_ra_dia", eRa.promedio_dia_cualquiera)} de un día cualquiera; ` +
      `p ${pv(eRa.p_azar)}), pero tras la corrección queda en el límite (${pv(eRa.p_bh)}). El retorno acumulado no tiene dirección y no hay nada en los días siguientes.`)]),
    bullet([bold("Antes del shock: "), plain("nada significativo tras la corrección. Con la versión corregida, el precio no viene moviéndose antes de que aumente la cantidad de noticias.")]),

    h1("4. Prueba pre-apertura: ¿qué vino primero?"),
    p("La rueda del shock incluye notas publicadas durante esa misma sesión, que pueden estar contando la suba o la baja del día. Por eso \"el precio se mueve más el día del shock\" " +
      "no dice qué vino primero. Esta prueba, agregada antes de correrla, cuenta solo las notas publicadas con el mercado cerrado (el mismo criterio de U6b) y mira el salto de apertura: " +
      "el único precio que se forma después de esas notas y antes de las de la sesión."),
    simpleTable(CAB, pre.map(filaTabla), ANCHOS),
    nota("Salto de apertura anormal. Mercado: apertura sobre cierre anterior del promedio de las 47, menos su promedio habitual. Empresa: su salto menos el del promedio de las 47. " +
      "p corregido: Benjamini-Hochberg sobre estas 6 pruebas."),
    bullet([bold("Empresas: "), plain(`el salto de apertura no es mayor que en un día cualquiera (${valor("abs_salto", eSalto.promedio_eventos)} contra ` +
      `${valor("abs_salto", eSalto.promedio_dia_cualquiera)}; p corregido ${pv(eSalto.p_bh)}). El volumen del día sí tiende a ser mayor (p corregido ${pv(eVolPre.p_bh)}).`)]),
    bullet([bold("Mercado: "), plain(`el salto de apertura es mayor (${valor("abs_salto", mSalto.promedio_eventos)} contra ${valor("abs_salto", mSalto.promedio_dia_cualquiera)}; ` +
      `p corregido ${pv(mSalto.p_bh)}), pero con solo ${mSalto.n} eventos y apoyado en un día: sacando el ${fecha(sinUno.sin_evento)}, el promedio baja a ` +
      `${valor("abs_salto", sinUno.promedio_eventos)} y el p sube a ${pv(sinUno.p_azar)}.`)]),
    simpleTable(["Sin el evento", "Eventos", "Salto promedio", "p (azar)"],
      sens.map(x => [fecha(x.sin_evento), x.n, valor("abs_salto", x.promedio_eventos), pv(x.p_azar)]), [30, 20, 25, 25]),
    p("El 24/09/2025 es el día del anuncio de apoyo financiero del Tesoro de Estados Unidos. Es el mismo patrón que U6b con las elecciones: un hecho grande " +
      "genera muchas noticias y mueve el precio, pero lo que mueve al mercado es el hecho, no la cantidad de cobertura."),

    h1("5. Análisis secundarios"),
    simpleTable(["Análisis", "Nivel", "Eventos", "|retorno anormal| del día: p (azar)", "Volumen del día: p (azar)"],
      [...new Set(sec.map(x => x.analisis))].flatMap(a => ["mercado", "empresas"].map(n => {
        const ra = sec.find(x => x.analisis === a && x.nivel === n && x.clave === "abs_ra_dia");
        const vo = sec.find(x => x.analisis === a && x.nivel === n && x.clave === "vol_día [0]");
        return [a.replace("robustez: ", "Robustez: ").replace("según el tono", "Según el tono"), n === "mercado" ? "Mercado" : "Empresas", ra.n, pv(ra.p_azar), pv(vo.p_azar)];
      })), [36, 13, 11, 20, 20]),
    nota("Sin corrección por pruebas múltiples: son controles de que el resultado de las empresas no depende de una decisión puntual."),
    p(`En las empresas, el movimiento y el volumen del día son mayores (p < 0,05 en las dos medidas) en: ${seMantiene.join("; ")}. ` +
      (noSeMantiene.length ? `No llegan a serlo en: ${noSeMantiene.join("; ")}. ` : "") +
      "En el mercado, ningún análisis secundario se distingue de un día cualquiera."),

    h1("6. La versión original"),
    simpleTable(CAB, original.map(filaTabla), ANCHOS),
    nota("Cantidad por rueda, sin dividir por los días que cubre. Sus eventos del mercado son todos ruedas después de un día sin mercado (sección 2)."),

    h1("7. Conclusión"),
    bullet([bold("H1 encuentra un apoyo parcial, en el volumen. "), plain("Según la regla fijada antes, el volumen anormal del día del shock en las empresas cuenta como evidencia, " +
      "y es significativo tras la corrección. Cuando una empresa está en muchas más notas, ese día se opera más.")]),
    bullet([bold("No hay un efecto con dirección sobre el precio. "), plain("El precio se mueve algo más el día del shock, para un lado o para el otro, pero no sube ni baja de forma sistemática " +
      "y no hay arrastre en los días siguientes.")]),
    bullet([bold("Las notas de la noche no anticipan la apertura de cada empresa. "), plain("Con la prueba que ordena en el tiempo, el precio de apertura no se mueve más. " +
      "El movimiento del día puede ser tanto la reacción a la noticia como la noticia contando el movimiento.")]),
    bullet([bold("Encaja con el resto de la tesis. "), plain("Los hechos grandes (las elecciones, el anuncio del Tesoro de Estados Unidos) mueven el precio y generan muchas noticias a la vez. " +
      "La cantidad de cobertura acompaña a la actividad del mercado, pero no la anticipa.")]),

    h1("8. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),

    h1("9. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("especificacion_previa.md")], "La especificación previa, el cambio posterior, la prueba pre-apertura y la sensibilidad, cada uno con su fecha"],
      [[code("eventos_mercado.csv"), plain(", "), code("eventos_empresa.csv")], "Los eventos de la versión principal, con todas sus medidas"],
      [[code("eventos_*_original.csv"), plain(", "), code("eventos_*_preapertura.csv")], "Los eventos de la versión original y de la prueba pre-apertura"],
      [[code("resultados_principales.csv")], "Las 14 pruebas de la versión principal y las 14 de la original"],
      [[code("resultados_preapertura.csv"), plain(", "), code("sensibilidad_preapertura.csv")], "Las 6 pruebas pre-apertura y el salto del mercado sacando un evento por vez"],
      [[code("resultados_secundarios.csv")], "Por tono de la rueda y las tres pruebas de robustez"],
      [[code("resumen_u7b.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u7b_shock_volumen.png")], "La figura de la sección 3"],
    ], [38, 62]),

    h1("10. Limitaciones"),
    bullet("Pocos eventos de mercado: con la definición corregida son 6, y 5 en la prueba pre-apertura. Un efecto chico en el mercado no se detectaría."),
    bullet("Con datos diarios no se puede ordenar lo que pasa dentro de la sesión; la prueba pre-apertura es la aproximación más cercana."),
    bullet("Algunas acciones argentinas cotizan también en Nueva York (ADR) hasta después del cierre local; las notas de la noche pueden estar contando esos movimientos, " +
      "que la apertura local después refleja."),
    bullet("Los precios de apertura vienen de Yahoo Finance; en algunos días la apertura puede no reflejar la primera operación real."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U7b_Shock_Volumen_Noticias.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
