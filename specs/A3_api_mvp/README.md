# A3 - API de escenarios, chat y reportes del MVP

## Resumen

Expone la capa FastAPI que convierte la predicción y la explicabilidad en herramientas de decisión: simulación de escenarios, respuesta conversacional y reportes descargables.

## Contexto del dominio

Después de A1 y A2, la interfaz del MVP necesita tres capacidades adicionales:

- comparar la línea base contra shocks deterministas
- preguntar en lenguaje natural usando contexto del modelo
- generar un reporte compartible en PDF o texto

Este bloque orquesta artefactos ya producidos por M1 a M5. No entrena modelos ni descarga datos crudos en runtime.

## Subtareas

| ID   | Archivo                                  | Qué hace                             | Depende de                                                                                                                     | Estado      |
| ---- | ---------------------------------------- | ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------ | ----------- |
| A3.1 | [A3.1_escenario.md](A3.1_escenario.md)   | `POST /escenario`                    | M1, M2, M3, M5, `data/feature_matrix.parquet`, `models/xgb_regressor_*.pkl`, `models/xgb_classifier_*.pkl`, shared/\*          | ✅ Completo |
| A3.2 | [A3.2_chat.md](A3.2_chat.md)             | `POST /chat`                         | `docs/dominio/glosario_agricola.md`, `data/predicciones_con_explicacion.parquet`, M4, `modules/conversational/*`, shared/\*    | ✅ Completo |
| A3.3 | [A3.3_reporte.md](A3.3_reporte.md)       | `GET /reporte/{municipio}/{cultivo}` | A2, A3.1, A3.2, `data/predicciones_con_explicacion.parquet`, `modules/conversational/*`, `modules/explainability/*`, shared/\* | ✅ Completo |
| A3.4 | [A3.4_validacion.md](A3.4_validacion.md) | Validación del contrato A3           | A3.1, A3.2, A3.3, artefactos M4/M5, `data/predicciones_con_explicacion.parquet`                                                | ✅ Completo |

> A3.1 puede arrancar en paralelo con A3.2 y A3.3 si ya existe la capa común de normalización y orquestación. A3.4 valida el bloque completo cuando los tres contratos estén expuestos.

## Outputs finales

| Contrato                             | Descripción                                                          |
| ------------------------------------ | -------------------------------------------------------------------- |
| `POST /escenario`                    | Devuelve línea base + escenarios con deltas y trazabilidad           |
| `POST /chat`                         | Devuelve respuesta generada con contexto recuperado y fuentes usadas |
| `GET /reporte/{municipio}/{cultivo}` | Devuelve reporte PDF o texto listo para compartir                    |
| `specs/A3_api_mvp/validate_a3.py`    | Script de validación independiente del contrato A3                   |

## Dependencias compartidas

| Módulo / artefacto                            | Uso                                                            |
| --------------------------------------------- | -------------------------------------------------------------- |
| `shared/config.py`                            | Rutas, umbrales y constantes del MVP                           |
| `shared/dane_codes.py`                        | Resolución canónica de municipios                              |
| `shared/normalization.py`                     | Normalización de municipio, cultivo y códigos                  |
| `data/feature_matrix.parquet`                 | Base histórica para construir la fila base de escenarios       |
| `data/predicciones_con_explicacion.parquet`   | Contexto persistido de predicción + SHAP + narrativa           |
| `data/eva_completa.parquet`                   | Histórico EVA para el reporte                                  |
| `data/clima_agregado.parquet`                 | Serie climática agregada para el reporte                       |
| `modules/predictive/scenarios.py`             | Motor determinista de escenarios                               |
| `modules/explainability/narrative_builder.py` | Narrativas explicativas persistidas                            |
| `modules/explainability/feature_extractor.py` | Top features y trazabilidad SHAP                               |
| `modules/conversational/rag.py`               | Recuperación semántica para chat                               |
| `modules/conversational/prompts.py`           | Plantillas de prompt y guardrails                              |
| `modules/conversational/reports.py`           | Generación de reporte PDF/texto                                |
| `docs/dominio/glosario_agricola.md`           | Vocabulario controlado para lenguaje campesino e institucional |

## Restricciones técnicas comunes

- Operaciones read-only sobre los datos fuente; no modificar Parquet de origen ni la base de datos.
- Normalizar siempre municipio y cultivo antes de resolver cualquier contexto.
- No reentrenar modelos ni recalcular features históricas en runtime.
- No usar pronóstico climático real; A3.1 solo simula shocks deterministas sobre la fila base.
- No permitir respuestas del chat sin trazabilidad mínima de fuentes o contexto recuperado.
- El reporte debe apoyarse en predicción, SHAP e históricos ya disponibles; no debe inventar valores.
- No usar `sodapy`; cualquier lectura parte de artefactos ya generados por los pipelines.

## Produce para

- F2
- F4
