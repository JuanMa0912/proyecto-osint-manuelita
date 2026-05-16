"""
langsmith_setup.py
------------------
Configuración de observabilidad con LangSmith para el Agente Manuelita S.A.
Módulo 2 — Bloque 5 (Observabilidad).

LangSmith traza automáticamente todas las llamadas LangChain cuando las
variables de entorno LANGCHAIN_TRACING_V2 y LANGCHAIN_API_KEY están definidas.
No requiere modificar el código del agente: actúa como middleware.

Variables de entorno requeridas (.env):
    LANGCHAIN_TRACING_V2=true
    LANGCHAIN_API_KEY=<tu-api-key-de-smith.langchain.com>
    LANGCHAIN_PROJECT=manuelita-osint-ia   # nombre del proyecto en LangSmith
    LANGCHAIN_ENDPOINT=https://api.smith.langchain.com  # opcional, es el default

Qué se traza automáticamente:
    - Llamadas al LLM (Gemini, Ollama)
    - Cadenas LangChain (RetrievalQA, ConversationalChain)
    - Embeddings
    - Retrievers (ChromaDB)
    - Memoria (ConversationBufferWindowMemory)
    - Herramientas (ManuelitaStructuredTool, ManuelitaRAG)

Uso:
    from src.langchain_app.langsmith_setup import init_langsmith, get_run_url

    # Inicializar al arrancar la app (una sola vez)
    status = init_langsmith()
    print(status["message"])

    # Etiquetar una corrida específica
    from langsmith import traceable

    @traceable(name="chat_manuelita", tags=["demo", "streamlit"])
    def mi_funcion(pregunta: str) -> str:
        ...
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────────────────────
# Constantes de configuración
# ─────────────────────────────────────────────────────────────

LANGSMITH_PROJECT  = os.getenv("LANGCHAIN_PROJECT", "manuelita-osint-ia")
LANGSMITH_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGSMITH_ENABLED  = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGSMITH_API_KEY  = os.getenv("LANGCHAIN_API_KEY", "")


# ─────────────────────────────────────────────────────────────
# Inicialización
# ─────────────────────────────────────────────────────────────

def init_langsmith(
    project: str | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """
    Inicializa y verifica la conexión con LangSmith.

    Establece las variables de entorno necesarias y verifica
    que el SDK de LangSmith esté disponible.

    Args:
        project: nombre del proyecto en LangSmith (default: LANGCHAIN_PROJECT env var)
        tags:    etiquetas adicionales para todas las trazas de esta sesión

    Returns:
        dict con:
          - enabled  (bool): True si LangSmith está activo
          - project  (str):  nombre del proyecto
          - endpoint (str):  URL del endpoint
          - message  (str):  mensaje de estado para logs
          - dashboard_url (str): URL del dashboard en LangSmith
    """
    _project = project or LANGSMITH_PROJECT

    # Asegurarse de que las variables estén en el entorno del proceso
    if LANGSMITH_API_KEY:
        os.environ.setdefault("LANGCHAIN_API_KEY", LANGSMITH_API_KEY)
    os.environ.setdefault("LANGCHAIN_PROJECT", _project)
    os.environ.setdefault("LANGCHAIN_ENDPOINT", LANGSMITH_ENDPOINT)

    if not LANGSMITH_ENABLED:
        return {
            "enabled": False,
            "project": _project,
            "endpoint": LANGSMITH_ENDPOINT,
            "message": (
                "LangSmith DESACTIVADO — "
                "establece LANGCHAIN_TRACING_V2=true en .env para activarlo"
            ),
            "dashboard_url": "",
        }

    if not LANGSMITH_API_KEY:
        return {
            "enabled": False,
            "project": _project,
            "endpoint": LANGSMITH_ENDPOINT,
            "message": (
                "LangSmith: falta LANGCHAIN_API_KEY en .env — "
                "obtén tu key en https://smith.langchain.com"
            ),
            "dashboard_url": "",
        }

    # Verificar que el SDK esté instalado
    try:
        from langsmith import Client  # noqa: F401
        sdk_ok = True
    except ImportError:
        return {
            "enabled": False,
            "project": _project,
            "endpoint": LANGSMITH_ENDPOINT,
            "message": "LangSmith SDK no instalado — ejecuta: uv add langsmith",
            "dashboard_url": "",
        }

    dashboard_url = f"https://smith.langchain.com/o/projects/{_project}"

    return {
        "enabled": True,
        "project": _project,
        "endpoint": LANGSMITH_ENDPOINT,
        "message": (
            f"LangSmith ACTIVO — proyecto: '{_project}' | "
            f"dashboard: {dashboard_url}"
        ),
        "dashboard_url": dashboard_url,
    }


# ─────────────────────────────────────────────────────────────
# Decorador @traceable para funciones clave
# ─────────────────────────────────────────────────────────────

def get_traceable():
    """
    Devuelve el decorador @traceable de LangSmith si está disponible,
    o un no-op decorador si LangSmith no está instalado.

    Uso:
        traceable = get_traceable()

        @traceable(name="mi_funcion", tags=["modulo2"])
        def mi_funcion(pregunta: str) -> str:
            ...

    Esto garantiza que el código funcione incluso sin LangSmith instalado.
    """
    try:
        from langsmith import traceable
        return traceable
    except ImportError:
        # No-op decorator cuando LangSmith no está disponible
        def _noop_traceable(*args, **kwargs):
            def decorator(fn):
                return fn
            # Soporta @traceable y @traceable(name="...")
            if args and callable(args[0]):
                return args[0]
            return decorator
        return _noop_traceable


# ─────────────────────────────────────────────────────────────
# Utilidades de estado
# ─────────────────────────────────────────────────────────────

def is_tracing_enabled() -> bool:
    """True si LangSmith está activo y configurado correctamente."""
    return LANGSMITH_ENABLED and bool(LANGSMITH_API_KEY)


def get_project_name() -> str:
    """Nombre del proyecto LangSmith configurado."""
    return LANGSMITH_PROJECT


def get_dashboard_url() -> str:
    """URL del dashboard de trazas en LangSmith."""
    if not is_tracing_enabled():
        return ""
    return f"https://smith.langchain.com/o/projects/{LANGSMITH_PROJECT}"


def langsmith_status_badge() -> str:
    """
    Devuelve un string de estado formateado para mostrar en la UI de Streamlit.

    Returns:
        Markdown string con badge de estado (verde si activo, gris si inactivo)
    """
    if is_tracing_enabled():
        url = get_dashboard_url()
        return (
            f":green[🔍 LangSmith activo] — "
            f"[ver trazas]({url})"
        )
    return ":gray[🔍 LangSmith inactivo]"


# ─────────────────────────────────────────────────────────────
# Ejecución directa — prueba de conexión
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n" + "=" * 55)
    print("  VERIFICACIÓN LANGSMITH — Manuelita S.A.")
    print("=" * 55)

    status = init_langsmith()
    print(f"\n  Estado   : {'ACTIVO ✓' if status['enabled'] else 'INACTIVO ✗'}")
    print(f"  Proyecto : {status['project']}")
    print(f"  Endpoint : {status['endpoint']}")
    print(f"  Mensaje  : {status['message']}")

    if status["enabled"]:
        print(f"\n  Dashboard: {status['dashboard_url']}")
        print("\n  Realizando una traza de prueba...")

        traceable = get_traceable()

        @traceable(name="test_manuelita_langsmith", tags=["test", "modulo2"])
        def dummy_query(pregunta: str) -> str:
            """Función de prueba para verificar que las trazas llegan a LangSmith."""
            return f"Respuesta de prueba para: {pregunta}"

        resultado = dummy_query("¿Cuál es el NIT de Manuelita?")
        print(f"  Resultado: {resultado}")
        print("\n  ✓ Verifica la traza en el dashboard de LangSmith.")
    else:
        print("\n  Para activar LangSmith:")
        print("  1. Crea una cuenta en https://smith.langchain.com")
        print("  2. Genera un API key en Settings → API Keys")
        print("  3. Agrega al .env:")
        print("       LANGCHAIN_TRACING_V2=true")
        print("       LANGCHAIN_API_KEY=tu-api-key")
        print("       LANGCHAIN_PROJECT=manuelita-osint-ia")
        print("  4. Reinicia la app: streamlit run app.py")

    print()
