"""
Módulo de recuperación de contexto (RAG) para el asistente conversacional.
Recupera información de predicciones, narrativas SHAP y glosario agrícola.
"""
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import pandas as pd

from shared.config import DATA_DIR, MODELS_DIR
from shared.dane_codes import DANE_TO_NAME, get_codigo, MVP_CODIGOS
from shared.normalization import normalize_dane_code, normalize_cultivo

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# C1.1 — Índice RAG en memoria
# ---------------------------------------------------------------------------

@dataclass
class RagDocument:
    """Representa un documento del corpus RAG (una fila del Parquet)."""
    codigo_dane: str
    municipio: str
    departamento: str
    cultivo: str
    año: int
    prediccion_riesgo: Optional[str]
    narrativa_riesgo: Optional[str]
    top_features: list          # lista de dicts [{feature, valor, importancia}]
    rendimiento_t1: Optional[float]
    rendimiento_prom3a: Optional[float]
    tendencia_rend_3a: Optional[float]
    prec_acum_mm: Optional[float]
    anomalia_prec: Optional[float]
    temp_media_c: Optional[float]
    anomalia_temp: Optional[float]
    dias_secos: Optional[float]
    hum_media_pct: Optional[float]
    pct_alta: Optional[float]
    pct_media: Optional[float]
    pct_baja: Optional[float]
    pct_exclusion: Optional[float]
    pct_condicionada: Optional[float]
    pct_no_condicionada: Optional[float]
    indice_agroinsumos: Optional[float]
    percentil_fertilizantes: Optional[float]
    señal_riesgo_economico: Optional[str]
    target_rendimiento: Optional[float]
    area_sembrada_t1: Optional[float]


class RagIndex:
    """Índice en memoria del corpus RAG, agrupado por (codigo_dane, cultivo)."""

    def __init__(self, documents: dict):
        # documents: {(codigo_dane, cultivo): [RagDocument, ...]}
        self._index: dict[tuple[str, str], list[RagDocument]] = documents

    @property
    def total_documents(self) -> int:
        return sum(len(v) for v in self._index.values())

    @property
    def keys(self) -> list:
        return list(self._index.keys())

    def get(self, codigo_dane: str, cultivo: str) -> list:
        return self._index.get((codigo_dane, cultivo), [])


# Instancia global lazy
_rag_index: Optional[RagIndex] = None


def _safe_float(value) -> Optional[float]:
    """Convierte un valor a float, retorna None si no es posible."""
    if value is None:
        return None
    try:
        f = float(value)
        return None if pd.isna(f) else f
    except (TypeError, ValueError):
        return None


def _safe_str(value) -> Optional[str]:
    """Convierte un valor a str, retorna None si es NaN/None."""
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def build_rag_index(path: Optional[Path] = None) -> RagIndex:
    """
    Carga el corpus y construye el índice RAG en memoria.

    Args:
        path: Ruta al Parquet. Si es None, usa DATA_DIR / "predicciones_con_explicacion.parquet".

    Returns:
        RagIndex con todos los documentos indexados por (codigo_dane, cultivo).

    Raises:
        FileNotFoundError: Si el archivo no existe.
        ValueError: Si el corpus está vacío o no tiene columnas requeridas.
    """
    if path is None:
        path = DATA_DIR / "predicciones_con_explicacion.parquet"

    if not path.exists():
        raise FileNotFoundError(
            f"[C1.1] No se encontró predicciones_con_explicacion.parquet: {path}"
        )

    try:
        df = pd.read_parquet(path)
    except Exception as e:
        logger.error(f"[C1.1] Error construyendo índice RAG: {e}")
        raise

    if df.empty:
        raise ValueError(
            "[C1.1] Corpus vacío: predicciones_con_explicacion.parquet no tiene registros"
        )

    # Validar columnas mínimas requeridas
    cols_requeridas = {"codigo_dane", "cultivo", "año"}
    cols_faltantes = cols_requeridas - set(df.columns)
    if cols_faltantes:
        raise ValueError(f"[C1.1] Columnas faltantes en el corpus: {cols_faltantes}")

    index: dict[tuple[str, str], list[RagDocument]] = {}
    filas_descartadas = 0

    for _, row in df.iterrows():
        # --- Normalizar codigo_dane ---
        raw_code = str(row.get("codigo_dane", ""))
        codigo_norm = normalize_dane_code(raw_code)
        if not codigo_norm or len(codigo_norm) != 5:
            logger.warning(f"[C1.1] codigo_dane no normalizable: {raw_code!r}")
            filas_descartadas += 1
            continue

        # --- Normalizar cultivo ---
        raw_cultivo = row.get("cultivo", "")
        cultivo_norm = normalize_cultivo(str(raw_cultivo) if raw_cultivo is not None else "")
        if cultivo_norm is None:
            logger.warning(f"[C1.1] Cultivo no reconocido descartado: {raw_cultivo!r}")
            filas_descartadas += 1
            continue

        # --- Parsear top_features ---
        raw_tf = row.get("top_features")
        top_features: list = []
        if raw_tf is not None:
            try:
                if isinstance(raw_tf, str):
                    top_features = json.loads(raw_tf)
                elif isinstance(raw_tf, list):
                    top_features = raw_tf
            except (json.JSONDecodeError, TypeError):
                año_val = row.get("año", "?")
                logger.warning(
                    f"[C1.1] top_features no parseable para {codigo_norm}/{cultivo_norm}/{año_val}"
                )
                top_features = []

        # --- Construir RagDocument ---
        doc = RagDocument(
            codigo_dane=codigo_norm,
            municipio=_safe_str(row.get("municipio")) or "",
            departamento=_safe_str(row.get("departamento")) or "",
            cultivo=cultivo_norm,
            año=int(row["año"]) if pd.notna(row.get("año")) else 0,
            prediccion_riesgo=_safe_str(row.get("prediccion_riesgo")),
            narrativa_riesgo=_safe_str(row.get("narrativa_riesgo")),
            top_features=top_features,
            rendimiento_t1=_safe_float(row.get("rendimiento_t1")),
            rendimiento_prom3a=_safe_float(row.get("rendimiento_prom3a")),
            tendencia_rend_3a=_safe_float(row.get("tendencia_rend_3a")),
            prec_acum_mm=_safe_float(row.get("prec_acum_mm")),
            anomalia_prec=_safe_float(row.get("anomalia_prec")),
            temp_media_c=_safe_float(row.get("temp_media_c")),
            anomalia_temp=_safe_float(row.get("anomalia_temp")),
            dias_secos=_safe_float(row.get("dias_secos")),
            hum_media_pct=_safe_float(row.get("hum_media_pct")),
            pct_alta=_safe_float(row.get("pct_alta")),
            pct_media=_safe_float(row.get("pct_media")),
            pct_baja=_safe_float(row.get("pct_baja")),
            pct_exclusion=_safe_float(row.get("pct_exclusion")),
            pct_condicionada=_safe_float(row.get("pct_condicionada")),
            pct_no_condicionada=_safe_float(row.get("pct_no_condicionada")),
            indice_agroinsumos=_safe_float(row.get("indice_agroinsumos")),
            percentil_fertilizantes=_safe_float(row.get("percentil_fertilizantes")),
            señal_riesgo_economico=_safe_str(row.get("señal_riesgo_economico")),
            target_rendimiento=_safe_float(row.get("target_rendimiento")),
            area_sembrada_t1=_safe_float(row.get("area_sembrada_t1")),
        )

        key = (codigo_norm, cultivo_norm)
        if key not in index:
            index[key] = []
        index[key].append(doc)

    rag_index = RagIndex(index)
    logger.info(
        f"[C1.1] Índice RAG construido: {rag_index.total_documents} documentos, "
        f"{len(rag_index.keys)} claves (codigo_dane, cultivo), "
        f"{filas_descartadas} filas descartadas"
    )
    return rag_index


def get_rag_index() -> RagIndex:
    """Retorna la instancia global del índice RAG (lazy singleton)."""
    global _rag_index
    if _rag_index is None:
        _rag_index = build_rag_index()
    return _rag_index

# Mapeo de features técnicas a nombres amigables
FEATURE_MAPPING = {
    # Variables climáticas
    "prec_acum_mm": "Precipitación acumulada",
    "temp_media_c": "Temperatura media",
    "hum_media_pct": "Humedad relativa",
    "anomalia_prec": "Anomalía de precipitación",
    "anomalia_temp": "Anomalía de temperatura",
    "dias_secos": "Días secos consecutivos",
    "prec_dias_secos": "Días secos",
    "prec_dias_lluvia": "Días de lluvia",
    
    # Variables de rendimiento histórico
    "rendimiento_t1": "Rendimiento año anterior",
    "rendimiento_prom3a": "Promedio 3 años",
    "tendencia_3a": "Tendencia rendimiento",
    "tendencia_rend_3a": "Tendencia rendimiento 3 años",
    "area_sembrada_t1": "Área sembrada año anterior",
    
    # Variables de aptitud
    "pct_alta": "Aptitud alta",
    "pct_media": "Aptitud media",
    "pct_baja": "Aptitud baja",
    "pct_exclusion": "Área de exclusión",
    
    # Variables de frontera
    "pct_condicionada": "Frontera condicionada",
    "pct_no_condicionada": "Frontera no condicionada",
    
    # Variables de agroinsumos
    "indice_total": "Índice de agroinsumos",
    "indice_agroinsumos": "Índice de agroinsumos",
    "percentil_fertilizantes": "Percentil fertilizantes",
    "fertilizantes": "Precio fertilizantes",
    "plaguicidas": "Precio plaguicidas",
    "señal_riesgo": "Señal de riesgo económico",
    "señal_riesgo_economico": "Señal de riesgo económico",
    "señal_riesgo_economico_encoded": "Señal de riesgo económico",
    
    # Variables de área
    "area_sembrada": "Área sembrada",
    "area_cosechada": "Área cosechada",
    
    # Otras
    "año": "Año",
}


class ContextoRecuperado:
    """Contenedor para el contexto recuperado de múltiples fuentes."""
    
    def __init__(self):
        self.prediccion: Optional[dict] = None
        self.narrativa: Optional[str] = None
        self.top_features: Optional[list] = None
        self.serie_historica: Optional[list] = None
        self.fuentes: list[str] = []
        self.contexto_efectivo: dict = {}
    
    def to_dict(self) -> dict:
        return {
            "prediccion": self.prediccion,
            "narrativa": self.narrativa,
            "top_features": self.top_features,
            "serie_historica": self.serie_historica,
            "fuentes": self.fuentes,
            "contexto_efectivo": self.contexto_efectivo
        }


def load_predicciones_con_explicacion() -> Optional[pd.DataFrame]:
    """
    Carga el archivo de predicciones con explicación SHAP.
    
    Returns:
        DataFrame con predicciones o None si no existe
    """
    path = DATA_DIR / "predicciones_con_explicacion.parquet"
    if not path.exists():
        logger.warning(f"Archivo de predicciones no encontrado: {path}")
        return None
    
    try:
        df = pd.read_parquet(path)
        logger.info(f"Predicciones cargadas: {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Error cargando predicciones: {e}")
        return None


def load_feature_matrix() -> Optional[pd.DataFrame]:
    """
    Carga la matriz de features para recuperar series históricas.
    
    Returns:
        DataFrame con features o None si no existe
    """
    path = DATA_DIR / "feature_matrix.parquet"
    if not path.exists():
        logger.warning(f"Feature matrix no encontrada: {path}")
        return None
    
    try:
        df = pd.read_parquet(path)
        logger.info(f"Feature matrix cargada: {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Error cargando feature matrix: {e}")
        return None


def load_glosario() -> str:
    """
    Carga el glosario agrícola como texto plano.
    
    Returns:
        str: Contenido del glosario o string vacío si no existe
    """
    path = Path("docs/dominio/glosario_agricola.md")
    if not path.exists():
        logger.warning(f"Glosario no encontrado: {path}")
        return ""
    
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        logger.error(f"Error cargando glosario: {e}")
        return ""


# ---------------------------------------------------------------------------
# C1.2 — Función de recuperación por municipio/cultivo
# ---------------------------------------------------------------------------

def _score_document(doc: RagDocument, año: Optional[int]) -> float:
    """
    Calcula la relevancia de un documento dado el año de referencia.

    Reglas de scoring:
    - año is None  → score = doc.año  (priorizar el más reciente)
    - año == doc.año → score = 1000   (coincidencia exacta)
    - año > doc.año  → score = 1000 - (año - doc.año)  (penalizar por distancia pasada)
    - año < doc.año  → score = 500  - (doc.año - año)  (penalizar más por ser futuro)

    Args:
        doc: Documento del índice RAG.
        año: Año de referencia de la consulta. None = priorizar más reciente.

    Returns:
        float: Score de relevancia. Mayor es más relevante.
    """
    if año is None:
        return float(doc.año)
    if año == doc.año:
        return 1000.0
    if año > doc.año:
        return 1000.0 - (año - doc.año)
    # año < doc.año  (documento más reciente que lo solicitado)
    return 500.0 - (doc.año - año)


def recuperar_contexto(
    municipio: Optional[str] = None,
    cultivo: Optional[str] = None,
    año: Optional[int] = None,
    escenario: Optional[str] = None,
    tono: str = "campesino"
) -> ContextoRecuperado:
    """
    Recupera contexto del índice RAG para alimentar el LLM.

    Usa get_rag_index() en lugar de leer el Parquet en cada llamada.
    La firma pública es idéntica a la versión anterior para no romper chat_engine.py.

    Args:
        municipio: Nombre display o código DANE del municipio.
        cultivo: Nombre del cultivo (Café, Cacao, Maíz).
        año: Año de referencia para el scoring de documentos.
        escenario: Escenario de simulación (informativo, no afecta recuperación).
        tono: Tono de la respuesta (informativo, no afecta recuperación).

    Returns:
        ContextoRecuperado con predicción, narrativa, top_features y fuentes.
        Retorna ContextoRecuperado vacío si no hay contexto suficiente o no hay coincidencia.
    """
    resultado = ContextoRecuperado()

    # --- 1. Normalizar municipio ---
    codigo_norm: Optional[str] = None
    municipio_display: Optional[str] = None

    if municipio:
        raw = str(municipio).strip()
        if raw.isdigit():
            codigo_norm = normalize_dane_code(raw)
        else:
            codigo_norm = get_codigo(raw)

        if codigo_norm and codigo_norm in DANE_TO_NAME:
            municipio_display = DANE_TO_NAME[codigo_norm]
        else:
            logger.warning(f"[C1.2] Municipio no reconocido: {municipio!r}")
            return resultado

    # --- 2. Normalizar cultivo ---
    cultivo_norm: Optional[str] = None
    if cultivo:
        cultivo_norm = normalize_cultivo(cultivo)
        if cultivo_norm is None:
            logger.warning(f"[C1.2] Cultivo no reconocido: {cultivo!r}")
            return resultado

    # Registrar contexto efectivo (siempre, incluso si vacío)
    resultado.contexto_efectivo = {
        "municipio": municipio_display,
        "cultivo": cultivo_norm,
        "año": año,
        "escenario": escenario,
    }

    # Sin municipio ni cultivo no hay nada que recuperar
    if not municipio and not cultivo:
        logger.info("[C1.2] Sin contexto específico, no se recuperan predicciones")
        return resultado

    # --- 3. Recuperar del índice RAG ---
    if codigo_norm and cultivo_norm:
        try:
            index = get_rag_index()
        except Exception as e:
            logger.error(f"[C1.2] Índice RAG no disponible: {e}")
            return resultado

        candidatos = index.get(codigo_norm, cultivo_norm)

        if not candidatos:
            logger.warning(f"[C1.2] Sin documentos para {municipio_display}/{cultivo_norm}")
        else:
            # --- 4. Seleccionar el documento con mayor score ---
            doc = max(candidatos, key=lambda d: _score_document(d, año))

            # --- 5. Construir ContextoRecuperado desde el documento ---
            resultado.prediccion = {
                "rendimiento_esperado": doc.rendimiento_t1,
                "etiqueta_riesgo": doc.prediccion_riesgo,
            }
            resultado.fuentes.append("predicciones_con_explicacion.parquet")

            if doc.narrativa_riesgo is not None:
                resultado.narrativa = doc.narrativa_riesgo
                resultado.fuentes.append("narrativa_riesgo")

            if doc.top_features:
                resultado.top_features = doc.top_features
                resultado.fuentes.append("top_features_shap")

    # --- 6. Serie histórica desde feature_matrix (lógica existente, sin cambios) ---
    df_features = load_feature_matrix()

    if df_features is not None and codigo_norm and cultivo_norm:
        df_features["codigo_dane"] = df_features["codigo_dane"].astype(str).str.zfill(5)

        filtro = df_features["codigo_dane"] == codigo_norm
        if "cultivo" in df_features.columns:
            filtro = filtro & (df_features["cultivo"] == cultivo_norm)

        df_hist = df_features[filtro].copy()

        if not df_hist.empty and "año" in df_hist.columns:
            df_hist = df_hist.sort_values("año", ascending=True)

            resultado.serie_historica = []
            for _, r in df_hist.tail(5).iterrows():
                rend_val = r.get("rendimiento")
                if rend_val is None or (isinstance(rend_val, float) and pd.isna(rend_val)):
                    rend_val = r.get("rendimiento_t1")
                resultado.serie_historica.append({
                    "año": int(r["año"]) if pd.notna(r.get("año")) else None,
                    "rendimiento": float(rend_val) if rend_val is not None and pd.notna(rend_val) else None,
                })

            if resultado.serie_historica:
                resultado.fuentes.append("feature_matrix.parquet")

    return resultado


def extraer_terminos_glosario(glosario: str, pregunta: str, max_terminos: int = 3) -> str:
    """
    Extrae términos relevantes del glosario basándose en la pregunta.
    
    Args:
        glosario: Texto completo del glosario
        pregunta: Pregunta del usuario
        max_terminos: Máximo número de términos a extraer
        
    Returns:
        str: Términos relevantes formateados
    """
    if not glosario or not pregunta:
        return ""
    
    pregunta_lower = pregunta.lower()
    
    # Palabras clave para detectar temas
    keywords = {
        "rendimiento": "### Rendimiento",
        "producción": "### Producción",
        "produccion": "### Producción",
        "área": "### Área sembrada",
        "area": "### Área sembrada",
        "clima": "## Conceptos climáticos",
        "lluvia": "### Anomalía climática",
        "precipitación": "### Anomalía climática",
        "temperatura": "### Estrés térmico",
        "riesgo": "### Semáforo de riesgo",
        "aptitud": "### Aptitud agroecológica",
        "café": "### Café",
        "cafe": "### Café",
        "cacao": "### Cacao",
        "maíz": "### Maíz",
        "maiz": "### Maíz",
        "umata": "### UMATA",
        "extensionista": "### Extensionista",
        "niño": "### Fenómeno El Niño",
        "niña": "### Fenómeno El Niño",
    }
    
    terminos = []
    for keyword, seccion in keywords.items():
        if keyword in pregunta_lower:
            # Buscar la sección en el glosario
            idx = glosario.find(seccion)
            if idx >= 0:
                # Extraer hasta el siguiente encabezado
                end_idx = glosario.find("\n##", idx + 1)
                if end_idx == -1:
                    end_idx = glosario.find("\n###", idx + 1)
                if end_idx == -1:
                    end_idx = min(idx + 500, len(glosario))
                
                texto = glosario[idx:end_idx].strip()
                terminos.append(texto)
                
                if len(terminos) >= max_terminos:
                    break
    
    return "\n\n---\n\n".join(terminos) if terminos else ""


def get_feature_mapping() -> dict:
    """
    Retorna el mapeo de features técnicas a nombres amigables.
    
    Returns:
        dict: Mapeo feature_id -> nombre_amigable
    """
    return FEATURE_MAPPING.copy()
