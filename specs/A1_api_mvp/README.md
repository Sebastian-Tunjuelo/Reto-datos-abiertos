# A1 - API base del MVP

## Resumen

Expone el contrato mínimo de la capa FastAPI del MVP: catálogo de municipios, cultivos disponibles por municipio y predicción de rendimiento/riesgo.

## Contexto del dominio

La interfaz del MVP necesita tres capacidades de solo lectura y una capacidad de predicción:

- listar los municipios priorizados del proyecto
- resolver los cultivos disponibles para un municipio dado
- pedir una predicción para una combinación municipio + cultivo + año

Este bloque no incluye SHAP, escenarios, chat, persistencia ni entrenamiento.

## Subtareas

| ID   | Archivo                                                          | Qué hace                    | Depende de                            | Estado        |
| ---- | ---------------------------------------------------------------- | --------------------------- | ------------------------------------- | ------------- |
| A1.1 | [A1.1_catalogo_municipios.md](A1.1_catalogo_municipios.md)       | `GET /municipios`           | `shared/dane_codes.py`                | ✅ Completado |
| A1.2 | [A1.2_cultivos_por_municipio.md](A1.2_cultivos_por_municipio.md) | `GET /cultivos/{municipio}` | A1.1 + `data/feature_matrix.parquet`  | ✅ Completado |
| A1.3 | [A1.3_predecir.md](A1.3_predecir.md)                             | `POST /predecir`            | A1.1 + A1.2 + M2 + M3                 | ✅ Completado |
| A1.4 | [A1.4_validacion.md](A1.4_validacion.md)                         | Validación del contrato     | A1.1 + A1.2 + A1.3 + artefactos M2/M3 | ✅ Completado |

> A1.1 y A1.2 pueden implementarse en paralelo. A1.3 depende del contrato estable de ambas. A1.4 valida el API completo una vez exista la capa funcional.

## Outputs finales

| Contrato                          | Descripción                                                           |
| --------------------------------- | --------------------------------------------------------------------- |
| `GET /municipios`                 | Devuelve los 15 municipios del MVP en orden canónico                  |
| `GET /cultivos/{municipio}`       | Devuelve los cultivos disponibles para el municipio solicitado        |
| `POST /predecir`                  | Devuelve rendimiento esperado, probabilidad de riesgo alto y semáforo |
| `specs/A1_api_mvp/validate_a1.py` | Script de validación independiente del contrato A1                    |

## Dependencias compartidas

| Módulo                              | Uso                                                                                      |
| ----------------------------------- | ---------------------------------------------------------------------------------------- |
| `shared/config.py`                  | `CULTIVOS_MVP`, `UMBRAL_RIESGO_MEDIO`, `UMBRAL_RIESGO_ALTO`, `DATA_DIR`, `MODELS_DIR`    |
| `shared/dane_codes.py`              | `MVP_CODIGOS`, `DANE_TO_NAME`, `DANE_TO_DEPT`, `get_codigo()`, `get_nombre()`            |
| `shared/normalization.py`           | `normalize_dane_code()`, `normalize_cultivo()`, `normalize_title_case()`                 |
| `data/feature_matrix.parquet`       | Base histórica para resolver cultivos disponibles y seleccionar la última fila histórica |
| `models/xgb_regressor_*.pkl`        | Modelo de rendimiento por cultivo                                                        |
| `models/xgb_regressor_*_meta.json`  | Orden y contrato de features del regressor                                               |
| `models/xgb_classifier_*.pkl`       | Modelo de riesgo por cultivo                                                             |
| `models/xgb_classifier_*_meta.json` | Orden y contrato de features del clasificador                                            |

## Restricciones técnicas comunes

- Operaciones read-only: la API no escribe Parquet ni modifica PostgreSQL.
- Mantener el orden canónico de municipios con `MVP_CODIGOS` y de cultivos con `CULTIVOS_MVP`.
- Normalizar siempre municipio y cultivo antes de buscar artefactos o datos.
- No usar `sodapy`; cualquier lectura de datos debe partir de los artefactos ya generados por los pipelines.
- No mezclar este contrato con SHAP, escenarios o chat.
- `prob_riesgo_alto` debe salir en rango `[0, 1]` y el semáforo debe derivarse de `shared/config.py`.

## Produce para

- F1
- F2
- F3
