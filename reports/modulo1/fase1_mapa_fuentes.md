# Fase 1: Mapa de Fuentes OSINT — Ingenio Manuelita / Manuelita Agroindustrial

**Fecha de reconocimiento:** 2026-04-18  
**Analista:** Data Collection Engineer  
**Estado:** Confirmado con reconocimiento real  
**Empresa objetivo:** Manuelita S.A. — Grupo Empresarial Agroindustrial (Colombia/Perú/Chile)

---

## 1. Mapa de Fuentes Objetivo

### 1.1 Fuentes Primarias — Sitio Oficial

| ID   | Fuente                          | URL                                                   | Tipo     | Prioridad |
|------|---------------------------------|-------------------------------------------------------|----------|-----------|
| F01  | Portal corporativo principal    | https://www.manuelita.com/                            | oficial  | CRÍTICA   |
| F02  | Perfil corporativo              | https://www.manuelita.com/perfil-corporativo/         | oficial  | CRÍTICA   |
| F03  | Historia                        | https://www.manuelita.com/historia/                   | oficial  | ALTA      |
| F04  | Presencia regional              | https://www.manuelita.com/presencia-regional/         | oficial  | ALTA      |
| F05  | Plataformas de negocio          | https://www.manuelita.com/plataformas-de-negocios/    | oficial  | CRÍTICA   |
| F06  | Sostenibilidad                  | https://www.manuelita.com/sostenibilidad/             | oficial  | ALTA      |
| F07  | Noticias / Prensa               | https://www.manuelita.com/manuelita-noticias/         | oficial  | ALTA      |
| F08  | Prioridades económicas          | https://www.manuelita.com/economico/                  | oficial  | MEDIA     |
| F09  | Sitio de innovación             | https://manuelitainnova.com/                          | oficial  | MEDIA     |
| F10  | Portal de talento / vacantes    | https://grupomanuelita.na.teamtailor.com/             | oficial  | MEDIA     |

### 1.2 PDFs Públicos Confirmados

| ID   | Documento                                     | URL                                                                                            | Año       |
|------|-----------------------------------------------|-----------------------------------------------------------------------------------------------|-----------|
| P01  | Informe de Sostenibilidad 2023–2024 (PDF)     | https://www.manuelita.com/wp-content/uploads/2025/06/Informe-de-Sostenibilidad-Manuelita-2023-2024.pdf | 2025 |
| P02  | Informe de Sostenibilidad 2021–2022 (PDF)     | https://www.manuelita.com/wp-content/uploads/2023/06/Informe_Sostenibilidad_Manuelita-2021-2022.pdf    | 2023 |
| P03  | Informe de Sostenibilidad 2017–2018           | https://www.manuelita.com/manuelita-noticias/informe-de-sostenibilidad-2017-2018/             | 2018      |
| P04  | Informe Agroindustrial Laredo (subsidiaria PE)| https://agroindustriallaredo.com/informes-de-sostenibilidad/                                  | variable  |

### 1.3 Redes Sociales Confirmadas

| ID   | Red Social  | Handle / Canal                     | URL                                                              | Seguidores aprox. | Estado    |
|------|-------------|-------------------------------------|------------------------------------------------------------------|--------------------|-----------|
| S01  | LinkedIn    | Manuelita (empresa)                 | https://co.linkedin.com/company/manuelita                        | 123,206            | ✅ activa |
| S02  | Instagram   | @manuelitaagroindustria             | https://www.instagram.com/manuelitaagroindustria/               | 8,823              | ✅ activa |
| S03  | Facebook    | ManuelitaAgroindustria              | https://www.facebook.com/ManuelitaAgroindustria/                | 102,211 likes      | ✅ activa |
| S04  | YouTube     | Manuelita (canal oficial)           | https://www.youtube.com/channel/UCanNTjBY24t7fID3tj0WfTw        | —                  | ✅ activa |
| S05  | X/Twitter   | No verificado como oficial          | —                                                                | —                  | ⚠️ buscar |

### 1.4 Fuentes de Prensa Externas

| ID   | Medio                  | URL de referencia                                                                              | Tipo    |
|------|------------------------|-----------------------------------------------------------------------------------------------|---------|
| N01  | Portafolio             | https://www.portafolio.co (búsqueda: "Manuelita")                                             | prensa  |
| N02  | Semana Economía        | https://www.semana.com/economia/                                                               | prensa  |
| N03  | El País Cali           | https://www.elpais.com.co/500-empresas/manuelita-3053.html                                    | prensa  |
| N04  | Revista iAlimentos     | https://www.revistaialimentos.com/es/noticias/manuelita-el-ingenio-de-los-negocios            | prensa  |
| N05  | Wikipedia              | https://en.wikipedia.org/wiki/Manuelita                                                       | tercero |
| N06  | ProColombia B2B        | https://b2bmarketplaceplus.procolombia.co/en/agro-industry/agroindustrial/ingenio-manuelita-sa.aspx | registro |

---

## 2. Priorización de Fuentes

```
PRIORIDAD 1 — CRÍTICA (scraping inmediato):
  F01, F02, F05  → Perfil e identidad corporativa
  P01, P02       → PDFs de sostenibilidad (fuente gold para RAG)
  S01            → LinkedIn (datos estructurados de empresa y personas)

PRIORIDAD 2 — ALTA (segunda iteración):
  F03, F04, F06, F07  → Historia, regiones, sostenibilidad, noticias
  N01–N04             → Prensa colombiana de alto impacto

PRIORIDAD 3 — MEDIA (tercera iteración):
  F08, F09, F10  → Innovación, económico, empleo
  S02, S03, S04  → Redes sociales (metadatos, no contenido privado)
  N05, N06       → Wikipedia y registros secundarios
```

---

## 3. Estrategia de Scraping por Tipo de Fuente

### 3.1 Sitio Web Oficial (manuelita.com)
- **Tipo de rendering:** WordPress con contenido mayormente estático + algunos elementos dinámicos
- **Herramienta recomendada:** `requests` + `BeautifulSoup` para páginas principales
- **Fallback:** `Playwright` si detecta JavaScript blocking o lazy loading en noticias
- **Restricción:** Respetar `robots.txt` ubicado en `https://www.manuelita.com/robots.txt`
- **Rate limiting:** Delay de 2–4 segundos entre requests, no más de 30 req/min
- **Profundidad:** Hasta 2 niveles de profundidad desde la homepage

### 3.2 PDFs Públicos
- **Herramienta:** `requests` para descarga directa + `pdfplumber` para extracción de texto
- **Restricción:** Solo PDFs enlazados públicamente desde el sitio oficial
- **Post-proceso:** Limpieza de texto con regex, detección de tablas con `pdfplumber`, OCR con `pytesseract` si el PDF es imagen

### 3.3 LinkedIn
- **Restricción IMPORTANTE:** LinkedIn prohíbe scraping automatizado en su ToS
- **Estrategia ética permitida:**
  - Usar LinkedIn API oficial (requiere aprobación de Partnerships)
  - Extracción manual y documentación de datos públicos visibles sin autenticación
  - Usar Google como intermediario: `site:linkedin.com "manuelita"` para indexados públicos
- **Alternativa:** Usar exportación manual de perfil de empresa si el usuario tiene cuenta

### 3.4 Instagram / Facebook
- **Restricción:** Meta prohíbe scraping sin API oficial
- **Estrategia ética permitida:**
  - Meta Graph API (requiere app aprobada) para datos públicos de página
  - Captura manual de metadatos visibles (bio, seguidores, descripción)
  - Scraping de links de posts indexados en Google

### 3.5 YouTube
- **Herramienta:** `YouTube Data API v3` (gratuita con cuota de 10,000 unidades/día)
- **Alternativa:** `yt-dlp` solo para metadatos (sin descarga de video)
- **Restricción:** No descargar videos, solo metadatos (títulos, descripciones, fechas, vistas)
- **Datos a capturar:** lista de videos, fechas, descripciones, thumbnails, estadísticas públicas

### 3.6 Prensa y Noticias
- **Herramienta:** `requests` + `BeautifulSoup` o `newspaper3k` para artículos
- **Alternativa:** Google News RSS feed filtrado por `"Manuelita" agroindustrial`
- **Herramienta complementaria:** `feedparser` para RSS/Atom de medios

### 3.7 Robots.txt — Política declarada
```
# A verificar al ejecutar el scraper:
# https://www.manuelita.com/robots.txt
# El scraper incluye verificación automática de robots.txt via urllib.robotparser
```

---

## 4. Riesgos Técnicos y Legales por Fuente

| ID   | Fuente        | Riesgo Técnico                          | Riesgo Legal                               | Mitigación                                    |
|------|---------------|-----------------------------------------|---------------------------------------------|-----------------------------------------------|
| F01  | manuelita.com | WordPress con posible CF / rate limit   | Bajo — sitio público                        | Delays, respeto a robots.txt, user-agent real |
| P01  | PDF oficial   | PDF puede ser imagen (requiere OCR)     | Ninguno — documento público                 | pdfplumber + pytesseract fallback             |
| S01  | LinkedIn      | Bloqueo por bot detection muy agresivo  | ALTO — ToS prohíbe scraping                 | Solo extracción manual o API oficial          |
| S02  | Instagram     | Requiere sesión para ver todo           | ALTO — ToS Meta                             | Solo datos públicos sin login via Graph API   |
| S03  | Facebook      | Similar a Instagram                     | ALTO — ToS Meta                             | Meta Graph API o extracción manual            |
| S04  | YouTube       | Ninguno con API oficial                 | Bajo con YouTube Data API v3               | Usar API key gratuita de Google               |
| N01  | Portafolio.co | Posible paywall parcial                 | Bajo — artículos públicos                   | Solo capturar párrafos visibles sin login     |
| N05  | Wikipedia     | Ninguno                                 | Ninguno — Creative Commons                  | Usar Wikipedia API oficial                    |

---

## 5. Librerías Recomendadas por Caso de Uso

```python
# SCRAPING WEB
requests==2.31.0          # HTTP requests básicos
beautifulsoup4==4.12.3    # Parsing HTML
lxml==5.1.0               # Parser rápido para BS4
playwright==1.43.0        # Sitios JavaScript dinámicos (fallback)

# PDFS
pdfplumber==0.11.0        # Extracción de texto y tablas de PDF
PyMuPDF==1.24.0           # Alternativa robusta (fitz)
pytesseract==0.3.10       # OCR para PDFs-imagen
Pillow==10.3.0            # Dependencia de pytesseract

# NOTICIAS
newspaper3k==0.2.8        # Extracción de artículos de prensa
feedparser==6.0.11        # RSS/Atom feeds

# YOUTUBE
google-api-python-client==2.120.0  # YouTube Data API v3
yt-dlp==2024.3.10                  # Metadatos sin descarga

# DATOS Y LIMPIEZA
pandas==2.2.1             # Tablas y DataFrames
spacy==3.7.4              # NER para entidades (es_core_news_lg)
langdetect==1.0.9         # Detección de idioma

# MARKDOWN Y OUTPUT
python-frontmatter==1.1.0 # YAML frontmatter en Markdown
jinja2==3.1.4             # Templates para markdown

# UTILIDADES
python-dotenv==1.0.1      # Variables de entorno desde .env
loguru==0.7.2             # Logging avanzado
tenacity==8.2.3           # Retries automáticos
fake-useragent==1.4.0     # Rotación ética de user agents
tqdm==4.66.2              # Barras de progreso
```

---

## 6. Matriz de Decisión Completa

| Fuente               | Tipo Contenido        | Método Captura          | Frecuencia Actualiz. | Dificultad | Formato Salida       |
|---------------------|-----------------------|-------------------------|----------------------|------------|----------------------|
| manuelita.com/perfil | HTML estático         | requests + BS4          | Bimestral            | BAJA       | JSON + Markdown      |
| manuelita.com/noticias | HTML dinámico      | requests + BS4 / Playwright | Semanal           | MEDIA      | JSON + Markdown      |
| PDF sostenibilidad   | PDF texto + tablas    | pdfplumber              | Anual                | MEDIA      | JSON + Markdown      |
| LinkedIn empresa     | HTML dinámico + login | API oficial / manual    | Mensual              | ALTA       | JSON                 |
| Instagram            | SPA JavaScript        | Meta Graph API / manual | Mensual              | ALTA       | JSON                 |
| Facebook             | SPA JavaScript        | Meta Graph API          | Mensual              | ALTA       | JSON                 |
| YouTube canal        | API REST              | YouTube Data API v3     | Semanal              | BAJA       | JSON + Markdown      |
| Portafolio / Semana  | HTML artículos        | newspaper3k             | Continuo             | MEDIA      | JSON + Markdown      |
| Wikipedia            | API Wikipedia         | Wikipedia REST API      | Semestral            | BAJA       | JSON + Markdown      |
| Google News RSS      | XML/RSS               | feedparser              | Diario               | BAJA       | JSON + Markdown      |

---

## 7. Jerarquía del Grupo Empresarial Manuelita (confirmado)

```
MANUELITA S.A. (Holding corporativo — Cali, Colombia)
│
├── PLATAFORMA CAÑA DE AZÚCAR
│   ├── Manuelita Azúcar y Energía — Valle del Cauca, Colombia
│   │   ├── Azúcar refinada (487,000 ton/año)
│   │   ├── Bioetanol combustible (275M litros/año)
│   │   └── Bioetanol industrial (6.8M litros/año)
│   └── Agroindustrial Laredo S.A. — Trujillo, Perú
│
├── PLATAFORMA ACEITE DE PALMA
│   ├── Manuelita Aceites y Energía — Meta, Colombia
│   └── Palmar de Altamira — Casanare, Colombia
│       ├── Aceite crudo de palma (144,000 ton/año)
│       ├── Aceite de palmiste (14,000 ton/año)
│       └── Biodiesel (137M litros/año)
│
├── PLATAFORMA ACUICULTURA
│   ├── Mejillones América — Puerto Montt, Chile (mejillones)
│   └── Océanos — Cartagena, Colombia (camarón exportación)
│
├── PLATAFORMA FRUTAS Y HORTALIZAS
│   └── Manuelita Frutas y Hortalizas — uvas de mesa y hortalizas frescas
│
└── CENTROS DE INNOVACIÓN
    └── Manuelita Innova — https://manuelitainnova.com/
```

---

*Documento generado: 2026-04-18 | Nivel de confianza del mapa: ALTO | Fuentes verificadas: búsqueda pública + datos del sitio oficial*
