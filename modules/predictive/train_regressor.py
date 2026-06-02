import logging
import warnings
from pathlib import Path
import pandas as pd
import numpy as np

import json
import joblib
import unicodedata
import re
from xgboost import XGBRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from shared.config import (
    DATA_DIR, MODELS_DIR, CULTIVOS_MVP,
    TRAIN_HASTA, VAL_AÑO, TEST_DESDE
)
from shared.normalization import normalize_dane_code

logger = logging.getLogger(__name__)

def load_feature_matrix(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """
    Carga feature_matrix.parquet desde la ruta especificada.
    """
    path = Path(data_dir) / "feature_matrix.parquet"
    if not path.exists():
        raise FileNotFoundError(f"M2.1: falta {path.name}")
    
    return pd.read_parquet(path)

def prepare_regression_frame(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], str]:
    """
    Valida el DataFrame de features y lo prepara para entrenamiento.
    """
    target_col = "target_rendimiento"
    
    required_cols = [
        "codigo_dane", "municipio", "departamento", "cultivo", "año",
        "prec_acum_mm", "anomalia_prec", "temp_media_c", "anomalia_temp", 
        "dias_secos", "hum_media_pct", "rendimiento_t1", "rendimiento_prom3a", 
        "tendencia_rend_3a", "area_sembrada_t1", "pct_alta", "pct_media", 
        "pct_baja", "pct_exclusion", "pct_condicionada", "pct_no_condicionada", 
        "indice_agroinsumos", "percentil_fertilizantes", "señal_riesgo_economico", 
        target_col
    ]
    
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"M2.1: columnas faltantes: {missing_cols}")
    
    if df.empty:
        raise ValueError("M2.1: no hay filas validas")
        
    # Filtrar a CULTIVOS_MVP
    initial_len = len(df)
    df_clean = df[df["cultivo"].isin(CULTIVOS_MVP)].copy()
    if len(df_clean) < initial_len:
        logger.info(f"Descartadas {initial_len - len(df_clean)} filas por cultivos fuera de MVP.")
        
    # Normalizar codigo_dane
    df_clean["codigo_dane_norm"] = df_clean["codigo_dane"].apply(normalize_dane_code)
    invalid_dane = df_clean["codigo_dane_norm"].isna()
    if invalid_dane.any():
        logger.warning(f"Descartadas {invalid_dane.sum()} filas por codigo_dane invalido.")
        df_clean = df_clean[~invalid_dane]
        
    df_clean["codigo_dane"] = df_clean["codigo_dane_norm"]
    df_clean = df_clean.drop(columns=["codigo_dane_norm"])
    
    # Filtrar años 2007-2024
    valid_years = (df_clean["año"] >= 2007) & (df_clean["año"] <= 2024)
    if (~valid_years).any():
        logger.info(f"Descartadas {(~valid_years).sum()} filas por año fuera de rango 2007-2024.")
        df_clean = df_clean[valid_years]
        
    # Convertir columnas numericas
    numeric_cols = [
        "prec_acum_mm", "anomalia_prec", "temp_media_c", "anomalia_temp", 
        "dias_secos", "hum_media_pct", "rendimiento_t1", "rendimiento_prom3a", 
        "tendencia_rend_3a", "area_sembrada_t1", "pct_alta", "pct_media", 
        "pct_baja", "pct_exclusion", "pct_condicionada", "pct_no_condicionada", 
        "indice_agroinsumos", "percentil_fertilizantes"
    ]
    for col in numeric_cols:
        df_clean[col] = pd.to_numeric(df_clean[col], errors="coerce")
        
    # Mapear señal_riesgo_economico
    risk_mapping = {"bajo": 0, "medio": 1, "alto": 2}
    
    def map_risk(x):
        if pd.isna(x):
            return np.nan
        val = str(x).strip().lower()
        if val in risk_mapping:
            return risk_mapping[val]
        warnings.warn(f"Valor no mapeado en señal_riesgo_economico: {x}")
        return np.nan

    df_clean["señal_riesgo_economico"] = df_clean["señal_riesgo_economico"].apply(map_risk)
    df_clean["señal_riesgo_economico"] = pd.to_numeric(df_clean["señal_riesgo_economico"], errors="coerce")
        
    # Eliminar filas con target_rendimiento NaN
    target_na = df_clean[target_col].isna()
    if target_na.any():
        df_clean = df_clean[~target_na]
        
    if df_clean.empty:
        raise ValueError("M2.1: no hay filas validas")
        
    # Definir feature_cols
    excluded_cols = {"codigo_dane", "municipio", "departamento", "cultivo", target_col}
    feature_cols = [c for c in df_clean.columns if c not in excluded_cols]
    
    return df_clean, feature_cols, target_col

def _train_single_cultivo(
    df_cultivo: pd.DataFrame,
    cultivo: str,
    feature_cols: list[str],
    target_col: str,
    models_dir: Path
) -> dict:
    import unicodedata
    import re
    
    slug = str(cultivo).lower()
    slug = unicodedata.normalize('NFD', slug).encode('ascii', 'ignore').decode('utf-8')
    slug = re.sub(r'[^a-z0-9]', '', slug)
    
    train_mask = df_cultivo["año"] <= TRAIN_HASTA
    val_mask = df_cultivo["año"] == VAL_AÑO
    test_mask = df_cultivo["año"] >= TEST_DESDE
    
    df_train = df_cultivo[train_mask]
    df_val = df_cultivo[val_mask]
    df_test = df_cultivo[test_mask]
    
    if df_train.empty or df_val.empty or df_test.empty:
        raise ValueError(f"M2.2: split vacio para {cultivo}")
        
    X_train, y_train = df_train[feature_cols], df_train[target_col]
    X_val, y_val = df_val[feature_cols], df_val[target_col]
    
    # In xgboost >=2.0, early_stopping_rounds should be passed to constructor
    model = XGBRegressor(
        objective="reg:squarederror",
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        early_stopping_rounds=30,
        eval_metric="rmse"
    )
    
    model.fit(
        X_train, y_train,
        eval_set=[(X_train, y_train), (X_val, y_val)],
        verbose=False
    )
    
    best_iteration = getattr(model, "best_iteration", None)
    
    # Crear carpeta models si no existe
    models_dir = Path(models_dir)
    models_dir.mkdir(parents=True, exist_ok=True)
    
    model_path = models_dir / f"xgb_regressor_{slug}.pkl"
    meta_path = models_dir / f"xgb_regressor_{slug}_meta.json"
    
    try:
        joblib.dump(model, model_path)
    except Exception as e:
        raise RuntimeError(f"Error al guardar modelo en {model_path}: {e}")
        
    meta = {
        "feature_cols": feature_cols,
        "target_col": target_col,
        "years_split": {
            "train_hasta": TRAIN_HASTA,
            "val_año": VAL_AÑO,
            "test_desde": TEST_DESDE
        },
        "best_iteration": best_iteration
    }
    
    try:
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=4, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Error al guardar meta en {meta_path}: {e}")
        
    return meta

def train_regressors(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str,
    models_dir: Path = MODELS_DIR,
) -> dict[str, dict]:
    """
    Entrena un XGBRegressor de forma independiente para cada cultivo en CULTIVOS_MVP.
    """
    results = {}
    for cultivo in CULTIVOS_MVP:
        df_cultivo = df[df["cultivo"] == cultivo]
        if df_cultivo.empty:
            logger.warning(f"No hay datos para el cultivo {cultivo}. Se omite.")
            continue
            
        logger.info(f"Entrenando modelo para {cultivo}...")
        meta = _train_single_cultivo(
            df_cultivo=df_cultivo,
            cultivo=cultivo,
            feature_cols=feature_cols,
            target_col=target_col,
            models_dir=models_dir
        )
        results[cultivo] = meta
        
    return results

def evaluate_and_save_metrics(
    df: pd.DataFrame,
    models_info: dict[str, dict],
    feature_cols: list[str],
    target_col: str,
    output_path: Path = MODELS_DIR / "m2_regression_metrics.json",
) -> list[dict]:
    """
    Calcula y guarda métricas (MAE, RMSE, R2) para train/val/test por cultivo.
    """
    metrics_records = []
    
    for cultivo in CULTIVOS_MVP:
        if cultivo not in models_info:
            continue
            
        slug = str(cultivo).lower()
        slug = unicodedata.normalize('NFD', slug).encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[^a-z0-9]', '', slug)
        
        # Cargar el modelo
        model_path = output_path.parent / f"xgb_regressor_{slug}.pkl"
        try:
            model = joblib.load(model_path)
        except Exception as e:
            logger.error(f"Error cargando modelo para {cultivo} desde {model_path}: {e}")
            continue
        
        df_cultivo = df[df["cultivo"] == cultivo]
        
        train_mask = df_cultivo["año"] <= TRAIN_HASTA
        val_mask = df_cultivo["año"] == VAL_AÑO
        test_mask = df_cultivo["año"] >= TEST_DESDE
        
        splits = {
            "train": df_cultivo[train_mask],
            "val": df_cultivo[val_mask],
            "test": df_cultivo[test_mask]
        }
        
        meta = models_info[cultivo]
        best_iteration = meta.get("best_iteration")
        
        for split_name, df_split in splits.items():
            if df_split.empty:
                continue
                
            X_split = df_split[feature_cols]
            y_true = df_split[target_col]
            
            y_pred = model.predict(X_split)
            
            # Chequear NaN_predictions
            valid_mask = ~np.isnan(y_pred)
            if not valid_mask.all():
                logger.warning(f"Predicciones NaN detectadas en split {split_name} para {cultivo} ({(~valid_mask).sum()} filas). Se omitirán.")
                y_true = y_true[valid_mask]
                y_pred = y_pred[valid_mask]
                
            if len(y_true) == 0:
                continue
                
            mae = mean_absolute_error(y_true, y_pred)
            rmse = np.sqrt(mean_squared_error(y_true, y_pred))
            
            try:
                r2 = r2_score(y_true, y_pred)
            except Exception:
                r2 = None
                
            # Validar que R2 no esté indefinido debido a varianza 0
            if np.var(y_true) == 0:
                logger.warning(f"Varianza 0 en target_rendimiento para {cultivo} ({split_name}). R2 indefinido.")
                r2 = None
                
            metrics_records.append({
                "cultivo": cultivo,
                "split": split_name,
                "n": len(y_true),
                "mae": float(mae),
                "rmse": float(rmse),
                "r2": float(r2) if r2 is not None else None,
                "best_iteration": best_iteration
            })
            
    # Guardar a JSON
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics_records, f, indent=4, ensure_ascii=False)
        logger.info(f"Métricas guardadas en {output_path}")
    except Exception as e:
        logger.error(f"Error al guardar métricas en {output_path}: {e}")
        raise
        
    return metrics_records
