"""
test_modulo2_completo.py
------------------------
Suite de tests integrada del Módulo 2 — Agente Conversacional con Memoria.

Ejecuta los cuatro bloques en secuencia y genera un informe de resultados:

  Bloque 1 — RAG con ChromaDB
  Bloque 2 — Herramienta de Datos Estructurados
  Bloque 3 — Agente Router HybridRouter
  Bloque 4 — Memoria Conversacional (ContextualAgent)

Genera un resumen final con métricas comparativas entre modos.

Uso:
    uv run python scripts/test_modulo2_completo.py

    # Con Gemini (recomendado para mejor score en preguntas RAG):
    $env:LLM_PROVIDER="gemini"; uv run python scripts/test_modulo2_completo.py

    # Con modo local (sin API):
    $env:LLM_PROVIDER="local"; uv run python scripts/test_modulo2_completo.py
"""

import os
import sys
import time
import json
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

SEP  = "=" * 65
SEP2 = "-" * 65


# ─────────────────────────────────────────────────────────────
# Bloque 2 — Datos Estructurados
# ─────────────────────────────────────────────────────────────

PRUEBAS_ESTRUCTURADO = [
    {"id": 1,  "pregunta": "¿Cuál es el NIT de Manuelita?",             "palabras_clave": ["891.300.241"]},
    {"id": 2,  "pregunta": "¿Quién es el presidente de Manuelita?",     "palabras_clave": ["Harold", "Eder"]},
    {"id": 3,  "pregunta": "¿En qué año fue fundada Manuelita?",        "palabras_clave": ["1864"]},
    {"id": 4,  "pregunta": "¿En qué países opera Manuelita?",           "palabras_clave": ["Colombia", "Perú", "Chile"]},
    {"id": 5,  "pregunta": "¿Cuántos empleados tiene Manuelita?",       "palabras_clave": ["7.971", "colaboradores"]},
    {"id": 6,  "pregunta": "¿Cuáles fueron los ingresos en 2023?",      "palabras_clave": ["1.043.562", "2023"]},
    {"id": 7,  "pregunta": "¿Cuál es el EBITDA de Manuelita?",          "palabras_clave": ["369.380", "2023"]},
    {"id": 8,  "pregunta": "¿Cuáles son las unidades de negocio?",      "palabras_clave": ["Laredo", "palma"]},
    {"id": 9,  "pregunta": "¿Cuál es la meta de carbono para 2030?",    "palabras_clave": ["70%", "2030"]},
    {"id": 10, "pregunta": "Cuéntame sobre Manuelita S.A.",             "palabras_clave": ["1864", "Colombia"]},
]


def test_bloque2() -> dict:
    print(f"\n{SEP2}")
    print("  BLOQUE 2 — Datos Estructurados")
    print(SEP2)

    from src.langchain_app.tools.structured_tool import ManuelitaStructuredTool
    tool = ManuelitaStructuredTool()
    hits_total = 0
    keywords_total = 0
    categoria_ok = 0
    t_total = 0.0

    for p in PRUEBAS_ESTRUCTURADO:
        t0 = time.time()
        resp = tool.query(p["pregunta"])
        elapsed = round(time.time() - t0, 4)
        t_total += elapsed

        resp_lower = resp.lower()
        hits = sum(1 for kw in p["palabras_clave"] if kw.lower() in resp_lower)
        hits_total += hits
        keywords_total += len(p["palabras_clave"])
        if hits == len(p["palabras_clave"]):
            categoria_ok += 1
        icono = "✓" if hits == len(p["palabras_clave"]) else "✗"
        print(f"  [{p['id']:02d}] {icono} {p['pregunta'][:55]}")
        print(f"       → {resp[:100]}...")

    score = round(hits_total / keywords_total * 100)
    avg_t = round(t_total / len(PRUEBAS_ESTRUCTURADO) * 1000, 2)

    print(f"\n  Score     : {hits_total}/{keywords_total} keywords ({score}%)")
    print(f"  Tiempo    : {avg_t}ms promedio")
    print(f"  Exactitud : {categoria_ok}/{len(PRUEBAS_ESTRUCTURADO)} preguntas al 100%")

    return {"bloque": 2, "score_pct": score, "exactitud_pct": round(categoria_ok/len(PRUEBAS_ESTRUCTURADO)*100), "tiempo_ms": avg_t}


# ─────────────────────────────────────────────────────────────
# Bloque 3 — Agente Router
# ─────────────────────────────────────────────────────────────

PRUEBAS_ROUTER = [
    {"id": 1, "pregunta": "¿Cuál es el NIT de Manuelita?",                    "herramienta": "estructurado", "palabras_clave": ["891.300.241"]},
    {"id": 2, "pregunta": "¿Quién es el presidente de Manuelita?",            "herramienta": "estructurado", "palabras_clave": ["Harold", "Eder"]},
    {"id": 3, "pregunta": "¿En qué año fue fundada Manuelita?",               "herramienta": "estructurado", "palabras_clave": ["1864"]},
    {"id": 4, "pregunta": "¿Cuántos empleados tiene Manuelita?",              "herramienta": "estructurado", "palabras_clave": ["7.971"]},
    {"id": 5, "pregunta": "¿Cuáles fueron los ingresos en 2023?",             "herramienta": "estructurado", "palabras_clave": ["1.043.562"]},
    {"id": 6, "pregunta": "¿Cuál es la meta de carbono para 2030?",           "herramienta": "estructurado", "palabras_clave": ["70%", "2030"]},
    {"id": 7, "pregunta": "¿Cuáles son los valores corporativos de Manuelita?","herramienta": "rag",          "palabras_clave": ["valores"]},
    {"id": 8, "pregunta": "¿Cómo gestiona Manuelita la sostenibilidad ambiental?","herramienta": "rag",       "palabras_clave": ["sostenibilidad"]},
    {"id": 9, "pregunta": "¿Qué premios o reconocimientos ha recibido Manuelita?","herramienta": "rag",       "palabras_clave": ["MERCO", "reputación"]},
    {"id": 10,"pregunta": "¿Cómo impacta Manuelita a las comunidades vecinas?",   "herramienta": "rag",       "palabras_clave": ["comunidades", "social"]},
]


def test_bloque3(provider: str) -> dict:
    print(f"\n{SEP2}")
    print(f"  BLOQUE 3 — Agente Router ({provider.upper()})")
    print(SEP2)

    from src.langchain_app.agent import ManuelitaAgent
    t_init = time.time()
    agent = ManuelitaAgent(provider=provider, verbose=False)
    print(f"  Inicializado en {round(time.time()-t_init, 1)}s\n")

    routing_ok = 0
    kw_hits = 0
    kw_total = 0
    t_total = 0.0

    for p in PRUEBAS_ROUTER:
        t0 = time.time()
        res = agent.ask(p["pregunta"])
        elapsed = round(time.time() - t0, 2)
        t_total += elapsed

        tool_ok = res["tool"] == p["herramienta"]
        if tool_ok:
            routing_ok += 1

        resp_lower = res["answer"].lower()
        hits = sum(1 for kw in p["palabras_clave"] if kw.lower() in resp_lower)
        kw_hits += hits
        kw_total += len(p["palabras_clave"])

        icono_t = "✓" if tool_ok else "✗"
        icono_k = "✓" if hits == len(p["palabras_clave"]) else ("~" if hits > 0 else "✗")
        print(f"  [{p['id']:02d}] {icono_t}{icono_k} [{res['tool'].upper():12s}] {p['pregunta'][:50]}")

    routing_pct = round(routing_ok / len(PRUEBAS_ROUTER) * 100)
    kw_pct = round(kw_hits / kw_total * 100)
    avg_t = round(t_total / len(PRUEBAS_ROUTER), 2)

    print(f"\n  Routing   : {routing_ok}/{len(PRUEBAS_ROUTER)} ({routing_pct}%)")
    print(f"  Keywords  : {kw_hits}/{kw_total} ({kw_pct}%)")
    print(f"  Tiempo    : {avg_t}s promedio")

    return {"bloque": 3, "routing_pct": routing_pct, "kw_pct": kw_pct, "tiempo_s": avg_t}


# ─────────────────────────────────────────────────────────────
# Bloque 4 — Memoria Conversacional
# ─────────────────────────────────────────────────────────────

DIALOGO_MEMORIA = [
    {"id": 1, "pregunta": "¿Cuál es el NIT de Manuelita?",             "herramienta": "estructurado", "palabras_clave": ["891.300.241"]},
    {"id": 2, "pregunta": "¿Quién es el presidente?",                  "herramienta": "estructurado", "palabras_clave": ["Harold", "Eder"]},
    {"id": 3, "pregunta": "¿En qué países opera Manuelita?",           "herramienta": "estructurado", "palabras_clave": ["Colombia", "Perú", "Chile"]},
    {"id": 4, "pregunta": "¿Y cuántos empleados tiene?",               "herramienta": "estructurado", "palabras_clave": ["7.971"],          "es_follow_up": True},
    {"id": 5, "pregunta": "¿Cuáles son los valores corporativos de Manuelita?", "herramienta": "rag", "palabras_clave": ["valores"]},
    {"id": 6, "pregunta": "¿Y cómo se relacionan con su estrategia de sostenibilidad?","herramienta": "rag","palabras_clave": ["sostenibilidad"], "es_follow_up": True},
]


def test_bloque4(provider: str) -> dict:
    print(f"\n{SEP2}")
    print(f"  BLOQUE 4 — Memoria Conversacional ({provider.upper()})")
    print(SEP2)

    from src.langchain_app.memory import ContextualAgent, build_memory

    # Sub-test 1: memoria básica
    mem = build_memory(window_size=3)
    mem.save_turn("¿Cuál es el NIT?", "El NIT es 891.300.241")
    mem.save_turn("¿Quién es el presidente?", "Harold Eder")
    assert not mem.is_empty() and mem.turn_count() == 2
    mem2 = build_memory(window_size=2)
    for i in range(4):
        mem2.save_turn(f"Pregunta {i}", f"Respuesta {i}")
    hist = mem2.get_history_text()
    ventana_ok = "Pregunta 0" not in hist and "Pregunta 3" in hist
    mem.reset()
    assert mem.is_empty()
    print(f"  ✓ Memoria básica OK")
    print(f"  {'✓' if ventana_ok else '✗'} Ventana deslizante {'OK' if ventana_ok else 'FAIL'}")

    # Sub-test 2: diálogo con follow-up
    t_init = time.time()
    agent = ContextualAgent(provider=provider, window_size=5, verbose=False)
    print(f"  Agente inicializado en {round(time.time()-t_init, 1)}s\n")

    routing_ok = 0
    kw_hits = 0
    kw_total = 0
    follow_up_enrich = 0
    follow_up_total = sum(1 for d in DIALOGO_MEMORIA if d.get("es_follow_up"))
    t_total = 0.0

    for d in DIALOGO_MEMORIA:
        t0 = time.time()
        res = agent.chat(d["pregunta"])
        elapsed = round(time.time() - t0, 2)
        t_total += elapsed

        tool_ok = res["tool"] == d["herramienta"]
        if tool_ok:
            routing_ok += 1

        resp_lower = res["answer"].lower()
        hits = sum(1 for kw in d["palabras_clave"] if kw.lower() in resp_lower)
        kw_hits += hits
        kw_total += len(d["palabras_clave"])

        if d.get("es_follow_up") and res.get("enriched"):
            follow_up_enrich += 1

        icono_t = "✓" if tool_ok else "✗"
        icono_e = "🔗" if res.get("enriched") else "  "
        print(f"  [{d['id']:02d}] {icono_t} {icono_e} [{res['tool'].upper():12s}] {d['pregunta'][:50]}")
        print(f"        → {res['answer'][:100]}...")

    routing_pct = round(routing_ok / len(DIALOGO_MEMORIA) * 100)
    kw_pct = round(kw_hits / kw_total * 100) if kw_total else 0
    avg_t = round(t_total / len(DIALOGO_MEMORIA), 2)

    print(f"\n  Routing    : {routing_ok}/{len(DIALOGO_MEMORIA)} ({routing_pct}%)")
    print(f"  Keywords   : {kw_hits}/{kw_total} ({kw_pct}%)")
    print(f"  Follow-ups : {follow_up_enrich}/{follow_up_total} enriquecidos")
    print(f"  Tiempo     : {avg_t}s promedio")
    print(f"  Historial  : {agent.memory.turn_count()} turnos guardados")

    return {
        "bloque": 4,
        "routing_pct": routing_pct,
        "kw_pct": kw_pct,
        "follow_up_enrich": follow_up_enrich,
        "follow_up_total": follow_up_total,
        "ventana_ok": ventana_ok,
        "tiempo_s": avg_t,
    }


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    provider = os.getenv("LLM_PROVIDER", "local")
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    print(f"\n{SEP}")
    print("  SUITE COMPLETA — MÓDULO 2 — MANUELITA S.A.")
    print(f"  Proveedor: {provider.upper()}  |  {fecha}")
    print(SEP)

    t_suite = time.time()
    resultados = []

    # Bloque 2 (sin LLM)
    r2 = test_bloque2()
    resultados.append(r2)

    # Bloque 3 (con LLM para RAG)
    r3 = test_bloque3(provider)
    resultados.append(r3)

    # Bloque 4 (con LLM para RAG + follow-up)
    r4 = test_bloque4(provider)
    resultados.append(r4)

    t_suite_total = round(time.time() - t_suite, 1)

    # ── Informe final ─────────────────────────────────────────
    print(f"\n{SEP}")
    print("  INFORME FINAL — MÓDULO 2")
    print(SEP)
    print(f"  Proveedor        : {provider.upper()}")
    print(f"  Fecha            : {fecha}")
    print(f"  Tiempo total     : {t_suite_total}s")
    print(SEP2)
    print("  BLOQUE 2 — Datos Estructurados")
    print(f"    Score keywords : {r2['score_pct']}%")
    print(f"    Exactitud      : {r2['exactitud_pct']}%")
    print(f"    Tiempo prom.   : {r2['tiempo_ms']}ms  (sin LLM, 0-latency)")
    print(SEP2)
    print("  BLOQUE 3 — Agente Router")
    print(f"    Routing        : {r3['routing_pct']}%  (objetivo: 100%)")
    print(f"    Score keywords : {r3['kw_pct']}%")
    print(f"    Tiempo prom.   : {r3['tiempo_s']}s/pregunta")
    print(SEP2)
    print("  BLOQUE 4 — Memoria Conversacional")
    print(f"    Routing        : {r4['routing_pct']}%")
    print(f"    Score keywords : {r4['kw_pct']}%")
    print(f"    Follow-ups     : {r4['follow_up_enrich']}/{r4['follow_up_total']} enriquecidos")
    print(f"    Ventana        : {'OK' if r4['ventana_ok'] else 'FAIL'}")
    print(f"    Tiempo prom.   : {r4['tiempo_s']}s/pregunta")
    print(SEP)

    # Evaluación global
    todos_ok = (
        r2["score_pct"] == 100
        and r3["routing_pct"] == 100
        and r4["routing_pct"] >= 80
        and r4["ventana_ok"]
    )

    if todos_ok:
        print("\n  ✓ MÓDULO 2 COMPLETADO — Todos los bloques funcionan correctamente.")
    else:
        print("\n  ~ MÓDULO 2 PARCIAL — Revisar los bloques marcados.")
        if r2["score_pct"] < 100:
            print("    ✗ Bloque 2: revisar structured_tool.py o manuelita_datos.json")
        if r3["routing_pct"] < 100:
            print("    ✗ Bloque 3: revisar _RAG_SIGNALS o keywords en agent.py")
        if r4["routing_pct"] < 80:
            print("    ✗ Bloque 4: revisar ContextualAgent.chat() en memory.py")
        if not r4["ventana_ok"]:
            print("    ✗ Bloque 4: revisar ConversationBufferWindowMemory window_size")

    # Guardar reporte JSON
    reporte = {
        "fecha": fecha,
        "proveedor": provider,
        "tiempo_total_s": t_suite_total,
        "bloques": resultados,
    }
    reports_dir = ROOT / "reports"
    reports_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    ruta = reports_dir / f"modulo2_test_{provider}_{ts}.json"
    ruta.write_text(json.dumps(reporte, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\n  Reporte guardado: {ruta.relative_to(ROOT)}")
    print()


if __name__ == "__main__":
    main()
