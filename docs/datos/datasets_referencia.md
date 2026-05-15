# Datasets de referencia — datos.gov.co

Referencia técnica de todos los datasets usados en el proyecto. Incluye IDs Socrata, columnas reales, advertencias y estrategias de descarga. Leer antes de implementar cualquier pipeline de datos.

**URL base de la API**: `https://www.datos.gov.co/resource/{dataset_id}.json`

---

## Datasets de producción agrícola (EVA)

### EVA histórica 2007-2018
| Campo | Valor |
|-------|-------|
| Dataset ID | `2pnw-mmge` |
| Registros totales | ~180.000 (Colombia completa) |
| Registros MVP | ~1.500–2.000 |

**Columnas reales en la API:**
| Columna | Tipo | Notas |
|---------|------|-------|
| `c_d_mun` | string | Código DANE — ⚠️ puede venir sin cero inicial (ej. `'5036'`) |
| `municipio` | string | MAYÚSCULAS |
| `departamento` | string | MAYÚSCULAS |
| `cultivo` | string | `'CAFÉ'`, `'CACAO'`, `'MAÍZ'` — siempre MAYÚSCULAS |
| `a_o` | string | Año como string: `'2007'`..`'2018'` |
| `periodo` | string | `'2015A'`, `'2015B'` o `'2015'` para anuales |
| `rendimiento_t_ha` | string | t/ha — viene como string, puede ser vacío o `'0'` |
| `rea_sembrada_ha` | string | ha |
| `rea_cosechada_ha` | string | ha |
| `producci_n_t` | string | toneladas |
| `ciclo_de_cultivo` | string | `'PERMANENTE'` o `'TRANSITORIO'` |

**Filtro SoQL recomendado:**
```
$where=cultivo IN ('CAFÉ','CACAO','MAÍZ') AND c_d_mun IN ('73001','73168','41001','41298','41551','68689','68615','05036','05030','17541','17524','50001','19256','19418','20001')
```

---

### EVA reciente 2019-2024
| Campo | Valor |
|-------|-------|
| Dataset ID | `uejq-wxrr` |
| Registros totales | ~60.000 (Colombia completa) |
| Registros MVP | ~500–800 |

**Columnas reales en la API:**
| Columna | Tipo | Notas |
|---------|------|-------|
| `c_digo_dane_municipio` | string | Código DANE — ✅ bien formateado con cero inicial |
| `municipio` | string | Title Case |
| `departamento` | string | Title Case |
| `cultivo` | string | `'Café'`, `'Cacao'`, `'Maíz'` — Title Case |
| `a_o` | string | Año como string: `'2019'`..`'2024'` |
| `periodo` | string | `'2022A'`, `'2022B'` o `'2022'` |
| `rendimiento` | string | t/ha — viene como string |
| `rea_sembrada` | string | ha |
| `rea_cosechada` | string | ha |
| `producci_n` | string | toneladas |
| `ciclo_del_cultivo` | string | `'PERMANENTE'` o `'TRANSITORIO'` |

**Filtro SoQL recomendado:**
```
$where=cultivo IN ('Café','Cacao','Maíz') AND c_digo_dane_municipio IN ('73001','73168','41001','41298','41551','68689','68615','05036','05030','17541','17524','50001','19256','19418','20001')
```

---

## Datasets climáticos (IDEAM)

### Catálogo Nacional de Estaciones IDEAM
| Campo | Valor |
|-------|-------|
| Dataset ID | `hp9r-jxuu` |
| Uso | Obtener códigos de estación por municipio antes de descargar clima |

**Columnas clave:** `codigo`, `nombre`, `categoria`, `tecnologia`, `estado`, `municipio`, `departamento`, `latitud`, `longitud`, `altitud`

**Categorías relevantes para el MVP:**
- `CLIMATOLOGICA ORDINARIA` — tiene precipitación + temperatura
- `CLIMATOLOGICA PRINCIPAL` — tiene precipitación + temperatura + humedad
- `AGROMETEOROLÓGICA` — tiene humedad relativa

**Estrategia**: filtrar por `estado = 'Activa'` y municipios del MVP. Usar `codigo` como llave para descargar datos de precipitación/temperatura.

---

### Precipitación IDEAM
| Campo | Valor |
|-------|-------|
| Dataset ID | `s54a-sgyg` |
| Registros totales | ~165 millones |
| ⚠️ Advertencia | NUNCA descargar sin filtros — usar agregaciones SoQL |

**Columnas clave:** `codigoestacion`, `fechaobservacion`, `valorobservado`, `municipio`, `departamento`, `latitud`, `longitud`

**Estrategia de descarga para el MVP:**
```
$select=codigoestacion,municipio,date_trunc_ym(fechaobservacion) AS mes,sum(valorobservado) AS prec_mensual
$where=codigoestacion IN ('...') AND fechaobservacion >= '2007-01-01'
$group=codigoestacion,municipio,date_trunc_ym(fechaobservacion)
```

---

### Temperatura Ambiente del Aire IDEAM
| Campo | Valor |
|-------|-------|
| Dataset ID | `sbwg-7ju4` |
| Registros totales | ~50 millones |
| ⚠️ Advertencia | Usar agregaciones, no descargar crudo |

**Columnas clave:** `codigoestacion`, `fechaobservacion`, `valorobservado`, `municipio`, `latitud`, `longitud`

**Estrategia**: misma que precipitación pero con `avg(valorobservado)` para temperatura media mensual.

---

### Humedad del Aire IDEAM
| Campo | Valor |
|-------|-------|
| Dataset ID | `uext-mhny` |
| Cobertura MVP | 15/15 municipios (vía estaciones climatológicas/agrometeorológicas) |

**Columnas clave:** `codigoestacion`, `fechaobservacion`, `valorobservado`, `municipio`

---

### Estaciones recientes IDEAM y de Terceros
| Campo | Valor |
|-------|-------|
| Dataset ID | `57sv-p2fu` |
| Uso | Datos casi en tiempo real para los 9 municipios con cobertura directa |
| Cobertura directa | 9/15 municipios del MVP |
| Cobertura vía catálogo | 6/15 municipios (usar `hp9r-jxuu`) |

**Municipios con datos recientes directos:** Ibagué, Neiva, Garzón, Pitalito, Amalfi, Pensilvania, Rionegro, Villavicencio, Valledupar

**Municipios sin datos recientes** (usar catálogo histórico): Palestina, Chaparral, Miranda, El Tambo, San Vicente de Chucurí, Anorí

---

## Datasets de aptitud UPRA

> ⚠️ **Advertencia crítica**: todos los datasets UPRA tienen geometrías pesadas (400k–500k registros). Usar siempre `$group` en SoQL para evitar descargar geometrías. Nunca hacer `fetch_all()` sin `group`.

### Aptitud para café
| Campo | Valor |
|-------|-------|
| Dataset ID | `kwvf-nwea` |
| Cobertura | 1.039 municipios |

**Columnas clave:** `municipio`, `departamento`, `codigo_dane`, `aptitud`, `area_ha`

**Query SoQL recomendada:**
```
$select=codigo_dane,municipio,departamento,aptitud,sum(area_ha) AS area_total
$where=codigo_dane IN ('73001','73168',...)
$group=codigo_dane,municipio,departamento,aptitud
```

---

### Aptitud para cacao
| Campo | Valor |
|-------|-------|
| Dataset ID | `jdjx-qer4` |
| Cobertura | 1.039 municipios |

Misma estructura que aptitud café.

---

### Aptitud para maíz (3 datasets — usar unión)
| Dataset | ID | Cobertura |
|---------|-----|-----------|
| Maíz tradicional | `frjn-92um` | 123 municipios ⚠️ |
| Maíz tecnificado 1er semestre | `a5yc-uszt` | 1.039 municipios |
| Maíz tecnificado 2do semestre | `tzga-4zse` | 1.039 municipios |

**Estrategia**: descargar los 3 y hacer unión. La cobertura sube de 123 a 1.039 municipios. Para el MVP, los 15 municipios tienen cobertura en al menos uno de los tres.

---

### Frontera agrícola
| Campo | Valor |
|-------|-------|
| Dataset ID | `fyc7-sbtz` |
| Cobertura | 1.039 municipios |

**Columnas clave:** `municipio`, `departamento`, `codigo_dane`, `tipo_frontera`, `area_ha`

**Valores de `tipo_frontera`:** `'Frontera Agrícola'`, `'Frontera Agrícola Condicionada'`

---

## Dataset económico

### Índice de precios de insumos agrícolas
| Campo | Valor |
|-------|-------|
| Dataset ID | `gwbi-fnzs` |
| Registros totales | ~200 (mensual, desde 2000) |
| Cobertura | Nacional — aplica a todos los municipios |

**Columnas clave:** `fecha`, `indice_total`, `fertilizantes`, `plaguicidas`, `herbicidas`, `fungicidas`, `insecticidas`, `urea`, `dap`, `kcl`

**Estrategia**: descargar completo con `fetch_all()` — es pequeño.

---

### Precios RAP Eje Cafetero
| Campo | Valor |
|-------|-------|
| Dataset ID | `gdqq-rry2` |
| Cobertura | 4 ciudades: Armenia, Ibagué, Manizales, Pereira |
| Relevancia MVP | Ibagué (directo) + Palestina/Pensilvania (cercanas a Manizales) |

**Columnas clave:** `producto`, `mercado`, `precio_minimo`, `precio_maximo`, `precio_medio`, `fecha_inicial`, `fecha_final`, `categoria`

---

## Advertencias técnicas generales

### Normalización de códigos DANE
- EVA histórica: `c_d_mun` puede venir sin cero inicial (ej. `'5036'` en lugar de `'05036'`)
- EVA reciente: `c_digo_dane_municipio` viene bien formateado
- Siempre normalizar con `normalize_dane_code()` de `shared/normalization.py`
- Usar código DANE de 5 dígitos como llave de unión entre todos los datasets

### Normalización de nombres de cultivos
- EVA histórica: `'CAFÉ'`, `'CACAO'`, `'MAÍZ'` (MAYÚSCULAS con tildes)
- EVA reciente: `'Café'`, `'Cacao'`, `'Maíz'` (Title Case)
- Usar `normalize_cultivo()` de `shared/normalization.py` para unificar

### Paginación Socrata
- Máximo 5.000 registros por llamada
- Usar `fetch_all()` de `shared/socrata_client.py` para paginación automática
- Siempre filtrar en SoQL (`$where`), nunca descargar Colombia completa

### Rangos de rendimiento válidos
| Cultivo | Mínimo | Máximo | Unidad |
|---------|--------|--------|--------|
| Café | 0.3 | 3.0 | t/ha |
| Cacao | 0.2 | 2.5 | t/ha |
| Maíz | 0.5 | 10.0 | t/ha |

Valores fuera de rango → `None` (no eliminar la fila). Definidos en `shared/config.py → RENDIMIENTO_RANGOS`.
