"""Figura del pipeline de la tesina con las fases de CRISP-DM (versión 6.0).

Cada fase es una columna con el nombre de la carpeta del proyecto y lo que hay adentro; las flechas
siguen el orden de ejecución. Escribe figuras/pipeline_crispdm.png.

Uso:  python figuras.py   (lo llama compilar_tesina.py)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

AQUI = Path(__file__).resolve().parent
DESTINO = AQUI / "figuras"
DESTINO.mkdir(exist_ok=True)

AZUL, AMBAR, TINTA, GRIS, FONDO = "#1F6FA3", "#B5700F", "#13202F", "#4A5568", "#F6F5F1"
FASES = [
    ("1. Comprensión\ndel problema", ["Hipótesis H1 / H0", "Criterio de aceptación", "Objetivos"], TINTA),
    ("2. Comprensión\nde los datos", ["Noticias: 7 portales", "Mercado: precios de BYMA"], TINTA),
    ("3. Preparación\nde los datos", ["Regla de las 17:00", "FinBETO (3 clases)", "Sentimiento inesperado",
                                      "Sentimiento propio (NER)", "VIX argentino", "Dataset 17 × 244"], AZUL),
    ("4. Modelado", ["Modelo A contra B", "Logística y random forest", "Noticias → precio", "Precio → sentimiento"], AZUL),
    ("5. Evaluación", ["Test feb.–abr. 2026", "ΔAUC con IC 95 %", "Robustez y Granger", "Veredicto"], AMBAR),
    ("6. Despliegue", ["Informe", "Presentación", "correr_todo.py"], TINTA),
]

fig, ax = plt.subplots(figsize=(13, 4.6))
ax.set_xlim(0, 6); ax.set_ylim(0, 1); ax.axis("off")
ancho = 0.86
for i, (titulo, items, color) in enumerate(FASES):
    x = i + (1 - ancho) / 2
    ax.add_patch(FancyBboxPatch((x, 0.04), ancho, 0.92, boxstyle="round,pad=0.005,rounding_size=0.03",
                                fc=FONDO, ec=color, lw=1.6))
    ax.text(x + ancho / 2, 0.88, titulo, ha="center", va="center", fontsize=10.5, fontweight="bold", color=color)
    for j, it in enumerate(items):
        ax.text(x + 0.06, 0.70 - j * 0.105, "· " + it, ha="left", va="center", fontsize=8.6, color=GRIS)
    if i < len(FASES) - 1:
        ax.add_patch(FancyArrowPatch((x + ancho, 0.5), (i + 1 + (1 - ancho) / 2, 0.5), arrowstyle="-|>",
                                     mutation_scale=14, color=TINTA, lw=1.4))
fig.tight_layout()
fig.savefig(DESTINO / "pipeline_crispdm.png", dpi=180, facecolor="white")
print("figuras/pipeline_crispdm.png")
