"""
app.py
------
Interfaz Streamlit para el Sistema Q&A de Manuelita S.A.
Módulo 1 — Base de Conocimiento Semántico

Ejecutar con:
    uv run streamlit run app.py
    # o
    streamlit run app.py
"""

import streamlit as st
from src.langchain_app.qa_system import ManuelitaQASystem, MODEL_NAME

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="Manuelita Q&A — Asistente Virtual",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# ESTILOS CSS
# ============================================================
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1a472a, #2d7a3a);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1rem;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
    }
    .answer-box {
        background: #f8f9fa;
        border-left: 4px solid #2d7a3a;
        padding: 1.2rem 1.5rem;
        border-radius: 0 8px 8px 0;
        margin-top: 1rem;
    }
    .metric-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# INICIALIZAR SISTEMA (una sola vez con caché)
# ============================================================
@st.cache_resource(show_spinner="🌱 Cargando corpus de Manuelita S.A. ...")
def get_qa_system():
    return ManuelitaQASystem(model_name=MODEL_NAME)

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.image("https://img.shields.io/badge/Manuelita-S.A.-2d7a3a?style=for-the-badge", use_container_width=True)
    st.markdown("### 🌱 Sistema Q&A")
    st.markdown("**Módulo 1** — Base de Conocimiento Semántico")
    st.divider()

    st.markdown("**📚 Corpus:**")
    st.markdown("- Perfil corporativo oficial")
    st.markdown("- Informes sostenibilidad 2021–2024")
    st.markdown("- Datos financieros Supersociedades")
    st.markdown("- LinkedIn y YouTube")
    st.divider()

    st.markdown(f"**🤖 Modelo:** `{MODEL_NAME}`")
    st.markdown("**🔗 Framework:** LangChain")
    st.markdown("**⚡ Motor:** Ollama (local)")
    st.divider()

    st.caption("Universidad Autónoma de Occidente · 2026")
    st.caption("Módulo 1 — Ingeniería de Sistemas")

# ============================================================
# HEADER PRINCIPAL
# ============================================================
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size:1.8rem;">🌱 Manuelita S.A. — Asistente Virtual</h1>
    <p style="margin:0.3rem 0 0 0; opacity:0.9;">
        Sistema Q&A basado en corpus OSINT · LangChain + Ollama · Prompt Engineering
    </p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# CARGAR SISTEMA
# ============================================================
try:
    qa = get_qa_system()
    st.success("✅ Sistema listo — Corpus cargado correctamente", icon="🌱")
except Exception as e:
    st.error(f"❌ Error al iniciar el sistema: {e}")
    st.info("💡 Verifica que Ollama esté corriendo: `ollama serve`")
    st.stop()

# ============================================================
# TABS PRINCIPALES
# ============================================================
tab1, tab2, tab3 = st.tabs(["📝 Resumen Ejecutivo", "❓ Preguntas Frecuentes", "💬 Q&A Libre"])

# ----------------------------
# TAB 1 — RESUMEN
# ----------------------------
with tab1:
    st.subheader("📝 Resumen Ejecutivo de Manuelita S.A.")
    st.markdown("Genera un resumen estructurado con la información más relevante de la empresa.")

    if st.button("🚀 Generar Resumen", type="primary", use_container_width=True):
        with st.spinner("Generando resumen ejecutivo..."):
            resumen = qa.get_resumen()
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.markdown(resumen)
        st.markdown('</div>', unsafe_allow_html=True)

        # Botón de descarga
        st.download_button(
            label="⬇️ Descargar Resumen",
            data=resumen,
            file_name="manuelita_resumen_ejecutivo.txt",
            mime="text/plain",
        )

# ----------------------------
# TAB 2 — FAQ
# ----------------------------
with tab2:
    st.subheader("❓ Preguntas Frecuentes sobre Manuelita S.A.")
    st.markdown("Genera automáticamente las 15 preguntas más relevantes que haría un cliente o colaborador.")

    if st.button("🚀 Generar FAQ", type="primary", use_container_width=True):
        with st.spinner("Generando preguntas frecuentes..."):
            faq = qa.get_faq()
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.markdown(faq)
        st.markdown('</div>', unsafe_allow_html=True)

        st.download_button(
            label="⬇️ Descargar FAQ",
            data=faq,
            file_name="manuelita_faq.txt",
            mime="text/plain",
        )

# ----------------------------
# TAB 3 — Q&A LIBRE
# ----------------------------
with tab3:
    st.subheader("💬 Pregunta lo que quieras sobre Manuelita S.A.")
    st.markdown("El asistente responde basándose **únicamente** en la información del corpus oficial.")

    # Preguntas de ejemplo
    st.markdown("**💡 Ejemplos de preguntas:**")
    example_cols = st.columns(3)
    examples = [
        "¿En qué año fue fundada Manuelita?",
        "¿Cuál fue el EBITDA de Manuelita en 2023?",
        "¿Qué productos exporta Manuelita?",
        "¿Cuántos litros de bioetanol produce Manuelita?",
        "¿Cuál es la meta de carbono de Manuelita para 2030?",
        "¿En qué países opera Manuelita?",
    ]

    for i, example in enumerate(examples):
        with example_cols[i % 3]:
            if st.button(example, key=f"ex_{i}", use_container_width=True):
                st.session_state["pregunta_actual"] = example

    st.divider()

    # Campo de pregunta
    pregunta = st.text_input(
        "✍️ Escribe tu pregunta:",
        value=st.session_state.get("pregunta_actual", ""),
        placeholder="Ej: ¿Cuántas toneladas de azúcar produce Manuelita por año?",
        key="input_pregunta",
    )

    if st.button("🔍 Preguntar", type="primary", use_container_width=True):
        if pregunta.strip():
            with st.spinner("Buscando respuesta en el corpus..."):
                respuesta = qa.answer_question(pregunta)

            st.markdown(f"**🙋 Pregunta:** {pregunta}")
            st.markdown('<div class="answer-box">', unsafe_allow_html=True)
            st.markdown(f"**🤖 Respuesta:**\n\n{respuesta}")
            st.markdown('</div>', unsafe_allow_html=True)

            # Guardar en historial
            if "historial" not in st.session_state:
                st.session_state["historial"] = []
            st.session_state["historial"].append({
                "pregunta": pregunta,
                "respuesta": respuesta,
            })
        else:
            st.warning("Por favor escribe una pregunta.")

    # Historial de preguntas
    if st.session_state.get("historial"):
        st.divider()
        st.markdown("**📋 Historial de preguntas:**")
        for i, item in enumerate(reversed(st.session_state["historial"][-5:]), 1):
            with st.expander(f"Q{i}: {item['pregunta'][:60]}..."):
                st.markdown(item["respuesta"])
