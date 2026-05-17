# Contexto General — SiembraSegura IA

Documento de referencia para agentes IA. Leer al inicio de cada sesión para no tener que explorar el proyecto desde cero.

---

## Qué es el proyecto

**SiembraSegura IA** es una plataforma web que predice rendimiento agrícola y riesgo climático por municipio y cultivo en Colombia. Integra datos abiertos de EVA, IDEAM, UPRA y agroinsumos desde `datos.gov.co`. Entrega: rendimiento esperado (t/ha), semáforo de riesgo (Bajo/Medio/Alto), factores SHAP, recomendación accionable y asistente conversacional.

**Usuarios objetivo**: extensionistas, UMATAs, secretarías de agricultura.

---

## Cultivos del MVP

`Café` · `Cacao` · `Maíz`

---

## 15 Municipios del MVP

| Municipio | Departamento | Código DANE |
|-----------|-------------|------------|
| Ibagué | Tolima | `73001` |
| Chaparral | Tolima | `73168` |
| Neiva | Huila | `41001` |
| Garzón | Huila | `41298` |
| Pitalito | Huila | `41551` |
| San Vicente de Chucurí | Santander | `68689` |
| Rionegro | Santander | `68615` |
| Anorí | Antioquia | `05036` |
| Amalfi | Antioquia | `05030` |
| Pensilvania | Caldas | `17541` |
| Palestina | Caldas | `17524` |
| Villavicencio | Meta | `50001` |
| El Tambo | Cauca | `19256` |
| Miranda | Cauca | `19418` |
| Valledupar | Cesar | `20001` |

Definidos en `shared/dane_codes.py → MVP_CODIGOS`. **No redefinirlos en otros módulos.**

---

## Stack tecnológico

| Capa | Herramientas |
|------|-------------|
| Datos / Backend | Python 3.11, pandas 2.1.4, duckdb 0.9.2, pyarrow 14.0.2 |
| Modelo | xgboost 2.0.3, scikit-learn 1.3.2, shap 0.44.0 |
| API | FastAPI 0.109.0, uvicorn, pydantic 2.5.3 |
| Base de datos | PostgreSQL 15, SQLAlchemy 2.0.25 |
| Frontend | Next.js 14 (App Router), react-leaflet, react-plotly.js, shadcn/ui |
| Infra | Docker Compose |
| HTTP Socrata | `requests` — **nunca `sodapy`** |

---

## Estructura de carpetas

```
siembrasegura/
├── .kiro/
│   ├── steering/          ← contexto persistente para agentes (este archivo)
│   └── skills/            ← skills adicionales
├── modules/
│   ├── agricultural/      ← ingestion.py, features.py, api.py
│   ├── climate/           ← ingestion.py, aggregation.py, anomalies.py, api.py
│   ├── territorial/       ← ingestion.py, aptitude.py, frontier.py, api.py
│   ├── economic/          ← ingestion.py, risk_score.py, api.py
│   ├── predictive/        ← feature_builder.py, train.py, predict.py, scenarios.py, api.py
│   ├── explainability/    ← shap_engine.py, narratives.py, api.py
│   └── conversational/    ← rag.py, prompts.py, reports.py, api.py
├── orchestrator/          ← main.py, router.py, pipeline.py
├── shared/                ← utilidades comunes (ver abajo)
├── data/                  ← Parquets generados (gitignored)
├── models/                ← modelos .pkl entrenados (gitignored)
├── specs/                 ← specs de desarrollo por pipeline
│   └── D1_pipeline_eva/   ← D1.1, D1.2, D1.3, D1.4
├── docs/                  ← documentación de dominio y datos
└── frontend/              ← Next.js
```

---

## Módulo `shared/` — utilidades comunes

### `shared/config.py`
Variables globales del proyecto. Importar desde aquí, no hardcodear.

```python
DATA_DIR          # Path a data/
MODELS_DIR        # Path a models/
SOCRATA_APP_TOKEN # Token API (desde .env)
DATASETS          # dict con todos los IDs Socrata del proyecto
CULTIVOS_MVP      # ['Café', 'Cacao', 'Maíz']
RENDIMIENTO_RANGOS # {'Café': (0.3, 3.0), 'Cacao': (0.2, 2.5), 'Maíz': (0.5, 10.0)}
TRAIN_HASTA = 2021
VAL_AÑO = 2022
TEST_DESDE = 2023
```

### `shared/dane_codes.py`
```python
DANE_CODES    # nombre normalizado → código DANE
DANE_TO_NAME  # código DANE → nombre display (Title Case)
DANE_TO_DEPT  # código DANE → departamento
MVP_MUNICIPIOS
MVP_CODIGOS   # lista de 15 códigos DANE del MVP
get_codigo(municipio_nombre) → str | None
get_nombre(codigo_dane) → str | None
```

### `shared/normalization.py`
```python
normalize_name(name)         # → MAYÚSCULAS sin tildes (para comparación)
normalize_cultivo(cultivo)   # → 'Café'|'Cacao'|'Maíz'|None
normalize_dane_code(code)    # → str 5 dígitos con cero inicial
normalize_title_case(name)   # → Title Case con tildes (para display)
```

### `shared/socrata_client.py`
```python
fetch(dataset_id, select, where, group, order, limit, offset) → list[dict]
fetch_all(dataset_id, select, where, group, order, page_size) → list[dict]
# Paginación automática, reintentos 3x con backoff 1s/2s/4s
# Máximo 5000 registros por llamada
```

---

## Datasets Socrata — IDs y columnas reales

### EVA histórica 2007-2018 — `2pnw-mmge`
| Columna API | Columna unificada | Notas |
|-------------|-------------------|-------|
| `c_d_mun` | `codigo_dane` | ⚠️ puede venir sin cero inicial (`'5036'`) |
| `municipio` | `municipio` | MAYÚSCULAS |
| `departamento` | `departamento` | MAYÚSCULAS |
| `cultivo` | `cultivo` | `'CAFÉ'`, `'CACAO'`, `'MAÍZ'` |
| `a_o` | `año` | string |
| `periodo` | `periodo` | `'2015A'`, `'2015B'`, `'2015'` |
| `rendimiento_t_ha` | `rendimiento` | string, puede ser vacío o `'0'` |
| `rea_sembrada_ha` | `area_sembrada` | string |
| `rea_cosechada_ha` | `area_cosechada` | string |
| `producci_n_t` | `produccion` | string |
| `ciclo_de_cultivo` | `ciclo` | `'PERMANENTE'`\|`'TRANSITORIO'` |

### EVA reciente 2019-2024 — `uejq-wxrr`
| Columna API | Columna unificada | Notas |
|-------------|-------------------|-------|
| `c_digo_dane_municipio` | `codigo_dane` | ✅ bien formateado |
| `municipio` | `municipio` | Title Case |
| `departamento` | `departamento` | Title Case |
| `cultivo` | `cultivo` | `'Café'`, `'Cacao'`, `'Maíz'` |
| `a_o` | `año` | string |
| `periodo` | `periodo` | |
| `rendimiento` | `rendimiento` | string |
| `rea_sembrada` | `area_sembrada` | string |
| `rea_cosechada` | `area_cosechada` | string |
| `producci_n` | `produccion` | string |
| `ciclo_del_cultivo` | `ciclo` | |

### Otros datasets
| Dataset | ID Socrata | Advertencia |
|---------|-----------|-------------|
| Catálogo estaciones IDEAM | `hp9r-jxuu` | — |
| Precipitación IDEAM | `s54a-sgyg` | ⚠️ ~165M registros — siempre agregar con `$group` |
| Temperatura IDEAM | `sbwg-7ju4` | ⚠️ ~50M registros — siempre agregar |
| Humedad IDEAM | `uext-mhny` | — |
| Estaciones recientes | `57sv-p2fu` | — |
| Aptitud café UPRA | `kwvf-nwea` | ⚠️ geometrías — siempre usar `$group` |
| Aptitud cacao UPRA | `jdjx-qer4` | ⚠️ geometrías |
| Maíz tradicional UPRA | `frjn-92um` | ⚠️ solo 123 municipios |
| Maíz tec 1er sem UPRA | `a5yc-uszt` | ⚠️ geometrías |
| Maíz tec 2do sem UPRA | `tzga-4zse` | ⚠️ geometrías |
| Frontera agrícola UPRA | `fyc7-sbtz` | ⚠️ geometrías |
| Índice agroinsumos | `gwbi-fnzs` | ~200 registros, descargar completo |
| Precios RAP Eje Cafetero | `gdqq-rry2` | 4 ciudades |

---

## Esquema unificado EVA (compartido por todos los pipelines)

```python
# Columnas en orden exacto
COLUMNAS_EVA = [
    'codigo_dane',    # str, 5 dígitos, ej: '05036'
    'municipio',      # str, Title Case, ej: 'Anorí'
    'departamento',   # str, Title Case, ej: 'Antioquia'
    'cultivo',        # str: 'Café' | 'Cacao' | 'Maíz'
    'año',            # Int64, 2007–2024
    'periodo',        # str: '2022A' | '2022B' | '2022'
    'rendimiento',    # float64, nullable, t/ha
    'area_sembrada',  # float64, nullable, ha
    'area_cosechada', # float64, nullable, ha
    'produccion',     # float64, nullable, toneladas
    'ciclo',          # str, nullable: 'PERMANENTE' | 'TRANSITORIO'
    'fuente',         # str: 'historica' | 'reciente'
]
```

---

## Archivos Parquet esperados en `data/`

| Archivo | Descripción |
|---------|-------------|
| `eva_historica.parquet` | EVA 2007-2018 limpia, esquema unificado |
| `eva_reciente.parquet` | EVA 2019-2024 limpia, esquema unificado |
| `eva_completa.parquet` | Unión ordenada de los dos anteriores |
| `clima_agregado.parquet` | `codigo_dane, municipio, año, prec_acum_mm, temp_media_c, hum_media_pct, dias_secos, anomalia_prec, anomalia_temp` |
| `aptitud_cafe.parquet` | `codigo_dane, municipio, pct_alta, pct_media, pct_baja, pct_exclusion` |
| `aptitud_cacao.parquet` | mismo esquema |
| `aptitud_maiz.parquet` | mismo esquema (unión 3 datasets UPRA) |
| `frontera.parquet` | `codigo_dane, municipio, pct_condicionada, pct_no_condicionada` |
| `agroinsumos.parquet` | `fecha, año, mes, indice_total, fertilizantes, plaguicidas, urea, dap, kcl` |
| `tabla_maestra.parquet` | todos los anteriores cruzados por `codigo_dane + cultivo + año` |

---

## Specs de desarrollo

| ID | Archivo | Estado | Función objetivo |
|----|---------|--------|-----------------|
| D1.1 | `specs/D1_pipeline_eva/D1.1_historica.md` | ✅ Completo | `modules/agricultural/ingestion.py → download_eva_historica()` |
| D1.2 | `specs/D1_pipeline_eva/D1.2_reciente.md` | ✅ Completo | `modules/agricultural/ingestion.py → download_eva_reciente()` |
| D1.3 | `specs/D1_pipeline_eva/D1.3_unificacion.md` | ✅ Completo | `modules/agricultural/ingestion.py → run_pipeline()` |
| D1.4 | `specs/D1_pipeline_eva/D1.4_validacion.md` | ✅ Completo | `scripts/validate_d1.py` |
| D2.1 | `specs/D2_pipeline_clima/D2.1_estaciones.md` | ✅ Completo | `modules/climate/ingestion.py → download_catalogo_estaciones()` |
| D2.2 | `specs/D2_pipeline_clima/D2.2_precipitacion.md` | ✅ Completo | `modules/climate/ingestion.py → download_precipitacion()` |
| D2.3 | `specs/D2_pipeline_clima/D2.3_temperatura_humedad.md` | ✅ Completo | `modules/climate/ingestion.py → download_temperatura() + download_humedad()` |
| D2.4 | `specs/D2_pipeline_clima/D2.4_anomalias_guardado.md` | ✅ Completo | `modules/climate/aggregation.py → calcular_anomalias()` + `modules/climate/ingestion.py → run_pipeline()` |
| D2.5 | `specs/D2_pipeline_clima/D2.5_validacion.md` | ✅ Completo | `specs/D2_pipeline_clima/validate_d2.py → run_validations()` |

> Actualizar el campo `Estado` cuando una spec se complete.

---

## Convenciones de código

### Reglas generales
- No usar `inplace=True` en pandas
- No usar `sodapy` — usar `shared/socrata_client.py`
- No hardcodear códigos DANE ni rangos de rendimiento — usar `shared/`
- Conversiones numéricas: `pd.to_numeric(col, errors='coerce')`
- Guardar Parquet: `df.to_parquet(path, index=False, engine='pyarrow')`
- Llave de unión entre datasets: `codigo_dane` (string 5 dígitos)

### Logging
```python
import logging
logger = logging.getLogger(__name__)
# Formato configurado en shared/config.py
# Nivel: INFO por defecto
```

### Manejo de errores en ingesta
- Reintentar API máximo 3 veces con backoff 1s/2s/4s (ya implementado en `fetch_all`)
- Municipio sin datos: `logger.warning("[D1.x] Sin datos para {municipio} en ...")` — no fallar
- Rendimiento fuera de rango: → `None`, no eliminar la fila, loggear
- DataFrame vacío tras filtros: lanzar `ValueError` con mensaje descriptivo

### Validación temporal — regla estricta
```python
TRAIN_HASTA = 2021   # Train: 2007–2021
VAL_AÑO = 2022       # Validación: 2022
TEST_DESDE = 2023    # Test: 2023–2024 (no tocar hasta el final)
# NUNCA split aleatorio en datos temporales
```

### Features permitidas vs prohibidas en el modelo
```
✅ Permitidas: rendimiento_t1, rendimiento_prom3a, area_sembrada, variables climáticas, aptitud, agroinsumos
❌ Prohibidas (fuga): produccion mismo año, area_cosechada mismo año, rendimiento mismo año
```

---

## Filtros SoQL de referencia

### EVA histórica (incluye ambas formas del código DANE)
```
$where=cultivo IN ('CAFÉ','CACAO','MAÍZ') AND c_d_mun IN ('73001','73168','41001','41298','41551','68689','68615','05036','05030','17541','17524','50001','19256','19418','20001','5036','5030','17541','17524','50001','19256','19418','20001')
```

### EVA reciente
```
$where=cultivo IN ('Café','Cacao','Maíz') AND c_digo_dane_municipio IN ('73001','73168','41001','41298','41551','68689','68615','05036','05030','17541','17524','50001','19256','19418','20001')
```

### UPRA (siempre con $group para evitar geometrías)
```
$select=cod_dane_m,municipio,departamen,aptitud,sum(area_ha) AS area_total
$where=cod_dane_m IN ('73001',...)
$group=cod_dane_m,municipio,departamen,aptitud
```

---

## Estado actual del código

| Archivo | Estado |
|---------|--------|
| `shared/config.py` | ✅ Completo |
| `shared/dane_codes.py` | ✅ Completo |
| `shared/normalization.py` | ✅ Completo |
| `shared/socrata_client.py` | ✅ Completo |
| `modules/agricultural/__init__.py` | ✅ (vacío) |
| `modules/agricultural/ingestion.py` | ✅ D1.1 completo (D1.2, D1.3 pendientes) |
| `modules/climate/__init__.py` | ✅ Expone `download_catalogo_estaciones`, `download_precipitacion`, `download_temperatura`, `download_humedad`, `run_pipeline`, `load_clima_agregado`, `calcular_anomalias` |
| `modules/climate/ingestion.py` | ✅ D2.1, D2.2, D2.3, D2.4 completos |
| `modules/climate/aggregation.py` | ✅ D2.4 completo — `calcular_anomalias()` |
| `modules/territorial/` | 🔲 Por implementar |
| `modules/economic/` | 🔲 Por implementar |
| `modules/predictive/` | 🔲 Por implementar |
| `modules/explainability/` | 🔲 Por implementar |
| `modules/conversational/` | 🔲 Por implementar |
| `orchestrator/` | 🔲 Por implementar |
| `frontend/` | 🔲 Por implementar |
