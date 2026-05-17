# D5 — Tabla Maestra (Feature Engineering)

## Resumen
Cruza los outputs de D1–D4 por `codigo_dane + cultivo + año`, construye las variables rezagadas y derivadas, y produce `tabla_maestra.parquet` — el input directo del módulo predictivo.

## Contexto del dominio
La tabla maestra es el artefacto central del pipeline de datos. Cada fila representa una combinación única `(municipio, cultivo, año)` con todas las variables que el modelo XGBoost necesita para predecir el rendimiento. Incluye:

- **Variables objetivo**: `rendimiento` (t/ha) del año actual — solo para entrenamiento, nunca como feature.
- **Features rezagadas de EVA**: rendimiento del año anterior, promedio 3 años, tendencia, área sembrada.
- **Features climáticas**: precipitación acumulada, temperatura media, humedad, días secos, anomalías.
- **Features territoriales**: % aptitud alta/media/baja por cultivo, % frontera condicionada.
- **Features económicas**: índice de fertilizantes anual, percentil histórico, señal de riesgo.

La tabla cubre los años 2007–2024 para los 15 municipios del MVP y los 3 cultivos del MVP. Las filas con año < 2010 pueden tener features rezagadas incompletas (NaN) — esto es esperado y no es un error.

## Subtareas

| ID | Archivo | Qué hace | Depende de | Estado |
|----|---------|----------|------------|--------|
| D5.1 | [D5.1_carga_validacion_inputs.md](D5.1_carga_validacion_inputs.md) | Carga y valida los 8 Parquets de entrada | D1–D4 | 🔲 Pendiente |
| D5.2 | [D5.2_features_eva.md](D5.2_features_eva.md) | Construye features rezagadas de EVA | D5.1 | 🔲 Pendiente |
| D5.3 | [D5.3_cruce_features.md](D5.3_cruce_features.md) | Cruza EVA + clima + territorial + económico | D5.2 | 🔲 Pendiente |
| D5.4 | [D5.4_validacion.md](D5.4_validacion.md) | Script de validación de la tabla maestra | D5.3 | 🔲 Pendiente |

> D5.1 y D5.2 son secuenciales. D5.3 depende de D5.2. D5.4 valida el output final.

## Outputs finales
| Archivo | Descripción |
|---------|-------------|
| `data/tabla_maestra.parquet` | Tabla cruzada con todas las features, lista para el modelo |

## Esquema de la tabla maestra
| Columna | Tipo | Nullable | Descripción |
|---------|------|----------|-------------|
| `codigo_dane` | `str` | No | 5 dígitos, llave de unión |
| `municipio` | `str` | No | Title Case |
| `departamento` | `str` | No | Title Case |
| `cultivo` | `str` | No | `'Café'` \| `'Cacao'` \| `'Maíz'` |
| `año` | `int` | No | 2007–2024 |
| `rendimiento` | `float` | Sí | Variable objetivo (t/ha) — no usar como feature |
| `area_sembrada` | `float` | Sí | Área sembrada ese año (ha) |
| `rendimiento_t1` | `float` | Sí | Rendimiento año anterior (feature rezagada) |
| `rendimiento_t2` | `float` | Sí | Rendimiento hace 2 años |
| `rendimiento_t3` | `float` | Sí | Rendimiento hace 3 años |
| `rendimiento_prom3a` | `float` | Sí | Promedio rendimiento últimos 3 años |
| `rendimiento_tend3a` | `float` | Sí | Pendiente lineal rendimiento últimos 3 años |
| `area_sembrada_t1` | `float` | Sí | Área sembrada año anterior |
| `area_cambio_pct` | `float` | Sí | Cambio % área sembrada vs año anterior |
| `prec_acum_mm` | `float` | Sí | Precipitación acumulada anual (mm) |
| `temp_media_c` | `float` | Sí | Temperatura media anual (°C) |
| `hum_media_pct` | `float` | Sí | Humedad relativa media anual (%) |
| `dias_secos` | `float` | Sí | Días con precipitación < 1 mm |
| `anomalia_prec` | `float` | Sí | Anomalía precipitación vs media histórica (%) |
| `anomalia_temp` | `float` | Sí | Anomalía temperatura vs media histórica (°C) |
| `pct_aptitud_alta` | `float` | Sí | % área con aptitud alta para el cultivo |
| `pct_aptitud_media` | `float` | Sí | % área con aptitud media |
| `pct_aptitud_baja` | `float` | Sí | % área con aptitud baja |
| `pct_exclusion` | `float` | Sí | % área de exclusión |
| `pct_condicionada` | `float` | Sí | % frontera agrícola condicionada |
| `fertilizantes` | `float` | Sí | Índice anual de fertilizantes |
| `pct_fertilizantes` | `float` | Sí | Percentil histórico del índice (0.0–1.0) |
| `señal_riesgo_eco` | `str` | Sí | `'Bajo'` \| `'Medio'` \| `'Alto'` |

> **Regla de fuga**: `rendimiento`, `area_cosechada` y `produccion` del mismo año **nunca** son features. Solo `rendimiento` se incluye como variable objetivo.

## Dependencias de entrada
| Parquet | Pipeline | Columnas usadas |
|---------|----------|-----------------|
| `eva_completa.parquet` | D1 | `codigo_dane, cultivo, año, rendimiento, area_sembrada` |
| `clima_agregado.parquet` | D2 | `codigo_dane, año, prec_acum_mm, temp_media_c, hum_media_pct, dias_secos, anomalia_prec, anomalia_temp` |
| `aptitud_cafe.parquet` | D3 | `codigo_dane, pct_alta, pct_media, pct_baja, pct_exclusion` |
| `aptitud_cacao.parquet` | D3 | mismo esquema |
| `aptitud_maiz.parquet` | D3 | mismo esquema |
| `frontera.parquet` | D3 | `codigo_dane, pct_condicionada` |
| `agroinsumos.parquet` | D4 | `año, fertilizantes, pct_fertilizantes, señal_riesgo` |

## Dependencias compartidas
| Módulo | Uso |
|--------|-----|
| `shared/dane_codes.py` | `MVP_CODIGOS`, `DANE_TO_NAME`, `DANE_TO_DEPT` |
| `shared/config.py` | `DATA_DIR`, `CULTIVOS_MVP`, `TRAIN_HASTA`, `VAL_AÑO`, `TEST_DESDE` |

## Restricciones técnicas (aplican a todas las subtareas)
- Llave de unión siempre `codigo_dane` (string 5 dígitos) — nunca por nombre de municipio
- Usar `pd.merge(..., how='left')` desde EVA como tabla base — nunca `inner` (perdería filas sin clima)
- No usar `inplace=True` en Pandas
- Guardar con `df.to_parquet(path, index=False, engine='pyarrow')`
- Features rezagadas con NaN son válidas — no imputar ni eliminar filas
- No hardcodear códigos DANE ni nombres de cultivos — usar `shared/`

## Produce para
- **M1** — feature engineering del modelo predictivo
- **M2** — entrenamiento XGBoost Regressor
- **M3** — entrenamiento XGBoost Classifier de riesgo
