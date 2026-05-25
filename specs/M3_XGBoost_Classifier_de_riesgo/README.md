# M3 - XGBoost Classifier de riesgo

## Resumen

Entrena tres modelos XGBoost de clasificación por cultivo (Café, Cacao y Maíz) para estimar la probabilidad de riesgo alto. El riesgo alto se define como una caída de `target_rendimiento` mayor al 15% frente al promedio histórico del mismo `codigo_dane` y cultivo, calculado solo con años anteriores para evitar fuga temporal. El módulo consume `data/feature_matrix.parquet` y guarda modelos, metadatos y métricas en `models/`.

## Contexto del dominio

Más allá de predecir un valor exacto de rendimiento, la plataforma necesita una señal binaria clara para activar el semáforo de riesgo. Ese semáforo debe ser interpretable, reproducible y estable por cultivo, porque alimenta tanto la interfaz de usuario como la capa de explicabilidad posterior.

## Subtareas

| ID   | Archivo                                                                  | Qué hace                               | Depende de | Estado       |
| ---- | ------------------------------------------------------------------------ | -------------------------------------- | ---------- | ------------ |
| M3.1 | [M3.1_construccion_target.md](M3.1_construccion_target.md)               | Construye la variable `target_riesgo`  | M1         | ⏳ Pendiente |
| M3.2 | [M3.2_entrenamiento_clasificador.md](M3.2_entrenamiento_clasificador.md) | Entrena XGBoost Classifier por cultivo | M3.1       | ⏳ Pendiente |
| M3.3 | [M3.3_evaluacion_y_guardado.md](M3.3_evaluacion_y_guardado.md)           | Calcula métricas y guarda artefactos   | M3.2       | ⏳ Pendiente |
| M3.4 | [M3.4_validacion.md](M3.4_validacion.md)                                 | Script de validación independiente     | M3.3       | ⏳ Pendiente |

## Outputs finales

| Archivo                                                | Descripción                                          |
| ------------------------------------------------------ | ---------------------------------------------------- |
| `models/xgb_classifier_cafe.pkl`                       | Modelo XGBoost Classifier para Café                  |
| `models/xgb_classifier_cacao.pkl`                      | Modelo XGBoost Classifier para Cacao                 |
| `models/xgb_classifier_maiz.pkl`                       | Modelo XGBoost Classifier para Maíz                  |
| `models/xgb_classifier_cafe_meta.json`                 | Metadatos de features y split (Café)                 |
| `models/xgb_classifier_cacao_meta.json`                | Metadatos de features y split (Cacao)                |
| `models/xgb_classifier_maiz_meta.json`                 | Metadatos de features y split (Maíz)                 |
| `models/m3_classification_metrics.json`                | Métricas F1/AUC/Recall/Precision por cultivo y split |
| `specs/M3_XGBoost_Classifier_de_riesgo/validate_m3.py` | Script de validación                                 |

## Contrato global de riesgo

| Campo                | Tipo    | Regla                                                                          |
| -------------------- | ------- | ------------------------------------------------------------------------------ |
| `target_riesgo`      | `int`   | `1` si `target_rendimiento < promedio_historico * 0.85`, `0` en caso contrario |
| `promedio_historico` | `float` | Helper calculado solo con años anteriores al registro actual                   |
| `umbral_riesgo`      | `float` | `promedio_historico * 0.85`                                                    |

Si una observación no tiene historial suficiente para calcular `promedio_historico`, el valor queda como `NaN` y se excluye del entrenamiento posterior.

## Inputs

| Archivo                       | Origen | Columnas mínimas                                                                                                      |
| ----------------------------- | ------ | --------------------------------------------------------------------------------------------------------------------- |
| `data/feature_matrix.parquet` | M1     | `codigo_dane, municipio, departamento, cultivo, año, target_rendimiento, señal_riesgo_economico` + features numéricas |

## Split temporal

Se aplica la misma regla estricta de validación temporal:

- Train: `año <= TRAIN_HASTA`
- Validación: `año == VAL_AÑO`
- Test: `año >= TEST_DESDE`

## Esquema de métricas (models/m3_classification_metrics.json)

| Campo            | Tipo    | Descripción                                       |
| ---------------- | ------- | ------------------------------------------------- |
| `cultivo`        | `str`   | `Café` \| `Cacao` \| `Maíz`                       |
| `split`          | `str`   | `train` \| `val` \| `test`                        |
| `n`              | `int`   | Número de filas del split                         |
| `accuracy`       | `float` | Exactitud (Accuracy)                              |
| `precision`      | `float` | Precisión de la clase positiva (riesgo alto)      |
| `recall`         | `float` | Exhaustividad (Sensibilidad) de la clase positiva |
| `f1_score`       | `float` | F1-Score ponderado                                |
| `auc_roc`        | `float` | Área bajo la curva ROC                            |
| `best_iteration` | `int`   | Iteración óptima del booster                      |

## Dependencias compartidas

| Módulo                                  | Uso                                                                  |
| --------------------------------------- | -------------------------------------------------------------------- |
| `shared/config.py`                      | `CULTIVOS_MVP`, `TRAIN_HASTA`, `VAL_AÑO`, `TEST_DESDE`, `MODELS_DIR` |
| `shared/normalization.py`               | `normalize_dane_code()`                                              |
| `modules/predictive/feature_builder.py` | Produce `data/feature_matrix.parquet` (M1)                           |

## Restricciones técnicas

- Un modelo clasificador por cultivo.
- No usar `codigo_dane`, `municipio`, `departamento`, `año`, `target_rendimiento`, `target_riesgo`, `promedio_historico` ni `umbral_riesgo` como features.
- Ajustar desbalance de clases con `scale_pos_weight` calculado sobre el split de train.
- Mantener `NaN` nativo para XGBoost cuando una feature no esté disponible.
- Guardar modelos de clasificación con `joblib.dump` en formato `.pkl`.
- Codificar `señal_riesgo_economico` de forma case-insensitive con orden explícito `bajo < medio < alto`.

## Produce para

- **M4** - SHAP, probabilidades del factor de riesgo para el dashboard.
- **A1** - endpoint `POST /predecir` (clasificación de la etiqueta y porcentaje en riesgo alto).
