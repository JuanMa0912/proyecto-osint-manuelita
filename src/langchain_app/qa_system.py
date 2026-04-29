"""
qa_system.py
------------
Motor del sistema Q&A de Manuelita S.A. usando LangChain + Ollama.

Arquitectura (NO es RAG):
  Corpus markdown → System Prompt → LLM (Ollama local) → Respuesta

Tres funcionalidades:
  1. get_resumen()        → Resumen ejecutivo de la empresa
  2. get_faq()           → 15 preguntas frecuentes generadas
  3. answer_question()   → Q&A libre sobre la empresa
"""

import os
import re
import unicodedata

from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)

from src.langchain_app.corpus_loader import load_corpus
from src.langchain_app.prompts import (
    SYSTEM_PROMPT_BASE,
    RESUMEN_PROMPT,
    FAQ_PROMPT,
    QA_PROMPT,
)

# ============================================================
# CONFIGURACIÓN DEL MODELO
# Cambiar MODEL_NAME según el modelo que tengas en Ollama.
# Verificar modelos disponibles con: ollama list
# ============================================================
MODEL_NAME = "gemma2:latest"    # Cambiar si usas otro modelo (ollama list para ver disponibles)
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_NUM_CTX = int(os.getenv("OLLAMA_NUM_CTX", "65536"))
RELEVANT_CONTEXT_CHARS = int(os.getenv("RELEVANT_CONTEXT_CHARS", "18000"))


STOPWORDS = {
    "a", "al", "con", "cual", "cuál", "de", "del", "el", "en", "es", "la",
    "las", "lo", "los", "me", "para", "por", "que", "qué", "quien", "quién",
    "se", "sobre", "su", "sus", "un", "una", "y",
}


class ManuelitaQASystem:
    """
    Sistema Q&A para Manuelita S.A. basado en LangChain + Ollama.
    El corpus completo se inyecta en el system prompt del LLM.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"Iniciando ManuelitaQASystem con modelo: {model_name}")

        # Cargar corpus una sola vez al iniciar
        print("Cargando corpus...")
        self.corpus = load_corpus()
        print(f"Corpus cargado: {len(self.corpus):,} caracteres\n")

        # Inicializar LLM con Ollama
        self.llm = OllamaLLM(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,       # Baja temperatura = respuestas más precisas y consistentes
            num_ctx=OLLAMA_NUM_CTX,  # Ventana de contexto amplia para el corpus
        )

        self.output_parser = StrOutputParser()
        self._build_chains()

    def _build_chains(self):
        """Construye las cadenas LangChain para cada funcionalidad."""

        system_with_corpus = SYSTEM_PROMPT_BASE.format(corpus=self.corpus)

        # --- Cadena 1: Resumen ---
        resumen_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_with_corpus),
            HumanMessagePromptTemplate.from_template(RESUMEN_PROMPT),
        ])
        self.resumen_chain = resumen_prompt | self.llm | self.output_parser

        # --- Cadena 2: FAQ ---
        faq_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_with_corpus),
            HumanMessagePromptTemplate.from_template(FAQ_PROMPT),
        ])
        self.faq_chain = faq_prompt | self.llm | self.output_parser

    def _normalize(self, text: str) -> str:
        """Normaliza texto para busqueda simple por palabras clave."""
        text = unicodedata.normalize("NFKD", text.lower())
        text = "".join(char for char in text if not unicodedata.combining(char))
        return text

    def _question_terms(self, question: str) -> set[str]:
        words = re.findall(r"[a-záéíóúñü0-9]+", question.lower())
        normalized_words = {self._normalize(word) for word in words}
        return {word for word in normalized_words if len(word) > 2 and word not in STOPWORDS}

    def _split_corpus_chunks(self) -> list[str]:
        chunks = re.split(r"\n={20,}\n|\n(?=#+\s)|\n\n+", self.corpus)
        return [chunk.strip() for chunk in chunks if len(chunk.strip()) > 80]

    def _get_relevant_context(self, question: str, max_chars: int = RELEVANT_CONTEXT_CHARS) -> str:
        """
        Recupera fragmentos relevantes del corpus por coincidencia lexical.
        Esto evita que el modelo pierda respuestas puntuales dentro de un prompt largo.
        """
        terms = self._question_terms(question)
        if not terms:
            return self.corpus[:max_chars]

        scored_chunks = []
        for chunk in self._split_corpus_chunks():
            normalized_chunk = self._normalize(chunk)
            score = 0

            for term in terms:
                occurrences = normalized_chunk.count(term)
                if occurrences:
                    score += occurrences * (3 if term in {"presidente", "fundador", "ebitda"} else 1)

            if score:
                scored_chunks.append((score, len(chunk), chunk))

        scored_chunks.sort(key=lambda item: (-item[0], item[1]))

        selected = []
        total_chars = 0
        for _, _, chunk in scored_chunks:
            if total_chars + len(chunk) > max_chars:
                continue
            selected.append(chunk)
            total_chars += len(chunk)
            if total_chars >= max_chars:
                break

        if not selected:
            return self.corpus[:max_chars]

        return "\n\n---\n\n".join(selected)

    def get_resumen(self) -> str:
        """
        Genera un resumen ejecutivo completo de Manuelita S.A.

        Returns:
            Resumen estructurado con secciones: descripción, plataformas,
            geografía, cifras clave, finanzas, sostenibilidad.
        """
        print("Generando resumen ejecutivo...")
        return self.resumen_chain.invoke({})

    def get_faq(self) -> str:
        """
        Genera 15 preguntas frecuentes sobre Manuelita S.A.

        Returns:
            Lista de 15 Q&A en formato: **P: pregunta** / R: respuesta
        """
        print("Generando FAQ...")
        return self.faq_chain.invoke({})

    def answer_question(self, question: str) -> str:
        """
        Responde una pregunta libre sobre Manuelita S.A.

        Args:
            question: Pregunta del usuario en lenguaje natural.

        Returns:
            Respuesta basada únicamente en el corpus. Si no hay información,
            retorna mensaje estándar de "no tengo información".
        """
        if not question or not question.strip():
            return "Por favor escribe una pregunta."

        print(f"Respondiendo: {question[:80]}...")
        relevant_context = self._get_relevant_context(question)
        qa_prompt_text = QA_PROMPT + """

Nota de interpretacion:
- Si el usuario usa una expresion cercana como "ingenio Manuelita", acepta
  equivalencias razonables del contexto, como Manuelita S.A. o Manuelita
  Azucar y Energia, pero aclara el nombre exacto encontrado.
"""
        qa_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(SYSTEM_PROMPT_BASE.format(corpus=relevant_context)),
            HumanMessagePromptTemplate.from_template(qa_prompt_text),
        ])
        qa_chain = qa_prompt | self.llm | self.output_parser
        return qa_chain.invoke({"question": question})


# ============================================================
# EJECUCIÓN DIRECTA — prueba rápida
# ============================================================
if __name__ == "__main__":
    qa = ManuelitaQASystem()

    print("\n" + "="*60)
    print("TEST 1 - PREGUNTA SIMPLE")
    print("="*60)
    resp = qa.answer_question("¿En qué año fue fundada Manuelita y dónde?")
    print(resp)

    print("\n" + "="*60)
    print("TEST 2 - CIFRA FINANCIERA")
    print("="*60)
    resp = qa.answer_question("¿Cuál fue el EBITDA de Manuelita en 2023?")
    print(resp)

    print("\n" + "="*60)
    print("TEST 3 - PREGUNTA SIN RESPUESTA EN EL CORPUS")
    print("="*60)
    resp = qa.answer_question("¿Cuántos empleados tiene Manuelita en Chile?")
    print(resp)
