// Genera Presentacion_Tesina.pptx — tesis versión 6.0. Fase 6 de CRISP-DM (despliegue).
// Uso:  node generar_presentacion.js   (necesita pptxgenjs: npm install pptxgenjs)
// Los números son los de los metricas.csv del proyecto (los mismos del informe); las figuras se toman de
// 6_despliegue/informe/figuras/. Las notas del orador dicen quién habla; el detalle está en GUION_PRESENTACION.md.
const fs = require("fs");
const path = require("path");
const pptxgen = require("pptxgenjs");

const AQUI = __dirname;
const FIG = path.join(AQUI, "..", "informe", "figuras");
const SALIDA = path.join(AQUI, "Presentacion_Tesina.pptx");

const COL = { tinta: "13202F", azul: "1F6FA3", celeste: "7CC3EE", ambar: "B5700F", gris: "4A5568",
              grisClaro: "B7C3D3", fondo: "FFFFFF", tarjeta: "F1F4F8", verde: "2E8B57", rojo: "C0392B" };
const TIT = "Cambria", CUE = "Calibri";
const W = 13.333, H = 7.5, M = 0.6;

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE";
pres.author = "Gino Frigoni y Nicolás Diego Diddi";
pres.title = "Impacto de shocks informativos en el comportamiento bursátil de empresas argentinas";
pres.theme = { headFontFace: TIT, bodyFontFace: CUE };

pres.defineSlideMaster({
  title: "CONTENIDO", background: { color: COL.fondo },
  objects: [{ text: { text: "Frigoni · Diddi — Universidad del Gran Rosario, 2026",
                      options: { x: M, y: 7.0, w: 6, h: 0.3, fontSize: 10, color: COL.gris, fontFace: CUE } } }],
  slideNumber: { x: W - M - 1, y: 7.0, w: 1, h: 0.3, fontSize: 10, color: COL.gris, fontFace: CUE, align: "right" },
});
pres.defineSlideMaster({ title: "OSCURO", background: { color: COL.tinta } });

// ── ayudas ────────────────────────────────────────────────────────────────
function tamPng(f) {
  const b = fs.readFileSync(f);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}
function imagen(s, nombre, x, y, wMax, hMax, alt) {
  const f = path.join(FIG, nombre);
  const t = tamPng(f), r = Math.min(wMax / t.w, hMax / t.h);
  const w = t.w * r, h = t.h * r;
  s.addImage({ path: f, x: x + (wMax - w) / 2, y: y + (hMax - h) / 2, w, h, altText: alt });
}
function encabezado(s, cejilla, titulo) {
  s.addText(cejilla.toUpperCase(), { x: M, y: 0.35, w: W - 2 * M, h: 0.35, fontSize: 13, bold: true,
    color: COL.azul, charSpacing: 2, fontFace: CUE, margin: 0, isTextBox: true });
  s.addText(titulo, { x: M, y: 0.72, w: W - 2 * M, h: 1.0, fontSize: 30, bold: true, color: COL.tinta,
    fontFace: TIT, valign: "top", margin: 0, isTextBox: true });
}
function tarjeta(s, x, y, w, h, etiqueta, cuerpo, op = {}) {
  const hl = !!op.hl;
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, rectRadius: 0.12,
    fill: { color: hl ? COL.tinta : COL.tarjeta }, line: { color: hl ? COL.tinta : COL.tarjeta } });
  const runs = [];
  if (etiqueta) runs.push({ text: etiqueta, options: { bold: true, fontSize: op.tagSize || 14,
    color: op.tagColor || (hl ? COL.celeste : COL.azul), breakLine: true, paraSpaceAfter: 6 } });
  const partes = Array.isArray(cuerpo) ? cuerpo : [cuerpo];
  partes.forEach((p, i) => {
    const t = typeof p === "string" ? { text: p } : p;
    runs.push({ text: t.text, options: { fontSize: op.size || 15, color: t.color || (hl ? "E6ECF3" : COL.gris),
      bold: !!t.bold, breakLine: i < partes.length - 1, paraSpaceAfter: 4 } });
  });
  s.addText(runs, { x: x + 0.18, y: y + 0.12, w: w - 0.36, h: h - 0.24, valign: "top", fontFace: CUE,
    margin: 0, isTextBox: true });
}
function dato(s, x, y, w, numero, rotulo, op = {}) {
  s.addText(numero, { x, y, w, h: 0.85, fontSize: op.size || 44, bold: true, fontFace: TIT,
    color: op.color || COL.azul, margin: 0, isTextBox: true });
  s.addText(rotulo, { x, y: y + 0.85, w, h: 0.6, fontSize: 14, color: COL.gris, fontFace: CUE,
    valign: "top", margin: 0, isTextBox: true });
}
function flecha(s, x, y, w = 0.4, color = COL.azul) {
  s.addShape(pres.shapes.RIGHT_ARROW, { x, y, w, h: 0.32, fill: { color }, line: { color } });
}
function nueva(seccion, notas) {
  const s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: seccion });
  if (notas) s.addNotes(notas);
  return s;
}
function separador(seccion, n, titulo, pregunta, notas) {
  pres.addSection({ title: seccion });
  const s = pres.addSlide({ masterName: "OSCURO", sectionTitle: seccion });
  s.addText(`PARTE ${n} DE 4`, { x: M + 0.2, y: 1.3, w: 6, h: 0.4, fontSize: 14, bold: true, color: COL.celeste,
    charSpacing: 2, fontFace: CUE, margin: 0, isTextBox: true });
  s.addText(`0${n}`, { x: M + 0.2, y: 1.8, w: 4, h: 1.6, fontSize: 96, bold: true, color: COL.celeste, fontFace: TIT,
    margin: 0, isTextBox: true });
  s.addText(titulo, { x: M + 0.2, y: 3.5, w: 11, h: 1.0, fontSize: 44, bold: true, color: "FFFFFF", fontFace: TIT,
    margin: 0, isTextBox: true });
  s.addText(pregunta, { x: M + 0.2, y: 4.6, w: 11, h: 0.8, fontSize: 20, color: COL.grisClaro, fontFace: CUE,
    margin: 0, isTextBox: true });
  const partes = ["El problema", "Los datos", "Preparación y modelado", "Evaluación y cierre"];
  partes.forEach((p, i) => s.addText(p, { x: M + 0.2 + i * 3.0, y: 6.2, w: 2.8, h: 0.4, fontSize: 14,
    bold: i === n - 1, color: i === n - 1 ? "FFFFFF" : "6B7A8C", fontFace: CUE, margin: 0, isTextBox: true }));
  s.addNotes(notas);
}

// ── 1. Portada ────────────────────────────────────────────────────────────
pres.addSection({ title: "Portada" });
{
  const s = pres.addSlide({ masterName: "OSCURO", sectionTitle: "Portada" });
  s.addImage({ path: path.join(AQUI, "..", "informe", "logo_ugr.png"), x: M + 0.2, y: 0.5, w: 2.2,
    h: 2.2 * tamPng(path.join(AQUI, "..", "informe", "logo_ugr.png")).h / tamPng(path.join(AQUI, "..", "informe", "logo_ugr.png")).w,
    altText: "Universidad del Gran Rosario" });
  s.addText("TRABAJO FINAL DE GRADO · LICENCIATURA EN CIENCIA DE DATOS", { x: M + 0.2, y: 1.7, w: 11, h: 0.4,
    fontSize: 14, bold: true, color: COL.celeste, charSpacing: 2, fontFace: CUE, margin: 0, isTextBox: true });
  s.addText("Una metodología de ciencia de datos para medir el sentimiento de las noticias económicas argentinas y evaluar su relación con el mercado",
    { x: M + 0.2, y: 2.2, w: 11.5, h: 2.0, fontSize: 36, bold: true, color: "FFFFFF", fontFace: TIT, valign: "top", margin: 0, isTextBox: true });
  s.addText("¿Las noticias anticipan a las acciones, o las acciones a las noticias?", { x: M + 0.2, y: 4.3, w: 11, h: 0.6,
    fontSize: 22, color: COL.grisClaro, fontFace: CUE, margin: 0, isTextBox: true });
  [["Gino Frigoni", "Lado de noticias"], ["Nicolás Diego Diddi", "Lado bursátil"], ["Universidad del Gran Rosario", "Rosario · 2026"]]
    .forEach(([a, b], i) => s.addText([{ text: a, options: { bold: true, color: "FFFFFF", fontSize: 18, breakLine: true } },
      { text: b, options: { color: COL.grisClaro, fontSize: 14 } }], { x: M + 0.2 + i * 4.0, y: 5.8, w: 3.8, h: 0.8,
      fontFace: CUE, margin: 0, isTextBox: true }));
  s.addNotes("NICOLÁS abre. Saludo, presentación de ambos y del título. Remarcar desde el inicio que es una metodología de ciencia de datos, organizada con CRISP-DM.");
}

// ── Parte 1 ───────────────────────────────────────────────────────────────
separador("Parte 1 · El problema", 1, "El problema", "¿Qué queremos saber, por qué importa y cómo lo vamos a responder?", "NICOLÁS. Separador de la Parte 1.");
const P1 = "Parte 1 · El problema";
{
  const s = nueva(P1, "NICOLÁS. Los días de noticias grandes son también días de movimientos fuertes, pero eso no dice qué vino primero. «El Merval subió 5 %» es una nota positiva causada por el precio.");
  encabezado(s, "El problema", "Los días de noticias fuertes son días de mercado fuerte, pero ¿quién va primero?");
  tarjeta(s, M, 2.0, 5.4, 2.6, "Noticias → mercado", ["La nota mueve al precio.", "Trae información nueva o cambia el ánimo de los inversores: el sentimiento se adelanta al precio."], { size: 17 });
  flecha(s, 6.25, 2.85, 0.8);
  s.addShape(pres.shapes.LEFT_ARROW, { x: 6.25, y: 3.4, w: 0.8, h: 0.32, fill: { color: COL.ambar }, line: { color: COL.ambar } });
  tarjeta(s, 7.33, 2.0, 5.4, 2.6, "Mercado → noticias", ["El precio mueve a la nota.", "La nota cuenta lo que el mercado ya hizo: el precio se adelanta al sentimiento."], { size: 17, tagColor: COL.ambar });
  s.addText("«El Merval subió 5 %» es una nota de sentimiento positivo… pero su causa es el precio. Para separar las dos posibilidades hay que medir el sentimiento y ordenarlo en el tiempo con el precio.",
    { x: M, y: 5.0, w: W - 2 * M, h: 1.2, fontSize: 18, color: COL.gris, fontFace: CUE, italic: true, margin: 0, isTextBox: true });
}
{
  const s = nueva(P1, "NICOLÁS. Tres instrumentos que no existían para el mercado argentino. Nombrar los antecedentes sin detenerse.");
  encabezado(s, "Relevancia", "Para el mercado argentino no existían los instrumentos para medirlo");
  const t = [["Un corpus", "No había un conjunto de noticias económicas argentinas fechadas y depuradas."],
             ["Un modelo de sentimiento", "No había un modelo en español entrenado con prensa económica argentina."],
             ["Un termómetro del mercado", "No hay un VIX argentino: no existen opciones líquidas para calcularlo."]];
  t.forEach(([a, b], i) => tarjeta(s, M + i * 4.1, 2.1, 3.85, 2.6, `0${i + 1}`, [{ text: a, bold: true, color: COL.tinta }, b], { size: 17, tagSize: 22 }));
  s.addText("Antecedentes: Tetlock (2007), Garcia (2013), Fang y Peress (2009), Verma et al. (2026).", { x: M, y: 5.2, w: W - 2 * M, h: 0.5,
    fontSize: 15, color: COL.gris, fontFace: CUE, margin: 0, isTextBox: true });
}
{
  const s = nueva(P1, "NICOLÁS. H1 en simple: se pone a prueba la metodología. H0 es su negación exacta. El criterio tiene dos partes que se cumplen a la vez y se fijó antes de mirar resultados.");
  encabezado(s, "Hipótesis", "¿Se puede construir una metodología que mida el sentimiento y lo relacione con el mercado?");
  tarjeta(s, M, 2.0, 6.1, 4.6, "H1 · Hipótesis", [{ text: "Es posible construir una metodología de ciencia de datos que mida el sentimiento de las noticias económicas argentinas y lo relacione con el comportamiento de las acciones de BYMA.", color: "FFFFFF" },
    { text: " ", color: "FFFFFF" }, { text: "H0 · Hipótesis nula", bold: true, color: COL.celeste },
    "No es posible: o el sentimiento no se mide mejor que con un modelo genérico, o no se relaciona con las acciones en ninguna dirección."], { hl: true, size: 17 });
  s.addText("Criterio de aceptación, fijado antes de ver los datos", { x: 7.0, y: 2.0, w: 5.7, h: 0.4, fontSize: 15, bold: true, color: COL.azul, fontFace: CUE, margin: 0, isTextBox: true });
  tarjeta(s, 7.0, 2.5, 5.73, 1.8, "1 · Medir", "FinBETO supera a un modelo de sentimiento en español ya existente, en noticias que no vio (F1 macro).", { size: 16 });
  tarjeta(s, 7.0, 4.5, 5.73, 2.1, "2 · Relacionar", "En al menos una dirección, el modelo con la información del otro lado predice mejor que sin ella: el IC 95 % de ΔAUC queda entero por encima de 0.", { size: 16 });
}
{
  const s = nueva(P1, "NICOLÁS. El docente pidió objetivos escritos como resultados y no como técnicas. Cada uno se retoma en las conclusiones.");
  encabezado(s, "Objetivos", "Cuatro objetivos, cada uno con un resultado concreto");
  const o = [["Objetivo 1 · Corpus", "Un corpus de noticias económicas depurado, con cada nota asignada a la primera rueda en que el mercado pudo reaccionar."],
             ["Objetivo 2 · Sentimiento", "Un modelo de sentimiento para la prensa económica, evaluado en noticias no vistas y comparado con uno existente."],
             ["Objetivo 3 · Variables", "Sentimiento inesperado, sentimiento propio de cada empresa, retorno, volumen anormal y VIX, por acción y por rueda."],
             ["Objetivo 4 · Modelo", "Un modelo predictivo evaluado en ruedas no vistas que diga en qué dirección va la relación, o si no hay ninguna."]];
  o.forEach(([a, b], i) => tarjeta(s, M + (i % 2) * 6.1, 2.0 + Math.floor(i / 2) * 2.35, 5.95, 2.15, a, b, { size: 17, hl: i === 3 }));
}
{
  const s = nueva(P1, "NICOLÁS. Las seis fases de CRISP-DM: cada una es una carpeta del proyecto y un capítulo del informe. La fase 5 es donde se pone a prueba la hipótesis. Pasa la palabra a Gino.");
  encabezado(s, "Metodología · CRISP-DM", "Seis fases, y una carpeta del proyecto por fase");
  imagen(s, "pipeline_crispdm.png", M, 1.9, W - 2 * M, 4.3, "Las seis fases de CRISP-DM aplicadas a la tesina");
  s.addText("Todo lo que define al modelo (variables, corte temporal, métricas y criterio) se fijó antes de mirar los resultados.", { x: M, y: 6.35, w: W - 2 * M, h: 0.4,
    fontSize: 15, color: COL.gris, fontFace: CUE, italic: true, margin: 0, isTextBox: true });
}

// ── Parte 2 ───────────────────────────────────────────────────────────────
separador("Parte 2 · Los datos", 2, "Los datos", "¿Qué recolectamos, cómo lo etiquetamos y cómo definimos cada variable?", "GINO. Separador de la Parte 2.");
const P2 = "Parte 2 · Los datos";
{
  const s = nueva(P2, "GINO. Cómo se recolectaron las notas y por qué la auditoría es parte del instrumento. Por qué se descartó la cantidad de notas: abril de 2026 no tiene iProfesional.");
  encabezado(s, "Datos · El corpus", "14.012 notas de 7 portales, recolectadas y depuradas");
  dato(s, M, 1.9, 3.8, "14.012", "notas de economía, depuradas");
  dato(s, M + 4.1, 1.9, 3.8, "7", "portales nacionales, en 9 fuentes");
  dato(s, M + 8.2, 1.9, 3.8, "419", "notas de plantilla eliminadas, como «Dólar hoy»", { color: COL.ambar });
  tarjeta(s, M, 3.75, 3.85, 2.9, "Cómo se recolectó", ["Wayback Machine: Ámbito, Clarín, Infobae, La Nación y TN.", "Mapas del sitio: Clarín, El Economista e iProfesional."]);
  tarjeta(s, M + 4.1, 3.75, 3.85, 2.9, "Cinco problemas depurados", "Duplicados exactos · publicación cruzada (verificada con Qwen3) · 192 fechas recuperadas · páginas que no eran noticias · plantillas con sentimiento constante.");
  tarjeta(s, M + 8.2, 3.75, 3.93, 2.9, "Qué no usamos", "La cantidad de notas: depende de qué capturó la Wayback Machine. El modelo usa el sentimiento, que es un promedio.", { tagColor: COL.ambar });
}
{
  const s = nueva(P2, "GINO. Una nota del martes a las 20 h la puede usar el mercado recién el miércoles. Es la clave para que nada mire al futuro.");
  encabezado(s, "Datos · Alineación", "Cada nota a su rueda: la regla de las 17:00");
  const barras = [[59.8, COL.azul, "59,8 % · antes de las 17:00: cuenta para su mismo día"], [24.8, COL.celeste, "24,8 % · después del cierre: pasa a la rueda siguiente"],
                  [15.4, COL.ambar, "15,4 % · día sin rueda: pasa a la rueda siguiente"]];
  let x = M;
  const anchoBarra = 5.4;
  barras.forEach(([p, c]) => { const w = anchoBarra * p / 100; s.addShape(pres.shapes.RECTANGLE, { x, y: 1.95, w, h: 0.6, fill: { color: c }, line: { color: c } }); x += w; });
  barras.forEach(([p, c, t], i) => tarjeta(s, M, 2.8 + i * 1.3, anchoBarra, 1.15, null, [{ text: t, color: COL.tinta }], { size: 16 }));
  imagen(s, "regla_17.png", 6.3, 1.9, W - M - 6.3, 4.95, "Hora de publicación de las notas y notas por rueda");
}
{
  const s = nueva(P2, "GINO. Lo pidió el profesor: el proceso con ejemplos. Los ejemplos se eligieron al azar, con semilla fija, entre noticias que FinBETO no vio. No hubo revisión humana: el F1 mide el acuerdo con Gemma.");
  encabezado(s, "Datos · Etiquetado", "Cómo Gemma etiquetó 11.605 oraciones, paso a paso");
  const pasos = [["1 · Selección", "408 noticias, una por fuente por tanda"], ["2 · Contexto", "Lee título, bajada y 3.000 caracteres: tema, actores y sentimiento general"],
                 ["3 · Oración por oración", "Etiqueta y escribe una razón para cada una"], ["4 · Limpieza", "Saca repetidas y relleno: quedan 10.855"]];
  pasos.forEach(([a, b], i) => { tarjeta(s, M + i * 3.1, 1.95, 2.75, 1.75, a, b, { size: 15, hl: i === 3 }); if (i < 3) flecha(s, M + i * 3.1 + 2.77, 2.65, 0.3); });
  tarjeta(s, M, 3.95, 5.95, 2.75, "POS · acierto de FinBETO", [{ text: "«…las acciones que podrían recibir más dinero si MSCI habilita una futura reclasificación.»", color: COL.tinta },
    "Razón de Gemma: identifica una potencial entrada de capitales, una señal favorable."], { size: 15 });
  tarjeta(s, M + 6.15, 3.95, 5.98, 2.75, "Era MIXTO → ahora NEU", [{ text: "«Aunque Höli Haus no brinda financiación directa, … existen bancos dispuestos a otorgar créditos…»", color: COL.tinta },
    "Razón de Gemma: una señal negativa compensada por una positiva."], { size: 15, tagColor: COL.ambar });
}
{
  const s = nueva(P2, "GINO. El docente pidió fórmulas. El inesperado mide la sorpresa (hoy +10, promedio +6 → +4). El propio compara una empresa contra el mercado el mismo día. ¿Por qué 20 ruedas? Un mes de mercado; se prueban 10 y 60 en la robustez. Pasa a Nicolás.");
  encabezado(s, "Datos · Definiciones", "Las fórmulas de lo que medimos");
  const f = [["Retorno", "r(t) = [cierre(t) − cierre(t−1)] / cierre(t−1)"], ["Volumen anormal", "ln(1 + vol(t)) − promedio de las 20 ruedas previas"],
             ["Sentimiento neto de una nota", "100 × (positivas − negativas) / oraciones"], ["Sentimiento inesperado", "sentimiento(t) − promedio de las 20 ruedas previas"]];
  f.forEach(([a, b], i) => tarjeta(s, M + (i % 2) * 6.1, 1.95 + Math.floor(i / 2) * 1.45, 5.95, 1.3, a, [{ text: b, color: COL.tinta }], { size: 17 }));
  tarjeta(s, M, 4.9, W - 2 * M, 1.55, "Sentimiento propio de una empresa", [{ text: "n / (n + K) × [sentimiento de las oraciones que la nombran − sentimiento de la rueda]", color: COL.tinta },
    "n = oraciones que la nombran · K = 8,85, estimado solo con el entrenamiento · vale 0 si no hubo noticias"], { size: 17 });
  s.addText("¿Por qué 20 ruedas? Un mes de mercado: el horizonte del VIX de Cboe y de Corsi (2009).", { x: M, y: 6.55, w: W - 2 * M, h: 0.35, fontSize: 13,
    color: COL.gris, fontFace: CUE, italic: true, margin: 0, isTextBox: true });
}
{
  const s = nueva(P2, "NICOLÁS. Sin opciones líquidas se usa la volatilidad realizada. Escala por terciles. Los umbrales de EE. UU. (20 y 30) no sirven: acá el promedio es 41,9 %. Devuelve a Gino.");
  encabezado(s, "Datos · Definiciones", "El VIX argentino y su escala, definidos antes de los resultados");
  tarjeta(s, M, 1.95, 5.6, 1.6, "Fórmula", [{ text: "VIX = desvío de los retornos de las últimas 20 ruedas × √252 × 100", color: "FFFFFF" }], { hl: true, size: 17 });
  const esc = [["Bajo · hasta 33,8 %", "82 ruedas · promedio 28,4 %", COL.verde], ["Medio · 33,8 % a 39,6 %", "81 ruedas · promedio 36,5 %", COL.ambar],
               ["Alto · más de 39,6 %", "81 ruedas · promedio 61,0 % · máx. 91,0 %", COL.rojo]];
  esc.forEach(([a, b, c], i) => tarjeta(s, M, 3.75 + i * 1.0, 5.6, 0.85, a, b, { tagColor: c, size: 14 }));
  imagen(s, "vix_arg.png", 6.45, 1.95, 6.28, 4.75, "S&P Merval y VIX argentino con su escala");
}

// ── Parte 3 ───────────────────────────────────────────────────────────────
separador("Parte 3 · Preparación y modelado", 3, "Preparación y modelado", "¿Cómo medimos el sentimiento y cómo diseñamos el modelo predictivo?", "GINO. Separador de la Parte 3.");
const P3 = "Parte 3 · Preparación y modelado";
{
  const s = nueva(P3, "GINO. Dos pasos: aprende el idioma y después a clasificar. MIXTO → NEU: aportaban lo mismo al sentimiento neto; se usaron las mismas oraciones y solo cambió la etiqueta.");
  encabezado(s, "Preparación · FinBETO", "FinBETO: un modelo que aprendió el idioma de la prensa económica");
  const p = [["Punto de partida", "BETO: un BERT preentrenado en español general"], ["Paso 1 · El idioma", "Adivina palabras ocultas en el texto del corpus"],
             ["Paso 2 · Clasificar", "Ajuste fino con las oraciones de Gemma, en 3 clases"], ["Resultado", "FinBETO clasifica las 413.515 oraciones del corpus"]];
  p.forEach(([a, b], i) => { tarjeta(s, M + i * 3.1, 1.95, 2.75, 2.0, a, b, { size: 16, hl: i === 3 }); if (i < 3) flecha(s, M + i * 3.1 + 2.77, 2.8, 0.3); });
  tarjeta(s, M, 4.3, 6.6, 2.3, "La prueba del idioma", [{ text: "«La [MASK] llegó al 3 % mensual según el INDEC»", color: COL.tinta }, { text: "→ «inflación» (probabilidad 0,81)", color: COL.azul, bold: true }], { size: 19 });
  tarjeta(s, M + 6.85, 4.3, 5.28, 2.3, "De 4 clases a 3", "MIXTO pasó a NEU: las dos aportaban 0 al sentimiento neto, y así la escala queda ordenada (−1, 0, +1).", { size: 17, tagColor: COL.ambar });
}
{
  const s = nueva(P3, "GINO. El F1 macro promedia el F1 de cada clase. 0,697 contra 0,542. Dividimos por noticia, no por oración. En las 662 oraciones comparables con la versión de 4 clases: 0,731 contra 0,546. Primera parte del criterio: cumplida.");
  encabezado(s, "Preparación · Evaluación de FinBETO", "FinBETO acierta el sentimiento de noticias que nunca vio");
  dato(s, M, 1.95, 3.2, "0,697", "F1 macro de FinBETO (± 0,012, 3 semillas)", { size: 54 });
  dato(s, M + 3.4, 1.95, 3.2, "0,542", "modelo de referencia, entrenado con tuits", { size: 54, color: COL.ambar });
  s.addText([{ text: "+15,5 puntos. ", options: { bold: true, color: COL.tinta } }, { text: "El de referencia dice «neutra» en 493 de las 786 oraciones: no entiende el lenguaje económico.", options: { color: COL.gris } }],
    { x: M, y: 3.7, w: 6.4, h: 1.2, fontSize: 18, fontFace: CUE, margin: 0, isTextBox: true });
  s.addText("Prueba: 786 oraciones de 39 noticias no vistas, divididas por noticia y no por oración, para no inflar el F1.", { x: M, y: 5.0, w: 6.4, h: 1.0, fontSize: 15,
    color: COL.gris, fontFace: CUE, margin: 0, isTextBox: true });
  const filas = [[{ text: "Gemma ↓ · FinBETO →", options: { bold: true, color: COL.gris } }, "POS", "NEG", "NEU"].map(c => typeof c === "string" ? { text: c, options: { bold: true, color: COL.gris, align: "center" } } : c)];
  [["POS", 172, 20, 48], ["NEG", 14, 136, 32], ["NEU", 56, 55, 253]].forEach((r, i) => filas.push([{ text: r[0], options: { bold: true, color: COL.gris } },
    ...r.slice(1).map((v, j) => ({ text: String(v), options: { align: "center", bold: i === j, color: i === j ? "FFFFFF" : COL.tinta, fill: { color: i === j ? COL.azul : COL.tarjeta } } }))]));
  s.addText("Matriz de confusión (modelo final)", { x: 7.4, y: 1.95, w: 5.3, h: 0.4, fontSize: 15, bold: true, color: COL.azul, fontFace: CUE, margin: 0, isTextBox: true });
  s.addTable(filas, { x: 7.4, y: 2.45, w: 5.3, colW: [2.0, 1.1, 1.1, 1.1], rowH: 0.62, fontSize: 18, fontFace: CUE, border: { type: "solid", pt: 2, color: "FFFFFF" }, valign: "middle" });
  s.addText("Casi nunca confunde positivo con negativo: los errores son con la clase neutra.", { x: 7.4, y: 5.1, w: 5.3, h: 0.9, fontSize: 15, color: COL.gris, fontFace: CUE, margin: 0, isTextBox: true });
}
{
  const s = nueva(P3, "GINO. La serie nueva correlaciona 0,976 con la anterior: cambió la etiqueta, no la dinámica. Después le paso a Nicolás.");
  encabezado(s, "Preparación · Sentimiento", "Del sentimiento de cada oración al de cada rueda y cada empresa");
  imagen(s, "sentimiento_por_rueda.png", M, 1.9, 7.2, 4.9, "Sentimiento por rueda y sentimiento inesperado");
  tarjeta(s, 8.05, 1.9, 4.68, 1.5, "Sentimiento inesperado", "La rueda contra las 20 anteriores. Igual para todas las acciones ese día.", { size: 15 });
  tarjeta(s, 8.05, 3.6, 4.68, 1.5, "Sentimiento propio (NER)", "spaCy y un diccionario de tickers: se une el 99,4 % de las menciones con su oración.", { size: 15 });
  tarjeta(s, 8.05, 5.3, 4.68, 1.5, "17 empresas · hubo noticia", "Solo el 70 % de las filas tiene noticias de la empresa: la variable lo distingue.", { size: 15, tagColor: COL.ambar });
}
{
  const s = nueva(P3, "NICOLÁS. La única diferencia entre A y B es la información del otro lado. Todo se conoce al cierre de t: la regla de las 17:00 manda las notas de la noche a la rueda siguiente.");
  encabezado(s, "Modelado · El experimento", "El mismo modelo, con y sin la información del otro lado");
  tarjeta(s, M, 1.95, 5.95, 3.0, "Noticias → precio · 17 empresas × rueda", ["Predice: ¿la acción sube mañana?", "A: retornos de t a t−4, volumen anormal y VIX",
    { text: "B: A + sentimiento inesperado, sentimiento propio y hubo noticia", color: COL.tinta, bold: true }], { size: 16 });
  tarjeta(s, M + 6.15, 1.95, 5.98, 3.0, "Precio → sentimiento · una fila por rueda", ["Predice: ¿el sentimiento de mañana será más positivo que lo habitual?", "A: sentimiento inesperado de t a t−4",
    { text: "B: A + retorno del Merval de t a t−4 y VIX", color: COL.tinta, bold: true }], { size: 16, tagColor: COL.ambar });
  [["Algoritmos", "Regresión logística (principal) y random forest (confirma)"], ["Variables", "Estandarizadas con media y desvío del entrenamiento"],
   ["Afuera", "Cantidad de notas (no confiable) y régimen (sale del VIX)"]].forEach(([a, b], i) => tarjeta(s, M + i * 4.1, 5.15, 3.85, 1.5, a, b, { size: 15 }));
}
{
  const s = nueva(P3, "NICOLÁS. Por qué temporal: en la práctica solo se conoce el pasado. Se sortean ruedas y no filas porque las acciones de un mismo día se mueven juntas. Pasa la palabra a Gino.");
  encabezado(s, "Modelado · Diseño de la evaluación", "Entrenar con el pasado, evaluar una sola vez con el futuro");
  const ancho = W - 2 * M;
  s.addShape(pres.shapes.RECTANGLE, { x: M, y: 2.1, w: ancho * 0.74, h: 0.8, fill: { color: COL.azul }, line: { color: COL.azul } });
  s.addShape(pres.shapes.RECTANGLE, { x: M + ancho * 0.74, y: 2.1, w: ancho * 0.26, h: 0.8, fill: { color: COL.ambar }, line: { color: COL.ambar } });
  s.addText("Entrenamiento · 165 ruedas · 2.805 filas", { x: M + 0.2, y: 2.1, w: ancho * 0.7, h: 0.8, fontSize: 17, bold: true, color: "FFFFFF", fontFace: CUE, margin: 0, valign: "middle", isTextBox: true });
  s.addText("Test · 58 ruedas", { x: M + ancho * 0.74 + 0.15, y: 2.1, w: ancho * 0.25, h: 0.8, fontSize: 17, bold: true, color: "FFFFFF", fontFace: CUE, margin: 0, valign: "middle", isTextBox: true });
  [["02/06/2025", M, "left"], ["corte: 01/02/2026", M + ancho * 0.74 - 1.5, "center"], ["29/04/2026", W - M - 2, "right"]].forEach(([t, x, a]) =>
    s.addText(t, { x, y: 3.0, w: a === "left" ? 2 : (a === "center" ? 3 : 2), h: 0.4, fontSize: 14, color: COL.gris, fontFace: CUE, align: a, margin: 0, isTextBox: true }));
  [["Validación temporal", "Dentro del entrenamiento, 5 cortes que se extienden en el tiempo, para elegir hiperparámetros."],
   ["Métricas, fijadas antes", "AUC, balanced accuracy, F1, matriz de confusión y ΔAUC (B − A) con IC 95 %."],
   ["Intervalo de confianza", "Bootstrap por bloques de 5 ruedas: se sortean días, no filas."]].forEach(([a, b], i) => tarjeta(s, M + i * 4.1, 3.9, 3.85, 2.4, a, b, { size: 16 }));
}

// ── Parte 4 ───────────────────────────────────────────────────────────────
separador("Parte 4 · Evaluación y cierre", 4, "Evaluación y cierre", "¿Qué pasó en las ruedas que ningún modelo vio, y qué responde eso sobre la hipótesis?", "GINO. Separador de la Parte 4.");
const P4 = "Parte 4 · Evaluación y cierre";
{
  const s = nueva(P4, "GINO. El test se usa una sola vez. La diferencia de AUC es casi cero y su intervalo incluye el cero: el sentimiento no agrega nada a lo que ya dicen los retornos, el volumen y el VIX. Random forest: −0,037 [−0,089; +0,024].");
  encabezado(s, "Evaluación · Noticias → precio", "En las ruedas que nunca vio, las noticias no mejoran la predicción del precio");
  dato(s, M, 1.95, 3.0, "0,533", "AUC modelo A, solo mercado");
  dato(s, M + 3.2, 1.95, 3.0, "0,521", "AUC modelo B, con noticias");
  dato(s, M + 6.4, 1.95, 5.7, "−0,012", "ΔAUC, IC 95 % [−0,054; +0,036]: incluye el 0", { color: COL.ambar });
  imagen(s, "noticias_a_precio.png", M, 3.65, W - 2 * M, 3.15, "Curva ROC y matrices de confusión de noticias a precio");
}
{
  const s = nueva(P4, "GINO. Al revés sí: 0,526 → 0,678. Random forest: +0,158 [+0,059; +0,323]. Granger: 14 de 17 empresas contra 0 de 17. Segunda parte del criterio: cumplida.");
  encabezado(s, "Evaluación · Precio → sentimiento", "Al revés sí funciona: el mercado anticipa el sentimiento de las noticias");
  dato(s, M, 1.95, 3.0, "0,526", "AUC modelo A, solo noticias anteriores");
  dato(s, M + 3.2, 1.95, 3.0, "0,678", "AUC modelo B, con el mercado");
  dato(s, M + 6.4, 1.95, 5.7, "+0,152", "ΔAUC, IC 95 % [+0,074; +0,267]: excluye el 0", { color: COL.ambar });
  imagen(s, "precio_a_sentimiento.png", M, 3.65, W - 2 * M, 3.15, "Curva ROC y matrices de confusión de precio a sentimiento");
}
{
  const s = nueva(P4, "GINO. Lo que más pesa es el retorno del Merval del mismo día. Las notas publicadas después del cierre cuentan para la rueda siguiente, y son las que cuentan cómo cerró el mercado.");
  encabezado(s, "Evaluación · Interpretabilidad", "Lo que más pesa es cómo cerró el mercado hoy");
  const etiq = ["Retorno del Merval de hoy", "Sentimiento inesperado de hoy", "Retorno del Merval de ayer", "Sentimiento inesperado de t−2", "VIX", "Sentimiento inesperado de t−3"];
  const val = [0.510, 0.250, 0.232, 0.209, 0.133, 0.122];
  s.addChart(pres.charts.BAR, [{ name: "Coeficiente estandarizado", labels: etiq.slice().reverse(), values: val.slice().reverse() }], {
    x: M, y: 1.9, w: 8.2, h: 4.8, barDir: "bar", chartColors: ["B5700F", "1F6FA3", "B5700F", "1F6FA3", "1F6FA3", "1F6FA3"].reverse(),
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 13, dataLabelFormatCode: "0.00", dataLabelFontFace: "+mn-lt", dataLabelColor: COL.tinta,
    catAxisLabelFontSize: 14, catAxisLabelFontFace: "+mn-lt", catAxisLabelColor: COL.tinta, valAxisHidden: true,
    valGridLine: { style: "none" }, catGridLine: { style: "none" }, showLegend: false, varyColors: true });
  tarjeta(s, 9.1, 1.9, 3.63, 4.8, "Cómo se lee", ["Coeficientes de la regresión logística, modelo B de precio → sentimiento.", "Todos positivos: si el Merval sube, el sentimiento de mañana es más positivo.",
    { text: "En ámbar, el mercado; en azul, las noticias.", color: COL.tinta }], { size: 16 });
}
{
  const s = nueva(P4, "GINO. Las variantes se fijaron antes, salvo «sin abril», que se agregó porque abril no tiene iProfesional y cae en el test. El ajuste por portal achica el efecto: lo decimos en la discusión.");
  encabezado(s, "Evaluación · Robustez", "Cambiando una decisión por vez, la dirección se mantiene");
  imagen(s, "robustez.png", M, 1.85, 8.3, 4.95, "ΔAUC de cada variante de robustez con su intervalo");
  tarjeta(s, 9.15, 1.85, 3.58, 2.3, "Noticias → precio", "No aporta en ninguna de las 9 variantes (ni con random forest).", { size: 16 });
  tarjeta(s, 9.15, 4.35, 3.58, 2.45, "Precio → sentimiento", "Positivo en las 9 y significativo en 6. No alcanza con ventanas de 10 o 60 ni con el ajuste por portal.", { size: 16, tagColor: COL.ambar });
}
{
  const s = nueva(P4, "GINO. El docente pidió los desaciertos. El límite más importante: el test es un período calmo; Garcia (2013) encontró efectos sobre todo en recesiones. Pasa a Nicolás.");
  encabezado(s, "Discusión", "Lo que salió mal, lo que corregimos y los límites del resultado");
  s.addText("Desaciertos corregidos", { x: M, y: 1.85, w: 5.9, h: 0.4, fontSize: 16, bold: true, color: COL.azul, fontFace: CUE, margin: 0, isTextBox: true });
  s.addText("Límites", { x: M + 6.15, y: 1.85, w: 5.9, h: 0.4, fontSize: 16, bold: true, color: COL.ambar, fontFace: CUE, margin: 0, isTextBox: true });
  [["Primera evaluación inflada", "Dividía por oración; por noticia, el F1 bajó a su valor honesto."], ["Clase MIXTO sin uso", "Se trataba igual que la neutra: se unió con NEU."],
   ["Cantidad de notas", "El plan definía el shock por cantidad, pero depende del archivo web."], ["Demasiadas pruebas", "Cientos de Granger: se pasó a una sola comparación predictiva."]]
    .forEach(([a, b], i) => tarjeta(s, M, 2.35 + i * 1.1, 5.95, 0.98, a, b, { size: 14, tagSize: 14 }));
  [["Test corto y calmo", "58 ruedas, todas en régimen Calmo: VIX 32,4 % contra 44,9 % al entrenar."], ["Ajuste por portal", "El efecto se achica a +0,051: puede venir de qué portales publican cada día."],
   ["Sin revisión humana", "El F1 mide el acuerdo con Gemma, no con personas."], ["Datos", "Un año diario · 13,4 % de notas con hora por defecto · 17 empresas."]]
    .forEach(([a, b], i) => tarjeta(s, M + 6.15, 2.35 + i * 1.1, 5.98, 0.98, a, b, { size: 14, tagSize: 14, tagColor: COL.ambar }));
}
{
  const s = nueva(P4, "NICOLÁS. Medir: cumplido; relacionar: cumplido en una dirección. Recorrer cada objetivo con su resultado y cerrar con las líneas futuras.");
  encabezado(s, "Conclusiones", "Se rechaza H0: la metodología mide el sentimiento y lo relaciona con el mercado");
  [["Objetivo 1 · Corpus ✓", "14.012 notas de 7 portales, depuradas y asignadas a su rueda."], ["Objetivo 2 · Sentimiento ✓", "FinBETO: F1 macro 0,697, +15,5 puntos sobre el de referencia."],
   ["Objetivo 3 · Variables ✓", "Sentimiento inesperado y propio, retorno, volumen anormal y VIX: 4.148 filas."], ["Objetivo 4 · Modelo ✓", "Precio → sentimiento: ΔAUC +0,152. Noticias → precio: −0,012, sin efecto."]]
    .forEach(([a, b], i) => tarjeta(s, M + (i % 2) * 6.1, 1.95 + Math.floor(i / 2) * 1.5, 5.95, 1.35, a, b, { size: 16, hl: i === 3 }));
  tarjeta(s, M, 5.15, W - 2 * M, 1.5, "Líneas futuras", "Revisión humana de una muestra · el matiz de las mixtas como dimensión aparte · análisis por portal · varios años, con crisis · precios intradiarios y en dólares.", { size: 16 });
}
{
  const s = pres.addSlide({ masterName: "OSCURO", sectionTitle: P4 });
  s.addText("CONCLUSIÓN PRINCIPAL", { x: M + 0.2, y: 1.3, w: 8, h: 0.4, fontSize: 14, bold: true, color: COL.celeste, charSpacing: 2, fontFace: CUE, margin: 0, isTextBox: true });
  s.addText("Se construyó una metodología de ciencia de datos que mide el sentimiento de la prensa económica argentina: en el período estudiado, los medios siguieron al mercado, no al revés.",
    { x: M + 0.2, y: 1.9, w: 11.6, h: 2.6, fontSize: 30, italic: true, color: "FFFFFF", fontFace: TIT, valign: "top", margin: 0, isTextBox: true });
  s.addText("¡Gracias! ¿Preguntas?", { x: M + 0.2, y: 5.0, w: 10, h: 0.8, fontSize: 36, bold: true, color: COL.celeste, fontFace: TIT, margin: 0, isTextBox: true });
  s.addText("Gino Frigoni · Nicolás Diego Diddi", { x: M + 0.2, y: 5.85, w: 10, h: 0.5, fontSize: 18, color: COL.grisClaro, fontFace: CUE, margin: 0, isTextBox: true });
  s.addNotes("AMBOS. Agradecen. En las preguntas, cada uno responde las de su lado; las del modelo, quien se sienta más seguro.");
}
pres.addSection({ title: "Anexo" });
{
  const s = pres.addSlide({ masterName: "CONTENIDO", sectionTitle: "Anexo" });
  encabezado(s, "Anexo", "Material de respaldo para las preguntas");
  [["A1 · Corpus", "Los cinco problemas de calidad y su solución (cap. 3)"], ["A2 · Etiquetado", "Seis ejemplos al azar con la razón de Gemma (cap. 4)"],
   ["A3 · FinBETO", "División por noticia y F1 por clase (cap. 4)"], ["A4 · VIX", "Los picos de cepo y elecciones, y el eco de 20 ruedas (cap. 4)"],
   ["A5 · Regímenes", "HMM: Calmo, Moderado y Tenso; BIC y transiciones (anexo C)"], ["A6 · Verificación clásica", "VAR y Granger: el retorno anticipa al sentimiento (cap. 6)"],
   ["A7 · Modelo", "Hiperparámetros elegidos por validación temporal (anexo B)"], ["A8 · Reproducibilidad", "Carpetas por fase y números generados por código (anexo A)"]]
    .forEach(([a, b], i) => tarjeta(s, M + (i % 2) * 6.1, 1.95 + Math.floor(i / 2) * 1.2, 5.95, 1.05, a, b, { size: 15 }));
  s.addNotes("No se expone. Cada ficha remite al informe, para mostrarla si el tribunal pregunta.");
}

pres.writeFile({ fileName: SALIDA }).then(f => console.log("escrito:", f));
