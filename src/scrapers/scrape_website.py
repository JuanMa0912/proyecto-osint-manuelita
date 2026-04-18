"""
scrape_website.py — Scraper del sitio oficial de Manuelita (manuelita.com).

Extrae contenido de todas las páginas internas conocidas:
  perfil corporativo, historia, presencia regional, plataformas de negocio,
  sostenibilidad, noticias, contacto, economico, innovacion.

Salida:
  - data_raw/web/{slug}.json  — datos crudos por página
  - data_raw/web/{slug}.html  — HTML raw para trazabilidad

Uso:
  python -m src.scrapers.scrape_website
  python -m src.scrapers.scrape_website --page perfil
  python -m src.scrapers.scrape_website --all
"""

import argparse
import json
from datetime import datetime
from pathlib import Path
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from loguru import logger

from src.utils.config import target_cfg, paths_cfg, scraping_cfg
from src.utils.utils import (
    safe_get, save_json, save_raw_html, clean_text, extract_main_text,
    extract_metadata_from_soup, url_to_slug, now_iso, setup_logging,
    polite_delay, generate_doc_id, content_hash,
)


# ============================================================
# EXTRACTOR DE PÁGINAS ESPECÍFICAS
# ============================================================

def scrape_page(url: str, page_key: str) -> dict:
    """
    Scrapea una URL del sitio oficial y retorna datos estructurados.

    Args:
        url: URL completa de la página
        page_key: identificador interno (ej: "perfil", "historia")

    Returns:
        Diccionario con todos los datos extraídos.
    """
    logger.info(f"Scrapeando: [{page_key}] {url}")

    response = safe_get(url)
    if not response:
        return {"url": url, "page_key": page_key, "status": "error", "error": "No response"}

    captured_at = now_iso()
    soup = BeautifulSoup(response.text, "lxml")

    # Metadatos SEO
    meta = extract_metadata_from_soup(soup, url)

    # Texto principal limpio
    main_text = extract_main_text(soup)

    # Extraer párrafos estructurados
    paragraphs = _extract_paragraphs(soup)

    # Extraer encabezados (estructura del documento)
    headings = _extract_headings(soup)

    # Extraer links relevantes
    internal_links = _extract_internal_links(soup, url)
    external_links = _extract_external_links(soup, url)

    # Extraer imágenes con alt text
    images = _extract_images(soup, url)

    # Datos estructurados (JSON-LD si existe)
    structured_data = _extract_json_ld(soup)

    doc_id = generate_doc_id("web", url, captured_at)

    result = {
        "id": doc_id,
        "company": target_cfg.company,
        "page_key": page_key,
        "source_type": "oficial",
        "source_name": "manuelita.com",
        "url": url,
        "captured_at": captured_at,
        "language": meta.get("lang", "es"),
        "country": "CO",
        "status_code": response.status_code,
        "content_hash": content_hash(main_text),
        "metadata": meta,
        "headings": headings,
        "paragraphs": paragraphs,
        "main_text": main_text,
        "internal_links": internal_links,
        "external_links": external_links,
        "images": images,
        "structured_data": structured_data,
        "word_count": len(main_text.split()),
        "char_count": len(main_text),
    }

    # Guardar JSON crudo
    slug = url_to_slug(url)
    json_path = paths_cfg.web() / f"{slug}.json"
    html_path = paths_cfg.web() / f"{slug}.html"

    save_json(result, json_path)
    save_raw_html(response.text, html_path)

    logger.success(f"✅ Página guardada: {page_key} ({result['word_count']} palabras)")
    return result


# ============================================================
# EXTRACTORES AUXILIARES
# ============================================================

def _extract_paragraphs(soup: BeautifulSoup) -> list[str]:
    """Extrae párrafos de texto no vacíos."""
    paragraphs = []
    for p in soup.find_all("p"):
        text = clean_text(p.get_text())
        if len(text) > 30:  # Ignorar párrafos muy cortos
            paragraphs.append(text)
    return paragraphs


def _extract_headings(soup: BeautifulSoup) -> list[dict]:
    """Extrae todos los encabezados H1-H4 con su nivel."""
    headings = []
    for level in range(1, 5):
        for tag in soup.find_all(f"h{level}"):
            text = clean_text(tag.get_text())
            if text:
                headings.append({"level": level, "text": text})
    return headings


def _extract_internal_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extrae links internos del sitio."""
    domain = urlparse(base_url).netloc
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = urljoin(base_url, a["href"].strip())
        if urlparse(href).netloc == domain and href not in seen:
            seen.add(href)
            links.append({"url": href, "text": clean_text(a.get_text())})
    return links[:50]  # Limitar a 50 links internos


def _extract_external_links(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extrae links externos con texto ancla."""
    domain = urlparse(base_url).netloc
    links = []
    seen = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if (href.startswith("http") and
                urlparse(href).netloc != domain and
                href not in seen):
            seen.add(href)
            links.append({"url": href, "text": clean_text(a.get_text())})
    return links[:20]


def _extract_images(soup: BeautifulSoup, base_url: str) -> list[dict]:
    """Extrae imágenes con src y alt text."""
    images = []
    for img in soup.find_all("img"):
        src = img.get("src", "").strip()
        if src:
            full_src = urljoin(base_url, src)
            images.append({
                "src": full_src,
                "alt": img.get("alt", "").strip(),
                "title": img.get("title", "").strip(),
            })
    return images[:30]


def _extract_json_ld(soup: BeautifulSoup) -> list[dict]:
    """Extrae datos estructurados JSON-LD si existen en la página."""
    structured = []
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string)
            structured.append(data)
        except Exception:
            pass
    return structured


# ============================================================
# SCRAPER DE NOTICIAS (PAGINADO)
# ============================================================

def scrape_news_listing(max_pages: int = None) -> list[dict]:
    """
    Scrapea el archivo de noticias de Manuelita con paginación.
    Extrae listado de artículos (título, fecha, resumen, URL).
    """
    max_p = max_pages or scraping_cfg.max_pages_web
    news_base = target_cfg.pages["noticias"]
    articles = []
    seen_urls = set()

    for page_num in range(1, max_p + 1):
        # WordPress usa /page/N/ para paginación
        page_url = news_base if page_num == 1 else f"{news_base}page/{page_num}/"
        logger.info(f"Noticias — página {page_num}: {page_url}")

        response = safe_get(page_url)
        if not response or response.status_code == 404:
            logger.info(f"Sin más páginas de noticias (página {page_num})")
            break

        soup = BeautifulSoup(response.text, "lxml")

        # Detectar artículos en la página
        article_items = (
            soup.find_all("article") or
            soup.find_all(class_=lambda c: c and "post" in c.lower()) or
            soup.find_all("li", class_=lambda c: c and "post" in str(c).lower())
        )

        if not article_items:
            logger.info(f"No se encontraron artículos en página {page_num}")
            break

        new_count = 0
        for item in article_items:
            # Título y URL
            title_tag = item.find(["h1", "h2", "h3", "h4"])
            link_tag = item.find("a", href=True)
            date_tag = item.find(["time", "span"],
                                  class_=lambda c: c and "date" in str(c).lower())

            if not title_tag or not link_tag:
                continue

            article_url = urljoin(news_base, link_tag["href"])
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)

            # Resumen/excerpt
            excerpt = ""
            excerpt_tag = item.find(["p", "div"],
                                     class_=lambda c: c and "excerpt" in str(c).lower())
            if excerpt_tag:
                excerpt = clean_text(excerpt_tag.get_text())

            articles.append({
                "title": clean_text(title_tag.get_text()),
                "url": article_url,
                "date": date_tag.get_text(strip=True) if date_tag else None,
                "excerpt": excerpt,
                "source": "noticias_listado",
            })
            new_count += 1

        logger.info(f"Artículos encontrados en página {page_num}: {new_count}")

        if new_count == 0:
            break

        polite_delay()

    logger.success(f"Total artículos de noticias descubiertos: {len(articles)}")
    return articles


def scrape_news_article(url: str) -> dict:
    """
    Scrapea el contenido completo de un artículo de noticias individual.
    """
    return scrape_page(url, page_key="noticia")


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def run_website_scraper(pages: list[str] = None, scrape_all: bool = False) -> list[dict]:
    """
    Ejecuta el scraper del sitio web oficial de Manuelita.

    Args:
        pages: Lista de keys de páginas a scrapear (ej: ["perfil", "historia"])
        scrape_all: Si True, scrapea todas las páginas conocidas

    Returns:
        Lista de documentos extraídos
    """
    setup_logging("scrape_website")
    paths_cfg.ensure_all()

    logger.info("=" * 60)
    logger.info("INICIO: Scraper sitio oficial — Manuelita Agroindustrial")
    logger.info("=" * 60)

    results = []
    target_pages = target_cfg.pages

    if scrape_all:
        selected_pages = target_pages
    elif pages:
        selected_pages = {k: v for k, v in target_pages.items() if k in pages}
    else:
        # Por defecto: scrapear páginas de alta prioridad
        priority_keys = ["home", "perfil", "historia", "presencia", "plataformas", "sostenibilidad"]
        selected_pages = {k: v for k, v in target_pages.items() if k in priority_keys}

    logger.info(f"Páginas objetivo: {list(selected_pages.keys())}")

    for key, url in selected_pages.items():
        try:
            result = scrape_page(url, page_key=key)
            results.append(result)
        except Exception as e:
            logger.error(f"Error scrapeando [{key}] {url}: {e}")
            results.append({"url": url, "page_key": key, "status": "error", "error": str(e)})
        finally:
            polite_delay()

    # Resumen final
    successful = [r for r in results if r.get("status") != "error"]
    logger.success(f"Scraping completado: {len(successful)}/{len(results)} páginas exitosas")

    # Guardar índice de sesión
    index_path = paths_cfg.web() / f"_index_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json({
        "session_at": now_iso(),
        "total_pages": len(results),
        "successful": len(successful),
        "pages": [{"key": r.get("page_key"), "url": r.get("url"),
                   "words": r.get("word_count", 0), "id": r.get("id")}
                  for r in results],
    }, index_path)

    return results


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper sitio oficial Manuelita")
    parser.add_argument("--page", nargs="+",
                        choices=list(target_cfg.pages.keys()),
                        help="Páginas específicas a scrapear")
    parser.add_argument("--all", action="store_true",
                        help="Scrapear todas las páginas conocidas")
    args = parser.parse_args()
    run_website_scraper(pages=args.page, scrape_all=args.all)
