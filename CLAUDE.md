# CLAUDE.md — Proyecto OSINT Manuelita S.A.

Guía de contexto para el agente de IA que trabaja en este repositorio.
Lee este archivo antes de hacer cualquier cambio de código.

---

## Identidad del proyecto

**Nombre:** Sistema OSINT + Agente Conversacional — Manuelita S.A.  
**Universidad:** Universidad Autónoma de Occidente — Maestría en IA y Ciencia de Datos  
**Módulo actual:** Módulo 2 — Agente Conversacional con Memoria y Herramientas  
**Rama activa:** `development`  
**Stack:** Python 3.11 · LangChain 0.3 · ChromaDB · Streamlit · uv

---

## Estructura de carpetas

```
proyecto_manuelita/
├── app.py                          # Interfaz Streamlit — chat conversacional (Módulo 2)
├── MODULO2.md                      # Documentación técnica completa del Módulo 2
├── PROVIDERS.md                    # Guía de los tres modos: gemini / local / ollama
├── CLAUDE.md                       # Este archivo
│
├── src/langchain_app/
│   ├── rag_engine.py               # Motor RAG con ChromaDB (Bloque 1)
│   ├── tools/
│   │   └── structured_tool.py      # Herramienta datos estructurados JSON (Bloque 2)
│   ├── agent.py                    # HybridRouter — ManuelitaAgent (Bloque 3)
│   ├── memory.py                   # ConversationMemory + ContextualAgent (Bloque 4)
│   ├── corpus_loader.py            # Carga del corpus Markdown (Módulo 1)
│   ├── prompts.py                  # Plantillas de prompts (Módulo 1)
│   └── qa_system.py                # Motor Q&A simple (Módulo 1 — conservado)
│
├── data/
│   ├── structured/
│   │   └── manuelita_datos.json    # JSON con datos exactos: NIT, cifras, directivos
│   └── vectorstore/                # Índice ChromaDB persistente (NO en git)
│
├── data_processed/markdown/
│   ├── key_facts_manuelita.md      # Corpus Q&A — formato clave para retrieval
│   └── *.md                        # Resto del corpus Markdown
│
├── scripts/
│   ├── test_rag_bloque1.py         # Tests RAG (usa --reindex para regenerar vectorstore)
│   ├── test_structured_tool.py     # Tests herramienta estructurada
│   ├── test_agente_bloque3.py      # Tests router 10 preguntas
│   ├── test_memoria_bloque4.py     # Tests memoria conversacional
│   └── test_modulo2_completo.py    # Suite integrada completa
│
└── reports/
    └── informe_modulo2.pdf         # Informe académico 11 páginas
```

---

## Arquitectura del Módulo 2

```
Usuario
  │
  ▼
ContextualAgent          ← memory.py — mantiene últimos 5 turnos (Bloque 4)
  │   ConversationBufferWindowMemory
  │   _enrich_question() → inyecta historial en preguntas de seguimiento
  │
  ▼
ManuelitaAgent           ← agent.py — HybridRouter (Bloque 3)
  │   _route(question) decide:
  │     1. Señales narrativas → RAG
  │     2. Categoría exacta  → Datos Estructurados
  │     3. Default           → RAG
  │
  ├─── ManuelitaStructuredTool    ← tools/structured_tool.py (Bloque 2)
  │      JSON en memoria · 0ms · 100% exacto · sin LLM
  │      Categorías: nit, presidente, fundacion, paises, empleados,
  │                  ingresos, ebitda, unidades, carbono, general
  │
  └─── ManuelitaRAG               ← rag_engine.py (Bloque 1)
         ChromaDB + Embeddings + LLM
         Corpus: data_processed/markdown/*.md
         Prioridad: key_facts_manuelita.md (formato Q&A)
  │
  ▼
Interfaz Streamlit       ← app.py (Bloque 5)
  Chat con burbujas · badges de fuente · selector de proveedor
```

---

## Tres modos de proveedor

Configurar con la variable de entorno `LLM_PROVIDER`:

| Modo | Embeddings | LLM | Requiere |
|------|-----------|-----|---------|
| `gemini` | `models/gemini-embedding-001` | `gemini-2.0-flash` | `GEMINI_API_KEY` en `.env` |
| `local` | `paraphrase-multilingual-MiniLM-L12-v2` (HuggingFace) | `llama3.2:3b` via Ollama | `ollama serve` corriendo |
| `ollama` | `nomic-embed-text` | `llama3.2:3b` via Ollama | `ollama serve` corriendo |

**Modo recomendado para desarrollo:** `local` (sin API, funciona offline).  
**Modo recomendado para producción/demo:** `gemini` (mejor calidad RAG ~95%).

### Comandos de ejecución (PowerShell)

```powershell
# Levantar la app
$env:LLM_PROVIDER="local"; uv run streamlit run app.py

# Tests individuales
uv run python scripts/test_structured_tool.py                           # sin LLM
$env:LLM_PROVIDER="local"; uv run python scripts/test_agente_bloque3.py
$env:LLM_PROVIDER="local"; uv run python scripts/test_memoria_bloque4.py

# Suite completa
$env:LLM_PROVIDER="local"; uv run python scripts/test_modulo2_completo.py

# Regenerar vectorstore (si está vacío o corrupto)
$env:LLM_PROVIDER="local"; uv run python scripts/test_rag_bloque1.py --reindex
```

---

## Variables de entorno (archivo `.env` en raíz)

```env
LLM_PROVIDER=local           # gemini | local | ollama

# Gemini (solo si LLM_PROVIDER=gemini)
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBED=models/gemini-embedding-001

# Ollama
OLLAMA_MODEL=llama3.2:3b     # modelo usado en modo local y ollama

# Memoria
MEMORY_WINDOW=5              # turnos de historial a mantener
```

---

## Reglas de desarrollo

### Routing — NO tocar sin leer esto primero

El router tiene una prioridad estricta en `agent.py → _route()`:

1. **`_RAG_SIGNALS`** (set de strings): palabras que fuerzan RAG sin importar nada más.
   - Incluye: `valores`, `cultura`, `cómo`, `gestiona`, `premios`, `comunidades`, etc.
   - **Si agregas una palabra a esta lista, verifica que no rompa el test Q8** (`¿Cómo gestiona Manuelita la sostenibilidad ambiental?` → debe ir a RAG).

2. **`_detect_category()`** en `structured_tool.py`: detecta categorías por keywords del JSON.
   - La sección `keywords` en `manuelita_datos.json` mapea categoría → lista de triggers.
   - **Nunca pongas `"sostenibilidad"` como keyword de `carbono`** — rompe el routing (fue un bug ya corregido).

3. **Default → RAG**: si no hay señal clara, va a RAG. Es el comportamiento correcto.

### Vectorstore

- La carpeta `data/vectorstore/` está en `.gitignore` — se regenera con `--reindex`.
- Si el vectorstore está vacío o da errores, siempre correr `--reindex` primero.
- El archivo `key_facts_manuelita.md` en formato Q&A es crítico para el score RAG. No eliminarlo.
- Parámetros actuales: `CHUNK_SIZE=500`, `CHUNK_OVERLAP=80`, `DEFAULT_K=5–6`.

### Memoria conversacional

- `ContextualAgent.chat()` guarda siempre la **pregunta original** en memoria, no la enriquecida.
- `_enrich_question()` solo inyecta historial cuando detecta señales de follow-up O la pregunta tiene menos de 5 palabras.
- `reset()` borra el historial — se llama desde el botón "Nueva conversación" de la UI.

### Números en español

- Usar siempre `f"{n:,}".replace(",", ".")` para formatear miles en español.
- Ejemplo: `7971` → `"7.971"` (NO `"7,971"`).
- El método `_fmt()` en `structured_tool.py` ya hace esto.

---

## Tests y resultados esperados

| Script | Score esperado | Tiempo aprox. |
|--------|---------------|--------------|
| `test_structured_tool.py` | 100% keywords, 100% categorías | <1s |
| `test_agente_bloque3.py` (local) | Routing 10/10 (100%), keywords ~60% | ~2min |
| `test_agente_bloque3.py` (gemini) | Routing 10/10 (100%), keywords ~95% | ~30s |
| `test_memoria_bloque4.py` | Memoria 100%, follow-up ≥85% | ~2min |

El score de keywords con modo `local` es bajo (~60%) por las limitaciones de `llama3.2:3b` en español. El **routing** siempre debe ser 100% — si falla, hay un bug en `_route()` o `_RAG_SIGNALS`.

---

## Historial de bugs corregidos — no repetir

| Bug | Causa | Fix |
|-----|-------|-----|
| Q8 iba a Estructurado en vez de RAG | `"sostenibilidad"` era keyword de `carbono` en JSON | Eliminada de JSON + añadida a `_RAG_SIGNALS` |
| Score RAG 0% con embeddings vacíos | Crash previo dejó `chroma.sqlite3` vacío | Siempre usar `--reindex` tras crash |
| Embedding 404 Gemini | Modelo `text-embedding-004` incorrecto | Usar `models/gemini-embedding-001` |
| Quota 429 Gemini | `gemini-2.5-flash` tiene límite 20/día | Cambiar a `gemini-2.0-flash` (~1500/día) |
| Números con coma en vez de punto | `f"{n:,}"` da `"7,971"` en inglés | `_fmt()` con `.replace(",", ".")` |
| `index.lock` en git | Proceso git colgado en mount Windows | Eliminar desde PowerShell con `Remove-Item` |
| Botones negros en Streamlit | CSS solo para `button[kind="primary"]` | Añadir CSS para `button:not([kind="primary"])` |

---

## Flujo de trabajo Git

- **Rama activa:** `development`
- **Convención de commits:** `feat(modulo2): ...` / `fix(app): ...` / `docs: ...`
- **NO commitear:** `data/vectorstore/`, `**/*.sqlite3`, `reports/resultados_rag_*.json`
- **Si hay `index.lock`:** eliminarlo desde PowerShell (`Remove-Item .git\index.lock -Force`), luego hacer git desde PowerShell (no desde el sandbox Linux).

---

## Contexto académico

- **Curso:** Maestría en IA y Ciencia de Datos — Universidad Autónoma de Occidente
- **Equipo:** Juan Manuel Velázquez · Julián Herrera · Juan Sebastián Plazas · Juliana Lozano
- El código debe estar **bien documentado** (docstrings, comentarios en secciones clave) para que los compañeros de equipo puedan entenderlo.
- Mantener compatibilidad hacia atrás: el Módulo 1 (`qa_system.py`, tabs Resumen/FAQ en `app.py`) debe seguir funcionando.
