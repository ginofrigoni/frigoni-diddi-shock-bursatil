"""
Diagrama del pipeline de la unión — tesis version 3.0
Dibuja pipeline_union.png: los dos lados como insumo, las decisiones pendientes (D1-D3)
y los pasos U1 a U9 agrupados por fase.
Uso:  python diagrama_pipeline_union.py
"""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

AQUI = Path(__file__).parent
FUENTE = "Segoe UI"   # con matplotlib 3.11, Calibri dentro de una caja a veces no se dibuja

AZUL, VERDE, VIOLETA, NARANJA, GRIS = "#2C5F8A", "#2E8B57", "#6A4C93", "#C26A00", "#5C6B7A"
FONDO = {AZUL: "#E3EEF7", VERDE: "#E4F3EA", VIOLETA: "#EEE8F5", NARANJA: "#FBEBD6", GRIS: "#EEF1F4"}

fig, ax = plt.subplots(figsize=(11, 15))
ax.set_xlim(0, 100)
ax.set_ylim(0, 150)
ax.axis("off")


def caja(x, y, w, h, titulo, texto, color, tam=8.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.4,rounding_size=1.2",
                                fc=FONDO[color], ec=color, lw=1.6))
    ax.text(x + 1.2, y + h - 1.6, titulo, fontsize=10.5, fontweight="bold", color=color, va="top", family=FUENTE)
    ax.text(x + 1.2, y + h - 5.0, texto, fontsize=tam, color="#1F2A36", va="top", family=FUENTE, linespacing=1.35)


def fase(y, texto):
    ax.text(0.5, y, texto, fontsize=9, fontweight="bold", color=GRIS, family=FUENTE, va="center")


def flecha(x1, y1, x2, y2, color=GRIS):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.4, shrinkA=2, shrinkB=2))


ax.text(50, 148, "Pipeline de la unión: lado bursátil + lado de noticias", ha="center",
        fontsize=15, fontweight="bold", color="#12263A", family=FUENTE)
ax.text(50, 144.8, "Azul = Nicolás · Verde = Gino · Naranja = decisiones · Violeta = paso de la unión",
        ha="center", fontsize=9, color=GRIS, family=FUENTE)

caja(2, 127, 46, 14, "Lado bursátil (cerrado 17/10)",
     "Precios y volumen de 47 acciones · VIX argentino\nrégimen HMM (Calmo/Moderado/Tenso)\n"
     "grupo de baja liquidez · sector · volatilidad", AZUL)
caja(52, 127, 46, 14, "Lado de noticias (actualizado 18/10)",
     "14.012 notas con hora · FinBETO por oración\n(F1 0,685 en notas no vistas) · serie diaria\n"
     "sentimiento por empresa e indicador (NER)", VERDE)

caja(2, 106, 96, 14, "Decisiones tomadas (24/10)",
     "D1 · Sentimiento congelado: se usan los datos actuales del lado de noticias, sin reentrenar\n"
     "D2 · Se analizan precio y volumen, con sentimiento, cantidad de notas y menciones por empresa\n"
     "D3 · Twitter documentado pero no usado · DLM a trabajo futuro · HMM por sector no se rehace", NARANJA)

fase(97.5, "FASE 1 · ALINEAR")
caja(2, 84, 96, 11, "U1 · Cada noticia a su rueda",
     "Hora en huso argentino · después de las 17:00 o en día sin mercado → rueda siguiente · marca de \"hora sospechosa\" (13% de las notas)", VIOLETA)

fase(79.5, "FASE 2 · SERIES")
caja(2, 64, 46, 13.5, "U2 · Series de mercado por rueda",
     "Sentimiento (simple y ajustado por portal)\ncantidad de notas · shocks con la regla\nelegida contra el azar", VIOLETA)
caja(52, 64, 46, 13.5, "U3 · Por empresa e indicador por rueda",
     "Cruce entidad × oración con la hora\n17 empresas con sentimiento propio\nsin noticia = vacío + \"hubo noticia\" = 0", VIOLETA)

fase(59.5, "FASE 3 · DATASETS")
caja(2, 46, 96, 11.5, "U4 · Datasets unificados",
     "dataset_mercado (244 ruedas) · dataset_panel (47 × 244): retorno, volumen anormal, sentimiento, notas, menciones,\n"
     "régimen, liquidez, sector y marcas (elecciones, eco de 20 ruedas, hueco de iProfesional en abril de 2026)", VIOLETA)

fase(41.5, "FASE 4 · MODELOS")
caja(2, 25, 30, 14, "U5 · ADF",
     "Estacionariedad de cada\nserie en las 244 ruedas", VIOLETA)
caja(35, 25, 30, 14, "U6 · VAR + Granger + IRF",
     "Precio y volumen · mercado,\n47 + 17 empresas, Calmo vs.\nTenso, sector · corrección BH", VIOLETA)
caja(68, 25, 30, 14, "U7 · Event study",
     "Shocks de U2 sin solapar\nCAR de precio y de volumen\ntest t y test de signo", VIOLETA)

fase(20.5, "FASE 5 · CIERRE")
caja(2, 5, 46, 13, "U8 · Robustez",
     "Por portal · régimen filtrado · No calmo ·\nsin ilíquidas · sin hora sospechosa ·\nsin abril 2026 · fecha calendario", VIOLETA)
caja(52, 5, 46, 13, "U9 · Entrega final",
     "PDF por paso · mapa completo de la tesis ·\ndiccionario de variables · plan actualizado ·\nbibliografía unificada · presentación", VIOLETA)

flecha(25, 127, 25, 120.4, AZUL)
flecha(75, 127, 75, 120.4, VERDE)
flecha(50, 106, 50, 95.4)
flecha(25, 84, 25, 77.9)
flecha(75, 84, 75, 77.9)
flecha(25, 64, 25, 57.9)
flecha(75, 64, 75, 57.9)
flecha(17, 46, 17, 39.4)
flecha(50, 46, 50, 39.4)
flecha(83, 46, 83, 39.4)
flecha(32.4, 32, 34.6, 32)
flecha(50, 25, 30, 18.4)
flecha(83, 25, 40, 18.4)
flecha(48.4, 11.5, 51.6, 11.5)

fig.savefig(AQUI / "pipeline_union.png", dpi=170, bbox_inches="tight", facecolor="white")
print("pipeline_union.png generado")
