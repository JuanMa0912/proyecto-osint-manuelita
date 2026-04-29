"""
corpus_loader.py
----------------
Carga y consolida documentos Markdown y JSON procesados del corpus de
Manuelita S.A. en un unico string de texto limpio para usar como contexto
en el system prompt.

NO es un RAG: todo el texto cargado va directo al LLM como contexto.
"""

import json
import os
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent.parent
MARKDOWN_DIR = PROJECT_ROOT / "data_processed" / "markdown"
JSON_DIR = PROJECT_ROOT / "data_processed" / "json"
RAW_DIR = PROJECT_ROOT / "data_raw"

# Ajustable sin tocar codigo:
# PowerShell: $env:CORPUS_MAX_CHARS="180000"
DEFAULT_MAX_CHARS = int(os.getenv("CORPUS_MAX_CHARS", "180000"))
INCLUDE_JSON = os.getenv("CORPUS_INCLUDE_JSON", "true").lower() in {"1", "true", "yes", "si"}
INCLUDE_RAW_JSON = os.getenv("CORPUS_INCLUDE_RAW_JSON", "true").lower() in {"1", "true", "yes", "si"}

# Archivos priorizados. Despues de estos, el loader incluye automaticamente
# cualquier otro .md/.json disponible en data_processed.
CORPUS_FILES = [
    "oficial_perfil_manuelit.md",
    "financiero_supersociedades_manuelit.md",
    "oficial_doc_manuelit.md",
    "oficial_pdf_sostenibilidad_manuelit.md",
    "red_social_linkedin_manuelit.md",
    "red_social_youtube_manuelit.md",
    "_INDICE_MAESTRO.md",
]

JSON_CORPUS_FILES = [
    "normalized_manuelita_web_f2a1c3b8_2026041.json",
    "normalized_manuelita_social_linkedin_2026.json",
    "news_index.json",
]

RAW_JSON_CORPUS_FILES = [
    RAW_DIR / "social" / "social_summary.json",
    RAW_DIR / "social" / "linkedin_metadata.json",
    RAW_DIR / "social" / "facebook_metadata.json",
    RAW_DIR / "social" / "instagram_metadata.json",
    RAW_DIR / "social" / "youtube_metadata.json",
    RAW_DIR / "youtube" / "canal_manuelita.json",
    RAW_DIR / "youtube" / "videos_lista.json",
    RAW_DIR / "youtube" / "playlists.json",
    RAW_DIR / "youtube" / "canal_manuelita_fallback.json",
]


def _strip_yaml_frontmatter(text: str) -> str:
    """Elimina el bloque YAML frontmatter (entre --- y ---) del documento."""
    pattern = r"^---\s*\n.*?\n---\s*\n"
    return re.sub(pattern, "", text, count=1, flags=re.DOTALL).strip()


def _clean_text(text: str) -> str:
    """Limpieza basica del texto: elimina lineas vacias excesivas."""
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _ordered_files(directory: Path, priority_files: list[str], suffix: str) -> list[Path]:
    """Retorna archivos existentes, primero los priorizados y luego el resto."""
    if not directory.exists():
        return []

    priority = [directory / filename for filename in priority_files]
    priority = [path for path in priority if path.exists()]
    priority_names = {path.name for path in priority}

    discovered = sorted(
        path
        for path in directory.glob(f"*{suffix}")
        if path.name not in priority_names and path.name != ".gitkeep"
    )
    return priority + discovered


def _ordered_raw_json_files() -> list[Path]:
    """Retorna JSON raw priorizados y luego cualquier otro JSON en data_raw."""
    if not RAW_DIR.exists():
        return []

    priority = [path for path in RAW_JSON_CORPUS_FILES if path.exists()]
    priority_paths = {path.resolve() for path in priority}
    discovered = sorted(
        path
        for path in RAW_DIR.rglob("*.json")
        if path.resolve() not in priority_paths and path.name != ".gitkeep"
    )
    return priority + discovered


def _json_to_context(data, indent: int = 0) -> str:
    """Convierte JSON a texto legible para el LLM sin perder estructura."""
    prefix = "  " * indent

    if isinstance(data, dict):
        lines = []
        for key, value in data.items():
            if isinstance(value, (dict, list)):
                lines.append(f"{prefix}- {key}:")
                nested = _json_to_context(value, indent + 1)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{prefix}- {key}: {value}")
        return "\n".join(lines)

    if isinstance(data, list):
        lines = []
        for item in data:
            if isinstance(item, (dict, list)):
                lines.append(f"{prefix}-")
                nested = _json_to_context(item, indent + 1)
                if nested:
                    lines.append(nested)
            else:
                lines.append(f"{prefix}- {item}")
        return "\n".join(lines)

    return f"{prefix}{data}"


def _load_markdown_file(filepath: Path) -> str:
    raw_text = filepath.read_text(encoding="utf-8")
    return _clean_text(_strip_yaml_frontmatter(raw_text))


def _load_json_file(filepath: Path) -> str:
    data = json.loads(filepath.read_text(encoding="utf-8"))
    return _clean_text(_json_to_context(data))


def _append_section(corpus_parts: list[str], total_chars: int, filename: str, clean_text: str, max_chars: int) -> int:
    section = f"\n\n{'=' * 60}\n{filename.upper()}\n{'=' * 60}\n{clean_text}"

    if total_chars + len(section) <= max_chars:
        corpus_parts.append(section)
        print(f"OK Cargado: {filename} ({len(clean_text):,} chars)")
        return total_chars + len(section)

    remaining = max_chars - total_chars
    if remaining > 2000:
        corpus_parts.append(section[:remaining].rstrip())
        print(f"AVISO Cargado parcial: {filename} ({remaining:,} chars)")
        return max_chars

    print(f"AVISO Limite de contexto alcanzado. Omitiendo: {filename}")
    return total_chars


def load_corpus(max_chars: int = DEFAULT_MAX_CHARS) -> str:
    """
    Carga los documentos del corpus y los consolida en un string.

    Args:
        max_chars: limite de caracteres para no exceder la ventana de contexto.
                   Con num_ctx=65536, 180K chars es un punto de partida
                   conservador. Puedes ajustar CORPUS_MAX_CHARS.

    Returns:
        Texto limpio consolidado de todos los documentos posibles.
    """
    corpus_parts = []
    total_chars = 0

    source_files = [(path, "markdown") for path in _ordered_files(MARKDOWN_DIR, CORPUS_FILES, ".md")]
    if INCLUDE_JSON:
        source_files.extend((path, "json") for path in _ordered_files(JSON_DIR, JSON_CORPUS_FILES, ".json"))
    if INCLUDE_RAW_JSON:
        source_files.extend((path, "raw_json") for path in _ordered_raw_json_files())

    for filepath, source_type in source_files:
        if total_chars >= max_chars:
            break

        try:
            clean_text = _load_markdown_file(filepath) if source_type == "markdown" else _load_json_file(filepath)
        except Exception as exc:
            print(f"AVISO No se pudo cargar {filepath.name}: {exc}")
            continue

        total_chars = _append_section(corpus_parts, total_chars, filepath.name, clean_text, max_chars)

    corpus = "\n".join(corpus_parts)
    print(f"\nCorpus consolidado: {len(corpus):,} caracteres de {len(corpus_parts)} documentos")
    return corpus


def get_corpus_summary() -> list[dict]:
    """Retorna estadisticas del corpus sin cargarlo completo en el prompt."""
    stats = []
    source_files = [(path, "markdown") for path in _ordered_files(MARKDOWN_DIR, CORPUS_FILES, ".md")]
    if INCLUDE_JSON:
        source_files.extend((path, "json") for path in _ordered_files(JSON_DIR, JSON_CORPUS_FILES, ".json"))
    if INCLUDE_RAW_JSON:
        source_files.extend((path, "raw_json") for path in _ordered_raw_json_files())

    for filepath, source_type in source_files:
        try:
            clean = _load_markdown_file(filepath) if source_type == "markdown" else _load_json_file(filepath)
        except Exception:
            continue

        stats.append({
            "file": filepath.name,
            "type": source_type,
            "chars": len(clean),
            "words": len(clean.split()),
        })
    return stats


if __name__ == "__main__":
    corpus = load_corpus()
    preview = corpus[:500].encode("ascii", errors="replace").decode("ascii")
    print(f"\nPrimeros 500 caracteres:\n{preview}")
