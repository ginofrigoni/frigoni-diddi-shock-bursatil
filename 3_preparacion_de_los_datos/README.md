# 3_preparacion_de_los_datos

Fase 3 de CRISP-DM: se integran los datos y se construyen las variables del modelo.

| Subcarpeta | Qué hay |
|---|---|
| `regla_17/` | Asigna cada nota a la rueda en la que el mercado pudo reaccionar (antes de las 17:00 → ese día; después → la rueda siguiente). |
| `sentimiento_finbeto/` | Pasa MIXTO a NEU, reentrena FinBETO con 3 clases y clasifica todas las oraciones del corpus. |
| `sentimiento_por_rueda/` | Sentimiento de cada rueda y sentimiento inesperado (contra las 20 ruedas anteriores). |
| `sentimiento_por_empresa/` | Cruza las entidades (NER) con el sentimiento: sentimiento propio de cada empresa. |
| `vix_argentino/` | VIX argentino: volatilidad de las últimas 20 ruedas, anualizada. Se copia de la 5.0. |
| `regimen_hmm/` | Regímenes Calmo, Moderado y Tenso (HMM sobre el VIX). Se copian de la 5.0; solo los usa el anexo. |
| `dataset_unificado/` | Une todo en una tabla: 17 empresas × 244 ruedas = 4.148 filas. |
