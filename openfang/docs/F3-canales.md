# Fase F3 — Canales (Telegram + WhatsApp)

> Maestría en IA y Ciencia de Datos — Universidad Autónoma de Occidente
> Módulo 3 · Fase F3 · Empresa: Manuelita S.A.

## 1. Objetivo

Exponer el agente `manuelita-bot` en canales de mensajería reales para la **prueba
de fuego** de la sustentación: que el profesor escriba al bot desde su propio teléfono.
El equipo decidió conectar **ambos** canales:

- **Telegram** — canal **principal** (más estable, integración nativa de OpenFang).
- **WhatsApp** — vía **gateway QR** con Baileys (enlaza un WhatsApp **personal**, sin
  la API Cloud de Meta).

## 2. Hallazgo crítico (verificado) — el endpoint REST exige UUID, no nombre

El gateway de WhatsApp reenvía cada mensaje a OpenFang con:

```
POST http://127.0.0.1:4200/api/agents/<AGENTE>/message
```

Prueba empírica contra el daemon (jun 2026, v0.6.9):

| `<AGENTE>` | Resultado |
|------------|-----------|
| `manuelita-bot` (nombre) | `HTTP 400 {"error":"Invalid agent ID"}` |
| `561b8865-...-6af10a62d90b` (UUID) | `HTTP 200` + el bot responde |

**Consecuencia:** el gateway debe arrancar con `OPENFANG_DEFAULT_AGENT=<UUID>`,
nunca con el nombre. Igual que el CLI `openfang message <UUID>`.

### El UUID es frágil — se lee en vivo, no se fija

El UUID de `manuelita-bot` es **v4 (aleatorio)**, y `02-deploy-agent.sh` **borra
`openfang.db`** en cada redeploy → **el UUID cambia**. Por eso el launcher
(`start-gateway.ps1`) lo lee dinámicamente desde WSL en vez de hardcodearlo:

```powershell
$agentLines = wsl -d Ubuntu -u root -- /root/.openfang/bin/openfang agent list
$uuid = (($agentLines | Select-String -SimpleMatch "manuelita-bot").Line -split '\s+')[0]
```

(Los Hands sí usan UUID v5 determinista; solo el agente conversacional es v4.)

## 3. WhatsApp — gateway Baileys (QR)

### 3.1 Qué es

`openfang/whatsapp-gateway/` es un proceso Node que:
- Levanta una sesión de WhatsApp Web con `@whiskeysockets/baileys` (no usa la API de Meta).
- Muestra un **QR** que se escanea desde *WhatsApp → Dispositivos vinculados*.
- Reenvía mensajes entrantes a OpenFang (`/api/agents/<UUID>/message`) y responde
  con `data.response`.
- Escucha en `127.0.0.1:3009`.

Archivos versionados (reproducibles): `index.js`, `package.json`, `package-lock.json`,
`start-gateway.ps1`. **No** se versionan `node_modules/` ni `auth_store/` (credenciales
de la sesión vinculada — ver `.gitignore`).

### 3.2 Cómo levantarlo

Requisitos: daemon OpenFang arriba en WSL, WSL en `networkingMode=mirrored`
(para que Windows alcance `127.0.0.1:4200` de WSL), Node ≥ 18 en Windows.

```powershell
cd openfang\whatsapp-gateway
.\start-gateway.ps1                 # lee el UUID, instala deps si faltan, arranca el gateway
```

En otra terminal, dispara el flujo de QR:

```powershell
Invoke-RestMethod -Method Post http://127.0.0.1:3009/login/start
```

El QR aparece **en ASCII en la terminal del gateway** (`printQRInTerminal=true`) y
también como `qr_data_url` (PNG base64) en la respuesta JSON. Se escanea con el
teléfono. Una vez `connected`, las credenciales quedan en `auth_store/` y reconecta
solo en arranques siguientes.

### 3.3 Endpoints del gateway

| Método | Ruta | Uso |
|--------|------|-----|
| `POST` | `/login/start` | Inicia sesión y devuelve el QR |
| `GET`  | `/login/status` | Estado de conexión |
| `POST` | `/message/send` | Envío saliente `{to, text}` |
| `GET`  | `/health` | Healthcheck |

### 3.4 Qué necesita del usuario

**Escanear el QR** con el WhatsApp personal. Es una acción manual ineludible (vincula
el dispositivo). El resto está automatizado en el launcher.

## 4. Telegram — canal nativo de OpenFang

### 4.1 Vía no-interactiva (la que usamos)

`openfang channel list` muestra que Telegram se detecta por la variable de entorno
**`TELEGRAM_BOT_TOKEN`** (estado `Not configured` hasta que exista). Hay un wizard
interactivo (`openfang channel setup telegram`) pero **no** es necesario: basta la
env var + `enable`.

Pasos (cuando llegue el token de **@BotFather**):

```bash
# 1) Token en el env del daemon (NO se commitea):
echo 'export TELEGRAM_BOT_TOKEN=123456:ABC...' >> ~/.openfang/manuelita.env

# 2) Reiniciar el daemon para que lo tome:
bash scripts/01-start-daemon.sh

# 3) Activar el canal y probar:
openfang channel enable telegram
openfang channel list            # debe pasar a configurado/enabled
openfang channel test telegram   # envía un mensaje de prueba
```

### 4.2 Incógnita abierta (a resolver en vivo, no inventar)

El **binding canal↔agente** no está documentado: falta confirmar a qué agente rutea
Telegram por defecto y cómo forzar que sea `manuelita-bot` (vs. el `assistant` por
defecto). Se verifica al cablear el token real; si rutea al agente equivocado, se
ajusta en `config.toml` o con la opción del `channel setup`. **No se asume resuelto.**

## 5. Cuota — disciplina para la demo

- Los **3 Hands quedan `Paused`** (ver F2) para no quemar cuota Gemini en segundo plano.
  Se reanudan solo para mostrarlos.
- Telegram + WhatsApp comparten el mismo `gemini-2.5-flash-lite`. Ensayar el flujo
  completo **días antes**, no el mismo día, para no agotar el free tier en pruebas.

## 6. Estado

| Canal | Estado |
|-------|--------|
| WhatsApp (gateway QR) | Gateway versionado y listo; **pendiente escanear QR** en vivo |
| Telegram (nativo) | Vía verificada; **pendiente el token de @BotFather** |

## 7. Próximo paso

F4 — informe técnico unificado (M1+M2+M3) en PDF.
