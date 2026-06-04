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
│   ├── F1-agente-manuelita.md         # Fase F1: el agente, prompt y pruebas
│   ├── F2-hands.md                    # Fase F2: operaciones autónomas (Hands)
│   └── F3-canales.md                  # Fase F3: canales Telegram + WhatsApp
├── agents/manuelita-bot/
│   ├── agent.toml                     # manifiesto: persona + system_prompt + tools
│   └── MEMORY.md                      # hechos curados de Manuelita
├── hands/sostenibilidad-manuelita/    # Custom Hand (HAND.toml + SKILL.md)
├── whatsapp-gateway/                  # Gateway QR (Baileys) → manuelita-bot (F3)
│   ├── index.js · package.json        # gateway Node (node_modules y auth_store NO se versionan)
│   └── start-gateway.ps1              # launcher: lee el UUID del agente en vivo y arranca
├── config/
│   └── config.example.toml            # config de OpenFang (Gemini / Ollama)
└── scripts/
    ├── 01-start-daemon.sh             # arranca el daemon con la API key
    └── 02-deploy-agent.sh             # despliega manuelita-bot (manifiesto + corpus + memoria)
```

## Quick start

Requisitos: Windows 11 + WSL2 con Ubuntu y OpenFang ya instalado (ver
[`docs/F0-spike-infraestructura.md`](docs/F0-spike-infraestructura.md)). Operar dentro
de WSL como root: `wsl -d Ubuntu -u root`.

1. **Key local** (una vez; NO se commitea):
   ```bash
   echo 'export GEMINI_API_KEY=TU_KEY' > ~/.openfang/manuelita.env && chmod 600 ~/.openfang/manuelita.env
   ```
2. **Desplegar el agente:**
   ```bash
   bash scripts/02-deploy-agent.sh
   ```
3. **Arrancar:**
   ```bash
   bash scripts/01-start-daemon.sh        # dashboard: http://127.0.0.1:4200
   ```
4. **Probar:**
   ```bash
   openfang agent list                    # copia el UUID de manuelita-bot
   openfang message <UUID> "¿Cuál es el NIT de Manuelita y quién es su presidente?"
   ```

> Detalles, comandos y solución de problemas (gotchas) en `docs/`.

## Estado del proyecto (junio 2026)

| Fase | Descripción | Estado |
|------|-------------|--------|
| F0 | Infraestructura OpenFang en WSL2 (instalación, networking, proveedores) | ✅ Validada |
| F1 | Agente `manuelita-bot`: persona + corpus + anti-alucinación proporcional | ✅ Responde (~3 s vía Gemini) |
| F2 | Hands: 2 built-in (`collector`, `lead`) + 1 Custom (`sostenibilidad-manuelita`) | ✅ Configuradas y pausadas |
| F3 | Canales: Telegram (nativo, **funcionando** → `manuelita-bot`) + WhatsApp (gateway QR versionado) | ✅ Telegram vivo y **ensayado en vivo desde teléfono real** · 🟡 WhatsApp listo, falta escanear QR |
| F4 | Informe técnico unificado | 🟡 Markdown completo y depurado (`reports/informe_final.md`, `0 POR VERIFICAR`) · falta solo exportar a PDF |
| F5 | Análisis t-SNE de conversaciones (opcional) | ⏳ Pendiente (opcional avanzado) |

## Notas

- **Proveedor LLM:** demo con Gemini `gemini-2.5-flash-lite` (el `gemini-2.0-flash`
  quedó con cuota free tier en 0). Modo soberanía con Ollama local documentado en F0
  (cableado, pero lento sin GPU).
- **Conocimiento:** OpenFang no hace RAG por embeddings; el agente usa su `system_prompt`
  + archivos del workspace (`file_read`) + memoria KV. Ver F1.
- La carpeta de trabajo real de OpenFang vive en WSL (`/root/.openfang/`); estos archivos
  son la **fuente versionada** que se despliega allí con `scripts/02-deploy-agent.sh`.

## Verificación contra upstream (jun 2026)

Estado del proyecto OpenFang revisado contra su repo oficial
([RightNow-AI/openfang](https://github.com/RightNow-AI/openfang)) el **3 jun 2026**:

- **Versión vigente: `v0.6.9` (12 may 2026) — sigue siendo la última.** Es la que tenemos
  fijada. **No actualizar antes de la sustentación** (pre-1.0, breaking changes entre minors).
  Que sea la última valida la decisión: no estamos atrasados.
- **El modelo de conocimiento no cambió.** No hay novedades de RAG / embeddings / vector store /
  ingesta semántica en el rango `0.6.5 → 0.6.9`. Esto **ratifica** lo documentado en
  [`docs/F1-agente-manuelita.md`](docs/F1-agente-manuelita.md): OpenFang hace **recuperación
  agéntica por archivos + KV**, no RAG por embeddings. El informe describe esto de forma honesta.
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
