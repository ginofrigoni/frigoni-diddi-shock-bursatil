# -*- coding: utf-8 -*-
"""
Loader minimo de archivos .env, sin dependencias externas (no requiere
instalar python-dotenv).

Antes, las credenciales de Internet Archive (IA_S3_KEY / IA_S3_SECRET)
estaban escritas en texto plano dentro de noticias_historico_v3.py. Ahora
viven en ../.env (fuera del codigo fuente) y se cargan con esta funcion.

Uso:
    from env_utils import cargar_env
    cargar_env()
    api_key = os.environ.get("IA_S3_KEY")
"""

import os


def cargar_env(ruta_env=None):
    """
    Lee un archivo .env (formato NOMBRE=valor, una variable por linea,
    '#' para comentarios y lineas vacias se ignoran) y carga las variables
    en os.environ. No sobreescribe una variable si ya existe en el entorno
    (permite overridear desde afuera sin tocar el archivo).

    Si no se pasa ruta_env, busca "../.env" relativo a este archivo
    (es decir, noticias/.env, un nivel arriba de scraping_noticias/).

    Devuelve True si encontro y leyo el archivo, False si no existe.
    """
    if ruta_env is None:
        ruta_env = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
    ruta_env = os.path.abspath(ruta_env)

    if not os.path.exists(ruta_env):
        return False

    with open(ruta_env, "r", encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("#") or "=" not in linea:
                continue
            clave, valor = linea.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip('"').strip("'")
            if clave and clave not in os.environ:
                os.environ[clave] = valor
    return True
