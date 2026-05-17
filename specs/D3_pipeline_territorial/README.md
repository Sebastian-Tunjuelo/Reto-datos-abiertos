# D3 — Pipeline Territorial (UPRA)

## Resumen
Descarga, agrega y unifica los datos de aptitud agrícola y frontera agropecuaria de los 15 municipios del MVP desde los datasets UPRA de datos.gov.co. Produce 4 archivos Parquet estáticos (uno por cultivo + frontera) listos para ser consumidos por D5 (tabla maestra) y el módulo predictivo.

## Contexto del dominio
UPRA (Unidad de Planificación Rural Agropecuaria) publica la zonificación de aptitud del suelo por cultivo y la delimitación de la frontera agrícola nacional. Para el modelo predictivo se necesitan variables **agregadas por municipio**: porcentaje de área en cada categoría de aptitud (Alta, Media, Baja, Exclusión) y porcentaje de área condicionada por la frontera. Estas variables son **estáticas** — no cambian por año — y se unen a la tabla maestra como features constantes por `(codigo_dane, cultivo)`.

El reto principal es que todos los datasets UPRA contienen geometrías (polígonos) que hacen que cada municipio tenga múltiples filas (una por polígono). **Nunca se descargan geometrías** — siempre se agrega con `$group` y `sum(area_ha)` en SoQL para obtener una fila por `(municipio, aptitud)`.

Para maíz existen 3 datasets complementarios: maíz tradicional (`frjn-92um`), maíz tecnificado 1er semestre (`a5yc-uszt`) y maíz tecnificado 2do semestre (`tzga-4zse`). Se descargan los tres y se consolida en un único `aptitud_maiz.parquet` tomando el máximo de aptitud por municipio.

## Subtareas

| ID | Archivo | Qué hace | Depende de | Estado |
|----|---------|----------|------------|--------|
| D3.1 | [D3.1_aptitud_cafe_cacao.md](D3.1_aptitud_cafe_cacao.md) | Descarga aptitud café (`kwvf-nwea`) y cacao (`jdjx-qer4`) | — | ✅ Completo |
| D3.2 | [D3.2_aptitud_maiz.md](D3.2_aptitud_maiz.md) | Descarga y consolida aptitud maíz (3 datasets UPRA) | — | ✅ Completo |
| D3.3 | [D3.3_frontera.md](D3.3_frontera.md) | Descarga frontera agrícola (`fyc7-sbtz`) | — | ✅ Completo |
| D3.4 | [D3.4_validacion.md](D3.4_validacion.md) | Script de validación de los 4 Parquets | D3.1 + D3.2 + D3.3 | ✅ Completo |

> D3.1, D3.2 y D3.3 son **independientes entre sí** — se pueden ejecutar en paralelo.

## Outputs finales
| Archivo | Descripción |
|---------|-------------|
| `data/aptitud_cafe.parquet` | Aptitud por municipio para café |
| `data/aptitud_cacao.parquet` | Aptitud por municipio para cacao |
| `data/aptitud_maiz.parquet` | Aptitud consolidada por municipio para maíz (3 datasets) |
| `data/frontera.parquet` | Porcentaje de área condicionada por frontera agrícola |

## Esquema unificado de aptitud (compartido por los 3 archivos de aptitud)
| Columna | Tipo | Nullable | Valores válidos |
|---------|------|----------|-----------------|
| `codigo_dane` | `str` | No | 5 dígitos, ej: `'05036'` |
| `municipio` | `str` | No | Title Case, ej: `'Anorí'` |
| `departamento` | `str` | No | Title Case |
| `cultivo` | `str` | No | `'Café'` \| `'Cacao'` \| `'Maíz'` |
| `area_alta_ha` | `float` | Sí | ha con aptitud Alta |
| `area_media_ha` | `float` | Sí | ha con aptitud Media |
| `area_baja_ha` | `float` | Sí | ha con aptitud Baja |
| `area_exclusion_ha` | `float` | Sí | ha con aptitud Exclusión / No apta |
| `area_total_ha` | `float` | No | Suma de todas las categorías |
| `pct_alta` | `float` | No | `area_alta_ha / area_total_ha` (0.0–1.0) |
| `pct_media` | `float` | No | `area_media_ha / area_total_ha` (0.0–1.0) |
| `pct_baja` | `float` | No | `area_baja_ha / area_total_ha` (0.0–1.0) |
| `pct_exclusion` | `float` | No | `area_exclusion_ha / area_total_ha` (0.0–1.0) |

## Esquema de frontera
| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `codigo_dane` | `str` | No | 5 dígitos |
| `municipio` | `str` | No | Title Case |
| `departamento` | `str` | No | Title Case |
| `area_condicionada_ha` | `float` | Sí | ha dentro de frontera condicionada |
| `area_no_condicionada_ha` | `float` | Sí | ha fuera de frontera (no apta para expansión) |
| `area_total_ha` | `float` | No | Suma de todas las categorías |
| `pct_condicionada` | `float` | No | `area_condicionada_ha / area_total_ha` (0.0–1.0) |
| `pct_no_condicionada` | `float` | No | `area_no_condicionada_ha / area_total_ha` (0.0–1.0) |

## Datasets UPRA — IDs y columnas reales
| Dataset | ID Socrata | Advertencia |
|---------|-----------|-------------|
| Aptitud café | `kwvf-nwea` | ⚠️ geometrías — siempre `$group` + `sum(area_ha)` |
| Aptitud cacao | `jdjx-qer4` | ⚠️ geometrías |
| Aptitud maíz tradicional | `frjn-92um` | ⚠️ solo 123 municipios en Colombia |
| Aptitud maíz tec. 1er sem. | `a5yc-uszt` | ⚠️ geometrías |
| Aptitud maíz tec. 2do sem. | `tzga-4zse` | ⚠️ geometrías |
| Frontera agrícola | `fyc7-sbtz` | ⚠️ geometrías |

### Columnas reales en los datasets de aptitud (café y cacao)
| Columna API | Tipo | Descripción |
|-------------|------|-------------|
| `cod_dane_m` | string | Código DANE municipio (5 dígitos, bien formateado) |
| `municipio` | string | Nombre del municipio (MAYÚSCULAS) |
| `departamen` | string | Nombre del departamento (MAYÚSCULAS, truncado) |
| `aptitud` | string | `'Alta'`, `'Media'`, `'Baja'`, `'Exclusión'` (o variantes) |
| `area_ha` | string | Área del polígono en hectáreas (viene como string) |

### Columnas reales en los datasets de maíz
| Columna API | Tipo | Descripción |
|-------------|------|-------------|
| `cod_dane_m` | string | Código DANE municipio |
| `municipio` | string | Nombre del municipio (MAYÚSCULAS) |
| `departamen` | string | Nombre del departamento (MAYÚSCULAS) |
| `aptitud` | string | Categoría de aptitud |
| `area_ha` | string | Área en hectáreas |

### Columnas reales en frontera agrícola
| Columna API | Tipo | Descripción |
|-------------|------|-------------|
| `cod_dane_m` | string | Código DANE municipio |
| `municipio` | string | Nombre del municipio (MAYÚSCULAS) |
| `departamen` | string | Nombre del departamento (MAYÚSCULAS) |
| `tipo_front` | string | `'Condicionada'`, `'No condicionada'` (o variantes) |
| `area_ha` | string | Área en hectáreas |

### Filtro SoQL de referencia (aplica a todos los datasets UPRA)
```
$select=cod_dane_m,municipio,departamen,aptitud,sum(area_ha) AS area_total
$where=cod_dane_m IN ('73001','73168','41001','41298','41551','68689','68615',
  '05036','05030','17541','17524','50001','19256','19418','20001')
$group=cod_dane_m,municipio,departamen,aptitud
```
> El `$group` es obligatorio para evitar descargar geometrías. Sin él, cada polígono es una fila separada y el volumen puede ser enorme.

## Categorías de aptitud — normalización
Los valores del campo `aptitud` pueden variar entre datasets. La normalización canónica es:

| Valor en API (posibles variantes) | Categoría canónica |
|-----------------------------------|-------------------|
| `'Alta'`, `'ALTA'`, `'A'` | `'Alta'` |
| `'Media'`, `'MEDIA'`, `'M'`, `'Moderada'` | `'Media'` |
| `'Baja'`, `'BAJA'`, `'B'` | `'Baja'` |
| `'Exclusión'`, `'EXCLUSION'`, `'No apta'`, `'E'` | `'Exclusion'` |

Cualquier valor no reconocido → `None`; loggear el valor inesperado.

## Dependencias compartidas
| Módulo | Uso |
|--------|-----|
| `shared/dane_codes.py` | `MVP_CODIGOS`, `DANE_TO_NAME`, `DANE_TO_DEPT` |
| `shared/normalization.py` | `normalize_dane_code()`, `normalize_title_case()` |
| `shared/socrata_client.py` | `fetch_all()` |
| `shared/config.py` | `DATA_DIR`, `DATASETS` |

## Restricciones técnicas (aplican a todas las subtareas)
- **Siempre** usar `$group` + `sum(area_ha)` en SoQL — nunca descargar geometrías
- Filtrar por `cod_dane_m` en SoQL — nunca descargar Colombia completa
- Usar `requests` vía `socrata_client.py`, no `sodapy`
- Guardar con `df.to_parquet(path, index=False, engine='pyarrow')`
- No usar `inplace=True` en Pandas
- Usar `pd.to_numeric(col, errors='coerce')` para conversiones numéricas
- Los datos son estáticos — no tienen dimensión temporal

## Produce para
- **D5** — tabla maestra (features de aptitud y frontera por `codigo_dane + cultivo`)
- **M1** — variables de entrada al modelo predictivo (aptitud UPRA, frontera)
