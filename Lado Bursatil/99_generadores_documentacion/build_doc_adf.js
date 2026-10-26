// Genera Documentacion_ADF.docx dentro de ../04_adf/
// Uso:  node build_doc_adf.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const { Packer } = require("docx");
const { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, documento, seccionReferencias } = require("./comun");

const CARPETA = path.join(RAIZ, "04_adf");
const res = leerCsv(path.join(CARPETA, "resultados_adf_47.csv"));
const panel = leerCsv(path.join(RAIZ, "01_scraping_acciones", "panel_acciones_final.csv"));
const vix = leerCsv(path.join(RAIZ, "03_vix_argentino", "vix_arg.csv"));
const empresa = Object.fromEntries(panel.map(r => [r.ticker, r.empresa]));

const coma = (x, d = 4) => Number(x).toFixed(d).replace(".", ",");
const precio = res.filter(r => r.tipo === "precio");
const retorno = res.filter(r => r.tipo === "retorno");
const N = precio.length;
const estP = precio.filter(r => r.resultado === "Estacionaria").sort((a, b) => Number(a.p_valor) - Number(b.p_valor));
const estR = retorno.filter(r => r.resultado === "Estacionaria");
const pRet = retorno.map(r => Number(r.p_valor));
const maxRet = retorno.reduce((a, b) => (Number(b.p_valor) > Number(a.p_valor) ? b : a));
const nMuyBajo = pRet.filter(x => x < 0.0001).length;
const esperados = (N * 0.05).toFixed(1).replace(".", ",");
const fIni = vix[0].fecha, fFin = vix[vix.length - 1].fecha;

const doc = documento({
  titulo: "Test ADF",
  subtitulo: "¿Con qué serie se puede trabajar — precio o retorno?",
  encabezado: "Test ADF — tesis version 3.0",
  ubicacion: [bold("Ubicación de todo lo generado. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\04_adf\\"),
    plain(`. Input: el panel de ${N} acciones de `), code("01_scraping_acciones"), plain(".")],
  children: [
    h1("1. Por qué hace falta este test"),
    p("El VAR y el test de causalidad de Granger —los próximos pasos del análisis— exigen series estacionarias: con media " +
      "y varianza estables en el tiempo. Si se usan series con tendencia (como el precio de una acción, que en general " +
      "sube con el tiempo), los resultados salen espurios — dos series que suben juntas parecen relacionadas aunque no " +
      "tengan nada que ver entre sí."),
    p([bold("El test: "), plain("Augmented Dickey-Fuller (ADF), con la cantidad de rezagos elegida por AIC. La hipótesis " +
      "nula es \"la serie NO es estacionaria\"; si el p-valor da menor a 0,05, se rechaza la nula y la serie se considera " +
      "estacionaria.")]),
    p("El ADF tiene variantes según la forma de la serie, y cada una se testea con la que le corresponde:", { keepNext: true }),
    simpleTable(["Serie", "Variante del ADF", "Por qué"], [
      ["Precio", "Constante + tendencia", "Los precios están en pesos nominales y suben de forma sostenida (inflación). Sin tendencia, el test puede confundir una suba pareja con una serie estable."],
      ["Retorno diario", "Solo constante", "El retorno es la variación de un día al otro: oscila alrededor de una media, sin tendencia."],
    ], [18, 24, 58]),
    p(""),
    refBox("Ventana usada — la del corpus de noticias, tomada de vix_arg.csv", [
      [plain("Se corre sobre "), bold(`${fIni} → ${fFin}`), plain(` (${vix.length} ruedas) — la ventana del corpus de noticias ` +
        "del compañero, leída directamente de "), code("../03_vix_argentino/vix_arg.csv"), plain(" (no está hardcodeada " +
        "acá, para que no se pueda desalinear si esa ventana cambia). El retorno se calcula sobre la serie completa de " +
        "precios y recién después se recorta a la ventana, para no perder el primer día por falta del precio anterior.")],
    ]),

    h1(`2. Resultado — ${N - estP.length} de ${N} precios no son estacionarios`),
    simpleTable(["Serie", "Estacionarias", "NO estacionarias"], [
      ["Precio (Close)", `${estP.length} de ${N}`, `${N - estP.length} de ${N}`],
      ["Retorno diario", `${estR.length} de ${N}`, `${N - estR.length} de ${N}`],
    ], [34, 33, 33]),
    p(""),
    figure(path.join(CARPETA, "resumen_adf.png"), 420),
    p([bold("La decisión que habilita el VAR: "), plain("se trabaja con "), bold("retornos, no con precios"),
      plain(` — los ${estR.length} retornos diarios dan estacionarios, ${nMuyBajo} de ellos con p < 0,0001 y el más alto ` +
      `con p = ${coma(maxRet.p_valor, 3)} (${maxRet.ticker}), muy por debajo del umbral de 0,05. En cambio, ` +
      `${N - estP.length} de los ${N} precios no lo son.`)]),

    h1(estP.length === 1 ? "3. La excepción — 1 precio que da estacionario" : `3. Las excepciones — ${estP.length} precios que dan estacionarios`),
    p(`${estP.length === 1 ? "No cambia" : "No cambian"} la decisión de trabajar con retornos, pero vale que quede el detalle registrado:`, { keepNext: true }),
    simpleTable(["Ticker", "Empresa", "Estadístico ADF", "p-valor"],
      estP.map(r => [r.ticker, empresa[r.ticker], coma(r.estadistico, 3), coma(r.p_valor)]), [18, 42, 20, 20]),
    p(""),
    p([bold(estP.length === 1 ? "Por qué no preocupa: " : "Por qué no preocupan: "), plain(`al correr ${N} tests a la vez ` +
      `con un umbral de 0,05, aun si ningún precio fuera estacionario se esperaría que alrededor de ${esperados} dieran ` +
      `p < 0,05 por puro azar — ${estP.length === 1 ? "aparece 1" : `aparecen ${estP.length}`}, ` +
      `${estP.length <= 2.4 ? "dentro de lo esperable" : "algo más de lo esperable"}. ` +
      (estP.length === 1
        ? `Su p-valor (${coma(estP[0].p_valor)}) está apenas debajo del umbral, así que no amerita un tratamiento especial: `
        : `Ninguno está muy por debajo del umbral (el menor es ${coma(estP[0].p_valor)}), así que no ameritan un tratamiento especial: `) +
      `en el VAR se usan los retornos de las ${N} acciones por igual.`)]),

    h1("4. Archivos generados"),
    p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\04_adf\\")]),
    simpleTable(["Archivo", "Qué es"], [
      ["adf_test.py", `Script único. Corre ADF sobre precio y retorno de las ${N} acciones, ventana tomada de vix_arg.csv.`],
      ["resultados_adf_47.csv", `Una fila por acción × tipo de serie (${res.length} filas): variante del ADF usada, estadístico, p-valor, resultado.`],
      ["resumen_adf.png", "Barras: cuántas acciones dan estacionarias en precio vs. en retorno."],
    ], [30, 70]),

    ...seccionReferencias("04_adf", 5),
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_ADF.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
