"""
U9 · Mapa completo de la tesis — tesis version 3.0 (Unión)

Dibuja mapa_tesis.png: el lado bursátil, el lado de noticias y la unión, con los números clave de cada paso.
Todos los números se leen de los archivos de cada carpeta (nada escrito a mano), y quedan en resumen_mapa_tesis.csv.
Uso:  python mapa_tesis.py
"""

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import FancyBboxPatch

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).parent
UNION = AQUI.parent
RAIZ = UNION.parent
B, N = RAIZ / "Lado Bursatil", RAIZ / "Lado Noticias"
FUENTE = "Segoe UI"   # con matplotlib 3.11, Calibri dentro de una caja a veces no se dibuja


def res(carpeta, archivo):
    return pd.read_csv(UNION / carpeta / archivo).set_index("metrica")["valor"]


def mil(x):
    return f"{int(round(float(x))):,}".replace(",", ".")


def coma(x, d=1):
    return f"{float(x):.{d}f}".replace(".", ",")


# ── Números del lado bursátil ────────────────────────────────────────────
panel = pd.read_csv(B / "01_scraping_acciones" / "panel_acciones_final.csv")
rob = pd.read_csv(B / "02_clustering_acciones" / "robustez_grupo_liquidez.csv")
vix = pd.read_csv(B / "03_vix_argentino" / "vix_arg.csv")
adf = pd.read_csv(B / "04_adf" / "resultados_adf_47.csv")
rank = pd.read_csv(B / "05_volatilidad_ranking" / "ranking_volatilidad.csv")
hmm = pd.read_csv(B / "06_hmm_regimen_mercado" / "hmm_regimen_mercado.csv")
reg = hmm["regimen_nombre"].value_counts()
ret_est = int(((adf["tipo"] == "retorno") & (adf["resultado"] == "Estacionaria")).sum())

# ── Números del lado de noticias ─────────────────────────────────────────
notas_corpus = sum(1 for f in (N / "noticias" / "resultados").glob("*.jsonl") for l in open(f, encoding="utf-8") if l.strip())
fase3 = pd.read_csv(N / "sentimiento_finbert" / "resultados_fase3" / "resumen.csv")
f1 = fase3.loc[fase3["division"] == "dataset_v2", "test_f1_macro"].mean()
serie = pd.read_csv(N / "sentimiento_finbert" / "finetuned_serie_diaria.csv")
ner = json.loads((N / "ner_entidades" / "resultados_ner" / "ner_sentimiento_reporte.json").read_text(encoding="utf-8"))

# ── Números de la unión ──────────────────────────────────────────────────
u1, u2, u3, u4 = res("01_alineacion_noticias_ruedas", "resumen_u1.csv"), res("02_sentimiento_por_rueda", "resumen_u2.csv"), \
    res("03_sentimiento_por_empresa", "resumen_u3.csv"), res("04_dataset_unificado", "resumen_u4.csv")
u5, u6, u6b = res("05_adf_union", "resumen_u5.csv"), res("06_var_granger", "resumen_u6.csv"), res("06b_noticias_preapertura", "resumen_u6b.csv")
u7, u8 = res("07_event_study", "resumen_u7.csv"), res("08_robustez", "resumen_u8.csv")
g6 = pd.read_csv(UNION / "06_var_granger" / "granger_resultados.csv")
p_rt = g6[(g6["nivel"] == "mercado") & (g6["prueba"] == "retorno → tono")]["p_bh"].iloc[0]
emp_rt = int(g6[(g6["nivel"] == "empresa") & (g6["prueba"] == "retorno → tono")]["signif_bh"].sum())
prop_rt = int(g6[(g6["nivel"] == "propio") & (g6["prueba"] == "retorno → tono propio")]["signif_bh"].sum())
nm = int(g6[(g6["direccion"] == "noticias → mercado") & g6["signif_bh"]].shape[0]); nm_total = int((g6["direccion"] == "noticias → mercado").sum())
p6b = pd.read_csv(UNION / "06b_noticias_preapertura" / "resultados_principales.csv")
p6b_m = p6b[(p6b["muestra"] == "todas las ruedas") & p6b["nivel"].str.startswith("mercado") & (p6b["retorno"] == "ret_apertura")]["p"].iloc[0]
r7 = pd.read_csv(UNION / "07_event_study" / "resultados_mercado.csv")
e7 = r7[(r7["eventos"] == "positivos") & (r7["muestra"] == "todos") & (r7["ventana"] == "día [0]")].iloc[0]
r7b = pd.read_csv(UNION / "07b_shock_volumen_noticias" / "resultados_principales.csv")
v7b = r7b[r7b["version"].str.startswith("principal") & (r7b["nivel"] == "empresas") & (r7b["clave"] == "vol_día [0]")].iloc[0]
pre7b = pd.read_csv(UNION / "07b_shock_volumen_noticias" / "resultados_preapertura.csv")
s7b = pre7b[(pre7b["nivel"] == "empresas") & (pre7b["clave"] == "abs_salto")].iloc[0]
fr = pd.read_csv(UNION / "08_robustez" / "efecto_por_franja.csv").set_index("franja")
repro = pd.read_csv(AQUI / "reproducibilidad.csv"); ctrl = pd.read_csv(AQUI / "controles_union.csv")

numeros = {
    "acciones": len(panel), "grupo_liquidez": rob.loc[0, "tamanos"].split(" / ")[0], "silueta": rob.loc[0, "silueta"],
    "ruedas_bursatil": len(vix), "retornos_estacionarios": ret_est, "calmo": reg.get("Calmo", 0), "moderado": reg.get("Moderado", 0), "tenso": reg.get("Tenso", 0),
    "notas_corpus": notas_corpus, "f1_noticias_no_vistas": round(f1, 3), "dias_serie": len(serie), "shocks_gino": int(serie["shock"].sum()),
    "cobertura_cruce_ner": ner["cobertura_pct"],
    "notas_en_ventana": u1["notas_en_ventana_union"], "ruedas_union": u1["ruedas_ventana"], "pct_cambian_de_dia": u1["pct_en_ventana_cambia_de_dia"],
    "shocks_union": u2["shocks"], "empresas_tono_propio": u3["empresas_con_sentimiento_propio"], "filas_panel": u4["filas_panel"],
    "series_adf": u5["series_probadas"], "p_retorno_tono": p_rt, "empresas_retorno_tono": emp_rt, "propio_retorno_tono": prop_rt,
    "noticias_mercado_sig": nm, "noticias_mercado_tests": nm_total, "p_preapertura": p6b_m, "car_dia0_positivos": e7["car_medio_pct"],
    "eventos_positivos": e7["n"], "eventos_cantidad_empresa": int(v7b["n"]), "vol_cantidad_empresa": v7b["promedio_eventos"],
    "vol_dia_cualquiera": v7b["promedio_dia_cualquiera"], "p_bh_vol_cantidad": v7b["p_bh"], "p_bh_salto_cantidad": s7b["p_bh"],
    "robustez_mantienen": u8["se_mantienen"], "robustez_total": u8["comparaciones"],
    "efecto_noche": fr.loc["noche anterior (17 a 24 h)", "efecto_por_desvio_ret"], "archivos_identicos": int(repro["identico"].sum()),
    "archivos_total": len(repro), "controles_ok": int(ctrl["pasa"].sum()), "controles_total": len(ctrl),
}
pd.DataFrame([{"metrica": k, "valor": v} for k, v in numeros.items()]).to_csv(AQUI / "resumen_mapa_tesis.csv", index=False, encoding="utf-8")
n_ = numeros

# ── Dibujo ───────────────────────────────────────────────────────────────
AZUL, VERDE, VIOLETA, ROJO, GRIS = "#2C5F8A", "#2E8B57", "#6A4C93", "#B03A2E", "#5C6B7A"
FONDO = {AZUL: "#E3EEF7", VERDE: "#E4F3EA", VIOLETA: "#EEE8F5", ROJO: "#FBE6E3"}
fig, ax = plt.subplots(figsize=(12, 13))
ax.set_xlim(0, 120); ax.set_ylim(0, 132); ax.axis("off")


def caja(x, y, w, h, titulo, texto, color, tam=8.3):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.35,rounding_size=1.0", fc=FONDO[color], ec=color, lw=1.4))
    ax.text(x + 1, y + h - 1.4, titulo, fontsize=9.4, fontweight="bold", color=color, va="top", family=FUENTE)
    ax.text(x + 1, y + h - 4.8, texto, fontsize=tam, color="#1F2A36", va="top", family=FUENTE, linespacing=1.32)


def flecha(x1, y1, x2, y2, color=GRIS):
    ax.annotate("", xy=(x2, y2), xytext=(x1, y1), arrowprops=dict(arrowstyle="-|>", color=color, lw=1.3, shrinkA=1, shrinkB=1))


ax.text(60, 130.5, "Mapa de la tesis: shocks informativos y acciones argentinas", ha="center", fontsize=15, fontweight="bold", color="#12263A", family=FUENTE)
ax.text(60, 127.2, "Azul = lado bursátil (Nicolás) · Verde = lado de noticias (Gino) · Violeta = unión · Rojo = resultado", ha="center",
        fontsize=9, color=GRIS, family=FUENTE)

ax.text(1, 123.5, "LADO BURSÁTIL", fontsize=10, fontweight="bold", color=AZUL, family=FUENTE)
bur = [("01 Acciones", f"{n_['acciones']} acciones de BYMA\nprecio y volumen, 3 años"),
       ("02 Clustering", f"grupo de {n_['grupo_liquidez']} acciones\nde baja liquidez"),
       ("03 VIX argentino", f"volatilidad de 20 ruedas\n{n_['ruedas_bursatil']} ruedas"),
       ("04 ADF", f"retornos estables:\n{n_['retornos_estacionarios']} de {n_['acciones']}"),
       ("05 Volatilidad", "ranking de las 47\ny picos propios"),
       ("06 Régimen (HMM)", f"Calmo {n_['calmo']} · Moderado {n_['moderado']}\nTenso {n_['tenso']} ruedas")]
for i, (t, txt) in enumerate(bur):
    caja(1 + i * 19.8, 110, 18.6, 11.5, t, txt, AZUL, 8)

ax.text(1, 104.5, "LADO DE NOTICIAS", fontsize=10, fontweight="bold", color=VERDE, family=FUENTE)
noti = [("Corpus", f"{mil(n_['notas_corpus'])} notas\n7 portales, depuradas"),
        ("Modelo de sentimiento", f"FinBETO, 4 clases\nF1 {coma(n_['f1_noticias_no_vistas'], 3)} en notas no vistas"),
        ("Serie diaria", f"{n_['dias_serie']} días\n{n_['shocks_gino']} shocks"),
        ("NER", f"47 empresas e indicadores\ncruce con oraciones: {coma(n_['cobertura_cruce_ner'], 1)}%")]
for i, (t, txt) in enumerate(noti):
    caja(1 + i * 29.7, 91, 28.4, 11.5, t, txt, VERDE, 8)

ax.text(60, 86.3, "▼   los dos lados se juntan en la unión   ▼", ha="center", fontsize=9.5, color=VIOLETA, fontweight="bold", family=FUENTE)
ax.text(1, 82.5, "UNIÓN", fontsize=10, fontweight="bold", color=VIOLETA, family=FUENTE)
uni = [("U1 · Notas → ruedas", f"{mil(n_['notas_en_ventana'])} notas en {n_['ruedas_union']} ruedas\n{coma(n_['pct_cambian_de_dia'], 0)}% cambia de día\n(regla de las 17:00)"),
       ("U2 · Tono por rueda", f"tono y atención\n{n_['shocks_union']} ruedas de tono\nextremo"),
       ("U3 · Tono por empresa", f"{n_['empresas_tono_propio']} empresas con\ntono propio\npanel 47 × {n_['ruedas_union']}"),
       ("U4 · Datasets", f"mercado y panel\n({mil(n_['filas_panel'])} filas)\ndiccionario de variables"),
       ("U5 · Estacionariedad", f"{n_['series_adf']} series\nel VAR usa el\ntono anormal")]
for i, (t, txt) in enumerate(uni):
    caja(1 + i * 23.8, 66, 22.6, 14, t, txt, VIOLETA, 8)

caja(1, 48, 57, 14, "U6 · VAR y Granger: ¿quién anticipa a quién?",
     f"Mercado → noticias: el retorno anticipa el tono (p {coma(n_['p_retorno_tono'], 4)}),\n"
     f"en {n_['empresas_retorno_tono']} de 47 empresas y en {n_['propio_retorno_tono']} de 17 con tono propio\n"
     f"Noticias → mercado: {n_['noticias_mercado_sig']} de {n_['noticias_mercado_tests']} pruebas, lo esperable por azar", VIOLETA, 8.5)
caja(62, 48, 57, 14, "U6b · Notas publicadas con el mercado cerrado",
     "La prueba más directa de la hipótesis (fijada de antemano):\n"
     f"el tono de la noche no anticipa la apertura (p = {coma(n_['p_preapertura'], 3)});\n"
     "solo las elecciones se reflejan en la apertura", VIOLETA, 8.5)
caja(1, 30, 57, 14, "U7 y U7b · Event studies",
     f"Tono extremo positivo ({n_['eventos_positivos']}): el Merval sube {coma(n_['car_dia0_positivos'], 2)}% ese día\ny ya venía subiendo antes; después no pasa nada.\n"
     f"Muchas más notas sobre una empresa ({n_['eventos_cantidad_empresa']} shocks, el del plan):\n"
     "se opera más ese día, sin dirección en el precio ni en la apertura", VIOLETA, 8.2)
caja(62, 30, 57, 14, "U8 · Robustez",
     f"{n_['robustez_mantienen']} de {n_['robustez_total']} comparaciones mantienen la conclusión;\n"
     f"el efecto está en las notas de la misma noche, post-cierre:\n+{coma(n_['efecto_noche'])} puntos de tono por desvío del retorno", VIOLETA, 8.5)

caja(1, 12, 118, 14, "Resultado de la tesis",
     "Los medios económicos argentinos siguen al mercado: las notas de la misma noche cuentan la suba o la baja con un tono que la acompaña.\n"
     "El tono de las noticias no anticipa los precios ni el volumen, ni siquiera con las notas publicadas antes de la apertura.\n"
     "Cuando una empresa aparece en muchas más notas, ese día se opera más, pero su precio no se mueve en una dirección ni se anticipa.\n"
     "Los hechos grandes (elecciones, el anuncio del Tesoro de EE. UU.) se reflejan de inmediato; la cobertura no agrega información nueva.", ROJO, 8.8)
caja(1, 1, 118, 7.5, "Reproducibilidad",
     f"Un solo comando (09_entrega_final/correr_todo.py) rehace toda la unión: {n_['archivos_identicos']} de {n_['archivos_total']} archivos idénticos · "
     f"{n_['controles_ok']} de {n_['controles_total']} controles automáticos pasan", ROJO, 8.8)

for x in (30, 90):
    flecha(x, 66, x, 62.4)
    flecha(x, 48, x, 44.4)
    flecha(x, 30, x, 26.4)

fig.savefig(AQUI / "mapa_tesis.png", dpi=170, bbox_inches="tight", facecolor="white")
print("mapa_tesis.png generado")
