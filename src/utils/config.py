"""
config.py — Configuración central del proyecto OSINT Manuelita
Lee variables desde .env y expone objetos de configuración tipados.
"""

import os
from pathlib import Path
from dataclasses import dataclass, field
from dotenv import load_dotenv

# Cargar .env desde la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]
load_dotenv(BASE_DIR / ".env")


@dataclass
class ScrapingConfig:
    """Parámetros de comportamiento del scraper."""
    delay_min: float = float(os.getenv("SCRAPING_DELAY_MIN", 2.0))
    delay_max: float = float(os.getenv("SCRAPING_DELAY_MAX", 4.0))
    max_pages_web: int = int(os.getenv("MAX_PAGES_WEB", 50))
    max_pages_news: int = int(os.getenv("MAX_PAGES_NEWS", 100))
    max_videos_youtube: int = int(os.getenv("MAX_VIDEOS_YOUTUBE", 200))
    request_timeout: int = int(os.getenv("REQUEST_TIMEOUT", 15))
    max_retries: int = int(os.getenv("MAX_RETRIES", 3))


@dataclass
class PathConfig:
    """Rutas absolutas del proyecto."""
    base: Path = BASE_DIR
    data_raw: Path = BASE_DIR / "data_raw"
    data_processed: Path = BASE_DIR / "data_processed"
    logs: Path = BASE_DIR / "logs"
    reports: Path = BASE_DIR / "reports"
    templates: Path = BASE_DIR / "templates"

    def web(self) -> Path:
        return self.data_raw / "web"

    def social(self) -> Path:
        return self.data_raw / "social"

    def youtube(self) -> Path:
        return self.data_raw / "youtube"

    def reviews(self) -> Path:
        return self.data_raw / "reviews"

    def news(self) -> Path:
        return self.data_raw / "news"

    def pdfs(self) -> Path:
        return self.data_raw / "pdfs"

    def markdown(self) -> Path:
        return self.data_processed / "markdown"

    def json_out(self) -> Path:
        return self.data_processed / "json"

    def tables(self) -> Path:
        return self.data_processed / "tables"

    def ensure_all(self):
        """Crea todos los directorios si no existen."""
        for attr in vars(self).values():
            if isinstance(attr, Path):
                attr.mkdir(parents=True, exist_ok=True)
        for subdir in [self.web(), self.social(), self.youtube(),
                        self.reviews(), self.news(), self.pdfs(),
                        self.markdown(), self.json_out(), self.tables()]:
            subdir.mkdir(parents=True, exist_ok=True)


@dataclass
class TargetConfig:
    """Datos de la empresa objetivo: Manuelita."""
    company: str = os.getenv("TARGET_COMPANY", "Manuelita")
    domain: str = os.getenv("TARGET_DOMAIN", "manuelita.com")
    base_url: str = os.getenv("TARGET_URL", "https://www.manuelita.com")

    # URLs internas confirmadas
    pages: dict = field(default_factory=lambda: {
        "home":             "https://www.manuelita.com/",
        "perfil":           "https://www.manuelita.com/perfil-corporativo/",
        "historia":         "https://www.manuelita.com/historia/",
        "presencia":        "https://www.manuelita.com/presencia-regional/",
        "plataformas":      "https://www.manuelita.com/plataformas-de-negocios/",
        "sostenibilidad":   "https://www.manuelita.com/sostenibilidad/",
        "noticias":         "https://www.manuelita.com/manuelita-noticias/",
        "economico":        "https://www.manuelita.com/economico/",
        "innovacion":       "https://manuelitainnova.com/",
        "talento":          "https://grupomanuelita.na.teamtailor.com/",
    })

    # PDFs públicos confirmados
    pdfs: dict = field(default_factory=lambda: {
        "sostenibilidad_2023_2024": "https://www.manuelita.com/wp-content/uploads/2025/06/Informe-de-Sostenibilidad-Manuelita-2023-2024.pdf",
        "sostenibilidad_2021_2022": "https://www.manuelita.com/wp-content/uploads/2023/06/Informe_Sostenibilidad_Manuelita-2021-2022.pdf",
    })

    # Redes sociales confirmadas
    social: dict = field(default_factory=lambda: {
        "linkedin":   "https://co.linkedin.com/company/manuelita",
        "instagram":  "https://www.instagram.com/manuelitaagroindustria/",
        "facebook":   "https://www.facebook.com/ManuelitaAgroindustria/",
        "youtube":    "https://www.youtube.com/channel/UCanNTjBY24t7fID3tj0WfTw",
    })


@dataclass
class APIConfig:
    """Credenciales de APIs externas."""
    youtube_api_key: str = os.getenv("YOUTUBE_API_KEY", "")
    youtube_channel_id: str = os.getenv("YOUTUBE_CHANNEL_ID", "UCanNTjBY24t7fID3tj0WfTw")
    meta_access_token: str = os.getenv("META_ACCESS_TOKEN", "")
    facebook_page_id: str = os.getenv("FACEBOOK_PAGE_ID", "ManuelitaAgroindustria")


@dataclass
class NLPConfig:
    """Configuración del pipeline NLP."""
    spacy_model: str = os.getenv("SPACY_MODEL", "es_core_news_lg")
    dedup_threshold: float = float(os.getenv("DEDUP_THRESHOLD", 0.85))


# ---- Instancias globales ----
scraping_cfg = ScrapingConfig()
paths_cfg = PathConfig()
target_cfg = TargetConfig()
api_cfg = APIConfig()
nlp_cfg = NLPConfig()
