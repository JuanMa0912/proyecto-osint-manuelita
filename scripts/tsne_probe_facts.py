#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Fuente única de verdad de los 20 hechos etiquetados del bonus t-SNE (Módulo 3).
================================================================================
Este módulo es el "ground-truth" del análisis de clústeres de la memoria real de
OpenFang. Define:

  - PROBE_FACTS: 20 hechos de Manuelita S.A. (4 por tema × 5 temas), idénticos a
    los que el loader inyecta a la memoria del agente vía `memory_store`. Son la
    verdad-de-terreno: cada hecho ya viene con su tema correcto.

  - clean_memory_content(): quita el envoltorio episódico con que OpenFang guarda
    las memorias ("User asked: ... <HECHO> ... I responded: ...") y devuelve el
    hecho/pregunta limpio.

  - match_theme(): fuzzy-match (acentos/mayúsculas normalizados) del content
    limpio contra PROBE_FACTS para asignar el tema de verdad-de-terreno, o None
    si la memoria no es etiquetable (p. ej. una conversación cualquiera).

  - load_probe(): loader que recorre PROBE_FACTS y los inyecta a la memoria del
    agente con `openfang message <uuid> "..."`. SOLO stdlib. Lo corre el
    orquestador DENTRO de WSL (requiere el binario y el daemon); NO se ejecuta en
    Windows.

Diseño: este archivo NO importa numpy ni sklearn ni nada pesado, para que
`tsne_sesiones_m3.py` y el loader de WSL puedan importarlo sin arrastrar deps.
"""
from __future__ import annotations

import difflib
import re
import subprocess
import sys
import time
import unicodedata

# ---------------------------------------------------------------------------
# 20 hechos etiquetados (4 por tema, 5 temas). Verdad-de-terreno del análisis.
# El TEXTO debe coincidir EXACTAMENTE con lo que el loader inyecta a la memoria,
# para que el fuzzy-match cierre con ratio alto.
# ---------------------------------------------------------------------------
PROBE_FACTS: list[tuple[str, str]] = [
    # --- Identidad/Corporativo ---
    ("Manuelita S.A. tiene NIT 891.300.241, fue fundada en 1864 por Santiago Eder, "
     "con sede principal en Palmira, Valle del Cauca, Colombia.",
     "Identidad/Corporativo"),
    ("El presidente de Manuelita S.A. es Harold Eder, y la empresa es dirigida por "
     "la familia Eder desde hace seis generaciones.",
     "Identidad/Corporativo"),
    ("Manuelita tiene aproximadamente 7.971 colaboradores y mas de 160 anos de "
     "trayectoria como empresa familiar agroindustrial colombiana.",
     "Identidad/Corporativo"),
    ("El centro corporativo de Manuelita esta en Cali; su actividad principal CIIU "
     "C1071 es la elaboracion y refinacion de azucar.",
     "Identidad/Corporativo"),

    # --- Geografia/Operacion ---
    ("Manuelita tiene operaciones agroindustriales en tres paises: Colombia, Peru y Chile.",
     "Geografía/Operación"),
    ("Manuelita exporta y vende sus productos al exterior a 49 paises en los cinco continentes.",
     "Geografía/Operación"),
    ("El ingenio azucarero principal de Manuelita esta en Palmira, Valle del Cauca, "
     "y en Peru opera la unidad Agroindustrial Laredo.",
     "Geografía/Operación"),
    ("La operacion de palma de aceite de Manuelita se desarrolla en los Llanos "
     "Orientales de Colombia.",
     "Geografía/Operación"),

    # --- Financiero ---
    ("En 2023 Manuelita tuvo ingresos individuales por 1.043.562 millones de COP, "
     "EBITDA de 369.380 millones (margen 35,4%) y utilidad neta de 78.153 millones.",
     "Financiero"),
    ("En 2022 los ingresos individuales de Manuelita S.A. fueron 966.169 millones de "
     "pesos colombianos.",
     "Financiero"),
    ("En 2021 los ingresos individuales de Manuelita S.A. fueron 648.942 millones de "
     "pesos colombianos.",
     "Financiero"),
    ("Las cifras individuales corresponden solo a Manuelita S.A.; las consolidadas del "
     "Grupo (cerca de 2,7 billones de COP en 2022) son un alcance contable distinto.",
     "Financiero"),

    # --- Sostenibilidad ---
    ("Las metas de sostenibilidad de Manuelita son reducir 70% de emisiones de Alcances "
     "1 y 2 al 2030 y alcanzar neutralidad de carbono al 2040.",
     "Sostenibilidad"),
    ("Manuelita beneficia a mas de 4.000 familias de empleados y comunidades vecinas con "
     "sus programas sociales.",
     "Sostenibilidad"),
    ("Manuelita cuenta con certificaciones de sostenibilidad RSPO, HACCP, ASC y GRI.",
     "Sostenibilidad"),
    ("Manuelita genera energia limpia a partir del bagazo de la cana y reporta su "
     "desempeno ambiental bajo el estandar GRI.",
     "Sostenibilidad"),

    # --- Productos/Produccion ---
    ("Manuelita tiene 4 plataformas de negocio: azucar de cana, palma de aceite, "
     "acuicultura, y frutas y hortalizas.",
     "Productos/Producción"),
    ("Manuelita tiene 7 unidades de negocio: Azucar y Energia, Laredo, Aceites y Energia, "
     "Palmar de Altamira, Acuicultura, Oceanos, y Frutas y Hortalizas.",
     "Productos/Producción"),
    ("Manuelita produce cerca de 487.000 toneladas de azucar al ano y unos 275 millones "
     "de litros de bioetanol.",
     "Productos/Producción"),
    ("En su plataforma de frutas y hortalizas Manuelita cultiva uva, aguacate y otros "
     "productos para exportacion.",
     "Productos/Producción"),
]

# Lista de temas válidos (para validar / iterar sin asumir orden).
PROBE_THEMES: list[str] = sorted({tema for _, tema in PROBE_FACTS})


# ---------------------------------------------------------------------------
# Limpieza del envoltorio episódico de las memorias de OpenFang
# ---------------------------------------------------------------------------
# Formato real observado (ver reports/modulo3/tsne_analisis.md y CLAUDE.md):
#   "User asked: Usa la herramienta memory_store para guardar EXACTAMENTE este
#    hecho de Manuelita, sin alterarlo: <HECHO>"
#   (a veces seguido de "\nI responded: ...").
# También hay memorias conversacionales: "User asked: <pregunta>\nI responded: <resp>".

# Patrón del prefijo de la instrucción memory_store. Tolerante a variantes de
# espaciado/acentos y a que "EXACTAMENTE" venga en cualquier capitalización.
_STORE_PREFIX = re.compile(
    r"usa\s+la\s+herramienta\s+memory_store\s+para\s+guardar\s+exactamente\s+"
    r"este\s+hecho\s+de\s+manuelita,?\s*sin\s+alterarlo\s*:\s*",
    re.IGNORECASE,
)

# "User asked:" / "I responded:" como delimitadores del turno episódico.
_USER_ASKED = re.compile(r"^\s*user\s+asked\s*:\s*", re.IGNORECASE)
_I_RESPONDED = re.compile(r"\bI\s+responded\s*:", re.IGNORECASE)


def clean_memory_content(content: str) -> str:
    """Devuelve el hecho/pregunta limpio de una fila `memories.content`.

    Reglas (en orden):
      1. Si el content trae el bloque "I responded:", nos quedamos solo con la
         parte de la pregunta (antes de la respuesta) para no contaminar el match.
      2. Se quita el prefijo "User asked:" si está.
      3. Si lo que queda es la instrucción de memory_store, se devuelve solo el
         <HECHO> que viene tras "...sin alterarlo:".
      4. Si no matchea ningún patrón conocido, se devuelve el texto tal cual
         (trim) — caso de memoria conversacional u otro formato.
    """
    if not content:
        return ""
    texto = content.strip()

    # 1) Cortar la parte "I responded: ..." si existe (nos interesa la pregunta).
    m = _I_RESPONDED.search(texto)
    if m:
        texto = texto[: m.start()].strip()

    # 2) Quitar "User asked:" inicial.
    texto = _USER_ASKED.sub("", texto).strip()

    # 3) ¿Es la instrucción de memory_store? Devolver solo el hecho.
    m = _STORE_PREFIX.search(texto)
    if m:
        return texto[m.end():].strip()

    # 4) Texto conversacional / desconocido — tal cual.
    return texto


# ---------------------------------------------------------------------------
# Fuzzy-match contra la verdad-de-terreno
# ---------------------------------------------------------------------------
def _normalizar(texto: str) -> str:
    """Minúsculas, sin acentos, sin puntuación, espacios colapsados."""
    texto = texto.lower().strip()
    # Quitar acentos (NFD + descartar diacríticos combinantes).
    texto = "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )
    # Sustituir todo lo no alfanumérico por espacio.
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _ratio_solapamiento_tokens(a: str, b: str) -> float:
    """Solapamiento Jaccard de tokens como señal complementaria al SequenceMatcher.

    Robusto cuando el LLM reordena/recorta el hecho pero conserva el vocabulario.
    Espera dos cadenas YA normalizadas (minúsculas, sin acentos).
    """
    ta, tb = set(a.split()), set(b.split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    union = len(ta | tb)
    return inter / union


def match_theme(content: str, umbral: float = 0.6) -> str | None:
    """Tema de verdad-de-terreno del content, o None si no es etiquetable.

    Combina dos métricas sobre el texto normalizado (acentos/mayúsculas fuera):
      - difflib.SequenceMatcher.ratio() (similitud de secuencia de caracteres).
      - solapamiento Jaccard de tokens (robusto a reordenamientos del LLM).
    Se queda con el mejor hecho según el MÁXIMO de ambas; si ese máximo supera el
    umbral, devuelve su tema. Si no, None (memoria conversacional/no etiquetable).
    """
    limpio = clean_memory_content(content)
    if not limpio:
        return None
    q = _normalizar(limpio)
    if not q:
        return None

    mejor_tema: str | None = None
    mejor_score = 0.0
    for fact, tema in PROBE_FACTS:
        f = _normalizar(fact)
        seq = difflib.SequenceMatcher(None, q, f).ratio()
        jac = _ratio_solapamiento_tokens(q, f)
        score = max(seq, jac)
        if score > mejor_score:
            mejor_score = score
            mejor_tema = tema

    return mejor_tema if mejor_score >= umbral else None


# ---------------------------------------------------------------------------
# Loader (se ejecuta DENTRO de WSL — solo stdlib)
# ---------------------------------------------------------------------------
def load_probe(uuid: str, sleep: float = 4.0,
               binary: str = "/root/.openfang/bin/openfang") -> int:
    """Inyecta los 20 PROBE_FACTS a la memoria del agente `uuid` vía memory_store.

    Recorre PROBE_FACTS y por cada hecho ejecuta:
        openfang message <uuid> "Usa la herramienta memory_store para guardar
        EXACTAMENTE este hecho de Manuelita, sin alterarlo: <HECHO>"
    con `sleep` segundos entre cada uno (evita 429 / saturar el daemon).

    Devuelve el número de hechos enviados sin excepción. NO se corre en Windows:
    requiere el binario de OpenFang y el daemon vivo dentro de WSL.
    """
    enviados = 0
    total = len(PROBE_FACTS)
    for i, (fact, tema) in enumerate(PROBE_FACTS, 1):
        prompt = ("Usa la herramienta memory_store para guardar EXACTAMENTE este "
                  f"hecho de Manuelita, sin alterarlo: {fact}")
        print(f"[{i}/{total}] ({tema}) -> {fact[:60]}...", flush=True)
        try:
            subprocess.run([binary, "message", uuid, prompt], check=False)
            enviados += 1
        except Exception as exc:  # noqa: BLE001 — queremos seguir con el resto
            print(f"   ERROR enviando hecho {i}: {exc}", file=sys.stderr, flush=True)
        if i < total:
            time.sleep(sleep)
    print(f"Hechos enviados: {enviados}/{total}", flush=True)
    return enviados


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("Uso: python tsne_probe_facts.py <uuid-del-agente> [sleep] [binary]\n"
                 "  (correr DENTRO de WSL, con el daemon de OpenFang vivo)")
    _uuid = sys.argv[1]
    _sleep = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
    _binary = sys.argv[3] if len(sys.argv) > 3 else "/root/.openfang/bin/openfang"
    load_probe(_uuid, sleep=_sleep, binary=_binary)
