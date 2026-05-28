"""
Módulo de generación de reportes para SiembraSegura IA.
Construye reportes por municipio y cultivo combinando predicciones,
serie histórica EVA, clima agregado y factores SHAP.
"""
import json
import logging
from io import BytesIO
from typing import Optional

import pandas as pd

from shared.config import DATA_DIR

logger = logging.getLogger(__name__)


def _get_feature_mapping() -> dict:
    """Importa FEATURE_MAPPING de rag.py de forma lazy para evitar dependencias circulares."""
    try:
        # Import directo del módulo, no del paquete, para evitar ejecutar __init__.py
        import importlib.util
        import os
        spec_path = os.path.join(os.path.dirname(__file__), "rag.py")
        spec = importlib.util.spec_from_file_location("rag_module", spec_path)
        rag_mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(rag_mod)
        return rag_mod.FEATURE_MAPPING
    except Exception:
        return {}

# ── Textos de recomendación por nivel de riesgo ───────────────────────────────

RECOMENDACIONES = {
    "Bajo": (
        "Las condiciones son favorables. Se recomienda mantener las prácticas "
        "actuales y monitorear el clima."
    ),
    "Medio": (
        "Existe riesgo moderado. Se recomienda revisar el plan de fertilización "
        "y estar atento a anomalías climáticas."
    ),
    "Alto": (
        "Riesgo elevado detectado. Se recomienda consultar con la UMATA local "
        "y considerar medidas de mitigación."
    ),
}

SECCIONES_ORDEN = [
    "Resumen ejecutivo",
    "Histórico",
    "Clima",
    "Riesgo",
    "Escenarios",
    "Recomendación",
]


# ── Carga de datos ────────────────────────────────────────────────────────────

def _load_predicciones() -> pd.DataFrame:
    """Carga predicciones_con_explicacion.parquet. Lanza FileNotFoundError si no existe."""
    path = DATA_DIR / "predicciones_con_explicacion.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    return pd.read_parquet(path)


def _load_eva_completa() -> pd.DataFrame:
    """Carga eva_completa.parquet. Lanza FileNotFoundError si no existe."""
    path = DATA_DIR / "eva_completa.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    return pd.read_parquet(path)


def _load_clima_agregado() -> pd.DataFrame:
    """Carga clima_agregado.parquet. Lanza FileNotFoundError si no existe."""
    path = DATA_DIR / "clima_agregado.parquet"
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    return pd.read_parquet(path)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _feature_nombre_amigable(feature_id: str) -> str:
    """Retorna el nombre amigable de una feature SHAP o el ID original si no está mapeado."""
    mapping = _get_feature_mapping()
    return mapping.get(feature_id, feature_id)


def _parse_top_features(raw) -> list:
    """Parsea top_features desde string JSON o lista."""
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return []
    return []


# ── Construcción de secciones ─────────────────────────────────────────────────

def _seccion_resumen_ejecutivo(
    municipio: str,
    departamento: str,
    cultivo: str,
    año: int,
    prediccion_riesgo: str,
) -> str:
    lineas = [
        f"Municipio: {municipio} ({departamento})",
        f"Cultivo: {cultivo}",
        f"Año de referencia: {año}",
        f"Nivel de riesgo predicho: {prediccion_riesgo}",
    ]
    return "\n".join(lineas)


def _seccion_historico(serie: list) -> str:
    """Construye la sección de histórico de rendimiento (últimos 5 años)."""
    if not serie:
        return "No hay datos históricos disponibles para este municipio y cultivo."
    lineas = ["Rendimiento histórico (t/ha):"]
    for item in serie:
        año = item.get("año", "N/D")
        rend = item.get("rendimiento")
        if rend is not None:
            lineas.append(f"  - {año}: {rend:.2f} t/ha")
        else:
            lineas.append(f"  - {año}: sin dato")
    return "\n".join(lineas)


def _seccion_clima(clima_row: Optional[dict]) -> str:
    """Construye la sección de clima del último año disponible."""
    if not clima_row:
        return "No hay datos climáticos disponibles para este municipio."
    año = clima_row.get("año", "N/D")
    lineas = [f"Clima del año {año}:"]
    prec = clima_row.get("prec_acum_mm")
    temp = clima_row.get("temp_media_c")
    hum = clima_row.get("hum_media_pct")
    if prec is not None:
        lineas.append(f"  - Precipitación acumulada: {prec:.1f} mm")
    if temp is not None:
        lineas.append(f"  - Temperatura media: {temp:.1f} °C")
    if hum is not None:
        lineas.append(f"  - Humedad relativa media: {hum:.1f}%")
    if len(lineas) == 1:
        lineas.append("  Sin datos climáticos detallados.")
    return "\n".join(lineas)


def _seccion_riesgo(
    prediccion_riesgo: str,
    narrativa: Optional[str],
    top_features: list,
) -> str:
    """Construye la sección de riesgo con narrativa y factores SHAP."""
    lineas = [f"Nivel de riesgo: {prediccion_riesgo}"]
    if narrativa:
        lineas.append(f"\nAnálisis: {narrativa}")
    if top_features:
        lineas.append("\nFactores determinantes (SHAP):")
        for i, feat in enumerate(top_features[:5], 1):
            if isinstance(feat, dict):
                feat_id = feat.get("feature_id", feat.get("feature", ""))
                nombre = _feature_nombre_amigable(feat_id)
                valor = feat.get("valor_original", feat.get("value"))
                direccion = feat.get("direccion", feat.get("direction", ""))
                if valor is not None:
                    try:
                        lineas.append(f"  {i}. {nombre}: {float(valor):.3f} ({direccion})")
                    except (TypeError, ValueError):
                        lineas.append(f"  {i}. {nombre}: {valor} ({direccion})")
                else:
                    lineas.append(f"  {i}. {nombre} ({direccion})")
            elif isinstance(feat, str):
                lineas.append(f"  {i}. {_feature_nombre_amigable(feat)}")
    return "\n".join(lineas)


def _seccion_escenarios() -> str:
    return "Ver endpoint /escenario para simulaciones de escenarios (seco, lluvioso, fertilizantes)."


def _seccion_recomendacion(prediccion_riesgo: str) -> str:
    return RECOMENDACIONES.get(prediccion_riesgo, RECOMENDACIONES["Medio"])


# ── Función principal ─────────────────────────────────────────────────────────

def build_reporte(
    codigo_dane: str,
    municipio: str,
    departamento: str,
    cultivo: str,
) -> dict:
    """
    Construye el contenido del reporte para un municipio y cultivo.

    Args:
        codigo_dane: Código DANE de 5 dígitos.
        municipio: Nombre display del municipio (Title Case).
        departamento: Nombre del departamento (Title Case).
        cultivo: Cultivo normalizado ('Café', 'Cacao' o 'Maíz').

    Returns:
        dict con claves: codigo_dane, municipio, departamento, cultivo,
        año_referencia, titulo, contenido_texto, secciones, fuentes.

    Raises:
        ValueError: si no hay predicción explicada disponible.
        FileNotFoundError: si los parquets no existen.
    """
    fuentes: list[str] = []

    # ── 1. Cargar y filtrar predicciones ──────────────────────────────────────
    df_pred = _load_predicciones()
    df_pred["codigo_dane"] = df_pred["codigo_dane"].astype(str).str.zfill(5)

    mask = (df_pred["codigo_dane"] == codigo_dane) & (df_pred["cultivo"] == cultivo)
    df_filtrado = df_pred[mask]

    if df_filtrado.empty:
        raise ValueError(
            f"No hay predicción explicada para {municipio} / {cultivo}"
        )

    # Tomar el registro con el año más alto
    df_filtrado = df_filtrado.sort_values("año", ascending=False)
    row = df_filtrado.iloc[0]
    año_ref = int(row["año"]) if pd.notna(row.get("año")) else 0
    prediccion_riesgo = str(row.get("prediccion_riesgo", "Medio"))
    narrativa = str(row["narrativa_riesgo"]) if pd.notna(row.get("narrativa_riesgo")) else None
    top_features = _parse_top_features(row.get("top_features"))
    fuentes.append("predicciones_con_explicacion.parquet")

    # ── 2. Serie histórica EVA (últimos 5 años) ───────────────────────────────
    serie_historica: list = []
    try:
        df_eva = _load_eva_completa()
        df_eva["codigo_dane"] = df_eva["codigo_dane"].astype(str).str.zfill(5)
        df_eva["año"] = pd.to_numeric(df_eva["año"], errors="coerce")
        df_eva = df_eva.dropna(subset=["año"])
        df_eva["año"] = df_eva["año"].astype(int)

        mask_eva = (df_eva["codigo_dane"] == codigo_dane) & (df_eva["cultivo"] == cultivo)
        df_hist = df_eva[mask_eva].copy()

        if not df_hist.empty:
            # Agregar por año (puede haber periodos A/B)
            df_hist = (
                df_hist.groupby("año", as_index=False)["rendimiento"]
                .mean()
                .sort_values("año", ascending=True)
            )
            for _, r in df_hist.tail(5).iterrows():
                rend = float(r["rendimiento"]) if pd.notna(r.get("rendimiento")) else None
                serie_historica.append({"año": int(r["año"]), "rendimiento": rend})
            fuentes.append("eva_completa.parquet")
    except FileNotFoundError:
        logger.warning("eva_completa.parquet no disponible; omitiendo histórico")

    # ── 3. Clima del último año disponible ────────────────────────────────────
    clima_row: Optional[dict] = None
    try:
        df_clima = _load_clima_agregado()
        df_clima["codigo_dane"] = df_clima["codigo_dane"].astype(str).str.zfill(5)
        df_clima["año"] = pd.to_numeric(df_clima["año"], errors="coerce")
        df_clima = df_clima.dropna(subset=["año"])

        mask_clima = df_clima["codigo_dane"] == codigo_dane
        df_mun_clima = df_clima[mask_clima].copy()

        if not df_mun_clima.empty:
            df_mun_clima = df_mun_clima.sort_values("año", ascending=False)
            r_clima = df_mun_clima.iloc[0]
            clima_row = {
                "año": int(r_clima["año"]),
                "prec_acum_mm": float(r_clima["prec_acum_mm"]) if pd.notna(r_clima.get("prec_acum_mm")) else None,
                "temp_media_c": float(r_clima["temp_media_c"]) if pd.notna(r_clima.get("temp_media_c")) else None,
                "hum_media_pct": float(r_clima["hum_media_pct"]) if pd.notna(r_clima.get("hum_media_pct")) else None,
            }
            fuentes.append("clima_agregado.parquet")
    except FileNotFoundError:
        logger.warning("clima_agregado.parquet no disponible; omitiendo clima")

    # ── 4. Construir secciones ────────────────────────────────────────────────
    sec_resumen = _seccion_resumen_ejecutivo(
        municipio, departamento, cultivo, año_ref, prediccion_riesgo
    )
    sec_historico = _seccion_historico(serie_historica)
    sec_clima = _seccion_clima(clima_row)
    sec_riesgo = _seccion_riesgo(prediccion_riesgo, narrativa, top_features)
    sec_escenarios = _seccion_escenarios()
    sec_recomendacion = _seccion_recomendacion(prediccion_riesgo)

    # ── 5. Concatenar contenido_texto ─────────────────────────────────────────
    bloques = [
        ("Resumen ejecutivo", sec_resumen),
        ("Histórico", sec_historico),
        ("Clima", sec_clima),
        ("Riesgo", sec_riesgo),
        ("Escenarios", sec_escenarios),
        ("Recomendación", sec_recomendacion),
    ]

    partes_texto = []
    for titulo_sec, contenido_sec in bloques:
        partes_texto.append(f"=== {titulo_sec} ===\n{contenido_sec}")

    contenido_texto = "\n\n".join(partes_texto)

    titulo = (
        f"Reporte municipal de riesgo y recomendación - {municipio} / {cultivo}"
    )

    return {
        "codigo_dane": codigo_dane,
        "municipio": municipio,
        "departamento": departamento,
        "cultivo": cultivo,
        "año_referencia": año_ref,
        "titulo": titulo,
        "contenido_texto": contenido_texto,
        "secciones": SECCIONES_ORDEN,
        "fuentes": fuentes,
    }


# ── Renderizado PDF ───────────────────────────────────────────────────────────

def render_pdf(reporte: dict) -> bytes:
    """
    Genera un PDF a partir del dict de reporte.

    Args:
        reporte: Dict retornado por build_reporte().

    Returns:
        bytes del PDF generado.

    Raises:
        ImportError: si reportlab no está instalado.
    """
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            HRFlowable,
        )
    except ImportError as exc:
        raise ImportError(
            "reportlab no está instalado. Instálalo con: pip install reportlab"
        ) from exc

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()

    style_titulo = ParagraphStyle(
        "Titulo",
        parent=styles["Heading1"],
        fontSize=16,
        spaceAfter=6,
        textColor=colors.HexColor("#1a5276"),
    )
    style_meta = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#555555"),
        spaceAfter=4,
    )
    style_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=styles["Heading2"],
        fontSize=12,
        spaceBefore=12,
        spaceAfter=4,
        textColor=colors.HexColor("#1a5276"),
    )
    style_cuerpo = ParagraphStyle(
        "Cuerpo",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=6,
    )
    style_footer = ParagraphStyle(
        "Footer",
        parent=styles["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#888888"),
        alignment=1,  # centrado
    )

    story = []

    # Título
    story.append(Paragraph(reporte["titulo"], style_titulo))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a5276")))
    story.append(Spacer(1, 0.3 * cm))

    # Metadatos
    story.append(Paragraph(f"<b>Municipio:</b> {reporte['municipio']}", style_meta))
    story.append(Paragraph(f"<b>Departamento:</b> {reporte['departamento']}", style_meta))
    story.append(Paragraph(f"<b>Cultivo:</b> {reporte['cultivo']}", style_meta))
    story.append(Paragraph(f"<b>Año de referencia:</b> {reporte['año_referencia']}", style_meta))
    story.append(Spacer(1, 0.5 * cm))

    # Secciones
    contenido = reporte.get("contenido_texto", "")
    # Parsear secciones del contenido_texto
    bloques = contenido.split("\n\n")
    for bloque in bloques:
        if bloque.startswith("=== ") and " ===" in bloque:
            # Separar título de sección y contenido
            primera_linea_fin = bloque.index("\n") if "\n" in bloque else len(bloque)
            titulo_sec = bloque[4:primera_linea_fin].replace(" ===", "").strip()
            contenido_sec = bloque[primera_linea_fin:].strip()
            story.append(Paragraph(titulo_sec, style_subtitulo))
            if contenido_sec:
                # Convertir saltos de línea en párrafos separados
                for linea in contenido_sec.split("\n"):
                    linea = linea.strip()
                    if linea:
                        # Escapar caracteres especiales para reportlab
                        linea = linea.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                        story.append(Paragraph(linea, style_cuerpo))
            story.append(Spacer(1, 0.2 * cm))

    # Footer
    story.append(Spacer(1, 1 * cm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc")))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph("Generado por SiembraSegura IA", style_footer))

    doc.build(story)
    return buffer.getvalue()
