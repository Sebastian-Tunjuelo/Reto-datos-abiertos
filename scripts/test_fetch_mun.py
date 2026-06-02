import sys
from pathlib import Path
# Añadir repo root
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from shared.socrata_client import fetch_all

if len(sys.argv) < 4:
    print('Uso: python test_fetch_mun.py MUNICIPIO START_ISO END_ISO')
    sys.exit(1)

municipio = sys.argv[1]
start = sys.argv[2]
end = sys.argv[3]

sel = (
    "municipio, date_trunc_y(fechaobservacion) AS año, "
    "sum(valorobservado) AS prec_acum_mm, count(*) AS n_observaciones"
)
where = (
    f"municipio = '{municipio}' AND valorobservado IS NOT NULL "
    f"AND fechaobservacion >= '{start}' AND fechaobservacion < '{end}'"
)
grp = "municipio, date_trunc_y(fechaobservacion)"
print('Ejecutando consulta reducida para', municipio, start, end)
res = fetch_all('s54a-sgyg', select=sel, where=where, group=grp, order=grp)
print('Resultado:', res)
