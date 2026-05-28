import logging
import json
import joblib
from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from xgboost import XGBClassifier
from shared.config import (
    MODELS_DIR, CULTIVOS_MVP,
    TRAIN_HASTA, VAL_AÑO, TEST_DESDE
)

logger = logging.getLogger(__name__)

def _encode_risk_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Codifica `señal_riesgo_economico` de forma case-insensitive con orden `bajo < medio < alto`.
    """
    if "señal_riesgo_economico" in df.columns:
        mapping = {"bajo": 0, "medio": 1, "alto": 2}
        
        def safe_lower(val):
            if pd.isna(val):
                return val
            return str(val).strip().lower()
            
        df["señal_riesgo_economico_encoded"] = df["señal_riesgo_economico"].apply(safe_lower).map(mapping)
        # Drop the original string column if it exists to avoid type errors in XGBoost
        df = df.drop(columns=["señal_riesgo_economico"])
        
    return df

def prepare_classification_frame(df: pd.DataFrame, feature_cols: list[str], target_col: str = "target_riesgo") -> tuple[pd.DataFrame, list[str]]:
    """
    Prepara el dataframe filtrando nulos en target y validando features.
    """
    if target_col not in df.columns:
        raise ValueError(f"Falta columna {target_col}")

    # Filtrar nulos en target_riesgo
    df_clean = df.dropna(subset=[target_col]).copy()
    if df_clean.empty:
        raise ValueError(f"No quedan filas despues de eliminar nulos en {target_col}")

    df_clean = _encode_risk_signal(df_clean)
    
    # Actualizar la lista de features para incluir la codificada y eliminar la original
    final_features = []
    for f in feature_cols:
        if f == "señal_riesgo_economico":
            final_features.append("señal_riesgo_economico_encoded")
        else:
            final_features.append(f)
            
    # Validar que queden features
    missing_features = [f for f in final_features if f not in df_clean.columns]
    if missing_features:
        raise ValueError(f"Faltan features en df: {missing_features}")
        
    if not final_features:
        raise ValueError("No quedan features utilizables")

    return df_clean, final_features

def _train_single_cultivo_classifier(df: pd.DataFrame, feature_cols: list[str], target_col: str) -> dict:
    # 3. Construir split temporal
    train_mask = df["año"] <= TRAIN_HASTA
    val_mask = df["año"] == VAL_AÑO
    test_mask = df["año"] >= TEST_DESDE

    df_train = df[train_mask]
    df_val = df[val_mask]
    df_test = df[test_mask]

    # 4. Verificar que train/val/test tengan filas y ambos valores de clase
    for split_name, split_df in zip(["train", "val", "test"], [df_train, df_val, df_test]):
        if split_df.empty:
            raise ValueError(f"Split {split_name} vacio")
        
        n_classes = split_df[target_col].nunique()
        if n_classes < 2:
            raise ValueError(f"Split {split_name} contiene una sola clase (clases = {n_classes})")

    X_train, y_train = df_train[feature_cols], df_train[target_col]
    X_val, y_val = df_val[feature_cols], df_val[target_col]
    X_test, y_test = df_test[feature_cols], df_test[target_col]

    # 6. Calcular scale_pos_weight
    negativos = (y_train == 0).sum()
    positivos = (y_train == 1).sum()
    scale_pos_weight = negativos / positivos
    
    logger.info(f"Target distribution train - 0: {negativos}, 1: {positivos}, scale_pos_weight: {scale_pos_weight:.2f}")

    # 7. Entrenar XGBClassifier
    clf = XGBClassifier(
        objective="binary:logistic",
        n_estimators=500,
        learning_rate=0.05,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_alpha=0.0,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=-1,
        eval_metric="auc",
        scale_pos_weight=scale_pos_weight,
        early_stopping_rounds=30
    )

    clf.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=False
    )

    return {
        "model": clf,
        "features": feature_cols,
        "scale_pos_weight": scale_pos_weight,
        "best_iteration": clf.best_iteration,
        "splits_size": {
            "train": len(X_train),
            "val": len(X_val),
            "test": len(X_test)
        },
        "split_data": {
            "train": (X_train, y_train),
            "val": (X_val, y_val),
            "test": (X_test, y_test)
        }
    }

def train_classifiers(
    df: pd.DataFrame,
    feature_cols: list[str],
    target_col: str = "target_riesgo",
    models_dir: Path = MODELS_DIR,
) -> dict[str, dict]:
    """
    Entrena un XGBClassifier por cultivo usando split temporal estricto 
    y mitigación de desbalance.
    """
    df_clean, final_features = prepare_classification_frame(df, feature_cols, target_col)
    
    results = {}
    for cultivo in CULTIVOS_MVP:
        logger.info(f"Iniciando entrenamiento clasificador para {cultivo}...")
        df_cultivo = df_clean[df_clean["cultivo"] == cultivo].copy()
        
        if df_cultivo.empty:
            logger.warning(f"No hay datos para cultivo {cultivo}")
            continue

        try:
            cultivo_result = _train_single_cultivo_classifier(df_cultivo, final_features, target_col)
            results[cultivo] = cultivo_result
            logger.info(f"Entrenamiento {cultivo} completado. Best iteration: {cultivo_result['best_iteration']}")
        except ValueError as e:
            logger.error(f"Error entrenando {cultivo}: {e}")
            raise ValueError(f"Error entrenando cultivo {cultivo}: {e}")
            
    return results

def evaluate_and_save_metrics(
    models_info: dict,
    output_dir: Path = MODELS_DIR,
) -> list[dict]:
    """
    Evalúa cada modelo sobre train, val y test, calcula métricas de clasificación binaria
    y guarda los artefactos finales del pipeline M3.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    metrics_records = []
    
    for cultivo, info in models_info.items():
        if "model" not in info or "split_data" not in info:
            raise ValueError(f"Falta 'model' o 'split_data' en models_info para {cultivo}")
            
        model = info["model"]
        split_data = info["split_data"]
        
        # Validar Predict proba
        if not hasattr(model, "predict_proba"):
            raise ValueError(f"El modelo para {cultivo} no expone predict_proba")
            
        for split_name in ["train", "val", "test"]:
            if split_name not in split_data:
                raise ValueError(f"Falta el split {split_name} para {cultivo}")
                
            X, y = split_data[split_name]
            
            if len(X) == 0:
                raise ValueError(f"El split {split_name} para {cultivo} está vacío.")
                
            y_pred = model.predict(X)
            y_proba = model.predict_proba(X)[:, 1]
            
            acc = accuracy_score(y, y_pred)
            prec = precision_score(y, y_pred, zero_division=0)
            rec = recall_score(y, y_pred, zero_division=0)
            f1 = f1_score(y, y_pred, zero_division=0)
            auc = roc_auc_score(y, y_proba)
            
            record = {
                "cultivo": cultivo,
                "split": split_name,
                "n": len(X),
                "accuracy": float(acc),
                "precision": float(prec),
                "recall": float(rec),
                "f1_score": float(f1),
                "auc_roc": float(auc),
                "best_iteration": int(info["best_iteration"])
            }
            metrics_records.append(record)
            
        import unicodedata
        import re
        slug = str(cultivo).lower()
        slug = unicodedata.normalize('NFD', slug).encode('ascii', 'ignore').decode('utf-8')
        slug = re.sub(r'[^a-z0-9]', '', slug)
        
        # Serialización de artefactos
        model_filename = output_dir / f"xgb_classifier_{slug}.pkl"
        meta_filename = output_dir / f"xgb_classifier_{slug}_meta.json"
        
        try:
            joblib.dump(model, model_filename)
        except Exception as e:
            raise RuntimeError(f"Error escribiendo {model_filename}: {e}")
            
        meta_content = {
            "feature_cols": info["features"],
            "best_iteration": int(info["best_iteration"])
        }
        
        try:
            with open(meta_filename, "w", encoding="utf-8") as f:
                json.dump(meta_content, f, indent=2, ensure_ascii=False)
        except Exception as e:
            raise RuntimeError(f"Error escribiendo {meta_filename}: {e}")
            
    # Guardar métricas globales
    metrics_filename = output_dir / "m3_classification_metrics.json"
    try:
        with open(metrics_filename, "w", encoding="utf-8") as f:
            json.dump(metrics_records, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise RuntimeError(f"Error escribiendo {metrics_filename}: {e}")
        
    return metrics_records
