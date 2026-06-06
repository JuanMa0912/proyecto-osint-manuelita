#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
t-SNE / análisis de clústeres del Módulo 3 (Ruta B — OpenFang Agent OS).
=========================================================================
Bonus "picante" del enunciado: reducción dimensional (t-SNE **y UMAP**, en **2D y
3D**) + análisis de clústeres con **métricas duras** sobre el espacio semántico del
agente `manuelita-bot` y su memoria/historial reales extraídos de `openfang.db`.

Dos vistas complementarias (cada una en su propio espacio de embeddings — NO se
mezclan, porque viven en dimensiones distintas):

  PANEL A — Mapa del ESPACIO DE CONOCIMIENTO del agente.
     Corpus Markdown desplegado (data/) + los 20 hechos núcleo etiquetados
     (verdad-de-terreno, ver `scripts/tsne_probe_facts.py`), re-embebidos
     localmente con un sentence-transformer multilingüe
     (paraphrase-multilingual-MiniLM-L12-v2, 384-dim — el mismo que el M2 usa en
     modo 'local', apropiado para español). Es la vista rica: muestra cómo el
     conocimiento se separa por tema. KMeans sobre los embeddings originales,
     color por tema declarado.

  PANEL B — Memoria semántica REAL del agente (datos vivos).
     Los vectores 768-dim que OpenFang guardó en la tabla `memories` de
     `openfang.db` (capa 2 del modelo de memoria de 6 capas). Cada memoria se
     LIMPIA (se quita el envoltorio episódico "User asked: ... I responded: ...")
     y se etiqueta por **verdad-de-terreno** con `match_theme()`. Las memorias que
     no matchean ningún hecho (conversacionales) se pintan gris y se EXCLUYEN del
     cálculo de pureza/silhouette/ARI (no son etiquetables).

NOTA DE FIDELIDAD: OpenFang almacena embeddings de 768 dimensiones (verificado
empíricamente en el DB). El `[memory]` de config.toml no fija `embedding_model`,
así que usa el default interno del OS (nombre no documentado públicamente). Para
el Panel A usamos un modelo local estándar y transparente; para el Panel B usamos
los vectores nativos del OS tal cual.

MÉTRICAS DURAS (consola + títulos/anotaciones de las figuras):
  - silhouette_score (sklearn) sobre los embeddings ORIGINALES, en ambos espacios.
  - adjusted_rand_score (ARI) entre las etiquetas KMeans y los temas
    verdad-de-terreno, en ambos espacios.
  - pureza global de clústeres (dominante por clúster), como antes.

Uso (Windows, en la raíz del repo):
    uv run python scripts/tsne_sesiones_m3.py
    uv run python scripts/tsne_sesiones_m3.py --db ruta/a/openfang.db

Salidas:
    reports/modulo3/tsne_clusters.png      (figura 2D, 2 paneles — compat. previa)
    reports/modulo3/tsne_clusters_3d.png   (figura 3D estática, fallback PDF)
    reports/modulo3/tsne_3d.html           (figura 3D interactiva Plotly — demo)
    reports/modulo3/tsne_sesiones.txt      (historial de sesión decodificado + costos)
"""
from __future__ import annotations
import argparse
import os
import struct
import sqlite3
import sys
import re
from collections import Counter

import numpy as np

# Verdad-de-terreno y utilidades de limpieza/etiquetado (fuente única).
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tsne_probe_facts import (  # noqa: E402
    PROBE_FACTS,
    clean_memory_content,
    match_theme,
)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DB = os.path.join(REPO, "reports", "modulo3", "_work", "openfang.db")
CORPUS_DIR = os.path.join(REPO, "data_processed", "markdown")
OUT_DIR = os.path.join(REPO, "reports", "modulo3")

SEED = 42  # reproducibilidad global

# Paleta de temas (coarse) usada para colorear y para etiquetar la verdad-de-terreno.
TEMA_COLOR = {
    "Identidad/Corporativo": "#1f77b4",
    "Geografía/Operación":   "#2ca02c",
    "Financiero":            "#d62728",
    "Sostenibilidad":        "#9467bd",
    "Productos/Producción":  "#ff7f0e",
    "Redes/Comunicación":    "#8c564b",
    "Índice/Meta":           "#7f7f7f",
    "Conversacional":        "#bbbbbb",  # memorias no etiquetables (gris)
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

# Los 20 hechos núcleo (verdad-de-terreno) provienen de tsne_probe_facts.PROBE_FACTS.
HECHOS = list(PROBE_FACTS)


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
    """Corpus + 20 hechos. Cap de chunks por archivo (muestreo uniforme) para
    que un solo documento (p. ej. YouTube) no inunde y desbalancee el espacio."""
    textos, temas, fuentes = [], [], []
    # 20 hechos núcleo (verdad-de-terreno)
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
# 3) Reducción dimensional — t-SNE y UMAP, en 2D y 3D, con clamping seguro
# ---------------------------------------------------------------------------
def _perplexity(n: int) -> float:
    """Perplexity de t-SNE clampada por n (debe ser < n; regla práctica n/3)."""
    return float(max(2, min(30, (n - 1) // 3)))


def _n_neighbors(n: int) -> int:
    """n_neighbors de UMAP clampado por n (debe ser < n; mínimo 2)."""
    return int(max(2, min(15, n - 1)))


def tsne_reducir(X: np.ndarray, n_components=2, seed=SEED):
    """t-SNE a 2D o 3D con perplexity clampada. Devuelve (coords, perplexity)."""
    from sklearn.manifold import TSNE
    n = X.shape[0]
    perp = _perplexity(n)
    ts = TSNE(n_components=n_components, perplexity=perp, init="pca",
              learning_rate="auto", random_state=seed)
    return ts.fit_transform(X), perp


def umap_reducir(X: np.ndarray, n_components=2, seed=SEED):
    """UMAP a 2D o 3D con n_neighbors clampado. Devuelve (coords, n_neighbors).

    Lanza ImportError con mensaje claro si `umap-learn` no está instalado.
    """
    try:
        import umap  # umap-learn
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "Falta 'umap-learn'. Instálalo con: uv add umap-learn plotly"
        ) from exc
    n = X.shape[0]
    nn = _n_neighbors(n)
    reducer = umap.UMAP(n_components=n_components, n_neighbors=nn,
                        min_dist=0.1, random_state=seed)
    return reducer.fit_transform(X), nn


# ---------------------------------------------------------------------------
# 4) Métricas duras
# ---------------------------------------------------------------------------
def metricas_duras(X: np.ndarray, labels_km, temas_gt):
    """silhouette (sobre X original) + ARI (KMeans vs verdad-de-terreno).

    Devuelve (silhouette, ari). Cualquiera puede ser None si no es calculable
    (p. ej. <2 clústeres efectivos, o menos puntos que clústeres).
    """
    from sklearn.metrics import silhouette_score, adjusted_rand_score
    sil = ari = None
    n = X.shape[0]
    n_labels = len(set(labels_km))
    # silhouette exige 2 <= n_labels <= n-1
    if n >= 3 and 2 <= n_labels <= n - 1:
        try:
            sil = float(silhouette_score(X, labels_km))
        except Exception:
            sil = None
    if temas_gt is not None and len(temas_gt) == n and n >= 2:
        try:
            ari = float(adjusted_rand_score(temas_gt, labels_km))
        except Exception:
            ari = None
    return sil, ari


def pureza_clusters(labels_km, temas_gt, k):
    """Pureza global (dominante por clúster) + filas de desglose."""
    aciertos = 0
    rows = []
    for c in range(k):
        idx = [i for i in range(len(temas_gt)) if labels_km[i] == c]
        if not idx:
            continue
        cnt = Counter(temas_gt[i] for i in idx)
        dom, dom_n = cnt.most_common(1)[0]
        aciertos += dom_n
        rows.append((c, len(idx), dom, dom_n))
    pureza = aciertos / len(temas_gt) if temas_gt else 0.0
    return pureza, rows


def _fmt_metric(v) -> str:
    return f"{v:.3f}" if isinstance(v, float) else "n/d"


# ---------------------------------------------------------------------------
# 5) main
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=DEFAULT_DB)
    args = ap.parse_args()

    os.makedirs(OUT_DIR, exist_ok=True)
    con = conectar(args.db)

    # --- datos reales del OS ---
    mem_content_raw, mem_vecs = leer_memorias_reales(con)
    sesiones = leer_sesiones(con)
    n_use, tin, tout, cost = leer_costos(con)
    con.close()

    # ===================================================================
    # PANEL A — espacio de conocimiento (corpus + 20 hechos), embeddings locales
    # ===================================================================
    print(">> Embebiendo corpus + hechos (paraphrase-multilingual-MiniLM-L12-v2, local)...")
    from sentence_transformers import SentenceTransformer
    modelo = SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
    textos, temas, fuentes = construir_conocimiento()
    X_know = np.asarray(modelo.encode(textos, show_progress_bar=False), dtype=np.float32)
    print(f"   {len(textos)} ítems de conocimiento embebidos -> {X_know.shape}")

    from sklearn.cluster import KMeans
    temas_unicos = sorted(set(temas))
    k = len(temas_unicos)
    km = KMeans(n_clusters=k, n_init=10, random_state=SEED).fit(X_know)

    pureza_A, cluster_rows = pureza_clusters(km.labels_, temas, k)
    sil_A, ari_A = metricas_duras(X_know, km.labels_, temas)

    # Reducciones del conocimiento (2D para compat + 3D para lo nuevo)
    know_tsne2, perp_k = tsne_reducir(X_know, n_components=2)
    know_tsne3, _ = tsne_reducir(X_know, n_components=3)
    try:
        know_umap3, nn_k = umap_reducir(X_know, n_components=3)
        umap_ok = True
    except ImportError as exc:
        print(f"   [aviso] {exc}")
        know_umap3, nn_k, umap_ok = np.zeros((len(textos), 3)), 0, False

    # ===================================================================
    # PANEL B — memoria real del OS: limpiar + etiquetar por verdad-de-terreno
    # ===================================================================
    mem_clean = [clean_memory_content(c) for c in mem_content_raw]
    temas_mem = []
    for c in mem_content_raw:
        t = match_theme(c)
        temas_mem.append(t if t is not None else "Conversacional")

    # Índices etiquetables (excluir "Conversacional" de métricas)
    idx_lab = [i for i, t in enumerate(temas_mem) if t != "Conversacional"]
    n_lab = len(idx_lab)
    n_conv = len(temas_mem) - n_lab
    print(f">> Memoria real: {mem_vecs.shape[0]} vectores | etiquetables={n_lab} | "
          f"conversacionales(gris)={n_conv}")

    # Métricas + reducciones del Panel B (solo si hay suficientes etiquetables)
    sil_B = ari_B = None
    pureza_B = None
    memB_tsne2 = memB_tsne3 = memB_umap3 = np.zeros((0, 3))
    temas_mem_lab = [temas_mem[i] for i in idx_lab]
    perp_m = nn_m = 0
    cluster_rows_B = []

    if n_lab >= 3:
        X_mem = mem_vecs[idx_lab]
        k_b = len(set(temas_mem_lab))
        k_b = max(2, min(k_b, n_lab - 1))  # KMeans exige 2 <= k <= n-1
        km_b = KMeans(n_clusters=k_b, n_init=10, random_state=SEED).fit(X_mem)
        pureza_B, cluster_rows_B = pureza_clusters(km_b.labels_, temas_mem_lab, k_b)
        sil_B, ari_B = metricas_duras(X_mem, km_b.labels_, temas_mem_lab)

        memB_tsne2, perp_m = tsne_reducir(X_mem, n_components=2)
        memB_tsne3, _ = tsne_reducir(X_mem, n_components=3)
        if umap_ok:
            try:
                memB_umap3, nn_m = umap_reducir(X_mem, n_components=3)
            except Exception as exc:  # UMAP con muy pocos puntos puede fallar
                print(f"   [aviso] UMAP Panel B no disponible: {exc}")
                memB_umap3 = np.zeros((n_lab, 3))
    else:
        print("   [aviso] <3 memorias etiquetables: Panel B sin métricas/3D robustos.")

    # Colores por punto del Panel B (todos los puntos, incluido gris)
    temas_mem_all = temas_mem
    # Subconjunto etiquetable para las proyecciones (las 3D se calcularon sobre idx_lab)
    temas_mem_proj = temas_mem_lab

    # ===================================================================
    # 6) FIGURA 2D (compatibilidad con el entregable previo)
    # ===================================================================
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(16, 7))
    axA = axes[0]
    for tema in temas_unicos:
        idx = [i for i, t in enumerate(temas) if t == tema]
        axA.scatter(know_tsne2[idx, 0], know_tsne2[idx, 1],
                    c=TEMA_COLOR.get(tema, "#333"), label=tema, s=45,
                    alpha=0.8, edgecolors="white", linewidths=0.4)
    axA.set_title(f"A) Espacio de conocimiento de manuelita-bot\n"
                  f"{len(textos)} ítems (corpus + {len(HECHOS)} hechos) · t-SNE perp={perp_k:.0f} · "
                  f"pureza {pureza_A:.0%} · silhouette {_fmt_metric(sil_A)} · ARI {_fmt_metric(ari_A)}",
                  fontsize=10)
    axA.legend(fontsize=8, loc="best", framealpha=0.9)
    axA.set_xticks([]); axA.set_yticks([])

    axB = axes[1]
    if memB_tsne2.shape[0]:
        for tema in sorted(set(temas_mem_proj)):
            idx = [i for i, t in enumerate(temas_mem_proj) if t == tema]
            axB.scatter(memB_tsne2[idx, 0], memB_tsne2[idx, 1],
                        c=TEMA_COLOR.get(tema, "#333"), label=tema, s=110,
                        alpha=0.85, edgecolors="black", linewidths=0.5)
        axB.set_title(f"B) Memoria semántica REAL del agente (openfang.db)\n"
                      f"{n_lab} etiquetadas / {mem_vecs.shape[0]} ({mem_vecs.shape[1]}-dim) · "
                      f"t-SNE perp={perp_m:.0f} · pureza {pureza_B:.0%} · "
                      f"silhouette {_fmt_metric(sil_B)} · ARI {_fmt_metric(ari_B)}", fontsize=10)
        axB.legend(fontsize=8, loc="best", framealpha=0.9)
    else:
        axB.text(0.5, 0.5, f"Memoria real: {mem_vecs.shape[0]} vectores, "
                 f"solo {n_lab} etiquetables\n(insuficiente para t-SNE/métricas)",
                 ha="center", va="center")
    axB.set_xticks([]); axB.set_yticks([])

    fig.suptitle("Módulo 3 — t-SNE del espacio semántico y la memoria del Agent OS (Manuelita S.A.)",
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out_png2d = os.path.join(OUT_DIR, "tsne_clusters.png")
    fig.savefig(out_png2d, dpi=150)
    plt.close(fig)
    print(f">> Figura 2D: {out_png2d}")

    # ===================================================================
    # 7) FIGURA 3D ESTÁTICA (matplotlib, fallback para el PDF)
    # ===================================================================
    from mpl_toolkits.mplot3d import Axes3D  # noqa: F401 (registra proj 3d)
    fig3 = plt.figure(figsize=(18, 8))

    def _scatter3d(ax, coords, temas_pt, size, vista):
        for tema in sorted(set(temas_pt)):
            idx = [i for i, t in enumerate(temas_pt) if t == tema]
            ax.scatter(coords[idx, 0], coords[idx, 1], coords[idx, 2],
                       c=TEMA_COLOR.get(tema, "#333"), label=tema, s=size,
                       alpha=0.85, edgecolors="white", linewidths=0.3)
        ax.view_init(elev=vista[0], azim=vista[1])
        ax.set_xticklabels([]); ax.set_yticklabels([]); ax.set_zticklabels([])

    # Panel A 3D (t-SNE) — dos ángulos
    axA1 = fig3.add_subplot(2, 2, 1, projection="3d")
    _scatter3d(axA1, know_tsne3, temas, 30, (22, 45))
    axA1.set_title(f"A) Conocimiento — t-SNE 3D (vista 1)\n"
                   f"pureza {pureza_A:.0%} · sil {_fmt_metric(sil_A)} · ARI {_fmt_metric(ari_A)}",
                   fontsize=9)
    axA1.legend(fontsize=6, loc="upper left")

    axA2 = fig3.add_subplot(2, 2, 2, projection="3d")
    src_A2 = know_umap3 if umap_ok else know_tsne3
    _scatter3d(axA2, src_A2, temas, 30, (18, 135))
    axA2.set_title(("A) Conocimiento — UMAP 3D" if umap_ok else "A) Conocimiento — t-SNE 3D (vista 2)")
                   + f"\n{len(textos)} ítems · {len(temas_unicos)} temas",
                   fontsize=9)

    # Panel B 3D — t-SNE y UMAP de la memoria real etiquetada
    axB1 = fig3.add_subplot(2, 2, 3, projection="3d")
    if memB_tsne3.shape[0] >= 3:
        _scatter3d(axB1, memB_tsne3, temas_mem_proj, 70, (22, 45))
        axB1.set_title(f"B) Memoria real — t-SNE 3D\n"
                       f"{n_lab} etiquetadas · sil {_fmt_metric(sil_B)} · ARI {_fmt_metric(ari_B)}",
                       fontsize=9)
        axB1.legend(fontsize=6, loc="upper left")
    else:
        axB1.text2D(0.5, 0.5, f"Memoria real insuficiente\n({n_lab} etiquetables)",
                    ha="center", transform=axB1.transAxes)

    axB2 = fig3.add_subplot(2, 2, 4, projection="3d")
    if umap_ok and memB_umap3.shape[0] >= 3:
        _scatter3d(axB2, memB_umap3, temas_mem_proj, 70, (18, 135))
        axB2.set_title(f"B) Memoria real — UMAP 3D\n{n_lab} etiquetadas (nn={nn_m})", fontsize=9)
    elif memB_tsne3.shape[0] >= 3:
        _scatter3d(axB2, memB_tsne3, temas_mem_proj, 70, (35, 200))
        axB2.set_title("B) Memoria real — t-SNE 3D (vista 2)", fontsize=9)
    else:
        axB2.text2D(0.5, 0.5, "UMAP/t-SNE Panel B no disponible",
                    ha="center", transform=axB2.transAxes)

    fig3.suptitle("Módulo 3 — Proyección 3D del espacio semántico y la memoria real "
                  "del Agent OS (Manuelita S.A.)", fontsize=13, fontweight="bold")
    fig3.tight_layout(rect=[0, 0, 1, 0.95])
    out_png3d = os.path.join(OUT_DIR, "tsne_clusters_3d.png")
    fig3.savefig(out_png3d, dpi=150)
    plt.close(fig3)
    print(f">> Figura 3D estática: {out_png3d}")

    # ===================================================================
    # 8) FIGURA 3D INTERACTIVA (Plotly) — la vistosa para la demo
    # ===================================================================
    try:
        out_html = _figura_plotly_3d(
            know_tsne3, know_umap3, umap_ok, textos, temas,
            memB_tsne3, memB_umap3, temas_mem_proj, mem_clean, idx_lab,
            pureza_A, sil_A, ari_A, pureza_B, sil_B, ari_B,
        )
        print(f">> Figura 3D interactiva: {out_html}")
    except ImportError as exc:
        print(f"   [aviso] Plotly no disponible ({exc}); omito tsne_3d.html. "
              f"Instálalo con: uv add plotly")

    # ===================================================================
    # 9) Métricas en consola
    # ===================================================================
    print("\n=== PANEL A — Conocimiento (corpus + hechos) ===")
    for c, n_c, dom, dom_n in cluster_rows:
        print(f"  Clúster {c}: n={n_c:3d} | dominante={dom:<22} ({dom_n}/{n_c})")
    print(f"  Pureza global : {pureza_A:.0%}")
    print(f"  silhouette    : {_fmt_metric(sil_A)}  (embeddings 384-dim originales)")
    print(f"  ARI (KMeans vs tema): {_fmt_metric(ari_A)}")

    print("\n=== PANEL B — Memoria real etiquetada (verdad-de-terreno) ===")
    print(f"  Memorias totales={mem_vecs.shape[0]} | etiquetables={n_lab} | conversacionales={n_conv}")
    if n_lab >= 3:
        for c, n_c, dom, dom_n in cluster_rows_B:
            print(f"  Clúster {c}: n={n_c:3d} | dominante={dom:<22} ({dom_n}/{n_c})")
        print(f"  Pureza global : {pureza_B:.0%}")
        print(f"  silhouette    : {_fmt_metric(sil_B)}  (vectores nativos {mem_vecs.shape[1]}-dim)")
        print(f"  ARI (KMeans vs tema): {_fmt_metric(ari_B)}")
        print("  NOTA: con pocos puntos estas métricas son inestables; léelas como "
              "indicativas, no concluyentes.")
    else:
        print("  Insuficientes memorias etiquetables (<3) para métricas/3D del Panel B.")

    # ===================================================================
    # 10) Artefacto: historial de sesión + costos
    # ===================================================================
    out_txt = os.path.join(OUT_DIR, "tsne_sesiones.txt")
    with open(out_txt, "w", encoding="utf-8") as fh:
        fh.write("HISTORIAL DE SESIONES REALES (decodificado de openfang.db / MessagePack)\n")
        fh.write("=" * 70 + "\n")
        for agent_id, created, turns in sesiones:
            fh.write(f"\nSesión agente={agent_id} creada={created} ({len(turns)} turnos)\n")
            for role, content in turns:
                fh.write(f"  [{role}] {content[:140].strip()}\n")
        fh.write("\n\nMEMORIAS (content limpio + tema verdad-de-terreno)\n" + "=" * 70 + "\n")
        for raw, limpio, tema in zip(mem_content_raw, mem_clean, temas_mem):
            fh.write(f"  [{tema}] {limpio[:120].strip()}\n")
        fh.write("\n\nCOSTOS (usage_events)\n" + "=" * 70 + "\n")
        fh.write(f"  llamadas={n_use} | input_tokens={tin:.0f} | output_tokens={tout:.0f} | "
                 f"costo_estimado_usd={cost:.4f}\n")
    print(f">> Historial + costos + memorias: {out_txt}")

    # ===================================================================
    # 11) Resumen
    # ===================================================================
    print("\n=== RESUMEN ===")
    print(f"  Conocimiento : {len(textos)} ítems en {k} temas | pureza {pureza_A:.0%} | "
          f"sil {_fmt_metric(sil_A)} | ARI {_fmt_metric(ari_A)}")
    print(f"  Memoria real : {mem_vecs.shape[0]} vectores "
          f"{mem_vecs.shape[1] if mem_vecs.shape[0] else 0}-dim "
          f"({n_lab} etiquetables) | sil {_fmt_metric(sil_B)} | ARI {_fmt_metric(ari_B)}")
    print(f"  Sesiones reales: {len(sesiones)} | Costo acumulado: ${cost:.4f} ({n_use} llamadas)")


# ---------------------------------------------------------------------------
# Plotly 3D — figura interactiva con botones t-SNE/UMAP × Panel A/B
# ---------------------------------------------------------------------------
def _figura_plotly_3d(know_tsne3, know_umap3, umap_ok, textos, temas,
                      memB_tsne3, memB_umap3, temas_mem_proj, mem_clean, idx_lab,
                      pureza_A, sil_A, ari_A, pureza_B, sil_B, ari_B):
    """Construye `tsne_3d.html` con 4 'capas' de trazas (t-SNE/UMAP × A/B) y un
    menú de botones para alternarlas. Color por tema; hover con texto truncado.

    Devuelve la ruta del HTML. Lanza ImportError si Plotly no está instalado.
    """
    import plotly.graph_objects as go  # ImportError si falta plotly

    def _trazas(coords, temas_pt, textos_pt, size, visible):
        trs = []
        for tema in sorted(set(temas_pt)):
            idx = [i for i, t in enumerate(temas_pt) if t == tema]
            if not idx:
                continue
            trs.append(go.Scatter3d(
                x=coords[idx, 0], y=coords[idx, 1], z=coords[idx, 2],
                mode="markers", name=tema,
                marker=dict(size=size, color=TEMA_COLOR.get(tema, "#333"),
                            opacity=0.85, line=dict(width=0.5, color="white")),
                text=[textos_pt[i][:110] for i in idx],
                hovertemplate="<b>%{text}</b><br>tema=" + tema + "<extra></extra>",
                visible=visible,
            ))
        return trs

    # Textos de hover de la memoria (content limpio, alineado a idx_lab)
    mem_textos = [mem_clean[i] for i in idx_lab]

    fuente_A_umap = know_umap3 if umap_ok else know_tsne3

    grupos = []  # (titulo_capa, lista_de_trazas)
    grupos.append(("A · t-SNE 3D", _trazas(know_tsne3, temas, textos, 4, True)))
    grupos.append(("A · UMAP 3D",  _trazas(fuente_A_umap, temas, textos, 4, False)))
    if memB_tsne3.shape[0] >= 1:
        grupos.append(("B · t-SNE 3D", _trazas(memB_tsne3, temas_mem_proj, mem_textos, 8, False)))
        src_B = memB_umap3 if (umap_ok and memB_umap3.shape[0] >= 1) else memB_tsne3
        grupos.append(("B · UMAP 3D", _trazas(src_B, temas_mem_proj, mem_textos, 8, False)))

    fig = go.Figure()
    rangos = []  # (inicio, fin) de trazas por grupo
    for _, trs in grupos:
        ini = len(fig.data)
        for t in trs:
            fig.add_trace(t)
        rangos.append((ini, len(fig.data)))

    total = len(fig.data)
    botones = []
    titulos_metricas = {
        "A · t-SNE 3D": f"Panel A (conocimiento) · t-SNE 3D · pureza {pureza_A:.0%} · "
                        f"sil {_fmt_metric(sil_A)} · ARI {_fmt_metric(ari_A)}",
        "A · UMAP 3D":  f"Panel A (conocimiento) · UMAP 3D · pureza {pureza_A:.0%} · "
                        f"sil {_fmt_metric(sil_A)} · ARI {_fmt_metric(ari_A)}",
        "B · t-SNE 3D": f"Panel B (memoria real OS) · t-SNE 3D · pureza "
                        f"{(pureza_B if pureza_B is not None else float('nan')):.0%} · "
                        f"sil {_fmt_metric(sil_B)} · ARI {_fmt_metric(ari_B)}",
        "B · UMAP 3D":  f"Panel B (memoria real OS) · UMAP 3D · sil {_fmt_metric(sil_B)} · "
                        f"ARI {_fmt_metric(ari_B)}",
    }
    for gi, (titulo, _) in enumerate(grupos):
        vis = [False] * total
        ini, fin = rangos[gi]
        for j in range(ini, fin):
            vis[j] = True
        botones.append(dict(
            label=titulo, method="update",
            args=[{"visible": vis},
                  {"title": titulos_metricas.get(titulo, titulo)}],
        ))

    fig.update_layout(
        title=titulos_metricas[grupos[0][0]],
        updatemenus=[dict(type="buttons", direction="right", x=0.5, xanchor="center",
                          y=1.12, yanchor="top", showactive=True, buttons=botones)],
        scene=dict(xaxis_title="dim 1", yaxis_title="dim 2", zaxis_title="dim 3"),
        legend=dict(title="Tema"),
        margin=dict(l=0, r=0, t=80, b=0),
    )
    out_html = os.path.join(OUT_DIR, "tsne_3d.html")
    fig.write_html(out_html, include_plotlyjs="cdn")
    return out_html


if __name__ == "__main__":
    main()
