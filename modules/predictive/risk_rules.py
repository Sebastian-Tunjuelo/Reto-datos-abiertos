"""
Módulo de reglas determinísticas para el semáforo de riesgo agrícola.

Reemplaza el XGBClassifier de M3 con una función explícita basada en la
caída de rendimiento predicho vs. el promedio histórico del municipio y cultivo.
"""
import logging
import math

from shared.config import UMBRAL_RIESGO_ALTO, UMBRAL_RIESGO_MEDIO

logger = logging.getLogger(__name__)


def calcular_etiqueta_riesgo(
    rend_predicho: float,
    promedio_historico: float,
    umbral_alto: float = UMBRAL_RIESGO_ALTO,
    umbral_medio: float = UMBRAL_RIESGO_MEDIO,
) -> tuple[str, float]:
    """
    Calcula la etiqueta de riesgo comparando el rendimiento predicho
    contra el promedio histórico del municipio y cultivo.

    La lógica es determinística: no depende de ningún modelo ML.

    Args:
        rend_predicho:      Rendimiento predicho por el regresor (t/ha).
        promedio_historico: Promedio histórico de rendimiento del municipio+cultivo (t/ha).
        umbral_alto:        Fracción de caída a partir de la cual el riesgo es "Alto".
                            Por defecto UMBRAL_RIESGO_ALTO de shared/config.py.
        umbral_medio:       Fracción de caída a partir de la cual el riesgo es "Medio".
                            Por defecto UMBRAL_RIESGO_MEDIO de shared/config.py.

    Returns:
        tuple[str, float]: (etiqueta, caida_pct) donde:
        - etiqueta:  'Alto' | 'Medio' | 'Bajo'
        - caida_pct: fracción de caída vs promedio histórico (0.0 si no hay caída)
    """
    # --- Validar promedio_historico ---
    if (
        promedio_historico is None
        or not isinstance(promedio_historico, (int, float))
        or math.isnan(promedio_historico)
        or not math.isfinite(promedio_historico)
        or promedio_historico <= 0
    ):
        logger.warning(
            "calcular_etiqueta_riesgo: promedio_historico inválido (%s). "
            "Retornando ('Bajo', 0.0).",
            promedio_historico,
        )
        return ("Bajo", 0.0)

    # --- Validar rend_predicho ---
    if (
        rend_predicho is None
        or not isinstance(rend_predicho, (int, float))
        or math.isnan(rend_predicho)
        or not math.isfinite(rend_predicho)
    ):
        return ("Bajo", 0.0)

    # --- Clampear rendimiento negativo a 0 ---
    if rend_predicho < 0:
        rend_predicho = 0.0

    # --- Calcular caída porcentual ---
    caida_pct = (promedio_historico - rend_predicho) / promedio_historico

    # --- Asignar etiqueta ---
    if caida_pct >= umbral_alto:
        return ("Alto", round(caida_pct, 6))

    if caida_pct >= umbral_medio:
        return ("Medio", round(caida_pct, 6))

    # caida_pct < umbral_medio (incluye valores negativos: rend > promedio)
    return ("Bajo", 0.0)
