# Análisis t-SNE — Espacio semántico y memoria del Agent OS (Módulo 3)

> **Bonus "picante" del enunciado (Ruta Transversal B).** Reducción dimensional
> (t-SNE) + análisis de clústeres sobre el espacio semántico del agente
> `manuelita-bot` y su historial de sesiones reales, extraído de la base de datos
> nativa de OpenFang (`openfang.db`). Reproducible con:
> `uv run python scripts/tsne_sesiones_m3.py`.
>
> Figura: [`tsne_clusters.png`](./tsne_clusters.png) · Artefacto de sesiones/costos:
> [`tsne_sesiones.txt`](./tsne_sesiones.txt) · Script: [`scripts/tsne_sesiones_m3.py`](../../scripts/tsne_sesiones_m3.py)

---

## 1. Objetivo

Demostrar, sobre datos **reales** del Agent OS, dos cosas:

1. Que la **memoria semántica de OpenFang** (capa 2 del modelo de 6 capas) almacena
   conocimiento como **vectores de embeddings** y que ese espacio tiene **estructura
   temática** recuperable con reducción dimensional.
2. Que el **historial de sesiones** del agente es extraíble y analizable
   programáticamente desde `openfang.db`.

## 2. Metodología

El pipeline (`scripts/tsne_sesiones_m3.py`) hace, sin gastar cuota del LLM (todo local):

1. **Extracción del DB de OpenFang** (`reports/modulo3/_work/openfang.db`, copia con WAL):
   - Tabla `memories` → vectores nativos **768-dim** + su contenido (capa semántica).
   - Tabla `sessions` → mensajes en **MessagePack**, decodificados a turnos user/assistant.
   - Tabla `usage_events` → tokens y costo por llamada.
2. **Construcción del espacio de conocimiento**: los 12 hechos núcleo de la memoria + el
   corpus Markdown desplegado en `data/` (con *cap* de 25 chunks por archivo para que un
   solo documento no inunde el espacio; se excluyen el índice meta y los archivos vacíos,
   igual que el deploy).
3. **Embeddings**: `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`
   (384-dim, multilingüe — el mismo modelo que el M2 usa en modo `local`, apropiado para
   español, a diferencia del `all-MiniLM-L6-v2` centrado en inglés).
4. **Reducción**: **t-SNE** a 2D (`perplexity=15` para el conocimiento; `=4` para la
   memoria real, por su tamaño). `init="pca"`, `random_state=42` (reproducible).
5. **Clustering**: **KMeans** (k = nº de temas) sobre los **embeddings originales**
   (no sobre las coordenadas 2D de t-SNE, cuyas distancias no son globalmente fiables).

> **Dos espacios separados, NO mezclados.** El Panel A vive en el espacio del modelo
> multilingüe (384-dim) y el Panel B en el espacio nativo de OpenFang (768-dim). Como son
> dimensiones distintas, **nunca** se grafican juntos en un mismo t-SNE.

## 3. Datos reales usados (verificados en `openfang.db`)

| Fuente | Valor |
|---|---|
| Vectores en memoria semántica (`memories`) | **14** vectores **768-dim** (capa 2) |
| Sesión real (`sessions`, MessagePack) | 1 sesión, **28 turnos** user/assistant |
| Ítems del espacio de conocimiento (corpus + hechos) | **96** en 6 temas |
| Costo acumulado (`usage_events`) | **US$0,1073** en 14 llamadas (input 106.103 / output 408 tokens) |

El historial decodificado (ver `tsne_sesiones.txt`) incluye la carga de los 12 hechos a
memoria y dos consultas de verificación, entre ellas la prueba de **alcance financiero**
(*"¿Cuánto facturó Manuelita en 2022? ¿individual o consolidada?"*), que el bot respondió
sin alucinar y distinguiendo individual vs. consolidado del Grupo.

## 4. Resultados

### Panel A — Espacio de conocimiento (96 ítems, color = tema)

KMeans recupera los temas con **pureza global del 60 %** (vs. ~17 % de un baseline
aleatorio para 6 clases). Desglose:

| Clúster | n | Tema dominante | Pureza |
|--------:|--:|---|--:|
| 0 | 18 | **Redes/Comunicación** | **18/18 (100 %)** |
| 1 | 27 | Identidad/Corporativo | 14/27 |
| 2 | 14 | Sostenibilidad | 8/14 |
| 3 | 14 | Sostenibilidad | 7/14 |
| 4 | 16 | Sostenibilidad | 8/16 |
| 5 | 7 | Redes/Comunicación | 3/7 |

Visualmente (t-SNE), **Redes/Comunicación** (YouTube) ocupa una región **claramente
separada** (arriba-izquierda); **Identidad/Corporativo** se concentra a la derecha y
**Sostenibilidad** abajo. **Financiero** y **Productos/Producción** quedan más dispersos.

### Panel B — Memoria semántica real del agente (14 vectores 768-dim)

Los vectores nativos extraídos de `openfang.db` se separan por tema en el plano t-SNE,
confirmando que OpenFang **sí** almacena embeddings densos y que su capa semántica es
analizable. Es una muestra pequeña (14 puntos: pre-sustentación el agente ha tenido poco
tráfico real), por lo que se lee como prueba de concepto del pipeline, no como un mapa
estadísticamente robusto.

## 5. Interpretación (hallazgos)

1. **El conocimiento NO está perfectamente "siloado" por tema.** La pureza del 60 % y el
   solapamiento de Sostenibilidad/Identidad/Financiero reflejan que un corpus corporativo
   **mono-dominio** comparte mucho vocabulario (la empresa, sus cifras y su sostenibilidad
   se narran con las mismas palabras). El contenido de **redes sociales/YouTube** es el más
   distinto (clúster puro), por su lenguaje y formato propios.
2. **Esto explica una decisión de arquitectura del M3.** Como los temas se solapan en el
   espacio de embeddings, la recuperación puramente semántica es ambigua entre temas
   corporativos cercanos; por eso el agente se apoya en el **mapa explícito tema→archivo**
   del `system_prompt` para desambiguar qué `data/*.md` leer. El t-SNE da evidencia visual
   de por qué ese mapa ayuda (la separación semántica sola no basta).
3. **La memoria episódica de OpenFang guarda el contexto de la interacción**, no solo el
   hecho limpio: los `content` de `memories` son del tipo *"User asked: Usa memory_store…:
   <hecho>"*. Útil saberlo para futuros análisis (conviene normalizar el texto antes de
   re-embeber si se quiere clusterizar por tema puro).

## 6. Honestidad y limitaciones

- **Historial de sesiones escaso.** Antes de la sustentación el agente solo registra la
  carga de memoria + verificaciones. El análisis rico corre sobre el **espacio de
  conocimiento** (corpus + hechos), con las sesiones reales como evidencia del pipeline de
  extracción, no como un dataset grande de conversaciones.
- **Etiquetas por archivo.** El "tema" de cada chunk se deriva del archivo de origen; es
  una etiqueta aproximada, lo que explica parte del 60 % (no es un error del método).
- **Modelo de embeddings.** Panel A usa un modelo local estándar y transparente; Panel B
  usa los vectores nativos del OS tal cual.

## 7. Dato corregido sobre OpenFang

La inspección del DB mostró que OpenFang almacena embeddings de **768 dimensiones**
(`memories.embedding` = 3.072 bytes = 768 × float32). El `[memory]` de `config.toml` **no**
fija `embedding_model`, de modo que el OS usa su **modelo por defecto interno** (768-dim).
Esto **corrige** una afirmación previa de las notas/informe que decía `all-MiniLM-L6-v2`
(que es de 384-dim): ese **no** es el modelo de embeddings nativo de OpenFang. El nombre
exacto del default no está documentado públicamente; lo verificable es la dimensión (768).
