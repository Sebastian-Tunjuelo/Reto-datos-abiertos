"""
Test de exploración de condición del bug — predicciones-riesgo-fix
===================================================================

**Validates: Requirements 1.3, 1.5**

PROPÓSITO:
    Este test codifica el comportamiento ESPERADO del parquet
    `data/predicciones_con_explicacion.parquet` una vez aplicado el fix.

    Ejecutado sobre el código SIN FIX, DEBE FALLAR — ese fallo confirma
    que el bug existe (columnas `rendimiento_esperado` y `etiqueta_riesgo`
    ausentes).

    Ejecutado sobre el código CON FIX, debe pasar — confirma que el bug
    fue corregido.

EXPECTED OUTCOME (código sin fix):
    - AssertionError / KeyError al verificar "rendimiento_esperado" in df.columns
    - AssertionError / KeyError al verificar "etiqueta_riesgo" in df.columns

NO MODIFICAR el código de producción ni este test cuando falle.
"""

import os
import pandas as pd
import pytest
from hypothesis import given, settings, HealthCheck
from hypothesis import strategies as st

# ---------------------------------------------------------------------------
# Ruta al parquet — relativa a la raíz del proyecto
# ---------------------------------------------------------------------------
_PARQUET_PATH = os.path.join(
    os.path.dirname(__file__),  # specs/predicciones-riesgo-fix/
    "..",                        # specs/
    "..",                        # siembrasegura/
    "data",
    "predicciones_con_explicacion.parquet",
)

# Cargar una sola vez para todos los tests
df = pd.read_parquet(_PARQUET_PATH)

# Número de filas esperadas (395 registros del MVP)
MAX_IDX = len(df) - 1  # 394


# ---------------------------------------------------------------------------
# Property 1 — Bug Condition: columna rendimiento_esperado presente
# ---------------------------------------------------------------------------

@given(st.integers(min_value=0, max_value=394))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_rendimiento_esperado_columna_presente(idx: int):
    """
    **Validates: Requirements 1.3**

    Para cualquier índice válido del parquet, la columna
    `rendimiento_esperado` debe existir y contener un float64 no nulo.

    EXPECTED FAILURE (sin fix):
        AssertionError: 'rendimiento_esperado' not in df.columns
    """
    # Verificar que la columna existe
    assert "rendimiento_esperado" in df.columns, (
        f"Bug confirmado: columna 'rendimiento_esperado' ausente en el parquet. "
        f"Índice probado: {idx}"
    )

    # Verificar que el valor en la fila idx es float64 no nulo
    # (solo se alcanza si la columna existe)
    bounded_idx = idx % len(df)
    valor = df.iloc[bounded_idx]["rendimiento_esperado"]

    assert pd.notna(valor), (
        f"rendimiento_esperado es nulo en fila {bounded_idx}"
    )
    assert isinstance(float(valor), float), (
        f"rendimiento_esperado no es float en fila {bounded_idx}: {type(valor)}"
    )


# ---------------------------------------------------------------------------
# Property 1 — Bug Condition: columna etiqueta_riesgo presente
# ---------------------------------------------------------------------------

@given(st.integers(min_value=0, max_value=394))
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_etiqueta_riesgo_columna_presente(idx: int):
    """
    **Validates: Requirements 1.5**

    Para cualquier índice válido del parquet, la columna `etiqueta_riesgo`
    debe existir y contener uno de los valores {"Bajo", "Medio", "Alto"}.

    EXPECTED FAILURE (sin fix):
        AssertionError: 'etiqueta_riesgo' not in df.columns
    """
    ETIQUETAS_VALIDAS = {"Bajo", "Medio", "Alto"}

    # Verificar que la columna existe
    assert "etiqueta_riesgo" in df.columns, (
        f"Bug confirmado: columna 'etiqueta_riesgo' ausente en el parquet. "
        f"Índice probado: {idx}"
    )

    # Verificar que el valor en la fila idx es una etiqueta válida
    bounded_idx = idx % len(df)
    etiqueta = df.iloc[bounded_idx]["etiqueta_riesgo"]

    assert etiqueta in ETIQUETAS_VALIDAS, (
        f"etiqueta_riesgo inválida en fila {bounded_idx}: '{etiqueta}'. "
        f"Valores válidos: {ETIQUETAS_VALIDAS}"
    )


# ---------------------------------------------------------------------------
# Test de columnas — verificación directa (no PBT) para diagnóstico rápido
# ---------------------------------------------------------------------------

def test_columnas_requeridas_presentes():
    """
    Verificación directa de la condición del bug.
    Falla inmediatamente con mensaje claro si las columnas faltan.

    **Validates: Requirements 1.3, 1.5**
    """
    columnas_actuales = set(df.columns)

    assert "rendimiento_esperado" in columnas_actuales, (
        f"BUG CONFIRMADO: 'rendimiento_esperado' no está en el parquet.\n"
        f"Columnas presentes: {sorted(columnas_actuales)}"
    )

    assert "etiqueta_riesgo" in columnas_actuales, (
        f"BUG CONFIRMADO: 'etiqueta_riesgo' no está en el parquet.\n"
        f"Columnas presentes: {sorted(columnas_actuales)}"
    )
