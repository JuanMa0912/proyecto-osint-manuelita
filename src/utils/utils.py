"""
utils.py — Funciones utilitarias reutilizables para todo el proyecto OSINT Manuelita.
Incluye: logging, delays, user agents, requests seguros, slugs, timestamps, robots.txt.
"""

import time
import random
import json
import hashlib
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
from typing import Optional, Any

import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential, before_log, after_log
from slugify import slugify

from src.utils.config import scraping_cfg, paths_cfg

# ============================================================
# CONFIGURACIÓN DE LOGGING
# ============================================================

def setup_logging(log_name: str = "scraper") -> None:
    """
    Configura loguru: consola + archivo rotativo en /logs/.
    Llamar al inicio de cada script.
    """
    paths_cfg.logs.mkdir(parents=True, exist_ok=True)
    log_file = paths_cfg.logs / f"{log_name}_{timestamp_slug()}.log"

    logger.remove()  # Eliminar handler por defecto
    logger.add(
        sink=log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="30 days",
        encoding="utf-8",
    )
    logger.add(
        sink=lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | {message}",
        level="INFO",
        colorize=True,
    )
    logger.info(f"Logging iniciado → {log_file}")


# ============================================================
# TIMESTAMPS Y SLUGS
# ============================================================

def now_iso() -> str:
    """Retorna timestamp ISO 8601 en UTC."""
    return datetime.now(timezone.utc).isoformat()


def timestamp_slug() -> str:
    """Retorna timestamp compacto para nombres de archivo."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def url_to_slug(url: str) -> str:
    """Convierte una URL en un slug seguro para nombre de archivo."""
    parsed = urlparse(url)
    path = parsed.path.strip("/").replace("/", "_") or "index"
    return slugify(f"{parsed.netloc}_{path}", max_length=100)


# ============================================================
# USER AGENTS
# ============================================================

_ua = None

def get_random_user_agent() -> str:
    """
    Retorna un User-Agent real aleatorio.
    Solo usar cuando sea ético y permitido por robots.txt.
    """
    global _ua
    try:
        if _ua is None:
            _ua = UserAgent()
        return _ua.random
    except Exception:
        # Fallback a un User-Agent fijo si fake-useragent falla
        return (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        )


def get_default_headers(referer: str = "") -> dict:
    """Construye headers HTTP realistas para requests."""
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "es-CO,es;q=0.9,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }
    if referer:
        headers["Referer"] = referer
    return headers


# ============================================================
# ROBOTS.TXT
# ============================================================

_robots_cache: dict[str, RobotFileParser] = {}

def can_fetch(url: str, user_agent: str = "*") -> bool:
    """
    Verifica si una URL puede ser scrapeada según robots.txt.
    Cachea el parser por dominio para evitar múltiples requests.
    """
    parsed = urlparse(url)
    base = f"{parsed.scheme}://{parsed.netloc}"

    if base not in _robots_cache:
        robots_url = urljoin(base, "/robots.txt")
        rp = RobotFileParser()
        rp.set_url(robots_url)
        try:
            rp.read()
            _robots_cache[base] = rp
            logger.info(f"robots.txt cargado: {robots_url}")
        except Exception as e:
            logger.warning(f"No se pudo leer robots.txt de {base}: {e}. Procediendo con cautela.")
            return True  # Si no se puede leer, asumir permitido con cautela

    return _robots_cache[base].can_fetch(user_agent, url)


# ============================================================
# REQUESTS SEGUROS CON RETRY
# ============================================================

@retry(
    stop=stop_after_attempt(scraping_cfg.max_retries),
    wait=wait_exponential(multiplier=1, min=3, max=15),
    before=before_log(logger, "DEBUG"),
    after=after_log(logger, "DEBUG"),
    reraise=True,
)
def safe_get(url: str, session: Optional[requests.Session] = None,
             extra_headers: Optional[dict] = None) -> Optional[requests.Response]:
    """
    Realiza un GET HTTP seguro con:
    - Verificación de robots.txt
    - Headers realistas
    - Retry automático con backoff exponencial
    - Timeout configurable
    - Logging detallado
    """
    if not can_fetch(url):
        logger.warning(f"BLOQUEADO por robots.txt: {url}")
        return None

    headers = get_default_headers(referer="https://www.google.com/")
    if extra_headers:
        headers.update(extra_headers)

    requester = session or requests
    try:
        response = requester.get(
            url,
            headers=headers,
            timeout=scraping_cfg.request_timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
        logger.info(f"GET {response.status_code} — {url}")
        return response
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP Error {e.response.status_code} en {url}")
        raise
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Error de conexión en {url}: {e}")
        raise
    except requests.exceptions.Timeout:
        logger.error(f"Timeout en {url}")
        raise


def polite_delay(min_sec: float = None, max_sec: float = None) -> None:
    """Pausa cortés entre requests para no sobrecargar el servidor."""
    min_s = min_sec or scraping_cfg.delay_min
    max_s = max_sec or scraping_cfg.delay_max
    delay = random.uniform(min_s, max_s)
    logger.debug(f"Esperando {delay:.2f}s antes del siguiente request...")
    time.sleep(delay)


# ============================================================
# PERSISTENCIA JSON
# ============================================================

def save_json(data: Any, filepath: Path, indent: int = 2) -> None:
    """Guarda datos como JSON con encoding UTF-8."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    logger.info(f"JSON guardado: {filepath}")


def load_json(filepath: Path) -> Any:
    """Carga un archivo JSON."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def save_raw_html(html: str, filepath: Path) -> None:
    """Guarda HTML crudo para trazabilidad."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)
    logger.debug(f"HTML raw guardado: {filepath}")


# ============================================================
# HASHING Y DEDUPLICACIÓN
# ============================================================

def content_hash(text: str) -> str:
    """Genera un hash SHA256 del contenido para deduplicación exacta."""
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()[:16]


def generate_doc_id(source_type: str, url: str, captured_at: str) -> str:
    """
    Genera un ID único y reproducible para cada documento.
    Formato: manuelita_{source_type}_{url_hash}_{date}
    """
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    date_part = captured_at[:10].replace("-", "")
    return f"manuelita_{source_type}_{url_hash}_{date_part}"


# ============================================================
# LIMPIEZA DE TEXTO
# ============================================================

def clean_text(text: str) -> str:
    """Limpia texto HTML extraído: espacios, caracteres especiales, líneas vacías."""
    if not text:
        return ""
    # Eliminar caracteres de control excepto newlines y tabs
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Normalizar espacios múltiples
    text = re.sub(r" {2,}", " ", text)
    # Normalizar líneas vacías múltiples
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_main_text(soup: BeautifulSoup) -> str:
    """
    Extrae el texto principal de una página BeautifulSoup,
    eliminando scripts, estilos y nav.
    """
    # Eliminar elementos no deseados
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "aside", "form", "noscript", "iframe"]):
        tag.decompose()

    # Intentar extraer el contenido principal
    main = (
        soup.find("main") or
        soup.find("article") or
        soup.find(id=re.compile(r"content|main|article", re.I)) or
        soup.find(class_=re.compile(r"content|main|article|entry", re.I)) or
        soup.body
    )
    if main:
        return clean_text(main.get_text(separator="\n"))
    return clean_text(soup.get_text(separator="\n"))


def extract_metadata_from_soup(soup: BeautifulSoup, url: str) -> dict:
    """Extrae metadatos SEO básicos de una página HTML."""
    meta = {
        "title": "",
        "description": "",
        "og_title": "",
        "og_description": "",
        "og_image": "",
        "canonical": url,
        "lang": "",
    }

    # Título
    if soup.title:
        meta["title"] = soup.title.string.strip() if soup.title.string else ""

    # Meta description
    desc_tag = soup.find("meta", attrs={"name": "description"})
    if desc_tag:
        meta["description"] = desc_tag.get("content", "").strip()

    # Open Graph
    og_title = soup.find("meta", property="og:title")
    if og_title:
        meta["og_title"] = og_title.get("content", "").strip()

    og_desc = soup.find("meta", property="og:description")
    if og_desc:
        meta["og_description"] = og_desc.get("content", "").strip()

    og_img = soup.find("meta", property="og:image")
    if og_img:
        meta["og_image"] = og_img.get("content", "").strip()

    # Canonical
    canonical = soup.find("link", rel="canonical")
    if canonical:
        meta["canonical"] = canonical.get("href", url)

    # Idioma
    html_tag = soup.find("html")
    if html_tag:
        meta["lang"] = html_tag.get("lang", "es")

    return meta
