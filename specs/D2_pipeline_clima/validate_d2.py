"""
Script de validación para el pipeline D2 — Clima.
Ejecutar después de modules.climate.ingestion.run_pipeline()

Uso:
    python specs/D2_pipeline_clima/validate_d2.py

O desde Python:
    from specs.D2_pipeline_clima.validate_d2 import run_validations
    run_validations()  # Lanza AssertionError si algo falla
"""
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from shared.config import DATA_DIR
from shared.dane_codes import MVP_CODIGOS, DANE_TO_NAME

COLUMNAS_ESPERADAS = [
    "codigo_dane",
    "municipio",
    "año",
    "prec_acum_mm",
    "prec_dias_secos",
    "prec_dias_lluvia",
    "temp_media_c",
    "temp_max_media_c",
    "hum_media_pct",
    "n_estaciones_prec",
    "n_estaciones_temp",
    "anomalia_prec",
    "anomalia_temp",
]

AÑOS_ESPERADOS = list(range(2007, 2025))  # 2007–2024 inclusive
N_MUNICIPIOS = 15
N_AÑOS = 18
N_FILAS_ESPERADAS = N_MUNICIPIOS * N_AÑOS  # 270


def run_validations(data_dir: Path = DATA_DIR) -> None:
    """
    Ejecuta todas las validaciones del pipeline D2.

    Lanza AssertionError con mensaje descriptivo si alguna validación falla.
    Las advertencias de cobertura se imprimen pero no detienen el script.

    Args:
        data_dir: Directorio donde buscar clima_agregado.parquet.
                  Default: DATA_DIR de shared/config.py.
    """
    print("=" * 60)
    print("D2.5 — Validación del pipeline climático")
    print("=" * 60)

    # ── Archivo existe ────────────────────────────────────────────────────────
    path = data_dir / "clima_agregado.parquet"
    assert path.exists(), (
        f"❌ Archivo no encontrado: {path}\n"
        f"   Ejecutar primero: python -m modules.climate.ingestion"
    )
    print(f"✅ Archivo encontrado: {path}")

    df = pd.read_parquet(path)

    # ── Dimensiones ───────────────────────────────────────────────────────────
    assert len(df) == N_FILAS_ESPERADAS, (
        f"❌ Se esperaban {N_FILAS_ESPERADAS} filas ({N_MUNICIPIOS} municipios × {N_AÑOS} años), "
        f"hay {len(df)}"
    )
    print(f"✅ Dimensiones: {len(df)} filas")

    assert len(df.columns) == len(COLUMNAS_ESPERADAS), (
        f"❌ Se esperaban {len(COLUMNAS_ESPERADAS)} columnas, hay {len(df.columns)}.\n"
        f"   Columnas reales: {list(df.columns)}"
    )

    # ── Esquema: columnas presentes y en orden exacto ─────────────────────────
    assert list(df.columns) == COLUMNAS_ESPERADAS, (
        f"❌ Columnas incorrectas o en orden incorrecto.\n"
        f"   Esperadas: {COLUMNAS_ESPERADAS}\n"
        f"   Reales:    {list(df.columns)}"
    )
    print(f"✅ Esquema: {len(COLUMNAS_ESPERADAS)} columnas en orden correcto")

    # ── Tipos de datos ────────────────────────────────────────────────────────
    assert df["codigo_dane"].dtype == object, (
        f"❌ codigo_dane no es string/object: {df['codigo_dane'].dtype}"
    )
    assert df["codigo_dane"].str.len().eq(5).all(), (
        f"❌ codigo_dane con longitud != 5 en {(~df['codigo_dane'].str.len().eq(5)).sum()} registros"
    )

    assert df["año"].dtype == "int64", (
        f"❌ año no es int64: {df['año'].dtype}"
    )

    assert df["prec_acum_mm"].dtype == "float64", (
        f"❌ prec_acum_mm no es float64: {df['prec_acum_mm'].dtype}"
    )
    assert df["prec_dias_secos"].dtype in ("float64", "Int64", "int64"), (
        f"❌ prec_dias_secos tipo inesperado: {df['prec_dias_secos'].dtype}"
    )
    assert df["prec_dias_lluvia"].dtype in ("float64", "Int64", "int64"), (
        f"❌ prec_dias_lluvia tipo inesperado: {df['prec_dias_lluvia'].dtype}"
    )
    assert df["temp_media_c"].dtype == "float64", (
        f"❌ temp_media_c no es float64: {df['temp_media_c'].dtype}"
    )
    assert df["temp_max_media_c"].dtype == "float64", (
        f"❌ temp_max_media_c no es float64: {df['temp_max_media_c'].dtype}"
    )
    assert df["hum_media_pct"].dtype == "float64", (
        f"❌ hum_media_pct no es float64: {df['hum_media_pct'].dtype}"
    )
    assert df["n_estaciones_prec"].dtype == "int64", (
        f"❌ n_estaciones_prec no es int64: {df['n_estaciones_prec'].dtype}"
    )
    assert df["n_estaciones_temp"].dtype == "int64", (
        f"❌ n_estaciones_temp no es int64: {df['n_estaciones_temp'].dtype}"
    )
    assert df["anomalia_prec"].dtype == "float64", (
        f"❌ anomalia_prec no es float64: {df['anomalia_prec'].dtype}"
    )
    assert df["anomalia_temp"].dtype == "float64", (
        f"❌ anomalia_temp no es float64: {df['anomalia_temp'].dtype}"
    )
    print("✅ Tipos de datos correctos")

    # ── Rango de años ─────────────────────────────────────────────────────────
    años_reales = sorted(df["año"].unique().tolist())
    assert años_reales == AÑOS_ESPERADOS, (
        f"❌ Años incorrectos.\n"
        f"   Esperados: {AÑOS_ESPERADOS}\n"
        f"   Reales:    {años_reales}"
    )
    print(f"✅ Rango de años: {AÑOS_ESPERADOS[0]}–{AÑOS_ESPERADOS[-1]}")

    # ── Valores físicamente imposibles ────────────────────────────────────────
    prec_neg = (df["prec_acum_mm"] < 0).sum()
    assert prec_neg == 0, (
        f"❌ {prec_neg} valores negativos en prec_acum_mm — "
        f"la precipitación no puede ser negativa"
    )

    temp_invalida = df["temp_media_c"].dropna()
    temp_invalida = temp_invalida[(temp_invalida < 0) | (temp_invalida > 45)]
    assert temp_invalida.empty, (
        f"❌ {len(temp_invalida)} valores de temp_media_c fuera del rango físico 0–45°C "
        f"(Colombia)"
    )

    hum_invalida = df["hum_media_pct"].dropna()
    hum_invalida = hum_invalida[(hum_invalida < 0) | (hum_invalida > 100)]
    assert hum_invalida.empty, (
        f"❌ {len(hum_invalida)} valores de hum_media_pct fuera del rango físico 0–100%"
    )
    print("✅ Rangos físicos válidos (precipitación ≥ 0, temperatura 0–45°C, humedad 0–100%)")

    # ── n_estaciones sin NaN y ≥ 0 ───────────────────────────────────────────
    assert df["n_estaciones_prec"].isna().sum() == 0, (
        "❌ n_estaciones_prec tiene NaN — debe ser 0 cuando no hay datos, no NaN"
    )
    assert df["n_estaciones_temp"].isna().sum() == 0, (
        "❌ n_estaciones_temp tiene NaN — debe ser 0 cuando no hay datos, no NaN"
    )
    assert (df["n_estaciones_prec"] >= 0).all(), (
        "❌ n_estaciones_prec tiene valores negativos"
    )
    assert (df["n_estaciones_temp"] >= 0).all(), (
        "❌ n_estaciones_temp tiene valores negativos"
    )
    print("✅ n_estaciones_prec y n_estaciones_temp: sin NaN, todos ≥ 0")

    # ── Cobertura del MVP ─────────────────────────────────────────────────────
    codigos_presentes = set(df["codigo_dane"].unique())
    faltantes = set(MVP_CODIGOS) - codigos_presentes
    assert not faltantes, (
        f"❌ Municipios del MVP ausentes en el output: {sorted(faltantes)}\n"
        f"   Estos municipios son obligatorios para el modelo predictivo"
    )

    assert df["codigo_dane"].nunique() == N_MUNICIPIOS, (
        f"❌ Se esperaban exactamente {N_MUNICIPIOS} municipios únicos, "
        f"hay {df['codigo_dane'].nunique()}"
    )
    print(f"✅ Cobertura MVP: los {N_MUNICIPIOS} municipios están presentes")

    # ── Cada municipio tiene exactamente N_AÑOS filas ─────────────────────────
    filas_por_municipio = df.groupby("codigo_dane").size()
    mal_conteo = filas_por_municipio[filas_por_municipio != N_AÑOS]
    assert mal_conteo.empty, (
        f"❌ Municipios con número incorrecto de filas (se esperan {N_AÑOS} por municipio):\n"
        + "\n".join(
            f"   {DANE_TO_NAME.get(c, c)} ({c}): {n} filas"
            for c, n in mal_conteo.items()
        )
    )
    print(f"✅ Cada municipio tiene exactamente {N_AÑOS} filas (una por año)")

    # ── Integridad: municipio consistente con codigo_dane ─────────────────────
    df_check = df[["codigo_dane", "municipio"]].drop_duplicates()
    inconsistentes = []
    for _, row in df_check.iterrows():
        esperado = DANE_TO_NAME.get(row["codigo_dane"])
        if row["municipio"] != esperado:
            inconsistentes.append(
                f"   {row['codigo_dane']}: tiene '{row['municipio']}', "
                f"se esperaba '{esperado}'"
            )
    assert not inconsistentes, (
        "❌ municipio inconsistente con codigo_dane (fuente de verdad: DANE_TO_NAME):\n"
        + "\n".join(inconsistentes)
    )
    print("✅ municipio consistente con codigo_dane en todos los registros")

    # ── Duplicados ────────────────────────────────────────────────────────────
    dups = df.duplicated(["codigo_dane", "año"]).sum()
    assert dups == 0, (
        f"❌ {dups} duplicados por (codigo_dane, año) — "
        f"cada combinación debe ser única"
    )
    print("✅ Sin duplicados por (codigo_dane, año)")

    # ── Advertencias de cobertura (no bloquean) ───────────────────────────────
    print("\n⚠️  Cobertura de datos (advertencias, no bloquean el pipeline):")
    umbrales = {
        "prec_acum_mm":  10,
        "temp_media_c":  10,
        "anomalia_prec": 5,
        "anomalia_temp": 5,
    }
    for variable, umbral_años in umbrales.items():
        cobertura = df.groupby("codigo_dane")[variable].apply(lambda s: s.notna().sum())
        municipios_ok = int((cobertura >= umbral_años).sum())
        if municipios_ok < 10:
            print(
                f"   ⚠️  {variable}: solo {municipios_ok}/{N_MUNICIPIOS} municipios "
                f"tienen ≥ {umbral_años} años con datos"
            )
        else:
            print(
                f"   ✅ {variable}: {municipios_ok}/{N_MUNICIPIOS} municipios "
                f"con ≥ {umbral_años} años de datos"
            )

    # ── Resumen final ─────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("✅ Todos los criterios de aceptación pasaron")
    print("=" * 60)
    print(f"\nResumen:")
    print(f"  Filas totales:    {len(df):>6,} ({N_MUNICIPIOS} municipios × {N_AÑOS} años)")
    print(f"  Años cubiertos:   {df['año'].min()}–{df['año'].max()}")
    print(f"  Municipios:       {df['codigo_dane'].nunique()}/{N_MUNICIPIOS}")
    print()

    metricas = [
        ("prec_acum_mm",  "Precipitación (mm)"),
        ("temp_media_c",  "Temperatura (°C)  "),
        ("hum_media_pct", "Humedad (%)       "),
        ("anomalia_prec", "Anomalía prec     "),
        ("anomalia_temp", "Anomalía temp (°C)"),
    ]
    for col, label in metricas:
        pct_nulo = df[col].isna().mean()
        media = df[col].mean()
        media_str = f"{media:>7.2f}" if not pd.isna(media) else "    N/A"
        print(f"  {label}: media={media_str} | NaN={pct_nulo:.1%}")


if __name__ == "__main__":
    run_validations()
