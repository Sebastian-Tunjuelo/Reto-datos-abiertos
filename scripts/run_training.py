import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from modules.predictive.feature_builder import build_feature_matrix, load_tabla_maestra, load_inputs, build_tabla_maestra
from modules.predictive.train_regressor import load_feature_matrix, prepare_regression_frame, train_regressors, evaluate_and_save_metrics as evaluate_reg
from modules.predictive.train_classifier import train_classifiers, evaluate_and_save_metrics as evaluate_clf

def run():
    print("Cargando matriz de features...")
    try:
        # Intentar cargar si existe
        df_matrix = load_feature_matrix()
    except Exception:
        print("Feature matrix no existe, se intentará construir...")
        # Construir tabla maestra
        try:
            tabla = load_tabla_maestra()
        except Exception:
            print("Tabla maestra no existe, construyendo inputs y tabla maestra...")
            inputs = load_inputs()
            tabla = build_tabla_maestra(inputs)
        df_matrix = build_feature_matrix(tabla)
        
    
    print(f"Matriz generada. Forma: {df_matrix.shape}")
    
    # Entrenar regresores (M2)
    print("\n--- Entrenando regresores (M2) ---")
    df_clean, feature_cols, target_col = prepare_regression_frame(df_matrix)
    print(f"Dataset de regresión listo. Forma: {df_clean.shape}")
    
    models_reg = train_regressors(df_clean, feature_cols, target_col)
    metrics_reg = evaluate_reg(df_clean, models_reg, feature_cols, target_col)
    
    print("Métricas de regresión (Validation):")
    for m in metrics_reg:
        if m["split"] == "val":
            print(f"- {m['cultivo']}: MAE={m['mae']:.3f}, R2={m.get('r2')}")
            
    # Entrenar clasificadores (M3)
    print("\n--- Entrenando clasificadores (M3) ---")
    # Generar 'target_riesgo' usando la regla de negocio que esté en target_riesgo.py o en la data if missing.
    from modules.predictive.target_riesgo import build_target_riesgo
    try:
        # Check if 'target_riesgo' is missing, it should be added
        if "target_riesgo" not in df_clean.columns:
            df_clean = build_target_riesgo(df_clean)
        
        models_clf = train_classifiers(df_clean, feature_cols, target_col="target_riesgo")
        metrics_clf = evaluate_clf(models_clf)
        
        print("Métricas de clasificación (Validation):")
        for m in metrics_clf:
            if m["split"] == "val":
                print(f"- {m['cultivo']}: AUC={m['auc_roc']:.3f}, F1={m['f1_score']:.3f}")
                
    except Exception as e:
        print(f"No se pudo entrenar M3 (Clasificador): {e}")

if __name__ == "__main__":
    run()