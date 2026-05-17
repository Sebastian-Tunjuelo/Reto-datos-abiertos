"""
D3 — Pipeline territorial: aptitud agrícola (UPRA) y frontera agrícola.

Funciones implementadas en este módulo:
  D3.1 - download_aptitud_cafe()   → aptitud_cafe.parquet
  D3.1 - download_aptitud_cacao()  → aptitud_cacao.parquet
  D3.2 - download_aptitud_maiz()   → aptitud_maiz.parquet (consolida 3 datasets)
  D3.3 - download_frontera()       → frontera.parquet

Pendiente:
  - run_pipeline()  → orquesta todo el pipeline territorial
"""
import logging
from typing import Optional

import pandas as pd

from shared.config import DATA_DIR, DATASETS
from shared.dane_codes import MVP_CODIGOS, DANE_TO_NAME
from shared.normalization import normalize_dane_code, normalize_title_case
from shared.socrata_client import fetch_all

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constantes compartidas
# ---------------------------------------------------------------------------

# Mapa de normalización de categorías de aptitud (compartido D3.1, D3.2, D3.3)
_APTITUD_MAP: dict[str, str] = {
    # Valores simples (spec original)
    "alta": "Alta",
    "a": "Alta",
    "media": "Media",
    "m": "Media",
    "moderada": "Media",
    "baja": "Baja",
    "b": "Baja",
    "exclusión": "Exclusion",
    "exclusion": "Exclusion",
    "no apta": "Exclusion",
    "e": "Exclusion",
    # Valores reales observados en la API UPRA (prefijo "Aptitud ")
    "aptitud alta": "Alta",
    "aptitud media": "Media",
    "aptitud baja": "Baja",
    "exclusión legal": "Exclusion",
    "exclusion legal": "Exclusion",
}

# Columnas de área por categoría (en orden canónico)
_AREA_COLS = ["area_alta_ha", "area_media_ha", "area_baja_ha", "area_exclusion_ha"]

# Esquema de salida final (orden exacto, compartido por café, cacao y maíz)
_SCHEMA_COLS = [
    "codigo_dane",
    "municipio",
    "departamento",
    "cultivo",
    "area_alta_ha",
    "area_media_ha",
    "area_baja_ha",
    "area_exclusion_ha",
    "area_total_ha",
    "pct_alta",
    "pct_media",
    "pct_baja",
    "pct_exclusion",
]

# IDs de los 3 datasets de maíz y sus etiquetas de fuente
_MAIZ_DATASETS: list[tuple[str, str]] = [
    (DATASETS["upra_maiz_trad"], "tradicional"),
    (DATASETS["upra_maiz_tec1"], "tec_1sem"),
    (DATASETS["upra_maiz_tec2"], "tec_2sem"),
]

# Mapa de normalización de tipos de frontera agrícola (D3.3)
_FRONTERA_MAP: dict[str, str] = {
    "condicionada": "Condicionada",
    "c": "Condicionada",
    "no condicionada": "No_condicionada",
    "no_condicionada": "No_condicionada",
    "nc": "No_condicionada",
}

# Esquema de salida para frontera (orden exacto)
_SCHEMA_FRONTERA_COLS = [
    "codigo_dane",
    "municipio",
    "departamento",
    "area_condicionada_ha",
    "area_no_condicionada_ha",
    "area_total_ha",
    "pct_condicionada",
    "pct_no_condicionada",
]


# ---------------------------------------------------------------------------
# Funciones privadas de utilidad
# ---------------------------------------------------------------------------

def _normalizar_aptitud(valor: Optional[str]) -> Optional[str]:
    """
    Normaliza una categoría de aptitud UPRA a su forma canónica.

    Returns:
        'Alta' | 'Media' | 'Baja' | 'Exclusion' | None si no reconocida.
    """
    if valor is None:
        return None
    return _APTITUD_MAP.get(valor.strip().lower(), None)


def _normalizar_frontera(valor: Optional[str]) -> Optional[str]:
    """
    Normaliza un tipo de frontera agrícola UPRA a su forma canónica.

    Returns:
        'Condicionada' | 'No_condicionada' | None si no reconocido.
    """
    if valor is None:
        return None
    return _FRONTERA_MAP.get(valor.strip().lower(), None)


def _build_where_clause(codigos_dane: list[str]) -> str:
    """Construye la cláusula $where SoQL para filtrar por códigos DANE."""
    quoted = ", ".join(f"'{c}'" for c in codigos_dane)
    return f"cod_dane_m IN ({quoted})"


def _pivot_aptitud(
    df: pd.DataFrame,
    cultivo: str,
    prefijo_log: str,
    codigos_dane: list[str],
) -> pd.DataFrame:
    """
    Recibe un DataFrame con columnas (codigo_dane, municipio, departamento,
    aptitud_norm, area_ha) y retorna un DataFrame pivotado con una fila
    por municipio y columnas de área y porcentaje por categoría.

    Pasos:
      - pivot_table por (codigo_dane, municipio, departamento) × aptitud_norm
      - Rellenar NaN con 0.0 para categorías sin área
      - Calcular area_total_ha y pct_* (redondeados a 4 decimales)
      - Agregar columna cultivo
      - Loggear municipios con area_total_ha == 0
      - Loggear municipios del MVP sin datos

    Args:
        df:           DataFrame con columnas mínimas requeridas.
        cultivo:      Nombre del cultivo para la columna 'cultivo'.
        prefijo_log:  Prefijo para mensajes de log.
        codigos_dane: Lista de códigos DANE esperados (para detectar faltantes).

    Returns:
        DataFrame con esquema unificado (_SCHEMA_COLS).
    """
    # Pivot: una fila por municipio, columnas por categoría de aptitud
    pivot = df.pivot_table(
        index=["codigo_dane", "municipio", "departamento"],
        columns="aptitud_norm",
        values="area_ha",
        aggfunc="sum",
    ).reset_index()

    # Aplanar el nombre del eje de columnas
    pivot.columns.name = None

    # Asegurar que existen las 4 columnas de área; renombrar o crear con 0.0
    for cat, col in [
        ("Alta", "area_alta_ha"),
        ("Media", "area_media_ha"),
        ("Baja", "area_baja_ha"),
        ("Exclusion", "area_exclusion_ha"),
    ]:
        if cat in pivot.columns:
            pivot = pivot.rename(columns={cat: col})
        else:
            pivot[col] = 0.0

    # Rellenar NaN con 0.0 (municipios sin alguna categoría)
    pivot[_AREA_COLS] = pivot[_AREA_COLS].fillna(0.0)

    # Calcular área total
    pivot["area_total_ha"] = pivot[_AREA_COLS].sum(axis=1)

    # Calcular porcentajes (None si area_total_ha == 0)
    for col_area, col_pct in zip(
        _AREA_COLS,
        ["pct_alta", "pct_media", "pct_baja", "pct_exclusion"],
    ):
        pivot[col_pct] = pivot.apply(
            lambda row, ca=col_area: (
                round(row[ca] / row["area_total_ha"], 4)
                if row["area_total_ha"] > 0
                else None
            ),
            axis=1,
        )

    # Loggear municipios con area_total_ha == 0
    mask_cero = pivot["area_total_ha"] == 0
    for _, row in pivot[mask_cero].iterrows():
        logger.warning(
            "%s %s: area_total_ha = 0, pct_* = None",
            prefijo_log, row["municipio"],
        )

    # Agregar columna cultivo
    pivot["cultivo"] = cultivo

    # Loggear municipios del MVP sin datos
    codigos_presentes = set(pivot["codigo_dane"].tolist())
    for codigo in codigos_dane:
        if codigo not in codigos_presentes:
            nombre = DANE_TO_NAME.get(codigo, codigo)
            logger.warning(
                "%s Sin datos de aptitud %s para %s (%s)",
                prefijo_log, cultivo, nombre, codigo,
            )

    return pivot[_SCHEMA_COLS].reset_index(drop=True)


def _fetch_one_dataset(
    dataset_id: str,
    fuente: str,
    codigos_dane: list[str],
    prefijo_log: str,
) -> Optional[pd.DataFrame]:
    """
    Descarga un único dataset UPRA, normaliza columnas y categorías de aptitud.

    Retorna None (con warning) si el dataset no tiene datos para los municipios
    indicados — esto es esperado para maíz tradicional que solo cubre 123 municipios.

    Returns:
        DataFrame con columnas (codigo_dane, municipio, departamento,
        aptitud_norm, area_ha, fuente), o None si no hay datos.
    """
    select = "cod_dane_m,municipio,departamen,aptitud,sum(area_ha) AS area_total"
    where = _build_where_clause(codigos_dane)
    group = "cod_dane_m,municipio,departamen,aptitud"
    order = "cod_dane_m,aptitud"

    logger.info(
        "%s Descargando dataset %s (fuente: %s)...",
        prefijo_log, dataset_id, fuente,
    )
    registros = fetch_all(
        dataset_id=dataset_id,
        select=select,
        where=where,
        group=group,
        order=order,
    )

    if not registros:
        logger.warning(
            "%s Dataset %s: sin datos para el MVP",
            prefijo_log, dataset_id,
        )
        return None

    df = pd.DataFrame(registros)

    # Renombrar columnas
    df = df.rename(columns={
        "cod_dane_m": "codigo_dane",
        "departamen": "departamento",
        "area_total": "area_ha",
    })

    # Normalizar código DANE y filtrar
    df["codigo_dane"] = df["codigo_dane"].apply(normalize_dane_code)
    df = df[df["codigo_dane"].isin(codigos_dane)].copy()

    if df.empty:
        logger.warning(
            "%s Dataset %s: sin datos tras filtrar códigos DANE",
            prefijo_log, dataset_id,
        )
        return None

    # Normalizar nombres
    df["municipio"] = df["municipio"].apply(normalize_title_case)
    df["departamento"] = df["departamento"].apply(normalize_title_case)

    # Convertir área a numérico
    df["area_ha"] = pd.to_numeric(df["area_ha"], errors="coerce")

    # Normalizar categoría de aptitud
    df["aptitud_norm"] = df["aptitud"].apply(_normalizar_aptitud)

    # Loggear y descartar aptitudes no reconocidas
    mask_desconocida = df["aptitud_norm"].isna()
    for val in df.loc[mask_desconocida, "aptitud"].unique():
        logger.warning("%s Aptitud desconocida: '%s'", prefijo_log, val)
    df = df[~mask_desconocida].copy()

    if df.empty:
        logger.warning(
            "%s Dataset %s: sin registros válidos tras normalizar categorías",
            prefijo_log, dataset_id,
        )
        return None

    # Marcar fuente
    df["fuente"] = fuente

    n_municipios = df["codigo_dane"].nunique()
    logger.info(
        "%s Dataset %s (%s): %d municipios con datos",
        prefijo_log, dataset_id, fuente, n_municipios,
    )

    return df[["codigo_dane", "municipio", "departamento", "aptitud_norm", "area_ha", "fuente"]]


def _download_aptitud(
    dataset_id: str,
    cultivo: str,
    codigos_dane: list[str],
    prefijo_log: str,
) -> pd.DataFrame:
    """
    Lógica común para descargar y agregar aptitud agrícola UPRA (un solo dataset).

    Usado por download_aptitud_cafe() y download_aptitud_cacao().

    Args:
        dataset_id:   ID Socrata del dataset UPRA.
        cultivo:      Nombre del cultivo ('Café' o 'Cacao').
        codigos_dane: Lista de códigos DANE a filtrar.
        prefijo_log:  Prefijo para mensajes de log (ej. '[D3.1]').

    Returns:
        DataFrame con esquema unificado (13 columnas).

    Raises:
        ValueError: Si el resultado está vacío tras aplicar filtros.
    """
    df = _fetch_one_dataset(
        dataset_id=dataset_id,
        fuente=cultivo.lower(),
        codigos_dane=codigos_dane,
        prefijo_log=prefijo_log,
    )

    if df is None or df.empty:
        raise ValueError(f"Aptitud {cultivo}: sin registros para el MVP")

    return _pivot_aptitud(
        df=df,
        cultivo=cultivo,
        prefijo_log=prefijo_log,
        codigos_dane=codigos_dane,
    )


# ---------------------------------------------------------------------------
# Funciones públicas — D3.1
# ---------------------------------------------------------------------------

def download_aptitud_cafe(
    codigos_dane: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Descarga y agrega aptitud agrícola UPRA para café.

    Args:
        codigos_dane: Lista de códigos DANE a filtrar.
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con una fila por municipio.
        Columnas: codigo_dane, municipio, departamento, cultivo,
                  area_alta_ha, area_media_ha, area_baja_ha, area_exclusion_ha,
                  area_total_ha, pct_alta, pct_media, pct_baja, pct_exclusion.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar filtros.
        requests.RequestException: Si la API falla tras reintentos.
    """
    codigos = codigos_dane if codigos_dane is not None else MVP_CODIGOS
    return _download_aptitud(
        dataset_id=DATASETS["upra_cafe"],
        cultivo="Café",
        codigos_dane=codigos,
        prefijo_log="[D3.1]",
    )


def download_aptitud_cacao(
    codigos_dane: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Descarga y agrega aptitud agrícola UPRA para cacao.
    Mismo esquema que download_aptitud_cafe(), cultivo = 'Cacao'.

    Args:
        codigos_dane: Lista de códigos DANE a filtrar.
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con una fila por municipio.
        Columnas: codigo_dane, municipio, departamento, cultivo,
                  area_alta_ha, area_media_ha, area_baja_ha, area_exclusion_ha,
                  area_total_ha, pct_alta, pct_media, pct_baja, pct_exclusion.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar filtros.
        requests.RequestException: Si la API falla tras reintentos.
    """
    codigos = codigos_dane if codigos_dane is not None else MVP_CODIGOS
    return _download_aptitud(
        dataset_id=DATASETS["upra_cacao"],
        cultivo="Cacao",
        codigos_dane=codigos,
        prefijo_log="[D3.1]",
    )


# ---------------------------------------------------------------------------
# Función pública — D3.2
# ---------------------------------------------------------------------------

def download_aptitud_maiz(
    codigos_dane: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Descarga y consolida aptitud agrícola UPRA para maíz desde 3 datasets.

    Descarga frjn-92um (tradicional), a5yc-uszt (tec. 1er sem) y
    tzga-4zse (tec. 2do sem). Consolida tomando el máximo de área
    por categoría entre los 3 datasets para cada municipio.

    La estrategia de máximo refleja el potencial productivo: si un municipio
    tiene aptitud Alta en maíz tecnificado pero no aparece en maíz tradicional,
    se usa el tecnificado como mejor estimación disponible.

    Args:
        codigos_dane: Lista de códigos DANE a filtrar.
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con una fila por municipio.
        Columnas: codigo_dane, municipio, departamento, cultivo,
                  area_alta_ha, area_media_ha, area_baja_ha, area_exclusion_ha,
                  area_total_ha, pct_alta, pct_media, pct_baja, pct_exclusion.

    Raises:
        ValueError: Si los 3 datasets están vacíos tras aplicar filtros.
        requests.RequestException: Si alguna descarga falla tras reintentos.
    """
    prefijo_log = "[D3.2]"
    codigos = codigos_dane if codigos_dane is not None else MVP_CODIGOS

    # 1. Descargar los 3 datasets individualmente
    frames: list[pd.DataFrame] = []
    cobertura: dict[str, int] = {}  # fuente → n municipios con datos

    for dataset_id, fuente in _MAIZ_DATASETS:
        df_fuente = _fetch_one_dataset(
            dataset_id=dataset_id,
            fuente=fuente,
            codigos_dane=codigos,
            prefijo_log=prefijo_log,
        )
        if df_fuente is not None:
            n = df_fuente["codigo_dane"].nunique()
            cobertura[fuente] = n
            frames.append(df_fuente)
        else:
            cobertura[fuente] = 0

    # 2. Verificar que al menos un dataset tiene datos
    if not frames:
        raise ValueError("Aptitud maíz: sin registros para el MVP en ningún dataset")

    df_todos = pd.concat(frames, ignore_index=True)

    # 3. Consolidar: máximo de área por (municipio, aptitud) entre los 3 datasets
    #    Esto preserva la mejor estimación disponible por categoría.
    df_consolidado = (
        df_todos
        .groupby(
            ["codigo_dane", "municipio", "departamento", "aptitud_norm"],
            as_index=False,
        )["area_ha"]
        .max()
    )

    # 4. Pivot + porcentajes (lógica compartida con D3.1)
    resultado = _pivot_aptitud(
        df=df_consolidado,
        cultivo="Maíz",
        prefijo_log=prefijo_log,
        codigos_dane=codigos,
    )

    # 5. Loggear resumen de cobertura por dataset
    n_consolidado = len(resultado)
    logger.info(
        "%s === Resumen D3.2 — Aptitud Maíz ===\n"
        "  Dataset %s (tradicional):   %d/%d municipios\n"
        "  Dataset %s (tec. 1er sem): %d/%d municipios\n"
        "  Dataset %s (tec. 2do sem): %d/%d municipios\n"
        "  Consolidado (máximo):       %d/%d municipios",
        prefijo_log,
        DATASETS["upra_maiz_trad"], cobertura.get("tradicional", 0), len(codigos),
        DATASETS["upra_maiz_tec1"], cobertura.get("tec_1sem", 0), len(codigos),
        DATASETS["upra_maiz_tec2"], cobertura.get("tec_2sem", 0), len(codigos),
        n_consolidado, len(codigos),
    )

    return resultado


# ---------------------------------------------------------------------------
# Función pública — D3.3
# ---------------------------------------------------------------------------

def download_frontera(
    codigos_dane: Optional[list[str]] = None,
) -> pd.DataFrame:
    """
    Descarga y agrega la frontera agrícola UPRA por municipio.

    Descarga el dataset fyc7-sbtz, agrega el área por tipo de frontera
    (Condicionada / No_condicionada) usando $group + sum(area_ha) para
    evitar descargar geometrías, y calcula los porcentajes de área.

    La frontera no depende del cultivo — aplica igual a café, cacao y maíz.
    D5 hará un join por codigo_dane y replicará el valor para los 3 cultivos.

    Args:
        codigos_dane: Lista de códigos DANE a filtrar.
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con una fila por municipio.
        Columnas: codigo_dane, municipio, departamento,
                  area_condicionada_ha, area_no_condicionada_ha,
                  area_total_ha, pct_condicionada, pct_no_condicionada.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar filtros.
        requests.RequestException: Si la API falla tras reintentos.
    """
    prefijo_log = "[D3.3]"
    codigos = codigos_dane if codigos_dane is not None else MVP_CODIGOS

    # 1. Descargar datos agregados (sin geometrías)
    select = "cod_dane_m,municipio,departamen,tipo_front,sum(area_ha) AS area_total"
    where = _build_where_clause(codigos)
    group = "cod_dane_m,municipio,departamen,tipo_front"
    order = "cod_dane_m,tipo_front"

    logger.info("%s Descargando frontera agrícola desde dataset %s", prefijo_log, DATASETS["upra_frontera"])
    registros = fetch_all(
        dataset_id=DATASETS["upra_frontera"],
        select=select,
        where=where,
        group=group,
        order=order,
    )

    # 2. Convertir a DataFrame
    df = pd.DataFrame(registros)
    if df.empty:
        raise ValueError("Frontera agrícola: sin registros para el MVP")

    logger.info("%s Registros descargados: %d", prefijo_log, len(df))

    # 3. Renombrar columnas
    df = df.rename(columns={
        "cod_dane_m": "codigo_dane",
        "departamen": "departamento",
        "area_total": "area_ha_raw",
    })

    # 4. Normalizar código DANE
    df["codigo_dane"] = df["codigo_dane"].apply(normalize_dane_code)

    # 5. Filtrar solo municipios del MVP
    df = df[df["codigo_dane"].isin(codigos)].copy()
    if df.empty:
        raise ValueError("Frontera agrícola: sin registros para el MVP tras filtrar códigos DANE")

    # 6. Normalizar nombres
    df["municipio"] = df["municipio"].apply(normalize_title_case)
    df["departamento"] = df["departamento"].apply(normalize_title_case)

    # 7. Convertir área a numérico
    df["area_ha_raw"] = pd.to_numeric(df["area_ha_raw"], errors="coerce")

    # 8. Normalizar tipo de frontera
    df["tipo_norm"] = df["tipo_front"].apply(_normalizar_frontera)

    # Loggear y descartar tipos no reconocidos
    mask_desconocido = df["tipo_norm"].isna()
    for val in df.loc[mask_desconocido, "tipo_front"].unique():
        logger.warning("%s Tipo de frontera desconocido: '%s'", prefijo_log, val)
    df = df[~mask_desconocido].copy()

    if df.empty:
        raise ValueError("Frontera agrícola: sin registros válidos tras normalizar tipos")

    # 9. Pivot: una fila por municipio, columnas por tipo de frontera
    pivot = df.pivot_table(
        index=["codigo_dane", "municipio", "departamento"],
        columns="tipo_norm",
        values="area_ha_raw",
        aggfunc="sum",
    ).reset_index()

    pivot.columns.name = None

    # Asegurar que existen las 2 columnas de área; renombrar o crear con 0.0
    for cat, col in [
        ("Condicionada", "area_condicionada_ha"),
        ("No_condicionada", "area_no_condicionada_ha"),
    ]:
        if cat in pivot.columns:
            pivot = pivot.rename(columns={cat: col})
        else:
            pivot[col] = 0.0

    _FRONTERA_AREA_COLS = ["area_condicionada_ha", "area_no_condicionada_ha"]
    pivot[_FRONTERA_AREA_COLS] = pivot[_FRONTERA_AREA_COLS].fillna(0.0)

    # 10. Calcular área total
    pivot["area_total_ha"] = pivot[_FRONTERA_AREA_COLS].sum(axis=1)

    # Loggear municipios con area_total_ha == 0
    mask_cero = pivot["area_total_ha"] == 0
    for _, row in pivot[mask_cero].iterrows():
        logger.warning(
            "%s %s: area_total_ha = 0, pct_* = None",
            prefijo_log, row["municipio"],
        )

    # 11. Calcular porcentajes (None si area_total_ha == 0)
    for col_area, col_pct in [
        ("area_condicionada_ha", "pct_condicionada"),
        ("area_no_condicionada_ha", "pct_no_condicionada"),
    ]:
        pivot[col_pct] = pivot.apply(
            lambda row, ca=col_area: (
                round(row[ca] / row["area_total_ha"], 4)
                if row["area_total_ha"] > 0
                else None
            ),
            axis=1,
        )

    # 12. Loggear municipios del MVP sin datos
    codigos_presentes = set(pivot["codigo_dane"].tolist())
    for codigo in codigos:
        if codigo not in codigos_presentes:
            nombre = DANE_TO_NAME.get(codigo, codigo)
            logger.warning(
                "%s Sin datos de frontera para %s (%s)",
                prefijo_log, nombre, codigo,
            )

    # 13. Retornar con columnas en orden del esquema de salida
    return pivot[_SCHEMA_FRONTERA_COLS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Punto de entrada como script
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import logging as _logging
    _logging.basicConfig(
        level=_logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    _PCT_COLS = ["municipio", "pct_alta", "pct_media", "pct_baja", "pct_exclusion"]

    print("=" * 60)
    print("D3 — Pipeline territorial")
    print("=" * 60)

    # D3.1 — Café
    print("\n[1/4] Descargando aptitud café...")
    df_cafe = download_aptitud_cafe()
    out_cafe = DATA_DIR / "aptitud_cafe.parquet"
    df_cafe.to_parquet(out_cafe, index=False, engine="pyarrow")
    print(f"  ✓ {len(df_cafe)} municipios → {out_cafe}")
    print(df_cafe[_PCT_COLS].to_string(index=False))

    # D3.1 — Cacao
    print("\n[2/4] Descargando aptitud cacao...")
    df_cacao = download_aptitud_cacao()
    out_cacao = DATA_DIR / "aptitud_cacao.parquet"
    df_cacao.to_parquet(out_cacao, index=False, engine="pyarrow")
    print(f"  ✓ {len(df_cacao)} municipios → {out_cacao}")
    print(df_cacao[_PCT_COLS].to_string(index=False))

    # D3.2 — Maíz
    print("\n[3/4] Descargando aptitud maíz (3 datasets)...")
    df_maiz = download_aptitud_maiz()
    out_maiz = DATA_DIR / "aptitud_maiz.parquet"
    df_maiz.to_parquet(out_maiz, index=False, engine="pyarrow")
    print(f"  ✓ {len(df_maiz)} municipios → {out_maiz}")
    print(df_maiz[_PCT_COLS].to_string(index=False))

    # D3.3 — Frontera
    print("\n[4/4] Descargando frontera agrícola...")
    df_frontera = download_frontera()
    out_frontera = DATA_DIR / "frontera.parquet"
    df_frontera.to_parquet(out_frontera, index=False, engine="pyarrow")
    print(f"  ✓ {len(df_frontera)} municipios → {out_frontera}")
    print(df_frontera[["municipio", "pct_condicionada", "pct_no_condicionada"]].to_string(index=False))

    print("\n✅ Pipeline territorial D3.1 + D3.2 + D3.3 completado.")
