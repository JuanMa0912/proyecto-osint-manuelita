#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
t-SNE / análisis de clústeres del Módulo 3 (Ruta B — OpenFang Agent OS).
=========================================================================
Bonus "picante" del enunciado: reducción dimensional (t-SNE) + análisis de
clústeres sobre el espacio semántico del agente `manuelita-bot` y su historial
de sesiones reales extraído de `openfang.db`.

Dos vistas complementarias (cada una en su propio espacio de embeddings — NO se
mezclan, porque viven en dimensiones distintas):

  PANEL A — Mapa del ESPACIO DE CONOCIMIENTO del agente.
     Corpus Markdown desplegado (data/) + los 12 hechos núcleo de la memoria,
     re-embebidos localmente con un sentence-transformer multilingüe
     (paraphrase-multilingual-MiniLM-L12-v2, 384-dim — el mismo que el M2 usa en
     modo 'local', apropiado para español). Es la vista rica: muestra cómo el
     conocimiento se separa por tema. KMeans sobre los embeddings originales,
     color por tema declarado.

  PANEL B — Memoria semántica REAL del agente (datos vivos).
     Los vectores 768-dim que OpenFang guardó en la tabla `memories` de
     `openfang.db` (capa 2 del modelo de memoria de 6 capas). Prueba de que el
     análisis corre sobre el estado real del Agent OS, no sobre datos sintéticos.

NOTA DE FIDELIDAD: OpenFang almacena embeddings de 768 dimensiones (verificado
empíricamente en el DB). El `[memory]` de config.toml no fija `embedding_model`,
así que usa el default interno del OS (nombre no documentado públicamente). Para
el Panel A usamos un modelo local estándar y transparente; para el Panel B usamos
los vectores nativos del OS tal cual.

Uso (Windows, en la raíz del repo):
    uv run python scripts/tsne_sesiones_m3.py
    uv run python scripts/tsne_sesiones_m3.py --db ruta/a/openfang.db

Salidas:
    reports/modulo3/tsne_clusters.png      (figura, 2 paneles)
    reports/modulo3/tsne_sesiones.txt      (historial de sesión decodificado + costos)
"""
from __future__ import annotations
import argparse
import os
import struct
import sqlite3
import sys
import re

import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(REPO, "reports", "modulo3", "_work", "openfang.db")
CORPUS_DIR = os.path.join(REPO, "data_processed", "markdown")
OUT_DIR = os.path.join(REPO, "reports", "modulo3")

# Paleta de temas (coarse) usada para colorear y para etiquetar la verdad-de-terreno.
TEMA_COLOR = {
    "Identidad/Corporativo": "#1f77b4",
    "Geografía/Operación":   "#2ca02c",
    "Financiero":            "#d62728",
    "Sostenibilidad":        "#9467bd",
    "Productos/Producción":  "#ff7f0e",
    "Redes/Comunicación":    "#8c564b",
    "Índice/Meta":           "#7f7f7f",
}

# Mapa archivo de corpus -> tema coarse.
ARCHIVO_TEMA = {
    "key_facts_manuelita.md":                 "Identidad/Corporativo",
    "oficial_perfil_manuelit.md":             "Productos/Producción",
    "oficial_pdf_sostenibilidad_manuelit.md": "Sostenibilidad",
    "oficial_doc_manuelit.md":                "Sostenibilidad",
    "financiero_supersociedades_manuelit.md": "Financiero",
    "red_social_youtube_manuelit.md":         "Redes/Comunicación",
    "_INDICE_MAESTRO.md":                     "Índice/Meta",
}

# Los 12 hechos núcleo (idénticos a 04-cargar-memoria-semantica.sh) con su tema.
HECHOS = [
    ("Manuelita S.A. tiene NIT 891.300.241, fundada en 1864, sede en Palmira, Valle del Cauca, Colombia.", "Identidad/Corporativo"),
    ("El presidente de Manuelita S.A. es Harold Eder.", "Identidad/Corporativo"),
    ("Manuelita opera en 3 países: Colombia, Perú y Chile.", "Geografía/Operación"),
    ("Manuelita exporta y vende sus productos a 49 países.", "Geografía/Operación"),
    ("Manuelita tiene 4 plataformas: azúcar de caña, palma de aceite, acuicultura, y frutas y hortalizas.", "Productos/Producción"),
    ("Manuelita tiene 7 unidades de negocio: Azúcar y Energía, Laredo, Aceites y Energía, Palmar de Altamira, Acuicultura, Océanos, Frutas y Hortalizas.", "Productos/Producción"),
    ("Manuelita tiene aproximadamente 7.971 colaboradores.", "Identidad/Corporativo"),
    ("En 2023 Manuelita tuvo ingresos de 1.043.562 millones COP, EBITDA 369.380 millones (margen 35,4%), utilidad neta 78.153 millones.", "Financiero"),
    ("Metas: reducir 70% emisiones Alcances 1 y 2 a 2030, y neutralidad de carbono a 2040.", "Sostenibilidad"),
    ("Manuelita produce ~487.000 toneladas de azúcar al año y ~275 millones de litros de bioetanol al año.", "Productos/Producción"),
    ("Manuelita beneficia a más de 4.000 familias de empleados y comunidades vecinas.", "Sostenibilidad"),
    ("Manuelita tiene certificaciones RSPO, HACCP, ASC y GRI; su actividad CIIU C1071 es elaboración y refinación de azúcar.", "Sostenibilidad"),
]


# ---------------------------------------------------------------------------
# 1) Lectura del DB de OpenFang
# ---------------------------------------------------------------------------
def conectar(db_path: str) -> sqlite3.Connection:
    if not os.path.exists(db_path):
        sys.exit(f"ERROR: no existe el DB {db_path}. Copia openfang.db (+ -wal/-shm) ahí.")
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA wal_checkpoint(FULL)")
    except sqlite3.Error:
        pass
    return con


def leer_memorias_reales(con: sqlite3.Connection):
    """Vectores 768-dim nativos + su contenido, desde la tabla `memories`."""
    contents, vecs = [], []
    for row in con.execute(
        "SELECT content, embedding FROM memories WHERE embedding IS NOT NULL AND deleted=0"
    ):
        blob = row["embedding"]
        n = len(blob) // 4
        vecs.append(np.array(struct.unpack(f"<{n}f", blob), dtype=np.float32))
        contents.append(row["content"])
    if not vecs:
        return [], np.zeros((0, 0))
    return contents, np.vstack(vecs)


def leer_sesiones(con: sqlite3.Connection):
    """Decodifica los mensajes (MessagePack) de las sesiones con contenido."""
    import msgpack
    out = []
    for row in con.execute(
        "SELECT agent_id, messages, created_at FROM sessions WHERE LENGTH(messages) > 5"
    ):
        try:
            msgs = msgpack.unpackb(row["messages"], raw=False)
        except Exception:
            continue
        turns = [(m.get("role"), str(m.get("content", "")))
                 for m in msgs if isinstance(m, dict)]
        if turns:
            out.append((row["agent_id"], row["created_at"], turns))
    return out


def leer_costos(con: sqlite3.Connection):
    tot_in = tot_out = 0.0
    cost = 0.0
    n = 0
    for row in con.execute(
        "SELECT input_tokens, output_tokens, cost_usd FROM usage_events"
    ):
        tot_in += float(row["input_tokens"] or 0)
        tot_out += float(row["output_tokens"] or 0)
        cost += float(row["cost_usd"] or 0)
        n += 1
    return n, tot_in, tot_out, cost


# ---------------------------------------------------------------------------
# 2) Construcción del dataset de conocimiento (corpus + hechos)
# ---------------------------------------------------------------------------
def quitar_frontmatter(texto: str) -> str:
    if texto.startswith("---"):
        partes = texto.split("---", 2)
        if len(partes) == 3:
            return partes[2]
    return texto


def chunkear(texto: str, min_palabras=8):
    """Chunking simple por párrafos; descarta líneas de tabla/separadores."""
    texto = quitar_frontmatter(texto)
    chunks = []
    for parrafo in re.split(r"\n\s*\n", texto):
        linea = " ".join(l.strip() for l in parrafo.splitlines()
                         if not l.strip().startswith(("|", "---", ">")) and "---" not in l)
        linea = re.sub(r"[#*`]", "", linea).strip()
        if len(linea.split()) >= min_palabras:
            # Trocear párrafos muy largos en ~60 palabras
            palabras = linea.split()
            for i in range(0, len(palabras), 60):
                trozo = " ".join(palabras[i:i + 60])
                if len(trozo.split()) >= min_palabras:
                    chunks.append(trozo)
    return chunks


def construir_conocimiento(cap_por_archivo=25):
    """Corpus + 12 hechos. Cap de chunks por archivo (muestreo uniforme) para
    que un solo documento (p. ej. YouTube) no inunde y desbalancee el espacio."""
    textos, temas, fuentes = [], [], []
    # 12 hechos núcleo
    for hecho, tema in HECHOS:
        textos.append(hecho); temas.append(tema); fuentes.append("hecho_nucleo")
    # corpus desplegado (excluye el índice meta y archivos vacíos)
    for fn in sorted(os.listdir(CORPUS_DIR)):
        if not fn.endswith(".md"):
            continue
        ruta = os.path.join(CORPUS_DIR, fn)
        with open(ruta, encoding="utf-8") as fh:
            contenido = fh.read()
        if re.search(r"^word_count:\s*0$", contenido, re.M):
            continue  # OSINT vacío (LinkedIn) — mismo criterio que el deploy
        tema = ARCHIVO_TEMA.get(fn, "Índice/Meta")
        if tema == "Índice/Meta":
            continue  # el índice maestro es meta, no conocimiento de dominio
        chunks = chunkear(contenido)
        if len(chunks) > cap_por_archivo:  # muestreo uniforme
            idx = np.linspace(0, len(chunks) - 1, cap_por_archivo).astype(int)
            chunks = [chunks[i] for i in idx]
        for ch in chunks:
            textos.append(ch); temas.append(tema); fuentes.append(fn)
    return textos, temas, fuentes


# ---------------------------------------------------------------------------
# 3) t-SNE + KMeans + figura
# ---------------------------------------------------------------------------
def tsne_2d(X: np.ndarray, seed=42):
    from sklearn.manifold import TSNE
    n = X.shape[0]
    perp = max(2, min(15, (n - 1) // 3))
    ts = TSNE(n_components=2, perplexity=perp, init="pca",
              learning_rate="auto", random_state=seed)
    return ts.fit_transform(X), perp


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    con = conectar(args.db)

    # --- datos reales del OS ---
    mem_content, mem_vecs = leer_memorias_reales(con)
    sesiones = leer_sesiones(con)
    n_use, tin, tout, cost = leer_costos(con)
    con.close()

    # --- dataset de conocimiento + embeddings locales ---
    #   Modelo MULTILINGÜE (mismo que el M2 usa en modo 'local') — apropiado para
    #   corpus en español, a diferencia de all-MiniLM-L6-v2 (centrado en inglés).
    print(">> Embebiendo corpus + hechos (paraphrase-multilingual-MiniLM-L12-v2, local)...")
    from sentence_transformers import SentenceTransformer
    modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    textos, temas, fuentes = construir_conocimiento()
    X_know = np.asarray(modelo.encode(textos, show_progress_bar=False), dtype=np.float32)
    print(f"   {len(textos)} ítems de conocimiento embebidos -> {X_know.shape}")

    # --- t-SNE de ambos espacios ---
    emb_know, perp_k = tsne_2d(X_know)
    from sklearn.cluster import KMeans
    temas_unicos = sorted(set(temas))
    k = len(temas_unicos)
    # KMeans sobre los embeddings ORIGINALES (no sobre las coords 2D de t-SNE:
    # las distancias de t-SNE no son globalmente fiables para clustering).
    km = KMeans(n_clusters=k, n_init=10, random_state=42).fit(X_know)

    # Pureza de clústeres (dominante por clúster) — se calcula antes para el título.
    from collections import Counter
    aciertos = 0
    cluster_rows = []
    for c in range(k):
        idx = [i for i in range(len(temas)) if km.labels_[i] == c]
        if not idx:
            continue
        cnt = Counter(temas[i] for i in idx)
        dom, dom_n = cnt.most_common(1)[0]
        aciertos += dom_n
        cluster_rows.append((c, len(idx), dom, dom_n))
    pureza = aciertos / len(temas)

    if mem_vecs.shape[0] >= 3:
        emb_mem, perp_m = tsne_2d(mem_vecs)
    else:
        emb_mem, perp_m = np.zeros((0, 2)), 0

    # Tema de cada memoria real (por similitud de su contenido a los hechos)
    def tema_de_memoria(texto: str) -> str:
        t = texto.lower()
        if any(w in t for w in ("ingreso", "ebitda", "utilidad", "financ")):
            return "Financiero"
        if any(w in t for w in ("emision", "carbono", "rspo", "famil", "comunidad", "sosteni", "neutralidad")):
            return "Sostenibilidad"
        if any(w in t for w in ("país", "pais", "exporta", "colombia", "peru", "chile")):
            return "Geografía/Operación"
        if any(w in t for w in ("azúcar", "azucar", "bioetanol", "plataforma", "unidad", "tonelada")):
            return "Productos/Producción"
        return "Identidad/Corporativo"

    temas_mem = [tema_de_memoria(c) for c in mem_content]

    # --- figura ---
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(16, 7))

    # Panel A
    axA = axes[0]
    for tema in temas_unicos:
        idx = [i for i, t in enumerate(temas) if t == tema]
        axA.scatter(emb_know[idx, 0], emb_know[idx, 1],
                    c=TEMA_COLOR.get(tema, "#333"), label=tema, s=45,
                    alpha=0.8, edgecolors="white", linewidths=0.4)
    axA.set_title(f"A) Espacio de conocimiento de manuelita-bot\n"
                  f"{len(textos)} ítems (corpus + 12 hechos) · t-SNE perp={perp_k} · "
                  f"color = tema · pureza KMeans {pureza:.0%}",
                  fontsize=11)
    axA.legend(fontsize=8, loc="best", framealpha=0.9)
    axA.set_xticks([]); axA.set_yticks([])

    # Panel B
    axB = axes[1]
    if emb_mem.shape[0]:
        for tema in sorted(set(temas_mem)):
            idx = [i for i, t in enumerate(temas_mem) if t == tema]
            axB.scatter(emb_mem[idx, 0], emb_mem[idx, 1],
                        c=TEMA_COLOR.get(tema, "#333"), label=tema, s=110,
                        alpha=0.85, edgecolors="black", linewidths=0.5)
        axB.set_title(f"B) Memoria semántica REAL del agente (openfang.db)\n"
                      f"{emb_mem.shape[0]} vectores nativos {mem_vecs.shape[1]}-dim · "
                      f"t-SNE perp={perp_m} · datos vivos del OS", fontsize=11)
        axB.legend(fontsize=8, loc="best", framealpha=0.9)
    else:
        axB.text(0.5, 0.5, "Sin suficientes memorias en el DB", ha="center")
    axB.set_xticks([]); axB.set_yticks([])

    fig.suptitle("Módulo 3 — t-SNE del espacio semántico y la memoria del Agent OS (Manuelita S.A.)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_png = os.path.join(OUT_DIR, "tsne_clusters.png")
    fig.savefig(out_png, dpi=150)
    print(f">> Figura: {out_png}")

    # --- pureza de clústeres (KMeans vs tema declarado) en Panel A ---
    print("\n=== Pureza de clústeres KMeans (Panel A) ===")
    for c, n_c, dom, dom_n in cluster_rows:
        print(f"  Clúster {c}: n={n_c:3d} | dominante={dom:<22} ({dom_n}/{n_c})")
    print(f"  -> Pureza global: {pureza:.0%}")

    # --- artefacto: historial de sesión + costos ---
    out_txt = os.path.join(OUT_DIR, "tsne_sesiones.txt")
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("HISTORIAL DE SESIONES REALES (decodificado de openfang.db / MessagePack)\n")
        fh.write("=" * 70 + "\n")
        for agent_id, created, turns in sesiones:
            fh.write(f"\nSesión agente={agent_id} creada={created} ({len(turns)} turnos)\n")
            for role, content in turns:
                fh.write(f"  [{role}] {content[:140].strip()}\n")
        fh.write("\n\nCOSTOS (usage_events)\n" + "=" * 70 + "\n")
        fh.write(f"  llamadas={n_use} | input_tokens={tin:.0f} | output_tokens={tout:.0f} | "
                 f"costo_estimado_usd={cost:.4f}\n")
    print(f">> Historial + costos: {out_txt}")

    print("\n=== RESUMEN ===")
    print(f"  Conocimiento: {len(textos)} ítems en {k} temas | pureza KMeans {pureza:.0%}")
    print(f"  Memoria real: {emb_mem.shape[0]} vectores {mem_vecs.shape[1] if mem_vecs.shape[0] else 0}-dim")
    print(f"  Sesiones reales: {len(sesiones)} | Costo acumulado: ${cost:.4f} ({n_use} llamadas)")


if __name__ == "__main__":
    main()
