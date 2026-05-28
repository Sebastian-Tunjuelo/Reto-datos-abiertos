"""
Pipeline M4: Explicabilidad SHAP y Narrativas.

Ejecuta:
1. Cálculo de explainers SHAP por cultivo
2. Extracción de top features
3. Generación de narrativas
4. Persiste predicciones_con_explicacion.parquet
"""
import sys
import json
import pickle
import logging
from pathlib import Path

import numpy as np
import pandas as pd
import shap

# Añadir raíz del proyecto al path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from shared.config import CULTIVOS_MVP, DATA_DIR, MODELS_DIR
from modules.explainability.shap_calculator import build_and_save_explainers
from modules.explainability.feature_extractor import get_top_n_features
from modules.explainability.narrative_builder import build_and_save_narratives_df

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

FEATURE_MATRIX_PATH = DATA_DIR / "feature_matrix.parquet"
OUTPUT_PATH = DATA_DIR / "predicciones_con_explicacion.parquet"

# Mapeo de features a nombres amigables
FEATURE_MAPPING = {
    # Variables climáticas
    "prec_acum_mm": "Precipitación acumulada",
    "temp_media_c": "Temperatura media",
    "hum_media_pct": "Humedad relativa",
    "anomalia_prec": "Anomalía de precipitación",
    "anomalia_temp": "Anomalía de temperatura",
    "dias_secos": "Días secos",
    "prec_dias_secos": "Días secos",
    "prec_dias_lluvia": "Días de lluvia",
    
    # Variables de rendimiento
    "rendimiento_t1": "Rendimiento año anterior",
    "rendimiento_prom3a": "Promedio 3 años",
    "tendencia_3a": "Tendencia",
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
    "indice_total": "Índice agroinsumos",
    "indice_agroinsumos": "Índice agroinsumos",
    "percentil_fertilizantes": "Percentil fertilizantes",
    "fertilizantes": "Precio fertilizantes",
    "plaguicidas": "Precio plaguicidas",
    "señal_riesgo": "Señal de riesgo",
    "señal_riesgo_economico": "Señal de riesgo económico",
    "señal_riesgo_economico_encoded": "Señal de riesgo económico",
    
    # Variables de área
    "area_sembrada": "Área sembrada",
    
    # Otras
    "año": "Año",
}


def load_classifier_and_meta(cultivo: str):
    """Carga el clasificador y sus metadatos para un cultivo."""
    cultivo_slug = cultivo.lower().replace("é", "e").replace("í", "i")
    
    model_path = MODELS_DIR / f"xgb_classifier_{cultivo_slug}.pkl"
    meta_path = MODELS_DIR / f"xgb_classifier_{cultivo_slug}_meta.json"
    
    if not model_path.exists():
        raise FileNotFoundError(f"Modelo no encontrado: {model_path}")
    if not meta_path.exists():
        raise FileNotFoundError(f"Metadatos no encontrados: {meta_path}")
    
    import joblib
    model = joblib.load(model_path)
    
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    
    return model, meta


def predict_risk_labels(model, X: pd.DataFrame) -> np.ndarray:
    """Predice etiquetas de riesgo (0=Bajo, 1=Medio, 2=Alto)."""
    probas = model.predict_proba(X)
    classes = model.classes_
    
    # Mapear probabilidades a etiquetas
    if len(classes) == 3:
        # Multiclase: [Bajo, Medio, Alto] o similar
        labels = np.argmax(probas, axis=1)
        # Asumimos orden 0,1,2 o necesitamos mapear
        return labels
    elif len(classes) == 2:
        # Binario: mapear a Bajo/Medio-Alto
        prob_high = probas[:, 1]
        labels = np.where(prob_high >= 0.20, 2, np.where(prob_high >= 0.10, 1, 0))
        return labels
    else:
        return np.zeros(len(X), dtype=int)


def label_to_text(label: int) -> str:
    """Convierte etiqueta numérica a texto."""
    mapping = {0: "Bajo", 1: "Medio", 2: "Alto"}
    return mapping.get(label, "Desconocido")


def _align_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """
    Alinea la feature matrix con las columnas que esperan los modelos entrenados.
    Agrega columnas derivadas que pueden faltar por diferencias entre versiones.
    """
    df = df.copy()
    
    # señal_riesgo_economico_encoded: codificación ordinal de la señal de riesgo
    # Valores posibles: 'bajo', 'medio', 'alto', None
    if "señal_riesgo_economico_encoded" not in df.columns:
        if "señal_riesgo_economico" in df.columns:
            mapping = {"bajo": 0, "medio": 1, "alto": 2, None: 0}
            df["señal_riesgo_economico_encoded"] = (
                df["señal_riesgo_economico"]
                .str.lower()
                .map(lambda x: mapping.get(x, 0) if x is not None else 0)
                .fillna(0)
                .astype(int)
            )
            logger.info("Columna 'señal_riesgo_economico_encoded' generada desde 'señal_riesgo_economico'")
        else:
            df["señal_riesgo_economico_encoded"] = 0
            logger.warning("Columna 'señal_riesgo_economico_encoded' no encontrada, usando 0 como fallback")
    
    return df


def run_m4_pipeline():
    """Ejecuta el pipeline completo de M4."""
    logger.info("Iniciando pipeline M4 - Explicabilidad SHAP")
    
    # 1. Cargar feature matrix
    if not FEATURE_MATRIX_PATH.exists():
        raise FileNotFoundError(f"Feature matrix no encontrada: {FEATURE_MATRIX_PATH}")
    
    logger.info(f"Cargando feature matrix desde {FEATURE_MATRIX_PATH}")
    df_features = pd.read_parquet(FEATURE_MATRIX_PATH)
    logger.info(f"Feature matrix cargada: {len(df_features)} filas")
    
    # 1b. Alinear columnas con lo que esperan los modelos
    df_features = _align_feature_matrix(df_features)
    
    # 2. Calcular explainers SHAP por cultivo
    logger.info("Calculando explainers SHAP...")
    explainers = build_and_save_explainers(MODELS_DIR, df_features, CULTIVOS_MVP)
    
    # 3. Para cada cultivo, extraer top features y generar predicciones
    all_results = []
    
    for cultivo in CULTIVOS_MVP:
        logger.info(f"Procesando {cultivo}...")
        
        cultivo_slug = cultivo.lower().replace("é", "e").replace("í", "i")
        
        # Filtrar datos por cultivo
        df_cultivo = df_features[df_features["cultivo"] == cultivo].copy()
        if df_cultivo.empty:
            logger.warning(f"No hay datos para {cultivo}")
            continue
        
        # Obtener explainer y features
        explainer_data = explainers[cultivo]
        explainer = explainer_data["explainer"]
        shap_values = explainer_data["shap_values"]
        feature_cols = explainer_data["feature_cols"]
        expected_value = explainer_data["expected_value"]
        
        # Cargar modelo para predicciones
        model, meta = load_classifier_and_meta(cultivo)
        
        # Preparar X en orden correcto
        X = df_cultivo[feature_cols].copy()
        
        # Predecir riesgo
        labels = predict_risk_labels(model, X)
        
        # Normalizar SHAP values (puede ser lista para multiclase)
        if isinstance(shap_values, list):
            # Para clasificación multiclase, tomamos la clase de mayor riesgo
            shap_array = shap_values[-1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_array = shap_values
        
        # Extraer top features por fila
        top_features_list = []
        for i in range(len(df_cultivo)):
            row = df_cultivo.iloc[i]
            shap_row = shap_array[i] if shap_array.ndim > 1 else shap_array
            
            top_feats = get_top_n_features(
                shap_values_row=shap_row,
                feature_names=feature_cols,
                original_row=row,
                feature_mapping=FEATURE_MAPPING,
                top_n=5
            )
            top_features_list.append(top_feats)
        
        # Agregar resultados al DataFrame
        df_cultivo = df_cultivo.copy()
        df_cultivo["prediccion_riesgo"] = [label_to_text(l) for l in labels]
        df_cultivo["top_features"] = top_features_list
        
        all_results.append(df_cultivo)
        logger.info(f"{cultivo}: {len(df_cultivo)} registros procesados")
    
    # 4. Consolidar resultados
    if not all_results:
        raise ValueError("No se generaron resultados para ningún cultivo")
    
    df_consolidated = pd.concat(all_results, ignore_index=True)
    logger.info(f"Total consolidado: {len(df_consolidated)} registros")
    
    # 5. Generar narrativas
    logger.info("Generando narrativas...")
    df_final = build_and_save_narratives_df(
        df_base=df_consolidated,
        top_features_col=df_consolidated["top_features"]
    )
    
    # 6. Guardar resultado final
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    df_final.to_parquet(OUTPUT_PATH, index=False)
    logger.info(f"Resultado guardado en {OUTPUT_PATH}")
    
    # Verificar columnas
    required_cols = {"codigo_dane", "cultivo", "prediccion_riesgo", "narrativa_riesgo"}
    missing = required_cols - set(df_final.columns)
    if missing:
        logger.warning(f"Columnas faltantes: {missing}")
    
    logger.info("Pipeline M4 completado exitosamente")
    return df_final


if __name__ == "__main__":
    try:
        df = run_m4_pipeline()
        print(f"\n[✔] M4 completado: {len(df)} registros en {OUTPUT_PATH}")
    except Exception as e:
        logger.error(f"Error en pipeline M4: {e}")
        raise
