# noticias

El corpus de noticias: 14.012 notas de 7 portales, recolectadas en 9 fuentes y ya depuradas. **Fase de CRISP-DM:** 2, comprensión de los datos.

- `datos/`: los 9 `.jsonl` del corpus y `reporte_dedup_semantico.json`, con los duplicados que se excluyen. Copiados de la 5.0: no se vuelve a scrapear.
- `scripts_recoleccion/`: los scrapers y los scripts de depuración. Son **documentación** y no se vuelven a correr.
- `documentacion/`: la auditoría del corpus (los cinco problemas y sus soluciones).
- `.env.example`: plantilla de credenciales de Internet Archive, sin claves.
- **Lo usan:** `3_preparacion_de_los_datos/regla_17` y `sentimiento_finbeto/sentimiento_por_nota.py`.
- **Límite:** la cantidad de notas por día depende de qué capturó la Wayback Machine. Por eso no entra al modelo.
