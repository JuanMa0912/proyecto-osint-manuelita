<div align="center">

# 🌱 Proyecto OSINT + Agente Conversacional — Manuelita S.A.

### De un pipeline OSINT con base de conocimiento (MLOps)
### a un asistente conversacional productizado sobre un Agent OS (AgentOps)

[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![LangChain](https://img.shields.io/badge/LangChain-0.3-1C3C3C?style=for-the-badge)](https://langchain.com)
[![ChromaDB](https://img.shields.io/badge/Vector_DB-ChromaDB-FF6F61?style=for-the-badge)](https://www.trychroma.com/)
[![OpenFang](https://img.shields.io/badge/Agent_OS-OpenFang_v0.6.9-orange?style=for-the-badge)](https://github.com/RightNow-AI/openfang)
[![LangSmith](https://img.shields.io/badge/Observabilidad-LangSmith-purple?style=for-the-badge)](https://smith.langchain.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

[🧭 Ciclo de vida](#-ciclo-de-vida-mlops--agentops) · [🚀 Inicio rápido](#-inicio-rápido) · [🗂️ Estructura](#️-estructura-del-repositorio) · [📊 Corpus](#-corpus-generado) · [📚 Documentación](#-documentación)

</div>

---

**Universidad Autónoma de Occidente — Maestría en IA y Ciencia de Datos**

| Estudiante | Código |
|-----------|--------|
| Juan Manuel Velázquez Terreros | 22501347 |
| Julián Andrés Herrera Sánchez | 22500247 |
| Juan Sebastián Plazas Gallo | 22501580 |
| Juliana María Lozano Santa | 22500696 |

---

## ¿Qué es este repositorio?

Sistema que captura información **pública** de **Manuelita S.A.** —una de las
agroindustrias más grandes e históricas de América Latina (fundada en **1864**, opera
en **3 países**, exporta a **+65**)— y la convierte primero en una **base de
conocimiento semántica**, luego en un **agente conversacional con RAG y memoria**, y
finalmente la **productiza sobre un Sistema Operativo Agéntico** que responde desde
Telegram y WhatsApp.

El repo no es un único entregable: es la **evolución completa de un sistema de IA**
recorrida en tres módulos, donde cada etapa del ciclo de vida tiene un lugar claro en
el árbol de carpetas (ver [§ Ciclo de vida](#-ciclo-de-vida-mlops--agentops)).

---

## 🧭 Estado del proyecto por módulos

| Módulo | Tema | Stack | Estado | Documentación |
|--------|------|-------|--------|---------------|
| **M1** | Base de conocimiento semántica + Q&A | Python · spaCy · LangChain | ✅ Entregado | Este README + [`reports/modulo1/`](reports/modulo1/) |
| **M2** | Agente RAG conversacional + memoria | LangChain · ChromaDB · Streamlit | ✅ Entregado | [`docs/MODULO2.md`](docs/MODULO2.md) |
| **M3** | Productización sobre Agent OS (**Ruta B — OpenFang**) | OpenFang (Rust) · WSL2 · Ollama/Gemini · Telegram + WhatsApp | 🟢 Demo-ready (F0–F3 ✅ · F5 t-SNE ✅ · F4 informe en markdown, PDF generado) | [`openfang/README.md`](openfang/README.md) |

> **Nota de arquitectura (M2 → M3).** En la Ruta B, el código del Módulo 2
> (LangChain/ChromaDB/Streamlit) **no se reutiliza como software vivo**: solo se migra
> el **corpus limpio del Módulo 1** a la memoria de OpenFang. El M2 permanece en el
> repo y en el informe como **evolución arquitectónica**, no como el binario en
> producción. El sistema "vivo" en M3 es el agente sobre OpenFang.
> Informe unificado: [`reports/informe_final.md`](reports/informe_final.md) ·
> [`reports/informe_final.pdf`](reports/informe_final.pdf).

---

## 🧭 Ciclo de vida MLOps → AgentOps

El proyecto se lee como un ciclo de vida de IA donde **M1+M2 ponen el fundamento MLOps**
(ingesta y procesamiento de datos, indexado, servicio, observabilidad) y **M3 lo
evoluciona a AgentOps** (productización del agente, operaciones autónomas, canales,
análisis del comportamiento del agente).

```
   ┌──────────────────── FUNDAMENTO MLOps (M1 + M2) ─────────────────────┐   ┌──── AgentOps (M3) ────┐
   │                                                                     │   │                       │
   ▼                                                                     ▼   ▼                       ▼
[1] Ingesta OSINT → [2] Procesado/NLP → [3] Base de conocimiento → [4] Servicio → [5] Observabilidad → [6] Productización agéntica
   (scrapers)         (cleaners,          (markdown + ChromaDB)     (RAG + chat)   (LangSmith, t-SNE)   (OpenFang: Hands + canales)
```

| # | Etapa del ciclo de vida | Qué ocurre | Dónde vive en el repo | Módulo |
|---|-------------------------|-----------|------------------------|--------|
| 1 | **Ingesta de datos (OSINT)** | Descubrir fuentes, scrapear web/PDFs/redes/YouTube respetando `robots.txt` | [`src/discover/`](src/discover/) · [`src/scrapers/`](src/scrapers/) · [`src/parsers/`](src/parsers/) → [`data_raw/`](data_raw/) | M1 |
| 2 | **Procesamiento / *features*** | NER con spaCy, normalización de entidades, dedup MinHash, construcción de SMART MARKDOWN | [`src/cleaners/`](src/cleaners/) · [`src/markdown_builders/`](src/markdown_builders/) → [`data_processed/`](data_processed/) | M1 |
| 3 | **Base de conocimiento / indexado** | Corpus Markdown + datos estructurados (NIT, cifras) + índice vectorial ChromaDB | [`data_processed/markdown/`](data_processed/markdown/) · [`data/structured/`](data/structured/) · `data/vectorstore/` (regenerable) | M1 → M2 |
| 4 | **Servicio / inferencia** | Router híbrido (datos exactos vs RAG), memoria conversacional, UI de chat | [`src/langchain_app/`](src/langchain_app/) · [`app.py`](app.py) | M2 |
| 5 | **Observabilidad** | Trazas de cada llamada (LLM, embeddings, retriever) + análisis t-SNE de las sesiones del agente | [`src/langchain_app/langsmith_setup.py`](src/langchain_app/langsmith_setup.py) · [`scripts/tsne_sesiones_m3.py`](scripts/tsne_sesiones_m3.py) · [`reports/modulo3/`](reports/modulo3/) | M2 → M3 |
| 6 | **Productización agéntica (AgentOps)** | Agent OS con persona, memoria semántica, *Hands* (operaciones autónomas) y canales reales (Telegram/WhatsApp) | [`openfang/`](openfang/) | M3 |
| — | **Reproducibilidad y entrega** | Entorno fijado (`uv.lock`), tests por bloque, runbook de demo, informes versionados | [`pyproject.toml`](pyproject.toml) · [`uv.lock`](uv.lock) · [`scripts/`](scripts/) · [`reports/`](reports/) | M1–M3 |

> **Qué hace de esto "AgentOps" y no solo MLOps:** el artefacto final no es un modelo
> que sirve predicciones, sino un **agente** con persona, herramientas, memoria
> persistente y autonomía operativa, **monitoreado en producción** (trazas LangSmith +
> análisis t-SNE del historial real de conversaciones). El M3 es donde el ciclo de vida
> cruza de "operar un modelo" a "operar un agente".

---

## 🗂️ Estructura del repositorio

```
proyecto_manuelita/
│
├── README.md                 ← este archivo (portada + ciclo de vida)
├── LICENSE                   ← MIT
├── CLAUDE.md                 ← guía para el agente de IA que trabaja el repo
├── app.py                    ← UI Streamlit (chat RAG, Módulo 2)
├── pyproject.toml · uv.lock  ← dependencias y lockfile reproducible (uv)
│
├── docs/                     ← documentación de apoyo
│   ├── MODULO2.md            ← documentación técnica completa del Módulo 2
│   ├── PROVIDERS.md          ← los tres modos de proveedor (gemini / local / ollama)
│   └── NOTAS_INTERNAS_M3.md  ← notas internas del equipo (privado, no versionado)
│
├── src/                      ← código del pipeline + app (M1 + M2)
│   ├── main.py               ← orquestador del pipeline OSINT (8 fases)
│   ├── discover/ scrapers/ parsers/ cleaners/ markdown_builders/   ← ETL OSINT (M1)
│   ├── langchain_app/        ← RAG, router híbrido, memoria, observabilidad (M2)
│   │   ├── rag_engine.py · agent.py · memory.py
│   │   ├── tools/structured_tool.py · langsmith_setup.py
│   │   └── qa_system.py · prompts.py · corpus_loader.py
│   └── utils/
│
├── data_raw/                 ← datos crudos OSINT (mayormente .gitignore)
├── data_processed/           ← 📤 corpus limpio (en repo)
│   ├── markdown/             ← SMART MARKDOWN + key_facts (formato Q&A)
│   └── json/                 ← datos normalizados
├── data/structured/          ← JSON de datos exactos (NIT, cifras, directivos)
│
├── openfang/                 ← 🤖 Módulo 3 — agente productizado sobre Agent OS
│   ├── README.md             ← estado por fases + quick start del agente
│   ├── agents/manuelita-bot/ ← manifiesto (persona, system_prompt, tools) + MEMORY.md
│   ├── hands/                ← operaciones autónomas (Hands: 2 built-in + 1 Custom)
│   ├── whatsapp-gateway/     ← gateway QR (Baileys) → manuelita-bot
│   ├── config/ · scripts/    ← config de proveedores + scripts de despliegue
│   └── docs/                 ← F0–F3 + RUNBOOK de la sustentación
│
├── scripts/                  ← tests por bloque (M2) + análisis t-SNE (M3)
├── reports/                  ← entregables: informes (md/pdf), t-SNE, guion
│   ├── modulo1/ · modulo2/ · modulo3/ · informe_final.{md,pdf}
├── templates/ · logs/        ← plantilla de markdown · logs de ejecución (.gitignore)
└── .env.example              ← plantilla de configuración
```

---

## 🚀 Inicio rápido

### Prerrequisitos

- Python **3.11+** y [`uv`](https://docs.astral.sh/uv/)
- (Opcional) `GEMINI_API_KEY` para el mejor modo RAG, o [Ollama](https://ollama.com) para modo local offline
- (Solo M3) WSL2 + Ubuntu para OpenFang — ver [`openfang/README.md`](openfang/README.md)

### Vía A — App conversacional RAG (Módulo 2)

```bash
# 1. Clonar e instalar
git clone <repo-url> && cd proyecto_manuelita
uv sync
uv run python -m spacy download es_core_news_lg     # solo si vas a correr el pipeline OSINT

# 2. Configurar credenciales
cp .env.example .env        # editar LLM_PROVIDER (local | gemini | ollama)

# 3. Levantar el chat (PowerShell)
$env:LLM_PROVIDER="local"; uv run streamlit run app.py
```

> Modo recomendado: `local` para desarrollo offline; `gemini` para mejor calidad
> (~95% RAG). Detalle de los tres modos en [`docs/PROVIDERS.md`](docs/PROVIDERS.md).

### Vía B — Pipeline OSINT (regenerar el corpus, Módulo 1)

```bash
uv run python src/main.py --quick     # ~10-15 min · fuentes prioritarias
uv run python src/main.py --full      # ~30-60 min · todas las fuentes
```

### Vía C — Agente productizado sobre Agent OS (Módulo 3)

El agente vive sobre **OpenFang** en WSL2 y responde desde Telegram/WhatsApp.
Despliegue paso a paso (keys, daemon, memoria semántica, Hands, canales) en
**[`openfang/README.md`](openfang/README.md)** y el runbook de demo en
[`openfang/docs/RUNBOOK-demo.md`](openfang/docs/RUNBOOK-demo.md).

---

## 🧪 Tests

```bash
# Sin LLM (rápido)
uv run python scripts/test_structured_tool.py

# Con LLM local (PowerShell)
$env:LLM_PROVIDER="local"; uv run python scripts/test_agente_bloque3.py     # routing 10/10
$env:LLM_PROVIDER="local"; uv run python scripts/test_memoria_bloque4.py    # memoria conversacional
$env:LLM_PROVIDER="local"; uv run python scripts/test_modulo2_completo.py   # suite integrada

# Regenerar el índice vectorial si está vacío/corrupto
$env:LLM_PROVIDER="local"; uv run python scripts/test_rag_bloque1.py --reindex
```

Resultados esperados por script en [`CLAUDE.md`](CLAUDE.md#tests-y-resultados-esperados).

---

## 📊 Corpus generado

| Métrica | Valor |
|---------|-------|
| 📄 Documentos SMART MARKDOWN | **6** |
| 📝 Palabras totales | **~56.800** |
| 📊 Tablas extraídas (PDFs) | **139** |
| 🏢 Organizaciones detectadas | **7** |
| 🌱 Temas clasificados | **11** |

| Documento | Fuente | Palabras | Tablas | Confianza |
|-----------|--------|----------|--------|-----------|
| [Perfil Corporativo](data_processed/markdown/oficial_perfil_manuelit.md) | manuelita.com | 2.840 | — | 0.95 |
| [Informe Sostenibilidad 2023-2024](data_processed/markdown/oficial_doc_manuelit.md) | PDF oficial | 17.687 | 21 | 0.97 |
| [Informe Sostenibilidad 2021-2022](data_processed/markdown/oficial_pdf_sostenibilidad_manuelit.md) | PDF oficial | 17.078 | 118 | 0.97 |
| [Datos Financieros Supersociedades](data_processed/markdown/financiero_supersociedades_manuelit.md) | Supersociedades 2019–2024 | 1.200 | 6 | 0.98 |
| [LinkedIn Empresa](data_processed/markdown/red_social_linkedin_manuelit.md) | LinkedIn | — | — | 0.65 |
| [Canal YouTube](data_processed/markdown/red_social_youtube_manuelit.md) | YouTube API v3 | — | — | 0.75 |

El archivo clave para retrieval es [`key_facts_manuelita.md`](data_processed/markdown/key_facts_manuelita.md) (formato Q&A).

---

## 🔭 Observabilidad

- **Trazas (M2):** con `LANGCHAIN_TRACING_V2=true`, LangSmith registra automáticamente
  cada llamada (LLM, embeddings, retriever, memoria, herramientas). Proyecto
  `manuelita-osint-ia`. API en [`langsmith_setup.py`](src/langchain_app/langsmith_setup.py).
- **Análisis del agente (M3, "picante"):** t-SNE/UMAP sobre el historial real de
  sesiones del daemon (embeddings 768-dim). Script
  [`tsne_sesiones_m3.py`](scripts/tsne_sesiones_m3.py); figuras y análisis en
  [`reports/modulo3/`](reports/modulo3/) (`tsne_clusters.png`, `tsne_analisis.md`).

---

## 🛠️ Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Scraping / OSINT | `requests` · `BeautifulSoup4` · `newspaper3k` · YouTube Data API v3 |
| Extracción PDF | `pdfplumber` → `PyMuPDF` → `pytesseract` (OCR fallback) |
| NLP / NER | `spaCy` (es_core_news_lg) · dedup `MinHash LSH` (datasketch) |
| RAG / Agente (M2) | `LangChain 0.3` · `ChromaDB` · `sentence-transformers` |
| UI | `Streamlit` |
| Observabilidad | `LangSmith` · `t-SNE`/`UMAP` (`scikit-learn`/`umap-learn`) |
| Agent OS (M3) | `OpenFang` v0.6.9 (Rust) · WSL2 · Ollama Cloud `gemma3:27b` / Gemini · Telegram · WhatsApp (Baileys) |
| Entorno | `uv` (lockfile reproducible) · `loguru` |

---

## ⚖️ Consideraciones éticas y legales

✅ Solo información **pública**; respeta `robots.txt`; delays corteses (2–4 s); usa APIs
oficiales (YouTube Data API v3); no almacena datos personales de individuos.

❌ No accede a áreas privadas ni evade autenticación; no scrapea
LinkedIn/Instagram/Facebook directamente (ToS); no descarga videos (solo metadatos); no
redistribuye los datos capturados.

---

## 📚 Documentación

| Documento | Para qué |
|-----------|----------|
| [`docs/MODULO2.md`](docs/MODULO2.md) | Documentación técnica completa del Módulo 2 (RAG, router, memoria, observabilidad) |
| [`docs/PROVIDERS.md`](docs/PROVIDERS.md) | Guía de los tres modos de proveedor LLM |
| [`openfang/README.md`](openfang/README.md) | Módulo 3: estado por fases, quick start y despliegue del agente |
| [`openfang/docs/RUNBOOK-demo.md`](openfang/docs/RUNBOOK-demo.md) | Guion operativo de la sustentación en vivo |
| [`reports/informe_final.md`](reports/informe_final.md) · [`.pdf`](reports/informe_final.pdf) | Informe técnico unificado M1+M2+M3 |
| [`CLAUDE.md`](CLAUDE.md) | Contexto de arquitectura y reglas para trabajar el repo |

---

<div align="center">

**Proyecto OSINT + Agente Conversacional — Manuelita S.A.**
Universidad Autónoma de Occidente · Maestría en IA y Ciencia de Datos · 2026

</div>
</content>
