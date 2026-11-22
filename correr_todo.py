"""
Reproducir la tesina con un solo comando — tesis versión 6.0

Corre los pasos en el orden de CRISP-DM (preparación → modelado → evaluación → despliegue), cada uno en
su carpeta, y después:
  1. verifica que pasen todos los controles automáticos (verificaciones.csv y los controles del dataset
     de FinBETO);
  2. compara la huella (sha256) de cada archivo de resultados antes y después de correr: si son
     idénticas, el proyecto es reproducible bit a bit.

Pasos que se saltan por defecto, porque son lentos o necesitan otra cosa:
  --con-gpu         reentrena FinBETO y vuelve a clasificar las 413.515 oraciones (necesita torch con CUDA;
                    por defecto usa ../tesis 4.0/.venv). Unos 6 minutos en una RTX 3090. El reentrenamiento
                    en GPU puede no dar idéntico bit a bit.
  --con-robustez    las 9 variantes de robustez (unos 25 minutos).
  --con-informe     compila el PDF del informe (necesita tectonic).
  --rapido          lo mismo que no pasar ninguna de las tres: es el valor por defecto.

Escribe en la raíz: reproducibilidad.csv (huella antes y después de cada resultado) y controles.csv
(todos los controles de todos los pasos).

Uso:  python correr_todo.py [--con-gpu] [--con-robustez] [--con-informe] [--python-gpu RUTA]
"""

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

RAIZ = Path(__file__).resolve().parent
P3 = "3_preparacion_de_los_datos"
FB = f"{P3}/sentimiento_finbeto"
GPU_POR_DEFECTO = RAIZ.parent / "tesis 4.0" / ".venv" / "Scripts" / "python.exe"

# (fase, carpeta, script, tipo) — tipo: "cpu", "gpu", "robustez", "informe"
PASOS = [
    ("3 · Preparación", f"{P3}/regla_17", "alinear_noticias_ruedas.py", "cpu"),
    ("3 · Preparación", FB, "preparar_dataset_v2.py", "cpu"),
    ("3 · Preparación", FB, "fase3_reentrenar_para_medir.py", "gpu"),
    ("3 · Preparación", FB, "comparar_baseline.py", "gpu"),
    ("3 · Preparación", FB, "clasificar_oraciones.py", "gpu"),
    ("3 · Preparación", FB, "sentimiento_por_nota.py", "cpu"),
    ("3 · Preparación", FB, "acuerdo_con_5.py", "cpu"),
    ("3 · Preparación", FB, "ejemplos_etiquetado.py", "cpu"),
    ("3 · Preparación", f"{P3}/sentimiento_por_rueda", "sentimiento_por_rueda.py", "cpu"),
    ("3 · Preparación", f"{P3}/sentimiento_por_empresa", "cruce_ner_sentimiento.py", "cpu"),
    ("3 · Preparación", f"{P3}/sentimiento_por_empresa", "sentimiento_por_empresa.py", "cpu"),
    ("3 · Preparación", f"{P3}/vix_argentino", "escala_vix.py", "cpu"),
    ("3 · Preparación", f"{P3}/dataset_unificado", "construir_datasets.py", "cpu"),
    ("4 · Modelado", "4_modelado/noticias_a_precio", "noticias_a_precio.py", "cpu"),
    ("4 · Modelado", "4_modelado/precio_a_sentimiento", "precio_a_sentimiento.py", "cpu"),
    ("5 · Evaluación", "5_evaluacion/anexo", "robustez.py", "robustez"),
    ("5 · Evaluación", "5_evaluacion/anexo", "var_granger.py", "cpu"),
    ("5 · Evaluación", "5_evaluacion/veredicto_hipotesis", "veredicto.py", "cpu"),
    ("6 · Despliegue", "6_despliegue/informe", "compilar_tesina.py", "informe"),
]
# Resultados cuya huella se compara (los CSV y JSON de resultados; no las figuras ni el PDF).
PATRONES = ["**/salidas/**/*.csv", "**/salidas/**/*.json", "**/metricas*.csv", "6_despliegue/informe/generado/**/*.tex"]
EXCLUIR = ("beto_oraciones_finetuned.csv", "registro_copia.csv", "reproducibilidad.csv", "controles.csv")


def huellas():
    h = {}
    for patron in PATRONES:
        for f in RAIZ.glob(patron):
            if f.is_file() and f.name not in EXCLUIR and ".git" not in f.parts:
                h[f.relative_to(RAIZ).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return h


def controles():
    filas = []
    for f in sorted(RAIZ.glob("**/salidas/verificaciones.csv")):
        v = pd.read_csv(f)
        for _, x in v.iterrows():
            filas.append({"paso": f.parent.parent.relative_to(RAIZ).as_posix(), "control": x["control"], "pasa": bool(x["pasa"])})
    rep = RAIZ / FB / "salidas" / "dataset_3clases" / "reporte.json"
    if rep.exists():
        for k, v in json.loads(rep.read_text(encoding="utf-8")).get("controles", {}).items():
            filas.append({"paso": f"{FB} (dataset)", "control": k, "pasa": bool(v)})
    return pd.DataFrame(filas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--con-gpu", action="store_true")
    ap.add_argument("--con-robustez", action="store_true")
    ap.add_argument("--con-informe", action="store_true")
    ap.add_argument("--rapido", action="store_true", help="valor por defecto: sin GPU, sin robustez y sin informe")
    ap.add_argument("--python-gpu", default=str(GPU_POR_DEFECTO))
    a = ap.parse_args()
    activos = {"cpu"} | ({"gpu"} if a.con_gpu else set()) | ({"robustez"} if a.con_robustez else set()) | ({"informe"} if a.con_informe else set())

    antes = huellas()
    tiempos, t_total = [], time.time()
    for fase, carpeta, script, tipo in PASOS:
        if tipo not in activos:
            print(f"[saltado] {carpeta}/{script} ({tipo})")
            tiempos.append({"fase": fase, "paso": f"{carpeta}/{script}", "estado": "saltado", "segundos": 0})
            continue
        python = a.python_gpu if tipo == "gpu" else sys.executable
        print(f"[corre]   {carpeta}/{script}", flush=True)
        t0 = time.time()
        r = subprocess.run([python, script], cwd=RAIZ / carpeta, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
        if r.returncode != 0:
            print(r.stdout[-3000:]); print(r.stderr[-3000:])
            sys.exit(f"Falló {carpeta}/{script}")
        tiempos.append({"fase": fase, "paso": f"{carpeta}/{script}", "estado": "ok", "segundos": round(time.time() - t0, 1)})

    despues = huellas()
    archivos = sorted(set(antes) | set(despues))
    rep = pd.DataFrame([{"archivo": f, "antes": antes.get(f, "")[:16], "despues": despues.get(f, "")[:16],
                         "identico": antes.get(f) == despues.get(f)} for f in archivos])
    rep.to_csv(RAIZ / "reproducibilidad.csv", index=False, encoding="utf-8")
    c = controles()
    c.to_csv(RAIZ / "controles.csv", index=False, encoding="utf-8")

    print()
    print(pd.DataFrame(tiempos).to_string(index=False))
    print(f"\nTiempo total: {round((time.time() - t_total) / 60, 1)} minutos")
    print(f"Controles: {int(c['pasa'].sum())} de {len(c)} pasan")
    for _, x in c[~c["pasa"]].iterrows():
        print(f"  NO PASA · {x['paso']}: {x['control']}")
    print(f"Resultados idénticos a la corrida anterior: {int(rep['identico'].sum())} de {len(rep)}")
    for _, x in rep[~rep["identico"]].iterrows():
        print(f"  cambió · {x['archivo']}")
    if not c["pasa"].all():
        sys.exit(1)


if __name__ == "__main__":
    main()
