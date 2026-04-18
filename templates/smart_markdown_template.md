---
# ============================================================
# PLANTILLA SMART MARKDOWN — PROYECTO OSINT MANUELITA
# Versión: 2.0 | Optimizada para RAG y análisis semántico
# ============================================================

id: ""                          # ID único del documento (generado automáticamente)
company: "Manuelita S.A."       # Empresa objetivo
source_type: ""                 # oficial | prensa | red_social | reseña | tercero | pdf
source_name: ""                 # Nombre de la fuente (ej: "manuelita.com", "Portafolio.co")
source_url: ""                  # URL completa de origen
page_title: ""                  # Título de la página o documento
captured_at: ""                 # ISO 8601 timestamp de captura (UTC)
language: "es"                  # Código de idioma (es, en, pt)
country: "CO"                   # Código de país principal (CO, PE, CL)
confidence_score: 0.0           # Score de confianza 0.0-1.0

# ---- Taxonomía y etiquetas ----
tags: []
  # Ejemplos:
  # - manuelita
  # - sostenibilidad
  # - azucar_bioetanol
  # - oficial

# ---- Entidades detectadas ----
entities:
  organizations: []
    # Ejemplos:
    # - "Manuelita S.A."
    # - "Agroindustrial Laredo S.A."
    # - "Mejillones América"
  people: []
    # Ejemplos:
    # - "Harold Eder (Presidente)"
  locations: []
    # Ejemplos:
    # - "Cali, Valle del Cauca (Colombia)"
    # - "Trujillo (Perú)"
    # - "Puerto Montt (Chile)"
  products: []
    # Ejemplos:
    # - "Azúcar refinada"
    # - "Bioetanol combustible"
    # - "Biodiesel de palma"
  business_units: []
    # Ejemplos:
    # - "Plataforma Azúcar y Energía"
    # - "Plataforma Aceites y Energía"
    # - "Plataforma Acuicultura"
    # - "Plataforma Frutas y Hortalizas"

# ---- Clasificación temática ----
topics: []
  # Valores posibles (taxonomía Manuelita):
  # azucar_bioetanol | palma_biodiesel | acuicultura | frutas_hortalizas
  # sostenibilidad_ambiental | sostenibilidad_social | sostenibilidad_economica
  # innovacion | gobernanza | talento_humano | mercados_internacionales

# ---- Cifras clave detectadas ----
key_figures: {}
  # Ejemplos:
  # produccion_azucar_ton: "487000"
  # empleados: "5000"
  # paises_exportacion: "65"
  # años_historia: "161"

# ---- Tipo de documento ----
document_type: ""
  # Valores: perfil | historia | noticias | sostenibilidad | pdf_informe
  #          youtube | instagram | facebook | linkedin | prensa | wikipedia

# ---- Metadatos adicionales ----
word_count: 0
detected_sections: []
---

# 📋 [Título del documento]

> **[Tipo de fuente]** — [[URL de origen]([URL de origen])]
> Capturado: `YYYY-MM-DD` | Idioma: `ES` | Confianza: `0.0`

---

## Resumen ejecutivo

[Descripción concisa del contenido del documento en 2-4 oraciones.
Qué información contiene, de dónde viene, y por qué es relevante
para el análisis de Manuelita Agroindustrial.]

---

## Datos clave extraídos

### Cifras identificadas

- **[Métrica]:** [Valor con unidad]
- **[Métrica]:** [Valor con unidad]

### Estadísticas del documento

- **Palabras totales:** [N]
- **Páginas (si PDF):** [N]
- **Método de extracción:** `[método]`

### Unidades de negocio mencionadas

- [Unidad de negocio 1]
- [Unidad de negocio 2]

---

## Contenido estructurado

### Estructura del documento (encabezados)

- **H1:** [Título principal]
  - **H2:** [Subtítulo]
    - **H3:** [Sección]

### Texto principal

[Contenido limpio extraído del documento.
Máximo 3,000 palabras en el Markdown.
Texto completo disponible en el JSON fuente.]

---

## Entidades detectadas

### Organizaciones

- `Manuelita S.A.`
- `[Subsidiaria o entidad relacionada]`

### Personas mencionadas

- [Nombre, cargo]

### Geografías / Presencia

- 📍 [Ubicación 1]
- 📍 [Ubicación 2]

### Temas principales (taxonomía Manuelita)

- **[tema]** `████████░░` 80% — keywords: [kw1], [kw2], [kw3]
- **[tema]** `█████░░░░░` 50% — keywords: [kw1], [kw2]

---

## Fechas y eventos relevantes

- `1864` — Fundación de Manuelita en el Valle del Cauca
- `[año]` — [Evento relevante]
- `[fecha]` — [Hito histórico o corporativo]

---

## Evidencia textual (citas clave)

> **1.** "[Cita textual literal del documento más relevante para Manuelita]"

> **2.** "[Segunda cita relevante]"

> **3.** "[Tercera cita relevante]"

---

## Relación con otras fuentes

### Páginas relacionadas (links internos)

- [[Título de página relacionada]([URL])]

### Fuentes externas referenciadas

- [[Nombre de fuente externa]([URL])]

---

## Observaciones de calidad

- **Tipo de fuente:** `[tipo]` — [Descripción del tipo]
- **Score de confianza:** `[0.0-1.0]` / 1.0
- **Estado de normalización:** `[completado|pendiente|insuficiente]`
- **Método de extracción:** `[método]`
- **Hash de contenido:** `[hash_sha256_16chars]`

### ⚠️ Advertencias (si aplica)

- [Descripción de advertencia o limitación del dato]

---

## URL original

[[URL completa del documento]([URL completa del documento])]

---
*Documento generado automáticamente — Proyecto OSINT Manuelita — [YYYY-MM-DD]*
