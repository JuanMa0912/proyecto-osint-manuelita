#!/usr/bin/env bash
# =============================================================================
# 06-whatsapp-gateway.sh — Prepara el gateway de WhatsApp (modo QR / WhatsApp Web).
# =============================================================================
# Contexto: con [channels.whatsapp] mode="web" en config.toml y Node>=18, el binario
# auto-extrae el gateway a ~/.openfang/whatsapp-gateway y corre 'npm install' al arrancar.
# PERO ese install se cuelga/corrompe por dos motivos (verificado jun 2026, v0.6.9):
#   1) Deps OPCIONALES nativas (sharp/jimp...) que necesitan compilador (make/gcc ausentes).
#   2) Doble 'npm install' simultaneo (el del daemon + uno manual) que se pisan -> baileys
#      queda a medias y el gateway crashea con "Cannot find package baileys".
# Solucion: con el daemon APAGADO, un UNICO install con --omit=optional (sin nativas).
#
# Requisito: Node.js >=18. Instalar (una vez) con NodeSource:
#   curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
#
# Uso (WSL root):  tr -d '\r' < .../openfang/scripts/06-whatsapp-gateway.sh | bash
# Luego: reinicia el daemon (levantar-todo.sh) y abre el dashboard -> Channels -> WhatsApp
#        para ver el QR; escanealo con el telefono (WhatsApp -> Dispositivos vinculados).
# =============================================================================
set -e
GW="${OPENFANG_HOME:-/root/.openfang}/whatsapp-gateway"

command -v node >/dev/null 2>&1 || { echo "ERROR: Node no instalado. Instala Node>=18 (NodeSource)."; exit 2; }
echo "Node $(node --version) | npm $(npm --version)"

if [ ! -d "$GW" ]; then
  echo "El gateway aun no existe en $GW."
  echo "-> Arranca el daemon UNA vez con [channels.whatsapp] en config.toml para que lo extraiga,"
  echo "   luego re-corre este script."
  exit 3
fi

# Mata cualquier install en curso para evitar el doble-install que corrompe baileys.
pkill -9 -f 'npm install' 2>/dev/null || true
sleep 1
cd "$GW"
rm -rf node_modules package-lock.json
echo ">> Instalando deps del gateway (--omit=optional para saltar nativas pesadas)..."
npm install --omit=optional --no-audit --no-fund --no-progress
echo ">> Deps OK. Verificando baileys:"
ls node_modules/@whiskeysockets/baileys/ | head -3
echo ""
echo "LISTO. Ahora: reinicia el daemon (levantar-todo.sh) y abre el dashboard"
echo "(http://127.0.0.1:4200) -> Channels -> WhatsApp para escanear el QR."
