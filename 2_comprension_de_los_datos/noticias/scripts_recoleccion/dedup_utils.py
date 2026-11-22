# -*- coding: utf-8 -*-
"""
Utilidades de deduplicacion compartidas por los scrapers de noticias.

Motivacion (ver AUDITORIA_CORPUS.md): cada script solo chequeaba su propio
checkpoint (su propio .jsonl) antes de bajar una URL, pero no sabia si esa
misma URL ya habia sido bajada por OTRO script hacia OTRO archivo. Asi se
duplicaron 205 articulos de Clarin: noticias_historico_v3.py los bajo hacia
clarin_economia.jsonl, y noticias_sitemap.py bajo las MISMAS URLs otra vez
hacia clarin_sitemap.jsonl. Esa duplicacion llego sin filtrarse hasta la
serie diaria de sentimiento (pesando el doble).

Estas funciones resuelven dos cosas distintas:
  1. Prevencion a futuro: cargar_urls_ya_scrapeadas() para que un scraper
     chequee contra TODOS los .jsonl de resultados/, no solo el suyo.
  2. Limpieza del corpus ya existente: deduplicar_entre_archivos().
"""

import json
import os


def cargar_urls_de_archivo(ruta_jsonl):
    """Lee un .jsonl y devuelve el set de URLs que contiene (vacio si no existe)."""
    urls = set()
    if not os.path.exists(ruta_jsonl):
        return urls
    with open(ruta_jsonl, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            try:
                art = json.loads(linea)
                if art.get("url"):
                    urls.add(art["url"])
            except Exception:
                continue
    return urls


def cargar_urls_ya_scrapeadas(carpeta_resultados):
    """
    Devuelve el set de URLs ya presentes en CUALQUIER .jsonl de carpeta_resultados.
    Se usa como checkpoint global: se une a (o reemplaza a) el checkpoint propio
    de cada script para que ningun scraper vuelva a bajar una nota que otro
    scraper ya bajo hacia un archivo distinto.
    """
    todas = set()
    if not os.path.isdir(carpeta_resultados):
        return todas
    for nombre in sorted(os.listdir(carpeta_resultados)):
        if nombre.endswith(".jsonl"):
            todas |= cargar_urls_de_archivo(os.path.join(carpeta_resultados, nombre))
    # Duplicados semanticos ya descartados (dedup_semantico_qwen.py): no estan en
    # ningun .jsonl, pero el sitemap sigue listandolos -- sin esto se volverian a bajar.
    reporte = os.path.join(carpeta_resultados, "..", "analisis_duplicados", "reporte_dedup_semantico.json")
    try:
        with open(reporte, "r", encoding="utf-8") as f:
            todas |= set(json.load(f).get("urls_a_eliminar", []))
    except Exception:
        pass
    # URLs eliminadas por depurar_corpus.py / depurar_plantillas.py (analisis_calidad/depuracion_*.json):
    # tampoco estan en ningun .jsonl y el sitemap las sigue listando.
    carpeta_calidad = os.path.join(carpeta_resultados, "..", "analisis_calidad")
    if os.path.isdir(carpeta_calidad):
        for nombre in sorted(os.listdir(carpeta_calidad)):
            if nombre.startswith("depuracion_") and nombre.endswith(".json"):
                try:
                    with open(os.path.join(carpeta_calidad, nombre), "r", encoding="utf-8") as f:
                        todas |= {e["url"] for e in json.load(f).get("eliminadas", [])}
                except Exception:
                    pass
    return todas


def deduplicar_jsonl(ruta_jsonl, ruta_salida=None):
    """
    Reescribe un .jsonl quedandose con la PRIMERA aparicion de cada URL
    (dedup interno, dentro de un mismo archivo).
    Devuelve (n_originales, n_finales, n_eliminados).
    """
    if ruta_salida is None:
        ruta_salida = ruta_jsonl

    vistos = set()
    filas_finales = []
    n_originales = 0

    with open(ruta_jsonl, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea:
                continue
            n_originales += 1
            try:
                art = json.loads(linea)
            except Exception:
                filas_finales.append(linea)
                continue
            url = art.get("url")
            if url and url in vistos:
                continue
            if url:
                vistos.add(url)
            filas_finales.append(linea)

    with open(ruta_salida, "w", encoding="utf-8") as f:
        for linea in filas_finales:
            f.write(linea + "\n")

    return n_originales, len(filas_finales), n_originales - len(filas_finales)


def deduplicar_entre_archivos(carpeta_resultados, prioridad=None, urls_excluir=None):
    """
    Deduplica por URL ENTRE todos los .jsonl de una carpeta (no solo dentro
    de cada uno). Si la misma URL aparece en mas de un archivo, se queda con
    la copia del archivo de mayor prioridad segun `prioridad` (lista de
    nombres de archivo, primero = gana); los no listados van al final por
    orden alfabetico.

    urls_excluir: set opcional de URLs a eliminar de TODOS los archivos sin
    excepcion (por ejemplo, duplicados detectados por analisis semantico
    -- mismo texto, URL distinta -- que ya fueron marcados por otro proceso).

    Devuelve un dict {nombre_archivo: (n_originales, n_finales, n_eliminados)}.
    """
    archivos = sorted(f for f in os.listdir(carpeta_resultados) if f.endswith(".jsonl"))
    if prioridad:
        orden = {nombre: i for i, nombre in enumerate(prioridad)}
        archivos.sort(key=lambda f: orden.get(f, len(prioridad)))

    urls_excluir = urls_excluir or set()
    vistos_global = set()
    reporte = {}

    for nombre in archivos:
        ruta = os.path.join(carpeta_resultados, nombre)
        with open(ruta, "r", encoding="utf-8") as f:
            lineas = [l.strip() for l in f if l.strip()]
        n_originales = len(lineas)

        filas_finales = []
        vistos_local = set()
        for linea in lineas:
            try:
                art = json.loads(linea)
            except Exception:
                filas_finales.append(linea)
                continue
            url = art.get("url")
            if url:
                if url in urls_excluir or url in vistos_global or url in vistos_local:
                    continue
                vistos_local.add(url)
            filas_finales.append(linea)
        vistos_global |= vistos_local

        with open(ruta, "w", encoding="utf-8") as f:
            for linea in filas_finales:
                f.write(linea + "\n")

        reporte[nombre] = (n_originales, len(filas_finales), n_originales - len(filas_finales))

    return reporte
