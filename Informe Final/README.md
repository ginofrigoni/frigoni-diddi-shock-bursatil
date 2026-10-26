# Informe Final

El documento de la tesina, armado sobre el esqueleto de `Esqueleto_Tesina.tex` (mismo orden de capítulos), con el contenido de todas las carpetas de `tesis version 3.0`.

## Archivos

| Archivo | Qué es |
|---|---|
| `Tesina_Final.pdf` | La tesina compilada |
| `Tesina_Final.tex` | Archivo principal: formato, portada, resumen, índices, siglas, bibliografía |
| `capitulos/` | Un archivo por capítulo (01 Introducción a 07 Conclusiones) y los anexos (08) |
| `bibliografia.tex` | Generado por `generar_bibliografia.py`: no editar a mano |
| `claves_bibliografia.txt` | Clave de cada referencia, para citarla con `\citet{clave}` o `\citep{clave}` |
| `tablas/` | Tablas largas de los anexos, generadas por `generar_tablas.py` desde los CSV |
| `figuras/` | Copias de las figuras de cada carpeta (las copia `compilar_tesina.py`) |
| `logo_ugr.png` | Logo de la Universidad del Gran Rosario (portada) |
| `Esqueleto_Tesina.tex` / `.pdf` | La guía de estructura (no se modificó) |

## Cómo compilar

```bash
python compilar_tesina.py
```

El script hace cuatro cosas:

1. Copia las figuras.
2. Arma la bibliografía a partir de los catálogos de papers:
   - `Lado Bursatil/99_generadores_documentacion/referencias.json`;
   - `Unión/10_papers_union/referencias_papers.bib`;
   - `Unión/11_papers_lado_noticias/referencias_papers.bib`.
3. Arma las tablas de los anexos.
4. Compila con tectonic (`C:\Users\nicol\tools\tectonic\tectonic.exe`) y verifica que cada enlace a un paper apunte a un archivo que existe.

## Bibliografía

- **Contenido:** 118 referencias, todas citadas en el texto. 84 tienen el PDF descargado (86 archivos, todos los de las carpetas `papers`, `10_papers_union` y `11_papers_lado_noticias`).
- **Ruta y enlace:** debajo de cada referencia está la ruta del PDF. En el PDF de la tesina esa ruta es un enlace que abre el archivo:
  - funciona en lectores de escritorio, como Acrobat (que pide confirmación);
  - los navegadores no abren enlaces a archivos locales;
  - funciona mientras `Informe Final` siga dentro de `tesis version 3.0`.
- **No descargadas:** las referencias sin PDF dicen por qué no se descargaron.

## Pendiente de completar

- Fecha de entrega: queda una línea en blanco en la portada.
