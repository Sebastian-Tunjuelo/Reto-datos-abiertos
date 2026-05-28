"""
Motor de chat que integra RAG con Google Gemini para generar respuestas.
"""
import logging
from typing import Optional

import google.generativeai as genai

from shared.config import LLM_API_KEY, LLM_MODEL
from modules.conversational.rag import (
    recuperar_contexto,
    extraer_terminos_glosario,
    load_glosario,
    get_feature_mapping
)
from modules.conversational.prompts import (
    build_system_prompt,
    build_user_prompt,
    build_contexto_recuperado
)

logger = logging.getLogger(__name__)


class ChatEngine:
    """
    Motor de conversación que usa RAG + Google Gemini para generar respuestas.
    """

    def __init__(self):
        """Inicializa el cliente de Gemini."""
        if not LLM_API_KEY:
            raise ValueError("LLM_API_KEY no está configurada en las variables de entorno")

        genai.configure(api_key=LLM_API_KEY)
        self.model_name = LLM_MODEL or "gemini-1.5-flash"
        self.model = genai.GenerativeModel(self.model_name)
        self.glosario = load_glosario()
        self.feature_mapping = get_feature_mapping()

        logger.info(f"ChatEngine inicializado con modelo Gemini: {self.model_name}")

    def chat(
        self,
        pregunta: str,
        municipio: Optional[str] = None,
        cultivo: Optional[str] = None,
        año: Optional[int] = None,
        escenario: Optional[str] = None,
        tono: str = "campesino"
    ) -> dict:
        """
        Genera una respuesta conversacional basada en contexto recuperado.

        Args:
            pregunta: Pregunta del usuario
            municipio: Nombre o código DANE del municipio
            cultivo: Nombre del cultivo
            año: Año de referencia
            escenario: Escenario de simulación
            tono: Tono de la respuesta (campesino o institucional)

        Returns:
            dict con claves: respuesta, tono_aplicado, contexto_usado, fuentes, reporte_disponible
        """
        # 1. Recuperar contexto
        logger.info(f"Recuperando contexto para: municipio={municipio}, cultivo={cultivo}, año={año}")
        contexto = recuperar_contexto(
            municipio=municipio,
            cultivo=cultivo,
            año=año,
            escenario=escenario,
            tono=tono
        )

        # 2. Construir texto de contexto recuperado
        contexto_recuperado = build_contexto_recuperado(
            prediccion=contexto.prediccion,
            narrativa=contexto.narrativa,
            top_features=contexto.top_features,
            serie_historica=contexto.serie_historica,
            tono=tono
        )

        # 3. Extraer términos relevantes del glosario
        glosario_relevante = ""
        if self.glosario:
            glosario_relevante = extraer_terminos_glosario(
                self.glosario,
                pregunta,
                max_terminos=2
            )

        # 4. Construir prompts
        system_prompt = build_system_prompt(tono)
        user_prompt = build_user_prompt(
            pregunta=pregunta,
            contexto=contexto.contexto_efectivo,
            contexto_recuperado=contexto_recuperado,
            glosario_relevante=glosario_relevante
        )

        # 5. Llamar a Gemini
        # Gemini no tiene un parámetro "system" separado en la API básica;
        # se concatena el system prompt al inicio del mensaje de usuario.
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            response = self.model.generate_content(
                full_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=500,
                    temperature=0.7,
                )
            )
            respuesta_texto = response.text.strip()

        except Exception as e:
            logger.error(f"Error llamando a Gemini: {e}")
            respuesta_texto = self._generate_fallback_response(
                pregunta=pregunta,
                contexto=contexto,
                tono=tono
            )

        # 6. Detectar si la pregunta menciona reportes
        reporte_disponible = self._detect_report_intent(pregunta)

        return {
            "respuesta": respuesta_texto,
            "tono_aplicado": tono,
            "contexto_usado": contexto.contexto_efectivo,
            "fuentes": contexto.fuentes if contexto.fuentes else ["conocimiento_general"],
            "reporte_disponible": reporte_disponible
        }

    def _generate_fallback_response(self, pregunta: str, contexto, tono: str) -> str:
        """Respuesta básica cuando Gemini no está disponible."""
        if contexto.prediccion:
            rend = contexto.prediccion.get("rendimiento_esperado")
            riesgo = contexto.prediccion.get("etiqueta_riesgo", "desconocido")
            municipio = contexto.contexto_efectivo.get("municipio", "el municipio")
            cultivo = contexto.contexto_efectivo.get("cultivo", "el cultivo")
            rend_str = f"{rend:.2f}" if isinstance(rend, (int, float)) else "N/A"

            if tono == "campesino":
                return (
                    f"Para {cultivo} en {municipio}, el rendimiento esperado es de "
                    f"{rend_str} toneladas por hectárea. El nivel de riesgo es {riesgo.lower()}."
                )
            else:
                return (
                    f"Predicción para {cultivo} en {municipio}: rendimiento esperado de "
                    f"{rend_str} t/ha con nivel de riesgo {riesgo}."
                )

        if contexto.narrativa:
            return contexto.narrativa

        if tono == "campesino":
            return "No tengo información específica para su pregunta. Por favor indique municipio y cultivo para darle datos precisos."
        return "No hay datos disponibles para el contexto solicitado. Especifique municipio y cultivo para obtener información detallada."

    def _detect_report_intent(self, pregunta: str) -> bool:
        """Detecta si la pregunta sugiere intención de generar un reporte."""
        keywords = [
            "reporte", "informe", "documento", "pdf",
            "imprimir", "descargar", "exportar",
            "resumen para", "presentar a", "mostrar a"
        ]
        return any(kw in pregunta.lower() for kw in keywords)


# Instancia global del motor (lazy initialization)
_engine: Optional[ChatEngine] = None


def get_chat_engine() -> ChatEngine:
    """Obtiene la instancia global del motor de chat."""
    global _engine
    if _engine is None:
        _engine = ChatEngine()
    return _engine


def reset_chat_engine():
    """Resetea la instancia global del motor (útil para tests)."""
    global _engine
    _engine = None
