"""
main.py — Orquestador principal del pipeline OSINT Manuelita.

Pipeline ETL completo:
  1. DISCOVER    → Descubrimiento y mapeo de fuentes
  2. SCRAPE      → Extracción de contenido por fuente
  3. PARSE       → Procesamiento de PDFs
  4. NORMALIZE   → NLP: entidades, temas, cifras
  5. BUILD       → Generación de SMART MARKDOWN
  6. REPORT      → Índice maestro y resumen de sesión

Modos de ejecución:
  python src/main.py --full              # Pipeline completo
  python src/main.py --phase discover   # Solo descubrimiento
  python src/main.py --phase scrape     # Solo scraping web
  python src/main.py --phase news       # Solo noticias
  python src/main.py --phase youtube    # Solo YouTube
  python src/main.py --phase social     # Solo redes sociales
  python src/main.py --phase pdfs       # Solo PDFs
  python src/main.py --phase normalize  # Solo normalización
  python src/main.py --phase markdown   # Solo generación Markdown
  python src/main.py --quick            # Solo páginas prioritarias (rápido)
"""

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.utils.config import paths_cfg
from src.utils.utils import setup_logging, save_json, now_iso


def run_full_pipeline(quick: bool = False) -> dict:
    """
    Ejecuta el pipeline ETL completo para Manuelita.

    Args:
        quick: Si True, solo extrae fuentes de alta prioridad

    Returns:
        Resumen de la sesión
    """
    setup_logging("pipeline_manuelita")
    paths_cfg.ensure_all()

    session_start = time.time()
    session_summary = {
        "session_id": f"manuelita_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "started_at": now_iso(),
        "mode": "quick" if quick else "full",
        "phases": {},
        "status": "running",
    }

    logger.info("=" * 70)
    logger.info("  PIPELINE OSINT — MANUELITA AGROINDUSTRIAL")
    logger.info(f"  Modo: {'RÁPIDO (alta prioridad)' if quick else 'COMPLETO'}")
    logger.info("=" * 70)

    # ==========================================
    # FASE 1: DESCUBRIMIENTO
    # ==========================================
    logger.info("\n📡 FASE 1/6: DESCUBRIMIENTO DE FUENTES")
    try:
        from src.discover.discover_sources import run_discovery

        sources = run_discovery()
        session_summary["phases"]["discover"] = {
            "status": "ok",
            "total_urls": sources.get("summary", {}).get("total_sitemap_urls", 0),
        }
        logger.success("✅ Fase 1 completada")
    except Exception as e:
        logger.error(f"❌ Fase 1 falló: {e}")
        session_summary["phases"]["discover"] = {"status": "error", "error": str(e)}

    # ==========================================
    # FASE 2: SCRAPING WEB
    # ==========================================
    logger.info("\n🌐 FASE 2/6: SCRAPING SITIO WEB OFICIAL")
    try:
        from src.scrapers.scrape_website import run_website_scraper

        priority_pages = [
            "home",
            "perfil",
            "historia",
            "presencia",
            "plataformas",
            "sostenibilidad",
        ]
        pages = priority_pages if quick else None
        results = run_website_scraper(pages=pages, scrape_all=not quick)

        successful = [r for r in results if r.get("status") != "error"]
        session_summary["phases"]["scrape_web"] = {
            "status": "ok",
            "pages_total": len(results),
            "pages_ok": len(successful),
        }
        logger.success(
            f"✅ Fase 2 completada: {len(successful)}/{len(results)} páginas"
        )
    except Exception as e:
        logger.error(f"❌ Fase 2 falló: {e}")
        session_summary["phases"]["scrape_web"] = {"status": "error", "error": str(e)}

    # ==========================================
    # FASE 3A: SCRAPING DE NOTICIAS
    # ==========================================
    if not quick:
        logger.info("\n📰 FASE 3A/6: SCRAPING DE NOTICIAS Y PRENSA")
        try:
            from src.scrapers.scrape_news import run_news_scraper

            news = run_news_scraper(max_full_articles=30)
            session_summary["phases"]["scrape_news"] = {
                "status": "ok",
                "total_items": news.get("total_news_items", 0),
                "full_articles": news.get("total_full_articles", 0),
            }
            logger.success("✅ Fase 3A completada")
        except Exception as e:
            logger.error(f"❌ Fase 3A falló: {e}")
            session_summary["phases"]["scrape_news"] = {
                "status": "error",
                "error": str(e),
            }

    # ==========================================
    # FASE 3B: REDES SOCIALES
    # ==========================================
    logger.info("\n📱 FASE 3B/6: EXTRACCIÓN REDES SOCIALES")
    try:
        from src.scrapers.scrape_social_links import run_social_scraper

        social = run_social_scraper()
        session_summary["phases"]["scrape_social"] = {
            "status": "ok",
            "platforms": social.get("platforms_ok", []),
        }
        logger.success("✅ Fase 3B completada")
    except Exception as e:
        logger.error(f"❌ Fase 3B falló: {e}")
        session_summary["phases"]["scrape_social"] = {
            "status": "error",
            "error": str(e),
        }

    # ==========================================
    # FASE 3C: YOUTUBE
    # ==========================================
    logger.info("\n🎬 FASE 3C/6: METADATOS YOUTUBE")
    try:
        from src.scrapers.scrape_youtube_metadata import run_youtube_scraper

        yt = run_youtube_scraper(max_videos=50 if quick else 200)
        session_summary["phases"]["scrape_youtube"] = {
            "status": "ok",
            "videos": yt.get("summary", {}).get("total_videos", 0),
        }
        logger.success("✅ Fase 3C completada")
    except Exception as e:
        logger.error(f"❌ Fase 3C falló: {e}")
        session_summary["phases"]["scrape_youtube"] = {
            "status": "error",
            "error": str(e),
        }

    # ==========================================
    # FASE 3D: PDFs
    # ==========================================
    logger.info("\n📄 FASE 3D/6: EXTRACCIÓN DE PDFs")
    try:
        from src.parsers.parse_pdfs import run_pdf_parser

        pdfs = run_pdf_parser()
        ok_pdfs = [p for p in pdfs if p.get("status") == "ok"]
        session_summary["phases"]["parse_pdfs"] = {
            "status": "ok",
            "pdfs_total": len(pdfs),
            "pdfs_ok": len(ok_pdfs),
        }
        logger.success(f"✅ Fase 3D completada: {len(ok_pdfs)}/{len(pdfs)} PDFs")
    except Exception as e:
        logger.error(f"❌ Fase 3D falló: {e}")
        session_summary["phases"]["parse_pdfs"] = {"status": "error", "error": str(e)}

    # ==========================================
    # FASE 4: NORMALIZACIÓN Y NLP
    # ==========================================
    logger.info("\n🧠 FASE 4/6: NORMALIZACIÓN Y EXTRACCIÓN DE ENTIDADES")
    try:
        from src.cleaners.normalize_entities import run_normalization

        normalized = run_normalization()
        session_summary["phases"]["normalize"] = {
            "status": "ok",
            "documents_normalized": len(normalized),
        }
        logger.success(
            f"✅ Fase 4 completada: {len(normalized)} documentos normalizados"
        )
    except Exception as e:
        logger.error(f"❌ Fase 4 falló: {e}")
        session_summary["phases"]["normalize"] = {"status": "error", "error": str(e)}

    # ==========================================
    # FASE 5: GENERACIÓN SMART MARKDOWN
    # ==========================================
    logger.info("\n✍️  FASE 5/6: GENERACIÓN DE SMART MARKDOWN")
    try:
        from src.markdown_builders.build_smart_markdown import run_markdown_builder

        md_files = run_markdown_builder()
        session_summary["phases"]["build_markdown"] = {
            "status": "ok",
            "files_generated": len(md_files),
        }
        logger.success(f"✅ Fase 5 completada: {len(md_files)} archivos Markdown")
    except Exception as e:
        logger.error(f"❌ Fase 5 falló: {e}")
        session_summary["phases"]["build_markdown"] = {
            "status": "error",
            "error": str(e),
        }

    # ==========================================
    # FASE 6: REPORTE FINAL
    # ==========================================
    session_duration = round(time.time() - session_start, 1)
    session_summary.update(
        {
            "finished_at": now_iso(),
            "duration_seconds": session_duration,
            "status": "completed",
        }
    )

    # Guardar resumen de sesión
    session_path = paths_cfg.reports / f"session_{session_summary['session_id']}.json"
    save_json(session_summary, session_path)

    # Log resumen final
    logger.info("\n" + "=" * 70)
    logger.info("  📊 RESUMEN FINAL DEL PIPELINE")
    logger.info("=" * 70)
    logger.info(f"  Duración total: {session_duration}s")
    logger.info(
        f"  Fases completadas: "
        f"{sum(1 for p in session_summary['phases'].values() if p.get('status') == 'ok')}"
        f"/{len(session_summary['phases'])}"
    )
    logger.info(f"  Reporte guardado: {session_path}")
    logger.info("=" * 70)

    return session_summary


# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Pipeline OSINT Manuelita Agroindustrial",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Ejemplos de uso:
            python src/main.py --full              # Pipeline completo
            python src/main.py --quick             # Solo fuentes prioritarias
            python src/main.py --phase discover    # Solo descubrimiento
            python src/main.py --phase scrape      # Solo scraping web
            python src/main.py --phase pdfs        # Solo PDFs
            python src/main.py --phase normalize   # Solo normalización
            python src/main.py --phase markdown    # Solo generación Markdown
        """,
    )

    parser.add_argument(
        "--full", action="store_true", help="Ejecutar pipeline completo"
    )
    parser.add_argument(
        "--quick", action="store_true", help="Solo fuentes de alta prioridad"
    )
    parser.add_argument(
        "--phase",
        choices=[
            "discover",
            "scrape",
            "news",
            "youtube",
            "social",
            "pdfs",
            "normalize",
            "markdown",
        ],
        help="Ejecutar una fase específica",
    )

    args = parser.parse_args()

    if args.full or args.quick:
        run_full_pipeline(quick=args.quick)

    elif args.phase == "discover":
        from src.discover.discover_sources import run_discovery

        run_discovery()

    elif args.phase == "scrape":
        from src.scrapers.scrape_website import run_website_scraper

        run_website_scraper(scrape_all=True)

    elif args.phase == "news":
        from src.scrapers.scrape_news import run_news_scraper

        run_news_scraper()

    elif args.phase == "youtube":
        from src.scrapers.scrape_youtube_metadata import run_youtube_scraper

        run_youtube_scraper()

    elif args.phase == "social":
        from src.scrapers.scrape_social_links import run_social_scraper

        run_social_scraper()

    elif args.phase == "pdfs":
        from src.parsers.parse_pdfs import run_pdf_parser

        run_pdf_parser()

    elif args.phase == "normalize":
        from src.cleaners.normalize_entities import run_normalization

        run_normalization()

    elif args.phase == "markdown":
        from src.markdown_builders.build_smart_markdown import run_markdown_builder

        run_markdown_builder()

    else:
        parser.print_help()
        logger.info("\nEjemplo rápido para empezar: python src/main.py --quick")
        sys.exit(0)
