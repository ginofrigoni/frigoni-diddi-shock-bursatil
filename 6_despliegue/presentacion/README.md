# presentacion

Presentación de la defensa. **Fase de CRISP-DM:** 6, despliegue (la presentación final).

| Archivo | Qué es |
|---|---|
| `Presentacion_Tesina.pptx` | La presentación, 28 diapositivas, con notas del orador que dicen quién habla en cada una |
| `Presentacion_Tesina.pdf` | La misma presentación en PDF |
| `GUION_PRESENTACION.md` | El guion: qué dice cada uno, cuánto tiempo, 12 preguntas probables con su respuesta y cómo recortar a 15 minutos |
| `generar_presentacion.js` | Genera el `.pptx` (`npm install pptxgenjs` y después `node generar_presentacion.js`). Toma las figuras de `../informe/figuras/` |
| `SIMULACION_PRESENTACION.md` | El guion de la versión anterior (5.0), como referencia |

- **Estructura:** 4 partes, como la presentación de referencia: el problema · los datos · preparación y modelado · evaluación y cierre.
- **Números:** son los de los `metricas.csv` del proyecto, los mismos que usa el informe.
- Para cambiar una diapositiva, se edita `generar_presentacion.js` y se vuelve a generar. Editarla a mano en PowerPoint también funciona, pero el cambio se pierde la próxima vez que se genere.
