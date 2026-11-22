# sentimiento_por_empresa

Cruza las entidades que detectó el NER con el sentimiento de cada oración, y arma el sentimiento de cada empresa en cada rueda.

**Fase de CRISP-DM:** 3, preparación de los datos (construir atributos derivados).

## Pasos, en orden

1. `python cruce_ner_sentimiento.py`: une cada mención con el sentimiento de su oración. Une el 99,4 % de las 242.312 oraciones con entidades.
2. `python sentimiento_por_empresa.py`: agrupa por rueda y arma el panel de 47 acciones × 244 ruedas.

- **Recibe:**
  - `datos/ner_oraciones.csv`, las menciones por oración (copiado de la 5.0);
  - `datos/cobertura_por_ticker.csv`;
  - `../sentimiento_finbeto/salidas/beto_oraciones_finetuned.csv`;
  - `../regla_17/salidas/nota_a_rueda.csv`;
  - el panel de acciones.
- **Entrega:**
  - `salidas/panel_empresas_rueda.csv`, con hubo_noticia, empresa_con_cobertura y sent_neto_empresa;
  - `salidas/ner_sentimiento*.csv`, `cobertura_empresas.csv`, `verificaciones.csv` y `cobertura_empresas.png`;
  - `metricas.csv`.
- **Estado:**
  - el cruce con las etiquetas de la 5.0 reproduce exactamente la salida de la 5.0;
  - el panel pasa 9/9 controles: son las mismas 17 empresas con cobertura, y `hubo_noticia` coincide con la 5.0 fila por fila.
- **Renombre (D4):** la marca 0/1 que en la 5.0 se llamaba `sentimiento_propio` ahora es `empresa_con_cobertura`.
