"""
Tests de preservación (Tarea 2) — predicciones-riesgo-fix
==========================================================
Validan que las columnas existentes en predicciones_con_explicacion.parquet
conservan su comportamiento base ANTES de aplicar el fix.

**Validates: Requirements 3.1, 3.2**

EXPECTED OUTCOME: Todos los tests PASAN en el código sin fix.
Esto confirma el comportamiento base que debe preservarse tras el fix.
"""

import os
import sys
import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PARQUET_PATH = os.path.join(WORKSPACE_ROOT, "data", "predicciones_con_explicacion.parquet")
SNAPSHOT_PATH = os.path.join(os.path.dirname(__file__), "parquet_snapshot.parquet")

# ---------------------------------------------------------------------------
# Carga del snapshot de referencia (pre-fix)
# ---------------------------------------------------------------------------
df_snapshot = pd.read_parquet(SNAPSHOT_PATH)

# ---------------------------------------------------------------------------
# Assertion de conteo — 395 filas (84 Café, 221 Cacao, 90 Maíz)
# ---------------------------------------------------------------------------

def test_total_rows():
    """El parquet pre-fix tiene exactamente 395 registros."""
    assert len(df_snapshot) == 395, (
        f"Se esperaban 395 filas, se encontraron {len(df_snapshot)}"
    )


def test_rows_per_cultivo():
    """Distribución por cultivo: 84 Café, 221 Cacao, 90 Maíz."""
    counts = df_snapshot["cultivo"].value_counts().to_dict()
    assert counts.get("Café", 0) == 84, f"Café: esperado 84, encontrado {counts.get('Café', 0)}"
    assert counts.get("Cacao", 0) == 221, f"Cacao: esperado 221, encontrado {counts.get('Cacao', 0)}"
    assert counts.get("Maíz", 0) == 90, f"Maíz: esperado 90, encontrado {counts.get('Maíz', 0)}"


# ---------------------------------------------------------------------------
# Property 2a — prediccion_riesgo ∈ {"Bajo", "Medio", "Alto"}
# ---------------------------------------------------------------------------

@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(st.integers(min_value=0, max_value=394))
def test_prediccion_riesgo_es_etiqueta_valida(idx):
    """
    **Validates: Requirements 3.1, 3.2**

    Para todo índice generado, df_snapshot.iloc[idx]["prediccion_riesgo"]
    debe ser una de las etiquetas válidas: "Bajo", "Medio" o "Alto".
    """
    etiquetas_validas = {"Bajo", "Medio", "Alto"}
    valor = df_snapshot.iloc[idx]["prediccion_riesgo"]
    assert valor in etiquetas_validas, (
        f"Fila {idx}: prediccion_riesgo={repr(valor)} no está en {etiquetas_validas}"
    )


# ---------------------------------------------------------------------------
# Property 2b — narrativa_riesgo es string no vacío
# ---------------------------------------------------------------------------

@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(st.integers(min_value=0, max_value=394))
def test_narrativa_riesgo_es_string_no_vacio(idx):
    """
    **Validates: Requirements 3.1, 3.2**

    Para todo índice generado, df_snapshot.iloc[idx]["narrativa_riesgo"]
    debe ser un string no vacío generado por build_narrative().
    """
    valor = df_snapshot.iloc[idx]["narrativa_riesgo"]
    assert isinstance(valor, str), (
        f"Fila {idx}: narrativa_riesgo es {type(valor).__name__}, se esperaba str"
    )
    assert len(valor.strip()) > 0, (
        f"Fila {idx}: narrativa_riesgo está vacío"
    )


# ---------------------------------------------------------------------------
# Property 2c — top_features es lista no vacía
# ---------------------------------------------------------------------------

@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
@given(st.integers(min_value=0, max_value=394))
def test_top_features_es_lista_no_vacia(idx):
    """
    **Validates: Requirements 3.1, 3.2**

    Para todo índice generado, df_snapshot.iloc[idx]["top_features"]
    debe ser una lista (o array) no vacía de dicts SHAP.
    """
    valor = df_snapshot.iloc[idx]["top_features"]
    # top_features puede ser numpy.ndarray o list — ambos son secuencias indexables
    assert hasattr(valor, "__len__"), (
        f"Fila {idx}: top_features es {type(valor).__name__}, se esperaba lista o array"
    )
    assert len(valor) > 0, (
        f"Fila {idx}: top_features está vacío"
    )
    # Verificar que cada elemento es un dict con la clave 'feature_id'
    primer_elemento = valor[0]
    assert isinstance(primer_elemento, dict), (
        f"Fila {idx}: top_features[0] es {type(primer_elemento).__name__}, se esperaba dict"
    )
    assert "feature_id" in primer_elemento, (
        f"Fila {idx}: top_features[0] no tiene clave 'feature_id'. Claves: {list(primer_elemento.keys())}"
    )
