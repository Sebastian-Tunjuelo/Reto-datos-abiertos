"""
D5 — Construcción de tabla maestra (features).

Este módulo implementa la carga y validación de inputs (D5.1).
"""
from __future__ import annotations

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from shared.config import CULTIVOS_MVP, DATA_DIR, TEST_DESDE, TRAIN_HASTA, VAL_AÑO
from shared.dane_codes import MVP_CODIGOS

logger = logging.getLogger(__name__)


_INPUT_SPECS = [
    {
        "key": "eva",
        "file": "eva_completa.parquet",
        "required": ["codigo_dane", "cultivo", "año", "rendimiento", "area_sembrada"],
        "pipeline": "D1.3",
    },
    {
        "key": "clima",
        "file": "clima_agregado.parquet",
        "required": [
            "codigo_dane",
            "año",
            "prec_acum_mm",
            "temp_media_c",
            "hum_media_pct",
            "dias_secos",
            "anomalia_prec",
            "anomalia_temp",
        ],
        "pipeline": "D2.3",
    },
    {
        "key": "aptitud_cafe",
        "file": "aptitud_cafe.parquet",
        "required": ["codigo_dane", "pct_alta", "pct_media", "pct_baja", "pct_exclusion"],
        "pipeline": "D3.4",
    },
    {
        "key": "aptitud_cacao",
        "file": "aptitud_cacao.parquet",
        "required": ["codigo_dane", "pct_alta", "pct_media", "pct_baja", "pct_exclusion"],
        "pipeline": "D3.4",
    },
    {
        "key": "aptitud_maiz",
        "file": "aptitud_maiz.parquet",
        "required": ["codigo_dane", "pct_alta", "pct_media", "pct_baja", "pct_exclusion"],
        "pipeline": "D3.4",
    },
    {
        "key": "frontera",
        "file": "frontera.parquet",
        "required": ["codigo_dane", "pct_condicionada"],
        "pipeline": "D3.4",
    },
    {
        "key": "agroinsumos",
        "file": "agroinsumos.parquet",
        "required": ["año", "fertilizantes", "pct_fertilizantes", "señal_riesgo"],
        "pipeline": "D4.2",
    },
]


def _log_nulls(df: pd.DataFrame, required: list[str], label: str) -> None:
    null_counts = df[required].isna().sum()
    for col, count in null_counts.items():
        if count > 0:
            logger.info("D5.1: %s tiene %d nulos en '%s'", label, int(count), col)


def _warn_missing_mvp(df: pd.DataFrame, label: str) -> None:
    codigos = (
        df["codigo_dane"]
        .dropna()
        .astype(str)
        .str.zfill(5)
        .unique()
        .tolist()
    )
    presentes = set(codigos)
    faltantes = [c for c in MVP_CODIGOS if c not in presentes]
    if faltantes:
        logger.warning("D5.1: %s sin datos para %s", label, faltantes)


def _log_year_range(df: pd.DataFrame, label: str) -> None:
    years = pd.to_numeric(df["año"], errors="coerce")
    if years.notna().any():
        min_year = int(years.min())
        max_year = int(years.max())
        logger.info("D5.1: %s cubre años %d–%d", label, min_year, max_year)
    else:
        logger.warning("D5.1: %s sin años válidos para reportar cobertura", label)


def load_inputs(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    """
    Carga y valida los Parquets de entrada para la tabla maestra.

    Args:
        data_dir: Directorio donde están los Parquets. Default: DATA_DIR.

    Returns:
        Diccionario con claves:
        'eva', 'clima', 'aptitud_cafe', 'aptitud_cacao',
        'aptitud_maiz', 'frontera', 'agroinsumos'.
        Cada valor es un DataFrame con al menos las columnas mínimas requeridas.

    Raises:
        FileNotFoundError: Si algún Parquet de entrada no existe.
        KeyError: Si algún Parquet no tiene las columnas requeridas.
    """
    inputs: dict[str, pd.DataFrame] = {}

    for spec in _INPUT_SPECS:
        path = Path(data_dir) / spec["file"]
        if not path.exists():
            raise FileNotFoundError(
                f"D5.1: Falta {spec['file']}. Ejecutar el pipeline {spec['pipeline']} primero."
            )

        df = pd.read_parquet(path)

        if spec["key"] == "clima" and "dias_secos" not in df.columns:
            if "prec_dias_secos" in df.columns:
                df = df.rename(columns={"prec_dias_secos": "dias_secos"})

        missing = [col for col in spec["required"] if col not in df.columns]
        if missing:
            raise KeyError(f"D5.1: {spec['file']} no tiene columnas: {missing}")

        logger.info(
            "D5.1: %s cargado — %d filas, %d columnas",
            spec["key"],
            len(df),
            df.shape[1],
        )
        _log_nulls(df, spec["required"], spec["key"])
        inputs[spec["key"]] = df

    _warn_missing_mvp(inputs["eva"], "EVA")
    _warn_missing_mvp(inputs["clima"], "Clima")
    _warn_missing_mvp(inputs["aptitud_cafe"], "Aptitud café")
    _warn_missing_mvp(inputs["aptitud_cacao"], "Aptitud cacao")
    _warn_missing_mvp(inputs["aptitud_maiz"], "Aptitud maíz")

    _log_year_range(inputs["eva"], "EVA")
    _log_year_range(inputs["clima"], "Clima")
    _log_year_range(inputs["agroinsumos"], "Agroinsumos")

    return inputs


def _agregar_anual(df_eva: pd.DataFrame) -> pd.DataFrame:
    llave = ["codigo_dane", "cultivo", "año"]
    if not df_eva.duplicated(llave).any():
        columnas = llave + ["municipio", "departamento", "rendimiento", "area_sembrada"]
        return df_eva[columnas].copy()

    def _prom_ponderado(grupo: pd.DataFrame) -> pd.Series:
        if "area_cosechada" in grupo.columns and grupo["area_cosechada"].notna().any():
            pesos = grupo["area_cosechada"].fillna(0)
            if float(pesos.sum()) > 0:
                rendimiento = (grupo["rendimiento"] * pesos).sum() / pesos.sum()
            else:
                rendimiento = grupo["rendimiento"].mean()
        else:
            rendimiento = grupo["rendimiento"].mean()

        return pd.Series(
            {
                "rendimiento": rendimiento,
                "area_sembrada": grupo["area_sembrada"].sum(),
                "municipio": grupo["municipio"].iloc[0],
                "departamento": grupo["departamento"].iloc[0],
            }
        )

    df_agregado = df_eva.groupby(llave, as_index=False).apply(_prom_ponderado)
    return df_agregado.reset_index(drop=True)


def _pendiente_3a(series: pd.Series) -> pd.Series:
    shifted = series.shift(1)

    def _slope(window: pd.Series) -> float:
        vals = window.dropna()
        if len(vals) < 2:
            return np.nan
        x = np.arange(len(vals))
        return float(np.polyfit(x, vals, 1)[0])

    return shifted.rolling(window=3, min_periods=2).apply(_slope, raw=False)


def build_eva_features(df_eva: pd.DataFrame) -> pd.DataFrame:
    """
    Construye las features rezagadas de EVA para la tabla maestra.

    Agrega a nivel anual si hay múltiples periodos, luego calcula
    lags de rendimiento y área sembrada, promedio y tendencia de 3 años.

    Args:
        df_eva: DataFrame EVA completo (output de load_inputs()['eva']).

    Returns:
        DataFrame con una fila por (codigo_dane, cultivo, año) y las
        14 columnas especificadas. Features rezagadas son NaN para
        años sin historial suficiente — esto es esperado.

    Raises:
        ValueError: Si df_eva está vacío o no tiene las columnas requeridas.
    """
    if df_eva is None or df_eva.empty:
        raise ValueError("D5.2: df_eva está vacío")

    columnas_req = [
        "codigo_dane",
        "municipio",
        "departamento",
        "cultivo",
        "año",
        "rendimiento",
        "area_sembrada",
    ]
    faltantes = [c for c in columnas_req if c not in df_eva.columns]
    if faltantes:
        raise ValueError(f"D5.2: df_eva sin columnas requeridas: {faltantes}")

    n_antes = len(df_eva)
    df = _agregar_anual(df_eva)
    n_despues = len(df)
    if n_despues < n_antes:
        logger.info("D5.2: Agregación anual redujo %d → %d filas", n_antes, n_despues)

    df = df.sort_values(["codigo_dane", "cultivo", "año"]).reset_index(drop=True)
    grupo = df.groupby(["codigo_dane", "cultivo"], sort=False)

    df = df.assign(
        rendimiento_t1=grupo["rendimiento"].shift(1),
        rendimiento_t2=grupo["rendimiento"].shift(2),
        rendimiento_t3=grupo["rendimiento"].shift(3),
        area_sembrada_t1=grupo["area_sembrada"].shift(1),
    )

    rendimiento_prom3a = (
        grupo["rendimiento"]
        .apply(lambda s: s.shift(1).rolling(window=3, min_periods=1).mean())
        .reset_index(level=[0, 1], drop=True)
    )
    rendimiento_tend3a = (
        grupo["rendimiento"]
        .apply(_pendiente_3a)
        .reset_index(level=[0, 1], drop=True)
    )

    df = df.assign(
        rendimiento_prom3a=rendimiento_prom3a,
        rendimiento_tend3a=rendimiento_tend3a,
    )

    area_cambio_pct = (df["area_sembrada"] - df["area_sembrada_t1"]) / df[
        "area_sembrada_t1"
    ] * 100
    area_cambio_pct = area_cambio_pct.where(
        df["area_sembrada_t1"].notna() & (df["area_sembrada_t1"] != 0)
    )
    df = df.assign(area_cambio_pct=area_cambio_pct)

    columnas_salida = [
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
    ]
    return df[columnas_salida]


def build_tabla_maestra(
    output_dir: Path = DATA_DIR,
    data_dir: Path = DATA_DIR,
) -> pd.DataFrame:
    """
    Construye y guarda la tabla maestra cruzando D1–D4.

    Internamente llama a load_inputs() y build_eva_features(),
    luego une clima, aptitud, frontera y agroinsumos.

    Args:
        output_dir: Directorio donde guardar tabla_maestra.parquet.
        data_dir: Directorio donde están los Parquets de entrada.

    Returns:
        tabla_maestra como DataFrame con 28 columnas.

    Raises:
        FileNotFoundError: Si algún Parquet de entrada no existe.
        AssertionError: Si la integridad del ensamble falla.
    """
    inputs = load_inputs(data_dir=data_dir)
    df_base = build_eva_features(inputs["eva"])
    df = df_base.copy()

    # Paso 1 — Join clima
    df = pd.merge(
        df,
        inputs["clima"][
            [
                "codigo_dane",
                "año",
                "prec_acum_mm",
                "temp_media_c",
                "hum_media_pct",
                "dias_secos",
                "anomalia_prec",
                "anomalia_temp",
            ]
        ],
        on=["codigo_dane", "año"],
        how="left",
    )
    n_clima_nan = int(df["prec_acum_mm"].isna().sum())
    if n_clima_nan > 0:
        logger.warning("D5.3: %d filas sin clima (prec_acum_mm NaN)", n_clima_nan)

    # Paso 2 — Join aptitud por cultivo (estática)
    aptitud_map = {
        "Café": inputs["aptitud_cafe"],
        "Cacao": inputs["aptitud_cacao"],
        "Maíz": inputs["aptitud_maiz"],
    }
    partes = []
    for cultivo, df_aptitud in aptitud_map.items():
        sub = df[df["cultivo"] == cultivo]
        sub = pd.merge(
            sub,
            df_aptitud[["codigo_dane", "pct_alta", "pct_media", "pct_baja", "pct_exclusion"]],
            on="codigo_dane",
            how="left",
        )
        sub = sub.rename(
            columns={
                "pct_alta": "pct_aptitud_alta",
                "pct_media": "pct_aptitud_media",
                "pct_baja": "pct_aptitud_baja",
            }
        )
        partes.append(sub)
    df = pd.concat(partes, ignore_index=True)

    # Paso 3 — Join frontera
    df = pd.merge(
        df,
        inputs["frontera"][["codigo_dane", "pct_condicionada"]],
        on="codigo_dane",
        how="left",
    )

    # Paso 4 — Join agroinsumos
    df = pd.merge(
        df,
        inputs["agroinsumos"][["año", "fertilizantes", "pct_fertilizantes", "señal_riesgo"]],
        on="año",
        how="left",
    )
    df = df.rename(columns={"señal_riesgo": "señal_riesgo_eco"})
    n_agro_nan = int(df["fertilizantes"].isna().sum())
    if n_agro_nan > 0:
        logger.warning("D5.3: %d filas sin agroinsumos (fertilizantes NaN)", n_agro_nan)

    columnas_finales = [
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
    df = df[columnas_finales]
    df = df.sort_values(["codigo_dane", "cultivo", "año"]).reset_index(drop=True)

    # Validaciones de integridad
    assert len(df) == len(
        df_base
    ), "D5.3: len(df) != len(df_base) — revisar duplicados en joins"
    assert list(df.columns) == columnas_finales, "D5.3: esquema final incorrecto"
    assert df["codigo_dane"].astype(str).str.len().eq(5).all(), (
        "D5.3: codigo_dane con longitud != 5"
    )
    assert set(df["cultivo"].unique()) <= set(CULTIVOS_MVP), (
        "D5.3: cultivo fuera de CULTIVOS_MVP"
    )

    pct_nan_clima = df["prec_acum_mm"].isna().mean() * 100
    if pct_nan_clima > 50:
        logger.warning("D5.3: %.1f%% filas sin clima (prec_acum_mm NaN)", pct_nan_clima)

    if df["pct_aptitud_alta"].isna().any():
        codigos_nan = (
            df.loc[df["pct_aptitud_alta"].isna(), "codigo_dane"]
            .dropna()
            .unique()
            .tolist()
        )
        logger.warning("D5.3: Aptitud sin datos para %s", codigos_nan)

    output_path = Path(output_dir) / "tabla_maestra.parquet"
    df.to_parquet(output_path, index=False, engine="pyarrow")

    # Resumen de ejecución
    n_total = len(df)
    n_municipios = df["codigo_dane"].nunique()
    n_cultivos = df["cultivo"].nunique()
    year_min = int(df["año"].min())
    year_max = int(df["año"].max())

    n_train = int((df["año"] <= TRAIN_HASTA).sum())
    n_val = int((df["año"] == VAL_AÑO).sum())
    n_test = int((df["año"] >= TEST_DESDE).sum())

    print("=== Resumen Tabla Maestra ===")
    print(f"Total filas:    {n_total}")
    print(f"Municipios:      {n_municipios}/15")
    print(f"Cultivos:         {n_cultivos}  ({', '.join(CULTIVOS_MVP)})")
    print(f"Años:         {year_min}–{year_max}")
    print("")
    print("Cobertura de features (% filas con valor):")
    for col in [
        "rendimiento_t1",
        "rendimiento_prom3a",
        "prec_acum_mm",
        "pct_aptitud_alta",
        "fertilizantes",
    ]:
        pct = df[col].notna().mean() * 100
        print(f"  {col:<20}: {pct:>5.1f}%")
    print("")
    print("Split temporal:")
    print(f"  Train  (<={TRAIN_HASTA}): {n_train} filas")
    print(f"  Val    ({VAL_AÑO}):   {n_val} filas")
    print(f"  Test   (>={TEST_DESDE}):  {n_test} filas")
    print("")
    print(f"Archivo guardado: {output_path.as_posix()}")

    return df


def load_tabla_maestra(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """
    Carga tabla_maestra.parquet desde disco.

    Raises:
        FileNotFoundError: Si el archivo no existe (ejecutar build_tabla_maestra primero).
    """
    path = Path(data_dir) / "tabla_maestra.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"D5.3: Falta {path.name}. Ejecutar build_tabla_maestra() primero."
        )
    return pd.read_parquet(path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s — %(message)s")
    build_tabla_maestra()
