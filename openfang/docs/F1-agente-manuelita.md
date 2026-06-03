# Fase F1 — Agente conversacional manuelita-bot

> Maestría en IA y Ciencia de Datos — Universidad Autónoma de Occidente
> Módulo 3 · Fase F1 · Empresa: Manuelita S.A. (agroindustrial colombiana)

---

## 1. Objetivo

Dotar al agente conversacional `manuelita-bot` de la **persona de Manuelita S.A.** y de su **conocimiento corporativo**, gobernado por un prompt anti-alucinación **proporcional**.

La proporcionalidad es el eje del diseño: el agente debe ser lo bastante estricto para **no inventar** datos que no estén respaldados por sus fuentes, pero sin **sobre-restringirse** hasta el punto de negarse a ayudar. Cuando falte un dato concreto, el agente lo admite con claridad y, en lugar de cerrar la conversación, ofrece la información relacionada que sí posee.

---

## 2. Cómo OpenFang da conocimiento a un agente

OpenFang es un Agent OS escrito en Rust (instalado en la fase F0). Un agente se define y alimenta de la siguiente manera (verificado en F0):

- **Manifiesto del agente** — `~/.openfang/agents/<nombre>/agent.toml`. Declara, entre otras secciones:
  - `[model]` con el `system_prompt` (persona + reglas + datos núcleo embebidos).
  - `[capabilities]` con la lista de `tools` que el agente puede usar.
- **Workspace del agente** — `~/.openfang/workspaces/<nombre>/`, que contiene:
  - Carpeta `data/` — archivos que el agente lee mediante la herramienta `file_read`.
  - `MEMORY.md` — la **Long-Term Memory** (memoria de largo plazo) curada con los hechos clave.
  - Memoria **KV** (clave-valor), accesible mediante herramientas de memoria.

**No hay RAG por embeddings.** OpenFang no indexa el conocimiento en un vectorstore ni realiza búsqueda semántica. La recuperación es **agéntica**: el conocimiento llega al agente por tres vías combinadas —archivos del workspace (leídos con herramientas), memoria KV y el `system_prompt`—, y es el propio LLM quien decide cuándo leer un archivo para responder.

---

## 3. Diseño del prompt (reglas anti-alucinación proporcionales)

El prompt aplica buenas prácticas reconocidas de mitigación de alucinaciones, adaptadas a un escenario de conocimiento corporativo cerrado. Referencias:

- [Microsoft Azure AI Foundry — Best practices for mitigating hallucinations in LLMs](https://techcommunity.microsoft.com/blog/azure-ai-foundry-blog/best-practices-for-mitigating-hallucinations-in-large-language-models-llms/4403129)
- [MachineLearningMastery — 7 Prompt Engineering Tricks to Mitigate Hallucinations](https://machinelearningmastery.com/7-prompt-engineering-tricks-to-mitigate-hallucinations-in-llms/)
- [AI Mastery — Advanced Prompting for RAG](https://aiamastery.substack.com/p/lesson-25-advanced-prompting-for)

Principios aplicados:

- **(a) Admitir el hueco en vez de inventar.** Ante una pregunta cuyo dato no está en las fuentes, el agente responde "No tengo ese dato confirmado en mis fuentes" en lugar de fabricar una respuesta plausible.
- **(b) Indicar el origen del dato.** El agente señala que su conocimiento proviene de la información corporativa de Manuelita S.A., dando trazabilidad a lo que afirma.
- **(c) Proporcionalidad.** "No tengo ese dato" **no es** "no puedo ayudarte". El agente ofrece lo relacionado que sí conoce, manteniendo la utilidad de la conversación sin caer en la sobre-restricción.
- **(d) Dos modos de interacción.**
  - *Preguntas sobre datos de la empresa* → modo **grounded estricto**: solo responde con lo respaldado por sus fuentes.
  - *Saludos y conversación general* → modo **natural**: responde con fluidez, sin aplicar la regla estricta de grounding.
- **(e) Datos núcleo embebidos.** Los hechos verificados más consultados van directamente en el `system_prompt`, lo que permite responder de forma rápida y exacta sin necesidad de invocar herramientas.

**Temperatura del modelo: 0.2** (configuración factual, que reduce la variabilidad y favorece respuestas deterministas y ancladas en los datos).

---

## 4. Datos núcleo de Manuelita (verificados)

| Campo | Valor |
|-------|-------|
| Razón social | Manuelita S.A. |
| NIT | 891.300.241 |
| Año de fundación | 1864 |
| Sede principal | Palmira, Valle del Cauca, Colombia (centro corporativo en Cali) |
| Presidente | Harold Eder |
| Países de operación | Colombia, Perú y Chile |
| Plataformas (4) | Azúcar · Palma de aceite · Acuicultura · Frutas y hortalizas |
| Colaboradores | ~7.971 |
| Ingresos 2023 | 1.043.562 millones COP |
| EBITDA 2023 | 369.380 millones COP (margen 35,4%) |
| Sostenibilidad | Meta -70% emisiones (Alcances 1 y 2) a 2030 · Neutralidad de carbono a 2040 |

**Unidades de negocio (7):**

1. Manuelita Azúcar y Energía
2. Agroindustrial Laredo
3. Manuelita Aceites y Energía
4. Palmar de Altamira
5. Manuelita Acuicultura
6. Océanos
7. Manuelita Frutas y Hortalizas

---

## 5. Inyección del corpus

Para el conocimiento que va más allá de los datos núcleo, se copiaron los **8 archivos Markdown** del corpus del Módulo 1 (origen `proyecto_manuelita/data_processed/markdown/*.md`) al workspace del agente, en `~/.openfang/workspaces/manuelita-bot/data/`:

1. `_INDICE_MAESTRO.md`
2. `financiero_supersociedades_manuelit.md`
3. `key_facts_manuelita.md`
4. `oficial_doc_manuelit.md`
5. `oficial_pdf_sostenibilidad_manuelit.md`
6. `oficial_perfil_manuelit.md`
7. `red_social_linkedin_manuelit.md`
8. `red_social_youtube_manuelit.md`

Adicionalmente, se curó el `MEMORY.md` del workspace con los hechos clave de la empresa.

El agente consulta estos archivos mediante las herramientas `file_read` / `file_list` cuando una pregunta excede los datos núcleo embebidos en el `system_prompt`.

---

## 6. Configuración técnica del agente

Manifiesto `agents/manuelita-bot/agent.toml`:

- **provider** = `"default"` (hereda el proveedor de la configuración global de OpenFang: **Gemini `gemini-2.5-flash-lite`**)
- **temperature** = `0.2`
- **max_tokens** = `4096`
- **tools** = `["file_read", "file_write", "file_list", "memory_store", "memory_recall", "web_fetch"]`

El `system_prompt` completo (persona, reglas anti-alucinación proporcionales y datos núcleo) está versionado en el repositorio en `openfang/agents/manuelita-bot/agent.toml`. Se referencia ahí para mantener una única fuente de verdad; no se reproduce íntegro en este documento.

---

## 7. Pruebas y resultados (verificados, junio 2026)

Entorno de prueba: modelo **gemini-2.5-flash-lite**, 1 agente, tiempo de respuesta ~3 segundos.

### Prueba 1 — Dato real (grounding)

**Pregunta:** ¿Cuál es el NIT de Manuelita y quién es su presidente?

**Respuesta:**
> El NIT de Manuelita S.A. es 891.300.241 y su presidente es Harold Eder.

Resultado: ✓ Correcto y grounded. El agente respondió con exactitud a partir de los datos núcleo.

### Prueba 2 — Anti-alucinación

**Pregunta:** ¿Cuál fue el salario exacto del presidente en 2019? (dato inexistente)

**Respuesta:**
> No tengo ese dato confirmado en mis fuentes. La información financiera que poseo sobre Manuelita S.A. incluye los ingresos y el EBITDA para el año 2023. ¿Te gustaría conocer esas cifras...?

Resultado: ✓ El agente **no inventó**, admitió el hueco y ofreció lo relacionado que sí conoce (comportamiento proporcional).

### Interpretación

Las dos pruebas demuestran el equilibrio buscado: **grounding sin sobre-restricción**. El agente es exacto cuando tiene el dato y honesto cuando no lo tiene, sin dejar de ser útil al redirigir hacia la información disponible.

---

## 8. Cómo reproducirlo

En `openfang/scripts/` del repositorio se encuentran los scripts necesarios:

- `01-start-daemon.sh` — arranca el daemon de OpenFang.
- `02-deploy-agent.sh` — despliega el agente: copia el `agent.toml`, el corpus y el `MEMORY.md` al directorio `~/.openfang`.

**Importante:** tras desplegar el agente, hay que borrar `openfang.db*` y reiniciar para que OpenFang cargue el nuevo manifiesto.

---

## 9. Limitaciones y próximos pasos

- **Recuperación agéntica, no garantizada.** El conocimiento profundo (más allá de los datos núcleo) depende de que el LLM **decida** leer los archivos del workspace. A diferencia de un retriever, no hay garantía determinista de que el contexto relevante se recupere en cada consulta.
- **Próxima fase (F3):** conectar **Telegram** para realizar la demo en vivo del agente.

---

## 10. Spike de grounding y elección de modelo (jun 2026) — evidencia

Se midió empíricamente (vía la misma API REST que usan los canales) si el agente
realmente consulta el corpus o improvisa. Hallazgos:

| Modelo | ¿Usa `file_read` solo? | Respuesta a pregunta abierta | Latencia | Tokens (aprox.) |
|--------|------------------------|------------------------------|----------|-----------------|
| `gemini-2.5-flash-lite` | **No** — ignora la orden del prompt | genérica / improvisada (alucinación blanda) | 3–9 s | ~7.500 |
| `gemini-2.5-flash` | **Sí** — 2–3 iteraciones | aterrizada, con datos del corpus y cita de fuente | 7–20 s | ~24.000 |

Conclusiones verificadas:
1. **Las tools de archivo funcionan, rápido y SIN aprobación** (`/api/approvals` quedó
   vacío antes y después; no bloquean la respuesta).
2. El fallo original no era de tools sino de **navegación**: el modelo hacía `file_list`
   de la raíz y no entraba en `data/`. El prompt ahora trae un **mapa tema→archivo** con
   rutas completas (`data/<archivo>`).
3. **Instruir no basta con un modelo pequeño:** `2.5-flash-lite` ignora "DEBES leer el
   archivo" en preguntas abiertas. Solo `2.5-flash` recupera de forma autónoma.

**Decisión:** el agente conversacional usa **`gemini-2.5-flash`** (override por-agente en
`agent.toml`), con **fallback a `gemini-2.5-flash-lite`** si topa cuota. Para que lo común
siga siendo rápido sin tool, se **curaron al núcleo** (DATOS NUCLEO) los hechos de mayor
probabilidad de demo (operación por país, cifras operativas, utilidad neta, familias
beneficiadas). El detalle profundo se recupera con `file_read` (~7–20 s).

**Costo a vigilar (cuota):** una pregunta profunda con `2.5-flash` gasta ~10× tokens que
el lite. El tope `max_llm_tokens_per_hour = 200000` da ~8 preguntas profundas/hora. Es
suficiente para una demo de 15 min, pero **no conviene ensayar en exceso** el mismo día.
