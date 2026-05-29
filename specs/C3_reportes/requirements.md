# Requirements Document — C3: Generador de reportes PDF por municipio

## Introduction

C3 formaliza y amplía el generador de reportes de SiembraSegura IA (`modules/conversational/reports.py`).
El módulo ya produce reportes PDF funcionales (A3.3 completo). C3 eleva la calidad del contenido
integrando el LLM (Gemini) para generar narrativa institucional vía el prompt UMATA de C2.2,
mejora el diseño visual del PDF con identidad de marca, semáforo de color y tabla de indicadores,
y agrega un script de validación end-to-end.

El endpoint `GET /reporte/{municipio}/{cultivo}` no cambia su contrato externo.

---

## Glossary

- **Report_Generator**: El módulo `modules/conversational/reports.py` responsable de construir y renderizar reportes.
- **LLM**: Modelo de lenguaje grande (Google Gemini `gemini-2.0-flash`) usado para generar contenido narrativo.
- **RAG_Engine**: El módulo `modules/conversational/rag.py` que expone `recuperar_contexto()` y retorna `ContextoRecuperado`.
- **UMATA_Prompt**: La función `build_prompt_reporte_umata()` de `modules/conversational/prompts.py` que construye el prompt institucional para el LLM.
- **Semaforo**: Indicador visual de color (verde/amarillo/rojo) que representa el nivel de riesgo predicho.
- **Tabla_Indicadores**: Tabla estructurada en el PDF con los indicadores clave del reporte (municipio, cultivo, riesgo, rendimiento histórico, factores SHAP).
- **Validator**: El script `specs/C3_reportes/validate_c3.py` que verifica el correcto funcionamiento de C3.
- **ContextoRecuperado**: Objeto retornado por `recuperar_contexto()` con `prediccion`, `narrativa`, `top_features` y `serie_historica`.
- **Fallback**: Comportamiento alternativo de `build_reporte_umata_llm()` cuando el LLM no está disponible: delega a `build_reporte()`.

---

## Requirements

### Requirement 1: Generación de contenido narrativo vía LLM

**User Story:** As a UMATA extensionist, I want the report to contain an LLM-generated narrative analysis, so that the content is contextual and actionable rather than static boilerplate text.

#### Acceptance Criteria

1. THE Report_Generator SHALL expose a function `build_reporte_umata_llm(codigo_dane, municipio, departamento, cultivo, tono)` in `modules/conversational/reports.py`.
2. WHEN `build_reporte_umata_llm()` is called, THE Report_Generator SHALL call `RAG_Engine.recuperar_contexto()` to obtain a `ContextoRecuperado` object before constructing the prompt.
3. WHEN a valid `ContextoRecuperado` is obtained, THE Report_Generator SHALL call `UMATA_Prompt.build_prompt_reporte_umata()` to build the institutional prompt.
4. WHEN the prompt is ready, THE Report_Generator SHALL call the LLM with `max_output_tokens=800` and `temperature=0.4` to generate the narrative content.
5. THE Report_Generator SHALL return a dict with the same keys as `build_reporte()` plus the key `"generado_por_llm": True` when the LLM responds successfully.
6. IF the LLM raises an exception or returns an empty response, THEN THE Report_Generator SHALL log a warning at level WARNING and delegate to `build_reporte()`, returning `"generado_por_llm": False`.
7. IF `ContextoRecuperado.prediccion` is None, THEN THE Report_Generator SHALL raise `ValueError` with a message that includes the municipio and cultivo names.
8. THE Report_Generator SHALL NOT modify the signature of `build_reporte(codigo_dane, municipio, departamento, cultivo)`.
9. THE Report_Generator SHALL NOT modify the signature of `render_pdf(reporte: dict) -> bytes`.

---

### Requirement 2: Compatibilidad del dict de reporte con render_pdf

**User Story:** As a developer, I want both `build_reporte()` and `build_reporte_umata_llm()` to return dicts that `render_pdf()` accepts without modification, so that the PDF rendering pipeline works uniformly.

#### Acceptance Criteria

1. THE Report_Generator SHALL include the keys `"prediccion_riesgo"`, `"serie_historica"` and `"top_features_display"` in the dict returned by `build_reporte()`.
2. THE Report_Generator SHALL include the keys `"prediccion_riesgo"`, `"serie_historica"` and `"top_features_display"` in the dict returned by `build_reporte_umata_llm()`.
3. WHEN `render_pdf()` receives a dict without the key `"prediccion_riesgo"`, THE Report_Generator SHALL generate a valid PDF without the Semaforo block and without raising an exception.
4. THE Report_Generator SHALL accept dicts from both `build_reporte()` and `build_reporte_umata_llm()` in `render_pdf()` without requiring changes to the caller.

---

### Requirement 3: Identidad visual de SiembraSegura IA en el PDF

**User Story:** As a UMATA director, I want the PDF report to display the SiembraSegura IA brand, so that the document is recognizable as an official institutional product.

#### Acceptance Criteria

1. WHEN `render_pdf()` is called, THE Report_Generator SHALL render a header with the text "SiembraSegura IA" in font size 20 and color `#1a5276` on the first page.
2. THE Report_Generator SHALL render a subtitle "Plataforma de predicción agrícola — Colombia" in font size 10 and color `#555555` below the main header.
3. THE Report_Generator SHALL render a footer on each page with the text "Generado por SiembraSegura IA" and the generation date in `YYYY-MM-DD` format.
4. THE Report_Generator SHALL NOT require external image files to render the header; text-based styling is sufficient.

---

### Requirement 4: Semáforo visual de riesgo en el PDF

**User Story:** As a farmer or extensionist, I want to see a color-coded risk indicator in the report, so that I can immediately understand the risk level without reading the full text.

#### Acceptance Criteria

1. WHEN `render_pdf()` receives a dict with `"prediccion_riesgo": "Bajo"`, THE Report_Generator SHALL render a green block (`#27ae60`) with the label "Riesgo: Bajo".
2. WHEN `render_pdf()` receives a dict with `"prediccion_riesgo": "Medio"`, THE Report_Generator SHALL render a yellow block (`#f39c12`) with the label "Riesgo: Medio".
3. WHEN `render_pdf()` receives a dict with `"prediccion_riesgo": "Alto"`, THE Report_Generator SHALL render a red block (`#e74c3c`) with the label "Riesgo: Alto".
4. IF `"prediccion_riesgo"` is absent or has an unrecognized value, THEN THE Report_Generator SHALL omit the Semaforo block and log a WARNING without raising an exception.

---

### Requirement 5: Tabla de indicadores clave en el PDF

**User Story:** As a UMATA extensionist, I want a structured data table in the report, so that I can quickly scan the key indicators without reading all the narrative text.

#### Acceptance Criteria

1. WHEN `render_pdf()` is called with a complete reporte dict, THE Report_Generator SHALL render a Tabla_Indicadores with at least the rows: Municipio, Departamento, Cultivo, Año de referencia, and Nivel de riesgo.
2. WHEN `"serie_historica"` contains at least one entry, THE Report_Generator SHALL add a row "Rendimiento año anterior" with the most recent value in t/ha format.
3. WHEN `"top_features_display"` contains at least one entry, THE Report_Generator SHALL add a row "Factor principal" with the first element of the list.
4. THE Report_Generator SHALL render the Tabla_Indicadores header row with background color `#1a5276` and white text.
5. THE Report_Generator SHALL render alternating row backgrounds: white and `#eaf4fb`.
6. IF `"serie_historica"` or `"top_features_display"` are absent, THEN THE Report_Generator SHALL omit those rows without raising an exception.

---

### Requirement 6: Validación end-to-end de C3

**User Story:** As a developer, I want a validation script that verifies all C3 functions work correctly, so that I can confirm the implementation is complete before marking C3 as done.

#### Acceptance Criteria

1. THE Validator SHALL exist at path `specs/C3_reportes/validate_c3.py` and be executable with `python specs/C3_reportes/validate_c3.py` from the project root.
2. THE Validator SHALL expose a function `run_validations() -> bool` that returns `True` when all validations pass or are skipped, and `False` when any validation fails.
3. WHEN `run_validations()` is called, THE Validator SHALL verify that `build_reporte()` returns a dict with the keys: `codigo_dane`, `municipio`, `departamento`, `cultivo`, `año_referencia`, `titulo`, `contenido_texto`, `secciones`, `fuentes`.
4. WHEN `run_validations()` is called with the LLM mocked to raise an exception, THE Validator SHALL verify that `build_reporte_umata_llm()` returns a valid dict with `"generado_por_llm": False`.
5. WHEN `run_validations()` is called and `LLM_API_KEY` is not configured, THE Validator SHALL mark the LLM real-call validation as SKIP and continue without failing.
6. WHEN `run_validations()` is called, THE Validator SHALL verify that `render_pdf()` returns bytes starting with `b'%PDF'` and with length greater than 1024 bytes.
7. WHEN `run_validations()` is called, THE Validator SHALL verify that `render_pdf()` does not raise an exception when the input dict lacks the key `"prediccion_riesgo"`.
8. THE Validator SHALL print each validation result in the format `[Vn] Description    PASS | FAIL | SKIP` and a final summary line.
9. THE Validator SHALL exit with code 0 if all validations pass or are skipped, and with code 1 if any validation fails.
10. THE Validator SHALL NOT modify any data files or source code files during execution.

---

### Requirement 7: Logging y trazabilidad

**User Story:** As a developer, I want all C3 functions to log their key steps, so that I can diagnose issues in production without adding debug code.

#### Acceptance Criteria

1. WHEN `build_reporte_umata_llm()` calls `recuperar_contexto()`, THE Report_Generator SHALL log at INFO level: `"[C3.1] Contexto recuperado para {municipio} / {cultivo}"`.
2. WHEN `build_reporte_umata_llm()` calls the LLM, THE Report_Generator SHALL log at INFO level: `"[C3.1] Llamando LLM para reporte UMATA"`.
3. WHEN the LLM fallback is triggered, THE Report_Generator SHALL log at WARNING level: `"[C3.1] LLM no disponible, usando fallback build_reporte()"`.
4. WHEN `render_pdf()` omits the Semaforo block due to missing or unrecognized `prediccion_riesgo`, THE Report_Generator SHALL log at WARNING level: `"[C3.2] prediccion_riesgo no disponible, omitiendo semáforo"`.
5. THE Report_Generator SHALL use `logger = logging.getLogger(__name__)` and SHALL NOT configure handlers directly in the module.
