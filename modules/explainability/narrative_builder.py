import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)

# Configuraciones de salida
DATA_DIR = Path("data")  # Idealmente importaría desde shared.config pero esto es independiente de la doc real
PREDICCIONES_FILE = DATA_DIR / "predicciones_con_explicacion.parquet"

def format_value(val) -> str:
    """Format original value to a legible string without failing in type matching."""
    if val is None or pd.isna(val):
        return "N/A"
    if isinstance(val, (int, float)):
        # Format floating numbers keeping max 2 decimal places to be legible
        return f"{val:.2f}".rstrip("0").rstrip(".") if isinstance(val, float) else f"{val}"
    return str(val)

def build_narrative(prediccion_riesgo: str, top_features: list[dict]) -> str:
    """
    Convert the list of top features into a brief summary of the prediction scenario.
    
    Args:
        prediccion_riesgo: The classified risk level (e.g., Alto, Medio, Bajo).
        top_features: JSON-like list of the most influential factors extracted via SHAP.
        
    Returns:
        str: A human-readable narrative.
    """
    try:
        prediccion_str = str(prediccion_riesgo).lower()
        if not top_features:
            return f"El modelo ha asignado un nivel de riesgo {prediccion_str} basándose en su perfil base sin identificar factores atípicos puntuales."
            
        # Separar en agravantes y mitigantes respetando el orden original (el original ya viene ordenado por impacto absoluto)
        agravantes = [f for f in top_features if f["direccion"] == "Aumenta riesgo"]
        mitigantes = [f for f in top_features if f["direccion"] == "Disminuye riesgo"]
        
        # Limitar a top 3
        agravantes = agravantes[:3]
        mitigantes = mitigantes[:3]
        
        narrativa = f"El riesgo pronosticado es {prediccion_str}."
        
        if agravantes:
            motivos = [f"{f['nombre_amigable']} (valor: {format_value(f.get('valor_original'))})" for f in agravantes]
            narrativa += f" Los principales factores que elevan este riesgo son: {', '.join(motivos)}."
            
        if mitigantes:
            motivos = [f"{f['nombre_amigable']} (valor: {format_value(f.get('valor_original'))})" for f in mitigantes]
            narrativa += f" Por otro lado, los factores que ayudan a disminuirlo son: {', '.join(motivos)}."

        return narrativa
        
    except Exception as e:
        logger.error(f"Error generando narrativa: {e}")
        # Retornar fallback genérico
        return f"El riesgo pronosticado es {str(prediccion_riesgo).lower()}. (Explicación detallada no disponible)"


def build_and_save_narratives_df(df_base: pd.DataFrame, top_features_col: pd.Series) -> pd.DataFrame:
    """
    Generate narratives for all elements into a DataFrame and persist it.
    
    Args:
        df_base: Base dataframe to which the narrative will be appended. MUST contain a 'riesgo' column or similar.
                 Assumption: 'prediccion_riesgo' column stores the current risk categorization.
        top_features_col: A pandas Series containing the top_features lists.
        
    Returns:
        pd.DataFrame: A dataFrame appending the 'narrativa_riesgo' feature.
    """
    # Create copy to not mutate original reference
    df_result = df_base.copy()
    
    # Check what the risk column is named, fallback to 'riesgo' if 'prediccion_riesgo' missing
    risk_col = 'prediccion_riesgo' if 'prediccion_riesgo' in df_result.columns else 'riesgo'
    if risk_col not in df_result.columns:
        # Provide fallback to be safe
        df_result[risk_col] = 'Desconocido'
        
    # Generate narrative
    narrativas = []
    
    # We zip base target & features ignoring indices safely 
    for risk_val, feat_list in zip(df_result[risk_col], top_features_col):
        val = feat_list if isinstance(feat_list, list) else [] # Enforce list behavior just in case
        narrativas.append(build_narrative(risk_val, val))
        
    df_result["narrativa_riesgo"] = narrativas
    
    # Save parquet to ensure availability to NEXT module/frontend
    # Note: Requires fastparquet or pyarrow installed environment.
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    df_result.to_parquet(PREDICCIONES_FILE, index=False)
    logger.info(f"Narrativas generadas y persistidas en {PREDICCIONES_FILE}")
    
    return df_result
