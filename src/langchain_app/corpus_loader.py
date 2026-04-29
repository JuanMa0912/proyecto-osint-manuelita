"""
corpus_loader.py
----------------
Carga y consolida los documentos SMART MARKDOWN del corpus de Manuelita S.A.
en un único string de texto limpio para usar como contexto en el system prompt.

NO es un RAG — todo el texto va directo al LLM como contexto.
"""

import re
from pathlib import Path


# Ruta a los documentos del corpus
MARKDOWN_DIR = Path(__file__).parent.parent.parent / "data_processed" / "markdown"

# Documentos a incluir en el corpus (ordenados por prioridad)
CORPUS_FILES = [
    "oficial_perfil_manuelit.md",
    "financiero_supersociedades_manuelit.md",
    "oficial_doc_manuelit.md",
    "oficial_pdf_sostenibilidad_manuelit.md",
    "red_social_linkedin_manuelit.md",
    "red_social_youtube_manuelit.md",
]


def _strip_yaml_frontmatter(text: str) -> str:
    """Elimina el bloque YAML frontmatter (entre --- y ---) del documento."""
    pattern = r"^---\s*\n.*?\n---\s*\n"
    return re.sub(pattern, "", text, count=1, flags=re.DOTALL).strip()


def _clean_text(text: str) -> str:
    """Limpieza básica del texto: elimina líneas vacías excesivas."""
    # Reducir múltiples líneas en blanco a máximo 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def load_corpus(max_chars: int = 80000) -> str:
    """
    Carga todos los documentos del corpus y los consolida en un string.

    Args:
        max_chars: Límite de caracteres para no exceder la ventana de contexto
                   del LLM. Gemma3/Mistral soportan ~32K tokens (~128K chars).

    Returns:
        Texto limpio consolidado de todos los documentos.
    """
    corpus_parts = []
    total_chars = 0

    for filename in CORPUS_FILES:
        filepath = MARKDOWN_DIR / filename
        if not filepath.exists():
            print(f"⚠️  Archivo no encontrado: {filename}")
            continue

        raw_text = filepath.read_text(encoding="utf-8")
        clean_text = _strip_yaml_frontmatter(raw_text)
        clean_text = _clean_text(clean_text)

        # Agregar separador entre documentos
        section = f"\n\n{'='*60}\n{filename.upper()}\n{'='*60}\n{clean_text}"

        if total_chars + len(section) > max_chars:
            print(f"⚠️  Límite de contexto alcanzado. Omitiendo: {filename}")
            break

        corpus_parts.append(section)
        total_chars += len(section)
        print(f"✅ Cargado: {filename} ({len(clean_text):,} chars)")

    corpus = "\n".join(corpus_parts)
    print(f"\n📚 Corpus consolidado: {len(corpus):,} caracteres de {len(corpus_parts)} documentos")
    return corpus


def get_corpus_summary() -> dict:
    """Retorna estadísticas del corpus sin cargarlo completo."""
    stats = []
    for filename in CORPUS_FILES:
        filepath = MARKDOWN_DIR / filename
        if filepath.exists():
            text = filepath.read_text(encoding="utf-8")
            clean = _strip_yaml_frontmatter(text)
            stats.append({
                "file": filename,
                "chars": len(clean),
                "words": len(clean.split()),
            })
    return stats


if __name__ == "__main__":
    corpus = load_corpus()
    print(f"\nPrimeros 500 caracteres:\n{corpus[:500]}")
