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

from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser

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
MODEL_NAME = "llama3.2:1b"    # Cambiar si usas otro modelo (ollama list para ver disponibles)
OLLAMA_BASE_URL = "http://localhost:11434"


class ManuelitaQASystem:
    """
    Sistema Q&A para Manuelita S.A. basado en LangChain + Ollama.
    El corpus completo se inyecta en el system prompt del LLM.
    """

    def __init__(self, model_name: str = MODEL_NAME):
        print(f"🚀 Iniciando ManuelitaQASystem con modelo: {model_name}")

        # Cargar corpus una sola vez al iniciar
        print("📚 Cargando corpus...")
        self.corpus = load_corpus()
        print(f"✅ Corpus cargado: {len(self.corpus):,} caracteres\n")

        # Inicializar LLM con Ollama
        self.llm = OllamaLLM(
            model=model_name,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,       # Baja temperatura = respuestas más precisas y consistentes
            num_ctx=32768,         # Ventana de contexto amplia para el corpus
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

        # --- Cadena 3: Q&A libre ---
        qa_prompt = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_with_corpus),
            HumanMessagePromptTemplate.from_template(QA_PROMPT),
        ])
        self.qa_chain = qa_prompt | self.llm | self.output_parser

    def get_resumen(self) -> str:
        """
        Genera un resumen ejecutivo completo de Manuelita S.A.

        Returns:
            Resumen estructurado con secciones: descripción, plataformas,
            geografía, cifras clave, finanzas, sostenibilidad.
        """
        print("📝 Generando resumen ejecutivo...")
        return self.resumen_chain.invoke({})

    def get_faq(self) -> str:
        """
        Genera 15 preguntas frecuentes sobre Manuelita S.A.

        Returns:
            Lista de 15 Q&A en formato: **P: pregunta** / R: respuesta
        """
        print("❓ Generando FAQ...")
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

        print(f"🔍 Respondiendo: {question[:80]}...")
        return self.qa_chain.invoke({"question": question})


# ============================================================
# EJECUCIÓN DIRECTA — prueba rápida
# ============================================================
if __name__ == "__main__":
    qa = ManuelitaQASystem()

    print("\n" + "="*60)
    print("TEST 1 — PREGUNTA SIMPLE")
    print("="*60)
    resp = qa.answer_question("¿En qué año fue fundada Manuelita y dónde?")
    print(resp)

    print("\n" + "="*60)
    print("TEST 2 — CIFRA FINANCIERA")
    print("="*60)
    resp = qa.answer_question("¿Cuál fue el EBITDA de Manuelita en 2023?")
    print(resp)

    print("\n" + "="*60)
    print("TEST 3 — PREGUNTA SIN RESPUESTA EN EL CORPUS")
    print("="*60)
    resp = qa.answer_question("¿Cuántos empleados tiene Manuelita en Chile?")
    print(resp)
