"""
prompts.py
----------
Diseño de prompts para el sistema Q&A de Manuelita S.A.

Técnicas aplicadas:
- Zero-shot prompting: instrucciones directas sin ejemplos
- Restricción al contexto: el LLM SOLO puede usar la información provista
- Anti-alucinación: instrucción explícita de no inventar datos
- Formato estructurado: salidas predecibles para la UI
"""

# ============================================================
# PROMPT BASE — System prompt con el corpus completo
# ============================================================

SYSTEM_PROMPT_BASE = """Eres un asistente virtual experto en Manuelita S.A., \
una de las organizaciones agroindustriales más importantes de América Latina.

Tu función es responder preguntas y generar análisis basándote ÚNICAMENTE \
en la siguiente información oficial de la empresa:

{corpus}

REGLAS ESTRICTAS QUE DEBES SEGUIR:
1. Responde SOLO con información que aparezca en el contexto anterior.
2. Si la información solicitada NO está en el contexto, responde exactamente: \
"No tengo información suficiente sobre ese tema en la base de conocimiento disponible."
3. NO inventes datos, cifras, fechas, nombres o hechos que no estén en el contexto.
4. Responde siempre en español.
5. Sé preciso y conciso. Cita cifras exactas cuando estén disponibles.
"""

# ============================================================
# PROMPT 1 — RESUMEN EJECUTIVO (Zero-shot)
# ============================================================

RESUMEN_PROMPT = """Genera un resumen ejecutivo completo de Manuelita S.A. \
basándote únicamente en la información del contexto.

El resumen debe incluir las siguientes secciones en orden:

1. **Descripción general** — qué es la empresa, cuándo fue fundada y dónde opera
2. **Plataformas de negocio** — las 4 unidades de negocio principales
3. **Presencia geográfica** — países y regiones donde opera
4. **Cifras clave de producción** — capacidades y volúmenes de producción
5. **Desempeño financiero** — ingresos, EBITDA y utilidad neta más recientes
6. **Sostenibilidad** — compromisos ambientales y metas de carbono
7. **Posicionamiento** — qué hace a Manuelita destacar en su sector

Usa un tono profesional y corporativo. Incluye cifras exactas cuando estén disponibles."""

# ============================================================
# PROMPT 2 — GENERACIÓN DE FAQ (Zero-shot)
# ============================================================

FAQ_PROMPT = """Genera una lista de exactamente 15 Preguntas Frecuentes (FAQ) \
sobre Manuelita S.A. que un cliente, proveedor o colaborador podría hacer \
al interactuar por primera vez con la empresa.

Las preguntas deben cubrir estos temas:
- Historia y fundación de la empresa
- Productos y servicios que ofrece
- Países y regiones donde opera
- Sostenibilidad y medio ambiente
- Información financiera y tamaño de la empresa
- Innovación y biocombustibles
- Contacto y vinculación

Formato de respuesta para cada pregunta:
**P: [pregunta]**
R: [respuesta basada únicamente en el contexto]

Si no tienes información para responder una pregunta, omítela y reemplázala \
por otra que sí puedas responder con el contexto disponible."""

# ============================================================
# PROMPT 3 — Q&A LIBRE (Zero-shot con restricción)
# ============================================================

QA_PROMPT = """Responde la siguiente pregunta del usuario basándote \
ÚNICAMENTE en la información del contexto sobre Manuelita S.A.

Pregunta: {question}

Instrucciones para tu respuesta:
- Si la respuesta está en el contexto, respóndela de forma clara y directa.
- Incluye cifras exactas y datos específicos cuando estén disponibles.
- Si la respuesta NO está en el contexto, di exactamente: \
"No tengo información suficiente sobre ese tema en la base de conocimiento disponible."
- No supongas ni inferencias. Solo hechos del contexto.
- Máximo 3 párrafos."""

# ============================================================
# DOCUMENTACIÓN DE EXPERIMENTOS CON PROMPTS
# ============================================================

PROMPT_EXPERIMENTS = """
Experimentos realizados durante el diseño de prompts:

EXPERIMENTO 1 — Resumen sin estructura
  Prompt: "Resume la empresa Manuelita"
  Problema: Respuestas genéricas sin datos específicos
  Solución: Agregar secciones obligatorias con datos concretos

EXPERIMENTO 2 — Anti-alucinación débil
  Prompt: "Responde solo con el contexto"
  Problema: El LLM a veces añadía datos de entrenamiento
  Solución: Instrucción explícita + frase exacta para respuesta vacía

EXPERIMENTO 3 — FAQ sin cobertura temática
  Prompt: "Genera 15 FAQs"
  Problema: Todas las preguntas sobre el mismo tema
  Solución: Especificar los 7 temas obligatorios

EXPERIMENTO 4 — Q&A con respuestas largas
  Prompt: Sin límite
  Problema: Respuestas de 10+ párrafos poco útiles para la UI
  Solución: Agregar "Máximo 3 párrafos"
"""
