<div align="center">

# 🌱 Proyecto OSINT Manuelita

### Pipeline de recolección, estructuración y almacenamiento de información pública  
### para análisis semántico y RAG sobre Manuelita Agroindustrial S.A.

[\![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[\![spaCy](https://img.shields.io/badge/NLP-spaCy%20es__core__news__lg-09A3D5?style=for-the-badge&logo=spacy&logoColor=white)](https://spacy.io)
[\![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[\![Estado](https://img.shields.io/badge/Estado-Activo-brightgreen?style=for-the-badge)]()
[\![RAG Ready](https://img.shields.io/badge/RAG-Ready-FF6B35?style=for-the-badge)]()

[📋 Ver Corpus](#corpus-generado) · [🚀 Inicio rápido](#instalación) · [📊 Resultados](#resultados) · [🗂️ Estructura](#estructura-del-proyecto)

</div>

---

## ¿Qué es este proyecto?

Pipeline completo de **OSINT corporativo** que captura información pública de **Manuelita S.A.** — una de las organizaciones agroindustriales más grandes e históricas de América Latina — y la convierte en una **base documental semántica** lista para:

- 🤖 **RAG** (Retrieval-Augmented Generation) con LangChain / LlamaIndex
- 🔍 **Búsqueda semántica** con embeddings vectoriales
- 📊 **Análisis empresarial** y minería de texto
- 🎓 **Investigación académica** sobre el sector agroindustrial latinoamericano

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

El corpus generado en la primera ejecución:

| Métrica | Valor |
|---------|-------|
| 📄 Documentos SMART MARKDOWN | **5** |
| 📝 Palabras totales | **~55,600** |
| 📊 Tablas extraídas (PDFs) | **139** |
| 🏢 Organizaciones detectadas | **7** |
| 📍 Geografías mapeadas | **6** |
| 🌱 Temas clasificados | **11** |
| ⏱️ Tiempo de ejecución | **~48 segundos** |

### Corpus generado

| Documento | Fuente | Palabras | Tablas | Confianza |
|-----------|--------|----------|--------|-----------|
| [Perfil Corporativo](data_processed/markdown/oficial_perfil_manuelit.md) | manuelita.com | 2,840 | — | 0.95 |
| [Informe Sostenibilidad 2023-2024](data_processed/markdown/oficial_doc_manuelit.md) | PDF oficial | 17,687 | 21 | 0.97 |
| [Informe Sostenibilidad 2021-2022](data_processed/markdown/oficial_pdf_sostenibilidad_manuelit.md) | PDF oficial | 17,078 | 118 | 0.97 |
| [LinkedIn Empresa](data_processed/markdown/red_social_linkedin_manuelit.md) | LinkedIn | — | — | 0.65 |
| [Canal YouTube](data_processed/markdown/red_social_youtube_manuelit.md) | YouTube API v3 | — | — | 0.75 |

---

## Arquitectura del pipeline

```
EXTRACT                    TRANSFORM                    LOAD
─────────────────────────────────────────────────────────────
                                                            
  manuelita.com  ──┐                                        
  PDFs públicos ──┤                                        
  LinkedIn      ──┤  →  NLP (spaCy)    →  SMART MARKDOWN  
  YouTube API   ──┤     Entidades         YAML frontmatter  
  Google RSS    ──┘     Temas             Índice maestro    
                        Cifras            JSON normalizado  
                        Deduplicación                       
```

### Flujo ETL en 8 fases

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

- Python **3.10+**
- pip
- (Opcional) YouTube Data API Key — [obtener gratis en Google Cloud](https://console.cloud.google.com)
- (Opcional) Tesseract OCR — para PDFs escaneados

### Pasos

```bash
# 1. Clonar el repositorio
git clone https://github.com/tu-usuario/proyecto-osint-manuelita.git
cd proyecto-osint-manuelita

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate      # Linux/Mac
# venv\Scripts\activate       # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar modelo NLP en español
python -m spacy download es_core_news_lg

# 5. Configurar credenciales
cp .env.example .env
# Editar .env con tu YOUTUBE_API_KEY (opcional)
```

---

## Uso

### Pipeline completo (recomendado para primera ejecución)

```bash
python src/main.py --quick      # ~10-15 min · fuentes prioritarias
python src/main.py --full       # ~30-60 min · todas las fuentes
```

### Por fase individual

```bash
python src/main.py --phase discover    # Mapeo de fuentes
python src/main.py --phase scrape      # Sitio web oficial
python src/main.py --phase news        # Prensa y RSS
python src/main.py --phase youtube     # Canal YouTube (requiere API key)
python src/main.py --phase social      # Redes sociales
python src/main.py --phase pdfs        # Informes PDF
python src/main.py --phase normalize   # NLP y entidades
python src/main.py --phase markdown    # Generar SMART MARKDOWN
```

### Por módulo directo

```bash
# Scrapear solo una página específica
python -m src.scrapers.scrape_website --page perfil historia sostenibilidad

# Procesar un PDF local
python -m src.parsers.parse_pdfs --local ruta/al/informe.pdf

# YouTube con límite de cuota conservador
python -m src.scrapers.scrape_youtube_metadata --max-videos 50
```

---

## Formato SMART MARKDOWN

Cada documento generado incluye **YAML frontmatter semántico** optimizado para RAG:

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
  business_units: [Plataforma Azúcar y Energía, Plataforma Aceites y Energía]
topics: [azucar_bioetanol, palma_biodiesel, acuicultura, mercados_internacionales]
key_figures:
  produccion_azucar_ton: '487000'
  produccion_bioetanol_litros: '275000000'
  años_historia: '161'
  paises_exportacion: '65'
---
```

El corpus es compatible con:

```python
# LangChain + ChromaDB
from langchain.document_loaders import DirectoryLoader, UnstructuredMarkdownLoader
from langchain.vectorstores import Chroma

loader = DirectoryLoader("data_processed/markdown/", glob="*.md",
                         loader_cls=UnstructuredMarkdownLoader)
docs = loader.load()
vectordb = Chroma.from_documents(docs, embeddings)
respuesta = vectordb.similarity_search("¿Cuál es la meta de carbono de Manuelita para 2030?")
```

---

## Estructura del proyecto

```
proyecto_manuelita/
│
├── 📋 README.md                      ← Este archivo
├── 📦 requirements.txt               ← Dependencias Python
├── 🔑 .env.example                   ← Plantilla de configuración
│
├── src/                              ← Código fuente
│   ├── main.py                       ← Orquestador del pipeline
│   ├── utils/
│   │   ├── config.py                 ← Configuración central tipada
│   │   └── utils.py                  ← Funciones reutilizables (15+)
│   ├── discover/
│   │   └── discover_sources.py       ← Reconocimiento de fuentes
│   ├── scrapers/
│   │   ├── scrape_website.py         ← Sitio oficial WordPress
│   │   ├── scrape_news.py            ← RSS + newspaper3k
│   │   ├── scrape_social_links.py    ← Redes sociales (ético)
│   │   └── scrape_youtube_metadata.py← YouTube Data API v3
│   ├── parsers/
│   │   └── parse_pdfs.py             ← pdfplumber → PyMuPDF → OCR
│   ├── cleaners/
│   │   └── normalize_entities.py     ← NLP, NER, deduplicación
│   └── markdown_builders/
│       └── build_smart_markdown.py   ← Generador SMART MARKDOWN
│
├── data_processed/                   ← 📤 Salidas del pipeline (en repo)
│   └── markdown/
│       ├── _INDICE_MAESTRO.md        ← Índice de todo el corpus
│       ├── oficial_perfil_manuelit.md
│       ├── oficial_doc_manuelit.md
│       ├── oficial_pdf_sostenibilidad_manuelit.md
│       ├── red_social_linkedin_manuelit.md
│       └── red_social_youtube_manuelit.md
│
├── data_raw/                         ← 📥 Datos crudos (en .gitignore)
│   ├── web/  social/  youtube/
│   ├── news/  reviews/
│   └── pdfs/  ← PDFs descargados (no versionados)
│
├── reports/                          ← Reportes de sesión
├── templates/
│   └── smart_markdown_template.md    ← Plantilla base
└── logs/                             ← Logs de ejecución (en .gitignore)
```

---

## Consideraciones éticas y legales

✅ **Lo que hace este proyecto:**
- Solo accede a información pública y abierta
- Respeta `robots.txt` de cada sitio automáticamente
- Implementa delays corteses (2-4s) entre requests
- Usa APIs oficiales (YouTube Data API v3, Wikipedia API)
- No almacena datos personales de individuos

❌ **Lo que NO hace:**
- No accede a áreas privadas ni evade autenticación
- No scrapea LinkedIn/Instagram/Facebook directamente (ToS)
- No descarga videos de YouTube — solo metadatos
- No publica ni redistribuye los datos capturados

---

## Taxonomía de temas

El corpus usa una taxonomía de **11 temas** específica para Manuelita:

`azucar_bioetanol` · `palma_biodiesel` · `acuicultura` · `frutas_hortalizas`  
`sostenibilidad_ambiental` · `sostenibilidad_social` · `sostenibilidad_economica`  
`innovacion` · `gobernanza` · `talento_humano` · `mercados_internacionales`

---

## Mejoras futuras

- [ ] Sistema RAG completo con LangChain + ChromaDB
- [ ] Scheduler para actualizaciones incrementales automáticas
- [ ] Dashboard Streamlit para explorar el corpus
- [ ] Expansión a subsidiarias: Agroindustrial Laredo, Mejillones América
- [ ] Knowledge Graph con NetworkX / Neo4j
- [ ] Análisis de sentimiento de noticias
- [ ] Embeddings automáticos en cada pipeline run

---

## Stack tecnológico

| Componente | Tecnología |
|------------|-----------|
| Scraping web | `requests` + `BeautifulSoup4` + `Playwright` |
| Extracción PDF | `pdfplumber` → `PyMuPDF` → `pytesseract` |
| NLP / NER | `spaCy` (es_core_news_lg) |
| Noticias | `newspaper3k` + `feedparser` |
| YouTube | YouTube Data API v3 |
| Deduplicación | SHA256 + `MinHash LSH` (datasketch) |
| Markdown | `python-frontmatter` + `jinja2` |
| Configuración | `python-dotenv` |
| Logging | `loguru` |
| Retries | `tenacity` |

---

<div align="center">

**Construido para análisis corporativo serio sobre información pública**  
Python · spaCy · pdfplumber · YouTube API · SMART MARKDOWN

</div>
