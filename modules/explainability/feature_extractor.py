import warnings
import numpy as np
import pandas as pd

def get_top_n_features(
    shap_values_row: np.ndarray,
    feature_names: list[str],
    original_row: dict | pd.Series,
    feature_mapping: dict,
    top_n: int = 5,
) -> list[dict]:
    """
    Given a SHAP vector for a specific prediction, order variables by absolute magnitude,
    separate by direction, map technical names to friendly names, and return top features.
    
    Args:
        shap_values_row: 1D vector with SHAP values of a prediction.
        feature_names: Ordered list with column names.
        original_row: dict or pd.Series with the original values of the observation.
        feature_mapping: Dictionary mapping technical names to friendly ones.
        top_n: Number of factors to return, defaults to 5.
        
    Returns:
        list[dict]: List of dictionaries containing the extracted top features info.
    """
    if len(shap_values_row) != len(feature_names):
        raise ValueError(
            f"Dimensión de SHAP distinta al número de features: "
            f"len(shap_values_row)={len(shap_values_row)} != len(feature_names)={len(feature_names)}"
        )
        
    # Filtrar valores no nulos
    non_zero_indices = np.where(shap_values_row != 0)[0]
    if len(non_zero_indices) == 0:
        return []
        
    # Ordenar por valor absoluto descendente
    abs_shap = np.abs(shap_values_row[non_zero_indices])
    sorted_non_zero = non_zero_indices[np.argsort(-abs_shap)]
    
    # Tomar los top N
    top_indices = sorted_non_zero[:top_n]
    
    results = []
    for idx in top_indices:
        feature_name = feature_names[idx]
        shap_val = float(shap_values_row[idx])
        
        # Obtener el valor original
        if isinstance(original_row, pd.Series):
            val_orig = original_row.get(feature_name, None)
        else:
            val_orig = original_row.get(feature_name, None)
            
        # Mapeo a nombre amigable
        if feature_name in feature_mapping:
            friendly_name = feature_mapping[feature_name]
        else:
            friendly_name = feature_name.replace("_", " ").title()
            warnings.warn(f"Falta mapeo humano para feature '{feature_name}'. Usando fallback: '{friendly_name}'")
            
        direccion = "Aumenta riesgo" if shap_val > 0 else "Disminuye riesgo"
        
        results.append({
            "feature_id": feature_name,
            "nombre_amigable": friendly_name,
            "shap_value": shap_val,
            "direccion": direccion,
            "valor_original": val_orig
        })
        
    return results
