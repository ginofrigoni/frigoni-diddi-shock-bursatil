# -*- coding: utf-8 -*-
"""
Deteccion de duplicados semanticos (cross-posting) usando un LLM local via Ollama.

Contexto (ver AUDITORIA_CORPUS.md, hallazgo 4.2): ademas de los duplicados
exactos por URL (dedup_utils.deduplicar_entre_archivos), hay articulos que el
mismo portal publica dos veces bajo URLs distintas (ej. cross-posteado a
/economia/ y /finanzas/ con minutos de diferencia). Un match de titulo NO
alcanza: hay features recurrentes con titulo identico publicadas dia a dia
("dolar hoy: a cuanto cotiza este viernes...") que NO son duplicados.

Procedimiento:
  1. Agrupa articulos por titulo normalizado.
  2. Dentro de cada grupo arma sub-clusters de articulos publicados a menos de
     VENTANA_HORAS de diferencia; los mas separados se descartan como
     "feature recurrente" sin consultar al modelo.
  3. Cada sub-cluster candidato se le consulta a un modelo local (Ollama), salvo
     que ya tenga veredicto en el reporte anterior (INCREMENTAL: una corrida
     repetida solo consulta los grupos nuevos).
  4. El reporte se ACUMULA: veredictos + URLs eliminadas. Los scrapers leen
     esas URLs (dedup_utils.cargar_urls_ya_scrapeadas) para no volver a bajar
     un duplicado ya descartado.

Integracion: noticias_diario.py / noticias_sitemap.py / noticias_historico_v3.py
llaman post_scraping() al terminar. Si Ollama o el modelo no estan disponibles
se omite el paso con un aviso (el scraping nunca falla por esto).

Uso manual:
    python dedup_semantico_qwen.py --aplicar   # elimina duplicados confirmados
    python dedup_semantico_qwen.py             # solo genera el reporte
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timedelta

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CARPETA_RESULTADOS = "../resultados"
CARPETA_REPORTE = "../analisis_duplicados"
VENTANA_HORAS = 48
MODELO = "qwen3.8"
OLLAMA_BASE = "http://localhost:11434"
OLLAMA_URL = OLLAMA_BASE + "/api/generate"


# ─────────────────────────────────────────────────────────────────
# CORPUS Y CANDIDATOS
# ─────────────────────────────────────────────────────────────────

def cargar_corpus(carpeta):
    articulos = []
    for nombre in sorted(os.listdir(carpeta)):
        if not nombre.endswith(".jsonl"):
            continue
        with open(os.path.join(carpeta, nombre), encoding="utf-8") as f:
            for linea in f:
                linea = linea.strip()
                if not linea:
                    continue
                try:
                    art = json.loads(linea)
                except Exception:
                    continue
                articulos.append({
                    "fuente": nombre.replace(".jsonl", ""),
                    "archivo": nombre,
                    "url": art.get("url"),
                    "titulo": art.get("titulo"),
                    "fecha": art.get("fecha_publicacion") or art.get("fecha_sitemap") or art.get("fecha_descarga"),
                    "contenido": (art.get("contenido") or "")[:700],
                })
    return articulos


def parsear_fecha(s):
    if not s:
        return None
    try:
        return datetime.strptime(s[:19].replace("T", " "), "%Y-%m-%d %H:%M:%S")
    except Exception:
        try:
            return datetime.strptime(s[:10], "%Y-%m-%d")
        except Exception:
            return None


def armar_candidatos(articulos, ventana_horas=VENTANA_HORAS):
    por_titulo = {}
    for a in articulos:
        if not a["titulo"]:
            continue
        key = re.sub(r"\s+", " ", a["titulo"].strip().lower())
        por_titulo.setdefault(key, []).append(a)

    grupos = []
    descartados = 0
    for titulo, arts in por_titulo.items():
        if len(arts) < 2:
            continue
        con_fecha = [(parsear_fecha(a["fecha"]), a) for a in arts]
        con_fecha = sorted([(f, a) for f, a in con_fecha if f is not None], key=lambda x: x[0])

        cluster = []
        for f, a in con_fecha:
            if not cluster:
                cluster = [(f, a)]
                continue
            if f - cluster[-1][0] <= timedelta(hours=ventana_horas):
                cluster.append((f, a))
            else:
                if len(cluster) > 1:
                    grupos.append({"titulo": titulo, "articulos": [x for _, x in cluster]})
                else:
                    descartados += 1
                cluster = [(f, a)]
        if len(cluster) > 1:
            grupos.append({"titulo": titulo, "articulos": [x for _, x in cluster]})
        elif cluster:
            descartados += 1
    return grupos, descartados


# ─────────────────────────────────────────────────────────────────
# LLM LOCAL (OLLAMA)
# ─────────────────────────────────────────────────────────────────

PROMPT_TEMPLATE = """Sos un asistente que ayuda a limpiar un corpus de noticias economicas argentinas. \
Te paso {n} articulos que tienen el MISMO titulo (o casi) y fueron publicados con menos de {ventana}hs de diferencia. \
Necesito que decidas si son LA MISMA nota republicada dos veces (cross-posting: el sitio la publico en dos secciones, \
o el scraper la bajo dos veces), o si son notas REALMENTE DISTINTAS que coinciden en el titulo por casualidad \
(por ejemplo, una correccion/actualizacion con contenido nuevo, o una coincidencia de tema).

Articulos:
{articulos}

Respondé UNICAMENTE con un JSON valido, sin texto antes ni despues, con este formato exacto:
{{"duplicado": true/false, "razon": "explicacion breve en una oracion", "url_canonica": "la URL que conviene conservar (la mas completa o la primera publicada), o null si duplicado es false"}}
"""


def ollama_disponible():
    """True si Ollama responde y el modelo esta descargado (no lanza excepciones)."""
    try:
        with urllib.request.urlopen(OLLAMA_BASE + "/api/tags", timeout=3) as resp:
            modelos = [m.get("name", "") for m in json.loads(resp.read().decode("utf-8")).get("models", [])]
        return any(m == MODELO or m.startswith(MODELO + ":") for m in modelos)
    except Exception:
        return False


def formatear_articulos(arts):
    return "\n\n".join(
        f"[{i}] fuente={a['fuente']} fecha={a['fecha']} url={a['url']}\n    contenido: {a['contenido'][:500]}"
        for i, a in enumerate(arts, 1)
    )


def extraer_json(texto):
    texto = re.sub(r"```$", "", re.sub(r"^```(json)?", "", texto.strip()).strip())
    inicio = texto.find("{")
    if inicio == -1:
        raise ValueError("sin JSON en la respuesta")
    profundidad = 0
    for i in range(inicio, len(texto)):
        if texto[i] == "{":
            profundidad += 1
        elif texto[i] == "}":
            profundidad -= 1
            if profundidad == 0:
                return json.loads(texto[inicio:i + 1])
    raise ValueError("JSON sin cerrar en la respuesta")


def consultar_ollama(prompt, reintentos=2):
    payload = json.dumps({
        "model": MODELO, "prompt": prompt, "stream": False, "format": "json",
        "options": {"temperature": 0.1},
    }).encode("utf-8")
    for intento in range(reintentos + 1):
        try:
            req = urllib.request.Request(OLLAMA_URL, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            # qwen3.8 a veces vuelca el JSON dentro de "thinking" y deja "response" vacio.
            texto = data.get("response") or ""
            if not texto.strip():
                texto = data.get("thinking") or ""
            return extraer_json(texto)
        except Exception as e:
            if intento == reintentos:
                return {"duplicado": None, "razon": f"error de consulta: {e}", "url_canonica": None}
            time.sleep(2)


def evaluar_grupo(grupo):
    prompt = PROMPT_TEMPLATE.format(n=len(grupo["articulos"]), ventana=VENTANA_HORAS,
                                    articulos=formatear_articulos(grupo["articulos"]))
    return consultar_ollama(prompt)


# ─────────────────────────────────────────────────────────────────
# REPORTE ACUMULADO + APLICACION
# ─────────────────────────────────────────────────────────────────

def ruta_reporte():
    return os.path.join(CARPETA_REPORTE, "reporte_dedup_semantico.json")


def cargar_reporte_previo():
    try:
        with open(ruta_reporte(), encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"detalle": [], "urls_a_eliminar": []}


def clave_grupo(urls):
    return "|".join(sorted(urls))


def eliminar_urls(urls_a_eliminar, verbose=True):
    """Quita las URLs de resultados/*.jsonl y deja los .json consistentes."""
    from calidad_utils import sincronizar_json
    cambios = {}
    for nombre in sorted(os.listdir(CARPETA_RESULTADOS)):
        if not nombre.endswith(".jsonl"):
            continue
        ruta = os.path.join(CARPETA_RESULTADOS, nombre)
        with open(ruta, encoding="utf-8") as f:
            lineas = [l.strip() for l in f if l.strip()]
        finales = []
        for l in lineas:
            try:
                if json.loads(l).get("url") in urls_a_eliminar:
                    continue
            except Exception:
                pass
            finales.append(l)
        if len(finales) != len(lineas):
            with open(ruta, "w", encoding="utf-8") as f:
                for l in finales:
                    f.write(l + "\n")
            sincronizar_json(ruta)
            cambios[nombre] = (len(lineas), len(finales))
            if verbose:
                print(f"  {nombre}: {len(lineas)} -> {len(finales)} ({len(lineas) - len(finales)} eliminados)")
    return cambios


def ejecutar(aplicar=True, verbose=True):
    """Corre el procedimiento completo (incremental). Devuelve un dict con estadisticas."""
    os.makedirs(CARPETA_REPORTE, exist_ok=True)
    previo = cargar_reporte_previo()
    cache = {}
    for d in previo.get("detalle", []):
        if d.get("veredicto", {}).get("duplicado") is not None:
            cache[clave_grupo([a["url"] for a in d["articulos"]])] = d

    articulos = cargar_corpus(CARPETA_RESULTADOS)
    grupos, descartados = armar_candidatos(articulos)
    nuevos = [g for g in grupos if clave_grupo([a["url"] for a in g["articulos"]]) not in cache]
    if verbose:
        print(f"Dedup semantico: {len(articulos)} articulos | {len(grupos)} grupos candidatos "
              f"({descartados} descartados por ventana) | {len(grupos) - len(nuevos)} con veredicto previo | {len(nuevos)} a consultar")

    detalle = list(previo.get("detalle", []))
    urls_a_eliminar = set(previo.get("urls_a_eliminar", []))
    n_nuevos_dup = 0
    for i, grupo in enumerate(nuevos, 1):
        urls = [a["url"] for a in grupo["articulos"]]
        veredicto = evaluar_grupo(grupo)
        if verbose:
            print(f"  [{i}/{len(nuevos)}] \"{grupo['titulo'][:60]}\" -> duplicado={veredicto.get('duplicado')}")
        detalle.append({
            "titulo": grupo["titulo"],
            "articulos": [{"fuente": a["fuente"], "url": a["url"], "fecha": a["fecha"]} for a in grupo["articulos"]],
            "veredicto": veredicto,
        })
        if veredicto.get("duplicado") is True:
            canonica = veredicto.get("url_canonica")
            for u in urls:
                if u != canonica:
                    urls_a_eliminar.add(u)
                    n_nuevos_dup += 1

    with open(ruta_reporte(), "w", encoding="utf-8") as f:
        json.dump({
            "modelo": MODELO, "ventana_horas": VENTANA_HORAS,
            "actualizado": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "grupos_evaluados": len(detalle),
            "grupos_marcados_duplicado": sum(1 for d in detalle if d["veredicto"].get("duplicado") is True),
            "urls_a_eliminar": sorted(urls_a_eliminar),
            "detalle": detalle,
        }, f, ensure_ascii=False, indent=2)

    eliminados = {}
    if aplicar and urls_a_eliminar:
        eliminados = eliminar_urls(urls_a_eliminar, verbose=verbose)
    return {"consultados": len(nuevos), "duplicados_nuevos": n_nuevos_dup, "eliminados": eliminados}


def post_scraping():
    """Gancho para los scrapers: corre el dedup semantico si Ollama esta disponible."""
    if not ollama_disponible():
        print(f"[AVISO] Ollama / modelo '{MODELO}' no disponible: se omite el dedup semantico "
              f"(correr dedup_semantico_qwen.py --aplicar cuando este disponible).")
        return None
    return ejecutar(aplicar=True)


def main():
    ap = argparse.ArgumentParser(description="Dedup semantico via LLM local (Ollama)")
    ap.add_argument("--aplicar", action="store_true", help="elimina de resultados/*.jsonl las URLs duplicadas confirmadas")
    args = ap.parse_args()
    if not ollama_disponible():
        print(f"Ollama no responde en {OLLAMA_BASE} o falta el modelo '{MODELO}' (ollama pull {MODELO}).")
        sys.exit(1)
    stats = ejecutar(aplicar=args.aplicar)
    print("\nResultado:", stats)
    if not args.aplicar:
        print("(no se aplico ningun cambio -- correr con --aplicar para eliminar los duplicados confirmados)")


if __name__ == "__main__":
    main()
