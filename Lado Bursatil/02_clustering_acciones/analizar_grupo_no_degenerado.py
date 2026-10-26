"""
Analiza qué distingue al cluster no degenerado encontrado por clustering_acciones.py
(13 features, 3 años, K-Means, k=2): el grupo chico contra el resto del panel.

El grupo NO se escribe a mano: se lee de resumen_clustering_47.csv, así este
script siempre analiza el grupo que salió en la última corrida del clustering.

Tres preguntas:
  1. ¿En qué se diferencia el grupo? Retorno, volatilidad y LIQUIDEZ por empresa
     (días sin operar, % de días con el precio igual al anterior, volumen típico).
  2. ¿Qué features separan al grupo? Diferencia de medias, en desvíos estándar.
  3. ¿El grupo es comportamiento o liquidez? Se repite el K-Means de 13 features
     a 3 años en tres versiones:
        A) como está hoy
        B) los días sin operación como dato faltante (no como retorno 0 y volumen 0)
        C) sin las 4 acciones con más días sin operación
     Si el grupo se deshace en C, depende de que existan acciones poco líquidas.

Corresponde a la sección 4 de Documentacion_Clustering_Acciones.pdf.

Input:  ../01_scraping_acciones/precios_diarios_47_acciones.csv
        resumen_clustering_47.csv
Output: comparacion_grupo_no_degenerado.csv   (una fila por empresa, con liquidez)
        features_que_separan_grupo.csv        (diferencia de cada feature, grupo vs. resto)
        robustez_grupo_liquidez.csv           (pruebas A, B y C)
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd

import clustering_acciones as ca   # solo las funciones y los datos; la corrida completa está en su main()

N_SACAR_EN_C = 4

res = pd.read_csv("resumen_clustering_47.csv")
km = res[(res.Analisis == "13 features") & (res.Periodo == "3 anos") & (res.Metodo == "K-Means")]
GRUPO = km.loc[km["N_empresas"].idxmin(), "Empresas"].split(", ")
print(f"Grupo leído de resumen_clustering_47.csv ({len(GRUPO)}): {', '.join(GRUPO)}\n")

# ── 1. Retorno, volatilidad y liquidez por empresa ──────────────────────────
df = pd.read_csv("../01_scraping_acciones/precios_diarios_47_acciones.csv")
df["Date"] = pd.to_datetime(df["Date"])
df = df.sort_values(["ticker", "Date"])
df["label"] = df["ticker"].str.replace(".BA", "", regex=False)
df["retorno"] = df.groupby("ticker")["Close"].transform(lambda x: np.log(x / x.shift(1)))

por_empresa = df.groupby("label").agg(
    ret_mean=("retorno", "mean"),
    volatilidad=("retorno", "std"),
    volumen_prom=("Volume", "mean"),
    volumen_mediano=("Volume", "median"),
    dias_sin_operar=("Volume", lambda v: int((v == 0).sum())),
    dias_precio_quieto=("retorno", lambda r: int((r == 0).sum())),
    ruedas=("Volume", "size"),
).reset_index()
por_empresa["pct_precio_quieto"] = (por_empresa["dias_precio_quieto"] / por_empresa["ruedas"] * 100).round(1)
por_empresa["rank_volumen"] = por_empresa["volumen_mediano"].rank(method="min").astype(int)   # 1 = el de menos volumen
por_empresa["en_grupo"] = por_empresa["label"].isin(GRUPO)
por_empresa = por_empresa.sort_values(["en_grupo", "label"], ascending=[False, True])
por_empresa.to_csv("comparacion_grupo_no_degenerado.csv", index=False)

print(por_empresa[por_empresa.en_grupo][["label", "dias_sin_operar", "pct_precio_quieto", "volumen_mediano", "rank_volumen"]].to_string(index=False))
print("\n── Promedio por grupo ──")
cols = ["ret_mean", "volatilidad", "pct_precio_quieto", "dias_sin_operar", "volumen_mediano"]
print(por_empresa.groupby("en_grupo")[cols].mean().round(4).to_string())

# ── 2. Qué features separan al grupo ────────────────────────────────────────
feat = ca.preparar_features(ca.df_3y)
z = (feat - feat.mean()) / feat.std()
en = z.index.isin(GRUPO)
separa = (z[en].mean() - z[~en].mean()).rename("diferencia_desvios").to_frame()
separa["abs"] = separa["diferencia_desvios"].abs()
separa = separa.sort_values("abs", ascending=False).drop(columns="abs")
separa.index.name = "feature"
separa.round(3).to_csv("features_que_separan_grupo.csv")
print("\n── Features que separan al grupo (en desvíos estándar) ──")
print(separa.round(2).to_string())


# ── 3. Robustez: ¿comportamiento o liquidez? ────────────────────────────────
def kmeans_13_features(d):
    f = ca.preparar_features(d)
    _, X, emp = ca.matrices_ward(f)
    r = ca.correr_kmeans(X, emp)
    lab, e = np.array(r["labels"]), np.array(r["empresas"])
    grupos = sorted([sorted(e[lab == c].tolist()) for c in set(lab)], key=len)
    return r["k_opt"], r["sil_opt"], grupos


menos_liquidas = por_empresa.sort_values("dias_sin_operar", ascending=False).head(N_SACAR_EN_C)["label"].tolist()

d_a = ca.df_3y.copy()
d_b = ca.df_3y.copy()
sin_operar = d_b["Volume"] == 0
d_b.loc[sin_operar, ["retorno", "Volume"]] = np.nan
d_c = ca.df_3y[~ca.df_3y["label"].isin(menos_liquidas)].copy()

pruebas = [
    ("A", "Como está hoy", d_a),
    ("B", "Días sin operación como dato faltante", d_b),
    ("C", f"Sin las {N_SACAR_EN_C} acciones con más días sin operar ({', '.join(menos_liquidas)})", d_c),
]
filas = []
print("\n── Robustez del grupo ──")
for clave, desc, d in pruebas:
    k, sil, grupos = kmeans_13_features(d)
    chico = grupos[0]
    filas.append({
        "prueba": clave, "descripcion": desc, "acciones": d["ticker"].nunique(), "k": k,
        "silueta": round(sil, 3), "tamanos": " / ".join(str(len(g)) for g in grupos),
        "grupo_chico": ", ".join(chico), "en_comun_con_grupo": len(set(chico) & set(GRUPO)),
    })
    print(f"  {clave}) {desc}: k={k}, silueta={sil:.3f}, tamaños={[len(g) for g in grupos]}, "
          f"en común con el grupo: {len(set(chico) & set(GRUPO))}")
pd.DataFrame(filas).to_csv("robustez_grupo_liquidez.csv", index=False)

print("\nGuardado: comparacion_grupo_no_degenerado.csv, features_que_separan_grupo.csv, robustez_grupo_liquidez.csv")
