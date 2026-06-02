"""
Módulo de ingesta de datos EVA (Evaluaciones Agropecuarias Municipales).

Funciones públicas:
    download_eva_historica() — D1.1: EVA 2007-2018 desde dataset 2pnw-mmge
    download_eva_reciente()  — D1.2: EVA 2019-2024 desde dataset uejq-wxrr
    run_pipeline()           — D1.3: unificación y guardado Parquet
    load_eva_completa()      — D1.3: carga eva_completa.parquet desde disco
"""
import logging
from pathlib import Path

import pandas as pd

from shared.config import DATA_DIR, DATASETS, RENDIMIENTO_RANGOS
from shared.dane_codes import DANE_TO_NAME, MVP_CODIGOS
from shared.normalization import (
    normalize_cultivo,
    normalize_dane_code,
    normalize_title_case,
)
from shared.socrata_client import fetch_all

logger = logging.getLogger(__name__)

# ── Constantes compartidas ────────────────────────────────────────────────────

# Orden exacto del esquema unificado EVA (compartido por D1.1 y D1.2)
_COLUMNAS_EVA = [
    "codigo_dane",
    "municipio",
    "departamento",
    "cultivo",
    "año",
    "periodo",
    "rendimiento",
    "area_sembrada",
    "area_cosechada",
    "produccion",
    "ciclo",
    "fuente",
]

_CICLOS_VALIDOS = {"PERMANENTE", "TRANSITORIO"}

# Filtro SoQL para EVA histórica.
# Incluye ambas formas del código DANE (con y sin cero inicial) para capturar
# registros que la API devuelve sin el cero inicial (ej. '5036' en lugar de '05036').
_CODIGOS_CON_SIN_CERO = [
    "73001", "73168",
    "41001", "41298", "41551",
    "68689", "68615",
    "05036", "5036",   # Anorí — puede venir sin cero
    "05030", "5030",   # Amalfi — puede venir sin cero
    "17541", "17524",
    "50001",
    "19256", "19418",
    "20001",
]
_WHERE_HISTORICA = (
    "cultivo IN ('CAFÉ','CACAO','MAÍZ') AND c_d_mun IN ("
    + ",".join(f"'{c}'" for c in _CODIGOS_CON_SIN_CERO)
    + ")"
)

# Filtro SoQL para EVA reciente.
# Los códigos DANE vienen bien formateados en este dataset — no necesita dobles.
_CODIGOS_MVP_STR = ",".join(f"'{c}'" for c in MVP_CODIGOS)
_WHERE_RECIENTE = (
    f"cultivo IN ('Café','Cacao','Maíz') AND c_digo_dane_municipio IN ({_CODIGOS_MVP_STR})"
)


# ── Función privada de limpieza compartida ────────────────────────────────────

def _limpiar_eva(
    df: pd.DataFrame,
    codigos_objetivo: list[str],
    fuente: str,
    prefijo_log: str,
) -> pd.DataFrame:
    """
    Aplica la pipeline de limpieza común a ambos datasets EVA.

    Pasos:
        1. Normaliza código DANE → str 5 dígitos
        2. Filtra por codigos_objetivo
        3. Normaliza cultivo; descarta no reconocidos
        4. Normaliza municipio y departamento a Title Case
        5. Convierte año a Int64
        6. Convierte rendimiento a float; invalida ceros y fuera de rango
        7. Convierte area_sembrada, area_cosechada, produccion a float
        8. Normaliza ciclo
        9. Asigna fuente
        10. Elimina duplicados por (codigo_dane, cultivo, año, periodo, fuente)
        11. Loggea warning por cada municipio objetivo sin datos
        12. Valida que el DataFrame no quedó vacío

    Args:
        df: DataFrame con columnas ya renombradas al esquema unificado.
        codigos_objetivo: Códigos DANE a conservar.
        fuente: Valor para la columna 'fuente' ('historica' | 'reciente').
        prefijo_log: Prefijo para mensajes de log (ej. '[D1.1]').

    Returns:
        DataFrame limpio con columnas en orden del esquema unificado.

    Raises:
        ValueError: Si el DataFrame queda vacío tras los filtros.
    """
    # ── 1. Normalizar código DANE ─────────────────────────────────────────────
    df = df.assign(
        codigo_dane=df["codigo_dane"].apply(
            lambda x: normalize_dane_code(x) if pd.notna(x) and str(x).strip() != "" else None
        )
    )

    # ── 2. Filtrar por códigos objetivo ───────────────────────────────────────
    n_antes = len(df)
    df = df[df["codigo_dane"].isin(codigos_objetivo)]
    logger.info(
        "%s Tras filtro por código DANE: %d → %d registros",
        prefijo_log, n_antes, len(df),
    )

    # ── 3. Normalizar cultivo ─────────────────────────────────────────────────
    df = df.assign(
        cultivo_norm=df["cultivo"].apply(
            lambda x: normalize_cultivo(str(x)) if pd.notna(x) else None
        )
    )

    for val in df[df["cultivo_norm"].isna()]["cultivo"].unique():
        logger.warning("%s Cultivo no reconocido descartado: '%s'", prefijo_log, val)

    n_antes = len(df)
    df = df[df["cultivo_norm"].notna()]
    n_desc = n_antes - len(df)
    if n_desc > 0:
        logger.info("%s Filas descartadas por cultivo no reconocido: %d", prefijo_log, n_desc)

    df = df.assign(cultivo=df["cultivo_norm"]).drop(columns=["cultivo_norm"])

    # ── 4. Normalizar municipio y departamento a Title Case ───────────────────
    df = df.assign(
        municipio=df["municipio"].apply(
            lambda x: normalize_title_case(str(x)) if pd.notna(x) else x
        ),
        departamento=df["departamento"].apply(
            lambda x: normalize_title_case(str(x)) if pd.notna(x) else x
        ),
    )

    # ── 5. Convertir año a Int64 ──────────────────────────────────────────────
    df = df.assign(año=pd.to_numeric(df["año"], errors="coerce").astype("Int64"))

    # ── 6. Convertir rendimiento; invalidar ceros y fuera de rango ───────────
    df = df.assign(rendimiento=pd.to_numeric(df["rendimiento"], errors="coerce"))
    df = df.assign(
        rendimiento=df["rendimiento"].where(df["rendimiento"] != 0.0, other=None)
    )

    def _validar_rendimiento(row: pd.Series) -> float | None:
        val = row["rendimiento"]
        cultivo = row["cultivo"]
        if pd.isna(val):
            return None
        rango = RENDIMIENTO_RANGOS.get(cultivo)
        if rango is None:
            return val
        min_r, max_r = rango
        if val < min_r or val > max_r:
            logger.warning(
                "%s Rendimiento fuera de rango (%.2f t/ha) para %s en %s — marcado None",
                prefijo_log, val, cultivo, row["municipio"],
            )
            return None
        return val

    df = df.assign(rendimiento=df.apply(_validar_rendimiento, axis=1))

    # ── 7. Convertir áreas y producción a float ───────────────────────────────
    df = df.assign(
        area_sembrada=pd.to_numeric(df["area_sembrada"], errors="coerce"),
        area_cosechada=pd.to_numeric(df["area_cosechada"], errors="coerce"),
        produccion=pd.to_numeric(df["produccion"], errors="coerce"),
    )

    # ── 8. Normalizar ciclo ───────────────────────────────────────────────────
    df = df.assign(
        ciclo=df["ciclo"].apply(
            lambda x: (
                str(x).strip().upper()
                if pd.notna(x) and str(x).strip().upper() in _CICLOS_VALIDOS
                else None
            )
        )
    )

    # ── 9. Asignar fuente ─────────────────────────────────────────────────────
    df = df.assign(fuente=fuente)

    # ── 10. Eliminar duplicados ───────────────────────────────────────────────
    clave_dedup = ["codigo_dane", "cultivo", "año", "periodo", "fuente"]
    n_antes = len(df)
    df = df.drop_duplicates(subset=clave_dedup)
    n_dup = n_antes - len(df)
    if n_dup > 0:
        logger.info("%s Duplicados eliminados: %d", prefijo_log, n_dup)

    # ── 11. Warning por municipio sin datos ───────────────────────────────────
    codigos_con_datos = set(df["codigo_dane"].unique())
    for codigo in codigos_objetivo:
        if codigo not in codigos_con_datos:
            nombre = DANE_TO_NAME.get(codigo, codigo)
            logger.warning("%s Sin datos para %s", prefijo_log, nombre)

    # ── 12. Validar que no quedó vacío ────────────────────────────────────────
    if df.empty:
        raise ValueError(f"EVA {fuente}: sin registros para el MVP")

    logger.info("%s Registros finales limpios: %d", prefijo_log, len(df))

    return df[_COLUMNAS_EVA].reset_index(drop=True)


# ── Funciones públicas ────────────────────────────────────────────────────────

def download_eva_historica(
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Descarga y limpia EVA histórica 2007-2018 (dataset 2pnw-mmge).

    Spec: D1.1

    Args:
        codigos_dane: Lista de códigos DANE a filtrar (5 dígitos con cero inicial).
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con esquema unificado del proyecto.
        Columnas: codigo_dane, municipio, departamento, cultivo,
                  año, periodo, rendimiento, area_sembrada,
                  area_cosechada, produccion, ciclo, fuente.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar todos los filtros.
        requests.RequestException: Si la API falla tras 3 reintentos.
    """
    codigos_objetivo = codigos_dane if codigos_dane is not None else MVP_CODIGOS

    dataset_id = DATASETS["eva_historica"]
    logger.info("[D1.1] Descargando EVA histórica (dataset %s)...", dataset_id)

    registros = fetch_all(dataset_id=dataset_id, where=_WHERE_HISTORICA)
    logger.info("[D1.1] Registros descargados de la API: %d", len(registros))

    if not registros:
        raise ValueError("EVA histórica: sin registros para el MVP")

    df = pd.DataFrame(registros)

    # Renombrar columnas al esquema unificado (nombres específicos de este dataset)
    df = df.rename(columns={
        "c_d_mun":          "codigo_dane",
        "a_o":              "año",
        "rendimiento_t_ha": "rendimiento",
        "rea_sembrada_ha":  "area_sembrada",
        "rea_cosechada_ha": "area_cosechada",
        "producci_n_t":     "produccion",
        "ciclo_de_cultivo": "ciclo",
    })

    return _limpiar_eva(df, codigos_objetivo, fuente="historica", prefijo_log="[D1.1]")


def download_eva_reciente(
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Descarga y limpia EVA reciente 2019-2024 (dataset uejq-wxrr).

    Spec: D1.2

    Args:
        codigos_dane: Lista de códigos DANE a filtrar (5 dígitos con cero inicial).
                      Si None, usa MVP_CODIGOS de shared/dane_codes.py.

    Returns:
        DataFrame con esquema unificado del proyecto.
        Columnas: codigo_dane, municipio, departamento, cultivo,
                  año, periodo, rendimiento, area_sembrada,
                  area_cosechada, produccion, ciclo, fuente.

    Raises:
        ValueError: Si el resultado está vacío tras aplicar todos los filtros.
        requests.RequestException: Si la API falla tras 3 reintentos.
    """
    codigos_objetivo = codigos_dane if codigos_dane is not None else MVP_CODIGOS

    dataset_id = DATASETS["eva_reciente"]
    logger.info("[D1.2] Descargando EVA reciente (dataset %s)...", dataset_id)

    registros = fetch_all(dataset_id=dataset_id, where=_WHERE_RECIENTE)
    logger.info("[D1.2] Registros descargados de la API: %d", len(registros))

    if not registros:
        raise ValueError("EVA reciente: sin registros para el MVP")

    df = pd.DataFrame(registros)

    # Renombrar columnas al esquema unificado (nombres específicos de este dataset)
    df = df.rename(columns={
        "c_digo_dane_municipio": "codigo_dane",
        "a_o":                   "año",
        # rendimiento ya se llama 'rendimiento' en este dataset
        "rea_sembrada":          "area_sembrada",
        "rea_cosechada":         "area_cosechada",
        "producci_n":            "produccion",
        "ciclo_del_cultivo":     "ciclo",
    })

    return _limpiar_eva(df, codigos_objetivo, fuente="reciente", prefijo_log="[D1.2]")


def run_pipeline(
    output_dir: Path = DATA_DIR,
    codigos_dane: list[str] | None = None,
) -> pd.DataFrame:
    """
    Ejecuta el pipeline completo EVA: descarga, limpia, unifica y guarda.

    Spec: D1.3

    Internamente llama a download_eva_historica() y download_eva_reciente(),
    luego ensambla y guarda los 3 archivos Parquet en output_dir.

    Args:
        output_dir: Directorio donde guardar los Parquet. Default: DATA_DIR.
        codigos_dane: Municipios a procesar. Si None, usa MVP_CODIGOS.

    Returns:
        eva_completa como DataFrame ordenado por (codigo_dane, cultivo, año, periodo).

    Raises:
        AssertionError: Si len(completa) != len(historica) + len(reciente).
        requests.RequestException: Si alguna descarga falla tras reintentos.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    codigos_objetivo = codigos_dane if codigos_dane is not None else MVP_CODIGOS

    # ── Descarga ──────────────────────────────────────────────────────────────
    df_historica = download_eva_historica(codigos_dane=codigos_objetivo)
    df_reciente = download_eva_reciente(codigos_dane=codigos_objetivo)

    # ── 1. Verificar que ninguno esté vacío ───────────────────────────────────
    if df_historica.empty:
        logger.warning("[D1.3] df_historica está vacío — revisar D1.1")
    if df_reciente.empty:
        logger.warning("[D1.3] df_reciente está vacío — revisar D1.2")

    # ── 2. Verificar solapamiento de años entre fuentes ───────────────────────
    if not df_historica.empty and not df_reciente.empty:
        max_hist = int(df_historica["año"].max())
        min_rec = int(df_reciente["año"].min())

        if max_hist > 2018:
            años_extra = sorted(df_historica[df_historica["año"] > 2018]["año"].unique().tolist())
            logger.warning("[D1.3] EVA histórica contiene años > 2018: %s", años_extra)

        if min_rec < 2019:
            años_extra = sorted(df_reciente[df_reciente["año"] < 2019]["año"].unique().tolist())
            logger.warning("[D1.3] EVA reciente contiene años < 2019: %s", años_extra)

        if max_hist >= min_rec:
            logger.warning(
                "[D1.3] Posible solapamiento de años: histórica llega a %d, reciente empieza en %d",
                max_hist, min_rec,
            )

    # ── Validaciones de consistencia entre fuentes (advertencias) ─────────────
    if not df_historica.empty and not df_reciente.empty:
        muns_hist = set(df_historica["codigo_dane"].unique())
        muns_rec = set(df_reciente["codigo_dane"].unique())
        solo_hist = muns_hist - muns_rec
        solo_rec = muns_rec - muns_hist
        if solo_hist:
            nombres = [DANE_TO_NAME.get(c, c) for c in solo_hist]
            logger.warning("[D1.3] Municipios solo en histórica: %s", nombres)
        if solo_rec:
            nombres = [DANE_TO_NAME.get(c, c) for c in solo_rec]
            logger.warning("[D1.3] Municipios solo en reciente: %s", nombres)

        cults_hist = set(df_historica["cultivo"].unique())
        cults_rec = set(df_reciente["cultivo"].unique())
        if cults_hist != cults_rec:
            logger.warning(
                "[D1.3] Cultivos difieren entre fuentes — histórica: %s | reciente: %s",
                sorted(cults_hist), sorted(cults_rec),
            )

    # ── 3 & 4. Guardar histórica y reciente ───────────────────────────────────
    path_hist = output_dir / "eva_historica.parquet"
    path_rec = output_dir / "eva_reciente.parquet"
    path_comp = output_dir / "eva_completa.parquet"

    df_historica.to_parquet(path_hist, index=False, engine="pyarrow")
    logger.info("[D1.3] Guardado: %s", path_hist)

    df_reciente.to_parquet(path_rec, index=False, engine="pyarrow")
    logger.info("[D1.3] Guardado: %s", path_rec)

    # ── 5 & 6. Concatenar y ordenar ───────────────────────────────────────────
    df_completa = pd.concat([df_historica, df_reciente], ignore_index=True)
    df_completa = df_completa.sort_values(
        ["codigo_dane", "cultivo", "año", "periodo"]
    ).reset_index(drop=True)

    # ── 7. Verificar integridad ───────────────────────────────────────────────
    n_esperado = len(df_historica) + len(df_reciente)
    n_real = len(df_completa)
    if n_real != n_esperado:
        raise AssertionError(
            f"[D1.3] Integridad fallida: esperado {n_esperado} registros, "
            f"obtenido {n_real} tras concat"
        )

    # ── 8. Guardar completa ───────────────────────────────────────────────────
    df_completa.to_parquet(path_comp, index=False, engine="pyarrow")
    logger.info("[D1.3] Guardado: %s", path_comp)

    # ── 9. Resumen de ejecución ───────────────────────────────────────────────
    def _cobertura(df: pd.DataFrame) -> str:
        n_muns = df["codigo_dane"].nunique()
        return f"{n_muns}/15 municipios"

    def _rango_años(df: pd.DataFrame) -> str:
        return f"años {int(df['año'].min())}-{int(df['año'].max())}"

    n_rend_nulos = int(df_completa["rendimiento"].isna().sum())
    pct_nulos = n_rend_nulos / len(df_completa) * 100 if len(df_completa) > 0 else 0.0

    # Municipios sin datos en alguna fuente
    muns_sin_datos: list[str] = []
    for codigo in codigos_objetivo:
        en_hist = not df_historica.empty and codigo in df_historica["codigo_dane"].values
        en_rec = not df_reciente.empty and codigo in df_reciente["codigo_dane"].values
        if not en_hist or not en_rec:
            muns_sin_datos.append(DANE_TO_NAME.get(codigo, codigo))

    resumen_cultivos = []
    for cultivo in sorted(df_completa["cultivo"].unique()):
        sub = df_completa[df_completa["cultivo"] == cultivo]
        rend_medio = sub["rendimiento"].mean()
        rend_str = f"{rend_medio:.2f} t/ha" if not pd.isna(rend_medio) else "N/D"
        resumen_cultivos.append(
            f"  {cultivo:<8} {len(sub):>6} registros | rendimiento medio: {rend_str}"
        )

    logger.info(
        "\n=== Resumen Pipeline EVA ===\n"
        "EVA histórica: %6d registros | %s | %s\n"
        "EVA reciente:  %6d registros | %s | %s\n"
        "EVA completa:  %6d registros | %s\n"
        "\nPor cultivo (completa):\n%s\n"
        "\nMunicipios sin datos en alguna fuente: %s\n"
        "Registros con rendimiento=None: %d (%.1f%%)\n"
        "Archivos guardados:\n  %s\n  %s\n  %s",
        len(df_historica), _rango_años(df_historica), _cobertura(df_historica),
        len(df_reciente), _rango_años(df_reciente), _cobertura(df_reciente),
        len(df_completa), _rango_años(df_completa),
        "\n".join(resumen_cultivos),
        ", ".join(muns_sin_datos) if muns_sin_datos else "ninguno",
        n_rend_nulos, pct_nulos,
        path_hist, path_rec, path_comp,
    )

    return df_completa


def load_eva_completa(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """
    Carga eva_completa.parquet desde disco.

    Args:
        data_dir: Directorio donde buscar el archivo. Default: DATA_DIR.

    Returns:
        DataFrame con el esquema unificado EVA.

    Raises:
        FileNotFoundError: Si el archivo no existe (ejecutar run_pipeline primero).
    """
    path = Path(data_dir) / "eva_completa.parquet"
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró {path}. Ejecutar run_pipeline() primero."
        )
    df = pd.read_parquet(path, engine="pyarrow")
    logger.info("[D1.3] Cargado %s (%d registros)", path, len(df))
    return df


# ── Punto de entrada como script ─────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
    )
    run_pipeline()
    sys.exit(0)
