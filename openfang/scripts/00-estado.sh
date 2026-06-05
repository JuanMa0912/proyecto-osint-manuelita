#!/usr/bin/env bash
# 00-estado.sh — Chequeo rapido del estado (SOLO LECTURA, no gasta cuota).
# Uso (WSL, root): bash openfang/scripts/00-estado.sh
OF=/root/.openfang/bin/openfang
echo "=== daemon procs [debe ser 1; si es 0 arranca, si es 2 hay conflicto 409] ==="
pgrep -x openfang | wc -l
echo "=== agentes [manuelita-bot + lead-hand + collector-hand + sostenibilidad-hand, MODEL=gemma3:27b] ==="
"$OF" agent list 2>/dev/null | tail -6
echo "=== hands activos [deben ser 3] ==="
"$OF" hand active 2>/dev/null | tail -5
echo "=== canal telegram [debe decir Ready] ==="
"$OF" channel list 2>/dev/null | grep -i telegram || echo "telegram NO configurado"
echo "=== memoria del agente [deben aparecer claves *_manuelita] ==="
"$OF" memory list manuelita-bot 2>/dev/null | grep -c '"key"' | sed 's/^/claves guardadas: /'
