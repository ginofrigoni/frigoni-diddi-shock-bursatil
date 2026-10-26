// Genera Documentacion_U7_Event_Study.docx dentro de ../07_event_study/
// Uso:  node build_doc_u7.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, coma, fecha } = u;

const CARPETA = path.join(u.RAIZ_UNION, "07_event_study");
const r = leerResumen(path.join(CARPETA, "resumen_u7.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const resM = leerCsv(path.join(CARPETA, "resultados_mercado.csv"));
const resE = leerCsv(path.join(CARPETA, "resultados_empresa.csv"));
const elec = leerCsv(path.join(CARPETA, "dias_electorales.csv"));
const evM = leerCsv(path.join(CARPETA, "eventos_mercado.csv"));
const v = k => Number(r[k].valor);
const pc = x => (Number(x) > 0 ? "+" : "") + coma(x, 2) + "%";
const pv = x => coma(x, 3);
const VENT = ["antes [−3, −1]", "día [0]", "después [+1, +5]", "total [−3, +5]"];
const filaM = (ev, vent, muestra = "todos") => resM.find(x => x.eventos === ev && x.ventana === vent && x.muestra === muestra);
const filaE = (ev, vent) => resE.find(x => x.eventos === ev && x.ventana === vent);
const tablaM = (ev, muestra = "todos") => VENT.map(w => { const x = filaM(ev, w, muestra);
  return [w, pc(x.car_medio_pct), `${x.positivos} de ${x.n}`, pv(x.p_t), pv(x.p_signo), pv(x.p_azar), `${coma(x.monto_anormal_medio, 2)} (p ${pv(x.p_vol_azar)})`]; });
const ev1030 = evM.find(x => x.rueda === "2025-10-30");
const posAntes = filaM("positivos", "antes [−3, −1]"), posDia = filaM("positivos", "día [0]"), posDesp = filaM("positivos", "después [+1, +5]");
const solDia = filaM("positivos", "día [0]", "sin solapados");
const volPA = posAntes, volPD = posDia;
const eAntes = filaE("positivos", "antes [−3, −1]"), eDesp = filaE("positivos", "después [+1, +5]");
const nAntes = filaE("negativos", "antes [−3, −1]"), nDesp = filaE("negativos", "después [+1, +5]");

const doc = u.documentoUnion({
  titulo: "U7 · Event study",
  subtitulo: "Qué hacen los precios y el volumen alrededor de las ruedas de noticias extremas",
  encabezado: "U7 · Event study — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\07_event_study\\"),
    plain(". Script: "), code("event_study.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `En las ruedas de tono extremo positivo, el Merval sube ${pc(posDia.car_medio_pct)} ese mismo día (${posDia.positivos} de ${posDia.n} eventos) y ya venía ` +
      `subiendo ${pc(posAntes.car_medio_pct)} en las tres ruedas previas; después no pasa nada. Con las empresas ocurre lo mismo: cuando se habla de una empresa de forma ` +
      `muy positiva, su acción ya había subido ${pc(eAntes.car_medio_pct)} más que el mercado antes. Las noticias acompañan o siguen al precio; no lo anticipan.`,
    ]),

    h1("1. Qué es un event study"),
    p("Se toman los días con noticias extremas (los eventos) y se mira qué hicieron los precios unos días antes y unos días después, comparado con lo que habría sido normal. " +
      "Si las noticias mueven al mercado, el precio debería cambiar el día del evento o después. Si las noticias reflejan lo que el mercado ya hizo, el cambio aparece antes."),
    p("La ventana va de 3 ruedas antes a 5 después del evento ([−3, +5]; la rueda 0 es la del evento) y se separa en tres tramos: antes [−3, −1], el día [0] y después [+1, +5]. " +
      "Lo \"normal\" se estima con las ruedas −25 a −4, que terminan antes de la ventana para que el evento no contamine su propia comparación. " +
      "Al movimiento de más o de menos respecto de lo normal se le llama retorno anormal, y a su suma en un tramo, retorno anormal acumulado (CAR)."),

    h1("2. Dos tipos de eventos"),
    p([bold("A. Ruedas de tono extremo del mercado. "), plain(`Son las de U2 (${v("eventos_mercado")} eventos). Son noticias generales: si mueven precios, mueven al Merval entero. ` +
      "Por eso se mide el Merval mismo, contra su retorno promedio de las ruedas −25 a −4. No se usa un modelo de mercado por acción, porque resta justamente el movimiento del Merval " +
      "y el efecto buscado desaparecería por construcción.")]),
    p([bold("B. Ruedas de tono propio extremo de cada empresa. "), plain(`Para las 17 empresas con tono propio, las ruedas en que se habló de ellas mucho mejor o mucho peor que del mercado ` +
      `(más de 2,5 desvíos de su propia serie): ${v("eventos_empresa")} eventos. Acá sí se usa el modelo de mercado por acción, porque la pregunta es si esa acción se movió distinto del resto.`)]),
    p([bold("Cómo se decide si un resultado es real. "), plain(`Con pocos eventos, además del test t y del test de signo, se compara contra fechas al azar: se sortean ${coma(5000, 0)} veces ` +
      `tantas fechas como eventos, entre ${v("ruedas_para_sorteo")} ruedas posibles, y se ve cuántas veces el azar da un promedio tan extremo como el observado.`)]),

    h1("3. Lo que hubo que corregir: el salto electoral"),
    p(`La primera corrida mostró un +6,3% en las ruedas previas a los eventos positivos. Mirado evento por evento, lo generaba casi todo uno solo: el del 30/10/2025, ` +
      `con ${pc(100 * Number(ev1030["car_antes [−3, −1]"]))} en su tramo \"antes\", porque incluía el 27/10, cuando el Merval saltó +21% después de las legislativas. ` +
      "Además, un salto así dentro de las ruedas −25 a −4 infla el \"promedio normal\" de los eventos siguientes."),
    p(`Por eso los dos días electorales (08/09 y 27/10) no entran al cálculo de lo normal, y los eventos cuya ventana incluye uno se analizan aparte ` +
      `(${r.eventos_con_eleccion.detalle.split(", ").map(fecha).join(" y ")}). Quedan ${v("eventos_mercado_principal")} eventos: ${v("eventos_pos")} positivos y ${v("eventos_neg")} negativos. ` +
      "El sorteo al azar aplica la misma exclusión."),
    simpleTable(["Día electoral", "¿Shock de tono?", "Antes", "Día", "Después", "Total"],
      elec.map(x => [`${fecha(x.rueda)} · ${x.evento}`, x.es_shock_de_tono === "True" ? "Sí (positivo)" : "No", pc(x["car_antes [−3, −1]"]), pc(x["car_día [0]"]),
        pc(x["car_después [+1, +5]"]), pc(x["car_total [−3, +5]"])]), [34, 16, 12, 12, 13, 13]),
    nota("Los días electorales fueron los mayores saltos del período. El 27/10 también fue una rueda de tono extremo positivo, pero el salto lo explica la elección, no el tono."),

    h1("4. Resultado A: el Merval en las ruedas de tono extremo"),
    p([bold(`Tono extremo positivo (${v("eventos_pos")} eventos)`)]),
    simpleTable(["Tramo", "CAR medio", "Eventos con suba", "p (test t)", "p (signo)", "p (azar)", "Volumen anormal (p azar)"], tablaM("positivos"), [19, 11, 13, 11, 11, 11, 24]),
    p([bold(`Tono extremo negativo (${v("eventos_neg")} eventos)`)]),
    simpleTable(["Tramo", "CAR medio", "Eventos con suba", "p (test t)", "p (signo)", "p (azar)", "Volumen anormal (p azar)"], tablaM("negativos"), [19, 11, 13, 11, 11, 11, 24]),
    figure(path.join(CARPETA, "u7_mercado.png"), 590),
    nota("Retorno anormal acumulado promedio del Merval desde 3 ruedas antes hasta 5 después de los eventos. La banda gris es el 95% de lo que da el azar con la misma cantidad de fechas."),
    p(`En las ruedas de tono extremo positivo, el Merval sube ${pc(posDia.car_medio_pct)} el mismo día, en ${posDia.positivos} de ${posDia.n} eventos (p del test t ${pv(posDia.p_t)}, contra el azar ${pv(posDia.p_azar)}). ` +
      `Y ya venía subiendo: ${pc(posAntes.car_medio_pct)} en las tres ruedas previas (contra el azar, p = ${pv(posAntes.p_azar)}). Después del evento no hay nada: ${pc(posDesp.car_medio_pct)}, ` +
      `que no se distingue del azar. En las ruedas de tono extremo negativo no aparece ningún movimiento.`),
    p(`Como control, dejando solo el primero de cada grupo de eventos solapados quedan ${solDia.n} eventos positivos: la suba del día se mantiene (${pc(solDia.car_medio_pct)}) ` +
      (Number(solDia.p_azar) < 0.05 ? `y sigue siendo distinta del azar (p = ${pv(solDia.p_azar)}), aunque con tan pocos eventos el test t da ${pv(solDia.p_t)}.`
                                    : `pero con tan pocos eventos ya no se distingue del azar (p = ${pv(solDia.p_azar)}).`)),
    p([bold("El volumen. "), plain(`El monto operado anormal del mercado (última columna; 0 es lo habitual, +0,69 el doble) acompaña al precio: en los eventos positivos ya estaba ` +
      `${coma(volPA.monto_anormal_medio, 2)} por encima de lo habitual en las tres ruedas previas (contra el azar, p = ${pv(volPA.p_vol_azar)}) y ${coma(volPD.monto_anormal_medio, 2)} el mismo día ` +
      `(p = ${pv(volPD.p_vol_azar)}); después vuelve a lo normal. En los eventos negativos no se distingue del azar. El test t, que no usa el azar como referencia, no llega al 5% en ningún tramo.`)]),

    h1("5. Resultado B: cada empresa en sus ruedas de tono propio extremo"),
    simpleTable(["Eventos", "Tramo", "CAR medio", "Con suba", "p (test t)", "Volumen anormal"],
      ["positivos", "negativos"].flatMap(ev => VENT.map(w => { const x = filaE(ev, w);
        return [w === VENT[0] ? `${ev} (${x.n})` : "", w, pc(x.car_medio_pct), `${x.positivos} de ${x.n}`, pv(x.p_t), `${coma(x.vol_anormal_medio, 3)} (p ${pv(x.p_vol)})`]; })),
      [16, 22, 14, 14, 14, 20]),
    figure(path.join(CARPETA, "u7_empresa.png"), 500),
    p(`Cuando se habla de una empresa de forma muy positiva, su acción ya había subido ${pc(eAntes.car_medio_pct)} más que el mercado en las tres ruedas previas (p = ${pv(eAntes.p_t)}), ` +
      `y después no pasa nada (${pc(eDesp.car_medio_pct)}). Con el tono muy negativo, la acción venía de bajar ${pc(nAntes.car_medio_pct)} (p = ${pv(nAntes.p_t)}) y después ` +
      `rebota ${pc(nDesp.car_medio_pct)}, pero ninguno de los dos llega al 5%. El volumen de la empresa no cambia. ` +
      `Se excluyeron ${v("eventos_empresa_con_eleccion")} eventos cuya ventana incluía un día electoral.`),

    h1("6. Cómo encaja con U6"),
    bullet([bold("El precio y el volumen se mueven antes o junto con las noticias, no después. "), plain("Es lo mismo que mostró Granger: el retorno anticipa el tono, y el tono no anticipa el retorno.")]),
    bullet([bold("El mismo día hay movimiento conjunto. "), plain("Las ruedas de tono muy positivo son ruedas de suba del Merval. Con datos diarios no se puede saber quién movió a quién dentro de la rueda; " +
      "lo que sí se ve es que, pasada esa rueda, el tono no deja nada por anticipar.")]),
    bullet([bold("La asimetría. "), plain("El efecto aparece con el tono positivo y no con el negativo. Con 7 y 9 eventos no se puede afirmar que sea una diferencia real; queda como observación.")]),

    h1("7. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),

    h1("8. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("eventos_mercado.csv")], "Cada evento del mercado: rueda, tipo, si es electoral o tiene una elección en la ventana, si se solapa, CAR y volumen por tramo"],
      [[code("resultados_mercado.csv")], "Promedios y tests por tipo de evento y tramo, con todos los eventos y sin los solapados"],
      [[code("eventos_empresa.csv"), plain(", "), code("resultados_empresa.csv")], "Lo mismo para los eventos de tono propio de las empresas, con el β de cada modelo de mercado"],
      [[code("dias_electorales.csv")], "El CAR del Merval alrededor de los dos días electorales"],
      [[code("resumen_u7.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u7_mercado.png"), plain(", "), code("u7_empresa.png")], "Las figuras"],
    ], [36, 64]),

    h1("9. Limitaciones"),
    bullet(`Hay pocos eventos del mercado (${v("eventos_pos")} positivos y ${v("eventos_neg")} negativos), y la mitad se solapan con otro. Por eso se usa también la comparación contra el azar.`),
    bullet("Las ruedas de tono extremo son las puntas de la variación normal del tono, no días excepcionales (U2). En U8 se repite con el umbral 3, que deja solo las más extremas."),
    bullet("El retorno anormal del Merval se mide contra su promedio reciente (modelo de media constante), porque no hay un índice externo con el cual compararlo."),
    bullet("Los retornos están en pesos nominales."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U7_Event_Study.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
