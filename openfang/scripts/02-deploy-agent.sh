#!/usr/bin/env bash
# Despliega el agente 'manuelita-bot' en OpenFang (dentro de WSL Ubuntu, como root).
# Copia el manifiesto, deja SOLO este agente, inyecta el corpus y la memoria curada.
# Uso:  wsl -d Ubuntu -u root -- bash 02-deploy-agent.sh
set -e

# Ruta del repo vista desde WSL (ajusta si tu repo esta en otra ruta de Windows):
REPO="${MANUELITA_REPO:-/mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita}"
OF="${OPENFANG_HOME:-/root/.openfang}"
AGENT="manuelita-bot"

echo ">> Repo: $REPO"
echo ">> OpenFang: $OF"

# 1) Manifiesto del agente
mkdir -p "$OF/agents/$AGENT"
cp "$REPO/openfang/agents/$AGENT/agent.toml" "$OF/agents/$AGENT/agent.toml"
echo ">> agent.toml copiado"

# 2) Config de OpenFang (si no existe aun)
if [ ! -f "$OF/config.toml" ]; then
  cp "$REPO/openfang/config/config.example.toml" "$OF/config.toml"
  echo ">> config.toml inicializado desde el ejemplo (revisa el proveedor)"
fi

# 3) Dejar SOLO este agente (mover los demas) y limpiar la DB para forzar recarga
#    (los 30 templates viven en openfang.db; sin borrarla reviven al reiniciar)
#    ⚠️ OJO: borrar openfang.db TAMBIEN borra la memoria KV/semantica del agente.
#       => Tras arrancar, hay que RE-CARGARLA con 04-cargar-memoria-semantica.sh
mkdir -p "$OF/agents_disabled"
for d in "$OF/agents"/*/; do
  n=$(basename "$d")
  if [ "$n" != "$AGENT" ]; then mv "$d" "$OF/agents_disabled/" 2>/dev/null || true; fi
done
rm -f "$OF/data/openfang.db" "$OF/data/openfang.db-shm" "$OF/data/openfang.db-wal"
echo ">> agentes plantilla desactivados + DB limpiada"

# 4) Workspace: corpus del Modulo 1 + MEMORY.md curado
mkdir -p "$OF/workspaces/$AGENT/data"
cp "$REPO/data_processed/markdown/"*.md "$OF/workspaces/$AGENT/data/" 2>/dev/null || true
cp "$REPO/openfang/agents/$AGENT/MEMORY.md" "$OF/workspaces/$AGENT/MEMORY.md"
echo ">> corpus ($(ls "$OF/workspaces/$AGENT/data" | wc -l) archivos) + MEMORY.md desplegados"

echo ""
echo "Listo. Pasos siguientes (EN ORDEN):"
echo "  1) Arranca el daemon:            bash 01-start-daemon.sh"
echo "  2) RE-CARGA la memoria semantica: bash 04-cargar-memoria-semantica.sh"
echo "     (este deploy borro openfang.db -> la memoria KV/semantica quedo vacia)"
echo "(Si es la primera vez y el workspace se regenera, vuelve a correr este script tras el primer arranque.)"
