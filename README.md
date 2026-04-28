<div align="center">

# 🌱 Proyecto OSINT Manuelita

### Pipeline de recolección, estructuración y almacenamiento de información pública  
### para el Sistema Q&A del chatbot de Manuelita Agroindustrial S.A.

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![spaCy](https://img.shields.io/badge/NLP-spaCy%20es__core__news__lg-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)](https://spacy.io)
[![LangChain](https://img.shields.io/badge/LangChain-Framework-1C3C3C?style=for-the-badge)](https://langchain.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Estado](https://img.shields.io/badge/Estado-Activo-brightgreen?style=for-the-badge)]()

[📋 Ver Corpus](#corpus-generado) · [🚀 Inicio rápido](#instalación) · [📊 Resultados](#resultados) · [🗂️ Estructura](#estructura-del-proyecto)

</div>

---

## Actividad Módulo 1 — Creación de la Base de Conocimiento Semántico y Sistema Q&A

**Universidad Autónoma de Occidente — Ingeniería de Sistemas**

| Estudiante | Código |
|-----------|--------|
| Juan Manuel Velázquez Terreros | — |
| Julián Andrés Herrera Sánchez | 22500247 |
| Juan Sebastián Plazas Gallo | — |
| Juliana María Lozano Santa | 22500696 |

---

## Descripción del problema

La gestión de la información dentro del Ingenio Manuelita enfrenta el desafío de optimizar sus flujos de comunicación interna y externa. Existe una dependencia de canales manuales o semi-automatizados que, ante el gran volumen de datos generados en la cadena de valor, incrementan el riesgo de asimetrías informativas, tiempos de respuesta prolongados y posibles errores humanos en la interpretación de reportes críticos.

Esta ausencia de un canal de comunicación centralizado y automatizado limita la capacidad de los colaboradores para tomar decisiones basadas en datos en tiempo real, generando la necesidad de implementar una solución tecnológica que garantice la precisión, trazabilidad y entrega oportuna de la información.

## Planteamiento de la solución

Se propone el diseño e implementación de un **Sistema de Preguntas y Respuestas (Q&A)** que actúa como núcleo de conocimiento para un futuro chatbot corporativo. El sistema consolida toda la información pública de Manuelita S.A. en un corpus semántico estructurado, y utiliza un LLM con **Prompt Engineering** para responder preguntas basándose únicamente en ese contexto.

> **Nota técnica:** Este sistema **NO es un RAG** (Retrieval-Augmented Generation). Todo el texto limpio del corpus se consolida directamente en el system prompt del LLM, siguiendo las instrucciones del Módulo 1.

La arquitectura opera en dos capas: (1) un **pipeline OSINT** que extrae, limpia y estructura información pública de múltiples fuentes, y (2) una **aplicación LangChain** con interfaz Streamlit que expone tres funcionalidades: Resumen ejecutivo, Generación de FAQ y Q&A libre.

---

## ¿Qué es este proyecto?

Pipeline completo de **OSINT corporativo** que captura información pública de **Manuelita S.A.** — una de las organizaciones agroindustriales más grandes e históricas de América Latina — y la convierte en una **base documental semántica** lista para:

- 💬 **Sistema Q&A** con LangChain — texto del corpus en el system prompt del LLM
- 📝 **Resumen ejecutivo** automático de la empresa
- ❓ **Generación de FAQs** sobre productos, historia y operaciones
- 📊 **Análisis empresarial** y minería de texto

### ¿Por qué Manuelita?

> Fundada en **1864** en el Valle del Cauca, Colombia. Opera en **4 plataformas de negocio**  
> en **3 países** (Colombia, Perú, Chile), exporta a **+65 países** y tiene **161 años** de historia.

```
GRUPO MANUELITA S.A.
├── 🍬 Caña de Azúcar y Energía    → Manuelita Azúcar y Energía (CO) + Agroindustrial Laredo (PE)
├── 🌴 Aceite de Palma y Energía   → Manuelita Aceites y Energía (Meta + Casanare, CO)
├── 🦐 Acuicultura                 → Mejillones América (CL) + Océanos (CO)
└── 🍇 Frutas y Hortalizas         → Uvas de mesa y vegetales de exportación
```

---

## Resultados

El corpus generado:

| Métrica | Valor |
|---------|-------|
| 📄 Documentos SMART MARKDOWN | **6** |
| 📝 Palabras totales | **~56,800** |
| 📊 Tablas extraídas (PDFs) | **139** |
| 🏢 Organizaciones detectadas | **7** |
| 📍 Geografías mapeadas | **6** |
| 🌱 Temas clasificados | **11** |
| ⏱️ Tiempo de ejecución pipeline | **~48 segundos** |

### Corpus generado

| Documento | Fuente | Palabras | Tablas | Confianza |
|-----------|--------|----------|--------|-----------|
| [Perfil Corporativo](data_processed/markdown/oficial_perfil_manuelit.md) | manuelita.com | 2,840 | — | 0.95 |
| [Informe Sostenibilidad 2023-2024](data_processed/markdown/oficial_doc_manuelit.md) | PDF oficial | 17,687 | 21 | 0.97 |
| [Informe Sostenibilidad 2021-2022](data_processed/markdown/oficial_pdf_sostenibilidad_manuelit.md) | PDF oficial | 17,078 | 118 | 0.97 |
| [Datos Financieros Supersociedades](data_processed/markdown/financiero_supersociedades_manuelit.md) | Supersociedades 2019–2024 | 1,200 | 6 | 0.98 |
| [LinkedIn Empresa](data_processed/markdown/red_social_linkedin_manuelit.md) | LinkedIn | — | — | 0.65 |
| [Canal YouTube](data_processed/markdown/red_social_youtube_manuelit.md) | YouTube API v3 | — | — | 0.75 |

---

## Arquitectura del sistema

```
MÓDULO 1 — BASE DE CONOCIMIENTO + SISTEMA Q&A
══════════════════════════════════════════════════════════════════

  CAPA 1: PIPELINE OSINT (Knowledge Base)
  ─────────────────────────────────────────
  manuelita.com  ──┐
  PDFs públicos ──┤                        ┌─ SMART MARKDOWN
  Supersocied.  ──┤ → NLP (spaCy) ──────→ ├─ YAML frontmatter
  LinkedIn      ──┤   Entidades           └─ Índice maestro
  YouTube API   ──┘   Temas · Cifras

  CAPA 2: APLICACIÓN Q&A (LangChain + Streamlit)
  ──────────────────────────────────────────────
  Corpus texto  ──→ System Prompt ──→ LLM ──→ [ Resumen ]
                                          ──→ [ FAQ     ]
                                          ──→ [ Q&A     ]
```

### Flujo ETL del pipeline — 8 fases

```
1. DISCOVER    → sitemap.xml + crawl + detección de PDFs
2. SCRAPE WEB  → requests + BeautifulSoup + robots.txt
3. SCRAPE NEWS → Google News RSS + newspaper3k
4. SOCIAL      → OG metadata + APIs oficiales (YouTube Data API v3)
5. PDFs        → pdfplumber → PyMuPDF → OCR Tesseract (fallback)
6. NORMALIZE   → spaCy NER + regex + taxonomía corporativa + MinHash dedup
7. BUILD MD    → YAML frontmatter semántico + 9 secciones estructuradas
8. INDEX       → Índice maestro JSON + Markdown
```

---

## Instalación

### Prerrequisitos

- Python **3.11+**
- `uv` (recomendado) o `pip`
- (Opcional) YouTube Data API Key — [obtener gratis en Google Cloud](https://console.cloud.google.com)
- (Opcional) Tesseract OCR — para PDFs escaneados

### Con uv (recomendado)

```bash
# 1. Clonar el repositorio
git clone https://github.com/JuanMa0912/proyecto-osint-manuelita.git
cd proyecto-osint-manuelita

# 2. Instalar dependencias con uv
uv sync

# 3. Instalar modelo NLP en español
uv run python -m spacy download es_core_news_lg

# 4. Configurar credenciales
cp .env.example .env
# Editar .env con tu YOUTUBE_API_KEY (opcional)
```

### Con pip (alternativa)

```bash
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

pip install -r requirements.txt
python -m spacy download es_core_news_lg
```

---

## Uso

### Pipeline de Knowledge Base

```bash
uv run python src/main.py --quick      # ~10-15 min · fuentes prioritarias
uv run python src/main.py --full       # ~30-60 min · todas las fuentes
```

### Aplicación Q&A (Streamlit)

```bash
uv run streamlit run app.py
```

### Por fase individual

```bash
uv run python src/main.py --phase discover    # Mapeo de fuentes
uv run python src/main.py --phase scrape      # Sitio web oficial
uv run python src/main.py --phase pdfs        # Informes PDF
uv run python src/main.py --phase normalize   # NLP y entidades
uv run python src/main.py --phase markdown    # Generar SMART MARKDOWN
```

---

## Formato SMART MARKDOWN

Cada documento del corpus incluye **YAML frontmatter semántico** que estructura la información para el sistema Q&A:

```yaml
---
id: manuelita_web_f2a1c3b8_20260418
company: Manuelita S.A.
source_type: oficial
source_url: https://www.manuelita.com/perfil-corporativo/
confidence_score: 0.95
tags: [manuelita, oficial, perfil, azucar_bioetanol, palma_biodiesel]
entities:
  organizations: [Manuelita S.A., Manuelita Azúcar y Energía, Agroindustrial Laredo S.A.]
  people: [Harold Eder (Presidente — Manuelita S.A.)]
  locations: [Cali, Valle del Cauca (Colombia), Trujillo (Perú), Puerto Montt (Chile)]
  products: [Azúcar refinada, Bioetanol combustible, Aceite de palma crudo, Biodiesel]
key_figures:
  ingresos_2023_cop_millones: '1043562'
  ebitda_2023_cop_millones: '369380'
  produccion_azucar_ton: '487000'
  paises_exportacion: '65'
---
```

---

## Estructura del proyecto

```
proyecto_manuelita/
│
├── 📋 README.md                      ← Este archivo
├── 📦 pyproject.toml                 ← Dependencias (uv)
├── 🔑 .env.example                   ← Plantilla de configuración
├── 🌐 app.py                         ← Interfaz Streamlit Q&A
│
├── src/                              ← Código fuente pipeline
│   ├── main.py                       ← Orquestador del pipeline
│   ├── langchain_app/                ← Aplicación Q&A LangChain
│   │   ├── qa_system.py              ← Motor Q&A (Resumen, FAQ, Q&A)
│   │   └── prompts.py                ← Prompt Engineering documentado
│   ├── utils/
│   ├── discover/
│   ├── scrapers/
│   ├── parsers/
│   ├── cleaners/
│   └── markdown_builders/
│
├── data_processed/                   ← 📤 Corpus (en repo)
│   └── markdown/
│       ├── _INDICE_MAESTRO.md
│       ├── oficial_perfil_manuelit.md
│       ├── oficial_doc_manuelit.md
│       ├── oficial_pdf_sostenibilidad_manuelit.md
│       ├── financiero_supersociedades_manuelit.md
│       ├── red_social_linkedin_manuelit.md
│       └── red_social_youtube_manuelit.md
│
├── data_raw/                         ← 📥 Datos crudos (.gitignore)
├── reports/                          ← Reportes de sesión y Q&A tests
├── templates/
└── logs/                             ← Logs de ejecución (.gitignore)
```

---

## Consideraciones éticas y legales

✅ **Lo que hace este proyecto:**
- Solo accede a información pública y abierta
- Respeta `robots.txt` de cada sitio automáticamente
- Implementa delays corteses (2-4s) entre requests
- Usa APIs oficiales (YouTube Data API v3)
- No almacena datos personales de individuos

❌ **Lo que NO hace:**
- No accede a áreas privadas ni evade autenticación
- No scrapea LinkedIn/Instagram/Facebook directamente (ToS)
- No descarga videos de YouTube — solo metadatos
- No publica ni redistribuye los datos capturados

---

## Stack tecnológico

| Componente | Tecnología |
|------------|-----------|
| Scraping web | `requests` + `BeautifulSoup4` |
| Extracción PDF | `pdfplumber` → `PyMuPDF` → `pytesseract` |
| NLP / NER | `spaCy` (es_core_news_lg) |
| Noticias | `newspaper3k` + `feedparser` |
| YouTube | YouTube Data API v3 |
| Deduplicación | SHA256 + `MinHash LSH` (datasketch) |
| Framework LLM | `LangChain` |
| Interfaz | `Streamlit` |
| Gestor paquetes | `uv` |
| Logging | `loguru` |

---

## Fuentes de información

### 🏢 Corporativo
- [Perfil Corporativo](https://www.manuelita.com/perfil-corporativo/)
- [Historia de la empresa](https://www.manuelita.com/historia/)
- [Gobierno Corporativo](https://www.manuelita.com/gobierno-corporativo/)
- [Línea Ética](https://www.manuelita.com/linea-etica/)
- [Ubicación espacial — Google Maps](https://www.google.com/maps/place/Ingenio+Manuelita/@3.5866869,-76.3348015,7868m/data=!3m1!1e3!4m10!1m2!2m1!1sfundaci%C3%B3n+manuelita+cali!3m6!1s0x8e3a031047e59b9d:0x9cb27379c1be0d59!8m2!3d3.5866877!4d-76.3053523!15sChlmdW5kYWNpw7NuIG1hbnVlbGl0YSBjYWxpgOIAQGSAR1pbmR1c3RyaWFsX2VxdWlwbWVudF9zdXBwbGllcuABAA!16s%2Fg%2F11c0qyq237?hl=es&entry=ttu&g_ep=EgoyMDI2MDQyMi4wIKXMDSoASAFQAw%3D%3D)

### 🌱 Sostenibilidad
- [Informe Sostenibilidad 2023-2024 (PDF)](https://www.manuelita.com/wp-content/uploads/2025/09/Informe-Manuelita-gobierno-corporativo.pdf)
- [Sostenibilidad Ambiental](https://www.manuelita.com/sostenib/ambiental/)
- [Sostenibilidad Económica](https://www.manuelita.com/economico/)
- [Noticias Ingenio](https://www.manuelita.com/manuelita-noticias/)

### 🛒 Productos
- [Azúcar](https://www.manuelita.com/azucar/)
- [Azúcar Industrial](https://www.manuelitaindustria.com/)
- [Energías Renovables](https://www.manuelita.com/manuelita-productos/energias-renovables/)
- [Derivados de la Caña](https://www.manuelita.com/manuelita-productos/derivados-de-la-cana/)
- [Derivados de la Palma](https://www.manuelita.com/manuelita-productos/derivados-de-la-palma/)
- [Frutas y Hortalizas](https://www.manuelita.com/manuelita-productos/frutas-y-hortalizas/)
- [Mejillones](https://www.manuelita.com/manuelita-productos/mejillones/)

### 🤝 Comunidad y Talento
- [Fundación Manuelita](https://fundacionmanuelita.org/)
- [Donaciones Fundación](https://fundacionmanuelita.org/donaciones/)
- [Vacantes disponibles](https://www.manuelita.com/talento/)
- [Portal Proveedores Caña](https://proveedores-cana.manuelita.com/static/index.html#/)

### 💰 Financiero
- [Datos Financieros Supersociedades](https://www.estrategiaenaccion.com/es/reportes)
- [Publicaciones / Valle Online](https://www.valleonline.org/)

---

<div align="center">

**Módulo 1 — Base de Conocimiento Semántico y Sistema Q&A**  
Universidad Autónoma de Occidente · 2026

</div>
