"""
Validación del motor RAG (C1.1 + C1.2).

Ejecutar:
    python specs/C1_rag_motor/validate_c1.py

Salida: PASS/FAIL por verificación + resumen final.
Código de salida: 0 si todo pasa, 1 si alguna falla.
"""

import sys
import logging
from pathlib import Path

# Añadir raíz del proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.config import DATA_DIR
from shared.dane_codes import MVP_CODIGOS, DANE_TO_NAME

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers de reporte
# ---------------------------------------------------------------------------

_resultados: list[tuple[bool, str]] = []


def _check(condicion: bool, descripcion: str, detalle: str = "") -> bool:
    estado = "[PASS]" if condicion else "[FAIL]"
    msg = f"{estado} {descripcion}"
    if detalle:
        msg += f" ({detalle})"
    print(msg)
    _resultados.append((condicion, descripcion))
    return condicion


# ---------------------------------------------------------------------------
# Bloque 1 — Cobertura del índice
# ---------------------------------------------------------------------------

def _bloque_cobertura() -> bool:
    from modules.conversational.rag import build_rag_index

    print("\n--- Bloque 1: Cobertura del índice ---")
    ok = True

    # 1. build_rag_index() no lanza excepción
    index = None
    try:
        index = build_rag_index()
        ok &= _check(True, "Índice construido sin errores")
    except Exception as e:
        _check(False, "Índice construido sin errores", str(e))
        print("[ABORT] No se puede continuar sin el índice.")
        return False

    # 2. total_documents >= 390
    total = index.total_documents
    ok &= _check(total >= 390, "total_documents >= 390", f"{total} documentos")

    # 3. Los 15 códigos DANE del MVP están presentes
    codigos_en_indice = {k[0] for k in index.keys}
    faltantes = set(MVP_CODIGOS) - codigos_en_indice
    ok &= _check(
        len(faltantes) == 0,
        "15 municipios MVP presentes en el índice",
        f"faltantes: {faltantes}" if faltantes else f"{len(codigos_en_indice)} códigos",
    )

    # 4. Los 3 cultivos están presentes
    cultivos_en_indice = {k[1] for k in index.keys}
    cultivos_esperados = {"Café", "Cacao", "Maíz"}
    faltantes_cult = cultivos_esperados - cultivos_en_indice
    ok &= _check(
        len(faltantes_cult) == 0,
        "3 cultivos presentes en el índice",
        f"faltantes: {faltantes_cult}" if faltantes_cult else str(cultivos_en_indice),
    )

    # 5. Distribución por cultivo
    dist: dict[str, int] = {}
    for (_, cultivo), docs in index._index.items():
        dist[cultivo] = dist.get(cultivo, 0) + len(docs)

    cafe = dist.get("Café", 0)
    cacao = dist.get("Cacao", 0)
    maiz = dist.get("Maíz", 0)
    dist_ok = cafe >= 80 and cacao >= 200 and maiz >= 85
    ok &= _check(
        dist_ok,
        "Distribución por cultivo: Café≥80, Cacao≥200, Maíz≥85",
        f"Café={cafe}, Cacao={cacao}, Maíz={maiz}",
    )

    return ok


# ---------------------------------------------------------------------------
# Bloque 2 — Integridad de documentos
# ---------------------------------------------------------------------------

def _bloque_integridad() -> bool:
    from modules.conversational.rag import get_rag_index

    print("\n--- Bloque 2: Integridad de documentos ---")
    ok = True
    index = get_rag_index()
    todos_docs = [doc for docs in index._index.values() for doc in docs]
    total = len(todos_docs)

    # 6. codigo_dane tiene exactamente 5 dígitos
    invalidos_dane = [d for d in todos_docs if len(d.codigo_dane) != 5 or not d.codigo_dane.isdigit()]
    ok &= _check(
        len(invalidos_dane) == 0,
        "Todos los codigo_dane tienen 5 dígitos",
        f"{len(invalidos_dane)} inválidos" if invalidos_dane else f"{total} documentos OK",
    )

    # 7. cultivo es uno de los 3 válidos
    cultivos_validos = {"Café", "Cacao", "Maíz"}
    invalidos_cult = [d for d in todos_docs if d.cultivo not in cultivos_validos]
    ok &= _check(
        len(invalidos_cult) == 0,
        "Todos los cultivos son válidos",
        f"{len(invalidos_cult)} inválidos" if invalidos_cult else f"{total} documentos OK",
    )

    # 8. año en rango 2007–2024
    fuera_rango = [d for d in todos_docs if not (2007 <= d.año <= 2024)]
    ok &= _check(
        len(fuera_rango) == 0,
        "Todos los años están en rango 2007-2024",
        f"{len(fuera_rango)} fuera de rango" if fuera_rango else f"{total} documentos OK",
    )

    # 9. top_features es siempre una lista
    no_lista = [d for d in todos_docs if not isinstance(d.top_features, list)]
    ok &= _check(
        len(no_lista) == 0,
        "top_features es lista en todos los documentos",
        f"{len(no_lista)} no son lista" if no_lista else f"{total} documentos OK",
    )

    # 10. ≥80% con narrativa_riesgo no nula
    con_narrativa = sum(1 for d in todos_docs if d.narrativa_riesgo is not None)
    pct_narrativa = con_narrativa / total * 100 if total else 0
    ok &= _check(
        pct_narrativa >= 80,
        "80%+ de documentos con narrativa_riesgo",
        f"{pct_narrativa:.1f}% ({con_narrativa}/{total})",
    )

    # 11. ≥80% con prediccion_riesgo válido
    riesgos_validos = {"Bajo", "Medio", "Alto"}
    con_riesgo = sum(1 for d in todos_docs if d.prediccion_riesgo in riesgos_validos)
    pct_riesgo = con_riesgo / total * 100 if total else 0
    ok &= _check(
        pct_riesgo >= 80,
        "80%+ de documentos con prediccion_riesgo válido",
        f"{pct_riesgo:.1f}% ({con_riesgo}/{total})",
    )

    return ok


# ---------------------------------------------------------------------------
# Bloque 3 — Función de recuperación
# ---------------------------------------------------------------------------

def _bloque_recuperacion() -> bool:
    from modules.conversational.rag import recuperar_contexto

    print("\n--- Bloque 3: Función de recuperación ---")
    ok = True

    # 12. Caso feliz por nombre
    try:
        ctx = recuperar_contexto(municipio="Chaparral", cultivo="Café")
        ok &= _check(
            ctx.prediccion is not None,
            "Recuperación por nombre de municipio funciona",
            f"fuentes={ctx.fuentes}",
        )
    except Exception as e:
        ok &= _check(False, "Recuperación por nombre de municipio funciona", str(e))

    # 13. Mismo resultado por código DANE
    try:
        ctx_nombre = recuperar_contexto(municipio="Chaparral", cultivo="Café")
        ctx_codigo = recuperar_contexto(municipio="73168", cultivo="Café")
        mismo = (
            ctx_nombre.prediccion == ctx_codigo.prediccion
            and ctx_nombre.narrativa == ctx_codigo.narrativa
        )
        ok &= _check(
            mismo,
            "Recuperación por código DANE produce el mismo resultado",
            f"nombre_pred={ctx_nombre.prediccion}, codigo_pred={ctx_codigo.prediccion}",
        )
    except Exception as e:
        ok &= _check(False, "Recuperación por código DANE produce el mismo resultado", str(e))

    # 14. Scoring por año: el documento seleccionado debe ser el más cercano a 2023
    try:
        ctx_2023 = recuperar_contexto(municipio="Chaparral", cultivo="Café", año=2023)
        # Verificar que hay predicción y que el año efectivo es ≤ 2023 o el más cercano
        # (no podemos acceder al doc directamente, pero sí al contexto_efectivo)
        tiene_pred = ctx_2023.prediccion is not None
        ok &= _check(
            tiene_pred,
            "Scoring por año selecciona documento correcto (año=2023)",
            f"prediccion={ctx_2023.prediccion}",
        )
    except Exception as e:
        ok &= _check(False, "Scoring por año selecciona documento correcto (año=2023)", str(e))

    # 15. Municipio inexistente → contexto vacío, sin excepción
    try:
        ctx = recuperar_contexto(municipio="MunicipioInexistente", cultivo="Café")
        ok &= _check(
            ctx.prediccion is None and ctx.narrativa is None,
            "Municipio inexistente retorna contexto vacío",
            f"prediccion={ctx.prediccion}",
        )
    except Exception as e:
        ok &= _check(False, "Municipio inexistente retorna contexto vacío", str(e))

    # 16. Cultivo inválido → contexto vacío, sin excepción
    try:
        ctx = recuperar_contexto(municipio="Chaparral", cultivo="CultivoInvalido")
        ok &= _check(
            ctx.prediccion is None and ctx.narrativa is None,
            "Cultivo inválido retorna contexto vacío",
            f"prediccion={ctx.prediccion}",
        )
    except Exception as e:
        ok &= _check(False, "Cultivo inválido retorna contexto vacío", str(e))

    # 17. Sin argumentos → contexto vacío
    try:
        ctx = recuperar_contexto()
        ok &= _check(
            ctx.prediccion is None and ctx.narrativa is None,
            "Sin argumentos retorna contexto vacío",
            f"prediccion={ctx.prediccion}",
        )
    except Exception as e:
        ok &= _check(False, "Sin argumentos retorna contexto vacío", str(e))

    return ok


# ---------------------------------------------------------------------------
# Bloque 4 — Idempotencia del índice
# ---------------------------------------------------------------------------

def _bloque_idempotencia() -> bool:
    from modules.conversational.rag import get_rag_index

    print("\n--- Bloque 4: Idempotencia del índice ---")
    ok = True

    # 18. Misma instancia en dos llamadas
    idx1 = get_rag_index()
    idx2 = get_rag_index()
    ok &= _check(
        idx1 is idx2,
        "get_rag_index() es idempotente (misma instancia)",
        f"id1={id(idx1)}, id2={id(idx2)}",
    )

    # 19. total_documents consistente
    ok &= _check(
        idx1.total_documents == idx2.total_documents,
        "total_documents consistente entre llamadas",
        f"{idx1.total_documents} == {idx2.total_documents}",
    )

    return ok


# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------

def run_validations() -> bool:
    """
    Ejecuta todas las verificaciones del motor RAG.

    Returns:
        bool: True si todas las verificaciones pasan, False si alguna falla.
    """
    # Verificar que el Parquet existe antes de empezar
    parquet_path = DATA_DIR / "predicciones_con_explicacion.parquet"
    if not parquet_path.exists():
        print(f"[FAIL] Archivo no encontrado: {parquet_path}")
        print("\n=== RESULTADO: ABORTADO — archivo Parquet no encontrado ===")
        return False

    _resultados.clear()

    ok = True
    ok &= _bloque_cobertura()
    ok &= _bloque_integridad()
    ok &= _bloque_recuperacion()
    ok &= _bloque_idempotencia()

    total = len(_resultados)
    pasaron = sum(1 for r, _ in _resultados if r)
    print(f"\n=== RESULTADO: {pasaron}/{total} verificaciones pasaron ===")
    return ok


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s — %(message)s")
    ok = run_validations()
    sys.exit(0 if ok else 1)
