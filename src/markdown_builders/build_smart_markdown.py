"""
build_smart_markdown.py — Constructor de SMART MARKDOWN semántico para Manuelita.

Convierte documentos JSON normalizados en archivos Markdown enriquecidos
con YAML frontmatter, listos para:
  - RAG (Retrieval-Augmented Generation)
  - Indexación semántica con embeddings
  - Consultas con LangChain, LlamaIndex, Haystack
  - Análisis empresarial y minería de texto

Uso:
  python -m src.markdown_builders.build_smart_markdown
  python -m src.markdown_builders.build_smart_markdown --source-dir data_processed/json/
  python -m src.markdown_builders.build_smart_markdown --file json/pdf_sostenibilidad_2023_2024.json
"""

import argparse
from pathlib import Path
from typing import Optional
import yaml

from loguru import logger

from src.utils.config import paths_cfg
from src.utils.utils import load_json, now_iso, setup_logging, url_to_slug


# ============================================================
# MAPEADOR DE TIPOS DE DOCUMENTOS
# ============================================================

SOURCE_TYPE_LABELS = {
    "oficial": "Fuente Oficial",
    "prensa": "Prensa / Medios",
    "red_social": "Red Social",
    "tercero": "Fuente Tercero",
    "reseña": "Reseña / Opinión",
    "pdf": "Documento PDF",
    "wikipedia": "Wikipedia",
}

DOC_TYPE_ICONS = {
    "perfil": "🏢",
    "historia": "📅",
    "presencia": "🌎",
    "plataformas": "⚙️",
    "sostenibilidad": "🌱",
    "noticias": "📰",
    "noticia": "📰",
    "youtube": "🎬",
    "facebook": "👥",
    "instagram": "📸",
    "linkedin": "💼",
    "pdf": "📄",
    "wikipedia": "📚",
    "default": "📋",
}


# ============================================================
# GENERADORES DE SECCIONES
# ============================================================

def build_yaml_frontmatter(doc: dict) -> str:
    """
    Construye el YAML frontmatter semántico del documento.
    Optimizado para indexación RAG y consultas semánticas.
    """
    entities = doc.get("entities", {})
    topics = doc.get("topics", [])
    key_figures = doc.get("key_figures", {})

    # Tags enriquecidos para RAG
    tags = []
    tags.append("manuelita")
    tags.append(doc.get("source_type", ""))
    page_key = doc.get("page_key", doc.get("platform", ""))
    if page_key:
        tags.append(page_key)
    for t in topics[:5]:
        tags.append(t["topic"])
    tags = [t for t in tags if t]

    frontmatter = {
        "id": doc.get("id", ""),
        "company": "Manuelita S.A.",
        "source_type": doc.get("source_type", ""),
        "source_name": doc.get("source_name", ""),
        "source_url": doc.get("source_url", doc.get("url", "")),
        "page_title": (
            doc.get("metadata", {}).get("title") or
            doc.get("title", "") or
            doc.get("channel_info", {}).get("title", "")
        ),
        "captured_at": doc.get("captured_at", ""),
        "language": doc.get("language", "es"),
        "country": doc.get("country", "CO"),
        "confidence_score": doc.get("confidence_score", 0.5),
        "tags": tags,
        "entities": {
            "organizations": entities.get("organizations", [])[:10],
            "people": entities.get("people", [])[:5],
            "locations": entities.get("locations", [])[:10],
            "products": entities.get("products", [])[:5],
            "business_units": entities.get("business_units", []),
        },
        "topics": [t["topic"] for t in topics[:5]],
        "key_figures": key_figures,
        "document_type": doc.get("page_key", doc.get("platform", "documento")),
        "word_count": doc.get("word_count", 0),
    }

    # Añadir secciones detectadas si es PDF
    if doc.get("detected_sections"):
        frontmatter["detected_sections"] = doc["detected_sections"]

    yaml_str = yaml.dump(
        frontmatter,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=False,
        width=120,
    )
    return f"---\n{yaml_str}---\n"


def build_executive_summary(doc: dict) -> str:
    """
    Construye el resumen ejecutivo del documento.
    """
    source_label = SOURCE_TYPE_LABELS.get(doc.get("source_type", ""), "Fuente")
    page_key = doc.get("page_key", doc.get("platform", ""))
    icon = DOC_TYPE_ICONS.get(page_key, DOC_TYPE_ICONS["default"])

    title = (
        doc.get("metadata", {}).get("title") or
        doc.get("title") or
        doc.get("page_key", "Documento Manuelita")
    )

    lines = [f"# {icon} {title}\n"]

    # Breadcrumb de fuente
    url = doc.get("source_url", doc.get("url", ""))
    lines.append(f"> **{source_label}** — [{url}]({url})\n")
    lines.append(f"> Capturado: `{doc.get('captured_at', '')[:10]}` | "
                 f"Idioma: `{doc.get('language', 'es').upper()}` | "
                 f"Confianza: `{doc.get('confidence_score', 0)}`\n")
    lines.append("\n## Resumen ejecutivo\n")

    # Generar resumen automático desde el texto
    description = (
        doc.get("metadata", {}).get("description") or
        doc.get("metadata", {}).get("og_description") or
        doc.get("description", "")
    )

    if description:
        lines.append(f"{description}\n")
    else:
        # Usar primeras oraciones del texto
        text = doc.get("full_text", "") or doc.get("main_text", "") or doc.get("text", "")
        if text:
            first_paragraph = text.strip().split("\n\n")[0][:600]
            lines.append(f"{first_paragraph}...\n")

    return "\n".join(lines)


def build_key_data_section(doc: dict) -> str:
    """
    Construye la sección de datos clave extraídos.
    """
    lines = ["## Datos clave extraídos\n"]

    # Cifras numéricas detectadas
    key_figures = doc.get("key_figures", {})
    if key_figures:
        lines.append("### Cifras identificadas\n")
        figure_labels = {
            "produccion_azucar_ton": "Producción azúcar (toneladas)",
            "produccion_bioetanol_litros": "Producción bioetanol (litros)",
            "empleados": "Empleados / Colaboradores",
            "ingresos_millones": "Ingresos (millones)",
            "familias_beneficiadas": "Familias beneficiadas",
            "paises_exportacion": "Países de exportación",
            "años_historia": "Años de historia",
        }
        for key, value in key_figures.items():
            label = figure_labels.get(key, key)
            lines.append(f"- **{label}:** {value}")
        lines.append("")

    # Estadísticas del documento
    lines.append("### Estadísticas del documento\n")
    stats = []
    if doc.get("word_count"):
        stats.append(f"- **Palabras totales:** {doc['word_count']:,}")
    if doc.get("page_count"):
        stats.append(f"- **Páginas (PDF):** {doc['page_count']}")
    if doc.get("table_count") or len(doc.get("tables", [])):
        stats.append(f"- **Tablas detectadas:** {len(doc.get('tables', []))}")
    if doc.get("extraction_method"):
        stats.append(f"- **Método de extracción:** `{doc['extraction_method']}`")

    lines.extend(stats)
    lines.append("")

    # Unidades de negocio mencionadas
    biz_units = doc.get("entities", {}).get("business_units", [])
    if biz_units:
        lines.append("### Unidades de negocio mencionadas\n")
        for unit in biz_units:
            lines.append(f"- {unit}")
        lines.append("")

    # Para YouTube: estadísticas del canal
    if doc.get("platform") == "youtube" and doc.get("channel_info"):
        ch = doc["channel_info"]
        stats_ch = ch.get("statistics", {})
        lines.append("### Estadísticas del canal YouTube\n")
        lines.append(f"- **Suscriptores:** {stats_ch.get('subscriber_count', 'N/A')}")
        lines.append(f"- **Total de videos:** {stats_ch.get('video_count', 'N/A')}")
        lines.append(f"- **Vistas totales:** {stats_ch.get('view_count', 'N/A')}")
        lines.append("")

    return "\n".join(lines)


def build_structured_content(doc: dict) -> str:
    """
    Construye la sección de contenido estructurado del documento.
    """
    lines = ["## Contenido estructurado\n"]

    # Encabezados del documento (para páginas web)
    headings = doc.get("headings", [])
    if headings:
        lines.append("### Estructura del documento (encabezados)\n")
        for h in headings[:20]:
            indent = "  " * (h["level"] - 1)
            lines.append(f"{indent}- **H{h['level']}:** {h['text']}")
        lines.append("")

    # Contenido principal
    main_text = (
        doc.get("full_text", "") or
        doc.get("main_text", "") or
        doc.get("text", "") or
        doc.get("extract", "")
    )

    if main_text:
        lines.append("### Texto principal\n")
        # Truncar a 3000 palabras para mantener el markdown manejable
        words = main_text.split()
        if len(words) > 3000:
            truncated = " ".join(words[:3000])
            lines.append(truncated)
            lines.append(f"\n\n> *[Texto truncado — {len(words) - 3000:,} palabras adicionales "
                         f"disponibles en el JSON fuente]*\n")
        else:
            lines.append(main_text)
        lines.append("")

    # Párrafos clave para páginas web
    paragraphs = doc.get("paragraphs", [])
    if paragraphs and not main_text:
        lines.append("### Párrafos extraídos\n")
        for i, para in enumerate(paragraphs[:10]):
            lines.append(f"> **P{i+1}:** {para}\n")
        lines.append("")

    # Videos de YouTube
    videos = doc.get("videos", [])
    if videos:
        lines.append("### Videos del canal (muestra)\n")
        for v in videos[:10]:
            date = v.get("published_at", "")[:10]
            views = v.get("view_count", "N/A")
            lines.append(f"- [{v.get('title', 'Sin título')}]({v.get('url', '')}) "
                         f"— {date} — {views} vistas")
        if len(videos) > 10:
            lines.append(f"\n*... y {len(videos) - 10} videos más (ver videos_lista.json)*")
        lines.append("")

    return "\n".join(lines)


def build_entities_section(doc: dict) -> str:
    """
    Construye la sección de entidades detectadas.
    """
    lines = ["## Entidades detectadas\n"]
    entities = doc.get("entities", {})

    # Organizaciones
    orgs = entities.get("organizations", [])
    if orgs:
        lines.append("### Organizaciones\n")
        for org in orgs[:15]:
            lines.append(f"- `{org}`")
        lines.append("")

    # Personas
    people = entities.get("people", [])
    if people:
        lines.append("### Personas mencionadas\n")
        for person in people[:10]:
            lines.append(f"- {person}")
        lines.append("")

    # Geografías
    locations = entities.get("locations", [])
    if locations:
        lines.append("### Geografías / Presencia\n")
        for loc in locations[:15]:
            lines.append(f"- 📍 {loc}")
        lines.append("")

    # Temas principales
    topics = doc.get("topics", [])
    if topics:
        lines.append("### Temas principales (taxonomía Manuelita)\n")
        for topic in topics[:8]:
            score_bar = "█" * int(topic["score"] * 10) + "░" * (10 - int(topic["score"] * 10))
            lines.append(
                f"- **{topic['topic']}** `{score_bar}` {topic['score']:.0%} "
                f"— keywords: {', '.join(topic.get('matched_keywords', [])[:3])}"
            )
        lines.append("")

    return "\n".join(lines)


def build_dates_section(doc: dict) -> str:
    """
    Construye la sección de fechas y eventos relevantes.
    """
    lines = ["## Fechas y eventos relevantes\n"]

    dates = doc.get("relevant_dates", [])
    if dates:
        for date in dates[:20]:
            lines.append(f"- `{date}`")
        lines.append("")
    else:
        lines.append("*No se detectaron fechas relevantes en el documento.*\n")

    return "\n".join(lines)


def build_evidence_section(doc: dict) -> str:
    """
    Construye la sección de evidencia textual (citas clave).
    """
    lines = ["## Evidencia textual (citas clave)\n"]

    key_quotes = doc.get("key_quotes", [])
    if key_quotes:
        for i, quote in enumerate(key_quotes[:5]):
            lines.append(f"> **{i+1}.** \"{quote}\"\n")
    else:
        # Intentar extraer primeros párrafos como evidencia
        paragraphs = doc.get("paragraphs", [])
        if paragraphs:
            for para in paragraphs[:3]:
                if len(para) > 80:
                    lines.append(f"> \"{para[:300]}...\"\n")

    if not key_quotes and not doc.get("paragraphs"):
        lines.append("*Sin citas textuales disponibles en este documento.*\n")

    return "\n".join(lines)


def build_relations_section(doc: dict) -> str:
    """
    Construye la sección de relaciones con otras fuentes del corpus.
    """
    lines = ["## Relación con otras fuentes\n"]

    # Links internos detectados (para páginas web)
    internal_links = doc.get("internal_links", [])
    if internal_links:
        lines.append("### Páginas relacionadas (links internos)\n")
        for link in internal_links[:10]:
            text = link.get("text", link.get("url", ""))[:50]
            url = link.get("url", "")
            if text and url:
                lines.append(f"- [{text}]({url})")
        lines.append("")

    # Links externos
    external_links = doc.get("external_links", [])
    if external_links:
        lines.append("### Fuentes externas referenciadas\n")
        for link in external_links[:5]:
            text = link.get("text", link.get("url", ""))[:50]
            url = link.get("url", "")
            if text and url:
                lines.append(f"- [{text}]({url})")
        lines.append("")

    return "\n".join(lines)


def build_quality_section(doc: dict) -> str:
    """
    Construye la sección de observaciones de calidad del dato.
    """
    lines = ["## Observaciones de calidad\n"]

    source_type = doc.get("source_type", "desconocida")
    confidence = doc.get("confidence_score", 0)
    norm_status = doc.get("normalization_status", "pendiente")
    extraction_method = doc.get("extraction_method", "N/A")

    observations = [
        f"- **Tipo de fuente:** `{source_type}` — {SOURCE_TYPE_LABELS.get(source_type, source_type)}",
        f"- **Score de confianza:** `{confidence}` / 1.0",
        f"- **Estado de normalización:** `{norm_status}`",
        f"- **Método de extracción:** `{extraction_method}`",
        f"- **Hash de contenido:** `{doc.get('content_hash', 'N/A')}`",
    ]

    # Advertencias específicas
    warnings = []
    if confidence < 0.3:
        warnings.append("⚠️ Score de confianza bajo — verificar manualmente")
    if source_type in ["reseña", "tercero"]:
        warnings.append("⚠️ Fuente no oficial — datos no verificados directamente por Manuelita")
    if doc.get("normalization_status") == "insufficient_text":
        warnings.append("⚠️ Texto insuficiente para normalización completa")
    if extraction_method == "ocr_tesseract":
        warnings.append("⚠️ Texto extraído por OCR — puede contener errores de reconocimiento")

    lines.extend(observations)

    if warnings:
        lines.append("\n### ⚠️ Advertencias\n")
        lines.extend(warnings)

    lines.append("")

    return "\n".join(lines)


# ============================================================
# CONSTRUCTOR PRINCIPAL DE SMART MARKDOWN
# ============================================================

def build_smart_markdown(doc: dict) -> str:
    """
    Construye el documento SMART MARKDOWN completo para un documento JSON.

    Args:
        doc: Diccionario de documento normalizado

    Returns:
        String con el contenido completo del Markdown
    """
    sections = [
        build_yaml_frontmatter(doc),
        build_executive_summary(doc),
        build_key_data_section(doc),
        build_structured_content(doc),
        build_entities_section(doc),
        build_dates_section(doc),
        build_evidence_section(doc),
        build_relations_section(doc),
        build_quality_section(doc),
    ]

    # Sección final: URL original y metadatos RAG
    url = doc.get("source_url", doc.get("url", ""))
    sections.append(f"## URL original\n\n[{url}]({url})\n")
    sections.append(
        f"---\n*Documento generado automáticamente — "
        f"Proyecto OSINT Manuelita — "
        f"{doc.get('captured_at', '')[:10]}*\n"
    )

    return "\n".join(sections)


def save_smart_markdown(doc: dict, output_dir: Optional[Path] = None) -> Path:
    """
    Guarda el SMART MARKDOWN de un documento en el directorio de salida.
    Retorna la ruta del archivo creado.
    """
    out_dir = output_dir or paths_cfg.markdown()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Generar nombre de archivo
    doc_id = doc.get("id", "")
    page_key = doc.get("page_key", doc.get("platform", "doc"))
    source_type = doc.get("source_type", "")
    filename = f"{source_type}_{page_key}_{doc_id[:8]}.md" if doc_id else f"{page_key}.md"
    filename = filename.replace(" ", "_").replace("/", "_")

    filepath = out_dir / filename
    content = build_smart_markdown(doc)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"SMART MARKDOWN guardado: {filepath}")
    return filepath


# ============================================================
# ÍNDICE MAESTRO
# ============================================================

def build_master_index(docs: list[dict], output_dir: Path = None) -> str:
    """
    Construye el índice maestro de todos los documentos en formato Markdown.
    """
    out_dir = output_dir or paths_cfg.markdown()
    lines = [
        "---",
        "title: Índice Maestro — Corpus OSINT Manuelita Agroindustrial",
        f"generated_at: {now_iso()}",
        f"total_documents: {len(docs)}",
        "---\n",
        "# 📚 Índice Maestro — Corpus OSINT Manuelita\n",
        f"> Corpus generado el `{now_iso()[:10]}` | "
        f"Total de documentos: **{len(docs)}**\n",
        "## Documentos por tipo de fuente\n",
    ]

    # Agrupar por tipo de fuente
    by_source = {}
    for doc in docs:
        st = doc.get("source_type", "desconocido")
        by_source.setdefault(st, []).append(doc)

    for source_type, source_docs in sorted(by_source.items()):
        lines.append(f"\n### {SOURCE_TYPE_LABELS.get(source_type, source_type)} ({len(source_docs)})\n")
        for doc in source_docs:
            title = (
                doc.get("metadata", {}).get("title") or
                doc.get("title") or
                doc.get("page_key", "Sin título")
            )[:60]
            url = doc.get("source_url", doc.get("url", "#"))
            doc_id = doc.get("id", "")
            confidence = doc.get("confidence_score", 0)
            lines.append(f"- [{title}]({url}) — `confianza: {confidence}` — id: `{doc_id[:8]}`")

    lines.append("\n## Cobertura temática\n")
    all_topics = []
    for doc in docs:
        all_topics.extend([t["topic"] for t in doc.get("topics", [])])

    from collections import Counter
    topic_counts = Counter(all_topics)
    for topic, count in topic_counts.most_common():
        lines.append(f"- **{topic}**: {count} documentos")

    index_content = "\n".join(lines)

    # Guardar índice
    index_path = out_dir / "_INDICE_MAESTRO.md"
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(index_content)

    logger.success(f"Índice maestro guardado: {index_path}")
    return index_content


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_markdown_builder(source_dir: str = None, input_file: str = None) -> list[Path]:
    """
    Construye todos los archivos SMART MARKDOWN desde los JSONs normalizados.
    """
    setup_logging("build_markdown")
    paths_cfg.ensure_all()

    logger.info("=" * 60)
    logger.info("INICIO: Constructor SMART MARKDOWN — Manuelita")
    logger.info("=" * 60)

    json_dir = Path(source_dir) if source_dir else paths_cfg.json_out()
    docs = []

    if input_file:
        json_files = [Path(input_file)]
    else:
        json_files = sorted(json_dir.glob("normalized_*.json"))
        if not json_files:
            # Intentar con todos los JSONs disponibles
            json_files = [f for f in json_dir.glob("*.json")
                          if not f.name.startswith("_")]

    for json_file in json_files:
        try:
            from src.utils.utils import load_json
            doc = load_json(json_file)
            if isinstance(doc, list):
                docs.extend(doc)
            else:
                docs.append(doc)
        except Exception as e:
            logger.warning(f"No se pudo cargar {json_file}: {e}")

    logger.info(f"Documentos a convertir a SMART MARKDOWN: {len(docs)}")

    saved_paths = []
    for doc in docs:
        try:
            path = save_smart_markdown(doc)
            saved_paths.append(path)
        except Exception as e:
            logger.error(f"Error generando markdown para {doc.get('id', 'unknown')}: {e}")

    # Construir índice maestro
    if docs:
        build_master_index(docs, output_dir=paths_cfg.markdown())

    logger.success(f"SMART MARKDOWN completado: {len(saved_paths)} archivos generados")
    return saved_paths


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Constructor SMART MARKDOWN — Manuelita")
    parser.add_argument("--source-dir", type=str,
                        help="Directorio con JSONs normalizados")
    parser.add_argument("--file", type=str,
                        help="Archivo JSON específico a convertir")
    args = parser.parse_args()
    run_markdown_builder(source_dir=args.source_dir, input_file=args.file)
