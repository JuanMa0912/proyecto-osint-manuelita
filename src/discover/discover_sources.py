"""
discover_sources.py — Módulo de reconocimiento y descubrimiento de fuentes para Manuelita.

Funciones:
  - Crawl del sitemap XML del sitio oficial
  - Descubrimiento de links internos desde la homepage
  - Búsqueda de PDFs enlazados públicamente
  - Verificación de redes sociales confirmadas
  - Exportación del mapa de fuentes a JSON

Uso:
  python -m src.discover.discover_sources
  python -m src.discover.discover_sources --output sources_map.json
"""

import argparse
import re
from pathlib import Path
from urllib.parse import urljoin, urlparse
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup
from loguru import logger

from src.utils.config import target_cfg, paths_cfg
from src.utils.utils import safe_get, save_json, now_iso, setup_logging, can_fetch


# ============================================================
# CONSTANTES
# ============================================================

SITEMAP_URLS = [
    "https://www.manuelita.com/sitemap.xml",
    "https://www.manuelita.com/sitemap_index.xml",
    "https://manuelitainnova.com/sitemap.xml",
]

SOCIAL_ACCOUNTS = {
    "linkedin":  "https://co.linkedin.com/company/manuelita",
    "instagram": "https://www.instagram.com/manuelitaagroindustria/",
    "facebook":  "https://www.facebook.com/ManuelitaAgroindustria/",
    "youtube":   "https://www.youtube.com/channel/UCanNTjBY24t7fID3tj0WfTw",
}

NEWS_SOURCES = {
    "portafolio":    "https://www.portafolio.co",
    "semana":        "https://www.semana.com",
    "elpais_cali":   "https://www.elpais.com.co",
    "revistaialimentos": "https://www.revistaialimentos.com",
    "wikipedia_en":  "https://en.wikipedia.org/wiki/Manuelita",
    "procolombia":   "https://b2bmarketplaceplus.procolombia.co/en/agro-industry/agroindustrial/ingenio-manuelita-sa.aspx",
}

CONFIRMED_PDFS = {
    "informe_sostenibilidad_2023_2024": "https://www.manuelita.com/wp-content/uploads/2025/06/Informe-de-Sostenibilidad-Manuelita-2023-2024.pdf",
    "informe_sostenibilidad_2021_2022": "https://www.manuelita.com/wp-content/uploads/2023/06/Informe_Sostenibilidad_Manuelita-2021-2022.pdf",
    "laredo_sostenibilidad":            "https://agroindustriallaredo.com/informes-de-sostenibilidad/",
}


# ============================================================
# DESCUBRIMIENTO DE SITEMAP
# ============================================================

def discover_from_sitemap(sitemap_url: str) -> list[dict]:
    """
    Intenta leer un sitemap XML y extraer las URLs listadas.
    Retorna lista de dicts con url, lastmod, priority.
    """
    urls = []
    logger.info(f"Intentando leer sitemap: {sitemap_url}")

    response = safe_get(sitemap_url)
    if not response:
        logger.warning(f"No se pudo acceder al sitemap: {sitemap_url}")
        return urls

    soup = BeautifulSoup(response.content, "lxml-xml")

    # Sitemap índice → múltiples sitemaps anidados
    sitemap_tags = soup.find_all("sitemap")
    if sitemap_tags:
        logger.info(f"Sitemap índice detectado con {len(sitemap_tags)} sub-sitemaps")
        for s in sitemap_tags:
            loc = s.find("loc")
            if loc:
                sub_urls = discover_from_sitemap(loc.text.strip())
                urls.extend(sub_urls)
        return urls

    # Sitemap regular → lista de URLs
    url_tags = soup.find_all("url")
    for tag in url_tags:
        loc = tag.find("loc")
        lastmod = tag.find("lastmod")
        priority = tag.find("priority")
        if loc:
            urls.append({
                "url": loc.text.strip(),
                "lastmod": lastmod.text.strip() if lastmod else None,
                "priority": float(priority.text.strip()) if priority else 0.5,
                "source": "sitemap",
            })

    logger.info(f"URLs encontradas en sitemap: {len(urls)}")
    return urls


# ============================================================
# CRAWL DE LINKS INTERNOS
# ============================================================

def discover_internal_links(base_url: str, max_depth: int = 2) -> list[dict]:
    """
    Crawl recursivo de links internos del sitio oficial.
    Respeta robots.txt y max_depth para limitar el scope.
    """
    domain = urlparse(base_url).netloc
    visited = set()
    to_visit = [(base_url, 0)]
    found_urls = []

    while to_visit:
        current_url, depth = to_visit.pop(0)

        if current_url in visited or depth > max_depth:
            continue
        visited.add(current_url)

        if not can_fetch(current_url):
            logger.debug(f"robots.txt bloquea: {current_url}")
            continue

        response = safe_get(current_url)
        if not response:
            continue

        soup = BeautifulSoup(response.text, "lxml")
        page_title = soup.title.string.strip() if soup.title and soup.title.string else ""

        found_urls.append({
            "url": current_url,
            "title": page_title,
            "depth": depth,
            "source": "crawl_interno",
        })

        # Encontrar todos los links internos
        if depth < max_depth:
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"].strip()
                full_url = urljoin(base_url, href)
                parsed = urlparse(full_url)

                # Solo seguir links del mismo dominio, ignorar anclas y params
                if (parsed.netloc == domain and
                        full_url not in visited and
                        not href.startswith("#") and
                        not href.startswith("mailto:") and
                        not href.startswith("tel:") and
                        parsed.path not in ["/wp-login.php", "/wp-admin/"]):
                    to_visit.append((full_url, depth + 1))

        from src.utils.utils import polite_delay
        polite_delay()

    logger.info(f"Links internos descubiertos: {len(found_urls)}")
    return found_urls


# ============================================================
# DETECCIÓN DE PDFs EN UNA PÁGINA
# ============================================================

def find_pdf_links(url: str) -> list[dict]:
    """
    Escanea una URL en busca de enlaces a PDFs públicos.
    """
    pdfs = []
    response = safe_get(url)
    if not response:
        return pdfs

    soup = BeautifulSoup(response.text, "lxml")
    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()
        if href.lower().endswith(".pdf"):
            full_url = urljoin(url, href)
            pdfs.append({
                "url": full_url,
                "anchor_text": a_tag.get_text(strip=True),
                "found_on": url,
                "source": "pdf_link",
            })

    logger.info(f"PDFs encontrados en {url}: {len(pdfs)}")
    return pdfs


# ============================================================
# VERIFICACIÓN DE REDES SOCIALES
# ============================================================

def verify_social_accounts() -> list[dict]:
    """
    Verifica el estado (accesible / bloqueado) de las cuentas sociales conocidas.
    No scrapea contenido — solo verifica existencia y headers.
    """
    results = []
    for platform, url in SOCIAL_ACCOUNTS.items():
        try:
            resp = requests.head(url, timeout=10, allow_redirects=True,
                                  headers={"User-Agent": "Mozilla/5.0"})
            status = "accesible" if resp.status_code < 400 else f"error_{resp.status_code}"
        except Exception as e:
            status = f"error: {str(e)[:50]}"

        results.append({
            "platform": platform,
            "url": url,
            "status": status,
            "scraping_method": _get_social_method(platform),
            "verified_at": now_iso(),
        })
        logger.info(f"Social [{platform}]: {status} — {url}")

    return results


def _get_social_method(platform: str) -> str:
    """Retorna el método de extracción recomendado para cada red social."""
    methods = {
        "linkedin":  "API oficial o extracción manual (ToS restringe scraping)",
        "instagram": "Meta Graph API (requiere app aprobada)",
        "facebook":  "Meta Graph API (requiere app aprobada)",
        "youtube":   "YouTube Data API v3 (gratuita, cuota 10K unidades/día)",
    }
    return methods.get(platform, "manual")


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_discovery(output_file: str = None) -> dict:
    """
    Ejecuta el proceso completo de descubrimiento de fuentes para Manuelita.
    Retorna un diccionario con el mapa completo de fuentes.
    """
    setup_logging("discover_sources")
    logger.info("=" * 60)
    logger.info("INICIO: Descubrimiento de fuentes — Manuelita Agroindustrial")
    logger.info("=" * 60)

    sources_map = {
        "company": target_cfg.company,
        "base_url": target_cfg.base_url,
        "discovered_at": now_iso(),
        "sitemap_urls": [],
        "internal_links": [],
        "pdf_links": list(CONFIRMED_PDFS.values()),
        "social_accounts": [],
        "news_sources": list(NEWS_SOURCES.values()),
        "confirmed_pages": list(target_cfg.pages.values()),
        "summary": {},
    }

    # 1. Intentar sitemap
    all_sitemap_urls = []
    for sitemap_url in SITEMAP_URLS:
        urls = discover_from_sitemap(sitemap_url)
        all_sitemap_urls.extend(urls)
    sources_map["sitemap_urls"] = all_sitemap_urls

    # 2. Crawl de links internos (solo 1 nivel para no sobrecargar)
    if can_fetch(target_cfg.base_url):
        internal = discover_internal_links(target_cfg.base_url, max_depth=1)
        sources_map["internal_links"] = internal
    else:
        logger.warning("robots.txt bloquea el crawl del home. Usando URLs confirmadas.")

    # 3. PDFs adicionales desde página de sostenibilidad
    pdf_sostenibilidad = find_pdf_links(target_cfg.pages["sostenibilidad"])
    extra_pdfs = [p["url"] for p in pdf_sostenibilidad if p["url"] not in sources_map["pdf_links"]]
    sources_map["pdf_links"].extend(extra_pdfs)

    # 4. Verificar redes sociales
    sources_map["social_accounts"] = verify_social_accounts()

    # 5. Resumen
    sources_map["summary"] = {
        "total_sitemap_urls": len(sources_map["sitemap_urls"]),
        "total_internal_links": len(sources_map["internal_links"]),
        "total_pdf_links": len(sources_map["pdf_links"]),
        "total_social_platforms": len(sources_map["social_accounts"]),
        "total_news_sources": len(sources_map["news_sources"]),
    }

    logger.info(f"Resumen de descubrimiento: {sources_map['summary']}")

    # 6. Guardar resultado
    out_path = paths_cfg.reports / (output_file or f"sources_map_{datetime.now().strftime('%Y%m%d')}.json")
    save_json(sources_map, out_path)
    logger.info(f"Mapa de fuentes guardado en: {out_path}")

    return sources_map


# ============================================================
# EJECUCIÓN DIRECTA
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Descubrimiento de fuentes OSINT — Manuelita")
    parser.add_argument("--output", type=str, default=None,
                        help="Nombre del archivo JSON de salida (en /reports/)")
    args = parser.parse_args()
    run_discovery(output_file=args.output)
