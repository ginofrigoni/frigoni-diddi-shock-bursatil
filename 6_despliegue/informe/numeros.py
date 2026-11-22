"""
Números y tablas del informe, generados desde los resultados — tesis versión 6.0
Fase 6 de CRISP-DM (despliegue).

Regla del plan: ningún número del informe se tipea a mano. Este script lee los metricas*.csv y las
salidas de cada carpeta y escribe:

  generado/numeros.tex   \\dato{clave} para cada número (formato en español: 14.012 · 0,697 · −0,012)
  generado/tablas/*.tex  las tablas del informe, ya armadas

Claves: <alias>.<métrica> para todo lo que está en un metricas*.csv; las variantes @0 … @3 redondean
a esa cantidad de decimales (p. ej. \\dato{rueda.sent_neto_media@1}). Las claves de otros archivos
se arman explícitamente más abajo. Si el texto usa una clave que no existe, la compilación se corta.

Excepción documentada: las cifras de la auditoría del corpus (duplicados, plantillas, metadatos)
vienen de 2_comprension_de_los_datos/noticias/documentacion/, porque la auditoría no se vuelve a
correr en la 6.0; están escritas en el capítulo con su fuente.

Uso:  python numeros.py   (lo llama compilar_tesina.py)
"""

import json
import math
import re
import sys
from pathlib import Path

import pandas as pd

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
P3 = RAIZ / "3_preparacion_de_los_datos"
FB = P3 / "sentimiento_finbeto"
GEN = AQUI / "generado"
TAB = GEN / "tablas"
TAB.mkdir(parents=True, exist_ok=True)
D = {}


# ── formato ──────────────────────────────────────────────────────────────
def esc(s):
    s = str(s)
    for a, b in (("\\", r"\textbackslash{}"), ("&", r"\&"), ("%", r"\%"), ("$", r"\$"), ("#", r"\#"),
                 ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}"), ("^", r"\^{}")):
        s = s.replace(a, b)
    return s


def miles(n):
    s = f"{abs(int(n)):,}".replace(",", ".")
    return ("−" if n < 0 else "") + s


def num(x, dec=None, signo=False):
    if isinstance(x, str):
        try:
            x = float(x)
        except ValueError:
            return esc(x)
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return "—"
    if dec is None:
        if float(x).is_integer():
            return ("+" if signo and x > 0 else "") + miles(x)
        dec = max(0, len(repr(float(x)).split(".")[1])) if "." in repr(float(x)) else 0
        dec = min(dec, 4)
    if dec == 0:
        return ("+" if signo and x > 0 else "") + miles(round(x))
    s = f"{abs(x):,.{dec}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if x < 0 and float(s.replace(".", "").replace(",", ".")) != 0:
        return "−" + s
    return ("+" if signo and x > 0 else "") + s


def pval(p):
    """p-valor: tres cifras significativas, o «< 0,001» si es más chico."""
    p = float(p)
    return r"$<$\,0,001" if p < 0.001 else num(float(f"{p:.2g}"))


def poner(clave, valor, dec=None, signo=False):
    D[clave] = num(valor, dec, signo)
    if not isinstance(valor, str) or re.fullmatch(r"-?\d+(\.\d+)?", str(valor)):
        try:
            v = float(valor)
            for k in range(4):
                D[f"{clave}@{k}"] = num(v, k, signo)
            D[f"{clave}@s3"] = num(v, 3, True)
            D[f"{clave}@pct1"] = num(100 * v, 1)
        except (TypeError, ValueError):
            pass


# ── 1. Todos los metricas*.csv ───────────────────────────────────────────
ALIAS = {
    P3 / "regla_17" / "metricas.csv": "regla17",
    FB / "metricas_dataset.csv": "fbdata",
    FB / "metricas_clasificacion.csv": "fbclas",
    FB / "metricas_por_nota.csv": "fbnota",
    FB / "metricas_acuerdo.csv": "fbacuerdo",
    P3 / "sentimiento_por_rueda" / "metricas.csv": "rueda",
    P3 / "sentimiento_por_empresa" / "metricas.csv": "empresa",
    P3 / "vix_argentino" / "metricas.csv": "vix",
    P3 / "dataset_unificado" / "metricas.csv": "dataset",
    RAIZ / "4_modelado" / "noticias_a_precio" / "metricas.csv": "np",
    RAIZ / "4_modelado" / "precio_a_sentimiento" / "metricas.csv": "ps",
    RAIZ / "5_evaluacion" / "anexo" / "metricas_robustez.csv": "rob",
    RAIZ / "5_evaluacion" / "veredicto_hipotesis" / "metricas.csv": "ver",
}
for ruta, alias in ALIAS.items():
    m = pd.read_csv(ruta, dtype=str, keep_default_na=False)
    for _, x in m.iterrows():
        poner(f"{alias}.{x['metrica']}", x["valor"])
        if "detalle" in m.columns and x["detalle"]:
            D[f"{alias}.{x['metrica']}:det"] = esc(x["detalle"])

# ── 2. Mercado y corpus ──────────────────────────────────────────────────
MERC = RAIZ / "2_comprension_de_los_datos" / "mercado" / "datos"
poner("mercado.acciones", len(pd.read_csv(MERC / "panel_acciones_final.csv")))
poner("mercado.candidatas", len(pd.read_csv(MERC / "cobertura_53_candidatas.csv")))
_panel = pd.read_csv(MERC / "panel_acciones_final.csv")
poner("mercado.sectores", _panel["sector"].nunique()); poner("mercado.en_merval", int(_panel["oficial"].sum()))
poner("mercado.ruedas_3anos", int(_panel["dias"].max()))
nota = pd.read_csv(FB / "salidas" / "sentimiento_por_nota.csv")
FUENTES = [("iprofesional_sitemap", "iProfesional", "Mapa del sitio"), ("clarin_sitemap", "Clarín", "Mapa del sitio"),
           ("clarin_economia", "Clarín — Economía", "Wayback Machine"), ("eleconomista_sitemap", "El Economista", "Mapa del sitio"),
           ("ambito_economia", "Ámbito Financiero — Economía", "Wayback Machine"),
           ("ambito_finanzas", "Ámbito Financiero — Finanzas", "Wayback Machine"),
           ("infobae_economia", "Infobae — Economía", "Wayback Machine"), ("lanacion_economia", "La Nación — Economía", "Wayback Machine"),
           ("tn_economia", "TN — Economía", "Wayback Machine")]
cuenta = nota["fuente"].value_counts()
filas = [f"{p} & {m} & {num(int(cuenta[f]))} \\\\" for f, p, m in FUENTES]
(TAB / "corpus.tex").write_text("\n".join(filas) + f"\n\\midrule\n\\textbf{{Total}} & & \\textbf{{{num(len(nota))}}} \\\\\n", encoding="utf-8")
poner("corpus.notas", len(nota)); poner("corpus.fuentes", len(FUENTES)); poner("corpus.portales", 7)

# ── 3. Etiquetado de Gemma y dataset de FinBETO ──────────────────────────
gem = pd.read_json(FB / "etiquetado_gemma" / "checkpoint.jsonl", lines=True)
poner("gemma.oraciones", len(gem)); poner("gemma.noticias", gem["url"].nunique())
por_fuente = gem.groupby("fuente")["url"].nunique()
poner("gemma.noticias_fuente_min", int(por_fuente.min())); poner("gemma.noticias_fuente_max", int(por_fuente.max()))
for c in ("POS", "NEG", "NEU", "MIXTO"):
    poner(f"gemma.pct_{c}", round(100 * (gem["label"] == c).mean(), 1))
lim = json.loads((FB / "etiquetado_gemma" / "limpieza_reporte.json").read_text(encoding="utf-8"))
poner("gemma.limpias", lim["filas_limpias"]); poner("gemma.eliminadas", lim["filas_eliminadas"])
rep = json.loads((FB / "salidas" / "dataset_3clases" / "reporte.json").read_text(encoding="utf-8"))
for conj in ("train", "val", "test"):
    poner(f"fbsplit.noticias_{conj}", rep["noticias_por_conjunto"][conj])
    poner(f"fbsplit.oraciones_{conj}", rep["oraciones_seleccionadas"][conj])
    for c, n in rep["clases_por_conjunto"][conj].items():
        poner(f"fbsplit.{conj}_{c}", n)
for c, w in rep["class_weights"].items():
    poner(f"fbsplit.peso_{c}", w)
lab = pd.read_csv(FB / "salidas" / "dataset_3clases" / "test.csv")
poner("fbsplit.test_exmixto", int((lab["label_original"] == "MIXTO").sum()))
filas = []
for conj, nombre in (("train", "Entrenamiento"), ("val", "Validación"), ("test", "Prueba")):
    cl = rep["clases_por_conjunto"][conj]
    filas.append(f"{nombre} & {num(rep['noticias_por_conjunto'][conj])} & {num(rep['oraciones_seleccionadas'][conj])} & "
                 f"{num(cl['POS'])} & {num(cl['NEG'])} & {num(cl['NEU'])} \\\\")
(TAB / "division_finbeto.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")

# ── 4. Resultados de FinBETO ─────────────────────────────────────────────
ENT = FB / "salidas" / "entrenamiento"
res = pd.read_csv(ENT / "resumen.csv")
for c in ("f1_macro", "accuracy", "balanced_accuracy", "f1_POS", "f1_NEG", "f1_NEU"):
    poner(f"fb.{c}_media", res[f"test_{c}"].mean()); poner(f"fb.{c}_desvio", res[f"test_{c}"].std())
poner("fb.semillas", len(res))
s42 = json.loads((ENT / "seed42.json").read_text(encoding="utf-8"))
poner("fb.mejor_epoca_42", s42["mejor_epoca"]); poner("fb.minutos", s42["minutos"])
for i, fi in enumerate(s42["orden_matriz"]):
    for j, co in enumerate(s42["orden_matriz"]):
        poner(f"fb.mat.{fi}.{co}", s42["matriz_confusion"][i][j])
for c, n in s42["ex_mixto_predichas_como"].items():
    poner(f"fb.exmixto.{c}", n)
mat = s42["matriz_confusion"]; orden = s42["orden_matriz"]
filas = [f"\\textbf{{{o}}} & " + " & ".join(num(v) for v in mat[i]) + f" & {num(sum(mat[i]))} \\\\" for i, o in enumerate(orden)]
(TAB / "matriz_finbeto.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")
cmp_ = pd.read_csv(ENT / "comparacion_baseline.csv").set_index("test")
for t, al in (("completo", "completo"), ("como_la_5.0", "como50")):
    for c in ("n", "referencia_f1_macro", "referencia_accuracy", "referencia_dice_neutro", "finbeto_f1_macro",
              "finbeto_desvio", "finbeto_accuracy", "ventaja_puntos"):
        poner(f"fbcmp.{al}.{c}", cmp_.loc[t, c])
det = json.loads((ENT / "comparacion_baseline.json").read_text(encoding="utf-8"))
for c in ("f1_POS", "f1_NEG", "f1_NEU"):
    poner(f"fbcmp.ref.{c}", det["completo"]["referencia"][c])
filas = [
    f"F1 macro & \\textbf{{{num(res['test_f1_macro'].mean(), 3)} $\\pm$ {num(res['test_f1_macro'].std(), 3)}}} & {num(cmp_.loc['completo', 'referencia_f1_macro'], 3)} \\\\",
    f"Exactitud (\\textit{{accuracy}}) & {num(res['test_accuracy'].mean(), 3)} & {num(cmp_.loc['completo', 'referencia_accuracy'], 3)} \\\\",
    f"F1 POS / NEG / NEU & {num(res['test_f1_POS'].mean(), 3)} / {num(res['test_f1_NEG'].mean(), 3)} / {num(res['test_f1_NEU'].mean(), 3)} & "
    f"{num(det['completo']['referencia']['f1_POS'], 3)} / {num(det['completo']['referencia']['f1_NEG'], 3)} / {num(det['completo']['referencia']['f1_NEU'], 3)} \\\\",
    f"Predichas como NEU, de {num(cmp_.loc['completo', 'n'])} (FinBETO: modelo final) & {num(sum(r[2] for r in mat))} & {num(cmp_.loc['completo', 'referencia_dice_neutro'])} \\\\",
    "\\midrule",
    f"F1 macro en las {num(cmp_.loc['como_la_5.0', 'n'])} oraciones que ya eran POS, NEG o NEU & {num(cmp_.loc['como_la_5.0', 'finbeto_f1_macro'], 3)}\\textsuperscript{{a}} & {num(cmp_.loc['como_la_5.0', 'referencia_f1_macro'], 3)} \\\\",
]
(TAB / "finbeto.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")

# ── 5. Ejemplos del etiquetado ───────────────────────────────────────────
ej = pd.read_csv(FB / "salidas" / "ejemplos_etiquetado.csv")


def corto(s, n=170):
    s = str(s)
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "…"


filas = []
for _, x in ej.iterrows():
    g = x["etiqueta_gemma_original"] + (" \\flecha{} NEU" if x["etiqueta_gemma_original"] == "MIXTO" else "")
    filas.append(f"{esc(x['tipo'])} & «{esc(x['oracion'])}» & {g} & {x['prediccion_finbeto']} & {esc(corto(x['razon_gemma']))} \\\\")
(TAB / "ejemplos.tex").write_text("\n\\addlinespace\n".join(filas) + "\n", encoding="utf-8")

# ── 6. VIX ───────────────────────────────────────────────────────────────
v = pd.read_csv(P3 / "vix_argentino" / "metricas.csv").set_index("metrica")["valor"]
filas = [f"Bajo & hasta {num(float(v['tercil_1']), 1)}\\% & {num(int(float(v['ruedas_bajo'])))} & {num(float(v['vix_media_bajo']), 1)}\\% & {num(int(float(v['ruedas_test_bajo'])))} \\\\",
         f"Medio & de {num(float(v['tercil_1']), 1)}\\% a {num(float(v['tercil_2']), 1)}\\% & {num(int(float(v['ruedas_medio'])))} & {num(float(v['vix_media_medio']), 1)}\\% & {num(int(float(v['ruedas_test_medio'])))} \\\\",
         f"Alto & más de {num(float(v['tercil_2']), 1)}\\% & {num(int(float(v['ruedas_alto'])))} & {num(float(v['vix_media_alto']), 1)}\\% & {num(int(float(v['ruedas_test_alto'])))} \\\\"]
(TAB / "vix_escala.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")

# ── 7. Modelos predictivos ───────────────────────────────────────────────
NOMBRE_ALG = {"línea base": "Línea base", "logistica": "Regresión logística", "random_forest": "Random forest"}
for sub, al in (("noticias_a_precio", "np"), ("precio_a_sentimiento", "ps")):
    S = RAIZ / "4_modelado" / sub / "salidas"
    mt = pd.read_csv(S / "metricas_test.csv")
    filas = []
    for _, x in mt.iterrows():
        k = "base" if x["algoritmo"] == "línea base" else f"{x['algoritmo']}.{x['modelo']}"
        for c in ("auc", "balanced_accuracy", "f1", "accuracy", "tn", "fp", "fn", "tp", "pct_clase_1_real", "pct_clase_1_predicha", "n"):
            poner(f"{al}.m.{k}.{c}", x[c])
        modelo = x["modelo"] if x["algoritmo"] != "línea base" else f"({x['modelo'].replace('siempre', 'siempre')})"
        negrita = x["algoritmo"] == "logistica"
        fila = f"{NOMBRE_ALG[x['algoritmo']]} & {esc(modelo)} & {num(x['auc'], 3)} & {num(x['balanced_accuracy'], 3)} & {num(x['f1'], 3)} & {num(x['accuracy'], 3)} \\\\"
        filas.append(fila)
    (TAB / f"metricas_{al}.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")
    dl = pd.read_csv(S / "delta_auc.csv").set_index("algoritmo")
    for alg in dl.index:
        for c in ("delta_auc", "ic95_inf", "ic95_sup", "p_unilateral"):
            poner(f"{al}.d.{alg}.{c}", dl.loc[alg, c], signo=c != "p_unilateral")
        D[f"{al}.d.{alg}.p_unilateral:p"] = pval(dl.loc[alg, "p_unilateral"])
    hp = pd.read_csv(S / "hiperparametros.csv")
    for _, x in hp.iterrows():
        for c in ("C", "max_depth", "min_samples_leaf", "auc_validacion"):
            if c in hp.columns and pd.notna(x.get(c)):
                poner(f"{al}.h.{x['algoritmo']}.{x['modelo']}.{c}", x[c])
    imp = pd.read_csv(S / "importancias.csv")
    for _, x in imp[imp["algoritmo"] == "logistica"].iterrows():
        poner(f"{al}.coef.{x['modelo']}.{x['variable']}", x["coeficiente_estandarizado"], signo=True)

_np = pd.read_csv(RAIZ / "4_modelado" / "noticias_a_precio" / "metricas.csv").set_index("metrica")["valor"]
_re, _rt = int(float(_np["ruedas_entrenamiento"])), int(float(_np["ruedas_test"]))
poner("np.pct_ruedas_entrenamiento", round(100 * _re / (_re + _rt))); poner("np.pct_ruedas_test", round(100 * _rt / (_re + _rt)))

# ── 8. Robustez ──────────────────────────────────────────────────────────
rob = pd.read_csv(RAIZ / "5_evaluacion" / "anexo" / "salidas" / "robustez.csv")
NOMBRE_VAR = {"principal": "Principal (capítulo~\\ref{cap:evaluacion})", "con_regimen": "Con el régimen (filtrado)",
              "ventana_10": "Ventana de 10 ruedas", "ventana_60": "Ventana de 60 ruedas",
              "corte_2026_01": "Test desde el 01/01/2026", "corte_2026_03": "Test desde el 01/03/2026",
              "sin_dias_electorales": "Sin días electorales", "sin_abril_2026": "Sin abril de 2026",
              "sentimiento_por_portal": "Sentimiento ajustado por portal"}


def celda(x):
    t = f"{num(x['delta_auc'], 3, True)} [{num(x['ic95_inf'], 3, True)}; {num(x['ic95_sup'], 3, True)}]"
    return f"\\textbf{{{t}}}" if x["aporta"] else t


filas = []
for var, nombre in NOMBRE_VAR.items():
    a = rob[(rob["variante"] == var) & (rob["algoritmo"] == "logistica") & (rob["direccion"] == "noticias → precio")].iloc[0]
    b = rob[(rob["variante"] == var) & (rob["algoritmo"] == "logistica") & (rob["direccion"] == "precio → sentimiento")].iloc[0]
    filas.append(f"{nombre} & {celda(a)} & {celda(b)} \\\\")
(TAB / "robustez.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")
for _, x in rob.iterrows():
    dk = "np" if x["direccion"].startswith("noticias") else "ps"
    for c in ("delta_auc", "ic95_inf", "ic95_sup"):
        poner(f"rob.{x['variante']}.{dk}.{x['algoritmo']}.{c}", x[c], signo=True)
    poner(f"rob.{x['variante']}.{dk}.{x['algoritmo']}.filas_entrenamiento", x["filas_entrenamiento"])

# ── 9. VAR y Granger ─────────────────────────────────────────────────────
ANX = RAIZ / "5_evaluacion" / "anexo" / "salidas"
gr = pd.read_csv(ANX / "granger_resultados.csv")
CLAVE_P = {"sentimiento inesperado → retorno": "ines_ret", "retorno → sentimiento inesperado": "ret_ines",
           "sentimiento propio → retorno": "prop_ret", "retorno → sentimiento propio": "ret_prop"}
for _, x in gr[gr["nivel"] == "mercado"].iterrows():
    k = CLAVE_P[x["prueba"]]
    D[f"var.mercado.{k}.p"] = pval(x["p"]); poner(f"var.mercado.{k}.F", x["F"]); poner(f"var.mercado.{k}.rezagos", x["rezagos"])
    poner(f"var.mercado.{k}.efecto", x["efecto_desvios"], signo=True)
emp = gr[gr["nivel"] == "empresa"]
filas = []
for prueba, k in CLAVE_P.items():
    g = emp[emp["prueba"] == prueba]
    sig = g[g["p"] < 0.05]
    poner(f"var.emp.{k}.sig", len(sig)); poner(f"var.emp.{k}.n", len(g)); poner(f"var.emp.{k}.positivas", int((sig["efecto_desvios"] > 0).sum()))
    mer = gr[(gr["nivel"] == "mercado") & (gr["prueba"] == prueba)]
    pm = pval(mer["p"].iloc[0]) if len(mer) else "—"
    celdas = [(prueba[0].upper() + prueba[1:]).replace("→", r"lecha{}"), pm, f"{len(sig)} de {len(g)}"]
    if len(sig) > 3:
        celdas = [f"\\textbf{{{c}}}" for c in celdas]
    filas.append(" & ".join(celdas) + " \\\\")
(TAB / "granger.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")
irf = pd.read_csv(ANX / "irf_mercado.csv")
for imp_, resp, k in (("ret_merval", "sentimiento_inesperado", "ret_ines"), ("sentimiento_inesperado", "ret_merval", "ines_ret")):
    for h in (0, 1, 2):
        x = irf[(irf["impulso"] == imp_) & (irf["respuesta"] == resp) & (irf["horizonte"] == h)].iloc[0]
        for c in ("irf", "banda_baja", "banda_alta"):
            poner(f"var.irf.{k}.h{h}.{c}", x[c])
poner("var.estables", int(pd.read_csv(ANX / "rezagos_var.csv")["estable"].sum()))
poner("var.modelos", len(pd.read_csv(ANX / "rezagos_var.csv")))

# ── 10. Regímenes (anexo) ────────────────────────────────────────────────
H = P3 / "regimen_hmm" / "salidas"
hmm = pd.read_csv(H / "hmm_regimen_mercado.csv")
ven = hmm[hmm["fecha"] >= "2025-05-05"]
filas = []
for reg in ("Calmo", "Moderado", "Tenso"):
    a, b = hmm[hmm["regimen_nombre"] == reg], ven[ven["regimen_nombre"] == reg]
    filas.append(f"{reg} & {num(a['vix_arg'].mean(), 1)}\\% & {num(len(a))} & {num(len(b))} & {num(int((ven['regimen_filtrado_nombre'] == reg).sum()))} \\\\")
    poner(f"hmm.{reg}.ruedas_ventana", len(b)); poner(f"hmm.{reg}.vix", round(a["vix_arg"].mean(), 1))
(TAB / "regimenes.tex").write_text("\n".join(filas) + "\n", encoding="utf-8")
poner("hmm.ruedas_total", len(hmm))
poner("hmm.coincidencia_filtrado_pct", round(100 * (hmm["regimen_nombre"] == hmm["regimen_filtrado_nombre"]).mean(), 1))
test_reg = ven[ven["fecha"] >= "2026-02-01"]["regimen_filtrado_nombre"].value_counts()
for reg in ("Calmo", "Moderado", "Tenso"):
    poner(f"hmm.test_{reg}", int(test_reg.get(reg, 0)))
tr = pd.read_csv(H / "matriz_transicion.csv", index_col=0)
(TAB / "transicion.tex").write_text("\n".join(f"{i} & " + " & ".join(f"{num(tr.loc[i, c], 1)}\\%" for c in tr.columns) + " \\\\" for i in tr.index) + "\n", encoding="utf-8")
bic = pd.read_csv(H / "bic_por_k.csv")
(TAB / "bic.tex").write_text("\n".join(
    (f"\\textbf{{{int(x['k'])}}} & \\textbf{{{num(x['bic'], 1)}}} & \\textbf{{Sí}} & \\textbf{{{num(int(x['min_dias_regimen']))} días}} & \\textbf{{Sí}} \\\\"
     if not x["degenerado"] else
     f"{int(x['k'])} & {num(x['bic'], 1)} & {'Sí' if x['convergio'] else 'No'} & {num(int(x['min_dias_regimen']))} día{'s' if x['min_dias_regimen'] > 1 else ''} & No \\\\")
    for _, x in bic.iterrows()) + "\n", encoding="utf-8")

# ── 11. Veredicto ────────────────────────────────────────────────────────
V = pd.read_csv(RAIZ / "5_evaluacion" / "veredicto_hipotesis" / "salidas" / "veredicto.csv")

# ── Escritura ────────────────────────────────────────────────────────────
lineas = ["% Generado por numeros.py: NO EDITAR A MANO. Cada número sale de los resultados del proyecto.",
          r"\makeatletter",
          r"\newcommand{\dato}[1]{\ifcsname dato@#1\endcsname\csname dato@#1\endcsname\else"
          r"\PackageError{numeros}{Falta el dato '#1'}{Correr numeros.py o revisar la clave}\fi}"]
for k, val in sorted(D.items()):
    if "{" in k or "}" in k or "\\" in k:
        continue
    lineas.append(f"\\expandafter\\def\\csname dato@{k}\\endcsname{{{val}}}")
lineas.append(r"\makeatother")
(GEN / "numeros.tex").write_text("\n".join(lineas) + "\n", encoding="utf-8")
print(f"{len(D)} datos y {len(list(TAB.glob('*.tex')))} tablas en {GEN.relative_to(AQUI)}")
