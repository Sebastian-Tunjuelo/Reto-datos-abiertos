# SiembraSegura IA

Plataforma de predicción de rendimiento agrícola y riesgo climático para municipios rurales de Colombia.

## Qué hace

Predice para cada combinación `municipio + cultivo + año`:
- Rendimiento esperado (t/ha)
- Riesgo de caída de rendimiento (Bajo / Medio / Alto)
- Factores que explican el riesgo (SHAP)
- Recomendación accionable en lenguaje claro
- Simulación de escenarios climáticos

## Cultivos
Café · Cacao · Maíz

## Municipios del MVP
15 municipios en 8 departamentos: Tolima, Huila, Santander, Antioquia, Caldas, Meta, Cauca, Cesar.
Ver `municipios_cobertura.md` para el análisis completo de cobertura de datos.

## Fuentes de datos
Todos los datos provienen de [datos.gov.co](https://www.datos.gov.co):
- EVA (Evaluaciones Agropecuarias Municipales) — `2pnw-mmge` / `uejq-wxrr`
- IDEAM precipitación, temperatura, humedad — `s54a-sgyg` / `sbwg-7ju4` / `uext-mhny`
- UPRA aptitud café, cacao, maíz — `kwvf-nwea` / `jdjx-qer4` / `frjn-92um`
- UPRA frontera agrícola — `fyc7-sbtz`
- Índice de agroinsumos — `gwbi-fnzs`

## Stack
- **Backend/Datos/Modelo:** Python 3.10, FastAPI, XGBoost, SHAP, DuckDB, Parquet
- **Frontend:** Next.js 14, react-leaflet, react-plotly.js, shadcn/ui
- **Infraestructura:** Docker Compose, PostgreSQL

## Inicio rápido

```bash
# 1. Clonar y entrar al proyecto
git clone https://github.com/Sebastian-Tunjuelo/Reto-datos-abiertos.git
cd Reto-datos-abiertos

# 2. Copiar variables de entorno
cp .env.example .env

# 3. Instalar dependencias Python
pip install -r requirements.txt

# 4. Ejecutar pipeline de datos (Semana 1)
python modules/agricultural/ingestion.py
python modules/climate/ingestion.py
python modules/territorial/ingestion.py
python modules/economic/ingestion.py

# 5. Levantar servicios
docker compose up -d
```

## Estructura del proyecto

```
siembrasegura/
├── .kiro/
│   ├── skills/          # Contexto persistente para agentes IA
│   └── specs/           # Specs de tareas de desarrollo
├── modules/
│   ├── climate/         # Ingesta y agregación IDEAM
│   ├── agricultural/    # Ingesta y normalización EVA
│   ├── territorial/     # Aptitud UPRA + frontera agrícola
│   ├── economic/        # Agroinsumos + precios
│   ├── predictive/      # XGBoost + validación temporal
│   ├── explainability/  # SHAP + narrativas
│   └── conversational/  # LLM + RAG + reportes
├── orchestrator/        # FastAPI principal
├── shared/              # Utilidades comunes (DANE, normalización, Socrata)
├── data/                # Parquets procesados (gitignored)
├── models/              # Modelos .pkl entrenados (gitignored)
├── specs/               # Specs de desarrollo (Spec-Driven)
└── frontend/            # Next.js
```

## Metodología de desarrollo
Spec-Driven Development con Task Decomposition por capa funcional.
Cada tarea tiene una spec en `specs/` con inputs, outputs y criterios de aceptación verificables.
