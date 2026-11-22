"""
Funciones comunes del modelado — tesis versión 6.0. Fase 4 de CRISP-DM.

Lo usan noticias_a_precio/ y precio_a_sentimiento/. El diseño está fijado en 4_modelado/README.md
antes de ver resultados: regresión logística (principal) y random forest (confirmatorio), hiperparámetros
elegidos por validación cruzada temporal dentro del entrenamiento, métricas con umbral 0,5 y ΔAUC (B − A)
con bootstrap por bloques de ruedas del test.
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, balanced_accuracy_score, confusion_matrix, f1_score,
                             roc_auc_score)
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

SEMILLA = 42
CORTE_TEST = "2026-02-01"
UMBRAL = 0.5
N_FOLDS = 5
BLOQUE = 5
N_BOOT = 2000
GRILLA_LOGIT = [{"C": c} for c in (0.001, 0.01, 0.1, 1, 10)]
GRILLA_RF = [{"max_depth": d, "min_samples_leaf": h} for d in (3, 5, 8) for h in (20, 50, 100)]


def crear(algoritmo, params):
    if algoritmo == "logistica":
        return make_pipeline(StandardScaler(), LogisticRegression(C=params["C"], max_iter=5000))
    return RandomForestClassifier(n_estimators=500, max_features="sqrt", random_state=SEMILLA, n_jobs=-1, **params)


def folds_temporales(fechas, n=N_FOLDS):
    """Cortes que se extienden: entrena con las primeras fechas y valida con el bloque siguiente."""
    unicas = np.array(sorted(pd.unique(fechas)))
    bordes = np.linspace(0, len(unicas), n + 2).astype(int)[1:]
    for i in range(n):
        ent, val = unicas[:bordes[i]], unicas[bordes[i]:bordes[i + 1]]
        yield np.isin(fechas, ent), np.isin(fechas, val)


def elegir_y_ajustar(algoritmo, X, y, fechas):
    """Elige los hiperparámetros por AUC en la validación temporal y reentrena con todo el entrenamiento."""
    grilla = GRILLA_LOGIT if algoritmo == "logistica" else GRILLA_RF
    puntajes = []
    for params in grilla:
        aucs = []
        for ent, val in folds_temporales(fechas):
            if len(np.unique(y[val])) < 2 or len(np.unique(y[ent])) < 2:
                continue
            mod = crear(algoritmo, params).fit(X[ent], y[ent])
            aucs.append(roc_auc_score(y[val], mod.predict_proba(X[val])[:, 1]))
        puntajes.append({**params, "auc_validacion": float(np.mean(aucs)), "n_folds": len(aucs)})
    tabla = pd.DataFrame(puntajes)
    mejor = tabla.sort_values("auc_validacion", ascending=False).iloc[0]
    params = {k: (int(mejor[k]) if k != "C" else float(mejor[k])) for k in grilla[0]}
    return crear(algoritmo, params).fit(X, y), params, tabla


def metricas(y, prob, umbral=UMBRAL):
    pred = (prob >= umbral).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
    return {"auc": roc_auc_score(y, prob) if len(np.unique(y)) > 1 else np.nan,
            "balanced_accuracy": balanced_accuracy_score(y, pred), "f1": f1_score(y, pred, zero_division=0),
            "accuracy": accuracy_score(y, pred), "tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp),
            "pct_clase_1_real": float(y.mean()), "pct_clase_1_predicha": float(pred.mean()), "n": int(len(y))}


def bootstrap_delta_auc(y, prob_a, prob_b, fechas, n_boot=N_BOOT, bloque=BLOQUE, semilla=SEMILLA):
    """ΔAUC = AUC(B) − AUC(A) con bootstrap por bloques de ruedas consecutivas del test."""
    rng = np.random.default_rng(semilla)
    unicas = np.array(sorted(pd.unique(fechas)))
    idx_por_fecha = {f: np.flatnonzero(fechas == f) for f in unicas}
    n = len(unicas)
    deltas = []
    for _ in range(n_boot):
        inicios = rng.integers(0, n - bloque + 1, size=int(np.ceil(n / bloque)))
        elegidas = np.concatenate([unicas[i:i + bloque] for i in inicios])[:n]
        idx = np.concatenate([idx_por_fecha[f] for f in elegidas])
        if len(np.unique(y[idx])) < 2:
            continue
        deltas.append(roc_auc_score(y[idx], prob_b[idx]) - roc_auc_score(y[idx], prob_a[idx]))
    deltas = np.array(deltas)
    return {"delta_auc": float(roc_auc_score(y, prob_b) - roc_auc_score(y, prob_a)),
            "ic95_inf": float(np.percentile(deltas, 2.5)), "ic95_sup": float(np.percentile(deltas, 97.5)),
            "p_unilateral": float((np.sum(deltas <= 0) + 1) / (len(deltas) + 1)), "repeticiones": int(len(deltas))}


def importancia(modelo, algoritmo, columnas):
    if algoritmo == "logistica":
        coef = modelo[-1].coef_[0]
        return pd.DataFrame({"variable": columnas, "coeficiente_estandarizado": coef,
                             "importancia": np.abs(coef)}).sort_values("importancia", ascending=False)
    return pd.DataFrame({"variable": columnas, "importancia": modelo.feature_importances_}).sort_values("importancia", ascending=False)


def correr_comparacion(d, objetivo, vars_a, vars_b, col_fecha="rueda"):
    """Entrena A y B con los dos algoritmos y devuelve métricas, ΔAUC, hiperparámetros e importancias."""
    ent = d[d[col_fecha] < CORTE_TEST].reset_index(drop=True)
    te = d[d[col_fecha] >= CORTE_TEST].reset_index(drop=True)
    y_ent, y_te = ent[objetivo].to_numpy(int), te[objetivo].to_numpy(int)
    f_ent, f_te = ent[col_fecha].to_numpy(), te[col_fecha].to_numpy()
    filas, deltas, hiper, imps, preds = [], [], [], [], {"rueda": f_te, "y": y_te}
    clase_mayor = int(y_ent.mean() >= 0.5)
    base = metricas(y_te, np.full(len(y_te), float(clase_mayor)))
    base["auc"] = 0.5
    filas.append({"algoritmo": "línea base", "modelo": f"siempre {clase_mayor}", **base})
    for alg in ("logistica", "random_forest"):
        prob = {}
        for nombre, vars_ in (("A", vars_a), ("B", vars_b)):
            mod, params, tabla = elegir_y_ajustar(alg, ent[vars_].to_numpy(float), y_ent, f_ent)
            prob[nombre] = mod.predict_proba(te[vars_].to_numpy(float))[:, 1]
            preds[f"{alg}_{nombre}"] = prob[nombre]
            filas.append({"algoritmo": alg, "modelo": nombre, **metricas(y_te, prob[nombre]),
                          "auc_entrenamiento": roc_auc_score(y_ent, mod.predict_proba(ent[vars_].to_numpy(float))[:, 1])})
            hiper.append({"algoritmo": alg, "modelo": nombre, **params, "auc_validacion": tabla["auc_validacion"].max()})
            imps.append(importancia(mod, alg, vars_).assign(algoritmo=alg, modelo=nombre))
        deltas.append({"algoritmo": alg, **bootstrap_delta_auc(y_te, prob["A"], prob["B"], f_te)})
    info = {"filas_entrenamiento": len(ent), "filas_test": len(te), "ruedas_entrenamiento": int(pd.Series(f_ent).nunique()),
            "ruedas_test": int(pd.Series(f_te).nunique()), "primera_rueda": str(ent[col_fecha].min())[:10],
            "ultima_rueda_entrenamiento": str(ent[col_fecha].max())[:10], "primera_rueda_test": str(te[col_fecha].min())[:10],
            "ultima_rueda_test": str(te[col_fecha].max())[:10], "pct_clase_1_entrenamiento": float(y_ent.mean())}
    return pd.DataFrame(filas), pd.DataFrame(deltas), pd.DataFrame(hiper), pd.concat(imps), pd.DataFrame(preds), info
