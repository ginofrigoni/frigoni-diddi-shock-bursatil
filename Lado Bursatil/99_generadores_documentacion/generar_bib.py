"""
Genera papers/referencias.bib en cada carpeta de tesis version 3.0, a partir
del catálogo único referencias.json (el mismo que usan los PDF).

Uso:  python generar_bib.py
"""
import json
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
REFS = json.load(open(os.path.join(AQUI, "referencias.json"), encoding="utf-8"))

# Títulos que contienen un punto propio (la regla general corta en el primer ". ")
TITULO_CON_PUNTO = {"caballero2016": 2}


def partes(r):
    m = re.match(r"(.+?) \((\d{4})\)\. (.+)", r["cita"])
    autores_txt, anio, resto = m.group(1), m.group(2), m.group(3)
    autores = re.findall(r"([^,]+?, [^,]+?\.)(?:, | y |$)", autores_txt.replace(" y ", ", "))
    n = TITULO_CON_PUNTO.get(r["clave"], 1)
    trozos = resto.split(". ")
    titulo = ". ".join(trozos[:n])
    publicado = ". ".join(trozos[n:]).rstrip(".")
    autores = [a.strip() for a in autores] or ["{" + autores_txt + "}"]   # autor institucional (ej. J.P. Morgan y Reuters)
    return autores, anio, titulo, publicado


def bib(r):
    autores, anio, titulo, publicado = partes(r)
    campos = {
        "author": " and ".join(autores),
        "title": "{" + titulo + "}",
        "year": anio,
        "howpublished": publicado,
        "url": r["enlace"],
        "note": ("Archivo local: " + r["archivo"]) if r["archivo"] else ("No descargado: " + r["no_descargado"]),
        "language": r["idioma"],
    }
    cuerpo = ",\n".join(f"  {k} = {{{v}}}" for k, v in campos.items() if v)
    return f"@misc{{{r['clave']},\n{cuerpo}\n}}\n"


if __name__ == "__main__":
    por_carpeta = {}
    for r in REFS:
        por_carpeta.setdefault(r["carpeta"], []).append(r)
    for carpeta, refs in por_carpeta.items():
        destino = os.path.join(RAIZ, carpeta, "papers", "referencias.bib")
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        with open(destino, "w", encoding="utf-8") as f:
            f.write(f"% Referencias de {carpeta} — generado por 99_generadores_documentacion/generar_bib.py\n\n")
            f.write("\n".join(bib(r) for r in refs))
        print(f"Guardado: {destino}  ({len(refs)} referencias)")
