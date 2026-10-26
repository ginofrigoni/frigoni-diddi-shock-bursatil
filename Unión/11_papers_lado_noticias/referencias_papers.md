# Papers relacionados con el lado de noticias

Actualizado: 24/10/2026

Esta carpeta junta trabajos de otros autores relacionados con lo que se hizo en el lado de noticias (`Lado Noticias`, Gino): la recolección del corpus, el modelo de sentimiento FinBETO y el reconocimiento de entidades (NER). Sirven para citar de dónde sale cada método y para comparar las decisiones tomadas con lo que hicieron otros.

- **Dónde está:** la carpeta está en `Unión` y no dentro de `Lado Noticias`, porque en ese lado no entra nada sin una decisión explícita de Gino. Si él la quiere, puede copiarla a su lado.
- **Búsqueda:** alphaXiv (arXiv) y web, en español y en inglés.
- **Nombre de cada archivo:** empieza con la carpeta de Gino a la que corresponde: `noticias_`, `sentimiento_` o `ner_`.
- **Qué hay:** 23 PDF descargados (sección 1) y 8 trabajos que se citan pero no se descargaron (sección 2).
- **Para citar:** las citas en formato BibTeX están en `referencias_papers.bib`.

Los resúmenes salen del abstract y de la primera página de cada paper. Antes de citar un número puntual, conviene confirmarlo en el PDF.

---

## 1. Papers descargados

### Recolección del corpus (`noticias/`)

**Barbaresi (2021). *Trafilatura: A Web Scraping Library and Command-Line Tool for Text Discovery and Extraction*.** Proceedings of ACL-IJCNLP 2021: System Demonstrations, 122–131.
- **Archivo:** `noticias_Barbaresi_2021_trafilatura.pdf`
- **Qué hace:** presenta la librería trafilatura, que extrae de una página web el texto principal y los metadatos (título, autor, fecha). La compara con otras herramientas.
- **Relación con el lado de noticias:**
  - Es una de las capas del extractor de Gino: primero el JSON-LD, después Open Graph, el `<h1>`, trafilatura y, por último, BeautifulSoup.
  - Es la cita obligada para esa herramienta.

**Garg, Alam, Ayala, Graham et al. (2025). *Longitudinal Sampling of URLs From the Wayback Machine*.** arXiv 2507.14752.
- **Archivo:** `noticias_2507.14752_wayback_machine_sampling.pdf`
- **Qué hace:** cuenta cómo se recolectaron millones de páginas archivadas en Internet Archive (la Wayback Machine) y qué problemas aparecieron.
- **Relación con el lado de noticias:**
  - Respalda el método principal de recolección de Gino, que usó la CDX API de Internet Archive.
  - También respalda la limitación que él menciona: el corpus depende de qué páginas archivó un tercero.

**Foley (2026). *WCXB: A Multi-Type Web Content Extraction Benchmark*.** arXiv 2605.21097.
- **Archivo:** `noticias_2605.21097_WCXB_extraccion_contenido.pdf`
- **Qué hace:** compara herramientas que separan el texto principal de una página del "relleno" (menús, publicidad, pies de página).
- **Relación con el lado de noticias:**
  - Explica por qué quedaron restos como "PUBLICIDAD" o el bloque "Sobre la firma / Newsletter Clarín" dentro del texto.
  - Esos restos hubo que filtrarlos después, en el sentimiento y en el NER.

**Hatwar, Partridge, Bhargava y Bermejo (2024). *Author Unknown: Evaluating Performance of Author Extraction Libraries on Global Online News Articles*.** arXiv 2410.19771.
- **Archivo:** `noticias_2410.19771_extraccion_autor_noticias.pdf`
- **Qué hace:** mide qué tan bien distintas librerías sacan el autor y otros metadatos de las noticias online.
- **Relación con el lado de noticias:**
  - Se relaciona con el problema de iProfesional y El Economista: los metadatos faltaban por un error de parseo del JSON-LD.
  - Muestra que la extracción de metadatos falla seguido y conviene validarla.

**Dodge, Sap, Marasović, Agnew et al. (2021). *Documenting Large Webtext Corpora: A Case Study on the Colossal Clean Crawled Corpus*.** arXiv 2104.08758.
- **Archivo:** `noticias_2104.08758_documentar_corpus_web_C4.pdf`
- **Qué hace:** audita un corpus sacado de la web y encuentra texto de plantilla, duplicados y contenido que no corresponde.
- **Relación con el lado de noticias:**
  - Respalda los documentos de auditoría de Gino (`AUDITORIA_CORPUS.md`, `DEPURACION_CALIDAD.md`).
  - La idea es la misma: un corpus de la web hay que documentarlo y auditarlo antes de usarlo.

**Lee, Ippolito, Nystrom, Zhang et al. (2021). *Deduplicating Training Data Makes Language Models Better*.** arXiv 2107.06499.
- **Archivo:** `noticias_2107.06499_deduplicacion.pdf`
- **Qué hace:** muestra que los corpus de texto tienen muchos duplicados y casi duplicados. También muestra que quitarlos mejora los modelos y evita que se "memoricen" textos repetidos.
- **Relación con el lado de noticias:**
  - Respalda la limpieza de duplicados de Gino: 205 duplicados exactos entre Wayback y sitemap, y la publicación cruzada de una misma nota.
  - También respalda haber quitado los párrafos fijos repetidos del conjunto etiquetado.

**Fronzetti Colladon y Vestrelli (2026). *Free Access to World News: Reconstructing Full-Text Articles from GDELT*.** Big Data and Cognitive Computing 10(2), 45; arXiv 2504.16063.
- **Archivo:** `noticias_2504.16063_GDELT_texto_completo.pdf`
- **Qué hace:** propone cómo reconstruir el texto completo de noticias a partir de GDELT, una base mundial de noticias.
- **Relación con el lado de noticias:**
  - Es una fuente alternativa para ampliar el corpus o cubrir huecos, como el de iProfesional en abril de 2026.
  - Queda como trabajo futuro.

### Modelo de sentimiento (`sentimiento_finbert/`)

**Cañete, Chaperon, Fuentes, Ho et al. (2020). *Spanish Pre-trained BERT Model and Evaluation Data*.** Workshop PML4DC, ICLR 2020; arXiv 2308.02976.
- **Archivo:** `sentimiento_2308.02976_BETO.pdf`
- **Qué hace:** presenta **BETO** (`dccuchile/bert-base-spanish-wwm-cased`), un modelo BERT entrenado en español por la Universidad de Chile.
- **Relación con el lado de noticias:** es el modelo base del que parte FinBETO y la cita obligada para él.

**Pérez, Rajngewerc, Giudici, Furman et al. (2021). *pysentimiento: A Python Toolkit for Opinion Mining and Social NLP tasks*.** arXiv 2106.09462.
- **Archivo:** `sentimiento_2106.09462_pysentimiento.pdf`
- **Qué hace:** presenta la librería pysentimiento (UBA y CONICET), con modelos de sentimiento en español entrenados con tuits (corpus TASS).
- **Relación con el lado de noticias:**
  - Es el origen del modelo de referencia con el que se comparó FinBETO (`finiteautomata/beto-sentiment-analysis`).
  - FinBETO lo supera en noticias no vistas: 0,724 contra 0,546 de F1 en 3 clases.
  - Este paper explica por qué el de referencia rinde peor: se entrenó con tuits, no con prensa económica.

**Gutiérrez-Fandiño, Armengol-Estapé, Pàmies, Llop-Palao et al. (2022). *MarIA: Spanish Language Models*.** Procesamiento del Lenguaje Natural 68, 39–60; arXiv 2107.07253.
- **Archivo:** `sentimiento_2107.07253_MarIA.pdf`
- **Qué hace:** presenta MarIA, la familia de modelos en español del Barcelona Supercomputing Center.
- **Relación con el lado de noticias:**
  - Es la principal alternativa a BETO.
  - En sentimiento financiero en español, MarIA y BETO son los que mejor rinden (ver Pan et al. 2023, sección 2).
  - Probar MarIA queda como trabajo futuro.

**Gururangan, Marasović, Swayamdipta, Lo et al. (2020). *Don't Stop Pretraining: Adapt Language Models to Domains and Tasks*.** ACL 2020; arXiv 2004.10964.
- **Archivo:** `sentimiento_2004.10964_dont_stop_pretraining.pdf`
- **Qué hace:** muestra que seguir entrenando un modelo con texto de su dominio, antes del ajuste fino, mejora su desempeño.
- **Relación con el lado de noticias:**
  - Es el respaldo directo del preentrenamiento continuado de BETO sobre el texto del corpus.
  - En ese paso Gino enmascaró el 15% de los tokens, durante 3 épocas.

**Araci (2019). *FinBERT: Financial Sentiment Analysis with Pre-trained Language Models*.** arXiv 1908.10063.
- **Archivo:** `sentimiento_1908.10063_FinBERT.pdf`
- **Qué hace:** adapta BERT al lenguaje financiero en inglés y lo ajusta para clasificar sentimiento.
- **Relación con el lado de noticias:** es el antecedente de "FinBETO", que hace lo mismo con BETO y en español.

**Malo, Sinha, Takala, Korhonen et al. (2014). *Good Debt or Bad Debt: Detecting Semantic Orientations in Economic Texts*.** Journal of the Association for Information Science and Technology; arXiv 1307.5336.
- **Archivo:** `sentimiento_1307.5336_Financial_PhraseBank.pdf`
- **Qué hace:** presenta el **Financial PhraseBank**, el conjunto clásico de oraciones financieras etiquetadas por personas como positivas, negativas o neutras.
- **Relación con el lado de noticias:**
  - Es el antecedente del conjunto etiquetado de Gino: 10.855 oraciones de prensa económica argentina.
  - Una diferencia importante: allí etiquetaron personas, y acá un modelo (Gemma).

**Gilardi, Alizadeh y Kubli (2023). *ChatGPT Outperforms Crowd-Workers for Text-Annotation Tasks*.** PNAS 120(30); arXiv 2303.15056.
- **Archivo:** `sentimiento_2303.15056_ChatGPT_anotador.pdf`
- **Qué hace:** compara las etiquetas de ChatGPT con las de personas contratadas para etiquetar textos. El modelo resulta más preciso y mucho más barato.
- **Relación con el lado de noticias:** respalda haber usado un modelo de lenguaje (Gemma) para etiquetar las oraciones de entrenamiento.

**Aguda, Siddagangappa, Kochkina, Kaur et al. (2024). *Large Language Models as Financial Data Annotators: A Study on Effectiveness and Efficiency*.** arXiv 2403.18152.
- **Archivo:** `sentimiento_2403.18152_LLM_anotadores_financieros.pdf`
- **Qué hace:** estudia qué tan bien etiquetan textos financieros los modelos de lenguaje, comparados con expertos. Es de JPMorgan AI Research.
- **Relación con el lado de noticias:** es lo mismo que el paper anterior, pero en el dominio financiero, que es el de Gino.

**Calderon, Reichart y Dror (2025). *The Alternative Annotator Test for LLM-as-a-Judge: How to Statistically Justify Replacing Human Annotators with LLMs*.** arXiv 2501.10970.
- **Archivo:** `sentimiento_2501.10970_alternative_annotator_test.pdf`
- **Qué hace:** propone una prueba estadística para decidir si un modelo de lenguaje puede reemplazar a anotadores humanos. Necesita solo una muestra chica etiquetada por personas.
- **Relación con el lado de noticias:**
  - Responde a la principal limitación del modelo: "las etiquetas provienen de un modelo, no de personas".
  - Es la guía más concreta para hacer la validación humana pendiente con pocas oraciones.

**Gemma Team, Google DeepMind (2026). *Gemma 4 Technical Report*.** arXiv 2607.02770.
- **Archivo:** `sentimiento_2607.02770_Gemma4.pdf`
- **Qué hace:** presenta la familia de modelos abiertos Gemma 4.
- **Relación con el lado de noticias:** es la cita del modelo que etiquetó las oraciones (`gemma4:26b`, servido con Ollama).

**Kapoor y Narayanan (2023). *Leakage and the Reproducibility Crisis in Machine-learning-based Science*.** Patterns 4(9); arXiv 2207.07048.
- **Archivo:** `sentimiento_2207.07048_leakage_reproducibilidad.pdf`
- **Qué hace:** muestra que muchos trabajos informan resultados inflados por "fuga de información", es decir, datos de prueba que también estaban en el entrenamiento.
- **Relación con el lado de noticias:**
  - Es el respaldo de la corrección más importante del modelo.
  - Dividir por oración y no por noticia hacía que el modelo se evaluara con notas que ya había visto en parte.
  - Al corregirlo, el F1 bajó de 0,732 a 0,685.

**Xue, Guesmi, Feng, Gong et al. (2026). *Temporal Leakage in Financial News NLP: A Multi-Architecture Audit with a Regime-Specific M&A Signal*.** arXiv 2608.17223.
- **Archivo:** `sentimiento_2608.17223_temporal_leakage_noticias_financieras.pdf`
- **Qué hace:** muestra que, con noticias financieras, el resultado cambia mucho según cómo se dividan entrenamiento y prueba (al azar o por fecha).
- **Relación con el lado de noticias:**
  - Es la misma familia de problemas que la división por noticia.
  - Una mejora posible sería dividir también por fecha.

### Reconocimiento de entidades (`ner_entidades/`)

**Tjong Kim Sang (2002). *Introduction to the CoNLL-2002 Shared Task: Language-Independent Named Entity Recognition*.** Proceedings of CoNLL-2002.
- **Archivo:** `ner_TjongKimSang_2002_CoNLL_NER_espanol.pdf`
- **Qué hace:** presenta la tarea y el conjunto de datos clásicos de NER en español.
- **Relación con el lado de noticias:**
  - De este trabajo vienen los cuatro tipos de entidad que usa spaCy en español: persona (PER), organización (ORG), lugar (LOC) y misceláneas (MISC).
  - Son los mismos cuatro tipos que reporta el NER de Gino.

**Ujiie, Iso, Yada, Wakamiya et al. (2021). *End-to-end Biomedical Entity Linking with Span-based Dictionary Matching*.** arXiv 2104.10493.
- **Archivo:** `ner_2104.10493_dictionary_matching.pdf`
- **Qué hace:** reconoce entidades buscando en un diccionario y une cada mención a un identificador único.
- **Relación con el lado de noticias:**
  - El ejemplo es biomédico, pero el método es el del gazetteer de empresas de Gino.
  - Cada alias ("Banco Galicia", "Grupo Financiero Galicia", "GGAL") se une a un identificador único, el ticker.

**Golde, Haller y Akbik (2025). *FiNERweb: Datasets and Artifacts for Scalable Multilingual Named Entity Recognition*.** arXiv 2512.13884.
- **Archivo:** `ner_2512.13884_FiNERweb.pdf`
- **Qué hace:** arma conjuntos de NER en muchos idiomas usando modelos de lenguaje como etiquetadores.
- **Relación con el lado de noticias:**
  - Es una alternativa para mejorar el NER.
  - El paper usa modelos de lenguaje para etiquetar, la misma idea que el etiquetado con Gemma del sentimiento.

**Asgarieh, Thadani y O'Hare (2024). *Scalable Detection of Salient Entities in News Articles*.** arXiv 2405.20461.
- **Archivo:** `ner_2405.20461_entidades_salientes_noticias.pdf`
- **Qué hace:** distingue las entidades centrales de una noticia de las que se mencionan al pasar. Es de Yahoo Research.
- **Relación con el lado de noticias:**
  - Se relaciona con una limitación del cruce entidad-sentimiento: una empresa nombrada al pasar recibe el tono de la oración aunque la nota no sea sobre ella.
  - Medir la "saliencia" de cada empresa sería una mejora.

---

## 2. Citados pero no descargados

| Tema | Referencia | Por qué no se descargó |
|---|---|---|
| Sentimiento | Pan, García-Díaz, García-Sánchez y Valencia-García (2023). *Evaluation of transformer models for financial targeted sentiment analysis in Spanish*. PeerJ Computer Science 9, e1377 | Es de acceso abierto, pero el sitio bloquea la descarga automática. Se puede bajar a mano desde https://peerj.com/articles/cs-1377. Es lo más parecido en español: titulares financieros, donde BETO y MarIA son los mejores modelos |
| Sentimiento | Marín, Valencia-García, García-Díaz et al. (2023). *Overview of FinancES 2023: Financial Targeted Sentiment Analysis in Spanish*. Procesamiento del Lenguaje Natural 71, 417–423 | No se encontró un PDF directo. Es el concurso de sentimiento financiero en español: sentimiento hacia la empresa principal, otras empresas y la sociedad |
| Sentimiento | García-Díaz, García-Sánchez y Valencia-García (2023). *Smart Analysis of Economics Sentiment in Spanish Based on Linguistic Features and Transformers*. IEEE Access 11, 14211–14224 | Es de acceso abierto, pero no se encontró un enlace directo al PDF; se baja a mano desde IEEE Xplore (DOI 10.1109/ACCESS.2023.3244065). Usa 15.915 tuits económicos en español |
| Sentimiento | Loughran y McDonald (2011). *When Is a Liability Not a Liability? Textual Analysis, Dictionaries, and 10-Ks*. Journal of Finance 66(1), 35–65 | Paga. Es el diccionario financiero clásico, la alternativa "por palabras" a FinBETO |
| Sentimiento | Devlin, Chang, Lee y Toutanova (2019). *BERT*. NAACL 2019 | Es la base de BETO; se cita a través del paper de BETO |
| Todo | Wirth y Hipp (2000). *CRISP-DM: Towards a Standard Process Model for Data Mining* | No se localizó una copia oficial. Es la metodología que mencionan los borradores de Gino ("fase 02") |
| NER | Honnibal, Montani, Van Landeghem y Boyd (2020). *spaCy: Industrial-strength Natural Language Processing in Python*. Zenodo | Es software, no un paper. Se cita como herramienta (modelo `es_core_news_lg`) |
| Sentimiento por entidad | FinEntity (Tang et al., 2023) y SEntFiN (Sinha et al., 2023) | Ya están descargados en `../10_papers_union/` (U3); no se duplican |

---

## 3. Qué dice la literatura sobre las decisiones del lado de noticias

- **Etiquetar con un modelo de lenguaje es una práctica aceptada,** con una condición: hay que validarlo contra personas.
  - Gilardi et al. (2023) y Aguda et al. (2024) muestran que puede funcionar.
  - Calderon et al. (2025) dan la prueba para justificarlo.
  - La validación humana que Gino dejó pendiente es justamente lo que pide esta literatura.
- **Dividir por noticia y no por oración fue la decisión correcta.** Kapoor y Narayanan (2023) muestran que la fuga de información infla los resultados. Por eso el F1 que corresponde informar es 0,685 y no 0,732.
- **El preentrenamiento continuado sobre el propio corpus** está respaldado por Gururangan et al. (2020).
- **Superar al modelo de referencia tiene sentido.** pysentimiento se entrenó con tuits, no con prensa económica. Por eso la ventaja de FinBETO (0,724 contra 0,546) es razonable.
- **En español hay pocos recursos de sentimiento financiero.** Están FinancES, Pan et al. y García-Díaz et al., todos de la Universidad de Murcia y casi todos sobre titulares y tuits. No hay un conjunto público de oraciones de prensa económica argentina. El conjunto de Gino es un aporte en sí mismo.
