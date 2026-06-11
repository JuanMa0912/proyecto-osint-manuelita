# CLAUDE.md — Proyecto OSINT Manuelita S.A.

Guía de contexto para el agente de IA que trabaja en este repositorio.
Lee este archivo antes de hacer cualquier cambio de código.

> **Reglas de interacción (obligatorias):** antes de responder, aplica
> [`.claude/rules.md`](.claude/rules.md) — define el estilo de trabajo esperado
> (crítica directa, empezar por los huecos, sin validación automática, e
> **investigar/verificar en la web en vez de inventar** versiones, APIs y prácticas).

---

## Identidad del proyecto

**Nombre:** Sistema OSINT + Agente Conversacional — Manuelita S.A.  
**Universidad:** Universidad Autónoma de Occidente — Maestría en IA y Ciencia de Datos  
**Módulo actual:** Módulo 3 — Productización y Sistemas Agénticos (**Ruta B: OpenFang Agent OS**). Ver [§ Módulo 3](#módulo-3--productización-ruta-b-openfang-agent-os).  
**Módulos previos:** M1 (OSINT + corpus) · M2 (agente RAG + memoria, ver [docs/MODULO2.md](docs/MODULO2.md))  
**Rama activa:** `development`  
**Stack M2:** Python 3.11 · LangChain 0.3 · ChromaDB · Streamlit · uv  
**Stack M3:** OpenFang (Agent OS, Rust) · WSL2 · Ollama/Gemini · Telegram + WhatsApp

---

## Estructura de carpetas

```
proyecto_manuelita/
├── app.py                          # Interfaz Streamlit — chat conversacional (Módulo 2)
├── README.md                       # Portada del repo (ciclo de vida MLOps → AgentOps)
├── CLAUDE.md                       # Este archivo
├── LICENSE                         # MIT
│
├── docs/                           # Documentación de apoyo
│   ├── MODULO2.md                  # Documentación técnica completa del Módulo 2
│   ├── PROVIDERS.md                # Guía de los tres modos: gemini / local / ollama
│   └── NOTAS_INTERNAS_M3.md        # Notas internas del equipo (privado, no en git)
│
├── src/langchain_app/
│   ├── rag_engine.py               # Motor RAG con ChromaDB (Bloque 1)
│   ├── tools/
│   │   └── structured_tool.py      # Herramienta datos estructurados JSON (Bloque 2)
│   ├── agent.py                    # ManuelitaAgent (HybridRouter) + build_react_agent() (Bloque 3)
│   ├── memory.py                   # ConversationMemory + ContextualAgent (Bloque 4)
│   ├── langsmith_setup.py          # Observabilidad LangSmith (Bloque 6)
│   ├── corpus_loader.py            # Carga del corpus Markdown (Módulo 1)
│   ├── prompts.py                  # Plantillas de prompts (Módulo 1)
│   └── qa_system.py                # Motor Q&A simple (Módulo 1 — conservado)
│
├── data/
│   ├── structured/
│   │   └── manuelita_datos.json    # JSON con datos exactos: NIT, cifras, directivos
│   └── vectorstore/{proveedor}/    # Índice ChromaDB persistente, una subcarpeta por proveedor (NO en git)
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
│   ├── test_langsmith_bloque5.py   # Test de observabilidad LangSmith (Bloque 6)
│   ├── test_modulo2_completo.py    # Suite integrada completa (Bloque 7)
│   └── test_20_preguntas.py        # Las 20 preguntas académicas (Módulo 1, qa_system)
│
└── reports/
    ├── informe_final.md            # Informe unificado M1+M2+M3 (VIGENTE; exportar a PDF)
    ├── modulo1/                     # Entregables M1 (QA, fase1 mapa de fuentes, .pdf/.docx/.tex)
    ├── modulo2/                     # Entregable M2 (informe_entrega2_modulo2.pdf)
    └── _archivo/                    # Documentos antiguos/superados (no vigentes)
```

---

## Arquitectura del Módulo 2

```
Usuario
  │
  ▼
Interfaz Streamlit       ← app.py (Bloque 5)
  │  Chat con burbujas · badges de fuente · selector de proveedor
  │  Sugerencias visuales en estado vacío (sin botones)
  │
  ▼
ContextualAgent          ← memory.py — mantiene últimos 5 turnos (Bloque 4)
  │   ConversationBufferWindowMemory
  │   _enrich_question() → inyecta historial en preguntas de seguimiento
  │
  ▼
ManuelitaAgent           ← agent.py — HybridRouter (Bloque 3, estrategia por defecto)
  │   _route(question) decide:
  │     0. Extrae pregunta real si viene enriquecida con historial
  │     1. Señales narrativas → RAG
  │     2. Categoría exacta  → Datos Estructurados (con fuzzy matching)
  │     3. Default           → RAG
  │   (Alternativa: build_react_agent() — agente ReAct de LangChain
  │    que deja al LLM razonar la herramienta. Ver "Estrategias de agente".)
  │
  ├─── ManuelitaStructuredTool    ← tools/structured_tool.py (Bloque 2)
  │      JSON en memoria · 0ms · 100% exacto · sin LLM
  │      Categorías: nit, presidente, fundacion, paises, empleados,
  │                  ingresos, ebitda, unidades, carbono, general
  │      Fuzzy matching: tolera typos (distancia Levenshtein ≤ 2)
  │
  └─── ManuelitaRAG               ← rag_engine.py (Bloque 1)
         ChromaDB + Embeddings + LLM
         Corpus: data_processed/markdown/*.md
         Prioridad: key_facts_manuelita.md (formato Q&A)
         retrieve() extrae pregunta real si viene con historial
  │
  ▼
Prompt RAG con contexto Manuelita + soporte conversacional + anti-alucinación
  │
  ▼
LangSmith                ← langsmith_setup.py (Bloque 6 — Observabilidad)
     Traza TODAS las llamadas LangChain automáticamente
     @traceable en ManuelitaAgent.ask() → run_name="manuelita_ask"
     Badge de estado en sidebar Streamlit
     Proyecto: manuelita-osint-ia
```

> **Numeración de bloques (canónica):** 1 RAG · 2 Estructurado · 3 Router ·
> 4 Memoria · 5 Streamlit · 6 Observabilidad LangSmith · 7 Tests + Informe.
> Si tocas la numeración, regenera también el informe del M2
> (`reports/modulo2/informe_entrega2_modulo2.pdf`) para que no quede desincronizado.

---

## Estrategias de agente — HybridRouter vs ReAct

`agent.py` implementa **dos** estrategias seleccionables sobre las mismas dos
herramientas (`ManuelitaDatosEstructurados` + `ManuelitaRAG`):

| Estrategia | Cómo decide | Cuándo usarla | Punto de entrada |
|------------|-------------|---------------|------------------|
| **HybridRouter** (por defecto) | Clasifica por keywords en `_route()` antes de invocar herramientas. Determinista, 0 tokens en el routing. | Producción y modo `local`: funciona con cualquier LLM, incluso pequeños. | `ManuelitaAgent(provider).ask(q)` |
| **ReAct** (demo académico) | El LLM razona en formato Thought/Action/Observation y elige la herramienta solo. `max_iterations=3`. | Demostrar razonamiento de agente. Requiere LLM capaz — recomendado `gemini-2.0-flash`; puede fallar con modelos <7B. | `build_react_agent(provider).invoke({"input": q})` |

- El `ManuelitaAgent.ask()` es lo que usa la UI (`app.py`) y la memoria
  (`ContextualAgent`). El ReAct es independiente y se invoca aparte.
- **Nota:** el default de `LLM_PROVIDER` en código (`agent.py`, `rag_engine.py`)
  es `"gemini"`. El `.env` del repo usa `local`. Si no defines la variable,
  arranca en modo `gemini` y exigirá `GEMINI_API_KEY`.

---

## Observabilidad — LangSmith (Bloque 6)

**Módulo:** `src/langchain_app/langsmith_setup.py`

LangSmith actúa como middleware de observabilidad: cuando `LANGCHAIN_TRACING_V2=true` está en `.env`, registra automáticamente cada llamada al LLM, embeddings, retriever, memoria y herramientas sin modificar el código del agente.

### Activación (una sola vez)

```powershell
# 1. Instalar SDK
uv add langsmith

# 2. Crear cuenta y API key en https://smith.langchain.com
# 3. Agregar al .env:
#    LANGCHAIN_TRACING_V2=true
#    LANGCHAIN_API_KEY=lsv2_pt_...
#    LANGCHAIN_PROJECT=manuelita-osint-ia

# 4. Verificar
uv run python scripts/test_langsmith_bloque5.py
```

### API del módulo

```python
from src.langchain_app.langsmith_setup import (
    init_langsmith,          # Inicializa y verifica — llamar al arrancar
    get_traceable,           # Devuelve @traceable o no-op si no instalado
    is_tracing_enabled,      # Bool — True si LANGCHAIN_TRACING_V2=true + API key
    get_project_name,        # "manuelita-osint-ia"
    get_dashboard_url,       # URL del dashboard en LangSmith
    langsmith_status_badge,  # String markdown para Streamlit
)
```

### Qué traza automáticamente

| Componente | Run name en LangSmith |
|------------|----------------------|
| `ManuelitaAgent.ask()` | `manuelita_ask` (tags: modulo2, hybrid_router) |
| LLM (Gemini/Ollama) | `ChatGoogleGenerativeAI` / `ChatOllama` |
| Embeddings | `GoogleGenerativeAIEmbeddings` / `HuggingFaceEmbeddings` |
| ChromaDB retriever | `VectorStoreRetriever` |
| Memoria | `ConversationBufferWindowMemory` |

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

### Conocimiento actualizado — investiga, no inventes

Antes de afirmar versiones, APIs, sintaxis, comandos o "mejores prácticas", y antes
de ejecutar comandos en la máquina del usuario: **verifícalo con búsqueda web contra
la documentación real**. El conocimiento de entrenamiento tiene fecha de corte y se
desactualiza; no respondas de memoria si hay duda. Prefiere siempre lo más reciente
y probado. Ejemplos de este repo: OpenFang (v0.6.9 verificada en su GitHub) y
gentle-ai (comandos confirmados antes de correrlos). Detalle completo en
[`.claude/rules.md`](.claude/rules.md) (reglas 10–11).

### Routing — NO tocar sin leer esto primero

El router tiene una prioridad estricta en `agent.py → _route()`:

0. **Extracción de pregunta real**: si la pregunta viene enriquecida con historial
   (formato `[Pregunta actual]\n...`), `_route()` extrae solo la pregunta actual.
   Esto evita que el historial contamine el routing (bug corregido: historial con "nit"
   hacía que preguntas sobre "presidente" se rutearan a NIT).

1. **`_RAG_SIGNALS`** (set de strings): palabras que fuerzan RAG sin importar nada más.
   - Incluye: `valores`, `cultura`, `cómo`, `gestiona`, `premios`, `comunidades`, etc.
   - **Si agregas una palabra a esta lista, verifica que no rompa el test Q8** (`¿Cómo gestiona Manuelita la sostenibilidad ambiental?` → debe ir a RAG).

2. **`_detect_category()`** en `structured_tool.py`: detecta categorías por keywords del JSON.
   - La sección `keywords` en `manuelita_datos.json` mapea categoría → lista de triggers.
   - **Keywords cortas (≤4 chars)** usan word boundaries (`\b`) para evitar falsos positivos
     (ej: `"nit"` no debe matchear `"unidades"`).
   - **Keywords largas (>4 chars)** usan fuzzy matching (Levenshtein ≤ 2) para tolerar typos
     (ej: `"presiente"` → matchea `"presidente"`).
   - **Nunca pongas `"sostenibilidad"` como keyword de `carbono`** — rompe el routing (fue un bug ya corregido).

3. **Default → RAG**: si no hay señal clara, va a RAG. Es el comportamiento correcto.

### Vectorstore

- La carpeta `data/vectorstore/` está en `.gitignore` — se regenera con `--reindex`.
- El índice se persiste en una **subcarpeta por proveedor**: `data/vectorstore/{proveedor}/`
  (`gemini/`, `local/`, `ollama/`). Cambiar de proveedor usa/crea su propio índice.
- Si el vectorstore está vacío o da errores, siempre correr `--reindex` primero.
- El archivo `key_facts_manuelita.md` en formato Q&A es crítico para el score RAG. No eliminarlo.
- Parámetros actuales (`rag_engine.py`): `CHUNK_SIZE=500`, `CHUNK_OVERLAP=80`,
  `DEFAULT_K=5`, `COLLECTION_NAME="manuelita_corpus"`. Ojo: `ManuelitaAgent.ask()`
  recupera con `k=6` (no con el `DEFAULT_K=5`), ver [agent.py:175](src/langchain_app/agent.py#L175).

### Memoria conversacional

- `ContextualAgent.chat()` guarda siempre la **pregunta original** en memoria, no la enriquecida.
- `_enrich_question()` solo inyecta historial cuando detecta señales de follow-up O la pregunta tiene menos de 5 palabras.
- `reset()` borra el historial — se llama desde el botón "Nueva conversación" de la UI.

### Manejo de preguntas enriquecidas (historial inyectado)

Cuando `_enrich_question()` inyecta historial, la pregunta tiene el formato:
```
[Contexto de la conversación]
Usuario: ...
Asistente: ...

[Pregunta actual]
<la pregunta real>
```

Tres puntos del código extraen la pregunta real antes de procesarla:
- **`agent.py → _route()`**: rutea sobre la pregunta real, no sobre el historial.
- **`rag_engine.py → retrieve()`**: busca en ChromaDB solo con la pregunta real.
- **`rag_engine.py → retrieve_with_scores()`**: ídem.

El prompt RAG sí recibe la pregunta completa (con historial) para que el LLM pueda
resolver referencias como "allí", "eso", "ese país".

### Prompts — diseño conversacional + anti-alucinación

Los prompts (`rag_engine.py`, `prompts.py`) distinguen dos tipos de interacción:
1. **Preguntas sobre la empresa** → solo responde con contexto recuperado, no inventa.
2. **Preguntas conversacionales** (saludos, nombre del usuario) → responde de forma natural
   usando el historial de conversación inyectado, sin aplicar regla anti-alucinación.

### Números en español

- Usar siempre `f"{n:,}".replace(",", ".")` para formatear miles en español.
- Ejemplo: `7971` → `"7.971"` (NO `"7,971"`).
- El método `_fmt()` en `structured_tool.py` ya hace esto.

---

## Tests y resultados esperados

| Script | Score esperado | Tiempo aprox. |
|--------|---------------|--------------|
| `test_structured_tool.py` | 100% keywords, 100% categorías | <1s |
| `test_rag_bloque1.py` (local, `--reindex`) | Score RAG ~86%, gemini ~95% | ~1-2min |
| `test_agente_bloque3.py` (local) | Routing 10/10 (100%), keywords ~60% | ~2min |
| `test_agente_bloque3.py` (gemini) | Routing 10/10 (100%), keywords ~95% | ~30s |
| `test_memoria_bloque4.py` | Memoria 100%, follow-up ≥85% | ~2min |
| `test_langsmith_bloque5.py` | Estado ACTIVO si `.env` tiene API key; traza visible en dashboard | <10s |
| `test_modulo2_completo.py` | Suite integrada Bloques 2+3+4; genera JSON en `reports/` | ~3-4min |
| `test_20_preguntas.py` | Las 20 preguntas académicas (Módulo 1, `qa_system`) | ~2-3min |

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
| "unidades" ruteaba a NIT | `"nit"` matcheaba como substring en `"unidades"` | Word boundaries (`\b`) para keywords ≤4 chars |
| Historial contaminaba routing | `_route()` evaluaba pregunta enriquecida completa | Extraer `[Pregunta actual]` antes de rutear |
| Typos rompían routing | `"presiente"` no matcheaba `"presidente"` | Fuzzy matching (Levenshtein ≤ 2) en `_detect_category()` |
| RAG buscaba con historial | `retrieve()` buscaba en ChromaDB con todo el bloque enriquecido | Extraer pregunta real antes de similarity_search |
| `.env` con modelos incorrectos | `gemini-2.5-flash` (20/día) y `gemma3:1b` (17% score) | Corregir a `gemini-2.0-flash` y `llama3.2:3b` |

---

## Flujo de trabajo Git

- **Rama activa:** `development`
- **Convención de commits:** `feat(modulo2): ...` / `fix(app): ...` / `docs: ...`
- **NO commitear:** `data/vectorstore/`, `**/*.sqlite3`, `reports/resultados_rag_*.json`
- **Si hay `index.lock`:** eliminarlo desde PowerShell (`Remove-Item .git\index.lock -Force`), luego hacer git desde PowerShell (no desde el sandbox Linux).

---

## Módulo 3 — Productización (Ruta B: OpenFang Agent OS)

> **Estado (jun 2026):** F0–F5 implementadas y versionadas.
> Motor: **Ollama Cloud `gemma3:27b`** + fallback `gemini-2.5-flash`. 3 Hands activos.
> Telegram funcionando · WhatsApp QR FUNCIONAL (baileys 7, parche LID).
> Seguridad anti-jailbreak: 4 capas (privilegio mínimo + system_prompt endurecido).
> t-SNE (F5): `scripts/tsne_sesiones_m3.py` + `reports/modulo3/`.
> Conflicto financiero resuelto: serie individual Supersociedades es la canónica.
> F4 (informe): markdown completo en
> [`reports/informe_final.md`](reports/informe_final.md) — falta solo exportar a PDF.
> Resumen de estado por fase en [`openfang/README.md`](openfang/README.md). La tabla
> de "Plan por fases" más abajo es la guía original; el estado real vive en ese README.
> Sigue verificando contra el repo antes de asumir que algo está implementado.

### Decisión de ruta

De las dos rutas del enunciado, el equipo eligió **Ruta B — Sistema Operativo
Agéntico con OpenFang** (en vez de Ruta A: FastAPI + Function Calling + N8N).

**Consecuencia clave:** en Ruta B **el código del Módulo 2 (LangChain, ChromaDB,
Streamlit) NO se reusa como base ejecutable.** Solo se migra el **corpus limpio
del Módulo 1** (`data_processed/markdown/*.md`) a la memoria de OpenFang. El M2
queda en el informe como "evolución arquitectónica", no como software vivo.

### Qué es OpenFang (datos verificados — no inventar sobre esto)

- Agent OS open source en **Rust**, MIT — [github.com/RightNow-AI/openfang](https://github.com/RightNow-AI/openfang).
- **Versión: v0.6.9, pre-1.0.** El README advierte: *"feature complete but still
  pre-1.0. Expect rough edges and breaking changes between minor versions."*
  → **Fijar la versión exacta** y no actualizar antes de la sustentación.
- Binario ~32MB, dashboard local en `http://localhost:4200`.
- 7 Hands incluidos (Clip, **Lead**, **Collector**, Predictor, Researcher,
  Twitter, Browser) · 27 proveedores LLM · ~40 adaptadores de canal.

### Decisiones de arquitectura (tomadas con el equipo)

| Tema | Decisión | Nota |
|------|----------|------|
| **Entorno** | WSL2 (Ubuntu) sobre Windows 11 | Más estable para Rust+Node pre-1.0. |
| **Motor LLM** | **Ollama Cloud `gemma3:27b`** (primario, ~4.2 s, sin GPU local, cuota independiente). Fallback: `gemini-2.5-flash`. Se descartaron Gemini free tier (cascada 429 RPM) y `gpt-oss:20b` (filtra razonamiento). Modo soberanía local sigue cableado pero lento sin GPU. | OpenFang permite override de proveedor por canal. |
| **Canales** | **Telegram + WhatsApp** (ambos). Telegram = principal por estabilidad. | Telegram: token de BotFather. WhatsApp: gateway Node QR en puerto 3009 (enlaza WhatsApp personal). |
| **Hands** | **2 built-in** (sugeridos: Lead + Collector) **+ 1 Custom** propio de Manuelita | El Custom es el "toque auténtico" que el enunciado premia. |
| **t-SNE ("picante")** | ✅ **HECHO** (F5, 4 jun 2026). `scripts/tsne_sesiones_m3.py` + `reports/modulo3/`. Datos reales del daemon (memorias 768-dim + sesiones MessagePack). Pureza KMeans 60%; clúster Redes/YouTube puro. | Extraer sesiones (SQLite) → embeddings → t-SNE/UMAP → clústeres. |

### Comandos base (verificados del README)

```bash
# Instalación (dentro de WSL2):
curl -fsSL https://openfang.sh/install | sh
openfang init
openfang start                       # dashboard en http://localhost:4200

# Hands:
openfang hand activate <nombre>      # ej. lead, collector
openfang hand status <nombre>

# WhatsApp gateway (puerto 3009, requiere Node):
node packages/whatsapp-gateway/index.js   # luego escanear QR (Linked Devices)
```

> El instalador nativo de Windows existe (`irm https://openfang.sh/install.ps1 | iex`)
> pero usamos WSL2 por estabilidad. Ollama se expone en el puerto `11434`.

### Punto de mayor riesgo — leer antes de avanzar

La **ingesta del corpus corporativo al vector store + KV de OpenFang** es el paso
**peor documentado** en el README (memoria vía crate `openfang-memory`, SQLite +
embeddings, pero "exact ingestion mechanics aren't detailed"). Es el paso con más
probabilidad de atascar el proyecto.

→ **Hacer un spike de este paso PRIMERO** (Fase 0), con 1 solo archivo del corpus,
antes de invertir en Hands y canales. Si la ingesta no sale en ~1 sesión, hay que
reconsiderar la ruta antes de quedarse sin tiempo para la sustentación.

### Hallazgos verificados — spike F0 (2 jun 2026, OpenFang v0.6.9)

Spike ejecutado en Ubuntu/WSL2. **No inventar sobre esto.**

> **⚠️ CORRECCIÓN (3 jun 2026) — leer antes que el bullet siguiente.** La afirmación
> original "OpenFang NO tiene vector store semántico" era **demasiado fuerte y es
> incorrecta**. La doc oficial (`docs/architecture.md`) describe un **sistema de memoria
> de 6 capas**, y la capa 2 es **Semantic Search**: *"Documents are embedded using the
> configured embedding driver and stored with their vectors. Queries are embedded at
> search time and matched by cosine similarity."* Las 6 capas: (1) Structured KV Store ·
> (2) Semantic Search (embeddings) · (3) Knowledge Graph · (4) Session Manager ·
> (5) Task Board · (6) Usage & Canonical Sessions. **El profe NO se equivocó:** el vector
> store existe. Lo que F0 sí verificó bien es que **no hay mecanismo de ingesta documental
> documentado** (ni CLI `ingest`, ni endpoint REST hallado). El CLI `memory` es solo KV
> (list/get/set/delete). Cómo se *puebla* la capa semántica con el corpus sigue siendo el
> **punto de mayor riesgo abierto** → ver [`openfang/docs/F1b-memoria-semantica.md`](openfang/docs/F1b-memoria-semantica.md).
> **Pista nueva:** existe `openfang migrate --from langchain` (el M2 era LangChain) —
> candidato a vía oficial de migración, aún por probar (`--dry-run` es seguro).

- **El mecanismo de ingesta documental NO está expuesto en CLI/REST conocidos.** Verificado:
  no hay comando `ingest`; `memory` es solo KV (list/get/set/delete); la API REST dio 404 en
  `/api/{memory,knowledge,documents,rag,embeddings,vector,ingest,upload}`. La capa semántica
  existe (arriba), pero su población documental no está documentada en v0.6.9.
- **Cómo se le da conocimiento a un agente (mecanismo real):**
  1. `[model] system_prompt` en `~/.openfang/agents/<agente>/agent.toml` → persona +
     reglas anti-alucinación. **Aquí se porta el contenido de los prompts del M2** (no
     las plantillas LangChain, solo el contenido/persona).
  2. **Workspace** `~/.openfang/workspaces/<agente>/data/` → se dejan los `.md` del
     corpus; el agente los lee con `file_read`/`file_list` (el template lo llama
     literalmente *"Access knowledge base"*). Es recuperación **agéntica por archivos**.
  3. **KV** (`memory_store`/`memory_recall`) → datos estructurados (NIT, cifras).
  4. `MEMORY.md` del workspace → *"Long-Term Memory: curated knowledge across sessions"*.
- **Conclusión (actualizada 4 jun 2026):** OpenFang hace **recuperación agéntica por
  archivos + KV + memoria semántica** (capa 2, embeddings 768-dim). La ingesta bulk no está
  expuesta (no hay CLI `ingest` ni REST); la capa semántica se puebla agent-driven vía
  `memory_store` (12 hechos, recall por similitud verificado). La clave sigue siendo la
  **calidad del corpus** (Markdown limpio, formato Q&A tipo `key_facts_manuelita.md`).
- **Base recomendada:** clonar el template `customer-support` o `sales-assistant`
  (manifiesto en `agent.toml`, tools ya incluyen `file_read`+`memory_*`).
- **Daemon:** `openfang start` → API/dashboard en `127.0.0.1:4200`. Provider por defecto
  `groq` (pide `GROQ_API_KEY`); cambiar a Ollama local o Gemini en `~/.openfang/config.toml`.

### Receta funcional verificada (2 jun 2026, motor actual 4 jun) — `manuelita-bot` responde ✅

Spike F0 cerrado (~3 s vía Gemini). Motor migrado a **Ollama Cloud `gemma3:27b`** el 4 jun
(~4.2 s, sin cuota RPM). Para arranque rápido usar `openfang/scripts/levantar-todo.sh`.
Detalle completo en `openfang/docs/RUNBOOK-demo.md`. Reproducible (spike histórico):

1. **Entorno:** Ubuntu en WSL2 (`wsl --install -d Ubuntu`). OpenFang vive bajo `/root`
   → operar como root: `wsl -d Ubuntu -u root`. Binario en `/root/.openfang/bin/openfang`.
2. **Red:** `~/.wslconfig` con `[wsl2]`/`networkingMode=mirrored` (+ `wsl --shutdown`)
   para que WSL alcance servicios de Windows por `localhost` (Ollama en `11434`).
3. **Un solo agente:** crear `agents/manuelita-bot/` (cp de un template) **y borrar
   `~/.openfang/data/openfang.db*`** — los 30 templates están registrados en la DB
   (no solo en disco); sin borrar la DB el daemon revive los 30. Tras borrarla spawnea 1.
4. **Proveedor demo: Gemini `gemini-2.5-flash-lite`.** ⚠️ `gemini-2.0-flash` quedó con
   free tier en **0** (HTTP 429); `2.5-flash-lite` sí tiene cupo (jun 2026, verificado).
   La key como env var `GEMINI_API_KEY` al lanzar el daemon (archivo `~/.openfang/manuelita.env`).
5. **Proveedor soberanía: Ollama.** Cableado pero **lento sin GPU** (>2 min con `llama3.2:3b`
   → el CLI corta a 120 s). **Fix del driver:** `base_url = "http://localhost:11434/v1"`
   (faltaba `/v1` → daba 404; bug #137/#212). Para acelerar usar un modelo 1b. El
   endpoint de embeddings `/v1/embeddings` aún falla en OpenFang.
6. **Arrancar/probar:** `openfang start` (con la key en env) → dashboard `127.0.0.1:4200`.
   `openfang message <uuid> "..."` (CLI corta a 120 s; con Gemini responde en ~3 s).

**Lección de cuota:** muchos agentes + free tier = 429 inmediato y quema de cupo. Con
**1 agente** y `2.5-flash-lite` el bot respondió en ~3 s.

### Plan por fases

| Fase | Objetivo | Entregable |
|------|----------|-----------|
| **F0** | Spike: instalar OpenFang en WSL2, `openfang start`, ingerir **1** archivo del corpus y validar 1 query RAG interna | Prueba de viabilidad |
| **F1** | Ingerir todo `data_processed/markdown/*.md` (historia, productos, sostenibilidad) a vector + KV | "Identidad base" de Manuelita en el OS |
| **F2** | Configurar `HAND.toml` + `SKILL.md` de los 3 Hands (2 built-in + 1 Custom) | Operaciones autónomas activas |
| **F3** | Conectar Telegram (BotFather) y WhatsApp (gateway 3009); prueba en vivo | Bot respondiendo desde un teléfono real |
| **F4** | Informe técnico **unificado** (M1+M2+M3) en PDF: problema, evolución arquitectónica, diagrama end-to-end | `reports/informe_final.pdf` |
| **F5** | (Opcional "picante") t-SNE/UMAP sobre el historial de sesiones | ✅ **Hecho** — `scripts/tsne_sesiones_m3.py` + `reports/modulo3/` (figura `tsne_clusters.png`, análisis `tsne_analisis.md`, sesiones/costos `tsne_sesiones.txt`) |

### Entregables del módulo (del enunciado)

1. **Informe técnico final unificado (PDF):** problema/solución · evolución M2→M3 ·
   ventajas del Agent OS (seguridad WASM, gestión de RAM) · `HAND.toml` elegido ·
   cómo se inyectó la memoria corporativa · diagrama end-to-end · t-SNE (si aplica).
2. **Sustentación en vivo (15 min, cero diapositivas):** demo práctica (código,
   terminal, dashboard). **Prueba de fuego:** el profesor escribe desde su propio
   teléfono al bot. Mitigación: ensayar el flujo completo end-to-end días antes.

---

## Contexto académico

- **Curso:** Maestría en IA y Ciencia de Datos — Universidad Autónoma de Occidente
- **Equipo:** Juan Manuel Velázquez · Julián Herrera · Juan Sebastián Plazas · Juliana Lozano
- El código debe estar **bien documentado** (docstrings, comentarios en secciones clave) para que los compañeros de equipo puedan entenderlo.
- Mantener compatibilidad hacia atrás: el Módulo 1 (`qa_system.py`, tabs Resumen/FAQ en `app.py`) debe seguir funcionando.
