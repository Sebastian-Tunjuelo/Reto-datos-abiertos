import sys
import json
import joblib
from pathlib import Path
from sklearn.metrics import accuracy_score
import logging

try:
    from xgboost import XGBClassifier
except ImportError:
    pass

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def run_validations():
    """
    Ejecuta las validaciones de los artefactos de M3.
    """
    models_dir = Path("models")
    
    cultivos = ["Café", "Cacao", "Maíz"]
    splits = ["train", "val", "test"]
    
    # 1. Verificar la existencia de los 3 .pkl, los 3 *_meta.json y models/m3_classification_metrics.json
    for cultivo in cultivos:
        model_path = models_dir / f"xgb_classifier_{cultivo.lower()}.pkl"
        meta_path = models_dir / f"xgb_classifier_{cultivo.lower()}_meta.json"
        
        assert model_path.exists(), f"Falta modelo de clasificación {model_path}"
        assert meta_path.exists(), f"Falta metadato {meta_path}"
        
        # 5. Cargar cada modelo con joblib.load() y confirmar que expone predict_proba
        try:
            model = joblib.load(model_path)
            assert hasattr(model, "predict_proba"), f"El modelo {cultivo} no expone predict_proba"
        except Exception as e:
            raise AssertionError(f"Fallo al cargar modelo {cultivo}: {e}")
            
        # 6. Cargar cada meta.json y comprobar que contiene feature_cols y best_iteration
        try:
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            assert "feature_cols" in meta and isinstance(meta["feature_cols"], list) and len(meta["feature_cols"]) > 0, f"feature_cols inválido en {cultivo}"
            assert "best_iteration" in meta and isinstance(meta["best_iteration"], int) and meta["best_iteration"] >= 0, f"best_iteration inválido en {cultivo}"
        except Exception as e:
            raise AssertionError(f"JSON meta inválido para {cultivo}: {e}")

    metrics_path = models_dir / "m3_classification_metrics.json"
    assert metrics_path.exists(), f"Falta archivo de métricas {metrics_path}"
    
    # 2. Cargar el JSON de métricas y comprobar que tiene 9 registros
    with open(metrics_path, "r", encoding="utf-8") as f:
        metrics = json.load(f)
        
    assert isinstance(metrics, list), "El JSON de métricas debe ser una lista"
    assert len(metrics) == 9, f"Se esperaban 9 registros de métricas, pero hay {len(metrics)}"
    
    expected_fields = ["cultivo", "split", "n", "accuracy", "precision", "recall", "f1_score", "auc_roc", "best_iteration"]
    
    # Track pairs seen
    seen_pairs = set()
    
    for r in metrics:
        # 3. Validar los campos esperados
        for field in expected_fields:
            assert field in r, f"Falta campo {field} en registro de métricas: {r}"
            
        # 4. Comprobar que split y cultivo pertenezcan a los esperados
        c = r["cultivo"]
        s = r["split"]
        assert c in cultivos, f"Cultivo desconocido {c}"
        assert s in splits, f"Split desconocido {s}"
        
        seen_pairs.add((c, s))
        
        # 7. Revisar rangos
        assert 0.0 <= r["auc_roc"] <= 1.0, f"auc_roc fuera de rango: {r['auc_roc']}"
        assert r["n"] > 0, f"Split size n = 0 detectado en {c} - {s}"
        
    assert len(seen_pairs) == 9, "Faltan combinaciones únicas de cultivo y split en las métricas"

    logging.info("Validación exitosa: Todos los artefactos de M3 se crearon y respetan el contrato.")

if __name__ == "__main__":
    try:
        run_validations()
        sys.exit(0)
    except AssertionError as e:
        logging.error(f"Validación falló: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error inesperado: {e}")
        sys.exit(1)
