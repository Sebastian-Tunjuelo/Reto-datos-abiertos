# Convenciones de Desarrollo — SiembraSegura IA

## Esquema unificado de EVA (después de normalización)
```python
EVA_SCHEMA = {
    'codigo_dane': str,      # '73001' — 5 dígitos con cero a la izquierda
    'municipio': str,        # 'Ibagué' — Title Case normalizado
    'departamento': str,     # 'Tolima'
    'cultivo': str,          # 'Café' | 'Cacao' | 'Maíz'
    'año': int,              # 2007..2024
    'periodo': str,          # '2022A' | '2022B'
    'rendimiento': float,    # t/ha — None si no disponible
    'area_sembrada': float,  # ha
    'area_cosechada': float, # ha
    'produccion': float,     # toneladas
    'ciclo': str,            # 'PERMANENTE' | 'TRANSITORIO'
    'fuente': str,           # 'historica' | 'reciente'
}
```

## Archivos Parquet esperados en data/
| Archivo | Columnas clave |
|---------|---------------|
| `eva_historica.parquet` | codigo_dane, municipio, departamento, cultivo, año, periodo, rendimiento, area_sembrada, produccion, ciclo, fuente |
| `eva_reciente.parquet` | mismo esquema |
| `eva_completa.parquet` | unión de los dos anteriores |
| `clima_agregado.parquet` | codigo_dane, municipio, año, prec_acum_mm, temp_media_c, hum_media_pct, dias_secos, anomalia_prec, anomalia_temp |
| `aptitud_cafe.parquet` | codigo_dane, municipio, pct_alta, pct_media, pct_baja, pct_exclusion |
| `aptitud_cacao.parquet` | mismo esquema |
| `aptitud_maiz.parquet` | mismo esquema (unión 3 datasets) |
| `frontera.parquet` | codigo_dane, municipio, pct_condicionada, pct_no_condicionada |
| `agroinsumos.parquet` | fecha, año, mes, indice_total, fertilizantes, plaguicidas, urea, dap, kcl |
| `tabla_maestra.parquet` | todos los anteriores cruzados por codigo_dane + cultivo + año |

## Validación temporal — regla estricta
- Train: 2007–2021
- Validación: 2022
- Test: 2023–2024
- **NUNCA mezclar años futuros en entrenamiento**

## Features permitidas vs prohibidas
### ✅ Permitidas
- rendimiento_t1, rendimiento_prom3a, tendencia_rend
- area_sembrada (del año actual), cambio_area
- prec_acum_mm, anomalia_prec, dias_secos
- temp_media_c, anomalia_temp, hum_media_pct
- pct_aptitud_alta, pct_aptitud_media, pct_condicionada
- indice_fertilizantes, indice_plaguicidas

### ❌ Prohibidas (fuga de información)
- produccion del mismo año
- area_cosechada del mismo año
- rendimiento del mismo año (es la variable objetivo)

## Etiqueta de riesgo
```python
def calcular_riesgo(rendimiento_actual: float, promedio_historico: float) -> str:
    if promedio_historico == 0:
        return 'Bajo'
    caida = (promedio_historico - rendimiento_actual) / promedio_historico
    if caida >= 0.20:
        return 'Alto'
    elif caida >= 0.10:
        return 'Medio'
    return 'Bajo'
```

## Variables de entorno (.env)
```
SOCRATA_APP_TOKEN=
POSTGRES_URL=postgresql://user:pass@localhost:5432/siembrasegura
LLM_API_KEY=
DATA_DIR=./data
MODELS_DIR=./models
LOG_LEVEL=INFO
```

## Manejo de errores en ingesta
- Reintentar API máximo 3 veces con backoff exponencial (1s, 2s, 4s)
- Municipio sin datos climáticos: registrar en log, no fallar el pipeline
- Rendimiento fuera de rango: marcar como None, no eliminar la fila
- Loggear siempre: registros descargados, registros válidos, registros descartados

## Formato de logs
```python
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(name)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger(__name__)
```
