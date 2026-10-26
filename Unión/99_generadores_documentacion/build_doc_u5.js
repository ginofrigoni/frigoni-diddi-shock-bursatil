// Genera Documentacion_U5_ADF.docx dentro de ../05_adf_union/
// Uso:  node build_doc_u5.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "05_adf_union");
const r = leerResumen(path.join(CARPETA, "resumen_u5.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const res = leerCsv(path.join(CARPETA, "resultados_adf_union.csv"));
const mercado = leerCsv(path.join(u.RAIZ_UNION, "04_dataset_unificado", "dataset_mercado.csv"));
const v = k => Number(r[k].valor);

// KPSS solo informa p-valores entre 0,01 y 0,10 (fuera de ese rango los recorta).
const pK = x => Number(x) >= 0.1 ? "≥ 0,10" : Number(x) <= 0.01 ? "≤ 0,01" : coma(x, 3);
const pA = x => Number(x) < 0.0001 ? "< 0,0001" : coma(x, 4);
const NOMBRE = {
  ret_merval: "Retorno del Merval", monto_anormal: "Monto operado anormal", n_notas: "Notas por rueda", atencion_anormal: "Atención anormal",
  sent_neto: "Tono de las noticias (nivel)", sent_neto_portal: "Tono ajustado por portal (nivel)", sent_anormal: "Tono anormal (variable del VAR)",
  sent_portal_anormal: "Tono por portal, anormal", vix_arg: "VIX argentino",
};
const filaMercado = (serie, forma = "") => res.find(x => x.ambito === "mercado" && x.serie === serie && x.forma === forma);
const ordenMercado = [["ret_merval"], ["monto_anormal"], ["atencion_anormal"], ["n_notas"], ["sent_anormal"], ["sent_portal_anormal"],
  ["sent_neto"], ["sent_neto_portal"], ["sent_neto", "cambio de tono"], ["vix_arg"]];
const conteo = (serie, forma = "") => {
  const g = res.filter(x => x.ambito === "panel" && x.serie === serie && x.forma === forma);
  const c = k => g.filter(x => x.conclusion === k).length;
  return [g.length, c("Estacionaria"), c("Estacionaria (ADF)"), c("Inconclusa") + c("No estacionaria")];
};
// Tono promedio por trimestre, para mostrar los ciclos lentos.
const trimestres = {};
// El trimestre se lee del texto de la fecha: new Date("2025-07-01") se interpreta en UTC y, en hora argentina,
// cae el 30/06, lo que mandaría el primer día de cada trimestre al trimestre anterior.
mercado.forEach(x => { const q = `${x.rueda.slice(0, 4)}T${Math.floor((Number(x.rueda.slice(5, 7)) - 1) / 3) + 1}`;
  (trimestres[q] = trimestres[q] || []).push(Number(x.sent_neto)); });
const medTrim = Object.entries(trimestres).map(([q, xs]) => `${q.replace("T", " T")}: ${(xs.reduce((a, b) => a + b, 0) / xs.length > 0 ? "+" : "")}${coma(xs.reduce((a, b) => a + b, 0) / xs.length)}`);
const tono = filaMercado("sent_neto"), anormal = filaMercado("sent_anormal");

const doc = u.documentoUnion({
  titulo: "U5 · Estacionariedad en la ventana de la unión",
  subtitulo: "Qué series se pueden usar en el VAR tal como están y cuál hubo que transformar",
  encabezado: "U5 · ADF de la unión — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\05_adf_union\\"),
    plain(". Script: "), code("adf_union.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `Se probaron ${v("series_probadas")} series en las 244 ruedas de la unión. Retornos, volumen y tono de cada empresa son estables. ` +
      "El tono general de las noticias dio inconcluso porque cambia en ciclos de meses; por eso el VAR usa el tono anormal (comparado con las 20 ruedas previas), " +
      "que es estable sin discusión. Decisión del 24/10/2026.",
    ]),

    h1("1. Para qué sirve este paso"),
    p("El VAR, que es el análisis principal de la tesis, necesita series estables (estacionarias): que suban y bajen alrededor de un mismo nivel, sin irse corriendo. " +
      "Si una serie se va corriendo, el VAR puede encontrar relaciones que no existen, solo porque dos series se movieron en la misma dirección."),
    p("La carpeta 04 del lado bursátil ya mostró, con 3 años de datos, que hay que trabajar con retornos y no con precios. Este paso repite la prueba en el tramo exacto de la unión " +
      "(244 ruedas) y la extiende a las series nuevas: tono de las noticias, atención y volumen."),

    h1("2. Cómo se prueba"),
    p([bold("ADF "), plain("(el mismo test y la misma especificación que la carpeta 04: con constante y rezagos elegidos por AIC). Puede decir \"es estable\" o \"no puedo afirmarlo\", " +
      "pero nunca prueba que una serie no sea estable.")]),
    p([bold("KPSS "), plain("(confirmación). Hace la pregunta al revés: parte de suponer que la serie es estable y busca evidencia en contra. Con los dos juntos hay cuatro resultados posibles:")]),
    simpleTable(["ADF", "KPSS", "Conclusión"], [
      ["Dice que es estable", "No encuentra problemas", "Estacionaria"],
      ["Dice que es estable", "Encuentra algo de persistencia", "Estacionaria (ADF): estable, con memoria"],
      ["No puede afirmarlo", "No encuentra problemas", "Inconclusa: los datos no alcanzan para decidir"],
      ["No puede afirmarlo", "Encuentra problemas", "No estacionaria"],
    ], [28, 30, 42]),

    h1("3. Series del mercado"),
    simpleTable(["Serie", "Datos", "ADF (p)", "KPSS (p)", "Conclusión"],
      ordenMercado.map(([s, f]) => { const x = filaMercado(s, f || ""); return [f ? "Cambio de tono (vs. rueda anterior)" : NOMBRE[s], x.n, pA(x.adf_p), pK(x.kpss_p), x.conclusion]; }),
      [36, 10, 15, 15, 24]),
    nota("El tono anormal y la atención tienen 224 datos porque las primeras 20 ruedas no tienen 20 ruedas previas de referencia. El KPSS solo informa p-valores entre 0,01 y 0,10."),

    h1("4. El tono de las noticias: inconcluso, y qué se hizo"),
    p(`El tono en nivel no permite concluir: el ADF da p = ${coma(tono.adf_p, 2)} y el KPSS tampoco encuentra problemas. La razón es que el tono cambia de a poco, en ciclos de varios meses. ` +
      `Promedio por trimestre: ${medTrim.join(" · ")}. Con un solo año de datos, el test no logra distinguir "un clima que va y viene" de "un clima que se va corriendo". ` +
      `Es un problema de pocos datos más que de la serie: con 5 rezagos fijos en lugar de los ${tono.adf_rezagos} que elige el AIC, el ADF sí la da estable.`),
    p("Como es la variable central del VAR, se compararon dos transformaciones:"),
    bullet([bold("Tono anormal: "), plain("tono de la rueda menos el promedio de las 20 ruedas previas. Responde \"¿las noticias están más optimistas o pesimistas que lo habitual?\".")]),
    bullet([bold("Cambio de tono: "), plain("tono de la rueda menos el de la rueda anterior. Responde \"¿mejoró o empeoró respecto de ayer?\"; es más ruidoso.")]),
    refBox("Decisión del 24/10/2026", [
      `El VAR usa el tono anormal (ADF p ${pA(anormal.adf_p)}, KPSS sin problemas). Tiene tres ventajas: es estable sin discusión; usa la misma lógica que la atención y el volumen ` +
      "anormales (todo comparado con lo habitual); y mide la sorpresa, que es lo que puede mover precios, en lugar del clima de fondo que el mercado ya conoce. " +
      "El tono en nivel se usa como robustez (U8). El tono anormal se agregó a los datasets de U4 (sent_anormal y sent_portal_anormal).",
    ]),
    p("El VIX argentino también da inconcluso, por la misma razón (sube y baja en episodios de semanas). No entra al VAR como variable: se usa como contexto a través del régimen del HMM."),

    h1("5. Series de cada acción"),
    simpleTable(["Serie", "Series", "Estacionaria", "Estacionaria (ADF)", "Inconclusa o no estacionaria"], [
      ["Retorno (47 acciones)", ...conteo("retorno")],
      ["Volumen anormal (47 acciones)", ...conteo("vol_anormal")],
      ["Tono propio de la empresa (17, variable del VAR)", ...conteo("tono_propio")],
      ["Tono de la empresa, completando los días sin noticia con el tono general", ...conteo("sent_neto_empresa", "completada")],
      ["Tono de la empresa, solo los días con noticia", ...conteo("sent_neto_empresa", "solo días con noticia")],
    ], [40, 12, 15, 17, 16]),
    p(`Todos los retornos son estables, como en la carpeta 04 con 3 años (${v("carpeta04_retornos_estacionarios")} de 47); el que más se acerca al límite es ${r.adf_p_max_retornos.detalle.replace(".BA", "")} ` +
      `(p = ${coma(v("adf_p_max_retornos"), 3)}). Los casos \"estables con memoria\" son ${r.estacionarias_solo_adf.detalle.replace(/\.BA/g, "")}.`),
    p("El tono de cada empresa es estable de las dos formas en que se lo puede armar, y también lo es el tono propio que se definió en U6 " +
      "(cuánto mejor o peor se habla de la empresa que del mercado, ponderado por la cantidad de oraciones), que es la variable de empresa que usa el VAR."),
    figure(path.join(CARPETA, "u5_resumen.png"), 560),
    nota("Proporción de series en cada categoría. Verde: estables. Amarillo: inconclusas."),

    h1("6. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),

    h1("7. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("resultados_adf_union.csv")], `Las ${v("series_probadas")} pruebas: serie, forma, acción, datos, estadístico y p-valor de ADF y KPSS, rezagos y conclusión`],
      [[code("resumen_por_serie.csv")], "Cuántas series de cada tipo cayeron en cada categoría"],
      [[code("resumen_u5.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u5_resumen.png")], "La figura de la sección 5"],
    ], [34, 66]),

    h1("8. Limitaciones"),
    bullet("Con 244 ruedas los tests tienen poca potencia: una serie persistente puede quedar inconclusa aunque sea estable. Por eso se usan dos tests y se informa el caso inconcluso como tal."),
    bullet("El tono anormal pierde las primeras 20 ruedas (mayo de 2025), que no tienen referencia previa."),
    bullet("Usar el tono anormal cambia la pregunta: el VAR mide el efecto de las sorpresas en el tono, no del nivel. La robustez con el tono en nivel (U8) muestra si la conclusión depende de esa elección."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U5_ADF.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
