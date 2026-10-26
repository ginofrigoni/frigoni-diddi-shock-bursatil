# -*- coding: utf-8 -*-
"""
Fase 1 de la correccion del conjunto etiquetado: limpieza de dataset_etiquetado/checkpoint.jsonl.

No modifica el original. Escribe:
  dataset_etiquetado/checkpoint_limpio.jsonl        etiquetas utilizables (una fila por texto)
  dataset_etiquetado/limpieza_filas_eliminadas.csv  cada fila descartada y su motivo
  dataset_etiquetado/limpieza_reporte.json          conteos

Antes de aplicar las reglas se agrega la columna `oracion_limpia`: la oracion sin las marcas de relleno
que el scraping dejo pegadas (MARCAS_RELLENO: "PUBLICIDAD", "Sobre la firma", "Mira tambien",
"Newsletter Clarin", "Tags relacionados", promocion de la cobertura de Clarin). En Infobae, por ejemplo,
muchas oraciones reales empiezan con "PUBLICIDAD ...". Las reglas comparan textos por `oracion_limpia`;
la columna `oracion` original se conserva.

Reglas, en este orden:
  1. relleno                  la fila tenia marcas de relleno y, al quitarlas, no queda una oracion
                              (menos de MIN_LETRAS letras): "PUBLICIDAD PUBLICIDAD PUBLICIDAD", "Sobre la
                              firma Newsletter Clarin", etc. Las oraciones cortas sin marcas (items de
                              listas con cifras, por ejemplo) se conservan.
  2. reproceso_conflicto      la misma oracion (url + posicion) etiquetada mas de una vez con etiquetas
                              distintas: se descartan todas las copias.
  3. reproceso_mismo_label    la misma oracion etiquetada mas de una vez con la misma etiqueta: se
                              conserva una copia.
  4. texto_repetido_conflicto el mismo texto en noticias distintas con etiquetas distintas: se
                              descartan todas las copias.
  5. texto_repetido           el mismo texto en noticias distintas (parrafos fijos de los sitios) con la
                              misma etiqueta: se conserva la primera aparicion (fecha, url, posicion).

Uso (desde sentimiento_finbert/):  python limpiar_etiquetado.py
"""

import json
import os
import re
import sys

import pandas as pd

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

AQUI = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(AQUI, "dataset_etiquetado")

MARCAS_RELLENO = [
    r"\bPUBLICIDAD\b",
    r"Sobre la firma",
    r"Mir[aá] tambi[eé]n",
    r"Newsletter Clar[ií]n",
    r"Tags relacionados",
    r"Segu[ií] las cotizaciones en esta cobertura minuto a minuto de Clar[ií]n\.?",
]
RX = re.compile("|".join(MARCAS_RELLENO))
MIN_LETRAS = 20


def limpiar(texto):
    return re.sub(r"\s+", " ", RX.sub(" ", texto)).strip()


def main():
    filas = [json.loads(l) for l in open(os.path.join(D, "checkpoint.jsonl"), encoding="utf-8") if l.strip()]
    original = pd.DataFrame(filas)
    df = original.copy()
    df["fila"] = range(len(df))
    df["or_idx"] = df["or_idx"].astype(int)
    df["oracion_limpia"] = df["oracion"].map(limpiar)
    con_marca = int((df["oracion_limpia"] != df["oracion"].str.strip()).sum())
    fuera = []

    def descartar(mask, motivo):
        nonlocal df
        x = df[mask].copy()
        x["motivo"] = motivo
        fuera.append(x)
        df = df[~mask]

    # 1. relleno
    letras = df["oracion_limpia"].str.count(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]")
    tenia_marca = df["oracion_limpia"] != df["oracion"].str.strip()
    descartar(tenia_marca & (letras < MIN_LETRAS), "relleno")

    # 2 y 3. misma oracion (url + posicion) etiquetada mas de una vez
    n_lab = df.groupby(["url", "or_idx"])["label"].transform("nunique")
    descartar(n_lab > 1, "reproceso_conflicto")
    df = df.sort_values("fila")
    descartar(df.duplicated(["url", "or_idx"], keep="first"), "reproceso_mismo_label")

    # 4 y 5. mismo texto (limpio) en noticias distintas
    n_lab = df.groupby("oracion_limpia")["label"].transform("nunique")
    descartar(n_lab > 1, "texto_repetido_conflicto")
    df = df.sort_values(["fecha", "url", "or_idx"])
    descartar(df.duplicated("oracion_limpia", keep="first"), "texto_repetido")

    df = df.sort_values("fila")
    with open(os.path.join(D, "checkpoint_limpio.jsonl"), "w", encoding="utf-8") as f:
        for r in df.drop(columns=["fila"]).to_dict("records"):
            r["or_idx"] = str(r["or_idx"])
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    E = pd.concat(fuera)
    E[["motivo", "fila", "url", "fuente", "or_idx", "label", "oracion", "oracion_limpia"]].sort_values(
        ["motivo", "fila"]).to_csv(os.path.join(D, "limpieza_filas_eliminadas.csv"), index=False, encoding="utf-8")

    rep = {
        "filas_originales": int(len(original)),
        "filas_eliminadas": int(len(E)),
        "filas_limpias": int(len(df)),
        "eliminadas_por_motivo": E["motivo"].value_counts().to_dict(),
        "eliminadas_por_motivo_y_clase": {m: g["label"].value_counts().to_dict() for m, g in E.groupby("motivo")},
        "noticias_originales": int(original["url"].nunique()),
        "noticias_limpias": int(df["url"].nunique()),
        "clases_originales": original["label"].value_counts().to_dict(),
        "clases_limpias": df["label"].value_counts().to_dict(),
        "filas_con_marcas_de_relleno_quitadas": con_marca,
        "textos_repetidos_en_limpio": int(df["oracion_limpia"].duplicated().sum()),
        "marcas_relleno": MARCAS_RELLENO,
        "min_letras": MIN_LETRAS,
    }
    with open(os.path.join(D, "limpieza_reporte.json"), "w", encoding="utf-8") as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print(json.dumps(rep, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
