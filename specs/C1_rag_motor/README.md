# C1 — Motor RAG: indexación y recuperación de predicciones + SHAP

## Resumen

Construye el motor RAG (Retrieval-Augmented Generation) del módulo conversacional de SiembraSegura IA.
Indexa el corpus de predicciones con explicación SHAP como documentos recuperables y expone una función
de recuperación por municipio y cultivo que alimenta al `ChatEngine` con contexto grounded.

## Contexto del dominio

El módulo conversacional (`modules/conversational/`) ya tiene implementados `rag.py`, `prompts.py`,
`chat_engine.py` y `reports.py` (A3.2 y A3.3 completos). Sin embargo, el `rag.py` actual realiza
recuperación ad-hoc sin un índice estructurado: carga el Parquet completo en cada llamada, filtra
por igualdad exacta y no tiene ranking ni scoring de relevancia.

La tarea C1 formaliza ese motor: define el corpus, construye el índice en memoria, implementa la
función de recuperación con scoring y valida el comportamiento end-to-end.

## Subtareas

| ID   | Archivo                                    | Qué hace                                                                 | Depende de                                                                                  | Estado      |
| ---- | ------------------------------------------ | ------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------- | ----------- |
| C1.1 | [C1.1_indexacion_corpus.md](C1.1_indexacion_corpus.md) | Carga `predicciones_con_explicacion.parquet` y construye el índice RAG en memoria | `data/predicciones_con_explicacion.parquet`, `shared/dane_codes.py`, `shared/normalization.py` | 🔲 Pendiente |
| C1.2 | [C1.2_funcion_recuperacion.md](C1.2_funcion_recuperacion.md) | Función de recuperación con scoring por municipio/cultivo/año            | C1.1, `shared/dane_codes.py`, `shared/normalization.py`                                     | 🔲 Pendiente |
| C1.3 | [C1.3_validacion.md](C1.3_validacion.md)   | Valida el motor RAG end-to-end: cobertura, ranking y contratos           | C1.1, C1.2, `data/predicciones_con_explicacion.parquet`                                     | 🔲 Pendiente |

> C1.1 debe completarse antes de C1.2. C1.3 valida el bloque completo.

## Outputs finales

| Artefacto                                          | Descripción                                                                                  |
| -------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| `modules/conversational/rag.py` (refactorizado)    | Motor RAG con índice en memoria, función `build_rag_index()` y `retrieve_context()` mejorada |
| `specs/C1_rag_motor/validate_c1.py`                | Script de validación independiente del motor RAG                                             |

## Dependencias compartidas

| Módulo / artefacto                                  | Uso                                                                    |
| --------------------------------------------------- | ---------------------------------------------------------------------- |
| `data/predicciones_con_explicacion.parquet`         | Corpus principal: 395 registros con predicciones, SHAP y narrativas    |
| `shared/config.py`                                  | `DATA_DIR`, `CULTIVOS_MVP`, `MVP_CODIGOS`                              |
| `shared/dane_codes.py`                              | `get_codigo()`, `get_nombre()`, `MVP_CODIGOS`, `DANE_TO_NAME`          |
| `shared/normalization.py`                           | `normalize_cultivo()`, `normalize_dane_code()`, `normalize_name()`     |
| `modules/conversational/chat_engine.py`             | Consumidor del motor RAG — no modificar su interfaz pública            |

## Restricciones técnicas comunes

- No usar `inplace=True` en pandas.
- No hardcodear códigos DANE — usar `shared/dane_codes.py`.
- Guardar Parquet con `df.to_parquet(path, index=False, engine='pyarrow')` si aplica.
- Logging con `logger = logging.getLogger(__name__)`.
- El índice RAG debe construirse en memoria al inicio; no requiere base de datos vectorial externa.
- La función `recuperar_contexto()` existente debe mantener su firma pública para no romper `chat_engine.py`.
- No reentrenar modelos ni recalcular features en runtime.
- Operaciones read-only sobre `predicciones_con_explicacion.parquet`.

## Produce para

- `modules/conversational/chat_engine.py` (consumidor directo)
- C2 (prompts que usan el contexto recuperado)
- F4 (chat interface del frontend)
