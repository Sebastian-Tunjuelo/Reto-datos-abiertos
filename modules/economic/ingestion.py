"""
D4.1 — Descarga y limpieza del índice de agroinsumos.
"""
import logging

from pathlib import Path

import pandas as pd

try:
    from scipy.stats import percentileofscore
except Exception:  # pragma: no cover - fallback si scipy no esta disponible
    percentileofscore = None

from shared.config import DATA_DIR, DATASETS
from shared.socrata_client import fetch, fetch_all

logger = logging.getLogger(__name__)

_COLUMNAS_ESPERADAS = [
    "fecha",
    "indice_total",
    "total_fertilizantes",
    "total_plaguicidas",
    "urea_46",
    "dap_18_46",
    "kcl_0_0_60",
]

_COLUMNAS_SALIDA = [
    "fecha",
    "año",
    "mes",
    "indice_total",
    "fertilizantes",
    "plaguicidas",
    "urea",
    "dap",
    "kcl",
]

_COLUMNAS_MENSUAL_ESPERADAS = _COLUMNAS_SALIDA

_COLUMNAS_ANUAL = [
    "año",
    "indice_total",
    "fertilizantes",
    "plaguicidas",
    "urea",
    "dap",
    "kcl",
    "n_meses",
    "pct_fertilizantes",
    "pct_indice_total",
    "señal_riesgo",
]


def download_agroinsumos() -> pd.DataFrame:
    """
    Descarga y limpia el índice de precios de agroinsumos.

    Descarga el dataset completo (sin filtros geográficos) y retorna
    una serie mensual limpia con el esquema unificado del proyecto.

    Returns:
        DataFrame con esquema mensual:
        fecha, año, mes, indice_total, fertilizantes, plaguicidas,
        urea, dap, kcl.
        Ordenado por (año, mes) ascendente.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar limpieza.
        KeyError: Si las columnas esperadas no están en el dataset.
        requests.RequestException: Si la API falla tras reintentos.
    """
    dataset_id = DATASETS["agroinsumos"]
    logger.info("[D4.1] Descargando agroinsumos (dataset %s)…", dataset_id)

    muestra = fetch(dataset_id=dataset_id, limit=3)
    if muestra:
        logger.info(
            "[D4.1] Columnas en muestra: %s",
            sorted(muestra[0].keys()),
        )
    else:
        logger.warning("[D4.1] Muestra vacía al verificar columnas")

    registros = fetch_all(dataset_id=dataset_id)
    logger.info("[D4.1] Registros descargados de la API: %d", len(registros))

    df = pd.DataFrame(registros)
    if df.empty:
        raise ValueError("Agroinsumos: sin registros tras limpieza")

    columnas_faltantes = [c for c in _COLUMNAS_ESPERADAS if c not in df.columns]
    if columnas_faltantes:
        logger.error("[D4.1] Columnas reales en API: %s", list(df.columns))
        raise KeyError(
            f"Agroinsumos: columnas faltantes en API: {columnas_faltantes}"
        )

    df = df.rename(columns={
        "total_fertilizantes": "fertilizantes",
        "total_plaguicidas": "plaguicidas",
        "urea_46": "urea",
        "dap_18_46": "dap",
        "kcl_0_0_60": "kcl",
    })

    fecha_dt = pd.to_datetime(df["fecha"], errors="coerce")
    n_no_parse = int(fecha_dt.isna().sum())
    if n_no_parse > 0:
        valores = df.loc[fecha_dt.isna(), "fecha"].dropna().unique().tolist()
        logger.warning(
            "[D4.1] Fechas no parseables: %d | valores=%s",
            n_no_parse,
            valores,
        )

    df = df.assign(fecha_dt=fecha_dt)
    df = df[df["fecha_dt"].notna()]

    df = df.assign(
        año=df["fecha_dt"].dt.year.astype("Int64"),
        mes=df["fecha_dt"].dt.month.astype("Int64"),
        fecha=df["fecha_dt"].dt.strftime("%Y-%m"),
    )

    for col in ["indice_total", "fertilizantes", "plaguicidas", "urea", "dap", "kcl"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    n_antes = len(df)
    df = df[df["año"].between(2007, 2024)]
    n_fuera = n_antes - len(df)
    if n_fuera > 0:
        logger.info("[D4.1] Filas fuera de rango 2007–2024: %d", n_fuera)

    n_antes = len(df)
    df = df.drop_duplicates(subset=["año", "mes"])
    n_dup = n_antes - len(df)
    if n_dup > 0:
        logger.info("[D4.1] Duplicados eliminados por (año, mes): %d", n_dup)

    df = df.sort_values(["año", "mes"]).reset_index(drop=True)

    if df.empty:
        raise ValueError("Agroinsumos: sin registros tras limpieza")

    return df[_COLUMNAS_SALIDA]


def _percentil_historico(valores: pd.Series, valor: float | None) -> float | None:
    if valor is None or pd.isna(valor):
        return None
    serie = valores.dropna().astype(float)
    if len(serie) < 3:
        return None
    if percentileofscore is None:
        ordenados = serie.sort_values().to_numpy()
        pos = int((ordenados <= valor).sum())
        return pos / len(ordenados)
    return percentileofscore(serie, valor, kind="rank") / 100


def _calcular_señal_riesgo(pct_fertilizantes: float | None) -> str:
    if pd.isna(pct_fertilizantes):
        return "Medio"
    if pct_fertilizantes >= 0.75:
        return "Alto"
    if pct_fertilizantes >= 0.40:
        return "Medio"
    return "Bajo"


def build_agroinsumos_anual(df_mensual: pd.DataFrame) -> pd.DataFrame:
    """
    Agrega la serie mensual a nivel anual y calcula percentiles históricos.

    Args:
        df_mensual: DataFrame con esquema mensual (output de download_agroinsumos()).

    Returns:
        DataFrame con esquema anual:
        año, indice_total, fertilizantes, plaguicidas, urea, dap, kcl,
        n_meses, pct_fertilizantes, pct_indice_total, señal_riesgo.
        Ordenado por año ascendente.

    Raises:
        ValueError: Si df_mensual está vacío o no tiene las columnas esperadas.
    """
    if df_mensual is None or df_mensual.empty:
        raise ValueError("Agroinsumos: df_mensual vacío")

    columnas_faltantes = [c for c in _COLUMNAS_MENSUAL_ESPERADAS if c not in df_mensual.columns]
    if columnas_faltantes:
        raise ValueError(
            f"Agroinsumos: df_mensual sin columnas esperadas: {columnas_faltantes}"
        )

    anual = (
        df_mensual
        .groupby("año")
        .agg(
            indice_total=("indice_total", "mean"),
            fertilizantes=("fertilizantes", "mean"),
            plaguicidas=("plaguicidas", "mean"),
            urea=("urea", "mean"),
            dap=("dap", "mean"),
            kcl=("kcl", "mean"),
            n_meses=("mes", "count"),
        )
        .reset_index()
    )

    anual = anual.sort_values("año").reset_index(drop=True)

    anual["n_meses"] = anual["n_meses"].astype("int64")
    anual["año"] = anual["año"].astype("int64")

    for _, row in anual[anual["n_meses"] < 6].iterrows():
        logger.warning(
            "[D4.2] Año %d con solo %d meses de datos",
            int(row["año"]),
            int(row["n_meses"]),
        )

    pct_fert: list[float | None] = []
    pct_total: list[float | None] = []

    for idx, row in anual.iterrows():
        año = row["año"]
        historico = anual[anual["año"] < año]

        pct_fert.append(
            _percentil_historico(historico["fertilizantes"], row["fertilizantes"])
        )
        pct_total.append(
            _percentil_historico(historico["indice_total"], row["indice_total"])
        )

    anual = anual.assign(
        pct_fertilizantes=pct_fert,
        pct_indice_total=pct_total,
    )

    anual["señal_riesgo"] = anual["pct_fertilizantes"].apply(_calcular_señal_riesgo)

    return anual[_COLUMNAS_ANUAL]


def run_pipeline(data_dir: Path = DATA_DIR) -> None:
    """
    Ejecuta el pipeline completo D4:
    1. Descarga y limpia la serie mensual (D4.1)
    2. Agrega a nivel anual y calcula percentiles (D4.2)
    3. Guarda los 2 Parquets en data/

    Args:
        data_dir: Directorio donde guardar los Parquets.
                  Por defecto usa DATA_DIR de shared/config.py.
    """
    output_dir = Path(data_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    df_mensual = download_agroinsumos()
    path_mensual = output_dir / "agroinsumos_mensual.parquet"
    df_mensual.to_parquet(path_mensual, index=False, engine="pyarrow")
    logger.info("[D4.2] Guardado: %s", path_mensual)

    df_anual = build_agroinsumos_anual(df_mensual)
    if df_anual.empty:
        raise ValueError("Agroinsumos: sin registros tras agregación anual")

    path_anual = output_dir / "agroinsumos.parquet"
    df_anual.to_parquet(path_anual, index=False, engine="pyarrow")
    logger.info("[D4.2] Guardado: %s", path_anual)

    años_min = int(df_anual["año"].min())
    años_max = int(df_anual["año"].max())
    n_meses_prom = float(df_anual["n_meses"].mean())
    distrib = df_anual["señal_riesgo"].value_counts().to_dict()

    logger.info(
        "[D4.2] Resumen: años %d–%d | n_meses promedio %.2f | señal_riesgo %s",
        años_min,
        años_max,
        n_meses_prom,
        distrib,
    )


if __name__ == "__main__":
    import logging as _logging
    import sys

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("Ejecutando pipeline economico D4…")
    try:
        run_pipeline()
        logger.info("Pipeline economico completado.")
        sys.exit(0)
    except Exception as exc:
        logger.error("Pipeline economico fallido: %s", exc, exc_info=True)
        sys.exit(1)
