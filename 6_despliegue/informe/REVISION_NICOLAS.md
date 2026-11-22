# Para revisar: cambios en el lado bursátil (Nicolás)

En la versión 6.0 el informe se reorganizó por las fases de CRISP-DM. Estos son los cambios que tocan
tu parte. Los números salen solos de los resultados (`numeros.py`), así que lo que hay que revisar es
el **texto y las decisiones**.

| Antes (5.0) | Ahora (6.0) | Dónde está |
|---|---|---|
| Cap. 5 «El VIX argentino y el panel de acciones» | El panel pasa al cap. 3 (Comprensión de los datos, sección 3.2); el VIX al cap. 4 (Preparación, sección 4.7) | `capitulos/03_comprension_datos.tex`, `capitulos/04_preparacion.tex` |
| VIX sin escala | **Escala nueva por terciles** de las 244 ruedas: bajo (hasta 33,8 %), medio (33,8–39,6 %), alto (más de 39,6 %). Decisión del 22/11, pedida por el docente | `3_preparacion_de_los_datos/vix_argentino/escala_vix.py` |
| Episodios del VIX (cepo y elecciones) en una tabla | Quedan en la figura y en una regla de lectura (el eco de 20 ruedas) | sección 4.7 |
| Volatilidad de cada acción y ranking | **Sale** (no se usa en el modelo) | — |
| Clustering de familias | **Sale** (decisión D3) | — |
| Cap. 6 «Los regímenes de mercado» (HMM) | Pasa al **anexo C**, más corto. En el modelo solo se usa como prueba de robustez, con el régimen filtrado | `capitulos/08_anexo.tex` |
| ADF | **Sale** (solo hacía falta para el VAR) | — |

Cosas para confirmar:
1. ¿Te parece bien la escala por terciles? Si preferís otra, se cambia en `escala_vix.py`.
2. Las 59 ruedas del test (feb.–abr. 2026) están todas en régimen Calmo. Está discutido como límite (sección 7.4).
3. La redacción de la sección 3.2 (panel) y 4.7 (retorno, volumen anormal, VIX).
