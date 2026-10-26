"""Arma bibliografia.tex a partir de los tres catálogos de papers de la tesis.

Fuentes (no se modifican):
  - Lado Bursatil/99_generadores_documentacion/referencias.json  (carpetas 00 a 06)
  - Unión/10_papers_union/referencias_papers.bib
  - Unión/11_papers_lado_noticias/referencias_papers.bib

Cada referencia sale en formato autor-año (estilo APA) con la ruta del PDF
descargado, relativa a la carpeta "tesis version 3.0" y con un enlace que se
abre desde el PDF de la tesina. Las que no se descargaron dicen por qué.

Uso:  python generar_bibliografia.py   (desde "Informe Final")
"""
import json
import re
import sys
import unicodedata
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent                      # tesis version 3.0
BURSATIL = RAIZ / "Lado Bursatil"
UNION = RAIZ / "Unión"

# Claves duplicadas entre catálogos: se usa una sola.
ALIAS = {"dickeyfuller1979": "dickey1979"}

# Archivo de las entradas sin arXiv en los .bib de la unión (ver referencias_papers.md).
ARCHIVOS_MANUALES = {
    "tetlock2007": "00_marco_Tetlock_2007_media_sentiment.pdf",
    "garcia2013": "00_marco_Garcia_2013_sentiment_recessions.pdf",
    "brana2016": "U2U3_Brana_Litterio_Fernandez_sentimiento_mercados_argentinos.pdf",
    "rodriguezgarcia2023": "U2_CEUR_3496_BETO_opiniones_financieras.pdf",
    "rojas2015": "U4U6_redalyc_retorno_volumen_LatAm.pdf",
    "coronado2022": "U6_Entropy_2022_transfer_entropy_COVID_LatAm.pdf",
    "coronado2023": "U6_MDPI_2023_Granger_variable_COVID_LatAm.pdf",
    "cruzmontana2025": "U6_CruzMontana_Tirado_2025_sentimiento_COLCAP.pdf",
    "galdi2018": "U6_Galdi_Goncalves_2018_RAE_pesimismo_noticias_Brasil.pdf",
    "barbaresi2021": "noticias_Barbaresi_2021_trafilatura.pdf",
    "tjongkimsang2002conll": "ner_TjongKimSang_2002_CoNLL_NER_espanol.pdf",
}

# Por qué no se descargaron las citadas de la unión (referencias_papers.md, sección 2).
NO_DESCARGADO = {
    "pan2023peerj": "de acceso abierto, pero el sitio bloquea la descarga automática; se baja a mano desde https://peerj.com/articles/cs-1377",
    "garciadiaz2023ieee": "de acceso abierto, pero sin enlace directo al PDF; se baja a mano desde IEEE Xplore",
    "marin2023finances": "no se encontró un PDF directo",
    "devlin2019bert": "se cita a través del artículo de BETO",
    "wirth2000crispdm": "no se localizó una copia oficial",
    "honnibal2020spacy": "es software; se cita como herramienta",
}
NO_DESCARGADO_POR_DEFECTO = "con derechos de autor y sin copia gratuita oficial"

# Clásicos citados en la tesina que no están en ningún catálogo de papers.
EXTRAS = [
    dict(clave="fama1970", autores=["Fama, E. F."], anio="1970",
         resto=r"Efficient capital markets: A review of theory and empirical work. \emph{The Journal of Finance}, 25(2), 383--417.",
         motivo="clásico citado; con derechos de autor"),
    dict(clave="brown1985", autores=["Brown, S. J.", "Warner, J. B."], anio="1985",
         resto=r"Using daily stock returns: The case of event studies. \emph{Journal of Financial Economics}, 14(1), 3--31.",
         motivo="clásico citado en el documento de la entrega final; con derechos de autor"),
    dict(clave="dougal2012", autores=["Dougal, C.", "Engelberg, J.", "García, D.", "Parsons, C. A."], anio="2012",
         resto=r"Journalists and the stock market. \emph{The Review of Financial Studies}, 25(3), 639--679.",
         motivo="clásico citado en el documento de la entrega final; con derechos de autor"),
    dict(clave="engelberg2011", autores=["Engelberg, J. E.", "Parsons, C. A."], anio="2011",
         resto=r"The causal impact of media in financial markets. \emph{The Journal of Finance}, 66(1), 67--97.",
         motivo="clásico citado en el documento de la entrega final; con derechos de autor"),
    dict(clave="shiffler1988", autores=["Shiffler, R. E."], anio="1988",
         resto=r"Maximum Z scores and outliers. \emph{The American Statistician}, 42(1), 79--80.",
         motivo="citado en el documento de la entrega final; con derechos de autor"),
    dict(clave="seabold2010", autores=["Seabold, S.", "Perktold, J."], anio="2010",
         resto=r"Statsmodels: Econometric and statistical modeling with Python. \emph{Proceedings of the 9th Python in Science Conference}, 92--96.",
         motivo="software usado en todos los modelos; se cita como herramienta"),
]

ESPECIALES = str.maketrans({"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_"})


def escapar(texto):
    """Escapa los caracteres especiales de LaTeX de un texto plano; las URL van en \\url."""
    partes = re.split(r"(https?://\S+?)(?=[.,;]?(?:\s|$))", texto)
    return "".join(r"\url{" + p + "}" if i % 2 else p.translate(ESPECIALES)
                   for i, p in enumerate(partes))


ACENTOS = {"'": "\u0301", "`": "\u0300", "^": "\u0302", '"': "\u0308", "~": "\u0303", "c": "\u0327"}


def a_unicode(texto):
    """Gon{\\c{c}}alves -> Gonçalves, Bra{\\~n}a -> Braña (para las etiquetas del texto)."""
    def reemplazo(m):
        letra = "ı" if m.group(2) == "\\i" else m.group(2)
        return unicodedata.normalize("NFC", letra + ACENTOS[m.group(1)])
    texto = re.sub(r"\\([`'^\"~c])\s*\{?(\\i|\w)\}?", reemplazo, texto)
    return texto.replace("{", "").replace("}", "")


def sin_acentos(texto):
    texto = re.sub(r"\\[`'^\"~=.uvHc]\{?(\w)\}?", r"\1", texto)
    texto = texto.replace("{", "").replace("}", "")
    texto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in texto if not unicodedata.combining(c)).lower()


def etiqueta(apellidos, anio):
    """Etiqueta autor-año para natbib: corta (en el texto) y larga."""
    if len(apellidos) == 1:
        corta = apellidos[0]
    elif len(apellidos) == 2:
        corta = f"{apellidos[0]} y {apellidos[1]}"
    else:
        corta = f"{apellidos[0]} et~al."
    larga = ", ".join(apellidos[:-1]) + f" y {apellidos[-1]}" if len(apellidos) > 1 else apellidos[0]
    return f"{corta}({anio}){larga}"


def autores_apa(lista):
    """['Apellido, I.', ...] -> 'Apellido, I., Otro, J. y Último, K.'"""
    if len(lista) == 1:
        return lista[0]
    return ", ".join(lista[:-1]) + " y " + lista[-1]


# ---------------------------------------------------------------- lado bursátil
def leer_bursatil():
    entradas = {}
    datos = json.loads((BURSATIL / "99_generadores_documentacion" / "referencias.json").read_text(encoding="utf-8"))
    for e in datos:
        clave = ALIAS.get(e["clave"], e["clave"])
        m = re.match(r"^(.*?) \((\d{4}[a-z]?)\)\. (.*)$", e["cita"])
        autores_txt, anio, resto = m.groups()
        if autores_txt.startswith("J.P. Morgan"):
            apellidos = ["J.P. Morgan", "Reuters"]
        else:
            # "Apellido, I. J., Otro, K. y Último, L."  ->  apellidos
            partes = re.split(r", (?=[A-ZÁÉÍÓÚÑŚ][^,.]*?, )| y ", autores_txt)
            apellidos = [p.split(",")[0].strip() for p in partes]
        archivo = None
        if e.get("archivo"):
            ruta = (BURSATIL / e["carpeta"] / e["archivo"]).resolve()
            archivo = ruta.relative_to(RAIZ).as_posix()
        previa = entradas.get(clave)
        if previa:
            if archivo and archivo not in previa["archivos"]:
                previa["archivos"].append(archivo)
            continue
        entradas[clave] = dict(
            clave=clave, apellidos=apellidos, anio=anio,
            cuerpo=f"{escapar(autores_txt)} ({anio}). {escapar(resto)}",
            enlace=e.get("enlace"), archivos=[archivo] if archivo else [],
            motivo=e.get("no_descargado"), origen="Lado Bursatil",
        )
    return entradas


# ---------------------------------------------------------------- unión (.bib)
def campos_bib(texto):
    """Lee los campos de una entrada BibTeX respetando las llaves anidadas."""
    campos, i = {}, 0
    patron = re.compile(r"(\w+)\s*=\s*")
    while True:
        m = patron.search(texto, i)
        if not m:
            return campos
        j = m.end()
        if texto[j] == "{":
            nivel, k = 0, j
            while True:
                if texto[k] == "{":
                    nivel += 1
                elif texto[k] == "}":
                    nivel -= 1
                    if nivel == 0:
                        break
                k += 1
            valor, i = texto[j + 1:k], k + 1
        else:
            k = re.search(r"[,}\n]", texto[j:]).start() + j
            valor, i = texto[j:k].strip(), k
        campos[m.group(1).lower()] = re.sub(r"\s+", " ", valor).strip()


def iniciales(nombres):
    out = []
    for n in re.split(r"\s+", nombres.strip()):
        if not n:
            continue
        if "-" in n and not n.startswith("{"):
            out.append("-".join(p[0] + "." for p in n.split("-") if p))
        elif re.match(r"^[A-Z]\.$", n):
            out.append(n)
        else:
            m = re.match(r"^(\{\\[^}]*\}|\\.\{?\w\}?|\{?\w)", n)
            out.append(m.group(1).strip("{}") + "." if m else n)
    return " ".join(out)


def autores_bib(campo):
    if campo.startswith("{") and campo.endswith("}"):      # autor institucional
        nombre = campo[1:-1]
        return nombre, [nombre.split(",")[0]]
    personas =[p.strip() for p in re.split(r"\s+and\s+", campo)]
    lista, apellidos, otros = [], [], False
    for p in personas:
        if p == "others":
            otros = True
            continue
        if "," in p:
            ap, nom = [x.strip() for x in p.split(",", 1)]
        else:
            ap, nom = p, ""
        lista.append(f"{ap}, {iniciales(nom)}" if nom else ap)
        apellidos.append(ap)
    texto = autores_apa(lista)
    if otros:
        texto = ", ".join(lista) + " et~al."
        apellidos = apellidos + ["otros"]
    return texto, apellidos


def leer_bib(carpeta):
    entradas = {}
    texto = (carpeta / "referencias_papers.bib").read_text(encoding="utf-8")
    pdfs = sorted(p.name for p in carpeta.glob("*.pdf") if not p.name.startswith("Referencias_"))
    for m in re.finditer(r"@(\w+)\{([^,]+),(.*?)\n\}", texto, re.S):
        tipo, clave, cuerpo = m.group(1).lower(), m.group(2).strip(), m.group(3)
        c = campos_bib(cuerpo)
        autores, apellidos = autores_bib(c["author"])
        titulo = c["title"]
        partes = [f"{autores} ({c['year']}). {titulo}."]
        if tipo == "article":
            ref = r"\emph{" + c["journal"] + "}"
            if c.get("volume"):
                ref += ", " + c["volume"]
            if c.get("number"):
                ref += f"({c['number']})" if c.get("volume") else ", n.º " + c["number"]
            if c.get("pages"):
                ref += ", " + c["pages"]
            partes.append(ref + ".")
        elif tipo == "book":
            partes.append(c.get("publisher", "") + ".")
        elif tipo == "inproceedings":
            ref = "En \\emph{" + c["booktitle"] + "}"
            if c.get("volume"):
                ref += ", vol. " + c["volume"]
            if c.get("pages"):
                ref += ", " + c["pages"]
            partes.append(ref + ".")
        elif tipo == "software":
            partes.append(c.get("publisher", "") + ".")
        else:
            if c.get("howpublished"):
                partes.append(c["howpublished"] + ".")
            if c.get("eprint"):
                partes.append(f"arXiv:{c['eprint']}.")
        if c.get("doi"):
            partes.append(r"\url{https://doi.org/" + c["doi"] + "}")
        elif c.get("url") and not c.get("eprint"):
            partes.append(r"\url{" + c["url"] + "}")
        if not c.get("eprint") and c.get("note", "").startswith("arXiv:"):
            c["eprint"] = c["note"][len("arXiv:"):]
            partes.append(f"arXiv:{c['eprint']}.")
        archivo = ARCHIVOS_MANUALES.get(clave)
        if not archivo and c.get("eprint"):
            archivo = next((p for p in pdfs if c["eprint"] in p), None)
        archivos = [(carpeta / archivo).relative_to(RAIZ).as_posix()] if archivo else []
        entradas[clave] = dict(
            clave=clave, apellidos=[a_unicode(a) for a in apellidos if a != "otros"]
            + (["otros"] if "otros" in apellidos else []),
            anio=c["year"], cuerpo=" ".join(partes), enlace=None, archivos=archivos,
            motivo=None if archivos else NO_DESCARGADO.get(clave, NO_DESCARGADO_POR_DEFECTO),
            origen=carpeta.name,
        )
    usados = {Path(a).name for e in entradas.values() for a in e["archivos"]}
    sueltos = [p for p in pdfs if p not in usados]
    if sueltos:
        sys.exit(f"PDF sin referencia en {carpeta.name}: {sueltos}")
    return entradas


def unir(*catalogos):
    todas = {}
    for cat in catalogos:
        for clave, e in cat.items():
            if clave in todas:
                for a in e["archivos"]:
                    if a not in todas[clave]["archivos"]:
                        todas[clave]["archivos"].append(a)
                continue
            todas[clave] = e
    for x in EXTRAS:
        apellidos = [a.split(",")[0] for a in x["autores"]]
        todas[x["clave"]] = dict(
            clave=x["clave"], apellidos=apellidos, anio=x["anio"],
            cuerpo=f"{autores_apa(x['autores'])} ({x['anio']}). {x['resto']}",
            enlace=None, archivos=[], motivo=x["motivo"], origen="extra")
    return todas


def bibitem(e):
    apellidos = [a for a in e["apellidos"] if a != "otros"]
    if "otros" in e["apellidos"]:
        lab = f"{apellidos[0]} et~al.({e['anio']}){apellidos[0]} et~al."
    else:
        lab = etiqueta(apellidos, e["anio"])
    lineas = [f"\\bibitem[{lab}]{{{e['clave']}}}", e["cuerpo"]]
    if e["archivos"]:
        rutas = "; ".join(f"\\archivo{{{a}}}" for a in e["archivos"])
        lineas.append(f"\\\\\\textit{{Archivo:}} {rutas}")
    else:
        extra = f" \\url{{{e['enlace']}}}" if e.get("enlace") else ""
        lineas.append(f"\\\\\\textit{{No descargado:}} {escapar(e['motivo'])}.{extra}")
    return "\n".join(lineas)


def main():
    todas = unir(leer_bursatil(), leer_bib(UNION / "10_papers_union"),
                 leer_bib(UNION / "11_papers_lado_noticias"))
    orden = sorted(todas.values(), key=lambda e: (sin_acentos(e["apellidos"][0]), e["anio"], e["clave"]))
    # Mismos autores y mismo año: 2022a, 2022b (APA).
    grupos = {}
    for e in orden:
        grupos.setdefault((tuple(e["apellidos"]), e["anio"]), []).append(e)
    for grupo in grupos.values():
        if len(grupo) > 1:
            for letra, e in zip("abcdefgh", grupo):
                e["cuerpo"] = e["cuerpo"].replace(f"({e['anio']})", f"({e['anio']}{letra})", 1)
                e["anio"] += letra
    salida =["% Generado por generar_bibliografia.py — no editar a mano.",
              f"% {len(orden)} referencias; {sum(1 for e in orden if e['archivos'])} con PDF descargado.",
              r"\begin{thebibliography}{999}", ""]
    salida += [bibitem(e) + "\n" for e in orden]
    salida.append(r"\end{thebibliography}")
    (AQUI / "bibliografia.tex").write_text("\n".join(salida), encoding="utf-8")
    (AQUI / "claves_bibliografia.txt").write_text(
        "\n".join(f"{e['clave']}\t{e['apellidos'][0]} ({e['anio']})\t{len(e['archivos'])}" for e in orden),
        encoding="utf-8")
    pdfs = sum(len(e["archivos"]) for e in orden)
    print(f"{len(orden)} referencias, {sum(1 for e in orden if e['archivos'])} con PDF ({pdfs} archivos)")


if __name__ == "__main__":
    main()
