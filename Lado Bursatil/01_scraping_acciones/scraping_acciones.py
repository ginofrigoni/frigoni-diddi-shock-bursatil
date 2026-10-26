"""
Scraping de acciones BYMA — tesis version 3.0
Tesina: Impacto de shocks informativos en empresas argentinas

Un solo script, tres pasos, tres resultados:

  1. Descarga las 53 candidatas originales (Panel General + Líderes de BYMA)
     y mide, para cada una, cuántos días de cotización trajo y qué % de esos
     días tuvo volumen real (no precio "pegado" por falta de operaciones).
        -> cobertura_53_candidatas.csv

  2. Aplica el criterio de selección:
        - dias == máximo observado   (cobertura de calendario 100%)
        - pct_dias_con_volumen >= 90%   (al menos 90% de esos días con operación real)
        -> panel_acciones_final.csv   (las que pasan)

  3. Vuelve a descargar, día por día (Open/High/Low/Close/Volume), las acciones
     que pasaron el criterio.
        -> precios_diarios_N_acciones.csv  (N = cantidad que pasa el criterio)

Ventana temporal fija: 2023-05-03 -> 2026-05-03 (3 años exactos, sin días de
más ni de menos) -- el final coincide con el final del corpus de noticias
del compañero (2026-05-03), para que el panel de 3 años y la ventana de
1 año usada en VIX/ADF/volatilidad terminen exactamente el mismo día.

CALENDARIO DE REFERENCIA: Yahoo Finance devuelve, para cada acción
individual, una fila "fantasma" en los feriados de BYMA (precio pegado al
cierre anterior, Volume=0) que el índice ^MERV directamente no tiene -- se
comprobó con YPFD.BA el 2026-05-01 (feriado, viernes): la acción trae una
fila con Volume=0, el índice no trae nada ese día. Para que todas las
acciones y el índice compartan exactamente el mismo calendario, se descarga
primero ^MERV y se usa su lista de fechas como calendario real de BYMA --
cualquier fila de una acción en una fecha que ^MERV no tenga se descarta,
sea cual sea el motivo.

EVENTOS CORPORATIVOS MAL AJUSTADOS: después del recorte al calendario se
aplican las correcciones de CORRECCIONES (ver más abajo) -- dos casos donde
Yahoo Finance no ajustó bien un split / dividendo en acciones. Se detectaron
buscando retornos diarios mayores a ±50% en todo el panel; el resto de los
saltos grandes se sostienen con volumen alto y son movimientos reales.

No modifica nada de "tesis version 2.0" — todo lo que genera este script
queda en esta carpeta, dentro de "tesis version 3.0".
"""

import yfinance as yf
import pandas as pd

# ── Ventana temporal — fija, 3 años exactos ─────────────────────────────────
FECHA_INICIO = "2023-05-03"
FECHA_FIN    = "2026-05-04"   # exclusivo en yfinance -> último día real: 2026-05-03

# ── Criterio de selección (DIAS_MAXIMO se calcula después de descargar) ────
UMBRAL_VOL_PCT = 90.0

# ── Calendario real de BYMA — tomado del índice ^MERV, no de cada acción ───
print("Descargando ^MERV para fijar el calendario real de ruedas...")
_merv = yf.download("^MERV", start=FECHA_INICIO, end=FECHA_FIN, progress=False, auto_adjust=True)
CALENDARIO_REAL = set(_merv.index.normalize())
print(f"Calendario real: {len(CALENDARIO_REAL)} ruedas ({min(CALENDARIO_REAL).date()} -> {max(CALENDARIO_REAL).date()})")

# ── Las 53 candidatas originales (Panel General + Panel Líderes de BYMA) ──
# Nombres y sectores verificados contra la ficha de cada ticker en Yahoo
# Finance; el sector se asigna por negocio principal. TGLT.BA y GCDI.BA son el
# mismo emisor (TGLT pasó a llamarse GCDI): las 53 candidatas son 52 empresas
# distintas, y TGLT "sin datos" es el ticker viejo, no una baja real.
EMPRESAS = [
    # ── S&P Merval (núcleo, 20 oficiales) ────────────────────────────────
    {"ticker": "YPFD.BA",  "empresa": "YPF SA",                            "sector": "Energía",        "oficial": True},
    {"ticker": "TGSU2.BA", "empresa": "Transportadora de Gas del Sur",     "sector": "Energía",        "oficial": True},
    {"ticker": "TGNO4.BA", "empresa": "Transportadora de Gas del Norte",   "sector": "Energía",        "oficial": True},
    {"ticker": "COME.BA",  "empresa": "Sociedad Comercial del Plata",      "sector": "Conglomerado",        "oficial": True},
    {"ticker": "PAMP.BA",  "empresa": "Pampa Energía",                     "sector": "Utilities",      "oficial": True},
    {"ticker": "CEPU.BA",  "empresa": "Central Puerto",                    "sector": "Utilities",      "oficial": True},
    {"ticker": "TRAN.BA",  "empresa": "Transener",                         "sector": "Utilities",      "oficial": True},
    {"ticker": "EDN.BA",   "empresa": "Edenor",                            "sector": "Utilities",      "oficial": True},
    {"ticker": "GGAL.BA",  "empresa": "Grupo Financiero Galicia",          "sector": "Financiero",     "oficial": True},
    {"ticker": "BMA.BA",   "empresa": "Banco Macro",                       "sector": "Financiero",     "oficial": True},
    {"ticker": "BBAR.BA",  "empresa": "BBVA Banco Francés",                "sector": "Financiero",     "oficial": True},
    {"ticker": "SUPV.BA",  "empresa": "Supervielle",                       "sector": "Financiero",     "oficial": True},
    {"ticker": "BYMA.BA",  "empresa": "Bolsas y Mercados Argentinos",      "sector": "Financiero",     "oficial": True},
    {"ticker": "VALO.BA",  "empresa": "Banco de Valores",                  "sector": "Financiero",     "oficial": True},
    {"ticker": "TXAR.BA",  "empresa": "Ternium Argentina",                 "sector": "Materiales",     "oficial": True},
    {"ticker": "ALUA.BA",  "empresa": "Aluar",                             "sector": "Materiales",     "oficial": True},
    {"ticker": "MIRG.BA",  "empresa": "Mirgor",                            "sector": "Consumo",        "oficial": True},
    {"ticker": "TECO2.BA", "empresa": "Telecom Argentina",                 "sector": "Comunicaciones", "oficial": True},
    {"ticker": "CVH.BA",   "empresa": "Cablevision Holding",               "sector": "Comunicaciones", "oficial": True},
    {"ticker": "CRES.BA",  "empresa": "Cresud",                            "sector": "Conglomerado",    "oficial": True},

    # ── Financiero / Bancos adicionales ──────────────────────────────────
    {"ticker": "BPAT.BA",  "empresa": "Banco Patagonia",                   "sector": "Financiero",     "oficial": False},
    {"ticker": "BHIP.BA",  "empresa": "Banco Hipotecario",                 "sector": "Financiero",     "oficial": False},
    {"ticker": "GCDI.BA",  "empresa": "GCDI S.A. (ex TGLT)",               "sector": "Real Estate",     "oficial": False},

    # ── Energía / Gas / Petróleo adicionales ─────────────────────────────
    {"ticker": "CAPX.BA",  "empresa": "CAPEX SA",                          "sector": "Energía",        "oficial": False},
    {"ticker": "CGPA2.BA", "empresa": "Camuzzi Gas Pampeana",              "sector": "Utilities",      "oficial": False},
    {"ticker": "DGCU2.BA", "empresa": "Distribuidora de Gas Cuyana",       "sector": "Utilities",      "oficial": False},
    {"ticker": "METR.BA",  "empresa": "MetroGas",                          "sector": "Utilities",      "oficial": False},
    {"ticker": "GBAN.BA",  "empresa": "Naturgy BAN",                       "sector": "Utilities",      "oficial": False},
    {"ticker": "OEST.BA",  "empresa": "Grupo Concesionario del Oeste",     "sector": "Industrial",        "oficial": False},

    # ── Materiales / Industria ────────────────────────────────────────────
    {"ticker": "LOMA.BA",  "empresa": "Loma Negra",                        "sector": "Materiales",     "oficial": False},
    {"ticker": "HARG.BA",  "empresa": "Holcim Argentina",                  "sector": "Materiales",     "oficial": False},
    {"ticker": "CELU.BA",  "empresa": "Celulosa Argentina",                "sector": "Materiales",     "oficial": False},
    {"ticker": "FIPL.BA",  "empresa": "Fiplasto",                          "sector": "Materiales",     "oficial": False},
    {"ticker": "RIGO.BA",  "empresa": "Rigolleau",                         "sector": "Materiales",     "oficial": False},

    # ── Consumo / Alimentos ───────────────────────────────────────────────
    {"ticker": "MOLI.BA",  "empresa": "Molinos Río de la Plata",           "sector": "Consumo",        "oficial": False},
    {"ticker": "LEDE.BA",  "empresa": "Ledesma",                           "sector": "Consumo",        "oficial": False},
    {"ticker": "SAMI.BA",  "empresa": "San Miguel",                        "sector": "Consumo",        "oficial": False},
    {"ticker": "AGRO.BA",  "empresa": "Agrometal",                         "sector": "Industrial",        "oficial": False},
    {"ticker": "MORI.BA",  "empresa": "Morixe Hermanos",                   "sector": "Consumo",        "oficial": False},
    {"ticker": "LONG.BA",  "empresa": "Longvie",                           "sector": "Consumo",        "oficial": False},
    {"ticker": "GRIM.BA",  "empresa": "Grimoldi",                          "sector": "Consumo",        "oficial": False},
    {"ticker": "HAVA.BA",  "empresa": "Havanna Holding",                   "sector": "Consumo",        "oficial": False},

    # ── Real Estate adicionales ───────────────────────────────────────────
    {"ticker": "IRSA.BA",  "empresa": "IRSA Inversiones y Representaciones","sector": "Real Estate",   "oficial": False},
    {"ticker": "CTIO.BA",  "empresa": "Consultatio",                       "sector": "Real Estate",    "oficial": False},
    {"ticker": "TGLT.BA",  "empresa": "TGLT SA (hoy GCDI)",                "sector": "Real Estate",    "oficial": False},

    # ── Comunicaciones adicionales ────────────────────────────────────────
    {"ticker": "NQNO.BA",  "empresa": "NII Holdings (Nextel)",             "sector": "Comunicaciones", "oficial": False},

    # ── Otros / Conglomerados ─────────────────────────────────────────────
    {"ticker": "GARO.BA",  "empresa": "Garovaglio y Zorraquín",            "sector": "Conglomerado",   "oficial": False},
    {"ticker": "POLL.BA",  "empresa": "Polledo",                           "sector": "Conglomerado",   "oficial": False},
    {"ticker": "SEMI.BA",  "empresa": "Molinos Juan Semino",               "sector": "Consumo",        "oficial": False},
    {"ticker": "ROSE.BA",  "empresa": "Instituto Rosenbusch",              "sector": "Salud",     "oficial": False},
    {"ticker": "BOLT.BA",  "empresa": "Boldt",                             "sector": "Tecnología",     "oficial": False},
    {"ticker": "AUSO.BA",  "empresa": "Autopistas del Sol",                "sector": "Industrial",     "oficial": False},
    {"ticker": "CARC.BA",  "empresa": "Carboclor",                         "sector": "Materiales",    "oficial": False},
]


# ── Correcciones de eventos corporativos que Yahoo Finance no ajustó bien ──
# Cada una divide Open/High/Low/Close por `factor` y multiplica Volume por
# `factor` en las fechas [desde, hasta] -- el ajuste estándar de un split.
# Saltos > ±50% que NO se corrigen porque son reales (se sostienen y vienen
# con volumen anormalmente alto): GCDI 24/01/2024, CELU 17/09/2025 y
# 18/02/2026, RIGO 18/06/2025.
CORRECCIONES = [
    # SEMI.BA: Yahoo registra un split de 4,227257 el 16/12/2024 y ajustó los
    # días anteriores, pero dejó ESE día con el precio sin dividir ($113,2 en
    # vez de ~$26,8; al día siguiente vuelve a $29,8). Se corrige solo ese día.
    {"ticker": "SEMI.BA", "desde": "2024-12-16", "hasta": "2024-12-16", "factor": 4.227257},
    # AGRO.BA: dividendo en acciones de noviembre 2023 (Yahoo lo registra como
    # split 21:10 el 06/11/2023) que Yahoo NO aplicó a los precios anteriores.
    # Se ajusta hasta el 02/11/2023 inclusive. El 03/11/2023 ($13,9, con 8,5 M
    # de volumen) es el primer día en la escala nueva y se deja tal cual: es
    # dudoso, pero no hay prueba de que sea un dato falso.
    {"ticker": "AGRO.BA", "desde": "2023-05-03", "hasta": "2023-11-02", "factor": 2.1},
]


def corregir_eventos_corporativos(ticker, datos):
    for c in CORRECCIONES:
        if c["ticker"] != ticker:
            continue
        fechas = datos.index.normalize()
        m = (fechas >= pd.Timestamp(c["desde"])) & (fechas <= pd.Timestamp(c["hasta"]))
        datos = datos.copy()
        datos.loc[m, ["Open", "High", "Low", "Close"]] = datos.loc[m, ["Open", "High", "Low", "Close"]] / c["factor"]
        volumen = datos["Volume"].astype(float)
        volumen[m] = (volumen[m] * c["factor"]).round()
        datos["Volume"] = volumen.astype("int64")
    return datos


def descargar(ticker, intentos=3):
    # Yahoo Finance falla de forma intermitente (red/rate-limit), no siempre
    # por falta real de datos -- se reintenta antes de declarar "sin datos".
    for intento in range(intentos):
        datos = yf.download(ticker, start=FECHA_INICIO, end=FECHA_FIN,
                             progress=False, auto_adjust=True)
        if not datos.empty:
            if isinstance(datos.columns, pd.MultiIndex):
                datos.columns = datos.columns.get_level_values(0)
            # Recorta al calendario real de BYMA (ver nota del módulo) --
            # saca filas "fantasma" en feriados que la acción trae y el
            # índice no (precio pegado, Volume=0).
            datos = datos[datos.index.normalize().isin(CALENDARIO_REAL)]
            return corregir_eventos_corporativos(ticker, datos)
    return datos  # vacío tras agotar los intentos


# ═══════════════════════════════════════════════════════════════════════
# PASO 1 — cobertura de las 53 candidatas
# ═══════════════════════════════════════════════════════════════════════
print("=" * 70)
print(f"PASO 1 — Cobertura de {len(EMPRESAS)} candidatas, ventana {FECHA_INICIO} -> {FECHA_FIN}")
print("=" * 70)

filas_cobertura = []
crudos = {}   # ticker -> DataFrame OHLCV, para reusar en el paso 3 sin re-descargar

for emp in EMPRESAS:
    ticker = emp["ticker"]
    try:
        datos = descargar(ticker)
        if datos.empty:
            print(f"  ✗  {ticker:12s} — sin datos en Yahoo Finance")
            filas_cobertura.append({**emp, "dias": 0, "fecha_inicio": None, "fecha_fin": None,
                                     "pct_dias_con_volumen": None, "vol_prom": None, "estado": "sin_datos"})
            continue

        n_dias = len(datos)
        pct_vol = float((datos["Volume"] > 0).mean() * 100)
        vol_prom = float(datos["Volume"].mean())
        f_ini, f_fin = datos.index.min().date(), datos.index.max().date()

        print(f"  ✓  {ticker:12s} — {n_dias:4d} días | {f_ini} -> {f_fin} | "
              f"vol_prom {vol_prom:>12,.0f} | días con volumen {pct_vol:.1f}%")

        filas_cobertura.append({**emp, "dias": n_dias, "fecha_inicio": f_ini, "fecha_fin": f_fin,
                                 "pct_dias_con_volumen": round(pct_vol, 1), "vol_prom": round(vol_prom, 0),
                                 "estado": "descargada"})
        crudos[ticker] = datos

    except Exception as e:
        print(f"  ✗  {ticker:12s} — error: {e}")
        filas_cobertura.append({**emp, "dias": 0, "fecha_inicio": None, "fecha_fin": None,
                                 "pct_dias_con_volumen": None, "vol_prom": None, "estado": "error"})

cobertura = pd.DataFrame(filas_cobertura).sort_values(["dias", "ticker"], ascending=[False, True])
cobertura.to_csv("cobertura_53_candidatas.csv", index=False)
print(f"\nGuardado: cobertura_53_candidatas.csv  ({len(cobertura)} filas)")

# ═══════════════════════════════════════════════════════════════════════
# PASO 2 — aplicar el criterio de selección
# ═══════════════════════════════════════════════════════════════════════
descargadas_tmp = cobertura[cobertura.estado == "descargada"]
DIAS_MAXIMO = int(descargadas_tmp["dias"].max())

print()
print("=" * 70)
print(f"PASO 2 — Criterio: dias == {DIAS_MAXIMO} (máximo observado)  y  pct_dias_con_volumen >= {UMBRAL_VOL_PCT}%")
print("=" * 70)

descargadas = cobertura[cobertura.estado == "descargada"].copy()
descargadas["pasa"] = (descargadas.dias == DIAS_MAXIMO) & (descargadas.pct_dias_con_volumen >= UMBRAL_VOL_PCT)

panel = descargadas[descargadas.pasa].drop(columns=["pasa"]).sort_values(["sector", "ticker"]).reset_index(drop=True)
descartadas = pd.concat([
    descargadas[~descargadas.pasa].drop(columns=["pasa"]),
    cobertura[cobertura.estado != "descargada"],
]).sort_values("ticker").reset_index(drop=True)

panel.to_csv("panel_acciones_final.csv", index=False)
descartadas.to_csv("descartadas_por_cobertura.csv", index=False)

print(f"Pasan el criterio: {len(panel)} de {len(cobertura)}")
print(panel.sector.value_counts().to_string())
print(f"\nGuardado: panel_acciones_final.csv  ({len(panel)} filas)")
print(f"Guardado: descartadas_por_cobertura.csv  ({len(descartadas)} filas)")

# ═══════════════════════════════════════════════════════════════════════
# PASO 3 — precios diarios de las que pasaron el criterio
# ═══════════════════════════════════════════════════════════════════════
print()
print("=" * 70)
print(f"PASO 3 — Precios día por día de las {len(panel)} acciones seleccionadas")
print("=" * 70)

filas_precios = []
for _, row in panel.iterrows():
    ticker, empresa, sector = row["ticker"], row["empresa"], row["sector"]
    datos = crudos.get(ticker)          # reusa lo ya descargado en el paso 1
    if datos is None or datos.empty:
        datos = descargar(ticker)       # por si acaso, vuelve a intentar
    if datos.empty:
        print(f"  ✗  {ticker:12s} — sin datos")
        continue

    datos = datos.copy()
    datos["ticker"], datos["empresa"], datos["sector"] = ticker, empresa, sector
    datos = datos.reset_index()
    filas_precios.append(datos)
    print(f"  ✓  {ticker:12s} — {len(datos)} días")

precios = pd.concat(filas_precios, ignore_index=True)
cols = ["Date", "ticker", "empresa", "sector", "Open", "High", "Low", "Close", "Volume"]
precios = precios[[c for c in cols if c in precios.columns]]
nombre_salida = f"precios_diarios_{len(panel)}_acciones.csv"
precios.to_csv(nombre_salida, index=False)

print("=" * 70)
print(f"Guardado: {nombre_salida}")
print(f"Filas totales: {len(precios):,}  |  Empresas: {precios['ticker'].nunique()}")
