import logging
import json
from pathlib import Path
import pandas as pd
import numpy as np
import joblib
from copy import deepcopy

from shared.config import MODELS_DIR

logger = logging.getLogger(__name__)

SCENARIO_CATALOG = ["base", "seco", "lluvioso", "fertilizantes"]

def _apply_shock(df: pd.DataFrame, scenario: str) -> tuple[pd.DataFrame, list[str]]:
    """Aplica shocks deterministas a un dataframe y devuelve las features tocadas."""
    df_shock = df.copy()
    features_modified = []
    
    if scenario == "base":
        return df_shock, features_modified
        
    elif scenario == "seco":
        if "prec_acum_mm" in df_shock.columns:
            df_shock["prec_acum_mm"] *= 0.7
            features_modified.append("prec_acum_mm")
        if "dias_secos" in df_shock.columns:
            df_shock["dias_secos"] *= 1.3
            features_modified.append("dias_secos")
        if "anomalia_prec" in df_shock.columns:
            df_shock["anomalia_prec"] -= 30.0
            features_modified.append("anomalia_prec")
            
    elif scenario == "lluvioso":
        if "prec_acum_mm" in df_shock.columns:
            df_shock["prec_acum_mm"] *= 1.3
            features_modified.append("prec_acum_mm")
        if "dias_secos" in df_shock.columns:
            df_shock["dias_secos"] *= 0.7
            features_modified.append("dias_secos")
        if "anomalia_prec" in df_shock.columns:
            df_shock["anomalia_prec"] += 30.0
            features_modified.append("anomalia_prec")
            
    elif scenario == "fertilizantes":
        if "indice_agroinsumos" in df_shock.columns:
            df_shock["indice_agroinsumos"] *= 1.2
            features_modified.append("indice_agroinsumos")
        if "percentil_fertilizantes" in df_shock.columns:
            df_shock["percentil_fertilizantes"] = np.clip(df_shock["percentil_fertilizantes"] + 20.0, 0, 100)
            features_modified.append("percentil_fertilizantes")
        if "señal_riesgo_economico" in df_shock.columns:
            # Assuming risk is numeric 0=bajo, 1=medio, 2=alto
            if pd.api.types.is_numeric_dtype(df_shock["señal_riesgo_economico"]):
                df_shock["señal_riesgo_economico"] = np.clip(df_shock["señal_riesgo_economico"] + 1, 0, 2)
            else:
                # If string
                risk_map = {"bajo": "medio", "medio": "alto", "alto": "alto"}
                df_shock["señal_riesgo_economico"] = df_shock["señal_riesgo_economico"].apply(
                    lambda x: risk_map.get(str(x).strip().lower(), x)
                )
            features_modified.append("señal_riesgo_economico")
            
    else:
        raise ValueError(f"Escenario no reconocido: {scenario}")
        
    return df_shock, features_modified

def simulate_scenarios(baseline_row: pd.DataFrame | dict, scenarios: list[str]) -> pd.DataFrame:
    """
    Genera escenarios contrafactuales de rendimiento y riesgo a partir de una fila base.
    """
    if isinstance(baseline_row, dict):
        baseline_row = pd.DataFrame([baseline_row])
        
    if len(baseline_row) != 1:
        raise ValueError("baseline_row debe contener exactamente una fila.")
        
    # Validar escenarios
    for s in scenarios:
        if s not in SCENARIO_CATALOG:
            raise ValueError(f"Escenario fuera del catálogo: {s}. Permitidos: {SCENARIO_CATALOG}")
            
    if "base" not in scenarios:
        scenarios = ["base"] + scenarios
        
    # Extraer variables principales para identificar el cultivo
    required_id_cols = ["codigo_dane", "municipio", "departamento", "cultivo", "año"]
    for col in required_id_cols:
        if col not in baseline_row.columns:
            raise KeyError(f"Falta columna requerida en fila base: {col}")
            
    cultivo = baseline_row.iloc[0]["cultivo"]
    cultivo_fmt = str(cultivo).lower().replace("á", "a").replace("é", "e").replace("í", "i").replace("ó", "o").replace("ú", "u")
    
    # Cargar modelos y metadatos
    regressor_path = MODELS_DIR / f"xgb_regressor_{cultivo_fmt}.pkl"
    regressor_meta_path = MODELS_DIR / f"xgb_regressor_{cultivo_fmt}_meta.json"
    classifier_path = MODELS_DIR / f"xgb_classifier_{cultivo_fmt}.pkl"
    classifier_meta_path = MODELS_DIR / f"xgb_classifier_{cultivo_fmt}_meta.json"
    
    if not (regressor_path.exists() and regressor_meta_path.exists() and 
            classifier_path.exists() and classifier_meta_path.exists()):
        raise FileNotFoundError(f"Modelos o metadatos no encontrados para cultivo {cultivo}")
        
    regressor = joblib.load(regressor_path)
    with open(regressor_meta_path, "r", encoding="utf-8") as f:
        regressor_meta = json.load(f)
        
    classifier = joblib.load(classifier_path)
    with open(classifier_meta_path, "r", encoding="utf-8") as f:
        classifier_meta = json.load(f)
        
    reg_features = regressor_meta.get("feature_cols", [])
    clf_features = classifier_meta.get("feature_cols", [])
    
    # Validar que baseline tenga todas las features
    # Permitir que falte la encoded de clasificador si está la original
    missing_reg = [f for f in reg_features if f not in baseline_row.columns]
    missing_clf = [f for f in clf_features if f not in baseline_row.columns and f != "señal_riesgo_economico_encoded"]
    if missing_reg or missing_clf:
        raise KeyError(f"Faltan features en baseline_row. Reg: {missing_reg}, Clf: {missing_clf}")
        
    results = []
    base_rendimiento = None
    base_prob_riesgo = None
    
    supuestos_text = {
        "base": "Línea base original",
        "seco": "Reducción del 30% en precipitación y aumento de días secos",
        "lluvioso": "Aumento del 30% en precipitación",
        "fertilizantes": "Aumento del 20% en costo de agroinsumos"
    }

    # Riesgo map to label if numeric
    risk_labels = {0: "Bajo", 1: "Medio", 2: "Alto"}
    
    for esc in scenarios:
        df_esc, mod_features = _apply_shock(baseline_row, esc)
        
        # Reordenar predictoras
        X_reg = df_esc.copy()
        
        # El clasificador requiere la versión encoded de la señal económica
        if "señal_riesgo_economico_encoded" in clf_features and "señal_riesgo_economico" in X_reg.columns:
            # Map based on what train_classifier did
            risk_map = {"bajo": 0, "medio": 1, "alto": 2}
            def safe_lower(val):
                if pd.isna(val): return val
                return str(val).strip().lower()
            if not pd.api.types.is_numeric_dtype(X_reg["señal_riesgo_economico"]):
                X_reg["señal_riesgo_economico_encoded"] = X_reg["señal_riesgo_economico"].apply(safe_lower).map(risk_map)
            else:
                X_reg["señal_riesgo_economico_encoded"] = X_reg["señal_riesgo_economico"]
                
        # Asegurar tipos numéricos para XGBoost
        for col in reg_features + clf_features:
            if col in X_reg.columns:
                X_reg[col] = pd.to_numeric(X_reg[col], errors='coerce')
        
        # XGBoost expects the columns in the exact order as its internal feature_names.
        # Although we reorder based on meta, we must ensure it matches booster's native columns exactly.
        # The booster's expected features are retrieved from regressor.get_booster().feature_names
        # if available.
        actual_reg_features = getattr(regressor, "feature_names_in_", reg_features)
        X_reg_ordered = X_reg[actual_reg_features]
        
        actual_clf_features = getattr(classifier, "feature_names_in_", clf_features)
        X_clf_ordered = X_reg[actual_clf_features]
        
        # Puesto que es una fila
        rendimiento_pred = float(regressor.predict(X_reg_ordered)[0])
        
        # Prob risk (assuming multiclass where class 2 is high risk, or binary where class 1 is high risk)
        # We need to get prob of HIGH risk. Let's assume binary (1=Alto, 0=Bajo/Medio) or multiclass (class 'Alto')
        try:
            proba = classifier.predict_proba(X_clf_ordered)[0]
            if len(proba) == 3: # 0=Bajo, 1=Medio, 2=Alto
                prob_riesgo_alto = float(proba[2])
                pred_label_idx = int(np.argmax(proba))
                etiqueta = risk_labels.get(pred_label_idx, str(pred_label_idx))
            else: # Asumiendo binario donde class 1 = Alto
                prob_riesgo_alto = float(proba[1])
                etiqueta = "Alto" if prob_riesgo_alto > 0.5 else "Bajo/Medio"
        except:
            # Fallback if no predict_proba
            pred = classifier.predict(X_clf)[0]
            prob_riesgo_alto = 1.0 if pred == 2 else 0.0 # Placeholder
            etiqueta = risk_labels.get(int(pred), str(pred))
            
        if esc == "base":
            base_rendimiento = rendimiento_pred
            base_prob_riesgo = prob_riesgo_alto
            
        delta_rend_abs = rendimiento_pred - base_rendimiento
        delta_rend_pct = (delta_rend_abs / base_rendimiento) if base_rendimiento else 0.0
        delta_prob = prob_riesgo_alto - base_prob_riesgo
        
        results.append({
            "codigo_dane": str(df_esc.iloc[0]["codigo_dane"]),
            "cultivo": str(df_esc.iloc[0]["cultivo"]),
            "año": int(df_esc.iloc[0]["año"]),
            "escenario": esc,
            "rendimiento_esperado": round(rendimiento_pred, 4),
            "prob_riesgo_alto": round(prob_riesgo_alto, 4),
            "etiqueta_riesgo": etiqueta,
            "delta_rendimiento_abs": round(delta_rend_abs, 4),
            "delta_rendimiento_pct": round(delta_rend_pct * 100, 2), # in percentage
            "delta_prob_riesgo_alto": round(delta_prob, 4),
            "features_modificadas": mod_features,
            "supuesto": supuestos_text.get(esc, "")
        })
        
    return pd.DataFrame(results)

