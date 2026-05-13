# Guía de Proveedores — Módulo 2 RAG

El motor RAG (`src/langchain_app/rag_engine.py`) soporta **tres modos de ejecución**
según los recursos disponibles. Todos comparten el mismo índice ChromaDB y el mismo
corpus Markdown; lo único que cambia es quién genera los embeddings y quién responde.

---

## Resumen rápido

| Proveedor | Variable | Embeddings | LLM | Requiere |
|-----------|----------|------------|-----|----------|
| `gemini`  | (default) | Google API `gemini-embedding-001` | `gemini-2.0-flash` | API key |
| `ollama`  | `LLM_PROVIDER=ollama` | Ollama `nomic-embed-text` | `llama3.2:3b` | Ollama corriendo |
| `local`   | `LLM_PROVIDER=local`  | HuggingFace `paraphrase-multilingual-MiniLM-L12-v2` | Ollama `llama3.2:3b` | Ollama corriendo |

---

## Modo 1 — Gemini (API Key)

**Embeddings:** `models/gemini-embedding-001` vía Google Generative AI API  
**LLM:** `gemini-2.0-flash` vía Google Generative AI API  
**Índice:** `data/vectorstore/gemini/`

### Configuración

1. Obtén tu API key gratuita en https://aistudio.google.com/apikey
2. Crea (o edita) el archivo `.env` en la raíz del proyecto:

```env
GEMINI_API_KEY=AIza...tu_clave_aqui...
LLM_PROVIDER=gemini
GEMINI_MODEL=gemini-2.0-flash
```

### Ejecución (PowerShell)

```powershell
# Primera vez — construye el índice:
uv run python scripts/test_rag_bloque1.py --reindex

# Siguientes veces — usa índice existente:
uv run python scripts/test_rag_bloque1.py
```

### Ejecución (bash / Git Bash)

```bash
uv run python scripts/test_rag_bloque1.py --reindex
```

### Limitaciones del tier gratuito

| Recurso | Límite free tier |
|---------|-----------------|
| `gemini-2.0-flash` (generateContent) | ~1 500 req/día |
| `gemini-2.5-flash` (generateContent) | 20 req/día ← **evitar** |
| `gemini-embedding-001` (embedContent) | 100 req/min |

Si aparece error `429 RESOURCE_EXHAUSTED` al indexar, espera 60 segundos y vuelve a intentar. El índice se construye **una sola vez** y queda guardado en `data/vectorstore/gemini/`.

---

## Modo 2 — Ollama (100% local, sin internet)

**Embeddings:** `nomic-embed-text` vía servidor Ollama local  
**LLM:** `llama3.2:3b` vía servidor Ollama local  
**Índice:** `data/vectorstore/ollama/`

### Instalación (una sola vez)

1. Descarga Ollama desde https://ollama.com/download e instálalo
2. Descarga los modelos necesarios:

```powershell
ollama pull nomic-embed-text   # modelo de embeddings (~274 MB)
ollama pull llama3.2:3b        # modelo de chat (~2 GB)
```

### Ejecución (PowerShell)

```powershell
# Terminal 1 — mantener abierta siempre que uses Ollama:
ollama serve

# Terminal 2 — primera vez:
$env:LLM_PROVIDER="ollama"; uv run python scripts/test_rag_bloque1.py --reindex

# Siguientes veces:
$env:LLM_PROVIDER="ollama"; uv run python scripts/test_rag_bloque1.py
```

### Ejecución (bash / Git Bash)

```bash
# Terminal 1:
ollama serve

# Terminal 2:
LLM_PROVIDER=ollama uv run python scripts/test_rag_bloque1.py --reindex
```

### Rendimiento esperado

- Inicialización: ~40 s (primera vez, con descarga de embeddings)
- Por pregunta: 5–20 s dependiendo del hardware
- Score RAG: ~17% con `gemma3:1b`, ~50-60% con `llama3.2:3b`

---

## Modo 3 — Local HuggingFace (recomendado sin API)

**Embeddings:** `paraphrase-multilingual-MiniLM-L12-v2` vía `sentence-transformers` (CPU, sin servidor)  
**LLM:** `llama3.2:3b` vía Ollama local  
**Índice:** `data/vectorstore/local/`

Este modo combina lo mejor de ambos mundos: los embeddings corren directamente en Python
(sin necesidad de que Ollama esté corriendo para esa parte) y el LLM usa Ollama.
Es el modo **más confiable sin API key**.

### Instalación (una sola vez)

1. Instala Ollama y descarga el LLM (igual que Modo 2):

```powershell
ollama pull llama3.2:3b
```

2. El modelo de embeddings se descarga automáticamente desde HuggingFace la primera vez
   (~471 MB, se guarda en `C:\Users\<usuario>\.cache\huggingface\`).

### Ejecución (PowerShell)

```powershell
# Terminal 1 — Ollama para el LLM:
ollama serve

# Terminal 2 — primera vez:
$env:LLM_PROVIDER="local"; uv run python scripts/test_rag_bloque1.py --reindex

# Siguientes veces (índice ya construido):
$env:LLM_PROVIDER="local"; uv run python scripts/test_rag_bloque1.py
```

### Ejecución (bash / Git Bash)

```bash
LLM_PROVIDER=local uv run python scripts/test_rag_bloque1.py --reindex
```

### Rendimiento esperado

- Primera inicialización: ~60–90 s (descarga modelo HuggingFace + indexación)
- Siguientes inicializaciones: ~8–12 s (carga modelo + índice cargado)
- Por pregunta: 10–20 s en CPU
- Score RAG con corpus optimizado: **86%**

---

## Configuración del archivo `.env`

Crea un archivo `.env` en la raíz del proyecto (no lo subas a Git — ya está en `.gitignore`):

```env
# ── Gemini (Modo 1) ──────────────────────────────────────
GEMINI_API_KEY=AIza...tu_clave_aqui...
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBED=models/gemini-embedding-001

# ── Ollama (Modo 2 y 3) ──────────────────────────────────
OLLAMA_MODEL=llama3.2:3b

# ── Proveedor activo (gemini | ollama | local) ───────────
LLM_PROVIDER=local
```

También puedes sobreescribir el proveedor al momento de ejecutar sin tocar el `.env`:

```powershell
# PowerShell:
$env:LLM_PROVIDER="gemini"; uv run python scripts/test_rag_bloque1.py

# bash:
LLM_PROVIDER=gemini uv run python scripts/test_rag_bloque1.py
```

---

## Comparación de resultados (Bloque 1 — 6 preguntas test)

| Modo | Score promedio | Tiempo/pregunta | Requiere internet |
|------|---------------|-----------------|-------------------|
| `gemini` (gemini-2.0-flash) | ~95% (estimado) | ~3 s | ✅ Sí (API) |
| `local` (HF embed + llama3.2:3b) | **86%** | ~15 s | ❌ No |
| `ollama` (nomic + llama3.2:3b) | ~60% | ~10 s | ❌ No |
| `ollama` (nomic + gemma3:1b) | ~17% | ~5 s | ❌ No |

> **Nota:** El score varía según el hardware. Los tiempos son en CPU (sin GPU dedicada).

---

## Solución de problemas frecuentes

### `ConnectionError: Failed to connect to Ollama`
Ollama no está corriendo. Abre una terminal y ejecuta `ollama serve`.

### `429 RESOURCE_EXHAUSTED` (Gemini embeddings)
Quota de embeddings excedida (100/min). Espera 60–90 segundos y vuelve a intentar.
El índice se guarda de forma incremental, así que puedes usar `--reindex` para reconstruirlo completo.

### `404 models/... is not found`
El nombre del modelo de embedding cambió. Corre:
```powershell
uv run python scripts/listar_modelos_gemini.py
```
Y actualiza `GEMINI_EMBED` en `.env` con el modelo disponible.

### `Índice cargado: 0 vectores`
El índice anterior quedó vacío por un crash. Fuerza la reindexación:
```powershell
uv run python scripts/test_rag_bloque1.py --reindex
```

### `LangChainDeprecationWarning: HuggingFaceEmbeddings`
Advertencia informativa, no es un error. El código sigue funcionando correctamente.
Para eliminarla, instala el paquete actualizado:
```powershell
uv add langchain-huggingface
```
Y cambia el import en `rag_engine.py`:
```python
from langchain_huggingface import HuggingFaceEmbeddings
```
