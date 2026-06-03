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
│   └── F2-hands.md                    # Fase F2: operaciones autónomas (Hands)
├── agents/manuelita-bot/
│   ├── agent.toml                     # manifiesto: persona + system_prompt + tools
│   └── MEMORY.md                      # hechos curados de Manuelita
├── hands/sostenibilidad-manuelita/    # Custom Hand (HAND.toml + SKILL.md)
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
| F3 | Conectar Telegram (BotFather) para la demo en vivo | ⏳ Pendiente |
| F4 | Informe técnico unificado | ⏳ Pendiente |
| F5 | Análisis t-SNE de conversaciones (opcional) | ⏳ Pendiente |

## Notas

- **Proveedor LLM:** demo con Gemini `gemini-2.5-flash-lite` (el `gemini-2.0-flash`
  quedó con cuota free tier en 0). Modo soberanía con Ollama local documentado en F0
  (cableado, pero lento sin GPU).
- **Conocimiento:** OpenFang no hace RAG por embeddings; el agente usa su `system_prompt`
  + archivos del workspace (`file_read`) + memoria KV. Ver F1.
- La carpeta de trabajo real de OpenFang vive en WSL (`/root/.openfang/`); estos archivos
  son la **fuente versionada** que se despliega allí con `scripts/02-deploy-agent.sh`.
