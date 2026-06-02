"""
validate_m6.py — Tests de criterios de aceptación para M6.1

Ejecutar desde la raíz del proyecto:
    .\.venv\Scripts\python.exe specs/M6_riesgo_deterministico/validate_m6.py
"""
import sys
from pathlib import Path

# Asegurar que la raíz del proyecto esté en sys.path
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from modules.predictive.risk_rules import calcular_etiqueta_riesgo
from shared.config import UMBRAL_RIESGO_ALTO, UMBRAL_RIESGO_MEDIO

TOLERANCE = 0.001
results = []


def check(test_id: str, condition: bool, description: str) -> bool:
    status = "PASS" if condition else "FAIL"
    print(f"  [{status}] {test_id}: {description}")
    results.append(condition)
    return condition


print("=" * 60)
print("validate_m6.py — M6.1 Semáforo de riesgo determinístico")
print("=" * 60)

# ------------------------------------------------------------------
# Test 1: rend_predicho=0.8, promedio_historico=1.2 → Alto, ≈0.333
# ------------------------------------------------------------------
print("\nTest 1 — Riesgo Alto (caída 33.3%)")
etiqueta, caida_pct = calcular_etiqueta_riesgo(0.8, 1.2)
check("T1a", etiqueta == "Alto", f'etiqueta == "Alto"  (got: "{etiqueta}")')
check("T1b", abs(caida_pct - 0.333) < TOLERANCE, f"caida_pct ≈ 0.333  (got: {caida_pct:.6f})")

# ------------------------------------------------------------------
# Test 2: rend_predicho=1.1, promedio_historico=1.2 → Medio, ≈0.083
# ------------------------------------------------------------------
print("\nTest 2 — Riesgo Medio (caída 8.3%)")
etiqueta, caida_pct = calcular_etiqueta_riesgo(1.1, 1.2)
check("T2a", etiqueta == "Medio", f'etiqueta == "Medio"  (got: "{etiqueta}")')
check("T2b", abs(caida_pct - 0.083) < TOLERANCE, f"caida_pct ≈ 0.083  (got: {caida_pct:.6f})")

# ------------------------------------------------------------------
# Test 3: rend_predicho=1.3, promedio_historico=1.2 → Bajo, 0.0
# ------------------------------------------------------------------
print("\nTest 3 — Riesgo Bajo (sin caída)")
etiqueta, caida_pct = calcular_etiqueta_riesgo(1.3, 1.2)
check("T3a", etiqueta == "Bajo", f'etiqueta == "Bajo"  (got: "{etiqueta}")')
check("T3b", caida_pct == 0.0, f"caida_pct == 0.0  (got: {caida_pct})")

# ------------------------------------------------------------------
# Test 4: promedio_historico=0.0 → ("Bajo", 0.0) sin excepción
# ------------------------------------------------------------------
print("\nTest 4 — promedio_historico=0.0 (sin excepción)")
try:
    etiqueta, caida_pct = calcular_etiqueta_riesgo(1.0, 0.0)
    check("T4a", etiqueta == "Bajo", f'etiqueta == "Bajo"  (got: "{etiqueta}")')
    check("T4b", caida_pct == 0.0, f"caida_pct == 0.0  (got: {caida_pct})")
    check("T4c", True, "no se lanzó excepción")
except Exception as exc:
    check("T4c", False, f"excepción inesperada: {exc}")

# ------------------------------------------------------------------
# Test 5: rend_predicho=-0.5 → clampea a 0.0, etiqueta "Alto"
# ------------------------------------------------------------------
print("\nTest 5 — Rendimiento negativo clampea a 0.0 → Alto")
etiqueta, caida_pct = calcular_etiqueta_riesgo(-0.5, 1.2)
check("T5a", etiqueta == "Alto", f'etiqueta == "Alto"  (got: "{etiqueta}")')

# ------------------------------------------------------------------
# Test 6: Umbrales en shared/config.py
# ------------------------------------------------------------------
print("\nTest 6 — Umbrales en shared/config.py")
check("T6a", UMBRAL_RIESGO_ALTO == 0.15, f"UMBRAL_RIESGO_ALTO == 0.15  (got: {UMBRAL_RIESGO_ALTO})")
check("T6b", UMBRAL_RIESGO_MEDIO == 0.07, f"UMBRAL_RIESGO_MEDIO == 0.07  (got: {UMBRAL_RIESGO_MEDIO})")

# ------------------------------------------------------------------
# Resumen
# ------------------------------------------------------------------
total = len(results)
passed = sum(results)
failed = total - passed

print("\n" + "=" * 60)
print(f"Resultado: {passed}/{total} tests pasaron")
if failed:
    print(f"FALLARON: {failed} test(s)")
else:
    print("Todos los tests PASARON ✓")
print("=" * 60)

sys.exit(0 if failed == 0 else 1)
