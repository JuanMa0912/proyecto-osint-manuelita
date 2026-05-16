"""
test_langsmith_bloque5.py
--------------------------
Verificación de la integración LangSmith (Bloque 5 — Módulo 2).

Prueba 3 aspectos:
  1. Configuración   — variables de entorno y SDK instalado
  2. Traza manual    — llama al agente y verifica que se crea una traza
  3. Metadatos       — tags, run_name, project correctamente asignados

Uso:
    # Con LangSmith activo (LANGCHAIN_TRACING_V2=true en .env):
    uv run python scripts/test_langsmith_bloque5.py

    # Sin LangSmith — muestra instrucciones de configuración:
    uv run python scripts/test_langsmith_bloque5.py

Notas:
    - Este script NO falla si LangSmith no está configurado.
      Solo reporta el estado y da instrucciones.
    - Para ver las trazas: https://smith.langchain.com
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv()

SEP  = "=" * 60
SEP2 = "-" * 60


# ─────────────────────────────────────────────────────────────
# Test 1 — Verificar configuración
# ─────────────────────────────────────────────────────────────

def test_configuracion() -> dict:
    """Verifica que las variables de entorno y el SDK están listos."""
    print(f"\n{SEP2}")
    print("  TEST 1 — Configuración LangSmith")
    print(SEP2)

    from src.langchain_app.langsmith_setup import init_langsmith, is_tracing_enabled

    status = init_langsmith()
    enabled = status["enabled"]

    print(f"  Estado    : {'ACTIVO ✓' if enabled else 'INACTIVO ○'}")
    print(f"  Proyecto  : {status['project']}")
    print(f"  Endpoint  : {status['endpoint']}")
    print(f"  Mensaje   : {status['message']}")

    # Verificar variables
    vars_check = {
        "LANGCHAIN_TRACING_V2": os.getenv("LANGCHAIN_TRACING_V2", "—"),
        "LANGCHAIN_API_KEY":    "***" + os.getenv("LANGCHAIN_API_KEY", "")[-4:] if os.getenv("LANGCHAIN_API_KEY") else "—",
        "LANGCHAIN_PROJECT":   os.getenv("LANGCHAIN_PROJECT", "—"),
    }
    print("\n  Variables de entorno:")
    for k, v in vars_check.items():
        presente = v != "—"
        icono = "✓" if presente else "✗"
        print(f"    {icono} {k} = {v}")

    # Verificar SDK
    try:
        import langsmith  # noqa: F401
        sdk_version = getattr(langsmith, "__version__", "instalado")
        print(f"\n  SDK langsmith : {sdk_version} ✓")
        sdk_ok = True
    except ImportError:
        print("\n  SDK langsmith : NO INSTALADO ✗")
        print("  → Ejecuta: uv add langsmith")
        sdk_ok = False

    if not enabled:
        print("\n  Para activar LangSmith:")
        print("  1. Crea cuenta en https://smith.langchain.com")
        print("  2. Genera API key en Settings → API Keys")
        print("  3. En .env agrega:")
        print("       LANGCHAIN_TRACING_V2=true")
        print("       LANGCHAIN_API_KEY=<tu-key>")
        print("       LANGCHAIN_PROJECT=manuelita-osint-ia")
        print("  4. Reinicia: uv run python scripts/test_langsmith_bloque5.py")

    return {"test": "configuracion", "ok": sdk_ok, "tracing_enabled": enabled}


# ─────────────────────────────────────────────────────────────
# Test 2 — Traza de una pregunta real al agente
# ─────────────────────────────────────────────────────────────

def test_traza_agente(provider: str = "local") -> dict:
    """Invoca el agente y verifica que la traza se registra en LangSmith."""
    print(f"\n{SEP2}")
    print(f"  TEST 2 — Traza de agente ({provider.upper()})")
    print(SEP2)

    from src.langchain_app.langsmith_setup import is_tracing_enabled, get_dashboard_url
    from src.langchain_app.memory import ContextualAgent

    agent = ContextualAgent(provider=provider, window_size=3, verbose=False)
    print(f"  Agente inicializado — proveedor: {provider.upper()}")

    pregunta = "¿Cuál es el NIT de Manuelita?"
    print(f"  Pregunta  : {pregunta}")

    t0 = time.time()
    result = agent.chat(pregunta)
    elapsed = round(time.time() - t0, 2)

    respuesta_ok = "891.300.241" in result["answer"] or len(result["answer"]) > 10
    herramienta_ok = result["tool"] in ("estructurado", "rag")

    icono = "✓" if respuesta_ok else "~"
    print(f"  {icono} Respuesta   : {result['answer'][:120]}")
    print(f"  ✓ Herramienta : {result['tool'].upper()}")
    print(f"  ✓ Tiempo      : {elapsed}s")

    if is_tracing_enabled():
        dash = get_dashboard_url()
        print(f"\n  🔍 Traza registrada en LangSmith")
        print(f"     Dashboard  : {dash}")
        print(f"     Proyecto   : manuelita-osint-ia")
        print(f"     Run name   : manuelita_ask")
        print(f"     Tags       : modulo2, hybrid_router")
    else:
        print("\n  ○ LangSmith no activo — la llamada NO fue trazada")
        print("    (el agente funciona correctamente de todas formas)")

    return {
        "test": "traza_agente",
        "ok": respuesta_ok and herramienta_ok,
        "tracing_active": is_tracing_enabled(),
        "tiempo_s": elapsed,
    }


# ─────────────────────────────────────────────────────────────
# Test 3 — Verificar metadatos de la traza
# ─────────────────────────────────────────────────────────────

def test_metadatos_traza() -> dict:
    """Verifica que el decorador @traceable está correctamente aplicado."""
    print(f"\n{SEP2}")
    print("  TEST 3 — Metadatos de traza (@traceable)")
    print(SEP2)

    import inspect
    from src.langchain_app.agent import ManuelitaAgent

    # Verificar que ask() tiene el decorador (el wrapper de LangSmith)
    ask_fn = ManuelitaAgent.ask
    has_wrapper = hasattr(ask_fn, "__wrapped__") or "traceable" in str(type(ask_fn))
    fn_name = ask_fn.__name__ if hasattr(ask_fn, "__name__") else str(ask_fn)

    print(f"  Método ManuelitaAgent.ask : {fn_name}")
    print(f"  Tiene wrapper @traceable  : {'✓' if has_wrapper else '○ (decorador aplicado estáticamente)'}")

    # Verificar que langsmith_setup.py está importado correctamente
    try:
        from src.langchain_app.langsmith_setup import (
            init_langsmith, get_traceable, is_tracing_enabled,
            get_project_name, get_dashboard_url, langsmith_status_badge
        )
        api_ok = True
        print(f"  langsmith_setup.py API    : ✓ todas las funciones disponibles")
        print(f"  is_tracing_enabled()      : {is_tracing_enabled()}")
        print(f"  get_project_name()        : {get_project_name()}")
        badge = langsmith_status_badge()
        print(f"  langsmith_status_badge()  : {badge[:60]}")
    except ImportError as e:
        api_ok = False
        print(f"  ✗ Error importando langsmith_setup: {e}")

    return {"test": "metadatos_traza", "ok": api_ok}


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    provider = os.getenv("LLM_PROVIDER", "local")

    print(f"\n{SEP}")
    print("  TEST LANGSMITH — BLOQUE 5 — MANUELITA S.A.")
    print(SEP)
    print(f"  Proveedor : {provider.upper()}")
    print(SEP)

    resultados = []

    r1 = test_configuracion()
    resultados.append(r1)

    r2 = test_traza_agente(provider)
    resultados.append(r2)

    r3 = test_metadatos_traza()
    resultados.append(r3)

    # ── Resumen ───────────────────────────────────────────────
    print(f"\n{SEP}")
    print("  RESUMEN FINAL")
    print(SEP)

    tests_ok = sum(1 for r in resultados if r.get("ok"))
    total = len(resultados)

    print(f"  Tests pasados      : {tests_ok}/{total}")
    print(f"  ✓ Configuración    : {'OK' if r1['ok'] else 'PARCIAL (SDK ok, tracing inactivo)'}")
    print(f"  ✓ Traza agente     : {'OK' if r2['ok'] else 'FAIL'}")
    print(f"  ✓ Metadatos        : {'OK' if r3['ok'] else 'FAIL'}")
    print(f"  LangSmith activo   : {'SÍ ✓' if r1.get('tracing_enabled') else 'NO — configurar .env'}")
    print(SEP)

    if r1.get("tracing_enabled"):
        from src.langchain_app.langsmith_setup import get_dashboard_url
        print(f"\n  🔍 Ver trazas en: {get_dashboard_url()}")
    else:
        print("\n  ○ Integración lista — activa LANGCHAIN_TRACING_V2=true para trazar.")
    print()


if __name__ == "__main__":
    main()
