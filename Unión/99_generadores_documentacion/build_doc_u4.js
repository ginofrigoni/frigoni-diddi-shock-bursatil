// Genera Documentacion_U4_Datasets.docx dentro de ../04_dataset_unificado/
// Uso:  node build_doc_u4.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, miles, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "04_dataset_unificado");
const r = leerResumen(path.join(CARPETA, "resumen_u4.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const dic = leerCsv(path.join(CARPETA, "diccionario_variables.csv"));
const desc = leerCsv(path.join(CARPETA, "descriptivos.csv"));
const v = k => Number(r[k].valor);
const NOMBRE = {
  ret_merval: "Retorno del Merval", vix_arg: "VIX argentino (%)", monto_anormal: "Monto operado anormal (log)", sent_neto: "Tono de las noticias",
  sent_neto_portal: "Tono ajustado por portal", sent_anormal: "Tono anormal (variable del VAR)", n_notas: "Notas por rueda", atencion_anormal: "Atención anormal (log)", retorno: "Retorno de cada acción",
  vol_anormal: "Volumen anormal de cada acción (log)", sent_neto_empresa: "Tono de la empresa (si hubo noticia)", n_oraciones_empresa: "Oraciones que mencionan a la empresa", tono_propio: "Tono propio (17 empresas)",
};
const fmt = (x, var_) => var_.startsWith("ret") ? coma(100 * Number(x), 2) + "%" : coma(x, 2);
const [propCon, propTot] = [v("filas_sentimiento_propio_con_noticia"), Number(r.filas_sentimiento_propio_con_noticia.detalle.replace("de ", ""))];

const doc = u.documentoUnion({
  titulo: "U4 · Datasets unificados",
  subtitulo: "Las dos tablas que juntan el lado bursátil con el lado de noticias",
  encabezado: "U4 · Datasets unificados — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\04_dataset_unificado\\"),
    plain(". Script: "), code("construir_datasets.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `Todo lo que usan los modelos quedó en dos archivos: dataset_mercado.csv (una fila por rueda, ${v("ruedas")} filas y ${v("columnas_mercado")} columnas) ` +
      `y dataset_panel.csv (una fila por acción y rueda, ${miles(v("filas_panel"))} filas y ${v("columnas_panel")} columnas). Cada columna está explicada en el diccionario ` +
      `de variables (anexo) y los ${v("controles_ok")} controles pasan.`,
    ]),

    h1("1. Qué hace este paso"),
    p("Hasta acá cada pieza estaba en su carpeta: los precios y el régimen en el lado bursátil, el tono y la atención en U2, el tono de cada empresa en U3. " +
      "Este paso las junta en dos tablas, para que ningún modelo tenga que armar su propio cruce: si dos modelos usan la misma variable, la sacan del mismo lugar."),
    simpleTable(["Tabla", "Una fila es", "Para qué se usa"], [
      [[code("dataset_mercado.csv")], "Una rueda", "VAR del mercado (U6), régimen y robustez"],
      [[code("dataset_panel.csv")], "Una acción en una rueda", "VAR por empresa y por sector (U6) y event study (U7)"],
    ], [30, 25, 45]),

    h1("2. Qué tiene cada tabla"),
    p([bold("Mercado. "), plain("Del lado bursátil: Merval y su retorno, VIX argentino, régimen del HMM (suavizado y filtrado) y la probabilidad de Tenso. " +
      "Del lado de noticias: cantidad de notas, atención anormal, tono simple y ajustado por portal, porcentaje de cada clase de oración y las ruedas de tono extremo. " +
      "Nuevo en U4: el monto operado del panel y su versión anormal, el tono anormal (decisión de U5) y tres marcas de días especiales.")]),
    p([bold("Tono anormal. "), plain("Es el tono de la rueda menos el promedio del tono de las 20 ruedas previas: cuánto más optimistas o pesimistas que lo habitual " +
      "están las noticias. Se agregó después de U5, donde el tono en nivel dio inconcluso en el test de estacionariedad; es la variable de tono que usa el VAR, " +
      "y el tono en nivel queda para las pruebas de robustez.")]),
    p([bold("Tono propio de la empresa. "), plain("Es cuánto mejor o peor se habla de la empresa que del mercado ese día, con más peso cuantas más oraciones la mencionan: " +
      `peso × (tono de la empresa − tono del mercado), con peso = n / (n + ${coma(v("k_peso_tono_propio"), 1)}). Si no hubo noticias de la empresa vale 0. ` +
      "El número del peso no se eligió a ojo: es la varianza de una oración suelta dividida por la varianza real del tono entre días (estimación empírica de Bayes). " +
      `Con 1 oración se confía un ${coma(100 * v("peso_con_1_oraciones"), 0)}%, con 5 un ${coma(100 * v("peso_con_5_oraciones"), 0)}%, con 10 un ${coma(100 * v("peso_con_10_oraciones"), 0)}% ` +
      `y con 30 un ${coma(100 * v("peso_con_30_oraciones"), 0)}%. Se agregó en U6, donde se decidió cómo tratar los días sin noticias y los días con una sola oración.`)]),
    p([bold("Panel. "), plain("Por cada acción y rueda: cierre, retorno, volumen, monto, volumen anormal, si no operó y si el precio quedó quieto; sector, si es oficial del Merval " +
      "y su grupo de liquidez; si hubo noticias de la empresa, cuántas y con qué tono; y, repetidas en cada fila, las variables de mercado de esa rueda.")]),

    h1("3. Las variables de volumen (decisión D2)"),
    p("El plan de tesis pide medir el impacto sobre precio y volumen. El volumen en bruto no sirve para comparar: cada acción tiene su propio nivel (YPF opera mucho más que Agrometal) " +
      "y los montos en pesos crecen con la inflación. Por eso se usa el volumen anormal: cuánto se operó hoy comparado con las 20 ruedas previas de la misma acción."),
    bullet([bold("Volumen anormal de cada acción "), plain("= log(1 + volumen de hoy) − promedio de log(1 + volumen) de las 20 ruedas previas. " +
      "0 es un día habitual; +0,69 es el doble de lo habitual; −0,69, la mitad. El \"1 +\" evita el problema de los días sin operaciones.")]),
    bullet([bold("Monto operado anormal del mercado: "), plain("lo mismo con el monto total (cierre × volumen, sumado sobre las 47 acciones).")]),
    p("Se calculan sobre la serie completa desde 2023 y recién después se recorta la ventana, como los retornos del lado bursátil; así la primera rueda de la ventana ya tiene sus 20 previas."),
    p([bold("Un detalle: "), plain(`los días en que una acción no operó dan un volumen anormal muy negativo (el mínimo es ${coma(desc.find(x => x.variable === "vol_anormal").minimo, 1)}), ` +
      "porque se compara un volumen de 0 con lo habitual. Son pocos días y quedan identificados con la columna sin_operar.")]),

    h1("4. Marcas de días especiales"),
    simpleTable(["Marca", "Ruedas", "Por qué"], [
      ["dia_electoral", "2", "Ruedas posteriores a las elecciones bonaerenses (08/09/2025) y legislativas (27/10/2025): son a la vez noticia y los mayores saltos del mercado"],
      ["eco_electoral", String(v("ruedas_eco_electoral")), "Las 20 ruedas desde cada día electoral: el salto sigue dentro de la ventana del VIX y arrastra el régimen (eco de 20 ruedas, carpeta 03)"],
      ["abril_2026", String(v("ruedas_abril_2026")), "Ruedas de abril de 2026, cuando el corpus casi no tiene notas de iProfesional"],
    ], [20, 12, 68]),
    p("Las marcas no cambian ningún dato: sirven para analizar esos días aparte o repetir los resultados sin ellos (U7 y U8)."),

    h1("5. La liquidez dentro de la ventana"),
    p(`Las 4 acciones con más días sin operar en los 3 años (GCDI, RIGO, GRIM y GARO, ${v("cuatro_iliquidas_sin_operar_3anos")} días entre las cuatro) casi no tienen ` +
      `días sin operar dentro de la ventana de la unión: ${v("cuatro_iliquidas_sin_operar")} en total (${r.cuatro_iliquidas_sin_operar.detalle}). Sus días sin operar se concentraban en 2023 y principios de 2024.`),
    p(`Lo que sí conservan son días de precio quieto (el cierre igual al del día anterior): ${v("cuatro_iliquidas_precio_quieto")} entre las cuatro (${r.cuatro_iliquidas_precio_quieto.detalle}), ` +
      `contra una mediana de ${v("precio_quieto_mediana")} en las 47 acciones. La cautela sobre su liquidez sigue, pero pesa menos en este tramo; en U8 se repiten los resultados sin ellas.`),

    h1("6. Panorama y números básicos"),
    figure(path.join(CARPETA, "u4_panorama.png"), 590),
    nota("Merval, tono de las noticias, atención de los medios y monto operado anormal en la ventana de la unión. El color de fondo es el régimen del HMM; las líneas punteadas, los días electorales."),
    simpleTable(["Variable", "Filas", "Media", "Desvío", "Mínimo", "Máximo"],
      desc.map(x => [NOMBRE[x.variable] || x.variable, miles(x.n), fmt(x.media, x.variable), fmt(x.desvio, x.variable), fmt(x.minimo, x.variable), fmt(x.maximo, x.variable)]),
      [36, 10, 13, 13, 14, 14]),
    nota(`La atención y el tono anormal tienen ${v("ruedas") - v("ruedas_atencion_vacia")} filas porque las primeras ${v("ruedas_atencion_vacia")} ruedas no tienen 20 previas de referencia. ` +
      "El tono de la empresa solo existe en las filas con noticias de la empresa."),

    h1("7. Lo que se resolvió para U6"),
    bullet([bold("Ruedas sin noticias y ruedas con una sola oración (resuelto en U6). "), plain(`Las 17 empresas con sentimiento propio tienen noticias en ${miles(propCon)} de sus ${miles(propTot)} filas ` +
      `(${coma(100 * propCon / propTot)}%), y muchas veces una sola oración. Las dos cosas se resolvieron con el tono propio (sección 2): vale 0 sin noticias y pondera por cantidad de oraciones.`)]),
    bullet([bold("Moderado. "), plain(`Tiene ${v("ruedas_moderado")} ruedas: el VAR por régimen compara Calmo (${v("ruedas_calmo")}) contra Tenso (${v("ruedas_tenso")}), como se decidió.`)]),

    h1("8. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),

    h1("9. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("dataset_mercado.csv")], `${v("ruedas")} ruedas × ${v("columnas_mercado")} columnas`],
      [[code("dataset_panel.csv")], `${miles(v("filas_panel"))} filas (47 acciones × ${v("ruedas")} ruedas) × ${v("columnas_panel")} columnas`],
      [[code("diccionario_variables.csv")], "Qué es cada columna, su unidad y de dónde sale (anexo de este documento)"],
      [[code("descriptivos.csv")], "Media, desvío, mínimo, mediana y máximo de las variables principales"],
      [[code("resumen_u4.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u4_panorama.png")], "La figura de la sección 6"],
    ], [34, 66]),

    h1("10. Limitaciones"),
    bullet("Precios, retornos y montos están en pesos nominales: incluyen inflación y tipo de cambio (la versión en dólares queda como trabajo futuro). Las variables anormales comparan con las 20 ruedas previas, lo que descuenta la tendencia lenta."),
    bullet("El monto operado del mercado es el de las 47 acciones del panel, no el total de BYMA."),
    bullet("El retorno del mercado es el del Merval; el event study lo usa como referencia para cada acción."),

    h1("Anexo · Diccionario de variables"),
    simpleTable(["Variable", "Tabla", "Qué es", "Unidad", "De dónde sale"],
      dic.map(x => [[code(x.variable)], x.dataset, x.descripcion, x.unidad, x.origen]), [22, 12, 34, 12, 20]),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U4_Datasets.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
