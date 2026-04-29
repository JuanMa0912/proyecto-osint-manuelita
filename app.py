"""
app.py
------
Interfaz Streamlit para el sistema Q&A de Manuelita S.A.

Ejecutar:
    uv run streamlit run app.py
"""

import streamlit as st

from src.langchain_app.qa_system import MODEL_NAME, ManuelitaQASystem


st.set_page_config(
    page_title="Manuelita Q&A - Asistente Virtual",
    page_icon="M",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
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
        color: #111827;
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Cargando corpus de Manuelita S.A. ...")
def get_qa_system() -> ManuelitaQASystem:
    return ManuelitaQASystem(model_name=MODEL_NAME)


def render_sidebar() -> None:
    with st.sidebar:
        st.image(
            "https://img.shields.io/badge/Manuelita-S.A.-2d7a3a?style=for-the-badge",
            use_container_width=True,
        )
        st.markdown("### Sistema Q&A")
        st.markdown("**Modulo 1** - Base de Conocimiento Semantico")
        st.divider()

        st.markdown("**Corpus:**")
        st.markdown("- Perfil corporativo oficial")
        st.markdown("- Informes de sostenibilidad")
        st.markdown("- Datos financieros Supersociedades")
        st.markdown("- LinkedIn y YouTube")
        st.divider()

        st.markdown(f"**Modelo:** `{MODEL_NAME}`")
        st.markdown("**Framework:** LangChain")
        st.markdown("**Motor:** Ollama local")
        st.divider()

        st.caption("Universidad Autonoma de Occidente - 2026")
        st.caption("Modulo 1 - Ingenieria de Sistemas")


def render_header() -> None:
    st.markdown(
        """
<div class="main-header">
    <h1 style="margin:0; font-size:1.8rem;">Manuelita S.A. - Asistente Virtual</h1>
    <p style="margin:0.3rem 0 0 0; opacity:0.9;">
        Sistema Q&A basado en corpus OSINT | LangChain + Ollama | Prompt Engineering
    </p>
</div>
""",
        unsafe_allow_html=True,
    )


def render_answer_box(content: str) -> None:
    st.markdown('<div class="answer-box">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div>", unsafe_allow_html=True)


def render_summary_tab(qa: ManuelitaQASystem) -> None:
    st.subheader("Resumen ejecutivo de Manuelita S.A.")
    st.markdown("Genera un resumen estructurado con la informacion mas relevante de la empresa.")

    if st.button("Generar Resumen", type="primary", use_container_width=True):
        with st.spinner("Generando resumen ejecutivo..."):
            resumen = qa.get_resumen()

        render_answer_box(resumen)
        st.download_button(
            label="Descargar Resumen",
            data=resumen,
            file_name="manuelita_resumen_ejecutivo.txt",
            mime="text/plain",
        )


def render_faq_tab(qa: ManuelitaQASystem) -> None:
    st.subheader("Preguntas frecuentes sobre Manuelita S.A.")
    st.markdown("Genera automaticamente 15 preguntas frecuentes basadas en el corpus.")

    if st.button("Generar FAQ", type="primary", use_container_width=True):
        with st.spinner("Generando preguntas frecuentes..."):
            faq = qa.get_faq()

        render_answer_box(faq)
        st.download_button(
            label="Descargar FAQ",
            data=faq,
            file_name="manuelita_faq.txt",
            mime="text/plain",
        )


def save_question_to_history(question: str, answer: str) -> None:
    if "historial" not in st.session_state:
        st.session_state["historial"] = []

    st.session_state["historial"].append({
        "pregunta": question,
        "respuesta": answer,
    })


def render_history() -> None:
    if not st.session_state.get("historial"):
        return

    st.divider()
    st.markdown("**Historial de preguntas:**")
    for index, item in enumerate(reversed(st.session_state["historial"][-5:]), 1):
        with st.expander(f"Q{index}: {item['pregunta'][:60]}..."):
            st.markdown(item["respuesta"])


def render_qa_tab(qa: ManuelitaQASystem) -> None:
    st.subheader("Pregunta lo que quieras sobre Manuelita S.A.")
    st.markdown("El asistente responde basandose unicamente en la informacion del corpus.")

    question = st.text_input(
        "Escribe tu pregunta:",
        placeholder="Ej: Cual es el presidente de Manuelita?",
        key="input_pregunta",
    )

    if st.button("Preguntar", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Por favor escribe una pregunta.")
            return

        with st.spinner("Buscando respuesta en el corpus..."):
            answer = qa.answer_question(question)

        st.markdown(f"**Pregunta:** {question}")
        render_answer_box(f"**Respuesta:**\n\n{answer}")
        save_question_to_history(question, answer)

    render_history()


def load_system() -> ManuelitaQASystem:
    try:
        qa = get_qa_system()
        st.success("Sistema listo - Corpus cargado correctamente")
        return qa
    except Exception as exc:
        st.error(f"Error al iniciar el sistema: {exc}")
        st.info("Verifica que Ollama este corriendo: `ollama serve`")
        st.stop()


def main() -> None:
    render_sidebar()
    render_header()

    qa = load_system()
    summary_tab, faq_tab, qa_tab = st.tabs([
        "Resumen Ejecutivo",
        "Preguntas Frecuentes",
        "Q&A Libre",
    ])

    with summary_tab:
        render_summary_tab(qa)
    with faq_tab:
        render_faq_tab(qa)
    with qa_tab:
        render_qa_tab(qa)


if __name__ == "__main__":
    main()
