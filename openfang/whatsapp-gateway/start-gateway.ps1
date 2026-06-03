# start-gateway.ps1 — Arranca el gateway de WhatsApp (Baileys) apuntando a manuelita-bot.
#
# Por que un launcher y no `node index.js` a secas:
#   El endpoint REST de OpenFang (POST /api/agents/<id>/message) exige el UUID del
#   agente, NO su nombre. Con el nombre devuelve 400 {"error":"Invalid agent ID"}.
#   Ademas el UUID de manuelita-bot es v4 (aleatorio) y CAMBIA cada vez que se
#   redepliega (02-deploy-agent.sh borra openfang.db). Por eso lo leemos en vivo
#   desde WSL en lugar de fijarlo.
#
# Pre-requisitos:
#   - Daemon de OpenFang corriendo en WSL  (bash scripts/01-start-daemon.sh)
#   - WSL en networkingMode=mirrored        (para que Windows alcance 127.0.0.1:4200)
#   - Node >= 18 en Windows
#
# Uso (desde esta carpeta, en PowerShell):
#   .\start-gateway.ps1
# Luego, en otra terminal, dispara el QR:
#   Invoke-RestMethod -Method Post http://127.0.0.1:3009/login/start
#   (el QR tambien se imprime en ASCII en esta terminal: printQRInTerminal=true)
#   Escanealo con WhatsApp -> Dispositivos vinculados.

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

# 1) UUID de manuelita-bot, leido en vivo desde OpenFang (WSL)
$agentLines = wsl -d Ubuntu -u root -- /root/.openfang/bin/openfang agent list
$match = $agentLines | Select-String -SimpleMatch "manuelita-bot" | Select-Object -First 1
if (-not $match) {
  Write-Error "No encuentro 'manuelita-bot'. Verifica que el daemon este arriba (bash scripts/01-start-daemon.sh) y que el agente este desplegado (bash scripts/02-deploy-agent.sh)."
  exit 1
}
$uuid = ($match.Line.Trim() -split '\s+')[0]
if ($uuid -notmatch '^[0-9a-f]{8}-') {
  Write-Error "El primer token de la linea no parece un UUID: '$uuid'. Linea: $($match.Line)"
  exit 1
}
Write-Host "manuelita-bot UUID = $uuid" -ForegroundColor Green

# 2) Dependencias (se reinstalan si faltan; no se commitea node_modules)
if (-not (Test-Path ".\node_modules")) {
  Write-Host "Instalando dependencias (npm install)..." -ForegroundColor Yellow
  npm install
}

# 3) Variables que consume index.js
$env:OPENFANG_DEFAULT_AGENT = $uuid                 # UUID, no el nombre (clave)
$env:OPENFANG_URL           = "http://127.0.0.1:4200"
$env:WHATSAPP_GATEWAY_PORT  = "3009"

Write-Host "Gateway -> agente $uuid en $($env:OPENFANG_URL)  (puerto $($env:WHATSAPP_GATEWAY_PORT))" -ForegroundColor Cyan
node index.js
