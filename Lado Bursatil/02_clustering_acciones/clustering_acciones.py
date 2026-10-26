"""
Clustering sobre las 47 acciones seleccionadas — tesis version 3.0
Tesina: Impacto de shocks informativos en empresas argentinas

Busca si existen grupos de acciones con comportamiento similar dentro del
panel definitivo de 47 acciones (ver 01_scraping_acciones): K-Means,
Jerárquico y MST, k=2..8, sobre 1 año y 3 años de historia.

Se usan solo representaciones que miden comportamiento, no magnitud —
un precio o volumen promedio sin normalizar agrupa por "caro vs. barato" o
"mucho vs. poco volumen", no por cómo se mueve la acción, y no responde la
pregunta de si hay familias que reaccionan parecido a las noticias:

  1. Precio    — retornos logarítmicos diarios, normalizados por empresa
  2. Volumen   — log-volumen diario, normalizado por empresa
  3. 13 features — variables estadísticas por empresa

"3 años" es el panel completo de 01_scraping_acciones (2023-05-03 ->
2026-05-03, exacto). "1 año" NO se calcula como "último año del panel" --
se toma la ventana de ../03_vix_argentino/vix_arg.csv, que es la ventana
real del corpus de noticias, para que el "1 año" de acá sea exactamente
el mismo período que usan VIX/ADF/volatilidad.

Input:  ../01_scraping_acciones/precios_diarios_47_acciones.csv
        ../03_vix_argentino/vix_arg.csv   (solo para la ventana de "1 año")
Output: resumen_clustering_47.csv          (una fila por cluster x método x período x análisis)
        clustering_1ano.png, clustering_3anos.png  (elbow K-Means + silueta comparativa)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy import stats
from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import squareform, pdist
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import minimum_spanning_tree
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import matplotlib.pyplot as plt

KS = list(range(2, 9))  # k = 2 a 8

# ── 1. Cargar datos ──────────────────────────────────────────────────────────
df = pd.read_csv("../01_scraping_acciones/precios_diarios_47_acciones.csv")
df["Date"] = pd.to_datetime(df["Date"]).dt.normalize()
df = df.sort_values(["ticker", "Date"])
df["label"] = df["ticker"].str.replace(".BA", "", regex=False)
N_PANEL = df["ticker"].nunique()

# Retorno logarítmico sobre la serie COMPLETA, antes de recortar ventanas --
# así el "1 año" no pierde su primer día por falta del precio anterior.
df["retorno"] = df.groupby("ticker")["Close"].transform(lambda x: np.log(x / x.shift(1)))

# "1 año" = la ventana de vix_arg.csv (la del corpus de noticias), no un
# recorte arbitrario de los últimos 365 días del panel.
vix = pd.read_csv("../03_vix_argentino/vix_arg.csv", parse_dates=["fecha"])
FECHA_1Y_INICIO, FECHA_1Y_FIN = vix["fecha"].min(), vix["fecha"].max()
df_1y = df[(df["Date"] >= FECHA_1Y_INICIO) & (df["Date"] <= FECHA_1Y_FIN)].copy()
df_3y = df.copy()

print(f"1 año : {df_1y['Date'].min().date()} -> {df_1y['Date'].max().date()} "
      f"| {df_1y['ticker'].nunique()} empresas | {len(df_1y):,} filas")
print(f"3 años: {df_3y['Date'].min().date()} -> {df_3y['Date'].max().date()} "
      f"| {df_3y['ticker'].nunique()} empresas | {len(df_3y):,} filas")


# ── 2. Preparación de datos por representación ───────────────────────────────
def preparar_precio(d0):
    d = d0.dropna(subset=["retorno"])
    ret_wide = d.pivot(index="Date", columns="label", values="retorno")
    return ret_wide.apply(lambda x: (x - x.mean()) / x.std()).fillna(0)


def preparar_volumen(d0):
    d = d0.copy()
    d["vol_log"] = np.log1p(d["Volume"])
    vol_wide = d.pivot(index="Date", columns="label", values="vol_log")
    return vol_wide.apply(lambda x: (x - x.mean()) / x.std()).fillna(0)


def preparar_features(d0):
    d = d0.copy()
    d["vol_log"] = np.log1p(d["Volume"])
    d = d.dropna(subset=["retorno"])
    ret_wide = d.pivot(index="Date", columns="label", values="retorno")
    price_wide = d.pivot(index="Date", columns="label", values="Close")
    raw_vol = d.pivot(index="Date", columns="label", values="Volume")
    vol_wide = d.pivot(index="Date", columns="label", values="vol_log")
    empresas = sorted(ret_wide.columns.tolist())
    # Referencia de mercado = promedio simple de los retornos del panel (no ^MERV)
    panel_ret = ret_wide.mean(axis=1)
    panel_var = panel_ret.var()

    features = {}
    for emp in empresas:
        r = ret_wide[emp].dropna()
        p = price_wide[emp].dropna()
        v = raw_vol[emp].dropna()
        vl = vol_wide[emp].dropna()
        idx = r.index.intersection(v.index)
        r_al, v_al, m_al = r.loc[idx], v.loc[idx], panel_ret.loc[idx]
        p_norm = p / p.iloc[0]
        pico = p_norm.cummax()
        beta = float(np.cov(r_al, m_al)[0, 1] / panel_var) if panel_var > 0 else 0.0
        ratio = (v / v.rolling(20, min_periods=5).mean()).replace([np.inf, -np.inf], np.nan).dropna()
        features[emp] = {
            "ret_mean": float(r.mean()), "volatilidad": float(r.std()),
            "skewness": float(stats.skew(r)), "kurtosis": float(stats.kurtosis(r)),
            "max_drawdown": float(((p_norm - pico) / pico).min()),
            "beta": beta,
            "corr_merval": float(np.corrcoef(r_al, m_al)[0, 1]),
            "momentum_20d": float(np.exp(r.iloc[-20:].sum()) - 1),
            "momentum_50d": float(np.exp(r.iloc[-50:].sum()) - 1),
            "vol_mean": float(vl.mean()), "vol_std": float(vl.std()),
            "vol_anormal": float(ratio.mean()) if len(ratio) else 0.0,
            "corr_vol_ret": float(np.corrcoef(np.abs(r_al), v_al)[0, 1]),
        }
    feat_df = pd.DataFrame(features).T
    if feat_df.isna().sum().sum() > 0:
        feat_df = feat_df.fillna(feat_df.mean())
    return feat_df


def matrices_corr(series_df):
    empresas = sorted(series_df.columns.tolist())
    S = series_df[empresas]
    corr = S.corr().values
    dist = np.clip(1 - corr, 0, 2)
    np.fill_diagonal(dist, 0)
    return dist, S.values.T, empresas


def matrices_ward(feat_df):
    empresas = list(feat_df.index)
    X = StandardScaler().fit_transform(feat_df.values)
    dist = squareform(pdist(X, metric="euclidean"))
    return dist, X, empresas


# ── 3. Algoritmos de clustering ──────────────────────────────────────────────
def correr_kmeans(X, empresas):
    inercias, siluetas = [], []
    for k in KS:
        km = KMeans(n_clusters=k, random_state=42, n_init=10).fit(X)
        inercias.append(float(km.inertia_))
        sil = silhouette_score(X, km.labels_) if len(set(km.labels_)) > 1 else 0.0
        siluetas.append(float(sil))
    k_opt = KS[int(np.argmax(siluetas))]
    km_opt = KMeans(n_clusters=k_opt, random_state=42, n_init=10).fit(X)
    return dict(empresas=empresas, ks=KS, inercias=inercias, siluetas=siluetas,
                k_opt=k_opt, sil_opt=max(siluetas), labels=list(km_opt.labels_))


def correr_jerarquico(dist, empresas, metodo="average"):
    Z = linkage(squareform(dist, checks=False), method=metodo)
    siluetas = []
    for k in KS:
        lbl = fcluster(Z, k, criterion="maxclust") - 1
        sil = silhouette_score(dist, lbl, metric="precomputed") if len(set(lbl)) > 1 else 0.0
        siluetas.append(float(sil))
    k_opt = KS[int(np.argmax(siluetas))]
    lbl_opt = list(fcluster(Z, k_opt, criterion="maxclust") - 1)
    return dict(empresas=empresas, ks=KS, siluetas=siluetas, k_opt=k_opt,
                sil_opt=max(siluetas), labels=lbl_opt)


def correr_mst(dist, empresas):
    n = len(empresas)
    mst = minimum_spanning_tree(csr_matrix(dist)).toarray()
    mst_sym = mst + mst.T
    aristas = [(mst_sym[i, j], i, j) for i in range(n) for j in range(i + 1, n) if mst_sym[i, j] > 0]
    aristas.sort(reverse=True)

    siluetas, labels_por_k = [], {}
    for k in KS:
        adj = mst_sym.copy()
        for w, i, j in aristas[:k - 1]:
            adj[i, j] = 0
            adj[j, i] = 0
        n_comp, labels = _componentes(adj)
        sil = silhouette_score(dist, labels, metric="precomputed") if len(set(labels)) > 1 else 0.0
        siluetas.append(float(sil))
        labels_por_k[k] = labels
    k_opt = KS[int(np.argmax(siluetas))]
    return dict(empresas=empresas, ks=KS, siluetas=siluetas, k_opt=k_opt,
                sil_opt=max(siluetas), labels=list(labels_por_k[k_opt]))


def _componentes(adj):
    from scipy.sparse.csgraph import connected_components
    n_comp, labels = connected_components(csr_matrix(adj), directed=False)
    return n_comp, labels


def main():
    # Corrida completa. Va dentro de main() para que otros scripts de esta carpeta
    # (analizar_grupo_no_degenerado.py) puedan importar las funciones de arriba
    # sin volver a correr todo ni reescribir los resultados.
    # ── 4. Correr las 3 representaciones x 2 períodos x 3 métodos ───────────────
    ANALISIS = {}
    for etiq, d0 in [("1 ano", df_1y), ("3 anos", df_3y)]:
        ret = preparar_precio(d0)
        vol = preparar_volumen(d0)
        feat = preparar_features(d0)

        dist_ret, X_ret, emp_ret = matrices_corr(ret)
        dist_vol, X_vol, emp_vol = matrices_corr(vol)
        dist_feat, X_feat, emp_feat = matrices_ward(feat)

        ANALISIS[("Precio", etiq)] = dict(
            km=correr_kmeans(X_ret, emp_ret), jer=correr_jerarquico(dist_ret, emp_ret, "average"),
            mst=correr_mst(dist_ret, emp_ret))
        ANALISIS[("Volumen", etiq)] = dict(
            km=correr_kmeans(X_vol, emp_vol), jer=correr_jerarquico(dist_vol, emp_vol, "average"),
            mst=correr_mst(dist_vol, emp_vol))
        ANALISIS[("13 features", etiq)] = dict(
            km=correr_kmeans(X_feat, emp_feat), jer=correr_jerarquico(dist_feat, emp_feat, "ward"),
            mst=correr_mst(dist_feat, emp_feat))

    print("\nCorridas completas:", list(ANALISIS.keys()))

    # ── 5. Tabla resumen — una fila por cluster x método x período x análisis ──
    filas = []
    for (analisis, periodo), res in ANALISIS.items():
        for metodo_nombre, metodo_key in [("K-Means", "km"), ("Jerarquico", "jer"), ("MST", "mst")]:
            r = res[metodo_key]
            labels = np.array(r["labels"])
            empresas = np.array(r["empresas"])
            for c in sorted(set(labels)):
                miembros = sorted(empresas[labels == c].tolist())
                filas.append({
                    "Analisis": analisis, "Periodo": periodo, "Metodo": metodo_nombre,
                    "k_optimo": r["k_opt"], "Silueta": round(r["sil_opt"], 3),
                    "Cluster": int(c) + 1, "N_empresas": len(miembros),
                    "Empresas": ", ".join(miembros),
                })

    resumen = pd.DataFrame(filas)
    resumen.to_csv("resumen_clustering_47.csv", index=False)
    print(f"\nGuardado: resumen_clustering_47.csv  ({len(resumen)} filas)")

    # Silueta de cada k (los mismos valores que se grafican en clustering_*.png)
    siluetas = pd.DataFrame([
        {"Analisis": a, "Periodo": per, "Metodo": nombre, "k": k, "Silueta": round(s, 3)}
        for (a, per), res in ANALISIS.items()
        for nombre, key in [("K-Means", "km"), ("Jerarquico", "jer"), ("MST", "mst")]
        for k, s in zip(res[key]["ks"], res[key]["siluetas"])
    ])
    siluetas.to_csv("siluetas_por_k.csv", index=False)
    print(f"Guardado: siluetas_por_k.csv  ({len(siluetas)} filas)")

    # ── 6. Alerta de clusters degenerados (1 empresa contra el resto) ──────────
    print("\n── Combinaciones con un cluster de 1 sola empresa contra el resto (degenerado) ──")
    deg = resumen[(resumen.N_empresas == 1)].merge(
        resumen.groupby(["Analisis", "Periodo", "Metodo", "k_optimo"])["N_empresas"].max().rename("max_grupo"),
        on=["Analisis", "Periodo", "Metodo", "k_optimo"])
    deg = deg[deg.max_grupo >= N_PANEL - 3]  # el otro grupo es casi todo el panel
    if len(deg):
        print(deg[["Analisis", "Periodo", "Metodo", "k_optimo", "Silueta", "Empresas"]].to_string(index=False))
    else:
        print("Ninguna.")

    # ── 7. Gráficos — elbow K-Means + silueta comparativa por período ──────────
    C_KM, C_JER, C_MST = "#E74C3C", "#2980B9", "#27AE60"
    for etiq in ["1 ano", "3 anos"]:
        analisis_periodo = [a for (a, p) in ANALISIS if p == etiq]
        fig, axes = plt.subplots(1, len(analisis_periodo), figsize=(6 * len(analisis_periodo), 4.2))
        if len(analisis_periodo) == 1:
            axes = [axes]
        for ax, analisis in zip(axes, analisis_periodo):
            res = ANALISIS[(analisis, etiq)]
            ax.plot(KS, res["km"]["siluetas"], "o-", color=C_KM, label="K-Means")
            ax.plot(KS, res["jer"]["siluetas"], "o-", color=C_JER, label="Jerárquico")
            ax.plot(KS, res["mst"]["siluetas"], "o-", color=C_MST, label="MST")
            ax.set_title(analisis, fontsize=11, fontweight="bold")
            ax.set_xlabel("k")
            ax.set_ylabel("Silueta")
            ax.legend(fontsize=8)
            ax.grid(alpha=0.3)
        fname = f"clustering_{etiq.replace(' ', '')}.png"
        plt.suptitle(f"Silueta por k — panel de 47 acciones ({etiq})", fontsize=13, y=1.03)
        plt.tight_layout()
        plt.savefig(fname, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"Gráfico guardado: {fname}")


if __name__ == "__main__":
    main()
