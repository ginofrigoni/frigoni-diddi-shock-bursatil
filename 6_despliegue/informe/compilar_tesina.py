"""Compila Informe_Final_NicolasDiddi-GinoFrigoni.pdf, la tesina (versión 6.0).

1. numeros.py: genera generado/numeros.tex y generado/tablas/ desde los resultados del proyecto.
2. Copia a figuras/ las figuras que generan las carpetas del proyecto (no las modifica) y corre
   figuras.py, que hace la figura del pipeline con las fases de CRISP-DM.
3. Verifica que cada cita del texto tenga su referencia en bibliografia.tex.
4. Corre tectonic y revisa los enlaces a los papers (avisa si falta alguno, sin cortar).

Uso:  python compilar_tesina.py   (desde 6_despliegue/informe)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
TECTONIC = Path.home() / "tools" / "tectonic" / "tectonic.exe"
DOCUMENTO = "Informe_Final_NicolasDiddi-GinoFrigoni"

FIGURAS = [
    "3_preparacion_de_los_datos/regla_17/salidas/regla_17.png",
    "3_preparacion_de_los_datos/sentimiento_por_rueda/salidas/sentimiento_por_rueda.png",
    "3_preparacion_de_los_datos/sentimiento_por_empresa/salidas/cobertura_empresas.png",
    "3_preparacion_de_los_datos/vix_argentino/salidas/vix_arg.png",
    "3_preparacion_de_los_datos/dataset_unificado/salidas/panorama.png",
    "4_modelado/noticias_a_precio/salidas/noticias_a_precio.png",
    "4_modelado/precio_a_sentimiento/salidas/precio_a_sentimiento.png",
    "5_evaluacion/anexo/salidas/robustez.png",
    "5_evaluacion/anexo/salidas/var_granger.png",
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
    print(f"{len(citadas)} citas, todas con su referencia; {len(claves - citadas)} referencias sin citar: {sorted(claves - citadas)}")


def main():
    subprocess.run([sys.executable, str(AQUI / "numeros.py")], check=True)
    destino = AQUI / "figuras"
    destino.mkdir(exist_ok=True)
    for f in FIGURAS:
        shutil.copy2(RAIZ / f, destino / Path(f).name)
    print(f"{len(FIGURAS)} figuras copiadas")
    subprocess.run([sys.executable, str(AQUI / "figuras.py")], check=True)
    verificar_citas()
    subprocess.run([str(TECTONIC), "--keep-logs", f"{DOCUMENTO}.tex"], cwd=AQUI, check=True)
    arreglar_enlaces(AQUI / f"{DOCUMENTO}.pdf")


def arreglar_enlaces(pdf):
    """hyperref guarda la ruta de los enlaces a archivos (acción Launch) como bytes UTF-8,
    que los lectores de PDF en Windows leen mal. Cada enlace se reescribe como una especificación
    de archivo con la ruta también en UTF-16 (/UF). Avisa si algún archivo no existe."""
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
            f = ruta.encode("cp1252", errors="replace").hex()
            uf = "FEFF" + ruta.encode("utf-16-be").hex()
            doc.xref_set_key(enlace["xref"], "A/F", f"<</Type/Filespec/F<{f}>/UF<{uf}>>>")
    temporal = pdf.with_suffix(".tmp.pdf")
    doc.save(temporal, garbage=3, deflate=True)
    doc.close()
    temporal.replace(pdf)
    print(f"{total} enlaces a archivos; {len(set(faltan))} apuntan a papers que todavía no están en la 6.0")


if __name__ == "__main__":
    main()
