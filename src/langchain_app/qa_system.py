"""
qa_system.py
------------
Motor del sistema Q&A de Manuelita S.A. usando LangChain.

Arquitectura (NO es RAG):
  Corpus markdown → System Prompt → LLM → Respuesta

Proveedores soportados:
  - "ollama"  → modelo local (sin internet, sin costo)
  - "gemini"  → Google Gemini API (gratis, 1M tokens contexto)

Tres funcionalidades:
  1. get_resumen()        → Resumen ejecutivo de la empresa
  2. get_faq()           → 15 preguntas frecuentes generadas
  3. answer_question()   → Q&A libre sobre la empresa

Configuración via variables de entorno (.env):
  LLM_PROVIDER=ollama|gemini
  OLLAMA_MODEL=llama3.2:1b
  OLLAMA_NUM_CTX=32768
  GEMINI_API_KEY=tu_key_aqui
  GEMINI_MODEL=gemini-1.5-flash
"""

import os
import re
import unicodedata

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from src.langchain_app.corpus_loader import load_corpus
from src.langchain_app.prompts import (
    FAQ_PROMPT,
    QA_PROMPT,
    RESUMEN_PROMPT,
    SYSTEM_PROMPT_BASE,
)

load_dotenv()

# ============================================================
# CONFIGURACIÓN — editar en .env o cambiar aquí directamente
# ============================================================
PROVIDER        = os.getenv("LLM_PROVIDER", "ollama")      # "ollama" | "gemini"

# Ollama (local)
MODEL_NAME      = os.getenv("OLLAMA_MODEL", "gemma3:1b")
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_NUM_CTX  = int(os.getenv("OLLAMA_NUM_CTX", "32768"))

# Gemini (API gratuita — Google AI Studio, NO Vertex AI)
# Modelos gratuitos: gemini-1.5-flash | gemini-2.0-flash | gemini-2.0-flash-lite
# Key en: https://aistudio.google.com/apikey  (sin tarjeta, sin facturación)
GEMINI_MODEL    = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")

# Modelos Gemini disponibles en capa gratuita (Google AI Studio)
GEMINI_FREE_MODELS = {
    "gemini-2.0-flash":      "Gemini 2.0 Flash — más reciente, gratis",
    "gemini-2.0-flash-lite": "Gemini 2.0 Flash Lite — más ligero, gratis",
    "gemini-1.5-flash":      "Gemini 1.5 Flash — estable, gratis",
    "gemini-1.5-flash-8b":   "Gemini 1.5 Flash 8B — ultra ligero, gratis",
}

RELEVANT_CONTEXT_CHARS = int(os.getenv("RELEVANT_CONTEXT_CHARS", "18000"))

STOPWORDS = {
    "a", "al", "con", "cual", "cuál", "de", "del", "el", "en", "es", "la",
    "las", "lo", "los", "me", "para", "por", "que", "qué", "quien", "quién",
    "se", "sobre", "su", "sus", "un", "una", "y",
}


def build_llm(provider: str = PROVIDER, model_name: str = MODEL_NAME,
              gemini_api_key: str = GEMINI_API_KEY):
    """
    Construye el LLM según el proveedor seleccionado.

    Args:
        provider: "ollama" para modelo local, "gemini" para Google Gemini API.
        model_name: Nombre del modelo Ollama (ignorado si provider=gemini).
        gemini_api_key: API key de Google AI Studio.

    Returns:
        Instancia del LLM compatible con LangChain ChatPromptTemplate.
    """
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        if not gemini_api_key:
            raise ValueError(
                "Falta GEMINI_API_KEY en el archivo .env\n"
                "Obtén tu key gratis en: https://aistudio.google.com/apikey"
            )
        print(f"Usando Google Gemini: {GEMINI_MODEL}")
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=gemini_api_key,
            temperature=0.1,
        )
    else:  # ollama (default)
        from langchain_ollama import ChatOllama
        print(f"Usando Ollama local: {model_name}")
        return ChatOllama(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            num_ctx=OLLAMA_NUM_CTX,
        )


class ManuelitaQASystem:
    """
    Sistema Q&A para Manuelita S.A. basado en LangChain.
    Soporta Ollama (local) y Google Gemini (API gratuita).
    El corpus se inyecta en el system prompt del LLM.
    """

    def __init__(self, provider: str = PROVIDER, model_name: str = MODEL_NAME,
                 gemini_api_key: str = GEMINI_API_KEY):
        self.provider = provider
        self.model_name = model_name if provider == "ollama" else GEMINI_MODEL

        print(f"Iniciando ManuelitaQASystem — proveedor: {provider.upper()}")
        print("Cargando corpus...")
        self.corpus = load_corpus()
        print(f"Corpus cargado: {len(self.corpus):,} caracteres\n")

        self.llm = build_llm(provider, model_name, gemini_api_key)
        self.output_parser = StrOutputParser()
        self._build_chains()

    def _build_chains(self):
        """Construye las cadenas LangChain para resumen y FAQ."""
        system_with_corpus = SYSTEM_PROMPT_BASE.format(corpus=self.corpus)

        resumen_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_with_corpus),
            HumanMessagePromptTemplate.from_template(RESUMEN_PROMPT),
        ])
        self.resumen_chain = resumen_prompt | self.llm | self.output_parser

        faq_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_with_corpus),
            HumanMessagePromptTemplate.from_template(FAQ_PROMPT),
        ])
        self.faq_chain = faq_prompt | self.llm | self.output_parser

    # ----------------------------------------------------------
    # Búsqueda léxica de contexto relevante
    # ----------------------------------------------------------

    def _normalize(self, text: str) -> str:
        text = unicodedata.normalize("NFKD", text.lower())
        return "".join(c for c in text if not unicodedata.combining(c))

    def _question_terms(self, question: str) -> set[str]:
        words = re.findall(r"[a-záéíóúñü0-9]+", question.lower())
        normalized = {self._normalize(w) for w in words}
        return {w for w in normalized if len(w) > 2 and w not in STOPWORDS}

    def _split_corpus_chunks(self) -> list[str]:
        chunks = re.split(r"\n={20,}\n|\n(?=#+\s)|\n\n+", self.corpus)
        return [c.strip() for c in chunks if len(c.strip()) > 80]

    def _get_relevant_context(self, question: str,
                               max_chars: int = RELEVANT_CONTEXT_CHARS) -> str:
        """Recupera fragmentos del corpus más relevantes para la pregunta."""
        terms = self._question_terms(question)
        if not terms:
            return self.corpus[:max_chars]

        scored = []
        for chunk in self._split_corpus_chunks():
            norm_chunk = self._normalize(chunk)
            score = sum(
                norm_chunk.count(t) * (3 if t in {"presidente", "fundador", "ebitda"} else 1)
                for t in terms
                if norm_chunk.count(t) > 0
            )
            if score:
                scored.append((score, len(chunk), chunk))

        scored.sort(key=lambda x: (-x[0], x[1]))

        selected, total = [], 0
        for _, _, chunk in scored:
            if total + len(chunk) <= max_chars:
                selected.append(chunk)
                total += len(chunk)

        return "\n\n---\n\n".join(selected) if selected else self.corpus[:max_chars]

    # ----------------------------------------------------------
    # API pública
    # ----------------------------------------------------------

    def get_resumen(self) -> str:
        """Genera un resumen ejecutivo completo de Manuelita S.A."""
        print("Generando resumen ejecutivo...")
        return self.resumen_chain.invoke({})

    def get_faq(self) -> str:
        """Genera 15 preguntas frecuentes sobre Manuelita S.A."""
        print("Generando FAQ...")
        return self.faq_chain.invoke({})

    def answer_question(self, question: str) -> str:
        """
        Responde una pregunta libre sobre Manuelita S.A.
        Usa búsqueda léxica para seleccionar el contexto más relevante.
        """
        if not question or not question.strip():
            return "Por favor escribe una pregunta."

        print(f"Respondiendo: {question[:80]}...")
        context = self._get_relevant_context(question)

        qa_prompt_text = QA_PROMPT + """

Nota de interpretacion:
- Si el usuario usa una expresion cercana como "ingenio Manuelita", acepta
  equivalencias razonables del contexto, como Manuelita S.A. o Manuelita
  Azucar y Energia, pero aclara el nombre exacto encontrado.
"""
        qa_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(
                SYSTEM_PROMPT_BASE.format(corpus=context)
            ),
            HumanMessagePromptTemplate.from_template(qa_prompt_text),
        ])
        chain = qa_prompt | self.llm | self.output_parser
        return chain.invoke({"question": question})


# ============================================================
# EJECUCIÓN DIRECTA — prueba rápida
# ============================================================
if __name__ == "__main__":
    qa = ManuelitaQASystem()

    print("\n" + "=" * 60)
    print("TEST 1 — PREGUNTA SIMPLE")
    print("=" * 60)
    print(qa.answer_question("¿En qué año fue fundada Manuelita y dónde?"))

    print("\n" + "=" * 60)
    print("TEST 2 — CIFRA FINANCIERA")
    print("=" * 60)
    print(qa.answer_question("¿Cuál fue el EBITDA de Manuelita en 2023?"))

    print("\n" + "=" * 60)
    print("TEST 3 — PREGUNTA SIN RESPUESTA")
    print("=" * 60)
    print(qa.answer_question("¿Cuántos empleados tiene Manuelita en Chile?"))
