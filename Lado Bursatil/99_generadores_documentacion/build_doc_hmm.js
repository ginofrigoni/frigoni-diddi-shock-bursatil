// Genera Documentacion_HMM_Regimen_Mercado.docx dentro de ../06_hmm_regimen_mercado/
// Uso:  node build_doc_hmm.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, AlignmentType, BorderStyle, PageBreak,
  Header, Footer, PageNumber, ImageRun,
} = require("docx");
const { seccionReferencias, leerCsv } = require("./comun");

// Régimen suavizado (el oficial) vs. filtrado (solo con información pasada), leído del CSV
const hmmCsv = leerCsv(path.join(__dirname, "..", "06_hmm_regimen_mercado", "hmm_regimen_mercado.csv"));
const nCoinciden = hmmCsv.filter(r => r.regimen_nombre === r.regimen_filtrado_nombre).length;
const fechaTxt = f => `${f.slice(8, 10)}/${f.slice(5, 7)}/${f.slice(0, 4)}`;
const tramos = (col, nombre) => {
  const out = [];
  hmmCsv.forEach((r, i) => {
    if (r[col] !== nombre) return;
    if (i === 0 || hmmCsv[i - 1][col] !== nombre) out.push({ ini: r.fecha, fin: r.fecha });
    else out[out.length - 1].fin = r.fecha;
  });
  return out;
};
const tensoSuav = tramos("regimen_nombre", "Tenso"), tensoFilt = tramos("regimen_filtrado_nombre", "Tenso");

const CARPETA = path.join(__dirname, "..", "06_hmm_regimen_mercado");
const LINE = "D9E0E7";

function h1(text) { return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 360, after: 160 }, text }); }
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
    rows: [new TableRow({ children: [new TableCell({
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

function pngSize(buf) { return { w: buf.readUInt32BE(16), h: buf.readUInt32BE(20) }; }
function figure(file, widthPx) {
  const buf = fs.readFileSync(path.join(CARPETA, file));
  const { w, h } = pngSize(buf);
  const width = widthPx || 500;
  const heightPx = Math.round(width * h / w);
  return new Paragraph({
    children: [new ImageRun({ data: buf, transformation: { width, height: heightPx }, type: "png" })],
    spacing: { after: 160 },
    alignment: AlignmentType.CENTER,
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Cambria", size: 30, bold: true, color: "12263A" },
        paragraph: { spacing: { before: 360, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "40798C", space: 4 } } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { font: "Cambria", size: 25, bold: true, color: "1C3A5C" },
        paragraph: { spacing: { before: 280, after: 120 } } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({
      alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Regímenes de mercado (HMM) — tesis version 3.0", size: 16, color: "5C6B7A" })],
    })]})},
    footers: { default: new Footer({ children: [new Paragraph({
      alignment: AlignmentType.CENTER,
      children: [
        new TextRun({ text: "Nicolás Diddi · ", size: 16, color: "5C6B7A" }),
        new TextRun({ text: "Página ", size: 16, color: "5C6B7A" }),
        new TextRun({ children: [PageNumber.CURRENT], size: 16, color: "5C6B7A" }),
        new TextRun({ text: " de ", size: 16, color: "5C6B7A" }),
        new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: "5C6B7A" }),
      ],
    })]})},
    children: [
      new Paragraph({ children: [new TextRun({ text: "Regímenes de Mercado (HMM)", bold: true, size: 44, font: "Cambria", color: "12263A" })], spacing: { after: 80 } }),
      new Paragraph({ children: [new TextRun({ text: "¿En qué estado de volatilidad estuvo el mercado cada día, y cuándo cambió?", size: 24, font: "Cambria", color: "1C3A5C", italics: true })], spacing: { after: 200 } }),
      new Paragraph({
        children: [new TextRun({
          text: "Tesina — Impacto de shocks informativos en acciones argentinas (BYMA / S&P Merval). " +
            "Documento exclusivamente del lado bursátil. No toca noticias, sentimiento ni gazetteer.",
          size: 19, color: "5C6B7A",
        })],
        spacing: { after: 200 },
        border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: LINE, space: 8 } },
      }),
      p([bold("Ubicación de todo lo generado. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\06_hmm_regimen_mercado\\"),
        plain(". Input: "), code("vix_arg.csv"), plain(" de "), code("03_vix_argentino"), plain(" — la misma ventana usada en VIX, ADF y volatilidad.")]),

      new Paragraph({ children: [new PageBreak()] }),

      h1("1. Qué es y para qué sirve"),
      p("El VIX argentino (volatilidad realizada del Merval) se mueve de forma muy dispareja en el tiempo: hay tramos largos " +
        "de calma y episodios cortos y violentos de estrés. Un modelo de Markov-Switching asume que, detrás de esa serie, " +
        "hay un número finito de \"regímenes\" (estados ocultos) — cada uno con su propio nivel promedio de volatilidad — y " +
        "que el mercado salta de uno a otro según una cadena de Markov: la probabilidad de estar en un régimen mañana " +
        "depende solo del régimen de hoy."),
      p([bold("Modelo: "), code("statsmodels.tsa.regime_switching.markov_regression.MarkovRegression"),
        plain(" ajustado sobre la serie "), code("vix_arg"), plain(". Técnicamente es un modelo Markov-Switching de media y " +
        "varianza, no un HMM discreto clásico — pero en la literatura de regímenes de mercado se lo llama \"HMM\" de forma " +
        "habitual, y así se lo nombra en este documento.")]),
      p("A cada día se le asigna el régimen con mayor probabilidad suavizada (smoothed marginal probability), calculada " +
        "usando toda la serie completa — no solo el pasado. El resultado es una etiqueta diaria (\"Calmo\", \"Moderado\" " +
        "o \"Tenso\") que sirve como variable de contexto para el análisis posterior (por ejemplo, para ver si la " +
        "relación entre noticias y precios cambia según el régimen de volatilidad vigente)."),
      refBox("Ventana usada — la misma que VIX, ADF y volatilidad", [
        [plain("323 días, "), bold("2025-01-02 → 2026-04-30"), plain(" — leída directamente de "), code("../03_vix_argentino/vix_arg.csv"),
          plain(" (no está hardcodeada acá). No hay una versión \"de 1 año\" de este análisis: el HMM necesita toda la " +
          "serie disponible para estimar bien las transiciones entre regímenes.")],
      ]),

      h1("2. Cuántos regímenes — barrido de k por BIC"),
      p("El número de regímenes k no se fija a mano: se ajusta el modelo para k=2 a 6 y se compara el BIC (Bayesian " +
        "Information Criterion) de cada ajuste, que penaliza modelos con más parámetros."),
      p([bold("El optimizador por defecto (BFGS) es inestable en esta serie: "), plain("con la cantidad de iteraciones " +
        "internas del EM que usa statsmodels por defecto, el ajuste falla por un problema numérico (el SVD no " +
        "converge). Se usa en su lugar el optimizador Nelder-Mead (\"nm\"), más robusto para esta superficie de " +
        "verosimilitud, y se fija una semilla aleatoria para que el resultado sea reproducible.")]),
      p([bold("Qué es un \"régimen degenerado\": "), plain("un estado que el modelo crea con varianza casi cero, pegado a " +
        "un único día. Como la varianza tiende a cero, la verosimilitud en ese punto se dispara y el BIC \"mejora\" " +
        "de forma artificial — es una falla conocida de los modelos de mezcla, no un régimen real del mercado. Por eso " +
        "la regla de selección descarta todo k que no converja o que tenga algún régimen de menos de 5 días.")]),
      simpleTable(
        ["k", "BIC", "Mín. días en un régimen", "¿Converge sin degenerar?"],
        [
          ["2", "2.202,9", "1 día", "No (con esta semilla)*"],
          [[bold("3")], [bold("2.119,4")], [bold("65 días")], [bold("Sí — elegido")]],
          ["4", "2.152,0", "1 día", "No"],
          ["5", "2.161,4", "1 día", "No"],
          ["6", "2.185,2", "1 día", "No"],
        ],
        [12, 26, 32, 30]
      ),
      p(""),
      figure("bic_curva.png", 440),
      p([plain("* k=2 depende del arranque aleatorio: con la semilla del script degenera, pero con otras semillas converge " +
        "bien (BIC 2.350,8 o 2.450,7). En cualquier caso su BIC es peor que el de k=3.")]),
      p([bold("k = 3 es el mínimo real: "), plain("tiene el menor BIC entre los k que convergen sin degenerar, y da " +
        "exactamente el mismo resultado con 10 semillas aleatorias distintas — a diferencia de k=2, no depende del arranque.")]),
      refBox("¿Por qué no 4 o 5 regímenes?", [
        [bold("Con k=4 "), plain("el modelo reproduce los mismos 3 regímenes de k=3 (VIX promedio 32,7% / 46,7% / 70,9%) " +
          "y el \"cuarto\" es un solo día: el 01/12/2025 (VIX 40,3%), un día de transición mientras la volatilidad bajaba " +
          "después de las elecciones. No aparece ninguna categoría nueva con sentido económico.")],
        [bold("Con k=5 "), plain("el mejor ajuste encontrado directamente se rompe: uno de los estados tiene varianza " +
          "exactamente cero, clavado en el valor mínimo de la serie (15,4%), y otro no queda asignado a ningún día.")],
        [plain("Con 323 días de datos, la serie sostiene 3 regímenes distinguibles; pedirle más solo genera estados " +
          "artificiales.")],
      ]),

      h1("3. Los 3 regímenes"),
      simpleTable(
        ["Régimen", "VIX prom.", "Retorno prom. diario", "Días", "% del período"],
        [
          ["Calmo", "33,0%", "-0,074%", "177", "54,8%"],
          ["Moderado", "46,6%", "0,053%", "81", "25,1%"],
          ["Tenso", "70,8%", "0,518%", "65", "20,1%"],
        ],
        [22, 18, 24, 14, 22]
      ),
      p(""),
      p([bold("El mercado pasó más de la mitad del período (54,8%) en el régimen Calmo. "), plain("El régimen " +
        "\"Tenso\" — el de mayor volatilidad — coincide con el retorno diario promedio más alto de los tres (0,518%), " +
        "no el más bajo: son los tramos donde el índice se mueve fuerte en cualquier dirección, e incluye la fuerte " +
        "suba del Merval alrededor de las elecciones legislativas de octubre-noviembre 2025.")]),

      h1("4. Matriz de transición"),
      p("Probabilidad de pasar de un régimen (fila, \"hoy\") a otro (columna, \"mañana\") de un día para el otro:", { keepNext: true }),
      simpleTable(
        ["Hoy \\ Mañana", "Calmo", "Moderado", "Tenso"],
        [
          ["Calmo", "98,0%", "0,0%", "2,0%"],
          ["Moderado", "4,2%", "95,8%", "0,0%"],
          ["Tenso", "0,0%", "4,9%", "95,1%"],
        ],
        [28, 24, 24, 24]
      ),
      p(""),
      p([bold("Los regímenes son muy persistentes: "), plain("la diagonal está entre 95% y 98% — una vez que el mercado " +
        "entra en un régimen, lo más probable es que siga en él al día siguiente. La matriz coincide con los cambios que " +
        "efectivamente se observan en la serie (10 cambios de régimen en 323 días): ")]),
      simpleTable(
        ["Cambio observado", "Veces", "Fechas"],
        [
          ["Calmo → Tenso", "2", "08/09/2025 · 27/10/2025"],
          ["Tenso → Moderado", "3", "16/05/2025 · 06/10/2025 · 25/11/2025"],
          ["Moderado → Calmo", "3", "22/05/2025 · 21/10/2025 · 01/12/2025"],
          ["Moderado → Tenso", "1", "07/04/2025"],
        ],
        [30, 12, 58]
      ),
      p(""),
      p([bold("La desescalada es gradual, la escalada no: "), plain("al salir de Tenso el mercado siempre pasó primero por " +
        "Moderado antes de volver a Calmo. En cambio, las dos veces que salió de Calmo saltó directo a Tenso, sin pasar " +
        "por el régimen intermedio — un shock lleva al mercado de la calma al estrés de un día para el otro.")]),

      h1("5. Los regímenes en el tiempo"),
      figure("hmm_regimen_mercado.png", 500),
      p([bold("Tres episodios Tensos: "), plain("07/04 → 15/05/2025 (VIX hasta ≈72%), 08/09 → 03/10/2025 y " +
        "27/10 → 21/11/2025, este último con el máximo de toda la serie (VIX ≈91%, 21/11/2025). El primer tramo del " +
        "período (enero-abril 2025) es Moderado; todo junio-agosto 2025 y prácticamente todo diciembre 2025 en adelante " +
        "quedan como Calmo, con el VIX cayendo hasta su mínimo de la serie (15,4%, 30/04/2026) en el último día disponible.")]),
      refBox("Cómo leer las fechas de los regímenes — el eco de la ventana de 20 días", [
        "El HMM se ajusta sobre el VIX argentino, que es un desvío de los últimos 20 días, así que hereda su eco (ver la " +
        "sección 3 de Documentacion_VIX_Argentino): un único día extremo queda adentro del cálculo durante exactamente 20 " +
        "ruedas. Los dos episodios Tensos del segundo semestre empiezan el día del shock — 08/09/2025 (−13,3%) y " +
        "27/10/2025 (+21,8%) — y terminan cuando ese día sale de la ventana, 20 ruedas después (06/10 y 25/11). Las " +
        "fechas de inicio marcan el shock; las de fin no marcan que el mercado se haya calmado ese día, sino que el shock " +
        "cumplió 20 ruedas. Por eso parte de los días Tensos son semanas posteriores al shock, y no días de shock en sí.",
      ]),

      refBox("Dos versiones del régimen: \"mirando todo el período\" y \"en tiempo real\"", [
        [plain("El régimen oficial de cada día (columna "), code("regimen_nombre"), plain(") usa las probabilidades " +
          "suavizadas: para decidir el régimen de un día, el modelo mira toda la serie, incluidos los días posteriores. " +
          "Es como relatar un partido después de verlo entero: sirve para describir qué pasó, pero no para anticipar nada.")],
        [plain("Por eso se guarda también la versión filtrada ("), code("regimen_filtrado_nombre"), plain("), que en cada día " +
          `solo usa la información disponible hasta ese día. Las dos coinciden en ${nCoinciden} de ${hmmCsv.length} días ` +
          `(${(nCoinciden / hmmCsv.length * 100).toFixed(1).replace(".", ",")}%). La diferencia aparece en los bordes de los ` +
          `episodios: por ejemplo, el primer Tenso empieza el ${fechaTxt(tensoSuav[0].ini)} en la versión suavizada, pero ` +
          `recién el ${fechaTxt(tensoFilt[0].ini)} en la filtrada — en tiempo real, el modelo tarda en confirmar el cambio.`)],
        [bold("Cuál usar: "), plain("la suavizada para describir el período (como en este documento); la filtrada si en la " +
          "etapa siguiente el régimen se usa para pronosticar o para condicionar un análisis sin mirar el futuro " +
          "(Majumder et al., 2023, en las referencias).")],
      ]),

      h1("6. Archivos generados"),
      p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\06_hmm_regimen_mercado\\")]),
      simpleTable(
        ["Archivo", "Qué es"],
        [
          ["hmm_regimen_mercado.py", "Script único. Barre k=2..6, elige k por BIC, ajusta el modelo final y genera todos los outputs."],
          ["hmm_regimen_mercado.csv", "1 fila por día (323): fecha, cierre Merval, retorno, VIX, régimen asignado (suavizado, el oficial), las probabilidades suavizadas y filtradas de cada régimen, y el régimen filtrado."],
          ["matriz_transicion.csv", "Matriz de transición 3×3, fila=régimen hoy, columna=régimen mañana."],
          ["bic_por_k.csv", "BIC, AIC, log-verosimilitud, convergencia y régimen mínimo para cada k barrido (2 a 6)."],
          ["bic_curva.png", "Gráfico de BIC vs. k, marcando el k elegido."],
          ["hmm_regimen_mercado.png", "3 paneles: Merval y VIX coloreados por régimen, y probabilidad suavizada de cada régimen por día."],
        ],
        [30, 70]
      ),

      ...seccionReferencias("06_hmm_regimen_mercado", 7),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_HMM_Regimen_Mercado.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
