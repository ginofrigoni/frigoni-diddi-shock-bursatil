"""
Veredicto sobre la hipótesis — tesis versión 6.0
Fase 5 de CRISP-DM (evaluación): se contrastan los resultados con el criterio de éxito.

H1: es posible construir una metodología de ciencia de datos que mida el sentimiento de las noticias
    económicas y lo relacione con el comportamiento de las acciones argentinas.
H0: no es posible.

Criterio de aceptación de H1 (fijado antes de ver resultados, PLAN_VERSION_6.md):
  1. FinBETO supera al modelo de referencia en noticias no vistas (F1 macro), y
  2. el modelo con la información del otro lado supera al modelo sin ella en al menos una dirección
     (noticias → precio o precio → sentimiento): límite inferior del IC 95 % de ΔAUC > 0 en la
     regresión logística.

Este script no calcula nada nuevo: lee los resultados de las otras carpetas y aplica el criterio.
Salidas: salidas/veredicto.csv, metricas.csv

Uso:  python veredicto.py
"""

import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
SALIDAS = AQUI / "salidas"
SALIDAS.mkdir(exist_ok=True)

fin = pd.read_csv(RAIZ / "3_preparacion_de_los_datos" / "sentimiento_finbeto" / "salidas" / "entrenamiento" / "comparacion_baseline.csv")
fin = fin.set_index("test").loc["completo"]
d_np = pd.read_csv(RAIZ / "4_modelado" / "noticias_a_precio" / "salidas" / "delta_auc.csv").set_index("algoritmo")
d_ps = pd.read_csv(RAIZ / "4_modelado" / "precio_a_sentimiento" / "salidas" / "delta_auc.csv").set_index("algoritmo")
rob = pd.read_csv(RAIZ / "5_evaluacion" / "anexo" / "salidas" / "robustez.csv")
vg = pd.read_csv(RAIZ / "5_evaluacion" / "anexo" / "metricas_var_granger.csv").set_index("metrica")

c1 = fin["finbeto_f1_macro"] > fin["referencia_f1_macro"]
np_aporta = d_np.loc["logistica", "ic95_inf"] > 0
ps_aporta = d_ps.loc["logistica", "ic95_inf"] > 0
c2 = np_aporta or ps_aporta
rob_l = rob[rob["algoritmo"] == "logistica"]
rob_ps = rob_l[rob_l["direccion"] == "precio → sentimiento"]
rob_np = rob_l[rob_l["direccion"] == "noticias → precio"]


def ic(d):
    return f"{d['delta_auc']:+.3f} [{d['ic95_inf']:+.3f}; {d['ic95_sup']:+.3f}]"


filas = [
    {"parte": "1. FinBETO supera a la referencia",
     "resultado": f"F1 macro {fin['finbeto_f1_macro']:.3f} contra {fin['referencia_f1_macro']:.3f} ({fin['ventaja_puntos']:+.1f} puntos)",
     "cumple": "sí" if c1 else "no"},
    {"parte": "2a. Noticias → precio", "resultado": f"ΔAUC logística {ic(d_np.loc['logistica'])}; RF {ic(d_np.loc['random_forest'])}",
     "cumple": "sí" if np_aporta else "no"},
    {"parte": "2b. Precio → sentimiento", "resultado": f"ΔAUC logística {ic(d_ps.loc['logistica'])}; RF {ic(d_ps.loc['random_forest'])}",
     "cumple": "sí" if ps_aporta else "no"},
    {"parte": "2. Al menos una dirección", "resultado": "precio → sentimiento" if ps_aporta else ("noticias → precio" if np_aporta else "ninguna"),
     "cumple": "sí" if c2 else "no"},
    {"parte": "Robustez precio → sentimiento", "resultado": f"aporta en {int(rob_ps['aporta'].sum())} de {len(rob_ps)} variantes "
               f"(ΔAUC entre {rob_ps['delta_auc'].min():+.3f} y {rob_ps['delta_auc'].max():+.3f})", "cumple": "—"},
    {"parte": "Robustez noticias → precio", "resultado": f"aporta en {int(rob_np['aporta'].sum())} de {len(rob_np)} variantes", "cumple": "—"},
    {"parte": "Verificación clásica (Granger)",
     "resultado": f"retorno → sentimiento en {vg.loc['empresas retorno → sentimiento inesperado: p < 0,05', 'valor']} empresas; "
                  f"sentimiento → retorno en {vg.loc['empresas sentimiento inesperado → retorno: p < 0,05', 'valor']}", "cumple": "—"},
    {"parte": "VEREDICTO", "resultado": "Se rechaza H0: se acepta H1" if (c1 and c2) else "No se rechaza H0", "cumple": "sí" if (c1 and c2) else "no"},
]
V = pd.DataFrame(filas)
V.to_csv(SALIDAS / "veredicto.csv", index=False, encoding="utf-8")
pd.DataFrame([{"metrica": "criterio_1_finbeto", "valor": "sí" if c1 else "no"},
              {"metrica": "criterio_2_alguna_direccion", "valor": "sí" if c2 else "no"},
              {"metrica": "noticias_a_precio_aporta", "valor": "sí" if np_aporta else "no"},
              {"metrica": "precio_a_sentimiento_aporta", "valor": "sí" if ps_aporta else "no"},
              {"metrica": "veredicto", "valor": "se rechaza H0" if (c1 and c2) else "no se rechaza H0"}]
             ).to_csv(AQUI / "metricas.csv", index=False, encoding="utf-8")
print(V.to_string(index=False))
