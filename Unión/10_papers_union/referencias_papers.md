# Papers relacionados con la unión

Actualizado: 24/10/2026

Esta carpeta junta trabajos de otros autores que hicieron pruebas parecidas a las de la unión (U1 a U8). Sirven para dos cosas: citar de dónde sale cada método y comparar nuestros resultados con lo que encontraron otros.

- **Búsqueda:** alphaXiv (arXiv) y web, en español y en inglés.
- **Nombre de cada archivo:** empieza con el paso al que corresponde. Por ejemplo, `U6b_...` es un paper que respalda la prueba U6b. Los que empiezan con `00_marco` sirven para toda la tesis.
- **Qué hay:** 29 PDF descargados (sección 1) y 13 clásicos que se citan pero no se descargaron, porque no tienen una copia gratuita oficial (sección 2).
- **Para citar:** las citas en formato BibTeX están en `referencias_papers.bib`.

Los resúmenes salen del abstract y de la primera página de cada paper. Antes de citar un número puntual, conviene confirmarlo en el PDF.

---

## 1. Papers descargados

### Marco general: ¿los medios anticipan al mercado o lo siguen?

**Tetlock (2007). *Giving Content to Investor Sentiment: The Role of Media in the Stock Market*.** Journal of Finance 62(3), 1139–1168.
- **Archivo:** `00_marco_Tetlock_2007_media_sentiment.pdf`
- **Qué hace:** mide el pesimismo de una columna diaria del Wall Street Journal y lo cruza con el mercado.
- **Qué encuentra:** el pesimismo anticipa una baja de precios que después se revierte, y los retornos bajos anticipan más pesimismo.
- **Relación con la tesis:**
  - Es el paper de referencia del tema.
  - Su segundo resultado es justamente el principal de la unión: el mercado anticipa el tono de los medios (U6).
  - La diferencia es que él también encuentra el efecto inverso, noticias → precios, y en Argentina no aparece.

**Garcia (2013). *Sentiment during Recessions*.** Journal of Finance 68(3), 1267–1300. En la carpeta está el borrador del autor, de diciembre de 2012.
- **Archivo:** `00_marco_Garcia_2013_sentiment_recessions.pdf`
- **Qué hace:** usa columnas financieras del New York Times entre 1905 y 2005.
- **Qué encuentra:** el tono de las noticias anticipa los retornos casi solo en las recesiones.
- **Relación con la tesis:**
  - Respalda el análisis por régimen de U6, que separa las ruedas Calmas de las Tensas.
  - También explica por qué el efecto puede no aparecer en un año como el de la ventana.

### U1. Cada nota a su rueda

No hay un paper específico sobre la regla de las 17:00. Los dos de U6b (más abajo) son los que justifican separar las notas publicadas con el mercado abierto de las publicadas con el mercado cerrado.

### U2. Tono por rueda y ruedas de tono extremo

**Braña, Litterio y Fernández (2016). *Sentiment Analysis para la clasificación de noticias financieras en los Mercados Argentinos*.** CAETI, Universidad Abierta Interamericana; repositorio SEDICI-UNLP.
- **Archivo:** `U2U3_Brana_Litterio_Fernandez_sentimiento_mercados_argentinos.pdf`
- **Idioma:** español.
- **Qué hace:** clasifica frases de noticias financieras argentinas en positivas, negativas o neutras.
- **Relación con la tesis:**
  - Es el antecedente argentino más directo del modelo de sentimiento de Gino.
  - Solo clasifica el sentimiento: no lo cruza con precios. Ese cruce es lo que agrega la tesis.

**Rodríguez-García, Riaño-Martínez, Roldán-Álvarez y Montalvo-Herranz (2023). *URJC-Team at FinancES 2023: Financial Targeted Sentiment Analysis in Spanish Combining Transformers*.** CEUR-WS, vol. 3496.
- **Archivo:** `U2_CEUR_3496_BETO_opiniones_financieras.pdf`
- **Qué hace:** sentimiento de noticias financieras en español con modelos tipo BERT, incluido BETO.
- **Relación con la tesis:**
  - Es de la misma familia que el FinBETO de Gino.
  - Mide el sentimiento hacia distintos destinatarios dentro de una noticia (por ejemplo, empresas y consumidores). Es parecido a lo que hace U3 con cada empresa.

**Stan, Lunghi, Vargetto, Ricci et al. (2026). *Causal Reconstruction of Sentiment Signals from Sparse News Data*.** arXiv 2603.23568.
- **Archivo:** `U2_2603.23568_sentiment_sparse_news.pdf`
- **Qué hace:** propone cómo armar una serie diaria de sentimiento cuando hay días con pocas noticias.
- **Relación con la tesis:**
  - Justifica que U2 mida el tono contra las 20 ruedas previas en lugar de tomarlo crudo.
  - También justifica que el ruido dependa de la cantidad de notas del día.

**Mavillonio, Borgioli, Giannetti, Ongari et al. (2026). *Measuring Sentiment News with Transformer-Based Language Models*.** arXiv 2607.13968.
- **Archivo:** `U2_2607.13968_sentiment_news_transformers.pdf`
- **Qué hace:** arma índices diarios de sentimiento con un modelo tipo BERT frase por frase y los compara con los de diccionario.
- **Relación con la tesis:** respalda la decisión de Gino de usar un modelo tipo BERT en lugar de un diccionario de palabras.

### U2 y U4. Tono ruidoso cuando hay pocas notas

**Carbó Casals (2026). *From Noisy News Sentiment Scores to Interpretable Temporal Dynamics: A Bayesian State-Space Model*.** arXiv 2601.16769.
- **Archivo:** `U2U4_2601.16769_noisy_sentiment_bayesian_state_space.pdf`
- **Qué hace:**
  - Muestra que una serie de sentimiento es ruidosa porque la cantidad de noticias cambia de un período a otro.
  - Propone darle menos peso a los períodos con pocas noticias.
- **Relación con la tesis:**
  - Es la misma idea que el "tono propio" de U4.
  - Allí, una empresa con una sola oración pesa el 8% y una con diez oraciones pesa el 48%.

### U3. Sentimiento de cada empresa

**Tang, Yang, Huang, Tam et al. (2023). *FinEntity: Entity-level Sentiment Classification for Financial Texts*.** arXiv 2310.12406.
- **Archivo:** `U3_2310.12406_FinEntity.pdf`
- **Qué hace:** clasifica el sentimiento hacia cada empresa nombrada en una noticia, no hacia la noticia entera.
- **Relación con la tesis:** es lo que hace U3 al cruzar las entidades de Gino con las oraciones.

**Sinha, Kedas, Kumar y Malo (2023). *SEntFiN 1.0: Entity-Aware Sentiment Analysis for Financial News*.** arXiv 2305.12257.
- **Archivo:** `U3_2305.12257_SEntFiN.pdf`
- **Qué hace:** arma una base de titulares donde una misma noticia puede ser buena para una empresa y mala para otra.
- **Relación con la tesis:** justifica medir el tono por empresa en lugar de usar el tono general de la nota.

**Chen (2025). *A Framework for Measuring How News Topics Drive Stock Movement*.** arXiv 2510.06864.
- **Archivo:** `U3_2510.06864_news_topics_stock_movement.pdf`
- **Qué hace:** critica que se resuma todo el sentimiento de un día en un solo número y separa las noticias por tema.
- **Relación con la tesis:**
  - Respalda que la unión mida el tono también por empresa y por sector, y no solo para el mercado.
  - El análisis por tema queda como trabajo futuro.

### U4. Atención y volumen

**Cao, Wunkaew y Geman (2025). *The Hype Index: an NLP-driven Measure of Market News Attention*.** arXiv 2506.06329.
- **Archivo:** `U4_2506.06329_hype_index_attention.pdf`
- **Qué hace:** mide cuánta atención le dan los medios a cada acción, contando las noticias y ajustando por el tamaño de la empresa.
- **Relación con la tesis:** respalda usar la cantidad de notas y de menciones como variable de atención, separada del tono.

**Rojas y Kristjanpoller (2015). *Relación precio-volumen mediante análisis de causalidad y efecto día de semana en los mercados accionarios latinoamericanos*.** Lecturas de Economía 83, 9–31.
- **Archivo:** `U4U6_redalyc_retorno_volumen_LatAm.pdf`
- **Idioma:** español.
- **Qué hace:** estudia la causalidad de Granger entre retorno y volumen en las bolsas latinoamericanas.
- **Qué encuentra:** en casi todos los mercados, el retorno causa al volumen.
- **Relación con la tesis:** es un buen antecedente regional para incluir el volumen anormal en el VAR de U6.

### U5. Estacionariedad del tono

**Correa Rocha (2026). *Stable Sentiment and Persistent Dynamics in U.S. Economic News over 45 Years*.** arXiv 2607.06220.
- **Archivo:** `U5_2607.06220_stable_sentiment_persistence.pdf`
- **Qué hace:** estudia la serie de tono de las noticias económicas de Estados Unidos a lo largo de 45 años.
- **Qué encuentra:** el tono es muy persistente, es decir, un día se parece mucho al anterior.
- **Relación con la tesis:**
  - Explica por qué el tono en nivel dio "inconcluso" en U5.
  - Justifica usar el tono anormal en el VAR.

### U6. VAR y Granger: ¿quién anticipa a quién?

**Verma, Tulsyan, Dhanuka y Sen (2026). *Quantitative Analysis of Media Bias and Stock Price Dynamics: The 2020 Shock*.** arXiv 2608.05899.
- **Archivo:** `U6_2608.05899_media_bias_stock_prices_2020.pdf`
- **Qué hace:** usa el shock de 2020 para preguntar si las noticias influyen en el precio o reflejan información que el precio ya tiene.
- **Relación con la tesis:** es exactamente la pregunta de la tesis.

**Mukherjee (2025). *Investor Sentiment and Market Movements: A Granger Causality Perspective*.** arXiv 2510.15915.
- **Archivo:** `U6_2510.15915_investor_sentiment_granger.pdf`
- **Qué hace:** prueba de Granger entre sentimiento y mercado, en las dos direcciones.
- **Relación con la tesis:** es un paper corto, útil como ejemplo del mismo método de U6.

**Chniguir y Henchiri (2022). *Causality between investor sentiment and the shares return on the Moroccan and Tunisian financial markets*.** Revue du Contrôle, de la Comptabilité et de l'Audit 6(4), 350–364; arXiv 2305.16632.
- **Archivo:** `U6_2305.16632_sentiment_returns_Morocco_Tunisia.pdf`
- **Qué hace:** prueba la causalidad entre el sentimiento y los retornos en dos mercados emergentes.
- **Relación con la tesis:** son mercados chicos y poco líquidos, como el argentino, lo que permite comparar.

**Wu, Liu, Chen, Li et al. (2026). *Do News and Social Media Tell the Same Story? Constructing and Comparing Sentiment Spillover Networks*.** arXiv 2604.26811.
- **Archivo:** `U6_2604.26811_news_vs_social_media_spillover.pdf`
- **Qué hace:** compara cómo se contagia el sentimiento entre empresas en las noticias y en las redes sociales.
- **Relación con la tesis:**
  - Sirve para el análisis por empresa y por sector de U6.
  - También sirve para justificar que Twitter quede como trabajo futuro.

**Jazbec, Pàsztor, Faltings, Antulov-Fantulin et al. (2020). *On the impact of publicly available news and information transfer to financial markets*.** arXiv 2010.12002.
- **Archivo:** `U6_2010.12002_public_news_information_transfer.pdf`
- **Qué hace:** mide cuánta información pasa de las noticias de la web a los precios.
- **Relación con la tesis:** es otra forma, distinta de Granger, de medir la misma dirección noticias → mercado.

**Coronado, Martinez, Gualajara y Rojas (2022). *Transfer Entropy Granger Causality between News Indices and Stock Markets in U.S. and Latin America during the COVID-19 Pandemic*.** Entropy 24, 1420.
- **Archivo:** `U6_Entropy_2022_transfer_entropy_COVID_LatAm.pdf`
- **Qué hace:** prueba la causalidad de Granger desde los índices de noticias del COVID hacia las bolsas de Estados Unidos y de Latinoamérica, incluida Argentina.
- **Relación con la tesis:**
  - Es uno de los pocos trabajos que incluye al mercado argentino.
  - Una diferencia importante: usa índices de cantidad de noticias, no de tono.

**Coronado, Martinez, Gualajara, Romero-Meza y Rojas (2023). *Time-Varying Granger Causality of COVID-19 News on Emerging Financial Markets: The Latin American Case*.** Mathematics 11, 394.
- **Archivo:** `U6_MDPI_2023_Granger_variable_COVID_LatAm.pdf`
- **Qué hace:** es la continuación del paper anterior, con una causalidad que cambia en el tiempo.
- **Relación con la tesis:** se relaciona con el análisis por régimen de U6. La causalidad puede existir en unos períodos y en otros no.

**Cruz Montaña y Tirado León (2025). *Análisis de sentimientos en noticias financieras y su impacto en la bolsa de valores de Colombia – COLCAP*.** Universidad EAN, Seminario de Investigación de Especialización.
- **Archivo:** `U6_CruzMontana_Tirado_2025_sentimiento_COLCAP.pdf`
- **Idioma:** español.
- **Qué hace:** cruza el tono de noticias financieras con el índice de la bolsa colombiana.
- **Relación con la tesis:** es el trabajo más parecido a la tesis en otro país latinoamericano y en español.

**Galdi y Gonçalves (2018). *Pessimismo e incerteza das notícias e o comportamento dos investidores no Brasil*.** RAE-Revista de Administração de Empresas 58(2), 130–148.
- **Archivo:** `U6_Galdi_Goncalves_2018_RAE_pesimismo_noticias_Brasil.pdf`
- **Idioma:** portugués, con resumen en español y en inglés.
- **Qué hace:** mide el tono de 1.237 ediciones diarias del diario Valor Econômico (2012–2016) y lo cruza con la rentabilidad y la volatilidad de los índices de la bolsa brasileña.
- **Qué encuentra:**
  - Las palabras de "incertidumbre" se asocian con menor rentabilidad.
  - Hay indicios más débiles de que las palabras "negativas" se asocian con más volatilidad.
- **Relación con la tesis:**
  - Es el antecedente más cercano en un país vecino, porque también usa el tono de un diario económico y lo cruza con el índice de la bolsa.
  - Reemplaza a la disertación de la UFPB, que no se pudo bajar (sección 3) y usa el mismo diario.
  - A diferencia de la tesis, en Brasil sí encuentran contenido informativo en las noticias.

### U6b. Notas publicadas con el mercado cerrado

**Glasserman, Krstovski, Laliberte y Mamaysky (2025). *Does Overnight News Explain Overnight Returns?*.** arXiv 2507.04481.
- **Archivo:** `U6b_2507.04481_overnight_news_overnight_returns.pdf`
- **Qué hace:** pregunta si las noticias publicadas de noche explican el retorno entre el cierre y la apertura.
- **Relación con la tesis:**
  - Es la prueba más parecida a U6b.
  - Él lo hace con el mercado de Estados Unidos y con muchas más noticias, así que su resultado sirve de comparación directa.

**Knuteson (2020). *Strikingly Suspicious Overnight and Intraday Returns*.** arXiv 2010.01727.
- **Archivo:** `U6b_2010.01727_overnight_intraday_returns.pdf`
- **Qué hace:** muestra que el retorno de la noche (del cierre a la apertura) y el del día se comportan de forma muy distinta.
- **Relación con la tesis:** justifica separar el retorno de apertura en U6b.

### U7. Event study

**Kargarzadeh, Khaledian, Parvini, Ghatak et al. (2026). *Buy the Rumor, Sell the News: When Is News Priced In?*.** arXiv 2608.14014.
- **Archivo:** `U7_2608.14014_buy_rumor_sell_news.pdf`
- **Qué hace:** mide en qué momento el precio incorpora una noticia: antes, el mismo día o después.
- **Relación con la tesis:**
  - Es la misma pregunta de U7.
  - En la tesis, el Merval ya venía subiendo +3,2% en las 3 ruedas previas a una rueda de tono extremo positivo.

**Ardia, Bluteau y Boudt (2022). *Media abnormal tone, earnings announcements, and the stock market*.** Journal of Financial Markets 61, 100683; arXiv 2110.10800.
- **Archivo:** `U7_2110.10800_media_abnormal_tone_earnings.pdf`
- **Qué hace:** event study con el "tono anormal" de los medios, es decir, el tono comparado con lo habitual.
- **Relación con la tesis:** es la misma idea que el `sent_anormal` y el `tono_propio` de U4, aplicada a un event study como el de U7.

**Guo, Peng, Tao y Tu (2017). *Joint News, Attention Spillover, and Stock Returns*.** arXiv 1703.02715.
- **Archivo:** `U7_1703.02715_joint_news_attention_spillover.pdf`
- **Qué hace:** estudia qué pasa con el precio de una empresa cuando aparece en la misma noticia que otra.
- **Relación con la tesis:** sirve para el event study por empresa de U7 y para el problema de las notas que nombran a varias empresas a la vez.

### U6 y U8. Muchas pruebas a la vez

**Harvey y Liu (2020). *False (and Missed) Discoveries in Financial Economics*.** arXiv 2006.04269.
- **Archivo:** `U6U8_2006.04269_false_missed_discoveries.pdf`
- **Qué hace:** explica que, cuando se hacen muchas pruebas, algunas salen significativas por azar. Propone cómo controlar los falsos positivos sin perder los verdaderos.
- **Relación con la tesis:**
  - Respalda la corrección de Benjamini-Hochberg de U6.
  - También respalda leer las 4 pruebas significativas de 152 en "noticias → mercado" como lo esperable por azar.

**Nikolopoulos (2026). *Spurious Predictability in Financial Machine Learning*.** arXiv 2604.15531.
- **Archivo:** `U8_2604.15531_spurious_predictability.pdf`
- **Qué hace:** muestra que, si se prueban muchas variantes hasta que una "funciona", aparecen resultados falsos.
- **Relación con la tesis:** justifica que U8 cambie una sola decisión por vez y que la especificación de U6b se haya fijado antes de ver los resultados.

---

## 2. Citados pero no descargados

Son trabajos con derechos de autor y sin una copia gratuita oficial. Están en `referencias_papers.bib` con su DOI, para conseguirlos desde la biblioteca de la facultad.

| Paso | Referencia | Para qué se usa |
|---|---|---|
| U4 | Efron y Morris (1975). *Data Analysis Using Stein's Estimator and its Generalizations*. JASA 70(350), 311–319 | El "encogimiento" del tono propio hacia 0 cuando hay pocas oraciones (bayes empírico, K = 10,9) |
| U4 | Fang y Peress (2009). *Media Coverage and the Cross-Section of Stock Returns*. Journal of Finance 64(5), 2023–2052 | Cobertura de medios como variable |
| U4 | Da, Engelberg y Gao (2011). *In Search of Attention*. Journal of Finance 66(5), 1461–1499 | Medidas de atención |
| U5 | Dickey y Fuller (1979). *Distribution of the Estimators for Autoregressive Time Series with a Unit Root*. JASA 74(366), 427–431 | La prueba ADF |
| U5 | Kwiatkowski, Phillips, Schmidt y Shin (1992). *Testing the null hypothesis of stationarity against the alternative of a unit root*. Journal of Econometrics 54, 159–178 | La prueba KPSS |
| U6 | Granger (1969). *Investigating Causal Relations by Econometric Models and Cross-spectral Methods*. Econometrica 37(3), 424–438 | La causalidad de Granger |
| U6 | Sims (1980). *Macroeconomics and Reality*. Econometrica 48(1), 1–48 | El modelo VAR |
| U6 | Lütkepohl (2005). *New Introduction to Multiple Time Series Analysis*. Springer | La elección de rezagos por AIC y las bandas de la impulso-respuesta |
| U6 | Benjamini y Hochberg (1995). *Controlling the False Discovery Rate*. JRSS B 57(1), 289–300 | La corrección BH |
| U6/U8 | Harvey, Liu y Zhu (2016). *... and the Cross-Section of Expected Returns*. Review of Financial Studies 29(1), 5–68 | Pruebas múltiples en finanzas |
| U7 | MacKinlay (1997). *Event Studies in Economics and Finance*. Journal of Economic Literature 35(1), 13–39 | El método del event study |
| U6 (régimen) | Rabiner (1989). *A Tutorial on Hidden Markov Models and Selected Applications in Speech Recognition*. Proceedings of the IEEE 77(2), 257–286 | El HMM de regímenes (Calmo, Moderado, Tenso) que usa el análisis por régimen; viene del plan de trabajo |
| Futuro | Yang, Fernández-Pérez e Indriawan (2024). *Spillover between investor sentiment and volatility: The role of social media*. International Review of Financial Analysis 96, 103643 | Sentimiento en redes sociales; respalda el uso de X/Twitter que quedó como trabajo futuro; viene del plan de trabajo |

---

## 3. Lo que no se pudo bajar

**Disertación de la UFPB (Brasil).** *O efeito do sentimento das notícias sobre o comportamento dos preços no mercado acionário brasileiro*.
- **Qué hace:** cruza el tono de 45.304 notas del diario Valor Econômico (2011–2017) con el Ibovespa.
- **Por qué no está:** el repositorio de la UFPB devolvió error 502 (servidor caído) en los tres intentos del 24/10/2026.
- **Para bajarlo después:** https://repositorio.ufpb.br/jspui/bitstream/123456789/12575/1/Arquivototal.pdf

---

## 4. Qué dice la literatura sobre los resultados de la tesis

- **Mercado → noticias:** lo encontraron Tetlock (2007) en Estados Unidos y ahora la unión en Argentina. Es un resultado conocido, y que se repita con medios argentinos lo hace más creíble.
- **Noticias → mercado:**
  - Tetlock (2007), Galdi y Gonçalves (2018) y la disertación brasileña lo encuentran.
  - Garcia (2013) lo encuentra casi solo en las recesiones.
  - Que en la ventana de la tesis no aparezca no contradice a la literatura: es compatible con lo que dice Garcia.
- **En español y en Latinoamérica:**
  - Hay muy pocos trabajos que crucen el tono de los medios con precios: el de Colombia, los dos brasileños (Galdi y Gonçalves, y la disertación de la UFPB) y los de COVID, que usan cantidad de noticias y no tono.
  - El de la UAI solo clasifica el sentimiento.
  - Esto deja a la tesis como un aporte en un tema poco estudiado en la región.
