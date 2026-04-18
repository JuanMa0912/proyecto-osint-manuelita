"""
scrape_news.py — Scraper de prensa y noticias externas sobre Manuelita.

Fuentes cubiertas:
  - Google News RSS (búsqueda: "Manuelita agroindustrial")
  - Portafolio.co
  - Semana.com
  - ElPais.com.co
  - Wikipedia API (contenido estructurado, libre de restricciones)
  - newspaper3k para extracción de artículos completos

Salida:
  - data_raw/news/{slug}.json — artículo estructurado
  - data_processed/json/news_index.json — índice de noticias

Uso:
  python -m src.scrapers.scrape_news
  python -m src.scrapers.scrape_news --source portafolio semana
  python -m src.scrapers.scrape_news --rss-only
"""

import argparse
import re
from datetime import datetime
from urllib.parse import urljoin, quote_plus

import feedparser
from bs4 import BeautifulSoup
from loguru import logger

try:
    from newspaper import Article
    NEWSPAPER_AVAILABLE = True
except ImportError:
    NEWSPAPER_AVAILABLE = False
    logger.warning("newspaper3k no disponible. Usando extractor básico.")

from src.utils.config import paths_cfg, scraping_cfg
from src.utils.utils import (
    safe_get, save_json, clean_text, url_to_slug, now_iso,
    setup_logging, polite_delay, generate_doc_id, content_hash,
)


# ============================================================
# RSS / GOOGLE NEWS
# ============================================================

GOOGLE_NEWS_RSS_TEMPLATE = (
    "https://news.google.com/rss/search?"
    "q={query}&hl=es-419&gl=CO&ceid=CO:es-419"
)

NEWS_QUERIES = [
    "Manuelita+agroindustrial",
    "Ingenio+Manuelita+Colombia",
    "Manuelita+azucar+Colombia",
    "Manuelita+sostenibilidad",
    "Agroindustrial+Laredo+Manuelita",
]


def scrape_google_news_rss(query: str = "Manuelita+agroindustrial",
                            max_items: int = 50) -> list[dict]:
    """
    Extrae artículos de Google News RSS para una query específica.
    Google News RSS es público y no requiere autenticación.
    """
    rss_url = GOOGLE_NEWS_RSS_TEMPLATE.format(query=query)
    logger.info(f"Leyendo Google News RSS: {rss_url}")

    feed = feedparser.parse(rss_url)
    articles = []

    for entry in feed.entries[:max_items]:
        article = {
            "title": getattr(entry, "title", ""),
            "url": getattr(entry, "link", ""),
            "published": getattr(entry, "published", None),
            "source_name": getattr(entry, "source", {}).get("title", "Google News"),
            "summary": clean_text(getattr(entry, "summary", "")),
            "query": query,
            "captured_at": now_iso(),
            "source_type": "prensa",
        }
        if article["url"]:
            articles.append(article)

    logger.info(f"RSS [{query}]: {len(articles)} artículos encontrados")
    return articles


def scrape_all_rss() -> list[dict]:
    """Scrapea todos los feeds RSS de noticias configurados."""
    all_articles = []
    seen_urls = set()

    for query in NEWS_QUERIES:
        articles = scrape_google_news_rss(query)
        for art in articles:
            if art["url"] not in seen_urls:
                seen_urls.add(art["url"])
                all_articles.append(art)
        polite_delay(1, 2)

    logger.info(f"Total artículos RSS únicos: {len(all_articles)}")
    return all_articles


# ============================================================
# EXTRACTOR DE ARTÍCULO COMPLETO
# ============================================================

def extract_article_content(url: str) -> dict:
    """
    Extrae el contenido completo de un artículo de prensa.
    Usa newspaper3k si está disponible, con fallback a BeautifulSoup.
    """
    captured_at = now_iso()
    result = {
        "url": url,
        "captured_at": captured_at,
        "source_type": "prensa",
        "extraction_method": None,
        "title": "",
        "authors": [],
        "publish_date": None,
        "text": "",
        "summary": "",
        "keywords": [],
        "images": [],
        "status": "error",
    }

    # Método 1: newspaper3k (más robusto para artículos)
    if NEWSPAPER_AVAILABLE:
        try:
            article = Article(url, language="es")
            article.download()
            article.parse()
            article.nlp()

            result.update({
                "title": article.title,
                "authors": article.authors,
                "publish_date": str(article.publish_date) if article.publish_date else None,
                "text": clean_text(article.text),
                "summary": article.summary,
                "keywords": article.keywords,
                "images": list(article.images)[:10],
                "extraction_method": "newspaper3k",
                "status": "ok",
                "word_count": len(article.text.split()),
                "content_hash": content_hash(article.text),
            })
            logger.info(f"Artículo extraído (newspaper3k): {article.title[:60]}")
            return result

        except Exception as e:
            logger.warning(f"newspaper3k falló para {url}: {e}. Usando fallback.")

    # Método 2: BeautifulSoup (fallback)
    response = safe_get(url)
    if not response:
        return result

    soup = BeautifulSoup(response.text, "lxml")

    # Título
    title = ""
    for tag in ["h1", "h2"]:
        t = soup.find(tag)
        if t:
            title = clean_text(t.get_text())
            break
    if not title and soup.title:
        title = clean_text(soup.title.string or "")

    # Texto principal
    article_tag = (
        soup.find("article") or
        soup.find(class_=re.compile(r"article|post|content|entry", re.I)) or
        soup.body
    )
    text = clean_text(article_tag.get_text(separator="\n")) if article_tag else ""

    # Fecha
    date_tag = soup.find("time")
    date_str = date_tag.get("datetime", date_tag.get_text(strip=True)) if date_tag else None

    result.update({
        "title": title,
        "text": text,
        "publish_date": date_str,
        "extraction_method": "beautifulsoup",
        "status": "ok",
        "word_count": len(text.split()),
        "content_hash": content_hash(text),
    })
    logger.info(f"Artículo extraído (BS4): {title[:60]}")
    return result


# ============================================================
# WIKIPEDIA API
# ============================================================

def scrape_wikipedia(lang: str = "es") -> dict:
    """
    Obtiene el contenido de la página de Wikipedia de Manuelita
    usando la API REST oficial de Wikipedia (sin restricciones de ToS).
    """
    base_api = f"https://{lang}.wikipedia.org/api/rest_v1"
    page_title = "Manuelita"

    # Intentar en español primero, luego inglés
    for language, title in [("es", "Manuelita"), ("en", "Manuelita")]:
        api_url = f"https://{language}.wikipedia.org/api/rest_v1/page/summary/{title}"
        try:
            response = safe_get(api_url)
            if response and response.status_code == 200:
                data = response.json()
                logger.info(f"Wikipedia [{language}]: {data.get('title', '')}")
                return {
                    "id": generate_doc_id("wikipedia", api_url, now_iso()),
                    "title": data.get("title", ""),
                    "url": data.get("content_urls", {}).get("desktop", {}).get("page", ""),
                    "extract": data.get("extract", ""),
                    "description": data.get("description", ""),
                    "thumbnail": data.get("thumbnail", {}).get("source", ""),
                    "language": language,
                    "source_type": "tercero",
                    "source_name": f"Wikipedia ({language})",
                    "captured_at": now_iso(),
                    "status": "ok",
                }
        except Exception as e:
            logger.warning(f"Wikipedia API [{language}] falló: {e}")

    return {"status": "error", "source_name": "Wikipedia"}


# ============================================================
# SCRAPER PORTAFOLIO.CO
# ============================================================

def scrape_portafolio(max_articles: int = 20) -> list[dict]:
    """
    Busca artículos sobre Manuelita en Portafolio.co.
    Portafolio es un medio colombiano de economía y empresas.
    Solo extrae artículos públicos (sin paywall).
    """
    search_url = "https://www.portafolio.co/?s=Manuelita"
    logger.info(f"Buscando en Portafolio.co: {search_url}")

    response = safe_get(search_url)
    if not response:
        return []

    soup = BeautifulSoup(response.text, "lxml")
    articles = []

    # Portafolio usa estructura de WordPress típica
    for item in soup.find_all(["article", "div"],
                               class_=lambda c: c and "article" in str(c).lower())[:max_articles]:
        link = item.find("a", href=True)
        title_tag = item.find(["h1", "h2", "h3", "h4"])
        date_tag = item.find("time")

        if not link or not title_tag:
            continue

        articles.append({
            "title": clean_text(title_tag.get_text()),
            "url": link["href"],
            "date": date_tag.get_text(strip=True) if date_tag else None,
            "source_name": "Portafolio.co",
            "source_type": "prensa",
            "captured_at": now_iso(),
        })

    logger.info(f"Portafolio.co: {len(articles)} artículos encontrados")
    return articles


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_news_scraper(sources: list[str] = None, rss_only: bool = False,
                     max_full_articles: int = 30) -> dict:
    """
    Ejecuta el scraper de noticias completo.

    Args:
        sources: Lista de fuentes específicas ("rss", "wikipedia", "portafolio")
        rss_only: Si True, solo usar RSS sin extraer artículos completos
        max_full_articles: Máximo de artículos completos a extraer

    Returns:
        Diccionario con resumen y datos de noticias
    """
    setup_logging("scrape_news")
    paths_cfg.ensure_all()

    logger.info("=" * 60)
    logger.info("INICIO: Scraper de noticias — Manuelita Agroindustrial")
    logger.info("=" * 60)

    all_news = []
    full_articles = []

    run_all = not sources
    active_sources = sources or ["rss", "wikipedia", "portafolio"]

    # 1. RSS
    if "rss" in active_sources or run_all:
        rss_articles = scrape_all_rss()
        all_news.extend(rss_articles)

    # 2. Wikipedia
    if "wikipedia" in active_sources or run_all:
        wiki = scrape_wikipedia()
        if wiki.get("status") == "ok":
            all_news.append(wiki)
            # Guardar Wikipedia aparte
            wiki_path = paths_cfg.news() / "wikipedia_manuelita.json"
            save_json(wiki, wiki_path)

    # 3. Portafolio
    if "portafolio" in active_sources or run_all:
        portafolio_articles = scrape_portafolio()
        all_news.extend(portafolio_articles)

    # 4. Extracción de artículos completos (si no es rss_only)
    if not rss_only:
        news_to_extract = [n for n in all_news if n.get("url") and n.get("status") != "ok"][:max_full_articles]
        logger.info(f"Extrayendo contenido completo de {len(news_to_extract)} artículos...")

        seen_hashes = set()
        for news_item in news_to_extract:
            url = news_item["url"]
            try:
                full = extract_article_content(url)
                if full.get("status") == "ok":
                    # Deduplicar por hash de contenido
                    h = full.get("content_hash", "")
                    if h and h not in seen_hashes:
                        seen_hashes.add(h)
                        full["source_type"] = news_item.get("source_type", "prensa")
                        full["source_name"] = news_item.get("source_name", "prensa")
                        full_articles.append(full)

                        # Guardar artículo individual
                        slug = url_to_slug(url)
                        article_path = paths_cfg.news() / f"{slug}.json"
                        save_json(full, article_path)

            except Exception as e:
                logger.error(f"Error extrayendo artículo {url}: {e}")
            finally:
                polite_delay()

    # Índice final
    index = {
        "captured_at": now_iso(),
        "total_news_items": len(all_news),
        "total_full_articles": len(full_articles),
        "sources_used": active_sources,
        "news_listing": all_news,
        "full_articles_index": [
            {"url": a["url"], "title": a["title"], "words": a.get("word_count", 0)}
            for a in full_articles
        ],
    }

    save_json(index, paths_cfg.json_out() / "news_index.json")
    logger.success(f"Scraping de noticias completado. Total: {len(all_news)} items, "
                   f"{len(full_articles)} artículos completos.")

    return index


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper de noticias — Manuelita")
    parser.add_argument("--source", nargs="+",
                        choices=["rss", "wikipedia", "portafolio", "semana"],
                        help="Fuentes específicas a scrapear")
    parser.add_argument("--rss-only", action="store_true",
                        help="Solo extraer listados RSS, sin artículos completos")
    parser.add_argument("--max-articles", type=int, default=30,
                        help="Máximo de artículos completos a extraer")
    args = parser.parse_args()
    run_news_scraper(sources=args.source, rss_only=args.rss_only,
                     max_full_articles=args.max_articles)
