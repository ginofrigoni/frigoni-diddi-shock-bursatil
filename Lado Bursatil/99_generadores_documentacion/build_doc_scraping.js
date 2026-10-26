// Genera Documentacion_Scraping_Acciones.docx dentro de ../01_scraping_acciones/
// Uso:  node build_doc_scraping.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const { Packer } = require("docx");
const { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, leerCsv, documento, seccionReferencias } = require("./comun");

const CARPETA = path.join(RAIZ, "01_scraping_acciones");
const panel = leerCsv(path.join(CARPETA, "panel_acciones_final.csv"));
const descartadas = leerCsv(path.join(CARPETA, "descartadas_por_cobertura.csv"));
const cobertura = leerCsv(path.join(CARPETA, "cobertura_53_candidatas.csv"));
const nFilasPrecios = fs.readFileSync(path.join(CARPETA, "precios_diarios_47_acciones.csv"), "utf-8").split(/\r?\n/).filter(l => l).length - 1;

const DIAS_MAX = Math.max(...cobertura.filter(r => r.estado === "descargada").map(r => Number(r.dias)));
const sinBA = t => t.replace(".BA", "");
const pct = v => Number(v).toFixed(1).replace(".", ",") + "%";
const miles = n => n.toLocaleString("es-AR");

// Tabla de sectores: cantidad + tickers, de mayor a menor
const porSector = {};
for (const r of panel) (porSector[r.sector] = porSector[r.sector] || []).push(sinBA(r.ticker));
const filasSector = Object.entries(porSector)
  .sort((a, b) => b[1].length - a[1].length || a[0].localeCompare(b[0]))
  .map(([s, ts]) => [s, String(ts.length), ts.sort().join(", ")]);

// Motivo de descarte, armado desde los datos
const filasDescartadas = descartadas.map(r => {
  let motivo;
  if (r.estado !== "descargada") motivo = "Sin datos en Yahoo Finance";
  else if (Number(r.dias) < DIAS_MAX) motivo = `${r.dias} de ${DIAS_MAX} días (cotiza desde ${r.fecha_inicio.slice(5, 7)}/${r.fecha_inicio.slice(0, 4)}) y solo ${pct(r.pct_dias_con_volumen)} con volumen real`;
  else motivo = `${r.dias} días, pero solo ${pct(r.pct_dias_con_volumen)} con volumen real`;
  return [r.ticker, r.empresa, motivo];
});

const nOficiales = panel.filter(r => r.oficial === "True").length;
const gcdi = cobertura.find(r => r.ticker === "GCDI.BA");
const rose = cobertura.find(r => r.ticker === "ROSE.BA");

const doc = documento({
  titulo: "Scraping de acciones",
  subtitulo: "Selección del panel de empresas",
  encabezado: "Scraping de acciones — tesis version 3.0",
  ubicacion: [bold("Ubicación de todo lo generado. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\01_scraping_acciones\\"),
    plain(". Es el punto de partida del lado bursátil: todas las carpetas siguientes leen el panel que sale de acá.")],
  children: [
    h1("1. Objetivo"),
    p("Definir con qué empresas se trabaja, con un criterio basado en datos verificables y guardado junto con el " +
      "resultado. La pregunta concreta: ¿el panel puede ampliarse más allá de las 20 empresas oficiales del S&P Merval? " +
      "Más empresas pueden dar mejores resultados en los análisis siguientes (clustering, VAR, HMM), pero sin sacrificar " +
      "calidad de dato: una acción con huecos de cotización o sin operaciones reales no aporta, contamina."),

    h1("2. Universo de partida — las 53 candidatas"),
    p("Se parte de 53 tickers del Panel General y Panel Líderes de BYMA: las 20 oficiales del Merval más 33 candidatas " +
      "de sectores similares."),
    refBox("53 tickers, 52 empresas", [
      [plain("TGLT.BA y GCDI.BA son el mismo emisor: TGLT pasó a llamarse GCDI. El ticker viejo ya no tiene datos en " +
        "Yahoo Finance, por eso TGLT figura como \"sin datos\" — no es una empresa que se haya caído del panel, sigue " +
        "presente como GCDI.")],
    ]),
    p(""),
    p([bold("Nombres y sectores. "), plain("Verificados contra la ficha de cada ticker en Yahoo Finance. El sector se " +
      "asigna por el negocio principal de la empresa; los holdings diversificados (Garovaglio y Zorraquín, Sociedad " +
      "Comercial del Plata, Cresud) van como Conglomerado.")]),
    p([bold("Ventana temporal — fija, 3 años exactos: "), plain("2023-05-03 → 2026-05-03. El final coincide a propósito " +
      "con el final de la ventana del corpus de noticias del compañero (2026-05-03), para que el panel de 3 años y la " +
      "ventana de 1 año que usan VIX, ADF y volatilidad terminen el mismo día. La última rueda con datos es el " +
      "30/04/2026: el 01/05 es feriado y el 02-03/05 es fin de semana.")]),

    h1("3. Qué se midió — cobertura de días y de volumen"),
    p("Para cada una de las 53 candidatas se descargó la serie diaria completa (Open/High/Low/Close/Volume, vía " +
      "yfinance, precios ajustados) y se midieron dos cosas por separado:"),
    simpleTable(["Medida", "Qué es"], [
      ["dias", `Cuántas ruedas trajo Yahoo Finance en la ventana, recortadas al calendario real de BYMA (ver sección 4). El máximo observado entre las 53 es ${DIAS_MAX}.`],
      ["pct_dias_con_volumen", "De esos días, qué porcentaje tuvo Volume > 0 (operaciones reales), contra días con Volume = 0."],
    ], [30, 70]),
    p(""),
    refBox("Qué pasa exactamente en un día con Volume = 0", [
      "No es una fila vacía ni un día faltante — Yahoo Finance sí entrega el renglón, pero con el precio \"pegado\" al " +
      "último valor que sí operó y Volume en cero. Ejemplo real, tomado de una de las candidatas con peor cobertura de " +
      "volumen (Polledo, POLL.BA): retorno diario exactamente 0,000000 en esos días, con rachas de varios días seguidos " +
      "así. Por eso el criterio de selección no puede basarse solo en el calendario, tiene que exigir también volumen real.",
    ]),

    h1("4. El criterio de selección"),
    p("Dos condiciones, ambas obligatorias:", { keepNext: true }),
    simpleTable(["Condición", "Umbral", "Por qué"], [
      ["Cobertura de calendario", `dias = máximo observado (${DIAS_MAX}), sin excepciones`, "Sin tolerancia: una empresa a la que le falta un solo día también queda afuera."],
      ["Días con volumen real", "≥ 90%", "Tolera algún corte de datos aislado, pero excluye a las que tienen huecos largos de inactividad."],
    ], [26, 30, 44]),
    p(""),
    refBox("Calendario real de BYMA — tomado del índice, no de cada acción", [
      "Yahoo Finance agrega, para cada acción individual, una fila \"fantasma\" en los feriados de BYMA (precio pegado al " +
      "cierre anterior, Volume = 0) que el índice ^MERV no tiene. Se confirmó con YPFD.BA el 01/05/2026 (feriado): la " +
      "acción trae una fila con Volume = 0, el índice no trae nada ese día. Como pasa en varias fechas a lo largo de los 3 " +
      "años, el script descarga primero ^MERV y usa su lista de fechas como filtro para todas las acciones — así todas " +
      "comparten exactamente las mismas ruedas que el índice. Sin ese filtro, el máximo de días sería 732 en vez de 731 y " +
      "la mayoría de las acciones mostraría ~99,9% de días con volumen en vez de 100%, por feriados que no son ruedas reales.",
    ]),
    p(""),
    refBox("Reintentos ante fallas transitorias de Yahoo Finance", [
      "Yahoo Finance falla de forma intermitente para algunos tickers: GARO.BA y HAVA.BA llegaron a dar \"sin datos\" en " +
      "una corrida y días completos en la siguiente. Para no confundir una falla de la fuente con una baja real, el script " +
      "reintenta hasta 3 veces por ticker antes de declarar \"sin datos\"; con eso el resultado es estable entre corridas.",
    ]),

    h1("5. Eventos corporativos mal ajustados por Yahoo Finance"),
    p("Yahoo Finance entrega precios ajustados por splits y dividendos en acciones, pero en dos casos el ajuste vino mal. " +
      "Se detectaron buscando retornos diarios mayores a ±50% en las 47 acciones seleccionadas, y se corrigen dentro " +
      "del propio script (lista CORRECCIONES), con el ajuste estándar de un split: precios divididos por el factor y " +
      "volumen multiplicado por el mismo factor.", { keepNext: true }),
    simpleTable(["Acción", "Qué vino mal", "Corrección"], [
      ["SEMI.BA", "Yahoo registra un split de 4,227 el 16/12/2024 y ajustó los días anteriores, pero dejó ese día con el precio sin dividir: $113,2 entre $27,3 y $29,8.",
        "Solo el 16/12/2024, dividido por 4,227 (queda en $26,8)."],
      ["AGRO.BA", "Dividendo en acciones de noviembre 2023 (Yahoo lo registra como split 21:10 el 06/11/2023) que Yahoo no aplicó a los precios anteriores: la serie mostraba una caída falsa de −88%.",
        "Todo hasta el 02/11/2023, dividido por 2,1."],
    ], [14, 54, 32]),
    p(""),
    refBox("Lo que se dejó como está", [
      [bold("AGRO.BA 03/11/2023: "), plain("aun después del ajuste, ese día cierra en $13,9 (−76%) y el siguiente en $27 (+94%). " +
        "Tiene 8,5 millones de acciones operadas, así que no hay prueba de que sea un dato falso; se mantiene, pero conviene " +
        "tenerlo presente al interpretar a AGRO en los análisis de 3 años.")],
      [bold("Saltos grandes que son reales: "), plain("GCDI 24/01/2024 (+97%), CELU 17/09/2025 (+54%) y 18/02/2026 (−40% y +50% " +
        "al día siguiente), RIGO 18/06/2025 (+31% y −20%). En todos el precio se sostiene o el movimiento viene con volumen " +
        "muy por encima de lo normal, la firma de un shock real y no de un error de datos.")],
    ]),

    h1(`6. Resultado — ${panel.length} de 53 pasan el criterio`),
    p(`${panel.length} de las 53 candidatas cumplen las dos condiciones. Quedan repartidas en ${filasSector.length} sectores:`, { keepNext: true }),
    simpleTable(["Sector", "Empresas", "Tickers"], filasSector, [22, 13, 65]),
    p(""),
    p(`Las ${descartadas.length} que quedan afuera:`, { keepNext: true }),
    simpleTable(["Ticker", "Empresa", "Motivo"], filasDescartadas, [16, 34, 50]),
    p(""),
    p([bold("Casos al borde del umbral de volumen. "), plain(`GCDI.BA entra con ${pct(gcdi.pct_dias_con_volumen)} de días ` +
      `con volumen real; ROSE.BA queda afuera con ${pct(rose.pct_dias_con_volumen)}.`)]),
    p([bold(`Las 20 oficiales del Merval, todas incluidas. `), plain(`Las 20 cumplen el máximo de días y ≥90% de volumen ` +
      `real. El panel las contiene a las ${nOficiales}, más ${panel.length - nOficiales} adicionales.`)]),

    h1("7. Archivos generados"),
    p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\01_scraping_acciones\\")]),
    simpleTable(["Archivo", "Qué es"], [
      ["scraping_acciones.py", "Único script. Descarga ^MERV para fijar el calendario real; descarga las 53 (con reintentos y las correcciones de eventos corporativos) y mide cobertura -> aplica el criterio -> guarda los precios diarios de las que pasan."],
      ["cobertura_53_candidatas.csv", "Las 53 candidatas con sus días, % de volumen y estado (descargada / sin_datos)."],
      ["panel_acciones_final.csv", `Las ${panel.length} que pasan el criterio, con empresa y sector.`],
      ["descartadas_por_cobertura.csv", `Las ${descartadas.length} que no pasan, con sus días y % de volumen.`],
      [`precios_diarios_${panel.length}_acciones.csv`, `Precios día por día (Open/High/Low/Close/Volume) de las ${panel.length} seleccionadas, recortados al calendario real y con los dos eventos corporativos corregidos — ${miles(nFilasPrecios)} filas.`],
    ], [34, 66]),

    h1("8. Qué queda fuera de este documento (a propósito)"),
    p("Este documento cubre únicamente la selección de acciones a partir de datos de mercado (cobertura y volumen). No " +
      "evalúa si estas empresas tienen o no menciones en el corpus de noticias, ni toca el diccionario de variantes de " +
      "nombres (gazetteer) usado para detectar sentimiento por empresa — eso corresponde a la rama de noticias del trabajo."),

    ...seccionReferencias("01_scraping_acciones", 9),
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_Scraping_Acciones.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
