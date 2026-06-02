# SiembraSegura IA

Plataforma de predicción de rendimiento agrícola y riesgo climático para municipios rurales de Colombia.

Predice para cada combinación `municipio + cultivo + año`:

- Rendimiento esperado (t/ha)
- Riesgo de caída de rendimiento (Bajo / Medio / Alto)
- Factores que explican el riesgo (SHAP)
- Recomendación accionable en lenguaje claro
- Simulación de escenarios climáticos (seco, lluvioso, fertilizantes)
- Asistente conversacional con RAG + LLM

**Cultivos:** Café · Cacao · Maíz  
**Cobertura:** 15 municipios en 8 departamentos (ver `municipios_cobertura.md`)

---

## Requisitos previos

- Python 3.10+
- Node.js 18+
- Git

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone <url-del-repo>
cd siembrasegura
```

### 2. Crear el entorno virtual de Python e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install anthropic==0.40.0   # SDK de Claude (fallback LLM)
```

### 3. Configurar variables de entorno

Copia el archivo de ejemplo y rellena tus keys:

```powershell
copy .env.example .env
```

Edita `.env` con tus valores:

```dotenv
# API datos.gov.co (opcional — aumenta rate limit)
SOCRATA_APP_TOKEN=tu_token_socrata

# LLM principal — Google Gemini
# Obtén tu key en: https://aistudio.google.com/app/apikey
# Para rotar cuota automáticamente, separa varias keys con coma:
# LLM_API_KEY=key1,key2,key3
LLM_API_KEY=tu_gemini_api_key
LLM_MODEL=gemini-2.0-flash

# LLM fallback — Anthropic Claude (se activa si Gemini agota cuota)
# Obtén tu key en: https://console.anthropic.com/
ANTHROPIC_API_KEY=tu_anthropic_api_key
ANTHROPIC_MODEL=claude-haiku-4-5
```

> **Nota:** Si no configuras `ANTHROPIC_API_KEY`, el sistema usará respuestas locales basadas en RAG cuando Gemini falle.

### 4. Instalar dependencias del frontend

```powershell
cd frontend
npm install
cd ..
```

---

## Cómo correr el proyecto

Abre **dos terminales** desde la raíz del repositorio.

### Terminal 1 — Backend (API FastAPI)

```powershell
# Activar entorno virtual
.\.venv\Scripts\Activate.ps1

# Levantar la API
.\.venv\Scripts\python.exe -m uvicorn orchestrator.main:app --host 0.0.0.0 --port 8000
```

La API queda disponible en:
- **Endpoints:** http://localhost:8000
- **Documentación interactiva (Swagger):** http://localhost:8000/docs

### Terminal 2 — Frontend (Next.js)

```powershell
cd frontend
npm run dev
```

El frontend queda disponible en:
- **Aplicación:** http://localhost:3000

---

## Verificar que todo funciona

Con ambos servicios corriendo, abre http://localhost:3000 y navega por:

| Sección | URL | Qué verifica |
|---|---|---|
| Mapa | `/` | Mapa interactivo con 15 municipios |
| Ficha municipal | `/municipio/[codigo]` | Predicción + SHAP + serie histórica |
| Comparador | `/comparador` | Ranking de cultivos por municipio |
| Asistente IA | `/asistente` | Chat RAG + tokens usados + modelo activo |

También puedes probar los endpoints directamente desde Swagger en http://localhost:8000/docs.

---

## Asistente IA — Comportamiento del LLM

El asistente usa una cascada de proveedores para garantizar disponibilidad:

```
1. Gemini (key #1) → si falla por cuota, prueba key #2, key #3...
2. Claude Haiku    → si todas las keys de Gemini están agotadas
3. RAG local       → si Claude tampoco está disponible (sin LLM)
```

Cada respuesta muestra en la parte inferior:
- **Fuentes RAG** usadas (badges grises)
- **Modelo activo** (badge verde con punto): ej. `gemini/gemini-2.0-flash`
- **Tokens consumidos** (badge gris): ej. `1.269 tokens`

---

## Estructura del proyecto

```
siembrasegura/
├── modules/
│   ├── agricultural/    # Ingesta y normalización EVA
│   ├── climate/         # Ingesta y agregación IDEAM
│   ├── territorial/     # Aptitud UPRA + frontera agrícola
│   ├── economic/        # Agroinsumos + precios
│   ├── predictive/      # XGBoost regressor + classifier + escenarios
│   ├── explainability/  # SHAP + narrativas
│   └── conversational/  # LLM (Gemini/Claude) + RAG + reportes PDF
├── orchestrator/        # FastAPI — endpoints principales
├── shared/              # Utilidades: DANE codes, normalización, Socrata client
├── data/                # Parquets procesados (gitignored)
├── models/              # Modelos .pkl entrenados (gitignored)
├── specs/               # Specs de desarrollo (todas implementadas)
├── scripts/             # Scripts de validación por pipeline
├── frontend/            # Aplicación Next.js 14
├── .env                 # Variables de entorno (no commitear)
├── .env.example         # Plantilla de variables de entorno
├── requirements.txt     # Dependencias Python
└── docker-compose.yml   # Opción de despliegue con Docker
```

---

## Opción con Docker

Si prefieres contenerizar los servicios:

```bash
docker compose up -d
```

> Asegúrate de tener el archivo `.env` configurado antes de levantar los contenedores.

---

## Fuentes de datos

Todos los datos provienen de [datos.gov.co](https://www.datos.gov.co) vía API Socrata:

| Dataset | ID Socrata |
|---|---|
| EVA histórica 2007-2018 | `2pnw-mmge` |
| EVA reciente 2019-2024 | `uejq-wxrr` |
| IDEAM precipitación | `s54a-sgyg` |
| IDEAM temperatura | `sbwg-7ju4` |
| IDEAM humedad | `uext-mhny` |
| UPRA aptitud café | `kwvf-nwea` |
| UPRA aptitud cacao | `jdjx-qer4` |
| UPRA aptitud maíz | `frjn-92um` |
| UPRA frontera agrícola | `fyc7-sbtz` |
| Índice de agroinsumos | `gwbi-fnzs` |

---

## Stack tecnológico

| Capa | Herramientas |
|---|---|
| Datos / Backend | Python 3.10, pandas 2.1.4, DuckDB 0.9.2, PyArrow 14.0.2 |
| Modelo | XGBoost 2.0.3, scikit-learn 1.3.2, SHAP 0.44.0 |
| API | FastAPI 0.109.0, uvicorn, pydantic 2.5.3 |
| LLM | Google Gemini (`gemini-2.0-flash`) + Anthropic Claude (`claude-haiku-4-5`) |
| Base de datos | PostgreSQL 15, SQLAlchemy 2.0.25 |
| Frontend | Next.js 14 (App Router), react-leaflet, react-plotly.js, shadcn/ui |
| Infraestructura | Docker Compose |
