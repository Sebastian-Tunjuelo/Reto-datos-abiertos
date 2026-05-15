"""
Configuración central del proyecto.
Carga variables de entorno desde .env.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Rutas
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = Path(os.getenv("DATA_DIR", str(ROOT_DIR / "data")))
MODELS_DIR = Path(os.getenv("MODELS_DIR", str(ROOT_DIR / "models")))

# API
SOCRATA_APP_TOKEN = os.getenv("SOCRATA_APP_TOKEN", "")
POSTGRES_URL = os.getenv("POSTGRES_URL", "")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Dataset IDs
DATASETS = {
    "eva_reciente": "uejq-wxrr",
    "eva_historica": "2pnw-mmge",
    "ideam_catalogo": "hp9r-jxuu",
    "ideam_precipitacion": "s54a-sgyg",
    "ideam_temperatura": "sbwg-7ju4",
    "ideam_humedad": "uext-mhny",
    "ideam_recientes": "57sv-p2fu",
    "upra_cafe": "kwvf-nwea",
    "upra_cacao": "jdjx-qer4",
    "upra_maiz_trad": "frjn-92um",
    "upra_maiz_tec1": "a5yc-uszt",
    "upra_maiz_tec2": "tzga-4zse",
    "upra_frontera": "fyc7-sbtz",
    "agroinsumos": "gwbi-fnzs",
    "precios_rap": "gdqq-rry2",
}

# Cultivos del MVP
CULTIVOS_MVP = ["Café", "Cacao", "Maíz"]

# Rangos de rendimiento válidos por cultivo (t/ha)
RENDIMIENTO_RANGOS = {
    "Café":  (0.3, 3.0),
    "Cacao": (0.2, 2.5),
    "Maíz":  (0.5, 10.0),
}

# Umbrales de riesgo
UMBRAL_RIESGO_ALTO = 0.20   # caída > 20% vs promedio histórico
UMBRAL_RIESGO_MEDIO = 0.10  # caída > 10%

# Validación temporal
TRAIN_HASTA = 2021
VAL_AÑO = 2022
TEST_DESDE = 2023
