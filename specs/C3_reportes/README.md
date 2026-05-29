# C3 — Generador de reportes PDF por municipio

## Resumen

C3 formaliza y amplía `modules/conversational/reports.py` para producir reportes PDF de calidad institucional.
Integra el prompt UMATA de C2.2 con el LLM (Gemini) para generar contenido narrativo enriquecido,
mejora el diseño visual del PDF con logo, semáforo de color y tabla de datos, y agrega un script
de validación end-to-end.

El endpoint `GET /reporte/{municipio}/{cultivo}` ya funciona (A3.3 completo). C3 no cambia su firma
ni su comportamiento externo: mejora la calidad del contenido y del PDF generado.

---

## Contexto del dominio

Los reportes son el artefacto principal que UMATAs y extensionistas comparten con productores y
secretarías de agricultura. Deben ser legibles fuera de la plataforma (PDF imprimible, enviable por
WhatsApp) y transmitir de forma clara el nivel de riesgo, los factores determinantes y la
recomendación accionable.

A3.3 generó un PDF funcional con texto estático. C3 eleva ese PDF a un documento institucional
con contenido generado por LLM, identidad visual de SiembraSegura IA y elementos visuales
(semáforo, tabla de datos) que facilitan la lectura rápida.

---

## Tabla de subtareas

| ID   | Archivo          | Qué hace                                                                 | Depende de       | Estado      |
| ---- | ---------------- | ------------------------------------------------------------------------ | ---------------- | ----------- |
| C3.1 | `C3.1_llm.md`    | Agrega `build_reporte_umata_llm()` que usa C2.2 + LLM para el contenido | C1 (rag.py), C2.2 (prompts.py), chat_engine.py | ✅ Completo |
| C3.2 | `C3.2_visual.md` | Mejora `render_pdf()` con logo, semáforo de color y tabla de datos       | C3.1             | ✅ Completo |
| C3.3 | `C3.3_validacion.md` | Script `validate_c3.py` que valida C3.1 y C3.2 end-to-end           | C3.1, C3.2       | ✅ Completo |

---

## Outputs finales

| Artefacto                                    | Descripción                                                                 |
| -------------------------------------------- | --------------------------------------------------------------------------- |
| `modules/conversational/reports.py` (modificado) | Agrega `build_reporte_umata_llm()` y mejora `render_pdf()`              |
| `specs/C3_reportes/validate_c3.py`           | Script de validación end-to-end para C3.1 y C3.2                           |

---

## Contrato global — funciones públicas de `reports.py`

```python
# Existentes — firma sin cambios (compatibilidad A3.3)
build_reporte(codigo_dane, municipio, departamento, cultivo) -> dict
render_pdf(reporte: dict) -> bytes

# Nueva — C3.1
build_reporte_umata_llm(
    codigo_dane: str,
    municipio: str,
    departamento: str,
    cultivo: str,
    tono: str = "institucional",
) -> dict
# Retorna el mismo esquema que build_reporte() pero con contenido_texto
# generado por LLM usando build_prompt_reporte_umata() de C2.2.
# render_pdf() acepta el dict de ambas funciones sin cambios.
```

---

## Dependencias compartidas

| Módulo / archivo                                  | Uso en C3                                                    |
| ------------------------------------------------- | ------------------------------------------------------------ |
| `modules/conversational/rag.py`                   | `recuperar_contexto()` → `ContextoRecuperado`                |
| `modules/conversational/prompts.py`               | `build_prompt_reporte_umata()` (C2.2)                        |
| `modules/conversational/chat_engine.py`           | `get_chat_engine()` → llamada al LLM (Gemini)                |
| `shared/config.py`                                | `DATA_DIR`, `LLM_API_KEY`, `LLM_MODEL`                       |
| `shared/dane_codes.py`                            | `get_codigo()`, `get_nombre()`, `DANE_TO_DEPT`               |
| `shared/normalization.py`                         | `normalize_cultivo()`, `normalize_dane_code()`               |
| `reportlab`                                       | Generación del PDF (ya instalado)                            |

---

## Restricciones técnicas comunes

- No usar `inplace=True` en pandas.
- No hardcodear códigos DANE — usar `shared/dane_codes.py`.
- Logging con `logger = logging.getLogger(__name__)`.
- No cambiar la firma pública de `build_reporte()` ni `render_pdf()`.
- No introducir dependencias nuevas fuera de las ya instaladas en el proyecto.
- El LLM es opcional: si falla o no está configurado, `build_reporte_umata_llm()` debe
  hacer fallback a `build_reporte()` y loggear un warning.

---

## Produce para

- `orchestrator/main.py` → `GET /reporte/{municipio}/{cultivo}` (sin cambios de contrato)
- F4 — pantalla de asistente con botón "Generar reporte"
