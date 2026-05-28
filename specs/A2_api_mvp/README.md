# A2 - API de series históricas del MVP

## Resumen

Expone el contrato read-only de la API para consultar la serie histórica de rendimiento EVA por municipio + cultivo y la serie climática agregada por municipio. Este bloque alimenta la ficha municipal, el comparador y el contexto explicativo de la plataforma.

## Contexto del dominio

La interfaz del MVP necesita histórico antes de mostrar gráficos o recomendaciones. Este bloque permite:

- visualizar la evolución del rendimiento por municipio y cultivo
- visualizar el clima agregado anual del municipio
- alimentar componentes de la ficha municipal y del comparador

No incluye predicción, SHAP, escenarios, chat ni persistencia.

## Subtareas

| ID   | Archivo                                                        | Qué hace                                 | Depende de                                                                                                                              | Estado      |
| ---- | -------------------------------------------------------------- | ---------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| A2.1 | [A2.1_rendimiento_historico.md](A2.1_rendimiento_historico.md) | `GET /rendimiento/{municipio}/{cultivo}` | `modules/agricultural/ingestion.py`, `data/eva_completa.parquet`, `shared/config.py`, `shared/dane_codes.py`, `shared/normalization.py` | 📝 Borrador |
| A2.2 | [A2.2_clima_municipio.md](A2.2_clima_municipio.md)             | `GET /clima/{municipio}`                 | `modules/climate/ingestion.py`, `data/clima_agregado.parquet`, `shared/config.py`, `shared/dane_codes.py`, `shared/normalization.py`    | 📝 Borrador |
| A2.3 | [A2.3_validacion.md](A2.3_validacion.md)                       | Validación del contrato A2               | A2.1 + A2.2 + artefactos EVA/IDEAM                                                                                                      | 📝 Borrador |

> A2.1 y A2.2 pueden implementarse en paralelo. A2.3 valida la API completa una vez exista la capa funcional.

## Outputs finales

| Contrato                                 | Descripción                                                                  |
| ---------------------------------------- | ---------------------------------------------------------------------------- |
| `GET /rendimiento/{municipio}/{cultivo}` | Devuelve la serie anual de rendimiento y área sembrada del municipio/cultivo |
| `GET /clima/{municipio}`                 | Devuelve la serie climática agregada anual del municipio                     |
| `specs/A2_api_mvp/validate_a2.py`        | Script de validación independiente del contrato A2                           |

## Dependencias compartidas

| Módulo / artefacto                  | Uso                                                                      |
| ----------------------------------- | ------------------------------------------------------------------------ |
| `shared/config.py`                  | `DATA_DIR`, `CULTIVOS_MVP`, `MVP_CODIGOS`                                |
| `shared/dane_codes.py`              | `DANE_TO_NAME`, `DANE_TO_DEPT`, `get_codigo()`, `get_nombre()`           |
| `shared/normalization.py`           | `normalize_dane_code()`, `normalize_cultivo()`, `normalize_title_case()` |
| `modules/agricultural/ingestion.py` | `load_eva_completa()`                                                    |
| `modules/climate/ingestion.py`      | `load_clima_agregado()`                                                  |
| `data/eva_completa.parquet`         | Histórico EVA limpio y unificado                                         |
| `data/clima_agregado.parquet`       | Serie climática anual agregada                                           |

## Restricciones técnicas comunes

- Operaciones read-only: la API no escribe Parquet ni modifica PostgreSQL.
- Normalizar siempre municipio y cultivo antes de buscar artefactos o datos.
- Usar `codigo_dane` como llave canónica de resolución.
- No usar `sodapy`; cualquier lectura parte de los artefactos ya generados por los pipelines.
- No mezclar este contrato con predicción, SHAP, escenarios o chat.
- A2.1 debe usar una agregación anual consistente con D5.2 cuando existan múltiples observaciones en el mismo año.
- A2.2 debe exponer el clima ya agregado en `clima_agregado.parquet`; no debe recomputar anomalías ni descargar IDEAM crudo.

## Produce para

- F2
- F3
