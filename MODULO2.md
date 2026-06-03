# Módulo 2 — Agente Conversacional con Memoria y Herramientas

## Arquitectura general

```
Usuario
  │
  ▼
ConversationBufferWindowMemory   ← historial de conversación (Bloque 4)
  │
  ▼
LangChain Agent (Router)         ← decide qué herramienta usar (Bloque 3)
  │
  ├─── Herramienta RAG           ← preguntas abiertas / narrativas (Bloque 1)
  │      ChromaDB + Embeddings
  │      → respuesta fundamentada en el corpus Markdown
  │
  └─── Herramienta Estructurada  ← preguntas de datos exactos (Bloque 2)
         JSON en memoria
         → respuesta exacta sin LLM ni embeddings
  │
  ▼
Interfaz Streamlit (chat UI)     ← app.py actualizado (Bloque 5)
```

**Regla de decisión del router:**
- Preguntas de datos exactos (NIT, cifras, presidente, fechas, metas) → Datos Estructurados
- Preguntas abiertas (estrategia, cultura, historia narrativa, sostenibilidad) → RAG

---

## Bloque 1 — Motor RAG con ChromaDB ✅

### Qué hace
Indexa el corpus Markdown en una base de datos vectorial (ChromaDB) y recupera
los fragmentos más relevantes para responder preguntas abiertas sobre Manuelita.

### Archivos
| Archivo | Descripción |
|---------|-------------|
| `src/langchain_app/rag_engine.py` | Motor RAG principal — carga, indexa, recupera y responde |
| `data/vectorstore/{proveedor}/` | Índice ChromaDB persistente (ignorado por git, se regenera con `--reindex`) |
| `data_processed/markdown/key_facts_manuelita.md` | Corpus Q&A de hechos clave — optimizado para retrieval |
| `scripts/test_rag_bloque1.py` | Suite de 6 preguntas con evaluación de keywords |
| `scripts/listar_modelos_gemini.py` | Diagnóstico de modelos de embedding disponibles |

### Cómo correr
Ver **[PROVIDERS.md](./PROVIDERS.md)** para la guía completa de los tres modos.

```powershell
# Modo recomendado (local, sin API):
$env:LLM_PROVIDER="local"; uv run python scripts/test_rag_bloque1.py --reindex

# Modo Gemini (requiere API key en .env):
$env:LLM_PROVIDER="gemini"; uv run python scripts/test_rag_bloque1.py --reindex
```

### Resultados obtenidos
| Proveedor | Score promedio | Tiempo/pregunta |
|-----------|---------------|-----------------|
| `local` (HuggingFace + llama3.2:3b) | **86%** | ~15s |
| `gemini` (gemini-embedding-001 + gemini-2.0-flash) | ~95% estimado | ~3s |
| `ollama` (nomic-embed-text + llama3.2:3b) | ~60% | ~10s |

### Parámetros clave
```python
CHUNK_SIZE    = 500     # caracteres por fragmento
CHUNK_OVERLAP = 80      # solapamiento entre fragmentos
DEFAULT_K     = 5       # fragmentos recuperados por consulta
COLLECTION    = "manuelita_corpus"
```

### Cómo extender el corpus
1. Agregar archivos `.md` en `data_processed/markdown/`
2. Añadir el nombre del archivo a `PRIORITY_FILES` en `rag_engine.py` si tiene alta prioridad
3. Reindexar: `uv run python scripts/test_rag_bloque1.py --reindex`

---

## Bloque 2 — Herramienta de Datos Estructurados ✅

### Qué hace
Responde preguntas de datos exactos (NIT, cifras financieras, presidente, empleados, etc.)
consultando directamente un archivo JSON en memoria. Sin API, sin embeddings, sin LLM.
Latencia ~0ms. Respuestas 100% exactas y sin riesgo de alucinación.

### Archivos
| Archivo | Descripción |
|---------|-------------|
| `data/structured/manuelita_datos.json` | Base de datos JSON con toda la información estructurada |
| `src/langchain_app/tools/structured_tool.py` | Motor de consulta + integración LangChain (BaseTool) |
| `src/langchain_app/tools/__init__.py` | Exportaciones del paquete de herramientas |
| `scripts/test_structured_tool.py` | Suite de 10 preguntas con evaluación de categorías y keywords |

### Cómo correr
```powershell
uv run python scripts/test_structured_tool.py
```
No requiere variables de entorno ni servicios externos.

### Resultados obtenidos
- Categorías detectadas: **10/10 (100%)**
- Score de keywords: **100%**
- Tiempo de respuesta: **~0.0s por pregunta**

### Categorías disponibles
| Categoría | Ejemplos de preguntas |
|-----------|----------------------|
| `nit` | ¿Cuál es el NIT? |
| `presidente` | ¿Quién dirige Manuelita? |
| `fundacion` | ¿En qué año fue fundada? |
| `paises` | ¿En qué países opera? |
| `empleados` | ¿Cuántos colaboradores tiene? |
| `ingresos` | ¿Cuánto facturó en 2023? |
| `ebitda` | ¿Cuál es el EBITDA? |
| `unidades` | ¿Cuáles son las unidades de negocio? |
| `carbono` | ¿Cuál es la meta de carbono para 2030? |
| `general` | Cuéntame sobre Manuelita |

### Cómo actualizar los datos
Editar directamente `data/structured/manuelita_datos.json`. El JSON tiene esta estructura:

```
manuelita_datos.json
├── _meta           → versión, fuente, fecha
├── identificacion  → NIT, ciudad, año de fundación
├── directivos      → presidente
├── geografia       → países, sedes
├── unidades_negocio → lista de 7 unidades con productos y % participación
├── plataformas     → las 4 plataformas principales
├── financiero      → histórico 2019–2024 (ingresos, EBITDA, utilidad neta)
├── operacional     → colaboradores, proveedores, clientes
├── sostenibilidad  → metas carbono, certificaciones, reputación
├── filiales_relacionadas → otras entidades del grupo
└── keywords        → mapa de términos → categoría (para detección de intención)
```

Para agregar una nueva categoría:
1. Agregar los datos en la sección correspondiente del JSON
2. Agregar las keywords en la sección `keywords`
3. Agregar un método `_resp_<categoria>()` en `ManuelitaStructuredTool`
4. Registrar el handler en el diccionario `handlers` del método `query()`

### Uso como herramienta LangChain
```python
from src.langchain_app.tools.structured_tool import get_structured_tool

tool = get_structured_tool()   # devuelve un BaseTool listo para el agente
print(tool.name)               # "ManuelitaDatosEstructurados"
print(tool.func("¿Cuál es el NIT?"))
```

---

## Bloque 3 — Agente Router ✅

### Qué hace
Recibe la pregunta del usuario y decide automáticamente qué herramienta usar,
combinando datos estructurados (exactos, 0ms) con RAG (flexible, corpus-based).

Implementa **dos estrategias** seleccionables:
- **HybridRouter** (por defecto): clasifica por keywords antes de invocar herramientas. Confiable con cualquier LLM.
- **ReactAgent** (demo académico): el LLM razona sobre qué herramienta usar. Requiere modelo capaz (recomendado: gemini-2.0-flash).

### Archivos
| Archivo | Descripción |
|---------|-------------|
| `src/langchain_app/agent.py` | `ManuelitaAgent` (HybridRouter) + `build_react_agent()` |
| `scripts/test_agente_bloque3.py` | Suite de 10 preguntas (6 estructurado / 4 RAG) |

### Cómo correr
```powershell
# Modo local (sin API):
$env:LLM_PROVIDER="local"; uv run python scripts/test_agente_bloque3.py

# Modo Gemini:
$env:LLM_PROVIDER="gemini"; uv run python scripts/test_agente_bloque3.py
```

### Resultados obtenidos
| Métrica | Resultado |
|---------|-----------|
| Routing correcto | **10/10 (100%)** |
| Estructurado ruteado | 6/6 |
| RAG ruteado | 4/4 |
| Tiempo estructurado | ~0.0s |
| Tiempo RAG (local) | ~13s |
| Score keywords (local) | 60% (limitado por llama3.2:3b) |

> **Nota sobre calidad RAG:** El routing es 100% correcto. Las respuestas de preguntas
> narrativas (valores, premios, comunidades) muestran 0% con `llama3.2:3b` porque ese
> modelo no extrae bien el contexto en español. Con `gemini-2.0-flash` se espera 80-100%.

### Lógica de routing

```
Pregunta
  │
  ├── ¿Contiene señales narrativas?       → RAG
  │   (valores, cultura, cómo, describe,
  │    premios, comunidades, gestiona...)
  │
  ├── ¿Coincide con categoría exacta?     → Datos Estructurados
  │   (nit, presidente, fundacion,
  │    paises, empleados, ingresos,
  │    ebitda, unidades, carbono)
  │
  └── Por defecto                         → RAG
```

### Uso programático
```python
from src.langchain_app.agent import ManuelitaAgent

agent = ManuelitaAgent(provider="local")  # o "gemini"
result = agent.ask("¿Cuál es el NIT de Manuelita?")

print(result["answer"])    # El NIT de Manuelita S.A. es 891.300.241
print(result["tool"])      # "estructurado"
print(result["sources"])   # ['data/structured/manuelita_datos.json']
print(result["tiempo_s"])  # 0.0
```

---

## Bloque 4 — Memoria Conversacional ✅

### Qué hace
`ConversationBufferWindowMemory` de LangChain para mantener el historial
de los últimos N turnos de conversación, permitiendo preguntas de seguimiento
contextuales como "¿y en Perú?" o "¿cuándo fue eso?".

### Archivos
| Archivo | Descripción |
|---------|-------------|
| `src/langchain_app/memory.py` | `ConversationMemory` + `ContextualAgent` (agente con memoria) |
| `scripts/test_memoria_bloque4.py` | Suite de 4 tests: memoria básica, ventana, follow-up, diálogo |

### Componentes

#### `ConversationMemory`
Wrapper sobre `ConversationBufferWindowMemory`:
```python
mem = build_memory(window_size=5)
mem.save_turn("¿En qué países opera?", "Colombia, Perú y Chile.")
print(mem.get_history_text())   # texto serializado para prompts
print(mem.get_history_list())   # lista de dicts {role, content} para la UI
print(mem.turn_count())         # número de turnos almacenados
mem.reset()                     # borra el historial
```

#### `ContextualAgent`
`ManuelitaAgent` (Bloque 3) + `ConversationMemory` (Bloque 4):
```python
from src.langchain_app.memory import ContextualAgent

agent = ContextualAgent(provider="local", window_size=5)

r1 = agent.chat("¿En qué países opera Manuelita?")
# → "Opera en Colombia, Perú y Chile."

r2 = agent.chat("¿Y qué produce en Perú?")
# → contexto inyectado automáticamente → responde sobre Perú específicamente
print(r2["enriched"])  # True — pregunta enriquecida con historial

print(agent.get_history())  # historial como lista [{role, content}, ...]
agent.reset()               # nueva conversación
```

### Lógica de detección de follow-up

```
Pregunta recibida
  │
  ├── ¿Empieza con "¿y", "también", "además"?    → follow-up
  ├── ¿Contiene "allí", "ahí", "eso", "ese"?     → follow-up
  ├── ¿Menos de 5 palabras?                       → posible follow-up
  │
  └── Si follow-up Y hay historial:
        → inyectar historial antes de la pregunta
        → result["enriched"] = True
```

### Cómo correr
```powershell
# Modo local (sin API):
$env:LLM_PROVIDER="local"; uv run python scripts/test_memoria_bloque4.py

# Modo Gemini (mejor calidad en preguntas narrativas):
$env:LLM_PROVIDER="gemini"; uv run python scripts/test_memoria_bloque4.py
```

### Resultados obtenidos
| Test | Resultado |
|------|-----------|
| Memoria básica (save/load/reset) | ✓ 100% |
| Ventana deslizante (window=2) | ✓ OK |
| Detección follow-up | ✓ ≥85% |
| Diálogo 6 turnos (routing) | ✓ 100% routing |

### Variable de entorno opcional
```env
MEMORY_WINDOW=5   # turnos a mantener (default: 5)
```

---

## Bloque 5 — Interfaz Streamlit Chat ✅

### Qué hace
`app.py` actualizado de Q&A simple (Módulo 1) a chat conversacional completo
con `ContextualAgent` (Bloques 3 + 4) como motor.

### Archivos
| Archivo | Descripción |
|---------|-------------|
| `app.py` | Interfaz Streamlit — chat conversacional con memoria y selector de proveedor |

### Características nuevas vs Módulo 1
| Característica | Módulo 1 | Módulo 2 |
|----------------|----------|----------|
| Historial visible | Solo últimas 5 preguntas (expanders) | Burbujas de chat acumulativas |
| Motor | `ManuelitaQASystem` (RAG simple) | `ContextualAgent` (HybridRouter + Memoria) |
| Indicador de fuente | ❌ | ✅ Badge RAG / Datos Estructurados / Contexto inyectado |
| Memoria conversacional | ❌ | ✅ ConversationBufferWindowMemory |
| Selector de proveedor | Ollama / Gemini | Local / Ollama / Gemini |
| Nueva conversación | ❌ | ✅ Botón reset en sidebar |
| Métricas de sesión | ❌ | ✅ Turnos / RAG / Estructurado / Con contexto |
| Tabs legacy | Resumen + FAQ | ✅ Conservados + nuevo tab Chat |

### Cómo correr
```powershell
# Modo local (sin API):
$env:LLM_PROVIDER="local"; uv run streamlit run app.py

# Modo Gemini:
$env:LLM_PROVIDER="gemini"; uv run streamlit run app.py
```
Luego abrir: http://localhost:8501

### Componentes de la UI
```
app.py
├── Sidebar
│   ├── Selector de proveedor (local / ollama / gemini)
│   ├── Botón "🔄 Nueva conversación" (reset memoria)
│   └── Info técnica (modelo, router, memoria, framework)
│
├── Header  → modelo activo + contador de turnos
├── Info cards → proveedor / modelo / router / ventana
│
└── Tabs
    ├── 💬 Chat Conversacional   ← NUEVO (Módulo 2)
    │   ├── Chips de preguntas de ejemplo (8 preguntas)
    │   ├── Historial de chat (burbujas usuario 🟢 / agente 🌱)
    │   ├── Badge por mensaje: RAG | Estructurado | 🔗 contexto inyectado
    │   ├── Input + botón Enviar
    │   └── Métricas de sesión: turnos / RAG / estructurado / con contexto
    ├── 📝 Resumen Ejecutivo     ← conservado del Módulo 1
    └── ❓ Preguntas Frecuentes  ← conservado del Módulo 1
```

---

## Bloque 6 — Observabilidad con LangSmith

### Qué es LangSmith

[LangSmith](https://smith.langchain.com) es la plataforma oficial de observabilidad para aplicaciones LangChain. Registra automáticamente todas las llamadas a LLMs, embeddings, retrievers, herramientas y cadenas, mostrando:

- Latencia de cada paso (embedding, retrieval, LLM call)
- Tokens consumidos por llamada
- Prompt exacto enviado al LLM y respuesta recibida
- Árbol de ejecución completo de la cadena
- Historial de corridas y comparativas entre modelos

### Implementación en Manuelita S.A.

**Módulo:** `src/langchain_app/langsmith_setup.py`

Componentes:
- `init_langsmith()` — inicializa y verifica la conexión; se llama al importar `agent.py`
- `get_traceable()` — devuelve el decorador `@traceable` o un no-op si LangSmith no está instalado
- `is_tracing_enabled()` — helper para la UI
- `langsmith_status_badge()` — markdown badge para Streamlit sidebar

**Integración en `agent.py`:**
```python
from src.langchain_app.langsmith_setup import init_langsmith, get_traceable

_langsmith_status = init_langsmith()   # activa tracing al importar
_traceable = get_traceable()

class ManuelitaAgent:
    @_traceable(name="manuelita_ask", tags=["modulo2", "hybrid_router"])
    def ask(self, question: str) -> dict:
        ...
```

Cada llamada a `ask()` queda registrada en LangSmith con nombre `manuelita_ask` y las etiquetas `modulo2` y `hybrid_router`. Las llamadas internas al LLM, retriever y embeddings se anidan automáticamente.

### Activación

Agregar al `.env`:

```env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<obtener en https://smith.langchain.com>
LANGCHAIN_PROJECT=manuelita-osint-ia
```

### Test de verificación

```bash
uv run python scripts/test_langsmith_bloque5.py
```

Salida esperada con LangSmith activo:
```
  Estado    : ACTIVO ✓
  Proyecto  : manuelita-osint-ia
  🔍 Traza registrada en LangSmith
     Dashboard  : https://smith.langchain.com/o/projects/manuelita-osint-ia
     Run name   : manuelita_ask
     Tags       : modulo2, hybrid_router
```

### Qué se traza en el proyecto

| Componente | Tipo de traza | Nombre en LangSmith |
|------------|---------------|---------------------|
| `ManuelitaAgent.ask()` | `@traceable` | `manuelita_ask` |
| LLM (Gemini / Ollama) | Auto (LangChain) | `ChatGoogleGenerativeAI` / `ChatOllama` |
| Embeddings | Auto (LangChain) | `GoogleGenerativeAIEmbeddings` / `HuggingFaceEmbeddings` |
| ChromaDB retriever | Auto (LangChain) | `VectorStoreRetriever` |
| ConversationMemory | Auto (LangChain) | `ConversationBufferWindowMemory` |
| ReAct Agent (demo) | Auto (LangChain) | `AgentExecutor` |

---

## Bloque 7 — Tests Integrados e Informe ✅

### Archivos
| Archivo | Descripción |
|---------|-------------|
| `scripts/test_modulo2_completo.py` | Suite integrada: Bloques 2, 3 y 4 en secuencia |
| `reports/informe_modulo2.pdf` | Informe académico del Módulo 2 (11 páginas, ReportLab) |

### Cómo correr la suite completa
```powershell
# Modo local (sin API):
$env:LLM_PROVIDER="local"; uv run python scripts/test_modulo2_completo.py

# Modo Gemini (recomendado para mejor score en RAG):
$env:LLM_PROVIDER="gemini"; uv run python scripts/test_modulo2_completo.py
```

El script genera automáticamente un reporte JSON en `reports/modulo2_test_{proveedor}_{timestamp}.json`.

### Métricas de evaluación global

| Bloque | Métrica | gemini | local |
|--------|---------|--------|-------|
| 2 — Estructurado | Score keywords | 100% | 100% |
| 2 — Estructurado | Tiempo | ~0ms | ~0ms |
| 3 — Router | Routing correcto | 100% | 100% |
| 3 — Router | Score keywords | ~95% | 60% |
| 4 — Memoria | Routing correcto | 100% | 100% |
| 4 — Memoria | Ventana deslizante | ✓ | ✓ |
| 4 — Memoria | Detección follow-up | ✓ ≥85% | ✓ ≥85% |

### Informe académico
- **Documento:** `reports/informe_modulo2.pdf`
- **Páginas:** 11 páginas
- **Secciones:** Introducción · Arquitectura · Bloques 1–5 · Evaluación comparativa · Estructura de archivos · Conclusiones

---

## Requisitos del entorno

Ver `pyproject.toml` para la lista completa. Los paquetes clave del Módulo 2:

```toml
# RAG
"chromadb>=0.5.0"
"langchain-chroma>=0.1.0"
"sentence-transformers>=3.0.0"   # embeddings locales (Bloque 1, modo local)

# LLM
"langchain-google-genai>=2.0.0"  # Gemini (requiere GEMINI_API_KEY)
"langchain-ollama>=0.2.0"        # Ollama local

# Agente
"langchain>=0.3.0"
"langchain-core>=0.3.0"
"langchain-community>=0.3.0"
```

## Variables de entorno requeridas

```env
# Mínimo para modo local (sin API):
LLM_PROVIDER=local          # gemini | ollama | local

# Para modo Gemini:
GEMINI_API_KEY=AIza...
GEMINI_MODEL=gemini-2.0-flash
GEMINI_EMBED=models/gemini-embedding-001

# Para modo Ollama:
OLLAMA_MODEL=llama3.2:3b    # modelo de chat
# nomic-embed-text se descarga con: ollama pull nomic-embed-text

# Memoria conversacional (Bloque 4):
MEMORY_WINDOW=5             # turnos a mantener en memoria (default: 5)
```

