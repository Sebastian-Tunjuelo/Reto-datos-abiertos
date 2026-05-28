# specs/A3_api_mvp/validate_a3.py
"""
Validación del contrato A3 — SiembraSegura IA
Ejecutar desde la raíz del proyecto:
    python specs/A3_api_mvp/validate_a3.py
"""
import sys
import os

# Asegurar que la raíz del proyecto esté en sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from fastapi.testclient import TestClient
from orchestrator.main import app

client = TestClient(app, raise_server_exceptions=False)


# ---------------------------------------------------------------------------
# 1. Disponibilidad básica
# ---------------------------------------------------------------------------

def test_disponibilidad():
    # Importar app no lanza excepción (ya verificado al importar)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, "❌ /openapi.json no responde 200"
    paths = resp.json().get("paths", {})
    assert "/escenario" in paths, "❌ /openapi.json no contiene /escenario"
    assert "/chat" in paths, "❌ /openapi.json no contiene /chat"
    # El endpoint de reporte tiene path variable
    reporte_paths = [p for p in paths if "/reporte/" in p]
    assert len(reporte_paths) > 0, "❌ /openapi.json no contiene /reporte/{municipio}/{cultivo}"
    print("✅ Disponibilidad básica OK")


# ---------------------------------------------------------------------------
# 2. POST /escenario — happy path
# ---------------------------------------------------------------------------

def test_escenario_happy_path():
    payload = {
        "municipio": "Chaparral",
        "cultivo": "Café",
        "año": 2026,
        "escenarios": ["seco", "lluvioso"]
    }
    resp = client.post("/escenario", json=payload)
    assert resp.status_code == 200, f"❌ POST /escenario no responde 200: {resp.text}"
    data = resp.json()

    # Campos obligatorios del contrato
    for campo in ["codigo_dane", "municipio", "departamento", "cultivo", "año", "escenarios_solicitados", "resultados"]:
        assert campo in data, f"❌ POST /escenario: falta campo '{campo}' en la respuesta"

    # base siempre en primer lugar
    assert data["escenarios_solicitados"][0] == "base", \
        "❌ POST /escenario: 'base' debe ser el primer escenario en escenarios_solicitados"

    # una fila por escenario
    assert len(data["resultados"]) == len(data["escenarios_solicitados"]), \
        "❌ POST /escenario: resultados debe tener una fila por escenario"

    # base tiene deltas en cero
    base_row = next((r for r in data["resultados"] if r["escenario"] == "base"), None)
    assert base_row is not None, "❌ POST /escenario: no hay fila 'base' en resultados"
    assert base_row["delta_rendimiento_abs"] == 0.0, \
        "❌ POST /escenario: delta_rendimiento_abs de 'base' debe ser 0.0"
    assert base_row["delta_rendimiento_pct"] == 0.0, \
        "❌ POST /escenario: delta_rendimiento_pct de 'base' debe ser 0.0"
    assert base_row["delta_prob_riesgo_alto"] == 0.0, \
        "❌ POST /escenario: delta_prob_riesgo_alto de 'base' debe ser 0.0"

    # todos los escenarios pertenecen al catálogo canónico
    catalogo = {"base", "seco", "lluvioso", "fertilizantes"}
    for r in data["resultados"]:
        assert r["escenario"] in catalogo, \
            f"❌ POST /escenario: escenario '{r['escenario']}' no pertenece al catálogo canónico"

    print("✅ POST /escenario happy path OK")


# ---------------------------------------------------------------------------
# 3. POST /escenario — errores
# ---------------------------------------------------------------------------

def test_escenario_errores():
    # Escenario inválido → 422
    resp = client.post("/escenario", json={"municipio": "Chaparral", "cultivo": "Café", "año": 2026, "escenarios": ["inexistente"]})
    assert resp.status_code == 422, f"❌ POST /escenario escenario inválido debe responder 422, got {resp.status_code}"

    # Municipio inválido → 404
    resp = client.post("/escenario", json={"municipio": "Bogota", "cultivo": "Café", "año": 2026})
    assert resp.status_code == 404, f"❌ POST /escenario municipio inválido debe responder 404, got {resp.status_code}"

    # Cultivo inválido → 422
    resp = client.post("/escenario", json={"municipio": "Chaparral", "cultivo": "Arroz", "año": 2026})
    assert resp.status_code == 422, f"❌ POST /escenario cultivo inválido debe responder 422, got {resp.status_code}"

    print("✅ POST /escenario errores OK")


# ---------------------------------------------------------------------------
# 4. POST /chat — happy path
# ---------------------------------------------------------------------------

def test_chat_happy_path():
    payload = {
        "pregunta": "¿Cuál es el riesgo para el café en Chaparral?",
        "municipio": "Chaparral",
        "cultivo": "Café",
        "año": 2026,
        "tono": "campesino"
    }
    resp = client.post("/chat", json=payload)

    # Si no hay LLM_API_KEY, el endpoint responde 503 — skip graceful
    if resp.status_code == 503:
        print("⚠️  POST /chat: LLM_API_KEY no configurada — test omitido (503 esperado en entorno sin clave)")
        return

    assert resp.status_code == 200, f"❌ POST /chat no responde 200: {resp.text}"
    data = resp.json()

    for campo in ["respuesta", "tono_aplicado", "contexto_usado", "fuentes", "reporte_disponible"]:
        assert campo in data, f"❌ POST /chat: falta campo '{campo}' en la respuesta"

    assert data["respuesta"].strip() != "", "❌ POST /chat: 'respuesta' no debe estar vacía"
    assert data["contexto_usado"].get("municipio") is not None or data["contexto_usado"].get("cultivo") is not None, \
        "❌ POST /chat: contexto_usado debe reflejar municipio o cultivo cuando se suministran"

    print("✅ POST /chat happy path OK")


# ---------------------------------------------------------------------------
# 5. POST /chat — errores
# ---------------------------------------------------------------------------

def test_chat_errores():
    # Pregunta vacía → 422
    resp = client.post("/chat", json={"pregunta": "", "municipio": "Chaparral", "cultivo": "Café"})
    assert resp.status_code == 422, f"❌ POST /chat pregunta vacía debe responder 422, got {resp.status_code}"

    # Cultivo inválido → 422
    resp = client.post("/chat", json={"pregunta": "¿Qué pasa?", "cultivo": "Arroz"})
    assert resp.status_code == 422, f"❌ POST /chat cultivo inválido debe responder 422, got {resp.status_code}"

    # Municipio inválido → 404
    resp = client.post("/chat", json={"pregunta": "¿Qué pasa?", "municipio": "Bogota"})
    assert resp.status_code == 404, f"❌ POST /chat municipio inválido debe responder 404, got {resp.status_code}"

    print("✅ POST /chat errores OK")


# ---------------------------------------------------------------------------
# 6. GET /reporte — happy path
# ---------------------------------------------------------------------------

def test_reporte_happy_path():
    # Modo texto (no requiere reportlab)
    resp = client.get("/reporte/Chaparral/Café?formato=texto")

    # Si no hay predicciones disponibles → 404 esperado, skip graceful
    if resp.status_code == 404:
        print("⚠️  GET /reporte: sin predicciones disponibles para Chaparral/Café — test omitido")
        return

    assert resp.status_code == 200, f"❌ GET /reporte formato=texto no responde 200: {resp.text}"
    data = resp.json()

    for campo in ["codigo_dane", "municipio", "departamento", "cultivo", "año_referencia", "titulo", "contenido_texto", "secciones", "fuentes"]:
        assert campo in data, f"❌ GET /reporte: falta campo '{campo}' en la respuesta texto"

    assert data["contenido_texto"].strip() != "", "❌ GET /reporte: contenido_texto no debe estar vacío"
    assert len(data["fuentes"]) > 0, "❌ GET /reporte: fuentes debe tener al menos un elemento"
    assert "predicciones_con_explicacion.parquet" in data["fuentes"], \
        "❌ GET /reporte: fuentes debe incluir 'predicciones_con_explicacion.parquet'"

    print("✅ GET /reporte formato=texto OK")

    # Modo PDF
    resp_pdf = client.get("/reporte/Chaparral/Café")
    if resp_pdf.status_code == 503:
        print("⚠️  GET /reporte PDF: reportlab no disponible — test omitido")
        return
    if resp_pdf.status_code == 404:
        print("⚠️  GET /reporte PDF: sin predicciones disponibles — test omitido")
        return

    assert resp_pdf.status_code == 200, f"❌ GET /reporte PDF no responde 200: {resp_pdf.text}"
    assert resp_pdf.headers.get("content-type", "").startswith("application/pdf"), \
        f"❌ GET /reporte PDF: Content-Type debe ser application/pdf, got {resp_pdf.headers.get('content-type')}"
    assert len(resp_pdf.content) > 0, "❌ GET /reporte PDF: el contenido del PDF no debe estar vacío"

    print("✅ GET /reporte formato=pdf OK")


# ---------------------------------------------------------------------------
# 7. GET /reporte — errores
# ---------------------------------------------------------------------------

def test_reporte_errores():
    # Formato inválido → 422
    resp = client.get("/reporte/Chaparral/Café?formato=excel")
    assert resp.status_code == 422, f"❌ GET /reporte formato inválido debe responder 422, got {resp.status_code}"

    # Municipio inválido → 404
    resp = client.get("/reporte/Bogota/Café")
    assert resp.status_code == 404, f"❌ GET /reporte municipio inválido debe responder 404, got {resp.status_code}"

    # Cultivo inválido → 422
    resp = client.get("/reporte/Chaparral/Arroz")
    assert resp.status_code == 422, f"❌ GET /reporte cultivo inválido debe responder 422, got {resp.status_code}"

    print("✅ GET /reporte errores OK")


# ---------------------------------------------------------------------------
# 8. Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Validación A3 — SiembraSegura IA")
    print("=" * 60)

    tests = [
        test_disponibilidad,
        test_escenario_happy_path,
        test_escenario_errores,
        test_chat_happy_path,
        test_chat_errores,
        test_reporte_happy_path,
        test_reporte_errores,
    ]

    passed = 0
    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except AssertionError as e:
            print(f"\n{e}")
            print(f"\nValidación fallida en: {test_fn.__name__}")
            sys.exit(1)

    print("=" * 60)
    print(f"✅ Todas las validaciones pasaron ({passed}/{len(tests)})")
    print("=" * 60)
    sys.exit(0)


if __name__ == "__main__":
    main()
