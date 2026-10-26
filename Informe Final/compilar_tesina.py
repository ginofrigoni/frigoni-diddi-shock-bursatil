"""Compila Informe_Final_NicolasDiddi-GinoFrigoni.pdf, la tesina.

1. Copia a figuras/ las figuras que generan las carpetas de la tesis (no las modifica) y genera
   las tres que rehace figuras.py.
2. Verifica que cada cita del texto tenga su referencia en bibliografia.tex.
3. Corre tectonic sobre Informe_Final_NicolasDiddi-GinoFrigoni.tex y verifica los enlaces a
   los papers.

Uso:  python compilar_tesina.py   (desde "Informe Final")
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
TECTONIC = Path.home() / "tools" / "tectonic" / "tectonic.exe"
DOCUMENTO = "Informe_Final_NicolasDiddi-GinoFrigoni"

FIGURAS = [
    "Lado Bursatil/05_volatilidad_ranking/ranking_volatilidad.png",
    "Lado Bursatil/06_hmm_regimen_mercado/bic_curva.png",
    "Lado Bursatil/06_hmm_regimen_mercado/hmm_regimen_mercado.png",
    "Unión/03_sentimiento_por_empresa/u3_cobertura.png",
    "Unión/06_var_granger/u6_irf_mercado.png",
    "Unión/06_var_granger/u6_empresas.png",
    "Unión/09_entrega_final/mapa_tesis.png",
]


def verificar_citas():
    textos = [AQUI / f"{DOCUMENTO}.tex"] + sorted((AQUI / "capitulos").glob("*.tex"))
    citadas = set()
    for f in textos:
        texto = re.sub(r"(?<!\\)%.*", "", f.read_text(encoding="utf-8"))
        for grupo in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", texto):
            citadas.update(c.strip() for c in grupo.split(","))
    bibliografia = (AQUI / "bibliografia.tex").read_text(encoding="utf-8")
    claves = set(re.findall(r"\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}", bibliografia))
    if citadas - claves:
        sys.exit(f"Citas sin referencia en bibliografia.tex: {sorted(citadas - claves)}")
    print(f"{len(citadas)} citas, todas con su referencia")


def main():
    destino = AQUI / "figuras"
    destino.mkdir(exist_ok=True)
    for f in FIGURAS:
        shutil.copy2(RAIZ / f, destino / Path(f).name)
    print(f"{len(FIGURAS)} figuras copiadas")
    subprocess.run([sys.executable, str(AQUI / "figuras.py")], check=True)
    verificar_citas()
    subprocess.run([str(TECTONIC), f"{DOCUMENTO}.tex"], cwd=AQUI, check=True)
    arreglar_enlaces(AQUI / f"{DOCUMENTO}.pdf")


def arreglar_enlaces(pdf):
    """hyperref guarda la ruta de los enlaces a archivos (acción Launch) como bytes UTF-8,
    que los lectores de PDF en Windows leen mal ("UniÃ³n"). Cada enlace se reescribe como una
    especificación de archivo con la ruta también en UTF-16 (/UF), y se verifica que el
    archivo exista."""
    import pymupdf
    from urllib.parse import unquote

    doc = pymupdf.open(pdf)
    total, faltan = 0, []
    for pagina in doc:
        for enlace in pagina.get_links():
            if not enlace.get("file") or "/Launch" not in doc.xref_object(enlace["xref"]):
                continue
            ruta = unquote(enlace["file"])
            total += 1
            if not (AQUI / ruta).resolve().exists():
                faltan.append(ruta)
            f = ruta.encode("cp1252").hex()
            uf = "FEFF" + ruta.encode("utf-16-be").hex()
            doc.xref_set_key(enlace["xref"], "A/F", f"<</Type/Filespec/F<{f}>/UF<{uf}>>>")
    if faltan:
        sys.exit(f"Enlaces a archivos que no existen: {sorted(set(faltan))}")
    temporal = pdf.with_suffix(".tmp.pdf")
    doc.save(temporal, garbage=3, deflate=True)
    doc.close()
    temporal.replace(pdf)
    print(f"{total} enlaces a archivos verificados")


if __name__ == "__main__":
    main()
