# informe

La tesina en LaTeX. **Fase de CRISP-DM:** 6, despliegue (el informe final).

- **Compilar:** `python compilar_tesina.py`. Genera los números y las tablas, copia las figuras, verifica las citas y compila con tectonic.
- **Números:** ninguno se escribe a mano.
  - `numeros.py` lee los `metricas*.csv` y las salidas de cada carpeta;
  - genera `generado/numeros.tex`, con `\dato{clave}`, y `generado/tablas/*.tex`;
  - si el texto pide una clave que no existe, la compilación se corta.
- **Capítulos** (`capitulos/`), en el orden de CRISP-DM: introducción · marco teórico · comprensión de los datos · preparación · modelado · evaluación · discusión y conclusiones · anexo.
- **Para revisar:** `REVISION_NICOLAS.md`, con los cambios en el lado bursátil.
- **Papers:** `papers/` tiene los 35 PDF que cita la bibliografía, copiados de la 5.0. En el PDF, cada referencia tiene un enlace que abre su archivo.
