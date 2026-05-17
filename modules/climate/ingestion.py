"""
D2 — Pipeline Climático: Ingesta de datos IDEAM.

Funciones:
    download_catalogo_estaciones()  ← D2.1
    download_precipitacion()        ← D2.2
    download_temperatura()          ← D2.3
    download_humedad()              ← D2.3
"""
import logging
from typing import Iterator

import pandas as pd

from shared.config import DATASETS
from shared.dane_codes import MVP_CODIGOS, get_codigo, get_nombre
from shared.normalization import normalize_title_case
from shared.socrata_client import fetch_all

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constantes internas
# ─────────────────────────────────────────────────────────────────────────────

_DATASET_ID = DATASETS["ideam_catalogo"]  # hp9r-jxuu

# Nombres de municipios tal como aparecen en el catálogo IDEAM (Title Case).
# Se incluyen variaciones conocidas de San Vicente de Chucurí.
_MUNICIPIOS_SOQL = (
    "'Ibagué','Chaparral','Neiva','Garzón','Pitalito',"
    "'San Vicente De Chucurí','San Vicente de Chucurí','San Vicente De Chucuri',"
    "'Rionegro','Anorí','Amalfi',"
    "'Pensilvania','Palestina','Villavicencio',"
    "'El Tambo','Miranda','Valledupar'"
)

_WHERE_SOQL = f"municipio IN ({_MUNICIPIOS_SOQL})"

# Columnas de salida en orden canónico (D2.1 spec)
_COLUMNAS_SALIDA = [
    "codigo_estacion",
    "nombre_estacion",
    "categoria",
    "tecnologia",
    "estado",
    "municipio",
    "departamento",
    "latitud",
    "longitud",
    "altitud_m",
    "codigo_dane",
]


# ─────────────────────────────────────────────────────────────────────────────
# D2.1 — Catálogo de estaciones IDEAM
# ─────────────────────────────────────────────────────────────────────────────

def download_catalogo_estaciones(
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Descarga el catálogo de estaciones IDEAM para los municipios del MVP.

    Args:
        codigos_dane: Lista de códigos DANE a filtrar.
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con una fila por estación.
        Columnas: codigo_estacion, nombre_estacion, categoria, tecnologia,
                  estado, municipio, departamento, latitud, longitud,
                  altitud_m, codigo_dane.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar filtros.
        requests.RequestException: Si la API falla tras reintentos.
    """
    codigos_objetivo = set(codigos_dane) if codigos_dane is not None else set(MVP_CODIGOS)

    # ── 1. Descarga desde Socrata ─────────────────────────────────────────────
    logger.info("[D2.1] Descargando catálogo de estaciones IDEAM (dataset %s)…", _DATASET_ID)
    registros = fetch_all(dataset_id=_DATASET_ID, where=_WHERE_SOQL)

    # ── 2. Convertir a DataFrame ──────────────────────────────────────────────
    df = pd.DataFrame(registros)
    if df.empty:
        raise ValueError("Catálogo IDEAM: sin estaciones para el MVP")

    # ── 3. Renombrar columnas según mapeo de la spec ──────────────────────────
    df = df.rename(columns={
        "codigo":       "codigo_estacion",
        "nombre":       "nombre_estacion",
        "categoria":    "categoria",
        "tecnologia":   "tecnologia",
        "estado":       "estado",
        "departamento": "departamento",
        "latitud":      "latitud",
        "longitud":     "longitud",
        "altitud":      "altitud_m",
    })

    # Conservar municipio_raw para derivar codigo_dane; se descarta al final
    df = df.rename(columns={"municipio": "municipio_raw"})

    # ── 4. strip() en columnas de texto ──────────────────────────────────────
    for col in ["codigo_estacion", "nombre_estacion", "categoria", "tecnologia", "estado"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # ── 5-6. Normalizar municipio y departamento a Title Case ─────────────────
    df["municipio"] = df["municipio_raw"].astype(str).str.strip().apply(normalize_title_case)

    if "departamento" in df.columns:
        df["departamento"] = df["departamento"].astype(str).str.strip().apply(normalize_title_case)
    else:
        df["departamento"] = None

    # ── 7-8. Convertir coordenadas y altitud a numérico ───────────────────────
    for col in ["latitud", "longitud"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = float("nan")

    if "altitud_m" in df.columns:
        df["altitud_m"] = pd.to_numeric(df["altitud_m"], errors="coerce")
    else:
        df["altitud_m"] = float("nan")

    # ── 9. Derivar codigo_dane cruzando municipio_raw con DANE_CODES ──────────
    def _derivar_codigo(municipio_raw: str) -> str | None:
        codigo = get_codigo(municipio_raw)
        return codigo

    df["codigo_dane"] = df["municipio_raw"].apply(_derivar_codigo)

    # Loggear estaciones sin código DANE derivable
    sin_codigo = df[df["codigo_dane"].isna()]
    for _, row in sin_codigo.iterrows():
        logger.warning(
            "[D2.1] Estación %s ('%s') sin código DANE — municipio_raw='%s'",
            row.get("codigo_estacion", "?"),
            row.get("nombre_estacion", "?"),
            row.get("municipio_raw", "?"),
        )

    # ── 10. Filtrar: conservar solo filas con codigo_dane en el objetivo ──────
    df = df[df["codigo_dane"].isin(codigos_objetivo)]

    if df.empty:
        raise ValueError("Catálogo IDEAM: sin estaciones para el MVP tras filtrar por código DANE")

    # ── 11. Eliminar duplicados por codigo_estacion ───────────────────────────
    df = df.drop_duplicates(subset=["codigo_estacion"])

    # ── 12. Loggear resumen por municipio ─────────────────────────────────────
    for codigo in sorted(codigos_objetivo):
        subset = df[df["codigo_dane"] == codigo]
        total = len(subset)
        activas = int((subset["estado"].str.lower() == "activa").sum()) if total > 0 else 0
        municipio_nombre = subset["municipio"].iloc[0] if total > 0 else codigo
        logger.info(
            "[D2.1] %s (%s): %d estaciones totales, %d activas",
            municipio_nombre, codigo, total, activas,
        )

    # ── 13. Warning por municipios del MVP sin ninguna estación ───────────────
    codigos_con_datos = set(df["codigo_dane"].dropna().unique())
    for codigo in sorted(codigos_objetivo):
        if codigo not in codigos_con_datos:
            nombre = get_nombre(codigo) or codigo
            logger.warning("[D2.1] Sin estaciones para %s (%s)", nombre, codigo)

    # ── 14. Retornar con columnas en orden canónico ───────────────────────────
    # Asegurar que todas las columnas de salida existan
    for col in _COLUMNAS_SALIDA:
        if col not in df.columns:
            df[col] = None

    return df[_COLUMNAS_SALIDA].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers internos compartidos
# ─────────────────────────────────────────────────────────────────────────────

_LOTE_MAX = 50  # máximo de códigos de estación por cláusula IN en SoQL
                # Lotes pequeños evitan timeouts en datasets grandes (~165M registros)


def _lotes(items: list, size: int) -> Iterator[list]:
    """Divide una lista en sublistas de tamaño máximo `size`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _where_estaciones(codigos: list[str]) -> str:
    """Construye la cláusula WHERE con los códigos de estación."""
    quoted = ",".join(f"'{c}'" for c in codigos)
    return f"codigoestacion IN ({quoted}) AND valorobservado IS NOT NULL"


def _fetch_variable_lotes(
    dataset_id: str,
    codigos: list[str],
    select: str,
    group: str,
    order: str,
) -> pd.DataFrame:
    """
    Ejecuta una consulta agregada sobre cualquier dataset IDEAM dividiendo
    en lotes si hay más de _LOTE_MAX estaciones.
    Reutilizado por D2.2 (precipitación) y D2.3 (temperatura, humedad).
    """
    partes: list[pd.DataFrame] = []
    for lote in _lotes(codigos, _LOTE_MAX):
        where = _where_estaciones(lote)
        registros = fetch_all(
            dataset_id=dataset_id,
            select=select,
            where=where,
            group=group,
            order=order,
        )
        if registros:
            partes.append(pd.DataFrame(registros))
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()


def _fetch_prec_lotes(
    codigos: list[str],
    select: str,
    group: str,
    order: str,
) -> pd.DataFrame:
    """Wrapper de _fetch_variable_lotes para el dataset de precipitación (D2.2)."""
    return _fetch_variable_lotes(
        dataset_id=DATASETS["ideam_precipitacion"],
        codigos=codigos,
        select=select,
        group=group,
        order=order,
    )


def _extraer_año(serie: pd.Series) -> pd.Series:
    """
    Convierte la columna 'año' que viene de date_trunc_y() de Socrata
    (ej. '2015-01-01T00:00:00.000') a entero.
    """
    return pd.to_datetime(serie, errors="coerce").dt.year.astype("Int64")


# ─────────────────────────────────────────────────────────────────────────────
# D2.2 — Precipitación agregada por municipio y año
# ─────────────────────────────────────────────────────────────────────────────

def download_precipitacion(
    df_estaciones: pd.DataFrame,
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Descarga precipitación anual agregada para los municipios del MVP.

    Toda la agregación ocurre en el servidor Socrata vía $group — nunca
    se descargan los ~165M registros crudos.

    Args:
        df_estaciones: Output de download_catalogo_estaciones() (D2.1).
        codigos_dane: Municipios a procesar. Si None, usa MVP_CODIGOS.

    Returns:
        DataFrame con precipitación anual por municipio.
        Columnas: codigo_dane, municipio, año, prec_acum_mm,
                  prec_dias_secos, prec_dias_lluvia, n_estaciones_prec.

    Raises:
        ValueError: Si df_estaciones está vacío o el resultado final está vacío.
        requests.RequestException: Si la API falla tras reintentos.
    """
    codigos_objetivo = set(codigos_dane) if codigos_dane is not None else set(MVP_CODIGOS)

    # ── 1. Validar input y extraer códigos de estación ────────────────────────
    if df_estaciones.empty:
        raise ValueError("D2.2: df_estaciones vacío — ejecutar D2.1 primero")

    df_est_mvp = df_estaciones[df_estaciones["codigo_dane"].isin(codigos_objetivo)]
    codigos_estacion = df_est_mvp["codigo_estacion"].dropna().unique().tolist()

    if not codigos_estacion:
        raise ValueError("D2.2: no hay estaciones para los municipios objetivo")

    logger.info(
        "[D2.2] Descargando precipitación para %d estaciones en %d municipios…",
        len(codigos_estacion),
        len(codigos_objetivo),
    )

    # ── 2-3. Consulta A — acumulado anual y conteo de observaciones ───────────
    logger.info("[D2.2] Consulta A: acumulado anual y n_observaciones…")
    df_acum = _fetch_prec_lotes(
        codigos=codigos_estacion,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "sum(valorobservado) AS prec_acum_mm, "
            "count(*) AS n_observaciones"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
    )

    if df_acum.empty:
        raise ValueError("D2.2: sin registros de precipitación para el MVP")

    # ── 4. Consulta B — días secos y días de lluvia (umbral 1 mm) ─────────────
    logger.info("[D2.2] Consulta B: días secos y días de lluvia…")
    df_dias = _fetch_prec_lotes(
        codigos=codigos_estacion,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "count(CASE WHEN valorobservado < '1' THEN 1 END) AS prec_dias_secos, "
            "count(CASE WHEN valorobservado >= '1' THEN 1 END) AS prec_dias_lluvia"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
    )

    # ── 5. Consulta C — n_estaciones_prec (conteo de observaciones por estación)
    logger.info("[D2.2] Consulta C: n_estaciones_prec…")
    df_nest = _fetch_prec_lotes(
        codigos=codigos_estacion,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "count(codigoestacion) AS n_estaciones_prec"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
    )

    # ── 6-7. Convertir tipos en df_acum ──────────────────────────────────────
    df_acum["año"] = _extraer_año(df_acum["año"])
    df_acum["prec_acum_mm"] = pd.to_numeric(df_acum["prec_acum_mm"], errors="coerce")
    df_acum["n_observaciones"] = pd.to_numeric(df_acum["n_observaciones"], errors="coerce")
    df_acum["municipio"] = df_acum["municipio"].astype(str).str.strip().apply(normalize_title_case)

    # Valores negativos de precipitación → None (imposible físicamente)
    mask_neg = df_acum["prec_acum_mm"] < 0
    if mask_neg.any():
        for _, row in df_acum[mask_neg].iterrows():
            logger.warning(
                "[D2.2] Precipitación negativa (%.1f mm) en %s año %s — se convierte a NaN",
                row["prec_acum_mm"], row["municipio"], row["año"],
            )
        df_acum.loc[mask_neg, "prec_acum_mm"] = float("nan")

    # ── 6-7. Convertir tipos en df_dias ──────────────────────────────────────
    if not df_dias.empty:
        df_dias["año"] = _extraer_año(df_dias["año"])
        df_dias["prec_dias_secos"] = pd.to_numeric(df_dias["prec_dias_secos"], errors="coerce")
        df_dias["prec_dias_lluvia"] = pd.to_numeric(df_dias["prec_dias_lluvia"], errors="coerce")
        df_dias["municipio"] = df_dias["municipio"].astype(str).str.strip().apply(normalize_title_case)

    # ── 6-7. Convertir tipos en df_nest ──────────────────────────────────────
    if not df_nest.empty:
        df_nest["año"] = _extraer_año(df_nest["año"])
        df_nest["n_estaciones_prec"] = pd.to_numeric(df_nest["n_estaciones_prec"], errors="coerce")
        df_nest["municipio"] = df_nest["municipio"].astype(str).str.strip().apply(normalize_title_case)

    # ── 8. Cruzar municipio → codigo_dane ────────────────────────────────────
    for df_part in [df_acum, df_dias, df_nest]:
        if not df_part.empty:
            df_part["codigo_dane"] = df_part["municipio"].apply(get_codigo)

    # ── 9. Filtrar por MVP_CODIGOS ────────────────────────────────────────────
    df_acum = df_acum[df_acum["codigo_dane"].isin(codigos_objetivo)]
    if not df_dias.empty:
        df_dias = df_dias[df_dias["codigo_dane"].isin(codigos_objetivo)]
    if not df_nest.empty:
        df_nest = df_nest[df_nest["codigo_dane"].isin(codigos_objetivo)]

    # ── 10. Merge de las tres consultas ──────────────────────────────────────
    _key = ["codigo_dane", "municipio", "año"]

    df = df_acum[_key + ["prec_acum_mm", "n_observaciones"]].copy()

    if not df_dias.empty:
        df = df.merge(
            df_dias[_key + ["prec_dias_secos", "prec_dias_lluvia"]],
            on=_key,
            how="outer",
        )
    else:
        df["prec_dias_secos"] = float("nan")
        df["prec_dias_lluvia"] = float("nan")

    if not df_nest.empty:
        df = df.merge(
            df_nest[_key + ["n_estaciones_prec"]],
            on=_key,
            how="outer",
        )
    else:
        df["n_estaciones_prec"] = float("nan")

    # ── 11. Filtrar años fuera de rango ───────────────────────────────────────
    df = df[df["año"].between(2007, 2024)]

    if df.empty:
        raise ValueError("D2.2: sin registros de precipitación para el MVP tras filtrar")

    # ── 12. Eliminar columna auxiliar n_observaciones ─────────────────────────
    df = df.drop(columns=["n_observaciones"], errors="ignore")

    # ── 13. Warning por municipios sin datos ──────────────────────────────────
    codigos_con_datos = set(df["codigo_dane"].dropna().unique())
    for codigo in sorted(codigos_objetivo):
        if codigo not in codigos_con_datos:
            nombre = get_nombre(codigo) or codigo
            logger.warning("[D2.2] Sin datos de precipitación para %s (%s)", nombre, codigo)

    # ── 14. Loggear resumen ───────────────────────────────────────────────────
    for codigo in sorted(codigos_con_datos & codigos_objetivo):
        subset = df[df["codigo_dane"] == codigo]
        nombre = subset["municipio"].iloc[0] if not subset.empty else codigo
        años_min = int(subset["año"].min())
        años_max = int(subset["año"].max())
        n_filas = len(subset)
        pct_nan = float(subset["prec_acum_mm"].isna().mean() * 100)
        logger.info(
            "[D2.2] %s (%s): %d registros, años %d–%d, %.1f%% NaN en prec_acum_mm",
            nombre, codigo, n_filas, años_min, años_max, pct_nan,
        )

    # ── 15. Retornar con columnas en orden canónico ───────────────────────────
    _COLUMNAS_PREC = [
        "codigo_dane",
        "municipio",
        "año",
        "prec_acum_mm",
        "prec_dias_secos",
        "prec_dias_lluvia",
        "n_estaciones_prec",
    ]

    for col in _COLUMNAS_PREC:
        if col not in df.columns:
            df[col] = float("nan")

    return df[_COLUMNAS_PREC].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# D2.3 — Helper privado compartido por temperatura y humedad
# ─────────────────────────────────────────────────────────────────────────────

def _agregar_variable_climatica(
    dataset_id: str,
    df_estaciones: pd.DataFrame,
    select: str,
    codigos_objetivo: set[str],
    prefijo_log: str,
) -> pd.DataFrame:
    """
    Descarga y agrega una variable climática por municipio y año.

    Pasos comunes a download_temperatura y download_humedad:
      1. Validar df_estaciones y extraer códigos de estación
      2. Ejecutar consulta SoQL agregada en lotes
      3. Convertir año (date_trunc_y → int)
      4. Normalizar municipio a Title Case
      5. Cruzar municipio → codigo_dane
      6. Filtrar por codigos_objetivo y rango 2007–2024

    Args:
        dataset_id:       ID Socrata del dataset a consultar.
        df_estaciones:    Output de download_catalogo_estaciones() (D2.1).
        select:           Cláusula $select de la consulta SoQL.
        codigos_objetivo: Conjunto de códigos DANE a conservar.
        prefijo_log:      Prefijo para mensajes de log (ej. '[D2.3-temp]').

    Returns:
        DataFrame con columnas: municipio, año, codigo_dane + las métricas
        definidas en `select`. Listo para filtrado de rango físico y
        construcción del output final.

    Raises:
        ValueError: Si df_estaciones está vacío, no hay estaciones, o el
                    resultado tras filtros está vacío.
    """
    if df_estaciones.empty:
        raise ValueError(f"{prefijo_log}: df_estaciones vacío — ejecutar D2.1 primero")

    df_est_mvp = df_estaciones[df_estaciones["codigo_dane"].isin(codigos_objetivo)]
    codigos_estacion = df_est_mvp["codigo_estacion"].dropna().unique().tolist()

    if not codigos_estacion:
        raise ValueError(f"{prefijo_log}: no hay estaciones para los municipios objetivo")

    logger.info(
        "%s Descargando %s para %d estaciones en %d municipios…",
        prefijo_log, dataset_id, len(codigos_estacion), len(codigos_objetivo),
    )

    registros = _fetch_variable_lotes(
        dataset_id=dataset_id,
        codigos=codigos_estacion,
        select=select,
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
    )

    if registros.empty:
        raise ValueError(f"{prefijo_log}: sin registros para el MVP")

    # Convertir año
    registros["año"] = _extraer_año(registros["año"])

    # Normalizar municipio
    registros["municipio"] = (
        registros["municipio"].astype(str).str.strip().apply(normalize_title_case)
    )

    # Cruzar municipio → codigo_dane
    registros["codigo_dane"] = registros["municipio"].apply(get_codigo)

    # Filtrar por MVP_CODIGOS
    registros = registros[registros["codigo_dane"].isin(codigos_objetivo)]

    # Filtrar rango de años
    registros = registros[registros["año"].between(2007, 2024)]

    if registros.empty:
        raise ValueError(f"{prefijo_log}: sin registros tras filtrar por municipio y año")

    return registros.reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# D2.3 — Temperatura agregada por municipio y año
# ─────────────────────────────────────────────────────────────────────────────

def download_temperatura(
    df_estaciones: pd.DataFrame,
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Descarga temperatura anual agregada para los municipios del MVP.

    Toda la agregación ocurre en el servidor Socrata vía $group — nunca
    se descargan los ~50M registros crudos.

    Nota: `temp_max_media_c` es el máximo absoluto anual (max(valorobservado)),
    no la media de máximas diarias. SoQL no soporta subconsultas para calcular
    la media de máximas diarias directamente. Es un proxy válido para señal
    de estrés térmico en el modelo predictivo.

    Args:
        df_estaciones: Output de download_catalogo_estaciones() (D2.1).
        codigos_dane: Municipios a procesar. Si None, usa MVP_CODIGOS.

    Returns:
        DataFrame con temperatura anual por municipio.
        Columnas: codigo_dane, municipio, año, temp_media_c,
                  temp_max_media_c (proxy: máximo absoluto anual),
                  n_estaciones_temp.

    Raises:
        ValueError: Si df_estaciones está vacío o el resultado final está vacío.
        requests.RequestException: Si la API falla tras reintentos.
    """
    codigos_objetivo = set(codigos_dane) if codigos_dane is not None else set(MVP_CODIGOS)

    # ── Consulta principal: media anual + máximo absoluto ─────────────────────
    select_temp = (
        "municipio, "
        "date_trunc_y(fechaobservacion) AS año, "
        "avg(valorobservado) AS temp_media_c, "
        "max(valorobservado) AS temp_max_media_c, "
        "count(*) AS n_obs_temp"
    )

    df = _agregar_variable_climatica(
        dataset_id=DATASETS["ideam_temperatura"],
        df_estaciones=df_estaciones,
        select=select_temp,
        codigos_objetivo=codigos_objetivo,
        prefijo_log="[D2.3-temp]",
    )

    # ── Convertir métricas a numérico ─────────────────────────────────────────
    for col in ["temp_media_c", "temp_max_media_c", "n_obs_temp"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Filtrar valores físicamente imposibles (Colombia: 0°C–45°C) ──────────
    _key = ["municipio", "año"]
    mask_media = (df["temp_media_c"] < 0) | (df["temp_media_c"] > 45)
    if mask_media.any():
        for _, row in df[mask_media].iterrows():
            logger.warning(
                "[D2.3-temp] Temperatura media fuera de rango (%.1f°C) en %s año %s — NaN",
                row["temp_media_c"], row["municipio"], row["año"],
            )
        df.loc[mask_media, "temp_media_c"] = float("nan")

    mask_max = (df["temp_max_media_c"] < 0) | (df["temp_max_media_c"] > 50)
    if mask_max.any():
        for _, row in df[mask_max].iterrows():
            logger.warning(
                "[D2.3-temp] Temperatura máxima fuera de rango (%.1f°C) en %s año %s — NaN",
                row["temp_max_media_c"], row["municipio"], row["año"],
            )
        df.loc[mask_max, "temp_max_media_c"] = float("nan")

    # ── Consulta n_estaciones_temp ────────────────────────────────────────────
    logger.info("[D2.3-temp] Consulta n_estaciones_temp…")
    df_est_mvp = df_estaciones[df_estaciones["codigo_dane"].isin(codigos_objetivo)]
    codigos_estacion = df_est_mvp["codigo_estacion"].dropna().unique().tolist()

    df_nest = _fetch_variable_lotes(
        dataset_id=DATASETS["ideam_temperatura"],
        codigos=codigos_estacion,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "count(codigoestacion) AS n_estaciones_temp"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
    )

    if not df_nest.empty:
        df_nest["año"] = _extraer_año(df_nest["año"])
        df_nest["n_estaciones_temp"] = pd.to_numeric(df_nest["n_estaciones_temp"], errors="coerce")
        df_nest["municipio"] = (
            df_nest["municipio"].astype(str).str.strip().apply(normalize_title_case)
        )
        df_nest["codigo_dane"] = df_nest["municipio"].apply(get_codigo)
        df_nest = df_nest[df_nest["codigo_dane"].isin(codigos_objetivo)]
        df_nest = df_nest[df_nest["año"].between(2007, 2024)]

        _key_merge = ["codigo_dane", "municipio", "año"]
        df = df.merge(
            df_nest[_key_merge + ["n_estaciones_temp"]],
            on=_key_merge,
            how="left",
        )
    else:
        df["n_estaciones_temp"] = float("nan")

    # ── Eliminar columna auxiliar ─────────────────────────────────────────────
    df = df.drop(columns=["n_obs_temp"], errors="ignore")

    # ── Warning por municipios sin datos ──────────────────────────────────────
    codigos_con_datos = set(df["codigo_dane"].dropna().unique())
    for codigo in sorted(codigos_objetivo):
        if codigo not in codigos_con_datos:
            nombre = get_nombre(codigo) or codigo
            logger.warning("[D2.3-temp] Sin datos de temperatura para %s (%s)", nombre, codigo)

    # ── Loggear resumen ───────────────────────────────────────────────────────
    for codigo in sorted(codigos_con_datos & codigos_objetivo):
        subset = df[df["codigo_dane"] == codigo]
        nombre = subset["municipio"].iloc[0] if not subset.empty else codigo
        años_min = int(subset["año"].min())
        años_max = int(subset["año"].max())
        pct_nan = float(subset["temp_media_c"].isna().mean() * 100)
        logger.info(
            "[D2.3-temp] %s (%s): %d registros, años %d–%d, %.1f%% NaN en temp_media_c",
            nombre, codigo, len(subset), años_min, años_max, pct_nan,
        )

    # ── Retornar con columnas en orden canónico ───────────────────────────────
    _COLUMNAS_TEMP = [
        "codigo_dane",
        "municipio",
        "año",
        "temp_media_c",
        "temp_max_media_c",
        "n_estaciones_temp",
    ]
    for col in _COLUMNAS_TEMP:
        if col not in df.columns:
            df[col] = float("nan")

    return df[_COLUMNAS_TEMP].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# D2.3 — Humedad relativa agregada por municipio y año
# ─────────────────────────────────────────────────────────────────────────────

def download_humedad(
    df_estaciones: pd.DataFrame,
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Descarga humedad relativa anual agregada para los municipios del MVP.

    Toda la agregación ocurre en el servidor Socrata vía $group.

    Args:
        df_estaciones: Output de download_catalogo_estaciones() (D2.1).
        codigos_dane: Municipios a procesar. Si None, usa MVP_CODIGOS.

    Returns:
        DataFrame con humedad anual por municipio.
        Columnas: codigo_dane, municipio, año, hum_media_pct.

    Raises:
        ValueError: Si df_estaciones está vacío o el resultado final está vacío.
        requests.RequestException: Si la API falla tras reintentos.
    """
    codigos_objetivo = set(codigos_dane) if codigos_dane is not None else set(MVP_CODIGOS)

    # ── Consulta principal: media anual de humedad ────────────────────────────
    select_hum = (
        "municipio, "
        "date_trunc_y(fechaobservacion) AS año, "
        "avg(valorobservado) AS hum_media_pct, "
        "count(*) AS n_obs_hum"
    )

    df = _agregar_variable_climatica(
        dataset_id=DATASETS["ideam_humedad"],
        df_estaciones=df_estaciones,
        select=select_hum,
        codigos_objetivo=codigos_objetivo,
        prefijo_log="[D2.3-hum]",
    )

    # ── Convertir métricas a numérico ─────────────────────────────────────────
    df["hum_media_pct"] = pd.to_numeric(df["hum_media_pct"], errors="coerce")

    # ── Filtrar valores físicamente imposibles (0%–100%) ─────────────────────
    mask_hum = (df["hum_media_pct"] < 0) | (df["hum_media_pct"] > 100)
    if mask_hum.any():
        for _, row in df[mask_hum].iterrows():
            logger.warning(
                "[D2.3-hum] Humedad fuera de rango (%.1f%%) en %s año %s — NaN",
                row["hum_media_pct"], row["municipio"], row["año"],
            )
        df.loc[mask_hum, "hum_media_pct"] = float("nan")

    # ── Eliminar columna auxiliar ─────────────────────────────────────────────
    df = df.drop(columns=["n_obs_hum"], errors="ignore")

    # ── Warning por municipios sin datos ──────────────────────────────────────
    codigos_con_datos = set(df["codigo_dane"].dropna().unique())
    for codigo in sorted(codigos_objetivo):
        if codigo not in codigos_con_datos:
            nombre = get_nombre(codigo) or codigo
            logger.warning("[D2.3-hum] Sin datos de humedad para %s (%s)", nombre, codigo)

    # ── Loggear resumen ───────────────────────────────────────────────────────
    for codigo in sorted(codigos_con_datos & codigos_objetivo):
        subset = df[df["codigo_dane"] == codigo]
        nombre = subset["municipio"].iloc[0] if not subset.empty else codigo
        años_min = int(subset["año"].min())
        años_max = int(subset["año"].max())
        pct_nan = float(subset["hum_media_pct"].isna().mean() * 100)
        logger.info(
            "[D2.3-hum] %s (%s): %d registros, años %d–%d, %.1f%% NaN en hum_media_pct",
            nombre, codigo, len(subset), años_min, años_max, pct_nan,
        )

    # ── Retornar con columnas en orden canónico ───────────────────────────────
    _COLUMNAS_HUM = [
        "codigo_dane",
        "municipio",
        "año",
        "hum_media_pct",
    ]
    for col in _COLUMNAS_HUM:
        if col not in df.columns:
            df[col] = float("nan")

    return df[_COLUMNAS_HUM].reset_index(drop=True)


# ─────────────────────────────────────────────────────────────────────────────
# D2.4 — Orquestación del pipeline completo + guardado Parquet
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(
    output_dir: "Path | None" = None,
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Ejecuta el pipeline completo de clima: descarga, agrega, calcula
    anomalías y guarda clima_agregado.parquet.

    Internamente llama a download_catalogo_estaciones(), download_precipitacion(),
    download_temperatura(), download_humedad() y calcular_anomalias().

    Args:
        output_dir: Directorio donde guardar el Parquet. Default: DATA_DIR.
        codigos_dane: Municipios a procesar. Si None, usa MVP_CODIGOS.

    Returns:
        clima_agregado como DataFrame ordenado.

    Raises:
        AssertionError: Si hay duplicados o municipios faltantes en el output.
        requests.RequestException: Si alguna descarga falla tras reintentos.
    """
    from pathlib import Path as _Path
    from shared.config import DATA_DIR, TRAIN_HASTA
    from shared.dane_codes import DANE_TO_NAME, MVP_CODIGOS as _MVP_CODIGOS
    from modules.climate.aggregation import calcular_anomalias

    if output_dir is None:
        output_dir = DATA_DIR
    output_dir = _Path(output_dir)

    codigos_objetivo = list(codigos_dane) if codigos_dane is not None else list(_MVP_CODIGOS)

    logger.info("[D2.4] Iniciando pipeline climático para %d municipios…", len(codigos_objetivo))

    # ── Paso 0: Descargar catálogo de estaciones ──────────────────────────────
    logger.info("[D2.4] Paso 0: descargando catálogo de estaciones…")
    df_estaciones = download_catalogo_estaciones(codigos_dane=codigos_objetivo)

    # ── Paso 0b: Descargar las tres variables climáticas ─────────────────────
    logger.info("[D2.4] Paso 0b: descargando precipitación…")
    df_prec = download_precipitacion(df_estaciones=df_estaciones, codigos_dane=codigos_objetivo)

    logger.info("[D2.4] Paso 0c: descargando temperatura…")
    df_temp = download_temperatura(df_estaciones=df_estaciones, codigos_dane=codigos_objetivo)

    logger.info("[D2.4] Paso 0d: descargando humedad…")
    df_hum = download_humedad(df_estaciones=df_estaciones, codigos_dane=codigos_objetivo)

    # ── Paso 1: Construir universo de combinaciones (municipio × año) ─────────
    logger.info("[D2.4] Paso 1: construyendo universo de combinaciones…")
    años = list(range(2007, 2025))  # 2007–2024 inclusive
    import itertools
    combinaciones = list(itertools.product(codigos_objetivo, años))
    df_base = pd.DataFrame(combinaciones, columns=["codigo_dane", "año"])
    df_base["municipio"] = df_base["codigo_dane"].map(DANE_TO_NAME)
    logger.info("[D2.4] Universo: %d filas (%d municipios × %d años)", len(df_base), len(codigos_objetivo), len(años))

    # ── Paso 2: Merge de las tres fuentes ─────────────────────────────────────
    logger.info("[D2.4] Paso 2: merge de las tres fuentes climáticas…")

    # Renombrar columna 'municipio' en cada fuente para evitar conflictos
    df_prec_m = df_prec.rename(columns={"municipio": "municipio_prec"})
    df_temp_m = df_temp.rename(columns={"municipio": "municipio_temp"})
    df_hum_m = df_hum.rename(columns={"municipio": "municipio_hum"})

    # Columnas a traer de cada fuente (sin 'municipio' renombrado)
    cols_prec = ["codigo_dane", "año", "prec_acum_mm", "prec_dias_secos", "prec_dias_lluvia", "n_estaciones_prec"]
    cols_temp = ["codigo_dane", "año", "temp_media_c", "temp_max_media_c", "n_estaciones_temp"]
    cols_hum  = ["codigo_dane", "año", "hum_media_pct"]

    # Asegurar que las columnas existen antes del merge
    for col in cols_prec:
        if col not in df_prec_m.columns:
            df_prec_m[col] = float("nan")
    for col in cols_temp:
        if col not in df_temp_m.columns:
            df_temp_m[col] = float("nan")
    for col in cols_hum:
        if col not in df_hum_m.columns:
            df_hum_m[col] = float("nan")

    df = df_base.merge(df_prec_m[cols_prec], on=["codigo_dane", "año"], how="left")
    df = df.merge(df_temp_m[cols_temp], on=["codigo_dane", "año"], how="left")
    df = df.merge(df_hum_m[cols_hum],  on=["codigo_dane", "año"], how="left")

    # municipio ya viene del df_base (DANE_TO_NAME — fuente de verdad)

    # ── Paso 3: Rellenar n_estaciones con 0 donde NaN ─────────────────────────
    logger.info("[D2.4] Paso 3: rellenando n_estaciones con 0 donde NaN…")
    df["n_estaciones_prec"] = df["n_estaciones_prec"].fillna(0).astype(int)
    df["n_estaciones_temp"] = df["n_estaciones_temp"].fillna(0).astype(int)

    # ── Loggear municipios sin datos en ninguna variable ──────────────────────
    vars_climaticas = ["prec_acum_mm", "temp_media_c", "hum_media_pct"]
    for codigo in sorted(codigos_objetivo):
        subset = df[df["codigo_dane"] == codigo]
        nombre = DANE_TO_NAME.get(codigo, codigo)
        sin_datos = subset[vars_climaticas].isna().all(axis=1).all()
        if sin_datos:
            logger.warning("[D2.4] %s (%s): sin datos climáticos en ninguna fuente", nombre, codigo)

    # ── Paso 4: Calcular anomalías ────────────────────────────────────────────
    logger.info("[D2.4] Paso 4: calculando anomalías climáticas (corte año <= %d)…", TRAIN_HASTA)
    df = calcular_anomalias(df, año_corte=TRAIN_HASTA)

    # ── Paso 5: Validaciones de integridad ────────────────────────────────────
    logger.info("[D2.4] Paso 5: validaciones de integridad…")

    n_filas = len(df)
    esperado = len(codigos_objetivo) * len(años)
    if n_filas != esperado:
        logger.warning(
            "[D2.4] Número de filas inesperado: %d (esperado %d = %d municipios × %d años)",
            n_filas, esperado, len(codigos_objetivo), len(años),
        )

    duplicados = df.duplicated(subset=["codigo_dane", "año"])
    if duplicados.any():
        detalle = df[duplicados][["codigo_dane", "año"]].to_dict("records")
        raise AssertionError(f"[D2.4] Duplicados en (codigo_dane, año): {detalle}")

    codigos_presentes = set(df["codigo_dane"].unique())
    faltantes = set(codigos_objetivo) - codigos_presentes
    if faltantes:
        raise AssertionError(f"[D2.4] Municipios del MVP ausentes en el output: {sorted(faltantes)}")

    # ── Paso 6: Ordenar y seleccionar columnas en orden exacto ───────────────
    logger.info("[D2.4] Paso 6: ordenando y seleccionando columnas…")

    _COLUMNAS_CLIMA = [
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

    for col in _COLUMNAS_CLIMA:
        if col not in df.columns:
            df[col] = float("nan")

    df = df.sort_values(["codigo_dane", "año"]).reset_index(drop=True)
    df = df[_COLUMNAS_CLIMA]

    # ── Paso 6b: Guardar Parquet ──────────────────────────────────────────────
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "clima_agregado.parquet"
    df.to_parquet(output_path, index=False, engine="pyarrow")
    logger.info("[D2.4] Guardado: %s", output_path)

    # ── Paso 7: Resumen de ejecución ──────────────────────────────────────────
    logger.info("[D2.4] ── Resumen de ejecución ──────────────────────────────")
    logger.info("[D2.4] Total de filas: %d", len(df))

    vars_cobertura = [
        "prec_acum_mm", "prec_dias_secos", "prec_dias_lluvia",
        "temp_media_c", "temp_max_media_c", "hum_media_pct",
        "anomalia_prec", "anomalia_temp",
    ]
    for var in vars_cobertura:
        if var in df.columns:
            pct = float(df[var].notna().mean() * 100)
            logger.info("[D2.4]   %-22s cobertura: %5.1f%%", var, pct)

    municipios_completos = []
    municipios_parciales = []
    for codigo in sorted(codigos_objetivo):
        nombre = DANE_TO_NAME.get(codigo, codigo)
        subset = df[df["codigo_dane"] == codigo]
        completo = subset[vars_cobertura].notna().all(axis=None)
        if completo:
            municipios_completos.append(nombre)
        else:
            municipios_parciales.append(nombre)

    logger.info(
        "[D2.4] Municipios con cobertura completa (%d): %s",
        len(municipios_completos), ", ".join(municipios_completos) or "ninguno",
    )
    logger.info(
        "[D2.4] Municipios con cobertura parcial (%d): %s",
        len(municipios_parciales), ", ".join(municipios_parciales) or "ninguno",
    )

    logger.info("[D2.4] Media histórica por municipio (precipitación y temperatura):")
    for codigo in sorted(codigos_objetivo):
        nombre = DANE_TO_NAME.get(codigo, codigo)
        subset_hist = df[(df["codigo_dane"] == codigo) & (df["año"] <= TRAIN_HASTA)]
        media_prec = subset_hist["prec_acum_mm"].mean()
        media_temp = subset_hist["temp_media_c"].mean()
        logger.info(
            "[D2.4]   %-30s prec_hist=%.1f mm  temp_hist=%.2f °C",
            nombre,
            media_prec if not pd.isna(media_prec) else -1,
            media_temp if not pd.isna(media_temp) else -1,
        )

    logger.info("[D2.4] Pipeline climático completado exitosamente.")
    return df


def load_clima_agregado(data_dir: "Path | None" = None) -> pd.DataFrame:
    """
    Carga clima_agregado.parquet desde disco.

    Args:
        data_dir: Directorio donde buscar el archivo. Default: DATA_DIR.

    Returns:
        DataFrame con el clima agregado.

    Raises:
        FileNotFoundError: Si el archivo no existe (ejecutar run_pipeline primero).
    """
    from pathlib import Path as _Path
    from shared.config import DATA_DIR

    if data_dir is None:
        data_dir = DATA_DIR
    data_dir = _Path(data_dir)

    path = data_dir / "clima_agregado.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró {path}. Ejecutar run_pipeline() primero."
        )
    return pd.read_parquet(path, engine="pyarrow")


# ─────────────────────────────────────────────────────────────────────────────
# Punto de entrada como script: python -m modules.climate.ingestion
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    import logging as _logging

    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger.info("Ejecutando pipeline climático completo…")
    try:
        df_resultado = run_pipeline()
        logger.info("Pipeline completado. Shape: %s", df_resultado.shape)
        print(df_resultado.head(10).to_string())
        sys.exit(0)
    except Exception as exc:
        logger.error("Pipeline fallido: %s", exc, exc_info=True)
        sys.exit(1)
