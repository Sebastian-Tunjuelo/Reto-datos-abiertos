# Investigación estratégica — SiembraSegura IA

La propuesta competitiva no debe ser solo "un modelo que predice rendimiento". Debe convertirse en una herramienta de decisión: **qué cultivo sembrar, dónde, cuándo, con qué riesgo climático y con qué expectativa productiva/económica**, usando datos abiertos verificables.

---

# 1. PROBLEMAS Y PRIORIZACIÓN

| Prioridad | Problema concreto | Impacto | Viabilidad 1 mes | Potencial hackathon |
|---:|---|---:|---:|---:|
| 1 | Predicción de caída de rendimiento por anomalías climáticas en cultivos clave | Muy alto | Alta | Muy alto |
| 2 | Decisiones de siembra en municipios con baja aptitud o alta restricción agropecuaria | Muy alto | Alta-media | Muy alto |
| 3 | Riesgo económico por precios de mercado e insumos agrícolas | Alto | Alta | Alto |
| 4 | Alertas de precio para productos perecederos regionales | Medio-alto | Media | Medio-alto |
| 5 | Calidad/anomalías de datos meteorológicos | Medio | Alta | Medio |

Los problemas 1, 2 y 3 se resuelven de forma integrada en la propuesta principal. Los problemas 4 y 5 son complementarios o descartables para el MVP.

---

# 2. PROPUESTA — SiembraSegura IA

**Semáforo de rendimiento, riesgo climático y recomendación de cultivo para municipios rurales de Colombia.**

Para cada combinación `municipio + cultivo + periodo` entrega:

1. Rendimiento esperado (t/ha).
2. Semáforo de riesgo: Bajo / Medio / Alto.
3. Factores que explican el riesgo (SHAP).
4. Recomendación accionable en lenguaje claro.
5. Comparador de cultivos con ranking.
6. Simulación de escenarios climáticos.
7. Reporte automático para UMATA/productor.
8. Asistente conversacional con RAG.

**Usuarios objetivo:** UMATAs, extensionistas, secretarías de agricultura, asociaciones campesinas.

**Cultivos MVP:** Café · Cacao · Maíz

**Cobertura:** 15 municipios priorizados (ver tabla en sección 9), modelo extensible a nivel nacional.

### Por qué es competitiva

| Solución tradicional | SiembraSegura IA |
|---|---|
| Muestra clima histórico | Calcula riesgo productivo |
| Muestra producción pasada | Predice rendimiento esperado |
| Dashboard descriptivo | Recomendación accionable |
| Sin explicación | Explica factores de riesgo vía SHAP |
| Datos aislados | Cruza EVA + IDEAM + UPRA + agroinsumos |

---

# 3. DATOS ABIERTOS

## Datasets principales — datos.gov.co

| Dataset | ID Socrata | Variables clave | Uso |
|---|---|---|---|
| EVA histórica 2007-2018 | `2pnw-mmge` | municipio, cultivo, año, área sembrada/cosechada, producción, rendimiento | Variable objetivo `rendimiento_t_ha` |
| EVA reciente 2019-2024 | `uejq-wxrr` | código DANE, cultivo, área, producción, rendimiento, año | Actualización para entrenamiento y validación |
| Precipitación IDEAM | `s54a-sgyg` | estación, fecha, valor mm, municipio, lat/lon | Lluvia acumulada, déficit, días secos ⚠️ ~165M registros — siempre agregar |
| Temperatura IDEAM | `sbwg-7ju4` | estación, fecha, temperatura °C, municipio | Temperatura media, anomalías, estrés térmico ⚠️ ~50M registros — siempre agregar |
| Humedad IDEAM | `uext-mhny` | estación, fecha, humedad relativa, municipio | Riesgo de enfermedades, estrés agroclimático |
| Estaciones recientes IDEAM | `57sv-p2fu` | estación, sensor, fecha, valor, municipio | Monitoreo reciente |
| Catálogo estaciones IDEAM | `hp9r-jxuu` | código, nombre, estado, municipio, altitud | Selección de estaciones cercanas |
| Frontera agrícola UPRA | `fyc7-sbtz` | municipio, código DANE, tipo frontera, área ha ⚠️ geometrías | Restricciones de uso del suelo |
| Aptitud café UPRA | `kwvf-nwea` | municipio, código DANE, aptitud, área ha ⚠️ geometrías | Variable de aptitud para café |
| Aptitud cacao UPRA | `jdjx-qer4` | municipio, código DANE, aptitud, área ha ⚠️ geometrías | Variable de aptitud para cacao |
| Aptitud maíz tradicional UPRA | `frjn-92um` | municipio, código DANE, aptitud, área ha | Variable de aptitud para maíz |
| Aptitud maíz tec. 1er sem. UPRA | `a5yc-uszt` | municipio, aptitud, área ha ⚠️ geometrías | Comparación por semestre |
| Aptitud maíz tec. 2do sem. UPRA | `tzga-4zse` | municipio, aptitud, área ha ⚠️ geometrías | Comparación por semestre |
| Índice agroinsumos | `gwbi-fnzs` | fecha, índice total, fertilizantes, plaguicidas, urea, DAP, KCL | Riesgo económico por costos |
| Precios RAP Eje Cafetero | `gdqq-rry2` | producto, mercado, precio mín/máx/medio, fecha, ciudad | Complemento económico regional |

## Fuentes adicionales opcionales

| Fuente | Uso |
|---|---|
| NASA POWER / CHIRPS | Clima histórico por coordenadas cuando no haya estación IDEAM cercana |
| ERA5 / Copernicus | Variables climáticas reanalizadas |
| TerriData / DNP | Variables socioeconómicas municipales |
| DANE SIPSA | Precios mayoristas nacionales |

---

# 4. MODELOS DE IA

## 4.1 Predicción de rendimiento — XGBoost Regressor

Predice `rendimiento_t_ha` por `municipio + cultivo + año`.

**Variables de entrada permitidas:**
- Rendimiento rezagado: año anterior, promedio 3 años, tendencia.
- Área sembrada histórica y cambio interanual.
- Precipitación acumulada, anomalía, días secos.
- Temperatura media y días de calor extremo.
- Humedad promedio.
- Aptitud UPRA: % área alta/media/baja.
- % frontera agrícola condicionada.
- Índice de agroinsumos.

**Variables prohibidas (fuga de información):** `produccion` y `area_cosechada` del mismo año/periodo.

## 4.2 Clasificación de riesgo — XGBoost Classifier

Clasifica riesgo de bajo rendimiento en Bajo / Medio / Alto.

> Riesgo alto = rendimiento esperado cae > 15% frente al promedio histórico municipal del cultivo.

Entrega probabilidad de riesgo + etiqueta + factores SHAP.

## 4.3 Riesgo económico — índice de scoring

No requiere modelo separado. Se calcula combinando rendimiento esperado + percentil del índice de fertilizantes + precio regional. Se expresa como semáforo adicional en la ficha municipal.

## 4.4 Recomendador de cultivo — motor de scoring

Ranking café vs cacao vs maíz por municipio, combinando:

| Factor | Peso |
|---|---|
| Rendimiento esperado (XGBoost) | Alto |
| Riesgo climático (XGBoost Classifier) | Alto |
| Aptitud UPRA | Medio |
| Frontera agrícola | Medio |
| Riesgo económico | Medio |
| Estabilidad histórica | Bajo |

Justificación generada por LLM en lenguaje claro.

## Validación temporal — regla estricta

```
Train:      2007–2021
Validación: 2022
Test:       2023–2024  ← no tocar hasta el final
```

**Nunca split aleatorio en datos temporales.**

---

# 5. ARQUITECTURA DEL SISTEMA

## Stack tecnológico

| Capa | Herramienta | Rol |
|---|---|---|
| Datos | Python + Pandas | Limpieza y construcción de tabla maestra |
| Datos | DuckDB | Queries SQL sobre Parquet sin servidor |
| Datos | Parquet | Almacenamiento eficiente de datos históricos |
| Modelo | XGBoost + scikit-learn | Predicción de rendimiento y clasificación de riesgo |
| Modelo | SHAP | Explicabilidad de cada predicción |
| API | FastAPI + uvicorn | Endpoints REST que exponen predicciones al frontend |
| Base de datos | PostgreSQL | Predicciones calculadas, listas para consultar |
| Infra | Docker + Docker Compose | Entorno unificado — `docker compose up` levanta todo |
| Frontend | Next.js 14 (App Router) | Framework principal |
| Frontend | react-leaflet | Mapa de Colombia coloreado por nivel de riesgo |
| Frontend | react-plotly.js | Gráficas de rendimiento, tendencia y SHAP |
| Frontend | shadcn/ui | Componentes UI: selectores, tarjetas, semáforo |
| Asistente | LLM + RAG | Responde preguntas usando resultados del modelo como contexto |

## Módulos del sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    ORQUESTADOR CENTRAL                       │
│              (FastAPI — capa de coordinación)                │
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

| Módulo | Consume | Produce | Endpoint |
|---|---|---|---|
| Climático | IDEAM (prec, temp, hum, catálogo) | `SerieClimática(municipio, año, prec_acum, temp_media, hum_media, dias_secos, anomalia_*)` | `GET /clima/{municipio}/{año}` |
| Agrícola | EVA histórica + reciente | `RendimientoHistórico(municipio, cultivo, año, rendimiento, area_sembrada, tendencia_3a)` | `GET /eva/{municipio}/{cultivo}` |
| Territorial | UPRA aptitud + frontera | `ZonaAptitud(municipio, cultivo, pct_alta, pct_media, pct_baja, pct_condicionada)` | `GET /aptitud/{municipio}/{cultivo}` |
| Económico | Agroinsumos + precios RAP | `RiesgoEconómico(fecha, indice_fertilizantes, precio_referencia, señal_riesgo)` | `GET /economia/{cultivo}/{año}` |
| Predictivo | Tabla maestra (salidas anteriores) | `Predicción(municipio, cultivo, año, rendimiento_esperado, prob_riesgo_alto, etiqueta_riesgo)` | `POST /predecir` |
| Explicabilidad | Predicción + modelo entrenado | `ExplicaciónSHAP(prediccion_id, factores_ordenados, narrativa_texto)` | `GET /explicar/{prediccion_id}` |
| Conversacional | Predicción + SHAP (contexto RAG) | `RespuestaGenerada(pregunta, respuesta, reporte_pdf)` | `POST /chat` |

## Flujo de ejemplo — "¿Cuál es el riesgo para café en Chaparral en 2025?"

```
1. Frontend → POST /predecir {municipio: "Chaparral", cultivo: "Café", año: 2025}

2. Orquestador llama en paralelo:
   ├── Climático   → SerieClimática(Chaparral, 2024)
   ├── Agrícola    → RendimientoHistórico(Chaparral, Café, 2007-2024)
   ├── Territorial → ZonaAptitud(Chaparral, Café)
   └── Económico   → RiesgoEconómico(Café, 2024)

3. Orquestador ensambla tabla maestra → Predictivo
   → rendimiento 0.82 t/ha, riesgo ALTO (prob 71%)

4. Explicabilidad
   → "Riesgo alto por déficit de lluvia acumulada (-23% vs media histórica)
      y aumento del índice de fertilizantes (+18% vs año anterior)"

5. Conversacional (si hay pregunta en chat)
   → Respuesta en lenguaje campesino/institucional + reporte PDF

6. Orquestador → Frontend: JSON con predicción + SHAP + narrativa
```

## Estructura de carpetas

```
siembrasegura/
├── modules/
│   ├── climate/          ingestion.py, aggregation.py, anomalies.py, api.py
│   ├── agricultural/     ingestion.py, features.py, api.py
│   ├── territorial/      ingestion.py, aptitude.py, frontier.py, api.py
│   ├── economic/         ingestion.py, risk_score.py, api.py
│   ├── predictive/       feature_builder.py, train.py, predict.py, scenarios.py, api.py
│   ├── explainability/   shap_engine.py, narratives.py, api.py
│   └── conversational/   rag.py, prompts.py, reports.py, api.py
├── orchestrator/         main.py, router.py, pipeline.py
├── shared/               config.py, dane_codes.py, normalization.py, socrata_client.py
├── data/                 *.parquet (gitignored)
├── models/               *.pkl (gitignored)
├── specs/                specs por pipeline
├── frontend/             Next.js
├── docker-compose.yml
└── README.md
```

---

# 6. DIFERENCIADORES PARA GANAR

## Innovación
- Predicción de rendimiento + clasificación de riesgo climático.
- Simulación de escenarios: año seco (-30% lluvia), año lluvioso (+30%), subida de fertilizantes (+20%).
- Explicabilidad SHAP visible en el frontend.
- Asistente generativo que traduce resultados técnicos a lenguaje campesino/institucional.

## Uso de datos abiertos
Mostrar trazabilidad explícita: "esta predicción usa EVA + IDEAM + UPRA + agroinsumos". Incluir IDs de datasets en la presentación. Datasets mínimos para la demo:

`2pnw-mmge` · `uejq-wxrr` · `s54a-sgyg` · `sbwg-7ju4` · `hp9r-jxuu` · `fyc7-sbtz` · `kwvf-nwea` · `jdjx-qer4` · `frjn-92um` · `gwbi-fnzs`

## Impacto social
- Enfocar en pequeños productores y municipios rurales vulnerables (PDET).
- Diseñar para UMATAs y extensionistas, no para científicos de datos.
- Reportes listos para compartir por WhatsApp o PDF.

## Escalabilidad
- Agregar cultivos o municipios cambiando configuración, sin tocar el modelo.
- Actualizar datos vía API Socrata automáticamente.

---

# 7. ERRORES A EVITAR

## Técnicos
1. Predecir a nivel finca con datos municipales — los datos EVA son municipales.
2. Usar `produccion` o `area_cosechada` del mismo año como features — fuga de información.
3. Split aleatorio en datos temporales — siempre validar por años futuros.
4. Descargar datos crudos de IDEAM sin agregar — son millones de registros.
5. No unificar códigos DANE — los nombres de municipios varían por tildes y grafías.
6. Prometer predicción climática sin fuente de pronóstico — presentar escenarios en su lugar.

## Estratégicos
1. Hacer solo un dashboard descriptivo — no se percibe como IA aplicada.
2. No conectar resultados con decisiones reales — el usuario debe saber qué hacer.
3. Sobrecomplicar con deep learning — un XGBoost bien validado y explicable es más convincente.
4. No tener MVP funcional — mejor app simple funcionando que arquitectura ambiciosa incompleta.
5. No mostrar datos abiertos en la demo — evidenciar el uso de datos.gov.co es criterio de evaluación.

---

# 8. METODOLOGÍA — SPEC-DRIVEN + TASK DECOMPOSITION

Cada módulo se define primero como una spec estructurada con requisitos, inputs, outputs y criterios de aceptación. El agente de IA lee la spec antes de escribir código. Las tareas se descomponen por capa para que puedan ejecutarse en paralelo.

## Estructura de cada spec

```markdown
# Spec: [Nombre del módulo]

## Objetivo
Qué debe hacer este módulo en una oración.

## Inputs
- Fuente 1: descripción, formato, columnas relevantes

## Outputs
- Archivo/endpoint: formato, columnas, ejemplo de fila

## Criterios de aceptación
- [ ] El output tiene las columnas X, Y, Z
- [ ] Los 15 municipios del MVP están presentes
- [ ] Tiempo de ejecución < N segundos

## Restricciones técnicas
- Usar shared/socrata_client.py — nunca sodapy
- Normalizar con shared/dane_codes.py y shared/normalization.py

## Dependencias
- Requiere: shared/socrata_client.py, shared/dane_codes.py
- Produce para: módulo predictivo (feature_builder.py)
```

## Descomposición de tareas

### Semana 1 — Datos

| ID | Tarea | Entregable |
|----|-------|-----------|
| D1 | Pipeline EVA: descargar histórica + reciente, unificar columnas | `eva_historica.parquet`, `eva_reciente.parquet` |
| D2 | Pipeline Clima: estaciones IDEAM, precipitación + temperatura agregadas, anomalías | `clima_agregado.parquet` |
| D3 | Pipeline UPRA: aptitud café/cacao/maíz + frontera agrícola (GROUP BY SoQL) | 4 archivos Parquet |
| D4 | Pipeline Económico: agroinsumos + percentil histórico | `agroinsumos.parquet` |
| D5 | Tabla maestra: cruzar D1-D4 por municipio/cultivo/año, features rezagadas | `tabla_maestra.parquet` |

### Semana 2 — Modelo

| ID | Tarea | Entregable |
|----|-------|-----------|
| M1 | Feature engineering: variables climáticas, rezagos, aptitud, riesgo económico | Features validadas |
| M2 | XGBoost Regressor por cultivo, split temporal, métricas MAE/RMSE/R² | 3 modelos `.pkl` + métricas |
| M3 | XGBoost Classifier de riesgo, etiqueta caída > 15%, métricas F1/AUC | 3 modelos `.pkl` + métricas |
| M4 | SHAP values, top 5 features por predicción, plantillas de narrativa | SHAP values + narrativas |
| M5 | Simulación de escenarios: año seco, lluvioso, subida fertilizantes | Función de escenarios |

### Semana 3 — API y Frontend

| ID | Tarea | Entregable |
|----|-------|-----------|
| A1 | `POST /predecir`, `GET /municipios`, `GET /cultivos/{municipio}` | Endpoints funcionales |
| A2 | `GET /rendimiento/{municipio}/{cultivo}`, `GET /clima/{municipio}` | Endpoints funcionales |
| A3 | `POST /escenario`, `POST /chat`, `GET /reporte/{municipio}/{cultivo}` | Endpoints funcionales |
| F1 | Mapa Colombia con react-leaflet, color por riesgo, filtro por cultivo | Pantalla mapa |
| F2 | Ficha municipal: gráfica histórica, semáforo, barras SHAP, recomendación | Pantalla ficha |
| F3 | Comparador de cultivos: tabla rendimiento/riesgo/aptitud, ranking | Pantalla comparador |

### Semana 4 — Conversacional y demo

| ID | Tarea | Entregable |
|----|-------|-----------|
| C1 | RAG: indexar predicciones + SHAP, función de recuperación por municipio/cultivo | Motor RAG |
| C2 | Prompts: lenguaje campesino, reporte institucional UMATA, comparación cultivos | Plantillas de prompt |
| C3 | Generador de reportes PDF por municipio | Generador de reportes |
| F4 | Chat interface shadcn/ui + integración `/chat` + botón "Generar reporte" | Pantalla asistente |

---

# 9. MUNICIPIOS DEL MVP

15 municipios seleccionados con cobertura en las 7 fuentes: EVA + IDEAM (prec+temp+hum) + UPRA (café+cacao+maíz+frontera) + Agroinsumos.

| Municipio | Departamento | Código DANE | Est. IDEAM | PDET |
|-----------|-------------|------------|-----------|------|
| Ibagué | Tolima | `73001` | 20 | — |
| Chaparral | Tolima | `73168` | 13 | ✅ |
| Neiva | Huila | `41001` | 10 | — |
| Garzón | Huila | `41298` | 9 | — |
| Pitalito | Huila | `41551` | 6 | — |
| San Vicente de Chucurí | Santander | `68689` | 12 | — |
| Rionegro | Santander | `68615` | 19 | — |
| Anorí | Antioquia | `05036` | 14 | ✅ |
| Amalfi | Antioquia | `05030` | 12 | — |
| Pensilvania | Caldas | `17541` | 20 | — |
| Palestina | Caldas | `17524` | 13 | — |
| Villavicencio | Meta | `50001` | 15 | — |
| El Tambo | Cauca | `19256` | 12 | ✅ |
| Miranda | Cauca | `19418` | 12 | — |
| Valledupar | Cesar | `20001` | 14 | — |
