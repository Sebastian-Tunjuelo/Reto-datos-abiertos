# M2 - XGBoost Regressor por cultivo

## Resumen

Entrena tres modelos XGBoost de regresion (Café, Cacao, Maíz) para predecir
`target_rendimiento` (t/ha) usando `feature_matrix.parquet` (M1). El split
temporal es estricto y se guardan modelos, metadatos y metricas.

## Contexto del dominio

El rendimiento agricola varia por cultivo y region, por eso el entrenamiento es
por cultivo. El modelo se consume en prediccion y explicabilidad (SHAP). No se
permite fuga de informacion: ninguna columna del año objetivo entra como
feature y la particion es por año.

## Subtareas

| ID   | Archivo                                                                | Que hace                                | Depende de | Estado     |
| ---- | ---------------------------------------------------------------------- | --------------------------------------- | ---------- | ---------- |
| M2.1 | [M2.1_carga_validacion_features.md](M2.1_carga_validacion_features.md) | Carga y valida `feature_matrix.parquet` | M1         | Completado |
| M2.2 | [M2.2_entrenamiento_por_cultivo.md](M2.2_entrenamiento_por_cultivo.md) | Entrena XGBoost por cultivo             | M2.1       | Completado |
| M2.3 | [M2.3_evaluacion_y_guardado.md](M2.3_evaluacion_y_guardado.md)         | Calcula metricas y guarda artefactos    | M2.2       | Completado |
| M2.4 | [M2.4_validacion.md](M2.4_validacion.md)                               | Script de validacion independiente      | M2.3       | Completado |

## Outputs finales

| Archivo                                                 | Descripcion                              |
| ------------------------------------------------------- | ---------------------------------------- |
| `models/xgb_regressor_cafe.pkl`                         | Modelo XGBoost para Café                 |
| `models/xgb_regressor_cacao.pkl`                        | Modelo XGBoost para Cacao                |
| `models/xgb_regressor_maiz.pkl`                         | Modelo XGBoost para Maíz                 |
| `models/xgb_regressor_cafe_meta.json`                   | Metadatos de features y split (Café)     |
| `models/xgb_regressor_cacao_meta.json`                  | Metadatos de features y split (Cacao)    |
| `models/xgb_regressor_maiz_meta.json`                   | Metadatos de features y split (Maíz)     |
| `models/m2_regression_metrics.json`                     | Metricas MAE/RMSE/R2 por cultivo y split |
| `specs/M2_XGBoost_Regressor_por_cultivo/validate_m2.py` | Script de validacion                     |

## Inputs

| Archivo                       | Origen | Columnas minimas                                                                             |
| ----------------------------- | ------ | -------------------------------------------------------------------------------------------- |
| `data/feature_matrix.parquet` | M1     | `codigo_dane, cultivo, año, target_rendimiento, señal_riesgo_economico` + features numericas |

## Split temporal

- Train: `año <= TRAIN_HASTA`
- Validacion: `año == VAL_AÑO`
- Test: `año >= TEST_DESDE`

## Esquema de metricas (models/m2_regression_metrics.json)

| Campo            | Tipo    | Descripcion                     |
| ---------------- | ------- | ------------------------------- |
| `cultivo`        | `str`   | `Café` \| `Cacao` \| `Maíz`     |
| `split`          | `str`   | `train` \| `val` \| `test`      |
| `n`              | `int`   | Numero de filas del split       |
| `mae`            | `float` | Error absoluto medio            |
| `rmse`           | `float` | Raiz del error cuadratico medio |
| `r2`             | `float` | Coeficiente de determinacion    |
| `best_iteration` | `int`   | Iteracion optima del booster    |

## Dependencias compartidas

| Modulo                                  | Uso                                                                                        |
| --------------------------------------- | ------------------------------------------------------------------------------------------ |
| `shared/config.py`                      | `CULTIVOS_MVP`, `RENDIMIENTO_RANGOS`, `TRAIN_HASTA`, `VAL_AÑO`, `TEST_DESDE`, `MODELS_DIR` |
| `shared/normalization.py`               | `normalize_dane_code()`                                                                    |
| `modules/predictive/feature_builder.py` | Output `feature_matrix.parquet` (M1)                                                       |

## Restricciones tecnicas

- Entrenar **un modelo por cultivo**; no entrenar un modelo global.
- Split temporal estricto, sin `train_test_split` aleatorio.
- No usar `target_rendimiento` ni identificadores (`codigo_dane`, `municipio`, `departamento`) como features.
- Mapear `señal_riesgo_economico` a numerico con orden `bajo < medio < alto`.
- No imputar `target_rendimiento`; filas sin target se descartan.
- Mantener NaN en features (XGBoost soporta NaN).
- Guardar modelos con `joblib.dump`.

## Produce para

- **M4** - SHAP y explicabilidad
- **A1** - endpoint `POST /predecir` (capa predictiva)
