// Genera Documentacion_Volatilidad_Ranking.docx dentro de ../05_volatilidad_ranking/
// Uso:  node build_doc_volatilidad.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const { Packer } = require("docx");
const { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, documento, seccionReferencias, notaAnualizacion } = require("./comun");

const CARPETA = path.join(RAIZ, "05_volatilidad_ranking");
const ranking = leerCsv(path.join(CARPETA, "ranking_volatilidad.csv"));
const picos = leerCsv(path.join(CARPETA, "picos_propios.csv"));
const vix = leerCsv(path.join(RAIZ, "03_vix_argentino", "vix_arg.csv"));
const nDias = fs.readFileSync(path.join(CARPETA, "volatilidad_acciones.csv"), "utf-8").split(/\r?\n/).filter(l => l).length - 1;

const N = ranking.length;
const coma = (v, d = 1) => Number(v).toFixed(d).replace(".", ",");
const fecha = f => `${f.slice(8, 10)}/${f.slice(5, 7)}/${f.slice(0, 4)}`;
const sinBA = t => t.replace(".BA", "");
const vixProm = vix.reduce((s, r) => s + Number(r.vix_arg), 0) / vix.length;
const panelProm = ranking.reduce((s, r) => s + Number(r.vol_prom), 0) / N;
const fIni = vix[0].fecha, fFin = vix[vix.length - 1].fecha;

const fila = r => [r.ticker, r.empresa, r.sector, coma(r.vol_prom) + "%"];
const calmas = ranking.slice(0, 5).map(fila);
const nerviosas = ranking.slice(-5).reverse().map(fila);

const porSector = {};
for (const r of ranking) (porSector[r.sector] = porSector[r.sector] || []).push(Number(r.vol_prom));
const filasSector = Object.entries(porSector)
  .map(([s, vs]) => [s, String(vs.length), vs.reduce((a, b) => a + b, 0) / vs.length])
  .sort((a, b) => a[2] - b[2])
  .map(([s, n, m]) => [s, n, coma(m) + "%"]);

const genuinos = picos.filter(r => r.tras_caida_vix === "False");
const eco = picos.filter(r => r.tras_caida_vix === "True");
const filasPicos = genuinos.map(r => [sinBA(r.ticker), `${fecha(r.desde)} → ${fecha(r.hasta)}`, r.dias, coma(r.pico_vol, 0) + "%", coma(r.vix_en_pico, 0) + "%"]);
const tickersEco = [...new Set(eco.map(r => sinBA(r.ticker)))].sort();

const doc = documento({
  titulo: "Volatilidad por acción",
  subtitulo: "El mismo cálculo del VIX, pero acción por acción",
  encabezado: "Volatilidad por acción y ranking — tesis version 3.0",
  ubicacion: [bold("Ubicación de todo lo generado. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\05_volatilidad_ranking\\"),
    plain(`. Input: el panel de ${N} acciones de `), code("01_scraping_acciones"), plain(" y la ventana de "), code("03_vix_argentino"), plain(".")],
  children: [
    h1("1. Qué mide y cómo se calcula"),
    p("Es el mismo cálculo del VIX argentino, pero por acción en vez de por el índice general: desvío estándar rodante de " +
      "20 días de los retornos diarios, anualizado (× raíz(252) × 100). Muestra qué tan nerviosa estuvo cada acción en " +
      "particular, día por día, y permite compararla contra el nerviosismo del mercado en su conjunto."),
    refBox("Ventana — la del corpus de noticias, tomada de vix_arg.csv", [
      [bold(`${fIni} → ${fFin}, ${nDias} días`), plain(" — exactamente los mismos días que el VIX argentino y el ADF, leídos " +
        "de "), code("vix_arg.csv"), plain(" (no hardcodeados acá). Tanto el retorno como el desvío rodante de 20 días se " +
        "calculan sobre la serie completa de precios y recién después se recortan a la ventana — igual que el VIX, que usa " +
        "los días previos como \"calentamiento\". Así el primer día de la ventana ya tiene su volatilidad, sin perder los " +
        "primeros 19 días.")],
    ]),

    p(""),
    notaAnualizacion(vix, panelProm, "la volatilidad de cada acción"),

    h1("2. Ranking — de más calma a más nerviosa"),
    p(`Volatilidad promedio del panel de ${N}: ${coma(panelProm)}%. VIX de mercado en los mismos ${nDias} días: ` +
      `${coma(vixProm)}% — el panel de acciones individuales es, en promedio, bastante más nervioso que el índice ` +
      `(esperable: el índice diversifica, cada acción sola no).`),
    figure(path.join(CARPETA, "ranking_volatilidad.png"), 470),
    p("Las 5 más calmas:", { keepNext: true }),
    simpleTable(["Ticker", "Empresa", "Sector", "Volatilidad prom."], calmas, [16, 40, 22, 22]),
    p(""),
    p("Las 5 más nerviosas:", { keepNext: true }),
    simpleTable(["Ticker", "Empresa", "Sector", "Volatilidad prom."], nerviosas, [16, 40, 22, 22]),

    h1("3. Volatilidad por sector, comparada contra el mercado"),
    p("Promedio de las acciones de cada sector, de más calmo a más nervioso:", { keepNext: true }),
    simpleTable(["Sector", "Acciones", "Volatilidad prom."], filasSector, [44, 22, 34]),
    p(""),
    figure(path.join(CARPETA, "volatilidad_por_sector.png"), 440),
    p("La mayoría de las acciones sigue de cerca al VIX de mercado — sube y baja con él, sobre todo en los episodios de " +
      "abril-mayo, septiembre-octubre y octubre-noviembre de 2025."),

    h1("4. Picos propios — la acción nerviosa con el mercado tranquilo"),
    p(`Se marca como "pico propio" cada tramo de 3 días o más en que la volatilidad de una acción supera al VIX por más ` +
      `de 60 puntos mientras el VIX está por debajo de 50% — la acción muy alterada en un mercado tranquilo. Los ` +
      `episodios se calculan en el script y quedan en picos_propios.csv (${picos.length} episodios en total).`),
    refBox("Cuidado con el eco de la ventana de 20 días", [
      `${eco.length} de los ${picos.length} episodios arrancan en los días siguientes a una caída brusca del VIX (más de 10 ` +
      `puntos en un día: 06/10/2025 y 25/11/2025). Esas caídas son el día más grande del mercado saliendo de la ventana ` +
      `de 20 ruedas: el VIX se "calma" de golpe, mientras cada acción todavía conserva en su propia ventana sus días ` +
      `grandes de las semanas anteriores. En esos casos (${tickersEco.join(", ")}) la acción no está necesariamente ` +
      `nerviosa por algo propio — el mercado se calmó antes en el cálculo. No se cuentan como picos propios.`,
    ]),
    p(""),
    p(`Quedan ${genuinos.length} episodios genuinos, en ${new Set(genuinos.map(r => r.ticker)).size} acciones:`, { keepNext: true }),
    simpleTable(["Acción", "Tramo", "Días", "Pico de la acción", "VIX ese día"], filasPicos, [14, 34, 12, 20, 20]),
    p(""),
    p([bold("Para cruzar con las noticias. "), plain("Estos tramos son los candidatos naturales a eventos propios de cada " +
      "empresa (una noticia puntual, un hecho relevante, un cambio de control). Cuando se una con el lado de sentimiento, " +
      "vale la pena ver si coinciden con algo en el corpus o si son ruido de mercado de acciones poco líquidas.")]),

    h1("5. Archivos generados"),
    p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\05_volatilidad_ranking\\")]),
    simpleTable(["Archivo", "Qué es"], [
      ["volatilidad_ranking.py", `Script único. Calcula la volatilidad rodante de las ${N} acciones, el ranking, los picos propios y los dos gráficos.`],
      ["volatilidad_acciones.csv", `Formato ancho: una columna por acción, una fila por día (${nDias} días).`],
      ["ranking_volatilidad.csv", "Una fila por acción: ticker, empresa, sector, volatilidad promedio."],
      ["picos_propios.csv", "Un episodio por fila: acción, tramo, pico, VIX ese día y si arranca tras una caída brusca del VIX (eco de ventana)."],
      ["ranking_volatilidad.png", "Barras horizontales, coloreadas por sector, con el VIX de mercado como referencia."],
      ["volatilidad_por_sector.png", "Un panel por sector, cada acción vs. el VIX de mercado."],
    ], [32, 68]),

    ...seccionReferencias("05_volatilidad_ranking", 6),
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_Volatilidad_Ranking.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
