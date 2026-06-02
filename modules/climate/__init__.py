"""
Módulo climático — SiembraSegura IA.

Expone las funciones de ingesta de datos IDEAM y orquestación del pipeline.
"""
from modules.climate.ingestion import (
    download_catalogo_estaciones,
    download_precipitacion,
    download_temperatura,
    download_humedad,
    run_pipeline,
    load_clima_agregado,
)
from modules.climate.aggregation import calcular_anomalias

__all__ = [
    "download_catalogo_estaciones",
    "download_precipitacion",
    "download_temperatura",
    "download_humedad",
    "run_pipeline",
    "load_clima_agregado",
    "calcular_anomalias",
]
