"""
app.py
------
Interfaz Streamlit para el sistema Q&A de Manuelita S.A.

Ejecutar:
    uv run streamlit run app.py
"""

import streamlit as st

from src.langchain_app.qa_system import MODEL_NAME, ManuelitaQASystem


DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_N = 40


st.set_page_config(
    page_title="Manuelita AI - Agroindustrial",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)


st.markdown(
    """
<style>
    :root {
        --green-900: #12351f;
        --green-800: #174b2a;
        --green-700: #1f6b3b;
        --green-100: #eaf5ee;
        --cane-500: #c7a24a;
        --cane-100: #f8efd9;
        --soil-700: #5d4730;
        --ink: #17211a;
        --muted: #5f6f63;
        --line: #dce8df;
        --surface: #ffffff;
    }

    .stApp {
        background:
            linear-gradient(180deg, rgba(234,245,238,0.95) 0%, rgba(255,255,255,0.98) 38%, #f7f9f4 100%);
        color: var(--ink);
    }

    [data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, var(--green-900) 0%, var(--green-800) 58%, #0f2c1a 100%);
        border-right: 1px solid rgba(255,255,255,0.12);
    }

    [data-testid="stSidebar"] * {
        color: #f6fbf7;
    }

    [data-testid="stSidebar"] .stSlider label,
    [data-testid="stSidebar"] .stMarkdown,
    [data-testid="stSidebar"] .stCaption {
        color: #f6fbf7 !important;
    }

    .main-header {
        background:
            linear-gradient(120deg, rgba(18,53,31,0.96), rgba(31,107,59,0.92)),
            linear-gradient(45deg, rgba(199,162,74,0.22), transparent);
        padding: 1.4rem 1.6rem;
        border-radius: 8px;
        color: #ffffff;
        margin-bottom: 1.5rem;
        border: 1px solid rgba(255,255,255,0.18);
        box-shadow: 0 18px 42px rgba(18,53,31,0.16);
    }
    .main-header h1 {
        letter-spacing: 0;
    }
    .header-kpis {
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        margin-top: 0.9rem;
    }
    .header-chip {
        background: rgba(255,255,255,0.14);
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 999px;
        padding: 0.28rem 0.72rem;
        font-size: 0.84rem;
        font-weight: 650;
    }
    .stTabs [data-baseweb="tab"] {
        background: var(--green-800);
        color: #ffffff;
        border: 1px solid var(--green-800);
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        padding: 0.5rem 1.5rem;
        margin-right: 0.45rem;
        transition: background 0.18s ease, color 0.18s ease, border-color 0.18s ease;
    }
    .stTabs [data-baseweb="tab"] p {
        color: inherit;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background: #ffffff;
        color: var(--green-800);
        border-color: var(--green-800);
    }
    .stTabs [aria-selected="true"] {
        background: var(--green-700);
        color: #ffffff;
        border-color: var(--green-700);
    }
    .stTabs [aria-selected="true"]:hover {
        background: #ffffff;
        color: var(--green-700);
        border-color: var(--green-700);
    }
    .answer-box {
        background: var(--surface);
        border: 1px solid var(--line);
        border-left: 5px solid var(--green-700);
        padding: 1.2rem 1.5rem;
        border-radius: 8px;
        margin-top: 1rem;
        color: #111827;
        box-shadow: 0 10px 28px rgba(18,53,31,0.06);
    }
    .question-box {
        background: var(--cane-100);
        border: 1px solid rgba(199,162,74,0.45);
        border-left: 5px solid var(--cane-500);
        padding: 0.95rem 1.1rem;
        border-radius: 8px;
        margin-top: 1rem;
        color: var(--soil-700);
        font-weight: 650;
    }
    .metric-card {
        background: rgba(255,255,255,0.78);
        border: 1px solid rgba(220,232,223,0.95);
        border-radius: 8px;
        padding: 0.85rem 1rem;
        margin-bottom: 0.75rem;
    }
    .metric-label {
        color: var(--muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.04rem;
        font-weight: 750;
    }
    .metric-value {
        color: var(--green-800);
        font-size: 1.05rem;
        font-weight: 800;
        margin-top: 0.15rem;
    }
    div.stButton > button {
        border-radius: 8px;
        border: 1px solid var(--green-700);
        font-weight: 700;
    }
    div.stButton > button[kind="primary"] {
        background: var(--green-800);
        border-color: var(--green-800);
    }
</style>
""",
    unsafe_allow_html=True,
)


@st.cache_resource(show_spinner="Cargando corpus de Manuelita S.A. ...")
def get_qa_system() -> ManuelitaQASystem:
    return ManuelitaQASystem(model_name=MODEL_NAME)


def apply_model_settings(qa: ManuelitaQASystem, temperature: float, top_n: int) -> None:
    """Aplica parametros interactivos al modelo Ollama cacheado."""
    qa.llm.temperature = temperature
    qa.llm.top_k = top_n


def render_sidebar() -> tuple[float, int]:
    with st.sidebar:
        st.image(
            "https://img.shields.io/badge/Manuelita-S.A.-2d7a3a?style=for-the-badge",
            use_container_width=True,
        )
        st.markdown("### Asistente Agroindustrial")
        st.markdown("Consulta semantica sobre Manuelita S.A.")
        st.divider()

        st.markdown("### Parametros del modelo")
        temperature = st.slider(
            "Temperature",
            min_value=0.0,
            max_value=1.0,
            value=DEFAULT_TEMPERATURE,
            step=0.05,
            help="Valores bajos hacen respuestas mas precisas; valores altos aumentan variacion.",
        )
        top_n = st.slider(
            "Top N",
            min_value=1,
            max_value=100,
            value=DEFAULT_TOP_N,
            step=1,
            help="Cantidad de candidatos considerados por el modelo en cada paso de generacion.",
        )
        st.caption(f"Configuracion activa: Temperature {temperature:.2f} · Top N {top_n}")
        st.divider()

        st.markdown("### Base de conocimiento")
        st.markdown("- Perfil corporativo oficial")
        st.markdown("- Informes de sostenibilidad")
        st.markdown("- Datos financieros")
        st.markdown("- Redes y fuentes OSINT")
        st.divider()

        st.markdown(f"**Modelo:** `{MODEL_NAME}`")
        st.markdown("**Motor:** Ollama local")
        st.markdown("**Framework:** LangChain")
        st.divider()

        st.caption("Universidad Autonoma de Occidente")
        st.caption("Proyecto OSINT Agroindustrial")

    return temperature, top_n


def render_header(temperature: float, top_n: int) -> None:
    st.markdown(
        f"""
<div class="main-header">
    <h1 style="margin:0; font-size:1.9rem;">Manuelita S.A. - Inteligencia Agroindustrial</h1>
    <p style="margin:0.3rem 0 0 0; opacity:0.9;">
        Consulta informacion corporativa, financiera y operativa desde un corpus OSINT enriquecido.
    </p>
    <div class="header-kpis">
        <span class="header-chip">Corpus semantico</span>
        <span class="header-chip">Temperature {temperature:.2f}</span>
        <span class="header-chip">Top N {top_n}</span>
        <span class="header-chip">Agroindustria sostenible</span>
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_answer_box(content: str) -> None:
    st.markdown('<div class="answer-box">', unsafe_allow_html=True)
    st.markdown(content)
    st.markdown("</div>", unsafe_allow_html=True)


def render_question_box(content: str) -> None:
    st.markdown(f'<div class="question-box">Pregunta: {content}</div>', unsafe_allow_html=True)


def render_info_cards(qa: ManuelitaQASystem, temperature: float, top_n: int) -> None:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Modelo</div>'
            f'<div class="metric-value">{MODEL_NAME}</div></div>',
            unsafe_allow_html=True,
        )
    with col2:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Corpus</div>'
            f'<div class="metric-value">{len(qa.corpus):,} caracteres</div></div>',
            unsafe_allow_html=True,
        )
    with col3:
        st.markdown(
            f'<div class="metric-card"><div class="metric-label">Generacion</div>'
            f'<div class="metric-value">T {temperature:.2f} · Top N {top_n}</div></div>',
            unsafe_allow_html=True,
        )


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

        render_question_box(question)
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
    temperature, top_n = render_sidebar()
    render_header(temperature, top_n)

    qa = load_system()
    apply_model_settings(qa, temperature, top_n)
    render_info_cards(qa, temperature, top_n)

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
