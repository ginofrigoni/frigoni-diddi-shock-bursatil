"""
serie_completa_finetuned.py
===========================
Corre FinBETO (modelo finetuneado) sobre TODOS los artículos del corpus
y genera la serie temporal diaria de sentimiento con detección de shocks.

Outputs en resultados_beto/:
  finetuned_articulos.csv      — un artículo por fila con métricas agregadas
  finetuned_serie_diaria.csv   — serie temporal diaria con shocks

Checkpoint: resultados_beto/checkpoint_finetuned.jsonl
  → nunca borrar, permite reanudar si el proceso se corta.

Uso:
    python serie_completa_finetuned.py
    python serie_completa_finetuned.py --batch-size 64   # si tenés más VRAM
    python serie_completa_finetuned.py --solo-serie       # skip inferencia, solo recalcula la serie
"""

import json
import re
import csv
import argparse
import os
import sys
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # consolas Windows cp1252 no imprimen "✓"
from collections import Counter
from datetime import datetime

# ─────────────────────────────────────────────────────────────────
# CONFIGURACIÓN
# ─────────────────────────────────────────────────────────────────

BASE_DIR        = Path(__file__).parent
JSONL_DIR       = BASE_DIR.parent / "noticias" / "resultados"
MODELO_DIR      = BASE_DIR / "beto_finetuned"
OUTPUT_DIR      = BASE_DIR
CHECKPOINT_PATH = OUTPUT_DIR / "checkpoint_finetuned.jsonl"
OUT_ARTICULOS   = OUTPUT_DIR / "finetuned_articulos.csv"
OUT_SERIE       = OUTPUT_DIR / "finetuned_serie_diaria.csv"

MIN_LARGO_ORACION  = 30   # chars mínimos por oración
MAX_TOKENS         = 512  # límite BETO
VENTANA_SHOCK      = 7    # días para la media móvil
SIGMA_SHOCK        = 1.5  # umbral de detección de shocks (±1.5σ)
MIN_ARTICULOS_DIA  = 5    # mínimo de artículos para considerar shock

JSONL_FILES = [
    "ambito_economia.jsonl",
    "ambito_finanzas.jsonl",
    "clarin_economia.jsonl",
    "clarin_sitemap.jsonl",
    "eleconomista_sitemap.jsonl",
    "infobae_economia.jsonl",
    "iprofesional_sitemap.jsonl",
    "lanacion_economia.jsonl",
    "tn_economia.jsonl",
]

# ─────────────────────────────────────────────────────────────────
# ARGS
# ─────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument("--batch-size", type=int, default=32,
                    help="Oraciones por batch de inferencia (default 32)")
parser.add_argument("--solo-serie", action="store_true",
                    help="Saltar la inferencia y solo recalcular la serie diaria")
parser.add_argument("--desde-oraciones", action="store_true",
                    help="Armar el sentimiento por articulo desde beto_oraciones_finetuned.csv (titulo + cuerpo, "
                         "el mismo archivo que usa el cruce NER x sentimiento), sin las oraciones de relleno. "
                         "No usa el modelo ni el checkpoint.")
ARGS = parser.parse_args()

# ─────────────────────────────────────────────────────────────────
# SENTENCE SPLITTER
# ─────────────────────────────────────────────────────────────────

def split_oraciones(texto: str) -> list[str]:
    try:
        import nltk
        try:
            tok = nltk.data.load("tokenizers/punkt_tab/Spanish.pickle")
        except Exception:
            try:
                tok = nltk.data.load("tokenizers/punkt/Spanish.pickle")
            except Exception:
                nltk.download("punkt", quiet=True)
                nltk.download("punkt_tab", quiet=True)
                tok = nltk.data.load("tokenizers/punkt/Spanish.pickle")
        ors = tok.tokenize(texto)
    except Exception:
        ors = re.split(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚÑÜ\"])", texto)

    resultado = []
    for o in ors:
        o = re.sub(r"\s+", " ", o.strip().replace("\n", " "))
        if len(o) >= MIN_LARGO_ORACION:
            resultado.append(o)
    return resultado

# ─────────────────────────────────────────────────────────────────
# CARGAR CORPUS
# ─────────────────────────────────────────────────────────────────

def cargar_urls_duplicadas_semantico() -> set[str]:
    """
    URLs marcadas como cross-posting (mismo hecho, URL distinta) por
    dedup_semantico_qwen.py -- ver .../noticias/analisis_duplicados/reporte_dedup_semantico.json.
    Se excluyen aca tambien para que un re-run desde cero no las vuelva a sumar.
    """
    reporte = JSONL_DIR.parent / "analisis_duplicados" / "reporte_dedup_semantico.json"
    if not reporte.exists():
        return set()
    with open(reporte, encoding="utf-8") as f:
        data = json.load(f)
    return set(data.get("urls_a_eliminar", []))


def cargar_corpus() -> list[dict]:
    """
    Carga los 9 .jsonl y deduplica por URL (ver AUDITORIA_CORPUS.md 4.1:
    205 articulos de Clarin se bajaron dos veces por dos scripts distintos
    y llegaron sin filtrar hasta esta serie). Tambien excluye los
    duplicados semanticos (cross-posting, URL distinta) ya detectados.
    Se queda con la PRIMERA aparicion de cada URL (orden de JSONL_FILES).
    """
    urls_semanticas_dup = cargar_urls_duplicadas_semantico()
    articulos = []
    urls_vistas = set()
    n_dup_exacto = 0
    n_dup_semantico = 0
    for fname in JSONL_FILES:
        fpath = JSONL_DIR / fname
        if not fpath.exists():
            print(f"  ⚠ No encontrado: {fpath}")
            continue
        n = 0
        for line in open(fpath, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            art = json.loads(line)
            url = art.get("url")
            if url in urls_semanticas_dup:
                n_dup_semantico += 1
                continue
            if url and url in urls_vistas:
                n_dup_exacto += 1
                continue
            if url:
                urls_vistas.add(url)
            art["_fuente"] = fname.replace(".jsonl", "")
            articulos.append(art)
            n += 1
        print(f"  {fname}: {n} artículos")
    if n_dup_exacto or n_dup_semantico:
        print(f"  (excluidos: {n_dup_exacto} duplicados exactos + {n_dup_semantico} duplicados semanticos)")
    print(f"  Total: {len(articulos)} artículos\n")
    return articulos

# ─────────────────────────────────────────────────────────────────
# CHECKPOINT
# ─────────────────────────────────────────────────────────────────

def sincronizar_checkpoint_con_corpus() -> tuple[int, int, int]:
    """
    Alinea el checkpoint con el corpus ACTUAL sin volver a correr el modelo:
      - descarta las filas de URLs que ya no estan en el corpus (depuracion,
        deduplicacion exacta o semantica) -- si no, esos articulos seguirian
        sumando a la serie diaria;
      - refresca 'fecha' desde fecha_publicacion del corpus (ej. fechas
        recuperadas despues de la inferencia: noticias/scripts/recuperar_metadatos.py).
    Devuelve (filas_descartadas, fechas_actualizadas, filas_finales).
    Reescribe el checkpoint solo si hubo cambios.
    """
    if not CHECKPOINT_PATH.exists():
        return 0, 0, 0
    excluir = cargar_urls_duplicadas_semantico()
    fecha_por_url: dict[str, str] = {}
    for fname in JSONL_FILES:
        fpath = JSONL_DIR / fname
        if not fpath.exists():
            continue
        for line in open(fpath, encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            art = json.loads(line)
            url = art.get("url")
            if url and url not in excluir and url not in fecha_por_url:
                fecha_por_url[url] = (art.get("fecha_publicacion") or "")[:10]

    finales, vistas = [], set()
    n_desc = n_fecha = 0
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            url = rec.get("url")
            if url not in fecha_por_url or url in vistas:
                n_desc += 1
                continue
            vistas.add(url)
            nueva = fecha_por_url[url]
            if nueva and rec.get("fecha") != nueva:
                rec["fecha"] = nueva
                n_fecha += 1
            finales.append(rec)

    if n_desc or n_fecha:
        tmp = CHECKPOINT_PATH.with_suffix(".jsonl.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            for rec in finales:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        os.replace(tmp, CHECKPOINT_PATH)
    print(f"  Checkpoint sincronizado con el corpus: -{n_desc} filas, {n_fecha} fechas actualizadas, {len(finales)} filas finales")
    return n_desc, n_fecha, len(finales)


def cargar_checkpoint() -> set:
    """Retorna el conjunto de URLs ya procesadas."""
    procesadas = set()
    if not CHECKPOINT_PATH.exists():
        return procesadas
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
                if rec.get("url"):
                    procesadas.add(rec["url"])
            except Exception:
                pass
    return procesadas

# ─────────────────────────────────────────────────────────────────
# AGREGACIÓN POR ARTÍCULO
# ─────────────────────────────────────────────────────────────────

def agregar(preds: list[dict]) -> dict:
    labels  = [p["label"] for p in preds]
    scores  = [p["score"] for p in preds]
    conteo  = Counter(labels)
    total   = len(labels)
    pct     = {l: round(conteo.get(l, 0) / total * 100, 2) for l in ("POS","NEG","NEU","MIXTO")}
    # sent_neto: POS aporta +1, NEG -1, NEU y MIXTO 0
    sent_neto = round(pct["POS"] - pct["NEG"], 2)
    return {
        "n_oraciones":    total,
        "label_dominante": conteo.most_common(1)[0][0] if conteo else "NEU",
        "pct_pos":        pct["POS"],
        "pct_neg":        pct["NEG"],
        "pct_neu":        pct["NEU"],
        "pct_mixto":      pct["MIXTO"],
        "sent_neto":      sent_neto,
        "n_pos":          conteo.get("POS",   0),
        "n_neg":          conteo.get("NEG",   0),
        "n_neu":          conteo.get("NEU",   0),
        "n_mixto":        conteo.get("MIXTO", 0),
        "score_promedio": round(sum(scores) / total, 4),
    }

# ─────────────────────────────────────────────────────────────────
# INFERENCIA SOBRE TODO EL CORPUS
# ─────────────────────────────────────────────────────────────────

def run_inferencia(articulos: list[dict], batch_size: int):
    import torch
    from transformers import pipeline

    ya_procesadas = cargar_checkpoint()
    pendientes    = [a for a in articulos if a.get("url") not in ya_procesadas]

    print(f"Ya procesados (checkpoint): {len(ya_procesadas)}")
    print(f"Pendientes:                 {len(pendientes)}\n")

    if not pendientes:
        print("✓ Todo ya procesado. Pasando a generación de serie.\n")
        return

    device = 0 if torch.cuda.is_available() else -1
    if device == 0:
        print(f"✓ GPU detectada: {torch.cuda.get_device_name(0)}\n")
    else:
        print("⚠ GPU no detectada. Usando CPU — puede tardar mucho.\n")

    print(f"Cargando modelo desde: {MODELO_DIR}")
    clf = pipeline(
        "text-classification",
        model=str(MODELO_DIR),
        tokenizer=str(MODELO_DIR),
        device=device,
        truncation=True,
        max_length=MAX_TOKENS,
    )
    print("✓ Modelo cargado.\n")

    OUTPUT_DIR.mkdir(exist_ok=True)
    ckpt_f = open(CHECKPOINT_PATH, "a", encoding="utf-8")

    for i, art in enumerate(pendientes):
        url      = art.get("url", "")
        titulo   = art.get("titulo", "")[:70]
        fuente   = art.get("_fuente", "")
        fecha    = (art.get("fecha_publicacion") or "")[:10]
        contenido = art.get("contenido") or ""

        print(f"[{i+1:>5}/{len(pendientes)}] {fuente} | {titulo}")

        ors = split_oraciones(contenido)
        if not ors:
            print("  → Sin oraciones válidas, saltando.\n")
            continue

        preds = clf(ors, batch_size=batch_size)
        # normalizar labels (el pipeline puede devolver str o dict)
        preds_norm = []
        for p in preds:
            if isinstance(p, dict):
                preds_norm.append({"label": p["label"], "score": p["score"]})
            else:
                preds_norm.append({"label": p[0]["label"], "score": p[0]["score"]})

        agr = agregar(preds_norm)
        registro = {
            "url":    url,
            "fuente": fuente,
            "fecha":  fecha,
            "titulo": art.get("titulo", ""),
            **agr,
        }

        ckpt_f.write(json.dumps(registro, ensure_ascii=False) + "\n")
        ckpt_f.flush()

        print(f"  → {agr['label_dominante']} | "
              f"POS {agr['pct_pos']}% NEG {agr['pct_neg']}% "
              f"NEU {agr['pct_neu']}% MIXTO {agr['pct_mixto']}% | "
              f"sent_neto={agr['sent_neto']}\n")

    ckpt_f.close()
    print("✓ Inferencia completada.\n")

# ─────────────────────────────────────────────────────────────────
# EXPORTAR CSV DE ARTÍCULOS
# ─────────────────────────────────────────────────────────────────

def exportar_articulos() -> list[dict]:
    registros = []
    with open(CHECKPOINT_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                registros.append(json.loads(line))
            except Exception:
                pass

    campos = ["url","fuente","fecha","titulo","n_oraciones","label_dominante",
              "pct_pos","pct_neg","pct_neu","pct_mixto","sent_neto",
              "n_pos","n_neg","n_neu","n_mixto","score_promedio"]
    with open(OUT_ARTICULOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(registros)

    print(f"✓ {OUT_ARTICULOS.name}: {len(registros)} artículos exportados")
    return registros


ORACIONES_PATH = OUTPUT_DIR / "beto_oraciones_finetuned.csv"


def registros_desde_oraciones() -> list[dict]:
    """
    Sentimiento por articulo a partir del sentimiento por oracion (beto_oraciones_finetuned.csv).

    Por que (revision del 2026-10-18): el checkpoint y el archivo por oracion son dos corridas del mismo
    modelo con criterios distintos (el checkpoint clasifico solo el cuerpo de la nota; el archivo por
    oracion, titulo + cuerpo con oraciones de 30 a 600 caracteres). La serie usaba el primero y el
    cruce NER x sentimiento el segundo. Armar la serie desde el archivo por oracion deja una sola
    clasificacion para las dos cosas.

    Ademas se excluyen las oraciones de relleno que el scraping dejo dentro del texto ("Sobre la firma",
    "Newsletter Clarin", "PUBLICIDAD PUBLICIDAD PUBLICIDAD"...): mismas reglas que limpiar_etiquetado.py
    (la oracion tenia marcas de relleno y sin ellas no queda una oracion). Las oraciones reales con una
    marca pegada ("PUBLICIDAD El ministro...") se conservan con su etiqueta.
    """
    from limpiar_etiquetado import MIN_LETRAS, limpiar

    articulos = cargar_corpus()
    por_url = {a["url"]: a for a in articulos}
    oraciones = {}            # url -> {or_idx: (label, score)}
    n_relleno = 0
    with open(ORACIONES_PATH, encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            url = r["url"]
            if url not in por_url:
                continue
            d = oraciones.setdefault(url, {})
            if r["or_idx"] in d:
                continue      # la misma oracion repetida (corpus viejo con URLs duplicadas)
            texto = r["oracion"].strip()
            sin_marca = limpiar(texto)
            letras = len(re.findall(r"[A-Za-zÁÉÍÓÚÑáéíóúñü]", sin_marca))
            if sin_marca != texto and letras < MIN_LETRAS:
                n_relleno += 1
                d[r["or_idx"]] = None
                continue
            d[r["or_idx"]] = {"label": r["label"], "score": float(r["score"])}

    registros, sin_oraciones = [], 0
    for url, art in por_url.items():
        preds = [p for p in oraciones.get(url, {}).values() if p is not None]
        if not preds:
            sin_oraciones += 1
            continue
        registros.append({"url": url, "fuente": art["_fuente"],
                          "fecha": (art.get("fecha_publicacion") or "")[:10],
                          "titulo": art.get("titulo", ""), **agregar(preds)})

    n_total = sum(len(d) for d in oraciones.values())
    print(f"  Oraciones de articulos del corpus: {n_total}  |  relleno excluido: {n_relleno}  |  "
          f"usadas: {n_total - n_relleno}")
    print(f"  Articulos con sentimiento: {len(registros)}  |  sin oraciones: {sin_oraciones}")

    campos = ["url","fuente","fecha","titulo","n_oraciones","label_dominante",
              "pct_pos","pct_neg","pct_neu","pct_mixto","sent_neto",
              "n_pos","n_neg","n_neu","n_mixto","score_promedio"]
    with open(OUT_ARTICULOS, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        w.writerows(registros)
    print(f"✓ {OUT_ARTICULOS.name}: {len(registros)} artículos exportados")
    return registros

# ─────────────────────────────────────────────────────────────────
# SERIE TEMPORAL DIARIA
# ─────────────────────────────────────────────────────────────────

def generar_serie(registros: list[dict]):
    import statistics

    # Agrupar por fecha
    por_fecha: dict[str, list] = {}
    for r in registros:
        fecha = r.get("fecha", "")
        if not fecha or len(fecha) < 10:
            continue
        fecha = fecha[:10]  # solo YYYY-MM-DD
        por_fecha.setdefault(fecha, []).append(r)

    if not por_fecha:
        print("⚠ Sin fechas válidas para construir la serie.")
        return

    fecha_min = min(por_fecha)
    fecha_max = max(por_fecha)
    print(f"  Rango de fechas: {fecha_min} → {fecha_max}")
    print(f"  Días con datos: {len(por_fecha)}")

    # Construir serie con TODOS los días del rango
    from datetime import date, timedelta
    d_ini = date.fromisoformat(fecha_min)
    d_fin = date.fromisoformat(fecha_max)
    todos_dias = []
    d = d_ini
    while d <= d_fin:
        todos_dias.append(d.isoformat())
        d += timedelta(days=1)

    # Calcular métricas diarias
    filas = []
    for fecha in todos_dias:
        arts = por_fecha.get(fecha, [])
        if arts:
            n = len(arts)
            sent_neto   = round(sum(a["sent_neto"]  for a in arts) / n, 4)
            pct_pos     = round(sum(a["pct_pos"]    for a in arts) / n, 4)
            pct_neg     = round(sum(a["pct_neg"]    for a in arts) / n, 4)
            pct_neu     = round(sum(a["pct_neu"]    for a in arts) / n, 4)
            pct_mixto   = round(sum(a["pct_mixto"]  for a in arts) / n, 4)
        else:
            n = sent_neto = pct_pos = pct_neg = pct_neu = pct_mixto = None

        filas.append({
            "fecha":     fecha,
            "n_articulos": n,
            "sent_neto": sent_neto,
            "pct_pos":   pct_pos,
            "pct_neg":   pct_neg,
            "pct_neu":   pct_neu,
            "pct_mixto": pct_mixto,
        })

    # Media móvil y bandas de shock (solo sobre días con datos)
    valores_con_fecha = [(f["fecha"], f["sent_neto"]) for f in filas if f["sent_neto"] is not None]

    mm_map = {}
    std_map = {}
    for idx, (fecha, _) in enumerate(valores_con_fecha):
        ventana = [v for _, v in valores_con_fecha[max(0, idx - VENTANA_SHOCK + 1): idx + 1]]
        if len(ventana) >= 2:
            mm_map[fecha]  = round(sum(ventana) / len(ventana), 4)
            std_map[fecha] = round(statistics.stdev(ventana), 4)
        else:
            mm_map[fecha]  = None
            std_map[fecha] = None

    # Agregar columnas de shock
    for fila in filas:
        fecha     = fila["fecha"]
        mm        = mm_map.get(fecha)
        std       = std_map.get(fecha)
        sent_neto = fila["sent_neto"]

        fila["mm7"]       = mm
        fila["std7"]      = std
        fila["banda_sup"] = round(mm + SIGMA_SHOCK * std, 4) if (mm is not None and std is not None) else None
        fila["banda_inf"] = round(mm - SIGMA_SHOCK * std, 4) if (mm is not None and std is not None) else None

        n_arts = fila.get("n_articulos") or 0
        if sent_neto is not None and mm is not None and std is not None and n_arts >= MIN_ARTICULOS_DIA:
            fila["shock_pos"] = sent_neto > mm + SIGMA_SHOCK * std
            fila["shock_neg"] = sent_neto < mm - SIGMA_SHOCK * std
            fila["shock"]     = fila["shock_pos"] or fila["shock_neg"]
        else:
            fila["shock_pos"] = fila["shock_neg"] = fila["shock"] = False

    # Guardar CSV
    campos = ["fecha","n_articulos","sent_neto","pct_pos","pct_neg","pct_neu","pct_mixto",
              "mm7","std7","banda_sup","banda_inf","shock_pos","shock_neg","shock"]
    with open(OUT_SERIE, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=campos)
        w.writeheader()
        w.writerows(filas)

    n_shocks = sum(1 for f in filas if f["shock"])
    n_sp     = sum(1 for f in filas if f["shock_pos"])
    n_sn     = sum(1 for f in filas if f["shock_neg"])
    print(f"✓ {OUT_SERIE.name} guardado:")
    print(f"  Total días:     {len(filas)}")
    print(f"  Días con datos: {sum(1 for f in filas if f['n_articulos'])}")
    print(f"  Shocks totales: {n_shocks} ({n_sp} positivos, {n_sn} negativos)")

# ─────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    print("=" * 65)
    print("  FinBETO — Serie temporal completa sobre corpus de noticias")
    print("=" * 65)
    print(f"  Modelo:     {MODELO_DIR}")
    print(f"  Corpus:     {JSONL_DIR}")
    print(f"  Checkpoint: {CHECKPOINT_PATH}")
    print(f"  Ventana shock: ±{SIGMA_SHOCK}σ sobre MM{VENTANA_SHOCK}, mín {MIN_ARTICULOS_DIA} arts/día")
    print("=" * 65 + "\n")

    if ARGS.desde_oraciones:
        print("[ --desde-oraciones: sentimiento por articulo desde beto_oraciones_finetuned.csv, sin relleno ]\n")
        registros = registros_desde_oraciones()
        print("\n[ Generando serie temporal diaria ]\n")
        generar_serie(registros)
        print("\n✓ Listo. Archivos en:", OUTPUT_DIR)
        print(f"  - {OUT_ARTICULOS.name}")
        print(f"  - {OUT_SERIE.name}")
        return

    if not ARGS.solo_serie:
        print("[ PASO 1 — Cargando corpus ]\n")
        articulos = cargar_corpus()

        print("[ PASO 2 — Inferencia con FinBETO ]\n")
        run_inferencia(articulos, ARGS.batch_size)
    else:
        print("[ --solo-serie: saltando inferencia ]\n")

    if not CHECKPOINT_PATH.exists():
        print("⚠ No hay checkpoint. Corré sin --solo-serie primero.")
        return

    print("[ PASO 3 — Sincronizando checkpoint con el corpus y exportando artículos ]\n")
    sincronizar_checkpoint_con_corpus()
    registros = exportar_articulos()

    print("\n[ PASO 4 — Generando serie temporal diaria ]\n")
    generar_serie(registros)

    print("\n✓ Listo. Archivos en:", OUTPUT_DIR)
    print(f"  - {OUT_ARTICULOS.name}")
    print(f"  - {OUT_SERIE.name}")


if __name__ == "__main__":
    main()
