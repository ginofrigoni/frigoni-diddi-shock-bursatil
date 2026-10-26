// Piezas compartidas por todos los generadores de documentación de tesis version 3.0.
const fs = require("fs");
const path = require("path");
const {
  Document, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, Header, Footer, PageNumber, ImageRun,
} = require("docx");

const RAIZ = path.join(__dirname, "..");
const LINE = "D9E0E7";

function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, keepNext: true, text }); }
function p(runsOrText, opts = {}) {
  const children = typeof runsOrText === "string" ? [new TextRun(runsOrText)] : runsOrText;
  return new Paragraph({ children, spacing: { after: 160, line: 300 }, ...opts });
}
function code(text) { return new TextRun({ text, font: "Consolas", size: 19, color: "1C3A5C" }); }
function bold(text) { return new TextRun({ text, bold: true }); }
function plain(text) { return new TextRun({ text }); }

function refBox(title, lines) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: LINE }, bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE },
      right: { style: BorderStyle.SINGLE, size: 4, color: LINE }, left: { style: BorderStyle.SINGLE, size: 24, color: "40798C" },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }, insideVertical: { style: BorderStyle.NONE, size: 0, color: "FFFFFF" },
    },
    rows: [new TableRow({ cantSplit: true, children: [new TableCell({
      shading: { type: ShadingType.CLEAR, fill: "F5F8FA" },
      margins: { top: 160, bottom: 160, left: 220, right: 220 },
      children: [
        new Paragraph({ children: [new TextRun({ text: title, bold: true, color: "1C3A5C" })], spacing: { after: 80 } }),
        ...lines.map(l => new Paragraph({ children: Array.isArray(l) ? l : [new TextRun(l)], spacing: { after: 60, line: 276 } })),
      ],
    })]})],
  });
}

function simpleTable(headers, rows, widthsPct) {
  const colWidths = widthsPct || headers.map(() => Math.floor(100 / headers.length));
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((htext, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.PERCENTAGE },
      shading: { type: ShadingType.CLEAR, fill: "1C3A5C" },
      margins: { top: 80, bottom: 80, left: 120, right: 120 },
      children: [new Paragraph({ children: [new TextRun({ text: htext, bold: true, color: "FFFFFF", size: 19 })] })],
    })),
  });
  const bodyRows = rows.map((r, ri) => new TableRow({
    cantSplit: true,
    children: r.map((cell, i) => new TableCell({
      width: { size: colWidths[i], type: WidthType.PERCENTAGE },
      shading: { type: ShadingType.CLEAR, fill: ri % 2 === 0 ? "FFFFFF" : "FAFCFD" },
      margins: { top: 70, bottom: 70, left: 120, right: 120 },
      children: [new Paragraph({ children: Array.isArray(cell) ? cell : [new TextRun({ text: String(cell), size: 19 })] })],
    })),
  }));
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: LINE }, bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE },
      left: { style: BorderStyle.SINGLE, size: 4, color: LINE }, right: { style: BorderStyle.SINGLE, size: 4, color: LINE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: LINE }, insideVertical: { style: BorderStyle.SINGLE, size: 4, color: LINE },
    },
    rows: [headerRow, ...bodyRows],
  });
}

function figure(file, widthPx) {
  const buf = fs.readFileSync(file);
  const w = buf.readUInt32BE(16), h = buf.readUInt32BE(20);
  const width = widthPx || 500;
  return new Paragraph({
    children: [new ImageRun({ data: buf, transformation: { width, height: Math.round(width * h / w) }, type: "png" })],
    spacing: { after: 160 },
    alignment: AlignmentType.CENTER,
  });
}

// Separa una línea de CSV respetando campos entre comillas (pandas los entrecomilla si tienen comas)
function partirLinea(l) {
  const campos = [];
  let actual = "", entreComillas = false;
  for (let i = 0; i < l.length; i++) {
    const ch = l[i];
    if (entreComillas) {
      if (ch === '"' && l[i + 1] === '"') { actual += '"'; i++; }
      else if (ch === '"') entreComillas = false;
      else actual += ch;
    } else if (ch === '"') entreComillas = true;
    else if (ch === ",") { campos.push(actual); actual = ""; }
    else actual += ch;
  }
  campos.push(actual);
  return campos;
}

function leerCsv(file) {
  const lineas = fs.readFileSync(file, "utf-8").split(/\r?\n/).filter(l => l.length);
  const cab = partirLinea(lineas[0]);
  return lineas.slice(1).map(l => {
    const v = partirLinea(l);
    return Object.fromEntries(cab.map((c, i) => [c, v[i]]));
  });
}

// Portada + documento con el estilo común. `children` es el cuerpo desde la sección 1.
function documento({ titulo, subtitulo, encabezado, ubicacion, children }) {
  return new Document({
    styles: {
      default: { document: { run: { font: "Calibri", size: 21 } } },
      paragraphStyles: [
        { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
          run: { font: "Cambria", size: 30, bold: true, color: "12263A" },
          paragraph: { spacing: { before: 360, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "40798C", space: 4 } } } },
      ],
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      headers: { default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: encabezado, size: 16, color: "5C6B7A" })],
      })]})},
      footers: { default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: "Nicolás Diddi · Página ", size: 16, color: "5C6B7A" }),
          new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "5C6B7A" }),
          new TextRun({ text: " de ", size: 16, color: "5C6B7A" }),
          new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "5C6B7A" }),
        ],
      })]})},
      children: [
        new Paragraph({ children: [new TextRun({ text: titulo, bold: true, size: 44, font: "Cambria", color: "12263A" })], spacing: { after: 80 } }),
        new Paragraph({ children: [new TextRun({ text: subtitulo, size: 24, font: "Cambria", color: "1C3A5C", italics: true })], spacing: { after: 200 } }),
        new Paragraph({
          children: [new TextRun({
            text: "Tesina — Impacto de shocks informativos en acciones argentinas (BYMA / S&P Merval). " +
              "Documento exclusivamente del lado bursátil. No toca noticias, sentimiento ni gazetteer.",
            size: 19, color: "5C6B7A",
          })],
          spacing: { after: 200 },
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE, space: 8 } },
        }),
        p(ubicacion),
        new Paragraph({ pageBreakBefore: true, children: [] }),
        ...children,
      ],
    }],
  });
}

// Sección "Referencias bibliográficas" de una carpeta, leída del catálogo referencias.json
// (una sola fuente para todas las citas). Devuelve los párrafos listos para el documento.
function seccionReferencias(carpeta, numero) {
  const todas = JSON.parse(fs.readFileSync(path.join(__dirname, "referencias.json"), "utf-8"));
  const refs = todas.filter(r => r.carpeta === carpeta);
  const locales = refs.filter(r => r.archivo && !r.archivo.startsWith("..")).length;
  const sangria = { left: 360 };
  const linea = (etiqueta, texto, extra = {}) => new Paragraph({
    indent: sangria, spacing: { after: 60, line: 276 },
    children: [new TextRun({ text: etiqueta, bold: true, size: 19, color: "1C3A5C" }), new TextRun({ text: texto, size: 19 })],
    ...extra,
  });
  const out = [
    h1(`${numero}. Referencias bibliográficas`),
    p([plain(`Trabajos previos sobre este tema, en español, inglés y portugués. Los que son de acceso libre están ` +
      `descargados en `), code("papers\\"), plain(` dentro de esta misma carpeta (${locales} archivos); los que tienen ` +
      `acceso restringido se citan con su enlace oficial. La misma lista, en formato BibTeX para citar en la tesis, está ` +
      `en `), code("papers\\referencias.bib"), plain(".")]),
  ];
  refs.forEach((r, i) => {
    out.push(new Paragraph({
      spacing: { before: 200, after: 80, line: 276 }, keepNext: true, keepLines: true,
      children: [new TextRun({ text: `[${i + 1}] `, bold: true, color: "40798C" }), new TextRun({ text: r.cita, bold: true, size: 20 })],
    }));
    out.push(linea("De qué trata: ", r.sobre, { keepNext: true, keepLines: true }));
    out.push(linea("Relación con este análisis: ", r.relacion, { keepNext: true, keepLines: true }));
    const donde = r.archivo
      ? [new TextRun({ text: "Archivo: ", bold: true, size: 19, color: "1C3A5C" }), code(r.archivo.replace(/\//g, "\\")),
         new TextRun({ text: `  ·  ${r.idioma}`, size: 19, color: "5C6B7A" })]
      : [new TextRun({ text: "No descargado: ", bold: true, size: 19, color: "C1272D" }),
         new TextRun({ text: `${r.no_descargado}. `, size: 19 }), new TextRun({ text: r.enlace, size: 18, color: "40798C" }),
         new TextRun({ text: `  ·  ${r.idioma}`, size: 19, color: "5C6B7A" })];
    out.push(new Paragraph({ indent: sangria, spacing: { after: 60, line: 276 }, keepLines: true, children: donde }));
  });
  return out;
}

// Nota sobre la anualización con √252 (convención) frente a las ruedas reales de BYMA.
// `filasVix` = filas de vix_arg.csv; `promedio` = el promedio anualizado que muestra ese documento.
function notaAnualizacion(filasVix, promedio, queSeAnualiza) {
  const ini = new Date(filasVix[0].fecha), fin = new Date(filasVix[filasVix.length - 1].fecha);
  const anios = (fin - ini) / (365.25 * 24 * 3600 * 1000);
  const ruedasPorAnio = filasVix.length / anios;
  const factor = Math.sqrt(ruedasPorAnio / 252);
  const c = (x, d = 1) => Number(x).toFixed(d).replace(".", ",");
  return refBox("Anualización: por qué √252 y no las ruedas reales de BYMA", [
    `Para expresar ${queSeAnualiza} como porcentaje anual, el desvío diario se multiplica por √252. El 252 es la cantidad ` +
    `de ruedas por año que se usa como convención internacional. BYMA tiene menos, por sus feriados: en esta ventana hubo ` +
    `${filasVix.length} ruedas en ${c(anios, 2)} años, unas ${c(ruedasPorAnio, 0)} por año. Con ese número, todos los ` +
    `valores serían un ${c((1 - factor) * 100, 1)}% más bajos (el promedio pasaría de ${c(promedio)}% a ` +
    `${c(promedio * factor)}%). Como el ajuste es el mismo para todos los días y todas las acciones, no cambia ninguna ` +
    `comparación ni ninguna conclusión; se mantiene la convención para que los valores sean comparables con otros trabajos.`,
  ]);
}

module.exports = { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, documento, seccionReferencias, notaAnualizacion };
