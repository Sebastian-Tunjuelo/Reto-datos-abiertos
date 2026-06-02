# Cómo funciona SiembraSegura IA

Documento de referencia técnica y funcional. Explica qué hace la plataforma, cómo procesa los datos, cómo calcula el rendimiento y el riesgo, y cómo se integran todos los componentes.

---

## Qué es

SiembraSegura IA es una plataforma web que predice el rendimiento agrícola y el riesgo climático para combinaciones de **municipio + cultivo + año** en Colombia. Está orientada a extensionistas rurales, UMATAs y secretarías de agricultura.

Para cada consulta entrega:

- **Rendimiento esperado** en toneladas por hectárea (t/ha)
- **Semáforo de riesgo** (Bajo / Medio / Alto)
- **Factores explicativos** (SHAP) que justifican la predicción
- **Narrativa en lenguaje natural** con los factores más relevantes
- **Simulación de escenarios** (año seco, año lluvioso, alza de fertilizantes)
- **Asistente conversacional** que responde preguntas en lenguaje campesino o institucional

**Cultivos cubiertos:** Café · Cacao · Maíz  
**Cobertura geográfica:** 15 municipios en 8 departamentos de Colombia

---

## Arquitectura general

```
Fuentes de datos (datos.gov.co)
        │
        ▼
  Pipelines de ingesta
  (EVA · IDEAM · UPRA · Agroinsumos)
        │
        ▼
  Archivos Parquet en data/
        │
        ▼
  Feature Engineering
  (rezagos, aptitud, clima, agroinsumos)
        │
        ▼
  Modelos XGBoost (uno por cultivo)
  ┌─────────────────────────────┐
  │  Regresor → rendimiento t/ha│
  └─────────────────────────────┘
        │
        ▼
  Semáforo determinístico
  (caída vs. promedio histórico)
        │
        ▼
  SHAP + Narrativas
        │
        ▼
  API FastAPI  ←→  Frontend Next.js
        │
        ▼
  Asistente conversacional
  (RAG + Gemini / Claude)
```

---

## Fuentes de datos

Todos los datos provienen de [datos.gov.co](https://www.datos.gov.co) vía API Socrata. No hay datos propietarios.

| Fuente | Qué aporta |
|--------|-----------|
| **EVA (MADR)** 2007–2024 | Rendimiento histórico, área sembrada, área cosechada, producción por municipio y cultivo |
| **IDEAM** | Precipitación acumulada, temperatura media, humedad relativa, días secos por municipio y año |
| **UPRA** | Aptitud agrológica del suelo para cada cultivo (% área en categoría Alta / Media / Baja / Exclusión) |
| **UPRA frontera agrícola** | Porcentaje del municipio dentro y fuera de la frontera agrícola |
| **Índice de agroinsumos** | Evolución mensual del costo de fertilizantes y plaguicidas a nivel nacional |

---

## Pipelines de datos

Los datos se descargan, limpian y guardan como archivos Parquet en `data/`. Cada pipeline tiene su propio módulo:

| Pipeline | Módulo | Salida |
|----------|--------|--------|
| D1 — EVA agrícola | `modules/agricultural/ingestion.py` | `eva_historica.parquet`, `eva_reciente.parquet`, `eva_completa.parquet` |
| D2 — Clima IDEAM | `modules/climate/ingestion.py` + `aggregation.py` | `clima_agregado.parquet` |
| D3 — Territorial UPRA | `modules/territorial/ingestion.py` | `aptitud_cafe.parquet`, `aptitud_cacao.parquet`, `aptitud_maiz.parquet`, `frontera.parquet` |
| D4 — Económico | `modules/economic/ingestion.py` | `agroinsumos_mensual.parquet`, `agroinsumos.parquet` |

---

## Feature Engineering — cómo se construye la tabla maestra

El módulo `modules/predictive/feature_builder.py` cruza todos los Parquet anteriores por la llave `codigo_dane + cultivo + año` y genera `data/feature_matrix.parquet`.

Las features que entran al modelo son:

### Variables de rendimiento histórico (rezagos)

| Feature | Descripción |
|---------|-------------|
| `rendimiento_t1` | Rendimiento del año anterior (t/ha) |
| `rendimiento_prom3a` | Promedio de los últimos 3 años (t/ha) |
| `tendencia_rend_3a` | Pendiente lineal de los últimos 3 años (positiva = mejora) |
| `area_sembrada_t1` | Área sembrada el año anterior (ha) |

> Estas son las features más importantes del modelo. El rendimiento pasado es el mejor predictor del rendimiento futuro.

### Variables climáticas

| Feature | Descripción |
|---------|-------------|
| `prec_acum_mm` | Precipitación acumulada anual (mm) |
| `anomalia_prec` | Desviación de la precipitación vs. la media histórica del municipio |
| `temp_media_c` | Temperatura media anual (°C) |
| `anomalia_temp` | Desviación de la temperatura vs. la media histórica |
| `dias_secos` | Número de días sin lluvia en el año |
| `hum_media_pct` | Humedad relativa media (%) |

### Variables de aptitud del suelo (UPRA)

| Feature | Descripción |
|---------|-------------|
| `pct_alta` | % del área municipal con aptitud alta para el cultivo |
| `pct_media` | % con aptitud media |
| `pct_baja` | % con aptitud baja |
| `pct_exclusion` | % excluido (no apto) |
| `pct_condicionada` | % dentro de la frontera agrícola condicionada |
| `pct_no_condicionada` | % fuera de la frontera agrícola |

### Variables económicas

| Feature | Descripción |
|---------|-------------|
| `indice_agroinsumos` | Índice de costo de fertilizantes y plaguicidas (base 100) |
| `percentil_fertilizantes` | Percentil histórico del costo de fertilizantes (0–100) |
| `señal_riesgo_economico_encoded` | Señal de riesgo económico codificada (0=Bajo, 1=Medio, 2=Alto) |

---

## Cómo se calcula el rendimiento esperado

### Modelo

Se entrena un **XGBoost Regressor** independiente para cada cultivo (Café, Cacao, Maíz). El entrenamiento usa datos de 2007 a 2021, validación en 2022 y test en 2023–2024.

```
Train:      2007–2021
Validación: 2022
Test:       2023–2024
```

El modelo aprende la relación entre las features descritas arriba y el rendimiento real (t/ha) reportado por EVA.

### Predicción para un año futuro

Cuando se solicita una predicción para un año que aún no tiene datos (por ejemplo, 2026), el sistema hace una **proyección iterativa**:

1. Toma la última fila histórica disponible del municipio y cultivo.
2. Para cada año entre el último dato y el año objetivo, predice el rendimiento usando el modelo.
3. El rendimiento predicho en cada paso se convierte en el `rendimiento_t1` del siguiente paso.
4. El promedio y la tendencia de los últimos 3 valores se actualizan en cada iteración.

Esto permite proyectar hasta 5 años en el futuro manteniendo coherencia en los rezagos temporales.

---

## Cómo se calcula el semáforo de riesgo

El riesgo **no** usa un clasificador de machine learning. Usa una **regla determinística** basada en la caída del rendimiento predicho respecto al promedio histórico del municipio y cultivo:

```
caída_pct = (promedio_histórico - rendimiento_predicho) / promedio_histórico

Si caída_pct ≥ umbral_alto  → Riesgo ALTO
Si caída_pct ≥ umbral_medio → Riesgo MEDIO
Si caída_pct < umbral_medio → Riesgo BAJO
  (incluye cuando el rendimiento predicho supera el promedio histórico)
```

Los umbrales están definidos en `shared/config.py` como `UMBRAL_RIESGO_ALTO` y `UMBRAL_RIESGO_MEDIO`.

Esta decisión de diseño hace el semáforo **completamente transparente y auditable**: no hay caja negra en la clasificación de riesgo.

---

## Explicabilidad con SHAP

Una vez entrenados los modelos, se calculan valores SHAP para cada predicción. SHAP (SHapley Additive exPlanations) mide cuánto contribuye cada feature a la predicción final.

El módulo `modules/explainability/` produce:

1. **`shap_explainer_*.pkl`** — explainers guardados por cultivo.
2. **`top_features`** — lista de las N features más influyentes para cada fila, con:
   - Nombre técnico y nombre amigable (ej. `rendimiento_t1` → "Rendimiento año anterior")
   - Valor SHAP (magnitud e impacto)
   - Dirección: "Aumenta riesgo" o "Disminuye riesgo"
   - Valor original de la feature
3. **`narrativa_riesgo`** — texto generado automáticamente que explica los factores principales en lenguaje legible.

Ejemplo de narrativa generada:
> "El riesgo pronosticado es alto. Los principales factores que elevan este riesgo son: Rendimiento año anterior (valor: 0.45), Precipitación acumulada (valor: 312.00). Por otro lado, los factores que ayudan a disminuirlo son: Aptitud alta del suelo (valor: 68.00)."

---

## Simulación de escenarios

El endpoint `/escenario` permite comparar qué pasaría bajo condiciones distintas. Los escenarios disponibles son:

| Escenario | Qué modifica |
|-----------|-------------|
| `base` | Sin cambios — línea de referencia |
| `seco` | Precipitación −30%, días secos +30%, anomalía de precipitación −30 mm |
| `lluvioso` | Precipitación +30%, días secos −30%, anomalía de precipitación +30 mm |
| `fertilizantes` | Índice de agroinsumos +20%, percentil de fertilizantes +20 puntos |

Para cada escenario se aplica el shock a las features, se re-predice con el mismo modelo y se calcula el delta de rendimiento y riesgo respecto a la línea base.

---

## Asistente conversacional

El asistente (`/chat`) combina dos técnicas:

### RAG (Retrieval-Augmented Generation)

Antes de llamar al LLM, el sistema recupera contexto relevante de los datos del proyecto:

- Predicción de rendimiento y riesgo para el municipio/cultivo/año solicitado
- Narrativa SHAP con los factores explicativos
- Serie histórica de rendimiento
- Glosario agrícola con términos técnicos

Este contexto se inyecta en el prompt para que el LLM responda con datos reales del proyecto, no con conocimiento genérico.

### LLM con cascada de proveedores

El sistema intenta los proveedores en este orden:

```
1. Google Gemini (gemini-2.0-flash) — key #1, key #2, key #3...
2. Anthropic Claude (claude-haiku-4-5) — si Gemini agota cuota
3. Respuesta local basada en RAG — si ambos LLM fallan
```

El tono de la respuesta es configurable:
- **`campesino`** — lenguaje cercano, directo, sin tecnicismos
- **`institucional`** — lenguaje técnico para informes y reportes

---

## API — Endpoints principales

La API corre en FastAPI en `http://localhost:8000`. Documentación interactiva en `/docs`.

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `GET` | `/municipios` | Lista los 15 municipios del MVP |
| `GET` | `/cultivos/{municipio}` | Cultivos disponibles para un municipio |
| `GET` | `/rendimiento/{municipio}/{cultivo}` | Serie histórica de rendimiento con rezagos |
| `GET` | `/clima/{municipio}` | Serie histórica climática |
| `POST` | `/predecir` | Predicción de rendimiento y riesgo para un año futuro |
| `POST` | `/escenario` | Simulación de escenarios climáticos y económicos |
| `POST` | `/chat` | Asistente conversacional con RAG + LLM |
| `GET` | `/reporte/{municipio}/{cultivo}` | Reporte descargable en PDF o texto |

---

## Frontend

La aplicación Next.js 14 (App Router) tiene tres secciones principales:

| Sección | Ruta | Qué muestra |
|---------|------|-------------|
| **Mapa interactivo** | `/` | Mapa de Colombia con los 15 municipios. Al hacer clic en uno se accede a su ficha. |
| **Ficha municipal** | `/municipio/[codigo]` | Predicción de rendimiento, semáforo de riesgo, gráfico histórico, factores SHAP y simulación de escenarios. |
| **Comparador de cultivos** | `/comparador` | Ranking de Café, Cacao y Maíz por municipio según rendimiento esperado y nivel de riesgo. |
| **Asistente IA** | `/asistente` | Chat en lenguaje natural. Muestra el modelo LLM activo y los tokens consumidos. |

---

## Limitaciones conocidas

- **Datos climáticos escasos:** solo 10 de los 15 municipios tienen datos IDEAM, y únicamente para 2023–2024. La mayoría de filas tienen variables climáticas en `NaN`. Como el modelo fue entrenado con estos valores nulos, los escenarios `seco` y `lluvioso` producen deltas de rendimiento cercanos a cero para la mayoría de municipios.
- **Escenario `fertilizantes`:** es el único escenario que puede mostrar un efecto real, ya que el índice de agroinsumos tiene cobertura nacional completa.
- **Proyección máxima:** el sistema acepta predicciones hasta 5 años en el futuro respecto al último dato histórico disponible.
- **Cobertura del MVP:** 15 municipios y 3 cultivos. No cubre el resto del territorio nacional.

---

## Cómo levantar el proyecto localmente

```powershell
# 1. Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# 2. Backend
.\.venv\Scripts\python.exe -m uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000

# 3. Frontend (en otra terminal)
cd frontend
npm run dev
```

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- App: http://localhost:3000
