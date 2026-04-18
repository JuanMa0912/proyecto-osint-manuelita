"""
scrape_youtube_metadata.py — Extracción de metadatos del canal oficial de Manuelita en YouTube.

Usa YouTube Data API v3 (gratuita, sin login) para extraer:
  - Información del canal
  - Lista de videos con metadatos (título, descripción, fecha, vistas, duración)
  - Playlists públicas
  - Estadísticas del canal

NO descarga videos. Solo metadatos públicos.

Requiere: YOUTUBE_API_KEY en .env (obtener en Google Cloud Console)

Uso:
  python -m src.scrapers.scrape_youtube_metadata
  python -m src.scrapers.scrape_youtube_metadata --max-videos 100
  python -m src.scrapers.scrape_youtube_metadata --no-api  # Fallback sin API key
"""

import argparse
from datetime import datetime

from loguru import logger

from src.utils.config import api_cfg, paths_cfg, scraping_cfg
from src.utils.utils import (
    safe_get, save_json, clean_text, now_iso,
    setup_logging, polite_delay, generate_doc_id,
)

# Canal oficial confirmado
CHANNEL_ID = "UCanNTjBY24t7fID3tj0WfTw"
CHANNEL_URL = "https://www.youtube.com/channel/UCanNTjBY24t7fID3tj0WfTw"
YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


# ============================================================
# CLIENTE API YOUTUBE DATA v3
# ============================================================

def get_channel_info(api_key: str, channel_id: str) -> dict:
    """
    Obtiene información general del canal de YouTube.
    Endpoint: channels.list
    """
    url = f"{YOUTUBE_API_BASE}/channels"
    params = {
        "key": api_key,
        "id": channel_id,
        "part": "snippet,statistics,brandingSettings",
    }
    response = safe_get(url + "?" + "&".join(f"{k}={v}" for k, v in params.items()))
    if not response:
        return {}

    data = response.json()
    items = data.get("items", [])
    if not items:
        logger.warning(f"Canal no encontrado: {channel_id}")
        return {}

    item = items[0]
    snippet = item.get("snippet", {})
    stats = item.get("statistics", {})
    branding = item.get("brandingSettings", {}).get("channel", {})

    return {
        "channel_id": channel_id,
        "channel_url": CHANNEL_URL,
        "title": snippet.get("title", ""),
        "description": clean_text(snippet.get("description", "")),
        "custom_url": snippet.get("customUrl", ""),
        "country": snippet.get("country", ""),
        "published_at": snippet.get("publishedAt", ""),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        "keywords": branding.get("keywords", ""),
        "statistics": {
            "subscriber_count": stats.get("subscriberCount", "0"),
            "video_count": stats.get("videoCount", "0"),
            "view_count": stats.get("viewCount", "0"),
        },
        "captured_at": now_iso(),
    }


def get_channel_videos(api_key: str, channel_id: str, max_videos: int = 200) -> list[dict]:
    """
    Obtiene la lista completa de videos del canal usando paginación.
    Endpoint: search.list (más eficiente que playlistItems para canal completo)
    """
    videos = []
    page_token = None
    results_per_page = min(50, max_videos)  # YouTube API max: 50 por request

    while len(videos) < max_videos:
        url = f"{YOUTUBE_API_BASE}/search"
        params = {
            "key": api_key,
            "channelId": channel_id,
            "part": "snippet",
            "type": "video",
            "order": "date",
            "maxResults": str(results_per_page),
        }
        if page_token:
            params["pageToken"] = page_token

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        response = safe_get(f"{url}?{query_string}")
        if not response:
            break

        data = response.json()

        # Verificar errores de API (quota, key inválida)
        if "error" in data:
            error = data["error"]
            logger.error(f"YouTube API error: {error.get('message', '')} (código {error.get('code')})")
            break

        for item in data.get("items", []):
            video_id = item.get("id", {}).get("videoId", "")
            snippet = item.get("snippet", {})

            if not video_id:
                continue

            videos.append({
                "video_id": video_id,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "title": snippet.get("title", ""),
                "description": clean_text(snippet.get("description", ""))[:500],
                "published_at": snippet.get("publishedAt", ""),
                "channel_title": snippet.get("channelTitle", ""),
                "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
                "live_broadcast_content": snippet.get("liveBroadcastContent", "none"),
                "captured_at": now_iso(),
            })

        page_token = data.get("nextPageToken")
        if not page_token or len(videos) >= max_videos:
            break

        polite_delay(0.5, 1.0)  # YouTube API tiene cuotas, ser conservador

    logger.info(f"Videos extraídos del canal: {len(videos)}")
    return videos


def get_video_details(api_key: str, video_ids: list[str]) -> list[dict]:
    """
    Obtiene estadísticas detalladas de una lista de video IDs.
    Hasta 50 videos por request (limitación de API).
    """
    details = []

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]
        ids_param = ",".join(batch)

        url = (
            f"{YOUTUBE_API_BASE}/videos"
            f"?key={api_key}"
            f"&id={ids_param}"
            f"&part=statistics,contentDetails,snippet"
        )
        response = safe_get(url)
        if not response:
            continue

        data = response.json()
        for item in data.get("items", []):
            stats = item.get("statistics", {})
            content = item.get("contentDetails", {})
            details.append({
                "video_id": item.get("id", ""),
                "duration": content.get("duration", ""),  # Formato ISO 8601 (PT4M13S)
                "view_count": stats.get("viewCount", "0"),
                "like_count": stats.get("likeCount", "0"),
                "comment_count": stats.get("commentCount", "0"),
                "favorite_count": stats.get("favoriteCount", "0"),
                "definition": content.get("definition", ""),
                "caption": content.get("caption", "false"),
            })

        polite_delay(0.3, 0.7)

    logger.info(f"Detalles de {len(details)} videos obtenidos")
    return details


def get_playlists(api_key: str, channel_id: str) -> list[dict]:
    """
    Obtiene las playlists públicas del canal.
    """
    url = (
        f"{YOUTUBE_API_BASE}/playlists"
        f"?key={api_key}"
        f"&channelId={channel_id}"
        f"&part=snippet,contentDetails"
        f"&maxResults=50"
    )
    response = safe_get(url)
    if not response:
        return []

    data = response.json()
    playlists = []
    for item in data.get("items", []):
        snippet = item.get("snippet", {})
        playlists.append({
            "playlist_id": item.get("id", ""),
            "title": snippet.get("title", ""),
            "description": clean_text(snippet.get("description", "")),
            "published_at": snippet.get("publishedAt", ""),
            "item_count": item.get("contentDetails", {}).get("itemCount", 0),
            "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url", ""),
        })

    logger.info(f"Playlists encontradas: {len(playlists)}")
    return playlists


# ============================================================
# FALLBACK SIN API KEY (scraping básico)
# ============================================================

def scrape_youtube_without_api() -> dict:
    """
    Extracción básica de metadatos del canal SIN API key.
    Solo disponible en modo degradado — extrae información muy limitada
    desde la página pública del canal.
    """
    logger.warning("Usando modo sin API key — datos muy limitados")

    response = safe_get(CHANNEL_URL)
    if not response:
        return {"status": "error", "message": "No se pudo acceder al canal de YouTube"}

    # YouTube es una SPA — BeautifulSoup tiene muy poco alcance aquí.
    # Solo podemos capturar metadatos OG básicos.
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, "lxml")

    result = {
        "channel_url": CHANNEL_URL,
        "channel_id": CHANNEL_ID,
        "captured_at": now_iso(),
        "extraction_method": "html_fallback_sin_api",
        "status": "degraded",
        "note": (
            "Sin API key de YouTube, los datos disponibles son muy limitados. "
            "Configura YOUTUBE_API_KEY en .env para extracción completa."
        ),
    }

    # Intentar metadatos OG
    for prop in ["og:title", "og:description"]:
        tag = soup.find("meta", property=prop)
        if tag:
            key = prop.replace("og:", "")
            result[key] = tag.get("content", "")

    return result


# ============================================================
# FUNCIÓN PRINCIPAL
# ============================================================

def run_youtube_scraper(max_videos: int = None, no_api: bool = False) -> dict:
    """
    Ejecuta el scraper completo de metadatos de YouTube para Manuelita.

    Args:
        max_videos: Límite de videos a extraer
        no_api: Si True, usa fallback sin API key

    Returns:
        Diccionario con datos del canal y videos
    """
    setup_logging("scrape_youtube")
    paths_cfg.ensure_all()

    logger.info("=" * 60)
    logger.info("INICIO: Scraper YouTube — Canal Manuelita Agroindustrial")
    logger.info("=" * 60)

    max_v = max_videos or scraping_cfg.max_videos_youtube
    api_key = api_cfg.youtube_api_key

    if no_api or not api_key or api_key == "TU_YOUTUBE_API_KEY_AQUI":
        logger.warning("No se encontró YOUTUBE_API_KEY válida. Usando modo degradado.")
        result = scrape_youtube_without_api()
        save_json(result, paths_cfg.youtube() / "canal_manuelita_fallback.json")
        return result

    # Con API Key
    logger.info("Usando YouTube Data API v3...")

    # 1. Info del canal
    channel_info = get_channel_info(api_key, CHANNEL_ID)
    if not channel_info:
        logger.error("No se pudo obtener información del canal")
        return {"status": "error", "channel_id": CHANNEL_ID}

    # 2. Lista de videos
    videos = get_channel_videos(api_key, CHANNEL_ID, max_videos=max_v)

    # 3. Detalles de videos (estadísticas)
    video_ids = [v["video_id"] for v in videos if v.get("video_id")]
    details = get_video_details(api_key, video_ids)

    # Combinar videos con detalles
    details_map = {d["video_id"]: d for d in details}
    for video in videos:
        vid_id = video.get("video_id", "")
        if vid_id in details_map:
            video.update(details_map[vid_id])

    # 4. Playlists
    playlists = get_playlists(api_key, CHANNEL_ID)

    # Resultado final
    result = {
        "id": generate_doc_id("youtube", CHANNEL_URL, now_iso()),
        "company": "Manuelita",
        "source_type": "red_social",
        "platform": "youtube",
        "channel_info": channel_info,
        "videos": videos,
        "playlists": playlists,
        "summary": {
            "total_videos": len(videos),
            "total_playlists": len(playlists),
            "subscriber_count": channel_info.get("statistics", {}).get("subscriber_count", "N/A"),
            "total_channel_views": channel_info.get("statistics", {}).get("view_count", "N/A"),
        },
    }

    # Guardar resultados
    save_json(result, paths_cfg.youtube() / "canal_manuelita.json")

    # Guardar videos en JSON separados para facilitar consulta
    save_json(videos, paths_cfg.youtube() / "videos_lista.json")
    save_json(playlists, paths_cfg.youtube() / "playlists.json")

    logger.success(
        f"YouTube scraping completado: {len(videos)} videos, "
        f"{len(playlists)} playlists, "
        f"suscriptores: {channel_info.get('statistics', {}).get('subscriber_count', 'N/A')}"
    )

    return result


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scraper YouTube — Manuelita")
    parser.add_argument("--max-videos", type=int, default=200,
                        help="Máximo de videos a extraer (default: 200)")
    parser.add_argument("--no-api", action="store_true",
                        help="Usar fallback sin YouTube API key")
    args = parser.parse_args()
    run_youtube_scraper(max_videos=args.max_videos, no_api=args.no_api)
