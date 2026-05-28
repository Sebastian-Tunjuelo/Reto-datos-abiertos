from fastapi.testclient import TestClient
from orchestrator.main import app

client = TestClient(app)

def run_validations():
    print("Iniciando validaciones A2...")

    # 1. Disponibilidad básica
    print("Verificando OpenAPI...")
    response = client.get("/openapi.json")
    assert response.status_code == 200, "❌ /openapi.json no responde"
    openapi_schema = response.json()
    paths = openapi_schema.get("paths", {})
    assert "/rendimiento/{municipio}/{cultivo}" in paths, "❌ GET /rendimiento no expuesto en OpenAPI"
    assert "/clima/{municipio}" in paths, "❌ GET /clima no expuesto en OpenAPI"

    # 2. GET /rendimiento/{municipio}/{cultivo}
    print("Verificando rendimiento histórico...")
    res = client.get("/rendimiento/Chaparral/Café")
    assert res.status_code == 200, f"❌ GET /rendimiento falló: {res.text}"
    data = res.json()
    assert data["codigo_dane"] == "73168", "❌ codigo_dane incorrecto"
    assert data["municipio"] == "Chaparral", "❌ municipio incorrecto"
    assert data["departamento"] == "Tolima", "❌ departamento incorrecto"
    assert data["cultivo"] == "Café", "❌ cultivo incorrecto"
    assert "n_anios" in data, "❌ falta n_anios"
    assert "año_min" in data, "❌ falta año_min"
    assert "año_max" in data, "❌ falta año_max"
    
    serie = data.get("serie", [])
    assert len(serie) > 0, "❌ la serie está vacía"
    
    años = []
    for item in serie:
        assert "año" in item, "❌ falta año en serie"
        assert "rendimiento" in item, "❌ falta rendimiento"
        assert "area_sembrada" in item, "❌ falta area_sembrada"
        assert "rendimiento_prom3a" in item, "❌ falta rendimiento_prom3a"
        assert "tendencia_3a" in item, "❌ falta tendencia_3a"
        años.append(item["año"])
        
    assert años == sorted(años), "❌ la serie no está ordenada por año ascendente"
    assert len(años) == len(set(años)), "❌ hay años duplicados en la serie"
    
    res_codigo = client.get("/rendimiento/73168/Café")
    assert res_codigo.status_code == 200, "❌ consulta por código DANE falló"
    assert res_codigo.json() == data, "❌ consulta por nombre y código DANE difieren"
    
    res_inv_cult = client.get("/rendimiento/Chaparral/Papa")
    assert res_inv_cult.status_code == 422, "❌ cultivo inválido no retornó 422"
    
    res_inv_mun = client.get("/rendimiento/Gotica/Café")
    assert res_inv_mun.status_code == 404, "❌ municipio inválido no retornó 404"

    # 3. GET /clima/{municipio}
    print("Verificando serie climática...")
    res_clima = client.get("/clima/Chaparral")
    assert res_clima.status_code == 200, f"❌ GET /clima falló: {res_clima.text}"
    cdata = res_clima.json()
    assert cdata["codigo_dane"] == "73168", "❌ codigo_dane incorrecto"
    assert cdata["municipio"] == "Chaparral", "❌ municipio incorrecto"
    assert "n_anios" in cdata, "❌ falta n_anios"
    assert "año_min" in cdata, "❌ falta año_min"
    assert "año_max" in cdata, "❌ falta año_max"
    
    c_serie = cdata.get("serie", [])
    assert len(c_serie) > 0, "❌ la serie climática está vacía"
    
    c_años = []
    for item in c_serie:
        assert "año" in item, "❌ falta año"
        assert "prec_acum_mm" in item, "❌ falta prec_acum_mm"
        assert "anomalia_prec" in item, "❌ falta anomalia_prec"
        assert "anomalia_temp" in item, "❌ falta anomalia_temp"
        if item.get("hum_media_pct") is not None:
            assert 0 <= item["hum_media_pct"] <= 100, "❌ hum_media_pct fuera de rango"
        c_años.append(item["año"])
        
    assert c_años == sorted(c_años), "❌ la serie climática no está ordenada por año ascendente"
    assert len(c_años) == len(set(c_años)), "❌ hay años duplicados en la serie climática"
    
    res_c_codigo = client.get("/clima/73168")
    assert res_c_codigo.status_code == 200, "❌ consulta de clima por código DANE falló"
    assert res_c_codigo.json() == cdata, "❌ consulta de clima por nombre y código difieren"
    
    res_c_inv_mun = client.get("/clima/Gotica")
    assert res_c_inv_mun.status_code == 404, "❌ municipio inválido en clima no retornó 404"

    print("✅ Todas las validaciones A2 completadas con éxito.")

if __name__ == "__main__":
    run_validations()