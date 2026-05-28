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

| Municipio              | Departamento | Código DANE |
| ---------------------- | ------------ | ----------- |
| Ibagué                 | Tolima       | `73001`     |
| Chaparral              | Tolima       | `73168`     |
| Neiva                  | Huila        | `41001`     |
| Garzón                 | Huila        | `41298`     |
| Pitalito               | Huila        | `41551`     |
| San Vicente de Chucurí | Santander    | `68689`     |
| Rionegro               | Santander    | `68615`     |
| Anorí                  | Antioquia    | `05036`     |
| Amalfi                 | Antioquia    | `05030`     |
| Pensilvania            | Caldas       | `17541`     |
| Palestina              | Caldas       | `17524`     |
| Villavicencio          | Meta         | `50001`     |
| El Tambo               | Cauca        | `19256`     |
| Miranda                | Cauca        | `19418`     |
| Valledupar             | Cesar        | `20001`     |

Definidos en `shared/dane_codes.py → MVP_CODIGOS`. **No redefinirlos en otros módulos.**

---

## Stack tecnológico

| Capa            | Herramientas                                                       |
| --------------- | ------------------------------------------------------------------ |
| Datos / Backend | Python 3.10, pandas 2.1.4, duckdb 0.9.2, pyarrow 14.0.2            |
| Modelo          | xgboost 2.0.3, scikit-learn 1.3.2, shap 0.44.0                     |
| API             | FastAPI 0.109.0, uvicorn, pydantic 2.5.3                           |
| Base de datos   | PostgreSQL 15, SQLAlchemy 2.0.25                                   |
| Frontend        | Next.js 14 (App Router), react-leaflet, react-plotly.js, shadcn/ui |
| Infra           | Docker Compose                                                     |
| HTTP Socrata    | `requests` — **nunca `sodapy`**                                    |

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

| Columna API        | Columna unificada | Notas                                      |
| ------------------ | ----------------- | ------------------------------------------ |
| `c_d_mun`          | `codigo_dane`     | ⚠️ puede venir sin cero inicial (`'5036'`) |
| `municipio`        | `municipio`       | MAYÚSCULAS                                 |
| `departamento`     | `departamento`    | MAYÚSCULAS                                 |
| `cultivo`          | `cultivo`         | `'CAFÉ'`, `'CACAO'`, `'MAÍZ'`              |
| `a_o`              | `año`             | string                                     |
| `periodo`          | `periodo`         | `'2015A'`, `'2015B'`, `'2015'`             |
| `rendimiento_t_ha` | `rendimiento`     | string, puede ser vacío o `'0'`            |
| `rea_sembrada_ha`  | `area_sembrada`   | string                                     |
| `rea_cosechada_ha` | `area_cosechada`  | string                                     |
| `producci_n_t`     | `produccion`      | string                                     |
| `ciclo_de_cultivo` | `ciclo`           | `'PERMANENTE'`\|`'TRANSITORIO'`            |

### EVA reciente 2019-2024 — `uejq-wxrr`

| Columna API             | Columna unificada | Notas                         |
| ----------------------- | ----------------- | ----------------------------- |
| `c_digo_dane_municipio` | `codigo_dane`     | ✅ bien formateado            |
| `municipio`             | `municipio`       | Title Case                    |
| `departamento`          | `departamento`    | Title Case                    |
| `cultivo`               | `cultivo`         | `'Café'`, `'Cacao'`, `'Maíz'` |
| `a_o`                   | `año`             | string                        |
| `periodo`               | `periodo`         |                               |
| `rendimiento`           | `rendimiento`     | string                        |
| `rea_sembrada`          | `area_sembrada`   | string                        |
| `rea_cosechada`         | `area_cosechada`  | string                        |
| `producci_n`            | `produccion`      | string                        |
| `ciclo_del_cultivo`     | `ciclo`           |                               |

### Otros datasets

| Dataset                   | ID Socrata  | Advertencia                                       |
| ------------------------- | ----------- | ------------------------------------------------- |
| Catálogo estaciones IDEAM | `hp9r-jxuu` | —                                                 |
| Precipitación IDEAM       | `s54a-sgyg` | ⚠️ ~165M registros — siempre agregar con `$group` |
| Temperatura IDEAM         | `sbwg-7ju4` | ⚠️ ~50M registros — siempre agregar               |
| Humedad IDEAM             | `uext-mhny` | —                                                 |
| Estaciones recientes      | `57sv-p2fu` | —                                                 |
| Aptitud café UPRA         | `kwvf-nwea` | ⚠️ geometrías — siempre usar `$group`             |
| Aptitud cacao UPRA        | `jdjx-qer4` | ⚠️ geometrías                                     |
| Maíz tradicional UPRA     | `frjn-92um` | ⚠️ solo 123 municipios                            |
| Maíz tec 1er sem UPRA     | `a5yc-uszt` | ⚠️ geometrías                                     |
| Maíz tec 2do sem UPRA     | `tzga-4zse` | ⚠️ geometrías                                     |
| Frontera agrícola UPRA    | `fyc7-sbtz` | ⚠️ geometrías                                     |
| Índice agroinsumos        | `gwbi-fnzs` | ~200 registros, descargar completo                |
| Precios RAP Eje Cafetero  | `gdqq-rry2` | 4 ciudades                                        |

### Agroinsumos (gwbi-fnzs) — columnas reales

| Columna API           | Columna unificada |
| --------------------- | ----------------- |
| `fecha`               | `fecha`           |
| `indice_total`        | `indice_total`    |
| `total_fertilizantes` | `fertilizantes`   |
| `total_plaguicidas`   | `plaguicidas`     |
| `urea_46`             | `urea`            |
| `dap_18_46`           | `dap`             |
| `kcl_0_0_60`          | `kcl`             |

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

| Archivo                       | Descripción                                                                                                                 |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| `eva_historica.parquet`       | EVA 2007-2018 limpia, esquema unificado                                                                                     |
| `eva_reciente.parquet`        | EVA 2019-2024 limpia, esquema unificado                                                                                     |
| `eva_completa.parquet`        | Unión ordenada de los dos anteriores                                                                                        |
| `clima_agregado.parquet`      | `codigo_dane, municipio, año, prec_acum_mm, temp_media_c, hum_media_pct, dias_secos, anomalia_prec, anomalia_temp`          |
| `aptitud_cafe.parquet`        | `codigo_dane, municipio, pct_alta, pct_media, pct_baja, pct_exclusion`                                                      |
| `aptitud_cacao.parquet`       | mismo esquema                                                                                                               |
| `aptitud_maiz.parquet`        | mismo esquema (unión 3 datasets UPRA)                                                                                       |
| `frontera.parquet`            | `codigo_dane, municipio, pct_condicionada, pct_no_condicionada`                                                             |
| `agroinsumos_mensual.parquet` | `fecha, año, mes, indice_total, fertilizantes, plaguicidas, urea, dap, kcl`                                                 |
| `agroinsumos.parquet`         | `año, indice_total, fertilizantes, plaguicidas, urea, dap, kcl, n_meses, pct_fertilizantes, pct_indice_total, señal_riesgo` |
| `tabla_maestra.parquet`       | todos los anteriores cruzados por `codigo_dane + cultivo + año`                                                             |

---

## Specs de desarrollo

| ID   | Archivo                                                                    | Estado      | Función objetivo                                                                                          |
| ---- | -------------------------------------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------------- |
| D1.1 | `specs/D1_pipeline_eva/D1.1_historica.md`                                  | ✅ Completo | `modules/agricultural/ingestion.py → download_eva_historica()`                                            |
| D1.2 | `specs/D1_pipeline_eva/D1.2_reciente.md`                                   | ✅ Completo | `modules/agricultural/ingestion.py → download_eva_reciente()`                                             |
| D1.3 | `specs/D1_pipeline_eva/D1.3_unificacion.md`                                | ✅ Completo | `modules/agricultural/ingestion.py → run_pipeline()`                                                      |
| D1.4 | `specs/D1_pipeline_eva/D1.4_validacion.md`                                 | ✅ Completo | `scripts/validate_d1.py`                                                                                  |
| D2.1 | `specs/D2_pipeline_clima/D2.1_estaciones.md`                               | ✅ Completo | `modules/climate/ingestion.py → download_catalogo_estaciones()`                                           |
| D2.2 | `specs/D2_pipeline_clima/D2.2_precipitacion.md`                            | ✅ Completo | `modules/climate/ingestion.py → download_precipitacion()`                                                 |
| D2.3 | `specs/D2_pipeline_clima/D2.3_temperatura_humedad.md`                      | ✅ Completo | `modules/climate/ingestion.py → download_temperatura() + download_humedad()`                              |
| D2.4 | `specs/D2_pipeline_clima/D2.4_anomalias_guardado.md`                       | ✅ Completo | `modules/climate/aggregation.py → calcular_anomalias()` + `modules/climate/ingestion.py → run_pipeline()` |
| D2.5 | `specs/D2_pipeline_clima/D2.5_validacion.md`                               | ✅ Completo | `specs/D2_pipeline_clima/validate_d2.py → run_validations()`                                              |
| D3.1 | `specs/D3_pipeline_territorial/D3.1_aptitud_cafe_cacao.md`                 | ✅ Completo | `modules/territorial/ingestion.py → download_aptitud_cafe() + download_aptitud_cacao()`                   |
| D3.2 | `specs/D3_pipeline_territorial/D3.2_aptitud_maiz.md`                       | ✅ Completo | `modules/territorial/ingestion.py → download_aptitud_maiz()`                                              |
| D3.3 | `specs/D3_pipeline_territorial/D3.3_frontera.md`                           | ✅ Completo | `modules/territorial/ingestion.py → download_frontera()`                                                  |
| D3.4 | `specs/D3_pipeline_territorial/D3.4_validacion.md`                         | ✅ Completo | `specs/D3_pipeline_territorial/validate_d3.py → run_validations()`                                        |
| D4.1 | `specs/D4_pipeline_economico/D4.1_descarga_limpieza.md`                    | ✅ Completo | `modules/economic/ingestion.py → download_agroinsumos()`                                                  |
| D4.2 | `specs/D4_pipeline_economico/D4.2_agregacion_anual.md`                     | ✅ Completo | `modules/economic/ingestion.py → build_agroinsumos_anual()` + `run_pipeline()`                            |
| D4.3 | `specs/D4_pipeline_economico/D4.3_validacion.md`                           | ✅ Completo | `specs/D4_pipeline_economico/validate_d4.py → run_validations()`                                          |
| D5.1 | `specs/D5_tabla_maestra/D5.1_carga_validacion_inputs.md`                   | ✅ Completo | `modules/predictive/feature_builder.py → load_inputs()`                                                   |
| D5.2 | `specs/D5_tabla_maestra/D5.2_features_eva.md`                              | ✅ Completo | `modules/predictive/feature_builder.py → build_eva_features()`                                            |
| D5.3 | `specs/D5_tabla_maestra/D5.3_cruce_features.md`                            | ✅ Completo | `modules/predictive/feature_builder.py → build_tabla_maestra()` + `load_tabla_maestra()`                  |
| D5.4 | `specs/D5_tabla_maestra/D5.4_validacion.md`                                | ✅ Completo | `specs/D5_tabla_maestra/validate_d5.py → run_validations()`                                               |
| M1.1 | `specs/M1_feature_engineering/M1.1_validacion_entrada_clima.md`            | ✅ Completo | `modules/predictive/feature_builder.py → _validate_input()` + `_apply_climate_ranges()`                   |
| M1.2 | `specs/M1_feature_engineering/M1.2_rezagos_temporales.md`                  | ✅ Completo | `modules/predictive/feature_builder.py → _build_lag_features()`                                           |
| M1.3 | `specs/M1_feature_engineering/M1.3_aptitud_agroinsumos_schema.md`          | ✅ Completo | `modules/predictive/feature_builder.py → build_feature_matrix()`                                          |
| M1.4 | `specs/M1_feature_engineering/M1.4_validacion.md`                          | ✅ Completo | `specs/M1_feature_engineering/validate_m1.py → run_validations()`                                         |
| M2.1 | `specs/M2_XGBoost_Regressor_por_cultivo/M2.1_carga_validacion_features.md` | ✅ Completo | `modules/predictive/train_regressor.py → load_feature_matrix()`, `prepare_regression_frame()`             |
| M2.2 | `specs/M2_XGBoost_Regressor_por_cultivo/M2.2_entrenamiento_por_cultivo.md` | ✅ Completo | `modules/predictive/train_regressor.py → train_regressors()`, `_train_single_cultivo()`                   |
| M2.3 | `specs/M2_XGBoost_Regressor_por_cultivo/M2.3_evaluacion_y_guardado.md`     | ✅ Completo | `modules/predictive/train_regressor.py → evaluate_and_save_metrics()`                                     |
| M2.4 | `specs/M2_XGBoost_Regressor_por_cultivo/M2.4_validacion.md`                | ✅ Completo | `specs/M2_XGBoost_Regressor_por_cultivo/validate_m2.py → run_validation()`                                |
| M3.1 | `specs/M3_XGBoost_Classifier_de_riesgo/M3.1_construccion_target.md`        | ✅ Completo | `modules/predictive/target_riesgo.py → build_target_riesgo()`                                             |
| M3.2 | `specs/M3_XGBoost_Classifier_de_riesgo/M3.2_entrenamiento_clasificador.md` | ✅ Completo | `modules/predictive/train_classifier.py → train_classifiers()`, `_train_single_cultivo_classifier()`      |
| M3.3 | `specs/M3_XGBoost_Classifier_de_riesgo/M3.3_evaluacion_y_guardado.md`      | ✅ Completo | `modules/predictive/train_classifier.py → evaluate_and_save_metrics()`                                    |
| M3.4 | `specs/M3_XGBoost_Classifier_de_riesgo/M3.4_validacion.md`                 | ✅ Completo | `specs/M3_XGBoost_Classifier_de_riesgo/validate_m3.py → run_validations()`                                |
| M4.1 | `specs/M4_Explicabilidad_SHAP/M4.1_calculo_shap.md`                        | ✅ Completo | `modules/explainability/shap_calculator.py → build_and_save_explainers()`                                 |
| M4.2 | `specs/M4_Explicabilidad_SHAP/M4.2_top_features.md`                        | ✅ Completo | `modules/explainability/feature_extractor.py → get_top_n_features()`                                      |
| M4.3 | `specs/M4_Explicabilidad_SHAP/M4.3_narrativas.md`                          | ✅ Completo | `modules/explainability/narrative_builder.py → build_and_save_narratives_df()`                            |
| M4.4 | `specs/M4_Explicabilidad_SHAP/M4.4_validacion.md`                          | ✅ Completo | `specs/M4_Explicabilidad_SHAP/validate_m4.py → validate_m4()`                                             |
| M5.1 | `specs/M5_simulacion_escenarios/M5.1_funcion_escenarios.md`                | ✅ Completo | `modules/predictive/scenarios.py → simulate_scenarios()` + `validate_m5.py`                               |

> Actualizar el campo `Estado` cuando una spec se complete.

---

## Semana 2 — Modelo (M1–M5)

- **M1 Feature Engineering:** valida clima, calcula rezagos, integra aptitud y agroinsumos, y genera `data/feature_matrix.parquet` con esquema canonico + `validate_m1.py`.
- **M2 Regressor por cultivo:** entrena 3 XGBoost (Cafe, Cacao, Maiz) con split temporal, guarda modelos, metadatos y `models/m2_regression_metrics.json` + `validate_m2.py`.
- **M3 Classifier de riesgo:** construye `target_riesgo` (caida > 15% vs promedio historico), entrena 3 clasificadores, guarda artefactos y `models/m3_classification_metrics.json` + `validate_m3.py`.
- **M4 SHAP y narrativas:** calcula explainers SHAP, extrae top features y genera narrativas; produce `models/shap_explainer_*.pkl`, `data/predicciones_con_explicacion.parquet` + `validate_m4.py`.
- **M5 Escenarios:** simula shocks deterministas (`seco`, `lluvioso`, `fertilizantes`) sobre una fila base, compara contra `base`, expone `modules/predictive/scenarios.py`, cache opcional y `validate_m5.py`.

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

### Variables de entorno para muestreo IDEAM (modo rápido)

Para acelerar descargas climáticas en pruebas:

```bash
IDEAM_ESTACIONES_POR_MUN=1  # selecciona N estaciones por municipio
IDEAM_MAX_ESTACIONES=50     # límite global alternativo (si no se usa por municipio)
IDEAM_YEAR_START=2023
IDEAM_YEAR_END=2024
IDEAM_YEAR_CHUNK=1
SOCRATA_TIMEOUT=300
SOCRATA_MAX_RETRIES=5
```

> Usar solo para pruebas; reduce cobertura climática.

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

| Archivo                             | Estado                                                                                                                                                                      |
| ----------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `shared/config.py`                  | ✅ Completo                                                                                                                                                                 |
| `shared/dane_codes.py`              | ✅ Completo                                                                                                                                                                 |
| `shared/normalization.py`           | ✅ Completo                                                                                                                                                                 |
| `shared/socrata_client.py`          | ✅ Completo                                                                                                                                                                 |
| `modules/agricultural/__init__.py`  | ✅ (vacío)                                                                                                                                                                  |
| `modules/agricultural/ingestion.py` | ✅ D1.1–D1.3 completos                                                                                                                                                      |
| `modules/climate/__init__.py`       | ✅ Expone `download_catalogo_estaciones`, `download_precipitacion`, `download_temperatura`, `download_humedad`, `run_pipeline`, `load_clima_agregado`, `calcular_anomalias` |
| `modules/climate/ingestion.py`      | ✅ D2.1, D2.2, D2.3, D2.4 completos                                                                                                                                         |
| `modules/climate/aggregation.py`    | ✅ D2.4 completo — `calcular_anomalias()`                                                                                                                                   |
| `modules/territorial/__init__.py`   | ✅ Expone `download_aptitud_cafe`, `download_aptitud_cacao`, `download_aptitud_maiz`, `download_frontera`                                                                   |
| `modules/territorial/ingestion.py`  | ✅ D3.1 completo — `download_aptitud_cafe()` + `download_aptitud_cacao()` / ✅ D3.2 completo — `download_aptitud_maiz()` / ✅ D3.3 completo — `download_frontera()`         |
| `modules/economic/`                 | ✅ D4.1–D4.3 completos (ingestion + validacion)                                                                                                                             |
| `modules/predictive/`               | ✅ D5, M1, M2, M3 y M5 Completos. Modelos XGBoost entrenados para rendimiento y riesgo y escenarios simulados.                                                              |
| `modules/explainability/`           | ✅ M4 Completo (SHAP validado y extractor de características funcionando)                                                                                                   |
| `modules/conversational/`           | 🔲 Por implementar                                                                                                                                                          |
| `orchestrator/`                     | 🔲 Por implementar                                                                                                                                                          |
| `frontend/`                         | 🔲 Por implementar                                                                                                                                                          |
