# D1 — Pipeline EVA (Evaluaciones Agropecuarias Municipales)

## Resumen
Descarga, limpia y unifica los datos de rendimiento agrícola de los 15 municipios del MVP desde las dos fuentes EVA oficiales del Ministerio de Agricultura de Colombia.

## Contexto del dominio
EVA registra por municipio, cultivo y año: área sembrada, área cosechada, producción total y rendimiento (t/ha). Es la **variable objetivo** del modelo predictivo. Existen dos datasets con esquemas distintos que deben unificarse:

| Dataset | Periodo | Cultivos | ID Socrata |
|---------|---------|----------|------------|
| EVA histórica | 2007–2018 | MAYÚSCULAS | `2pnw-mmge` |
| EVA reciente | 2019–2024 | Title Case | `uejq-wxrr` |

## Subtareas

| ID | Archivo | Qué hace | Depende de | Estado |
|----|---------|----------|------------|--------|
| D1.1 | [D1.1_historica.md](D1.1_historica.md) | Descarga y limpia EVA 2007-2018 | — | 🔲 Pendiente |
| D1.2 | [D1.2_reciente.md](D1.2_reciente.md) | Descarga y limpia EVA 2019-2024 | — | 🔲 Pendiente |
| D1.3 | [D1.3_unificacion.md](D1.3_unificacion.md) | Merge, validación y guardado Parquet | D1.1 + D1.2 | 🔲 Pendiente |
| D1.4 | [D1.4_validacion.md](D1.4_validacion.md) | Script de aceptación y resumen | D1.3 | 🔲 Pendiente |

> D1.1 y D1.2 son **independientes entre sí** — se pueden ejecutar en paralelo.

## Outputs finales
| Archivo | Descripción |
|---------|-------------|
| `data/eva_historica.parquet` | Registros 2007–2018 limpios |
| `data/eva_reciente.parquet` | Registros 2019–2024 limpios |
| `data/eva_completa.parquet` | Unión ordenada de los dos anteriores |

## Esquema unificado (compartido por los 3 archivos)
| Columna | Tipo | Nullable | Valores válidos |
|---------|------|----------|-----------------|
| `codigo_dane` | `str` | No | 5 dígitos, ej: `'05036'` |
| `municipio` | `str` | No | Title Case, ej: `'Anorí'` |
| `departamento` | `str` | No | Title Case, ej: `'Antioquia'` |
| `cultivo` | `str` | No | `'Café'` \| `'Cacao'` \| `'Maíz'` |
| `año` | `int` | No | 2007–2024 |
| `periodo` | `str` | No | `'2022A'` \| `'2022B'` \| `'2022'` |
| `rendimiento` | `float` | Sí | t/ha, `None` si inválido |
| `area_sembrada` | `float` | Sí | ha |
| `area_cosechada` | `float` | Sí | ha |
| `produccion` | `float` | Sí | toneladas |
| `ciclo` | `str` | Sí | `'PERMANENTE'` \| `'TRANSITORIO'` |
| `fuente` | `str` | No | `'historica'` \| `'reciente'` |

## Dependencias compartidas
| Módulo | Uso |
|--------|-----|
| `shared/dane_codes.py` | `MVP_CODIGOS`, `DANE_TO_NAME` |
| `shared/normalization.py` | `normalize_dane_code()`, `normalize_cultivo()`, `normalize_title_case()` |
| `shared/socrata_client.py` | `fetch_all()` |
| `shared/config.py` | `DATA_DIR`, `DATASETS`, `RENDIMIENTO_RANGOS` |

## Restricciones técnicas (aplican a todas las subtareas)
- Filtrar en SoQL, nunca descargar Colombia completa
- Máximo 5.000 registros por llamada; paginación automática vía `fetch_all()`
- Usar `requests` vía `socrata_client.py`, no `sodapy`
- Guardar con `df.to_parquet(path, index=False, engine='pyarrow')`
- No usar `inplace=True` en Pandas
- Usar `pd.to_numeric(col, errors='coerce')` para conversiones numéricas

## Produce para
- **D5** — tabla maestra (feature engineering)
- **M1** — modelo predictivo (variable objetivo `rendimiento`)
