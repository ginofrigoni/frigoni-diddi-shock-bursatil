"""Compila Tesina_Reducida.pdf (la versión reducida de la tesina).

1. Copia a figuras/ las figuras de la versión completa y las que suma la reducida, y genera
   las tres que la reducida rehace (figuras_reducida.py).
2. Arma bibliografia_reducida.tex con solo las referencias que cita la versión reducida,
   tomadas tal cual de bibliografia.tex (que arma generar_bibliografia.py para la versión
   completa y no se modifica).
3. Corre tectonic sobre Tesina_Reducida.tex y verifica los enlaces a los papers.

Uso:  python compilar_reducida.py   (desde "Informe Final")
"""
import re
import shutil
import subprocess
import sys

from compilar_tesina import AQUI, FIGURAS, RAIZ, TECTONIC, arreglar_enlaces

FIGURAS_EXTRA = [
    "Lado Bursatil/06_hmm_regimen_mercado/bic_curva.png",
]


def claves_citadas():
    textos = [AQUI / "Tesina_Reducida.tex"] + sorted((AQUI / "capitulos_reducida").glob("*.tex"))
    claves = set()
    for f in textos:
        texto = re.sub(r"(?<!\\)%.*", "", f.read_text(encoding="utf-8"))
        for grupo in re.findall(r"\\cite[tp]?\*?(?:\[[^\]]*\])*\{([^}]+)\}", texto):
            claves.update(c.strip() for c in grupo.split(","))
    return claves


def armar_bibliografia():
    completa = (AQUI / "bibliografia.tex").read_text(encoding="utf-8")
    entradas = re.findall(r"(\\bibitem(?:\[[^\]]*\])?\{([^}]+)\}.*?)(?=\n\\bibitem|\n\\end\{thebibliography\})",
                          completa, flags=re.S)
    citadas = claves_citadas()
    elegidas = [texto.strip() for texto, clave in entradas if clave in citadas]
    faltan = citadas - {clave for _, clave in entradas}
    if faltan:
        raise SystemExit(f"Citas sin referencia en bibliografia.tex: {sorted(faltan)}")
    con_pdf = sum("\\archivo{" in e for e in elegidas)
    salida = ["% Generado por compilar_reducida.py a partir de bibliografia.tex — no editar a mano.",
              f"% {len(elegidas)} referencias; {con_pdf} con PDF descargado.",
              "\\begin{thebibliography}{999}", ""]
    for e in elegidas:
        salida += [e, ""]
    salida.append("\\end{thebibliography}")
    (AQUI / "bibliografia_reducida.tex").write_text("\n".join(salida) + "\n", encoding="utf-8")
    print(f"{len(elegidas)} referencias en bibliografia_reducida.tex")


def main():
    destino = AQUI / "figuras"
    destino.mkdir(exist_ok=True)
    for f in FIGURAS + FIGURAS_EXTRA:
        shutil.copy2(RAIZ / f, destino / f.rsplit("/", 1)[-1])
    print(f"{len(FIGURAS) + len(FIGURAS_EXTRA)} figuras copiadas")
    subprocess.run([sys.executable, str(AQUI / "figuras_reducida.py")], check=True)
    armar_bibliografia()
    subprocess.run([str(TECTONIC), "Tesina_Reducida.tex"], cwd=AQUI, check=True)
    arreglar_enlaces(AQUI / "Tesina_Reducida.pdf")


if __name__ == "__main__":
    main()
