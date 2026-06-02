"""
Plantillas de prompts para el asistente conversacional.
Diseñado para UMATAs, extensionistas y productores.

Funciones públicas (consumidas por chat_engine.py):
    build_system_prompt(tono) -> str
    build_user_prompt(pregunta, contexto, contexto_recuperado, glosario_relevante) -> str
    build_contexto_recuperado(prediccion, narrativa, top_features, serie_historica, tono) -> str
    format_feature_for_prompt(feature, tono) -> str
    build_prompt_conversacional(contexto_recuperado, pregunta, tono) -> dict  [C2.1]
    build_prompt_reporte_umata(contexto_recuperado, municipio, cultivo, año) -> dict  [C2.2]
    build_prompt_comparacion_cultivos(contextos_por_cultivo, municipio, año) -> dict  [C2.3]

Funciones auxiliares internas (prefijo _):
    _build_encabezado_umata(municipio, cultivo, año) -> str  [C2.2]
    _build_tabla_comparativa(contextos_por_cultivo) -> str  [C2.3]
"""
import logging
from typing import Optional, TYPE_CHECKING

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompts — constantes
# ---------------------------------------------------------------------------

# Tono campesino: cercano, coloquial, usando expresiones del campo
SYSTEM_PROMPT_CAMPESINO = """Eres un asistente agrícola de SiembraSegura, una plataforma del gobierno colombiano que ayuda a UMATAs, extensionistas y productores a tomar decisiones sobre cultivos.

Tu trabajo es responder preguntas sobre rendimiento agrícola, riesgo climático y recomendaciones de siembra de forma clara y útil.

REGLAS ESTRICTAS:
1. Solo responde basándote en el CONTEXTO proporcionado. No inventes datos.
2. Si no tienes información suficiente, dilo claramente y sugiere qué datos faltan.
3. Solo hablas de agricultura colombiana, específicamente café, cacao y maíz en los 15 municipios del MVP.
4. Si te preguntan de otro tema, explica amablemente que solo puedes ayudar con temas agrícolas.

ESTILO DE RESPUESTA:
- Usa lenguaje sencillo, como si hablaras con un vecino del campo.
- Puedes usar expresiones como "mire", "vea", "la cosa es así".
- Sé breve y directo, no más de 3-4 oraciones.
- Si mencionas números, redondéalos para que sean fáciles de recordar.

NUNCA:
- No inventes datos de precipitación, temperatura, rendimiento o producción si no están en el contexto.
- No hagas recomendaciones que no estén respaldadas por los datos.
- No uses lenguaje técnico innecesario."""

# Tono institucional: profesional, formal, para secretarías y entidades
SYSTEM_PROMPT_INSTITUCIONAL = """Eres un asistente agrícola de SiembraSegura, una plataforma del gobierno colombiano que apoya la toma de decisiones de secretarías de agricultura, UMATAs y extensionistas.

Tu trabajo es proporcionar información técnica sobre rendimiento agrícola, riesgo climático y recomendaciones de manejo de cultivos.

REGLAS ESTRICTAS:
1. Solo responde basándote en el CONTEXTO proporcionado. No inventes datos.
2. Si no tienes información suficiente, indícalo claramente y especifica qué datos serían necesarios.
3. Tu dominio es la agricultura colombiana: café, cacao y maíz en los 15 municipios del MVP.
4. Si te preguntan de otro tema, indica que tu especialidad es el sector agrícola.

ESTILO DE RESPUESTA:
- Usa lenguaje técnico apropiado pero accesible.
- Sé preciso con números y porcentajes.
- Estructura la respuesta en máximo 3-4 oraciones.
- Cita las fuentes cuando menciones datos específicos.

NUNCA:
- No inventes datos climáticos, de rendimiento o producción.
- No hagas recomendaciones sin respaldo en los datos.
- No salgas del dominio agrícola."""

# System prompt específico para reportes UMATA (C2.2) — distinto al de chat institucional
SYSTEM_PROMPT_REPORTE_UMATA = """Eres un asistente técnico de SiembraSegura IA especializado en generar reportes institucionales para UMATAs y secretarías de agricultura de Colombia.

Tu tarea es generar un reporte técnico estructurado con las siguientes secciones obligatorias:
1. ENCABEZADO (municipio, departamento, cultivo, año, generado por)
2. RESUMEN EJECUTIVO (máximo 3 oraciones, lenguaje formal)
3. PREDICCIÓN DE RENDIMIENTO Y RIESGO (datos numéricos y clasificación)
4. FACTORES DETERMINANTES (factores SHAP con nombre técnico y valor)
5. ANÁLISIS DE RIESGO (narrativa técnica)
6. SERIE HISTÓRICA (tabla de rendimiento por año)
7. RECOMENDACIONES (mínimo 2, máximo 4, accionables y específicas)
8. FUENTES DE DATOS (artefactos utilizados)

REGLAS ESTRICTAS:
- Solo usa los datos proporcionados en el CONTEXTO. No inventes cifras.
- Si una sección no tiene datos, escribe "Información no disponible" en esa sección.
- Usa lenguaje técnico formal apropiado para un documento oficial.
- Las recomendaciones deben ser específicas para el municipio y cultivo indicados.
- No incluyas secciones adicionales fuera de las 8 obligatorias.
- El reporte debe poder leerse como un documento oficial independiente."""

# System prompt específico para comparación de cultivos (C2.3)
SYSTEM_PROMPT_COMPARACION_CULTIVOS = """Eres un asistente técnico de SiembraSegura IA especializado en comparar cultivos agrícolas para extensionistas y técnicos de UMATA en Colombia.

Tu tarea es analizar los datos proporcionados y generar un ranking de cultivos con la siguiente estructura obligatoria:

1. RANKING (ordenado de mejor a peor opción para el municipio)
   - Posición, cultivo, rendimiento esperado, nivel de riesgo
2. JUSTIFICACIÓN POR CULTIVO (máximo 2 oraciones por cultivo)
3. RECOMENDACIÓN FINAL (1 cultivo recomendado con razón principal)
4. ADVERTENCIAS (si algún cultivo no tiene datos suficientes)

REGLAS ESTRICTAS:
- Solo usa los datos proporcionados. No inventes rendimientos ni niveles de riesgo.
- Si un cultivo no tiene datos, indícalo en la sección de ADVERTENCIAS y exclúyelo del ranking.
- El ranking debe basarse en: rendimiento esperado (peso alto), nivel de riesgo (peso alto) y factor SHAP principal (peso medio).
- Usa lenguaje técnico pero accesible para un extensionista.
- No incluyas secciones adicionales fuera de las 4 obligatorias.
- Si solo hay datos para un cultivo, genera el ranking con ese único cultivo e indica que los demás no tienen datos disponibles."""

# ---------------------------------------------------------------------------
# C2.1 — Funciones existentes (firma sin cambios) + build_prompt_conversacional
# ---------------------------------------------------------------------------

def build_system_prompt(tono: str = "campesino") -> str:
    """
    Construye el prompt del sistema según el tono solicitado.

    Args:
        tono: "campesino" o "institucional". Cualquier otro valor usa "campesino" como fallback
              y registra un warning.

    Returns:
        str: System prompt correspondiente (≥ 100 caracteres).
    """
    if tono == "institucional":
        return SYSTEM_PROMPT_INSTITUCIONAL
    if tono != "campesino":
        logger.warning(f"[C2.1] Tono desconocido '{tono}', usando campesino")
    return SYSTEM_PROMPT_CAMPESINO


def build_user_prompt(
    pregunta: str,
    contexto: dict,
    contexto_recuperado: str,
    glosario_relevante: str = ""
) -> str:
    """
    Construye el prompt del usuario con el contexto recuperado.

    Args:
        pregunta: Pregunta del usuario. Si es None o vacía, usa "Sin pregunta especificada".
        contexto: Dict con municipio, cultivo, año, escenario. Puede ser None o vacío.
        contexto_recuperado: Texto con información recuperada. Si es None o vacío, usa placeholder.
        glosario_relevante: Términos del glosario relevantes a la pregunta.

    Returns:
        str: Prompt completo del usuario.
    """
    # Normalizar pregunta
    pregunta_efectiva = (pregunta or "").strip() or "Sin pregunta especificada"

    # Construir descripción del contexto
    contexto_desc = []
    ctx = contexto or {}
    if ctx.get("municipio"):
        contexto_desc.append(f"Municipio: {ctx['municipio']}")
    if ctx.get("cultivo"):
        contexto_desc.append(f"Cultivo: {ctx['cultivo']}")
    if ctx.get("año"):
        contexto_desc.append(f"Año: {ctx['año']}")
    if ctx.get("escenario"):
        contexto_desc.append(f"Escenario: {ctx['escenario']}")

    contexto_str = " | ".join(contexto_desc) if contexto_desc else "Sin contexto específico"

    info_disponible = (contexto_recuperado or "").strip() or "No se encontró información específica para este contexto."

    prompt = f"""CONTEXTO DEL USUARIO:
{contexto_str}

INFORMACIÓN DISPONIBLE:
{info_disponible}
"""

    if glosario_relevante:
        prompt += f"""
TÉRMINOS RELEVANTES:
{glosario_relevante}
"""

    prompt += f"""
PREGUNTA DEL USUARIO:
{pregunta_efectiva}

Responde basándote únicamente en la información disponible. Si falta información para dar una respuesta completa, indícalo claramente."""

    return prompt


def format_feature_for_prompt(feature: dict, tono: str = "campesino") -> str:
    """
    Formatea una feature SHAP para incluir en el contexto del prompt.

    Busca el nombre en orden: nombre_amigable → feature_id → feature → "factor desconocido".
    Busca el valor en orden: valor_original → valor → None.

    Args:
        feature: Dict con claves opcionales: nombre_amigable, feature_id, feature,
                 valor_original, valor, direccion.
        tono: "campesino" o "institucional".

    Returns:
        str: Descripción formateada de la feature. Nunca lanza excepción.
    """
    if not feature:
        return "factor desconocido: sin dato"

    # Nombre: nombre_amigable > feature_id > feature > fallback
    nombre = (
        feature.get("nombre_amigable")
        or feature.get("feature_id")
        or feature.get("feature")
        or "factor desconocido"
    )

    # Valor: valor_original > valor > None
    valor = feature.get("valor_original")
    if valor is None:
        valor = feature.get("valor")

    # Formatear valor
    if valor is None:
        valor_str = "sin dato"
    elif isinstance(valor, float):
        valor_str = f"{valor:.2f}"
    else:
        valor_str = str(valor)

    direccion = (feature.get("direccion") or "").lower()

    if tono == "campesino":
        if "aumenta" in direccion:
            return f"{nombre} ({valor_str}) está aumentando el riesgo"
        elif "disminuye" in direccion:
            return f"{nombre} ({valor_str}) está ayudando a bajar el riesgo"
        else:
            return f"{nombre}: {valor_str}"
    else:
        if "aumenta" in direccion:
            return f"{nombre} ({valor_str}): factor que incrementa el riesgo"
        elif "disminuye" in direccion:
            return f"{nombre} ({valor_str}): factor que mitiga el riesgo"
        else:
            return f"{nombre}: {valor_str}"


def build_contexto_recuperado(
    prediccion: Optional[dict] = None,
    narrativa: Optional[str] = None,
    top_features: Optional[list] = None,
    serie_historica: Optional[list] = None,
    tono: str = "campesino"
) -> str:
    """
    Construye el texto de contexto recuperado para el prompt.

    Tolerante a None en todos los campos opcionales. Si todos son None o vacíos,
    retorna "No hay información disponible para este contexto."

    Args:
        prediccion: Dict con rendimiento_esperado, prob_riesgo_alto, etiqueta_riesgo.
        narrativa: Texto de narrativa de riesgo.
        top_features: Lista de features SHAP (máximo 3 se incluyen).
        serie_historica: Lista de dicts con año y rendimiento (últimos 3 con rendimiento no None).
        tono: "campesino" o "institucional".

    Returns:
        str: Texto formateado con toda la información recuperada.
    """
    partes = []

    # --- Predicción ---
    if prediccion is not None:
        rendimiento = prediccion.get("rendimiento_esperado")
        prob_riesgo = prediccion.get("prob_riesgo_alto")
        etiqueta = prediccion.get("etiqueta_riesgo") or ""

        if tono == "campesino":
            if rendimiento is not None:
                partes.append(f"RENDIMIENTO ESPERADO: {rendimiento:.2f} toneladas por hectárea")
            if etiqueta:
                semaforo = {"Alto": "🔴 alto", "Medio": "🟡 medio", "Bajo": "🟢 bajo"}.get(etiqueta, etiqueta)
                partes.append(f"NIVEL DE RIESGO: {semaforo}")
        else:
            if rendimiento is not None:
                partes.append(f"Rendimiento esperado: {rendimiento:.2f} t/ha")
            if prob_riesgo is not None:
                partes.append(f"Probabilidad de riesgo alto: {prob_riesgo:.1%}")
            if etiqueta:
                partes.append(f"Clasificación de riesgo: {etiqueta}")

    # --- Narrativa ---
    if narrativa and narrativa.strip():
        if tono == "campesino":
            partes.append(f"EXPLICACIÓN: {narrativa}")
        else:
            partes.append(f"Análisis: {narrativa}")

    # --- Top features (máximo 3) ---
    if top_features:
        if tono == "campesino":
            partes.append("FACTORES IMPORTANTES:")
        else:
            partes.append("Factores determinantes:")
        for i, feat in enumerate(top_features[:3], 1):
            partes.append(f"  {i}. {format_feature_for_prompt(feat, tono)}")

    # --- Serie histórica (últimos 3 con rendimiento no None) ---
    if serie_historica:
        registros_validos = [s for s in serie_historica if s.get("rendimiento") is not None]
        ultimos = registros_validos[-3:] if len(registros_validos) >= 3 else registros_validos
        if ultimos:
            if tono == "campesino":
                partes.append("RENDIMIENTO DE AÑOS ANTERIORES:")
            else:
                partes.append("Serie histórica de rendimiento:")
            for s in ultimos:
                partes.append(f"  - {s.get('año')}: {s['rendimiento']:.2f} t/ha")

    return "\n".join(partes) if partes else "No hay información disponible para este contexto."


def build_prompt_conversacional(
    contexto_recuperado: "ContextoRecuperado",
    pregunta: str,
    tono: str = "campesino"
) -> dict:
    """
    Punto de entrada unificado para el prompt conversacional (C2.1).

    Orquesta build_contexto_recuperado, build_user_prompt y build_system_prompt.
    No lanza excepción si algún campo de contexto_recuperado es None.

    Args:
        contexto_recuperado: Instancia de ContextoRecuperado. El objeto en sí no puede ser None.
        pregunta: Pregunta del usuario. Si es None o vacía, usa "Sin pregunta especificada".
        tono: "campesino" o "institucional". Fallback a "campesino" si no reconocido.

    Returns:
        dict con claves "system" y "user", ambas strings no vacíos.
    """
    texto_contexto = build_contexto_recuperado(
        prediccion=contexto_recuperado.prediccion,
        narrativa=contexto_recuperado.narrativa,
        top_features=contexto_recuperado.top_features,
        serie_historica=contexto_recuperado.serie_historica,
        tono=tono,
    )
    system_prompt = build_system_prompt(tono)
    user_prompt = build_user_prompt(
        pregunta=pregunta,
        contexto=contexto_recuperado.contexto_efectivo or {},
        contexto_recuperado=texto_contexto,
        glosario_relevante="",
    )
    return {"system": system_prompt, "user": user_prompt}

# ---------------------------------------------------------------------------
# C2.2 — Plantilla de prompt para reporte institucional UMATA
# ---------------------------------------------------------------------------

def _build_encabezado_umata(
    municipio: Optional[str],
    cultivo: Optional[str],
    año: Optional[int]
) -> str:
    """
    Construye el encabezado institucional del reporte UMATA.

    Usa shared/dane_codes.py para obtener el departamento a partir del municipio.
    No lanza excepción si municipio es None o no está en dane_codes.

    Args:
        municipio: Nombre display del municipio (Title Case). Puede ser None.
        cultivo: Nombre del cultivo. Puede ser None.
        año: Año de referencia. Puede ser None.

    Returns:
        str: Encabezado formateado con 5 líneas.
    """
    from shared.dane_codes import get_codigo, DANE_TO_DEPT

    municipio_str = municipio or "Municipio no especificado"
    cultivo_str = cultivo or "Cultivo no especificado"
    año_str = str(año) if año is not None else "Año no especificado"
    departamento_str = "Departamento no disponible"

    if municipio:
        codigo = get_codigo(municipio)
        if codigo:
            departamento_str = DANE_TO_DEPT.get(codigo, "Departamento no disponible")
        else:
            logger.warning(f"[C2.2] Municipio '{municipio}' no encontrado en dane_codes")

    return (
        f"MUNICIPIO: {municipio_str}\n"
        f"DEPARTAMENTO: {departamento_str}\n"
        f"CULTIVO: {cultivo_str}\n"
        f"AÑO DE REFERENCIA: {año_str}\n"
        f"GENERADO POR: SiembraSegura IA"
    )


def build_prompt_reporte_umata(
    contexto_recuperado: "ContextoRecuperado",
    municipio: Optional[str] = None,
    cultivo: Optional[str] = None,
    año: Optional[int] = None
) -> dict:
    """
    Construye el prompt completo para generar un reporte institucional UMATA (C2.2).

    El system prompt instruye al LLM a generar un documento con 8 secciones fijas.
    El user prompt inyecta todos los datos disponibles del ContextoRecuperado.
    No lanza excepción si los campos opcionales son None.

    Args:
        contexto_recuperado: Instancia de ContextoRecuperado. El objeto en sí no puede ser None.
        municipio: Nombre display del municipio. Puede ser None.
        cultivo: Nombre del cultivo. Puede ser None.
        año: Año de referencia. Puede ser None.

    Returns:
        dict con claves "system" y "user", ambas strings no vacíos.
    """
    # --- Encabezado ---
    encabezado = _build_encabezado_umata(municipio, cultivo, año)

    # --- Sección predicción ---
    prediccion = contexto_recuperado.prediccion
    if prediccion is not None:
        rendimiento = prediccion.get("rendimiento_esperado")
        etiqueta = prediccion.get("etiqueta_riesgo")
        prob = prediccion.get("prob_riesgo_alto")
        lineas_pred = []
        if rendimiento is not None:
            lineas_pred.append(f"Rendimiento esperado: {rendimiento:.2f} t/ha")
        if etiqueta:
            lineas_pred.append(f"Clasificación de riesgo: {etiqueta}")
        if prob is not None:
            lineas_pred.append(f"Probabilidad de riesgo alto: {prob:.1%}")
        datos_prediccion = "\n".join(lineas_pred) if lineas_pred else "Predicción no disponible"
    else:
        datos_prediccion = "Predicción no disponible"

    # --- Sección factores SHAP (hasta 5) ---
    top_features = contexto_recuperado.top_features
    if top_features:
        lineas_feat = []
        for i, feat in enumerate(top_features[:5], 1):
            nombre = (
                feat.get("nombre_amigable")
                or feat.get("feature_id")
                or feat.get("feature")
                or "factor desconocido"
            )
            valor = feat.get("valor_original") or feat.get("valor")
            valor_str = f"{valor:.2f}" if isinstance(valor, float) else (str(valor) if valor is not None else "N/D")
            lineas_feat.append(f"  {i}. {nombre}: {valor_str}")
        datos_features = "\n".join(lineas_feat)
    else:
        datos_features = "Factores SHAP no disponibles"

    # --- Sección narrativa ---
    narrativa_str = contexto_recuperado.narrativa or "Análisis narrativo no disponible"

    # --- Sección histórica (últimos 3 años) ---
    serie = contexto_recuperado.serie_historica
    if serie:
        registros_validos = [s for s in serie if s.get("rendimiento") is not None]
        ultimos = registros_validos[-3:] if len(registros_validos) >= 3 else registros_validos
        if ultimos:
            lineas_hist = [f"  - {s.get('año')}: {s['rendimiento']:.2f} t/ha" for s in ultimos]
            serie_str = "\n".join(lineas_hist)
        else:
            serie_str = "Serie histórica no disponible"
    else:
        serie_str = "Serie histórica no disponible"

    # --- Fuentes ---
    fuentes = contexto_recuperado.fuentes or []
    fuentes_str = "\n".join(f"  - {f}" for f in fuentes) if fuentes else "  - No especificadas"

    user_prompt = f"""DATOS PARA EL REPORTE:

{encabezado}

PREDICCIÓN:
{datos_prediccion}

FACTORES DETERMINANTES (SHAP):
{datos_features}

ANÁLISIS DE RIESGO:
{narrativa_str}

SERIE HISTÓRICA:
{serie_str}

FUENTES UTILIZADAS:
{fuentes_str}

---
Genera el reporte institucional completo con las 8 secciones obligatorias."""

    return {"system": SYSTEM_PROMPT_REPORTE_UMATA, "user": user_prompt}

# ---------------------------------------------------------------------------
# C2.3 — Plantilla de prompt para comparación de cultivos
# ---------------------------------------------------------------------------

def _build_tabla_comparativa(contextos_por_cultivo: dict) -> str:
    """
    Construye una tabla de texto comparando los cultivos disponibles (C2.3).

    Usa CULTIVOS_MVP de shared/config.py para determinar el orden y los cultivos faltantes.
    Para cultivos sin datos en el dict, muestra "Sin datos disponibles".

    Args:
        contextos_por_cultivo: dict {cultivo: ContextoRecuperado}. Al menos una entrada.

    Returns:
        str: Tabla formateada con una fila por cultivo MVP.
    """
    from shared.config import CULTIVOS_MVP

    filas = []
    for cultivo in CULTIVOS_MVP:
        if cultivo in contextos_por_cultivo:
            ctx = contextos_por_cultivo[cultivo]
            pred = ctx.prediccion if ctx is not None else None

            if pred is not None:
                rendimiento = pred.get("rendimiento_esperado")
                etiqueta = pred.get("etiqueta_riesgo") or "N/D"
                rend_str = f"{rendimiento:.2f} t/ha" if rendimiento is not None else "N/D"
            else:
                rend_str = "N/D"
                etiqueta = "N/D"

            # Factor SHAP principal
            top_features = ctx.top_features if ctx is not None else None
            if top_features:
                feat = top_features[0]
                factor = (
                    feat.get("nombre_amigable")
                    or feat.get("feature_id")
                    or feat.get("feature")
                    or "N/D"
                )
            else:
                factor = "N/D"

            filas.append(
                f"{cultivo} | {rend_str} | Riesgo: {etiqueta} | Factor principal: {factor}"
            )
        else:
            filas.append(f"{cultivo} | Sin datos disponibles")

    return "\n".join(filas)


def build_prompt_comparacion_cultivos(
    contextos_por_cultivo: dict,
    municipio: Optional[str] = None,
    año: Optional[int] = None
) -> dict:
    """
    Construye el prompt completo para generar un ranking comparativo de cultivos (C2.3).

    Args:
        contextos_por_cultivo: dict con clave = nombre cultivo, valor = ContextoRecuperado.
                               Al menos una entrada requerida.
        municipio: Nombre display del municipio. Puede ser None.
        año: Año de referencia. Puede ser None.

    Returns:
        dict con claves "system" y "user", ambas strings no vacíos.

    Raises:
        ValueError: Si contextos_por_cultivo es None o vacío.
    """
    from shared.config import CULTIVOS_MVP

    if not contextos_por_cultivo:
        raise ValueError("[C2.3] contextos_por_cultivo no puede estar vacío")

    # Advertir sobre cultivos fuera del MVP
    for cultivo in contextos_por_cultivo:
        if cultivo not in CULTIVOS_MVP:
            logger.warning(f"[C2.3] Cultivo '{cultivo}' no está en CULTIVOS_MVP, se incluye de todas formas")

    municipio_str = municipio or "Municipio no especificado"
    año_str = str(año) if año is not None else "Año no especificado"

    # Tabla comparativa
    tabla = _build_tabla_comparativa(contextos_por_cultivo)

    # Nota de cultivos faltantes
    cultivos_faltantes = [c for c in CULTIVOS_MVP if c not in contextos_por_cultivo]
    if cultivos_faltantes:
        cultivos_con_datos = [c for c in CULTIVOS_MVP if c in contextos_por_cultivo]
        con_datos_str = ", ".join(cultivos_con_datos) if cultivos_con_datos else "ninguno"
        faltantes_str = ", ".join(cultivos_faltantes)
        nota_faltantes = (
            f"Nota: Solo se dispone de datos para {con_datos_str}. "
            f"{faltantes_str} no tienen datos disponibles."
        )
    else:
        nota_faltantes = ""

    # Narrativas por cultivo (máximo 2 oraciones por cultivo)
    narrativas_partes = []
    for cultivo, ctx in contextos_por_cultivo.items():
        if ctx is not None and ctx.narrativa:
            # Tomar máximo 2 oraciones
            oraciones = ctx.narrativa.replace(".", ". ").split(". ")
            oraciones = [o.strip() for o in oraciones if o.strip()]
            resumen = ". ".join(oraciones[:2])
            if resumen and not resumen.endswith("."):
                resumen += "."
            narrativas_partes.append(f"{cultivo}: {resumen}")

    narrativas_str = "\n".join(narrativas_partes) if narrativas_partes else "No hay narrativas disponibles."

    user_prompt = f"""COMPARACIÓN DE CULTIVOS PARA {municipio_str} — AÑO {año_str}

DATOS DISPONIBLES:
{tabla}

{nota_faltantes}

NARRATIVAS DE RIESGO:
{narrativas_str}

---
Genera el ranking comparativo con las 4 secciones obligatorias."""

    return {"system": SYSTEM_PROMPT_COMPARACION_CULTIVOS, "user": user_prompt}
