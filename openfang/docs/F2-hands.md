# Fase F2 — Operaciones autónomas (Hands)

> Maestría en IA y Ciencia de Datos — Universidad Autónoma de Occidente
> Módulo 3 · Fase F2 · Empresa: Manuelita S.A.

## 1. Objetivo

Configurar las **Hands** de OpenFang: operaciones autónomas que corren en *schedule*
(a diferencia del agente conversacional `manuelita-bot`, que es reactivo). El enunciado
pide activar una o más; el equipo eligió **2 built-in + 1 Custom**.

## 2. Qué es una Hand

Una Hand es un *playbook* de capacidad autónoma: un agente con un system_prompt
multi-fase, herramientas restringidas, ajustes configurables y métricas de dashboard,
que se ejecuta solo en ciclos programados. Se gestionan con:

```bash
openfang hand list                       # hands disponibles (9 built-in)
openfang hand activate <id>              # activar
openfang hand config <id> --set K=V      # configurar ajustes
openfang hand active                     # instancias activas (muestra el INSTANCE UUID)
openfang hand pause <instance_uuid>      # pausar / reanudar: usan el INSTANCE UUID, NO el nombre
openfang hand resume <instance_uuid>     #   (verificado: pasar el nombre reporta "'' paused" sin efecto)
openfang hand install <dir>              # instalar una Hand custom (dir con HAND.toml)
```

> **Gotcha verificado (jun 2026):** `pause`/`resume` esperan el **INSTANCE UUID** que
> lista `openfang hand active` (col. INSTANCE), no el id del hand. Con el nombre el CLI
> dice `✔ Hand instance '' paused.` pero el estado sigue `Active`. Con el UUID pasa a `Paused`.

## 3. Hands desplegadas

| Hand | Tipo | Rol para Manuelita |
|------|------|--------------------|
| `collector` | Built-in | Inteligencia competitiva OSINT del sector agroindustrial (perfil analítico) |
| `lead` | Built-in | Generación/calificación de leads para productos de Manuelita (perfil comercial) |
| `sostenibilidad-manuelita` | **Custom** | Monitor OSINT de metas de carbono y reputación ambiental (toque auténtico) |

### Configuración del Collector (quota-safe)
```bash
openfang hand config collector \
  --set target_subject="Manuelita S.A. y el sector agroindustrial (azucar, palma de aceite, acuicultura) en Colombia, Peru y Chile" \
  --set focus_area=competitor \
  --set collection_depth=surface \
  --set update_frequency=weekly \
  --set max_sources_per_cycle=10
```

## 4. Estrategia de cuota

Las Hands corren autónomas y hacen llamadas LLM → consumen cuota del free tier de Gemini
(el mismo riesgo de 429 ya documentado en F0). Estrategia aplicada:

- **`update_frequency = weekly`** y profundidad `surface` → mínimos barridos.
- Tras activarlas, **`hand pause`** todas. Se reanudan (`hand resume`) solo para la demo.

## 5. El Custom Hand — esquema del HAND.toml (verificado)

El esquema **no está documentado** públicamente; se obtuvo de forma **empírica** dejando
que el validador de `openfang hand install` guiara los campos requeridos. Estructura final:

```toml
[hand]
id = "..."
name = "..."
description = "..."
category = "data"
icon = "🌱"
tools = ["web_search", "web_fetch", "file_read", "memory_store", ...]
requirements = []

[hand.agent]
name = "..."
description = "..."
provider = "gemini"
model = "gemini-2.5-flash-lite"
system_prompt = """<playbook multi-fase, inline>"""

[[hand.settings]]
key = "update_frequency"
label = "..."
setting_type = "select"
default = "weekly"
options = [ { label = "Diario", value = "daily" }, { label = "Semanal", value = "weekly" } ]
```

Aprendizajes del validador (errores que guiaron el esquema):
1. `missing field 'hand'` → la metadata va bajo una tabla `[hand]`.
2. `[hand]` `missing field 'agent'` → el agente va **anidado**: `[hand.agent]`.
3. `[hand.agent]` `missing field 'system_prompt'` → el playbook va **inline** (no en un archivo aparte).
4. `dashboard` da error de tipo (no "missing") → es **opcional**; se omitió.

Archivos de la Hand custom (en `openfang/hands/sostenibilidad-manuelita/`):
- `HAND.toml` — manifiesto (incluye el system_prompt multi-fase inline).
- `SKILL.md` — conocimiento experto de sostenibilidad de Manuelita (frontmatter YAML + cuerpo).

Instalación y activación:
```bash
openfang hand install <repo>/openfang/hands/sostenibilidad-manuelita
openfang hand activate sostenibilidad-manuelita
openfang hand config sostenibilidad-manuelita --set update_frequency=weekly
openfang hand pause sostenibilidad-manuelita
```

## 6. Estado

Las 3 Hands quedaron **activadas, configuradas y pausadas** (quota-safe). Para la demo se
reanudan con `openfang hand resume <instance_uuid>` y se observan en el dashboard
`http://127.0.0.1:4200`.

## 7. Spike de ejecución del Custom Hand (jun 2026) — evidencia

Se ejecutó el Hand de sostenibilidad **bajo demanda** (mensaje directo a su agente, ya que
activar no dispara el ciclo: eso corre en el `schedule` semanal). Resultados verificados:

- **La operación autónoma funciona.** `iterations=4`: el Hand planificó, hizo **`web_search`
  real** (encontró la pagina de sostenibilidad de Manuelita y el PDF del Informe 2023-2024),
  analizó, citó fuentes y **persistió en memoria** (`memory/<fecha>.md`). Fue honesto cuando
  no pudo acceder al PDF completo — sin alucinar. ~15 s.
- **Pero `flash-lite` no completó el `file_write`** del reporte nombrado (mismo patrón que el
  agente conversacional: el modelo pequeño no cierra de forma fiable todas las fases con tool).
  → El `HAND.toml` se fijó a **`gemini-2.5-flash`** para que cierre el ciclo (incluye el reporte).

### Gotcha verificado — una Hand registrada NO se puede actualizar en caliente

OpenFang v0.6.9 **no** tiene `hand uninstall` ni `install --force`. Tras registrar una Hand,
`hand install` repetido falla con `Hand already registered`, y `deactivate` solo detiene la
instancia (no la des-registra). Para cambiarle el modelo/definición hay que **resetear la DB**
(`openfang.db`), lo cual borra también la config de canales. Implicación práctica:

- En un **entorno limpio** (un compañero clonando: `02-deploy-agent.sh` borra `openfang.db`),
  la Hand se registra **desde cero con el `HAND.toml` del repo** (ya en `gemini-2.5-flash`) y
  completa el `file_write`.
- En un entorno **ya poblado**, la Hand queda con el modelo con que se registró por primera vez.

## 8. Próximo paso

F3 — canales (Telegram ✅ probado) y luego F4 — informe unificado.
