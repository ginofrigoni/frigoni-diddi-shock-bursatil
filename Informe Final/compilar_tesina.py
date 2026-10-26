"""Compila Tesina_Final.pdf desde cero.

1. Copia a figuras/ las figuras que generan las carpetas de la tesis (no las modifica).
2. Arma bibliografia.tex (generar_bibliografia.py) y las tablas de los anexos (generar_tablas.py).
3. Corre tectonic sobre Tesina_Final.tex.

Uso:  python compilar_tesina.py   (desde "Informe Final")
"""
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
TECTONIC = Path.home() / "tools" / "tectonic" / "tectonic.exe"

FIGURAS = [
    "Lado Bursatil/03_vix_argentino/vix_arg.png",
    "Lado Bursatil/05_volatilidad_ranking/ranking_volatilidad.png",
    "Lado Bursatil/06_hmm_regimen_mercado/hmm_regimen_mercado.png",
    "Unión/01_alineacion_noticias_ruedas/u1_alineacion.png",
    "Unión/02_sentimiento_por_rueda/u2_serie.png",
    "Unión/03_sentimiento_por_empresa/u3_cobertura.png",
    "Unión/04_dataset_unificado/u4_panorama.png",
    "Unión/06_var_granger/u6_irf_mercado.png",
    "Unión/06_var_granger/u6_empresas.png",
    "Unión/06b_noticias_preapertura/u6b_preapertura.png",
    "Unión/07_event_study/u7_mercado.png",
    "Unión/07_event_study/u7_empresa.png",
    "Unión/07b_shock_volumen_noticias/u7b_shock_volumen.png",
    "Unión/08_robustez/u8_robustez.png",
    "Unión/09_entrega_final/mapa_tesis.png",
]


def main():
    destino = AQUI / "figuras"
    destino.mkdir(exist_ok=True)
    for f in FIGURAS:
        shutil.copy2(RAIZ / f, destino / Path(f).name)
    print(f"{len(FIGURAS)} figuras copiadas")
    for script in ("generar_bibliografia.py", "generar_tablas.py"):
        subprocess.run([sys.executable, str(AQUI / script)], check=True)
    subprocess.run([str(TECTONIC), "Tesina_Final.tex"], cwd=AQUI, check=True)
    arreglar_enlaces(AQUI / "Tesina_Final.pdf")


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
