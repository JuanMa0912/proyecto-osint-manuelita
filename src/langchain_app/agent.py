"""
agent.py
--------
Agente conversacional de Manuelita S.A. — Módulo 2, Bloque 3.

Implementa DOS estrategias de routing:

1. HybridRouter (recomendado)
   Clasifica la pregunta por keywords antes de invocar herramientas.
   - Preguntas de datos exactos  → ManuelitaDatosEstructurados (0ms, sin LLM)
   - Preguntas abiertas/narrativas → ManuelitaRAG (embeddings + LLM)
   Ventaja: funciona con cualquier LLM, incluso modelos pequeños.

2. ReactAgent (demo académico)
   Agente ReAct de LangChain — el LLM razona sobre qué herramienta usar.
   Requiere un LLM capaz de seguir el formato Pensamiento/Acción/Observación.
   Recomendado con gemini-2.0-flash; puede fallar con modelos <7B.

Observabilidad (LangSmith — Bloque 5):
   Cuando LANGCHAIN_TRACING_V2=true y LANGCHAIN_API_KEY están en .env,
   LangSmith registra automáticamente TODAS las llamadas LangChain:
   embeddings, retrievers, LLM calls, cadenas y herramientas.
   El método ask() también usa @traceable para nombrar cada corrida.

Uso rápido:
    from src.langchain_app.agent import ManuelitaAgent
    agent = ManuelitaAgent(provider="local")
    result = agent.ask("¿Cuál es el NIT de Manuelita?")
    print(result["answer"])   # respuesta
    print(result["tool"])     # "estructurado" o "rag"
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent.parent
PROVIDER = os.getenv("LLM_PROVIDER", "gemini")

# ── Observabilidad con LangSmith ──────────────────────────────
# Se inicializa una sola vez al importar el módulo.
# Si LANGCHAIN_TRACING_V2=true en .env, todas las llamadas
# LangChain quedan automáticamente registradas en LangSmith.
from src.langchain_app.langsmith_setup import init_langsmith, get_traceable  # noqa: E402

_langsmith_status = init_langsmith()
_traceable = get_traceable()   # @traceable o no-op si no está instalado


# ─────────────────────────────────────────────────────────────
# Agente principal — ManuelitaAgent (HybridRouter)
# ─────────────────────────────────────────────────────────────

class ManuelitaAgent:
    """
    Agente conversacional con router híbrido.

    Combina la herramienta de datos estructurados (exacta, 0ms)
    con el motor RAG (flexible, corpus-based) eligiendo
    automáticamente la más adecuada para cada pregunta.

    Args:
        provider: "gemini" | "ollama" | "local"
        verbose:  mostrar trazas de decisión en consola
    """

    def __init__(self, provider: str = PROVIDER, verbose: bool = False):
        self.provider = provider
        self.verbose = verbose

        # ── Herramienta 1: Datos estructurados ────────────────
        from src.langchain_app.tools.structured_tool import ManuelitaStructuredTool
        self.structured = ManuelitaStructuredTool()

        # ── Herramienta 2: RAG ────────────────────────────────
        from src.langchain_app.rag_engine import ManuelitaRAG
        self.rag = ManuelitaRAG(provider=provider)

        if verbose:
            print(f"  [Agent] Inicializado — proveedor: {provider.upper()}")
            print(f"  [Agent] Herramientas: DatosEstructurados + RAG")

    # ── Router ────────────────────────────────────────────────

    # Palabras que indican preguntas narrativas/abiertas → siempre RAG
    _RAG_SIGNALS = {
        "valores", "cultura", "estrategia", "historia", "filosofia",
        "misión", "vision", "propósito", "proposito", "premios",
        "reconocimientos", "certificaciones", "comunidades", "impacto",
        "cómo", "como", "gestiona", "maneja", "describe", "explica",
        "cuéntame", "cuentame", "qué hace", "que hace", "por qué",
        "sostenibilidad ambiental", "sostenibilidad social",
        "gobierno corporativo", "talento humano", "buen gobierno",
    }

    def _route(self, question: str) -> tuple[str, str]:
        """
        Determina qué herramienta usar para la pregunta.

        Lógica de prioridad:
          1. Si la pregunta contiene señales narrativas → RAG
          2. Si la herramienta estructurada tiene una categoría → estructurado
          3. Por defecto → RAG

        Returns:
            ("structured", categoria) o ("rag", "corpus")
        """
        # Extraer solo la pregunta actual si viene enriquecida con historial
        q_for_routing = question
        if "[Pregunta actual]" in question:
            q_for_routing = question.split("[Pregunta actual]")[-1].strip()

        q_lower = q_for_routing.lower()

        # 1. Señales narrativas/abiertas → forzar RAG
        if any(signal in q_lower for signal in self._RAG_SIGNALS):
            return "rag", "corpus"

        # 2. Categoría estructurada detectada
        category = self.structured._detect_category(q_for_routing)
        if category != "general":
            return "structured", category

        # 3. Por defecto → RAG para preguntas abiertas
        return "rag", "corpus"

    # ── API pública ───────────────────────────────────────────

    @_traceable(name="manuelita_ask", tags=["modulo2", "hybrid_router"])
    def ask(self, question: str) -> dict[str, Any]:
        """
        Responde una pregunta eligiendo la herramienta más adecuada.

        LangSmith traza esta llamada automáticamente cuando
        LANGCHAIN_TRACING_V2=true — incluyendo el routing,
        la llamada al LLM o al JSON estructurado, y las fuentes.

        Args:
            question: pregunta en lenguaje natural

        Returns:
            dict con claves:
              - answer   : respuesta textual
              - tool     : "estructurado" o "rag"
              - category : categoría detectada
              - sources  : lista de fuentes usadas
              - tiempo_s : tiempo de respuesta
        """
        if not question or not question.strip():
            return {
                "answer": "Por favor escribe una pregunta.",
                "tool": None,
                "category": None,
                "sources": [],
                "tiempo_s": 0.0,
            }

        t0 = time.time()
        tool_name, category = self._route(question)

        if self.verbose:
            print(f"\n  [Router] '{question[:60]}...' → {tool_name.upper()} ({category})")

        if tool_name == "structured":
            answer = self.structured.query(question)
            sources = ["data/structured/manuelita_datos.json"]
        else:
            result = self.rag.answer_with_sources(question, k=6)
            answer = result["answer"]
            sources = result["sources"]

        elapsed = round(time.time() - t0, 3)

        if self.verbose:
            print(f"  [Agent] Respuesta en {elapsed}s — fuentes: {sources}")

        return {
            "answer": answer,
            "tool": "estructurado" if tool_name == "structured" else "rag",
            "category": category,
            "sources": sources,
            "tiempo_s": elapsed,
        }

    def ask_batch(self, questions: list[str]) -> list[dict]:
        """Responde múltiples preguntas en secuencia."""
        return [self.ask(q) for q in questions]


# ─────────────────────────────────────────────────────────────
# ReAct Agent — demo con LangChain AgentExecutor
# ─────────────────────────────────────────────────────────────

def build_react_agent(provider: str = PROVIDER, verbose: bool = True):
    """
    Construye un agente ReAct de LangChain con ambas herramientas.

    El LLM razona en formato Thought/Action/Observation para
    decidir qué herramienta usar y cómo combinar los resultados.

    NOTA: Requiere LLM con buena capacidad de razonamiento.
          Recomendado: gemini-2.0-flash.
          Puede fallar con modelos locales pequeños (<7B parámetros).

    Args:
        provider: "gemini" | "ollama" | "local"
        verbose:  mostrar trazas del agente

    Returns:
        AgentExecutor de LangChain listo para invocar con {"input": "..."}
    """
    from langchain.agents import AgentType, initialize_agent
    from src.langchain_app.tools.structured_tool import get_structured_tool
    from src.langchain_app.rag_engine import ManuelitaRAG, build_llm

    # Herramienta 1: datos estructurados
    structured_lc = get_structured_tool()

    # Herramienta 2: RAG como Tool de LangChain
    from langchain.tools import Tool
    rag = ManuelitaRAG(provider=provider)

    rag_lc = Tool(
        name="ManuelitaRAG",
        func=lambda q: rag.answer(q, k=6),
        description=(
            "Útil para preguntas abiertas, narrativas o de contexto sobre Manuelita S.A.: "
            "historia, estrategia, cultura corporativa, sostenibilidad detallada, "
            "premios, certificaciones, valores, y cualquier pregunta que no sea "
            "un dato exacto o cifra específica. "
            "NO usar para NIT, cifras financieras exactas, o datos de directivos — "
            "para eso usar ManuelitaDatosEstructurados."
        ),
    )

    tools = [structured_lc, rag_lc]
    llm = build_llm(provider)

    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=3,
    )
    return agent


# ─────────────────────────────────────────────────────────────
# Ejecución directa — prueba rápida
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    provider = sys.argv[1] if len(sys.argv) > 1 else PROVIDER
    print(f"\n{'='*55}")
    print(f"  AGENTE MANUELITA — proveedor: {provider.upper()}")
    print(f"{'='*55}")

    agent = ManuelitaAgent(provider=provider, verbose=True)

    preguntas = [
        "¿Cuál es el NIT de Manuelita?",
        "¿Quién es el presidente?",
        "¿Cuáles son los valores corporativos de Manuelita?",
        "¿Cuánto fue el EBITDA en 2023?",
        "¿En qué países opera Manuelita y qué hace en cada uno?",
    ]

    for q in preguntas:
        print(f"\n▶ {q}")
        r = agent.ask(q)
        print(f"  Herramienta : {r['tool'].upper()} ({r['category']})")
        print(f"  Respuesta   : {r['answer'][:200]}")
        print(f"  Fuentes     : {r['sources']}")
        print(f"  Tiempo      : {r['tiempo_s']}s")
