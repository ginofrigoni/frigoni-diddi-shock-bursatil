# -*- coding: utf-8 -*-
"""
Equivalencias entre terminos del gazetteer de indicadores economicos (IND_ECO).

El gazetteer de indicadores no esta canonicalizado (a diferencia del de empresas, que resuelve cada
alias a su ticker): cada termino es una entidad. Por eso sinonimos como "ccl" y "contado con
liquidacion" aparecian como dos indicadores distintos. Esta tabla los une.

Criterio:
  * solo se unen nombres distintos del MISMO indicador (siglas, nombre completo, variantes de uso);
  * el nombre canonico es la forma mas frecuente en el corpus (n de oraciones en ner_sentimiento.csv
    antes de unificar, 2026-10-18);
  * todos los terminos unidos tienen el mismo subtipo.

NO se unen, a proposito, terminos relacionados pero distintos:
  inflacion / inflacion mensual / anual / interanual / acumulada (medidas distintas);
  indice de precios (generico) vs. ipc; dolar libre (ambiguo tras la salida del cepo);
  reservas brutas / netas / internacionales; deficit fiscal / deficit primario / resultado primario;
  tasa de interes / tasa de referencia / tasa de politica monetaria;
  emision monetaria / expansion monetaria / base monetaria;
  jubilaciones / haberes previsionales / movilidad jubilatoria;
  deuda publica / deuda soberana / deuda externa; plazo fijo / plazo fijo uva;
  dolar financiero vs. dolar mep y ccl.

Se aplica en cruce_ner_sentimiento.py. ner_articulos.csv, ner_oraciones.csv y ner_resumen.csv
(salidas del notebook) conservan los terminos originales.
"""

EQUIVALENCIAS_IND_ECO = {
    # macro
    "contado con liquidacion": "ccl",
    "contado con liqui": "ccl",
    "pib": "pbi",
    "producto bruto interno": "pbi",
    "dolar bolsa": "dolar mep",
    "cepo al dolar": "cepo cambiario",
    "saldo comercial": "balanza comercial",
    "cesacion de pagos": "default",
    # precios
    "indice de precios al consumidor": "ipc",
    "canasta basica alimentaria": "cba",
    "canasta basica total": "cbt",
    "tasa de pobreza": "pobreza",
    "tasa de indigencia": "indigencia",
    # laboral
    "tasa de desempleo": "desempleo",
    "tasa de desocupacion": "desempleo",
    "salario minimo vital y movil": "smvm",
    "negociacion paritaria": "paritarias",
    "cct": "convenio colectivo de trabajo",
    "trabajo no registrado": "empleo informal",
    "empleo en negro": "empleo informal",
    # fiscal
    "derechos de exportacion": "retenciones",
    "recaudacion impositiva": "recaudacion tributaria",
    # financiero
    "indice merval": "merval",
    "fondos comunes de inversion": "fci",
}


def canonico(entidad, tipo):
    """Nombre canonico de una entidad (solo cambia indicadores IND_ECO con equivalencia)."""
    if tipo == "IND_ECO":
        return EQUIVALENCIAS_IND_ECO.get(entidad, entidad)
    return entidad
