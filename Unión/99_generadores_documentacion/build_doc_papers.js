// Genera el PDF de referencias de una carpeta de papers a partir de su referencias_papers.md.
// Uso:  node build_doc_papers.js            → ../10_papers_union/Referencias_Papers_Union.docx
//       node build_doc_papers.js noticias   → ../11_papers_lado_noticias/Referencias_Papers_Lado_Noticias.docx
// (después convertir a PDF con LibreOffice headless)
// El contenido sale de referencias_papers.md: el PDF y el markdown no pueden quedar distintos.
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, simpleTable, nota } = u;
const { Paragraph, TextRun } = docx;

const DOCS = {
  union: { carpeta: "10_papers_union", salida: "Referencias_Papers_Union",
    titulo: "Papers relacionados con la unión", subtitulo: "Qué trabajos respaldan cada prueba y qué encontraron",
    encabezado: "Referencias de papers — tesis version 3.0", anchos: [10, 55, 35] },
  noticias: { carpeta: "11_papers_lado_noticias", salida: "Referencias_Papers_Lado_Noticias",
    titulo: "Papers relacionados con el lado de noticias", subtitulo: "Qué trabajos respaldan la recolección, el sentimiento y el NER",
    encabezado: "Referencias de papers del lado de noticias — tesis version 3.0", anchos: [17, 46, 37] },
};
const cfg = DOCS[process.argv[2] || "union"];
const CARPETA = path.join(u.RAIZ_UNION, cfg.carpeta);
const md = fs.readFileSync(path.join(CARPETA, "referencias_papers.md"), "utf8").split(/\r?\n/);

// Texto con **negrita**, *cursiva* y `código` → runs de docx.
function runs(texto, base = {}) {
  const out = [];
  let negrita = false, cursiva = false, buf = "";
  const volcar = () => { if (buf) out.push(new TextRun({ text: buf, bold: negrita, italics: cursiva, ...base })); buf = ""; };
  for (let i = 0; i < texto.length; i++) {
    if (texto.startsWith("**", i)) { volcar(); negrita = !negrita; i++; }
    else if (texto[i] === "*") { volcar(); cursiva = !cursiva; }
    else if (texto[i] === "`") {
      volcar();
      const fin = texto.indexOf("`", i + 1);
      out.push(new TextRun({ text: texto.slice(i + 1, fin), font: "Consolas", size: 18, color: "1C3A5C" }));
      i = fin;
    } else buf += texto[i];
  }
  volcar();
  return out;
}

const vineta = (texto, nivel) => p([new TextRun(nivel ? "–  " : "•  "), ...runs(texto)],
  { indent: { left: 360 + nivel * 360, hanging: 240 }, spacing: { after: 40 } });
const subtitulo = texto => new Paragraph({ keepNext: true, spacing: { before: 240, after: 100 },
  children: runs(texto, { size: 24, color: "1C3A5C", font: "Cambria" }).map(r => r) });

const cuerpo = [];
let tabla = [];
const cerrarTabla = () => {
  if (!tabla.length) return;
  const filas = tabla.filter(l => !/^\|[\s|-]+\|$/.test(l)).map(l => l.slice(1, -1).split("|").map(c => c.trim()));
  cuerpo.push(simpleTable(filas[0], filas.slice(1).map(f => f.map(c => runs(c, { size: 19 }))), cfg.anchos));
  tabla = [];
};

for (const linea of md.slice(1)) {             // la primera línea (# título) va en la portada
  if (linea.startsWith("|")) { tabla.push(linea.trim()); continue; }
  cerrarTabla();
  if (!linea.trim() || linea.trim() === "---" || linea.startsWith("Actualizado:")) continue;
  if (linea.startsWith("## ")) cuerpo.push(h1(linea.slice(3)));
  else if (linea.startsWith("### ")) cuerpo.push(subtitulo(linea.slice(4)));
  else if (/^\s*- /.test(linea)) cuerpo.push(vineta(linea.replace(/^\s*- /, ""), linea.search(/\S/) >= 2 ? 1 : 0));
  else if (linea.startsWith("**")) cuerpo.push(p(runs(linea), { keepNext: true, spacing: { before: 160, after: 60 } }));
  else cuerpo.push(p(runs(linea), { spacing: { before: 120 } }));
}
cerrarTabla();

const n = fs.readdirSync(CARPETA).filter(f => f.endsWith(".pdf") && f !== cfg.salida + ".pdf").length;
const doc = u.documentoUnion({
  titulo: cfg.titulo,
  subtitulo: cfg.subtitulo,
  encabezado: cfg.encabezado,
  ubicacion: [u.bold("Ubicación. "), code(`D:\\2.Tesina\\tesis version 3.0\\Unión\\${cfg.carpeta}\\`),
    u.plain(` (${n} PDF). Este documento se genera desde referencias_papers.md.`)],
  children: [...cuerpo, nota("Búsqueda hecha el 24/10/2026 en alphaXiv (arXiv) y en la web, en español y en inglés.")],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, cfg.salida + ".docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
