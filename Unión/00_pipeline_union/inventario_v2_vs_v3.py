"""
Inventario: qué pasó de "tesis version 2.0" a "tesis version 3.0" — tesis version 3.0

Recorre TODOS los archivos de la 2.0 (sin entornos virtuales ni cachés) y le asigna a cada uno:
  grupo        tema al que pertenece (para organizar)
  estado       Pasó / Reemplazado en 3.0 / Rehacer en la unión / No pasó
  en_3_0       dónde está (o qué lo reemplaza) en la 3.0
  hace_falta   Sí / Para la tesis / No — si hay que traerlo
  responsable  Nicolás / Gino / Ambos
Las carpetas de pesos del modelo (beto_finetuned, beto_further_pretrained) cuentan como una fila cada una.

Solo lee. Escribe en esta carpeta:  inventario_v2_vs_v3.csv
Uso:  python inventario_v2_vs_v3.py
"""

import os
from pathlib import Path

import pandas as pd

AQUI = Path(__file__).parent
V2 = AQUI.parent.parent.parent / "tesis version 2.0"
V3 = AQUI.parent.parent
OMITIR = {".venv", "node_modules", "__pycache__", ".git", ".ipynb_checkpoints"}
CARPETAS_MODELO = ("beto_finetuned", "beto_further_pretrained")

PP = "pipeline_productivo/"
AC = "analisis_complementarios/"
NOT = PP + "02_data_understanding/noticias/"
FIN = PP + "04_modeling/sentimiento_finbert/"

# (prefijo de ruta, grupo, estado, en_3_0, hace_falta, responsable). Gana la primera regla que coincide.
REGLAS = [
    # ── README de la estructura vieja: cada carpeta 3.0 tiene el suyo ──
    ("README.md", "J. Estructura vieja (README)", "Reemplazado en 3.0", "Cada carpeta 3.0 tiene su propio README o PDF", "No", "Ambos"),
    ("*/README.md", "J. Estructura vieja (README)", "Reemplazado en 3.0", "Cada carpeta 3.0 tiene su propio README o PDF", "No", "Ambos"),

    # ── A. Modelo de sentimiento (Gino) ──
    (FIN + "beto_finetuned/", "A. Modelo de sentimiento", "No pasó", "—", "Solo para analizar noticias nuevas", "Gino"),
    (FIN + "beto_further_pretrained/", "A. Modelo de sentimiento", "No pasó", "—", "No (paso intermedio del entrenamiento)", "Gino"),
    (FIN + "01_further_pretraining.ipynb", "A. Modelo de sentimiento", "No pasó", "—", "Para la tesis (cómo se entrenó)", "Gino"),
    (FIN + "03_finetuning.ipynb", "A. Modelo de sentimiento", "No pasó", "—", "Para la tesis (cómo se entrenó)", "Gino"),
    (FIN, "A. Modelo de sentimiento", "Pasó", "Lado Noticias/sentimiento_finbert/ (actualizado)", "—", "Gino"),
    (PP + "03_data_preparation/sentimiento/construir_sentimiento_empresa.py", "B. Sentimiento por empresa (versión vieja)", "Reemplazado en 3.0",
     "Lado Noticias/ner_entidades/ (47 empresas, por oración)", "No", "Gino"),
    (PP + "03_data_preparation/sentimiento/", "A. Modelo de sentimiento", "No pasó", "—", "Para la tesis (de dónde salieron las etiquetas)", "Gino"),
    (AC + "finetuning_evaluacion/beto_oraciones_finetuned.csv", "A. Modelo de sentimiento", "No pasó", "—", "Sí (paso U3 de la unión)", "Gino"),
    (AC + "finetuning_evaluacion/", "A. Modelo de sentimiento", "No pasó", "—", "Para la tesis (métricas del modelo)", "Gino"),
    (AC + "baseline_beto_sin_finetuning/", "A. Modelo de sentimiento", "No pasó", "—", "Para la tesis (comparación sin ajuste)", "Gino"),

    # ── B/C. Corpus y NER (Gino) ──
    (NOT + "resultados/*.png", "C. Corpus de noticias", "No pasó", "—", "No (imágenes de formas geométricas sin uso; parecen de otro trabajo)", "Gino"),
    (NOT + "resultados/","C. Corpus de noticias", "Pasó", "Lado Noticias/noticias/resultados/ (depurado)", "—", "Gino"),
    (NOT + "scraping_noticias/noticias_historico.py", "C. Corpus de noticias", "No pasó", "—", "No (versión obsoleta, reemplazada por v3)", "Gino"),
    (NOT + "scraping_noticias/noticias_historico_v2.py", "C. Corpus de noticias", "No pasó", "—", "No (versión obsoleta, reemplazada por v3)", "Gino"),
    (NOT + "scraping_noticias/", "C. Corpus de noticias", "Pasó", "Lado Noticias/noticias/scripts/ (actualizado)", "—", "Gino"),
    (AC + "ner_entidades/", "D. NER (entidades)", "Pasó", "Lado Noticias/ner_entidades/ (rehecho, 47 empresas)", "—", "Gino"),
    (PP + "03_data_preparation/construccion_dataset/sentimiento_por_empresa.csv", "B. Sentimiento por empresa (versión vieja)", "Reemplazado en 3.0",
     "Lado Noticias/ner_entidades/resultados_ner/ner_sentimiento_diario.csv", "No", "Gino"),

    # ── E. Lado bursátil (Nicolás) ──
    (PP + "02_data_understanding/bursatil/descargar_merval.py", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/01_scraping_acciones/scraping_acciones.py", "No", "Nicolás"),
    (PP + "02_data_understanding/bursatil/merval_precios.csv", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/01_scraping_acciones/precios_diarios_47_acciones.csv", "No", "Nicolás"),
    (PP + "02_data_understanding/bursatil/merval_resumen.csv", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/01_scraping_acciones/panel_acciones_final.csv", "No", "Nicolás"),
    (PP + "02_data_understanding/bursatil/", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/03_vix_argentino/", "No", "Nicolás"),
    (PP + "04_modeling/hmm_regimen_mercado/", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/06_hmm_regimen_mercado/", "No", "Nicolás"),
    (AC + "clustering_acciones/", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/02_clustering_acciones/", "No", "Nicolás"),
    (AC + "volatilidad_ranking/adf_", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/04_adf/", "No", "Nicolás"),
    (AC + "volatilidad_ranking/merval_precios.csv", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/01_scraping_acciones/ (copia repetida)", "No", "Nicolás"),
    (AC + "volatilidad_ranking/vix_arg.csv", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/03_vix_argentino/ (copia repetida)", "No", "Nicolás"),
    (AC + "volatilidad_ranking/", "E. Lado bursátil", "Reemplazado en 3.0", "Lado Bursatil/05_volatilidad_ranking/", "No", "Nicolás"),
    (AC + "hmm_sectores_acciones/merval_precios.csv", "F. HMM por sector y por acción", "No pasó", "—", "No (copia repetida de precios)", "Nicolás"),
    (AC + "hmm_sectores_acciones/vix_arg.csv", "F. HMM por sector y por acción", "No pasó", "—", "No (copia repetida del VIX)", "Nicolás"),
    (AC + "hmm_sectores_acciones/", "F. HMM por sector y por acción", "No pasó", "—", "Decidir: dejar afuera o rehacer", "Nicolás"),

    # ── G. Unión de la versión anterior ──
    (PP + "03_data_preparation/construccion_dataset/", "G. Unión de la versión anterior", "Rehacer en la unión", "Unión — paso U4 (datasets)", "No (se rehace con las reglas nuevas)", "Ambos"),
    (PP + "04_modeling/var_econometria/script5_event_study.py", "G. Unión de la versión anterior", "Rehacer en la unión", "Unión — paso U7 (event study)", "Como referencia", "Ambos"),
    (PP + "04_modeling/var_econometria/script1_adf.py", "G. Unión de la versión anterior", "Rehacer en la unión", "Unión — paso U5 (ADF)", "Como referencia", "Ambos"),
    (PP + "04_modeling/var_econometria/script", "G. Unión de la versión anterior", "Rehacer en la unión", "Unión — paso U6 (VAR, Granger, IRF)", "Como referencia", "Ambos"),
    (PP + "04_modeling/var_econometria/resultados/", "G. Unión de la versión anterior", "Rehacer en la unión", "Unión — pasos U5 a U7", "No (resultados viejos)", "Ambos"),
    (PP + "05_evaluation/", "G. Unión de la versión anterior", "Rehacer en la unión", "Unión — pasos U2 y U9 (gráficos de shocks)", "Como referencia", "Ambos"),

    # ── H. Plan y documentación ──
    (PP + "01_business_understanding/~$", "H. Plan y documentación", "No pasó", "—", "No (archivo de bloqueo de Word)", "Ambos"),
    (PP + "01_business_understanding/plan_de_trabajo_v2.pdf", "H. Plan y documentación", "No pasó", "—", "Sí (objetivos de la tesis; corregir apellido \"Didi\")", "Ambos"),
    (PP + "01_business_understanding/resumen_metodologico.docx", "H. Plan y documentación", "No pasó", "—", "Revisar (dice \"etiquetado manual\": fue Gemma)", "Ambos"),
    (PP + "01_business_understanding/diccionario_variables.docx", "H. Plan y documentación", "No pasó", "—", "Sí (rehacer con las variables de la unión)", "Ambos"),
    (PP + "01_business_understanding/notas.txt", "H. Plan y documentación", "No pasó", "—", "Como referencia (ideas iniciales)", "Ambos"),
    (PP + "01_business_understanding/", "H. Plan y documentación", "No pasó", "—", "Como referencia (tesis de ejemplo de otros autores)", "Ambos"),
    ("00_documentacion/Documentacion_Detallada_Lado_Bursatil", "H. Plan y documentación", "Reemplazado en 3.0", "Lado Bursatil/ (un PDF por carpeta)", "No", "Nicolás"),
    ("00_documentacion/Mapa_Pipeline_Tesina.docx", "H. Plan y documentación", "Reemplazado en 3.0", "Lado Bursatil/00_mapa_lado_bursatil/ + Unión/00_pipeline_union/", "No", "Ambos"),
    ("00_documentacion/MAPA_PIPELINE.md", "H. Plan y documentación", "Reemplazado en 3.0", "Lado Bursatil/00_mapa_lado_bursatil/ + Unión/00_pipeline_union/", "No", "Ambos"),
    ("00_documentacion/MEMORIA.md", "H. Plan y documentación", "No pasó", "—", "No (desactualizada)", "Ambos"),
    ("00_documentacion/InformeFinal-GaunaPasinato.pdf", "H. Plan y documentación", "No pasó", "—", "Como referencia (tesis de ejemplo de otros autores)", "Ambos"),
    ("00_documentacion/", "H. Plan y documentación", "No pasó", "—", "Como referencia", "Ambos"),

    # ── I. Presentación e infografías ──
    (PP + "06_deployment/", "I. Presentación de avance e infografías", "No pasó", "—", "Para la presentación final (rehacer con resultados nuevos)", "Ambos"),
    ("00_infografias/", "I. Presentación de avance e infografías", "No pasó", "—", "Rehacer con resultados nuevos (R05 cuenta mal las empresas)", "Ambos"),

    # ── K. Bibliografía ──
    ("00_bibliografia/conversacion chat gpt.pdf", "K. Bibliografía general", "No pasó", "—", "No (no es una fuente citable)", "Ambos"),
    ("00_bibliografia/Clasificación temporal del dengue", "K. Bibliografía general", "No pasó", "—", "Revisar (tema dengue: ¿antecedente metodológico?)", "Ambos"),
    ("00_bibliografia/Tendencias sociales", "K. Bibliografía general", "No pasó", "—", "Revisar (tema dengue: ¿antecedente metodológico?)", "Ambos"),
    ("00_bibliografia/Procesamiento del Lenguaje Natural", "K. Bibliografía general", "No pasó", "—", "Revisar (artículo de Medium, no académico)", "Ambos"),
    ("00_bibliografia/", "K. Bibliografía general", "No pasó", "—", "Sí (papers de noticias y bolsa para la unión)", "Ambos"),
]


def clasificar(rel):
    for prefijo, *resto in REGLAS:
        if prefijo == "*/README.md":
            if rel.endswith("/README.md"):
                return resto
        elif prefijo.endswith("*.png"):
            if rel.startswith(prefijo[:-5]) and rel.endswith(".png"):
                return resto
        elif rel.startswith(prefijo):
            return resto
    return ["SIN CLASIFICAR", "?", "?", "?", "?"]


def recorrer(raiz):
    for d, ds, fs in os.walk(raiz):
        ds[:] = [x for x in ds if x not in OMITIR]
        for f in fs:
            yield Path(d) / f


filas, modelos_vistos = [], {}
for p in sorted(recorrer(V2)):
    rel = p.relative_to(V2).as_posix()
    carpeta_modelo = next((m for m in CARPETAS_MODELO if f"/{m}/" in f"/{rel}"), None)
    if carpeta_modelo:
        clave = rel.split(carpeta_modelo)[0] + carpeta_modelo + "/"
        modelos_vistos.setdefault(clave, [0, 0])
        modelos_vistos[clave][0] += 1
        modelos_vistos[clave][1] += p.stat().st_size
        continue
    filas.append([rel, p.stat().st_size, *clasificar(rel)])
for clave, (n, tam) in modelos_vistos.items():
    filas.append([f"{clave} ({n} archivos)", tam, *clasificar(clave)])

inv = pd.DataFrame(filas, columns=["archivo_v2", "bytes", "grupo", "estado", "en_3_0", "hace_falta", "responsable"])
inv["tamano"] = inv["bytes"].map(lambda b: f"{b / 2**20:.1f} MB" if b >= 2**20 else f"{b / 1024:.0f} KB")
inv = inv.sort_values(["grupo", "estado", "archivo_v2"])[["grupo", "estado", "archivo_v2", "tamano", "en_3_0", "hace_falta", "responsable", "bytes"]]
inv.to_csv(AQUI / "inventario_v2_vs_v3.csv", index=False, encoding="utf-8-sig")

# Versión para leer: un bloque por grupo, primero lo que falta traer.
ORDEN_ESTADO = {"No pasó": 0, "Rehacer en la unión": 1, "Reemplazado en 3.0": 2, "Pasó": 3}
lineas = ["# Inventario: tesis version 2.0 → tesis version 3.0", "",
          f"Generado por `inventario_v2_vs_v3.py`. {len(inv)} archivos de la 2.0 (sin entornos virtuales ni cachés; "
          "cada carpeta de pesos del modelo cuenta como una fila).", "",
          "**Estados:** *No pasó* = no está en la 3.0 · *Rehacer en la unión* = se reconstruye en un paso del pipeline · "
          "*Reemplazado en 3.0* = hay una versión nueva · *Pasó* = está en la 3.0 (actualizado).", "",
          "## Resumen", "", "| Grupo | No pasó | Rehacer en la unión | Reemplazado | Pasó | Total |", "|---|---:|---:|---:|---:|---:|"]
tabla = inv.pivot_table(index="grupo", columns="estado", values="bytes", aggfunc="size", fill_value=0)
for g, r in tabla.iterrows():
    vals = [int(r.get(e, 0)) for e in ("No pasó", "Rehacer en la unión", "Reemplazado en 3.0", "Pasó")]
    lineas.append(f"| {g} | " + " | ".join(str(v) if v else "·" for v in vals) + f" | {sum(vals)} |")
for g, sub in inv.groupby("grupo"):
    sub = sub.assign(o=sub["estado"].map(ORDEN_ESTADO)).sort_values(["o", "archivo_v2"])
    lineas += ["", f"## {g}", "", "| Estado | Archivo en la 2.0 | Tamaño | En la 3.0 | ¿Hace falta? | Responsable |", "|---|---|---:|---|---|---|"]
    for _, r in sub.iterrows():
        lineas.append(f"| {r.estado} | `{r.archivo_v2}` | {r.tamano} | {r.en_3_0} | {r.hace_falta} | {r.responsable} |")
(AQUI / "inventario_v2_vs_v3.md").write_text("\n".join(lineas) + "\n", encoding="utf-8")

print(f"{len(inv)} filas | sin clasificar: {(inv['grupo'] == 'SIN CLASIFICAR').sum()}")
print(inv.groupby(["grupo", "estado"]).size().to_string())
