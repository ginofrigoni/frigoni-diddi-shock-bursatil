# anexo

Pruebas de robustez del modelo predictivo y verificación clásica con VAR y Granger.

**Fase de CRISP-DM:** 5, evaluación.

| Script | Qué hace |
|---|---|
| `robustez.py` | Repite la comparación A contra B en las dos direcciones, **cambiando una sola decisión por vez** (9 variantes) |
| `var_granger.py` | VAR y Granger con las variables del modelo, a nivel mercado y para las 17 empresas |

- **Recibe:** `3_preparacion_de_los_datos/dataset_unificado/salidas/` y los precios completos, que hacen falta para recalcular el volumen anormal con otras ventanas.
- **Entrega:**
  - `salidas/robustez.csv` y `robustez.png`; `metricas_robustez.csv`;
  - `salidas/granger_resultados.csv`, `rezagos_var.csv`, `irf_mercado.csv` y `var_granger.png`; `metricas_var_granger.csv`.

## Robustez (ΔAUC = B − A, IC 95 %, regresión logística)

| Variante | Noticias → precio | Precio → sentimiento |
|---|---|---|
| Principal (reproduce `4_modelado`) | −0,012 [−0,054; +0,037] | **+0,152 [+0,074; +0,267]** |
| Con régimen (filtrado) | −0,009 [−0,054; +0,041] | **+0,154 [+0,084; +0,276]** |
| Ventana de 10 ruedas | −0,013 [−0,057; +0,036] | +0,042 [−0,069; +0,154] |
| Ventana de 60 ruedas | +0,001 [−0,041; +0,039] | +0,093 [−0,101; +0,404] |
| Test desde 01/01/2026 | −0,011 [−0,057; +0,031] | **+0,117 [+0,064; +0,197]** |
| Test desde 01/03/2026 | +0,005 [−0,052; +0,048] | **+0,134 [+0,043; +0,260]** |
| Sin días electorales | −0,011 [−0,059; +0,045] | **+0,139 [+0,052; +0,275]** |
| Sin abril de 2026 | −0,021 [−0,065; +0,054] | **+0,151 [+0,004; +0,296]** |
| Sentimiento ajustado por portal | −0,010 [−0,054; +0,039] | +0,051 [−0,093; +0,191] |

**Cómo se lee:**
- **Noticias → precio:** no aporta en **ninguna** de las 9 variantes, ni con la regresión logística ni con el random forest. Es el resultado más estable.
- **Precio → sentimiento:**
  - ΔAUC es **positivo en las 9 variantes**, entre +0,04 y +0,15;
  - el intervalo excluye el 0 en **6 de 9** (con random forest, en 5 de 9).
  - No alcanza en tres casos:
    - con **ventana de 10 ruedas**: el objetivo es más ruidoso;
    - con **ventana de 60**: quedan solo 121 ruedas de entrenamiento y el intervalo es muy ancho;
    - con el **sentimiento ajustado por portal**.
  - **Lectura:** la dirección es la misma siempre, pero el tamaño depende de cómo se define el sentimiento inesperado. Lo del ajuste por portal hay que discutirlo en el informe, porque puede indicar que parte del efecto viene de qué portales publican en cada rueda. Es una hipótesis: no está verificada.
- **Abril de 2026, sin iProfesional:** sacarlo no cambia el resultado. ΔAUC sigue siendo +0,151, aunque con un test más chico.

## Verificación clásica (VAR y Granger, 224 ruedas)

| Prueba | Mercado | Empresas con p < 0,05 (de 17) |
|---|---|---|
| Sentimiento inesperado → retorno | p = 0,37 | 0 |
| **Retorno → sentimiento inesperado** | **p = 0,000003** | **14**, todas con efecto positivo |
| Sentimiento propio → retorno | — | 1 |
| **Retorno → sentimiento propio** | — | **14**, todas con efecto positivo |

Por azar se esperaría menos de 1 empresa de 17. En el impulso-respuesta, una suba del Merval hace subir el sentimiento de la rueda siguiente (+1,8 puntos, banda de +1,1 a +2,6). **Los dos métodos, el predictivo y el clásico, dicen lo mismo.**

**Estado:** ✅ la variante principal reproduce `4_modelado`, y los 18 VAR son estables.
