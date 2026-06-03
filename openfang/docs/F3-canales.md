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

### 2.4 Conflicto HTTP 409 por doble daemon (reproducido y resuelto)

Telegram (Bot API) **solo admite un poller `getUpdates` por token**. Si quedan **dos
daemons** de OpenFang vivos a la vez, ambos hacen *long-polling* del mismo bot y Telegram
responde repetidamente `409 Conflict — stale polling session, retrying` → **el bot deja de
responder de forma fiable**.

Causa raíz (reproducida en vivo, jun 2026): `openfang stop` (basado en *pidfile*) resultó
**poco fiable** matando daemons lanzados por `nohup` → en cada reinicio se acumulaba un daemon
huérfano. Diagnóstico: `pgrep -x openfang` mostraba **2** procesos y el log llenándose de 409.

Fix aplicado en `scripts/01-start-daemon.sh` y `scripts/03-switch-provider.sh`: matar por
**nombre del binario** antes de arrancar —

```bash
pkill -9 -x openfang 2>/dev/null || true   # mata el daemon por nombre, no por pidfile
sleep 1
```

⚠️ **No usar** `pkill -f "openfang start"`: ese patrón coincide con el propio script (que
contiene la cadena) y se **auto-mata**, dejando dos daemons o ninguno. Verificación de éxito:
`pgrep -x openfang` debe devolver **1** y `grep -c 409 daemon.log` debe quedar en **0**.

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

## 4. Telegram — canal nativo de OpenFang (procedimiento verificado, funcionando ✅)

> Corrige un supuesto previo: `channel enable` **no** es la vía. La envvar sola deja
> el canal en `Not configured`, y `enable` sobre un canal sin configurar devuelve
> `404` (`POST /api/channels/telegram/enable`). Lo que **configura** el canal es el
> wizard `channel setup`, que persiste `[channels.telegram]` en `config.toml`.

### 4.1 Pasos reales (los que dejaron el bot respondiendo)

```bash
# 1) Token en el env del daemon (NO se commitea — va a ~/.openfang/manuelita.env):
echo 'export TELEGRAM_BOT_TOKEN=123456:ABC...' >> ~/.openfang/manuelita.env
chmod 600 ~/.openfang/manuelita.env

# 2) Configurar el canal. El wizard pide UNA cosa: pegar el token. Es interactivo,
#    pero se puede alimentar por stdin de forma no-interactiva:
source ~/.openfang/manuelita.env
printf '%s\n' "$TELEGRAM_BOT_TOKEN" | openfang channel setup telegram
#  -> escribe [channels.telegram] en config.toml  +  guarda el token en ~/.openfang/.env

# 3) Apuntar el canal a NUESTRO agente (por defecto queda 'assistant', que NO existe
#    porque deshabilitamos los templates). El canal resuelve el agente POR NOMBRE
#    (busca el manifiesto agents/<nombre>/agent.toml), NO por UUID -> usar el nombre,
#    que ademas sobrevive redeploys (el UUID v4 no):
openfang config set channels.telegram.default_agent manuelita-bot

# 4) Reiniciar el daemon (con el token en env) para activar el bridge:
openfang stop; source ~/.openfang/manuelita.env; \
  nohup openfang start > ~/.openfang/daemon.log 2>&1 < /dev/null & disown

# 5) Verificar:
openfang channel list            # telegram -> STATUS "Ready"
grep -i telegram ~/.openfang/daemon.log | tail
#  Esperado en el log:
#    telegram default agent: manuelita-bot (561b8865-...)
#    Telegram bot @<tu_bot> connected
#    Telegram: cleared webhook, polling mode active
#    telegram channel bridge started
```

### 4.2 Binding canal↔agente — RESUELTO

El canal busca el agente por **nombre** (ruta del manifiesto), confirmado por el log:
`could not find or spawn default agent 'assistant': Manifest not found:
/root/.openfang/agents/assistant/agent.toml`. Por eso `default_agent = "manuelita-bot"`
(nombre) es correcto y estable. Si quedara mal, el síntoma es ese WARN en el log y el
bot no responde aunque Telegram esté conectado.

### 4.3 Gotcha de reinicio (cuota) — verificado

Cada `openfang start` **revive los Hands built-in como `Active`** con **instance UUIDs
nuevos**; el estado `Paused` **no persiste** entre reinicios. → Pausar los Hands
**después del último arranque** del daemon, justo antes de la demo, no antes.

## 5. Cuota — disciplina para la demo

- Los Hands se dejan **`Paused`** para no quemar cuota Gemini en segundo plano, y
  **se re-pausan tras el último reinicio** (ver 4.3). Se reanudan solo para mostrarlos.
- Telegram + WhatsApp comparten el mismo `gemini-2.5-flash-lite`. Ensayar el flujo
  completo **días antes**, no el mismo día, para no agotar el free tier en pruebas.

## 6. Estado

| Canal | Estado |
|-------|--------|
| Telegram (nativo) | ✅ **Funcionando** — bot `@Cortana_Juanito0312_bot` conectado, ruteando a `manuelita-bot`. Falta prueba en vivo desde un teléfono. |
| WhatsApp (gateway QR) | Gateway versionado y listo; **pendiente escanear QR** en vivo |

## 7. Próximo paso

F4 — informe técnico unificado (M1+M2+M3) en PDF.
