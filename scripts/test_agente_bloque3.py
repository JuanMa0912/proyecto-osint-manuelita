"""
test_agente_bloque3.py
----------------------
Verificación completa del agente router (Bloque 3 — Módulo 2).

Prueba 3 aspectos:
  1. Routing    — la herramienta correcta se elige para cada tipo de pregunta
  2. Respuesta  — la respuesta contiene las palabras clave esperadas
  3. Integración — ambas herramientas coexisten sin conflictos

Uso:
    uv run python scripts/test_agente_bloque3.py

    # Con Gemini:
    $env:LLM_PROVIDER="gemini"; uv run python scripts/test_agente_bloque3.py

    # Con Ollama (requiere ollama serve + llama3.2:3b):
    $env:LLM_PROVIDER="local"; uv run python scripts/test_agente_bloque3.py
"""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.langchain_app.agent import ManuelitaAgent

SEP = "=" * 60

PRUEBAS = [
    # ── Preguntas que deben ir a DATOS ESTRUCTURADOS ──────────
    {
        "id": 1,
        "pregunta": "¿Cuál es el NIT de Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["891.300.241"],
    },
    {
        "id": 2,
        "pregunta": "¿Quién es el presidente de Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["Harold", "Eder"],
    },
    {
        "id": 3,
        "pregunta": "¿En qué año fue fundada Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["1864"],
    },
    {
        "id": 4,
        "pregunta": "¿Cuántos empleados tiene Manuelita?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["7.971", "colaboradores"],
    },
    {
        "id": 5,
        "pregunta": "¿Cuáles fueron los ingresos en 2023?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["1.043.562", "2023"],
    },
    {
        "id": 6,
        "pregunta": "¿Cuál es la meta de carbono para 2030?",
        "herramienta_esperada": "estructurado",
        "palabras_clave": ["70%", "2030"],
    },
    # ── Preguntas que deben ir a RAG ──────────────────────────
    {
        "id": 7,
        "pregunta": "¿Cuáles son los valores corporativos de Manuelita?",
        "herramienta_esperada": "rag",
        "palabras_clave": ["integridad", "valores"],
    },
    {
        "id": 8,
        "pregunta": "¿Cómo gestiona Manuelita la sostenibilidad ambiental?",
        "herramienta_esperada": "rag",
        "palabras_clave": ["sostenibilidad", "ambiental"],
    },
    {
        "id": 9,
        "pregunta": "¿Qué premios o reconocimientos ha recibido Manuelita?",
        "herramienta_esperada": "rag",
        "palabras_clave": ["MERCO", "reputación"],
    },
    {
        "id": 10,
        "pregunta": "¿Cómo impacta Manuelita a las comunidades vecinas?",
        "herramienta_esperada": "rag",
        "palabras_clave": ["comunidades", "social"],
    },
]


def evaluar(respuesta: str, palabras: list[str]) -> tuple[int, list[str]]:
    resp_lower = respuesta.lower()
    encontradas = [kw for kw in palabras if kw.lower() in resp_lower]
    return len(encontradas), encontradas


def main():
    provider = os.getenv("LLM_PROVIDER", "local")

    print(f"\n{SEP}")
    print("  TEST AGENTE ROUTER — BLOQUE 3 — MANUELITA S.A.")
    print(SEP)
    print(f"  Proveedor RAG : {provider.upper()}")
    print(f"  Preguntas     : {len(PRUEBAS)} ({sum(1 for p in PRUEBAS if p['herramienta_esperada']=='estructurado')} estructurado / {sum(1 for p in PRUEBAS if p['herramienta_esperada']=='rag')} RAG)")
    print(SEP)

    t_init = time.time()
    agent = ManuelitaAgent(provider=provider, verbose=False)
    print(f"  Agente inicializado en {round(time.time()-t_init, 1)}s\n")

    resultados = []
    routing_ok = 0

    for p in PRUEBAS:
        t0 = time.time()
        result = agent.ask(p["pregunta"])
        elapsed = round(time.time() - t0, 2)

        hits, encontradas = evaluar(result["answer"], p["palabras_clave"])
        score_pct = round(hits / len(p["palabras_clave"]) * 100)
        tool_ok = result["tool"] == p["herramienta_esperada"]
        if tool_ok:
            routing_ok += 1

        icono_tool = "✓" if tool_ok else "✗"
        icono_kw   = "✓" if score_pct == 100 else ("~" if score_pct > 0 else "✗")

        print(f"[{p['id']:02d}] {p['pregunta']}")
        print(f"     Herramienta : {result['tool'].upper():12s} {icono_tool}  (esperada: {p['herramienta_esperada']})")
        print(f"     Respuesta   : {result['answer'][:180]}{'...' if len(result['answer']) > 180 else ''}")
        print(f"     Keywords    : {encontradas} ({score_pct}%) {icono_kw}")
        print(f"     Fuentes     : {result['sources']}")
        print(f"     Tiempo      : {elapsed}s\n")

        resultados.append({
            "id": p["id"],
            "herramienta_esperada": p["herramienta_esperada"],
            "herramienta_usada": result["tool"],
            "routing_ok": tool_ok,
            "score_pct": score_pct,
            "tiempo_s": elapsed,
        })

    # ── Resumen ───────────────────────────────────────────────
    avg_score = round(sum(r["score_pct"] for r in resultados) / len(resultados))
    avg_time  = round(sum(r["tiempo_s"] for r in resultados) / len(resultados), 2)
    routing_pct = round(routing_ok / len(resultados) * 100)

    estructurado_ok = sum(1 for r in resultados if r["herramienta_esperada"] == "estructurado" and r["routing_ok"])
    rag_ok          = sum(1 for r in resultados if r["herramienta_esperada"] == "rag" and r["routing_ok"])

    print(SEP)
    print("  RESUMEN")
    print(SEP)
    print(f"  Preguntas probadas       : {len(resultados)}")
    print(f"  Routing correcto         : {routing_ok}/{len(resultados)} ({routing_pct}%)")
    print(f"    → Estructurado         : {estructurado_ok}/{sum(1 for p in PRUEBAS if p['herramienta_esperada']=='estructurado')}")
    print(f"    → RAG                  : {rag_ok}/{sum(1 for p in PRUEBAS if p['herramienta_esperada']=='rag')}")
    print(f"  Score keywords promedio  : {avg_score}%")
    print(f"  Tiempo promedio          : {avg_time}s por pregunta")
    print(SEP)

    if routing_pct == 100:
        print("\n  ✓ Router funcionando perfectamente — Bloque 3 completado.")
    elif routing_pct >= 80:
        print("\n  ~ Router funcionando bien — revisar casos fallidos.")
    else:
        print("\n  ✗ Router necesita ajuste — revisar keywords en structured_tool.py.")
    print()


if __name__ == "__main__":
    main()
