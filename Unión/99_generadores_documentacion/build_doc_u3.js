// Genera Documentacion_U3_Sentimiento_por_Empresa.docx dentro de ../03_sentimiento_por_empresa/
// Uso:  node build_doc_u3.js   (después convertir a PDF con LibreOffice headless)
const fs = require("fs");
const path = require("path");
const u = require("./comun_union");
const { docx, h1, p, code, bold, plain, refBox, simpleTable, figure, leerCsv, bullet, nota, leerResumen, miles, coma } = u;

const CARPETA = path.join(u.RAIZ_UNION, "03_sentimiento_por_empresa");
const r = leerResumen(path.join(CARPETA, "resumen_u3.csv"));
const verif = leerCsv(path.join(CARPETA, "verificaciones.csv"));
const cob = leerCsv(path.join(CARPETA, "cobertura_empresas.csv"));
const largo = leerCsv(path.join(CARPETA, "sentimiento_entidad_rueda.csv"));
const v = k => Number(r[k].valor);
const corte = r.empresas_con_sentimiento_propio.detalle.match(/\d+/)[0];
const propias = cob.filter(x => x.sentimiento_propio === "True");
const alua = cob.find(x => x.ticker === "ALUA.BA");
const siguiente = cob.filter(x => x.sentimiento_propio !== "True")[1];
const indicadores = new Set(largo.filter(x => x.tipo === "IND_ECO").map(x => x.entidad)).size;
const filasInd = largo.filter(x => x.tipo === "IND_ECO").length;
const sinMencion = r.empresas_sin_mencion.detalle;
const signo = x => (Number(x) > 0 ? "+" : "") + coma(x);

const doc = u.documentoUnion({
  titulo: "U3 · Sentimiento por empresa por rueda",
  subtitulo: "Qué tono tuvieron las noticias de cada empresa en cada día de bolsa",
  encabezado: "U3 · Sentimiento por empresa — tesis version 3.0",
  ubicacion: [bold("Ubicación. "), code("D:\\2.Tesina\\tesis version 3.0\\Unión\\03_sentimiento_por_empresa\\"),
    plain(". Script: "), code("sentimiento_por_empresa.py"), plain(".")],
  children: [
    refBox("En una frase", [
      `Se rehízo el cruce de Gino entre las menciones de empresas y el sentimiento de cada oración, agrupando por rueda en lugar de por fecha. ` +
      `Resultado: un panel de 47 acciones × ${v("ruedas")} ruedas que dice, para cada día, si hubo noticias de la empresa y con qué tono. ` +
      `${propias.length} empresas tienen noticias en al menos ${corte} ruedas y usan su sentimiento propio; las demás usan el sentimiento general del mercado.`,
    ]),

    h1("1. Qué hace este paso"),
    p("Gino ya había calculado el sentimiento de cada empresa por fecha: buscó en cada oración las menciones de las 47 empresas (NER) y les asignó el tono de esa oración " +
      "según el modelo de sentimiento. Este paso repite exactamente ese cálculo, con una sola diferencia: cada oración cuenta para la rueda de su nota (U1), " +
      "no para su fecha de calendario. Así el sentimiento de una empresa se compara con el precio que pudo verse afectado por esas noticias."),
    p("Para que el cálculo sea idéntico, el script no copia el código de Gino: importa sus propias funciones (cómo se normaliza el texto, cómo se unifican los indicadores " +
      "sinónimos y cómo se calcula el sentimiento neto)."),

    h1("2. Cómo se arma"),
    bullet([bold("Unión mención–sentimiento. "), plain(`Cada mención se une con el sentimiento de su oración por nota y número de oración, exigiendo además que el texto coincida. ` +
      `Se unen ${miles(v("oraciones_unidas"))} de ${miles(v("oraciones_con_entidades"))} oraciones con entidades (${coma(v("cobertura_cruce_pct"), 2)}%), igual que en el cruce de Gino.`)]),
    bullet([bold("Una oración, un voto. "), plain("Si una oración menciona dos veces a la misma empresa, cuenta una sola vez.")]),
    bullet([bold("Sentimiento neto. "), plain("Para cada empresa y rueda: (oraciones positivas − oraciones negativas) / oraciones que la mencionan × 100, la misma fórmula del resto del trabajo.")]),
    bullet([bold("Sin noticia no es tono neutro. "), plain("Si una empresa no aparece en una rueda, su sentimiento queda vacío y la marca hubo_noticia vale 0. " +
      "No se completa con 0, porque 0 significa \"tono neutro\" y haría parecer neutras a las empresas de las que nadie habla.")]),

    h1("3. Cuántas ruedas tienen noticias de cada empresa"),
    figure(path.join(CARPETA, "u3_cobertura.png"), 590),
    nota(`Arriba: ruedas con al menos una noticia de cada empresa (azul: las que usan sentimiento propio). Abajo: el sentimiento propio de esas ${propias.length} empresas en cada rueda.`),
    p([bold("El corte de las 90 ruedas. "), plain(
      `El corte se había fijado en 95 ruedas para incluir a Aluar (ALUA), que en el diagnóstico previo figuraba con ${alua.ruedas_diagnostico.replace(".0", "")}. ` +
      "Ese número era una estimación: usaba solo la fecha de cada nota, porque la hora recién se incorpora en U1. Con la regla completa, ALUA tiene " +
      `${alua.ruedas_con_noticias} ruedas, así que el 24/10 el corte se bajó a ${corte}. Cualquier corte entre ${Number(siguiente.ruedas_con_noticias) + 1} y ${alua.ruedas_con_noticias} ` +
      `da exactamente las mismas ${propias.length} empresas: la siguiente, ${siguiente.ticker.replace(".BA", "")}, tiene ${siguiente.ruedas_con_noticias}.`)]),
    simpleTable(["Empresa", "Sector", "Ruedas con noticias", "Estimación previa", "Tono total"],
      propias.map(x => [`${x.ticker.replace(".BA", "")} · ${x.empresa}`, x.sector, `${x.ruedas_con_noticias} (${coma(x.pct_ruedas)}%)`,
        x.ruedas_diagnostico.replace(".0", ""), signo(x.sent_neto_total)]),
      [38, 15, 19, 14, 14]),
    nota("Tono total: sentimiento neto de todas las oraciones que mencionan a la empresa en la ventana de la unión."),
    p(`Del resto: ${v("empresas_menos_10_ruedas")} empresas tienen menos de 10 ruedas con noticias y ${v("empresas_sin_mencion")} ninguna (${sinMencion}). ` +
      "Estas empresas entran igual a los modelos, con el sentimiento general del mercado; solo no tienen una serie propia."),

    h1("4. Un aviso para los modelos"),
    p(`En las empresas con sentimiento propio, una rueda con noticias tiene una mediana de ${v("mediana_oraciones_por_rueda_empresa")} oraciones que mencionan a la empresa, ` +
      `y en el ${coma(v("pct_ruedas_empresa_una_oracion"))}% de esas ruedas hay una sola. Ese día el sentimiento sale todo o nada: +100 si la oración es positiva, ` +
      "−100 si es negativa y 0 si es neutra. Por eso el mapa de colores salta tanto entre verde y rojo."),
    p("No es un error, pero vuelve muy ruidosa la serie de cada empresa. En U4 se guardan las dos cosas que hacen falta para tratarlo, el sentimiento y la cantidad de oraciones, " +
      "y en U6 se decide cómo usarlas (por ejemplo, dándoles más peso a las ruedas con más oraciones)."),

    h1("5. También los indicadores"),
    p(`El mismo archivo largo (sentimiento_entidad_rueda.csv) trae el sentimiento por rueda de ${indicadores} indicadores económicos (inflación, tipo de cambio, riesgo país, ` +
      `etc.), en ${miles(filasInd)} filas, con las equivalencias de Gino ya aplicadas. No entran al pipeline principal, pero quedan disponibles por si se quieren usar como control.`),

    h1("6. Controles"),
    simpleTable(["Control", "Resultado"], verif.map(x => [x.control, x.pasa === "True" ? "Pasa" : "NO PASA"]), [82, 18]),
    p("El primer control es el más importante: si en lugar de agrupar por rueda se agrupa por fecha, el resultado es idéntico, fila por fila, al archivo ner_sentimiento_diario.csv de Gino. " +
      `La única diferencia con su trabajo es la regla de la rueda. ${v("notas_con_mencion_fuera_de_ventana")} notas con menciones quedan fuera porque su rueda cae antes o después de la ventana.`),

    h1("7. Archivos que genera"),
    simpleTable(["Archivo", "Qué tiene"], [
      [[code("panel_empresas_rueda.csv")], `47 acciones × ${v("ruedas")} ruedas: hubo_noticia, si usa sentimiento propio, artículos, oraciones, cantidad de cada clase y sentimiento neto (vacío si no hubo noticia)`],
      [[code("sentimiento_entidad_rueda.csv")], "Una fila por rueda × entidad (empresas e indicadores) con noticias, en el mismo formato que el archivo diario de Gino"],
      [[code("cobertura_empresas.csv")], "Ruedas con noticias de cada acción, artículos, oraciones, tono total, estimación previa y si usa sentimiento propio"],
      [[code("resumen_u3.csv"), plain(", "), code("verificaciones.csv")], "Las cifras y los controles de este documento"],
      [[code("u3_cobertura.png")], "La figura de la sección 3"],
    ], [34, 66]),

    h1("8. Limitaciones"),
    bullet("El sentimiento de una empresa es el de las oraciones que la mencionan, no una opinión sobre la empresa: una oración negativa sobre el sector que nombra a la empresa cuenta como negativa para ella."),
    bullet("Hereda los límites del NER de Gino: una empresa nombrada de una forma que el gazetteer no reconoce no se cuenta."),
    bullet("En muchas ruedas el sentimiento de la empresa se apoya en una o dos oraciones (sección 4)."),
  ],
});

docx.Packer.toBuffer(doc).then(buf => {
  const out = path.join(CARPETA, "Documentacion_U3_Sentimiento_por_Empresa.docx");
  fs.writeFileSync(out, buf);
  console.log("Generado:", out);
});
