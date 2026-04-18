"""
normalize_entities.py — Normalización y extracción de entidades nombradas para Manuelita.

Pipeline NLP:
  1. Detección de entidades con spaCy (es_core_news_lg)
  2. Normalización de nombres de entidades conocidas
  3. Extracción de fechas relevantes
  4. Extracción de cifras clave (producción, ingresos, empleados)
  5. Clasificación de temas principales (taxonomía Manuelita)
  6. Deduplicación por similitud (MinHash LSH)

Uso:
  python -m src.cleaners.normalize_entities --input data_processed/json/
  python -m src.cleaners.normalize_entities --file pdf_sostenibilidad_2023_2024.json
"""

import argparse
import re
from pathlib import Path
from collections import Counter, defaultdict
from typing import Optional

from loguru import logger

from src.utils.config import nlp_cfg, paths_cfg
from src.utils.utils import load_json, save_json, now_iso, setup_logging, content_hash


# ============================================================
# DICCIONARIO DE NORMALIZACIÓN — ESPECÍFICO PARA MANUELITA
# ============================================================

# Aliases conocidos de la empresa y sus unidades de negocio
ENTITY_NORMALIZER = {
    # Empresa principal
    "manuelita": "Manuelita S.A.",
    "grupo manuelita": "Manuelita S.A.",
    "ingenio manuelita": "Manuelita S.A. — Plataforma Azúcar",
    "manuelita agroindustrial": "Manuelita S.A.",
    "manuelita s.a.": "Manuelita S.A.",

    # Unidades de negocio Colombia
    "manuelita azúcar y energía": "Manuelita Azúcar y Energía",
    "manuelita azucar": "Manuelita Azúcar y Energía",
    "manuelita aceites y energía": "Manuelita Aceites y Energía",
    "manuelita aceites": "Manuelita Aceites y Energía",
    "manuelita frutas y hortalizas": "Manuelita Frutas y Hortalizas",
    "manuelita innova": "Manuelita Innova",
    "océanos": "Océanos (Acuicultura Colombia)",
    "oceanos manuelita": "Océanos (Acuicultura Colombia)",

    # Subsidiarias internacionales
    "agroindustrial laredo": "Agroindustrial Laredo S.A.",
    "laredo": "Agroindustrial Laredo S.A.",
    "mejillones américa": "Mejillones América (Chile)",
    "mejillones america": "Mejillones América (Chile)",
    "palmar de altamira": "Palmar de Altamira (Casanare)",

    # Personas clave (verificadas públicamente)
    "harold eder": "Harold Eder (Presidente — Manuelita S.A.)",

    # Geografías
    "valle del cauca": "Valle del Cauca (Colombia)",
    "cali": "Cali, Valle del Cauca (Colombia)",
    "trujillo, perú": "Trujillo (Perú)",
    "meta": "Meta (Colombia)",
    "casanare": "Casanare (Colombia)",
    "puerto montt": "Puerto Montt (Chile)",
    "cartagena": "Cartagena de Indias (Colombia)",
}

# Taxonomía temática para Manuelita
TOPIC_TAXONOMY = {
    "azucar_bioetanol": [
        "azúcar", "caña de azúcar", "bioetanol", "etanol", "melaza", "guarapo",
        "refinería", "cristalización", "ingenio azucarero",
    ],
    "palma_biodiesel": [
        "palma de aceite", "aceite de palma", "biodiesel", "palmiste", "racimo",
        "extracción de aceite", "palma africana",
    ],
    "acuicultura": [
        "mejillón", "camarón", "acuicultura", "piscicultura", "exportación pesquera",
        "iqf", "congelados", "valva", "mariscos",
    ],
    "frutas_hortalizas": [
        "uva de mesa", "uvas", "hortalizas", "aguacate", "fruta fresca",
        "exportación agrícola",
    ],
    "sostenibilidad_ambiental": [
        "emisiones", "carbono", "huella de carbono", "agua", "biodiversidad",
        "scope 1", "scope 2", "scope 3", "carbono neutral", "ods", "gri",
        "residuos", "energías renovables", "solar", "biomasa",
    ],
    "sostenibilidad_social": [
        "comunidades", "educación", "salud", "vivienda", "género",
        "equidad", "diversidad", "inclusión", "voluntariado",
        "fundación", "responsabilidad social", "emprendimiento",
    ],
    "sostenibilidad_economica": [
        "ingresos", "utilidades", "rentabilidad", "inversión", "exportaciones",
        "producción", "capacidad instalada", "empleo", "proveedores",
    ],
    "innovacion": [
        "innovación", "tecnología", "i+d", "investigación", "startup",
        "digital", "automatización", "manuelita innova",
    ],
    "gobernanza": [
        "gobierno corporativo", "junta directiva", "comité", "ética",
        "transparencia", "anticorrupción", "compliance",
    ],
    "talento_humano": [
        "empleados", "trabajadores", "colaboradores", "recursos humanos",
        "capacitación", "bienestar laboral", "sindicato",
    ],
    "mercados_internacionales": [
        "exportación", "latinoamérica", "colombia", "perú", "chile",
        "europa", "asia", "mercado internacional",
    ],
}

# Patrones para cifras clave
NUMERIC_PATTERNS = {
    "produccion_azucar_ton": r"(\d[\d.,]+)\s*(?:mil|millones)?\s*(?:ton(?:eladas)?)\s*(?:de)?\s*azúcar",
    "produccion_bioetanol_litros": r"(\d[\d.,]+)\s*(?:mil|millones)?\s*(?:litros)\s*(?:de)?\s*(?:bio)?etanol",
    "empleados": r"(\d[\d.,]+)\s*(?:empleados?|trabajadores?|colaboradores?)",
    "ingresos_millones": r"(?:ingresos?|ventas?)\s*(?:de)?\s*(?:USD|COP|US\$|\$)?\s*(\d[\d.,]+)\s*(?:millones|mil millones)",
    "familias_beneficiadas": r"(\d[\d.,]+)\s*(?:familias?)\s*(?:beneficiadas?|atendidas?)",
    "paises_exportacion": r"(?:más de)?\s*(\d+)\s*países",
    "años_historia": r"(\d+)\s*años?\s*(?:de historia|de experiencia|de trayectoria)",
}


# ============================================================
# CARGA DE MODELO NLP
# ============================================================

_nlp_model = None

def load_nlp_model():
    """Carga el modelo de spaCy en español (singleton)."""
    global _nlp_model
    if _nlp_model is None:
        try:
            import spacy
            _nlp_model = spacy.load(nlp_cfg.spacy_model)
            logger.info(f"Modelo NLP cargado: {nlp_cfg.spacy_model}")
        except Exception as e:
            logger.warning(f"No se pudo cargar {nlp_cfg.spacy_model}: {e}")
            logger.warning("NER deshabilitado. Usando extracción por regex.")
    return _nlp_model


# ============================================================
# EXTRACCIÓN DE ENTIDADES
# ============================================================

def extract_entities_spacy(text: str) -> dict:
    """
    Extrae entidades nombradas usando spaCy.
    Categorías: ORG, PER/PERSON, LOC/GPE, DATE, MONEY, MISC
    """
    entities = defaultdict(list)
    nlp = load_nlp_model()

    if not nlp:
        return dict(entities)

    # Procesar en chunks para textos largos (spaCy tiene límite de ~1M chars)
    chunk_size = 50000
    text_chunks = [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    for chunk in text_chunks:
        doc = nlp(chunk)
        for ent in doc.ents:
            normalized = normalize_entity(ent.text.strip(), ent.label_)
            if normalized and len(normalized) > 2:
                entities[ent.label_].append(normalized)

    # Deduplicar y contar frecuencias
    result = {}
    for label, ent_list in entities.items():
        counts = Counter(ent_list)
        result[label] = [
            {"text": ent, "count": count}
            for ent, count in counts.most_common(20)
        ]

    return result


def extract_entities_regex(text: str) -> dict:
    """
    Extracción básica de entidades por regex cuando spaCy no está disponible.
    Específica para el corpus de Manuelita.
    """
    entities = {
        "organizations": [],
        "locations": [],
        "products": [],
        "business_units": [],
    }

    text_lower = text.lower()

    # Detectar organizaciones conocidas
    org_patterns = list(ENTITY_NORMALIZER.keys())
    for pattern in sorted(org_patterns, key=len, reverse=True):  # Longest match first
        if pattern in text_lower:
            canonical = ENTITY_NORMALIZER[pattern]
            if canonical not in entities["organizations"]:
                entities["organizations"].append(canonical)

    # Localidades conocidas
    locations = ["Colombia", "Perú", "Chile", "Cali", "Valle del Cauca",
                 "Meta", "Casanare", "Puerto Montt", "Trujillo", "Cartagena"]
    for loc in locations:
        if loc.lower() in text_lower and loc not in entities["locations"]:
            entities["locations"].append(loc)

    # Unidades de negocio
    business_units_keywords = {
        "Plataforma Azúcar y Energía": ["azúcar y energía", "ingenio", "caña"],
        "Plataforma Aceites y Energía": ["aceites y energía", "palma"],
        "Plataforma Acuicultura": ["acuicultura", "mejillones", "camarón"],
        "Plataforma Frutas y Hortalizas": ["frutas y hortalizas", "uvas", "hortalizas"],
    }
    for unit, keywords in business_units_keywords.items():
        if any(kw in text_lower for kw in keywords):
            entities["business_units"].append(unit)

    return entities


def normalize_entity(text: str, label: str = "") -> str:
    """
    Normaliza el texto de una entidad aplicando el diccionario de normalización.
    """
    normalized = ENTITY_NORMALIZER.get(text.lower().strip(), text.strip())
    # Capitalizar si no está en el diccionario
    if normalized == text.strip() and text.strip():
        normalized = text.strip().title() if text.islower() else text.strip()
    return normalized


# ============================================================
# EXTRACCIÓN DE TEMAS
# ============================================================

def classify_topics(text: str) -> list[dict]:
    """
    Clasifica el texto en temas de la taxonomía de Manuelita.
    Retorna lista de temas con score de relevancia.
    """
    text_lower = text.lower()
    topics = []

    for topic, keywords in TOPIC_TAXONOMY.items():
        matches = [kw for kw in keywords if kw in text_lower]
        if matches:
            score = min(len(matches) / len(keywords), 1.0)
            topics.append({
                "topic": topic,
                "score": round(score, 3),
                "matched_keywords": matches[:5],
            })

    # Ordenar por score descendente
    return sorted(topics, key=lambda x: x["score"], reverse=True)


# ============================================================
# EXTRACCIÓN DE CIFRAS CLAVE
# ============================================================

def extract_key_figures(text: str) -> dict:
    """
    Extrae cifras numéricas clave del texto usando regex.
    """
    figures = {}
    for key, pattern in NUMERIC_PATTERNS.items():
        matches = re.findall(pattern, text, re.IGNORECASE)
        if matches:
            figures[key] = matches[0].replace(",", "").replace(".", "")
    return figures


# ============================================================
# EXTRACCIÓN DE FECHAS
# ============================================================

def extract_dates(text: str) -> list[str]:
    """
    Extrae fechas y años relevantes del texto.
    """
    date_patterns = [
        r"\b(19\d{2}|20[012]\d)\b",                    # Años: 1864, 2024
        r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b",     # DD/MM/YYYY
        r"\b(\d{4})[/-](\d{1,2})[/-](\d{1,2})\b",     # YYYY-MM-DD
        r"\b(enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|"
        r"octubre|noviembre|diciembre)\s+(?:de\s+)?(\d{4})\b",
    ]

    dates = []
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            date_str = match if isinstance(match, str) else " ".join(match)
            if date_str and date_str not in dates:
                dates.append(date_str)

    return sorted(set(dates))[:30]


# ============================================================
# NORMALIZACIÓN DE DOCUMENTO COMPLETO
# ============================================================

def normalize_document(doc: dict) -> dict:
    """
    Aplica el pipeline completo de normalización a un documento JSON.
    Enriquece el documento con entidades, temas y cifras.
    """
    text = doc.get("full_text") or doc.get("main_text") or doc.get("text", "")
    if not text:
        # Intentar reconstruir desde párrafos
        paragraphs = doc.get("paragraphs", [])
        text = "\n".join(paragraphs)

    if not text or len(text) < 50:
        doc["normalization_status"] = "insufficient_text"
        return doc

    logger.debug(f"Normalizando documento: {doc.get('id', 'unknown')}")

    # Extracción de entidades
    try:
        entities_spacy = extract_entities_spacy(text)
    except Exception:
        entities_spacy = {}

    entities_regex = extract_entities_regex(text)

    # Combinar entidades
    combined_entities = {
        "organizations": list(set(
            entities_regex.get("organizations", []) +
            [e["text"] for e in entities_spacy.get("ORG", [])]
        ))[:20],
        "people": [e["text"] for e in entities_spacy.get("PER", [])][:10] +
                  [e["text"] for e in entities_spacy.get("PERSON", [])][:10],
        "locations": list(set(
            entities_regex.get("locations", []) +
            [e["text"] for e in entities_spacy.get("LOC", [])] +
            [e["text"] for e in entities_spacy.get("GPE", [])]
        ))[:20],
        "products": entities_regex.get("products", []),
        "business_units": entities_regex.get("business_units", []),
        "raw_spacy": entities_spacy,
    }

    # Clasificación de temas
    topics = classify_topics(text)

    # Cifras clave
    key_figures = extract_key_figures(text)

    # Fechas
    dates = extract_dates(text)

    # Citas textuales clave (primeras oraciones de párrafos relevantes)
    key_quotes = _extract_key_quotes(text, combined_entities["organizations"])

    # Actualizar documento
    doc.update({
        "entities": combined_entities,
        "topics": topics,
        "key_figures": key_figures,
        "relevant_dates": dates,
        "key_quotes": key_quotes,
        "confidence_score": _calculate_confidence(doc, topics, combined_entities),
        "normalized_at": now_iso(),
        "normalization_status": "completed",
    })

    return doc


def _extract_key_quotes(text: str, organizations: list) -> list[str]:
    """
    Extrae hasta 5 citas textuales relevantes del texto.
    Prioriza oraciones que mencionan a Manuelita directamente.
    """
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > 60]
    manuelita_sentences = [
        s for s in sentences
        if "manuelita" in s.lower() and len(s) < 400
    ]
    return manuelita_sentences[:5]


def _calculate_confidence(doc: dict, topics: list, entities: dict) -> float:
    """
    Calcula un score de confianza (0.0 - 1.0) para el documento.
    Basado en: tipo de fuente, cantidad de entidades detectadas,
    temas identificados, longitud del texto.
    """
    score = 0.0

    # Fuente oficial tiene mayor confianza
    source_type = doc.get("source_type", "")
    source_scores = {"oficial": 0.4, "prensa": 0.25, "red_social": 0.15,
                     "tercero": 0.1, "reseña": 0.05}
    score += source_scores.get(source_type, 0.1)

    # Temas identificados
    if topics:
        score += min(len(topics) * 0.05, 0.2)

    # Entidades detectadas
    total_entities = sum(len(v) for v in entities.values() if isinstance(v, list))
    score += min(total_entities * 0.01, 0.2)

    # Longitud del texto
    word_count = doc.get("word_count", 0) or len(doc.get("full_text", "").split())
    if word_count > 500:
        score += 0.1
    if word_count > 2000:
        score += 0.1

    return round(min(score, 1.0), 2)


# ============================================================
# DEDUPLICACIÓN
# ============================================================

def deduplicate_documents(docs: list[dict], threshold: float = None) -> list[dict]:
    """
    Elimina documentos duplicados o muy similares.
    Usa hash exacto primero, luego MinHash LSH si está disponible.
    """
    from src.utils.config import nlp_cfg
    dedup_threshold = threshold or nlp_cfg.dedup_threshold

    # Paso 1: Deduplicación exacta por hash
    seen_hashes = set()
    unique_docs = []
    for doc in docs:
        doc_hash = doc.get("content_hash") or content_hash(
            doc.get("full_text", "") or doc.get("main_text", "") or doc.get("text", "")
        )
        if doc_hash not in seen_hashes:
            seen_hashes.add(doc_hash)
            unique_docs.append(doc)

    exact_removed = len(docs) - len(unique_docs)
    if exact_removed > 0:
        logger.info(f"Deduplicación exacta: eliminados {exact_removed} documentos duplicados")

    # Paso 2: Deduplicación semántica con MinHash (si disponible)
    try:
        from datasketch import MinHash, MinHashLSH
        lsh = MinHashLSH(threshold=dedup_threshold, num_perm=128)
        final_docs = []

        for i, doc in enumerate(unique_docs):
            text = doc.get("full_text", "") or doc.get("main_text", "") or doc.get("text", "")
            tokens = set(text.lower().split())

            m = MinHash(num_perm=128)
            for token in tokens:
                m.update(token.encode("utf-8"))

            doc_key = f"doc_{i}"
            try:
                result = lsh.query(m)
                if not result:
                    lsh.insert(doc_key, m)
                    final_docs.append(doc)
                else:
                    logger.debug(f"Duplicado semántico detectado para doc_{i}")
            except Exception:
                final_docs.append(doc)

        semantic_removed = len(unique_docs) - len(final_docs)
        if semantic_removed > 0:
            logger.info(f"Deduplicación semántica: eliminados {semantic_removed} near-duplicates")

        return final_docs

    except ImportError:
        logger.debug("datasketch no disponible. Solo deduplicación exacta.")
        return unique_docs


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_normalization(input_dir: str = None, input_file: str = None) -> list[dict]:
    """
    Ejecuta el pipeline completo de normalización sobre todos los JSONs generados.
    """
    setup_logging("normalize_entities")
    paths_cfg.ensure_all()

    logger.info("=" * 60)
    logger.info("INICIO: Normalización de entidades — Manuelita")
    logger.info("=" * 60)

    # Cargar documentos
    json_dir = Path(input_dir) if input_dir else paths_cfg.json_out()
    documents = []

    if input_file:
        json_files = [Path(input_file)]
    else:
        json_files = list(json_dir.glob("*.json"))

    for json_file in json_files:
        if json_file.name.startswith("_"):
            continue
        try:
            doc = load_json(json_file)
            if isinstance(doc, dict):
                documents.append(doc)
            elif isinstance(doc, list):
                documents.extend(doc)
        except Exception as e:
            logger.warning(f"No se pudo cargar {json_file}: {e}")

    logger.info(f"Documentos a normalizar: {len(documents)}")

    # Normalizar
    normalized = []
    for doc in documents:
        try:
            norm_doc = normalize_document(doc)
            normalized.append(norm_doc)
        except Exception as e:
            logger.error(f"Error normalizando {doc.get('id', 'unknown')}: {e}")
            normalized.append(doc)

    # Deduplicar
    unique_docs = deduplicate_documents(normalized)

    # Guardar documentos normalizados
    for doc in unique_docs:
        doc_id = doc.get("id", f"doc_{now_iso()}")
        safe_id = doc_id.replace(":", "-").replace("+", "_")
        out_path = paths_cfg.json_out() / f"normalized_{safe_id}.json"
        save_json(doc, out_path)

    logger.success(f"Normalización completada: {len(unique_docs)} documentos únicos")
    return unique_docs


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normalizador de entidades — Manuelita")
    parser.add_argument("--input", type=str, help="Directorio con JSONs a normalizar")
    parser.add_argument("--file", type=str, help="Archivo JSON específico a normalizar")
    args = parser.parse_args()
    run_normalization(input_dir=args.input, input_file=args.file)
