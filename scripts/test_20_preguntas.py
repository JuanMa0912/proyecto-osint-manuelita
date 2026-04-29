"""
test_20_preguntas.py
--------------------
Script de prueba automático para el sistema Q&A de Manuelita S.A.
Ejecuta las 20 preguntas del trabajo académico (Módulo 1) y guarda los
resultados en reports/resultados_20_preguntas.json y en un resumen .txt.

Uso:
    cd proyecto_manuelita
    uv run python scripts/test_20_preguntas.py

    # Forzar proveedor sin cambiar el .env:
    LLM_PROVIDER=gemini uv run python scripts/test_20_preguntas.py
    LLM_PROVIDER=ollama uv run python scripts/test_20_preguntas.py
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Asegurar que el root del proyecto esté en el path
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from src.langchain_app.qa_system import ManuelitaQASystem

# ---------------------------------------------------------------------------
# Las 20 preguntas del trabajo académico
# ---------------------------------------------------------------------------
PREGUNTAS = [
    "¿Cuántos años tiene Manuelita de haber sido fundada?",
    "¿Cuáles son sus unidades de negocio?",
    "¿Cuántos empleados tiene?",
    "¿Quién es el presidente de Manuelita?",
    "¿En qué año empezaron a producir bioetanol y biodiésel?",
    "¿Cuál es la capacidad de procesamiento de caña por año?",
    "¿En qué lugares tiene operaciones Manuelita?",
    "¿Cuáles son los ingresos económicos reportados en 2023?",
    "¿Cuál es el NIT de la empresa?",
    "¿Cuáles fueron las utilidades brutas 2019-2024?",
    "¿Cuál es el capital de trabajo neto en 2024?",
    "NIT 891.300.199 ¿a qué razón social corresponde?",
    "¿Qué porcentaje de mujeres aumentó con política de equidad?",
    "¿En qué zonas realiza operaciones de acuicultura?",
    "¿Cuál es el tema principal del LinkedIn de Manuelita?",
    "¿Cuántos videos tiene el canal de YouTube?",
    "¿Manuelita asistió a la COP16?",
    "¿Cuántos suscriptores tiene el canal de YouTube?",
    "¿Cuál es la meta de emisión de carbono para 2030?",
    "¿En qué países tiene presencia Manuelita?",
]

SEPARATOR = "=" * 70


def run_tests(provider: str | None = None) -> dict:
    """Ejecuta las 20 preguntas y devuelve el dict con resultados."""
    provider = provider or os.getenv("LLM_PROVIDER", "gemini")
    gemini_api_key = os.getenv("GEMINI_API_KEY", "")

    print(SEPARATOR)
    print("  TEST AUTOMÁTICO — 20 PREGUNTAS — MANUELITA S.A.")
    print(SEPARATOR)
    print(f"  Proveedor: {provider.upper()}")
    print(f"  Inicio   : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR + "\n")

    qa = ManuelitaQASystem(provider=provider, gemini_api_key=gemini_api_key)

    resultados = []
    for i, pregunta in enumerate(PREGUNTAS, 1):
        print(f"[{i:02d}/20] {pregunta}")
        t0 = time.time()
        try:
            respuesta = qa.answer_question(pregunta)
            estado = "OK"
        except Exception as exc:
            respuesta = f"ERROR: {exc}"
            estado = "ERROR"
        elapsed = round(time.time() - t0, 2)

        print(f"        → {respuesta[:200]}{'...' if len(respuesta) > 200 else ''}")
        print(f"        ⏱  {elapsed}s  [{estado}]\n")

        resultados.append({
            "num": i,
            "pregunta": pregunta,
            "respuesta": respuesta,
            "tiempo_segundos": elapsed,
            "estado": estado,
        })

    # Estadísticas
    ok_count = sum(1 for r in resultados if r["estado"] == "OK")
    err_count = len(resultados) - ok_count
    total_time = round(sum(r["tiempo_segundos"] for r in resultados), 2)
    avg_time = round(total_time / len(resultados), 2)

    output = {
        "metadata": {
            "fecha": datetime.now().isoformat(),
            "proveedor": provider,
            "modelo": qa.model_name,
            "total_preguntas": len(resultados),
            "respuestas_ok": ok_count,
            "errores": err_count,
            "tiempo_total_segundos": total_time,
            "tiempo_promedio_segundos": avg_time,
        },
        "resultados": resultados,
    }

    print(SEPARATOR)
    print("  RESUMEN")
    print(SEPARATOR)
    print(f"  Preguntas respondidas : {ok_count}/{len(resultados)}")
    print(f"  Errores               : {err_count}")
    print(f"  Tiempo total          : {total_time}s")
    print(f"  Tiempo promedio       : {avg_time}s por pregunta")
    print(SEPARATOR)

    return output


def save_results(output: dict, out_dir: Path) -> tuple[Path, Path]:
    """Guarda JSON y TXT con los resultados."""
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    provider = output["metadata"]["proveedor"]

    # JSON completo
    json_path = out_dir / f"resultados_20_preguntas_{provider}_{ts}.json"
    json_path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    # TXT legible para el informe
    txt_path = out_dir / f"resultados_20_preguntas_{provider}_{ts}.txt"
    lines = [
        "RESULTADOS TEST AUTOMÁTICO — 20 PREGUNTAS — MANUELITA S.A.",
        "=" * 70,
        f"Fecha     : {output['metadata']['fecha']}",
        f"Proveedor : {output['metadata']['proveedor'].upper()}",
        f"Modelo    : {output['metadata']['modelo']}",
        f"OK / Total: {output['metadata']['respuestas_ok']} / {output['metadata']['total_preguntas']}",
        f"Tiempo    : {output['metadata']['tiempo_total_segundos']}s total  "
        f"({output['metadata']['tiempo_promedio_segundos']}s promedio)",
        "=" * 70,
        "",
    ]
    for r in output["resultados"]:
        lines += [
            f"[{r['num']:02d}] {r['pregunta']}",
            f"     → {r['respuesta']}",
            f"     ⏱ {r['tiempo_segundos']}s  [{r['estado']}]",
            "",
        ]
    txt_path.write_text("\n".join(lines), encoding="utf-8")

    return json_path, txt_path


if __name__ == "__main__":
    out_dir = ROOT / "reports"
    output = run_tests()
    json_path, txt_path = save_results(output, out_dir)

    print(f"\n✅  JSON guardado en: {json_path.relative_to(ROOT)}")
    print(f"✅  TXT  guardado en: {txt_path.relative_to(ROOT)}")
