# D2 — Pipeline Clima (IDEAM)

## Resumen

Descarga, agrega y procesa las variables climáticas de los 15 municipios del MVP desde los datasets IDEAM de datos.gov.co. Produce una serie anual por municipio con precipitación, temperatura, humedad y anomalías, lista para ser consumida por el módulo predictivo.

El pipeline ya fue ejecutado con éxito y genera `data/clima_agregado.parquet`. La implementación final quedó ajustada para tolerar timeouts de Socrata, guardar intermedios y re-agregar localmente los bloques descargados.

## Contexto del dominio

IDEAM publica mediciones de estaciones meteorológicas a nivel de observación individual (horaria o diaria). Para el modelo predictivo se necesitan variables **agregadas por municipio y año**: acumulados, promedios, conteos de días extremos y anomalías respecto a la media histórica. El reto principal es el volumen: precipitación tiene ~165M registros y temperatura ~50M — nunca se descargan crudos, siempre se agrega en SoQL.

La relación entre estaciones y municipios no es directa: una estación tiene coordenadas y un campo `municipio`, pero puede estar en un municipio distinto al que sirve. La estrategia del MVP es filtrar por nombre de municipio en la API y aceptar las estaciones que IDEAM ya asoció a ese municipio.

## ⚠️ Nota de arquitectura — estrategia de filtrado por municipio

Los datasets de observaciones IDEAM (`s54a-sgyg`, `sbwg-7ju4`, `uext-mhny`) **no tienen índice sobre `codigoestacion`** en el servidor Socrata de `datos.gov.co`. Cualquier consulta con `WHERE codigoestacion IN (...)` provoca un full-scan y hace timeout incluso con 1 sola estación y 1 año de datos.

**Estrategia adoptada en D2.2 y D2.3**:

- Filtrar por `municipio IN (...)` en **MAYÚSCULAS** (campo indexado en el servidor)
- Dividir el rango temporal en **ventanas de 6 meses** (`IDEAM_MONTH_CHUNK`, default 6 meses) para acotar el volumen por llamada
- Re-agregar localmente con pandas los resultados parciales de cada ventana
- El catálogo de estaciones (D2.1) se mantiene como output de auditoría pero **ya no se usa como intermediario** para filtrar las consultas de observaciones

**Resultado operativo**: la estrategia por municipio permitió obtener datos reales y completar el parquet final, aunque con cobertura parcial en la corrida reducida 2023–2024. El spec queda listo para continuar con más años si se decide ampliar la ventana de descarga.

## Subtareas

| ID   | Archivo                                                    | Qué hace                                                     | Depende de  | Estado      |
| ---- | ---------------------------------------------------------- | ------------------------------------------------------------ | ----------- | ----------- |
| D2.1 | [D2.1_estaciones.md](D2.1_estaciones.md)                   | Descarga catálogo de estaciones IDEAM para los 15 municipios | —           | ✅ Completo |
| D2.2 | [D2.2_precipitacion.md](D2.2_precipitacion.md)             | Descarga precipitación agregada por municipio y año          | D2.1        | ✅ Completo |
| D2.3 | [D2.3_temperatura_humedad.md](D2.3_temperatura_humedad.md) | Descarga temperatura y humedad agregadas por municipio y año | D2.1        | ✅ Completo |
| D2.4 | [D2.4_anomalias_guardado.md](D2.4_anomalias_guardado.md)   | Calcula anomalías, une variables y guarda Parquet            | D2.2 + D2.3 | ✅ Completo |
| D2.5 | [D2.5_validacion.md](D2.5_validacion.md)                   | Script de aceptación y resumen                               | D2.4        | ✅ Completo |

> D2.2 y D2.3 son **independientes entre sí** — se pueden ejecutar en paralelo una vez que D2.1 esté completo.

> Estado operativo reciente: `run_pipeline()` dejó guardados `data/precipitacion.parquet`, `data/temperatura.parquet`, `data/humedad.parquet` y el agregado final `data/clima_agregado.parquet`.

## Output final

| Archivo                       | Descripción                                                  |
| ----------------------------- | ------------------------------------------------------------ |
| `data/clima_agregado.parquet` | Serie anual por municipio con todas las variables climáticas |

## Intermedios guardados

| Archivo                      | Descripción                                              |
| ---------------------------- | -------------------------------------------------------- |
| `data/precipitacion.parquet` | Intermedio agregado de precipitación por municipio y año |
| `data/temperatura.parquet`   | Intermedio agregado de temperatura por municipio y año   |
| `data/humedad.parquet`       | Intermedio agregado de humedad por municipio y año       |

## Esquema del output (compartido por todas las subtareas)

| Columna             | Tipo    | Nullable | Descripción                                                                      |
| ------------------- | ------- | -------- | -------------------------------------------------------------------------------- |
| `codigo_dane`       | `str`   | No       | 5 dígitos, ej: `'05036'`                                                         |
| `municipio`         | `str`   | No       | Title Case, ej: `'Anorí'`                                                        |
| `año`               | `int`   | No       | 2007–2024                                                                        |
| `prec_acum_mm`      | `float` | Sí       | Precipitación acumulada anual (mm)                                               |
| `prec_dias_secos`   | `int`   | Sí       | Días con precipitación < 1 mm                                                    |
| `prec_dias_lluvia`  | `int`   | Sí       | Días con precipitación ≥ 1 mm                                                    |
| `temp_media_c`      | `float` | Sí       | Temperatura media anual (°C)                                                     |
| `temp_max_media_c`  | `float` | Sí       | Media de temperaturas máximas diarias (°C)                                       |
| `hum_media_pct`     | `float` | Sí       | Humedad relativa media anual (%)                                                 |
| `n_estaciones_prec` | `int`   | No       | Número de estaciones usadas para precipitación                                   |
| `n_estaciones_temp` | `int`   | No       | Número de estaciones usadas para temperatura                                     |
| `anomalia_prec`     | `float` | Sí       | Desviación de `prec_acum_mm` respecto a media histórica (fracción: 0.0 = normal) |
| `anomalia_temp`     | `float` | Sí       | Desviación de `temp_media_c` respecto a media histórica (°C absolutos)           |

## Dependencias compartidas

| Módulo                     | Uso                                               |
| -------------------------- | ------------------------------------------------- |
| `shared/dane_codes.py`     | `MVP_CODIGOS`, `DANE_TO_NAME`, `MVP_MUNICIPIOS`   |
| `shared/normalization.py`  | `normalize_dane_code()`, `normalize_title_case()` |
| `shared/socrata_client.py` | `fetch_all()`, `fetch()`                          |
| `shared/config.py`         | `DATA_DIR`, `DATASETS`                            |

## Restricciones técnicas (aplican a todas las subtareas)

- **Nunca** descargar registros crudos de precipitación o temperatura — siempre agregar con `$group` en SoQL
- **Nunca** filtrar por `codigoestacion` en D2.2/D2.3 — usar `municipio` en MAYÚSCULAS (ver nota de arquitectura)
- Máximo 5.000 registros por llamada; paginación automática vía `fetch_all()`
- Usar `requests` vía `socrata_client.py`, no `sodapy`
- Guardar con `df.to_parquet(path, index=False, engine='pyarrow')`
- No usar `inplace=True` en Pandas
- Usar `pd.to_numeric(col, errors='coerce')` para conversiones numéricas
- Filtrar siempre por nombre de municipio en SoQL — no descargar Colombia completa

## Estado de cierre

- El pipeline D2 ya produjo el parquet final y los intermedios necesarios para continuar iterando sin repetir la descarga completa.
- La siguiente ampliación natural es ejecutar con más años si se quiere aumentar cobertura histórica y mejorar anomalías.

## Produce para

- **D5** — tabla maestra (feature engineering climático)
- **M1** — variables de entrada al modelo predictivo
