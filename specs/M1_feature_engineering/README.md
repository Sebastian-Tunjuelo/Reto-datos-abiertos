# M1 — Feature Engineering (Feature_Matrix)

## Resumen

Construye la matriz de features para M2/M3 a partir de `tabla_maestra.parquet` (D5).
Extiende las features base con clima, rezagos temporales, aptitud territorial y
senales economicas, y guarda `feature_matrix.parquet` sin fuga de informacion.

## Contexto del dominio

La variable objetivo es `rendimiento`. La Feature_Matrix se usa para entrenar:

- M2: XGBoost regresion de rendimiento
- M3: XGBoost clasificacion de riesgo

## Subtareas

| ID   | Archivo                                                                  | Que hace                                | Depende de | Estado       |
| ---- | ------------------------------------------------------------------------ | --------------------------------------- | ---------- | ------------ |
| M1.1 | [M1.1_validacion_entrada_clima.md](M1.1_validacion_entrada_clima.md)     | Validacion de input + clamping de clima | —          | ⏳ Pendiente |
| M1.2 | [M1.2_rezagos_temporales.md](M1.2_rezagos_temporales.md)                 | Rezagos sin fuga por municipio-cultivo  | M1.1       | ⏳ Pendiente |
| M1.3 | [M1.3_aptitud_agroinsumos_schema.md](M1.3_aptitud_agroinsumos_schema.md) | Aptitud, agroinsumos, esquema, guardado | M1.2       | ⏳ Pendiente |
| M1.4 | [M1.4_validacion.md](M1.4_validacion.md)                                 | Script de validacion independiente      | M1.3       | ⏳ Pendiente |

> M1.1, M1.2 y M1.3 son secuenciales. M1.4 depende del output final.

## Outputs finales

| Archivo                                       | Descripcion                                    |
| --------------------------------------------- | ---------------------------------------------- |
| `data/feature_matrix.parquet`                 | Matriz final con 25 columnas listas para M2/M3 |
| `specs/M1_feature_engineering/validate_m1.py` | Script de validacion independiente             |

## Esquema de salida (Feature_Matrix)

| Columna                   | Tipo    | Nullable | Notas                       |
| ------------------------- | ------- | -------- | --------------------------- |
| `codigo_dane`             | `str`   | No       | 5 digitos                   |
| `municipio`               | `str`   | No       | Title Case                  |
| `departamento`            | `str`   | No       | Title Case                  |
| `cultivo`                 | `str`   | No       | `Café` \| `Cacao` \| `Maíz` |
| `año`                     | `Int64` | No       | 2007–2024                   |
| `prec_acum_mm`            | `float` | Si       | mm                          |
| `anomalia_prec`           | `float` | Si       | mm                          |
| `temp_media_c`            | `float` | Si       | °C                          |
| `anomalia_temp`           | `float` | Si       | °C                          |
| `dias_secos`              | `float` | Si       | 0–365                       |
| `hum_media_pct`           | `float` | Si       | 0–100                       |
| `rendimiento_t1`          | `float` | Si       | t-1                         |
| `rendimiento_prom3a`      | `float` | Si       | prom t-1..t-3 (min 2)       |
| `tendencia_rend_3a`       | `float` | Si       | pendiente t-1..t-3          |
| `area_sembrada_t1`        | `float` | Si       | ha                          |
| `pct_alta`                | `float` | Si       | aptitud UPRA                |
| `pct_media`               | `float` | Si       | aptitud UPRA                |
| `pct_baja`                | `float` | Si       | aptitud UPRA                |
| `pct_exclusion`           | `float` | Si       | aptitud UPRA                |
| `pct_condicionada`        | `float` | Si       | frontera agricola           |
| `pct_no_condicionada`     | `float` | Si       | frontera agricola           |
| `indice_agroinsumos`      | `float` | Si       | `indice_total`              |
| `percentil_fertilizantes` | `float` | Si       | 0–100, expanding            |
| `señal_riesgo_economico`  | `str`   | Si       | `bajo` \| `medio` \| `alto` |
| `target_rendimiento`      | `float` | Si       | objetivo                    |

## Dependencias compartidas

| Modulo                                  | Uso                                                                                      |
| --------------------------------------- | ---------------------------------------------------------------------------------------- |
| `shared/config.py`                      | `CULTIVOS_MVP`, `RENDIMIENTO_RANGOS`, `TRAIN_HASTA`, `VAL_AÑO`, `TEST_DESDE`, `DATA_DIR` |
| `shared/dane_codes.py`                  | `MVP_CODIGOS`                                                                            |
| `shared/normalization.py`               | `normalize_dane_code()`                                                                  |
| `modules/predictive/feature_builder.py` | `build_feature_matrix()` y helpers                                                       |

## Restricciones tecnicas

- No usar `inplace=True` en Pandas.
- No incluir columnas prohibidas: `produccion`, `area_cosechada`, `rendimiento`.
- Guardar con `df.to_parquet(..., index=False, engine='pyarrow')`.
- Usar `pd.to_numeric(col, errors='coerce')` para columnas numericas.
- No usar datos del año t ni futuros para rezagos o percentiles.
- No modificar funciones D5 existentes.

## Produce para

- **M2** — XGBoost Regressor por cultivo
- **M3** — Clasificacion de riesgo
