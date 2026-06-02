import sys
from pathlib import Path

# Asegurar que el root del repo esté en sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared.socrata_client import fetch_all

sel = (
    "municipio, date_trunc_y(fechaobservacion) AS año, "
    "sum(valorobservado) AS prec_acum_mm, count(*) AS n_observaciones"
)
where = (
    "municipio = 'IBAGUE' AND valorobservado IS NOT NULL "
    "AND fechaobservacion >= '2023-01-01T00:00:00.000' "
    "AND fechaobservacion < '2023-07-01T00:00:00.000'"
)
grp = "municipio, date_trunc_y(fechaobservacion)"
print('Ejecutando consulta reducida...')
res = fetch_all('s54a-sgyg', select=sel, where=where, group=grp, order=grp)
print('Resultado:', res)
