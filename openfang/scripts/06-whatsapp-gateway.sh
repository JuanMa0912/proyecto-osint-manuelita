#!/usr/bin/env bash
# =============================================================================
# 06-whatsapp-gateway.sh — Setup COMPLETO y reproducible del gateway WhatsApp (QR/web).
# =============================================================================
# Aplica TODO lo que costo descubrir (jun 2026, OpenFang v0.6.9) para que WhatsApp
# RESPONDA de verdad. Con [channels.whatsapp] mode="web" en config.toml y Node>=18, el
# binario auto-extrae el gateway a ~/.openfang/whatsapp-gateway al arrancar; este script
# lo deja FUNCIONAL resolviendo los 4 problemas que encontramos:
#
#   1) npm install SE CUELGA: por deps OPCIONALES nativas (sin compilador make/gcc) y por
#      DOBLE install simultaneo (el del daemon + uno manual) -> baileys queda a medias.
#      Fix: daemon apagado + UN install --omit=optional (termina en ~10s).
#   2) HANDSHAKE nunca completa (fetchProps -> "Timed Out" 408) con baileys 6.x: el socket
#      conecta pero no inicializa, no descifra ni responde.
#      Fix: subir a baileys 7.0.0-rc13 (alineado al protocolo actual de WhatsApp).
#   3) RUTEO: el gateway postea POST /api/agents/<default_agent>/message; la API EXIGE el
#      UUID, no el nombre (con el nombre da 400 "Invalid agent ID").
#      Fix: poner el UUID del agente en default_agent del canal whatsapp.
#   4) ENTREGA: con direccionamiento LID, el gateway respondia a <lid>@s.whatsapp.net
#      (numero inexistente) -> "Replied" pero no llega. Fix: parche en index.js para
#      responder al numero real (msg.key.remoteJidAlt) cuando el msg viene en @lid.
#
# Uso (WSL root, daemon idealmente apagado):
#   tr -d '\r' < .../openfang/scripts/06-whatsapp-gateway.sh | bash
# Luego: reinicia (levantar-todo.sh) y abre el dashboard -> Channels -> WhatsApp para el QR.
#
# NOTA multi-dispositivo (importante): el QR vincula el gateway a TU cuenta de WhatsApp
# (es un device mas, como WhatsApp Web). El "bot" vive en TU numero; la prueba real es
# que OTRA persona escriba a tu numero y el gateway responda como Manuelita-Bot.
# =============================================================================
set -e
OF="${OPENFANG_HOME:-/root/.openfang}"
GW="$OF/whatsapp-gateway"
BIN="$OF/bin/openfang"
CFG="$OF/config.toml"

command -v node >/dev/null 2>&1 || { echo "ERROR: instala Node>=18 (NodeSource)."; exit 2; }
echo "Node $(node --version) | npm $(npm --version)"
[ -d "$GW" ] || { echo "Gateway no existe en $GW. Arranca el daemon UNA vez con [channels.whatsapp] en config y re-corre esto."; exit 3; }

# (1)+(2) deps limpias con baileys 7
pkill -9 -f 'npm install' 2>/dev/null || true
sed -i 's#"@whiskeysockets/baileys": *"[^"]*"#"@whiskeysockets/baileys": "7.0.0-rc13"#' "$GW/package.json"
echo ">> baileys fijado a:$(grep baileys "$GW/package.json")"
cd "$GW"
rm -rf node_modules package-lock.json
echo ">> npm install --omit=optional (evita nativas que se cuelgan)..."
npm install --omit=optional --no-audit --no-fund --no-progress
echo ">> instalado: $(grep '"version"' node_modules/@whiskeysockets/baileys/package.json | head -1)"

# (4) parche LID: responder al numero real (remoteJidAlt) cuando el msg viene en @lid
python3 - "$GW/index.js" <<'PY'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
old = "senderJid.replace(/@.*$/, '') + '@s.whatsapp.net'"
new = "(remoteJid.endsWith('@lid') ? (msg.key.remoteJidAlt || remoteJid) : senderJid.replace(/@.*$/, '') + '@s.whatsapp.net')"
if new in s:
    print(">> LID patch: ya estaba aplicado")
elif old in s:
    open(p + ".bak.lid", "w", encoding="utf-8").write(s)
    open(p, "w", encoding="utf-8").write(s.replace(old, new))
    print(">> LID patch aplicado (backup en index.js.bak.lid)")
else:
    print(">> OJO: patron LID no encontrado — revisar index.js a mano (linea del replyJid)")
PY

# (5) parche anti-fuga de tool calls: gemma3 a veces escribe ```tool_code
#     [memory_store(...)]``` como TEXTO visible en su respuesta. Este parche inserta
#     stripToolArtifacts() y lo aplica en los 2 envios -> WhatsApp nunca ve esos bloques.
python3 - "$GW/index.js" <<'PY'
import sys
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
if "stripToolArtifacts" in s:
    print(">> toolstrip: ya estaba aplicado")
else:
    FUNC = r'''
function stripToolArtifacts(s) {
  if (typeof s !== 'string') return s;
  let out = s;
  out = out.replace(/```[^\n`]*\n?[\s\S]*?```/g, function (m) {
    return /(memory_store|memory_recall|file_read|file_list|web_[a-z_]+|shell_exec|tool_code)/i.test(m) ? '' : m;
  });
  out = out.replace(/^[ \t]*\[?[ \t]*(?:memory_store|memory_recall|file_read|file_list|web_[a-z_]+|shell_exec)[ \t]*\([\s\S]*?\)[ \t]*\]?[ \t]*$/gim, '');
  out = out.replace(/^[ \t]*tool_code[ \t]*$/gim, '');
  out = out.replace(/[,;]?\s*(?:disponibles?\s+en|que\s+se\s+encuentran?\s+en|seg[uú]n\s+el\s+archivo|en\s+el\s+archivo|del\s+archivo|disponibles?|en|de)\s+`?\bdata\/[\w./-]+\.md`?/gi, '');
  out = out.replace(/`?\bdata\/[\w./-]+\.md`?/gi, '');
  out = out.replace(/\.?\s*Esta informaci[oó]n proviene de (?:los?\s+)?DATOS\s+N[UÚ]CLEO\.?/gi, '.');
  out = out.replace(/\bDATOS\s+N[UÚ]CLEO\b/gi, 'la información corporativa de Manuelita');
  out = out.replace(/[ \t]+([,.;:])/g, '$1').replace(/[ \t]{2,}/g, ' ').replace(/\n{3,}/g, '\n\n').trim();
  if (!out) out = 'Listo.';
  return out;
}
'''
    anchor = "async function sendMessage(to, text) {"
    if anchor in s:
        orig = s
        s = s.replace(anchor, FUNC.strip() + "\n\n" + anchor, 1)
        s = s.replace("{ text: response }", "{ text: stripToolArtifacts(response) }")
        s = s.replace("await sock.sendMessage(jid, { text });", "await sock.sendMessage(jid, { text: stripToolArtifacts(text) });")
        open(p + ".bak.toolstrip", "w", encoding="utf-8").write(orig)
        open(p, "w", encoding="utf-8").write(s)
        print(">> toolstrip aplicado (backup en index.js.bak.toolstrip)")
    else:
        print(">> OJO: anchor sendMessage no encontrado para toolstrip")
PY

# (6) anti-quema de tokens: COALESCING con guardia in-flight. El gateway postea
#     directo a /api/agents/<uuid>/message -> NO pasa por el rate-limit del bridge,
#     asi que el control va aqui. Mientras hay una respuesta EN CURSO para un
#     remitente, los mensajes nuevos se ACUMULAN y se contestan en UNA sola llamada
#     al LLM (una rafaga de 5 mensajes = 1 invocacion, no 5). Latencia casi nula
#     para un mensaje suelto (ventana corta COALESCE_MS, def. 1200ms).
python3 - "$GW/index.js" <<'PY'
import sys, re
p = sys.argv[1]; s = open(p, encoding="utf-8").read()
if "enqueueMessage" in s:
    print(">> coalesce: ya estaba aplicado")
else:
    INFRA = r'''// ---------------------------------------------------------------------------
// Coalescing anti-quema de tokens: agrupa mensajes rapidos del MISMO remitente
// en UNA sola llamada al LLM. Mientras hay una respuesta en curso para ese
// remitente, los mensajes nuevos se acumulan y se contestan juntos.
// ---------------------------------------------------------------------------
const COALESCE_MS = parseInt(process.env.WHATSAPP_COALESCE_MS || '1200', 10);
const pendingMsgs = new Map(); // replyJid -> { queue:[], busy:false, ctx }

function enqueueMessage(replyJid, text, ctx) {
  let st = pendingMsgs.get(replyJid);
  if (!st) { st = { queue: [], busy: false, ctx }; pendingMsgs.set(replyJid, st); }
  st.queue.push(text);
  st.ctx = ctx;
  console.log(`[gateway] Buffered from ${ctx.pushName} (${st.queue.length} en cola)`);
  if (!st.busy) processQueue(replyJid);
}

async function processQueue(replyJid) {
  const st = pendingMsgs.get(replyJid);
  if (!st || st.busy) return;
  if (st.queue.length === 0) { pendingMsgs.delete(replyJid); return; }
  st.busy = true;
  await new Promise((r) => setTimeout(r, COALESCE_MS)); // ventana de coalescing
  const batch = st.queue.splice(0);
  const combined = batch.join('\n');
  const { phone, pushName, metadata, isGroup, remoteJid } = st.ctx;
  try {
    const response = await forwardToOpenFang(combined, phone, pushName, metadata);
    if (response && sock) {
      await sock.sendMessage(replyJid, { text: stripToolArtifacts(response) });
      console.log(`[gateway] Replied to ${pushName}${isGroup ? ' in group ' + remoteJid : ''} (lote de ${batch.length})`);
    }
  } catch (err) {
    console.error(`[gateway] Forward/reply failed:`, err.message);
  } finally {
    st.busy = false;
    if (st.queue.length > 0) processQueue(replyJid); // llegaron mas durante la llamada
    else pendingMsgs.delete(replyJid);
  }
}

'''
    anchor = "function forwardToOpenFang("
    pat = re.compile(r"// Forward to OpenFang agent.*?Forward/reply failed:`, err\.message\);\s*\n\s*\}", re.DOTALL)
    repl = ("// Coalescing anti-quema: bufferiza rafagas del mismo remitente; responde una vez.\n"
            "      const replyJid = isGroup ? remoteJid : (remoteJid.endsWith('@lid') ? (msg.key.remoteJidAlt || remoteJid) : senderJid.replace(/@.*$/, '') + '@s.whatsapp.net');\n"
            "      enqueueMessage(replyJid, text, { phone, pushName, metadata, isGroup, remoteJid });")
    if anchor not in s:
        print(">> OJO: anchor forwardToOpenFang no encontrado — coalesce NO aplicado")
    else:
        s2, n = pat.subn(repl, s, count=1)
        if n != 1:
            print(">> OJO: bloque forward+reply no encontrado — coalesce NO aplicado")
        else:
            s2 = s2.replace(anchor, INFRA + anchor, 1)
            open(p + ".bak.coalesce", "w", encoding="utf-8").write(s)
            open(p, "w", encoding="utf-8").write(s2)
            print(">> coalesce aplicado (backup en index.js.bak.coalesce)")
PY

# (3) default_agent del canal whatsapp = UUID (la API exige UUID, no nombre).
#     'agent list' lee la DB y funciona aunque el daemon este abajo.
UUID=$("$BIN" agent list 2>/dev/null | grep -i 'manuelita-bot' | awk '{print $1}' | head -1)
if [ -n "$UUID" ]; then
  # Solo dentro del bloque [channels.whatsapp] (asumido ULTIMO en el config -> rango a EOF).
  sed -i "/\[channels.whatsapp\]/,\$s|^default_agent = \"manuelita-bot\"|default_agent = \"$UUID\"|" "$CFG"
  echo ">> default_agent (whatsapp) = $UUID"
else
  echo ">> AVISO: no pude leer el UUID de manuelita-bot. Pon a mano en [channels.whatsapp]: default_agent = \"<UUID>\""
fi

echo ""
echo "LISTO. Reinicia el daemon (levantar-todo.sh) y abre el dashboard"
echo "(http://127.0.0.1:4200) -> Channels -> WhatsApp para escanear el QR."
echo "Prueba real: que OTRA persona escriba a tu numero -> el gateway responde como Manuelita-Bot."
