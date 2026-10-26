// Genera Documentacion_Mapa_Lado_Bursatil.docx dentro de ../00_mapa_lado_bursatil/
// Uso:  node build_doc_mapa.js   (después convertir a PDF con LibreOffice headless)
// Los números salen de resumen_mapa.csv (que genera mapa_lado_bursatil.py leyendo las carpetas 01-06).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, ImageRun, AlignmentType, BorderStyle, PageOrientation,
  Header, Footer, PageNumber,
} = require("docx");
const { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, leerCsv, seccionReferencias } = require("./comun");

const CARPETA = path.join(RAIZ, "00_mapa_lado_bursatil");
const V = Object.fromEntries(leerCsv(path.join(CARPETA, "resumen_mapa.csv")).map(r => [r[""], Number(r.valor)]));
const vix = leerCsv(path.join(RAIZ, "03_vix_argentino", "vix_arg.csv"));
const precios1 = fs.readFileSync(path.join(RAIZ, "01_scraping_acciones", "precios_diarios_47_acciones.csv"), "utf-8").split(/\r?\n/);
const coma = (x, d = 1) => Number(x).toFixed(d).replace(".", ",");
const fecha = f => `${f.slice(8, 10)}/${f.slice(5, 7)}/${f.slice(0, 4)}`;
const ini3 = precios1[1].slice(0, 10), fin3 = precios1.filter(l => l).map(l => l.slice(0, 10)).slice(1).sort().pop();
const iniV = vix[0].fecha, finV = vix[vix.length - 1].fecha;

const GRIS = "5C6B7A", LINE = "D9E0E7";
const pie = () => new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
  new TextRun({ text: "Nicolás Diddi · Página ", size: 16, color: GRIS }),
  new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GRIS }),
  new TextRun({ text: " de ", size: 16, color: GRIS }),
  new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GRIS }),
]})]});
const cabecera = () => new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
  children: [new TextRun({ text: "Mapa del lado bursátil — tesis version 3.0", size: 16, color: GRIS })] })] });
const A4 = { width: 11906, height: 16838 };
const margen = { top: 1134, bottom: 1134, left: 1134, right: 1134 };

// Imagen del mapa a lo ancho de una página A4 apaisada
const png = fs.readFileSync(path.join(CARPETA, "mapa_lado_bursatil.png"));
const pw = png.readUInt32BE(16), ph = png.readUInt32BE(20);
const anchoPx = 980;   // ~ ancho útil apaisado a 96 dpi

const N = V.panel, NV = V.ruedas_ventana_noticias;

const portada = [
  new Paragraph({ children: [new TextRun({ text: "Mapa del lado bursátil", bold: true, size: 44, font: "Cambria", color: "12263A" })], spacing: { after: 80 } }),
  new Paragraph({ children: [new TextRun({ text: "De Yahoo Finance a la etapa que se une con las noticias", size: 24, font: "Cambria", color: "1C3A5C", italics: true })], spacing: { after: 200 } }),
  new Paragraph({
    children: [new TextRun({ text: "Tesina — Impacto de shocks informativos en acciones argentinas (BYMA / S&P Merval). " +
      "Documento exclusivamente del lado bursátil. Resume las carpetas 01 a 06 de tesis version 3.0 en una sola vista.", size: 19, color: GRIS })],
    spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE, space: 8 } },
  }),
  p([bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\00_mapa_lado_bursatil\\"),
    plain(". El mapa se genera con un script que lee los resultados de cada carpeta: no tiene números escritos a mano.")]),
  p([bold("Cómo está organizado. "), plain("La página siguiente es el mapa completo. Después, el recorrido carpeta por " +
    "carpeta con la decisión que habilita cada paso, las dos ventanas de fechas, las correcciones de datos y lo que falta.")]),
];

const mapa = [
  new Paragraph({ alignment: AlignmentType.CENTER, children: [new ImageRun({ data: png, type: "png",
    transformation: { width: anchoPx, height: Math.round(anchoPx * ph / pw) } })] }),
];

const cuerpo = [
  h1("1. El recorrido, carpeta por carpeta"),
  p("Cada paso responde una pregunta y deja una decisión tomada para el siguiente:", { keepNext: true }),
  simpleTable(["Carpeta", "Pregunta", "Resultado clave", "Qué decisión habilita"], [
    ["01 Scraping", "¿Con qué empresas se trabaja?",
      `${V.candidatas} tickers → ${N} acciones en ${V.sectores} sectores (100% de las ruedas y ≥ 90% de días con volumen)`,
      `El panel de ${N} que usan todos los pasos siguientes`],
    ["03 VIX argentino", "¿Qué tan nervioso estuvo el mercado cada día?",
      `${NV} ruedas, promedio ${coma(V.vix_promedio)}%, máximo ${coma(V.vix_maximo)}%`,
      "Fija la ventana de noticias y da la serie para el HMM"],
    ["02 Clustering", "¿Hay familias de acciones que se mueven parecido?",
      `${V.combinaciones_degeneradas} de ${V.combinaciones} combinaciones aíslan 1-2 outliers; el único grupo de tamaño real (${V.grupo_clustering} acciones, silueta ${coma(V.silueta_grupo, 3)}) se explica sobre todo por baja liquidez`,
      "No hay familias claras: el análisis se hace por acción (y por sector)"],
    ["04 ADF", "¿Se puede usar el precio, o hay que usar el retorno?",
      `Precios: ${N - V.precios_estacionarios} de ${N} NO estacionarios. Retornos: ${V.retornos_estacionarios} de ${N} estacionarios`,
      "El VAR se hace con retornos"],
    ["05 Volatilidad", "¿Qué acciones son más nerviosas que el mercado?",
      `Panel ${coma(V.vol_promedio_panel)}% vs. VIX ${coma(V.vix_promedio)}%; ${V.picos_propios_genuinos} picos propios`,
      "Los picos propios son candidatos a cruzar con noticias"],
    ["06 HMM", "¿En qué régimen estaba el mercado cada día?",
      `k = 3: Calmo ${V.dias_calmo} · Moderado ${V.dias_moderado} · Tenso ${V.dias_tenso} días`,
      "La etiqueta de régimen para el VAR por régimen"],
  ], [15, 23, 34, 28]),
  p(""),
  p([bold("Por qué el 03 va antes que el 02 en el mapa. "), plain("El número de carpeta sigue el orden en que se " +
    "hicieron, pero el VIX es un dato base: define la ventana de fechas que después leen el clustering (1 año), el ADF, " +
    "la volatilidad y el HMM.")]),

  h1("2. Las dos ventanas de fechas"),
  simpleTable(["Ventana", "Desde", "Hasta", "Ruedas", "Quién la usa"], [
    ["3 años", fecha(ini3), fecha(fin3), String(V.ruedas_3_anos), "01 Scraping, 02 Clustering (3 años)"],
    ["Ventana de noticias", fecha(iniV), fecha(finV), String(NV), "02 Clustering (1 año), 03, 04, 05, 06"],
  ], [20, 14, 14, 11, 41]),
  p(""),
  p([plain("Las fechas pedidas terminan el 03/05/2026 (el final del corpus de noticias); la última rueda real es el " +
    `${fecha(finV)} porque el 01/05 es feriado y el 02-03/05 es fin de semana. La ventana de noticias se define una sola ` +
    "vez, en la carpeta 03, y las demás la leen de "), code("vix_arg.csv"), plain(" — no puede desalinearse.")]),

  h1("3. Calidad de datos — lo que se corrigió en el camino"),
  simpleTable(["Problema", "Dónde", "Cómo se resolvió"], [
    ["Yahoo agrega filas \"fantasma\" en feriados para cada acción (precio pegado, volumen 0)", "01", "Se usa el calendario del índice ^MERV como calendario real de BYMA"],
    ["Yahoo falla de forma intermitente para algunos tickers", "01", "Hasta 3 reintentos por ticker antes de declarar \"sin datos\""],
    ["Split de SEMI mal fechado: el 16/12/2024 quedó con el precio sin dividir", "01", "Ese día dividido por 4,227 (el factor que registra Yahoo)"],
    ["Dividendo en acciones de AGRO (nov. 2023) sin aplicar a los precios anteriores", "01", "Precios hasta el 02/11/2023 divididos por 2,1"],
    ["Nombres y sectores mal cargados en 12 tickers", "01", "Verificados contra Yahoo; sector por negocio principal"],
    ["Precios en pesos nominales, con tendencia", "04", "ADF de precios con constante + tendencia"],
    ["El VIX realizado tiene un eco de 20 días tras cada shock", "03, 05, 06", "Documentado; los picos de volatilidad que son eco se descartan"],
  ], [48, 12, 40]),

  h1("4. Lo que falta — la etapa que se une con las noticias"),
  p("Las tres cajas punteadas del mapa. Se construyen sobre el panel, las fechas y los regímenes que dejan las " +
    "carpetas 01 a 06:", { keepNext: true }),
  simpleTable(["Paso", "Qué hace", "Qué necesita"], [
    ["Dataset unificado", "Junta mercado (retornos, VIX, régimen) con sentimiento diario y shocks de noticias", "Serie de sentimiento diario desde el 02/01/2025"],
    ["VAR + Granger + IRF", "¿El sentimiento anticipa a los precios, o al revés? General, por empresa, por régimen y por sector", "Sentimiento por empresa para las acciones del panel"],
    ["Event study", "Qué pasa con los precios alrededor de los shocks de noticias", "Lista de shocks de noticias"],
  ], [20, 46, 34]),
  p(""),
  refBox("Lo que hay que coordinar con el lado de noticias", [
    [bold("Sentimiento por empresa: "), plain(`hoy existe solo para las 20 empresas oficiales del Merval. Para el VAR por ` +
      `empresa con las ${N} hace falta ampliar el diccionario de nombres (gazetteer) — o decidir hacerlo con un subconjunto.`)],
    [bold("Ventana: "), plain(`la serie de sentimiento tiene que cubrir desde el ${fecha(iniV)}, el inicio de la ventana de noticias.`)],
  ]),

  h1("5. Archivos generados"),
  p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\00_mapa_lado_bursatil\\")]),
  simpleTable(["Archivo", "Qué es"], [
    ["mapa_lado_bursatil.py", "Script único. Lee los resultados de las carpetas 01 a 06 y dibuja el mapa."],
    ["mapa_lado_bursatil.png", "El mapa del pipeline (fuente → datos base → análisis → próxima etapa) y la línea de tiempo de las dos ventanas."],
    ["resumen_mapa.csv", "Los números que aparecen en el mapa, uno por fila, para verificarlos o citarlos."],
  ], [32, 68]),

  h1("6. Trabajos previos por carpeta"),
  p("Cada carpeta tiene su propia sección de referencias bibliográficas al final de su PDF, con los trabajos descargados " +
    "en su subcarpeta papers\\. Resumen:", { keepNext: true }),
  simpleTable(["Carpeta", "Referencias", "Descargadas", "De acceso restringido"], (() => {
    const refs = JSON.parse(fs.readFileSync(path.join(__dirname, "referencias.json"), "utf-8"));
    const orden = [...new Set(refs.map(r => r.carpeta))].sort();
    return orden.map(c => {
      const rs = refs.filter(r => r.carpeta === c);
      const desc = rs.filter(r => r.archivo).length;
      return [c, String(rs.length), String(desc), String(rs.length - desc)];
    });
  })(), [40, 20, 20, 20]),
  p(""),
  p("Algunos trabajos aparecen en más de una carpeta porque sirven a los dos temas (por ejemplo, el de los \"ghost features\" " +
    "explica tanto el eco del VIX como el de la volatilidad por acción); el PDF se guarda una sola vez, en la carpeta 03."),

  ...seccionReferencias("00_mapa_lado_bursatil", 7),
];

const estilos = {
  default: { document: { run: { font: "Calibri", size: 21 } } },
  paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
    run: { font: "Cambria", size: 30, bold: true, color: "12263A" },
    paragraph: { spacing: { before: 360, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "40798C", space: 4 } } } }],
};
const doc = new Document({ styles: estilos, sections: [
  { properties: { page: { size: A4, margin: margen } }, headers: { default: cabecera() }, footers: { default: pie() }, children: portada },
  { properties: { page: { size: { ...A4, orientation: PageOrientation.LANDSCAPE }, margin: { top: 700, bottom: 700, left: 700, right: 700 } } },
    headers: { default: cabecera() }, footers: { default: pie() }, children: mapa },
  { properties: { page: { size: A4, margin: margen } }, headers: { default: cabecera() }, footers: { default: pie() }, children: cuerpo },
]});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_Mapa_Lado_Bursatil.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
