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

if [ -z "${GEMINI_API_KEY:-}" ]; then
  echo "AVISO: GEMINI_API_KEY no definida."
  echo "  Crea $OF/manuelita.env con:  export GEMINI_API_KEY=tu_key"
  echo "  (Sin key, el agente Gemini devolvera errores.)"
fi

echo "Arrancando OpenFang... dashboard: http://127.0.0.1:4200"
exec "$OF/bin/openfang" start
