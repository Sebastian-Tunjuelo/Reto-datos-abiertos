"""
validate_c2.py — Validación de las plantillas de prompt C2.

Ejecutar desde la raíz del proyecto:
    python specs/C2_prompts/validate_c2.py

Cubre 4 bloques:
    Bloque 1: C2.1 — Prompt conversacional
    Bloque 2: C2.2 — Reporte UMATA
    Bloque 3: C2.3 — Comparación de cultivos
    Bloque 4: Compatibilidad con chat_engine.py (firmas existentes)

Código de salida 0 si todas pasan, 1 si alguna falla.
No llama al LLM ni lee archivos Parquet.
"""
import sys
import inspect
import logging

# Silenciar warnings de importación durante la validación
logging.disable(logging.WARNING)

try:
    from modules.conversational.prompts import (
        build_system_prompt,
        build_user_prompt,
        build_contexto_recuperado,
        format_feature_for_prompt,
        build_prompt_conversacional,
        build_prompt_reporte_umata,
        build_prompt_comparacion_cultivos,
    )
    from modules.conversational.rag import ContextoRecuperado
except ImportError as e:
    print(f"[ERROR] No se pudo importar el módulo: {e}")
    sys.exit(1)

logging.disable(logging.NOTSET)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check(nombre: str, condicion: bool, detalle: str = "") -> bool:
    """Imprime [PASS] o [FAIL] y retorna True si pasó."""
    estado = "[PASS]" if condicion else "[FAIL]"
    msg = f"{estado} {nombre}"
    if not condicion and detalle:
        msg += f": {detalle}"
    print(msg)
    return condicion


def _build_ctx_completo() -> ContextoRecuperado:
    """Fixture completo — todos los campos con valor."""
    ctx = ContextoRecuperado()
    ctx.prediccion = {
        "rendimiento_esperado": 1.45,
        "etiqueta_riesgo": "Alto",
        "prob_riesgo_alto": 0.71,
    }
    ctx.narrativa = (
        "El déficit de lluvia acumulada y el aumento del índice de fertilizantes elevan el riesgo."
    )
    ctx.top_features = [
        {
            "feature": "prec_acum_mm",
            "nombre_amigable": "Precipitación acumulada",
            "valor": 320.5,
            "importancia": 0.42,
            "direccion": "aumenta riesgo",
        },
        {
            "feature": "indice_agroinsumos",
            "nombre_amigable": "Índice de agroinsumos",
            "valor": 118.3,
            "importancia": 0.28,
            "direccion": "aumenta riesgo",
        },
        {
            "feature": "rendimiento_t1",
            "nombre_amigable": "Rendimiento año anterior",
            "valor": 1.2,
            "importancia": 0.15,
            "direccion": "disminuye riesgo",
        },
    ]
    ctx.serie_historica = [
        {"año": 2022, "rendimiento": 1.30},
        {"año": 2023, "rendimiento": 1.45},
        {"año": 2024, "rendimiento": 1.20},
    ]
    ctx.fuentes = ["predicciones_con_explicacion.parquet", "narrativa_riesgo", "top_features_shap"]
    ctx.contexto_efectivo = {
        "municipio": "Chaparral",
        "cultivo": "Café",
        "año": 2024,
        "escenario": "base",
    }
    return ctx


def _build_ctx_vacio() -> ContextoRecuperado:
    """Fixture vacío — todos los campos opcionales None."""
    ctx = ContextoRecuperado()
    ctx.contexto_efectivo = {}
    return ctx


# ---------------------------------------------------------------------------
# Bloque 1 — C2.1: Prompt conversacional
# ---------------------------------------------------------------------------

def _bloque1(ctx_completo: ContextoRecuperado, ctx_vacio: ContextoRecuperado) -> int:
    """Retorna número de fallos del bloque."""
    fallos = 0
    print("\n=== Bloque 1: C2.1 — Prompt conversacional ===")

    # 1.1 build_system_prompt("campesino") retorna string ≥ 100 chars
    try:
        r = build_system_prompt("campesino")
        ok = isinstance(r, str) and len(r) >= 100
        if not _check("C2.1.1 build_system_prompt('campesino') retorna string ≥ 100 chars", ok,
                      f"longitud={len(r) if isinstance(r, str) else 'no-str'}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.1 build_system_prompt('campesino') retorna string ≥ 100 chars", False, f"excepción: {e}")
        fallos += 1

    # 1.2 build_system_prompt("institucional") retorna string ≥ 100 chars
    try:
        r = build_system_prompt("institucional")
        ok = isinstance(r, str) and len(r) >= 100
        if not _check("C2.1.2 build_system_prompt('institucional') retorna string ≥ 100 chars", ok,
                      f"longitud={len(r) if isinstance(r, str) else 'no-str'}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.2 build_system_prompt('institucional') retorna string ≥ 100 chars", False, f"excepción: {e}")
        fallos += 1

    # 1.3 build_system_prompt("desconocido") usa fallback campesino
    try:
        r_desc = build_system_prompt("desconocido")
        r_camp = build_system_prompt("campesino")
        ok = r_desc == r_camp
        if not _check("C2.1.3 build_system_prompt('desconocido') usa fallback campesino", ok,
                      "no coincide con prompt campesino"):
            fallos += 1
    except Exception as e:
        _check("C2.1.3 build_system_prompt('desconocido') usa fallback campesino", False, f"excepción: {e}")
        fallos += 1

    # 1.4 build_contexto_recuperado(None, None, None, None) retorna placeholder
    try:
        r = build_contexto_recuperado(None, None, None, None)
        ok = isinstance(r, str) and len(r) > 0 and "no" in r.lower()
        if not _check("C2.1.4 build_contexto_recuperado(None×4) retorna placeholder no vacío", ok,
                      f"resultado={r!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.4 build_contexto_recuperado(None×4) retorna placeholder no vacío", False, f"excepción: {e}")
        fallos += 1

    # 1.5 build_contexto_recuperado con prediccion contiene el rendimiento "1.45"
    try:
        r = build_contexto_recuperado(prediccion=ctx_completo.prediccion, tono="campesino")
        ok = isinstance(r, str) and ("1.45" in r or "1,45" in r)
        if not _check("C2.1.5 build_contexto_recuperado con prediccion contiene '1.45'", ok,
                      f"resultado={r[:120]!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.5 build_contexto_recuperado con prediccion contiene '1.45'", False, f"excepción: {e}")
        fallos += 1

    # 1.6 format_feature_for_prompt({}) retorna string no vacío sin excepción
    try:
        r = format_feature_for_prompt({}, "campesino")
        ok = isinstance(r, str) and len(r) > 0
        if not _check("C2.1.6 format_feature_for_prompt({}) retorna string no vacío", ok,
                      f"resultado={r!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.6 format_feature_for_prompt({}) retorna string no vacío", False, f"excepción: {e}")
        fallos += 1

    # 1.7 format_feature_for_prompt con valor 320.5 contiene "320"
    try:
        r = format_feature_for_prompt({"feature": "prec_acum_mm", "valor": 320.5}, "campesino")
        ok = isinstance(r, str) and "320" in r
        if not _check("C2.1.7 format_feature_for_prompt con valor 320.5 contiene '320'", ok,
                      f"resultado={r!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.7 format_feature_for_prompt con valor 320.5 contiene '320'", False, f"excepción: {e}")
        fallos += 1

    # 1.8 build_prompt_conversacional(ctx_completo, ...) retorna dict con "system" y "user"
    try:
        r = build_prompt_conversacional(ctx_completo, "¿Cuál es el riesgo?", "campesino")
        ok = (isinstance(r, dict)
              and "system" in r and "user" in r
              and isinstance(r["system"], str) and len(r["system"]) > 0
              and isinstance(r["user"], str) and len(r["user"]) > 0)
        if not _check("C2.1.8 build_prompt_conversacional(ctx_completo) retorna dict {system, user}", ok,
                      f"claves={list(r.keys()) if isinstance(r, dict) else 'no-dict'}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.8 build_prompt_conversacional(ctx_completo) retorna dict {system, user}", False, f"excepción: {e}")
        fallos += 1

    # 1.9 build_prompt_conversacional(ctx_vacio, "") retorna dict válido sin excepción
    try:
        r = build_prompt_conversacional(ctx_vacio, "", "campesino")
        ok = isinstance(r, dict) and "system" in r and "user" in r
        if not _check("C2.1.9 build_prompt_conversacional(ctx_vacio, '') retorna dict válido", ok,
                      f"resultado={r!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.1.9 build_prompt_conversacional(ctx_vacio, '') retorna dict válido", False, f"excepción: {e}")
        fallos += 1

    # 1.10 "user" de build_prompt_conversacional(ctx_completo) contiene la narrativa
    try:
        r = build_prompt_conversacional(ctx_completo, "test", "campesino")
        narrativa_fragmento = "déficit de lluvia"
        ok = isinstance(r, dict) and narrativa_fragmento in r.get("user", "")
        if not _check("C2.1.10 'user' contiene la narrativa del fixture", ok,
                      f"narrativa no encontrada en user prompt"):
            fallos += 1
    except Exception as e:
        _check("C2.1.10 'user' contiene la narrativa del fixture", False, f"excepción: {e}")
        fallos += 1

    return fallos


# ---------------------------------------------------------------------------
# Bloque 2 — C2.2: Reporte UMATA
# ---------------------------------------------------------------------------

def _bloque2(ctx_completo: ContextoRecuperado, ctx_vacio: ContextoRecuperado) -> int:
    fallos = 0
    print("\n=== Bloque 2: C2.2 — Reporte UMATA ===")

    # 2.1 retorna dict con "system" y "user"
    try:
        r = build_prompt_reporte_umata(ctx_completo, "Chaparral", "Café", 2024)
        ok = isinstance(r, dict) and "system" in r and "user" in r
        if not _check("C2.2.1 build_prompt_reporte_umata retorna dict {system, user}", ok,
                      f"claves={list(r.keys()) if isinstance(r, dict) else 'no-dict'}"):
            fallos += 1
    except Exception as e:
        _check("C2.2.1 build_prompt_reporte_umata retorna dict {system, user}", False, f"excepción: {e}")
        fallos += 1

    # 2.2 "user" contiene "Chaparral" y "Tolima"
    try:
        r = build_prompt_reporte_umata(ctx_completo, "Chaparral", "Café", 2024)
        user = r.get("user", "")
        ok = "Chaparral" in user and "Tolima" in user
        if not _check("C2.2.2 'user' contiene 'Chaparral' y 'Tolima'", ok,
                      f"'Chaparral' en user={('Chaparral' in user)}, 'Tolima' en user={('Tolima' in user)}"):
            fallos += 1
    except Exception as e:
        _check("C2.2.2 'user' contiene 'Chaparral' y 'Tolima'", False, f"excepción: {e}")
        fallos += 1

    # 2.3 "user" contiene "Café" y "2024"
    try:
        r = build_prompt_reporte_umata(ctx_completo, "Chaparral", "Café", 2024)
        user = r.get("user", "")
        ok = "Café" in user and "2024" in user
        if not _check("C2.2.3 'user' contiene 'Café' y '2024'", ok,
                      f"'Café' en user={('Café' in user)}, '2024' en user={('2024' in user)}"):
            fallos += 1
    except Exception as e:
        _check("C2.2.3 'user' contiene 'Café' y '2024'", False, f"excepción: {e}")
        fallos += 1

    # 2.4 "system" contiene al menos 5 de las 8 secciones obligatorias
    try:
        r = build_prompt_reporte_umata(ctx_completo, "Chaparral", "Café", 2024)
        system = r.get("system", "")
        secciones = [
            "ENCABEZADO", "RESUMEN EJECUTIVO", "PREDICCIÓN", "FACTORES",
            "ANÁLISIS", "SERIE HISTÓRICA", "RECOMENDACIONES", "FUENTES"
        ]
        encontradas = sum(1 for s in secciones if s.upper() in system.upper())
        ok = encontradas >= 5
        if not _check(f"C2.2.4 'system' contiene ≥5 de 8 secciones obligatorias ({encontradas}/8)", ok,
                      f"solo {encontradas} secciones encontradas"):
            fallos += 1
    except Exception as e:
        _check("C2.2.4 'system' contiene ≥5 de 8 secciones obligatorias", False, f"excepción: {e}")
        fallos += 1

    # 2.5 build_prompt_reporte_umata(ctx_vacio, None, None, None) no lanza excepción
    try:
        r = build_prompt_reporte_umata(ctx_vacio, None, None, None)
        ok = isinstance(r, dict) and "system" in r and "user" in r
        if not _check("C2.2.5 build_prompt_reporte_umata(ctx_vacio, None×3) retorna dict válido", ok):
            fallos += 1
    except Exception as e:
        _check("C2.2.5 build_prompt_reporte_umata(ctx_vacio, None×3) retorna dict válido", False, f"excepción: {e}")
        fallos += 1

    # 2.6 "user" de ctx_vacio contiene "no disponible" (case-insensitive)
    try:
        r = build_prompt_reporte_umata(ctx_vacio, None, None, None)
        user = r.get("user", "")
        ok = "no disponible" in user.lower()
        if not _check("C2.2.6 'user' (ctx_vacio) contiene 'no disponible'", ok,
                      f"texto user={user[:200]!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.2.6 'user' (ctx_vacio) contiene 'no disponible'", False, f"excepción: {e}")
        fallos += 1

    # 2.7 municipio inexistente no lanza excepción
    try:
        r = build_prompt_reporte_umata(ctx_completo, "MunicipioInexistente", "Café", 2024)
        ok = isinstance(r, dict) and "system" in r and "user" in r
        if not _check("C2.2.7 municipio inexistente no lanza excepción", ok):
            fallos += 1
    except Exception as e:
        _check("C2.2.7 municipio inexistente no lanza excepción", False, f"excepción: {e}")
        fallos += 1

    return fallos


# ---------------------------------------------------------------------------
# Bloque 3 — C2.3: Comparación de cultivos
# ---------------------------------------------------------------------------

def _bloque3(ctx_completo: ContextoRecuperado, ctx_vacio: ContextoRecuperado) -> int:
    fallos = 0
    print("\n=== Bloque 3: C2.3 — Comparación de cultivos ===")

    # 3.1 retorna dict con "system" y "user" (solo Café)
    try:
        r = build_prompt_comparacion_cultivos({"Café": ctx_completo}, "Chaparral", 2024)
        ok = isinstance(r, dict) and "system" in r and "user" in r
        if not _check("C2.3.1 build_prompt_comparacion_cultivos({'Café': ctx}) retorna dict {system, user}", ok,
                      f"claves={list(r.keys()) if isinstance(r, dict) else 'no-dict'}"):
            fallos += 1
    except Exception as e:
        _check("C2.3.1 build_prompt_comparacion_cultivos({'Café': ctx}) retorna dict {system, user}", False, f"excepción: {e}")
        fallos += 1

    # 3.2 "user" contiene "Café"
    try:
        r = build_prompt_comparacion_cultivos({"Café": ctx_completo}, "Chaparral", 2024)
        ok = "Café" in r.get("user", "")
        if not _check("C2.3.2 'user' contiene 'Café'", ok):
            fallos += 1
    except Exception as e:
        _check("C2.3.2 'user' contiene 'Café'", False, f"excepción: {e}")
        fallos += 1

    # 3.3 "user" contiene nota de cultivos faltantes (Cacao y Maíz)
    try:
        r = build_prompt_comparacion_cultivos({"Café": ctx_completo}, "Chaparral", 2024)
        user = r.get("user", "")
        ok = ("Cacao" in user or "cacao" in user.lower()) and ("Maíz" in user or "maiz" in user.lower() or "Maiz" in user)
        if not _check("C2.3.3 'user' contiene nota de Cacao y Maíz faltantes", ok,
                      f"user={user[:300]!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.3.3 'user' contiene nota de Cacao y Maíz faltantes", False, f"excepción: {e}")
        fallos += 1

    # 3.4 con los 3 cultivos, "user" contiene los tres
    try:
        r = build_prompt_comparacion_cultivos(
            {"Café": ctx_completo, "Cacao": ctx_completo, "Maíz": ctx_completo},
            "Chaparral", 2024
        )
        user = r.get("user", "")
        ok = "Café" in user and "Cacao" in user and ("Maíz" in user or "Maiz" in user)
        if not _check("C2.3.4 con 3 cultivos, 'user' contiene Café, Cacao y Maíz", ok,
                      f"user={user[:300]!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.3.4 con 3 cultivos, 'user' contiene Café, Cacao y Maíz", False, f"excepción: {e}")
        fallos += 1

    # 3.5 dict vacío lanza ValueError con "[C2.3]"
    try:
        build_prompt_comparacion_cultivos({}, "Chaparral", 2024)
        _check("C2.3.5 dict vacío lanza ValueError con '[C2.3]'", False, "no lanzó excepción")
        fallos += 1
    except ValueError as e:
        ok = "[C2.3]" in str(e)
        if not _check("C2.3.5 dict vacío lanza ValueError con '[C2.3]'", ok,
                      f"mensaje={str(e)!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.3.5 dict vacío lanza ValueError con '[C2.3]'", False, f"excepción inesperada: {e}")
        fallos += 1

    # 3.6 ctx con prediccion=None no lanza excepción
    try:
        r = build_prompt_comparacion_cultivos({"Café": ctx_vacio}, "Chaparral", 2024)
        ok = isinstance(r, dict) and "system" in r and "user" in r
        if not _check("C2.3.6 ctx con prediccion=None no lanza excepción", ok):
            fallos += 1
    except Exception as e:
        _check("C2.3.6 ctx con prediccion=None no lanza excepción", False, f"excepción: {e}")
        fallos += 1

    # 3.7 "system" contiene las 4 secciones obligatorias del ranking
    try:
        r = build_prompt_comparacion_cultivos({"Café": ctx_completo}, "Chaparral", 2024)
        system = r.get("system", "")
        secciones = ["RANKING", "JUSTIFICACIÓN", "RECOMENDACIÓN", "ADVERTENCIAS"]
        encontradas = sum(1 for s in secciones if s.upper() in system.upper())
        ok = encontradas >= 4
        if not _check(f"C2.3.7 'system' contiene las 4 secciones del ranking ({encontradas}/4)", ok,
                      f"solo {encontradas} secciones encontradas"):
            fallos += 1
    except Exception as e:
        _check("C2.3.7 'system' contiene las 4 secciones del ranking", False, f"excepción: {e}")
        fallos += 1

    return fallos


# ---------------------------------------------------------------------------
# Bloque 4 — Compatibilidad con chat_engine.py (firmas existentes)
# ---------------------------------------------------------------------------

def _bloque4() -> int:
    fallos = 0
    print("\n=== Bloque 4: Compatibilidad con chat_engine.py ===")

    # 4.1 build_system_prompt acepta (tono="campesino")
    try:
        sig = inspect.signature(build_system_prompt)
        params = list(sig.parameters.keys())
        ok = params == ["tono"] and sig.parameters["tono"].default == "campesino"
        if not _check("C2.4.1 build_system_prompt firma: (tono='campesino')", ok,
                      f"params={params}, default={sig.parameters.get('tono', {})!r}"):
            fallos += 1
    except Exception as e:
        _check("C2.4.1 build_system_prompt firma: (tono='campesino')", False, f"excepción: {e}")
        fallos += 1

    # 4.2 build_user_prompt acepta (pregunta, contexto, contexto_recuperado, glosario_relevante="")
    try:
        sig = inspect.signature(build_user_prompt)
        params = list(sig.parameters.keys())
        ok = (
            params == ["pregunta", "contexto", "contexto_recuperado", "glosario_relevante"]
            and sig.parameters["glosario_relevante"].default == ""
        )
        if not _check("C2.4.2 build_user_prompt firma: (pregunta, contexto, contexto_recuperado, glosario_relevante='')", ok,
                      f"params={params}"):
            fallos += 1
    except Exception as e:
        _check("C2.4.2 build_user_prompt firma compatible", False, f"excepción: {e}")
        fallos += 1

    # 4.3 build_contexto_recuperado acepta (prediccion=None, narrativa=None, top_features=None, serie_historica=None, tono="campesino")
    try:
        sig = inspect.signature(build_contexto_recuperado)
        params = list(sig.parameters.keys())
        expected = ["prediccion", "narrativa", "top_features", "serie_historica", "tono"]
        ok = (
            params == expected
            and sig.parameters["prediccion"].default is None
            and sig.parameters["narrativa"].default is None
            and sig.parameters["top_features"].default is None
            and sig.parameters["serie_historica"].default is None
            and sig.parameters["tono"].default == "campesino"
        )
        if not _check("C2.4.3 build_contexto_recuperado firma: (prediccion=None, narrativa=None, top_features=None, serie_historica=None, tono='campesino')", ok,
                      f"params={params}"):
            fallos += 1
    except Exception as e:
        _check("C2.4.3 build_contexto_recuperado firma compatible", False, f"excepción: {e}")
        fallos += 1

    # 4.4 format_feature_for_prompt acepta (feature, tono="campesino")
    try:
        sig = inspect.signature(format_feature_for_prompt)
        params = list(sig.parameters.keys())
        ok = (
            params == ["feature", "tono"]
            and sig.parameters["tono"].default == "campesino"
        )
        if not _check("C2.4.4 format_feature_for_prompt firma: (feature, tono='campesino')", ok,
                      f"params={params}"):
            fallos += 1
    except Exception as e:
        _check("C2.4.4 format_feature_for_prompt firma compatible", False, f"excepción: {e}")
        fallos += 1

    return fallos


# ---------------------------------------------------------------------------
# Orquestador principal
# ---------------------------------------------------------------------------

def run_validations() -> int:
    """Ejecuta todas las verificaciones. Retorna número de fallos."""
    ctx_completo = _build_ctx_completo()
    ctx_vacio = _build_ctx_vacio()

    fallos = 0
    fallos += _bloque1(ctx_completo, ctx_vacio)
    fallos += _bloque2(ctx_completo, ctx_vacio)
    fallos += _bloque3(ctx_completo, ctx_vacio)
    fallos += _bloque4()

    # Contar total de verificaciones ejecutadas (10 + 7 + 7 + 4 = 28)
    total = 28
    pasaron = total - fallos
    print(f"\nResultado: {pasaron}/{total} verificaciones pasaron")
    return fallos


if __name__ == "__main__":
    fallos = run_validations()
    sys.exit(0 if fallos == 0 else 1)
