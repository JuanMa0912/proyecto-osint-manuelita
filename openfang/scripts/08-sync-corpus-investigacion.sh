#!/usr/bin/env bash
# =============================================================================
# 08-sync-corpus-investigacion.sh
# -----------------------------------------------------------------------------
# Puente entre el Hand "investigador-corpus-manuelita" y el corpus del bot.
# Cada Hand escribe en SU PROPIO workspace (sandbox); este script lleva su nota
# de investigacion (investigacion_web_manuelit.md) a:
#   1) el corpus del repo:      data_processed/markdown/   (versionable)
#   2) el workspace del bot:    ~/.openfang/workspaces/manuelita-bot/data/  (live)
# para que el asistente la lea con file_read en la proxima pregunta.
#
# Uso (WSL root):  bash openfang/scripts/08-sync-corpus-investigacion.sh
# Idempotente. No pisa el corpus oficial: solo crea/actualiza el archivo de
# investigacion web (claramente etiquetado como no oficial).
# =============================================================================
set -e
OF="${OPENFANG_HOME:-/root/.openfang}"
REPO="${MANUELITA_REPO:-/mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita}"
NOTE="investigacion_web_manuelit.md"
HAND_AGENT="investigador-corpus-hand"

SRC="$OF/workspaces/$HAND_AGENT/data/$NOTE"
echo ">> buscando la nota del Hand: $SRC"
if [ ! -f "$SRC" ]; then
  # fallback: buscar el archivo en cualquier workspace (por si cambia el nombre del agente)
  ALT=$(find "$OF/workspaces" -maxdepth 3 -name "$NOTE" 2>/dev/null | head -1)
  if [ -n "$ALT" ]; then
    SRC="$ALT"; echo ">> encontrada en: $SRC"
  else
    echo ">> ERROR: el Hand aun no ha generado $NOTE. Corre/activa el Hand primero."
    exit 3
  fi
fi

echo "== (1) -> corpus del repo =="
cp "$SRC" "$REPO/data_processed/markdown/$NOTE"
echo "   $REPO/data_processed/markdown/$NOTE ($(wc -l < "$SRC") lineas)"

echo "== (2) -> workspace VIVO del bot (lectura inmediata) =="
mkdir -p "$OF/workspaces/manuelita-bot/data"
cp "$SRC" "$OF/workspaces/manuelita-bot/data/$NOTE"
echo "   $OF/workspaces/manuelita-bot/data/$NOTE"

echo ""
echo ">> LISTO. El asistente ya puede leer 'data/$NOTE' con file_read."
echo ">> (Opcional) para que quede en el corpus canonico permanente, commitea el .md"
echo "   y vuelve a desplegar con 02-deploy-agent.sh."
