#!/usr/bin/env bash
#
# 04-cargar-memoria-semantica.sh
# -----------------------------------------------------------------------------
# Puebla la MEMORIA SEMANTICA de OpenFang (capa 2 "Semantic Search") del agente
# manuelita-bot, de forma agent-driven: por cada hecho clave envia una instruccion
# memory_store. Verificado: el agente recupera estos hechos por SIMILITUD de
# significado y de forma PERSISTENTE (sobrevive a reinicio del daemon).
#
# ⚠️ IMPORTANTE: 02-deploy-agent.sh BORRA openfang.db -> tambien borra esta memoria.
#    => Ejecutar ESTE script DESPUES de cada despliegue (y antes de la demo).
#
# Cuota: cada hecho = 1 llamada al LLM (~pocos miles de tokens). Correr UNA vez,
#        fuera de horario de demo. Requiere ~/.openfang/manuelita.env con la key.
#
# Uso (en WSL, como root):
#   bash openfang/scripts/04-cargar-memoria-semantica.sh
# -----------------------------------------------------------------------------
set -e
OF=/root/.openfang/bin/openfang

# Hechos nucleo de Manuelita (alineados con DATOS NUCLEO del agent.toml y el JSON estructurado)
FACTS=(
  "Manuelita S.A. tiene NIT 891.300.241, fue fundada en 1864 y su sede principal esta en Palmira, Valle del Cauca, Colombia, con centro corporativo en Cali."
  "El presidente de Manuelita S.A. es Harold Eder."
  "Manuelita tiene operaciones en 3 paises: Colombia, Peru y Chile."
  "Manuelita exporta y vende sus productos al exterior a 49 paises (exportaciones internacionales: 49 paises de destino)."
  "Manuelita tiene 4 plataformas de negocio: azucar de cana, palma de aceite, acuicultura, y frutas y hortalizas."
  "Manuelita tiene 7 unidades de negocio: Manuelita Azucar y Energia, Agroindustrial Laredo, Manuelita Aceites y Energia, Palmar de Altamira, Manuelita Acuicultura, Oceanos, y Manuelita Frutas y Hortalizas."
  "Manuelita tiene aproximadamente 7.971 colaboradores."
  "En 2023 Manuelita tuvo ingresos por 1.043.562 millones de COP, un EBITDA de 369.380 millones de COP con margen de 35,4 por ciento, y una utilidad neta de 78.153 millones de COP."
  "Las metas de sostenibilidad de Manuelita son reducir el 70 por ciento de emisiones de Alcances 1 y 2 al ano 2030, y alcanzar neutralidad de carbono al ano 2040."
  "Manuelita produce cerca de 487.000 toneladas de azucar al ano y unos 275 millones de litros de bioetanol al ano, con mas de 160 anos de trayectoria."
  "Manuelita beneficia a mas de 4.000 familias de empleados y comunidades vecinas."
  "Manuelita cuenta con certificaciones de sostenibilidad: RSPO, HACCP, ASC y GRI. Su actividad principal (CIIU C1071) es la elaboracion y refinacion de azucar."
)

echo "=== (re)arranque idempotente del daemon ==="
pkill -9 -x openfang 2>/dev/null || true
sleep 1
source ~/.openfang/manuelita.env
nohup "$OF" start > ~/.openfang/daemon.log 2>&1 < /dev/null & disown
sleep 6
echo -n "daemon_procs="; pgrep -x openfang | wc -l

UUID=$("$OF" agent list 2>/dev/null | grep -i manuelita-bot | awk '{print $1}')
if [ -z "$UUID" ]; then echo "ERROR: no se encontro manuelita-bot"; exit 4; fi
echo "agente UUID=$UUID"

# ⚠️ CUOTA: cada mensaje dispara 2-3 iteraciones del modelo. Sin pausa entre hechos se
#    revienta el limite POR MINUTO (RPM) de Gemini free tier -> 429 y el agente se atasca.
#    SLEEP_BETWEEN espacia las llamadas para mantenerse bajo el RPM. Subelo si ves 429.
SLEEP_BETWEEN="${SLEEP_BETWEEN:-10}"
echo "=== cargando ${#FACTS[@]} hechos a memoria semantica (memory_store), pausa ${SLEEP_BETWEEN}s entre cada uno ==="
i=0
for f in "${FACTS[@]}"; do
  i=$((i+1))
  echo "--- [$i/${#FACTS[@]}] $f"
  "$OF" message "$UUID" "Usa la herramienta memory_store para guardar EXACTAMENTE este hecho de Manuelita, sin alterarlo: $f" 2>&1 | tail -3
  sleep "$SLEEP_BETWEEN"
done

echo "=== verificacion: recall semantico (consulta reformulada) ==="
"$OF" message "$UUID" "Segun tu memoria, cuantas familias beneficia la empresa y a cuantos paises le vende sus productos al exterior?" 2>&1 | tail -6
echo "=== FIN — memoria semantica poblada ==="
