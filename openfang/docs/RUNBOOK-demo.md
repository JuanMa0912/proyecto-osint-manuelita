# RUNBOOK — Arranque y demo de `manuelita-bot` (OpenFang, Módulo 3)

> Guía paso-a-paso para dejar el sistema listo y sustentar **sin problemas con el daemon**.
> Todo corre en **WSL2 (Ubuntu) como root**. Motor: **Ollama Cloud `gemma3:27b`** (cuota
> independiente de Gemini, GPU remota).

---

## 0. Reglas de oro (leer una vez)

1. **Un solo daemon.** Telegram solo admite un poller por token; dos daemons = error `409` y el
   bot deja de responder. Antes de arrancar, **siempre** `pkill -9 -x openfang`.
2. **El Hand Custom (`sostenibilidad-manuelita`) NO sobrevive a un reinicio del daemon.** Los
   built-in reviven solos; el Custom no. → `05-setup-hands.sh` se corre **AL FINAL** y **cada vez
   que reinicies** el daemon.
3. **`04-cargar-memoria` reinicia el daemon** → por eso va ANTES de `05-setup-hands`.
4. **No ensayes en bucle.** El free tier de Ollama Cloud se mide por tiempo de GPU (sesión 5 h +
   semanal). Carga la memoria **una vez** y ensaya con pocas preguntas espaciadas.
5. **Preguntas atómicas, no ráfagas.** Varios mensajes seguidos en la misma sesión confunden al
   agente (se "pega" a la respuesta anterior). En la demo, una pregunta, esperas la respuesta, otra.

---

## 1. Prerrequisitos (una sola vez)

- WSL2 con Ubuntu y OpenFang instalado en `/root/.openfang/bin/openfang` (ver `docs/F0-spike-infraestructura.md`).
- Archivo de claves `~/.openfang/manuelita.env` (NO se commitea), con:
  ```bash
  export OLLAMA_API_KEY=...        # ollama.com/settings/keys (gratis) — motor primario
  export GEMINI_API_KEY=...        # fallback
  export TELEGRAM_BOT_TOKEN=...    # BotFather
  chmod 600 ~/.openfang/manuelita.env
  ```
- Entrar a WSL como root: `wsl -d Ubuntu -u root`
- Ir al repo (visto desde WSL): `cd /mnt/c/Users/PROYECTOS/Desktop/Claude_Multi_Agents_Projects/proyecto_manuelita/openfang/scripts`

---

## 2. Arranque desde cero (orden EXACTO)

```bash
# 1) Desplegar el agente (copia manifiesto + corpus NO vacio + MEMORY.md; borra openfang.db)
bash 02-deploy-agent.sh

# 2) Arrancar el daemon (mata cualquier daemon previo, arranca con las claves del env)
bash 01-start-daemon.sh
#    Dashboard: http://127.0.0.1:4200

# 3) Repoblar la memoria semantica (12 hechos via memory_store). OJO: REINICIA el daemon.
bash 04-cargar-memoria-semantica.sh

# 4) Dejar los 3 Hands listos (AL FINAL, porque el paso 3 reinicio el daemon)
bash 05-setup-hands.sh
```

> Si en algún punto reinicias el daemon (manual o con `01-start`), **vuelve a correr el paso 4**
> (`05-setup-hands.sh`), o el Hand Custom desaparecerá.

---

## 3. Verificación (antes de la demo) — NO gasta cuota

```bash
bash 00-estado.sh
```
Debe mostrar:
- `daemon procs = 1`
- 4 agentes `Running` con `MODEL = gemma3:27b` (manuelita-bot, lead-hand, collector-hand, sostenibilidad-hand)
- 3 Hands `Active`
- telegram `Ready`
- claves de memoria guardadas (> 0)

Una prueba funcional mínima (gasta 1 llamada; úsala con moderación):
```bash
UUID=$(/root/.openfang/bin/openfang agent list | grep -i "manuelita-bot" | awk '{print $1}')
/root/.openfang/bin/openfang message "$UUID" "Cual es el NIT de Manuelita y a cuantos paises exporta?"
```
Esperado: NIT 891.300.241 y 49 países, respuesta limpia en español.

---

## 4. Flujo de la demo (15 min, sin diapositivas)

1. **Dashboard** (`http://127.0.0.1:4200`): mostrar los 4 agentes corriendo y **Hands → Active 3**
   (lead, collector, sostenibilidad). Explicar que **cada Hand es un agente** especializado.
2. **Memoria / "RAG interno":** `openfang memory list manuelita-bot` muestra los hechos curados;
   explicar el modelo de **6 capas** (KV + semántica por embeddings + sesiones…). Opcional: store
   en vivo de un hecho y recuperarlo reformulado (demuestra recall semántico).
3. **Prueba de fuego (Telegram):** el evaluador escribe al bot `@Cortana_Juanito0312_bot` desde su
   teléfono. Preguntas sugeridas (atómicas):
   - "¿Cuál es el NIT de Manuelita y quién es su presidente?"
   - "¿A cuántos países exporta y cuántos colaboradores tiene?"
   - "¿Cuáles son sus metas de carbono?"
   - Una de control anti-alucinación: "¿Cuál fue el salario del presidente en 2019?" → debe decir
     "No tengo ese dato confirmado en mis fuentes".
4. **Tras bambalinas:** mostrar la terminal/logs (`openfang logs` o `tail ~/.openfang/daemon.log`)
   mientras responde.

---

## 5. Troubleshooting del daemon

| Síntoma | Causa | Solución |
|---------|-------|----------|
| Bot no responde por Telegram; log lleno de `409 Conflict` | Dos daemons vivos | `pkill -9 -x openfang; sleep 1; bash 01-start-daemon.sh` (verifica `pgrep -x openfang` = 1) |
| Solo 2 Hands activos (falta el Custom) | Reinicio borró el Custom | `bash 05-setup-hands.sh` |
| Respuestas con `429` / "rate limit" | Cuota Gemini agotada (fallback) o ráfaga | El primario es Ollama Cloud; si insiste, espera unos minutos y espacia preguntas |
| Respuesta repite lo anterior a preguntas distintas | Sesión acumulada | Reinicia daemon (`01-start`) + re-corre `05-setup-hands`; en demo, preguntas espaciadas |
| El bot inventa una cifra | Archivo de corpus vacío/escaso | El deploy ya excluye vacíos; no preguntar por datos que no están en el corpus |
| `openfang message` "Daemon communication error" | Daemon caído o atascado | `bash 01-start-daemon.sh` y reintenta |

---

## 6. Apagar / dejar en reposo (cuidar cuota)

```bash
# Pausar Hands para que no corran en segundo plano:
/root/.openfang/bin/openfang hand active        # copia los INSTANCE UUID
/root/.openfang/bin/openfang hand pause <INSTANCE_UUID>   # uno por cada Hand
# (o detener todo el daemon)
pkill -9 -x openfang
```
> Recuerda: al reanudar/reiniciar tendrás que re-correr `04` (memoria) y `05` (hands).
