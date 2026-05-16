"""
rag_engine.py
-------------
Motor RAG (Retrieval-Augmented Generation) para Manuelita S.A. — Módulo 2.

Arquitectura:
  Corpus Markdown  →  Chunks  →  Embeddings  →  ChromaDB (persistente)
  Pregunta  →  Embedding  →  Búsqueda vectorial  →  Top-K chunks  →  LLM

Proveedores de embedding soportados:
  - "gemini"  → GoogleGenerativeAIEmbeddings  (text-embedding-004, gratuito)
  - "ollama"  → OllamaEmbeddings              (nomic-embed-text, local)

Uso rápido:
    from src.langchain_app.rag_engine import ManuelitaRAG

    rag = ManuelitaRAG(provider="gemini")   # construye o carga índice
    docs = rag.retrieve("¿Quién es el presidente?", k=4)
    print(docs[0].page_content)

    answer = rag.answer("¿Cuál es el NIT de Manuelita?")
    print(answer)
"""

from __future__ import annotations

import os
import re
import unicodedata
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter

load_dotenv()

# ──────────────────────────────────────────────────────────────────────────────
# Rutas
# ──────────────────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent
MARKDOWN_DIR = ROOT / "data_processed" / "markdown"
VECTORSTORE_DIR = ROOT / "data" / "vectorstore"

# ──────────────────────────────────────────────────────────────────────────────
# Configuración
# ──────────────────────────────────────────────────────────────────────────────
PROVIDER         = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_API_KEY   = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL     = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
GEMINI_EMBED     = os.getenv("GEMINI_EMBED", "models/gemini-embedding-001")

OLLAMA_BASE_URL  = "http://localhost:11434"
OLLAMA_MODEL     = os.getenv("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED     = "nomic-embed-text"            # pull con: ollama pull nomic-embed-text

# Embeddings locales (sin API) — sentence-transformers multilingüe
# Proveedor "local": usa este modelo para embeddings + Gemini para el LLM
LOCAL_EMBED_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

CHUNK_SIZE       = 500    # caracteres por chunk
CHUNK_OVERLAP    = 80     # solapamiento entre chunks
DEFAULT_K        = 5      # chunks a recuperar por consulta

COLLECTION_NAME  = "manuelita_corpus"

# Orden de prioridad de los archivos del corpus
PRIORITY_FILES = [
    "key_facts_manuelita.md",              # Hechos clave consolidados — máxima prioridad
    "oficial_perfil_manuelit.md",
    "financiero_supersociedades_manuelit.md",
    "oficial_doc_manuelit.md",
    "oficial_pdf_sostenibilidad_manuelit.md",
    "red_social_linkedin_manuelit.md",
    "red_social_youtube_manuelit.md",
]


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de texto
# ──────────────────────────────────────────────────────────────────────────────

def _extract_frontmatter_as_text(text: str) -> tuple[str, str]:
    """
    Extrae el bloque YAML frontmatter y lo convierte en texto plano legible.
    Retorna (frontmatter_text, body_text).
    """
    match = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, flags=re.DOTALL)
    if not match:
        return "", text.strip()

    yaml_block = match.group(1)
    body = text[match.end():].strip()

    # Convertir YAML a texto plano (sin parsear YAML completo)
    lines = []
    for line in yaml_block.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Convertir clave: valor en frases legibles
        if ": " in line:
            key, _, val = line.partition(": ")
            key = key.lstrip("- ").strip()
            val = val.strip().strip("'\"")
            if val:
                lines.append(f"{key}: {val}")
        elif line.startswith("- "):
            lines.append(line[2:].strip().strip("'\""))

    frontmatter_text = "\n".join(lines)
    return frontmatter_text, body


def _strip_frontmatter(text: str) -> str:
    """Elimina el bloque YAML frontmatter (--- ... ---). Usado como fallback."""
    return re.sub(r"^---\s*\n.*?\n---\s*\n", "", text, count=1, flags=re.DOTALL).strip()


def _clean(text: str) -> str:
    return re.sub(r"\n{3,}", "\n\n", text).strip()


# ──────────────────────────────────────────────────────────────────────────────
# Carga y fragmentación del corpus
# ──────────────────────────────────────────────────────────────────────────────

def load_documents() -> List[Document]:
    """
    Carga los archivos Markdown del corpus y los convierte en Documents
    de LangChain con metadatos: source, file_type, priority.

    Returns:
        Lista de Document listos para ser fragmentados.
    """
    if not MARKDOWN_DIR.exists():
        raise FileNotFoundError(f"Directorio de corpus no encontrado: {MARKDOWN_DIR}")

    priority_map = {name: i for i, name in enumerate(PRIORITY_FILES)}
    paths = sorted(MARKDOWN_DIR.glob("*.md"), key=lambda p: priority_map.get(p.name, 99))

    docs: List[Document] = []
    for path in paths:
        if path.name == "_INDICE_MAESTRO.md":
            continue
        raw = path.read_text(encoding="utf-8")
        content = _clean(_strip_frontmatter(raw))
        if len(content) < 100:
            continue
        docs.append(Document(
            page_content=content,
            metadata={
                "source": path.name,
                "priority": priority_map.get(path.name, 99),
                "chars": len(content),
            },
        ))
        print(f"  Cargado: {path.name}  ({len(content):,} chars)")

    print(f"\n  Total: {len(docs)} documentos  "
          f"({sum(d.metadata['chars'] for d in docs):,} chars)\n")
    return docs


def split_documents(docs: List[Document]) -> List[Document]:
    """
    Divide los documentos en chunks usando RecursiveCharacterTextSplitter.
    Preserva los metadatos de origen en cada chunk.

    Returns:
        Lista de chunks como Documents.
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(docs)

    # Añadir índice de chunk al metadata
    source_counters: dict[str, int] = {}
    for chunk in chunks:
        src = chunk.metadata["source"]
        source_counters[src] = source_counters.get(src, 0) + 1
        chunk.metadata["chunk_index"] = source_counters[src]

    print(f"  Chunks generados: {len(chunks)}  "
          f"(tamaño aprox: {CHUNK_SIZE} chars, overlap: {CHUNK_OVERLAP})")
    return chunks


# ──────────────────────────────────────────────────────────────────────────────
# Embeddings
# ──────────────────────────────────────────────────────────────────────────────

def build_embeddings(provider: str = PROVIDER):
    """
    Construye el modelo de embeddings según el proveedor.

    Gemini:  text-embedding-004 — 768 dim (requiere GEMINI_API_KEY).
             Si falla con 404, usa: $env:LLM_PROVIDER="local"
    Ollama:  nomic-embed-text   — 768 dim, local.
             Instalar: ollama pull nomic-embed-text
    Local:   paraphrase-multilingual-MiniLM-L12-v2 — 384 dim, sin API.
             Usa Gemini como LLM pero embeddings locales vía sentence-transformers.
    """
    if provider == "gemini":
        from langchain_google_genai import GoogleGenerativeAIEmbeddings
        if not GEMINI_API_KEY:
            raise ValueError(
                "Falta GEMINI_API_KEY en .env\n"
                "Obtén tu clave en: https://aistudio.google.com/apikey"
            )
        print(f"  Embeddings: Google Gemini  ({GEMINI_EMBED})")
        return GoogleGenerativeAIEmbeddings(
            model=GEMINI_EMBED,
            google_api_key=GEMINI_API_KEY,
        )
    elif provider == "local":
        from langchain_community.embeddings import HuggingFaceEmbeddings
        print(f"  Embeddings: Local HuggingFace  ({LOCAL_EMBED_MODEL})")
        return HuggingFaceEmbeddings(
            model_name=LOCAL_EMBED_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
    else:  # ollama
        from langchain_ollama import OllamaEmbeddings
        print(f"  Embeddings: Ollama  ({OLLAMA_EMBED})")
        return OllamaEmbeddings(
            model=OLLAMA_EMBED,
            base_url=OLLAMA_BASE_URL,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Vector Store (ChromaDB)
# ──────────────────────────────────────────────────────────────────────────────

def build_vectorstore(chunks: List[Document], embeddings, persist_dir: Path):
    """Crea un vector store ChromaDB nuevo e indexa los chunks."""
    from langchain_chroma import Chroma

    print(f"  Indexando {len(chunks)} chunks en ChromaDB...")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(persist_dir),
    )
    print(f"  Índice guardado en: {persist_dir}")
    return vectorstore


def load_vectorstore(embeddings, persist_dir: Path):
    """Carga un vector store ChromaDB existente."""
    from langchain_chroma import Chroma

    print(f"  Cargando índice existente desde: {persist_dir}")
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(persist_dir),
    )


# ──────────────────────────────────────────────────────────────────────────────
# LLM
# ──────────────────────────────────────────────────────────────────────────────

def build_llm(provider: str = PROVIDER):
    """
    Construye el LLM según el proveedor.
    "local" usa embeddings locales pero Gemini como LLM (mejor calidad de respuesta).
    """
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=GEMINI_MODEL,
            google_api_key=GEMINI_API_KEY,
            temperature=0.1,
        )
    else:  # ollama o local — usa modelo local sin API
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=OLLAMA_MODEL,
            base_url=OLLAMA_BASE_URL,
            temperature=0.1,
            num_ctx=32768,
        )


# ──────────────────────────────────────────────────────────────────────────────
# Prompt RAG
# ──────────────────────────────────────────────────────────────────────────────

RAG_PROMPT_TEMPLATE = """\
Eres un asistente experto en Manuelita S.A., empresa agroindustrial colombiana \
fundada en 1864, con operaciones en Colombia, Perú y Chile en las plataformas \
de caña de azúcar, palma de aceite, acuicultura y frutas y hortalizas. \
También eres amable y conversacional.

### INSTRUCCIONES:
1. PREGUNTAS SOBRE LA EMPRESA: Responde basándote ÚNICAMENTE en el contexto recuperado.
   - Incluye cifras exactas y usa negritas (**dato**) para resaltar datos clave.
   - Si la respuesta NO está en el contexto, di exactamente: \
"No encontré información suficiente sobre ese tema."
   - No inventes datos, cifras ni hechos.
2. PREGUNTAS CONVERSACIONALES: Si el usuario te saluda, se despide, o pregunta \
por información personal que él mismo compartió (como su nombre), responde de \
forma natural y cordial usando el historial de conversación.
3. Si la pregunta incluye un historial de conversación previo, úsalo para \
resolver referencias como "allí", "eso", "ese país", etc.
4. Responde en español, de forma clara y estructurada. Máximo 3 párrafos \
salvo que la pregunta requiera una lista detallada.

### CONTEXTO RECUPERADO:
{context}

### PREGUNTA DEL USUARIO (puede incluir historial de conversación):
{question}

### RESPUESTA:"""

RAG_PROMPT = ChatPromptTemplate.from_template(RAG_PROMPT_TEMPLATE)


# ──────────────────────────────────────────────────────────────────────────────
# Clase principal
# ──────────────────────────────────────────────────────────────────────────────

class ManuelitaRAG:
    """
    Motor RAG para Manuelita S.A.

    Carga o construye el índice vectorial ChromaDB y expone:
      - retrieve(question, k)  → lista de Documents relevantes
      - answer(question, k)    → respuesta en texto usando LLM + RAG
      - get_retriever(k)       → retriever compatible con LangChain chains

    Args:
        provider:    "gemini" o "ollama"
        force_reindex: True para reconstruir el índice aunque ya exista
        persist_dir: directorio donde guardar ChromaDB
    """

    def __init__(
        self,
        provider: str = PROVIDER,
        force_reindex: bool = False,
        persist_dir: Path | None = None,
    ):
        self.provider = provider
        self.persist_dir = persist_dir or (VECTORSTORE_DIR / provider)
        self.persist_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n{'='*55}")
        print(f"  ManuelitaRAG — proveedor: {provider.upper()}")
        print(f"{'='*55}")

        self.embeddings = build_embeddings(provider)

        index_exists = (self.persist_dir / "chroma.sqlite3").exists()

        if index_exists and not force_reindex:
            self.vectorstore = load_vectorstore(self.embeddings, self.persist_dir)
            count = self.vectorstore._collection.count()
            print(f"  Índice cargado: {count} vectores")
        else:
            print("  Construyendo índice desde el corpus...")
            docs   = load_documents()
            chunks = split_documents(docs)
            self.vectorstore = build_vectorstore(chunks, self.embeddings, self.persist_dir)

        self.llm = build_llm(provider)
        self._chain = RAG_PROMPT | self.llm | StrOutputParser()
        print(f"{'='*55}\n")

    # ── API pública ──────────────────────────────────────────

    def retrieve(self, question: str, k: int = DEFAULT_K) -> List[Document]:
        """
        Recupera los k chunks más relevantes para la pregunta.

        Si la pregunta viene enriquecida con historial conversacional,
        extrae solo la pregunta actual para la búsqueda vectorial.

        Returns:
            Lista de Documents ordenados por relevancia.
        """
        search_query = question
        if "[Pregunta actual]" in question:
            search_query = question.split("[Pregunta actual]")[-1].strip()

        return self.vectorstore.similarity_search(search_query, k=k)

    def retrieve_with_scores(self, question: str, k: int = DEFAULT_K):
        """
        Recupera chunks con su puntaje de similitud.

        Si la pregunta viene enriquecida con historial conversacional,
        extrae solo la pregunta actual para la búsqueda vectorial.

        Returns:
            Lista de tuplas (Document, score).  Score más bajo = más similar.
        """
        search_query = question
        if "[Pregunta actual]" in question:
            search_query = question.split("[Pregunta actual]")[-1].strip()

        return self.vectorstore.similarity_search_with_score(search_query, k=k)

    def get_retriever(self, k: int = DEFAULT_K):
        """
        Devuelve un retriever compatible con LangChain chains y agentes.
        Útil para integrarlo con ConversationalRetrievalChain o Agent tools.
        """
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k},
        )

    def answer(self, question: str, k: int = DEFAULT_K) -> str:
        """
        Responde una pregunta usando el pipeline RAG completo:
        pregunta → recuperación → contexto → LLM → respuesta.

        Args:
            question: pregunta en lenguaje natural
            k:        número de chunks a recuperar

        Returns:
            Respuesta en texto generada por el LLM.
        """
        if not question or not question.strip():
            return "Por favor escribe una pregunta."

        docs = self.retrieve(question, k=k)
        context = "\n\n---\n\n".join(
            f"[Fuente: {d.metadata.get('source', '?')}]\n{d.page_content}"
            for d in docs
        )
        return self._chain.invoke({"context": context, "question": question})

    def answer_with_sources(self, question: str, k: int = DEFAULT_K) -> dict:
        """
        Versión extendida de answer() que también devuelve las fuentes usadas.

        Returns:
            dict con claves: 'answer', 'sources', 'chunks'
        """
        docs = self.retrieve(question, k=k)
        context = "\n\n---\n\n".join(
            f"[Fuente: {d.metadata.get('source', '?')}]\n{d.page_content}"
            for d in docs
        )
        answer = self._chain.invoke({"context": context, "question": question})
        sources = list({d.metadata.get("source", "?") for d in docs})
        return {
            "answer": answer,
            "sources": sources,
            "chunks": [d.page_content[:200] + "..." for d in docs],
        }


# ──────────────────────────────────────────────────────────────────────────────
# Ejecución directa — prueba rápida
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    provider = sys.argv[1] if len(sys.argv) > 1 else "gemini"
    force    = "--reindex" in sys.argv

    rag = ManuelitaRAG(provider=provider, force_reindex=force)

    preguntas = [
        "¿En qué año fue fundada Manuelita y dónde?",
        "¿Cuál es el NIT de la empresa?",
        "¿Quién es el presidente de Manuelita?",
        "¿Cuál es la meta de carbono para 2030?",
        "¿En qué países tiene operaciones Manuelita?",
    ]

    print("\n" + "="*55)
    print("  TEST RAG — 5 preguntas")
    print("="*55)

    for i, q in enumerate(preguntas, 1):
        print(f"\n[{i}] {q}")
        result = rag.answer_with_sources(q)
        print(f"    Respuesta: {result['answer'][:300]}")
        print(f"    Fuentes:   {', '.join(result['sources'])}")
