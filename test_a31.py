from fastapi.testclient import TestClient
from orchestrator.main import app

client = TestClient(app)

def test_escenario():
    response = client.post('/escenario', json={
        'municipio': 'Chaparral',
        'cultivo': 'Café',
        'año': 2025,
        'escenarios': ['base', 'seco', 'lluvioso']
    })
    print(response.status_code)
    print(response.json())

test_escenario()
