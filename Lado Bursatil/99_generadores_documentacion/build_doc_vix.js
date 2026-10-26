// Genera Documentacion_VIX_Argentino.docx dentro de ../03_vix_argentino/
// Uso:  node build_doc_vix.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const { Packer } = require("docx");
const { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, documento, seccionReferencias, notaAnualizacion } = require("./comun");

const CARPETA = path.join(RAIZ, "03_vix_argentino");
const v = leerCsv(path.join(CARPETA, "vix_arg.csv")).map(r => ({
  fecha: r.fecha, merv: Number(r.merv_cierre), ret: Number(r.retorno_diario), vix: Number(r.vix_arg),
}));

const VENTANA = 20, UMBRAL_ALTO = 55;
const coma = (x, d = 1) => Number(x).toFixed(d).replace(".", ",");
const pct = (x, d = 1) => (x >= 0 ? "+" : "−") + coma(Math.abs(x) * 100, d) + "%";
const fecha = f => `${f.slice(8, 10)}/${f.slice(5, 7)}/${f.slice(0, 4)}`;
const millones = x => "$" + coma(x / 1e6, 2) + " M";

const prom = v.reduce((s, r) => s + r.vix, 0) / v.length;
const minV = v.reduce((a, b) => (b.vix < a.vix ? b : a));
const maxV = v.reduce((a, b) => (b.vix > a.vix ? b : a));
const minM = v.reduce((a, b) => (b.merv < a.merv ? b : a));
const maxM = v.reduce((a, b) => (b.merv > a.merv ? b : a));

// Episodios con VIX > UMBRAL_ALTO; el disparador es el mayor |retorno| entre los 3 días previos y el inicio
const episodios = [];
for (let i = 0; i < v.length; i++) {
  if (v[i].vix <= UMBRAL_ALTO || (i > 0 && v[i - 1].vix > UMBRAL_ALTO)) continue;
  let j = i;
  while (j + 1 < v.length && v[j + 1].vix > UMBRAL_ALTO) j++;
  let d = Math.max(i - 3, 0);
  for (let k = d; k <= i; k++) if (Math.abs(v[k].ret) > Math.abs(v[d].ret)) d = k;
  let pico = i;
  for (let k = i; k <= j; k++) if (v[k].vix > v[pico].vix) pico = k;
  episodios.push({ ini: v[i].fecha, fin: v[j].fecha, ruedas: j - i + 1, pico: v[pico], disp: v[d],
    sale: d + VENTANA < v.length ? v[d + VENTANA] : null });
}

// Saltos de un día del VIX de más de 10 puntos
const saltos = [];
for (let i = 1; i < v.length; i++) {
  const dv = v[i].vix - v[i - 1].vix;
  if (Math.abs(dv) > 10) saltos.push({ f: v[i].fecha, de: v[i - 1].vix, a: v[i].vix, ret: v[i].ret });
}

// Contexto de cada episodio (hechos fechados del período)
const CONTEXTO = {
  "2025-04": "Turbulencia global por los aranceles de EE.UU.: el disparador es el rebote del 09/04, el día de la pausa de los aranceles. Incluye la salida del cepo cambiario (14/04/2025).",
  "2025-09": "El disparador es la caída del 08/09, el día hábil siguiente a la elección legislativa de la provincia de Buenos Aires (07/09/2025). En este tramo el Merval toca el mínimo de toda la ventana.",
  "2025-10": "El disparador es la suba del 27/10, el día hábil siguiente a las elecciones legislativas nacionales (26/10/2025). El máximo de toda la serie viene de una SUBA, no de una caída.",
};

const doc = documento({
  titulo: "VIX argentino",
  subtitulo: "Volatilidad realizada del mercado, día por día",
  encabezado: "VIX argentino — tesis version 3.0",
  ubicacion: [bold("Ubicación de todo lo generado. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\03_vix_argentino\\"),
    plain(". Su ventana de fechas es la que después leen ADF, volatilidad por acción, clustering (1 año) y HMM.")],
  children: [
    h1("1. Qué es y cómo se calcula"),
    p("El VIX de Chicago Board se construye con precios de opciones sobre el S&P 500 — mide volatilidad implícita, lo que " +
      "el mercado espera que pase. En Argentina no existe un mercado de opciones con la liquidez necesaria para calcular " +
      "algo así, así que se construye un análogo con volatilidad realizada: qué tan dispersos fueron los retornos del " +
      "índice en los últimos días.", { keepNext: true }),
    simpleTable(["Paso", "Cálculo"], [
      ["1", "Cierre diario del índice ^MERV (Yahoo Finance)"],
      ["2", "Retorno diario: (hoy − ayer) / ayer"],
      ["3", `Desvío estándar de los últimos ${VENTANA} días de retornos`],
      ["4", "Anualizado: × raíz(252) × 100, para leerlo como % anual"],
    ], [12, 88]),
    p(""),
    notaAnualizacion(v, prom, "la volatilidad del Merval"),
    p(""),
    refBox("Independiente del panel de acciones — y con la ventana del corpus de noticias", [
      [plain("Este cálculo usa el índice ^MERV directamente — no depende de qué empresas estén en el panel de " +
        "01_scraping_acciones. La ventana final (2025-01-02 → 2026-05-03) es la que cubre el corpus de noticias del " +
        "compañero — es la que va a definir el dataset combinado final. Los análisis siguientes leen esta misma ventana " +
        "directamente de "), code("vix_arg.csv"), plain(", no la repiten a mano, para que no puedan desalinearse.")],
    ]),

    h1("2. Ventana y resultado"),
    simpleTable(["", "Valor"], [
      ["Ventana pedida", "2025-01-02 → 2026-05-03"],
      ["Descarga (con margen para la ventana rodante)", "2024-11-15 → 2026-05-03"],
      ["Días con VIX válido", String(v.length)],
      ["Rango efectivo del vix_arg", `${v[0].fecha} → ${v[v.length - 1].fecha} (no hay ruedas el 01-03/05/2026: feriado y fin de semana)`],
      ["Promedio", coma(prom) + "%"],
      ["Mínimo", `${coma(minV.vix)}% — ${fecha(minV.fecha)}`],
      ["Máximo", `${coma(maxV.vix)}% — ${fecha(maxV.fecha)}`],
      ["Merval: mínimo y máximo de la ventana", `${millones(minM.merv)} el ${fecha(minM.fecha)} · ${millones(maxM.merv)} el ${fecha(maxM.fecha)}`],
    ], [44, 56]),

    h1(`3. Cómo leer este VIX — el eco de la ventana de ${VENTANA} días`),
    p(`Al ser un desvío de los últimos ${VENTANA} días, un único día con un movimiento extremo queda adentro del cálculo ` +
      `durante exactamente ${VENTANA} ruedas: el VIX salta el día en que entra, y cae de golpe el día en que sale — aunque ` +
      `ese día el mercado no haga nada especial. Además mide movimiento en cualquier dirección: una suba fuerte lo ` +
      `dispara igual que una caída.`),
    p(`En toda la ventana hay ${saltos.length} saltos del VIX de más de 10 puntos en un día:`, { keepNext: true }),
    simpleTable(["Fecha", "VIX", "Retorno del Merval ese día", "Qué es"], saltos.map(s => {
      const disp = episodios.find(e => e.sale && e.sale.fecha === s.f);
      return [fecha(s.f), `${coma(s.de)}% → ${coma(s.a)}%`, pct(s.ret),
        s.a > s.de ? "Entra un día extremo a la ventana" :
          (disp ? `Sale de la ventana el ${pct(disp.disp.ret)} del ${fecha(disp.disp.fecha)}` : "Sale un día extremo de la ventana")];
    }), [16, 24, 24, 36]),
    p(""),
    p([bold("Consecuencia práctica: "), plain("las subidas bruscas del VIX marcan el día del shock, pero las bajadas bruscas no " +
      "marcan que el mercado se haya calmado ese día — marcan que el shock cumplió 20 ruedas. Cualquier análisis que use " +
      "el VIX para separar \"días calmos\" de \"días nerviosos\" (como el HMM de régimen) hereda estas fechas.")]),

    h1(`4. Los episodios de volatilidad alta (VIX > ${UMBRAL_ALTO}%)`),
    simpleTable(["Período", "Ruedas", "Pico", "Día que lo dispara", "Contexto"], episodios.map(e => [
      `${fecha(e.ini)} → ${fecha(e.fin)}`, String(e.ruedas), `${coma(e.pico.vix)}% (${fecha(e.pico.fecha)})`,
      `${fecha(e.disp.fecha)}: ${pct(e.disp.ret)}`, CONTEXTO[e.ini.slice(0, 7)] || "",
    ]), [17, 9, 16, 17, 41]),
    p(""),
    p(`Los dos episodios del segundo semestre duran exactamente ${VENTANA} ruedas: son, casi en su totalidad, el eco de un ` +
      `único día. El de abril-mayo es más largo porque acumula varios días grandes seguidos.`),

    h1("5. Gráfico"),
    figure(path.join(CARPETA, "vix_arg.png"), 560),
    p("Panel superior: índice Merval en pesos (nominal, sin ajustar por inflación — por eso la tendencia de fondo es tan " +
      "marcada). Panel inferior: el VIX argentino, con el promedio de referencia y sombreado el tiempo que estuvo por " +
      "encima de él."),

    h1("6. Archivos generados"),
    p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\03_vix_argentino\\")]),
    simpleTable(["Archivo", "Qué es"], [
      ["calcular_vix_arg.py", "Script único. Descarga ^MERV, calcula retorno y VIX argentino, guarda el CSV y el gráfico."],
      ["vix_arg.csv", `fecha, merv_cierre, retorno_diario, vix_arg — ${v.length} filas.`],
      ["vix_arg.png", "Merval + VIX argentino, dos paneles."],
    ], [30, 70]),

    ...seccionReferencias("03_vix_argentino", 7),
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_VIX_Argentino.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
