# -*- coding: utf-8 -*-
"""
Controles de calidad compartidos por los scrapers y los scripts de depuracion
(solo libreria estandar).

Origen de cada control (ver AUDITORIA_CORPUS.md y DEPURACION_CALIDAD.md):
  - metadata_jsonld(): el JSON-LD de El Economista e iProfesional trae
    caracteres de control crudos dentro de strings; json.loads() estricto
    falla y los scrapers lo descartaban en silencio, perdiendo fecha, autor
    y tags. strict=False lo resuelve.
  - PATRON_ARTICULO: el filtro de categoria ("/economia/" in url) dejaba
    pasar paginas indice de seccion (eleconomista.com.ar/economia/).
  - es_paywall(): La Nacion sirve un stub "Suscribite a LA NACION..." (527
    caracteres de relleno) en vez del articulo.
  - fecha_fuera_de_ventana(): el sitemap filtra por lastmod, no por fecha de
    publicacion, y deja entrar notas viejas que fueron reeditadas.
"""

import json
import re
from datetime import datetime

PATRON_ARTICULO = {
    "ambito_economia":      r"ambito\.com/economia/.+-n\d+",
    "ambito_finanzas":      r"ambito\.com/finanzas/.+-n\d+",
    "lanacion_economia":    r"lanacion\.com\.ar/economia/.+-nid\d+",
    "clarin_economia":      r"clarin\.com/economia/.+_0_[A-Za-z0-9]+\.html",
    "clarin_sitemap":       r"clarin\.com/economia/.+_0_[A-Za-z0-9]+\.html",
    "tn_economia":          r"tn\.com\.ar/economia/.+/\d{4}/\d{2}/\d{2}/.+",
    "infobae_economia":     r"infobae\.com/economia/\d{4}/\d{2}/\d{2}/.+",
    "eleconomista_sitemap": r"eleconomista\.com\.ar/(economia|finanzas)/.+-n\d+$",
    "iprofesional_sitemap": r"iprofesional\.com/(index\.php/)?(economia|finanzas)/\d+-.+",
}

PAYWALL_TITULOS = re.compile(r"suscrib[ií]te a la naci[oó]n", re.I)


def url_es_articulo(url, patron):
    return bool(patron and url and re.search(patron, url))


def es_paywall(noticia):
    return bool(PAYWALL_TITULOS.search(noticia.get("titulo") or ""))


def parsear_fecha(fecha_str):
    """'2025-05-29T18:22:00-03:00' / '2025-05-29' -> datetime naive (solo fecha) o None."""
    if not fecha_str:
        return None
    try:
        return datetime.strptime(fecha_str[:10], "%Y-%m-%d")
    except ValueError:
        return None


def fecha_fuera_de_ventana(noticia, desde_dt):
    """True si la fecha de PUBLICACION real (no el lastmod del sitemap) es anterior a desde_dt."""
    f = parsear_fecha(noticia.get("fecha_publicacion"))
    return bool(f and f < desde_dt.replace(hour=0, minute=0, second=0, microsecond=0))


def fecha_posterior_a_recoleccion(noticia, hasta_dt):
    """True si la fecha de publicacion es POSTERIOR al fin de la recoleccion: pasa cuando una nota
    vieja fue re-fechada por el sitio despues de bajada y el dato recuperado ya no describe el contenido."""
    f = parsear_fecha(noticia.get("fecha_publicacion"))
    return bool(f and f > hasta_dt)


def motivo_descarte(noticia, desde_dt=None):
    """Devuelve un motivo (str) si la noticia no debe entrar al corpus, o None."""
    if es_paywall(noticia):
        return "paywall"
    if desde_dt is not None and fecha_fuera_de_ventana(noticia, desde_dt):
        return "fecha_fuera_de_ventana"
    return None


def sincronizar_json(ruta_jsonl):
    """
    Regenera el .json hermano de un .jsonl (mismo nombre) para que ambos
    queden consistentes despues de editar el .jsonl: conserva el 'meta' del
    .json existente, reemplaza 'noticias' y actualiza total_noticias.
    """
    ruta_json = ruta_jsonl[:-1] if ruta_jsonl.endswith(".jsonl") else ruta_jsonl
    noticias = []
    with open(ruta_jsonl, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if linea:
                try:
                    noticias.append(json.loads(linea))
                except Exception:
                    continue
    meta = {}
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            meta = json.load(f).get("meta", {})
    except Exception:
        pass
    meta["total_noticias"] = len(noticias)
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump({"meta": meta, "noticias": noticias}, f, ensure_ascii=False, indent=2)
    return len(noticias)


def metadata_jsonld(html):
    """
    Extrae metadatos del bloque JSON-LD tipo *Article sin depender de BeautifulSoup.
    Devuelve dict con las claves que existan: titulo, bajada, fecha_publicacion,
    fecha_modificacion, autor, tags.
    """
    meta = {}
    for bloque in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', html, re.S | re.I):
        try:
            data = json.loads(bloque, strict=False)
        except Exception:
            continue
        if isinstance(data, list):
            data = next((d for d in data if isinstance(d, dict) and "Article" in str(d.get("@type", ""))), {})
        if not isinstance(data, dict):
            continue
        tipos = data.get("@type", "")
        if isinstance(tipos, list):
            tipos = " ".join(tipos)
        if "Article" not in tipos:
            continue
        meta["titulo"] = data.get("headline")
        meta["bajada"] = data.get("description")
        meta["fecha_publicacion"] = data.get("datePublished")
        meta["fecha_modificacion"] = data.get("dateModified")
        autor = data.get("author")
        if isinstance(autor, dict):
            meta["autor"] = autor.get("name")
        elif isinstance(autor, list) and autor:
            meta["autor"] = autor[0].get("name") if isinstance(autor[0], dict) else str(autor[0])
        elif isinstance(autor, str):
            meta["autor"] = autor
        kw = data.get("keywords", "")
        meta["tags"] = [t.strip() for t in kw.split(",") if t.strip()] if isinstance(kw, str) else (kw or [])
        break
    return {k: v for k, v in meta.items() if v}
