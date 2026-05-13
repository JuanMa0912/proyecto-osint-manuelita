"""
test_rag_bloque1.py
-------------------
Verificación completa del motor RAG (Bloque 1 — Módulo 2).

Prueba 4 aspectos clave:
  1. Indexación  — corpus cargado y dividido en chunks correctamente
  2. Recuperación — los chunks más relevantes se recuperan para cada pregunta
  3. Calidad RAG  — las respuestas están fundamentadas en el contexto recuperado
  4. Puntajes    — similitud coseno de los chunks recuperados

Uso:
    # Primera vez (construye el índice):
    uv run python scripts/test_rag_bloque1.py

    # Forzar reindexación:
    uv run python scripts/test_rag_bloque1.py --reindex

    # Usar Ollama en lugar de Gemini (PowerShell):
    $env:LLM_PROVIDER="ollama"; uv run python scripts/test_rag_bloque1.py

    # Usar Ollama en lugar de Gemini (bash/Git Bash):
    LLM_PROVIDER=ollama uv run python scripts/test_rag_bloque1.py
"""

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.langchain_app.rag_engine import ManuelitaRAG

SEP = "=" * 60

# ── Preguntas de prueba ───────────────────────────────────────
PRUEBAS = [
    {
        "id": 1,
        "categoria": "Datos básicos",
        "pregunta": "¿En qué año fue fundada Manuelita y dónde tiene su sede principal?",
        "palabras_clave": ["1864", "Palmira"],
    },
    {
        "id": 2,
        "categoria": "Financiero",
        "pregunta": "¿Cuál es el NIT de Manuelita S.A.?",
        "palabras_clave": ["891.300.241", "NIT"],
    },
    {
        "id": 3,
        "categoria": "Directivos",
        "pregunta": "¿Quién es el presidente de Manuelita?",
        "palabras_clave": ["Harold", "Eder"],
    },
    {
        "id": 4,
        "categoria": "Sostenibilidad",
        "pregunta": "¿Cuál es la meta de emisiones de carbono de Manuelita para 2030?",
        "palabras_clave": ["2030", "carbono", "neutralidad"],
    },
    {
        "id": 5,
        "categoria": "Geografía",
        "pregunta": "¿En qué países tiene operaciones Manuelita?",
        "palabras_clave": ["Colombia", "Perú", "Chile"],
    },
    {
        "id": 6,
        "categoria": "Negocio",
        "pregunta": "¿Cuáles son las unidades de negocio de Manuelita?",
        "palabras_clave": ["azúcar", "palma", "acuicultura"],
    },
]


def evaluar_respuesta(respuesta: str, palabras_clave: list[str]) -> tuple[int, list[str]]:
    """Cuenta cuántas palabras clave aparecen en la respuesta."""
    resp_lower = respuesta.lower()
    encontradas = [kw for kw in palabras_clave if kw.lower() in resp_lower]
    return len(encontradas), encontradas


def main():
    provider   = os.getenv("LLM_PROVIDER", "gemini")
    reindex    = "--reindex" in sys.argv

    print(f"\n{SEP}")
    print("  TEST RAG — BLOQUE 1 — MANUELITA S.A.")
    print(SEP)
    print(f"  Proveedor : {provider.upper()}")
    print(f"  Preguntas : {len(PRUEBAS)}")
    print(SEP)

    # ── 1. Inicializar RAG ─────────────────────────────────────
    t0 = time.time()
    rag = ManuelitaRAG(provider=provider, force_reindex=reindex)
    t_init = round(time.time() - t0, 1)
    print(f"  RAG inicializado en {t_init}s\n")

    # ── 2. Probar recuperación y respuesta ─────────────────────
    resultados = []
    for p in PRUEBAS:
        print(f"[{p['id']}] {p['categoria']}: {p['pregunta']}")

        t1 = time.time()
        result = rag.answer_with_sources(p["pregunta"], k=6)
        elapsed = round(time.time() - t1, 2)

        hits, encontradas = evaluar_respuesta(result["answer"], p["palabras_clave"])
        score_pct = round(hits / len(p["palabras_clave"]) * 100)

        print(f"     Respuesta : {result['answer'][:250]}{'...' if len(result['answer']) > 250 else ''}")
        print(f"     Fuentes   : {', '.join(result['sources'])}")
        print(f"     Palabras  : {encontradas} ({score_pct}% de las esperadas)")
        print(f"     Tiempo    : {elapsed}s\n")

        resultados.append({
            "id": p["id"],
            "categoria": p["categoria"],
            "pregunta": p["pregunta"],
            "respuesta": result["answer"],
            "fuentes": result["sources"],
            "palabras_clave_esperadas": p["palabras_clave"],
            "palabras_encontradas": encontradas,
            "score_pct": score_pct,
            "tiempo_s": elapsed,
        })

    # ── 3. Probar puntajes de similitud ────────────────────────
    print(SEP)
    print("  PUNTAJES DE SIMILITUD (menor = más relevante)")
    print(SEP)
    pregunta_test = "¿Cuántos empleados tiene Manuelita?"
    docs_scores = rag.retrieve_with_scores(pregunta_test, k=3)
    print(f"  Pregunta: {pregunta_test}")
    for i, (doc, score) in enumerate(docs_scores, 1):
        print(f"  [{i}] score={score:.4f}  fuente={doc.metadata['source']}")
        print(f"       {doc.page_content[:120]}...")

    # ── 4. Resumen ─────────────────────────────────────────────
    avg_score = round(sum(r["score_pct"] for r in resultados) / len(resultados))
    avg_time  = round(sum(r["tiempo_s"] for r in resultados) / len(resultados), 2)

    print(f"\n{SEP}")
    print("  RESUMEN")
    print(SEP)
    print(f"  Preguntas probadas  : {len(resultados)}")
    print(f"  Score promedio RAG  : {avg_score}%  (palabras clave halladas)")
    print(f"  Tiempo promedio     : {avg_time}s por pregunta")
    print(SEP)

    # ── 5. Guardar resultados ──────────────────────────────────
    out_path = ROOT / "reports" / f"resultados_rag_bloque1_{provider}.json"
    out_path.parent.mkdir(exist_ok=True)
    out_path.write_text(
        json.dumps(
            {"provider": provider, "resultados": resultados},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"\n  Resultados guardados en: {out_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
