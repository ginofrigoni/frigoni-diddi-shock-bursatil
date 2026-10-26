// Genera Documentacion_Pipeline_Union.docx dentro de ../00_pipeline_union/
// Uso:  node build_doc_pipeline_union.js   (después convertir a PDF con LibreOffice headless)
// Reutiliza las piezas de estilo del lado bursátil (comun.js y su node_modules/docx).
const fs = require("fs");
const path = require("path");
const BURSATIL_GEN = path.join(__dirname, "..", "..", "Lado Bursatil", "99_generadores_documentacion");
// docx se resuelve igual que desde comun.js: si se cargara por ruta directa saldría otra copia del
// paquete y los párrafos de comun.js se descartarían en silencio (instanceof distinto).
const requireComun = require("module").createRequire(path.join(BURSATIL_GEN, "comun.js"));
const { Packer, Document, Paragraph, TextRun, AlignmentType, BorderStyle, Header, Footer, PageNumber } = requireComun("docx");
const { h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv } = require(path.join(BURSATIL_GEN, "comun"));

const CARPETA = path.join(__dirname, "..", "00_pipeline_union");
const diag = Object.fromEntries(leerCsv(path.join(CARPETA, "diagnostico_resumen.csv")).map(r => [r.metrica, r]));
const cob = leerCsv(path.join(CARPETA, "cobertura_por_ticker.csv"));

const n = k => Number(diag[k].valor);
const det = k => diag[k].detalle;
const miles = x => Math.round(x).toLocaleString("es-AR");
const coma = (x, d = 1) => Number(x).toFixed(d).replace(".", ",");
const fecha = s => s.slice(0, 10).split("-").reverse().join("/");
const [ventIni, ventFin] = det("ruedas_ventana_comun").split(" a ");
const corte = det("tickers_con_var_propio").match(/\d+/)[0];
const conVar = cob.filter(r => r.var_propio === "True");
const azar = k => det(k).replace("azar: ", "").replace(".", ",");

const GRIS = "5C6B7A";
function bullet(runs) { return p(Array.isArray(runs) ? [plain("•  "), ...runs] : [plain("•  " + runs)], { indent: { left: 360, hanging: 240 } }); }
function nota(texto) { return p([new TextRun({ text: texto, size: 18, color: GRIS, italics: true })]); }

// Un paso del pipeline: qué, por qué, entra, sale, quién, cuándo está terminado.
function paso(id, titulo, quien, depende, que, porque, entra, sale, terminado) {
  return [
    new Paragraph({ keepNext: true, spacing: { before: 280, after: 100 },
      children: [new TextRun({ text: `${id} · ${titulo}`, bold: true, size: 25, font: "Cambria", color: "6A4C93" }),
        new TextRun({ text: `   (${quien} · depende de: ${depende})`, size: 18, color: GRIS })] }),
    p([bold("Qué se hace. "), plain(que)]),
    p([bold("Por qué. "), plain(porque)]),
    p([bold("Entra. "), ...entra]),
    p([bold("Sale. "), ...sale]),
    p([bold("Está terminado cuando "), plain(terminado)]),
  ];
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 21 } } },
    paragraphStyles: [{ id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { font: "Cambria", size: 30, bold: true, color: "12263A" },
      paragraph: { spacing: { before: 360, after: 160 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "40798C", space: 4 } } } }],
  },
  sections: [{
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1134, bottom: 1134, left: 1134, right: 1134 } } },
    headers: { default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
      children: [new TextRun({ text: "Pipeline de la unión — tesis version 3.0", size: 16, color: GRIS })] })] }) },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, children: [
      new TextRun({ text: "Nicolás Diddi · Gino Frigoni · Página ", size: 16, color: GRIS }),
      new TextRun({ children: [PageNumber.CURRENT], size: 16, color: GRIS }),
      new TextRun({ text: " de ", size: 16, color: GRIS }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], size: 16, color: GRIS })] })] }) },
    children: [
      new Paragraph({ children: [new TextRun({ text: "Pipeline de la unión", bold: true, size: 44, font: "Cambria", color: "12263A" })], spacing: { after: 80 } }),
      new Paragraph({ children: [new TextRun({ text: "Los pasos para unir el lado bursátil con el lado de noticias y cerrar los archivos finales", size: 24, font: "Cambria", color: "1C3A5C", italics: true })], spacing: { after: 200 } }),
      new Paragraph({ spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: "D9E0E7", space: 8 } },
        children: [new TextRun({ text: "Tesina — Impacto de shocks informativos en acciones argentinas (BYMA / S&P Merval). " +
          "Documento de la unión: lee los dos lados y no modifica ninguno. Versión del 23/10/2026, con el lado de noticias actualizado al 18/10.", size: 19, color: GRIS })] }),
      p([bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\00_pipeline_union\\"),
        plain(". Los números salen de "), code("diagnostico_union.py"), plain(", que solo lee "), code("Lado Bursatil"),
        plain(" y "), code("Lado Noticias"), plain(".")]),
      refBox("En una frase", [
        "Los dos lados están completos. Para unirlos hay que mandar cada noticia a la rueda en la que el mercado pudo reaccionar, " +
        "armar dos tablas (mercado y empresas) y sobre ellas correr el VAR, Granger y el event study. Antes de armar las series " +
        "las decisiones previas (D1 a D3) ya están tomadas: el sentimiento queda congelado y se analizan precio y volumen.",
      ]),
      figure(path.join(CARPETA, "pipeline_union.png"), 560),

      h1("1. Dónde está cada lado"),
      p([bold("Lado bursátil (Nicolás): cerrado el 17/10. "), plain(
        "Carpetas 00 a 06 con su script, sus CSV y su PDF: precios y volumen de 47 acciones, clustering, VIX argentino, ADF, volatilidad y régimen de mercado (HMM). " +
        "No hay cambios desde la versión anterior de este documento.")]),
      p([bold("Lado de noticias (Gino): actualizado el 18/10. "), plain("Los cambios que importan para la unión:")]),
      simpleTable(["Qué cambió", "Efecto en la unión"], [
        ["Trajo a la carpeta el sentimiento por oración (beto_oraciones_finetuned.csv), el etiquetado de Gemma, los datos de entrenamiento y el modelo de partida, cada uno con su hash", "Ya está todo lo necesario para U3, sin leer nada fuera de esta carpeta"],
        ["Limpió el etiquetado (750 filas de relleno o repetidas) y midió de nuevo la calidad del modelo con una división por noticia", "La calidad que se informa es F1 0,685 (4 clases) y 0,724 contra 0,546 del modelo de referencia (3 clases)"],
        ["La serie diaria ahora se arma desde el sentimiento por oración y sin las frases de relleno", `${n("shocks_serie_actual")} shocks en lugar de 33; la serie anterior y la nueva tienen correlación 0,996`],
        ["Unificó indicadores sinónimos del NER (ccl y contado con liquidación, pib y pbi, etc.)", "El sentimiento por indicador queda sin dobles conteos"],
        ["Documentó el hueco de iProfesional en abril de 2026 y las horas en UTC", "Las dos cosas se resuelven del lado de la unión (U1, U4 y U8)"],
        ["Dejó escrito que la regla de shocks incluye el propio día y que la unión la redefine", "La regla de shocks se elige en U2"],
        ["Dejó pendiente reentrenar el modelo que clasificó el corpus con los datos limpios (su plan de mejora, pasos 2 y 5)", "Decidido en D1: no se reentrena, se congela la versión actual"],
      ], [55, 45]),
      nota("El lado de noticias lleva su propio registro: cada archivo traído desde afuera figura en su README con su origen y su hash."),

      h1("2. Lo que ya está decidido"),
      simpleTable(["Decisión", "Qué se decidió"], [
        ["Ventana", `${fecha(ventIni)} → ${fecha(ventFin)} (${n("ruedas_ventana_comun")} ruedas). Las carpetas de cada lado no cambian sus fechas: la unión usa ese tramo.`],
        ["Regla de cierre", "Una nota publicada a las 17:00 o después, o en un día sin mercado, cuenta para la rueda siguiente."],
        ["Régimen (HMM)", "Se usa tal como está en la carpeta 06, sin reentrenar. La unión toma las filas desde mayo de 2025."],
        ["Moderado", `Tiene ${n("dias_moderado_ventana_comun")} días en la ventana común. El VAR por régimen compara Calmo vs. Tenso; "No calmo" (Moderado + Tenso) va como robustez.`],
        ["Sentimiento propio por empresa", `Solo para las ${conVar.length} acciones con al menos ${corte} ruedas con noticias. Las demás usan el sentimiento general.`],
        ["Dólares CCL", "No se hace. Queda como idea a futuro y como limitación."],
        ["Regla de shocks", "La banda se calcula sin el día evaluado (acordado con Gino). La ventana y el umbral se eligen en U2, comparando contra el azar."],
        ["D1 · Modelo de sentimiento (24/10)", "Se congela: los datos actuales del lado de noticias son los finales y no se reentrena. La tesis aclara que el modelo en uso se entrenó con la división original."],
        ["D2 · Variables del plan (24/10)", "Se suman el volumen operado (volumen anormal), la cantidad de notas por rueda y si hubo noticia de cada empresa, como pide el plan de tesis."],
        ["D3 · Twitter, DLM y HMM por sector (24/10)", "Twitter queda documentado pero no se usa. El DLM queda como trabajo futuro (el VAR ya trabaja con rezagos). El HMM por sector y por acción de la versión anterior no se rehace."],
      ], [26, 74]),

      h1("3. Qué implican las decisiones D1 a D3"),
      p([bold("D1 · Sentimiento congelado. "), plain(
        "La unión usa beto_oraciones_finetuned.csv y finetuned_articulos.csv tal como están hoy en Lado Noticias. U2 y U3 ya no esperan nada. " +
        "En la tesis se declara que la calidad informada (F1 0,685) se midió reentrenando con datos limpios, mientras que el modelo que clasificó el corpus es el original.")]),
      p([bold("D2 · Precio y volumen, sentimiento y atención. "), plain(
        "No suma datos ni reentrena: usa columnas que ya existen. El volumen anormal sale del volumen de la carpeta 01; la cantidad de notas, de contar las notas de cada rueda (U1); " +
        "la marca de noticia por empresa, del NER (U3). Entran como variables en U4, U6 y U7, y así la tesis cubre el objetivo general (precio y volumen) y el objetivo 4 (volumetría, sentimiento y entidades).")]),
      p([bold("D3 · Fuera del análisis. "), plain(
        "Los trending topics de X/Twitter quedan documentados como fuente prevista pero no utilizada; el plan de trabajo se ajusta en U9. El DLM pasa a trabajo futuro. " +
        "El HMM por sector y por acción no se rehace: tenía el régimen atado al VIX del mercado, y la pregunta queda cubierta por el VAR por sector (U6) y la volatilidad propia (carpeta 05).")]),

      h1("4. Lo que mostró el cruce de los datos"),
      p([bold("Ventana. "), plain(`Hay ${n("articulos_ene_abr_2025")} notas entre enero y abril de 2025; la unión arranca el ${fecha(ventIni)}.`)]),
      p([bold("Calendario. "), plain(`De los ${n("shocks_serie_actual")} shocks de la serie de noticias, ${n("shocks_en_dia_sin_mercado")} caen en días sin mercado.`)]),
      p([bold("Horario. "), plain(
        `El ${coma(n("pct_publicadas_tras_cierre"))}% de las notas sale a las 17:00 o después. Con la regla de la rueda, el ${coma(n("pct_cambian_de_dia_al_alinear"))}% ` +
        `cambia de día y todas las ruedas tienen noticias (mínimo ${n("articulos_por_rueda_min")}, mediana ${n("articulos_por_rueda_mediana")}). ` +
        `${n("articulos_fecha_cambia_por_huso")} notas quedaban con el día siguiente por la hora en UTC.`)]),
      p([bold("Horas sospechosas. "), plain(
        `El ${coma(n("pct_hora_por_defecto"))}% de las notas (${miles(n("articulos_hora_por_defecto"))}) tiene una hora repetida que no puede ser la real ` +
        `(una misma hora junta más del 3% de las notas de su portal): Clarín a las 07:00 o 07:08, Ámbito a las 00:00, TN a las 05:55, entre otras. ` +
        "La regla de las 17:00 las manda al mismo día; si en realidad salieron de noche, corresponden al día siguiente. Se marcan en U1 y se prueba sin ellas en U8.")]),
      p([bold("Portales. "), plain(
        `El sentimiento medio por portal va de ${coma(n("sent_neto_medio_fuente_min"))} a +${coma(n("sent_neto_medio_fuente_max"))}, ` +
        `e iProfesional pasa de ${n("iprofesional_mar_2026")} notas en marzo de 2026 a ${n("iprofesional_abr_2026")} en abril. Por eso hay una versión ajustada por portal.`)]),
      p([bold("Empresas y régimen. "), plain(
        `${conVar.length} acciones tienen sentimiento propio suficiente; ${n("tickers_sin_ninguna_mencion")} no tienen ninguna mención. ` +
        `En la ventana común hay ${n("dias_calmo_ventana_comun")} días Calmo, ${n("dias_moderado_ventana_comun")} Moderado y ${n("dias_tenso_ventana_comun")} Tenso.`)]),
      p([bold("Shocks contra el azar. "), plain(
        "Se armó la serie por rueda y se contó cuántas ruedas marca cada regla como shock, contra lo que marcaría una serie de números al azar:")]),
      simpleTable(["Regla", "Serie por rueda", "Puro azar"], [
        ["La de Gino (7 días, incluye el día, 1,5σ)", `${coma(n("shocks_rueda_regla_gino_pct"))}%`, `${azar("shocks_rueda_regla_gino_pct")}`],
        ["7 días previos, 2σ", `${coma(n("shocks_rueda_sin_dia_7d_2s_pct"))}%`, `${azar("shocks_rueda_sin_dia_7d_2s_pct")}`],
        ["20 días previos, 2σ", `${coma(n("shocks_rueda_sin_dia_20d_2s_pct"))}%`, `${azar("shocks_rueda_sin_dia_20d_2s_pct")}`],
      ], [56, 22, 22]),
      p([plain("Con cualquier regla la proporción es casi la del azar: definir \"shock\" mirando solo los días previos no separa bien un evento de una fluctuación. " +
        "Esto afecta solo al event study (U7). El VAR y Granger (U6) usan la serie completa de sentimiento y no dependen de esta definición. " +
        "En U2 se prueban reglas alternativas (por ejemplo, medir cuánto se aparta el día teniendo en cuenta cuántas notas tiene) y se elige la que más se distinga del azar.")]),

      h1("5. El pipeline, paso a paso"),
      p("Cada paso tiene su carpeta dentro de Unión, con su script, sus CSV y su PDF, igual que los dos lados. Ningún paso modifica Lado Bursatil ni Lado Noticias. " +
        "Se avanza de a un paso: se corre, se revisa el resultado y recién ahí se sigue."),

      ...paso("U1", "Cada noticia a su rueda", "Unión", "nada (se puede hacer ya)",
        `Pasar la hora de publicación de las ${miles(n("articulos_corpus"))} notas a hora argentina y asignar cada una a una rueda: la del mismo día si salió antes de las 17:00, ` +
        "y la siguiente si salió después o en un día sin mercado. Marcar las notas con hora sospechosa.",
        "La noticia cuenta desde el primer momento en que alguien pudo operar con ella. Sin esto, una nota del viernes a la noche se compara con un precio que se formó antes.",
        [code("noticias/resultados/*.jsonl"), plain(" (Gino) y el calendario de "), code("03_vix_argentino/vix_arg.csv"), plain(" (Nicolás).")],
        [code("01_alineacion_noticias_ruedas/nota_a_rueda.csv"), plain(": url, portal, hora argentina, rueda, hora sospechosa.")],
        "cada nota del corpus tiene una rueda o un motivo para no tenerla, y el conteo por rueda coincide con el diagnóstico."),

      ...paso("U2", "Series de mercado por rueda", "Unión", "U1",
        "Para cada rueda: sentimiento promedio (simple y ajustado por portal), cantidad de notas y porcentaje de notas de cada portal. Después, elegir la regla de shocks: " +
        "probar varias (ventana, umbral, ajuste por cantidad de notas), compararlas contra el azar y quedarse con la que más se distinga.",
        "Es la variable de noticias del análisis de mercado. La regla de shocks se justifica con datos, no se elige a ojo.",
        [code("sentimiento_finbert/finetuned_articulos.csv"), plain(" (versión congelada) y "), code("nota_a_rueda.csv"), plain(".")],
        [code("02_sentimiento_por_rueda/sentimiento_mercado_rueda.csv"), plain(", "), code("shocks_rueda.csv"), plain(" y la tabla de reglas probadas.")],
        `la serie tiene las ${n("ruedas_ventana_comun")} ruedas, y la regla elegida y su comparación con el azar quedan documentadas.`),

      ...paso("U3", "Sentimiento por empresa e indicador por rueda", "Unión", "U1",
        "Rehacer el cruce entidad × oración de Gino agrupando por rueda en lugar de por fecha, con sus mismas equivalencias de indicadores. " +
        "Una rueda sin noticias de una empresa queda vacía, con la marca hubo_noticia = 0, y no con sentimiento 0.",
        "Sentimiento 0 quiere decir tono neutro; no tener noticias es otra cosa. Mezclarlos haría parecer neutras a las empresas de las que nadie habla.",
        [code("ner_entidades/resultados_ner/ner_oraciones.csv"), plain(", "), code("beto_oraciones_finetuned.csv"), plain(", "), code("equivalencias_indicadores.py"), plain(" y "), code("nota_a_rueda.csv"), plain(".")],
        [code("03_sentimiento_por_empresa/sentimiento_entidad_rueda.csv"), plain(" (rueda × empresa o indicador) y la cobertura exacta por empresa.")],
        `con fecha calendario reproduce los totales de ner_sentimiento_diario.csv de Gino, y la cobertura confirma (o corrige) las ${conVar.length} empresas con sentimiento propio.`),

      ...paso("U4", "Datasets unificados", "Unión", "U2 y U3",
        `Dos tablas. Mercado: una fila por rueda (${n("ruedas_ventana_comun")}) con retorno del Merval, VIX, régimen suavizado y filtrado, volumen total, ` +
        "sentimiento (simple y por portal), cantidad de notas y shocks. Panel: una fila por acción y rueda (47 × 244) con retorno, volumen anormal, sentimiento propio y " +
        "hubo_noticia, sentimiento de mercado, sector, grupo de liquidez y régimen. Las dos con marcas de días especiales: elecciones (08/09/2025 y 27/10/2025), " +
        "eco de 20 ruedas de esos saltos y abril de 2026 (hueco de iProfesional).",
        "Son los únicos insumos de los modelos. Con todo en dos archivos, ningún script arma su propio cruce.",
        [plain("U2, U3 y las carpetas 01, 02, 03 y 06 del lado bursátil.")],
        [code("04_dataset_unificado/dataset_mercado.csv"), plain(", "), code("dataset_panel.csv"), plain(" y un diccionario de variables.")],
        "no se pierde ninguna rueda ni ninguna acción, y cada columna está en el diccionario con su origen."),

      ...paso("U5", "Estacionariedad en la ventana común", "Unión", "U4",
        "ADF sobre cada serie que entra a los modelos (retornos, volumen anormal, sentimiento, cantidad de notas), en las 244 ruedas, con constante.",
        "El VAR exige series estables en el tramo exacto que usa. El ADF de la carpeta 04 justificó usar retornos con 3 años de datos; este confirma el tramo de la unión.",
        [code("dataset_mercado.csv"), plain(" y "), code("dataset_panel.csv"), plain(".")],
        [code("05_adf_union/resultados_adf_union.csv"), plain(".")],
        "cada serie tiene su resultado y las que no son estables tienen su transformación decidida."),

      ...paso("U6", "VAR, Granger e impulso-respuesta", "Unión", "U5",
        "Siempre en las dos direcciones (noticias → mercado y mercado → noticias) y para retorno y volumen: mercado; cada una de las 47 acciones con el sentimiento general " +
        `y las ${conVar.length} con su sentimiento propio; por régimen (Calmo vs. Tenso); y por sector. Rezagos elegidos por AIC/BIC y corrección por pruebas múltiples (Benjamini-Hochberg).`,
        "Es el núcleo de la tesis (objetivo 6). Con decenas de tests, sin corrección aparecen resultados \"significativos\" por azar.",
        [code("dataset_mercado.csv"), plain(", "), code("dataset_panel.csv"), plain(" y "), code("resultados_adf_union.csv"), plain(".")],
        [code("06_var_granger/"), plain(": p-valores sin corregir y corregidos, rezagos e IRF.")],
        "cada test tiene su p-valor corregido y cada resultado se puede rastrear a su modelo."),

      ...paso("U7", "Event study", "Unión", "U4 (y la regla de shocks de U2)",
        "Con los shocks de U2, uniendo los que estén pegados, estimar para cada acción el modelo de mercado en [−25, −4] y medir el retorno y el volumen anormal " +
        "acumulados en [−3, +5]. Test t y test de signo, separando shocks positivos y negativos y dejando aparte los días electorales.",
        "Mide qué pasa con precio y volumen alrededor de los días de noticias extremas. Con pocos eventos, el test de signo es más confiable que el t.",
        [code("dataset_panel.csv"), plain(" y "), code("shocks_rueda.csv"), plain(".")],
        [code("07_event_study/"), plain(": CAR por evento, por tipo de shock y por acción.")],
        "cada evento tiene su ventana completa o un motivo de exclusión documentado."),

      ...paso("U8", "Robustez", "Unión", "U6 y U7",
        "Repetir los resultados principales cambiando una cosa por vez: sentimiento ajustado por portal, régimen filtrado, Calmo vs. No calmo, sin las 4 acciones menos " +
        "líquidas (GCDI, RIGO, GRIM y GARO), sin notas con hora sospechosa, sin abril de 2026 y con fecha calendario en lugar de la regla de las 17:00.",
        "Un resultado que aparece con una sola opción es frágil; uno que aparece con todas se puede defender.",
        [plain("U6, U7 y los datasets de U4.")],
        [code("08_robustez/"), plain(": una tabla que compara cada variante con el resultado base.")],
        "cada resultado principal tiene su fila de robustez."),

      ...paso("U9", "Entrega final", "Nicolás + Gino", "todo lo anterior",
        "Un PDF por paso (mismo formato que los dos lados), el mapa completo de la tesis (lado bursátil, lado de noticias y unión), el diccionario de variables, " +
        "el plan de trabajo actualizado (objetivos según lo hecho y el apellido corregido), la bibliografía unificada de los dos lados y la presentación con los resultados nuevos.",
        "Es lo que va a la tesina y lo que se defiende frente al jurado.",
        [plain("todo lo anterior, los PDF de cada lado y los papers de noticias y bolsa del inventario (grupo K).")],
        [code("09_entrega_final/"), plain(".")],
        "cada archivo final lee sus números de los CSV, sin valores escritos a mano."),

      h1("6. Cómo queda la carpeta Unión"),
      simpleTable(["Carpeta", "Contenido"], [
        [[code("00_pipeline_union")], "Este documento, el diagnóstico, el inventario de archivos y los mensajes para Gino"],
        [[code("01_alineacion_noticias_ruedas")], "U1"],
        [[code("02_sentimiento_por_rueda")], "U2"],
        [[code("03_sentimiento_por_empresa")], "U3"],
        [[code("04_dataset_unificado")], "U4 y el diccionario de variables"],
        [[code("05_adf_union")], "U5"],
        [[code("06_var_granger")], "U6"],
        [[code("06b_noticias_preapertura")], "U6b: notas publicadas con el mercado cerrado → apertura"],
        [[code("07_event_study")], "U7"],
        [[code("07b_shock_volumen_noticias")], "U7b: event study del shock de cantidad de noticias (definición del plan)"],
        [[code("08_robustez")], "U8"],
        [[code("09_entrega_final")], "U9: mapa completo, plan actualizado, bibliografía, presentación"],
        [[code("10_papers_union")], "Papers relacionados con cada prueba de la unión"],
        [[code("11_papers_lado_noticias")], "Papers relacionados con el lado de noticias"],
        [[code("99_generadores_documentacion")], "Los generadores de los PDF de la unión"],
      ], [36, 64]),
      nota("Para la entrega conviene que la carpeta raíz tenga un solo nombre. El nombre queda pendiente de acordar con Gino."),

      h1("7. Orden de trabajo"),
      simpleTable(["Paso", "Depende de", "Se puede empezar"], [
        ["U1", "—", "Ya"],
        ["U2, U3", "U1", "Después de U1"],
        ["U4", "U2 y U3", "Después de U2 y U3"],
        ["U5 → U6", "U4", "Después de U4"],
        ["U7", "U4 y la regla de U2", "Después de U4, en paralelo con U5 y U6"],
        ["U8", "U6 y U7", "Al final"],
        ["U9", "Todo", "Al final (el mapa y el plan se pueden ir armando antes)"],
      ], [18, 40, 42]),

      h1("8. Cuidados que vienen de cada lado"),
      bullet([bold("Liquidez. "), plain("GCDI, RIGO, GRIM y GARO tienen muchos días sin operar: su precio se repite y pueden parecer lentas para reaccionar.")]),
      bullet([bold("Eco de 20 días. "), plain("El VIX y el régimen arrastran los saltos del 08/09/2025 y del 27/10/2025 durante 20 ruedas.")]),
      bullet([bold("Elecciones. "), plain("Los dos días electorales son a la vez shocks de noticias y los mayores saltos del mercado: se analizan aparte para no atribuírselos al sentimiento.")]),
      bullet([bold("Pesos nominales. "), plain("Los retornos incluyen inflación y tipo de cambio; la versión en dólares queda como trabajo futuro.")]),
      bullet([bold("Etiquetas de Gemma. "), plain("El sentimiento se apoya en etiquetas de un modelo, sin validación humana: es una limitación que la unión hereda y que la tesis declara.")]),
      bullet([bold("Tono del contexto. "), plain("El sentimiento por empresa es el de las oraciones que la mencionan, no una opinión sobre la empresa.")]),
    ],
  }],
});

Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_Pipeline_Union.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
