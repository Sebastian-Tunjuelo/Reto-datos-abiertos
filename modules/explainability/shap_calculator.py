import json
import logging
import pickle
from pathlib import Path
import numpy as np
import pandas as pd
import shap
import time

logger = logging.getLogger(__name__)

def calculate_shap_values(explainer: shap.TreeExplainer, X: pd.DataFrame) -> tuple[np.ndarray, float]:
    """
    Calculate SHAP values for a given DataFrame using a pre-instantiated explainer.
    
    Args:
        explainer: A trained shap.TreeExplainer.
        X: The feature matrix.
        
    Returns:
        tuple[np.ndarray, float]: SHAP values and the expected/base value.
    """
    shap_values = explainer.shap_values(X)
    
    # expected_value can be an array if multi-class, but for risk prediction (usually binary or multi),
    # depending on objective. Generally we take the raw format.
    expected_value = explainer.expected_value
    
    if isinstance(expected_value, np.ndarray) and len(expected_value) == 1:
        expected_value = float(expected_value[0])
    
    return shap_values, expected_value

def build_and_save_explainers(model_dir: Path, data: pd.DataFrame, cultivos: list[str]) -> dict:
    """
    Instantiate TreeExplainers per crop, calculate SHAP values over the input matrix,
    and save the explainers for inference.
    
    Args:
        model_dir: Path where models and meta.jsons are stored.
        data: Base feature matrix dataframe.
        cultivos: List of normalized crop names (e.g., ['Café', 'Cacao', 'Maíz']).
        
    Returns:
        dict: Dictionary containing explainer, shap values, and feature order per crop.
              Format: { crop: {'explainer': explainer, 'shap_values': shap_values, 'expected_value': expected_value, 'feature_cols': list} }
    """
    results = {}
    
    for cultivo in cultivos:
        logger.info(f"Processing SHAP explainer for {cultivo}")
        cultivo_norm = cultivo.lower().replace("é", "e").replace("í", "i")
        
        meta_path = model_dir / f"xgb_classifier_{cultivo_norm}_meta.json"
        model_path = model_dir / f"xgb_classifier_{cultivo_norm}.pkl"
        
        if not meta_path.exists():
            raise FileNotFoundError(f"Metadata file missing for crop {cultivo}: {meta_path}")
        if not model_path.exists():
            raise FileNotFoundError(f"Model file missing for crop {cultivo}: {model_path}")
            
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
            
        feature_cols = meta.get("feature_cols", [])
        if not feature_cols:
            raise ValueError(f"No 'feature_cols' found in {meta_path}")
            
        # Check column existence in data
        missing_cols = [col for col in feature_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in feature matrix for {cultivo}: {missing_cols}")
            
        # Filter data for this crop, if applicable. But the spec says:
        # "calcular los valores SHAP sobre la matriz de features usada por el clasificador de riesgo"
        # We assume the dataframe passed is already the dataset goal, but we need to reorder features.
        # It's better to filter rows by crop if the dataset contains them all, but spec just says
        # reorder X exactly as training.
        X_input = data[feature_cols].copy()
        
        # Load model
        with open(model_path, "rb") as f:
            model = pickle.load(f)
            
        logger.info(f"Instantiating TreeExplainer for {cultivo}")
        start_time = time.time()
        explainer = shap.TreeExplainer(model)
        instantiation_time = time.time() - start_time
        
        if instantiation_time >= 5.0:
            logger.warning(f"Explainer instantiation for {cultivo} took {instantiation_time:.2f} seconds.")
            
        start_time = time.time()
        shap_values, expected_value = calculate_shap_values(explainer, X_input)
        calc_time = time.time() - start_time
        logger.info(f"Calculated SHAP values in {calc_time:.2f} seconds.")
        
        # Verify dimensions
        # TreeExplainer shap_values can be (n_samples, n_features) or a list if multi-class
        if isinstance(shap_values, list):
            n_features = shap_values[0].shape[1]
        else:
            if len(shap_values.shape) == 3:
                 n_features = shap_values.shape[2]
            else:
                 n_features = shap_values.shape[1]
                 
        if n_features != len(feature_cols):
             raise ValueError(f"SHAP values dimension mismatch. Expected {len(feature_cols)} features, got {n_features}")

        # The spec states: "Suma total de SHAP y base_value difiere -> AssertionError"
        pred_margin = model.predict(X_input, output_margin=True)
        if isinstance(shap_values, list): # multi-class
            for i, class_shaps in enumerate(shap_values):
                sum_shap = class_shaps.sum(axis=1) + (expected_value[i] if isinstance(expected_value, (list, np.ndarray)) else expected_value)
                np.testing.assert_allclose(sum_shap, pred_margin[:, i], rtol=1e-3, atol=1e-3, err_msg="Suma total de SHAP y base_value difiere de la predicción margin")
        else:
            sum_shap = shap_values.sum(axis=1) + expected_value
            if len(pred_margin.shape) > 1 and pred_margin.shape[1] > 1: # Some XGBoost binary output 2 columns? Standard is 1D
                pred_to_check = pred_margin[:, 1] if pred_margin.shape[1] == 2 else pred_margin
            else:
                pred_to_check = pred_margin
            np.testing.assert_allclose(sum_shap, pred_to_check, rtol=1e-3, atol=1e-3, err_msg="Suma total de SHAP y base_value difiere de la predicción margin")
        
        # Save explainer
        out_path = model_dir / f"shap_explainer_{cultivo_norm}.pkl"
        with open(out_path, "wb") as f:
            pickle.dump(explainer, f)
        logger.info(f"Saved explainer for {cultivo} to {out_path}")
            
        results[cultivo] = {
            "explainer": explainer,
            "shap_values": shap_values,
            "expected_value": expected_value,
            "feature_cols": feature_cols
        }
        
    return results
