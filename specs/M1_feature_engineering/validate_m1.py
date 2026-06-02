"""
Script de validacion para M1 — Feature Engineering.
Ejecutar despues de build_feature_matrix().
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared.config import DATA_DIR, RENDIMIENTO_RANGOS, TRAIN_HASTA
from shared.dane_codes import MVP_CODIGOS

COLUMNAS_FEATURE_MATRIX = [
    "codigo_dane", "municipio", "departamento", "cultivo", "año",
    "prec_acum_mm", "anomalia_prec", "temp_media_c", "anomalia_temp",
    "dias_secos", "hum_media_pct",
    "rendimiento_t1", "rendimiento_prom3a", "tendencia_rend_3a",
    "area_sembrada_t1",
    "pct_alta", "pct_media", "pct_baja", "pct_exclusion",
    "pct_condicionada", "pct_no_condicionada",
    "indice_agroinsumos", "percentil_fertilizantes", "señal_riesgo_economico",
    "target_rendimiento",
]

COLUMNAS_PROHIBIDAS = {"produccion", "area_cosechada", "rendimiento"}
FEATURES_CRITICAS = ["rendimiento_t1", "prec_acum_mm", "temp_media_c", "indice_agroinsumos"]


class WarnCollector:
    def __init__(self) -> None:
        self.count = 0

    def warn(self, msg: str) -> None:
        self.count += 1
        print(f"WARNING: {msg}")


def run_validations(data_dir: Path = DATA_DIR) -> int:
    warn = WarnCollector()

    path = data_dir / "feature_matrix.parquet"
    if not path.exists():
        raise FileNotFoundError(f"❌ Archivo no encontrado: {path}")

    df = pd.read_parquet(path)
    if df.empty:
        raise AssertionError("❌ Feature_Matrix vacia")

    # --- Esquema ---
    if list(df.columns) != COLUMNAS_FEATURE_MATRIX:
        faltantes = [c for c in COLUMNAS_FEATURE_MATRIX if c not in df.columns]
        extras = [c for c in df.columns if c not in COLUMNAS_FEATURE_MATRIX]
        raise AssertionError(
            f"❌ Esquema incorrecto. Faltantes: {faltantes} | Extras: {extras}"
        )

    # --- No fuga ---
    prohibidas = [c for c in df.columns if c in COLUMNAS_PROHIBIDAS]
    if prohibidas:
        raise AssertionError(f"❌ Fuga detectada — columnas prohibidas: {prohibidas}")

    # --- Cobertura MVP ---
    codigos_presentes = set(df["codigo_dane"].dropna().astype(str).str.zfill(5).unique())
    faltantes_mvp = [c for c in MVP_CODIGOS if c not in codigos_presentes]
    if faltantes_mvp:
        raise AssertionError(f"❌ Municipios MVP ausentes: {faltantes_mvp}")

    # --- Train subset ---
    train = df[df["año"] <= TRAIN_HASTA].copy()

    # --- Features criticas sin NaN en train (por MVP) ---
    for codigo in MVP_CODIGOS:
        sub = train[train["codigo_dane"].astype(str).str.zfill(5) == codigo]
        if sub.empty:
            continue
        for feat in FEATURES_CRITICAS:
            n_nan = int(sub[feat].isna().sum())
            if n_nan > 0:
                warn.warn(f"[M1] {feat}: {n_nan} NaN en train para {codigo}")

    # --- Rangos de rendimiento_t1 ---
    for cultivo, (rmin, rmax) in RENDIMIENTO_RANGOS.items():
        sub = train[train["cultivo"] == cultivo]
        fuera = sub[sub["rendimiento_t1"].notna() & ((sub["rendimiento_t1"] < rmin) | (sub["rendimiento_t1"] > rmax))]
        for _, row in fuera.iterrows():
            warn.warn(
                f"[M1] {row['codigo_dane']} {cultivo} {int(row['año'])}: rendimiento_t1={row['rendimiento_t1']} fuera de rango"
            )

    # --- prec_acum_mm > 0 en train ---
    malos_prec = train[train["prec_acum_mm"].notna() & (train["prec_acum_mm"] <= 0)]
    for _, row in malos_prec.iterrows():
        warn.warn(f"[M1] {row['codigo_dane']} {int(row['año'])}: prec_acum_mm={row['prec_acum_mm']} <= 0")

    # --- Suma aptitud en MVP ---
    for (codigo, cultivo), sub in train.groupby(["codigo_dane", "cultivo"], dropna=True):
        suma = (sub["pct_alta"] + sub["pct_media"] + sub["pct_baja"] + sub["pct_exclusion"]).iloc[0]
        if pd.notna(suma) and (suma < 99 or suma > 101):
            warn.warn(f"[M1] {codigo} {cultivo}: suma aptitud = {suma:.1f}% fuera de [99,101]")

    # --- Minimo de filas en train por combo ---
    for (codigo, cultivo), sub in train.groupby(["codigo_dane", "cultivo"], dropna=True):
        if len(sub) < 3:
            warn.warn(f"[M1] {codigo} {cultivo}: solo {len(sub)} filas en train (minimo 3)")

    # --- Cobertura 3 cultivos en >=10 municipios (train) ---
    cubiertos = 0
    for codigo in MVP_CODIGOS:
        sub = train[train["codigo_dane"].astype(str).str.zfill(5) == codigo]
        cultivos = set(sub["cultivo"].dropna().unique())
        if {"Café", "Cacao", "Maíz"}.issubset(cultivos):
            cubiertos += 1
    if cubiertos < 10:
        warn.warn(
            f"[M1] Cobertura de cultivos insuficiente: {cubiertos}/10 municipios con 3 cultivos en train"
        )

    # --- Resultado final ---
    if warn.count == 0:
        print("[M1] VALIDACIÓN COMPLETA: PASS")
    else:
        print("[M1] VALIDACIÓN COMPLETA: WARN — revisar warnings")
    return 0


if __name__ == "__main__":
    try:
        code = run_validations()
    except Exception as exc:  # pragma: no cover
        print(str(exc))
        code = 1
    raise SystemExit(code)