"""
memory.py
---------
Módulo de memoria conversacional para el Agente Manuelita S.A. — Módulo 2, Bloque 4.

Implementa ConversationBufferWindowMemory de LangChain para mantener el historial
de los últimos N turnos de conversación. Esto permite preguntas de seguimiento
contextuales como:

    Usuario: ¿En qué países opera Manuelita?
    Agente:  Opera en Colombia, Perú y Chile.
    Usuario: ¿Y qué hace en Perú?          ← referencia resuelta con memoria
    Agente:  En Perú opera Agroindustrial Laredo (caña de azúcar)
             y Manuelita Frutas y Hortalizas (uva, espárragos, mandarinas).

Componentes:
  - ConversationMemory     : wrapper de ConversationBufferWindowMemory
  - build_memory()         : factory function con parámetros por defecto
  - ContextualAgent        : ManuelitaAgent extendido con soporte de memoria
  - format_history_prompt  : utilidad para serializar el historial en prompts

Uso básico:
    from src.langchain_app.memory import ContextualAgent

    agent = ContextualAgent(provider="local")
    r1 = agent.chat("¿En qué países opera Manuelita?")
    r2 = agent.chat("¿Y qué produce en Perú?")   # resuelve "Perú" con contexto
    print(r2["answer"])
    agent.reset()  # limpia el historial
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

# Número de turnos (pares pregunta-respuesta) que se mantienen en memoria
DEFAULT_WINDOW_SIZE = int(os.getenv("MEMORY_WINDOW", "5"))


# ─────────────────────────────────────────────────────────────
# Clase de Memoria
# ─────────────────────────────────────────────────────────────

class ConversationMemory:
    """
    Wrapper sobre ConversationBufferWindowMemory de LangChain.

    Mantiene los últimos `window_size` turnos de conversación
    (cada turno = 1 pregunta + 1 respuesta).

    La memoria se serializa como texto plano para ser inyectada
    en el prompt del agente.

    Args:
        window_size: número de turnos a conservar (por defecto 5)
    """

    def __init__(self, window_size: int = DEFAULT_WINDOW_SIZE):
        from langchain.memory import ConversationBufferWindowMemory

        self.window_size = window_size
        self._memory = ConversationBufferWindowMemory(
            k=window_size,
            memory_key="chat_history",
            return_messages=False,   # texto plano, más simple para inyección
            human_prefix="Usuario",
            ai_prefix="Asistente",
        )

    # ── API pública ────────────────────────────────────────────

    def save_turn(self, question: str, answer: str) -> None:
        """Guarda un turno completo (pregunta + respuesta) en la memoria."""
        self._memory.save_context(
            {"input": question},
            {"output": answer},
        )

    def get_history_text(self) -> str:
        """
        Devuelve el historial como texto formateado para insertar en prompts.

        Ejemplo de salida:
            Usuario: ¿En qué países opera Manuelita?
            Asistente: Opera en Colombia, Perú y Chile.
            Usuario: ¿Y qué produce en Perú?
            Asistente: En Perú opera Agroindustrial Laredo...
        """
        variables = self._memory.load_memory_variables({})
        return variables.get("chat_history", "").strip()

    def get_history_list(self) -> list[dict[str, str]]:
        """
        Devuelve el historial como lista de dicts para la UI.

        Returns:
            Lista de {"role": "user"|"assistant", "content": "..."}
        """
        text = self.get_history_text()
        if not text:
            return []

        turns = []
        for line in text.split("\n"):
            line = line.strip()
            if line.startswith("Usuario:"):
                turns.append({"role": "user", "content": line[len("Usuario:"):].strip()})
            elif line.startswith("Asistente:"):
                turns.append({"role": "assistant", "content": line[len("Asistente:"):].strip()})
        return turns

    def is_empty(self) -> bool:
        """True si no hay historial guardado."""
        return not bool(self.get_history_text())

    def turn_count(self) -> int:
        """Número de turnos almacenados actualmente."""
        history = self.get_history_list()
        user_turns = sum(1 for h in history if h["role"] == "user")
        return user_turns

    def reset(self) -> None:
        """Borra completamente el historial de conversación."""
        self._memory.clear()


# ─────────────────────────────────────────────────────────────
# Factory
# ─────────────────────────────────────────────────────────────

def build_memory(window_size: int = DEFAULT_WINDOW_SIZE) -> ConversationMemory:
    """
    Factory function — crea una instancia de ConversationMemory lista para usar.

    Args:
        window_size: turnos a mantener (default: 5, configurable con MEMORY_WINDOW env var)

    Returns:
        ConversationMemory configurada
    """
    return ConversationMemory(window_size=window_size)


# ─────────────────────────────────────────────────────────────
# Utilidad de prompt
# ─────────────────────────────────────────────────────────────

def format_history_prompt(history_text: str) -> str:
    """
    Envuelve el historial en un bloque para el prompt del agente.

    Si no hay historial, devuelve cadena vacía (no añade ruido al prompt).

    Args:
        history_text: texto del historial de ConversationMemory.get_history_text()

    Returns:
        Bloque formateado listo para concatenar al prompt, o "" si no hay historial.
    """
    if not history_text:
        return ""
    return (
        "\n\n[Historial de conversación reciente]\n"
        f"{history_text}\n"
        "[Fin del historial]\n"
    )


# ─────────────────────────────────────────────────────────────
# Agente con Memoria — ContextualAgent
# ─────────────────────────────────────────────────────────────

class ContextualAgent:
    """
    Extensión de ManuelitaAgent con memoria conversacional.

    Combina el router híbrido (HybridRouter) del Bloque 3
    con ConversationBufferWindowMemory del Bloque 4.

    Características:
    - Mantiene historial de los últimos N turnos
    - Inyecta el contexto histórico en las preguntas abiertas (RAG)
    - Para preguntas estructuradas (datos exactos) el historial no altera la respuesta
    - Soporta preguntas de seguimiento con pronombres y referencias ("¿y allí?", "¿cuándo fue eso?")
    - Método reset() para reiniciar la conversación

    Args:
        provider    : "gemini" | "ollama" | "local"
        window_size : turnos de historial a mantener (default 5)
        verbose     : mostrar trazas de decisión en consola

    Ejemplo:
        agent = ContextualAgent(provider="local", window_size=3)
        r1 = agent.chat("¿En qué países opera Manuelita?")
        r2 = agent.chat("¿Y qué produce en Perú?")
        print(r2["answer"])
        agent.reset()
    """

    def __init__(
        self,
        provider: str = PROVIDER,
        window_size: int = DEFAULT_WINDOW_SIZE,
        verbose: bool = False,
    ):
        self.provider = provider
        self.verbose = verbose

        # ── Agente base (Bloque 3) ────────────────────────────
        from src.langchain_app.agent import ManuelitaAgent
        self._agent = ManuelitaAgent(provider=provider, verbose=verbose)

        # ── Memoria (Bloque 4) ────────────────────────────────
        self.memory = build_memory(window_size=window_size)

        if verbose:
            print(f"  [ContextualAgent] Inicializado — proveedor: {provider.upper()}")
            print(f"  [ContextualAgent] Ventana de memoria: {window_size} turnos")

    # ── Construcción de pregunta contextualizada ──────────────

    def _enrich_question(self, question: str) -> str:
        """
        Enriquece la pregunta con el historial cuando es necesario.

        Si la pregunta contiene pronombres o referencias implícitas
        (y, allí, eso, ese, esa, ahí, también, además, cuándo fue, etc.)
        se añade el historial reciente al principio de la consulta
        para que el LLM pueda resolver la referencia.

        Solo aplica a preguntas que van a RAG (abiertas).
        Para datos estructurados el contexto no es necesario.
        """
        if self.memory.is_empty():
            return question

        # Señales de que la pregunta es de seguimiento / referencial
        _FOLLOW_UP_SIGNALS = {
            "¿y ", "y ", "¿también", "también", "además",
            "¿allí", "allí", "¿ahí", "ahí",
            "¿ese", "ese", "¿esa", "esa", "¿eso", "eso",
            "¿cuándo fue", "cuándo fue", "¿qué más", "qué más",
            "¿cómo lo", "cómo lo", "¿por qué", "por qué",
            "¿en ese", "en ese", "¿de ese", "de ese",
            "¿cuántos", "cuántos",  # puede ser follow-up
            "mencionaste", "dijiste", "antes", "anterior",
        }

        q_lower = question.lower().strip()
        is_follow_up = any(q_lower.startswith(sig) or sig in q_lower
                           for sig in _FOLLOW_UP_SIGNALS)

        # Preguntas muy cortas (<5 palabras) también son sospechosas de ser follow-up
        if len(question.split()) < 5:
            is_follow_up = True

        if is_follow_up:
            history = self.memory.get_history_text()
            enriched = (
                f"[Contexto de la conversación]\n{history}\n\n"
                f"[Pregunta actual]\n{question}"
            )
            if self.verbose:
                print(f"  [Memory] Follow-up detectado — inyectando {self.memory.turn_count()} turnos")
            return enriched

        return question

    # ── API pública ───────────────────────────────────────────

    def chat(self, question: str) -> dict[str, Any]:
        """
        Responde una pregunta manteniendo el contexto conversacional.

        Igual que ManuelitaAgent.ask() pero con memoria de historial.
        Las preguntas de seguimiento se resuelven con el contexto previo.

        Args:
            question: pregunta del usuario en lenguaje natural

        Returns:
            dict con claves:
              - answer      : respuesta textual
              - tool        : "estructurado" o "rag"
              - category    : categoría detectada
              - sources     : fuentes usadas
              - tiempo_s    : tiempo de respuesta
              - turn        : número de turno en la conversación
              - enriched    : True si la pregunta fue enriquecida con contexto
        """
        if not question or not question.strip():
            return {
                "answer": "Por favor escribe una pregunta.",
                "tool": None,
                "category": None,
                "sources": [],
                "tiempo_s": 0.0,
                "turn": self.memory.turn_count(),
                "enriched": False,
            }

        t0 = time.time()

        # Determinar si es follow-up ANTES de enriquecer
        enriched_question = self._enrich_question(question)
        was_enriched = enriched_question != question

        # Preguntar al agente base
        result = self._agent.ask(enriched_question)

        # Guardar en memoria (siempre la pregunta original, no la enriquecida)
        self.memory.save_turn(question, result["answer"])

        elapsed = round(time.time() - t0, 3)

        if self.verbose:
            turn_n = self.memory.turn_count()
            print(f"  [Memory] Turno {turn_n} guardado — historial: {turn_n} turnos")

        return {
            **result,
            "tiempo_s": elapsed,
            "turn": self.memory.turn_count(),
            "enriched": was_enriched,
        }

    def reset(self) -> None:
        """Reinicia la conversación — borra todo el historial."""
        self.memory.reset()
        if self.verbose:
            print("  [Memory] Historial borrado — nueva conversación")

    def get_history(self) -> list[dict[str, str]]:
        """Devuelve el historial como lista de dicts para la UI."""
        return self.memory.get_history_list()

    def summary(self) -> str:
        """Resumen del estado actual del agente (para debug)."""
        return (
            f"ContextualAgent("
            f"provider={self.provider}, "
            f"window={self.memory.window_size}, "
            f"turns={self.memory.turn_count()})"
        )


# ─────────────────────────────────────────────────────────────
# Ejecución directa — prueba rápida
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    provider = sys.argv[1] if len(sys.argv) > 1 else PROVIDER
    print(f"\n{'='*55}")
    print(f"  AGENTE CON MEMORIA — proveedor: {provider.upper()}")
    print(f"{'='*55}")

    agent = ContextualAgent(provider=provider, verbose=True)

    dialogo = [
        ("Turno 1 — dato exacto", "¿Cuál es el NIT de Manuelita?"),
        ("Turno 2 — dato exacto", "¿Quién es el presidente?"),
        ("Turno 3 — pregunta abierta", "¿En qué países opera Manuelita?"),
        ("Turno 4 — follow-up implícito", "¿Y qué produce en Perú?"),
        ("Turno 5 — follow-up con pronombre", "¿Qué certificaciones tiene?"),
        ("Turno 6 — dato exacto nuevo", "¿Cuántos empleados tiene?"),
    ]

    for label, pregunta in dialogo:
        print(f"\n── {label}")
        print(f"▶ {pregunta}")
        r = agent.chat(pregunta)
        print(f"  Herramienta : {r['tool'].upper()} ({r['category']})")
        print(f"  Enriquecida : {r['enriched']}")
        print(f"  Respuesta   : {r['answer'][:200]}")
        print(f"  Turno       : {r['turn']} | Tiempo: {r['tiempo_s']}s")

    print(f"\n  Estado final: {agent.summary()}")
    print(f"\n  Historial completo:")
    for h in agent.get_history():
        role_icon = "👤" if h["role"] == "user" else "🤖"
        print(f"  {role_icon} {h['content'][:80]}")
