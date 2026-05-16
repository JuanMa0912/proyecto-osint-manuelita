"""
structured_tool.py
------------------
Herramienta LangChain para consulta de datos estructurados de Manuelita S.A.

Carga un JSON con cifras exactas (financiero, operacional, sostenibilidad)
y responde preguntas directas sin necesidad de embeddings ni LLM.

Ventajas frente al RAG:
  - Respuestas exactas (sin alucinaciones)
  - Sin costo de API (no usa embeddings ni LLM)
  - Latencia ~0ms (búsqueda por keywords en memoria)
  - Ideal para cifras numéricas y datos factuales

Uso directo:
    from src.langchain_app.tools.structured_tool import ManuelitaStructuredTool
    tool = ManuelitaStructuredTool()
    print(tool.query("¿Cuántos empleados tiene Manuelita?"))

Uso como herramienta LangChain (para el agente del Bloque 3):
    from src.langchain_app.tools.structured_tool import get_structured_tool
    lc_tool = get_structured_tool()
    # lc_tool es un BaseTool listo para pasarle al AgentExecutor
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ──────────────────────────────────────────────────────────────
# Ruta al JSON de datos estructurados
# ──────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_PATH = ROOT / "data" / "structured" / "manuelita_datos.json"


# ──────────────────────────────────────────────────────────────
# Motor de consulta
# ──────────────────────────────────────────────────────────────

class ManuelitaStructuredTool:
    """
    Motor de consulta sobre datos estructurados de Manuelita S.A.

    Detecta la intención de la pregunta por keywords y devuelve
    una respuesta textual precisa construida desde el JSON.

    Categorías soportadas:
      nit, presidente, fundacion, paises, empleados,
      ingresos, ebitda, unidades, carbono, general
    """

    def __init__(self, data_path: Path = DATA_PATH):
        if not data_path.exists():
            raise FileNotFoundError(
                f"No se encontró el archivo de datos estructurados: {data_path}\n"
                f"Asegúrate de que existe: data/structured/manuelita_datos.json"
            )
        with open(data_path, encoding="utf-8") as f:
            self.data: dict[str, Any] = json.load(f)

        self.keywords: dict[str, list[str]] = self.data.get("keywords", {})

    # ── Detección de intención ─────────────────────────────────

    def _detect_category(self, question: str) -> str:
        """Detecta la categoría temática de la pregunta por keywords.

        Usa word boundaries (\\b) para evitar falsos positivos por substring.
        Ejemplo: 'nit' no debe matchear 'unidades' ni 'comunitar'.
        """
        q = question.lower()
        q = re.sub(r"[¿?¡!.,;:]", "", q)

        for category, kws in self.keywords.items():
            for kw in kws:
                kw_lower = kw.lower()
                # Usar word boundaries para keywords cortas (<=4 chars)
                # para evitar matches parciales como "nit" en "unidades"
                if len(kw_lower) <= 4:
                    if re.search(r"\b" + re.escape(kw_lower) + r"\b", q):
                        return category
                else:
                    if kw_lower in q:
                        return category
        return "general"

    # ── Constructores de respuesta por categoría ───────────────

    def _resp_nit(self) -> str:
        id_ = self.data["identificacion"]
        return (
            f"El NIT de {id_['razon_social']} es **{id_['nit']}**."
        )

    def _resp_presidente(self) -> str:
        d = self.data["directivos"]
        return f"El presidente de Manuelita S.A. es **{d['presidente']}**."

    def _resp_fundacion(self) -> str:
        id_ = self.data["identificacion"]
        return (
            f"Manuelita fue fundada en **{id_['año_fundacion']}** "
            f"en {id_['ciudad_sede']}, {id_['departamento_sede']}, {id_['pais_sede']}. "
            f"Tiene más de {id_['años_historia']} años de historia."
        )

    def _resp_paises(self) -> str:
        geo = self.data["geografia"]
        paises = ", ".join(geo["paises_operacion"])
        return (
            f"Manuelita tiene operaciones en **{geo['numero_paises']} países**: {paises}. "
            f"Sus productos llegan a {geo['paises_exportacion']} países en el mundo."
        )

    @staticmethod
    def _fmt(n: int | float) -> str:
        """Formatea número con punto como separador de miles (estilo español)."""
        return f"{n:,}".replace(",", ".")

    def _resp_empleados(self) -> str:
        op = self.data["operacional"]
        return (
            f"Manuelita cuenta con aproximadamente "
            f"**{self._fmt(op['colaboradores_2022'])} colaboradores** (2022). "
            f"Adicionalmente beneficia a más de {self._fmt(op['familias_beneficiadas'])} familias "
            f"de empleados y comunidades vecinas."
        )

    def _resp_ingresos(self) -> str:
        fin = self.data["financiero"]
        anio = fin["año_mas_reciente"]
        hist = fin["historico"][str(anio)]
        return (
            f"Los ingresos de Manuelita en **{anio}** fueron de "
            f"**${self._fmt(hist['ingresos'])} millones COP**. "
            f"En 2022 alcanzaron ${self._fmt(fin['historico']['2022']['ingresos'])} millones COP "
            f"(+48.9% vs 2021, impulsado por precios del azúcar)."
        )

    def _resp_ebitda(self) -> str:
        fin = self.data["financiero"]
        anio = fin["año_mas_reciente"]
        hist = fin["historico"][str(anio)]
        return (
            f"El EBITDA de Manuelita en **{anio}** fue de "
            f"**${self._fmt(hist['ebitda'])} millones COP** "
            f"(margen {hist['ebitda_margen_pct']}%). "
            f"El ratio Deuda/EBITDA es de {hist['ratio_deuda_ebitda']}x, "
            f"lo que indica una sólida salud financiera."
        )

    def _resp_unidades(self) -> str:
        unidades = self.data["unidades_negocio"]
        plataformas = self.data["plataformas"]
        lineas = []
        for u in unidades:
            lineas.append(
                f"  - **{u['nombre']}** ({u['pais']}, {u['participacion_pct']}%) "
                f"— {', '.join(u['productos'][:2])}"
            )
        return (
            f"Manuelita opera **{len(unidades)} unidades de negocio** "
            f"en {len(plataformas)} plataformas ({', '.join(plataformas)}):\n"
            + "\n".join(lineas)
        )

    def _resp_carbono(self) -> str:
        sos = self.data["sostenibilidad"]["metas_carbono"]
        return (
            f"La meta de carbono de Manuelita para **2030** es una "
            f"**reducción del {sos['reduccion_pct_2030']}%** en emisiones "
            f"de Alcances 1 y 2 (Scope 1 y 2). "
            f"La neutralidad de carbono está proyectada para **{sos['año_neutralidad']}**. "
            f"En 2024 redujo sus emisiones un {sos['reduccion_2024_vs_2023_pct']}% "
            f"respecto a 2023."
        )

    def _resp_general(self) -> str:
        id_ = self.data["identificacion"]
        geo = self.data["geografia"]
        fin = self.data["financiero"]
        anio = fin["año_mas_reciente"]
        return (
            f"**{id_['razon_social']}** (NIT {id_['nit']}) es una empresa "
            f"agroindustrial colombiana fundada en {id_['año_fundacion']} en "
            f"{id_['ciudad_sede']}, {id_['pais_sede']}. "
            f"Opera en {geo['numero_paises']} países "
            f"({', '.join(geo['paises_operacion'])}) con "
            f"{len(self.data['unidades_negocio'])} unidades de negocio. "
            f"En {anio} reportó ingresos de "
            f"${self._fmt(fin['historico'][str(anio)]['ingresos'])} millones COP."
        )

    # ── API pública ────────────────────────────────────────────

    def query(self, question: str) -> str:
        """
        Responde una pregunta usando los datos estructurados.

        Args:
            question: pregunta en lenguaje natural

        Returns:
            Respuesta textual precisa construida desde el JSON.
            Si no hay datos suficientes devuelve un mensaje indicándolo.
        """
        if not question or not question.strip():
            return "Por favor escribe una pregunta."

        category = self._detect_category(question)
        handlers = {
            "nit":        self._resp_nit,
            "presidente": self._resp_presidente,
            "fundacion":  self._resp_fundacion,
            "paises":     self._resp_paises,
            "empleados":  self._resp_empleados,
            "ingresos":   self._resp_ingresos,
            "ebitda":     self._resp_ebitda,
            "unidades":   self._resp_unidades,
            "carbono":    self._resp_carbono,
            "general":    self._resp_general,
        }
        return handlers[category]()

    def get_categories(self) -> list[str]:
        """Devuelve las categorías temáticas disponibles."""
        return list(self.keywords.keys())

    def get_raw(self, section: str) -> Any:
        """Acceso directo a una sección del JSON (para uso avanzado)."""
        return self.data.get(section)


# ──────────────────────────────────────────────────────────────
# Integración con LangChain (BaseTool)
# ──────────────────────────────────────────────────────────────

def get_structured_tool():
    """
    Devuelve la herramienta como un BaseTool de LangChain,
    lista para pasarle al AgentExecutor del Bloque 3.

    Uso:
        tools = [get_structured_tool(), get_rag_tool()]
        agent = initialize_agent(tools, llm, ...)
    """
    from langchain.tools import Tool

    engine = ManuelitaStructuredTool()

    return Tool(
        name="ManuelitaDatosEstructurados",
        func=engine.query,
        description=(
            "Útil para responder preguntas con datos exactos de Manuelita S.A.: "
            "NIT, presidente, año de fundación, países de operación, número de empleados, "
            "cifras financieras (ingresos, EBITDA), unidades de negocio, "
            "y metas de sostenibilidad/carbono. "
            "NO usar para preguntas abiertas sobre estrategia, cultura o historia narrativa — "
            "para eso usar la herramienta RAG."
        ),
    )


# ──────────────────────────────────────────────────────────────
# Ejecución directa — prueba rápida
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tool = ManuelitaStructuredTool()
    preguntas = [
        "¿Cuál es el NIT de Manuelita?",
        "¿Quién es el presidente?",
        "¿En qué año fue fundada?",
        "¿En qué países opera?",
        "¿Cuántos empleados tiene?",
        "¿Cuáles fueron los ingresos en 2023?",
        "¿Cuál es el EBITDA?",
        "¿Cuáles son las unidades de negocio?",
        "¿Cuál es la meta de carbono para 2030?",
    ]
    print("\n" + "="*55)
    print("  TEST STRUCTURED TOOL — MANUELITA S.A.")
    print("="*55)
    for q in preguntas:
        print(f"\n▶ {q}")
        print(f"  {tool.query(q)}")
