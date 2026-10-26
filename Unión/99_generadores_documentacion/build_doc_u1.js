// Genera Documentacion_U1_Alineacion.docx dentro de ../01_alineacion_noticias_ruedas/
// Uso:  node build_doc_u1.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, miles, coma, fecha } = u;

const CARPETA = path.join(u.RAIZ_UNION, "01_alineacion_noticias_ruedas");
const r = leerResumen(path.join(CARPETA, "resumen_u1.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const v = k => Number(r[k].valor);
const enVentana = v("notas_en_ventana_union");
const pct = k => coma(100 * v(k) / enVentana);
const [rIni, rFin] = r.notas_en_ventana_union.detalle.replace("ruedas ", "").split(" a ");

const doc = u.documentoUnion({
  titulo: "U1 · Cada noticia a su rueda",
  subtitulo: "En qué día de bolsa pudo reaccionar el mercado a cada noticia",
  encabezado: "U1 · Alineación de noticias y ruedas — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\01_alineacion_noticias_ruedas\\"),
    plain(". Script: "), code("alinear_noticias_ruedas.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `Cada una de las ${miles(v("notas"))} notas quedó asignada a la rueda en la que el mercado pudo reaccionar a ella. ` +
      `El ${coma(v("pct_en_ventana_cambia_de_dia"))}% cambia de día respecto de su fecha de publicación, todas las ruedas reciben noticias ` +
      `y los ${v("controles_ok")} controles automáticos pasan.`,
    ]),

    h1("1. Qué problema resuelve"),
    p("Las noticias salen todos los días y a cualquier hora; el precio de una acción se forma solo en las ruedas, de lunes a viernes de 11 a 17 horas. " +
      "Para medir si una noticia mueve el precio, hay que compararla con el primer precio que pudo verse afectado por ella."),
    p([bold("Ejemplo. "), plain("Una nota del martes a las 20:00 sale con el mercado cerrado: el precio del martes ya estaba formado. " +
      "La primera vez que alguien puede comprar o vender con esa información es el miércoles. Una nota del sábado, lo mismo: cuenta para el lunes. " +
      "Si se uniera \"fecha con fecha\", la nota de la noche se compararía con un precio anterior a ella, y la del sábado se perdería.")]),

    h1("2. La regla"),
    bullet([bold("Hora argentina. "), plain(`Clarín, Infobae y La Nación informan la hora en UTC (tres horas más). Se pasa todo a hora argentina; ` +
      `${v("notas_cambia_por_huso")} notas publicadas de noche cambian de fecha con esta conversión.`)]),
    bullet([bold("Antes de las 17:00 de un día con rueda: "), plain("cuenta para esa rueda.")]),
    bullet([bold("A las 17:00 o después: "), plain("cuenta para la rueda siguiente. Las 17:00 en punto ya cuentan como después del cierre.")]),
    bullet([bold("En un día sin rueda (fin de semana o feriado): "), plain("cuenta para la primera rueda posterior.")]),
    p([plain("El calendario de ruedas es el del lado bursátil ("), code("03_vix_argentino/vix_arg.csv"),
      plain("), el mismo que usan el VIX y el régimen. La ventana de la unión empieza en la rueda del "), plain(fecha(rIni)),
      plain(" y termina en la del "), plain(fecha(rFin)), plain(".")]),

    h1("3. Resultado"),
    simpleTable(["Dónde quedó cada nota", "Notas", "%"], [
      ["En su mismo día (antes de las 17:00 de un día con rueda)", miles(v("en_ventana_rueda_del_dia")), pct("en_ventana_rueda_del_dia")],
      ["En la rueda siguiente, por salir después del cierre", miles(v("en_ventana_tras_el_cierre")), pct("en_ventana_tras_el_cierre")],
      ["En la rueda siguiente, por salir en un día sin rueda", miles(v("en_ventana_dia_sin_rueda")), pct("en_ventana_dia_sin_rueda")],
      [[bold("Total dentro de la ventana de la unión")], [bold(miles(enVentana))], [bold("100")]],
      ["Fuera: van a ruedas de enero a abril de 2025", miles(v("notas_antes_de_la_ventana")), "—"],
      ["Fuera: publicadas después del cierre del 30/04/2026", miles(v("notas_despues_del_calendario")), "—"],
    ], [64, 18, 18]),
    p(`Las ${v("notas_antes_de_la_ventana")} notas de enero a marzo de 2025 son las que motivaron empezar la unión en mayo: con tan pocas notas no hay serie. ` +
      `Las ${v("notas_despues_del_calendario")} del final son del 30/04/2026 a la noche y del 1 al 3 de mayo: su rueda caería después del calendario bursátil.`),
    figure(path.join(CARPETA, "u1_alineacion.png"), 590),
    nota("Arriba: hora de publicación de las notas, con la rueda abierta sombreada y el cierre de las 17:00. Las barras rojas son horas repetidas que no pueden ser reales " +
      "(sección 5). Abajo: notas que recibe cada rueda, separadas según de dónde vienen."),

    h1("4. Cuántas notas recibe cada rueda"),
    p(`Todas las ${v("ruedas_ventana")} ruedas de la ventana reciben noticias: mínimo ${v("notas_por_rueda_min")}, mediana ${v("notas_por_rueda_mediana")} ` +
      `y máximo ${v("notas_por_rueda_max")}. Esta cantidad es la variable de atención de los medios que pide el plan de tesis (decisión D2) y queda en ` +
      `notas_por_rueda.csv, separada por portal.`),
    bullet([bold("Los lunes reciben el fin de semana. "), plain(`Mediana de ${v("notas_mediana_lunes")} notas los lunes contra ${v("notas_mediana_resto")} el resto de los días: ` +
      "las barras violetas del gráfico son las notas del sábado y del domingo.")]),
    bullet([bold("La rueda con más notas "), plain(`es la del ${fecha(r.rueda_mas_notas.valor)} (${r.rueda_mas_notas.detalle}): el viernes 15/08/2025 fue feriado, ` +
      "así que esa rueda junta las notas de cuatro días.")]),
    bullet([bold("La espera más larga "), plain(`es de ${v("max_dias_hasta_rueda")} días: una nota del viernes ${fecha(r.max_dias_hasta_rueda.detalle)} a la noche ` +
      "cuenta para el miércoles 18/02/2026, porque el lunes 16 y el martes 17 fueron feriados de Carnaval.")]),
    bullet([bold("Abril de 2026 "), plain("recibe menos notas porque iProfesional, el portal más grande, casi no tiene notas ese mes (hueco de recolección documentado por Gino).")]),
    p("Como una rueda que viene de un fin de semana o un feriado junta más notas, en los modelos la cantidad de notas se va a usar comparada con lo habitual " +
      "para ese día de la semana, y no en bruto. Eso se define en U2."),

    h1("5. Horas sospechosas"),
    p(`El ${coma(v("pct_hora_sospechosa"))}% de las notas (${miles(v("notas_hora_sospechosa"))}) tiene una hora que se repite demasiado dentro de su portal: ` +
      "más del 3% de las notas del portal a un mismo minuto, cuando lo normal sería una fracción mínima. No es la hora real de cada nota, sino una hora " +
      "por defecto del sitio. Son estas:"),
    p([code(r.notas_hora_sospechosa.detalle)]),
    p("La mayoría (Clarín a las 07:00 y 07:08, Ámbito a las 00:00, TN a las 05:55) cae de madrugada o temprano, así que la regla las manda a la rueda del mismo día. " +
      "Si en realidad esas notas salieron la noche anterior, ya estarían en la rueda correcta; si salieron después de las 17:00, deberían ir a la siguiente. " +
      "No hay forma de saberlo con los datos: se marcan con hora_sospechosa = sí, y en U8 se repiten los resultados sin ellas."),

    h1("6. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),
    p("Los dos controles contra los archivos de Gino importan especialmente: las notas son exactamente las mismas que tienen sentimiento, con el mismo portal, " +
      "y tomando la fecha sin convertir se reproduce la fecha que usa su serie diaria. La única diferencia con su serie es la regla de la rueda."),

    h1("7. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("nota_a_rueda.csv")], "Una fila por nota: url, portal, fecha original, hora argentina, si salió después del cierre, si fue en día sin rueda, rueda asignada, días de espera, motivo, si está en la ventana y si la hora es sospechosa"],
      [[code("notas_por_rueda.csv")], "Una fila por rueda de la ventana: notas totales, según de dónde vienen (mismo día, tras el cierre, día sin rueda), con hora sospechosa y por portal"],
      [[code("resumen_u1.csv")], "Las cifras de este documento"],
      [[code("verificaciones.csv")], "Los controles de la sección 6"],
      [[code("u1_alineacion.png")], "La figura de la sección 3"],
    ], [30, 70]),

    h1("8. Limitaciones"),
    bullet("La regla supone que el mercado reacciona en la primera rueda posible. Si una noticia tarda más en difundirse, el efecto aparecerá en rezagos posteriores, y eso lo mide el VAR (U6)."),
    bullet("Se usa la hora de publicación que informa cada portal. Además de las horas sospechosas, una nota puede actualizarse después de publicada; se toma la primera hora informada."),
    bullet("El cierre se fija a las 17:00 para todo el período. Si en algún día puntual la rueda cerró a otra hora, las notas de ese tramo quedan del lado equivocado."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U1_Alineacion.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
