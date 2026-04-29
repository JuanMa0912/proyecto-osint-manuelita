"""
app.py
------
Interfaz Streamlit para el sistema Q&A de Manuelita S.A.

Ejecutar:
    uv run streamlit run app.py
"""

import os

import streamlit as st
from dotenv import load_dotenv

from src.langchain_app.qa_system import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    MODEL_NAME,
    PROVIDER,
    ManuelitaQASystem,
)

load_dotenv()

DEFAULT_TEMPERATURE = 0.1
DEFAULT_TOP_N = 40

EXAMPLE_QUESTIONS = [
    "¿En qué año fue fundada Manuelita?",
    "¿Cuál fue el EBITDA de Manuelita en 2023?",
    "¿Qué productos exporta Manuelita?",
    "¿En qué países opera Manuelita?",
    "¿Cuál es la meta de carbono para 2030?",
    "¿Cuántos litros de bioetanol produce Manuelita?",
]

st.set_page_config(
    page_title="Manuelita AI — Asistente Agroindustrial",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    :root {
        --green-900: #12351f;
        --green-800: #174b2a;
        --green-700: #1f6b3b;
        --green-600: #2a8a4e;
        --green-100: #eaf5ee;
        --cane-500: #c7a24a;
        --cane-100: #f8efd9;
        --soil-700: #5d4730;
        --ink: #17211a;
        --muted: #5f6f63;
        --line: #dce8df;
        --surface: #ffffff;
    }

    /* ── Fondo general ── */
    .stApp {
        background: linear-gradient(160deg, #eaf5ee 0%, #f7f9f4 60%, #ffffff 100%);
        color: var(--ink);
    }

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2c1a 0%, var(--green-900) 40%, var(--green-800) 100%);
        border-right: 1px solid rgba(255,255,255,0.10);
    }
    [data-testid="stSidebar"] * { color: #f0f8f2 !important; }
    [data-testid="stSidebar"] .stRadio label { color: #f0f8f2 !important; }

    /* ── Header principal ── */
    .main-header {
        background: linear-gradient(120deg, rgba(18,53,31,0.97) 0%, rgba(31,107,59,0.93) 100%);
        padding: 1.6rem 2rem;
        border-radius: 12px;
        color: #fff;
        margin-bottom: 1.2rem;
        border: 1px solid rgba(255,255,255,0.15);
        box-shadow: 0 12px 40px rgba(18,53,31,0.18);
        display: flex;
        align-items: center;
        gap: 1.4rem;
    }
    .header-logo {
        font-size: 3rem;
        line-height: 1;
    }
    .header-text h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 800;
        letter-spacing: -0.01em;
    }
    .header-text p {
        margin: 0.3rem 0 0.8rem 0;
        opacity: 0.85;
        font-size: 0.95rem;
    }
    .header-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .chip {
        background: rgba(255,255,255,0.15);
        border: 1px solid rgba(255,255,255,0.22);
        border-radius: 999px;
        padding: 0.22rem 0.7rem;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .chip-gold {
        background: rgba(199,162,74,0.28);
        border-color: rgba(199,162,74,0.5);
    }

    /* ── Tabs ── */
    .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
    .stTabs [data-baseweb="tab"] {
        background: var(--green-800);
        color: #fff !important;
        border: 1px solid var(--green-800);
        border-radius: 8px;
        font-size: 0.95rem;
        font-weight: 600;
        padding: 0.5rem 1.4rem;
        transition: all 0.18s ease;
    }
    .stTabs [data-baseweb="tab"] p { color: inherit !important; }
    .stTabs [data-baseweb="tab"]:hover {
        background: #fff;
        color: var(--green-800) !important;
        border-color: var(--green-800);
    }
    .stTabs [aria-selected="true"] {
        background: var(--green-700) !important;
        border-color: var(--green-700) !important;
    }

    /* ── Tarjetas de info ── */
    .info-grid { display: flex; gap: 0.75rem; margin-bottom: 1.2rem; }
    .info-card {
        flex: 1;
        background: #fff;
        border: 1px solid var(--line);
        border-top: 3px solid var(--green-700);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        box-shadow: 0 2px 12px rgba(18,53,31,0.06);
    }
    .info-label {
        color: var(--muted);
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        font-weight: 700;
    }
    .info-value {
        color: var(--green-800);
        font-size: 1rem;
        font-weight: 800;
        margin-top: 0.2rem;
    }

    /* ── Caja de pregunta ── */
    .question-box {
        background: var(--cane-100);
        border: 1px solid rgba(199,162,74,0.4);
        border-left: 5px solid var(--cane-500);
        padding: 0.9rem 1.2rem;
        border-radius: 8px;
        margin-top: 1rem;
        color: var(--soil-700);
        font-weight: 600;
        font-size: 0.97rem;
    }

    /* ── Caja de respuesta ── */
    .answer-box {
        background: #fff;
        border: 1px solid var(--line);
        border-left: 5px solid var(--green-700);
        padding: 1.3rem 1.6rem;
        border-radius: 8px;
        margin-top: 0.6rem;
        color: #111827;
        box-shadow: 0 4px 20px rgba(18,53,31,0.07);
        line-height: 1.7;
    }

    /* ── Botones de ejemplo ── */
    .example-btn > div > button {
        background: #fff !important;
        border: 1px solid var(--green-700) !important;
        color: var(--green-800) !important;
        border-radius: 999px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 0.3rem 0.9rem !important;
        transition: all 0.15s ease !important;
    }
    .example-btn > div > button:hover {
        background: var(--green-700) !important;
        color: #fff !important;
    }

    /* ── Botón primario ── */
    div.stButton > button[kind="primary"] {
        background: var(--green-800);
        border: none;
        border-radius: 8px;
        font-weight: 700;
        font-size: 1rem;
        letter-spacing: 0.01em;
        padding: 0.6rem 1.2rem;
    }
    div.stButton > button[kind="primary"]:hover {
        background: var(--green-700);
    }

    /* ── Historial ── */
    .stExpander { border: 1px solid var(--line) !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)


# ── Cache & sistema ──────────────────────────────────────────
@st.cache_resource(show_spinner="🌱 Cargando corpus de Manuelita S.A. ...")
def get_qa_system(provider: str, gemini_api_key: str = "") -> ManuelitaQASystem:
    return ManuelitaQASystem(
        provider=provider,
        model_name=MODEL_NAME,
        gemini_api_key=gemini_api_key,
    )


def apply_model_settings(qa: ManuelitaQASystem, temperature: float, top_n: int) -> None:
    try:
        qa.llm.temperature = temperature
        if hasattr(qa.llm, "top_k"):
            qa.llm.top_k = top_n
    except Exception:
        pass


# ── Sidebar ──────────────────────────────────────────────────
def render_sidebar() -> tuple[float, int, str, str]:
    with st.sidebar:
        st.markdown("## 🌱 Manuelita S.A.")
        st.markdown("**Asistente de Inteligencia Agroindustrial**")
        st.divider()

        st.markdown("#### Motor de IA")
        provider_options = {"🖥️ Ollama (local)": "ollama", "✨ Google Gemini (gratis)": "gemini"}
        provider_label = st.radio(
            "Proveedor:",
            options=list(provider_options.keys()),
            index=0 if PROVIDER == "ollama" else 1,
            label_visibility="collapsed",
        )
        selected_provider = provider_options[provider_label]

        gemini_key = GEMINI_API_KEY
        if selected_provider == "gemini":
            if not GEMINI_API_KEY:
                gemini_key = st.text_input(
                    "API Key de Gemini",
                    type="password",
                    placeholder="Obtén tu key en aistudio.google.com",
                )
            else:
                st.success(f"✅ `{GEMINI_MODEL}`")
                st.caption("Capa gratuita · AI Studio · Sin facturación")

        st.divider()
        st.markdown("#### Parámetros del modelo")
        temperature = st.slider("Temperature", 0.0, 1.0, DEFAULT_TEMPERATURE, 0.05,
            help="Baja = más preciso · Alta = más creativo")
        top_n = st.slider("Top N", 1, 100, DEFAULT_TOP_N, 1,
            help="Candidatos por paso de generación")
        st.caption(f"T {temperature:.2f} · Top N {top_n}")

        st.divider()
        st.markdown("#### Corpus")
        st.caption("📄 Perfil corporativo oficial")
        st.caption("📊 Datos financieros Supersociedades")
        st.caption("♻️ Informes de sostenibilidad")
        st.caption("🔗 LinkedIn · YouTube · OSINT")

        st.divider()
        if selected_provider == "gemini":
            st.markdown(f"**Modelo** `{GEMINI_MODEL}`")
            st.markdown("**Motor** Google Gemini API")
            st.markdown("**Tier** Free — AI Studio")
        else:
            st.markdown(f"**Modelo** `{MODEL_NAME}`")
            st.markdown("**Motor** Ollama local")
        st.markdown("**Framework** LangChain")

        st.divider()
        st.caption("Universidad Autónoma de Occidente · 2026")
        st.caption("Módulo 1 — Ingeniería de Sistemas")

    return temperature, top_n, selected_provider, gemini_key


# ── Header ───────────────────────────────────────────────────
def render_header(provider: str, temperature: float, top_n: int) -> None:
    model_display = GEMINI_MODEL if provider == "gemini" else MODEL_NAME
    motor_display = "Google Gemini API" if provider == "gemini" else "Ollama local"
    st.markdown(f"""
<div class="main-header">
    <div class="header-logo">🌱</div>
    <div class="header-text">
        <h1>Manuelita S.A. — Asistente Agroindustrial</h1>
        <p>Consulta corporativa, financiera y operativa desde corpus OSINT enriquecido</p>
        <div class="header-chips">
            <span class="chip chip-gold">🤖 {model_display}</span>
            <span class="chip">{motor_display}</span>
            <span class="chip">LangChain</span>
            <span class="chip">T {temperature:.2f}</span>
            <span class="chip">Agroindustria sostenible</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Tarjetas de info ──────────────────────────────────────────
def render_info_cards(qa: ManuelitaQASystem, provider: str, temperature: float, top_n: int) -> None:
    model_display = GEMINI_MODEL if provider == "gemini" else MODEL_NAME
    st.markdown(f"""
<div class="info-grid">
    <div class="info-card">
        <div class="info-label">Modelo activo</div>
        <div class="info-value">{model_display}</div>
    </div>
    <div class="info-card">
        <div class="info-label">Corpus cargado</div>
        <div class="info-value">{len(qa.corpus):,} caracteres</div>
    </div>
    <div class="info-card">
        <div class="info-label">Configuración</div>
        <div class="info-value">T {temperature:.2f} · Top N {top_n}</div>
    </div>
    <div class="info-card">
        <div class="info-label">Arquitectura</div>
        <div class="info-value">Corpus → Prompt → LLM</div>
    </div>
</div>
""", unsafe_allow_html=True)


# ── Tabs ──────────────────────────────────────────────────────
def render_summary_tab(qa: ManuelitaQASystem) -> None:
    st.subheader("📝 Resumen Ejecutivo")
    st.markdown("Genera un resumen estructurado con la información más relevante de la empresa.")
    if st.button("Generar Resumen", type="primary", use_container_width=True):
        with st.spinner("Generando resumen ejecutivo..."):
            resumen = qa.get_resumen()
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.markdown(resumen)
        st.markdown('</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Descargar Resumen", data=resumen,
            file_name="manuelita_resumen.txt", mime="text/plain")


def render_faq_tab(qa: ManuelitaQASystem) -> None:
    st.subheader("❓ Preguntas Frecuentes")
    st.markdown("Genera automáticamente las 15 preguntas más relevantes sobre la empresa.")
    if st.button("Generar FAQ", type="primary", use_container_width=True):
        with st.spinner("Generando preguntas frecuentes..."):
            faq = qa.get_faq()
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.markdown(faq)
        st.markdown('</div>', unsafe_allow_html=True)
        st.download_button("⬇️ Descargar FAQ", data=faq,
            file_name="manuelita_faq.txt", mime="text/plain")


def render_qa_tab(qa: ManuelitaQASystem) -> None:
    st.subheader("💬 Pregunta lo que quieras")
    st.markdown("El asistente responde basándose **únicamente** en el corpus oficial.")

    question = st.text_input(
        "✍️ Escribe tu pregunta:",
        value=st.session_state.get("pregunta_actual", ""),
        placeholder="Ej: ¿Cuántas toneladas de azúcar produce Manuelita por año?",
        key="input_pregunta",
    )

    if st.button("🔍 Preguntar", type="primary", use_container_width=True):
        if not question.strip():
            st.warning("Por favor escribe una pregunta.")
            return

        with st.spinner("Consultando el corpus..."):
            answer = qa.answer_question(question)

        st.markdown(f'<div class="question-box">🙋 {question}</div>', unsafe_allow_html=True)
        st.markdown('<div class="answer-box">', unsafe_allow_html=True)
        st.markdown(f"**🤖 Respuesta:**\n\n{answer}")
        st.markdown('</div>', unsafe_allow_html=True)

        if "historial" not in st.session_state:
            st.session_state["historial"] = []
        st.session_state["historial"].append({"pregunta": question, "respuesta": answer})

    # Historial
    if st.session_state.get("historial"):
        st.divider()
        st.markdown("**📋 Historial:**")
        for i, item in enumerate(reversed(st.session_state["historial"][-5:]), 1):
            with st.expander(f"Q{i}: {item['pregunta'][:65]}..."):
                st.markdown(item["respuesta"])


# ── Main ──────────────────────────────────────────────────────
def load_system(provider: str, gemini_key: str) -> ManuelitaQASystem:
    try:
        qa = get_qa_system(provider=provider, gemini_api_key=gemini_key)
        return qa
    except Exception as exc:
        st.error(f"❌ Error al iniciar el sistema: {exc}")
        if provider == "ollama":
            st.info("Verifica que Ollama esté corriendo: `ollama serve`")
        else:
            st.info("Verifica que GEMINI_API_KEY sea válida en tu archivo `.env`")
        st.stop()


def main() -> None:
    temperature, top_n, provider, gemini_key = render_sidebar()
    render_header(provider, temperature, top_n)

    qa = load_system(provider, gemini_key)
    apply_model_settings(qa, temperature, top_n)
    render_info_cards(qa, provider, temperature, top_n)

    summary_tab, faq_tab, qa_tab = st.tabs([
        "📝 Resumen Ejecutivo",
        "❓ Preguntas Frecuentes",
        "💬 Q&A Libre",
    ])

    with summary_tab:
        render_summary_tab(qa)
    with faq_tab:
        render_faq_tab(qa)
    with qa_tab:
        render_qa_tab(qa)


if __name__ == "__main__":
    main()
