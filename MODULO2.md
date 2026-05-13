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

## Bloque 5 — Interfaz Streamlit Chat 🔄 *(en construcción)*

### Qué hará
Actualizar `app.py` de una interfaz Q&A simple a un chat con historial,
burbujas de mensaje, indicador de fuente (RAG vs Estructurado) y selector
de proveedor (gemini / local / ollama).

---

## Bloque 6 — Tests finales e Informe 🔄 *(en construcción)*

### Qué incluirá
- Suite de tests integrada (agente completo con memoria)
- Informe académico del Módulo 2 en LaTeX/PDF
- Métricas de evaluación comparativa entre modos

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
