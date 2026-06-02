import sys
import os
import logging

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from unittest.mock import patch

from shared.config import LLM_API_KEY
from modules.conversational.reports import (
    build_reporte,
    build_reporte_umata_llm,
    render_pdf
)

# Configurar logging para la validación (evitar que los warnings del código saturen la consola)
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


def _print_result(v_id: str, desc: str, status: str, extra: str = ""):
    status_color = status
    if status == "PASS":
        status_color = "\033[92mPASS\033[0m"
    elif status == "FAIL":
        status_color = "\033[91mFAIL\033[0m"
    elif status == "SKIP":
        status_color = "\033[93mSKIP\033[0m"
    
    extra_str = f"  ({extra})" if extra else ""
    print(f"[{v_id}] {desc:<45} {status_color}{extra_str}")


def run_validations() -> bool:
    """
    Ejecuta todas las validaciones de C3.
    Retorna True si todas pasan (o las opcionales son SKIP), False si alguna falla.
    """
    pasadas = 0
    totales = 7
    skips = 0

    print("Iniciando validaciones de C3_reportes...\n")

    # Municipio de prueba (Chaparral, Café)
    codigo_dane = "73168"
    municipio = "Chaparral"
    departamento = "Tolima"
    cultivo = "Café"

    # --- V1: Retrocompatibilidad build_reporte() ---
    try:
        dict_v1 = build_reporte(codigo_dane, municipio, departamento, cultivo)
        claves_esperadas = {
            "codigo_dane", "municipio", "departamento", "cultivo", 
            "año_referencia", "titulo", "contenido_texto", "secciones", "fuentes"
        }
        if claves_esperadas.issubset(set(dict_v1.keys())):
            _print_result("V1", "Retrocompatibilidad build_reporte()", "PASS")
            pasadas += 1
        else:
            faltantes = claves_esperadas - set(dict_v1.keys())
            _print_result("V1", "Retrocompatibilidad build_reporte()", "FAIL", f"Faltan claves: {faltantes}")
    except Exception as e:
        _print_result("V1", "Retrocompatibilidad build_reporte()", "FAIL", str(e))

    # --- V2: build_reporte_umata_llm() fallback (mock) ---
    try:
        dict_v2 = None
        # Hacemos mock de generate_content para que lance excepcion
        with patch("google.generativeai.GenerativeModel.generate_content") as mock_generate:
            mock_generate.side_effect = Exception("API Caída simulada")
            dict_v2 = build_reporte_umata_llm(codigo_dane, municipio, departamento, cultivo)
            
            if dict_v2.get("generado_por_llm") is False and "contenido_texto" in dict_v2:
                _print_result("V2", "build_reporte_umata_llm() fallback (mock)", "PASS")
                pasadas += 1
            else:
                _print_result("V2", "build_reporte_umata_llm() fallback (mock)", "FAIL", "generado_por_llm no es False o falta contenido")
    except Exception as e:
        _print_result("V2", "build_reporte_umata_llm() fallback (mock)", "FAIL", str(e))

    # --- V3: build_reporte_umata_llm() con LLM real ---
    if not LLM_API_KEY:
        _print_result("V3", "build_reporte_umata_llm() con LLM real", "SKIP", "LLM_API_KEY no configurada")
        skips += 1
    else:
        try:
            dict_v3 = build_reporte_umata_llm(codigo_dane, municipio, departamento, cultivo)
            if dict_v3.get("generado_por_llm") is True and len(dict_v3.get("contenido_texto", "")) > 100:
                _print_result("V3", "build_reporte_umata_llm() con LLM real", "PASS")
                pasadas += 1
            else:
                _print_result("V3", "build_reporte_umata_llm() con LLM real", "FAIL", "generado_por_llm no es True o contenido muy corto")
        except Exception as e:
            _print_result("V3", "build_reporte_umata_llm() con LLM real", "FAIL", str(e))

    # --- V4: render_pdf() con dict de build_reporte() ---
    try:
        pdf_v4 = render_pdf(dict_v1)
        kb = len(pdf_v4) / 1024
        if pdf_v4.startswith(b"%PDF") and len(pdf_v4) > 1024:
            _print_result("V4", "render_pdf() con build_reporte()", "PASS", f"{kb:.1f} KB")
            pasadas += 1
        else:
            _print_result("V4", "render_pdf() con build_reporte()", "FAIL", "PDF no es válido o es muy pequeño")
    except Exception as e:
        _print_result("V4", "render_pdf() con build_reporte()", "FAIL", str(e))

    # --- V5: render_pdf() con dict de build_reporte_umata_llm() ---
    try:
        # Usamos el dict_v2 (fallback) que es seguro de tener
        pdf_v5 = render_pdf(dict_v2)
        kb = len(pdf_v5) / 1024
        if pdf_v5.startswith(b"%PDF") and len(pdf_v5) > 1024:
            _print_result("V5", "render_pdf() con build_reporte_umata_llm()", "PASS", f"{kb:.1f} KB")
            pasadas += 1
        else:
            _print_result("V5", "render_pdf() con build_reporte_umata_llm()", "FAIL", "PDF no es válido")
    except Exception as e:
        _print_result("V5", "render_pdf() con build_reporte_umata_llm()", "FAIL", str(e))

    # --- V6: render_pdf() sin prediccion_riesgo ---
    try:
        dict_minimo = {
            "codigo_dane": "12345",
            "municipio": "Test",
            "departamento": "TestDept",
            "cultivo": "Café",
            "año_referencia": 2024,
            "titulo": "Reporte Test",
            "contenido_texto": "=== Resumen ejecutivo ===\nHola",
            "secciones": ["Resumen ejecutivo"],
            "fuentes": []
        }
        pdf_v6 = render_pdf(dict_minimo)
        if pdf_v6.startswith(b"%PDF"):
            _print_result("V6", "render_pdf() sin prediccion_riesgo", "PASS")
            pasadas += 1
        else:
            _print_result("V6", "render_pdf() sin prediccion_riesgo", "FAIL", "PDF no es válido")
    except Exception as e:
        _print_result("V6", "render_pdf() sin prediccion_riesgo", "FAIL", str(e))

    # --- V7: ValueError para municipio sin predicción ---
    try:
        # Cultivo absurdo para forzar ValueError
        build_reporte_umata_llm(codigo_dane, municipio, departamento, "CultivoInexistente")
        _print_result("V7", "ValueError para municipio sin predicción", "FAIL", "No lanzó ValueError")
    except ValueError:
        _print_result("V7", "ValueError para municipio sin predicción", "PASS")
        pasadas += 1
    except Exception as e:
        _print_result("V7", "ValueError para municipio sin predicción", "FAIL", f"Lanzó otra excepción: {e}")

    # --- Resumen Final ---
    print("\n" + "-"*60)
    if skips > 0:
        print(f"C3 Validaciones: {pasadas}/{totales} pasadas ({skips} SKIP)")
    else:
        print(f"C3 Validaciones: {pasadas}/{totales} pasadas")
    
    return pasadas + skips == totales

if __name__ == "__main__":
    ok = run_validations()
    sys.exit(0 if ok else 1)
