#!/usr/bin/env bash
# Arranca el daemon de OpenFang con la API key de Gemini cargada.
# Ejecutar dentro de WSL (Ubuntu) como root:  wsl -d Ubuntu -u root -- bash 01-start-daemon.sh
#
# Requisito previo (una sola vez, NO se commitea la key):
#   echo 'export GEMINI_API_KEY=TU_KEY' > ~/.openfang/manuelita.env && chmod 600 ~/.openfang/manuelita.env

OF="${OPENFANG_HOME:-/root/.openfang}"

if [ -f "$OF/manuelita.env" ]; then
  # shellcheck disable=SC1090
  source "$OF/manuelita.env"
fi

# Los Hands built-in (collector, lead) heredan provider=openai de [default_model]
# pero NO su api_key_env -> buscan OPENAI_API_KEY (bug OpenFang v0.6.9). Lo aliasamos
# al de Ollama Cloud (mismo valor) para que booteen sin tocar la DB.
export OPENAI_API_KEY="${OPENAI_API_KEY:-$OLLAMA_API_KEY}"
export OPENAI_BASE_URL="${OPENAI_BASE_URL:-https://ollama.com/v1}"

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "AVISO: GEMINI_API_KEY no definida."
  echo "  Crea $OF/manuelita.env con:  export GEMINI_API_KEY=tu_key"
  echo "  (Sin key, el agente Gemini devolvera errores.)"
fi

# Idempotencia: mata cualquier daemon previo para evitar DOBLE polling de Telegram
# (error 409 Conflict). Se mata por NOMBRE del binario (-x openfang); NO usar
# 'pkill -f "openfang start"' porque ese patron coincide con este mismo script.
pkill -9 -x openfang 2>/dev/null || true
sleep 1

echo "Arrancando OpenFang... dashboard: http://127.0.0.1:4200"
exec "$OF/bin/openfang" start
