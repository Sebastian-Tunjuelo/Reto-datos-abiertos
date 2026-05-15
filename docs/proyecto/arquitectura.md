# Arquitectura del sistema — SiembraSegura IA

## Stack tecnológico

### Backend y datos
| Herramienta | Versión | Uso |
|-------------|---------|-----|
| Python | 3.11+ | Lenguaje principal |
| Pandas | 2.1.4 | Limpieza y construcción de tabla maestra |
| DuckDB | 0.9.2 | Queries SQL sobre Parquet sin servidor |
| Parquet + PyArrow | 14.0.2 | Almacenamiento eficiente de datos históricos |
| XGBoost | 2.0.3 | Predicción de rendimiento y clasificación de riesgo |
| scikit-learn | 1.3.2 | Utilidades, métricas, validación temporal |
| SHAP | 0.44.0 | Explicabilidad de cada predicción |
| FastAPI | 0.109.0 | API REST que expone predicciones al frontend |
| PostgreSQL | 15 | Predicciones calculadas, listas para consultar |
| Docker + Compose | — | Entorno unificado para todo el equipo |

### Frontend
| Herramienta | Uso |
|-------------|-----|
| Next.js | Framework principal, SSR, rutas API integradas |
| react-leaflet | Mapa de Colombia coloreado por nivel de riesgo |
| react-plotly.js | Gráficas de rendimiento, tendencia y SHAP |
| shadcn/ui | Componentes UI: selectores, tarjetas, semáforo |
| fetch / axios | Comunicación con FastAPI |
| LLM + RAG | Asistente conversacional sobre resultados del modelo |

---

## Módulos del sistema

El sistema se organiza en 7 módulos funcionales más un orquestador central.

```
┌─────────────────────────────────────────────────────────────┐
│                    ORQUESTADOR CENTRAL                       │
│              (FastAPI — orchestrator/main.py)                │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────┘
       │          │          │          │          │
       ▼          ▼          ▼          ▼          ▼
  ┌─────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────────┐
  │Climático│ │Agrícola│ │Territ. │ │Económ. │ │Predictivo  │
  └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └─────┬──────┘
       └──────────┴──────────┴──────────┴─────────────┘
                             │
                    ┌────────▼────────┐
                    │ Explicabilidad  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ Conversacional  │
                    └─────────────────┘
```

### Módulo Climático (`modules/climate/`)
- **Responsabilidad**: variables climáticas agregadas por municipio y año
- **Consume**: `hp9r-jxuu` (catálogo), `s54a-sgyg` (precipitación), `sbwg-7ju4` (temperatura), `uext-mhny` (humedad), `57sv-p2fu` (recientes)
- **Produce**: `clima_agregado.parquet` con `prec_acum, temp_media, hum_media, dias_secos, anomalia_prec, anomalia_temp`
- **Archivos**: `ingestion.py`, `aggregation.py`, `anomalies.py`, `api.py`

### Módulo Agrícola (`modules/agricultural/`)
- **Responsabilidad**: rendimiento histórico y área sembrada por municipio y cultivo
- **Consume**: `2pnw-mmge` (EVA 2007-2018), `uejq-wxrr` (EVA 2019-2024)
- **Produce**: `eva_historica.parquet`, `eva_reciente.parquet`, `eva_completa.parquet`
- **Archivos**: `ingestion.py`, `features.py`, `api.py`

### Módulo Territorial (`modules/territorial/`)
- **Responsabilidad**: aptitud agroecológica y restricciones de frontera agrícola
- **Consume**: `kwvf-nwea` (café), `jdjx-qer4` (cacao), `frjn-92um`+`a5yc-uszt`+`tzga-4zse` (maíz), `fyc7-sbtz` (frontera)
- **Produce**: `aptitud_cafe.parquet`, `aptitud_cacao.parquet`, `aptitud_maiz.parquet`, `frontera.parquet`
- **Archivos**: `ingestion.py`, `aptitude.py`, `frontier.py`, `api.py`
- **Nota crítica**: usar siempre `$group` en SoQL para evitar descargar geometrías (400k–500k registros)

### Módulo Económico (`modules/economic/`)
- **Responsabilidad**: índice de agroinsumos y señal de riesgo económico
- **Consume**: `gwbi-fnzs` (agroinsumos), `gdqq-rry2` (precios RAP Eje Cafetero)
- **Produce**: `agroinsumos.parquet` con percentil histórico y señal de riesgo
- **Archivos**: `ingestion.py`, `risk_score.py`, `api.py`

### Módulo Predictivo (`modules/predictive/`)
- **Responsabilidad**: entrenar y ejecutar XGBoost de rendimiento y riesgo
- **Consume**: salidas de los 4 módulos anteriores (tabla maestra)
- **Produce**: predicciones `{rendimiento_esperado, prob_riesgo_alto, etiqueta_riesgo}`
- **Archivos**: `feature_builder.py`, `train.py`, `predict.py`, `scenarios.py`, `api.py`
- **Modelos**: `xgb_rendimiento_{cafe,cacao,maiz}.pkl`, `xgb_riesgo_{cafe,cacao,maiz}.pkl`

### Módulo Explicabilidad (`modules/explainability/`)
- **Responsabilidad**: valores SHAP y narrativa de factores de riesgo
- **Consume**: modelo entrenado + predicción
- **Produce**: top 5 features con valores SHAP + texto explicativo
- **Archivos**: `shap_engine.py`, `narratives.py`, `api.py`

### Módulo Conversacional (`modules/conversational/`)
- **Responsabilidad**: asistente LLM + RAG + reportes automáticos
- **Consume**: predicciones + SHAP como contexto
- **Produce**: respuestas en lenguaje natural + PDF/texto de reporte
- **Archivos**: `rag.py`, `prompts.py`, `reports.py`, `api.py`

---

## Flujo de orquestación

Ejemplo: "¿Cuál es el riesgo para café en Chaparral en 2025?"

```
1. Frontend → POST /predecir {municipio: "Chaparral", cultivo: "Café", año: 2025}

2. Orquestador llama en paralelo:
   ├── Módulo Climático   → SerieClimática(Chaparral, 2024)
   ├── Módulo Agrícola    → RendimientoHistórico(Chaparral, Café, 2007-2024)
   ├── Módulo Territorial → ZonaAptitud(Chaparral, Café)
   └── Módulo Económico   → RiesgoEconómico(Café, 2024)

3. Orquestador ensambla tabla maestra → Módulo Predictivo
   → Predicción: rendimiento 0.82 t/ha, riesgo ALTO (prob 71%)

4. Módulo Explicabilidad
   → "Riesgo alto por déficit de lluvia (-23% vs media) y
      alza de fertilizantes (+18% vs año anterior)"

5. Módulo Conversacional (si hay pregunta en chat)
   → Respuesta en lenguaje campesino/institucional + reporte PDF

6. Orquestador → Frontend: JSON con predicción + SHAP + narrativa
```

---

## Estructura de carpetas del proyecto

```
siembrasegura/
├── docs/                    ← contexto e investigación (este directorio)
├── specs/                   ← especificaciones ejecutables por capa
│   ├── D1_pipeline_eva/
│   ├── D2_pipeline_clima/
│   ├── D3_pipeline_upra/
│   ├── D4_pipeline_economico/
│   └── D5_tabla_maestra/
├── modules/                 ← código de implementación
│   ├── agricultural/
│   ├── climate/
│   ├── territorial/
│   ├── economic/
│   ├── predictive/
│   ├── explainability/
│   └── conversational/
├── orchestrator/            ← FastAPI app principal
│   ├── main.py
│   ├── router.py
│   └── pipeline.py
├── shared/                  ← utilidades compartidas
│   ├── config.py
│   ├── dane_codes.py
│   ├── normalization.py
│   └── socrata_client.py
├── data/                    ← Parquets generados (gitignored)
├── models/                  ← modelos .pkl entrenados (gitignored)
├── frontend/                ← Next.js
├── docker-compose.yml
└── README.md
```

---

## Validación temporal del modelo

**Regla crítica**: nunca hacer split aleatorio en datos de series de tiempo agrícolas.

| Conjunto | Años | Uso |
|----------|------|-----|
| Train | 2007–2021 | Entrenamiento del modelo |
| Validación | 2022 | Ajuste de hiperparámetros |
| Test | 2023–2024 | Evaluación final (no tocar hasta el final) |

Definido en `shared/config.py`:
```python
TRAIN_HASTA = 2021
VAL_AÑO = 2022
TEST_DESDE = 2023
```

---

## Métricas de evaluación

| Métrica | Modelo | Umbral aceptable |
|---------|--------|-----------------|
| MAE | Regressor (rendimiento) | < 0.3 t/ha |
| RMSE | Regressor (rendimiento) | < 0.5 t/ha |
| R² | Regressor (rendimiento) | > 0.6 |
| F1-score macro | Classifier (riesgo) | > 0.65 |
| AUC-ROC | Classifier (riesgo) | > 0.75 |

Reportar métricas **por cultivo** y **por departamento**, no solo globales.

---

## Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/predecir` | Predicción + riesgo + SHAP para municipio/cultivo/año |
| `POST` | `/escenario` | Predicción bajo escenario climático (seco/lluvioso/normal) |
| `GET` | `/municipios` | Lista de municipios disponibles |
| `GET` | `/cultivos/{municipio}` | Cultivos disponibles para un municipio |
| `GET` | `/rendimiento/{municipio}/{cultivo}` | Serie histórica de rendimiento |
| `GET` | `/clima/{municipio}` | Serie climática histórica |
| `POST` | `/chat` | Pregunta en lenguaje natural → respuesta LLM |
| `GET` | `/reporte/{municipio}/{cultivo}` | Reporte PDF/texto generado |

---

## Pantallas del frontend

| Pantalla | Componentes clave |
|----------|------------------|
| Mapa de riesgo | react-leaflet, color por riesgo, filtro por cultivo |
| Ficha municipal | Gráfica rendimiento (plotly), semáforo, barras SHAP, recomendación |
| Comparador de cultivos | Tabla comparativa rendimiento/riesgo/aptitud, ranking |
| Asistente IA | Chat (shadcn/ui), botón "Generar reporte" |
