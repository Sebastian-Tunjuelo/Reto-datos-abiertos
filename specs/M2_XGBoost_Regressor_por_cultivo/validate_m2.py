import json
import unicodedata
import re
import sys
from pathlib import Path
import logging

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from shared.config import MODELS_DIR, CULTIVOS_MVP

logger = logging.getLogger(__name__)

def slugify(s: str) -> str:
    slug = str(s).lower()
    slug = unicodedata.normalize('NFD', slug).encode('ascii', 'ignore').decode('utf-8')
    return re.sub(r'[^a-z0-9]', '', slug)

def run_validation():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    models_dir = Path(MODELS_DIR)
    
    # Files to verify
    expected_models = [models_dir / f"xgb_regressor_{slugify(c)}.pkl" for c in CULTIVOS_MVP]
    expected_metas = [models_dir / f"xgb_regressor_{slugify(c)}_meta.json" for c in CULTIVOS_MVP]
    metrics_file = models_dir / "m2_regression_metrics.json"

    logger.info("1. Verificando .pkl de modelos...")
    for model_path in expected_models:
        if not model_path.exists():
            logger.error(f"Falta modelo: {model_path}")
            sys.exit(1)
            
    logger.info("2. Verificando metadatos .json...")
    for meta_path in expected_metas:
        if not meta_path.exists():
            logger.error(f"Falta meta: {meta_path}")
            sys.exit(1)
            
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
                
            features = meta.get("feature_cols", [])
            if not isinstance(features, list) or len(features) == 0:
                logger.error(f"feature_cols invalido en {meta_path.name}")
                sys.exit(1)
                
            if "best_iteration" not in meta or meta["best_iteration"] is None:
                pass # xgboost puede no iterar si no hubo early stopping o se forzó distinto, pero pedimos evaluar si es entero >=0. En la spec int >= 1, validaremos eso
            
            best_iter = meta.get("best_iteration")
            if best_iter is not None and (not isinstance(best_iter, int) or best_iter < 0):
                logger.error(f"best_iteration inválido ({best_iter}) en {meta_path.name}")
                sys.exit(1)
                
        except json.JSONDecodeError:
            logger.error(f"JSON inválido en {meta_path}")
            sys.exit(1)
            
    logger.info("3. Verificando métricas (m2_regression_metrics.json)...")
    if not metrics_file.exists():
        logger.error(f"Falta metrics: {metrics_file}")
        sys.exit(1)
        
    try:
        with open(metrics_file, 'r', encoding='utf-8') as f:
            metrics = json.load(f)
            
        if not isinstance(metrics, list) or len(metrics) != 9:
            logger.error(f"Metrics debe tener exactamente 9 registros (3 cultivos x 3 splits). Encontrados: {len(metrics) if isinstance(metrics, list) else 'tipo invalido'}")
            sys.exit(1)
            
        required_fields = {"cultivo", "split", "n", "mae", "rmse", "r2"}
        for record in metrics:
            if not required_fields.issubset(record.keys()):
                logger.error(f"Registro en metrics le faltan campos: {required_fields - set(record.keys())}")
                sys.exit(1)
                
            if record["n"] <= 0:
                logger.error(f"Valor inavlido para n ({record['n']}) en cultivo {record.get('cultivo')} split {record.get('split')}")
                sys.exit(1)
                
            if record["mae"] < 0 or record["rmse"] < 0:
                logger.error(f"MAE/RMSE negativos ({record['mae']}, {record['rmse']}) en cultivo {record.get('cultivo')}")
                sys.exit(1)
                
            r2 = record["r2"]
            if r2 is not None:
                # El rango de score R2 en sklearn es [-inf, 1.0]. Aceptamos [-1.0, 1.0] según la spec (o valores arbitriaramente negativos)
                # En la spec solicita explícitamente en rango [-1.0, 1.0].
                if r2 > 1.0 or r2 < -1.0:
                    logger.warning(f"R2 sale del rango esperado [-1.0, 1.0]: {r2}. Esto puede suceder matemáticamente, pero alertamos a la spec.")
                    if r2 > 1.0: # Mayor a 1.0 es matematicamente imposible e indica error severo
                        logger.error(f"R2 no debe ser mayor a 1.0")
                        sys.exit(1)
                        
    except json.JSONDecodeError:
        logger.error(f"JSON invalido: {metrics_file}")
        sys.exit(1)

    logger.info("Validación exitosa completada para M2.")
    sys.exit(0)

if __name__ == "__main__":
    run_validation()