#!/usr/bin/env bash
#
# 05-setup-hands.sh
# -----------------------------------------------------------------------------
# Deja los 4 Hands listos para la demo: reinstala los 2 Hands Custom, activa los 4
# (2 built-in + 2 Custom) y configura el collector quota-safe.
#
# ⚠️ POR QUE ESTE SCRIPT: el Hand Custom (sostenibilidad-manuelita) NO sobrevive ni a un
#    wipe de openfang.db (02-deploy) NI a un simple REINICIO del daemon. Los built-in
#    (collector, lead) reviven solos porque vienen empaquetados en disco; el Custom NO.
#    => Re-corre este script DESPUES de cualquier 'openfang start'/reinicio, y SIEMPRE
#       AL FINAL (despues de 04-cargar-memoria, que reinicia el daemon). Si reinicias
#       luego por cualquier motivo, vuelve a correrlo.
#
# En OpenFang un Hand ES un agente especializado (system_prompt + tools + schedule);
# por eso en la vista de Agentes/Chat los veras como agentes: lead-hand, collector-hand,
# sostenibilidad-hand. Es lo esperado.
#
# Orden completo de despliegue (05 va AL FINAL, tras la carga que reinicia el daemon):
#   02-deploy -> 01-start -> 04-cargar-memoria -> 05-setup-hands -> probar
#
# Uso (en WSL, como root, con el daemon ARRIBA):
#   bash openfang/scripts/05-setup-hands.sh
# -----------------------------------------------------------------------------
set -e
REPO="${MANUELITA_REPO:-/mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita}"
OF=/root/.openfang/bin/openfang

echo ">> reinstalar los 2 Hands Custom (idempotente; si ya estan registrados, no pasa nada)"
"$OF" hand install "$REPO/openfang/hands/sostenibilidad-manuelita" 2>&1 | tail -2 || true
"$OF" hand install "$REPO/openfang/hands/investigador-corpus-manuelita" 2>&1 | tail -2 || true

echo ">> activar los 4 Hands (2 built-in + 2 Custom)"
"$OF" hand activate collector 2>&1 | tail -1 || true
"$OF" hand activate lead 2>&1 | tail -1 || true
"$OF" hand activate sostenibilidad-manuelita 2>&1 | tail -1 || true
"$OF" hand activate investigador-corpus-manuelita 2>&1 | tail -1 || true

echo ">> configurar collector (quota-safe: barrido superficial, semanal)"
"$OF" hand config collector \
  --set target_subject="Manuelita S.A. y el sector agroindustrial (azucar, palma, acuicultura) en Colombia, Peru y Chile" \
  --set focus_area=competitor --set collection_depth=surface \
  --set update_frequency=weekly --set max_sources_per_cycle=10 2>&1 | tail -3 || true

echo ""
echo ">> estado final (deben aparecer 4 Hands activos en gemma3:27b)"
"$OF" hand active 2>&1 | tail -8
echo ""
echo "Listo. Para la demo: muestra el dashboard (Hands -> Active 4). Los Hands corren en"
echo "schedule SEMANAL; para verlos trabajar en vivo, dispara el Custom por mensaje a su agente."
echo "Para no consumir cuota en reposo, puedes pausarlos: openfang hand pause <INSTANCE_UUID>."
