// Genera Documentacion_Clustering_Acciones.docx dentro de ../02_clustering_acciones/
// Uso:  node build_doc_clustering.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const { Packer } = require("docx");
const { RAIZ, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, documento, seccionReferencias } = require("./comun");

const CARPETA = path.join(RAIZ, "02_clustering_acciones");
const resumen = leerCsv(path.join(CARPETA, "resumen_clustering_47.csv"));
const siluetas = leerCsv(path.join(CARPETA, "siluetas_por_k.csv"));
const comparacion = leerCsv(path.join(CARPETA, "comparacion_grupo_no_degenerado.csv"));
const N = new Set(comparacion.map(r => r.label)).size;

const coma = (v, d = 3) => Number(v).toFixed(d).replace(".", ",");
const periodo = s => s === "3 anos" ? "3 años" : "1 año";
const metodo = s => s === "Jerarquico" ? "Jerárquico" : s;

// Una entrada por combinación (análisis × período × método) con los tamaños de sus grupos
const combos = {};
for (const r of resumen) {
  const key = [r.Analisis, r.Periodo, r.Metodo].join("|");
  (combos[key] = combos[key] || { a: r.Analisis, per: r.Periodo, m: r.Metodo, k: r.k_optimo, sil: Number(r.Silueta), grupos: [] })
    .grupos.push({ n: Number(r.N_empresas), emp: r.Empresas });
}
const ranking = Object.values(combos).sort((x, y) => y.sil - x.sil);
const describir = c => {
  const tam = c.grupos.map(g => g.n).sort((a, b) => b - a);
  const lista = tam.length === 2 ? `${tam[0]} y ${tam[1]}` : tam.slice(0, -1).join(", ") + " y " + tam[tam.length - 1];
  if (tam.length === 2 && tam[1] === 1) return `${lista} — degenerado (${c.grupos.find(g => g.n === 1).emp} aislada)`;
  if (tam.length === 2 && tam[1] >= 5) return `${lista} — tamaño real (ver sección 4)`;
  return lista;
};

// El grupo: K-Means y Jerárquico, 13 features, 3 años
const chico = (m) => combos[`13 features|3 anos|${m}`].grupos.reduce((a, b) => (a.n < b.n ? a : b));
const gKM = chico("K-Means"), gJer = chico("Jerarquico");
const kmLista = gKM.emp.split(", "), jerLista = gJer.emp.split(", ");
const soloKM = kmLista.filter(e => !jerLista.includes(e));
const silKM = combos["13 features|3 anos|K-Means"].sil, silJer = combos["13 features|3 anos|Jerarquico"].sil;
const prom = (en) => {
  const filas = comparacion.filter(r => r.en_grupo === en);
  const m = c => filas.reduce((s, r) => s + Number(r[c]), 0) / filas.length;
  return { ret: m("ret_mean") * 100, vol: m("volatilidad") * 100, quieto: m("pct_precio_quieto"),
           sinOperar: m("dias_sin_operar"), volMed: m("volumen_mediano") };
};
const pg = prom("True"), po = prom("False");
const miles = x => Math.round(Number(x)).toLocaleString("es-AR");
const delGrupo = comparacion.filter(r => r.en_grupo === "True")
  .sort((a, b) => Number(b.dias_sin_operar) - Number(a.dias_sin_operar));
const enMitadBaja = delGrupo.filter(r => Number(r.rank_volumen) <= N / 2).length;
const separa = leerCsv(path.join(CARPETA, "features_que_separan_grupo.csv"));
const robustez = leerCsv(path.join(CARPETA, "robustez_grupo_liquidez.csv"));
const rob = Object.fromEntries(robustez.map(r => [r.prueba, r]));
const NOMBRE_FEATURE = {
  corr_merval: "Correlación con el promedio del panel", vol_anormal: "Volumen anormal (irregularidad del volumen)",
  vol_std: "Desvío del volumen", ret_mean: "Retorno medio", kurtosis: "Curtosis (días extremos)", beta: "Beta",
  max_drawdown: "Máxima caída", volatilidad: "Volatilidad", vol_mean: "Volumen medio", skewness: "Asimetría",
  corr_vol_ret: "Correlación volumen-retorno", momentum_20d: "Momentum 20 días", momentum_50d: "Momentum 50 días",
};
const signo = x => (Number(x) >= 0 ? "+" : "−") + coma(Math.abs(Number(x)), 2);

// Rango de K-Means en Precio y Volumen (sin estructura)
const kmPV = siluetas.filter(s => s.Metodo === "K-Means" && s.Analisis !== "13 features").map(s => Number(s.Silueta));
const mst3 = combos["13 features|3 anos|MST"];
const aisladaMST = mst3.grupos.find(g => g.n === 1).emp;

const doc = documento({
  titulo: "Clustering de acciones",
  subtitulo: "¿Existen familias de acciones que se comportan parecido?",
  encabezado: "Clustering de acciones — tesis version 3.0",
  ubicacion: [bold("Ubicación de todo lo generado. "), code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\02_clustering_acciones\\"),
    plain(`. Input: el panel de ${N} acciones de `), code("01_scraping_acciones"), plain(".")],
  children: [
    h1("1. Objetivo"),
    p(`Si existen grupos de acciones que reaccionan de forma parecida entre sí, el impacto de las noticias se podría ` +
      `analizar por familia en vez de acción por acción — más señal, menos ruido, un relato más simple que ${N} series ` +
      `sueltas. Este documento evalúa esa pregunta sobre el panel de ${N} acciones (ver 01_scraping_acciones): K-Means, ` +
      `Jerárquico y MST, sobre 3 representaciones de comportamiento, en 2 ventanas temporales.`),
    refBox("Qué representaciones se usan, y por qué no otras", [
      "Se usan solo representaciones que miden comportamiento (cómo se mueve el precio, cómo varía el volumen) — se " +
      "descartó deliberadamente cualquier representación de nivel \"crudo\" (precio promedio, volumen promedio sin " +
      "normalizar), porque eso agrupa por magnitud — caro contra barato, mucho volumen contra poco — no por " +
      "comportamiento, y no responde la pregunta de la sección anterior.",
    ]),

    h1("2. Metodología aplicada"),
    simpleTable(["Representación", "Qué mide", "Distancia / algoritmo base"], [
      ["Precio", "Retornos logarítmicos diarios, normalizados por empresa", "1 − correlación entre series"],
      ["Volumen", "Log-volumen diario, normalizado por empresa", "1 − correlación entre series"],
      ["13 features", "Retorno medio, volatilidad, asimetría, curtosis, máxima caída, beta y correlación contra el promedio del panel, momentum 20d/50d, volumen medio/desvío, volumen anormal, correlación volumen-retorno", "Distancia euclídea (features estandarizadas)"],
    ], [20, 50, 30]),
    p(""),
    p(`Cada representación se corrió con 3 algoritmos (K-Means, Jerárquico con linkage average/ward, MST) sobre 2 ` +
      `ventanas, probando k de 2 a 8 y quedándose con el k de mayor silueta. En total, 18 combinaciones (3 ` +
      `representaciones × 2 ventanas × 3 algoritmos) sobre las ${N} acciones del panel.`),
    refBox("Las dos ventanas, alineadas con el resto del análisis", [
      [plain("\"3 años\" es el panel completo (2023-05-03 → 2026-05-03, exacto). \"1 año\" no es un recorte arbitrario de " +
        "los últimos 365 días del panel — se toma la ventana de "), code("../03_vix_argentino/vix_arg.csv"),
        plain(" (2025-01-02 → 2026-04-30), la misma que usan VIX, ADF y volatilidad por acción. El retorno se calcula " +
        "sobre la serie completa y recién después se recorta a cada ventana, para no perder el primer día.")],
    ]),
    p(""),
    p([bold("Datos de entrada. "), plain("Los precios ya incluyen las dos correcciones de eventos corporativos de " +
      "01_scraping_acciones (SEMI 16/12/2024 y AGRO hasta el 02/11/2023), que entran de lleno en la ventana de 3 años.")]),

    h1("3. Resultado — casi todo degenerado, y un grupo de tamaño real"),
    p("Ranking de las 10 combinaciones con mejor silueta, y qué tan parejo es el reparto real de empresas:", { keepNext: true }),
    simpleTable(["Análisis", "Período", "Método", "k", "Silueta", "Tamaños de los grupos"],
      ranking.slice(0, 10).map(c => [c.a, periodo(c.per), metodo(c.m), c.k, coma(c.sil), describir(c)]),
      [15, 11, 14, 6, 11, 43]),
    p(""),
    p(`La mejor silueta de todas (${coma(mst3.sil)}, MST) es un caso degenerado: aísla a ${aisladaMST} sola contra las ` +
      `otras ${N - 1}. La mayoría del top 10 tiene esa misma firma — 1 o 2 outliers contra el resto —, salvo dos splits ` +
      `con tamaño real, ambos sobre "13 features" a 3 años: ${N - jerLista.length}/${jerLista.length} con Jerárquico y ` +
      `${N - kmLista.length}/${kmLista.length} con K-Means.`),

    h1(`4. El grupo de ${kmLista.length} — qué lo distingue: sobre todo, la liquidez`),
    p(`13 features, 3 años, K-Means, k=2, silueta ${coma(silKM)} separa ${N - kmLista.length} empresas de un grupo de ` +
      `${kmLista.length}: ${kmLista.join(", ")}. Jerárquico (silueta ${coma(silJer)}) encuentra prácticamente el mismo ` +
      `grupo: coincide en ${jerLista.length} de las ${kmLista.length}, todas menos ${soloKM.join(", ")}.`),
    p("A primera vista el grupo es más volátil y rinde menos que el resto:", { keepNext: true }),
    simpleTable(["Grupo", "Retorno diario promedio", "Volatilidad diaria (desvío)"], [
      [`Las otras ${N - kmLista.length}`, coma(po.ret) + "%", coma(po.vol, 2) + "%"],
      [kmLista.join(", "), coma(pg.ret) + "%", coma(pg.vol, 2) + "%"],
    ], [44, 28, 28]),
    p(""),
    p([bold("Pero lo que más lo separa del resto es la liquidez. "), plain("Ordenando las 13 features según cuánto " +
      "difieren entre el grupo y el resto, las primeras no son la volatilidad sino las huellas de una acción que se opera " +
      "de a ratos: poca correlación con las demás y un volumen irregular.")], { keepNext: true }),
    simpleTable(["Feature", "Diferencia grupo vs. resto (en desvíos estándar)"],
      separa.slice(0, 6).map(r => [NOMBRE_FEATURE[r.feature] || r.feature, signo(r.diferencia_desvios)]), [60, 40]),
    p(""),
    p("La liquidez de cada empresa del grupo, en los 3 años:", { keepNext: true }),
    simpleTable(["Empresa", "Días sin operar", "Días con el precio igual al anterior", "Acciones operadas en un día típico", "Puesto por volumen (1 = el menor)"],
      delGrupo.map(r => [r.label, r.dias_sin_operar, coma(r.pct_precio_quieto, 1) + "%", miles(r.volumen_mediano), `${r.rank_volumen} de ${N}`]),
      [14, 16, 24, 24, 22]),
    p(""),
    p(`En promedio, el precio de una empresa del grupo queda igual al del día anterior en el ${coma(pg.quieto, 1)}% de los ` +
      `días, contra ${coma(po.quieto, 1)}% en el resto del panel; ${enMitadBaja} de las ${kmLista.length} están en la mitad ` +
      `del panel con menos volumen. Las cuatro con más días sin operar — ${delGrupo.slice(0, 4).map(r => r.label).join(", ")} — ` +
      `están todas en el grupo.`),
    refBox("Por qué la baja liquidez arma un grupo", [
      "Tener un dato todos los días no es lo mismo que operar todos los días: cuando nadie opera una acción, Yahoo Finance " +
      "igual entrega la fila, con el precio del día anterior y volumen 0. Una acción cuyo precio queda congelado muchos " +
      "días \"no acompaña\" al resto del mercado aunque su negocio sí lo haga, y su correlación medida con las demás sale " +
      "más baja que la real (Nanyonga et al., 2025, en las referencias de 01_scraping_acciones). El clustering la ve " +
      "distinta por cómo se actualiza su precio, no por cómo reacciona.",
    ]),
    p(""),
    p("Para comprobarlo, se repitió el mismo K-Means en tres versiones (robustez_grupo_liquidez.csv):", { keepNext: true }),
    simpleTable(["Prueba", "Acciones", "Silueta", "Tamaños", "Coincidencia con el grupo"],
      robustez.map(r => [`${r.prueba}) ${r.descripcion}`, r.acciones, coma(r.silueta), r.tamanos, `${r.en_comun_con_grupo} de ${kmLista.length}`]),
      [42, 11, 11, 14, 22]),
    p(""),
    p([bold("Lectura: "), plain(`tratar los días sin operación como faltantes casi no cambia nada (prueba B: silueta ` +
      `${coma(rob.B.silueta)}, ${rob.B.en_comun_con_grupo} de las ${kmLista.length}), así que el grupo no es un error de ` +
      `carga de esos días. Pero si se sacan las ${N - Number(rob.C.acciones)} acciones menos líquidas (prueba C), el grupo ` +
      `se deshace: la silueta cae de ${coma(rob.A.silueta)} a ${coma(rob.C.silueta)} y el reparto pasa a ${rob.C.tamanos}, ` +
      `sin una identidad clara. El grupo existe, sobre todo, porque existen acciones de baja liquidez. Las otras ` +
      `${kmLista.length - 4} del grupo se operan con normalidad y entran por otros rasgos — por ejemplo, la volatilidad ` +
      `extrema de CELU o el día dudoso de AGRO.`)]),
    refBox("Dos aclaraciones", [
      [bold("GCDI: "), plain("hoy se opera con normalidad (su volumen típico es como el de la acción promedio); sus días " +
        "sin operar se concentran en 2023 y principios de 2024, antes del salto de precio del 24/01/2024.")],
      [bold("AGRO: "), plain("además de estar en el grupo es la empresa que MST aísla sola. Conserva un día dudoso " +
        "(03/11/2023: −76% y +94% al día siguiente, ver 01_scraping_acciones) que infla su volatilidad, curtosis y máxima " +
        "caída en la ventana de 3 años.")],
    ]),

    h1("5. Gráficos — silueta por k, cada ventana"),
    p("Ventana de 1 año", { keepNext: true }),
    figure(path.join(CARPETA, "clustering_1ano.png"), 600),
    p("Ventana de 3 años (todo el período)", { keepNext: true }),
    figure(path.join(CARPETA, "clustering_3anos.png"), 600),
    p(`En Precio y Volumen, K-Means se mantiene bajo y plano para todo k (silueta entre ${coma(Math.min(...kmPV))} y ` +
      `${coma(Math.max(...kmPV))}) — sin estructura de grupos. Jerárquico y MST muestran en general la silueta cayendo a ` +
      `medida que k crece, la firma típica de ir "pelando" un outlier a la vez en vez de encontrar grupos genuinos. ` +
      `Solo "13 features" a 3 años despega con K-Means y Jerárquico, exactamente en el resultado de la sección 4. Los ` +
      `valores de cada punto están en siluetas_por_k.csv.`),

    h1("6. Conclusión de este paso"),
    p(`Sobre el panel de ${N} acciones no aparecen familias de comportamiento bien definidas. Casi todas las combinaciones ` +
      `solo aíslan 1 o 2 outliers, y el único grupo de tamaño real (${kmLista.length} empresas) se explica sobre todo por la ` +
      `baja liquidez de varias de sus integrantes: al sacarlas, la estructura desaparece. Para el análisis con noticias, ` +
      `esto lleva a trabajar acción por acción (y por sector), no por familias.`),
    p([bold("Para la etapa siguiente: "), plain(`en las acciones de baja liquidez (${delGrupo.slice(0, 4).map(r => r.label).join(", ")}) ` +
      "el precio se actualiza menos seguido. En un VAR o un test de Granger eso puede hacer que parezcan reaccionar con " +
      "retraso aunque no sea así, por lo que sus resultados por empresa deben leerse con cautela.")]),

    h1("7. Archivos generados"),
    p([code("D:\\2.Tesina\\tesis version 3.0\\Lado Bursatil\\02_clustering_acciones\\")]),
    simpleTable(["Archivo", "Qué es"], [
      ["clustering_acciones.py", `Script principal. Carga el panel de ${N}, corre las 18 combinaciones, guarda el resumen, las siluetas y los gráficos.`],
      ["resumen_clustering_47.csv", `Una fila por cluster × método × período × análisis (${resumen.length} filas).`],
      ["siluetas_por_k.csv", `Silueta de cada k (2 a 8) para las 18 combinaciones (${siluetas.length} filas) — los mismos valores de los gráficos.`],
      ["clustering_1ano.png / clustering_3anos.png", "Silueta vs. k, 3 algoritmos, una figura por representación."],
      ["analizar_grupo_no_degenerado.py", "Script de la sección 4: lee el grupo de resumen_clustering_47.csv, mide su liquidez, qué features lo separan, y corre las pruebas de robustez A, B y C."],
      ["comparacion_grupo_no_degenerado.csv", `Una fila por empresa (${N}): retorno, volatilidad, volumen, días sin operar, % de días con el precio quieto y puesto por volumen.`],
      ["features_que_separan_grupo.csv", "Diferencia de cada una de las 13 features entre el grupo y el resto, en desvíos estándar."],
      ["robustez_grupo_liquidez.csv", "Las pruebas A, B y C: silueta, tamaños y coincidencia con el grupo en cada versión."],
    ], [38, 62]),

    ...seccionReferencias("02_clustering_acciones", 8),
  ],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(CARPETA, "Documentacion_Clustering_Acciones.docx");
  fs.writeFileSync(out, buf);
  console.log("OK:", out, buf.length, "bytes");
});
