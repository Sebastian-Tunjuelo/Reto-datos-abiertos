"""
Módulo conversacional de SiembraSegura IA.

Proporciona capacidades de chat basadas en RAG (Retrieval-Augmented Generation)
para responder preguntas sobre rendimiento agrícola, riesgo climático y recomendaciones.
"""

from modules.conversational.rag import (
    recuperar_contexto,
    load_predicciones_con_explicacion,
    load_feature_matrix,
    load_glosario,
    extraer_terminos_glosario,
    get_feature_mapping,
    ContextoRecuperado
)

from modules.conversational.prompts import (
    build_system_prompt,
    build_user_prompt,
    build_contexto_recuperado,
    format_feature_for_prompt
)

try:
    from modules.conversational.chat_engine import (
        ChatEngine,
        get_chat_engine,
        reset_chat_engine,
    )
    _CHAT_ENGINE_AVAILABLE = True
except ImportError:
    # openai u otras dependencias opcionales no instaladas
    ChatEngine = None  # type: ignore[assignment,misc]
    get_chat_engine = None  # type: ignore[assignment]
    reset_chat_engine = None  # type: ignore[assignment]
    _CHAT_ENGINE_AVAILABLE = False

__all__ = [
    # RAG
    "recuperar_contexto",
    "load_predicciones_con_explicacion",
    "load_feature_matrix",
    "load_glosario",
    "extraer_terminos_glosario",
    "get_feature_mapping",
    "ContextoRecuperado",
    
    # Prompts
    "build_system_prompt",
    "build_user_prompt",
    "build_contexto_recuperado",
    "format_feature_for_prompt",
    
    # Chat Engine
    "ChatEngine",
    "get_chat_engine",
    "reset_chat_engine"
]
