"""
D2 — Pipeline Climático: Ingesta de datos IDEAM.

Funciones:
    download_catalogo_estaciones()  ← D2.1
    download_precipitacion()        ← D2.2
    download_temperatura()          ← D2.3
    download_humedad()              ← D2.3

# ─── Nota de arquitectura: estrategia de filtrado por municipio ───────────────
#
# Los datasets de observaciones IDEAM (precipitación s54a-sgyg, temperatura
# sbwg-7ju4, humedad uext-mhny) tienen entre 50M y 165M de registros.
# El servidor Socrata de datos.gov.co NO tiene índice sobre `codigoestacion`,
# por lo que cualquier consulta con WHERE codigoestacion IN (...) provoca un
# full-scan y hace timeout incluso con 1 sola estación y 1 año de datos.
#
# Estrategia adoptada (D2.2 / D2.3):
#   - Filtrar directamente por `municipio IN (...)` en MAYÚSCULAS, que sí
#     está indexado en el servidor.
#   - Usar ventanas temporales mensuales (IDEAM_MONTH_CHUNK meses) para
#     acotar el volumen por llamada y evitar timeouts.
#   - Agregar en el servidor con $group=municipio,date_trunc_y(fechaobservacion)
#     para nunca descargar registros crudos.
#   - El catálogo de estaciones (D2.1) se mantiene como output independiente
#     para auditoría, pero ya NO se usa como intermediario para filtrar
#     las consultas de observaciones.
#
# Consecuencia: `df_estaciones` sigue siendo parámetro de download_precipitacion,
# download_temperatura y download_humedad por compatibilidad de interfaz, pero
# internamente no se usa para construir el WHERE de las observaciones.
# ─────────────────────────────────────────────────────────────────────────────
"""
import logging
import os
from typing import Iterator

import pandas as pd

from shared.config import DATASETS
from shared.dane_codes import DANE_CODES, MVP_CODIGOS, get_codigo, get_nombre
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

# Nombres de municipios en MAYÚSCULAS tal como aparecen en los datasets de
# observaciones IDEAM (precipitación, temperatura, humedad).
# Fuente: DANE_CODES keys de shared/dane_codes.py.
# Se incluyen variaciones conocidas de San Vicente de Chucurí.
_MUNICIPIOS_OBS_UPPER = list(DANE_CODES.keys()) + [
    "SAN VICENTE CHUCURI",
    "SAN VICENTE DE CHUCURÍ",
]

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

# Ventanas temporales para consultas IDEAM.
# Se usan ventanas MENSUALES (no anuales) para acotar el volumen por llamada
# y evitar timeouts en los datasets grandes (~165M registros de precipitación).
# IDEAM_MONTH_CHUNK controla cuántos meses abarca cada ventana (default: 6).
# Aumentar a 6+ meses reduce el n° total de consultas y alivia timeouts del servidor.
# Se reduce el rango anual por defecto para bajar aún más la carga.
_YEAR_START = int(os.getenv("IDEAM_YEAR_START", "2023"))
_YEAR_END = int(os.getenv("IDEAM_YEAR_END", "2024"))
_MONTH_CHUNK = int(os.getenv("IDEAM_MONTH_CHUNK", "6"))


def _lotes(items: list, size: int) -> Iterator[list]:
    """Divide una lista en sublistas de tamaño máximo `size`."""
    for i in range(0, len(items), size):
        yield items[i : i + size]


def _municipios_soql_upper(codigos_objetivo: set[str]) -> str:
    """
    Construye la cláusula WHERE para filtrar por municipio en MAYÚSCULAS,
    tal como aparecen en los datasets de observaciones IDEAM.

    Los datasets de observaciones (precipitación, temperatura, humedad) tienen
    el campo `municipio` en MAYÚSCULAS y SÍ está indexado en el servidor
    Socrata, a diferencia de `codigoestacion` que provoca full-scans y timeouts.

    Args:
        codigos_objetivo: Conjunto de códigos DANE a incluir.

    Returns:
        Cláusula WHERE lista para usar en $where de SoQL.
    """
    from shared.dane_codes import DANE_CODES as _DC
    # Invertir DANE_CODES para obtener nombre_upper → codigo
    upper_to_codigo = {v: k for k, v in _DC.items()}
    # Nombres en MAYÚSCULAS para los códigos objetivo
    nombres = [k for k, v in _DC.items() if v in codigos_objetivo]
    # Añadir variaciones conocidas de San Vicente de Chucurí
    if "68689" in codigos_objetivo:
        nombres += ["SAN VICENTE CHUCURI", "SAN VICENTE DE CHUCURÍ"]
    quoted = ",".join(f"'{n}'" for n in sorted(set(nombres)))
    return f"municipio IN ({quoted}) AND valorobservado IS NOT NULL"


def _municipios_upper_por_codigos(codigos_objetivo: set[str]) -> list[str]:
    """Retorna nombres de municipios en MAYUSCULAS para los codigos DANE objetivo."""
    nombres = [k for k, v in DANE_CODES.items() if v in codigos_objetivo]
    if "68689" in codigos_objetivo:
        nombres += ["SAN VICENTE CHUCURI", "SAN VICENTE DE CHUCURI", "SAN VICENTE DE CHUCURÍ"]
    return sorted(set(nombres))


def _month_windows() -> list[tuple[str, str]]:
    """
    Genera ventanas temporales para el rango IDEAM_YEAR_START–IDEAM_YEAR_END.

    Cada ventana es un par (fecha_inicio_iso, fecha_fin_iso) que se usa en el
    filtro SoQL: fechaobservacion >= fecha_inicio AND fechaobservacion < fecha_fin.

    Con _MONTH_CHUNK=3 (default) genera 72 ventanas (18 años × 12/3 = 72).
    Esto reduce el n° total de consultas comparado con ventanas mensuales (216),
    manteniendo cada consulta acotada a un volumen manejable por el servidor Socrata,
    evitando timeouts.

    Returns:
        Lista de tuplas (inicio_iso, fin_iso) en formato 'YYYY-MM-DDT00:00:00.000'.
    """
    import calendar

    if _YEAR_END < _YEAR_START:
        return []

    windows: list[tuple[str, str]] = []
    year, month = _YEAR_START, 1

    while (year, month) <= (_YEAR_END, 12):
        # Calcular fin de ventana sumando _MONTH_CHUNK meses
        end_month = month + _MONTH_CHUNK - 1
        end_year = year + (end_month - 1) // 12
        end_month = ((end_month - 1) % 12) + 1

        # Clamp al límite final
        if end_year > _YEAR_END or (end_year == _YEAR_END and end_month > 12):
            end_year, end_month = _YEAR_END, 12

        # Primer día del mes siguiente al fin de ventana
        last_day = calendar.monthrange(end_year, end_month)[1]
        next_month = end_month + 1
        next_year = end_year + (1 if next_month > 12 else 0)
        next_month = 1 if next_month > 12 else next_month

        inicio = f"{year:04d}-{month:02d}-01T00:00:00.000"
        fin = f"{next_year:04d}-{next_month:02d}-01T00:00:00.000"
        windows.append((inicio, fin))

        # Avanzar al siguiente chunk
        month = end_month + 1
        if month > 12:
            month = 1
            year += 1
        year += (end_year - year) if end_year > year else 0

        if year > _YEAR_END:
            break

    return windows


def _fetch_obs_por_municipio(
    dataset_id: str,
    codigos_objetivo: set[str],
    select: str,
    group: str,
    order: str,
    prefijo_log: str,
) -> pd.DataFrame:
    """
    Descarga observaciones IDEAM agregadas filtrando por `municipio` (MAYÚSCULAS).

    Estrategia:
      - Filtra por `municipio IN (...)` en lugar de `codigoestacion IN (...)`.
        El campo `municipio` está indexado en el servidor Socrata; `codigoestacion`
        no lo está y provoca full-scans con timeout en datasets de 50M–165M registros.
      - Divide el rango temporal en ventanas mensuales (IDEAM_MONTH_CHUNK) para
        acotar el volumen por llamada y evitar timeouts.
      - Cada ventana genera una llamada fetch_all() con $group, nunca datos crudos.

    Args:
        dataset_id:       ID Socrata del dataset de observaciones.
        codigos_objetivo: Códigos DANE de los municipios a consultar.
        select:           Cláusula $select con las métricas de agregación.
                          Debe incluir `municipio` y `date_trunc_y(fechaobservacion) AS año`.
        group:            Cláusula $group correspondiente al select.
        order:            Cláusula $order.
        prefijo_log:      Prefijo para mensajes de log.

    Returns:
        DataFrame con los resultados concatenados de todas las ventanas.
        Columnas según el `select` proporcionado.
    """
    municipios_upper = _municipios_upper_por_codigos(codigos_objetivo)
    ventanas = _month_windows()

    if not ventanas or not municipios_upper:
        logger.warning("%s Sin ventanas temporales — verificar IDEAM_YEAR_START/END", prefijo_log)
        return pd.DataFrame()

    logger.info(
        "%s Consultando %s en %d ventanas x %d municipios (%d–%d)…",
        prefijo_log, dataset_id, len(ventanas), len(municipios_upper), _YEAR_START, _YEAR_END,
    )

    partes: list[pd.DataFrame] = []
    fallos = 0
    for inicio, fin in ventanas:
        for municipio in municipios_upper:
            where = (
                f"municipio = '{municipio}' AND valorobservado IS NOT NULL"
                f" AND fechaobservacion >= '{inicio}'"
                f" AND fechaobservacion < '{fin}'"
            )
            try:
                registros = fetch_all(
                    dataset_id=dataset_id,
                    select=select,
                    where=where,
                    group=group,
                    order=order,
                )
                if registros:
                    partes.append(pd.DataFrame(registros))
            except Exception as exc:
                fallos += 1
                logger.warning(
                    "%s Bloque fallido dataset=%s municipio=%s ventana=%s..%s: %s",
                    prefijo_log,
                    dataset_id,
                    municipio,
                    inicio,
                    fin,
                    exc,
                )

    if fallos:
        logger.warning("%s Bloques fallidos: %d (se continua con datos parciales)", prefijo_log, fallos)

    if not partes:
        return pd.DataFrame()

    df = pd.concat(partes, ignore_index=True)

    # Re-agregar: las ventanas mensuales pueden producir filas duplicadas por
    # (municipio, año) cuando _MONTH_CHUNK < 12. Se consolida aquí en Python.
    # La re-agregación depende de las métricas; se delega al llamador que
    # conoce las columnas exactas. Retornamos el DataFrame crudo para que
    # cada función pública haga su propia consolidación.
    return df


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

    Estrategia de filtrado:
        Filtra por `municipio IN (...)` en MAYÚSCULAS, NO por `codigoestacion`.
        El campo `codigoestacion` no está indexado en el servidor Socrata de
        datos.gov.co y provoca full-scans con timeout incluso con 1 estación.
        El campo `municipio` sí está indexado y responde en tiempo razonable.
        Las consultas se dividen en ventanas mensuales (IDEAM_MONTH_CHUNK) para
        acotar el volumen por llamada. Los resultados parciales se re-agregan
        localmente con pandas antes de retornar.

    Args:
        df_estaciones: Output de download_catalogo_estaciones() (D2.1).
                       Se acepta por compatibilidad de interfaz pero no se usa
                       para construir el filtro de observaciones.
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

    if df_estaciones.empty:
        raise ValueError("D2.2: df_estaciones vacío — ejecutar D2.1 primero")

    logger.info(
        "[D2.2] Descargando precipitación para %d municipios (filtro por municipio)…",
        len(codigos_objetivo),
    )

    # ── Consulta A — acumulado anual ──────────────────────────────────────────
    logger.info("[D2.2] Consulta A: acumulado anual…")
    df_acum_raw = _fetch_obs_por_municipio(
        dataset_id=DATASETS["ideam_precipitacion"],
        codigos_objetivo=codigos_objetivo,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "sum(valorobservado) AS prec_acum_mm, "
            "count(*) AS n_observaciones"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
        prefijo_log="[D2.2-A]",
    )

    if df_acum_raw.empty:
        raise ValueError("D2.2: sin registros de precipitación para el MVP")

    # Re-agregar por (municipio, año) — las ventanas mensuales pueden duplicar
    df_acum_raw["prec_acum_mm"] = pd.to_numeric(df_acum_raw["prec_acum_mm"], errors="coerce")
    df_acum_raw["n_observaciones"] = pd.to_numeric(df_acum_raw["n_observaciones"], errors="coerce")
    df_acum_raw["año"] = _extraer_año(df_acum_raw["año"])
    df_acum_raw["municipio"] = df_acum_raw["municipio"].astype(str).str.strip().apply(normalize_title_case)

    df_acum = (
        df_acum_raw.groupby(["municipio", "año"], as_index=False)
        .agg(prec_acum_mm=("prec_acum_mm", "sum"), n_observaciones=("n_observaciones", "sum"))
    )

    # ── Consulta B — días secos y días de lluvia ──────────────────────────────
    logger.info("[D2.2] Consulta B: días secos y días de lluvia…")
    df_dias_raw = _fetch_obs_por_municipio(
        dataset_id=DATASETS["ideam_precipitacion"],
        codigos_objetivo=codigos_objetivo,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "count(CASE WHEN valorobservado < '1' THEN 1 END) AS prec_dias_secos, "
            "count(CASE WHEN valorobservado >= '1' THEN 1 END) AS prec_dias_lluvia"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
        prefijo_log="[D2.2-B]",
    )

    if not df_dias_raw.empty:
        df_dias_raw["prec_dias_secos"] = pd.to_numeric(df_dias_raw["prec_dias_secos"], errors="coerce")
        df_dias_raw["prec_dias_lluvia"] = pd.to_numeric(df_dias_raw["prec_dias_lluvia"], errors="coerce")
        df_dias_raw["año"] = _extraer_año(df_dias_raw["año"])
        df_dias_raw["municipio"] = df_dias_raw["municipio"].astype(str).str.strip().apply(normalize_title_case)
        df_dias = (
            df_dias_raw.groupby(["municipio", "año"], as_index=False)
            .agg(
                prec_dias_secos=("prec_dias_secos", "sum"),
                prec_dias_lluvia=("prec_dias_lluvia", "sum"),
            )
        )
    else:
        df_dias = pd.DataFrame()

    # ── Consulta C — n_estaciones_prec ────────────────────────────────────────
    logger.info("[D2.2] Consulta C: n_estaciones_prec…")
    df_nest_raw = _fetch_obs_por_municipio(
        dataset_id=DATASETS["ideam_precipitacion"],
        codigos_objetivo=codigos_objetivo,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "count(codigoestacion) AS n_estaciones_prec"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
        prefijo_log="[D2.2-C]",
    )

    if not df_nest_raw.empty:
        df_nest_raw["n_estaciones_prec"] = pd.to_numeric(df_nest_raw["n_estaciones_prec"], errors="coerce")
        df_nest_raw["año"] = _extraer_año(df_nest_raw["año"])
        df_nest_raw["municipio"] = df_nest_raw["municipio"].astype(str).str.strip().apply(normalize_title_case)
        df_nest = (
            df_nest_raw.groupby(["municipio", "año"], as_index=False)
            .agg(n_estaciones_prec=("n_estaciones_prec", "sum"))
        )
    else:
        df_nest = pd.DataFrame()

    # ── Valores negativos de precipitación → NaN ─────────────────────────────
    mask_neg = df_acum["prec_acum_mm"] < 0
    if mask_neg.any():
        for _, row in df_acum[mask_neg].iterrows():
            logger.warning(
                "[D2.2] Precipitación negativa (%.1f mm) en %s año %s — se convierte a NaN",
                row["prec_acum_mm"], row["municipio"], row["año"],
            )
        df_acum.loc[mask_neg, "prec_acum_mm"] = float("nan")

    # ── Cruzar municipio → codigo_dane ────────────────────────────────────────
    for df_part in [df_acum, df_dias, df_nest]:
        if not df_part.empty:
            df_part["codigo_dane"] = df_part["municipio"].apply(get_codigo)

    # ── Filtrar por codigos_objetivo ──────────────────────────────────────────
    df_acum = df_acum[df_acum["codigo_dane"].isin(codigos_objetivo)]
    if not df_dias.empty:
        df_dias = df_dias[df_dias["codigo_dane"].isin(codigos_objetivo)]
    if not df_nest.empty:
        df_nest = df_nest[df_nest["codigo_dane"].isin(codigos_objetivo)]

    # ── Merge de las tres consultas ───────────────────────────────────────────
    _key = ["codigo_dane", "municipio", "año"]
    df = df_acum[_key + ["prec_acum_mm", "n_observaciones"]].copy()

    if not df_dias.empty:
        df = df.merge(df_dias[_key + ["prec_dias_secos", "prec_dias_lluvia"]], on=_key, how="outer")
    else:
        df["prec_dias_secos"] = float("nan")
        df["prec_dias_lluvia"] = float("nan")

    if not df_nest.empty:
        df = df.merge(df_nest[_key + ["n_estaciones_prec"]], on=_key, how="outer")
    else:
        df["n_estaciones_prec"] = float("nan")

    # ── Filtrar años fuera de rango ───────────────────────────────────────────
    df = df[df["año"].between(_YEAR_START, _YEAR_END)]

    if df.empty:
        raise ValueError("D2.2: sin registros de precipitación para el MVP tras filtrar")

    df = df.drop(columns=["n_observaciones"], errors="ignore")

    # ── Warning por municipios sin datos ──────────────────────────────────────
    codigos_con_datos = set(df["codigo_dane"].dropna().unique())
    for codigo in sorted(codigos_objetivo):
        if codigo not in codigos_con_datos:
            nombre = get_nombre(codigo) or codigo
            logger.warning("[D2.2] Sin datos de precipitación para %s (%s)", nombre, codigo)

    # ── Loggear resumen ───────────────────────────────────────────────────────
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

    # ── Retornar con columnas en orden canónico ───────────────────────────────
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
      1. Validar df_estaciones (solo comprueba que no esté vacío)
      2. Ejecutar consulta SoQL agregada con ventanas mensuales,
         filtrando por municipio en MAYÚSCULAS (no por codigoestacion)
      3. Re-agregar localmente por (municipio, año) para consolidar ventanas
      4. Convertir año (date_trunc_y → int)
      5. Normalizar municipio a Title Case
      6. Cruzar municipio → codigo_dane
      7. Filtrar por codigos_objetivo y rango YEAR_START–YEAR_END

    Nota sobre la estrategia de filtrado:
        Se filtra por `municipio` (MAYÚSCULAS) en lugar de `codigoestacion`
        porque el servidor Socrata de datos.gov.co no tiene índice sobre
        `codigoestacion` en los datasets de observaciones. Cualquier consulta
        con WHERE codigoestacion IN (...) provoca un full-scan y hace timeout.
        Ver docstring del módulo para el diagnóstico completo.

    Args:
        dataset_id:       ID Socrata del dataset a consultar.
        df_estaciones:    Output de download_catalogo_estaciones() (D2.1).
                          Se acepta por compatibilidad pero no se usa para
                          construir el filtro de observaciones.
        select:           Cláusula $select de la consulta SoQL.
                          Debe incluir `municipio` y `date_trunc_y(...) AS año`.
        codigos_objetivo: Conjunto de códigos DANE a conservar.
        prefijo_log:      Prefijo para mensajes de log (ej. '[D2.3-temp]').

    Returns:
        DataFrame con columnas: municipio, año, codigo_dane + las métricas
        definidas en `select`. Listo para filtrado de rango físico y
        construcción del output final.

    Raises:
        ValueError: Si df_estaciones está vacío o el resultado tras filtros
                    está vacío.
    """
    if df_estaciones.empty:
        raise ValueError(f"{prefijo_log}: df_estaciones vacío — ejecutar D2.1 primero")

    logger.info(
        "%s Descargando %s para %d municipios (filtro por municipio)…",
        prefijo_log, dataset_id, len(codigos_objetivo),
    )

    df_raw = _fetch_obs_por_municipio(
        dataset_id=dataset_id,
        codigos_objetivo=codigos_objetivo,
        select=select,
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
        prefijo_log=prefijo_log,
    )

    if df_raw.empty:
        raise ValueError(f"{prefijo_log}: sin registros para el MVP")

    # Convertir año
    df_raw["año"] = _extraer_año(df_raw["año"])

    # Normalizar municipio
    df_raw["municipio"] = (
        df_raw["municipio"].astype(str).str.strip().apply(normalize_title_case)
    )

    # Cruzar municipio → codigo_dane
    df_raw["codigo_dane"] = df_raw["municipio"].apply(get_codigo)

    # Filtrar por codigos_objetivo
    df_raw = df_raw[df_raw["codigo_dane"].isin(codigos_objetivo)]

    # Filtrar rango de años
    df_raw = df_raw[df_raw["año"].between(_YEAR_START, _YEAR_END)]

    if df_raw.empty:
        raise ValueError(f"{prefijo_log}: sin registros tras filtrar por municipio y año")

    return df_raw.reset_index(drop=True)


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

    Estrategia de filtrado:
        Filtra por `municipio IN (...)` en MAYÚSCULAS, NO por `codigoestacion`.
        Ver docstring del módulo para el diagnóstico completo del problema de
        timeouts con filtros por codigoestacion.

    Nota: `temp_max_media_c` es el máximo absoluto anual (max(valorobservado)),
    no la media de máximas diarias. SoQL no soporta subconsultas para calcular
    la media de máximas diarias directamente. Es un proxy válido para señal
    de estrés térmico en el modelo predictivo.

    Args:
        df_estaciones: Output de download_catalogo_estaciones() (D2.1).
                       Se acepta por compatibilidad de interfaz pero no se usa
                       para construir el filtro de observaciones.
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

    df_nest_raw = _fetch_obs_por_municipio(
        dataset_id=DATASETS["ideam_temperatura"],
        codigos_objetivo=codigos_objetivo,
        select=(
            "municipio, "
            "date_trunc_y(fechaobservacion) AS año, "
            "count(codigoestacion) AS n_estaciones_temp"
        ),
        group="municipio, date_trunc_y(fechaobservacion)",
        order="municipio, date_trunc_y(fechaobservacion)",
        prefijo_log="[D2.3-temp-nest]",
    )

    if not df_nest_raw.empty:
        df_nest_raw["año"] = _extraer_año(df_nest_raw["año"])
        df_nest_raw["n_estaciones_temp"] = pd.to_numeric(df_nest_raw["n_estaciones_temp"], errors="coerce")
        df_nest_raw["municipio"] = (
            df_nest_raw["municipio"].astype(str).str.strip().apply(normalize_title_case)
        )
        df_nest_raw["codigo_dane"] = df_nest_raw["municipio"].apply(get_codigo)
        df_nest_raw = df_nest_raw[df_nest_raw["codigo_dane"].isin(codigos_objetivo)]
        df_nest_raw = df_nest_raw[df_nest_raw["año"].between(_YEAR_START, _YEAR_END)]

        df_nest = (
            df_nest_raw.groupby(["codigo_dane", "municipio", "año"], as_index=False)
            .agg(n_estaciones_temp=("n_estaciones_temp", "sum"))
        )

        _key_merge = ["codigo_dane", "municipio", "año"]
        df = df.merge(df_nest[_key_merge + ["n_estaciones_temp"]], on=_key_merge, how="left")
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

    Estrategia de filtrado:
        Filtra por `municipio IN (...)` en MAYÚSCULAS, NO por `codigoestacion`.
        Ver docstring del módulo para el diagnóstico completo del problema de
        timeouts con filtros por codigoestacion.

    Args:
        df_estaciones: Output de download_catalogo_estaciones() (D2.1).
                       Se acepta por compatibilidad de interfaz pero no se usa
                       para construir el filtro de observaciones.
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

    # ── Guardar intermedios (prec, temp, hum) para inspección sin re-ejecutar ──
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        prec_path = output_dir / "precipitacion.parquet"
        df_prec.to_parquet(prec_path, index=False, engine="pyarrow")
        logger.info("[D2.4] Intermedio guardado: %s", prec_path)
    except Exception as e:
        logger.warning("[D2.4] No se pudo guardar precipitacion intermedia: %s", e)
    try:
        temp_path = output_dir / "temperatura.parquet"
        df_temp.to_parquet(temp_path, index=False, engine="pyarrow")
        logger.info("[D2.4] Intermedio guardado: %s", temp_path)
    except Exception as e:
        logger.warning("[D2.4] No se pudo guardar temperatura intermedia: %s", e)
    try:
        hum_path = output_dir / "humedad.parquet"
        df_hum.to_parquet(hum_path, index=False, engine="pyarrow")
        logger.info("[D2.4] Intermedio guardado: %s", hum_path)
    except Exception as e:
        logger.warning("[D2.4] No se pudo guardar humedad intermedia: %s", e)

    # ── Deduplicación segura: consolidar posibles filas duplicadas por (codigo_dane, año)
    # Precipitación: sumar acumulados y contar observaciones; n_estaciones -> max
    if not df_prec.empty:
        agg_prec = {}
        if "prec_acum_mm" in df_prec.columns:
            agg_prec["prec_acum_mm"] = ("prec_acum_mm", "sum")
        if "prec_dias_secos" in df_prec.columns:
            agg_prec["prec_dias_secos"] = ("prec_dias_secos", "sum")
        if "prec_dias_lluvia" in df_prec.columns:
            agg_prec["prec_dias_lluvia"] = ("prec_dias_lluvia", "sum")
        if "n_observaciones" in df_prec.columns:
            agg_prec["n_observaciones"] = ("n_observaciones", "sum")
        if "n_estaciones_prec" in df_prec.columns:
            agg_prec["n_estaciones_prec"] = ("n_estaciones_prec", "max")
        if agg_prec:
            df_prec = (
                df_prec.groupby(["codigo_dane", "año"], as_index=False)
                .agg(**{k: v for k, v in agg_prec.items()})
            )

    # Temperatura: promediar medias, tomar max de máximas; n_estaciones -> max
    if not df_temp.empty:
        agg_temp = {}
        if "temp_media_c" in df_temp.columns:
            agg_temp["temp_media_c"] = ("temp_media_c", "mean")
        if "temp_max_media_c" in df_temp.columns:
            agg_temp["temp_max_media_c"] = ("temp_max_media_c", "max")
        if "n_obs_temp" in df_temp.columns:
            agg_temp["n_obs_temp"] = ("n_obs_temp", "sum")
        if "n_estaciones_temp" in df_temp.columns:
            agg_temp["n_estaciones_temp"] = ("n_estaciones_temp", "max")
        if agg_temp:
            df_temp = (
                df_temp.groupby(["codigo_dane", "año"], as_index=False)
                .agg(**{k: v for k, v in agg_temp.items()})
            )

    # Humedad: promediar
    if not df_hum.empty:
        agg_hum = {}
        if "hum_media_pct" in df_hum.columns:
            agg_hum["hum_media_pct"] = ("hum_media_pct", "mean")
        if agg_hum:
            df_hum = (
                df_hum.groupby(["codigo_dane", "año"], as_index=False)
                .agg(**{k: v for k, v in agg_hum.items()})
            )

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
    # For consistency with validators, force 64-bit integer dtype
    df["n_estaciones_prec"] = df["n_estaciones_prec"].fillna(0).astype("int64")
    df["n_estaciones_temp"] = df["n_estaciones_temp"].fillna(0).astype("int64")

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
