# OpenFang — Agente `manuelita-bot` (Módulo 3, Ruta B)

Productización del asistente conversacional de **Manuelita S.A.** sobre **OpenFang**
(Agent OS open source en Rust), corriendo en **WSL2 (Ubuntu)**.

Esta carpeta contiene la configuración **versionada y reproducible** del agente, para
que el equipo pueda clonar el repo y levantarlo con pocos pasos.

## Estructura

```
openfang/
├── README.md                          # este archivo
├── docs/
│   ├── F0-spike-infraestructura.md    # Fase F0: instalar y validar OpenFang
│   ├── F1-agente-manuelita.md         # Fase F1: el agente, prompt, seguridad y pruebas
│   ├── F1b-memoria-semantica.md       # Memoria semántica: modelo 6 capas, Vía B verificada
│   ├── F2-hands.md                    # Fase F2: operaciones autónomas (Hands)
│   ├── F3-canales.md                  # Fase F3: canales Telegram + WhatsApp
│   └── RUNBOOK-demo.md                # Guía paso-a-paso para la sustentación
├── agents/manuelita-bot/
│   ├── agent.toml                     # manifiesto: persona + system_prompt + tools (solo lectura)
│   └── MEMORY.md                      # hechos curados de Manuelita
├── hands/sostenibilidad-manuelita/    # Custom Hand (HAND.toml + SKILL.md)
├── whatsapp-gateway/                  # Gateway QR (Baileys) → manuelita-bot (F3)
│   ├── index.js · package.json        # gateway Node (node_modules y auth_store NO se versionan)
│   └── start-gateway.ps1              # launcher: lee el UUID del agente en vivo y arranca
├── config/
│   └── config.example.toml            # config de OpenFang (Ollama Cloud / Gemini / Ollama local)
└── scripts/
    ├── 00-estado.sh                       # chequeo read-only del sistema (no gasta cuota)
    ├── 01-start-daemon.sh                 # arranca el daemon (OLLAMA_API_KEY primario)
    ├── 02-deploy-agent.sh                 # despliega manuelita-bot (manifiesto + corpus + MEMORY.md)
    ├── 03-switch-provider.sh              # alterna proveedor LLM (demostración soberanía)
    ├── 04-cargar-memoria-semantica.sh     # puebla la memoria SEMANTICA via memory_store (RE-correr tras cada deploy)
    ├── 05-setup-hands.sh                  # reinstala+activa los 3 Hands (AL FINAL, tras cada reinicio)
    ├── 06-whatsapp-gateway.sh             # configura e instala el gateway WhatsApp QR (una vez)
    └── levantar-todo.sh                   # arranque de UN comando (Escenario A: DB intacta, no gasta cuota)
```

## Quick start

> 📋 **Para la demo, sigue el [`docs/RUNBOOK-demo.md`](docs/RUNBOOK-demo.md)** — paso a paso con
> verificación y troubleshooting del daemon. Chequeo rápido de estado: `bash scripts/00-estado.sh`.


Requisitos: Windows 11 + WSL2 con Ubuntu y OpenFang ya instalado (ver
[`docs/F0-spike-infraestructura.md`](docs/F0-spike-infraestructura.md)). Operar dentro
de WSL como root: `wsl -d Ubuntu -u root`.

1. **Keys locales** (una vez; NO se commitean). El agente usa **Ollama Cloud** como motor
   primario (rápido, sin GPU local, cuota aparte) y Gemini como fallback:
   ```bash
   echo 'export OLLAMA_API_KEY=TU_KEY_OLLAMA' >  ~/.openfang/manuelita.env   # ollama.com/settings/keys (gratis)
   echo 'export GEMINI_API_KEY=TU_KEY_GEMINI' >> ~/.openfang/manuelita.env   # fallback
   chmod 600 ~/.openfang/manuelita.env
   ```
2. **Desplegar el agente:**
   ```bash
   bash scripts/02-deploy-agent.sh
   ```
3. **Arrancar:**
   ```bash
   bash scripts/01-start-daemon.sh        # dashboard: http://127.0.0.1:4200
   ```
4. **Cargar la memoria semántica** (⚠️ obligatorio tras cada deploy — el paso 2 borra
   `openfang.db` y con ella la memoria KV/semántica):
   ```bash
   bash scripts/04-cargar-memoria-semantica.sh   # ~10 hechos via memory_store (gasta ~11 llamadas LLM)
   ```
5. **Probar:**
   ```bash
   openfang agent list                    # copia el UUID de manuelita-bot
   openfang message <UUID> "¿Cuál es el NIT de Manuelita y quién es su presidente?"
   ```

> **Orden crítico (tras cada deploy):** `02-deploy` → `01-start` → `04-cargar-memoria` → `05-setup-hands` → probar.
> - `04-cargar-memoria-semantica.sh`: repuebla la memoria semántica. **OJO: reinicia el daemon.**
> - `05-setup-hands.sh`: reinstala+activa los 3 Hands. **DEBE ir AL FINAL**, porque el Hand Custom
>   **no sobrevive a un reinicio del daemon** (los built-in reviven solos; el Custom no). Cualquier
>   `openfang start`/reinicio posterior **vuelve a borrar el Custom** → re-corre `05-setup-hands`.
> Detalle en [`docs/F1b-memoria-semantica.md`](docs/F1b-memoria-semantica.md). **Nota:** en OpenFang
> cada Hand es un agente especializado, por eso aparecen como agentes (`lead-hand`, `collector-hand`,
> `sostenibilidad-hand`) en la vista de Agentes/Chat — es lo esperado.
>
> Detalles, comandos y solución de problemas (gotchas) en `docs/`.

## Estado del proyecto (junio 2026)

| Fase | Descripción | Estado |
|------|-------------|--------|
| F0 | Infraestructura OpenFang en WSL2 (instalación, networking, proveedores) | ✅ Validada |
| F1 | Agente `manuelita-bot`: persona + corpus + anti-alucinación proporcional | ✅ Responde (~3 s vía Gemini) |
| F2 | Hands: 2 built-in (`collector`, `lead`) + 1 Custom (`sostenibilidad-manuelita`) | ✅ Configuradas y pausadas |
| F3 | Canales: Telegram (nativo, **funcionando** → `manuelita-bot`) + WhatsApp (gateway QR funcional) | ✅ Telegram vivo y ensayado en vivo · ✅ **WhatsApp QR FUNCIONAL** (baileys 7.0.0-rc13, parche LID, responde de verdad — ver `scripts/06-whatsapp-gateway.sh`) |
| F4 | Informe técnico unificado | 🟡 Markdown completo y depurado (`reports/informe_final.md`, `0 POR VERIFICAR`) · falta solo exportar a PDF |
| F5 | Análisis t-SNE de conversaciones (opcional) | ✅ **Hecho** — `scripts/tsne_sesiones_m3.py` + `reports/modulo3/` (figura, análisis, sesiones). Datos reales 768-dim del daemon. |

## Notas

- **Proveedor LLM (jun 2026):** primario **Ollama Cloud `gemma3:27b`** vía endpoint
  OpenAI-compatible (`https://ollama.com/v1`, auth Bearer `OLLAMA_API_KEY`) —
  **verificado end-to-end**: ~4.2 s, limpio en español, sin fuga de razonamiento, cuota
  independiente de Gemini. Fallback: Gemini `gemini-2.5-flash`. Se descartaron
  `gpt-oss:20b` (filtra su razonamiento en el loop de herramientas) y Gemini free tier
  (cascada de 429 por RPM: un mensaje = varias llamadas).
  Modo soberanía pura con Ollama local sigue documentado (cableado, pero lento sin GPU).
- **Conocimiento:** el agente usa su `system_prompt` (datos núcleo) + archivos del workspace
  (`file_read`) + **memoria semántica** (capa 2, 12 hechos vía `memory_store`, 768-dim,
  recall por similitud verificado). Ver F1 y F1b.
- La carpeta de trabajo real de OpenFang vive en WSL (`/root/.openfang/`); estos archivos
  son la **fuente versionada** que se despliega allí con `scripts/02-deploy-agent.sh`.

## Verificación contra upstream (jun 2026)

Estado del proyecto OpenFang revisado contra su repo oficial
([RightNow-AI/openfang](https://github.com/RightNow-AI/openfang)) el **3 jun 2026**:

- **Versión vigente: `v0.6.9` (12 may 2026) — sigue siendo la última.** Es la que tenemos
  fijada. **No actualizar antes de la sustentación** (pre-1.0, breaking changes entre minors).
  Que sea la última valida la decisión: no estamos atrasados.
- **Memoria — resuelto (3-4 jun 2026).** La doc oficial
  ([`architecture.md`](https://github.com/RightNow-AI/openfang/blob/main/docs/architecture.md))
  describe una **memoria de 6 capas**, incluida **Semantic Search por embeddings** (capa 2).
  **OpenFang SÍ tiene vector store semántico** (embeddings de 768-dim, verificado en
  `openfang.db`). La capa se puebla **vía agent-driven** (`memory_store` del agente, no por
  CLI `ingest` ni REST — esos no existen). `openfang migrate --from langchain` resultó ser un
  stub en v0.6.9. La **Vía B** (`04-cargar-memoria-semantica.sh`, 12 hechos) está
  **verificada**: recall semántico persistente tras reinicio del daemon. Detalle en
  [`docs/F1b-memoria-semantica.md`](docs/F1b-memoria-semantica.md).
- **Gotcha de Hands sigue vigente.** Confirmado contra el changelog: **no** existe `hand uninstall`
  ni `hand install --force` en 0.6.x. Para cambiar una Hand registrada hay que resetear
  `openfang.db` (ver [`docs/F2-hands.md`](docs/F2-hands.md) §7). El nuevo
  `DELETE /api/agents/{id}/uninstall` (v0.6.7) es para **agentes conversacionales**, no para Hands.

### Novedades 0.6.x que NO adoptamos (y por qué)

| Novedad upstream | Versión | Decisión |
|------------------|---------|----------|
| `OLLAMA_HOST` como env override | v0.6.8 | **No migrar para la demo.** Nuestro cableado actual (`base_url=…/v1`) funciona; cambiarlo ahora es riesgo sin upside. Anotado como mejora opcional post-sustentación. |
| Telegram `message_thread_id` routing por tópico | v0.6.8 | No aplica: un solo agente, un solo chat. |
| `DELETE /api/agents/{id}/uninstall` (borrar agente desde chat) | v0.6.7 | No necesario en la demo; útil solo en mantenimiento. No resuelve el gotcha de Hands. |

> Regla del equipo: congelar versión y configuración antes de la sustentación. Estas novedades
> quedan registradas para una iteración posterior, no para tocar el sistema que ya funciona.
