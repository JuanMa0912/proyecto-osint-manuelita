# Informe tecnico para la definicion de un proyecto de IA avanzada

## Proyecto OSINT Manuelita: inteligencia de fuentes abiertas para analitica organizacional

## 1. Resumen ejecutivo

El proyecto `proyecto-osint-manuelita` constituye una base tecnica para construir un sistema de inteligencia organizacional apoyado en fuentes abiertas. Su proposito es recolectar, procesar, estructurar y analizar informacion publica relacionada con Manuelita S.A. y su entorno agroindustrial, convirtiendo documentos dispersos, noticias, datos financieros, sitios web corporativos y metadatos sociales en un corpus semantico consultable mediante tecnicas de Inteligencia Artificial.

El problema central que aborda el proyecto es la fragmentacion de la informacion publica relevante para la toma de decisiones. En organizaciones agroindustriales con presencia nacional e internacional, la informacion externa influye en reputacion, riesgo regulatorio, posicionamiento competitivo, sostenibilidad, relacionamiento con comunidades, mercados, proveedores e inversionistas. Sin un sistema OSINT estructurado, la organizacion depende de busquedas manuales, monitoreo reactivo y analisis no reproducibles.

La solucion propuesta evoluciona el prototipo actual hacia una plataforma de inteligencia basada en IA que combine: automatizacion de scraping, procesamiento de lenguaje natural, extraccion de entidades, clasificacion tematica, analisis de sentimiento, clustering de narrativas, deteccion de anomalias y un modulo de preguntas y respuestas soportado por evidencia. Esta combinacion permite pasar de un repositorio documental a una capacidad analitica continua, trazable y accionable.

Desde el punto de vista tecnico, el repositorio ya contiene componentes relevantes: scrapers para sitio web, noticias, redes sociales y YouTube; parsing de PDF; normalizacion de entidades; generacion de documentos SMART Markdown; un corpus procesado; y una aplicacion Q&A con LangChain, Ollama y Streamlit. El informe recomienda fortalecer esta arquitectura con indices vectoriales, evaluacion sistematica, taxonomias de riesgo reputacional y modelos supervisados o semi-supervisados para analitica OSINT.

## 2. Proposito del proyecto OSINT

El enfoque OSINT del proyecto consiste en transformar informacion publica en conocimiento estructurado para apoyar decisiones estrategicas y operativas. No se trata solo de recopilar datos; el valor aparece cuando el sistema identifica senales, patrones, entidades, eventos, riesgos y cambios en la conversacion publica.

Los objetivos funcionales son:

- Construir una base de conocimiento publica sobre Manuelita S.A., sus unidades de negocio, presencia geografica, resultados, sostenibilidad y entorno competitivo.
- Automatizar la captura de fuentes abiertas: sitio web oficial, informes PDF, noticias, bases publicas, redes sociales, metadatos de YouTube y fuentes sectoriales.
- Normalizar la informacion en formatos reutilizables, con metadatos, trazabilidad, fechas, fuente, tipo documental y puntaje de confianza.
- Aplicar NLP para extraer entidades, temas, indicadores, relaciones y sentimiento.
- Habilitar consultas en lenguaje natural para usuarios tecnicos y directivos.
- Generar alertas y reportes sobre reputacion, riesgos, eventos relevantes y cambios en el entorno.

En un contexto organizacional, este tipo de sistema permite que areas como comunicaciones, sostenibilidad, riesgos, estrategia, asuntos corporativos, seguridad, legal y analitica cuenten con una vision consolidada de informacion externa.

## 3. Problema a resolver y relevancia practica

### 3.1 Problema de negocio

Las organizaciones agroindustriales estan expuestas a multiples fuentes de presion publica: cambios regulatorios, coyunturas ambientales, conflictos sociales, exigencias de sostenibilidad, variaciones de mercado, reputacion corporativa, seguridad territorial, relacion con proveedores, percepcion de consumidores y actividad de competidores. Buena parte de esas senales aparece primero en fuentes abiertas antes de convertirse en reportes formales.

El problema especifico puede formularse asi:

> Manuelita requiere una capacidad sistematica para monitorear, organizar y analizar informacion publica relevante, con el fin de detectar oportunamente riesgos, oportunidades y narrativas externas que impacten su posicionamiento estrategico y su operacion.

Sin una plataforma OSINT apoyada en IA, aparecen limitaciones claras:

- Baja trazabilidad: los analisis dependen de busquedas individuales y no de pipelines auditables.
- Tiempos altos de respuesta: recopilar noticias, informes y datos publicos consume horas de trabajo manual.
- Duplicidad y ruido: la misma noticia puede aparecer en multiples medios, redes o agregadores.
- Sesgo de cobertura: se privilegian fuentes faciles de encontrar y se omiten fuentes menos visibles.
- Dificultad para priorizar: no toda mencion publica tiene igual impacto reputacional o estrategico.
- Riesgo de interpretacion: titulares, resenas, comentarios o articulos pueden tener tono ambiguo, ironico o incompleto.

### 3.2 Casos de uso prioritarios

El proyecto debe enfocarse inicialmente en casos de uso de alto valor y viabilidad tecnica:

1. Monitoreo reputacional: identificar menciones positivas, negativas o neutras sobre Manuelita, sus productos, operaciones, sostenibilidad y relacionamiento social.
2. Inteligencia competitiva: comparar presencia publica, temas recurrentes y posicionamiento frente a actores agroindustriales similares.
3. Riesgo regulatorio y socioambiental: detectar senales asociadas a sostenibilidad, comunidades, agua, tierra, emisiones, empleo, seguridad alimentaria o cumplimiento.
4. Analisis financiero-publico: integrar datos de Supersociedades, informes corporativos y noticias economicas.
5. Q&A corporativo basado en evidencia: responder preguntas sobre la organizacion a partir del corpus procesado, evitando respuestas sin respaldo documental.
6. Alertas tempranas: identificar cambios inusuales en volumen de menciones, sentimiento negativo, aparicion de nuevas entidades o temas emergentes.

## 4. Estado tecnico del proyecto base

El repositorio ya implementa una primera version de pipeline OSINT y sistema Q&A. Sus componentes principales son:

- Recoleccion: scrapers para sitio web oficial, noticias por Google News RSS, Portafolio, Wikipedia, enlaces sociales y metadatos de YouTube.
- Procesamiento documental: extraccion desde PDF con `pdfplumber`, `PyMuPDF` y fallback OCR con `pytesseract`.
- Normalizacion: limpieza textual, deteccion de entidades, deduplicacion, hashes de contenido y metadatos.
- Almacenamiento intermedio: JSON en `data_processed/json` y documentos Markdown en `data_processed/markdown`.
- Corpus semantico: documentos SMART Markdown con frontmatter, entidades, cifras clave, fuente, confianza y secciones estructuradas.
- Aplicacion Q&A: motor LangChain con Ollama local, modelo `gemma2:latest`, interfaz Streamlit y funciones de resumen, FAQ y preguntas libres.

Una observacion tecnica importante es que el Q&A actual no implementa RAG completo. El sistema carga el corpus o un contexto lexicalmente relevante en el prompt del modelo. Esta decision es razonable para un prototipo academico y un corpus pequeno, pero limita escalabilidad, trazabilidad fina y evaluacion de recuperacion cuando el volumen crezca.

## 5. Analisis tecnico de tecnicas de IA adecuadas

### 5.1 Procesamiento de Lenguaje Natural

NLP es la columna vertebral del proyecto porque la mayoria de fuentes OSINT son no estructuradas o semiestructuradas: articulos, reportes, paginas web, comunicados, descripciones sociales, metadatos audiovisuales y documentos financieros.

Tecnicas recomendadas:

- Limpieza y normalizacion textual: eliminacion de boilerplate, conversion de codificaciones, segmentacion por parrafos, deteccion de idioma y normalizacion de fechas.
- Tokenizacion y lematizacion: utiles para clasificacion, busqueda lexical y reduccion de variabilidad morfologica.
- Extraccion de entidades: organizaciones, personas, ubicaciones, productos, instituciones publicas, indicadores financieros y temas ESG.
- Extraccion de relaciones: asociar entidades con eventos, cargos, ubicaciones, cifras o unidades de negocio.
- Resumen automatico: producir sintesis ejecutivas de documentos largos y clusters de noticias.
- Q&A documental: responder preguntas con soporte en fuentes identificables.

Justificacion:

- El corpus esta dominado por texto en espanol, por lo que herramientas como `spaCy` con modelos en espanol son viables y de bajo costo computacional.
- Los modelos transformer multilingues o especializados en espanol aumentan la precision en tareas complejas como sentimiento, inferencia y clasificacion semantica.
- La combinacion de NLP clasico y embeddings permite equilibrar velocidad, explicabilidad y desempeno.

### 5.2 Clasificacion tematica y analisis de sentimientos

La clasificacion permite convertir menciones publicas en categorias accionables. Para un sistema OSINT corporativo, no basta con saber que una fuente menciona a Manuelita; es necesario saber si la mencion corresponde a sostenibilidad, finanzas, comunidad, empleo, operacion, litigio, seguridad, mercado, innovacion o reputacion.

Taxonomia inicial recomendada:

- Reputacion corporativa.
- Sostenibilidad ambiental.
- Comunidad y relacionamiento social.
- Gobierno corporativo y cumplimiento.
- Resultados financieros.
- Productos y mercados.
- Talento humano y empleo.
- Riesgo regulatorio o legal.
- Innovacion, energia y agroindustria.
- Seguridad operacional o territorial.

Modelos sugeridos:

- Baseline: TF-IDF + regresion logistica o SVM para establecer una linea base interpretable.
- Produccion ligera: embeddings sentence-transformers + clasificador lineal.
- Mayor desempeno: modelos transformer en espanol o multilingues, ajustados con ejemplos etiquetados.
- Zero-shot temporal: modelos NLI multilingues para clasificar categorias cuando aun no exista dataset etiquetado suficiente.

Analisis de sentimiento:

- Clasificacion polar: positivo, negativo, neutro.
- Intensidad: escala de riesgo o criticidad.
- Aspect-based sentiment: sentimiento por tema, por ejemplo sostenibilidad positiva pero finanzas neutras.

Justificacion:

- El sentimiento general puede ser insuficiente para decisiones corporativas. Una noticia critica sobre el sector no necesariamente es negativa para la empresa; por eso conviene clasificar tambien el tema y la entidad afectada.
- Un enfoque incremental permite iniciar con reglas y modelos zero-shot, luego pasar a modelos supervisados cuando exista retroalimentacion de expertos.
- La complejidad computacional es moderada: los modelos ligeros corren en CPU; los transformers pueden ejecutarse por lotes y no requieren inferencia en tiempo real para todas las fuentes.

### 5.3 Extraccion de entidades

NER permite construir un mapa de actores y conceptos relevantes. En OSINT organizacional, las entidades no son solo nombres propios; tambien incluyen unidades de negocio, regiones, productos, indicadores, instituciones y temas sensibles.

Entidades recomendadas:

- Organizaciones: Manuelita S.A., filiales, competidores, proveedores, entidades publicas, gremios.
- Personas: directivos, voceros, autoridades, autores de publicaciones.
- Ubicaciones: paises, departamentos, municipios, zonas de operacion, plantas y mercados.
- Productos: azucar, bioetanol, energia, palma, biodiesel, acuicultura, frutas y hortalizas.
- Indicadores: ingresos, EBITDA, produccion, exportaciones, hectareas, emisiones, inversiones.
- Eventos: reportes, alianzas, conflictos, sanciones, premios, convocatorias, publicaciones.

Herramientas:

- `spaCy` para NER base y reglas con `EntityRuler`.
- Regex y patrones para cifras, unidades, fechas, NIT, porcentajes y montos.
- Modelos transformer ajustados cuando se requiera mayor precision en entidades especializadas.
- Knowledge graph para relaciones entidad-evento-fuente.

Justificacion:

- NER mejora busqueda, filtros, alertas y trazabilidad.
- Las reglas son eficientes para indicadores financieros y unidades, donde los modelos genericos suelen fallar.
- Un grafo de entidades permite analisis longitudinal: quien aparece, con que tema, en que fuente y bajo que sentimiento.

### 5.4 Clustering, modelado de temas y deteccion de anomalias

El monitoreo OSINT no debe limitarse a clasificar documentos individualmente. Tambien debe detectar agrupaciones de narrativas y cambios inusuales en el tiempo.

Clustering recomendado:

- Embeddings de documentos o parrafos.
- HDBSCAN o K-Means para agrupar noticias y menciones similares.
- BERTopic para descubrir topicos emergentes en corpus de noticias y redes.
- Deduplicacion semantica para agrupar articulos replicados por varios medios.

Deteccion de anomalias:

- Volumen de menciones por fuente, tema o entidad.
- Incrementos abruptos de sentimiento negativo.
- Aparicion de entidades nuevas asociadas a la empresa.
- Cambios en la mezcla tematica del corpus.
- Menciones inusuales en fuentes de baja frecuencia pero alta criticidad.

Modelos sugeridos:

- Estadistica robusta: z-score robusto, IQR, EWMA y control charts para series de volumen.
- Isolation Forest para patrones multivariados.
- Autoencoders si el volumen historico es suficiente.
- Reglas de negocio para eventos criticos, por ejemplo menciones a sancion, demanda, protesta, accidente o investigacion.

Justificacion:

- En OSINT, los eventos relevantes suelen manifestarse como cambios de patron, no como documentos aislados.
- HDBSCAN y BERTopic son adecuados para descubrir temas sin imponer categorias rigidas.
- Los metodos estadisticos robustos son explicables y suficientes para alertas iniciales.

### 5.5 Automatizacion de scraping y pipelines de datos

La automatizacion es esencial para que el sistema sea sostenible. El repositorio ya contiene una base adecuada, pero debe formalizarse como pipeline observable y reejecutable.

Componentes recomendados:

- Discovery: identificacion de sitemaps, enlaces, PDFs y fuentes autorizadas.
- Scraping respetuoso: `requests`, `BeautifulSoup`, `feedparser`, APIs oficiales, delays y respeto de `robots.txt`.
- Extraccion: newspaper3k, parsing HTML, extraccion PDF, OCR y metadatos.
- Normalizacion: limpieza, idioma, entidades, hashes, deduplicacion y taxonomia.
- Persistencia: data lake local o nube con capas raw, processed y curated.
- Indexacion: indice lexical, indice vectorial y catalogo de fuentes.
- Orquestacion: tareas programadas con cron, Prefect, Airflow o GitHub Actions segun despliegue.
- Observabilidad: logs, metricas de ejecucion, errores por fuente, cambios de schema y tasas de extraccion.

Justificacion:

- La IA no compensa un pipeline de datos debil. La calidad del resultado depende de trazabilidad, frescura, deduplicacion y control de errores.
- Batch diario o semanal es suficiente para la mayoria de fuentes corporativas y noticias; streaming se reserva para redes sociales, crisis reputacionales o alertas criticas.
- Una arquitectura modular permite reemplazar fuentes o modelos sin reescribir todo el sistema.

## 6. Justificacion de elecciones tecnicas

La solucion recomendada debe equilibrar desempeno, escalabilidad, costo computacional y viabilidad academica/organizacional.

| Decision tecnica | Justificacion | Riesgo controlado |
|---|---|---|
| Python como lenguaje base | Ecosistema maduro para scraping, NLP, ML y automatizacion | Dependencia de ambientes y versiones |
| spaCy + reglas | Rapido, interpretable y adecuado para espanol | Menor precision en dominios especializados |
| Transformers para sentimiento y clasificacion | Mejor desempeno semantico en textos ambiguos | Mayor costo computacional |
| RAG con embeddings | Escala mejor que cargar todo el corpus en prompt | Requiere evaluar recuperacion |
| Indice hibrido BM25 + vectores | Combina precision lexical y similitud semantica | Complejidad adicional |
| Batch para ingesta general | Suficiente para noticias, PDFs y sitios oficiales | Menor inmediatez |
| Streaming solo para alertas criticas | Reduce costo y complejidad operacional | Requiere priorizar fuentes |
| Ollama/local para prototipo | Privacidad y bajo costo de experimentacion | Calidad y latencia dependen del hardware |
| APIs oficiales cuando existan | Mayor estabilidad legal y tecnica | Dependencia de cuotas y credenciales |

La arquitectura debe evitar depender exclusivamente de un LLM. Los modelos de lenguaje son utiles para interaccion, resumen y explicacion, pero la precision OSINT proviene de una cadena completa: captura confiable, metadatos, deduplicacion, clasificacion, recuperacion, validacion y auditoria.

## 7. Solucion integral propuesta

### 7.1 Flujo de datos

```text
Fuentes abiertas
  |-- Sitio oficial Manuelita
  |-- PDFs e informes de sostenibilidad
  |-- Supersociedades y bases publicas
  |-- Noticias y Google News RSS
  |-- YouTube API y metadatos sociales
  |-- Fuentes sectoriales y regulatorias
        |
        v
Ingestion
  |-- Discovery de URLs y documentos
  |-- Scraping/API
  |-- Descarga controlada
  |-- Registro de fuente, fecha y metodo
        |
        v
Procesamiento
  |-- Limpieza y normalizacion
  |-- Extraccion PDF/OCR
  |-- Deduplicacion por hash y similitud
  |-- NER, temas, sentimiento y riesgo
        |
        v
Almacenamiento
  |-- Raw JSON/PDF/HTML
  |-- Processed JSON
  |-- SMART Markdown
  |-- Indice lexical y vectorial
        |
        v
Analitica IA
  |-- Clasificacion tematica
  |-- Sentimiento/aspectos
  |-- Clustering/topicos
  |-- Anomalias y alertas
  |-- Q&A con evidencia
        |
        v
Consumo
  |-- Dashboard ejecutivo
  |-- Alertas reputacionales
  |-- Reportes OSINT
  |-- Chat corporativo
  |-- Exportacion de evidencia
```

### 7.2 Arquitectura batch vs streaming

La recomendacion es una arquitectura hibrida:

- Batch programado para fuentes estables: sitio web, PDFs, Supersociedades, informes y noticias generales. Frecuencia sugerida: diaria para noticias, semanal para sitios corporativos, mensual o bajo demanda para reportes financieros.
- Micro-batch para fuentes dinamicas: RSS, metadatos sociales y busquedas tematicas. Frecuencia sugerida: cada 1 a 6 horas segun criticidad.
- Streaming o near-real-time para escenarios de crisis: menciones negativas, incidentes, palabras clave criticas o fuentes de alta prioridad. No debe ser la arquitectura inicial, sino una extension focalizada.

Esta decision reduce complejidad y costos, manteniendo capacidad de alerta cuando el caso de uso lo justifique.

### 7.3 Arquitectura logica

Capas propuestas:

- Capa de fuentes: conectores para web, RSS, PDFs, APIs, bases publicas y redes con acceso autorizado.
- Capa de ingestion: jobs idempotentes, logs, control de errores, versionado y limites de frecuencia.
- Capa de procesamiento NLP: limpieza, NER, clasificacion, sentimiento, embeddings y enriquecimiento.
- Capa de almacenamiento: raw, processed, curated, indice vectorial y catalogo de metadatos.
- Capa analitica: modelos, dashboards, alertas, clustering y consultas.
- Capa de gobierno: politicas de privacidad, control de acceso, auditoria, calidad y evaluacion.

### 7.4 Herramientas y tecnologias sugeridas

| Componente | Herramientas recomendadas |
|---|---|
| Lenguaje y datos | Python, pandas, pydantic |
| Scraping | requests, BeautifulSoup, feedparser, newspaper3k, Playwright para casos dinamicos |
| PDF/OCR | pdfplumber, PyMuPDF, pytesseract |
| NLP base | spaCy, langdetect, regex, EntityRuler |
| Embeddings | sentence-transformers, modelos multilingues, Ollama embeddings o API privada |
| Clasificacion | scikit-learn, PyTorch, Hugging Face Transformers |
| Topicos/clustering | BERTopic, HDBSCAN, UMAP, scikit-learn |
| Vector store | FAISS, Chroma, Qdrant o pgvector |
| Orquestacion | Prefect, Airflow o tareas programadas |
| LLM/Q&A | LangChain, Ollama local, modelos privados o APIs empresariales |
| Interfaz | Streamlit para prototipo; FastAPI + dashboard para produccion |
| Observabilidad | loguru, MLflow, Evidently, dashboards de metricas |

## 8. Requerimientos de datos

### 8.1 Tipos de fuentes

Fuentes primarias y oficiales:

- Sitio web oficial de Manuelita.
- Informes de sostenibilidad y gobierno corporativo.
- Comunicados, noticias corporativas y paginas de productos.
- Datos financieros publicados o reportes de Supersociedades.

Fuentes secundarias:

- Medios economicos y regionales.
- Google News RSS.
- Wikipedia u otras bases enciclopedicas con trazabilidad.
- Publicaciones sectoriales agroindustriales.

Fuentes sociales y audiovisuales:

- YouTube Data API para metadatos de videos, playlists y canal.
- Metadatos publicos de redes, siempre respetando terminos de uso.
- Comentarios o publicaciones solo si existe autorizacion y cumplimiento normativo.

Fuentes regulatorias y de riesgo:

- Entidades publicas, normatividad, registros empresariales, sanciones publicas, reportes ambientales y bases abiertas.

### 8.2 Volumen esperado

Para un prototipo robusto:

- 100 a 500 documentos procesados.
- 1.000 a 10.000 menciones o registros noticiosos.
- 6 a 24 meses de historico para analisis temporal inicial.
- 300 a 1.000 ejemplos etiquetados para una primera clasificacion supervisada.

Para produccion:

- Ingestion incremental diaria.
- Historico multianual.
- Banco de evaluacion con preguntas, documentos relevantes, etiquetas de sentimiento y categorias de riesgo.
- Muestreo periodico etiquetado por expertos para medir drift y recalibrar modelos.

### 8.3 Calidad y desafios

Principales retos:

- Ruido: menus, cookies, pie de pagina, publicidad y texto repetido.
- Duplicidad: noticias republicadas, agregadores y versiones similares.
- Sesgo de fuente: predominio de fuentes oficiales o de medios con cobertura positiva/negativa.
- Veracidad: informacion publica no siempre es correcta, completa o actualizada.
- Ambiguedad: "Manuelita" puede referirse a marca, empresa, ingenio, fundacion, producto o personas.
- OCR imperfecto: errores en cifras, tablas y nombres propios.
- Cambios de layout: los scrapers pueden romperse ante cambios de sitio.
- Desbalance: eventos negativos o criticos suelen ser menos frecuentes, pero mas importantes.

Controles requeridos:

- Hash de contenido y deduplicacion semantica.
- Puntaje de confianza por fuente y documento.
- Validacion de fechas y URLs.
- Registro de metodo de extraccion.
- Versionamiento de corpus e indices.
- Revision humana de eventos criticos.
- Separacion entre hechos extraidos, inferencias del modelo y opiniones externas.

## 9. Metricas de evaluacion

### 9.1 Modelos de clasificacion y sentimiento

Metricas principales:

- Precision: proporcion de predicciones positivas que son correctas.
- Recall: capacidad de detectar todos los casos relevantes.
- F1-score: balance entre precision y recall.
- Macro-F1: recomendable cuando las clases estan desbalanceadas.
- PR-AUC: util para clases raras, como riesgo alto o crisis reputacional.
- Matriz de confusion por categoria: necesaria para entender errores entre temas cercanos.

Criterios sugeridos:

- Macro-F1 minimo de 0.75 para clasificacion tematica inicial.
- Recall alto en categorias criticas, incluso si baja la precision.
- Evaluacion separada por fuente, porque noticias, PDFs y redes tienen estilos distintos.

### 9.2 NER y extraccion de informacion

Metricas:

- Precision, recall y F1 por tipo de entidad.
- Exact match para entidades normalizadas.
- Tasa de vinculacion correcta entidad-fuente.
- Error en extraccion de cifras y fechas.

Objetivo inicial:

- Alta precision en entidades corporativas y financieras, porque errores en nombres, cargos o cifras afectan confianza ejecutiva.

### 9.3 Recuperacion y Q&A

Metricas:

- Precision@K y Recall@K.
- Mean Reciprocal Rank.
- NDCG.
- Faithfulness: respuesta soportada por evidencia.
- Exactitud factual validada por experto.
- Tasa de abstencion correcta cuando no hay evidencia.
- Porcentaje de respuestas con fuente citada.

Objetivo:

- Mantener trazabilidad documental en todas las respuestas de negocio.
- Penalizar respuestas plausibles sin evidencia, incluso si son linguisticamente correctas.

### 9.4 Sistema y operacion

Metricas:

- Latencia de consulta Q&A.
- Tiempo total de pipeline.
- Tasa de exito por fuente.
- Costo por documento procesado.
- Documentos procesados por minuto.
- Porcentaje de duplicados detectados.
- Frescura del corpus.
- Tiempo medio de deteccion de evento relevante.

### 9.5 Valor para el negocio

Indicadores:

- Reduccion del tiempo de busqueda manual.
- Numero de alertas accionables validadas.
- Cobertura de fuentes criticas.
- Tiempo de respuesta ante menciones negativas.
- Calidad percibida por usuarios directivos y tecnicos.
- Reutilizacion de reportes OSINT en comites de riesgo, comunicaciones o estrategia.

## 10. Riesgos y limitaciones

### 10.1 Riesgos eticos y legales

- Privacidad: aunque las fuentes sean abiertas, el tratamiento de datos personales debe ser proporcional y justificado.
- Terminos de uso: no todas las plataformas permiten scraping directo.
- Perfilamiento indebido: el sistema no debe convertirse en herramienta de vigilancia de individuos.
- Sesgo reputacional: una fuente ruidosa puede amplificar percepciones no representativas.
- Opacidad: los usuarios deben diferenciar entre informacion original, inferencia automatica y conclusion analitica.

Mitigaciones:

- Usar APIs oficiales cuando existan.
- Respetar `robots.txt`, limites de frecuencia y condiciones de cada fuente.
- Minimizar datos personales y evitar almacenamiento innecesario.
- Registrar fuentes, fechas y metodos.
- Aplicar revision humana en alertas de alto impacto.
- Definir una politica de uso responsable de OSINT.

### 10.2 Riesgos tecnicos

- Drift de datos: cambian lenguaje, fuentes, narrativas y distribuciones.
- Alucinaciones del LLM: respuestas no soportadas por el corpus.
- Errores de OCR: cifras y tablas mal extraidas.
- Rotura de scrapers: cambios en HTML o bloqueos.
- Desbalance de clases: pocos ejemplos de riesgos criticos.
- Baja cobertura: fuentes faltantes pueden sesgar el analisis.

Mitigaciones:

- Evaluacion continua con dataset etiquetado.
- RAG con evidencia y citas.
- Monitoreo de drift y calidad de extraccion.
- Alertas por fallas de scraping.
- Versionamiento de modelos e indices.
- Muestreo humano periodico.

### 10.3 Riesgos operativos

- Falta de adopcion por usuarios si el sistema no se integra a flujos reales.
- Exceso de alertas de baja calidad.
- Dependencia de personal tecnico para mantenimiento.
- Falta de responsables para validar taxonomias y etiquetas.
- Expectativas sobredimensionadas sobre capacidades del LLM.

Mitigaciones:

- Disenar tableros por rol: comunicaciones, riesgos, estrategia, sostenibilidad.
- Ajustar umbrales de alerta con retroalimentacion.
- Documentar fuentes y pipelines.
- Definir propietarios de datos y modelos.
- Capacitar a usuarios en interpretacion de resultados.

## 11. Impacto esperado

### 11.1 Impacto estrategico

El proyecto permitiria a la organizacion anticipar cambios en el entorno y responder con mayor oportunidad. Al consolidar fuentes abiertas en una plataforma analitica, la direccion puede observar tendencias reputacionales, narrativas emergentes, actividad de competidores, riesgos socioambientales y senales financieras sin depender exclusivamente de reportes manuales.

Impactos esperados:

- Mayor inteligencia competitiva sobre el sector agroindustrial.
- Mejor lectura de reputacion y sostenibilidad.
- Priorizacion de riesgos basada en evidencia.
- Apoyo a comunicaciones corporativas y relacionamiento con stakeholders.
- Memoria institucional consultable y auditable.

### 11.2 Impacto operativo

En operacion, el sistema reduce tiempos de busqueda, facilita reportes periodicos y mejora la trazabilidad de analisis. Un analista podria pasar de revisar manualmente decenas de fuentes a validar alertas, interpretar clusters y profundizar en eventos de alto valor.

Beneficios operativos:

- Automatizacion de recoleccion y normalizacion.
- Reduccion de duplicados y ruido informativo.
- Consultas en lenguaje natural sobre el corpus.
- Alertas por cambios de volumen, sentimiento o tema.
- Reportes semanales o mensuales generados con evidencia.

## 12. Hoja de ruta recomendada

### Fase 1: Consolidacion del pipeline OSINT

- Fortalecer scrapers existentes.
- Normalizar metadatos minimos: fuente, URL, fecha, tipo, confianza, hash.
- Implementar control de calidad y deduplicacion semantica.
- Ampliar fuentes financieras, regulatorias y sectoriales.

### Fase 2: Analitica NLP

- Definir taxonomia oficial de temas y riesgos.
- Etiquetar un conjunto inicial de documentos.
- Implementar clasificador baseline y modelo de sentimiento.
- Evaluar NER por tipo de entidad.

### Fase 3: RAG y Q&A con evidencia

- Construir chunks semanticos.
- Crear embeddings e indice vectorial.
- Implementar recuperacion hibrida.
- Exigir citas o referencias en respuestas.
- Crear banco de preguntas y respuestas esperadas.

### Fase 4: Alertas y dashboard

- Medir volumen, sentimiento, temas y entidades por periodo.
- Implementar clustering y deteccion de anomalias.
- Construir tablero ejecutivo.
- Disenar alertas con severidad y evidencia.

### Fase 5: Gobierno y mejora continua

- Definir politica de uso responsable.
- Versionar datasets, modelos e indices.
- Medir drift y calidad del sistema.
- Incorporar retroalimentacion de usuarios expertos.

## 13. Recomendacion final

El proyecto debe evolucionar desde un prototipo de corpus y Q&A hacia una plataforma OSINT analitica, gobernada y medible. La prioridad tecnica no debe ser incorporar modelos cada vez mas grandes, sino construir una cadena confiable de datos, metadatos, recuperacion, evaluacion y trazabilidad.

La combinacion recomendada es:

- Pipeline batch para ingestion controlada de fuentes abiertas.
- NLP con spaCy, reglas y modelos transformer para entidades, temas y sentimiento.
- RAG con indices hibridos para responder preguntas con evidencia.
- Clustering y anomalias para detectar narrativas emergentes.
- Dashboard y alertas para convertir analisis en accion organizacional.

Con esta arquitectura, el sistema puede generar valor real para directivos y equipos tecnicos: menos tiempo buscando informacion, mayor capacidad de anticipacion, mejor soporte documental y una lectura mas estructurada del entorno publico que rodea a la organizacion.
