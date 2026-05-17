# D4 — Pipeline Económico (Agroinsumos)

## Resumen
Descarga, limpia y procesa el índice de precios de agroinsumos desde datos.gov.co. Produce una serie mensual con el índice total y sus componentes (fertilizantes, plaguicidas, urea, DAP, KCL), enriquecida con percentiles históricos y señales de riesgo económico, lista para ser consumida por D5 (tabla maestra) y el módulo predictivo.

## Contexto del dominio
El índice de agroinsumos mide la variación de precios de los insumos agrícolas en Colombia. Un aumento sostenido del índice de fertilizantes reduce el margen del productor y puede llevar a reducir el área sembrada o a usar menos insumos, lo que impacta directamente el rendimiento esperado. Para el modelo predictivo se necesita el **valor anual del índice** (promedio de los meses del año) y su **percentil histórico** (¿qué tan caro está este año respecto a los últimos 10 años?).

A diferencia de los pipelines D2 y D3, este dataset es pequeño (~200 registros) y **no tiene dimensión geográfica** — aplica igual a todos los municipios del MVP. Se descarga completo sin filtros SoQL y se agrega por año en Python.

## Subtareas

| ID | Archivo | Qué hace | Depende de | Estado |
|----|---------|----------|------------|--------|
| D4.1 | [D4.1_descarga_limpieza.md](D4.1_descarga_limpieza.md) | Descarga el índice completo y limpia columnas | — | ✅ Completo |
| D4.2 | [D4.2_agregacion_anual.md](D4.2_agregacion_anual.md) | Agrega a nivel anual y calcula percentiles históricos | D4.1 | ✅ Completo |
| D4.3 | [D4.3_validacion.md](D4.3_validacion.md) | Script de validación de los 2 Parquets | D4.2 | ✅ Completo |

> D4.1 y D4.2 son secuenciales. D4.3 valida el output final.

## Outputs finales
| Archivo | Descripción |
|---------|-------------|
| `data/agroinsumos_mensual.parquet` | Serie mensual limpia con todos los componentes del índice |
| `data/agroinsumos.parquet` | Serie anual con índices promedio y percentiles históricos |

## Esquema mensual — `agroinsumos_mensual.parquet`
| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `fecha` | `str` | No | `'YYYY-MM'`, ej: `'2015-03'` |
| `año` | `int` | No | 2007–2024 |
| `mes` | `int` | No | 1–12 |
| `indice_total` | `float` | Sí | Índice general de agroinsumos |
| `fertilizantes` | `float` | Sí | Sub-índice fertilizantes |
| `plaguicidas` | `float` | Sí | Sub-índice plaguicidas |
| `urea` | `float` | Sí | Sub-índice urea |
| `dap` | `float` | Sí | Sub-índice DAP (fosfato diamónico) |
| `kcl` | `float` | Sí | Sub-índice KCL (cloruro de potasio) |

## Esquema anual — `agroinsumos.parquet`
| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `año` | `int` | No | 2007–2024 |
| `indice_total` | `float` | Sí | Promedio anual del índice general |
| `fertilizantes` | `float` | Sí | Promedio anual sub-índice fertilizantes |
| `plaguicidas` | `float` | Sí | Promedio anual sub-índice plaguicidas |
| `urea` | `float` | Sí | Promedio anual sub-índice urea |
| `dap` | `float` | Sí | Promedio anual sub-índice DAP |
| `kcl` | `float` | Sí | Promedio anual sub-índice KCL |
| `n_meses` | `int` | No | Número de meses con datos ese año (1–12) |
| `pct_fertilizantes` | `float` | Sí | Percentil histórico de `fertilizantes` (0.0–1.0) |
| `pct_indice_total` | `float` | Sí | Percentil histórico de `indice_total` (0.0–1.0) |
| `señal_riesgo` | `str` | No | `'Bajo'` \| `'Medio'` \| `'Alto'` según `pct_fertilizantes` |

## Dataset Socrata — ID y columnas reales
| Campo | Valor |
|-------|-------|
| Dataset ID | `gwbi-fnzs` |
| URL | `https://www.datos.gov.co/resource/gwbi-fnzs.json` |
| Registros totales | ~200 (descargar completo, sin filtros) |
| Frecuencia | Mensual |
| Cobertura temporal | ~2007–2024 |

### Columnas reales en la API
| Columna API | Columna unificada | Notas |
|-------------|-------------------|-------|
| `fecha` | `fecha` | string, formato variable (ver D4.1) |
| `indice_total` | `indice_total` | string numérico |
| `total_fertilizantes` | `fertilizantes` | string numérico |
| `total_plaguicidas` | `plaguicidas` | string numérico |
| `urea_46` | `urea` | string numérico |
| `dap_18_46` | `dap` | string numérico |
| `kcl_0_0_60` | `kcl` | string numérico |

> ⚠️ Verificar con una llamada de prueba antes de implementar. La API puede cambiar los nombres.

## Dependencias compartidas
| Módulo | Uso |
|--------|-----|
| `shared/socrata_client.py` | `fetch_all()` — descarga completa sin filtros |
| `shared/config.py` | `DATA_DIR`, `DATASETS` |

> Este pipeline **no usa** `shared/dane_codes.py` ni `shared/normalization.py` porque el dataset no tiene dimensión geográfica.

## Restricciones técnicas (aplican a todas las subtareas)
- Descargar el dataset completo sin filtros SoQL (son ~200 registros)
- Usar `requests` vía `socrata_client.py`, no `sodapy`
- Guardar con `df.to_parquet(path, index=False, engine='pyarrow')`
- No usar `inplace=True` en Pandas
- Usar `pd.to_numeric(col, errors='coerce')` para conversiones numéricas
- La agregación anual se hace en Python, no en SoQL

## Produce para
- **D5** — tabla maestra (feature `fertilizantes`, `pct_fertilizantes`, `señal_riesgo` por año)
- **M1** — variable de entrada al modelo predictivo (riesgo económico por insumos)
