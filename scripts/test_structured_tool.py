"""
test_structured_tool.py
-----------------------
Verificación completa de la herramienta de datos estructurados (Bloque 2).

Prueba 3 aspectos:
  1. Detección de intención  — categoría correcta por keywords
  2. Calidad de respuesta    — palabras clave esperadas en la respuesta
  3. Integración LangChain   — herramienta funciona como BaseTool

Uso:
    uv run python scripts/test_structured_tool.py
"""

import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.langchain_app.tools.structured_tool import ManuelitaStructuredTool, get_structured_tool

SEP = "=" * 60

PRUEBAS = [
    {
        "id": 1,
        "categoria_esperada": "nit",
        "pregunta": "¿Cuál es el NIT de Manuelita S.A.?",
        "palabras_clave": ["891.300.241", "NIT"],
    },
    {
        "id": 2,
        "categoria_esperada": "presidente",
        "pregunta": "¿Quién es el presidente de Manuelita?",
        "palabras_clave": ["Harold", "Eder"],
    },
    {
        "id": 3,
        "categoria_esperada": "fundacion",
        "pregunta": "¿En qué año fue fundada Manuelita y dónde?",
        "palabras_clave": ["1864", "Palmira"],
    },
    {
        "id": 4,
        "categoria_esperada": "paises",
        "pregunta": "¿En qué países tiene operaciones Manuelita?",
        "palabras_clave": ["Colombia", "Perú", "Chile"],
    },
    {
        "id": 5,
        "categoria_esperada": "empleados",
        "pregunta": "¿Cuántos empleados o colaboradores tiene Manuelita?",
        "palabras_clave": ["7.971", "colaboradores"],
    },
    {
        "id": 6,
        "categoria_esperada": "ingresos",
        "pregunta": "¿Cuáles fueron los ingresos de Manuelita en 2023?",
        "palabras_clave": ["1.043.562", "2023"],
    },
    {
        "id": 7,
        "categoria_esperada": "ebitda",
        "pregunta": "¿Cuál es el EBITDA de Manuelita?",
        "palabras_clave": ["369.380", "35.4"],
    },
    {
        "id": 8,
        "categoria_esperada": "unidades",
        "pregunta": "¿Cuáles son las unidades de negocio de Manuelita?",
        "palabras_clave": ["Azúcar", "Aceites", "Acuicultura"],
    },
    {
        "id": 9,
        "categoria_esperada": "carbono",
        "pregunta": "¿Cuál es la meta de emisiones de carbono para 2030?",
        "palabras_clave": ["70%", "2030", "2040"],
    },
    {
        "id": 10,
        "categoria_esperada": "general",
        "pregunta": "Cuéntame sobre Manuelita",
        "palabras_clave": ["1864", "Colombia", "NIT"],
    },
]


def evaluar(respuesta: str, palabras: list[str]) -> tuple[int, list[str]]:
    resp_lower = respuesta.lower()
    encontradas = [kw for kw in palabras if kw.lower() in resp_lower]
    return len(encontradas), encontradas


def main():
    print(f"\n{SEP}")
    print("  TEST STRUCTURED TOOL — BLOQUE 2 — MANUELITA S.A.")
    print(SEP)

    tool = ManuelitaStructuredTool()
    print(f"  Categorías disponibles: {tool.get_categories()}\n")

    resultados = []
    cat_correctas = 0

    for p in PRUEBAS:
        t0 = time.time()
        categoria_detectada = tool._detect_category(p["pregunta"])
        respuesta = tool.query(p["pregunta"])
        elapsed = round(time.time() - t0, 4)

        hits, encontradas = evaluar(respuesta, p["palabras_clave"])
        score_pct = round(hits / len(p["palabras_clave"]) * 100)
        cat_ok = categoria_detectada == p["categoria_esperada"]
        if cat_ok:
            cat_correctas += 1

        estado_cat = "✓" if cat_ok else "✗"
        print(f"[{p['id']:02d}] {p['pregunta']}")
        print(f"     Categoría : {categoria_detectada} {estado_cat}  (esperada: {p['categoria_esperada']})")
        print(f"     Respuesta : {respuesta[:200]}{'...' if len(respuesta) > 200 else ''}")
        print(f"     Keywords  : {encontradas} ({score_pct}%)")
        print(f"     Tiempo    : {elapsed}s\n")

        resultados.append({
            "id": p["id"],
            "categoria_ok": cat_ok,
            "score_pct": score_pct,
            "tiempo_s": elapsed,
        })

    # ── Resumen ───────────────────────────────────────────────
    avg_score = round(sum(r["score_pct"] for r in resultados) / len(resultados))
    avg_time = round(sum(r["tiempo_s"] for r in resultados) / len(resultados), 4)

    print(SEP)
    print("  RESUMEN")
    print(SEP)
    print(f"  Preguntas probadas       : {len(resultados)}")
    print(f"  Categorías detectadas OK : {cat_correctas}/{len(resultados)} ({round(cat_correctas/len(resultados)*100)}%)")
    print(f"  Score keywords promedio  : {avg_score}%")
    print(f"  Tiempo promedio          : {avg_time}s por pregunta")
    print(SEP)

    # ── Test integración LangChain ─────────────────────────────
    print("\n  TEST INTEGRACIÓN LANGCHAIN")
    print(SEP)
    lc_tool = get_structured_tool()
    print(f"  Nombre     : {lc_tool.name}")
    print(f"  Descripción: {lc_tool.description[:100]}...")
    resp_lc = lc_tool.func("¿Cuál es el NIT de Manuelita?")
    print(f"  Prueba NIT : {resp_lc}")
    print(f"  Estado     : {'✓ OK' if '891.300.241' in resp_lc else '✗ FALLA'}")
    print(SEP)


if __name__ == "__main__":
    main()
