// Genera Documentacion_U2_Sentimiento_por_Rueda.docx dentro de ../02_sentimiento_por_rueda/
// Uso:  node build_doc_u2.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, miles, coma, fecha } = u;

const CARPETA = path.join(u.RAIZ_UNION, "02_sentimiento_por_rueda");
const r = leerResumen(path.join(CARPETA, "resumen_u2.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const reglas = leerCsv(path.join(CARPETA, "reglas_shock.csv"));
const shocks = leerCsv(path.join(CARPETA, "shocks_rueda.csv"));
const v = k => Number(r[k].valor);
const sdNota = v("sd_nota_ajustada");
const azarDe = k => r[k].detalle.replace("azar: ", "").split(";")[0].replace(".", ",");

const NOMBRE_PORTAL = {
  ambito_economia: "Ámbito Economía", ambito_finanzas: "Ámbito Finanzas", clarin_economia: "Clarín Economía",
  clarin_sitemap: "Clarín (sitemap)", eleconomista_sitemap: "El Economista", infobae_economia: "Infobae",
  iprofesional_sitemap: "iProfesional", lanacion_economia: "La Nación", tn_economia: "TN",
};
const portales = Object.keys(r).filter(k => k.startsWith("portal_")).map(k => ({
  nombre: NOMBRE_PORTAL[k.replace("portal_", "")], media: Number(r[k].valor), notas: Number(r[k].detalle),
})).sort((a, b) => b.media - a.media);

const ventana20 = reglas.filter(x => x.serie === "ajustada por portal" && x.ventana === "20");
const filaRegla = (fam, k) => ventana20.find(x => x.familia === fam && Number(x.umbral) === k);
const elegida = reglas.find(x => x.elegida === "True");
const pct = (a, b) => coma(100 * a / b);
const margen = nNotas => coma(sdNota / Math.sqrt(nNotas));
const veces = nNotas => coma(9 / (sdNota / Math.sqrt(nNotas)));
const conGino = Number(r.shocks_coinciden_gino.valor);
const ginoSinMercado = leerCsv(path.join(u.RAIZ_UNION, "00_pipeline_union", "shocks_serie_actual.csv"))
  .filter(x => x.es_rueda === "False").map(x => Number(x.n_articulos)).sort((a, b) => a - b);
const ginoMenos15 = ginoSinMercado.filter(x => x < 15).length;

const doc = u.documentoUnion({
  titulo: "U2 · Sentimiento de mercado por rueda",
  subtitulo: "El tono de las noticias, la atención de los medios y las ruedas de tono extremo",
  encabezado: "U2 · Sentimiento por rueda — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\02_sentimiento_por_rueda\\"),
    plain(". Script: "), code("sentimiento_por_rueda.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `Para cada una de las ${v("ruedas")} ruedas quedan tres variables de noticias: el tono (sentimiento), la atención de los medios ` +
      `(cuántas notas, comparado con lo habitual) y si fue una rueda de tono extremo. Hay ${v("shocks")} ruedas de tono extremo ` +
      `(${v("shocks_pos")} positivas y ${v("shocks_neg")} negativas), elegidas con una regla que tiene en cuenta cuántas notas tiene cada rueda.`,
    ]),

    h1("1. Qué hace este paso"),
    p("Toma la rueda asignada a cada nota en U1 y el sentimiento de cada nota calculado por Gino (versión congelada, decisión D1), y arma tres series por rueda:"),
    bullet([bold("Tono: "), plain("el promedio del sentimiento neto de las notas de la rueda, con igual peso por nota. Es la misma definición de la serie diaria de Gino; solo cambia la regla de la rueda.")]),
    bullet([bold("Atención: "), plain("cuántas notas recibió la rueda, comparado con lo habitual. Es la \"volumetría de publicaciones\" que pide el plan de tesis (decisión D2).")]),
    bullet([bold("Tono extremo (shock): "), plain("si la rueda se aparta mucho del tono habitual. Lo usa el event study (U7).")]),

    h1("2. El tono de las noticias por rueda"),
    p(`El tono medio de las ${v("ruedas")} ruedas es ${coma(v("sent_neto_media"))} puntos, con un desvío de ${coma(v("sent_neto_desvio"))}. ` +
      `La rueda más negativa es la del ${fecha(r.sent_neto_min.detalle)} (${coma(v("sent_neto_min"))}) y la más positiva, la del ` +
      `${fecha(r.sent_neto_max.detalle)} (+${coma(v("sent_neto_max"))}). El tono de una rueda se parece al de la anterior ` +
      `(autocorrelación ${coma(v("autocorrelacion_sentimiento"), 2)}): el clima de las noticias cambia de a poco.`),
    p([bold("Versión ajustada por portal. "), plain("Cada portal tiene su propio tono promedio:")]),
    simpleTable(["Portal", "Tono promedio", "Notas"], portales.map(x => [x.nombre, (x.media > 0 ? "+" : "") + coma(x.media), miles(x.notas)]), [50, 25, 25]),
    p("Un día con muchas notas de TN parecería optimista solo por la mezcla de portales, y abril de 2026, casi sin iProfesional, cambia de composición. " +
      "Para evitarlo, a cada nota se le resta el promedio de su portal antes de promediar. Las dos versiones se parecen mucho " +
      `(correlación ${coma(v("correlacion_simple_vs_portal"), 3)}): la simple va a los modelos y la ajustada se usa para los shocks y como robustez (U8).`),

    h1("3. La atención de los medios"),
    p(`Una rueda que viene de un fin de semana o un feriado junta más notas. La mediana de notas según cuántos días cubre la rueda es: ` +
      `${r.notas_mediana_por_dias_cubiertos.valor.replace(/; /g, " · ").replace(/(\d): /g, "$1 día(s): ")}. Por eso la atención no se mide en bruto, sino en dos pasos:`),
    bullet("se compara la cantidad de notas con la mediana de las ruedas que cubren la misma cantidad de días;"),
    bullet("a eso se le descuenta el nivel de las 20 ruedas previas, para que los cambios lentos (como el hueco de iProfesional) no cuenten como cambios de atención."),
    p(`El resultado es la atención anormal: 0 es lo habitual, +0,69 es el doble de notas y −0,69 la mitad. La más alta es la del ${fecha(r.atencion_max.detalle)} ` +
      `(+${coma(v("atencion_max"), 2)}) y la más baja la del ${fecha(r.atencion_min.detalle)} (${coma(v("atencion_min"), 2)}), en pleno hueco de iProfesional. ` +
      "Las primeras 20 ruedas no tienen valor, porque no tienen 20 ruedas previas de referencia."),
    figure(path.join(CARPETA, "u2_serie.png"), 590),
    nota("Arriba: tono de cada rueda (ajustado por portal), su media de las 20 ruedas previas y las ruedas de tono extremo. Abajo: atención anormal de los medios."),

    h1("4. Cómo se eligen las ruedas de tono extremo"),
    p("Las dos reglas que se compararon responden la misma pregunta, \"¿el tono de hoy es raro?\", pero miden lo normal de forma distinta. " +
      "Supongamos que lo habitual es un tono de 4 y que hoy es 13: hoy está 9 puntos arriba."),
    p([bold("Regla 1: desvío de los días previos (el estilo de la serie de Gino). "), plain(
      "Mira cuánto saltaron los días anteriores. Si de un día a otro el tono suele moverse unos 3 puntos, con un umbral de 2,5 el rango normal va de 4 − 7,5 a 4 + 7,5, " +
      "es decir, de −3,5 a 11,5. Hoy (13) queda afuera: es shock. Esta regla no mira cuántas notas tiene hoy.")]),
    p([bold("Regla 2: por muestreo. "), plain(
      `Pregunta cuánto podría moverse el promedio de hoy solo por casualidad, según cuántas notas tiene. Las notas son muy distintas entre sí (el desvío de una nota es de ${coma(sdNota)} puntos), ` +
      "así que el promedio de pocas notas puede salir cualquier cosa, y el de muchas se estabiliza:")]),
    simpleTable(["", "Hoy con 100 notas", "Hoy con 16 notas"], [
      ["Diferencia con lo habitual", "9 puntos", "9 puntos"],
      ["Cuánto puede moverse el promedio por casualidad", `± ${margen(100)}`, `± ${margen(16)}`],
      ["Veces que la diferencia supera a la casualidad", veces(100), veces(16)],
      ["¿Supera el umbral de 2,5?", "Sí: es shock", "No"],
    ], [46, 27, 27]),
    p("Es el mismo razonamiento que el margen de error de una encuesta: una suba de 9 puntos con 100 encuestados es creíble; con 16, puede ser casualidad."),
    p([bold("La comparación contra el azar. "), plain(
      "Para saber si una regla detecta algo, se mezclaron las notas al azar entre las ruedas, conservando cuántas notas tiene cada una, y se contó cuántos shocks marca cada regla. " +
      `Si marca lo mismo con las notas mezcladas, no detecta nada. Resultado con 20 ruedas de referencia (serie ajustada por portal, ${300} mezclas):`)]),
    simpleTable(["Regla", "Umbral", "Noticias reales", "Notas mezcladas al azar"], [
      ...[1.5, 2, 2.5, 3].map(k => { const x = filaRegla("desvío de los días previos", k); return ["Desvío de los días previos", coma(k), x.shocks, coma(x.azar_promedio)]; }),
      ...[2, 2.5, 3, 3.5].map(k => { const x = filaRegla("por muestreo", k); return [k === 2.5 ? [bold("Por muestreo (elegida)")] : "Por muestreo", coma(k), x.shocks, coma(x.azar_promedio)]; }),
      ["Regla original de Gino (7 días, incluye el día)", "1,5", r.gino_rueda_portal.valor, azarDe("gino_rueda_portal")],
    ], [46, 14, 18, 22]),
    figure(path.join(CARPETA, "u2_reglas.png"), 560),
    p("La regla 1, en todas sus variantes, marca casi lo mismo que el azar. La regla 2 marca bastante más. " +
      `El criterio, fijado antes de mirar el resultado, fue: ventana de 20 ruedas (la del VIX y la volatilidad del lado bursátil) y el umbral que más shocks detecta con a lo sumo 20% de falsos esperados. ` +
      `Quedó el umbral ${coma(elegida.umbral)}: ${elegida.shocks} shocks, contra ${coma(elegida.azar_promedio)} esperables por azar (${coma(elegida.falsos_esperados_pct)}%).`),

    h1("5. Qué significan esos shocks (decisión A)"),
    p("La mezcla al azar supone que las notas de un mismo día son independientes, como personas encuestadas al azar. No lo son: un mismo día todos los medios hablan de los mismos temas, " +
      "como si en una encuesta se preguntara a varios integrantes de una misma familia. Por eso todos los días varían más de lo que predice su cantidad de notas."),
    p(`Medido: la distancia de cada rueda a lo habitual, en \"veces la casualidad\", tiene un desvío de ${coma(v("desvio_z"), 2)} en lugar de 1, y es parejo en casi todas las ruedas ` +
      `(curtosis ${coma(v("curtosis_z"), 2)}, cerca de 0, el valor de una normal). Teniendo eso en cuenta, se esperarían ${coma(v("shocks_esperados_sobredispersion"))} shocks, ` +
      `prácticamente los ${v("shocks")} que hay.`),
    refBox("Decisión del 24/10/2026", [
      `Los ${v("shocks")} shocks se usan como las ruedas de tono más extremo del período (el 8% más alejado de lo habitual), no como días estadísticamente excepcionales. ` +
      "El event study (U7) pregunta si en esas ruedas se mueve el mercado. En U8 se repite con umbral 3, que deja solo las 8 más extremas.",
    ]),
    p("Esto no afecta al análisis principal: el VAR y Granger (U6) usan la serie completa de tono de las 244 ruedas, no los shocks."),

    h1("6. Las ruedas de tono extremo"),
    simpleTable(["Evento", "Rueda", "Tipo", "Distancia (veces la casualidad)", "Notas", "Día electoral", "También shock en la serie de Gino"],
      shocks.map(x => [x.evento_id, fecha(x.rueda), x.tipo, coma(x.z_shock, 2), x.n_notas, x.dia_electoral ? "Sí" : "", x.coincide_con_shock_gino === "True" ? "Sí" : ""]),
      [10, 15, 13, 20, 10, 14, 18]),
    p(`${conGino} de los ${shocks.length} coinciden con un shock de la serie diaria de Gino. Las diferencias se deben a la regla de la rueda, al ajuste por portal y, sobre todo, ` +
      `a que la regla nueva no marca días con pocas notas: ${ginoSinMercado.length} shocks de la serie de Gino caían en días sin mercado, ` +
      `${ginoMenos15} de ellos con menos de 15 notas (entre ${ginoSinMercado[0]} y ${ginoSinMercado[ginoSinMercado.length - 1]}).`),
    p([bold("Los días electorales. "), plain(
      `La rueda del 27/10/2025, después de las legislativas, es una rueda de tono extremo positivo. La del 08/09/2025, después de las elecciones bonaerenses, ` +
      "tiene tono negativo pero no extremo, aunque el mercado cayó fuerte ese día. Los dos días se analizan aparte en U7, para no atribuirle al tono lo que fue un hecho político.")]),

    h1("7. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),

    h1("8. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("sentimiento_mercado_rueda.csv")], "Una fila por rueda: notas, días que cubre, atención anormal, tono simple y ajustado por portal, porcentaje de cada clase, distancia a lo habitual, shock y evento"],
      [[code("shocks_rueda.csv")], "Las ruedas de tono extremo, con su evento, tipo, distancia, si es día electoral, si coincide con la serie de Gino y qué fechas de calendario junta"],
      [[code("reglas_shock.csv")], "Todas las reglas probadas (2 familias, 4 ventanas, 4 umbrales, 2 versiones del tono) contra el azar"],
      [[code("resumen_u2.csv")], "Las cifras de este documento"],
      [[code("verificaciones.csv")], "Los controles de la sección 7"],
      [[code("u2_serie.png"), plain(", "), code("u2_reglas.png")], "Las figuras"],
    ], [34, 66]),

    h1("9. Limitaciones"),
    bullet("El tono es el promedio de notas con igual peso: una nota corta pesa lo mismo que una larga, como en la serie de Gino."),
    bullet("Las ruedas de tono extremo son las puntas de la variación normal del tono, no días excepcionales; la tesis lo declara así."),
    bullet(`Las primeras 20 ruedas (mayo de 2025) no tienen shocks ni atención anormal, porque no tienen 20 ruedas previas de referencia.`),
    bullet("El ajuste por portal usa el promedio de cada portal en toda la ventana. Si un portal cambió su tono a lo largo del período, el ajuste no lo capta."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U2_Sentimiento_por_Rueda.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
