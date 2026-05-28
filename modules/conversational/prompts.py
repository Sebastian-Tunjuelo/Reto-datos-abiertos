"""
Plantillas de prompts para el asistente conversacional.
Diseñado para UMATAs, extensionistas y productores.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)

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

def build_system_prompt(tono: str = "campesino") -> str:
    """
    Construye el prompt del sistema según el tono solicitado.
    
    Args:
        tono: "campesino" o "institucional"
        
    Returns:
        str: System prompt correspondiente
    """
    if tono == "institucional":
        return SYSTEM_PROMPT_INSTITUCIONAL
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
        pregunta: Pregunta del usuario
        contexto: Dict con municipio, cultivo, año, escenario
        contexto_recuperado: Texto con información recuperada de predicciones/narrativas
        glosario_relevante: Términos del glosario relevantes a la pregunta
        
    Returns:
        str: Prompt completo del usuario
    """
    # Construir descripción del contexto
    contexto_desc = []
    if contexto.get("municipio"):
        contexto_desc.append(f"Municipio: {contexto['municipio']}")
    if contexto.get("cultivo"):
        contexto_desc.append(f"Cultivo: {contexto['cultivo']}")
    if contexto.get("año"):
        contexto_desc.append(f"Año: {contexto['año']}")
    if contexto.get("escenario"):
        contexto_desc.append(f"Escenario: {contexto['escenario']}")
    
    contexto_str = " | ".join(contexto_desc) if contexto_desc else "Sin contexto específico"
    
    prompt = f"""CONTEXTO DEL USUARIO:
{contexto_str}

INFORMACIÓN DISPONIBLE:
{contexto_recuperado if contexto_recuperado else "No se encontró información específica para este contexto."}
"""
    
    if glosario_relevante:
        prompt += f"""
TÉRMINOS RELEVANTES:
{glosario_relevante}
"""
    
    prompt += f"""
PREGUNTA DEL USUARIO:
{pregunta}

Responde basándote únicamente en la información disponible. Si falta información para dar una respuesta completa, indícalo claramente."""

    return prompt


def format_feature_for_prompt(feature: dict, tono: str = "campesino") -> str:
    """
    Formatea una feature SHAP para incluir en el contexto del prompt.
    
    Args:
        feature: Dict con feature_id, nombre_amigable, shap_value, direccion, valor_original
        tono: "campesino" o "institucional"
        
    Returns:
        str: Descripción formateada de la feature
    """
    nombre = feature.get("nombre_amigable", feature.get("feature_id", "factor"))
    valor = feature.get("valor_original")
    direccion = feature.get("direccion", "")
    
    # Formatear valor
    if valor is None:
        valor_str = "sin dato"
    elif isinstance(valor, float):
        valor_str = f"{valor:.2f}"
    else:
        valor_str = str(valor)
    
    if tono == "campesino":
        if "aumenta" in direccion.lower():
            return f"{nombre} ({valor_str}) está aumentando el riesgo"
        elif "disminuye" in direccion.lower():
            return f"{nombre} ({valor_str}) está ayudando a bajar el riesgo"
        else:
            return f"{nombre}: {valor_str}"
    else:
        if "aumenta" in direccion.lower():
            return f"{nombre} ({valor_str}): factor que incrementa el riesgo"
        elif "disminuye" in direccion.lower():
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
    
    Args:
        prediccion: Dict con rendimiento_esperado, prob_riesgo_alto, etiqueta_riesgo
        narrativa: Texto de narrativa de riesgo
        top_features: Lista de features SHAP
        serie_historica: Lista de dicts con años y rendimientos históricos
        tono: "campesino" o "institucional"
        
    Returns:
        str: Texto formateado con toda la información recuperada
    """
    partes = []
    
    # Predicción
    if prediccion:
        rendimiento = prediccion.get("rendimiento_esperado")
        prob_riesgo = prediccion.get("prob_riesgo_alto")
        etiqueta = prediccion.get("etiqueta_riesgo", "")

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
    
    # Narrativa
    if narrativa:
        if tono == "campesino":
            partes.append(f"EXPLICACIÓN: {narrativa}")
        else:
            partes.append(f"Análisis: {narrativa}")
    
    # Top features
    if top_features:
        if tono == "campesino":
            partes.append("FACTORES IMPORTANTES:")
        else:
            partes.append("Factores determinantes:")
        
        for i, feat in enumerate(top_features[:3], 1):
            partes.append(f"  {i}. {format_feature_for_prompt(feat, tono)}")
    
    # Serie histórica (últimos 3 años)
    if serie_historica and len(serie_historica) > 0:
        ultimos = serie_historica[-3:] if len(serie_historica) >= 3 else serie_historica
        if tono == "campesino":
            partes.append("RENDIMIENTO DE AÑOS ANTERIORES:")
            for s in ultimos:
                año = s.get("año")
                rend = s.get("rendimiento")
                if rend is not None:
                    partes.append(f"  - {año}: {rend:.2f} t/ha")
        else:
            partes.append("Serie histórica de rendimiento:")
            for s in ultimos:
                año = s.get("año")
                rend = s.get("rendimiento")
                if rend is not None:
                    partes.append(f"  - {año}: {rend:.2f} t/ha")
    
    return "\n".join(partes) if partes else ""
