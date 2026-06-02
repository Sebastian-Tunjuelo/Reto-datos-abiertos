# M5 - Simulación de escenarios de rendimiento y riesgo

## Resumen

M5 define el motor determinista que toma una fila base de features y simula escenarios contrafactuales para responder preguntas del tipo: qué pasa si el año es más seco, más lluvioso o si sube el costo de los fertilizantes. El módulo reutiliza los modelos entrenados de M2 y M3 para comparar línea base vs. shock, sin reentrenar nada.

## Contexto del dominio

La pregunta de negocio no es solo cuál es el rendimiento esperado, sino cómo cambia ese rendimiento si varían las condiciones más sensibles para el productor. Por eso M5 no debe presentarse como pronóstico climático: es una simulación sobre features conocidas y unifica el resultado en una salida clara para el endpoint `POST /escenario`.

## Subtareas

| ID   | Archivo                                                  | Qué hace                                                                                    | Depende de | Estado        |
| ---- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ---------- | ------------- |
| M5.1 | [M5.1_funcion_escenarios.md](M5.1_funcion_escenarios.md) | Define el catálogo de escenarios, aplica shocks y genera la comparación base vs. escenarios | M1, M2, M3 | ✅ Completado |

> M5.1 concentra la lógica funcional y define la validación (incluye `validate_m5.py`).

## Outputs finales

| Archivo                                         | Descripción                                                   |
| ----------------------------------------------- | ------------------------------------------------------------- |
| `modules/predictive/scenarios.py`               | Motor de simulación de escenarios y comparador base vs. shock |
| `data/escenarios_simulados.parquet`             | Caché opcional de escenarios simulados para pruebas o demo    |
| `specs/M5_simulacion_escenarios/validate_m5.py` | Script de validación independiente                            |

## Inputs

| Archivo o contrato                  | Origen           | Descripción                                                                                |
| ----------------------------------- | ---------------- | ------------------------------------------------------------------------------------------ |
| Fila base de features               | M1 / orquestador | Registro alineado con el esquema de inferencia, sin usar `target_rendimiento` como entrada |
| `models/xgb_regressor_*.pkl`        | M2               | Modelos de rendimiento por cultivo                                                         |
| `models/xgb_regressor_*_meta.json`  | M2               | Orden exacto de las features del regresor                                                  |
| `models/xgb_classifier_*.pkl`       | M3               | Clasificadores de riesgo por cultivo                                                       |
| `models/xgb_classifier_*_meta.json` | M3               | Orden exacto de las features del clasificador                                              |

## Contrato global de escenarios

| Escenario       | Shock principal       | Regla base                                                |
| --------------- | --------------------- | --------------------------------------------------------- |
| `base`          | Sin shock             | Copia exacta de la fila base                              |
| `seco`          | -30% de precipitación | Ajuste determinista sobre variables climáticas permitidas |
| `lluvioso`      | +30% de precipitación | Ajuste determinista sobre variables climáticas permitidas |
| `fertilizantes` | +20% en fertilizantes | Ajuste determinista sobre variables económicas permitidas |

El contrato debe ser explícito sobre qué columnas se modifican y cuáles se conservan. Si una variable derivada no puede recalcularse con información local, se deja documentado como valor base preservado y se emite warning.

## Dependencias compartidas

| Módulo                                  | Uso                                               |
| --------------------------------------- | ------------------------------------------------- |
| `shared/config.py`                      | `MODELS_DIR`, `CULTIVOS_MVP` y constantes de ruta |
| `shared/normalization.py`               | Normalización de códigos DANE y texto de entrada  |
| `modules/predictive/feature_builder.py` | Esquema de features usado por el modelo           |

## Restricciones técnicas

- No reentrenar modelos.
- No introducir aleatoriedad en la simulación.
- No usar `produccion` ni `area_cosechada` del mismo año como features.
- No modificar la fila base; cada escenario debe operar sobre una copia.
- Conservar el orden exacto de las features definido por los metadatos de M2/M3.
- Rechazar escenarios fuera del catálogo o con campos no permitidos.
- Mantener trazabilidad de qué columnas fueron perturbadas en cada escenario.

## Produce para

- **A3** - endpoint `POST /escenario`
- **Frontend** - comparación visual de escenarios en la ficha municipal
