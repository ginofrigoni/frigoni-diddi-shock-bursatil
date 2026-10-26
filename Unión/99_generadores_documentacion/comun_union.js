// Piezas compartidas por los generadores de documentación de la Unión.
// Reutiliza el estilo del lado bursátil (comun.js) y su paquete docx.
const path = require("path");
const BURSATIL_GEN = path.join(__dirname, "..", "..", "Lado Bursatil", "99_generadores_documentacion");
// docx se resuelve igual que desde comun.js: si se cargara por ruta directa saldría otra copia del
// paquete y los párrafos de comun.js se descartarían en silencio (instanceof distinto).
const requireComun = require("module").createRequire(path.join(BURSATIL_GEN, "comun.js"));
const docx = requireComun("docx");
const comun = require(path.join(BURSATIL_GEN, "comun"));
const { Document, Paragraph, TextRun, AlignmentType, BorderStyle, Header, Footer, PageNumber } = docx;
const { p, plain } = comun;

const RAIZ_UNION = path.join(__dirname, "..");
const GRIS = "5C6B7A";

function bullet(runs) {
  return p(Array.isArray(runs) ? [plain("•  "), ...runs] : [plain("•  " + runs)], { indent: { left: 360, hanging: 240 } });
}
function nota(texto) { return p([new TextRun({ text: texto, size: 18, color: GRIS, italics: true })]); }

// Lee un CSV de resumen (metrica, valor, detalle) como diccionario.
function leerResumen(archivo) {
  return Object.fromEntries(comun.leerCsv(archivo).map(r => [r.metrica, r]));
}

const miles = x => Math.round(Number(x)).toLocaleString("es-AR");
const coma = (x, d = 1) => Number(x).toFixed(d).replace(".", ",");
const fecha = s => s.slice(0, 10).split("-").reverse().join("/");

// Portada + documento con el estilo de la tesis. `children` es el cuerpo desde la sección 1.
function documentoUnion({ titulo, subtitulo, encabezado, ubicacion, children }) {
  return new Document({
    styles: {
      default: { document: { run: { font: "Calibri", size: 21 } } },
      paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Cambria", size: 30, bold: true, color: "12263A" },
        paragraph: { spacing: { before: 360, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "40798C", space: 4 } } } }],
    },
    sections: [{
      properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
      headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: encabezado, size: 16, color: GRIS })] })] }) },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
        new TextRun({ text: "Nicolás Diddi · Gino Frigoni · Página ", size: 16, color: GRIS }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GRIS }),
        new TextRun({ text: " de ", size: 16, color: GRIS }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GRIS })] })] }) },
      children: [
        new Paragraph({ children: [new TextRun({ text: titulo, bold: true, size: 44, font: "Cambria", color: "12263A" })], spacing: { after: 80 } }),
        new Paragraph({ children: [new TextRun({ text: subtitulo, size: 24, font: "Cambria", color: "1C3A5C", italics: true })], spacing: { after: 200 } }),
        new Paragraph({ spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D9E0E7", space: 8 } },
          children: [new TextRun({ text: "Tesina — Impacto de shocks informativos en acciones argentinas (BYMA / S&P Merval). " +
            "Documento de la unión: lee el lado bursátil y el lado de noticias sin modificarlos.", size: 19, color: GRIS })] }),
        p(ubicacion),
        ...children,
      ],
    }],
  });
}

module.exports = { ...comun, docx, RAIZ_UNION, GRIS, bullet, nota, leerResumen, miles, coma, fecha, documentoUnion };
