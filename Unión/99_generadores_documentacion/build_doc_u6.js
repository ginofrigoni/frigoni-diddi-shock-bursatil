// Genera Documentacion_U6_VAR_Granger.docx dentro de ../06_var_granger/
// Uso:  node build_doc_u6.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "06_var_granger");
const r = leerResumen(path.join(CARPETA, "resumen_u6.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const gr = leerCsv(path.join(CARPETA, "granger_resultados.csv"));
const rg = leerCsv(path.join(CARPETA, "regimen_resultados.csv"));
const v = k => Number(r[k].valor);
const d = k => r[k].detalle;
const pv = x => Number(x) < 0.0001 ? "< 0,0001" : coma(x, 4);
const sigTxt = x => x.signif_bh === "True" ? "Sí" : (Number(x.p) < 0.05 ? "Solo sin corregir" : "No");
const dir = x => x.direccion === "noticias → mercado" ? "Noticias → mercado" : "Mercado → noticias";
const fecha = s => s.slice(0, 10).split("-").reverse().join("/");
const [ini, fin] = d("ruedas").split(" a ");

const mercado = gr.filter(x => x.nivel === "mercado");
const empresa = gr.filter(x => x.nivel === "empresa");
const propio = gr.filter(x => x.nivel === "propio");
const sector = gr.filter(x => x.nivel === "sector");
const resumenNivel = (filas, pruebas) => pruebas.map(pr => {
  const g = filas.filter(x => x.prueba === pr);
  const bh = g.filter(x => x.signif_bh === "True");
  return [pr, g.length, g.filter(x => Number(x.p) < 0.05).length, bh.length,
    bh.length ? `${bh.filter(x => x.signo === "+").length} +, ${bh.filter(x => x.signo === "−").length} −` : "—"];
});
const irf = (imp, resp, h) => { const x = r[`irf_${imp}__${resp}__h${h}`]; return { val: Number(x.valor), fuera: x.detalle.includes("distinto") }; };
const r1 = irf("ret_merval", "sent_anormal", 1), r2 = irf("ret_merval", "sent_anormal", 2), r3 = irf("ret_merval", "sent_anormal", 3);
const t0 = irf("sent_anormal", "ret_merval", 0), t1 = irf("sent_anormal", "ret_merval", 1);
const propSig = propio.filter(x => x.signif_bh === "True" && x.causa === "retorno").map(x => x.unidad.replace(".BA", ""));
const propNoSig = propio.filter(x => x.causa === "retorno" && x.signif_bh !== "True").map(x => x.unidad.replace(".BA", ""));
const nmEmpresa = empresa.filter(x => x.direccion === "noticias → mercado" && x.signif_bh === "True");
const nmPropio = propio.filter(x => x.direccion === "noticias → mercado" && x.signif_bh === "True");
const retTonoEmp = empresa.filter(x => x.prueba === "retorno → tono");
// Precisión de U8: en qué franja de publicación está el efecto retorno → tono.
const franjas = leerCsv(path.join(u.RAIZ_UNION, "08_robustez", "efecto_por_franja.csv"))
  .map(x => ({ ...x, efecto_por_desvio_ret: Number(x.efecto_por_desvio_ret), p: Number(x.p) }));
const frNoche = franjas.find(x => x.franja.startsWith("noche")), frManana = franjas.find(x => x.franja.startsWith("madrugada"));
const regFila = (causa, efecto, cuando) => rg.find(x => x.causa === causa && x.efecto === efecto && x.cuando === cuando);

const doc = u.documentoUnion({
  titulo: "U6 · VAR, Granger e impulso-respuesta",
  subtitulo: "¿Las noticias anticipan al mercado, o el mercado anticipa a las noticias?",
  encabezado: "U6 · VAR y Granger — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\06_var_granger\\"),
    plain(". Script: "), code("var_granger.py"), plain(".")],
  children: [
    refBox("En una frase", [
      "El mercado anticipa a las noticias, y no al revés. Cuando el Merval sube, el tono de las noticias de las ruedas siguientes es más positivo; " +
      `pasa en el mercado, en ${retTonoEmp.filter(x => x.signif_bh === "True").length} de las 47 empresas, en ${propSig.length} de las 17 con tono propio y en casi todos los sectores, ` +
      "siempre con el mismo signo. En la dirección contraria, de las noticias hacia los precios o el volumen, no aparece nada consistente.",
    ]),

    h1("1. Qué pregunta responde"),
    p("Es la pregunta central de la tesis: si el tono de las noticias económicas ayuda a anticipar lo que hacen los precios y el volumen operado, o si es al revés, " +
      "y las noticias reflejan lo que el mercado ya hizo. Se mira siempre en las dos direcciones."),
    p(`Se usan las ${v("ruedas")} ruedas del ${fecha(ini)} al ${fecha(fin)}: las 244 de la ventana de la unión menos las 20 primeras, ` +
      "que no tienen tono anormal ni atención porque les faltan 20 ruedas previas de referencia."),

    h1("2. Las herramientas, en simple"),
    p([bold("VAR. "), plain("Un modelo que explica cada variable de hoy con lo que pasó en los días anteriores con todas las variables. Por ejemplo, el retorno de hoy " +
      "con los retornos, el volumen y el tono de las ruedas previas. Cuántos días hacia atrás mira (los rezagos) lo elige el propio modelo, entre 1 y 5, con el criterio AIC.")]),
    p([bold("Causalidad de Granger. "), plain("Pregunta si conocer el pasado de una variable mejora la predicción de otra. \"El tono causa en sentido de Granger al retorno\" " +
      "quiere decir que el tono de los días anteriores ayuda a anticipar el retorno. No prueba una causa en sentido estricto: prueba que una variable se mueve antes que la otra.")]),
    p([bold("Impulso-respuesta. "), plain("Simula un golpe de un desvío en una variable y muestra cómo responden las demás en las ruedas siguientes, con una banda del 95%. " +
      "Si la banda no toca el cero, la respuesta es distinta de cero. Para ordenar el golpe, las noticias van primero: una nota asignada a una rueda puede mover el precio de ese día, " +
      "pero el precio de ese día no puede cambiar una nota ya publicada.")]),
    p([bold("Muchos tests a la vez. "), plain(`Se hicieron ${v("tests_granger")} tests de Granger. Aunque no hubiera ningún efecto real, al 5% saldrían unos 15 \"significativos\" por casualidad. ` +
      "Por eso cada p-valor se corrige con el método de Benjamini-Hochberg, dentro de cada nivel. En las tablas, \"Sí\" significa significativo después de la corrección.")]),
    p([bold("Control de calibración. "), plain(`Se repitió el test por empresa con el tono mezclado al azar (${d("placebo_pct_p05").split(" tests")[0]} tests): ` +
      `dio p < 0,05 en el ${coma(v("placebo_pct_p05"))}% de los casos, cerca del 5% que corresponde. El test no inventa resultados.`)]),
    simpleTable(["Nivel", "Variables del VAR", "Modelos"], [
      ["Mercado", "Tono anormal, atención anormal, retorno del Merval, monto operado anormal", "1"],
      ["Empresa", "Tono anormal del mercado, retorno y volumen anormal de la acción", "47"],
      ["Tono propio", "Lo anterior más el tono propio de la empresa", "17"],
      ["Sector", "Tono anormal, retorno y volumen anormal promedio del sector", "10"],
      ["Régimen", "¿Cambia el efecto en los días Tenso? (todos los días, con una marca de día Tenso)", "4 regresiones"],
    ], [18, 64, 18]),

    h1("3. El mercado"),
    simpleTable(["Prueba", "Dirección", "p", "p corregido", "Significativo"],
      mercado.map(x => [x.prueba, dir(x), pv(x.p), pv(x.p_bh), sigTxt(x)]), [26, 26, 15, 15, 18]),
    p(`De las ocho pruebas, una sola es significativa, y es fuerte: el retorno del Merval anticipa el tono de las noticias (p corregido ${pv(mercado.find(x => x.prueba === "retorno → tono").p_bh)}). ` +
      "Ninguna prueba en la dirección de las noticias hacia el mercado llega a ser significativa, tampoco la atención de los medios."),
    figure(path.join(CARPETA, "u6_irf_mercado.png"), 590),
    nota("Respuesta de cada variable, en las ruedas siguientes, a un golpe de un desvío en otra. La banda es el intervalo del 95%; si no toca el cero, la respuesta es distinta de cero."),
    p([bold("Cuánto. "), plain(`Un día en que el Merval sube un desvío (${coma(v("sd_ret_merval"))}%), el tono anormal de las noticias sube ${coma(r1.val, 2)} puntos en la rueda siguiente ` +
      `y ${coma(r2.val, 2)} en la segunda (las dos distintas de cero); a la tercera (${coma(r3.val, 2)}) ya no se distingue de cero. ` +
      `Un desvío del tono anormal son ${coma(v("sd_sent_anormal"))} puntos: la suba de la rueda siguiente es de un tercio de desvío.`)]),
    p([bold("El mismo día. "), plain(`El tono y el retorno de una misma rueda se mueven juntos (correlación de las sorpresas: ${coma(v("corr_mismo_dia_tono_retorno"), 2)}). ` +
      `El impulso-respuesta lo atribuye a las noticias (${t0.fuera ? "distinto de cero" : "no distinto de cero"} en la rueda del golpe), pero solo porque las noticias se ordenaron primero: ` +
      "con datos diarios no se puede saber quién movió a quién dentro de una misma rueda. Desde la rueda siguiente, el efecto del tono sobre el retorno " +
      `${t1.fuera ? "es distinto de cero" : "ya no se distingue de cero"}.`)]),

    h1("4. Las 47 empresas"),
    simpleTable(["Prueba", "Tests", "p < 0,05 sin corregir", "Significativos (BH)", "Signo"],
      resumenNivel(empresa, ["tono → retorno", "tono → volumen", "retorno → tono", "volumen → tono"]), [30, 12, 20, 20, 18]),
    figure(path.join(CARPETA, "u6_empresas.png"), 420),
    nota("Cada fila es una empresa y cada columna una prueba. Más oscuro, p más chico; ○ p < 0,05 sin corregir; ● significativo después de la corrección."),
    p(`El retorno de casi todas las empresas anticipa el tono de las noticias (${retTonoEmp.filter(x => x.signif_bh === "True").length} de 47, todas con signo positivo). ` +
      "Hay que leerlo con cuidado: en este nivel el tono es el del mercado, no el de cada empresa, y los retornos de las empresas se mueven junto con el Merval. " +
      "En buena parte es el mismo hallazgo del mercado repetido 47 veces. La evidencia propia de cada empresa está en la sección siguiente."),
    p(`En la dirección contraria, ${empresa.filter(x => x.direccion === "noticias → mercado" && Number(x.p) < 0.05).length} de 94 pruebas dan p < 0,05 sin corregir, ` +
      `cuando por azar se esperarían unas ${coma(v("esperados_por_azar_empresa"))}. Después de la corrección quedan ${nmEmpresa.length} ` +
      `(${nmEmpresa.map(x => `${x.unidad.replace(".BA", "")}: ${x.prueba}`).join("; ")}). Es lo esperable por casualidad; no hay un patrón.`),

    h1("5. El tono propio de las 17 empresas"),
    p("Acá la variable de noticias es el tono propio: cuánto mejor o peor se habla de la empresa que del mercado, con más peso cuantas más oraciones (U4). " +
      "Es la prueba más exigente, porque descuenta el clima general."),
    simpleTable(["Prueba", "Tests", "p < 0,05 sin corregir", "Significativos (BH)", "Signo"],
      resumenNivel(propio, ["tono propio → retorno", "tono propio → volumen", "retorno → tono propio", "volumen → tono propio"]), [30, 12, 20, 20, 18]),
    p(`En ${propSig.length} de las 17 empresas, cuando la acción sube, en las ruedas siguientes se habla de ella mejor que del resto del mercado (${propSig.join(", ")}). ` +
      `No aparece en ${propNoSig.join(" ni ")}. Es el resultado más fuerte de la tesis, porque es específico de cada empresa: no se explica por el clima general de las noticias.`),
    p(`En la dirección contraria queda ${nmPropio.length} prueba significativa (${nmPropio.map(x => `${x.unidad.replace(".BA", "")}: ${x.prueba}`).join("; ")}), ` +
      "aislada y sin patrón: el tono propio no anticipa ni el retorno ni el volumen de las empresas."),

    h1("6. Los sectores"),
    simpleTable(["Sector (acciones)", "Tono → retorno", "Tono → volumen", "Retorno → tono", "Volumen → tono"],
      [...new Set(sector.map(x => x.unidad))].map(sec => [sec, ...["tono → retorno", "tono → volumen", "retorno → tono", "volumen → tono"].map(pr => {
        const x = sector.find(y => y.unidad === sec && y.prueba === pr); return x.signif_bh === "True" ? `Sí (${x.signo})` : (Number(x.p) < 0.05 ? "sin corregir" : "—");
      })]), [28, 18, 18, 18, 18]),
    p(`El retorno anticipa el tono en ${sector.filter(x => x.prueba === "retorno → tono" && x.signif_bh === "True").length} de los 10 sectores; la excepción es Tecnología, que es una sola acción (BOLT). ` +
      "En la otra dirección, solo en Conglomerado el tono anticipa el volumen, y con signo negativo: un resultado aislado."),

    h1("7. Días Calmo contra días Tenso"),
    p("Para ver si el efecto cambia cuando el mercado está nervioso, no se separaron los días de cada régimen (eso pegaría días que no son consecutivos). " +
      "Se usaron todos los días con una marca de día Tenso, y se probó el efecto en los días Calmo, en los Tenso y la diferencia. Los días Moderado no se usan como efecto."),
    simpleTable(["Prueba", "En días Calmo", "En días Tenso", "Diferencia"],
      [["sent_anormal", "ret_merval"], ["sent_anormal", "monto_anormal"], ["ret_merval", "sent_anormal"], ["monto_anormal", "sent_anormal"]].map(([c, e]) => {
        const f = q => { const x = regFila(c, e, q); return `p = ${pv(x.p)}${x.signif_bh === "True" ? " (Sí)" : ""}`; };
        return [regFila(c, e, "en días Calmo").prueba, f("en días Calmo"), f("en días Tenso"), f("diferencia Tenso − Calmo")];
      }), [25, 25, 25, 25]),
    p(`El retorno anticipa el tono tanto en días Calmo como en días Tenso, sin diferencia entre ellos. El volumen anticipa el tono solo en los días Tenso, ` +
      `pero la diferencia con los días Calmo no llega a ser significativa después de la corrección. Hay ${regFila("ret_merval", "sent_anormal", "en días Calmo").n_tenso} ` +
      "días Tenso con datos: es poco para afirmar diferencias entre regímenes. En ningún régimen el tono anticipa al mercado."),

    h1("8. Cómo leer el resultado"),
    bullet([bold("Los medios siguen al mercado. "), plain("Después de una suba, las notas asignadas a las ruedas siguientes son más positivas, en general y para cada empresa: " +
      "después de que una acción sube, se habla mejor de esa empresa que del resto.")]),
    refBox("Precisión de U8: cuándo lo siguen", [
      `La prueba de robustez (U8) separó las notas según la hora en que se publicaron. El efecto está en las notas de la misma noche, entre las 17:00 y la medianoche del día de la rueda: ` +
      `un desvío del retorno sube su tono ${coma(frNoche.efecto_por_desvio_ret, 1)} puntos (p ${frNoche.p < 0.0001 ? "< 0,0001" : coma(frNoche.p, 4)}). En las notas de la mañana siguiente ` +
      `es casi nulo (${coma(frManana.efecto_por_desvio_ret, 1)} puntos, p = ${coma(frManana.p, 2)}). La regla de las 17:00 manda las notas de la noche a la rueda siguiente, y por eso acá el efecto ` +
      "aparece como \"el retorno anticipa el tono de las ruedas siguientes\". Lo que pasa en realidad es que, después del cierre, los medios cuentan cómo le fue al mercado y a cada empresa " +
      "con un tono que acompaña la suba o la baja, y no hay un efecto que dure días. Usando solo las notas del día antes del cierre, el resultado desaparece, también en el tono propio de las empresas.",
    ]),
    bullet([bold("No hay evidencia de que el tono anticipe a los precios. "), plain("Ni en el mercado, ni en las empresas, ni en los sectores, ni según el régimen. " +
      "Es lo que esperaría un mercado que incorpora la información rápido: si una noticia mueve el precio, lo hace en la misma rueda, y a la rueda siguiente ya no queda nada para anticipar.")]),
    bullet([bold("La atención de los medios tampoco anticipa el volumen operado. "), plain("Que haya más notas que lo habitual no anuncia más operaciones en los días siguientes.")]),

    h1("9. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),
    p("Un detalle técnico: las bandas del impulso-respuesta son las asintóticas (estimación ± 1,96 errores estándar). Las bandas por simulación de statsmodels 0.14.6 " +
      "devuelven el límite inferior igual al superior, así que no se usaron."),

    h1("10. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("granger_resultados.csv")], `Los ${v("tests_granger")} tests: nivel, unidad, causa, efecto, dirección, rezagos, F, p, p corregido y signo del efecto`],
      [[code("regimen_resultados.csv")], "Las 12 pruebas por régimen (Calmo, Tenso y diferencia)"],
      [[code("rezagos.csv")], `Rezagos elegidos y estabilidad de cada uno de los ${v("modelos_var")} VAR`],
      [[code("irf_mercado.csv")], "Impulso-respuesta del mercado, con sus bandas, para cada par de variables y cada horizonte"],
      [[code("resumen_u6.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u6_irf_mercado.png"), plain(", "), code("u6_empresas.png")], "Las figuras"],
    ], [34, 66]),

    h1("11. Limitaciones"),
    bullet("Granger mide quién se mueve antes, no causas en sentido estricto. Lo que pasa dentro de una misma rueda no se puede ordenar con datos diarios."),
    bullet("Es un año de datos (224 ruedas). Un efecto chico de las noticias sobre los precios podría existir y no detectarse."),
    bullet("El tono depende del modelo de sentimiento, que se entrenó con etiquetas de Gemma sin validación humana, y el tono por empresa es el de las oraciones que la mencionan."),
    bullet("Los retornos están en pesos nominales. Las pruebas de robustez (U8) repiten los resultados principales con otras decisiones."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U6_VAR_Granger.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
