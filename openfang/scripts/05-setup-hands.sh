#!/usr/bin/env bash
#
# 05-setup-hands.sh
# -----------------------------------------------------------------------------
# Deja los 3 Hands listos para la demo: reinstala el Hand Custom, activa los 3
# (2 built-in + 1 Custom) y configura el collector quota-safe.
#
# ⚠️ POR QUE ESTE SCRIPT: 02-deploy-agent.sh borra openfang.db -> eso DES-REGISTRA
#    el Hand Custom (sostenibilidad-manuelita). Los built-in (collector, lead) reviven
#    solos al arrancar el daemon, pero el Custom NO. Hay que re-instalarlo aqui.
#
# En OpenFang un Hand ES un agente especializado (system_prompt + tools + schedule);
# por eso en la vista de Agentes/Chat los veras como agentes: lead-hand, collector-hand,
# sostenibilidad-hand. Es lo esperado.
#
# Orden completo de despliegue:
#   02-deploy -> 01-start -> 05-setup-hands -> 04-cargar-memoria -> probar
#
# Uso (en WSL, como root, con el daemon ARRIBA):
#   bash openfang/scripts/05-setup-hands.sh
# -----------------------------------------------------------------------------
set -e
REPO="${MANUELITA_REPO:-/mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita}"
OF=/root/.openfang/bin/openfang

echo ">> reinstalar el Hand Custom (idempotente; si ya esta registrado, no pasa nada)"
"$OF" hand install "$REPO/openfang/hands/sostenibilidad-manuelita" 2>&1 | tail -2 || true

echo ">> activar los 3 Hands"
"$OF" hand activate collector 2>&1 | tail -1 || true
"$OF" hand activate lead 2>&1 | tail -1 || true
"$OF" hand activate sostenibilidad-manuelita 2>&1 | tail -1 || true

echo ">> configurar collector (quota-safe: barrido superficial, semanal)"
"$OF" hand config collector \
  --set target_subject="Manuelita S.A. y el sector agroindustrial (azucar, palma, acuicultura) en Colombia, Peru y Chile" \
  --set focus_area=competitor --set collection_depth=surface \
  --set update_frequency=weekly --set max_sources_per_cycle=10 2>&1 | tail -3 || true

echo ""
echo ">> estado final (deben aparecer 3 Hands activos en gemma3:27b)"
"$OF" hand active 2>&1 | tail -8
echo ""
echo "Listo. Para la demo: muestra el dashboard (Hands -> Active 3). Los Hands corren en"
echo "schedule SEMANAL; para verlos trabajar en vivo, dispara el Custom por mensaje a su agente."
echo "Para no consumir cuota en reposo, puedes pausarlos: openfang hand pause <INSTANCE_UUID>."
