# Contexto del Proyecto — SiembraSegura IA

## Qué es
Plataforma web que predice rendimiento agrícola y riesgo climático por municipio y cultivo en Colombia, integrando datos abiertos de datos.gov.co. Entrega un semáforo de riesgo (Bajo/Medio/Alto), rendimiento esperado, explicación de factores y recomendación accionable.

## Cultivos del MVP
- Café
- Cacao
- Maíz (tradicional + tecnificado)

## 15 Municipios del MVP (validados con datos reales)

| Municipio | Departamento | Código DANE | Est. IDEAM | Años EVA | PDET |
|-----------|-------------|------------|-----------|---------|------|
| Ibagué | Tolima | 73001 | 20 | 18 | No |
| Chaparral | Tolima | 73168 | 13 | 18 | Sí |
| Neiva | Huila | 41001 | 10 | 18 | No |
| Garzón | Huila | 41298 | 9 | 18 | No |
| Pitalito | Huila | 41551 | 6 | 18 | No |
| San Vicente de Chucurí | Santander | 68689 | 12 | 18 | No |
| Rionegro | Santander | 68615 | 19 | 18 | No |
| Anorí | Antioquia | 05036 | 14 | 18 | Sí |
| Amalfi | Antioquia | 05030 | 12 | 18 | No |
| Pensilvania | Caldas | 17541 | 20 | 18 | No |
| Palestina | Caldas | 17524 | 13 | 18 | No |
| Villavicencio | Meta | 50001 | 15 | 18 | No |
| El Tambo | Cauca | 19256 | 12 | 18 | Sí |
| Miranda | Cauca | 19418 | 12 | 18 | No |
| Valledupar | Cesar | 20001 | 14 | 18 | No |

## Stack tecnológico

### Backend / Datos / Modelo
- Python 3.10
- pandas, duckdb, pyarrow
- xgboost, scikit-learn, shap
- fastapi, uvicorn
- requests (cliente Socrata)
- reportlab o weasyprint (PDFs)

### Frontend
- Next.js 14 (App Router)
- react-leaflet (mapas)
- react-plotly.js (gráficas)
- shadcn/ui (componentes)
- axios (HTTP)

### Infraestructura
- Docker + Docker Compose
- PostgreSQL (predicciones calculadas)
- Parquet + DuckDB (datos históricos)

## Estructura de carpetas
```
siembrasegura/
├── modules/
│   ├── climate/          # Ingesta y agregación IDEAM
│   ├── agricultural/     # Ingesta y normalización EVA
│   ├── territorial/      # Aptitud UPRA + frontera agrícola
│   ├── economic/         # Agroinsumos + precios
│   ├── predictive/       # XGBoost + validación temporal
│   ├── explainability/   # SHAP + narrativas
│   └── conversational/   # LLM + RAG + reportes
├── orchestrator/         # FastAPI principal
├── shared/               # Utilidades comunes
├── data/                 # Parquets procesados
├── models/               # Modelos .pkl entrenados
├── specs/                # Specs de desarrollo
└── frontend/             # Next.js
```

## Convenciones de código
- Archivos de datos: snake_case, extensión .parquet
- Modelos: `xgb_{tipo}_{cultivo}.pkl` (ej: `xgb_rendimiento_cafe.pkl`)
- Funciones de ingesta: siempre retornan DataFrame de pandas
- Logging: usar `logging` estándar de Python, nivel INFO por defecto
- Variables de entorno: cargar desde `.env` con `python-dotenv`
- Llave de unión entre datasets: `codigo_dane` (string de 5 dígitos con cero a la izquierda)
