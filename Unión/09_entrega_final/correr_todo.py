"""
U9 · Reproducir la unión completa con un solo comando — tesis version 3.0 (Unión)

Corre los pasos de la unión en orden (diagnóstico, U1 a U8), cada uno en su carpeta, y después:
  1. verifica que pasen todos los controles automáticos de cada paso (verificaciones.csv);
  2. compara la huella (sha256) de los archivos de resultados antes y después de correr: si son idénticas,
     la unión es reproducible bit a bit.
No regenera los PDF (eso lo hacen los generadores de 99_generadores_documentacion).

Escribe en esta carpeta: reproducibilidad.csv (un archivo de resultados por fila, con su huella antes y después)
y controles_union.csv (todos los controles de todos los pasos).
Uso:  python correr_todo.py
"""

import hashlib
import subprocess
import sys
import time
from pathlib import Path

import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).parent
UNION = AQUI.parent
PASOS = [
    ("00", "00_pipeline_union", "diagnostico_union.py"),
    ("U1", "01_alineacion_noticias_ruedas", "alinear_noticias_ruedas.py"),
    ("U2", "02_sentimiento_por_rueda", "sentimiento_por_rueda.py"),
    ("U3", "03_sentimiento_por_empresa", "sentimiento_por_empresa.py"),
    ("U4", "04_dataset_unificado", "construir_datasets.py"),
    ("U5", "05_adf_union", "adf_union.py"),
    ("U6", "06_var_granger", "var_granger.py"),
    ("U6b", "06b_noticias_preapertura", "noticias_preapertura.py"),
    ("U7", "07_event_study", "event_study.py"),
    ("U7b", "07b_shock_volumen_noticias", "shock_volumen_noticias.py"),
    ("U8", "08_robustez", "robustez.py"),
]


def huellas():
    out = {}
    for _, carpeta, _ in PASOS:
        for f in sorted((UNION / carpeta).glob("*.csv")):
            out[f.relative_to(UNION).as_posix()] = hashlib.sha256(f.read_bytes()).hexdigest()
    return out


antes = huellas()
tiempos = []
for paso, carpeta, script in PASOS:
    t0 = time.time()
    print(f"[{paso}] {carpeta}/{script} ...", flush=True)
    r = subprocess.run([sys.executable, "-X", "utf8", script], cwd=UNION / carpeta, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-4000:])
        raise SystemExit(f"Falló {paso}: {script}")
    tiempos.append((paso, round(time.time() - t0, 1)))
despues = huellas()

repro = pd.DataFrame([{"archivo": k, "huella_antes": antes.get(k, ""), "huella_despues": v, "identico": antes.get(k) == v}
                      for k, v in despues.items()])
repro.to_csv(AQUI / "reproducibilidad.csv", index=False, encoding="utf-8")

controles = []
for paso, carpeta, _ in PASOS:
    f = UNION / carpeta / "verificaciones.csv"
    if f.exists():
        controles += [{"paso": paso, **x} for x in pd.read_csv(f).to_dict("records")]
ctrl = pd.DataFrame(controles)
ctrl.to_csv(AQUI / "controles_union.csv", index=False, encoding="utf-8")

print()
for paso, seg in tiempos:
    print(f"  {paso:4s} {seg:6.1f} s")
print(f"\nArchivos de resultados: {len(repro)} · idénticos a la corrida anterior: {int(repro['identico'].sum())}")
distintos = repro[~repro["identico"]]
if len(distintos):
    print("Distintos:", ", ".join(distintos["archivo"]))
print(f"Controles: {int(ctrl['pasa'].sum())} de {len(ctrl)} pasan")
