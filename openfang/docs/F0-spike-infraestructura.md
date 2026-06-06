# Fase F0 — Infraestructura OpenFang (spike)

Documento técnico del Módulo 3 — Maestría en IA y Ciencia de Datos, Universidad Autónoma de Occidente.
Productización del agente conversacional de **Manuelita S.A.** sobre **OpenFang** (un Agent OS en Rust).

---

## 1. Objetivo

Montar OpenFang sobre WSL2 y **validar que un agente responde** antes de empezar a construir el agente Manuelita.

Esta es la fase **F0**: no se construye lógica del agente todavía. El propósito es dejar la infraestructura de pie, reproducible y verificada, de modo que cuando arranque la fase F1 (construcción del agente) el equipo ya tenga un entorno funcional y documentado.

---

## 2. Entorno verificado

Todos los datos de este documento fueron probados en una máquina real con la siguiente configuración:

| Componente | Versión / Detalle |
|------------|-------------------|
| Sistema operativo | Windows 11 (build 26200) |
| WSL | 2.5.7 |
| Kernel Linux (WSL2) | 6.6.87.1-microsoft-standard-WSL2 |
| Distribución en WSL2 | Ubuntu |
| Node | v24 (en Windows) |
| Ollama | en Windows, con modelos `llama3.2:3b`, `llama3.2:1b`, `gemma3:1b`, entre otros |
| OpenFang | v0.6.9 |

> ⚠️ **OpenFang v0.6.9 es pre-1.0.** Su propio README advierte: *"expect rough edges and breaking changes"*. Varias de las soluciones de este documento existen precisamente porque el software aún está en evolución.

---

## 3. Instalación paso a paso

### 3.1 Instalar Ubuntu en WSL2

```powershell
wsl --install -d Ubuntu --no-launch
```

Con `--no-launch` se difiere el setup interactivo. Al primer arranque con `wsl -d Ubuntu`, Ubuntu pide **crear un usuario Unix + password**.

> El password **no se muestra al escribir**: es el comportamiento normal de Linux, no un cuelgue.

OpenFang se instaló como **root**, por lo que vive bajo `/root`. En consecuencia, se opera siempre con el usuario root:

```powershell
wsl -d Ubuntu -u root
```

### 3.2 Instalar OpenFang dentro de Ubuntu

```bash
curl -fsSL https://openfang.sh/install | sh
```

El instalador deja el binario en:

```
/root/.openfang/bin/openfang
```

y lo añade al `PATH` vía `~/.bashrc`.

### 3.3 Inicializar OpenFang

```bash
openfang init
```

Esto crea:

```
~/.openfang/config.toml
~/.openfang/data/
```

> En modo no-interactivo, `openfang init` entra en **"quick mode"** con el provider `groq` por defecto. Ese provider por defecto se cambia más adelante (sección 5).

---

## 4. Networking espejo (mirrored)

Por defecto, WSL2 usa NAT y **no alcanza servicios de Windows en `localhost`**. Esto rompe el acceso al Ollama que corre en Windows (`localhost:11434`).

**Solución verificada:** crear el archivo `C:\Users\<usuario>\.wslconfig` con el modo de red espejo:

```toml
[wsl2]
networkingMode=mirrored
```

Luego reiniciar WSL por completo (esto cierra todas las sesiones WSL abiertas) y volver a abrir:

```powershell
wsl --shutdown
```

Tras reabrir WSL, la conexión hacia el Ollama de Windows funciona. Verificación realizada desde dentro de WSL:

```bash
curl http://localhost:11434/api/version
```

Devolvió **HTTP 200** (alcanza el Ollama de Windows).

> Requiere **WSL >= 2.0**.

---

## 5. Proveedores LLM

La configuración del modelo vive en `~/.openfang/config.toml`, sección `[default_model]`. Se documentan dos modos.

### 5.1 Gemini (modo demo — validado en F0; motor actual: Ollama Cloud)

> **Nota (4 jun 2026):** el motor en producción es **Ollama Cloud `gemma3:27b`**
> (proveedor `openai`, endpoint `https://ollama.com/v1`). Gemini se mantiene como
> fallback. Ver `config/config.example.toml` para la config actual.

```toml
[default_model]
provider = "gemini"
model = "gemini-2.5-flash-lite"
api_key_env = "GEMINI_API_KEY"
```

La API key se carga como variable de entorno `GEMINI_API_KEY` al lanzar el daemon (la key **no se commitea**).

> ⚠️ **DATO VERIFICADO (junio 2026, free tier):**
> - `gemini-2.0-flash` y `gemini-2.0-flash-lite` devolvieron **HTTP 429** con `"Quota exceeded ... limit: 0"`.
> - En cambio `gemini-2.5-flash`, `gemini-2.5-flash-lite` y `gemini-3-flash-preview` devolvieron **HTTP 200**.
>
> Por eso se usa `gemini-2.5-flash-lite`.

### 5.2 Ollama (modo soberanía / local)

```toml
[default_model]
provider = "ollama"
model = "llama3.2:3b"
base_url = "http://localhost:11434/v1"
api_key_env = ""
```

> 🔴 **DATO CRÍTICO:** el `base_url` **debe terminar en `/v1`**. OpenFang trata a Ollama como un endpoint OpenAI-compatible; sin `/v1` devuelve el error `"404 page not found"`. Es el bug conocido de los issues **#137** y **#212** del repositorio de OpenFang.

**Limitaciones verificadas en CPU sin GPU:**

- `llama3.2:3b` tardó **>2 minutos por respuesta** y el CLI **corta a los 120s**. Para acelerar, usar un modelo **1b**.
- El endpoint de embeddings `/v1/embeddings` de Ollama **todavía falla** en OpenFang (`"error sending request"`).

---

## 6. Restringir a un solo agente

**Hallazgo importante:** al arrancar, OpenFang **auto-levanta TODOS los agentes plantilla** de `~/.openfang/agents/` (son **30**) y además los persiste en la base SQLite `~/.openfang/data/openfang.db`.

Mover o borrar carpetas de `agents/` **no basta**, porque los agentes **reviven desde la DB**.

**Solución verificada:**

1. Dejar en `~/.openfang/agents/` **solo la carpeta del agente deseado**.
2. Borrar la base de datos completa (db + shm + wal):

```bash
rm ~/.openfang/data/openfang.db*
```

Al reiniciar el daemon, OpenFang **reconstruye desde disco** y queda **1 agente** (`openfang status` mostró `Agents: 1`).

> **Por qué importa:** 30 agentes contra el free tier de Gemini = una tormenta de 429 instantánea; contra Ollama en CPU = sobrecarga.

---

## 7. Arrancar y verificar

Con `GEMINI_API_KEY` en el entorno, levantar el daemon:

```bash
openfang start
```

- El **dashboard web** queda en `http://127.0.0.1:4200` (accesible desde el navegador de Windows).
- Estado del sistema, agentes y provider:

```bash
openfang status
```

Probar un agente (el UUID se saca de `openfang agent list`):

```bash
openfang agent list
openfang message <UUID> "texto"
```

> El CLI **corta a 120s**.

---

## 8. Hallazgo arquitectónico clave

> **Corrección posterior (3-4 jun 2026):** la afirmación "no hay vector store" era
> demasiado fuerte. La doc oficial describe una **memoria de 6 capas** que incluye
> **Semantic Search (embeddings, 768-dim)**. Lo que NO existe es ingesta documental
> bulk (sin CLI `ingest` ni REST). La capa semántica se puebla vía `memory_store`
> agent-driven — verificado y funcionando. Ver `docs/F1b-memoria-semantica.md`.

**OpenFang v0.6.9 NO expone ingesta documental bulk** (CLI `ingest` ni REST para documentos).
Lo verificado en este spike sigue siendo correcto:

- No hay comando `ingest`. El comando `memory` es **solo KV** (`list` / `get` / `set` / `delete`).
- La API REST devuelve **404** en todas estas rutas: `/api/memory`, `/api/knowledge`, `/api/documents`, `/api/rag`, `/api/embeddings`, `/api/vector`, `/api/ingest`.

El conocimiento se le da al agente por otras vías:

1. El **`system_prompt`** del manifiesto.
2. Archivos en el **workspace del agente**, leídos con la herramienta `file_read`.
3. **Memoria KV** (`memory_store` / `memory_recall`).
4. El **`MEMORY.md`** del workspace.

Es decir: **recuperación AGÉNTICA por archivos, no RAG por embeddings.**

> Esta diferencia arquitectónica se detalla en la fase **F1**.

---

## 9. Tabla de problemas resueltos (gotchas)

| Problema | Causa | Solución |
|----------|-------|----------|
| 30 agentes "zombie" | Persistidos en `openfang.db` | Borrar `openfang.db*` y dejar 1 carpeta en `agents/` |
| Ollama `"404 page not found"` | Falta `/v1` en `base_url` | `base_url = "http://localhost:11434/v1"` |
| WSL no ve el Ollama de Windows | NAT de WSL2 | `networkingMode=mirrored` en `.wslconfig` + `wsl --shutdown` |
| Gemini 2.0-flash `429 limit:0` | Cuota free tier agotada / en 0 | Usar `gemini-2.5-flash-lite` |
| Respuesta Ollama >2min y timeout | Modelo 3b en CPU sin GPU | Usar un modelo 1b |
