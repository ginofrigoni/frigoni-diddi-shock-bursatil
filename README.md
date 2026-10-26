<div align="center">

<img src="Informe%20Final/logo_ugr.png" alt="Universidad del Gran Rosario" width="360">

<br><br>

# Impacto de shocks informativos en el comportamiento bursátil de empresas argentinas

### Un enfoque basado en análisis de sentimiento y modelos de series temporales

**Trabajo Final de Grado · Licenciatura en Ciencia de Datos**<br>
Universidad del Gran Rosario · Seminario de Trabajo Final

![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)
![Transformers](https://img.shields.io/badge/BETO-FinBETO-FFB000)
![statsmodels](https://img.shields.io/badge/statsmodels-VAR%20%C2%B7%20Granger%20%C2%B7%20HMM-1F4E79)
![LaTeX](https://img.shields.io/badge/LaTeX-tectonic-008080?logo=latex&logoColor=white)

[**Leer la tesina (PDF)**](Informe%20Final/Informe_Final_NicolasDiddi-GinoFrigoni.pdf)

</div>

---

## Autores

| | |
|---|---|
| **Gino Frigoni** | Lado de noticias: corpus, análisis de sentimiento (FinBETO) y reconocimiento de entidades |
| **Nicolás Diego Diddi** | Lado bursátil: panel de acciones, clustering, VIX argentino, estacionariedad y regímenes de mercado |

La unión de los dos lados, que responde la pregunta de la tesina, es trabajo de ambos.

## Docentes

- **Alejandro Mario Hernandez**
- **Briant Alcides Gauna**
- **Jorge Manuel Fernández Acuña**

---

## De qué se trata

En la bolsa argentina está muy extendida la idea de que *«las noticias mueven las acciones»*. Los días de noticias grandes, como los posteriores a una elección, son también días de movimientos fuertes del S&P Merval. Pero esa coincidencia no dice qué vino primero: puede que las noticias muevan al mercado, o que los medios cuenten lo que el mercado ya hizo.

Esta tesina separa esas dos posibilidades con datos. Durante un año de ruedas de BYMA (mayo de 2025 a abril de 2026), ordena en el tiempo el **tono** y la **cantidad** de las noticias económicas de siete portales argentinos y el **precio** y el **volumen** de 47 acciones, y prueba en las dos direcciones quién anticipa a quién.

### Cuatro instrumentos y un experimento

Para responder la pregunta hubo que construir cuatro instrumentos que no existían para el mercado argentino:

| | Instrumento | Qué mide |
|:---:|---|---|
| 📰 | **Corpus de noticias** | 14.012 notas de Clarín, La Nación, Infobae, Ámbito, TN, El Economista e iProfesional, recolectadas con la Wayback Machine y los mapas del sitio, auditadas y asignadas a la rueda en que el mercado pudo reaccionar |
| 🌡️ | **FinBETO** | Un termómetro emocional de la prensa económica: BETO adaptado al dominio y ajustado para clasificar oraciones en cuatro clases (F1 macro 0,685 en noticias no vistas, contra 0,546 del modelo de referencia), con reconocimiento de entidades para medir el tono de cada empresa |
| 📈 | **VIX argentino** | La tensión diaria del mercado, construida con la volatilidad realizada del S&P Merval |
| 🔀 | **Regímenes de mercado** | Un modelo oculto de Markov que clasifica cada rueda como Calmo, Moderado o Tenso |

Con ellos, el experimento —modelos **VAR** con pruebas de **causalidad de Granger**, estudios de eventos y doce variantes de robustez— contrasta la hipótesis.

<div align="center">
<img src="Informe%20Final/figuras/vix_arg.png" alt="S&P Merval y VIX argentino, con la salida del cepo y las elecciones de 2025" width="85%">
<br><sub>S&P Merval y VIX argentino entre enero de 2025 y abril de 2026. Las líneas punteadas marcan la salida del cepo y las dos elecciones.</sub>
</div>

### Qué encontramos

> **Los medios económicos argentinos, en el período estudiado, siguieron al mercado.**

- **Las noticias no anticipan al mercado.** El tono no anticipó el precio ni el volumen: ni en el mercado, ni en las empresas, ni en los sectores, ni en ningún régimen. De 152 pruebas en esa dirección, solo 4 son significativas, lo esperable por azar.
- **El mercado anticipa a las noticias.** Cuando el S&P Merval sube, el tono de las notas siguientes es más positivo: pasa en 39 de las 47 empresas y, con el tono propio de cada empresa, en 15 de 17.
- **El efecto está en las notas de la misma noche.** Las notas publicadas entre el cierre y la medianoche cuentan cómo le fue al mercado, con un tono que acompaña la suba o la baja.
- **La cantidad de noticias acompaña a la actividad.** Cuando una empresa aparece en muchas más notas que lo habitual, ese día su acción se opera más, sin una dirección en el precio.

---

## Organización del repositorio

El trabajo tiene tres partes que no se modifican entre sí. Cada paso es una carpeta con su script, sus resultados, sus controles automáticos y su documentación en PDF.

| Carpeta | Contenido |
|---|---|
| 📂 [`Lado Noticias/`](Lado%20Noticias/) | Corpus de noticias, FinBETO y reconocimiento de entidades |
| 📂 [`Lado Bursatil/`](Lado%20Bursatil/) | Panel de 47 acciones, clustering, VIX argentino, estacionariedad, volatilidad y regímenes |
| 📂 [`Unión/`](Uni%C3%B3n/) | Cada nota a su rueda, datasets unificados, VAR y Granger, estudios de eventos y robustez |
| 📂 [`Informe Final/`](Informe%20Final/) | La tesina en LaTeX y los scripts que la compilan |

Cada carpeta tiene su propio README con el detalle. En los PDF de la tesina, debajo de cada referencia está la ruta del paper dentro de este repositorio; con un lector de escritorio, la ruta abre el archivo.

## Cómo se reproduce

| Parte | Cómo |
|---|---|
| **Lado de noticias** | Entorno Python 3.13 desde `Lado Noticias/requirements.txt` (ver `Lado Noticias/README.md`). La recolección usa credenciales de Internet Archive en `Lado Noticias/noticias/.env`, que no se sube: copiar `.env.example` y completarlo |
| **Lado bursátil** | Cada carpeta tiene un script de Python; los PDF de documentación se generan con Node desde `Lado Bursatil/99_generadores_documentacion` (`npm install`) |
| **Unión** | Desde `Unión/09_entrega_final`, `python correr_todo.py` rehace todos los pasos, verifica los 66 controles automáticos y compara los 64 archivos de resultados con la corrida anterior |
| **Tesina** | Desde `Informe Final`, `python compilar_tesina.py` genera `Informe_Final_NicolasDiddi-GinoFrigoni.pdf`, con [tectonic](https://tectonic-typesetting.github.io/) en `~/tools/tectonic/tectonic.exe` |

### Un archivo comprimido

`Lado Noticias/sentimiento_finbert/beto_oraciones_finetuned.csv` (169 MB) es el sentimiento FinBETO de las 408.939 oraciones del corpus, y lo leen el cruce con el NER y la unión. Está comprimido en `beto_oraciones_finetuned.csv.gz` (30 MB). Antes de correr esos pasos hay que descomprimirlo en la misma carpeta:

```bash
gzip -dk "Lado Noticias/sentimiento_finbert/beto_oraciones_finetuned.csv.gz"
```

El archivo descomprimido tiene sha256 `f4b9c10f…`, el mismo del original.

### Archivos excluidos

GitHub no acepta archivos de más de 100 MB. Estos cuatro quedaron afuera por su tamaño:

| Archivo | Tamaño | Cómo se obtiene |
|---|---:|---|
| `Lado Noticias/sentimiento_finbert/beto_further_pretrained/model.safetensors` | 419 MB | Pesos de BETO con preentrenamiento continuado sobre el corpus; copia de los autores (sha256 `b4ff46aa…`). Solo lo usa la medición de calidad (Fase 3) |
| `Lado Noticias/sentimiento_finbert/baseline_finiteautomata/pytorch_model.bin` | 419 MB | Modelo de referencia, de Hugging Face: [`finiteautomata/beto-sentiment-analysis`](https://huggingface.co/finiteautomata/beto-sentiment-analysis), revisión `9384c7f3…` |
| `Lado Noticias/ner_entidades/resultados_ner/ner_oraciones.csv` | 221 MB | Se regenera con `Lado Noticias/ner_entidades/ner_analisis.ipynb` |
| `Lado Noticias/ner_entidades/resultados_ner/ner_articulos.csv` | 79 MB | Ídem |

Tampoco se suben los entornos (`.venv/`, `node_modules/`), que se reinstalan, ni el archivo de credenciales `.env`.

---

<div align="center">
<sub>Gino Frigoni · Nicolás Diego Diddi — Universidad del Gran Rosario, 2026</sub>
</div>
