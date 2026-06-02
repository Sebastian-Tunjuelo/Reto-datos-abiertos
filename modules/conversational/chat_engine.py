"""
Motor de chat que integra RAG con Google Gemini (rotación de keys)
y Anthropic Claude como fallback final.
"""
import logging
from typing import Optional

import google.generativeai as genai

from shared.config import LLM_API_KEYS, LLM_MODEL, ANTHROPIC_API_KEY, ANTHROPIC_MODEL
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

# Errores de Gemini que indican cuota agotada o key inválida → rotar a la siguiente
_GEMINI_QUOTA_ERRORS = (
    "RESOURCE_EXHAUSTED",
    "quota",
    "rate limit",
    "429",
    "INVALID_ARGUMENT",
    "API_KEY_INVALID",
)


def _is_quota_error(exc: Exception) -> bool:
    """Devuelve True si la excepción indica cuota agotada o key inválida."""
    msg = str(exc).lower()
    return any(kw.lower() in msg for kw in _GEMINI_QUOTA_ERRORS)


class ChatEngine:
    """
    Motor de conversación que usa RAG + Google Gemini para generar respuestas.

    Estrategia de LLM:
    1. Intenta cada key de Gemini en orden (rotación).
    2. Si todas las keys de Gemini fallan por cuota/error, usa Claude Haiku como fallback.
    3. Si Claude también falla, usa la respuesta local basada en RAG.
    """

    def __init__(self):
        if not LLM_API_KEYS:
            raise ValueError("LLM_API_KEY no está configurada en las variables de entorno")

        self.api_keys = LLM_API_KEYS
        self.model_name = LLM_MODEL or "gemini-2.0-flash"
        self.glosario = load_glosario()
        self.feature_mapping = get_feature_mapping()

        logger.info(
            f"ChatEngine inicializado — Gemini: {self.model_name} "
            f"({len(self.api_keys)} key(s)), "
            f"Fallback Claude: {'sí' if ANTHROPIC_API_KEY else 'no configurado'}"
        )

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------

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

        Returns:
            dict con claves:
                respuesta, tono_aplicado, contexto_usado, fuentes,
                reporte_disponible, tokens_usados, proveedor_llm
        """
        # 1. Recuperar contexto RAG
        logger.info(
            f"Recuperando contexto: municipio={municipio}, cultivo={cultivo}, año={año}"
        )
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

        # 3. Términos relevantes del glosario
        glosario_relevante = ""
        if self.glosario:
            glosario_relevante = extraer_terminos_glosario(
                self.glosario, pregunta, max_terminos=2
            )

        # 4. Construir prompts
        system_prompt = build_system_prompt(tono)
        user_prompt = build_user_prompt(
            pregunta=pregunta,
            contexto=contexto.contexto_efectivo,
            contexto_recuperado=contexto_recuperado,
            glosario_relevante=glosario_relevante
        )
        full_prompt = f"{system_prompt}\n\n{user_prompt}"

        # 5. Intentar Gemini con rotación de keys
        respuesta_texto, tokens_usados, proveedor = self._call_gemini(full_prompt)

        # 6. Fallback a Claude si Gemini falló completamente
        if respuesta_texto is None:
            respuesta_texto, tokens_usados, proveedor = self._call_claude(
                system_prompt, user_prompt
            )

        # 7. Fallback local si Claude también falló
        if respuesta_texto is None:
            logger.warning("Todos los LLM fallaron — usando respuesta local RAG")
            respuesta_texto = self._generate_fallback_response(
                pregunta=pregunta, contexto=contexto, tono=tono
            )
            tokens_usados = 0
            proveedor = "local_rag"

        # 8. Detectar intención de reporte
        reporte_disponible = self._detect_report_intent(pregunta)

        return {
            "respuesta": respuesta_texto,
            "tono_aplicado": tono,
            "contexto_usado": contexto.contexto_efectivo,
            "fuentes": contexto.fuentes if contexto.fuentes else ["conocimiento_general"],
            "reporte_disponible": reporte_disponible,
            "tokens_usados": tokens_usados,
            "proveedor_llm": proveedor,
        }

    # ------------------------------------------------------------------
    # Llamadas a LLM
    # ------------------------------------------------------------------

    def _call_gemini(self, full_prompt: str) -> tuple[Optional[str], int, str]:
        """
        Intenta generar respuesta con cada key de Gemini en orden.
        Devuelve (texto, tokens, proveedor) o (None, 0, "") si todas fallan.
        """
        for idx, api_key in enumerate(self.api_keys):
            try:
                genai.configure(api_key=api_key)
                model = genai.GenerativeModel(self.model_name)
                response = model.generate_content(
                    full_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.7,
                    )
                )
                texto = response.text.strip()

                # Extraer conteo de tokens si está disponible
                tokens = 0
                try:
                    usage = response.usage_metadata
                    if usage:
                        tokens = (
                            getattr(usage, "total_token_count", 0)
                            or (
                                getattr(usage, "prompt_token_count", 0)
                                + getattr(usage, "candidates_token_count", 0)
                            )
                        )
                except Exception:
                    pass

                key_label = f"key_{idx + 1}" if len(self.api_keys) > 1 else ""
                proveedor = f"gemini/{self.model_name}" + (f" ({key_label})" if key_label else "")
                logger.info(f"Gemini respondió con key #{idx + 1} — tokens: {tokens}")
                return texto, tokens, proveedor

            except Exception as exc:
                if _is_quota_error(exc):
                    logger.warning(
                        f"Gemini key #{idx + 1} agotada o inválida — "
                        f"{'probando siguiente' if idx + 1 < len(self.api_keys) else 'sin más keys'}"
                    )
                else:
                    logger.error(f"Error inesperado con Gemini key #{idx + 1}: {exc}")

        return None, 0, ""

    def _call_claude(
        self, system_prompt: str, user_prompt: str
    ) -> tuple[Optional[str], int, str]:
        """
        Llama a Anthropic Claude Haiku como fallback.
        Devuelve (texto, tokens, proveedor) o (None, 0, "") si falla.
        """
        if not ANTHROPIC_API_KEY:
            logger.warning("ANTHROPIC_API_KEY no configurada — saltando fallback Claude")
            return None, 0, ""

        try:
            import anthropic

            client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
            model = ANTHROPIC_MODEL or "claude-haiku-4-5"

            message = client.messages.create(
                model=model,
                max_tokens=8096,
                temperature=0.7,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            texto = message.content[0].text.strip()
            tokens = getattr(message.usage, "input_tokens", 0) + getattr(
                message.usage, "output_tokens", 0
            )
            proveedor = f"claude/{model}"
            logger.info(f"Claude respondió como fallback — tokens: {tokens}")
            return texto, tokens, proveedor

        except Exception as exc:
            logger.error(f"Error llamando a Claude: {exc}")
            return None, 0, ""

    # ------------------------------------------------------------------
    # Respuesta local (sin LLM)
    # ------------------------------------------------------------------

    _RECOMENDACION_KEYWORDS = [
        "recomien", "recomend", "qué hago", "qué hacer", "cómo reduc", "cómo mejor",
        "qué debo", "qué puedo", "consejos", "sugerencias", "acciones",
        "estrategia", "medidas", "mitigar", "mejorar", "aumentar rendimiento",
        "que hago", "que hacer", "como reduc", "como mejor", "que debo", "que puedo",
    ]

    def _es_pregunta_recomendacion(self, pregunta: str) -> bool:
        p = pregunta.lower()
        return any(kw in p for kw in self._RECOMENDACION_KEYWORDS)

    def _generate_fallback_response(self, pregunta: str, contexto, tono: str) -> str:
        """Respuesta basada en reglas cuando ningún LLM está disponible."""
        municipio = contexto.contexto_efectivo.get("municipio", "el municipio")
        cultivo = contexto.contexto_efectivo.get("cultivo", "el cultivo")

        if self._es_pregunta_recomendacion(pregunta) and contexto.prediccion:
            return self._generate_recomendacion(municipio, cultivo, contexto, tono)

        partes = []

        if contexto.prediccion:
            rend = contexto.prediccion.get("rendimiento_esperado")
            riesgo = contexto.prediccion.get("etiqueta_riesgo", "desconocido")
            rend_valido = isinstance(rend, (int, float)) and rend == rend

            if tono == "campesino":
                if rend_valido:
                    partes.append(
                        f"Para {cultivo} en {municipio}, el rendimiento esperado es de "
                        f"{rend:.2f} toneladas por hectárea. El nivel de riesgo es {riesgo.lower()}."
                    )
                else:
                    partes.append(
                        f"Para {cultivo} en {municipio}, el nivel de riesgo es {riesgo.lower()}."
                    )
            else:
                if rend_valido:
                    partes.append(
                        f"Predicción para {cultivo} en {municipio}: rendimiento esperado de "
                        f"{rend:.2f} t/ha con nivel de riesgo {riesgo}."
                    )
                else:
                    partes.append(
                        f"Predicción para {cultivo} en {municipio}: nivel de riesgo {riesgo}."
                    )

        if contexto.narrativa:
            partes.append(contexto.narrativa)

        if not contexto.narrativa and contexto.top_features:
            features_str = ", ".join(
                f"{f['feature']} ({f['valor']:.3f})"
                if isinstance(f.get("valor"), (int, float))
                else f["feature"]
                for f in contexto.top_features[:3]
            )
            if tono == "campesino":
                partes.append(f"Los factores más importantes son: {features_str}.")
            else:
                partes.append(f"Principales factores SHAP: {features_str}.")

        if contexto.serie_historica:
            ultimos = [
                f"{r['año']}: {r['rendimiento']:.2f} t/ha"
                for r in contexto.serie_historica[-3:]
                if r.get("rendimiento") is not None
            ]
            if ultimos:
                if tono == "campesino":
                    partes.append(f"En los últimos años el rendimiento fue: {', '.join(ultimos)}.")
                else:
                    partes.append(f"Serie histórica reciente: {', '.join(ultimos)}.")

        if partes:
            return " ".join(partes)

        if tono == "campesino":
            return (
                "No tengo información específica para su pregunta. "
                "Por favor indique municipio y cultivo para darle datos precisos."
            )
        return (
            "No hay datos disponibles para el contexto solicitado. "
            "Especifique municipio y cultivo para obtener información detallada."
        )

    def _generate_recomendacion(self, municipio: str, cultivo: str, contexto, tono: str) -> str:
        """Genera recomendaciones accionables basadas en el contexto RAG."""
        riesgo = contexto.prediccion.get("etiqueta_riesgo", "alto").lower()
        partes = []

        if tono == "campesino":
            partes.append(
                f"Para reducir el riesgo {riesgo} en {cultivo} en {municipio}, "
                f"le recomiendo lo siguiente:"
            )
        else:
            partes.append(
                f"Recomendaciones técnicas para mitigar el riesgo {riesgo} "
                f"en {cultivo} — {municipio}:"
            )

        recomendaciones = []

        if contexto.narrativa:
            narrativa = contexto.narrativa.lower()

            if "aptitud" in narrativa:
                if tono == "campesino":
                    recomendaciones.append(
                        "Aproveche las zonas de alta aptitud del municipio para concentrar "
                        "la siembra y obtener mejores rendimientos."
                    )
                else:
                    recomendaciones.append(
                        "Priorizar áreas con clasificación de aptitud alta según UPRA "
                        "para maximizar el potencial productivo."
                    )

            if "promedio 3 años" in narrativa or "rendimiento" in narrativa:
                if tono == "campesino":
                    recomendaciones.append(
                        "El rendimiento histórico es bajo. Considere mejorar las prácticas "
                        "de manejo del cultivo, fertilización y control de plagas."
                    )
                else:
                    recomendaciones.append(
                        "El bajo rendimiento histórico sugiere revisar el plan de manejo "
                        "agronómico: densidad de siembra, nutrición y sanidad vegetal."
                    )

            if "precipitaci" in narrativa or "lluvia" in narrativa or "clima" in narrativa:
                if tono == "campesino":
                    recomendaciones.append(
                        "Esté atento a las lluvias. En épocas secas, asegure riego "
                        "suplementario si es posible."
                    )
                else:
                    recomendaciones.append(
                        "Implementar sistemas de captación de agua o riego suplementario "
                        "para mitigar el impacto de anomalías de precipitación."
                    )

            if "fertilizante" in narrativa or "agroinsumo" in narrativa:
                if tono == "campesino":
                    recomendaciones.append(
                        "Los precios de fertilizantes están altos. Planifique la compra "
                        "con anticipación o explore alternativas orgánicas."
                    )
                else:
                    recomendaciones.append(
                        "El índice de agroinsumos indica presión de costos. "
                        "Evaluar sustitución parcial con abonos orgánicos o bioinsumos."
                    )

        if len(recomendaciones) < 2:
            if tono == "campesino":
                recomendaciones.append(
                    f"Consulte con la UMATA de {municipio} para un plan de manejo "
                    f"específico para {cultivo} en su zona."
                )
                recomendaciones.append(
                    "Lleve un registro de sus cosechas para identificar qué prácticas "
                    "funcionan mejor en su finca."
                )
            else:
                recomendaciones.append(
                    f"Se recomienda articular con la UMATA de {municipio} para diseñar "
                    f"un plan de manejo adaptado a las condiciones locales de {cultivo}."
                )
                recomendaciones.append(
                    "Implementar un sistema de monitoreo de rendimiento por lote "
                    "para identificar factores limitantes específicos."
                )

        for i, rec in enumerate(recomendaciones, 1):
            partes.append(f"{i}. {rec}")

        if contexto.serie_historica:
            ultimos = [
                f"{r['año']}: {r['rendimiento']:.2f} t/ha"
                for r in contexto.serie_historica[-3:]
                if r.get("rendimiento") is not None
            ]
            if ultimos:
                if tono == "campesino":
                    partes.append(f"(Rendimientos recientes: {', '.join(ultimos)})")
                else:
                    partes.append(f"Referencia histórica: {', '.join(ultimos)}.")

        return "\n".join(partes)

    def _detect_report_intent(self, pregunta: str) -> bool:
        keywords = [
            "reporte", "informe", "documento", "pdf",
            "imprimir", "descargar", "exportar",
            "resumen para", "presentar a", "mostrar a"
        ]
        return any(kw in pregunta.lower() for kw in keywords)


# ------------------------------------------------------------------
# Instancia global (lazy)
# ------------------------------------------------------------------

_engine: Optional[ChatEngine] = None


def get_chat_engine() -> ChatEngine:
    global _engine
    if _engine is None:
        _engine = ChatEngine()
    return _engine


def reset_chat_engine():
    global _engine
    _engine = None
