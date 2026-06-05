#!/usr/bin/env bash
# =============================================================================
# levantar-todo.sh — Levanta TODO el sistema OpenFang con UN solo comando.
# =============================================================================
# Escenario A (el normal): la DB (openfang.db) esta intacta, solo se cayo el
# proceso (reiniciaste el PC / cerraste WSL). Arranca el daemon + re-activa los
# 3 Hands + verifica. **NO wipea la DB ni recarga memoria -> NO gasta cuota.**
#
# (Para estado LIMPIO tras cambiar agent.toml/corpus, usa el orden completo:
#  02-deploy -> 04-cargar-memoria -> 05-setup-hands. Eso SI gasta cuota.)
#
# USO (en WSL como root). Por el CRLF de Windows, correlo SIEMPRE asi:
#   tr -d '\r' < /mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita/openfang/scripts/levantar-todo.sh | bash
# =============================================================================
set -e
REPO="${MANUELITA_REPO:-/mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita}"
SC="$REPO/openfang/scripts"
OF=/root/.openfang/bin/openfang

echo "== 1) Arrancando el daemon (mata cualquier previo para evitar el 409) =="
pkill -9 -x openfang 2>/dev/null || true
sleep 1
[ -f ~/.openfang/manuelita.env ] && source ~/.openfang/manuelita.env || \
  echo "   AVISO: no encontre ~/.openfang/manuelita.env (faltarian las API keys)"
nohup "$OF" start > ~/.openfang/daemon.log 2>&1 < /dev/null & disown
sleep 7
echo -n "   daemon_procs (debe ser 1) = "; pgrep -x openfang | wc -l

echo ""
echo "== 2) Re-activando los 3 Hands (el Custom NO sobrevive al reinicio) =="
tr -d '\r' < "$SC/05-setup-hands.sh" | bash

echo ""
echo "== 3) Estado final =="
tr -d '\r' < "$SC/00-estado.sh" | bash

UUID=$("$OF" agent list 2>/dev/null | grep -i manuelita-bot | awk '{print $1}')
echo ""
echo "============================================================"
echo ">> LISTO si arriba ves: daemon=1 · 3 Hands Active · Telegram Ready."
echo ">> Probar por CLI:  openfang message $UUID 'cual es el NIT de Manuelita?'"
echo ">> Probar por Telegram: escribe a @Cortana_Juanito0312_bot"
echo ">> Apagar para cuidar cuota:  pkill -9 -x openfang"
echo "============================================================"
