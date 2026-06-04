#!/usr/bin/env bash
# Cambia el proveedor LLM de manuelita-bot: Gemini (nube) <-> Ollama (local / soberania de datos).
# Demuestra el "motor LLM intercambiable" del Modulo 3 sin reescribir el agente.
#
# Uso (dentro de WSL, como root):
#   bash 03-switch-provider.sh gemini
#   bash 03-switch-provider.sh ollama [modelo]   # modelo por defecto llama3.2:3b
#                                                # usa llama3.2:1b para mas velocidad sin GPU
#
# OJO: Ollama SIN GPU es lento (>1-2 min con 3b). Para la demo en vivo conviene
# dejar Gemini; Ollama se usa para DEMOSTRAR la soberania de datos (idealmente con 1b).
set -e
OF_BIN=/root/.openfang/bin/openfang
AGENT_TOML=/root/.openfang/agents/manuelita-bot/agent.toml
ENV_FILE=/root/.openfang/manuelita.env
MODE="${1:-}"
MODEL_ARG="${2:-}"

case "$MODE" in
  gemini) PROVIDER=gemini; MODEL="${MODEL_ARG:-gemini-2.5-flash}" ;;
  ollama) PROVIDER=ollama; MODEL="${MODEL_ARG:-llama3.2:3b}" ;;
  *) echo "Uso: $0 [gemini|ollama] [modelo]"; exit 1 ;;
esac

# Edita SOLO el bloque [model] (no el [[fallback_models]]) con python (TOML-aware y robusto).
python3 - "$AGENT_TOML" "$PROVIDER" "$MODEL" <<'PY'
import sys, re
path, provider, model = sys.argv[1:4]
t = open(path, encoding='utf-8').read()
def repl(m):
    b = m.group(0)
    b = re.sub(r'(?m)^\s*provider\s*=.*$', f'provider = "{provider}"', b, count=1)
    b = re.sub(r'(?m)^\s*model\s*=.*$',    f'model = "{model}"',       b, count=1)
    return b
t = re.sub(r'(?s)\[model\].*?(?=\n\[)', repl, t, count=1)
open(path, 'w', encoding='utf-8').write(t)
print(f"manuelita-bot -> provider={provider}, model={model}")
PY

echo ">> Reiniciando daemon para aplicar el cambio..."
# Mata por NOMBRE del binario (-x openfang). NO uses 'pkill -f "openfang start"':
# ese patron coincide con este propio script (contiene la cadena) y se auto-mata,
# dejando dos daemons o ninguno. 'openfang stop' por pidfile resulto poco fiable
# con daemons lanzados por nohup -> se acumulaban (Telegram 409 por doble polling).
pkill -9 -x openfang 2>/dev/null || true
sleep 2
# shellcheck disable=SC1090
[ -f "$ENV_FILE" ] && source "$ENV_FILE"
nohup "$OF_BIN" start > /root/.openfang/daemon.log 2>&1 < /dev/null & disown
sleep 9
echo ">> Estado del agente:"
"$OF_BIN" status 2>/dev/null | grep -i 'manuelita-bot' || true
echo ">> Recuerda re-pausar los Hands tras el reinicio (su estado no persiste)."
