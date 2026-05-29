"""
Genera colombia_mvp.geojson con polígonos aproximados (bounding boxes)
para los 15 municipios del MVP. Usa coordenadas reales del centroide
de cada municipio con un radio aproximado según el tamaño del municipio.
"""
import json
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Centroides reales (lat, lon) y radio aproximado en grados para cada municipio
# Radio basado en el área aproximada del municipio
MUNICIPIOS = [
    # (codigo_dane, municipio, departamento, lat, lon, radio_deg)
    ("73001", "Ibagué",               "Tolima",    4.4389,  -75.2322, 0.25),
    ("73168", "Chaparral",            "Tolima",    3.7267,  -75.4897, 0.35),
    ("41001", "Neiva",                "Huila",     2.9273,  -75.2819, 0.22),
    ("41298", "Garzón",               "Huila",     2.1997,  -75.6267, 0.28),
    ("41551", "Pitalito",             "Huila",     1.8500,  -76.0500, 0.25),
    ("68689", "San Vicente de Chucurí","Santander", 6.8939,  -73.3736, 0.30),
    ("68615", "Rionegro",             "Santander", 7.3756,  -73.1561, 0.28),
    ("05036", "Anorí",                "Antioquia", 7.0736,  -75.1408, 0.30),
    ("05030", "Amalfi",               "Antioquia", 6.9128,  -75.0736, 0.25),
    ("17541", "Pensilvania",          "Caldas",    5.3833,  -75.1667, 0.22),
    ("17524", "Palestina",            "Caldas",    5.0500,  -75.6667, 0.18),
    ("50001", "Villavicencio",        "Meta",      4.1420,  -73.6266, 0.25),
    ("19256", "El Tambo",             "Cauca",     2.4500,  -76.8167, 0.35),
    ("19418", "Miranda",              "Cauca",     3.2500,  -76.2167, 0.18),
    ("20001", "Valledupar",           "Cesar",    10.4631,  -73.2532, 0.28),
]


def make_polygon(lat: float, lon: float, r: float) -> dict:
    """Genera un polígono hexagonal aproximado centrado en (lat, lon) con radio r."""
    coords = []
    for i in range(7):  # 6 lados + cierre
        angle = math.radians(60 * i)
        coords.append([
            round(lon + r * math.cos(angle), 6),
            round(lat + r * math.sin(angle), 6),
        ])
    return {"type": "Polygon", "coordinates": [coords]}


features = []
for codigo, municipio, departamento, lat, lon, radio in MUNICIPIOS:
    features.append({
        "type": "Feature",
        "properties": {
            "codigo_dane": codigo,
            "municipio": municipio,
            "departamento": departamento,
        },
        "geometry": make_polygon(lat, lon, radio),
    })

geojson = {"type": "FeatureCollection", "features": features}

out_path = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "frontend", "public", "geo", "colombia_mvp.geojson"
)

with open(out_path, "w", encoding="utf-8") as f:
    json.dump(geojson, f, ensure_ascii=False, indent=2)

print(f"Generado: {out_path}")
print(f"Features: {len(features)}")
