// Genera Documentacion_U8_Robustez.docx dentro de ../08_robustez/
// Uso:  node build_doc_u8.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "08_robustez");
const r = leerResumen(path.join(CARPETA, "resumen_u8.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const rob = leerCsv(path.join(CARPETA, "robustez.csv"));
const fr = leerCsv(path.join(CARPETA, "efecto_por_franja.csv"));
const v = k => Number(r[k].valor);
const val = (variante, resultado) => { const x = rob.find(y => y.variante === variante && y.resultado === resultado); return x && x.valor !== "" ? Number(x.valor) : null; };
const pv = x => x === null ? "—" : (x < 0.0001 ? "< 0,0001" : coma(x, 4));
const ent = x => x === null ? "—" : String(Math.round(x));
const pct = x => x === null ? "—" : `${x > 0 ? "+" : ""}${coma(x, 2)}%`;
const ETQ = {
  base: "Base (U6 y U7)", portal: "Tono ajustado por portal", nivel: "Tono en nivel (no anormal)", sin_sospechosa: "Sin notas de hora sospechosa",
  calendario: "Fecha de calendario (sin regla de las 17:00)", mismo_dia: "Solo notas del día, antes del cierre", sin_abril: "Sin abril de 2026",
  electorales: "Días electorales como control", sin_iliquidas: "Sin las 4 acciones ilíquidas", filtrado: "Régimen filtrado", no_calmo: "Calmo contra No calmo",
  umbral_3: "Umbral de shocks 3", umbral_2: "Umbral de shocks 2",
};
const principales = ["base", "portal", "nivel", "sin_sospechosa", "calendario", "mismo_dia", "sin_abril", "electorales"];
const frNoche = fr.find(x => x.franja.startsWith("noche")), frManana = fr.find(x => x.franja.startsWith("madrugada"));
const frSesion = fr.find(x => x.franja.startsWith("sesión")), frFinde = fr.find(x => x.franja.startsWith("día sin"));

const doc = u.documentoUnion({
  titulo: "U8 · Robustez",
  subtitulo: "¿Los resultados se sostienen si se cambia una decisión por vez?",
  encabezado: "U8 · Robustez — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\08_robustez\\"),
    plain(". Script: "), code("robustez.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `De ${v("comparaciones")} comparaciones, ${v("se_mantienen")} mantienen la conclusión. Que el tono de las noticias no anticipa al mercado se sostiene en todas las variantes. ` +
      "Que el mercado anticipa al tono también, salvo en dos variantes, y esas dos muestran dónde está el efecto: en las notas publicadas la misma noche, " +
      `después del cierre (un desvío del retorno sube ${coma(frNoche.efecto_por_desvio_ret, 1)} puntos su tono). A la mañana siguiente ya no queda.`,
    ]),

    h1("1. Cómo se prueba"),
    p("Cada resultado de la tesis depende de decisiones: qué tono usar, cómo asignar las notas a las ruedas, qué días incluir. Una prueba de robustez cambia una sola decisión por vez " +
      "y mira si la conclusión sigue en pie. Un resultado que aparece con una sola opción es frágil; uno que aparece con todas se puede defender."),
    p("Antes de cambiar nada, el script rearma todo con las decisiones originales y comprueba que reproduce exactamente U6 y U7 (sección 7). Así las diferencias se deben a la decisión cambiada y no al código."),
    p("Los resultados que se repiten son los principales: en el mercado, si el retorno anticipa el tono y si el tono anticipa el retorno; en las 17 empresas con tono propio y en las 47 con el tono del mercado, " +
      "en cuántas aparece cada dirección; por régimen; y, en el event study, el retorno del Merval en las ruedas de tono extremo positivo."),

    h1("2. Los resultados en cada variante"),
    simpleTable(["Variante", "Retorno → tono (p)", "Tono → retorno (p)", "Retorno → tono propio (de 17)", "Tono propio → retorno (de 17)", "Retorno → tono (de 47)"],
      principales.map(vr => [ETQ[vr], pv(val(vr, "A ret→tono")), pv(val(vr, "A tono→ret")), ent(val(vr, "B retorno→tono propio (de 17)")),
        ent(val(vr, "B tono propio→retorno (de 17)")), ent(val(vr, "C retorno→tono (de 47)"))]), [28, 15, 15, 15, 14, 13]),
    nota(`Los p están corregidos por pruebas múltiples, como en U6. Sin las 4 acciones ilíquidas, el retorno anticipa el tono en ${ent(val("sin_iliquidas", "C retorno→tono (de 43)"))} de 43 empresas ` +
      `y el tono anticipa el retorno en ${ent(val("sin_iliquidas", "C tono→retorno (de 43)"))}.`),
    figure(path.join(CARPETA, "u8_robustez.png"), 560),

    h1("3. Lo que se sostiene en todas las variantes"),
    bullet([bold("El tono no anticipa al mercado. "), plain("En ninguna variante el tono anticipa el retorno, ni en el mercado ni en ninguna empresa. Es el resultado más firme de la tesis.")]),
    bullet([bold("El mercado anticipa al tono, con cualquier tono y sin los días dudosos. "), plain("Se mantiene con el tono ajustado por portal, con el tono en nivel, " +
      "sin las notas de hora sospechosa, sin abril de 2026, con los días electorales como control y sin las acciones ilíquidas.")]),

    h1("4. Lo que cambia, y qué enseña"),
    p("Con dos variantes el efecto del retorno sobre el tono desaparece: la fecha de calendario y las notas del día antes del cierre. Las dos tienen algo en común: " +
      "dejan afuera, o mueven de rueda, las notas publicadas después del cierre. Para ver exactamente dónde está el efecto, se separaron las notas según la franja en que se publicaron " +
      "y se midió, para cada franja, cuánto se relaciona su tono con el retorno de la rueda anterior:"),
    simpleTable(["Franja de publicación", "Notas", "Efecto de un desvío del retorno (puntos de tono)", "p"],
      fr.map(x => [x.franja, x.notas, `${Number(x.efecto_por_desvio_ret) > 0 ? "+" : ""}${coma(x.efecto_por_desvio_ret, 2)}`, pv(Number(x.p))]), [36, 12, 34, 18]),
    p(`El efecto está en las notas de la misma noche, publicadas entre las 17:00 y la medianoche del día de la rueda: un desvío del retorno sube su tono ${coma(frNoche.efecto_por_desvio_ret, 1)} puntos ` +
      `(p ${pv(Number(frNoche.p))}). En las notas del fin de semana es más chico y no llega al 5% (p = ${coma(frFinde.p, 2)}); en las de la madrugada y la mañana siguiente es casi nulo ` +
      `(p = ${coma(frManana.p, 2)}); en las de la sesión, chico (p = ${coma(frSesion.p, 2)}).`),
    p([bold("Qué significa. "), plain("La regla de las 17:00 manda las notas de la noche a la rueda siguiente, y por eso en U6 el efecto aparecía como \"el retorno de hoy anticipa el tono de mañana\". " +
      "En realidad es más directo: después del cierre, los medios cuentan cómo le fue al mercado y a cada empresa, con un tono que acompaña la suba o la baja. Con la fecha de calendario, " +
      "esas notas quedan en el mismo día del retorno, y el efecto pasa a ser del mismo día, que el Granger no mide. A la mañana siguiente, el tono ya no refleja el retorno del día anterior.")]),
    p([bold("Cómo cambia la conclusión. "), plain("No cambia la dirección: los medios siguen al mercado. Precisa el cuándo: lo siguen esa misma noche, en las notas posteriores al cierre, " +
      "y no hay un arrastre que dure días. Con el tono propio de cada empresa pasa lo mismo: usando solo las notas del día antes del cierre, el efecto desaparece en las 17 empresas " +
      `(${ent(val("mismo_dia", "B retorno→tono propio (de 17)"))} de 17, contra ${ent(val("base", "B retorno→tono propio (de 17)"))} en la base). La descomposición por franja se midió para el mercado, no para cada empresa.`)]),

    h1("5. Régimen"),
    simpleTable(["Prueba", "Base", "Régimen filtrado", "Calmo contra No calmo"], [
      ["Retorno → tono en días Calmo", pv(val("base", "D ret→tono en Calmo")), pv(val("filtrado", "D ret→tono en Calmo")), pv(val("no_calmo", "D ret→tono en Calmo"))],
      ["Retorno → tono en días Tenso (No calmo)", pv(val("base", "D ret→tono en Tenso")), pv(val("filtrado", "D ret→tono en Tenso")), pv(val("no_calmo", "D ret→tono en No calmo"))],
      ["Tono → retorno en días Calmo", pv(val("base", "D tono→ret en Calmo")), pv(val("filtrado", "D tono→ret en Calmo")), pv(val("no_calmo", "D tono→ret en Calmo"))],
      ["Tono → retorno en días Tenso (No calmo)", pv(val("base", "D tono→ret en Tenso")), pv(val("filtrado", "D tono→ret en Tenso")), pv(val("no_calmo", "D tono→ret en No calmo"))],
    ], [40, 20, 20, 20]),
    p("Con el régimen filtrado o juntando Moderado con Tenso, la conclusión es la misma: el retorno anticipa el tono en los dos tipos de días y el tono no anticipa el retorno en ninguno."),

    h1("6. Event study"),
    simpleTable(["Variante", "Eventos positivos", "Retorno del Merval el día del evento", "p", "En las 3 ruedas previas"],
      ["base", "umbral_3", "umbral_2", "sin_sospechosa", "sin_abril", "calendario", "mismo_dia"].map(vr => [ETQ[vr], ent(val(vr, "E positivos: eventos")),
        pct(val(vr, "E positivos: día 0 (%)")), pv(val(vr, "E positivos: p día 0")), pct(val(vr, "E positivos: antes (%)"))]), [30, 14, 22, 14, 20]),
    p("La suba del Merval el día de tono extremo positivo se mantiene con el umbral 3 (solo las ruedas más extremas), con el umbral 2 y sin las notas de hora sospechosa. " +
      "Con la fecha de calendario o con solo las notas del día quedan muy pocos eventos para sacar conclusiones."),

    h1("7. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),
    p("El p de la base difiere de U6 en el quinto dígito porque U6 parte del tono redondeado a 4 decimales en el CSV de U2, y U8 lo recalcula sin redondear."),

    h1("8. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("robustez.csv")], "Cada resultado en cada variante, con el número de ruedas y si mantiene la conclusión"],
      [[code("efecto_por_franja.csv")], "El efecto del retorno sobre el tono según la franja de publicación de las notas"],
      [[code("resumen_u8.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u8_robustez.png")], "La figura de la sección 2"],
    ], [34, 66]),

    h1("9. Limitaciones"),
    bullet("Se cambia una decisión por vez; no se prueban todas las combinaciones."),
    bullet("Las franjas horarias usan la hora informada por cada portal; las notas con hora sospechosa están en la base y fuera de la variante que las excluye."),
    bullet("Las variantes que reducen las notas (fecha de calendario, solo notas del día) dejan pocos eventos para el event study."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U8_Robustez.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
