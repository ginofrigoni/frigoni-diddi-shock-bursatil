# regimen_hmm

Regímenes del mercado (Calmo, Moderado y Tenso), estimados con un modelo oculto de Markov sobre el VIX argentino. **Fase de CRISP-DM:** 3, preparación.

- `salidas/hmm_regimen_mercado.csv`: el régimen de cada rueda, en sus versiones suavizada y filtrada. Lo calculó el lado bursátil con `hmm_regimen_mercado.py`, que es documentación y no se reentrena.
- `salidas/bic_por_k.csv` y `matriz_transicion.csv`: la elección de k = 3 y las transiciones.
- **En la 6.0 no entra al modelo principal**, porque sale del mismo VIX y sería duplicar. Se usa solo en la robustez (`5_evaluacion/anexo`), con el régimen **filtrado**, que no usa información futura, y se describe en el anexo C del informe.
