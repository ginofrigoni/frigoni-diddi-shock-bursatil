"""Arma las tablas largas de los anexos leyendo los CSV de la tesis (no los modifica).

Salida en tablas/:
  panel_acciones.tex     las 47 acciones: sector, liquidez, volatilidad y noticias
  diccionario.tex        el diccionario de variables de los dos datasets (U4)
  granger_propio.tex     Granger con el tono propio de las 17 empresas (U6)
  granger_empresas.tex   Granger de las 47 empresas con el tono del mercado (U6)

Uso:  python generar_tablas.py   (desde "Informe Final")
"""
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
BURSATIL = RAIZ / "Lado Bursatil"
UNION = RAIZ / "Unión"
SALIDA = AQUI / "tablas"

ESPECIALES = str.maketrans({"&": r"\&", "%": r"\%", "#": r"\#", "_": r"\_", "^": r"\^{}",
                            "→": r"$\rightarrow$", "−": "$-$", "×": r"$\times$", "≥": r"$\geq$"})


def tex(valor):
    return str(valor).translate(ESPECIALES)


def coma(x, dec=1):
    return f"{x:.{dec}f}".replace(".", ",")


def p_txt(p):
    return "$<$0,0001" if p < 0.0001 else coma(p, 4)


def panel_acciones():
    panel = pd.read_csv(BURSATIL / "01_scraping_acciones" / "panel_acciones_final.csv")
    vol = pd.read_csv(BURSATIL / "05_volatilidad_ranking" / "ranking_volatilidad.csv")
    cob = pd.read_csv(UNION / "03_sentimiento_por_empresa" / "cobertura_empresas.csv")
    df = (panel.merge(vol[["ticker", "vol_prom"]].rename(columns={"vol_prom": "volat"}), on="ticker")
          .merge(cob[["ticker", "ruedas_con_noticias", "sentimiento_propio"]], on="ticker", how="left"))
    assert len(df) == 47
    df = df.sort_values(["sector", "ticker"])
    filas = []
    for r in df.itertuples():
        filas.append(" & ".join([
            tex(r.ticker.replace(".BA", "")), tex(r.empresa), tex(r.sector),
            "Sí" if r.oficial else "No", coma(r.pct_dias_con_volumen), coma(r.volat),
            str(int(r.ruedas_con_noticias)), "Sí" if r.sentimiento_propio else "No"]) + r" \\")
    return "\n".join(filas)


def ruta_cortable(texto):
    """Las palabras con '/' (rutas) van en \\nolinkurl, que puede cortarlas en / y _."""
    return " ".join(r"\nolinkurl{" + p + "}" if "/" in p else tex(p) for p in str(texto).split(" "))


def diccionario():
    d = pd.read_csv(UNION / "04_dataset_unificado" / "diccionario_variables.csv")
    filas = [" & ".join([r"\nolinkurl{" + r.variable + "}", tex(r.dataset), tex(r.descripcion),
                         tex(r.unidad), ruta_cortable(r.origen)]) + r" \\" for r in d.itertuples()]
    return "\n".join(filas), len(d)


def granger(nivel, pruebas):
    g = pd.read_csv(UNION / "06_var_granger" / "granger_resultados.csv")
    g = g[g.nivel == nivel]
    filas = []
    for unidad, sub in g.groupby("unidad"):
        celdas = [tex(unidad.replace(".BA", "")), str(int(sub.rezagos.iloc[0]))]
        for prueba in pruebas:
            r = sub[sub.prueba == prueba].iloc[0]
            marca = r"$^{\bullet}$" if r.signif_bh else (r"$^{\circ}$" if r.signif_sin_corregir else "")
            celdas.append(f"{p_txt(r.p_bh)}{marca}")
        filas.append(" & ".join(celdas) + r" \\")
    return "\n".join(filas), g


def main():
    SALIDA.mkdir(exist_ok=True)
    (SALIDA / "panel_acciones.tex").write_text(panel_acciones(), encoding="utf-8")
    filas, n = diccionario()
    (SALIDA / "diccionario.tex").write_text(filas, encoding="utf-8")
    pruebas_propio = ["tono propio → retorno", "tono propio → volumen", "retorno → tono propio",
                      "volumen → tono propio"]
    filas_p, gp = granger("propio", pruebas_propio)
    (SALIDA / "granger_propio.tex").write_text(filas_p, encoding="utf-8")
    pruebas_emp = ["tono → retorno", "tono → volumen", "retorno → tono", "volumen → tono"]
    filas_e, ge = granger("empresa", pruebas_emp)
    (SALIDA / "granger_empresas.tex").write_text(filas_e, encoding="utf-8")
    assert sorted(gp.prueba.unique()) == sorted(pruebas_propio), gp.prueba.unique()
    assert sorted(ge.prueba.unique()) == sorted(pruebas_emp), ge.prueba.unique()
    print(f"Tablas: 47 acciones, {n} variables, {gp.unidad.nunique()} empresas con tono propio, "
          f"{ge.unidad.nunique()} empresas")


if __name__ == "__main__":
    main()
