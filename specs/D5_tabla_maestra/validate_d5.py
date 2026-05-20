"""
Script de validación para el pipeline D5 — Tabla Maestra.
Ejecutar después de modules.predictive.feature_builder.build_tabla_maestra()
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared.config import DATA_DIR, CULTIVOS_MVP, TRAIN_HASTA, VAL_AÑO, TEST_DESDE
from shared.dane_codes import MVP_CODIGOS

COLUMNAS_ESPERADAS = [
    "codigo_dane",
    "municipio",
    "departamento",
    "cultivo",
    "año",
    "rendimiento",
    "area_sembrada",
    "rendimiento_t1",
    "rendimiento_t2",
    "rendimiento_t3",
    "rendimiento_prom3a",
    "rendimiento_tend3a",
    "area_sembrada_t1",
    "area_cambio_pct",
    "prec_acum_mm",
    "temp_media_c",
    "hum_media_pct",
    "dias_secos",
    "anomalia_prec",
    "anomalia_temp",
    "pct_aptitud_alta",
    "pct_aptitud_media",
    "pct_aptitud_baja",
    "pct_exclusion",
    "pct_condicionada",
    "fertilizantes",
    "pct_fertilizantes",
    "señal_riesgo_eco",
]

COLUMNAS_FUGA = ["area_cosechada", "produccion"]
CULTIVOS_ESPERADOS = set(CULTIVOS_MVP)
SEÑALES_VALIDAS = {"Bajo", "Medio", "Alto"}


def run_validations(data_dir: Path = DATA_DIR) -> None:
    """Ejecuta todas las validaciones. Lanza AssertionError si alguna falla."""
    path = Path(data_dir) / "tabla_maestra.parquet"
    assert path.exists(), f"❌ Archivo no encontrado: {path}"
    df = pd.read_parquet(path)

    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    assert not faltantes, f"❌ Columnas faltantes: {faltantes}"

    extras = [c for c in df.columns if c not in COLUMNAS_ESPERADAS]
    assert not extras, f"❌ Columnas inesperadas (posible fuga): {extras}"

    assert list(df.columns) == COLUMNAS_ESPERADAS, (
        "❌ El orden de columnas no coincide con el esquema esperado"
    )

    assert df["codigo_dane"].astype(str).str.len().eq(5).all(), (
        "❌ codigo_dane con longitud != 5"
    )
    assert df["año"].dtype in ("int64", "Int64"), (
        f"❌ año no es int64/Int64: {df['año'].dtype}"
    )
    assert df["rendimiento"].dtype == "float64", (
        f"❌ rendimiento no es float64: {df['rendimiento'].dtype}"
    )
    for col in [
        "rendimiento_t1",
        "rendimiento_prom3a",
        "prec_acum_mm",
        "pct_aptitud_alta",
        "fertilizantes",
        "pct_fertilizantes",
    ]:
        assert df[col].dtype == "float64", f"❌ {col} no es float64: {df[col].dtype}"

    señales_reales = set(df["señal_riesgo_eco"].dropna().unique())
    invalidas = señales_reales - SEÑALES_VALIDAS
    assert not invalidas, f"❌ señal_riesgo_eco con valores inválidos: {invalidas}"

    for col in COLUMNAS_FUGA:
        assert col not in df.columns, (
            f"❌ Columna de fuga detectada: '{col}' no debe estar en la tabla maestra"
        )

    sample = df[df["cultivo"] == CULTIVOS_MVP[0]].sort_values(["codigo_dane", "año"])
    for codigo in sample["codigo_dane"].unique()[:3]:
        sub = sample[sample["codigo_dane"] == codigo].reset_index(drop=True)
        for i in range(1, len(sub)):
            rend_actual_t1 = sub.loc[i, "rendimiento_t1"]
            rend_año_anterior = sub.loc[i - 1, "rendimiento"]
            if pd.notna(rend_actual_t1) and pd.notna(rend_año_anterior):
                assert abs(rend_actual_t1 - rend_año_anterior) < 1e-6, (
                    f"❌ rendimiento_t1 incorrecto para {codigo} año {sub.loc[i, 'año']}: "
                    f"esperado {rend_año_anterior:.4f}, obtenido {rend_actual_t1:.4f}"
                )

    codigos_presentes = set(df["codigo_dane"].unique())
    faltantes_mvp = set(MVP_CODIGOS) - codigos_presentes
    assert not faltantes_mvp, f"❌ Municipios MVP sin datos: {faltantes_mvp}"

    cultivos_reales = set(df["cultivo"].unique())
    assert cultivos_reales == CULTIVOS_ESPERADOS, (
        f"❌ Cultivos inesperados: {cultivos_reales - CULTIVOS_ESPERADOS}"
    )

    combinaciones = df.groupby(["codigo_dane", "cultivo"]).ngroups
    eva_path = Path(data_dir) / "eva_completa.parquet"
    if eva_path.exists():
        eva = pd.read_parquet(eva_path)
        eva["codigo_dane"] = eva["codigo_dane"].astype(str)
        eva["cultivo"] = eva["cultivo"].astype(str)
        combos_eva = eva.groupby(["codigo_dane", "cultivo"]).ngroups
        assert combinaciones == combos_eva, (
            f"❌ Combinaciones municipio/cultivo en tabla ({combinaciones}) "
            f"!= EVA ({combos_eva})"
        )
    else:
        assert combinaciones >= 45, (
            f"❌ Se esperaban >= 45 combinaciones municipio/cultivo, hay {combinaciones}"
        )

    llave = ["codigo_dane", "cultivo", "año"]
    dups = int(df.duplicated(llave).sum())
    assert dups == 0, f"❌ {dups} duplicados por {llave}"

    if eva_path.exists():
        eva = pd.read_parquet(eva_path)
        n_eva_anual = eva.groupby(["codigo_dane", "cultivo", "año"]).ngroups
        assert len(df) == n_eva_anual, (
            f"❌ Tabla maestra ({len(df)} filas) != EVA agregada anual ({n_eva_anual} filas)"
        )

    primer_año_por_grupo = df.groupby(["codigo_dane", "cultivo"])["año"].min()
    for (codigo, cultivo), año_min in primer_año_por_grupo.items():
        fila = df[
            (df["codigo_dane"] == codigo)
            & (df["cultivo"] == cultivo)
            & (df["año"] == año_min)
        ]
        assert fila["rendimiento_t1"].isna().all(), (
            f"❌ rendimiento_t1 no es NaN para el primer año de {codigo}/{cultivo} ({año_min})"
        )

    assert (df["año"] <= TRAIN_HASTA).any(), (
        f"❌ No hay filas de entrenamiento (año <= {TRAIN_HASTA})"
    )
    assert (df["año"] == VAL_AÑO).any(), (
        f"❌ No hay filas de validación (año == {VAL_AÑO})"
    )
    assert (df["año"] >= TEST_DESDE).any(), (
        f"❌ No hay filas de test (año >= {TEST_DESDE})"
    )

    n_train = int((df["año"] <= TRAIN_HASTA).sum())
    n_val = int((df["año"] == VAL_AÑO).sum())
    n_test = int((df["año"] >= TEST_DESDE).sum())

    print("OK: Todos los criterios de aceptación pasaron")
    print("\nResumen:")
    print(f"  Total filas:    {len(df):>6,}")
    print(f"  Municipios:     {df['codigo_dane'].nunique():>6}/15")
    print(f"  Cultivos:       {df['cultivo'].nunique():>6}/3")
    print(f"  Años:           {int(df['año'].min())}–{int(df['año'].max())}")
    print("\n  Split temporal:")
    print(f"    Train  (<={TRAIN_HASTA}): {n_train:>5,} filas")
    print(f"    Val    ({VAL_AÑO}):   {n_val:>5,} filas")
    print(f"    Test   (>={TEST_DESDE}):   {n_test:>5,} filas")
    print("\n  Cobertura de features (% filas con valor):")
    for col in [
        "rendimiento_t1",
        "rendimiento_prom3a",
        "prec_acum_mm",
        "pct_aptitud_alta",
        "fertilizantes",
    ]:
        pct = df[col].notna().mean() * 100
        print(f"    {col:<25}: {pct:>5.1f}%")
    print("\n  Columnas de fuga verificadas: ninguna detectada")


if __name__ == "__main__":
    run_validations()
