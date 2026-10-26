# Informe Final

El documento de la tesina, en LaTeX, con el contenido de todas las carpetas del proyecto.

## Archivos

| Archivo | Qué es |
|---|---|
| `Informe_Final_NicolasDiddi-GinoFrigoni.pdf` | La tesina compilada (46 páginas) |
| `Informe_Final_NicolasDiddi-GinoFrigoni.tex` | Archivo principal: formato, portada, resumen, índice, siglas, bibliografía |
| `capitulos_reducida/` | Un archivo por capítulo (01 Introducción a 08 Conclusiones) y el anexo (09) |
| `bibliografia_reducida.tex` | Las referencias citadas en la tesina, tomadas de `bibliografia.tex`: no editar a mano |
| `figuras/` | Copias de las figuras de cada carpeta, más las tres que rehace `figuras_reducida.py` |
| `logo_ugr.png` | Logo de la Universidad del Gran Rosario (portada) |
| `capitulos/`, `tablas/`, `bibliografia.tex` | Fuentes de la versión completa de 92 páginas, de las que sale la bibliografía |

## Cómo compilar

```bash
python compilar_reducida.py
```

El script hace cuatro cosas:

1. Copia las figuras de cada carpeta y genera las tres que la tesina rehace (`figuras_reducida.py`): la alineación de las notas, la serie de tono y atención, y el VIX con la salida del cepo y las elecciones marcadas.
2. Arma `bibliografia_reducida.tex` con las referencias que cita el texto.
3. Compila con [tectonic](https://tectonic-typesetting.github.io/), que tiene que estar en `~/tools/tectonic/tectonic.exe`.
4. Verifica que cada enlace a un paper apunte a un archivo que existe.

## Bibliografía

Debajo de cada referencia está la ruta del PDF del paper dentro del repositorio. En el PDF de la tesina esa ruta es un enlace que abre el archivo:

- funciona en lectores de escritorio, como Acrobat (que pide confirmación);
- los navegadores no abren enlaces a archivos locales;
- funciona mientras `Informe Final` siga dentro de la carpeta del proyecto.

Las referencias sin PDF dicen por qué no se descargaron.

## Pendiente de completar

- Fecha de entrega: queda una línea en blanco en la portada.
