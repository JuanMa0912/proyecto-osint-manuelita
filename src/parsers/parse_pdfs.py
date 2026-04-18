"""
parse_pdfs.py — Extracción y estructuración de contenido de PDFs públicos de Manuelita.

PDFs objetivo confirmados:
  - Informe de Sostenibilidad 2023-2024
  - Informe de Sostenibilidad 2021-2022
  - Cualquier PDF encontrado durante el scraping del sitio

Pipeline:
  1. Descarga del PDF (si no está en caché local)
  2. Extracción de texto con pdfplumber (texto nativo)
  3. Fallback: PyMuPDF (fitz) para PDFs con fuentes complejas
  4. Fallback: pytesseract OCR para PDFs-imagen escaneados
  5. Extracción de tablas
  6. Estructuración en formato JSON + Markdown

Uso:
  python -m src.parsers.parse_pdfs
  python -m src.parsers.parse_pdfs --pdf sostenibilidad_2023_2024
  python -m src.parsers.parse_pdfs --local ruta/al/archivo.pdf
"""

import argparse
import io
import re
from pathlib import Path
from datetime import datetime

import requests
from loguru import logger

from src.utils.config import target_cfg, paths_cfg
from src.utils.utils import (
    safe_get, save_json, clean_text, now_iso,
    setup_logging, generate_doc_id, content_hash, url_to_slug,
)

# ============================================================
# IMPORTACIONES CONDICIONALES
# ============================================================

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False
    logger.warning("pdfplumber no disponible")

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False
    logger.warning("PyMuPDF no disponible")

try:
    import pytesseract
    from PIL import Image
    TESSERACT_AVAILABLE = True
except ImportError:
    TESSERACT_AVAILABLE = False
    logger.warning("pytesseract no disponible (OCR deshabilitado)")


# ============================================================
# DESCARGA DE PDF
# ============================================================

def download_pdf(url: str, force_reload: bool = False) -> Path:
    """
    Descarga un PDF desde una URL y lo guarda en data_raw/pdfs/.
    Si ya existe localmente, retorna la ruta sin re-descargar.

    Args:
        url: URL pública del PDF
        force_reload: Si True, descarga aunque exista localmente

    Returns:
        Path al archivo PDF local
    """
    slug = url_to_slug(url)
    local_path = paths_cfg.pdfs() / f"{slug}.pdf"

    if local_path.exists() and not force_reload:
        logger.info(f"PDF ya existe localmente: {local_path}")
        return local_path

    logger.info(f"Descargando PDF: {url}")
    response = safe_get(url, extra_headers={"Accept": "application/pdf"})

    if not response:
        raise FileNotFoundError(f"No se pudo descargar el PDF: {url}")

    content_type = response.headers.get("content-type", "")
    if "pdf" not in content_type.lower() and not url.lower().endswith(".pdf"):
        logger.warning(f"Content-Type inesperado: {content_type}")

    paths_cfg.pdfs().mkdir(parents=True, exist_ok=True)
    with open(local_path, "wb") as f:
        f.write(response.content)

    size_mb = len(response.content) / 1024 / 1024
    logger.success(f"PDF descargado: {local_path} ({size_mb:.2f} MB)")
    return local_path


# ============================================================
# EXTRACCIÓN CON PDFPLUMBER
# ============================================================

def extract_with_pdfplumber(pdf_path: Path) -> dict:
    """
    Extrae texto y tablas de un PDF usando pdfplumber.
    Método principal — mejor para texto nativo y tablas.
    """
    if not PDFPLUMBER_AVAILABLE:
        raise ImportError("pdfplumber no está instalado")

    logger.info(f"Extrayendo con pdfplumber: {pdf_path.name}")
    result = {
        "method": "pdfplumber",
        "pages": [],
        "full_text": "",
        "tables": [],
        "metadata": {},
        "page_count": 0,
    }

    with pdfplumber.open(pdf_path) as pdf:
        result["page_count"] = len(pdf.pages)

        # Metadatos del PDF
        if pdf.metadata:
            result["metadata"] = {
                k: str(v) for k, v in pdf.metadata.items()
                if v and k in ["Title", "Author", "Creator", "Producer", "CreationDate", "Subject"]
            }

        full_text_parts = []

        for i, page in enumerate(pdf.pages):
            page_num = i + 1

            # Extraer texto
            page_text = page.extract_text(x_tolerance=3, y_tolerance=3)
            if page_text:
                page_text = clean_text(page_text)
                full_text_parts.append(f"\n--- Página {page_num} ---\n{page_text}")

            # Extraer tablas
            tables = page.extract_tables()
            page_tables = []
            for j, table in enumerate(tables):
                if table:
                    cleaned_table = [
                        [clean_text(str(cell or "")) for cell in row]
                        for row in table if any(cell for cell in row)
                    ]
                    if cleaned_table:
                        page_tables.append({
                            "table_index": j,
                            "page": page_num,
                            "rows": len(cleaned_table),
                            "cols": len(cleaned_table[0]) if cleaned_table else 0,
                            "data": cleaned_table,
                        })
                        result["tables"].extend(page_tables)

            result["pages"].append({
                "page_number": page_num,
                "text": page_text or "",
                "word_count": len((page_text or "").split()),
                "has_tables": len(page_tables) > 0,
                "table_count": len(page_tables),
            })

            if page_num % 10 == 0:
                logger.debug(f"Procesadas {page_num}/{result['page_count']} páginas...")

        result["full_text"] = "\n".join(full_text_parts)

    text_pages = [p for p in result["pages"] if p["word_count"] > 0]
    logger.success(
        f"pdfplumber: {result['page_count']} páginas, "
        f"{len(text_pages)} con texto, "
        f"{len(result['tables'])} tablas, "
        f"{len(result['full_text'].split())} palabras totales"
    )
    return result


# ============================================================
# EXTRACCIÓN CON PYMUPDF (fallback)
# ============================================================

def extract_with_pymupdf(pdf_path: Path) -> dict:
    """
    Extrae texto usando PyMuPDF (fitz).
    Mejor para PDFs con fuentes complejas o texto en múltiples columnas.
    """
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF no está instalado")

    logger.info(f"Extrayendo con PyMuPDF: {pdf_path.name}")
    result = {
        "method": "pymupdf",
        "pages": [],
        "full_text": "",
        "tables": [],
        "metadata": {},
        "page_count": 0,
    }

    doc = fitz.open(str(pdf_path))
    result["page_count"] = doc.page_count
    result["metadata"] = dict(doc.metadata)

    full_text_parts = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        text = page.get_text("text")
        text = clean_text(text)

        if text:
            full_text_parts.append(f"\n--- Página {page_num + 1} ---\n{text}")

        result["pages"].append({
            "page_number": page_num + 1,
            "text": text,
            "word_count": len(text.split()),
        })

    doc.close()
    result["full_text"] = "\n".join(full_text_parts)
    logger.success(f"PyMuPDF: {result['page_count']} páginas, {len(result['full_text'].split())} palabras")
    return result


# ============================================================
# EXTRACCIÓN OCR (fallback para PDFs escaneados)
# ============================================================

def extract_with_ocr(pdf_path: Path, lang: str = "spa") -> dict:
    """
    Extrae texto de PDFs escaneados usando OCR con Tesseract.
    Requiere: pytesseract, Pillow, y Tesseract instalado en el sistema.
    """
    if not TESSERACT_AVAILABLE:
        raise ImportError("pytesseract o Pillow no instalados")
    if not PYMUPDF_AVAILABLE:
        raise ImportError("PyMuPDF necesario para convertir páginas PDF a imagen")

    logger.info(f"Extrayendo con OCR (Tesseract): {pdf_path.name}")
    result = {
        "method": "ocr_tesseract",
        "pages": [],
        "full_text": "",
        "tables": [],
        "metadata": {},
        "page_count": 0,
        "ocr_language": lang,
    }

    doc = fitz.open(str(pdf_path))
    result["page_count"] = doc.page_count
    full_text_parts = []

    for page_num in range(doc.page_count):
        page = doc[page_num]
        # Renderizar página como imagen (300 DPI para mejor OCR)
        mat = fitz.Matrix(300 / 72, 300 / 72)
        pix = page.get_pixmap(matrix=mat)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

        # OCR
        ocr_config = f"--oem 3 --psm 3 -l {lang}"
        text = pytesseract.image_to_string(img, config=ocr_config)
        text = clean_text(text)

        if text:
            full_text_parts.append(f"\n--- Página {page_num + 1} (OCR) ---\n{text}")

        result["pages"].append({
            "page_number": page_num + 1,
            "text": text,
            "word_count": len(text.split()),
            "ocr": True,
        })

        if (page_num + 1) % 5 == 0:
            logger.debug(f"OCR: {page_num + 1}/{result['page_count']} páginas...")

    doc.close()
    result["full_text"] = "\n".join(full_text_parts)
    logger.success(f"OCR completado: {result['page_count']} páginas, {len(result['full_text'].split())} palabras")
    return result


# ============================================================
# PIPELINE COMPLETO DE EXTRACCIÓN
# ============================================================

def extract_pdf(pdf_path: Path, url: str = "", min_words_threshold: int = 100) -> dict:
    """
    Pipeline completo de extracción con fallback automático:
    pdfplumber → PyMuPDF → OCR Tesseract

    Args:
        pdf_path: Ruta local al PDF
        url: URL de origen (para trazabilidad)
        min_words_threshold: Mínimo de palabras para considerar extracción exitosa

    Returns:
        Diccionario con todos los datos extraídos
    """
    captured_at = now_iso()
    doc_id = generate_doc_id("pdf", url or str(pdf_path), captured_at)

    base_result = {
        "id": doc_id,
        "company": "Manuelita",
        "source_type": "oficial",
        "source_name": "Informe PDF Manuelita",
        "source_url": url or str(pdf_path),
        "local_path": str(pdf_path),
        "filename": pdf_path.name,
        "file_size_mb": round(pdf_path.stat().st_size / 1024 / 1024, 2),
        "captured_at": captured_at,
        "language": "es",
        "country": "CO",
        "document_type": "informe",
        "status": "error",
    }

    extraction_result = None

    # Intento 1: pdfplumber
    if PDFPLUMBER_AVAILABLE:
        try:
            extraction_result = extract_with_pdfplumber(pdf_path)
            if len(extraction_result.get("full_text", "").split()) >= min_words_threshold:
                logger.info("pdfplumber: extracción exitosa")
            else:
                logger.warning("pdfplumber: texto insuficiente, intentando PyMuPDF...")
                extraction_result = None
        except Exception as e:
            logger.warning(f"pdfplumber falló: {e}")

    # Intento 2: PyMuPDF
    if not extraction_result and PYMUPDF_AVAILABLE:
        try:
            extraction_result = extract_with_pymupdf(pdf_path)
            if len(extraction_result.get("full_text", "").split()) >= min_words_threshold:
                logger.info("PyMuPDF: extracción exitosa")
            else:
                logger.warning("PyMuPDF: texto insuficiente, intentando OCR...")
                extraction_result = None
        except Exception as e:
            logger.warning(f"PyMuPDF falló: {e}")

    # Intento 3: OCR
    if not extraction_result and TESSERACT_AVAILABLE:
        try:
            extraction_result = extract_with_ocr(pdf_path)
            logger.info("OCR Tesseract: extracción completada")
        except Exception as e:
            logger.error(f"OCR falló: {e}")

    if not extraction_result:
        base_result["status"] = "all_methods_failed"
        return base_result

    # Combinar resultados
    base_result.update({
        "status": "ok",
        "extraction_method": extraction_result.get("method", "unknown"),
        "page_count": extraction_result.get("page_count", 0),
        "full_text": extraction_result.get("full_text", ""),
        "word_count": len(extraction_result.get("full_text", "").split()),
        "content_hash": content_hash(extraction_result.get("full_text", "")),
        "pages": extraction_result.get("pages", []),
        "tables": extraction_result.get("tables", []),
        "pdf_metadata": extraction_result.get("metadata", {}),
    })

    # Detectar secciones del informe de sostenibilidad de Manuelita
    full_text_lower = base_result["full_text"].lower()
    base_result["detected_sections"] = _detect_report_sections(full_text_lower)

    return base_result


def _detect_report_sections(text_lower: str) -> list[str]:
    """
    Detecta secciones clave en el informe de sostenibilidad de Manuelita.
    """
    section_keywords = {
        "perfil_corporativo": ["perfil corporativo", "quiénes somos", "historia"],
        "gobierno_corporativo": ["gobierno corporativo", "junta directiva", "comité"],
        "sostenibilidad_economica": ["sostenibilidad económica", "ingresos", "rentabilidad", "utilidad"],
        "sostenibilidad_social": ["sostenibilidad social", "empleados", "comunidades", "educación"],
        "sostenibilidad_ambiental": ["sostenibilidad ambiental", "emisiones", "agua", "biodiversidad"],
        "gri": ["gri", "global reporting initiative", "índice gri"],
        "ods": ["ods", "objetivos de desarrollo sostenible", "agenda 2030"],
        "carbono_neutralidad": ["carbono neutral", "huella de carbono", "scope 1", "scope 2"],
        "biocombustibles": ["bioetanol", "biodiesel", "biocombustible"],
        "palma": ["palma de aceite", "aceite de palma", "palmicultores"],
        "azucar": ["azúcar", "caña de azúcar", "ingenio"],
    }

    detected = []
    for section, keywords in section_keywords.items():
        if any(kw in text_lower for kw in keywords):
            detected.append(section)

    return detected


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_pdf_parser(pdf_keys: list[str] = None, local_path: str = None) -> list[dict]:
    """
    Ejecuta el parser de PDFs para los informes de Manuelita.

    Args:
        pdf_keys: Keys de PDFs configurados en target_cfg (ej: ["sostenibilidad_2023_2024"])
        local_path: Ruta a un PDF local específico

    Returns:
        Lista de documentos extraídos
    """
    setup_logging("parse_pdfs")
    paths_cfg.ensure_all()

    logger.info("=" * 60)
    logger.info("INICIO: Parser de PDFs — Manuelita Agroindustrial")
    logger.info("=" * 60)

    results = []

    # Procesar PDF local específico
    if local_path:
        path = Path(local_path)
        if not path.exists():
            logger.error(f"Archivo no encontrado: {local_path}")
            return results
        result = extract_pdf(path)
        results.append(result)
        out_path = paths_cfg.json_out() / f"pdf_{path.stem}.json"
        save_json(result, out_path)
        return results

    # Procesar PDFs configurados
    target_pdfs = target_cfg.pdfs
    if pdf_keys:
        target_pdfs = {k: v for k, v in target_pdfs.items() if k in pdf_keys}

    for pdf_key, pdf_url in target_pdfs.items():
        logger.info(f"Procesando PDF: {pdf_key}")
        try:
            # Descargar
            local_pdf = download_pdf(pdf_url)

            # Extraer
            result = extract_pdf(local_pdf, url=pdf_url)
            result["pdf_key"] = pdf_key

            results.append(result)

            # Guardar JSON
            out_path = paths_cfg.json_out() / f"pdf_{pdf_key}.json"
            save_json(result, out_path)

            logger.success(
                f"PDF '{pdf_key}' procesado: {result.get('page_count', 0)} páginas, "
                f"{result.get('word_count', 0)} palabras, "
                f"secciones: {result.get('detected_sections', [])}"
            )

        except Exception as e:
            logger.error(f"Error procesando PDF '{pdf_key}': {e}")
            results.append({"pdf_key": pdf_key, "url": pdf_url, "status": "error", "error": str(e)})

    logger.success(f"Parser PDFs completado: {len(results)} documentos procesados")
    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parser de PDFs — Manuelita")
    parser.add_argument("--pdf", nargs="+",
                        choices=list(target_cfg.pdfs.keys()),
                        help="PDFs específicos a procesar por key")
    parser.add_argument("--local", type=str,
                        help="Ruta a un archivo PDF local")
    args = parser.parse_args()
    run_pdf_parser(pdf_keys=args.pdf, local_path=args.local)
