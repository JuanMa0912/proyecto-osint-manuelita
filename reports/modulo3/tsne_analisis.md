# Análisis t-SNE / UMAP **3D** — Espacio semántico y memoria del Agent OS (Módulo 3)

> **Bonus "picante" del enunciado (Ruta Transversal B).** Reducción dimensional
> (**t-SNE** y **UMAP**, en **2D y 3D**) + análisis de clústeres con **métricas
> duras** sobre el espacio semántico del agente `manuelita-bot` (OpenFang Agent OS)
> y su memoria real, extraída de la base de datos nativa `openfang.db`.
>
> Reproducible: `uv run python scripts/tsne_sesiones_m3.py`
> · Notebook interactivo: [`tsne_3d_manuelita.ipynb`](./tsne_3d_manuelita.ipynb)
> · Figura 3D estática: [`tsne_clusters_3d.png`](./tsne_clusters_3d.png)
> · Figura 3D interactiva (Plotly): [`tsne_3d.html`](./tsne_3d.html)
> · Figura 2D: [`tsne_clusters.png`](./tsne_clusters.png)
> · Sesiones/costos/memorias: [`tsne_sesiones.txt`](./tsne_sesiones.txt)
> · Script: [`scripts/tsne_sesiones_m3.py`](../../scripts/tsne_sesiones_m3.py)
> · Hechos etiquetados (verdad-de-terreno): [`scripts/tsne_probe_facts.py`](../../scripts/tsne_probe_facts.py)

---

## 1. Objetivo

Demostrar, sobre datos **reales** del Agent OS, y responder la pregunta del equipo:

1. Que la **memoria semántica de OpenFang** (capa 2 del modelo de 6 capas) almacena
   conocimiento como **vectores de embeddings** densos (768-dim).
2. **¿Esa memoria clusteriza por tema?** — medido sobre los embeddings **nativos**
   del OS con etiquetas de **verdad-de-terreno**, no sobre un proxy ni un heurístico.
3. Que el **historial de sesiones** y los **costos** del agente son extraíbles y
   analizables programáticamente desde `openfang.db`.

## 2. Metodología

El pipeline (`scripts/tsne_sesiones_m3.py`), todo local, sin gastar cuota del LLM:

1. **Extracción del `openfang.db`** (copia en `reports/modulo3/_work/`, snapshot con WAL):
   - `memories` → vectores nativos **768-dim** + contenido (capa semántica).
   - `sessions` → mensajes en **MessagePack**, decodificados a turnos user/assistant.
   - `usage_events` → tokens y costo por llamada.
2. **Espacio de conocimiento (Panel A):** los **20 hechos núcleo etiquetados**
   (`scripts/tsne_probe_facts.py`, 4 por tema × 5 temas — verdad-de-terreno) + el
   corpus Markdown desplegado (cap de 25 chunks/archivo; se excluyen índice meta y
   archivos vacíos, igual que el deploy). Embeddings con
   `paraphrase-multilingual-MiniLM-L12-v2` (384-dim, multilingüe).
3. **Memoria real (Panel B):** los vectores nativos 768-dim. Cada memoria se
   **limpia** (`clean_memory_content`: quita el envoltorio episódico
   `User asked: … I responded: …`) y se etiqueta por **verdad-de-terreno**
   (`match_theme`: fuzzy-match contra los 20 hechos). Las memorias que no matchean
   (conversacionales) se pintan en gris y se **excluyen** de las métricas.
4. **Reducción:** **t-SNE** y **UMAP**, en **2D y 3D**. `random_state=42`,
   `perplexity`/`n_neighbors` clampados por nº de puntos (reproducible).
5. **Clustering + métricas duras:** **KMeans** sobre los **embeddings originales**, y
   se reportan **pureza**, **silhouette** y **ARI** (Adjusted Rand Index, KMeans vs
   tema verdad-de-terreno) para ambos espacios.

> **Dos espacios separados, NO mezclados.** Panel A vive en 384-dim (modelo local) y
> Panel B en 768-dim (nativo del OS). Por ser dimensiones distintas **nunca** se
> grafican juntos en un mismo t-SNE.

> **Nota de fidelidad del embebedor (verificado jun 2026):** los 768-dim del Panel B
> los genera el **embebedor local de OpenFang: `ollama / nomic-embed-text`** (768-dim),
> detectado automáticamente cuando NO hay `OPENAI_API_KEY` en el entorno. Con el alias
> `OPENAI_API_KEY` activo (necesario para los Hands built-in), OpenFang enruta los
> embeddings a `api.openai.com` → 401 → guarda **sin** vector. Por eso la carga de
> memoria para este análisis se hizo con el embebedor local (Ollama en `localhost:11434`).

## 3. Datos reales usados (verificados en `openfang.db`)

| Fuente | Valor |
|---|---|
| Vectores en memoria semántica (`memories`) | **21** vectores **768-dim** (20 etiquetables + 1 conversacional) |
| Ítems del espacio de conocimiento (corpus + 20 hechos) | **104** en 6 temas |
| Sesión real (`sessions`, MessagePack) | 1 sesión (decodificada a turnos) |
| Costo acumulado (`usage_events`) | **US$0,1855** en 21 llamadas (DB de esta sesión) |

## 4. Resultados

| Espacio | n | pureza KMeans | silhouette | ARI |
|---|---:|---:|---:|---:|
| **A) Conocimiento** (corpus + 20 hechos, 384-dim) | 104 | **58 %** | 0.091 | **+0.228** |
| **B) Memoria real del OS** (768-dim, etiquetada) | 20 | **65 %** | 0.090 | **+0.259** |

*(Baseline aleatorio para 5–6 clases ≈ 17 %; ARI aleatorio ≈ 0.)*

### Panel A — Espacio de conocimiento (104 ítems)

KMeans recupera los temas con **pureza 58 %** y **ARI +0.228**. **Redes/Comunicación**
(YouTube) forma un clúster **100 % puro** (15/15) y claramente separado; el resto
(Identidad, Sostenibilidad, Financiero) se solapa más.

### Panel B — Memoria semántica REAL del agente (20 vectores etiquetados, 768-dim)

**Respuesta a "¿la memoria clusteriza por tema?": sí, con señal moderada.** Pureza
**65 %**, **ARI +0.259** (positivo, por encima del azar). Desglose de clústeres:

| Clúster | n | Tema dominante | Aciertos |
|--------:|--:|---|--:|
| 1 | 4 | Financiero | 3/4 |
| 2 | 6 | Geografía/Operación | 3/6 |
| 3 | 5 | Productos/Producción | 3/5 |
| 4 | 4 | Sostenibilidad | 3/4 |
| 0 | 1 | Identidad/Corporativo | 1/1 |

Los embeddings nativos del OS **recuperan la estructura temática** del corpus
corporativo. Es una muestra pequeña (20 puntos), así que las métricas se leen como
**indicativas, no concluyentes** — pero el salto frente a la iteración previa
(con memoria contaminada y heurística, ARI **−0.032**) confirma que el método y la
limpieza importan.

## 5. Interpretación (hallazgos)

1. **El conocimiento corporativo NO está perfectamente siloado por tema.** La
   pureza/ARI moderados reflejan que un corpus **mono-dominio** comparte mucho
   vocabulario (la empresa, sus cifras y su sostenibilidad se narran con las mismas
   palabras). El contenido de **redes/YouTube** es el más distinto (clúster puro).
2. **La memoria nativa del OS sí preserva el tema.** Medido sobre los 768-dim reales
   (no un proxy), KMeans reagrupa Financiero, Geografía, Productos y Sostenibilidad
   con 3/4–3/6 de acierto por clúster. Evidencia de que la capa 2 de OpenFang es un
   espacio semántico real y analizable.
3. **Consecuencia de arquitectura.** Como los temas corporativos se solapan en el
   espacio de embeddings, la recuperación puramente semántica es ambigua entre temas
   cercanos; por eso `manuelita-bot` se apoya además en el **mapa explícito
   tema→archivo** del `system_prompt` y en los **DATOS NÚCLEO**. El t-SNE/UMAP da
   evidencia visual de por qué esa red de seguridad ayuda.

## 6. Honestidad y limitaciones

- **Muestra pequeña en el Panel B (20 puntos).** Las métricas son indicativas; no se
  presentan como un mapa estadísticamente robusto. La figura 3D y el ARI se leen
  como prueba de concepto del pipeline sobre datos vivos, con señal real positiva (ARI +0.259).
- **Etiquetas de verdad-de-terreno.** A diferencia de la versión previa (tema por
  archivo / heurístico de keywords), el tema de cada memoria del Panel B se deriva por
  fuzzy-match contra los 20 hechos cargados — etiqueta confiable, no circular.
- **Modelos de embeddings distintos por panel** (384-dim local en A; 768-dim nativo del
  OS en B). Se mantienen separados a propósito.
- **El historial de sesiones sigue siendo escaso** (1 sesión). El análisis rico corre
  sobre el espacio de conocimiento + la memoria real; las sesiones son evidencia del
  pipeline de extracción, no un dataset grande de conversaciones.

## 7. Dato verificado sobre OpenFang (embeddings)

La inspección del DB confirma embeddings de **768 dimensiones**
(`memories.embedding` = 3.072 bytes = 768 × float32), generados por el embebedor local
**`ollama / nomic-embed-text`**. El `[memory]` de `config.toml` no fija
`embedding_model`: OpenFang **auto-detecta** el driver (Ollama local si no hay
`OPENAI_API_KEY`; OpenAI si lo hay). Esto **corrige** una afirmación previa que decía
`all-MiniLM-L6-v2` (384-dim): ese **no** es el embebedor nativo del OS.
