# M4 - Explicabilidad (SHAP) y Narrativas

## Resumen

Este módulo toma la matriz de features del proyecto y los modelos XGBoost, calcula la contribución de cada variable a través de los valores SHAP (SHapley Additive exPlanations), extrae las top N features más influyentes por predicción y las traduce a un lenguaje humano claro mediante plantillas de narrativa. El resultado alimenta la tabla final `data/predicciones_con_explicacion.parquet`.

## Contexto del dominio

La adopción de herramientas de IA en el sector agrícola fracasa si los usuarios no confían en la herramienta y no la entienden. Proveer explicabilidad técnica cruda no basta. Por ello, M4 no solo genera valores SHAP, sino que mapea los nombres matemáticos de las features (ej. `temp_media_anomalia_zscore`) a descripciones comprensibles (ej. "temperatura más alta de lo normal") y construye una narrativa útil para que los agentes territoriales (UMATAs) y campesinos sepan exactamente por qué el modelo asignó cierto nivel de riesgo.

## Subtareas

| ID   | Archivo                                      | Qué hace                                    | Depende de | Estado        |
| ---- | -------------------------------------------- | ------------------------------------------- | ---------- | ------------- |
| M4.1 | [M4.1_calculo_shap.md](M4.1_calculo_shap.md) | Calcula valores SHAP y genera explainers    | M2, M3     | 🟢 Completado |
| M4.2 | [M4.2_top_features.md](M4.2_top_features.md) | Mapea columnas a descripciones y saca top N | M4.1       | 🟢 Completado |
| M4.3 | [M4.3_narrativas.md](M4.3_narrativas.md)     | Aplica plantillas para generar narrativa    | M4.2       | 🟢 Completado |
| M4.4 | [M4.4_validacion.md](M4.4_validacion.md)     | Script de validación independiente          | M4.3       | 🟢 Completado |

## Outputs finales

| Archivo                                       | Descripción                                                                      |
| --------------------------------------------- | -------------------------------------------------------------------------------- |
| `models/shap_explainer_cafe.pkl`              | Objeto TreeExplainer guardado para Café                                          |
| `models/shap_explainer_cacao.pkl`             | Objeto TreeExplainer guardado para Cacao                                         |
| `models/shap_explainer_maiz.pkl`              | Objeto TreeExplainer guardado para Maíz                                          |
| `data/predicciones_con_explicacion.parquet`   | Tabla maestra con las predicciones, top features y textos de narrativa generados |
| `specs/M4_Explicabilidad_SHAP/validate_m4.py` | Script de validación independiente                                               |

## Inputs

| Archivo                             | Origen | Descripción                                                                  |
| ----------------------------------- | ------ | ---------------------------------------------------------------------------- |
| `data/feature_matrix.parquet`       | M1     | Dataset con las features numéricas para reconstruir la muestra de validación |
| `models/xgb_classifier_*.pkl`       | M3     | Modelos que serán explicados                                                 |
| `models/xgb_classifier_*_meta.json` | M3     | Orden exacto de las features utilizadas en cada modelo                       |
