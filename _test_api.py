"""Verificación rápida: catálogo de estaciones con filtro corregido."""
import os, sys
sys.path.insert(0, r"c:\Users\sebas\Desktop\Charla\siembrasegura")
from dotenv import load_dotenv
load_dotenv()

from shared.socrata_client import fetch_all

WHERE = (
    "municipio IN ("
    "'Ibagué','Chaparral','Neiva','Garzón','Pitalito',"
    "'San Vicente De Chucurí','San Vicente de Chucurí','San Vicente De Chucuri',"
    "'Rionegro','Anorí','Amalfi',"
    "'Pensilvania','Palestina','Villavicencio',"
    "'El Tambo','Miranda','Valledupar'"
    ")"
)

registros = fetch_all(dataset_id="hp9r-jxuu", where=WHERE)
print(f"Estaciones encontradas: {len(registros)}")
if registros:
    municipios = sorted(set(r.get("municipio","?") for r in registros))
    print(f"Municipios únicos ({len(municipios)}): {municipios}")
