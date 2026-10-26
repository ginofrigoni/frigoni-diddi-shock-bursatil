"""Figuras propias de la versión reducida de la tesina.

Rehace tres figuras a partir de los CSV que ya generan sus carpetas, con los mismos colores y
el mismo estilo, y con los cambios pedidos para la versión reducida. No toca los scripts ni las
figuras originales: escribe en figuras/ con el sufijo _reducida.

  u1_alineacion_reducida.png  como u1_alineacion.png, sin la marca de abril de 2026
  u2_serie_reducida.png       como u2_serie.png, con la atención explicada (leyenda y escala)
  vix_arg_reducida.png        como vix_arg.png, con la salida del cepo y las elecciones marcadas

Uso:  python figuras_reducida.py   (desde "Informe Final"; lo llama compilar_reducida.py)
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent
UNION = RAIZ / "Unión"
BURSATIL = RAIZ / "Lado Bursatil"
DESTINO = AQUI / "figuras"

CIERRE_BYMA = 17
VENTANA = 20
DIAS_ELECTORALES = {"2025-09-08": "elecciones bonaerenses", "2025-10-27": "elecciones legislativas"}


def figura_u1():
    carpeta = UNION / "01_alineacion_noticias_ruedas"
    notas = pd.read_csv(carpeta / "nota_a_rueda.csv", parse_dates=["hora_ar"])
    por_rueda = pd.read_csv(carpeta / "notas_por_rueda.csv", index_col="rueda")

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8.2), gridspec_kw={"height_ratios": [1, 1.15]})
    horas = notas["hora_ar"].dt.hour + notas["hora_ar"].dt.minute / 60
    sosp = notas["hora_sospechosa"].astype(bool)
    a1.hist(horas[~sosp], bins=96, range=(0, 24), color="#4A90C8", label="Hora real")
    a1.hist(horas[sosp], bins=96, range=(0, 24), color="#D7301F", label="Hora sospechosa (repetida)")
    a1.axvline(CIERRE_BYMA, color="#12263A", lw=1.6, ls="--")
    a1.axvspan(11, CIERRE_BYMA, color="#2E8B57", alpha=0.08)
    a1.text(14, a1.get_ylim()[1] * 0.92, "Rueda abierta\n(11 a 17 h)", ha="center", va="top", fontsize=9, color="#2E8B57")
    a1.text(CIERRE_BYMA + 0.2, a1.get_ylim()[1] * 0.92, "17:00 · cierre: lo que sale\ndespués va a la rueda siguiente",
            va="top", fontsize=9, color="#12263A")
    a1.set_xlim(0, 24); a1.set_xticks(range(0, 25, 2)); a1.set_xlabel("Hora de publicación (hora argentina)")
    a1.set_ylabel("Notas (cada 15 min)"); a1.legend(loc="upper left", frameon=False, fontsize=9)
    a1.set_title("¿A qué hora salen las notas?", loc="left", fontsize=12, fontweight="bold")

    x = pd.to_datetime(por_rueda.index)
    a2.bar(x, por_rueda["n_mismo_dia"], width=1, color="#4A90C8", label="Publicadas ese día antes de las 17:00")
    a2.bar(x, por_rueda["n_tras_cierre"], width=1, bottom=por_rueda["n_mismo_dia"], color="#F2A900",
           label="Publicadas la rueda anterior después del cierre")
    a2.bar(x, por_rueda["n_dia_sin_rueda"], width=1, bottom=por_rueda["n_mismo_dia"] + por_rueda["n_tras_cierre"],
           color="#8C6BB1", label="Publicadas en un día sin rueda")
    a2.set_ylabel("Notas por rueda"); a2.legend(loc="upper left", frameon=False, fontsize=8.5, ncol=1)
    a2.set_title("Cantidad de notas que recibe cada rueda", loc="left", fontsize=12, fontweight="bold")
    for ax in (a1, a2):
        ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(DESTINO / "u1_alineacion_reducida.png", dpi=160, facecolor="white")
    plt.close(fig)


def figura_u2():
    s = pd.read_csv(UNION / "02_sentimiento_por_rueda" / "sentimiento_mercado_rueda.csv")
    s["shock_pos"] = s["shock_pos"].astype(bool)
    s["shock_neg"] = s["shock_neg"].astype(bool)
    media_previa = s["sent_neto_portal"].shift(1).rolling(VENTANA, min_periods=VENTANA).mean()
    x = pd.to_datetime(s["rueda"])

    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 8.4), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]})
    a1.plot(x, s["sent_neto_portal"], color="#4A90C8", lw=1.1, label="Sentimiento ajustado por portal")
    a1.plot(x, media_previa, color="#5C6B7A", lw=1.4, ls="--", label=f"Media de las {VENTANA} ruedas previas")
    a1.scatter(x[s["shock_pos"]], s.loc[s["shock_pos"], "sent_neto_portal"], color="#2E8B57", s=46, zorder=3,
               label="Rueda de tono extremo positivo")
    a1.scatter(x[s["shock_neg"]], s.loc[s["shock_neg"], "sent_neto_portal"], color="#D7301F", s=46, zorder=3,
               label="Rueda de tono extremo negativo")
    for ax in (a1, a2):
        for (f, txt), alto in zip(DIAS_ELECTORALES.items(), (1.0, 0.93)):
            ax.axvline(pd.Timestamp(f), color="#C26A00", lw=1, ls=":")
            if ax is a1:
                y0, y1 = ax.get_ylim()
                ax.text(pd.Timestamp(f), y0 + (y1 - y0) * alto, " " + txt, fontsize=8, color="#C26A00", va="top")
    a1.axhline(0, color="#999", lw=0.6)
    a1.set_ylabel("Sentimiento neto (puntos)")
    a1.set_title("Tono de las noticias por rueda y ruedas de tono extremo", loc="left", fontsize=12, fontweight="bold")
    a1.legend(loc="lower left", frameon=False, fontsize=8.5, ncol=2)

    at = s["atencion_anormal"]
    a2.bar(x, at, width=1, color=np.where(at > 0, "#F2A900", "#8C6BB1"))
    a2.axhline(0, color="#999", lw=0.6)
    a2.set_ylabel("Atención anormal (log)")
    a2.set_yticks([-np.log(2), 0, np.log(1.5), np.log(2)] if at.max() > np.log(1.9) else [-np.log(2), -np.log(1.5), 0, np.log(1.5)])
    a2.set_yticklabels([f"{v:.2f}".replace(".", ",") for v in a2.get_yticks()])
    sec = a2.secondary_yaxis("right")
    sec.set_yticks(a2.get_yticks())
    sec.set_yticklabels([f"×{np.exp(v):.2g}".replace(".", ",") if v >= 0 else f"×{np.exp(v):.2g}".replace(".", ",")
                         for v in a2.get_yticks()])
    sec.set_ylabel("Notas respecto de lo habitual")
    a2.set_title("Atención de los medios: cantidad de notas de la rueda respecto de lo habitual",
                 loc="left", fontsize=12, fontweight="bold")
    a2.legend(handles=[Patch(color="#F2A900", label="Más notas que lo habitual"),
                       Patch(color="#8C6BB1", label="Menos notas que lo habitual")],
              loc="lower left", frameon=False, fontsize=8.5, ncol=2)
    primera = x[at.notna()].min()
    a2.axvspan(x.min(), primera, color="#999", alpha=0.08)
    a2.text(x.min() + (primera - x.min()) / 2, 0.02, f"sin dato:\nprimeras\n{VENTANA} ruedas",
            ha="center", va="bottom", fontsize=7.5, color="#5C6B7A")
    for ax in (a1, a2):
        ax.spines[["top"]].set_visible(False)
    a1.spines[["right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(DESTINO / "u2_serie_reducida.png", dpi=160, facecolor="white")
    plt.close(fig)


def figura_vix():
    r = pd.read_csv(BURSATIL / "03_vix_argentino" / "vix_arg.csv", parse_dates=["fecha"], index_col="fecha")
    eventos = [("2025-04-14", "Salida del cepo"), ("2025-09-07", "Elecciones bonaerenses"),
               ("2025-10-26", "Elecciones legislativas")]

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    ax1.plot(r.index, r["merv_cierre"], color="steelblue", linewidth=1.2)
    ax1.set_title("Índice Merval (2025-01-02 – 2026-05-03)", fontsize=13)
    ax1.set_ylabel("Puntos")
    ax1.grid(alpha=0.3)

    ax2.plot(r.index, r["vix_arg"], color="firebrick", linewidth=1.2)
    ax2.axhline(r["vix_arg"].mean(), color="gray", linestyle="--", linewidth=1,
                label=f"Promedio: {r['vix_arg'].mean():.1f}%")
    ax2.fill_between(r.index, r["vix_arg"], r["vix_arg"].mean(), where=r["vix_arg"] > r["vix_arg"].mean(),
                     alpha=0.2, color="firebrick", label="Por encima del promedio (nervioso)")
    ax2.set_title(f"VIX Argentina — volatilidad realizada (ventana {VENTANA} días, anualizada)", fontsize=13)
    ax2.set_ylabel("Volatilidad (%)")
    ax2.grid(alpha=0.3)

    for f, txt in eventos:
        for ax in (ax1, ax2):
            ax.axvline(pd.Timestamp(f), color="#12263A", lw=1.1, ls="--", alpha=0.75)
        y0, y1 = ax1.get_ylim()
        # Las dos elecciones están a siete semanas: la primera se rotula a la izquierda de su línea.
        izquierda = txt == "Elecciones bonaerenses"
        ax1.text(pd.Timestamp(f), y1 - (y1 - y0) * 0.03, (txt + " ") if izquierda else (" " + txt),
                 fontsize=9, color="#12263A", va="top", ha="right" if izquierda else "left")
    ax2.plot([], [], color="#12263A", lw=1.1, ls="--", alpha=0.75, label="Evento (salida del cepo, elecciones)")
    ax2.legend(loc="upper right")

    plt.tight_layout()
    plt.savefig(DESTINO / "vix_arg_reducida.png", dpi=150)
    plt.close(fig)


def main():
    DESTINO.mkdir(exist_ok=True)
    figura_u1()
    figura_u2()
    figura_vix()
    print("3 figuras de la versión reducida generadas")


if __name__ == "__main__":
    main()
