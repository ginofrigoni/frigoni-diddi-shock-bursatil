// Genera Documentacion_Entrega_Final.docx dentro de ../09_entrega_final/
// Uso:  node build_doc_final.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, miles, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "09_entrega_final");
const n = Object.fromEntries(leerCsv(path.join(CARPETA, "resumen_mapa_tesis.csv")).map(x => [x.metrica, x.valor]));
const N = k => Number(n[k]);
const g6 = leerCsv(path.join(u.RAIZ_UNION, "06_var_granger", "granger_resultados.csv"));
const mer = pr => g6.find(x => x.nivel === "mercado" && x.prueba === pr);
const pv = x => Number(x) < 0.0001 ? "< 0,0001" : coma(x, 4);
const sig = x => x.signif_bh === "True" ? "Sí" : "No";

const doc = u.documentoUnion({
  titulo: "Entrega final: resultados de la tesis",
  subtitulo: "Impacto de shocks informativos en el comportamiento bursátil de empresas argentinas",
  encabezado: "Entrega final — tesis version 3.0",
  ubicacion: [bold("Autores. "), plain("Gino Frigoni (lado de noticias) y Nicolás Diddi (lado bursátil). "), bold("Ubicación. "),
    code("D:\\2.Tesina\\tesis version 3.0\\Unión\\09_entrega_final\\"), plain(".")],
  children: [
    refBox("La tesis en un párrafo", [
      "Se estudió si las noticias económicas de los medios digitales argentinos anticipan el precio y el volumen de las acciones de BYMA. " +
      `Se unieron ${miles(N("notas_corpus"))} notas de 7 portales, clasificadas con un modelo de sentimiento propio, con ${N("acciones")} acciones durante ${N("ruedas_union")} ruedas ` +
      "(mayo de 2025 a abril de 2026). La respuesta es que no: lo que aparece es lo contrario. Los medios siguen al mercado: en las notas de la misma noche, después del cierre, " +
      "cuentan la suba o la baja con un tono que la acompaña, para el mercado y para cada empresa. Ni el tono ni la cantidad de noticias anticipan los precios o el volumen, " +
      "ni siquiera con las notas publicadas antes de la apertura. Con la definición de shock del plan (muchas más notas que lo habitual), lo único que aparece es que " +
      "la acción de la empresa se opera más ese mismo día, sin una dirección en el precio. Los hechos grandes, como las elecciones o el anuncio del Tesoro de " +
      "Estados Unidos, se reflejan de inmediato en el precio.",
    ]),
    figure(path.join(CARPETA, "mapa_tesis.png"), 600),

    h1("1. Los resultados principales"),
    simpleTable(["Pregunta", "Prueba", "Resultado", "Dónde"], [
      ["¿El tono de las noticias anticipa al mercado?", "VAR y Granger (mercado, 47 empresas, 17 con tono propio, 10 sectores, régimen)",
        `No. ${N("noticias_mercado_sig")} de ${N("noticias_mercado_tests")} pruebas significativas, lo esperable por azar`, "U6"],
      ["¿Y con las notas publicadas antes de la apertura?", "Tono de la noche → salto de apertura, regla fijada de antemano",
        `No (p = ${coma(N("p_preapertura"), 3)}); solo las elecciones mueven la apertura`, "U6b"],
      ["¿La cantidad de noticias (atención) anticipa al mercado?", "Atención anormal → retorno y volumen",
        `No (p = ${pv(mer("atención → retorno").p)} y ${pv(mer("atención → volumen").p)})`, "U6"],
      ["¿El mercado anticipa al tono de las noticias?", "Retorno → tono",
        `Sí (p ${pv(N("p_retorno_tono"))}), en ${N("empresas_retorno_tono")} de 47 empresas y ${N("propio_retorno_tono")} de 17 con tono propio`, "U6"],
      ["¿Cuándo?", "Tono según la franja de publicación de las notas",
        `En las notas de la misma noche, post-cierre (+${coma(N("efecto_noche"))} puntos por desvío del retorno); a la mañana ya no queda`, "U8"],
      ["¿Qué hace el precio en las ruedas de tono extremo?", "Event study del Merval y de cada empresa",
        `Sube ${coma(N("car_dia0_positivos"), 2)}% el mismo día y venía subiendo antes; después nada`, "U7"],
      ["¿Y en los shocks de cantidad de noticias, como los define el plan?", "Event study de los días con muchas más notas que lo habitual (z > 2 contra 30 ruedas), regla fijada de antemano",
        `En las empresas (${N("eventos_cantidad_empresa")} shocks) se opera más ese día (p corregido ${coma(N("p_bh_vol_cantidad"), 3)}); ` +
        `el precio no se mueve en una dirección y la apertura no se anticipa (p corregido ${coma(N("p_bh_salto_cantidad"), 3)}). En el mercado, nada`, "U7b"],
      ["¿Es robusto?", "12 variantes, una decisión por vez", `${N("robustez_mantienen")} de ${N("robustez_total")} comparaciones mantienen la conclusión`, "U8"],
    ], [24, 30, 36, 10]),

    h1("2. Cómo se cumplió cada objetivo del plan de tesis"),
    simpleTable(["Objetivo del plan", "Qué se hizo", "Estado"], [
      ["General: modelar el impacto de los shocks informativos sobre el precio y el volumen de transacciones",
        "VAR, Granger, event study y la prueba de notas pre-apertura, siempre para retorno y para volumen (U6, U6b, U7)", "Cumplido"],
      ["1. Corpus de noticias de economía y finanzas, como serie temporal por portal y fecha",
        `${miles(N("notas_corpus"))} notas de 7 portales, depuradas; asignadas a ruedas con la regla de las 17:00 (lado de noticias y U1)`, "Cumplido"],
      ["2. Modelo de sentimiento financiero en español (BETO ajustado)",
        `FinBETO, 4 clases; F1 ${coma(N("f1_noticias_no_vistas"), 3)} en notas no vistas, por encima del modelo de referencia (lado de noticias)`, "Cumplido"],
      ["3. Trending topics de X/Twitter como variable complementaria", "Los datos no están en ninguna versión del proyecto; se documenta y queda como trabajo futuro", "No realizado"],
      ["4. Variables de shock: volumetría de publicaciones, temperatura del sentimiento y presencia de entidades",
        "Atención anormal (cantidad de notas), tono anormal, ruedas de tono extremo y tono propio de cada empresa con hubo_noticia (U2, U3, U4); " +
        "el shock de cantidad con la definición del plan, por día de calendario (U7b)", "Cumplido"],
      ["5. Clusters de empresas por sector y sensibilidad al flujo informativo",
        "Clustering de las 47 (grupo de baja liquidez, carpeta 02) y VAR por sector y por empresa (U6)", "Cumplido"],
      ["6. Modelar la relación con desfases temporales", "VAR con rezagos elegidos por AIC (U6). El modelo DLM del plan queda como trabajo futuro: el VAR ya mide efectos con rezagos", "Cumplido (con VAR)"],
    ], [38, 48, 14]),
    nota("El plan de trabajo original figura con el apellido \"Didi\"; el correcto es Diddi."),

    h1("3. Las decisiones que sostienen los resultados"),
    simpleTable(["Decisión", "Qué se decidió y por qué"], [
      ["Ventana", `${N("ruedas_union")} ruedas, del 05/05/2025 al 30/04/2026: antes de mayo de 2025 casi no hay notas`],
      ["Regla de las 17:00", "Una nota cuenta para la primera rueda en que el mercado pudo reaccionar a ella (U1)"],
      ["Sentimiento congelado", "Se usó la clasificación del lado de noticias tal como está, sin reentrenar"],
      ["Precio y volumen", "Se analizaron los dos, con volumen anormal comparado con las 20 ruedas previas (D2)"],
      ["Tono anormal", "El tono en nivel dio inconcluso en el test de estacionariedad; el VAR usa el tono comparado con las 20 ruedas previas (U5)"],
      ["Tono propio", "Cuánto mejor o peor se habla de la empresa que del mercado, ponderado por la cantidad de oraciones; 0 sin noticias (U6)"],
      ["Régimen", "HMM tal como está; el VAR por régimen compara Calmo y Tenso con una marca de día Tenso, sin cortar la serie"],
      ["Ruedas de tono extremo", "Regla por muestreo elegida contra el azar; se interpretan como las ruedas más extremas, no como días excepcionales (U2)"],
      ["Corrección por pruebas múltiples", "Benjamini-Hochberg en todas las familias de pruebas"],
    ], [24, 76]),

    h1("4. Limitaciones"),
    bullet("Un año de datos: un efecto chico de las noticias sobre los precios podría existir y no detectarse."),
    bullet("Las etiquetas del modelo de sentimiento las generó un modelo (Gemma), sin validación humana."),
    bullet("Los retornos están en pesos nominales: incluyen inflación y tipo de cambio."),
    bullet("Con datos diarios no se puede ordenar lo que pasa dentro de una misma rueda; la prueba pre-apertura (U6b) es la aproximación más cercana."),
    bullet("La hora de publicación es la que informa cada portal; el 13% de las notas tiene horas de relleno, y los resultados se repitieron sin ellas."),

    h1("5. Trabajo futuro"),
    bullet("Repetir el análisis en dólares (contado con liquidación)."),
    bullet("Incorporar trending topics de redes sociales y un modelo de rezagos distribuidos (DLM), como preveía el plan."),
    bullet("Validar con personas una muestra de las etiquetas de sentimiento."),
    bullet("Usar precios intradiarios para ordenar noticias y precios dentro de la rueda."),

    h1("6. Documentos de la tesis"),
    simpleTable(["Parte", "Documento (PDF)", "Carpeta"], [
      ["Lado bursátil", "Mapa del lado bursátil y documentación de cada carpeta (01 a 06)", "Lado Bursatil/00 a 06"],
      ["Lado de noticias", "README y SECCION_TESIS de noticias, sentimiento y NER", "Lado Noticias/"],
      ["Unión", "Pipeline de la unión", "Unión/00_pipeline_union"],
      ["Unión", "U1 · Cada noticia a su rueda", "Unión/01_alineacion_noticias_ruedas"],
      ["Unión", "U2 · Sentimiento de mercado por rueda", "Unión/02_sentimiento_por_rueda"],
      ["Unión", "U3 · Sentimiento por empresa por rueda", "Unión/03_sentimiento_por_empresa"],
      ["Unión", "U4 · Datasets unificados (con el diccionario de variables)", "Unión/04_dataset_unificado"],
      ["Unión", "U5 · Estacionariedad", "Unión/05_adf_union"],
      ["Unión", "U6 · VAR, Granger e impulso-respuesta", "Unión/06_var_granger"],
      ["Unión", "U6b · Noticias publicadas con el mercado cerrado", "Unión/06b_noticias_preapertura"],
      ["Unión", "U7 · Event study", "Unión/07_event_study"],
      ["Unión", "U7b · Shock de cantidad de noticias (definición del plan)", "Unión/07b_shock_volumen_noticias"],
      ["Unión", "U8 · Robustez", "Unión/08_robustez"],
      ["Unión", "Este documento, el mapa de la tesis y el plan de trabajo actualizado", "Unión/09_entrega_final"],
      ["Bibliografía", "Papers de cada prueba de la unión, con sus referencias", "Unión/10_papers_union"],
      ["Bibliografía", "Papers del lado de noticias (corpus, sentimiento y NER), con sus referencias", "Unión/11_papers_lado_noticias"],
    ], [18, 52, 30]),
    p([bold("Reproducibilidad. "), plain(`Toda la unión se rehace con un solo comando, `), code("python correr_todo.py"),
      plain(` desde 09_entrega_final: corre los pasos en orden, ${N("archivos_identicos")} de ${N("archivos_total")} archivos de resultados salen idénticos y ` +
        `${N("controles_ok")} de ${N("controles_total")} controles automáticos pasan.`)]),

    h1("7. Referencias metodológicas"),
    ...[
      "Benjamini, Y. y Hochberg, Y. (1995). Controlling the false discovery rate: a practical and powerful approach to multiple testing. Journal of the Royal Statistical Society, Series B, 57(1), 289–300.",
      "Brown, S. J. y Warner, J. B. (1985). Using daily stock returns: the case of event studies. Journal of Financial Economics, 14(1), 3–31.",
      "Da, Z., Engelberg, J. y Gao, P. (2011). In search of attention. The Journal of Finance, 66(5), 1461–1499.",
      "Dougal, C., Engelberg, J., García, D. y Parsons, C. A. (2012). Journalists and the stock market. The Review of Financial Studies, 25(3), 639–679.",
      "Engelberg, J. E. y Parsons, C. A. (2011). The causal impact of media in financial markets. The Journal of Finance, 66(1), 67–97.",
      "Fang, L. y Peress, J. (2009). Media coverage and the cross-section of stock returns. The Journal of Finance, 64(5), 2023–2052.",
      "Granger, C. W. J. (1969). Investigating causal relations by econometric models and cross-spectral methods. Econometrica, 37(3), 424–438.",
      "Kwiatkowski, D., Phillips, P. C. B., Schmidt, P. y Shin, Y. (1992). Testing the null hypothesis of stationarity against the alternative of a unit root. Journal of Econometrics, 54(1–3), 159–178.",
      "Lütkepohl, H. (2005). New Introduction to Multiple Time Series Analysis. Springer.",
      "MacKinlay, A. C. (1997). Event studies in economics and finance. Journal of Economic Literature, 35(1), 13–39.",
      "Rabiner, L. R. (1989). A tutorial on hidden Markov models and selected applications in speech recognition. Proceedings of the IEEE, 77(2), 257–286.",
      "Shiffler, R. E. (1988). Maximum Z scores and outliers. The American Statistician, 42(1), 79–80.",
      "Sims, C. A. (1980). Macroeconomics and reality. Econometrica, 48(1), 1–48.",
      "Tetlock, P. C. (2007). Giving content to investor sentiment: the role of media in the stock market. The Journal of Finance, 62(3), 1139–1168.",
      "Yang, N., Fernández-Pérez, A. e Indriawan, I. (2024). Spillover between investor sentiment and volatility: the role of social media. International Review of Financial Analysis, 96, 103643.",
    ].map(t => p(t, { indent: { left: 360, hanging: 360 } })),
    nota("Citadas, no descargadas. Rabiner (1989) y Yang et al. (2024) vienen del plan de trabajo: el primero respalda el HMM de regímenes y el segundo, " +
      "el uso de redes sociales que queda como trabajo futuro. La bibliografía completa está en Lado Bursatil/*/papers, Unión/10_papers_union " +
      "y Unión/11_papers_lado_noticias, cada una con su referencias_papers.md y su .bib."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_Entrega_Final.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
