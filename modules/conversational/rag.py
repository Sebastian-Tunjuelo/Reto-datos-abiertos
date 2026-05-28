"""
Módulo de recuperación de contexto (RAG) para el asistente conversacional.
Recupera información de predicciones, narrativas SHAP y glosario agrícola.
"""
import logging
from pathlib import Path
from typing import Optional
import pandas as pd

from shared.config import DATA_DIR, MODELS_DIR
from shared.dane_codes import DANE_TO_NAME, get_codigo
from shared.normalization import normalize_dane_code, normalize_cultivo

logger = logging.getLogger(__name__)

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


def recuperar_contexto(
    municipio: Optional[str] = None,
    cultivo: Optional[str] = None,
    año: Optional[int] = None,
    escenario: Optional[str] = None,
    tono: str = "campesino"
) -> ContextoRecuperado:
    """
    Recupera contexto de múltiples fuentes para alimentar el LLM.
    
    Args:
        municipio: Nombre o código DANE del municipio
        cultivo: Nombre del cultivo (Café, Cacao, Maíz)
        año: Año de referencia
        escenario: Escenario de simulación (base, seco, lluvioso, fertilizantes)
        tono: Tono de la respuesta (campesino o institucional)
        
    Returns:
        ContextoRecuperado: Objeto con toda la información recuperada
    """
    resultado = ContextoRecuperado()
    
    # Normalizar municipio
    codigo_norm = None
    municipio_display = None
    
    if municipio:
        if str(municipio).isdigit():
            codigo_norm = normalize_dane_code(municipio)
        else:
            codigo_norm = get_codigo(municipio)
        
        if codigo_norm and codigo_norm in DANE_TO_NAME:
            municipio_display = DANE_TO_NAME[codigo_norm]
        else:
            logger.warning(f"Municipio no reconocido: {municipio}")
            return resultado
    
    # Normalizar cultivo
    cultivo_norm = None
    if cultivo:
        cultivo_norm = normalize_cultivo(cultivo)
    
    # Registrar contexto efectivo
    resultado.contexto_efectivo = {
        "municipio": municipio_display,
        "cultivo": cultivo_norm,
        "año": año,
        "escenario": escenario
    }
    
    # Si no hay contexto suficiente, retornar vacío
    if not municipio and not cultivo:
        logger.info("Sin contexto específico, no se recuperan predicciones")
        return resultado
    
    # Intentar cargar predicciones con explicación
    df_pred = load_predicciones_con_explicacion()
    
    if df_pred is not None and codigo_norm and cultivo_norm:
        # Filtrar por municipio y cultivo
        df_pred["codigo_dane"] = df_pred["codigo_dane"].astype(str).str.zfill(5)
        
        filtro = (df_pred["codigo_dane"] == codigo_norm)
        if "cultivo" in df_pred.columns:
            filtro = filtro & (df_pred["cultivo"] == cultivo_norm)
        
        df_filtrado = df_pred[filtro]
        
        if not df_filtrado.empty:
            # Tomar el registro más reciente
            if "año" in df_filtrado.columns:
                df_filtrado = df_filtrado.sort_values("año", ascending=False)
            
            row = df_filtrado.iloc[0]
            
            # Extraer predicción — columnas reales del parquet
            def _safe_get(r, *keys):
                for k in keys:
                    v = r.get(k)
                    if v is not None and not (isinstance(v, float) and pd.isna(v)):
                        return v
                return None

            resultado.prediccion = {
                "rendimiento_esperado": _safe_get(row, "rendimiento_esperado", "rendimiento_predicho", "rendimiento_t1"),
                "prob_riesgo_alto": _safe_get(row, "prob_riesgo_alto", "prob_riesgo"),
                "etiqueta_riesgo": _safe_get(row, "etiqueta_riesgo", "prediccion_riesgo", "riesgo")
            }
            resultado.fuentes.append("predicciones_con_explicacion.parquet")

            # Extraer narrativa
            narrativa_val = row.get("narrativa_riesgo")
            if narrativa_val is not None:
                try:
                    if pd.notna(narrativa_val):
                        resultado.narrativa = str(narrativa_val)
                        resultado.fuentes.append("narrativa_riesgo")
                except (TypeError, ValueError):
                    pass

            # Extraer top features si existen
            top_val = row.get("top_features")
            if top_val is not None:
                try:
                    import json
                    if isinstance(top_val, str):
                        resultado.top_features = json.loads(top_val)
                    elif isinstance(top_val, list):
                        resultado.top_features = top_val
                    if resultado.top_features:
                        resultado.fuentes.append("top_features_shap")
                except Exception as e:
                    logger.warning(f"Error parseando top_features: {e}")
    
    # Intentar cargar serie histórica de feature_matrix
    df_features = load_feature_matrix()
    
    if df_features is not None and codigo_norm and cultivo_norm:
        df_features["codigo_dane"] = df_features["codigo_dane"].astype(str).str.zfill(5)
        
        filtro = (df_features["codigo_dane"] == codigo_norm)
        if "cultivo" in df_features.columns:
            filtro = filtro & (df_features["cultivo"] == cultivo_norm)
        
        df_hist = df_features[filtro].copy()
        
        if not df_hist.empty and "año" in df_hist.columns:
            df_hist = df_hist.sort_values("año", ascending=True)
            
            # Extraer últimos 5 años de rendimiento
            resultado.serie_historica = []
            for _, r in df_hist.tail(5).iterrows():
                rend_val = r.get("rendimiento") if pd.notna(r.get("rendimiento")) else r.get("rendimiento_t1")
                resultado.serie_historica.append({
                    "año": int(r["año"]) if pd.notna(r.get("año")) else None,
                    "rendimiento": float(rend_val) if rend_val is not None and pd.notna(rend_val) else None
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
