# C2 — Prompts: plantillas conversacionales para lenguaje campesino, reporte UMATA y comparación de cultivos

## Resumen

Formaliza y amplía el módulo de plantillas de prompt de SiembraSegura IA.
El `prompts.py` actual cubre el caso básico de A3.2 (tono campesino/institucional para chat libre).
C2 lo refactoriza para cubrir tres casos de uso diferenciados con contratos explícitos, y agrega
un script de validación que verifica renderizado, cobertura de campos y comportamiento ante
entradas incompletas.

## Contexto del dominio

El módulo conversacional (`modules/conversational/`) tiene:

- `rag.py` — motor RAG (C1): expone `recuperar_contexto()` que retorna `ContextoRecuperado`.
- `prompts.py` — implementación inicial de A3.2: `build_system_prompt()`, `build_user_prompt()`,
  `build_contexto_recuperado()`, `format_feature_for_prompt()`.
- `chat_engine.py` — usa Google Gemini `gemini-2.0-flash`, consume `ContextoRecuperado` y llama
  a `prompts.py` con las firmas actuales.
- `reports.py` — generador de reportes (A3.3).

C2 amplía `prompts.py` sin romper las firmas que ya consume `chat_engine.py`.
Los tres casos de uso nuevos se implementan como funciones adicionales con contratos propios.

## Subtareas

| ID   | Archivo                                                                          | Qué hace                                                                                                  | Depende de                                                                                  | Estado       |
| ---- | -------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- | ------------ |
| C2.1 | [C2.1_prompt_conversacional.md](C2.1_prompt_conversacional.md)                   | Refactoriza y formaliza las plantillas de prompt conversacional (tono campesino e institucional)          | `modules/conversational/rag.py`, `shared/dane_codes.py`                                     | ✅ Completo  |
| C2.2 | [C2.2_prompt_reporte_umata.md](C2.2_prompt_reporte_umata.md)                     | Plantilla de prompt para reporte institucional UMATA (secretaría de agricultura, técnico)                 | C2.1, `modules/conversational/rag.py`                                                       | ✅ Completo  |
| C2.3 | [C2.3_prompt_comparacion_cultivos.md](C2.3_prompt_comparacion_cultivos.md)       | Plantilla de prompt para comparación y ranking de cultivos (café/cacao/maíz) por municipio                | C2.1, `modules/conversational/rag.py`, `shared/config.py`                                   | ✅ Completo  |
| C2.4 | [C2.4_validacion_prompts.md](C2.4_validacion_prompts.md)                         | Valida las tres plantillas: renderizado, cobertura de campos y comportamiento ante entradas incompletas   | C2.1, C2.2, C2.3                                                                            | ✅ Completo  |

> C2.1 debe completarse antes de C2.2 y C2.3. C2.4 valida el bloque completo.

## Outputs finales

| Artefacto                                              | Descripción                                                                                                    |
| ------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| `modules/conversational/prompts.py` (ampliado)         | Módulo con las tres plantillas formalizadas y las funciones auxiliares existentes sin cambios de firma         |
| `specs/C2_prompts/validate_c2.py`                      | Script de validación independiente: renderizado, cobertura y comportamiento ante entradas incompletas          |

## Contrato global de `ContextoRecuperado`

Todas las plantillas reciben un objeto `ContextoRecuperado` con los siguientes campos.
Las plantillas deben tolerar que cualquier campo opcional sea `None`.

```python
class ContextoRecuperado:
    prediccion: Optional[dict]       # {"rendimiento_esperado": float, "etiqueta_riesgo": str, "prob_riesgo_alto": float}
    narrativa: Optional[str]         # narrativa de riesgo generada por M4
    top_features: Optional[list]     # [{"feature": str, "valor": any, "importancia": float}, ...]
    fuentes: list                    # artefactos usados (strings)
    contexto_efectivo: dict          # {"municipio": str, "cultivo": str, "año": int, "escenario": str}
    serie_historica: Optional[list]  # [{"año": int, "rendimiento": float}, ...]
```

> ⚠️ El parquet real usa `rendimiento_t1` y `prediccion_riesgo` en lugar de `rendimiento_esperado`
> y `etiqueta_riesgo`. El RAG ya mapea estos campos en `ContextoRecuperado.prediccion`.
> Las plantillas deben usar los nombres del contrato (`rendimiento_esperado`, `etiqueta_riesgo`),
> no los nombres crudos del parquet.

## Dependencias compartidas

| Módulo / artefacto                          | Uso                                                                                  |
| ------------------------------------------- | ------------------------------------------------------------------------------------ |
| `modules/conversational/rag.py`             | Fuente de `ContextoRecuperado` — no modificar su interfaz pública                   |
| `modules/conversational/chat_engine.py`     | Consumidor de `prompts.py` — no romper firmas existentes                             |
| `shared/config.py`                          | `CULTIVOS_MVP` para la plantilla de comparación                                      |
| `shared/dane_codes.py`                      | `get_nombre()`, `DANE_TO_DEPT` para encabezados institucionales                      |

## Restricciones técnicas comunes

- No hardcodear códigos DANE — usar `shared/dane_codes.py`.
- Logging con `logger = logging.getLogger(__name__)`.
- Las plantillas de prompt son funciones Python puras en `modules/conversational/prompts.py`.
- No cambiar la firma pública de `build_system_prompt()`, `build_user_prompt()`,
  `build_contexto_recuperado()` ni `format_feature_for_prompt()`.
- Las nuevas funciones deben seguir el mismo patrón de firma: reciben datos tipados y retornan `str`.
- No llamar a Gemini ni a ningún LLM desde `prompts.py` — solo construir strings.
- No leer archivos Parquet desde `prompts.py` — los datos llegan como parámetros.
- Tolerancia a `None`: ninguna función debe lanzar excepción si un campo opcional es `None`.

## Produce para

- `modules/conversational/chat_engine.py` (consumidor directo de las plantillas conversacionales)
- `modules/conversational/reports.py` (consumidor de la plantilla UMATA)
- C3 (generador de reportes PDF que usa la plantilla UMATA)
- F4 (chat interface que usa las tres plantillas según el modo de la UI)
