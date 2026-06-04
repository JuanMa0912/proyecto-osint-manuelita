# Fase F1b — Memoria semántica de OpenFang (vector store) y migración del conocimiento

> Maestría en IA y Ciencia de Datos — Universidad Autónoma de Occidente
> Módulo 3 · Ruta B · Empresa: Manuelita S.A.
> **Estado:** 🟢 Resuelto en lo esencial (3 jun 2026) — la memoria semántica persistente
> de OpenFang **funciona** (Vía B verificada, §4). Falta solo **cargar el corpus** con un
> script `memory_store` (one-shot). Afecta el **30% de la rúbrica** (ítem 1).

## 1. Por qué existe este documento

El enunciado y la rúbrica exigen explícitamente migrar el conocimiento corporativo al
**Vector Store (almacenamiento semántico)** de OpenFang, usando su **sistema de memoria de
6 capas**, y demostrar un **"RAG interno del OS"**:

> Enunciado §2: *"inyectarán el contexto corporativo en el **Vector Store (almacenamiento
> semántico)** y en el Structured KV Store… usando el **sistema de memoria de 6 capas**."*
> Enunciado §4: *"…recuperará información del contexto ingerido (**RAG interno del OS**)."*
> Rúbrica ítem 1 (30%): *"**Migración impecable del conocimiento corporativo a la memoria
> de OpenFang**…"*

Nuestro spike F0 había concluido (de forma **demasiado fuerte**) que *"OpenFang no tiene
vector store"*. **Esa conclusión está corregida aquí.**

## 2. Lo verificado (3 jun 2026, v0.6.9)

### 2.1 El vector store SÍ existe (doc oficial)

`docs/architecture.md` de OpenFang describe una **memoria de 6 capas**:

| # | Capa | Qué hace |
|---|------|----------|
| 1 | **Structured KV Store** | KV por agente, valores JSON (SQLite). Tools `memory_store`/`memory_recall`. |
| 2 | **Semantic Search** | *"Documents are embedded using the configured embedding driver and stored with their vectors. Queries are embedded at search time and matched by cosine similarity."* **← el vector store que pide el profe.** |
| 3 | Knowledge Graph | Entidades-relaciones con traversal. |
| 4 | Session Manager | Historial de conversación con conteo de tokens. |
| 5 | Task Board | Cola de tareas multi-agente. |
| 6 | Usage & Canonical Sessions | Costos + resúmenes de sesión multicanal. |

### 2.2 Lo que NO está documentado: la ingesta documental

Verificado por CLI en WSL (`openfang --help`, `openfang memory --help`):

- El CLI **`memory` es solo KV**: `list | get | set | delete`. No hay subcomando de
  ingesta ni de búsqueda semántica.
- **No existe** comando `ingest`. La API REST devolvió **404** en
  `/api/{memory,knowledge,documents,rag,embeddings,vector,ingest,upload}` (F0).
- Conclusión honesta: **la capa 2 existe, pero v0.6.9 no expone un mecanismo documentado
  para cargar documentos en ella.** Este es el riesgo abierto.

### 2.3 Pista nueva — comando `migrate`

```
openfang migrate --from <openclaw|langchain|autogpt> [--source-dir <dir>] [--dry-run]
```

El **Módulo 2 fue LangChain**. `openfang migrate --from langchain` es **candidato a la vía
oficial** de migración del conocimiento. `--dry-run` es seguro (no escribe). **Sin probar aún.**

## 3. Qué tenemos hoy (mapeo honesto a las 6 capas)

El agente `manuelita-bot` ya usa, de forma verificada:

- **Capa 1 (KV):** datos núcleo (NIT, cifras) vía `memory_store`/`memory_recall`.
- **Capa 4 (Sessions):** memoria conversacional del canal (corto/largo plazo).
- **`system_prompt` + workspace `data/*.md` (file_read):** el grueso del corpus.

**El hueco:** la **capa 2 (Semantic Search)** no está poblada con el corpus. Hoy la
recuperación profunda es **agéntica por archivos** (`file_read`), no por similitud vectorial.
Funciona y es defendible, pero **no es** lo que el profe llama "vector store / RAG interno".

## 4. Plan para resolverlo (en orden de preferencia)

> Todo esto corre en WSL contra el daemon vivo. **Ojo cuota:** poblar la capa semántica
> genera embeddings → consume cuota del driver. Probar con **1 archivo** primero (disciplina F0).

### Vía A — `migrate --from langchain` → ❌ DESCARTADA (verificado 3 jun 2026)
`openfang migrate --from langchain --dry-run` responde literal:
`Migration failed: Unsupported source: LangChain migration is not yet supported. Coming soon!`
→ En v0.6.9 el comando es un **stub**. No es vía viable. (Solo `openclaw`/`autogpt` podrían
estar implementados, pero ninguno aplica a nuestro M2.)

### Vía B — poblar la capa semántica vía `memory_store` → ✅ VERIFICADA QUE FUNCIONA (3 jun 2026)

**Contexto:** `config.toml` `[memory]` solo expone `decay_rate`; no hay knob de *embedding
driver* ni endpoint de ingesta documental. La población **bulk** no está expuesta. PERO la
vía **agent-driven** sí funciona y da recuperación semántica persistente. Evidencia del spike:

| Paso | Acción | Resultado |
|------|--------|-----------|
| 1 | Agente ejecuta `memory_store`: *"el proyecto piloto interno se llama Colibrí Azul y lo lidera Marta Ruiz"* | Guardado ✓ |
| 2 | Pregunta reformulada **sin** "colibrí" ni "proyecto": *"¿quién está a cargo del experimento del **ave pequeña**?"* | **"Marta Ruiz"** ✓ (recall por significado) |
| 3 | **Reinicio del daemon** (borra buffer de sesión en RAM) + misma pregunta en frío | **"Marta Ruiz"** ✓ (persistente, no era contexto de sesión) |

**Conclusión:** `memory_store` deja el dato en **memoria persistente** y el agente lo recupera
por **similitud semántica** (no por clave exacta), sobreviviendo al reinicio. Esto **es** el
"vector store / RAG interno del OS" que pide el enunciado, poblado por vía agent-driven.

**Cómo escalarlo al corpus:** un script que recorra `data_processed/markdown/*.md` por *chunks*
y, por cada uno, envíe al agente una instrucción `memory_store` (o llame al tool por API).
⚠️ Gasta cuota de embeddings/LLM → cargar **una vez**, fuera de horario de demo, y con el
corpus ya curado. Probar primero con `key_facts_manuelita.md`.

### Vía C — fallback honesto (si A y B no poblan la capa en v0.6.9)
- **No falsear.** Explicar en informe y demo que v0.6.9 (pre-1.0) **expone** la capa
  semántica pero **no documenta** su ingesta documental, y que la migración se hizo a las
  capas **KV + Sessions + system_prompt + workspace** (recuperación agéntica por archivos).
- Mapear explícitamente nuestra implementación a las 6 capas (sección 3) → demuestra
  **dominio de la arquitectura**, que es lo que la rúbrica realmente evalúa.
- Demostrar en vivo la búsqueda semántica **mínima que sí funcione** (aunque sea KV +
  sessions) para no llegar con las manos vacías al "RAG interno".

## 5. Decisión (actualizada 3 jun 2026 — con evidencia)

Estado tras las sondas + spike en WSL:
- **Vía A (migrate): ❌ stub**, no viable.
- **Vía B (`memory_store` agent-driven): ✅ FUNCIONA** — recall semántico **persistente**
  verificado (tabla §4). Es la vía buena.
- **Vía C (mapeo honesto a 6 capas): se mantiene como narrativa de respaldo.**

**Plan adoptado (Vía C + B, según decisión del equipo):**
1. **Base (C):** en informe y demo, mapear explícitamente la implementación a las 6 capas y
   explicar honestamente que la ingesta **bulk** no está expuesta en v0.6.9; la población es
   **agent-driven** vía `memory_store`.
2. **Escalar (B):** cargar el corpus (o al menos `key_facts_manuelita.md` + datos núcleo) a
   memoria con un script `memory_store`, **una sola vez** y fuera de horario de demo, para
   tener **memoria semántica real demostrable** en vivo.
3. **No sacrificar el ensayo** de la prueba de fuego por perfeccionar la carga. La carga es
   one-shot; el ensayo de la demo pesa igual en la nota.

**Para la sustentación:** se puede reproducir el spike de §4 en vivo (store + recall semántico
tras reinicio) como prueba contundente del "RAG interno del OS". ~3 llamadas Gemini.

## 6. Pendiente de actualizar cuando se resuelva

- [ ] `reports/informe_final.md` — la "Nota de honestidad técnica" (§3.2) afirma que no hay
  vector store; **reescribir** con el modelo de 6 capas y la vía elegida.
- [ ] `docs/F1-agente-manuelita.md` §2 — suavizar "No hay RAG por embeddings".
- [ ] Este doc — registrar el resultado del spike (A/B/C) con evidencia.
