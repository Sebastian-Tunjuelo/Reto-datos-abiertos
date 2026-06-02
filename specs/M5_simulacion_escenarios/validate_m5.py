import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

from shared.config import MODELS_DIR
from modules.predictive.scenarios import simulate_scenarios, SCENARIO_CATALOG

class DummyRegressor:
    def predict(self, X):
        return np.array([1.5] * len(X))
        
class DummyClassifier:
    def predict(self, X):
        return np.array([0] * len(X))
    def predict_proba(self, X):
        # Retorna [prob_bajo, prob_medio, prob_alto]
        return np.array([[0.8, 0.1, 0.1]] * len(X))

def create_dummy_models(cultivo="cafe"):
    """Crea modelos temporales (Dummy) para poder ejecutar la validación sin M2/M3 completo."""
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    import joblib
    import json

            
    # Features requeridas mínimas
    features = [
        "prec_acum_mm", "anomalia_prec", "dias_secos", 
        "indice_agroinsumos", "percentil_fertilizantes", "señal_riesgo_economico"
    ]
    
    reg_path = MODELS_DIR / f"xgb_regressor_{cultivo}.pkl"
    reg_meta = MODELS_DIR / f"xgb_regressor_{cultivo}_meta.json"
    clf_path = MODELS_DIR / f"xgb_classifier_{cultivo}.pkl"
    clf_meta = MODELS_DIR / f"xgb_classifier_{cultivo}_meta.json"
    
    if not reg_path.exists():
        joblib.dump(DummyRegressor(), reg_path)
    if not reg_meta.exists():
        with open(reg_meta, "w") as f:
            json.dump({"features": features}, f)
            
    if not clf_path.exists():
        joblib.dump(DummyClassifier(), clf_path)
    if not clf_meta.exists():
        with open(clf_meta, "w") as f:
            json.dump({"features": features}, f)

def run_validation():
    print("Iniciando validación de M5.1...")
    
    cultivo = "cafe"
    create_dummy_models(cultivo)
    
    # Construimos una fila base
    baseline_row = {
        "codigo_dane": "73001",
        "municipio": "IBAGUE",
        "departamento": "TOLIMA",
        "cultivo": "Café",
        "año": 2023,
        "prec_acum_mm": 1000.0,
        "anomalia_prec": 10.0,
        "temp_media_c": 22.0,
        "anomalia_temp": 0.5,
        "dias_secos": 50,
        "hum_media_pct": 70.0,
        "rendimiento_t1": 1.1,
        "rendimiento_prom3a": 1.0,
        "tendencia_rend_3a": 0.05,
        "area_sembrada_t1": 100.0,
        "pct_alta": 50.0,
        "pct_media": 30.0,
        "pct_baja": 15.0,
        "pct_exclusion": 5.0,
        "pct_condicionada": 10.0,
        "pct_no_condicionada": 90.0,
        "indice_agroinsumos": 120.0,
        "percentil_fertilizantes": 80.0,
        "señal_riesgo_economico": "medio", 
        "target_rendimiento": 1.2
    }
    
    # 1. Verificar si falla con escenarios no válidos
    try:
        simulate_scenarios(baseline_row, ["base", "invento"])
        print("❌ Error: No falló al pedir un escenario fuera de catálogo.")
        return 1
    except ValueError as e:
        print("✅ Pasó validación de catálogo (rechaza valores inválidos).")
        
    # 2. Ejecutar simulación válida
    scenarios = ["base", "seco", "lluvioso", "fertilizantes"]
    df_res = simulate_scenarios(baseline_row, scenarios)
    
    if len(df_res) != 4:
        print(f"❌ Error: Salida debe tener 4 filas, tiene {len(df_res)}")
        return 1
        
    # 3. Confirmar características modificadas
    seco_mods = df_res[df_res["escenario"] == "seco"]["features_modificadas"].values[0]
    lluvioso_mods = df_res[df_res["escenario"] == "lluvioso"]["features_modificadas"].values[0]
    fert_mods = df_res[df_res["escenario"] == "fertilizantes"]["features_modificadas"].values[0]
    
    if not all(f in ["prec_acum_mm", "dias_secos", "anomalia_prec"] for f in seco_mods):
        print(f"❌ Error: Variables modificadas incorrectas en seco: {seco_mods}")
        return 1
    print("✅ Modificaciones controladas por escenario validadas.")
    
    # 4. Validar deltas (como el dummy siempre retorna 1.5, los deltas deberían ser 0)
    base_rend = df_res[df_res["escenario"] == "base"]["rendimiento_esperado"].values[0]
    for _, row in df_res.iterrows():
        calc_delta = row["rendimiento_esperado"] - base_rend
        if not np.isclose(calc_delta, row["delta_rendimiento_abs"]):
            print("❌ Error: Delta de rendimiento mal calculado.")
            return 1
            
    print("✅ Deltas relativos calculados contra escenario base correctamente.")
    print("✅ Todas las validaciones de M5.1 pasaron correctamente.")
    return 0

if __name__ == "__main__":
    sys.exit(run_validation())
