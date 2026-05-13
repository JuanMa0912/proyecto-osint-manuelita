"""
test_memoria_bloque4.py
-----------------------
Verificación completa del módulo de memoria conversacional (Bloque 4 — Módulo 2).

Prueba 4 aspectos:
  1. Memoria básica      — save/load de historial funciona correctamente
  2. Detección follow-up — preguntas de seguimiento se enriquecen con contexto
  3. Ventana deslizante  — solo se mantienen los últimos N turnos
  4. Diálogo end-to-end  — secuencia real de pregunta → follow-up → respuesta

Uso:
    uv run python scripts/test_memoria_bloque4.py

    # Con Gemini (mejor calidad en follow-ups narrativos):
    $env:LLM_PROVIDER="gemini"; uv run python scripts/test_memoria_bloque4.py

    # Con proveedor local (sin API):
    $env:LLM_PROVIDER="local"; uv run python scripts/test_memoria_bloque4.py
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.langchain_app.memory import ConversationMemory, ContextualAgent, build_memory

SEP  = "=" * 60
SEP2 = "-" * 60

# ─────────────────────────────────────────────────────────────
# Pruebas unitarias de la clase ConversationMemory
# ─────────────────────────────────────────────────────────────

def test_memoria_basica() -> dict:
    """Verifica que save/load del historial funciona correctamente."""
    print(f"\n{SEP2}")
    print("  TEST 1 — Memoria básica (save/load)")
    print(SEP2)

    mem = build_memory(window_size=3)
    errores = []

    # 1. Memoria vacía al inicio
    assert mem.is_empty(), "❌ Debería estar vacía al inicio"
    assert mem.turn_count() == 0, "❌ turn_count debería ser 0"
    print("  ✓ Memoria vacía al inicio")

    # 2. Guardar un turno
    mem.save_turn("¿Cuál es el NIT?", "El NIT es 891.300.241")
    assert not mem.is_empty(), "❌ Debería tener datos"
    assert mem.turn_count() == 1, f"❌ turn_count debería ser 1, es {mem.turn_count()}"
    print("  ✓ Primer turno guardado correctamente")

    # 3. Historial contiene el turno
    history = mem.get_history_text()
    assert "NIT" in history, "❌ Historial no contiene la pregunta"
    assert "891.300.241" in history, "❌ Historial no contiene la respuesta"
    print("  ✓ Historial contiene pregunta y respuesta")

    # 4. Historial como lista
    hist_list = mem.get_history_list()
    assert len(hist_list) == 2, f"❌ Debería haber 2 items (user+assistant), hay {len(hist_list)}"
    assert hist_list[0]["role"] == "user"
    assert hist_list[1]["role"] == "assistant"
    print("  ✓ get_history_list() devuelve formato correcto")

    # 5. Guardar más turnos
    mem.save_turn("¿Quién es el presidente?", "Harold Eder")
    mem.save_turn("¿En qué países opera?", "Colombia, Perú y Chile")
    assert mem.turn_count() == 3, f"❌ Debería haber 3 turnos"
    print("  ✓ Tres turnos guardados")

    # 6. Reset
    mem.reset()
    assert mem.is_empty(), "❌ Después de reset debería estar vacía"
    assert mem.turn_count() == 0, "❌ turn_count debería ser 0 tras reset"
    print("  ✓ reset() limpia el historial correctamente")

    return {"test": "memoria_basica", "ok": True, "errores": errores}


def test_ventana_deslizante() -> dict:
    """Verifica que la ventana deslizante descarta los turnos más antiguos."""
    print(f"\n{SEP2}")
    print("  TEST 2 — Ventana deslizante (window_size)")
    print(SEP2)

    WINDOW = 2
    mem = build_memory(window_size=WINDOW)

    # Guardar 4 turnos (más que la ventana)
    turnos = [
        ("Turno A", "Respuesta A"),
        ("Turno B", "Respuesta B"),
        ("Turno C", "Respuesta C"),
        ("Turno D", "Respuesta D"),
    ]
    for q, a in turnos:
        mem.save_turn(q, a)

    history = mem.get_history_text()

    # Los turnos A y B deben haber salido de la ventana
    turno_a_presente = "Turno A" in history
    turno_b_presente = "Turno B" in history
    turno_c_presente = "Turno C" in history
    turno_d_presente = "Turno D" in history

    print(f"  Turno A (debería salir): {'presente ✗' if turno_a_presente else 'descartado ✓'}")
    print(f"  Turno B (debería salir): {'presente ✗' if turno_b_presente else 'descartado ✓'}")
    print(f"  Turno C (debería estar): {'presente ✓' if turno_c_presente else 'ausente ✗'}")
    print(f"  Turno D (debería estar): {'presente ✓' if turno_d_presente else 'ausente ✗'}")

    ventana_ok = (not turno_a_presente) and (not turno_b_presente) and turno_c_presente and turno_d_presente

    if ventana_ok:
        print(f"  ✓ Ventana deslizante funciona correctamente (window={WINDOW})")
    else:
        print(f"  ✗ Ventana deslizante con problemas — revisar ConversationBufferWindowMemory")

    return {"test": "ventana_deslizante", "ok": ventana_ok}


def test_deteccion_follow_up(provider: str) -> dict:
    """Verifica que el agente detecta preguntas de seguimiento."""
    print(f"\n{SEP2}")
    print("  TEST 3 — Detección de follow-up (sin LLM)")
    print(SEP2)

    agent = ContextualAgent(provider=provider, window_size=3, verbose=False)

    # Simular que hay historial
    agent.memory.save_turn(
        "¿En qué países opera Manuelita?",
        "Manuelita opera en Colombia, Perú y Chile."
    )
    agent.memory.save_turn(
        "¿Cuántos empleados tiene?",
        "Tiene aproximadamente 7.971 colaboradores."
    )

    PRUEBAS_FOLLOW_UP = [
        # (pregunta, debería_enriquecer)
        ("¿Y qué produce en Perú?",            True),   # starts with "¿Y"
        ("¿También opera en Brasil?",           True),   # "también"
        ("¿Qué más hace allí?",                 True),   # "más" + "allí"
        ("¿Cuándo fue fundada?",                False),  # pregunta nueva, suficientes palabras
        ("¿Cuál es el NIT de Manuelita S.A.?",  False),  # pregunta nueva independiente
        ("¿Y eso?",                             True),   # muy corta + follow-up
        ("¿Qué?",                               True),   # muy corta
    ]

    hits = 0
    total = len(PRUEBAS_FOLLOW_UP)

    for pregunta, esperado in PRUEBAS_FOLLOW_UP:
        enriched = agent._enrich_question(pregunta)
        fue_enriquecida = enriched != pregunta
        ok = fue_enriquecida == esperado
        if ok:
            hits += 1
        icono = "✓" if ok else "✗"
        tag = "follow-up" if esperado else "independiente"
        print(f"  {icono} [{tag:12s}] '{pregunta[:50]}'")
        if not ok:
            print(f"       esperado enriquecida={esperado}, obtenido={fue_enriquecida}")

    score = round(hits / total * 100)
    print(f"\n  Score: {hits}/{total} ({score}%)")

    return {"test": "deteccion_follow_up", "ok": score >= 85, "score_pct": score}


# ─────────────────────────────────────────────────────────────
# Prueba de diálogo end-to-end
# ─────────────────────────────────────────────────────────────

DIALOGO = [
    {
        "id": 1,
        "pregunta": "¿Cuál es el NIT de Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["891.300.241"],
        "es_follow_up": False,
    },
    {
        "id": 2,
        "pregunta": "¿Quién es el presidente de Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["Harold", "Eder"],
        "es_follow_up": False,
    },
    {
        "id": 3,
        "pregunta": "¿En qué países opera Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["Colombia", "Perú", "Chile"],
        "es_follow_up": False,
    },
    {
        "id": 4,
        "pregunta": "¿Y cuántos empleados tiene?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["7.971", "colaboradores"],
        "es_follow_up": True,   # "¿Y..." → follow-up
    },
    {
        "id": 5,
        "pregunta": "¿Cuáles son los valores corporativos de Manuelita?",
        "herramienta_esperada": "rag",
        "palabras_clave": ["valores"],
        "es_follow_up": False,
    },
    {
        "id": 6,
        "pregunta": "¿Y cómo se reflejan esos valores en su sostenibilidad?",
        "herramienta_esperada": "rag",
        "palabras_clave": ["sostenibilidad"],
        "es_follow_up": True,   # "¿Y..." + "esos" → follow-up
    },
]


def evaluar_keywords(respuesta: str, palabras: list[str]) -> tuple[int, list[str]]:
    resp_lower = respuesta.lower()
    encontradas = [kw for kw in palabras if kw.lower() in resp_lower]
    return len(encontradas), encontradas


def test_dialogo_completo(provider: str) -> dict:
    """Prueba un diálogo completo de 6 turnos con el agente con memoria."""
    print(f"\n{SEP2}")
    print(f"  TEST 4 — Diálogo end-to-end ({provider.upper()})")
    print(SEP2)

    t_init = time.time()
    agent = ContextualAgent(provider=provider, window_size=5, verbose=False)
    print(f"  Agente inicializado en {round(time.time()-t_init, 1)}s\n")

    resultados = []
    routing_ok = 0

    for turno in DIALOGO:
        t0 = time.time()
        result = agent.chat(turno["pregunta"])
        elapsed = round(time.time() - t0, 2)

        hits, encontradas = evaluar_keywords(result["answer"], turno["palabras_clave"])
        score_pct = round(hits / len(turno["palabras_clave"]) * 100)
        tool_ok = result["tool"] == turno["herramienta_esperada"]
        if tool_ok:
            routing_ok += 1

        icono_tool = "✓" if tool_ok else "✗"
        icono_kw   = "✓" if score_pct == 100 else ("~" if score_pct > 0 else "✗")
        icono_mem  = "🔗" if result.get("enriched") else "  "

        print(f"[{turno['id']:02d}] {icono_mem} {turno['pregunta']}")
        print(f"     Herramienta : {result['tool'].upper():12s} {icono_tool}  (esperada: {turno['herramienta_esperada']})")
        print(f"     Respuesta   : {result['answer'][:160]}{'...' if len(result['answer']) > 160 else ''}")
        print(f"     Keywords    : {encontradas} ({score_pct}%) {icono_kw}")
        print(f"     Memoria     : turno {result.get('turn')}, enriquecida={result.get('enriched')}")
        print(f"     Tiempo      : {elapsed}s\n")

        resultados.append({
            "id": turno["id"],
            "herramienta_esperada": turno["herramienta_esperada"],
            "herramienta_usada": result["tool"],
            "routing_ok": tool_ok,
            "score_pct": score_pct,
            "tiempo_s": elapsed,
            "enriched": result.get("enriched", False),
            "es_follow_up": turno["es_follow_up"],
        })

    # Verificar que el historial se acumuló
    history = agent.get_history()
    print(f"  Historial final: {agent.memory.turn_count()} turnos guardados (window=5)")
    assert agent.memory.turn_count() > 0, "❌ El historial no se guardó"
    print("  ✓ Historial acumulado correctamente\n")

    # ── Resumen ───────────────────────────────────────────────
    avg_score    = round(sum(r["score_pct"] for r in resultados) / len(resultados))
    avg_time     = round(sum(r["tiempo_s"] for r in resultados) / len(resultados), 2)
    routing_pct  = round(routing_ok / len(resultados) * 100)
    enriched_ok  = sum(1 for r in resultados if r["es_follow_up"] and r["enriched"])
    follow_up_n  = sum(1 for r in resultados if r["es_follow_up"])

    return {
        "test": "dialogo_completo",
        "ok": routing_pct == 100,
        "routing_pct": routing_pct,
        "avg_score_pct": avg_score,
        "avg_time_s": avg_time,
        "enriched_ok": enriched_ok,
        "follow_up_n": follow_up_n,
    }


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main():
    provider = os.getenv("LLM_PROVIDER", "local")

    print(f"\n{SEP}")
    print("  TEST MEMORIA CONVERSACIONAL — BLOQUE 4 — MANUELITA S.A.")
    print(SEP)
    print(f"  Proveedor : {provider.upper()}")
    print(SEP)

    resultados_suite = []

    # Test 1: memoria básica (sin LLM)
    r1 = test_memoria_basica()
    resultados_suite.append(r1)

    # Test 2: ventana deslizante (sin LLM)
    r2 = test_ventana_deslizante()
    resultados_suite.append(r2)

    # Test 3: detección de follow-up (con agente, sin invocar LLM)
    r3 = test_deteccion_follow_up(provider)
    resultados_suite.append(r3)

    # Test 4: diálogo completo (usa LLM para preguntas RAG)
    r4 = test_dialogo_completo(provider)
    resultados_suite.append(r4)

    # ── Resumen general ───────────────────────────────────────
    print(f"\n{SEP}")
    print("  RESUMEN FINAL")
    print(SEP)

    tests_ok = sum(1 for r in resultados_suite if r.get("ok"))
    total_tests = len(resultados_suite)

    print(f"  Tests pasados          : {tests_ok}/{total_tests}")
    print(f"  ✓ Memoria básica       : {'OK' if r1['ok'] else 'FAIL'}")
    print(f"  ✓ Ventana deslizante   : {'OK' if r2['ok'] else 'FAIL'}")
    print(f"  ✓ Detección follow-up  : {'OK (' + str(r3['score_pct']) + '%)' if r3['ok'] else 'FAIL (' + str(r3['score_pct']) + '%)'}")
    print(f"  ✓ Diálogo end-to-end   : {'OK' if r4['ok'] else 'FAIL'}")
    print(f"     Routing             : {r4['routing_pct']}%")
    print(f"     Score keywords      : {r4['avg_score_pct']}%")
    print(f"     Tiempo promedio     : {r4['avg_time_s']}s/pregunta")
    print(f"     Follow-ups enriq.   : {r4['enriched_ok']}/{r4['follow_up_n']}")
    print(SEP)

    if tests_ok == total_tests:
        print("\n  ✓ Memoria conversacional funcionando — Bloque 4 completado.")
    elif tests_ok >= 3:
        print("\n  ~ Memoria funcionando bien — revisar casos fallidos.")
    else:
        print("\n  ✗ Hay problemas en la memoria — revisar memory.py.")
    print()


if __name__ == "__main__":
    main()
