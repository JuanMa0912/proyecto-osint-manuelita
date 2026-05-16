"""
app.py
------
Interfaz Streamlit — Agente Conversacional de Manuelita S.A.
Módulo 2, Bloque 5.

Cambios respecto al Módulo 1:
  - Chat conversacional con historial (burbujas de mensaje)
  - Motor: ContextualAgent (HybridRouter + ConversationBufferWindowMemory)
  - Indicador de fuente por mensaje (RAG vs Datos Estructurados)
  - Selector de proveedor en sidebar (gemini / local / ollama)
  - Botón de nueva conversación (reset de memoria)
  - Preguntas de ejemplo integradas en la UI de chat
  - Tabs: Chat | Resumen | FAQ (Módulo 1 conservado)

Ejecutar:
    uv run streamlit run app.py

    # Con proveedor específico:
    $env:LLM_PROVIDER="gemini"; uv run streamlit run app.py
    $env:LLM_PROVIDER="local";  uv run streamlit run app.py
"""

import os
import time

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

PROVIDER       = os.getenv("LLM_PROVIDER", "local")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL   = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemma3:1b")

try:
    from src.langchain_app.qa_system import MODEL_NAME
except ImportError:
    MODEL_NAME = OLLAMA_MODEL

MEMORY_WINDOW = int(os.getenv("MEMORY_WINDOW", "5"))

EXAMPLE_QUESTIONS = [
    "¿Cuál es el NIT de Manuelita?",
    "¿Quién es el presidente de Manuelita?",
    "¿En qué países opera Manuelita?",
    "¿Cuántos empleados tiene?",
    "¿Cuáles fueron los ingresos en 2023?",
    "¿Cuál es la meta de carbono para 2030?",
    "¿Cuáles son los valores corporativos?",
    "¿Cómo gestiona Manuelita la sostenibilidad ambiental?",
]

st.set_page_config(
    page_title="Manuelita AI — Agente Conversacional",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    :root {
        --green-900: #12351f; --green-800: #174b2a; --green-700: #1f6b3b;
        --cane-500: #c7a24a; --cane-100: #f8efd9; --soil-700: #5d4730;
        --ink: #17211a; --muted: #5f6f63; --line: #dce8df;
    }
    .stApp {
        background: linear-gradient(160deg, #eaf5ee 0%, #f7f9f4 60%, #ffffff 100%);
        color: var(--ink);
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f2c1a 0%, var(--green-900) 40%, var(--green-800) 100%);
        border-right: 1px solid rgba(255,255,255,0.10);
    }
    [data-testid="stSidebar"] * { color: #f0f8f2 !important; }
    .main-header {
        background: linear-gradient(120deg, rgba(18,53,31,0.97) 0%, rgba(31,107,59,0.93) 100%);
        padding: 1.4rem 2rem; border-radius: 12px; color: #fff; margin-bottom: 1.2rem;
        border: 1px solid rgba(255,255,255,0.15); box-shadow: 0 12px 40px rgba(18,53,31,0.18);
        display: flex; align-items: center; gap: 1.4rem;
    }
    .header-logo { font-size: 2.6rem; }
    .header-text h1 { margin: 0; font-size: 1.6rem; font-weight: 800; }
    .header-text p  { margin: 0.25rem 0 0.7rem 0; opacity: 0.85; font-size: 0.9rem; }
    .header-chips { display: flex; flex-wrap: wrap; gap: 0.4rem; }
    .chip {
        background: rgba(255,255,255,0.15); border: 1px solid rgba(255,255,255,0.22);
        border-radius: 999px; padding: 0.2rem 0.65rem; font-size: 0.78rem; font-weight: 600;
    }
    .chip-gold { background: rgba(199,162,74,0.28); border-color: rgba(199,162,74,0.5); }
    .chip-mem  { background: rgba(100,180,255,0.2);  border-color: rgba(100,180,255,0.4); }
    .msg-row-user      { display: flex; justify-content: flex-end; margin: 0.5rem 0; }
    .msg-row-assistant { display: flex; justify-content: flex-start; gap: 0.5rem; margin: 0.5rem 0; align-items: flex-start; }
    .bubble-user {
        background: var(--green-800); color: #fff;
        border-radius: 16px 16px 4px 16px; padding: 0.75rem 1.1rem;
        max-width: 72%; font-size: 0.95rem; line-height: 1.55;
        box-shadow: 0 2px 10px rgba(18,53,31,0.18);
    }
    .bubble-bot {
        background: #fff; border: 1px solid var(--line);
        border-radius: 4px 16px 16px 16px; padding: 0.75rem 1.1rem;
        max-width: 76%; font-size: 0.95rem; line-height: 1.6; color: var(--ink);
        box-shadow: 0 2px 12px rgba(18,53,31,0.07);
    }
    .avatar {
        width: 32px; height: 32px; border-radius: 50%;
        background: var(--green-700); display: flex; align-items: center;
        justify-content: center; font-size: 1rem; flex-shrink: 0; margin-top: 2px;
    }
    .sbadge {
        display: inline-block; border-radius: 999px; padding: 0.12rem 0.5rem;
        font-size: 0.68rem; font-weight: 700; margin-top: 0.35rem;
    }
    .sbadge-rag    { background: rgba(31,107,59,0.1); color: #1f6b3b; border: 1px solid rgba(31,107,59,0.25); }
    .sbadge-struct { background: rgba(199,162,74,0.15); color: #5d4730; border: 1px solid rgba(199,162,74,0.35); }
    .sbadge-enrich { background: rgba(100,150,255,0.1); color: #2c5fa8; border: 1px solid rgba(100,150,255,0.3); }
    .info-grid { display: flex; gap: 0.75rem; margin-bottom: 1rem; }
    .info-card {
        flex: 1; background: #fff; border: 1px solid var(--line);
        border-top: 3px solid var(--green-700); border-radius: 10px;
        padding: 0.75rem 1rem; box-shadow: 0 2px 12px rgba(18,53,31,0.06);
    }
    .info-label { color: var(--muted); font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.06em; font-weight: 700; }
    .info-value { color: var(--green-800); font-size: 0.95rem; font-weight: 800; margin-top: 0.15rem; }
    .question-box {
        background: var(--cane-100); border: 1px solid rgba(199,162,74,0.4);
        border-left: 5px solid var(--cane-500); padding: 0.9rem 1.2rem;
        border-radius: 8px; margin-top: 1rem; color: var(--soil-700); font-weight: 600;
    }
    .answer-box {
        background: #fff; border: 1px solid var(--line); border-left: 5px solid var(--green-700);
        padding: 1.3rem 1.6rem; border-radius: 8px; margin-top: 0.6rem;
        box-shadow: 0 4px 20px rgba(18,53,31,0.07); line-height: 1.7;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 0.4rem; }
    .stTabs [data-baseweb="tab"] {
        background: var(--green-800); color: #fff !important; border: 1px solid var(--green-800);
        border-radius: 8px; font-size: 0.95rem; font-weight: 600; padding: 0.5rem 1.4rem;
    }
    .stTabs [data-baseweb="tab"] p { color: inherit !important; }
    .stTabs [data-baseweb="tab"]:hover { background: #fff; color: var(--green-800) !important; }
    .stTabs [aria-selected="true"] { background: var(--green-700) !important; border-color: var(--green-700) !important; }

    /* Boton primario */
    div.stButton > button[kind="primary"] {
        background: var(--green-800); border: none; border-radius: 8px;
        font-weight: 700; font-size: 1rem; padding: 0.6rem 1.2rem;
        color: #fff !important;
    }
    div.stButton > button[kind="primary"]:hover { background: var(--green-700); }

    /* Botones secundarios — chips de ejemplo */
    div.stButton > button[kind="secondary"],
    div.stButton > button:not([kind="primary"]) {
        background: #ffffff !important;
        color: var(--green-800) !important;
        border: 1.5px solid var(--green-700) !important;
        border-radius: 8px !important;
        font-size: 0.82rem !important;
        font-weight: 600 !important;
        padding: 0.3rem 0.7rem !important;
        transition: all 0.15s ease !important;
    }
    div.stButton > button[kind="secondary"]:hover,
    div.stButton > button:not([kind="primary"]):hover {
        background: var(--green-700) !important;
        color: #ffffff !important;
        border-color: var(--green-700) !important;
    }

    /* Boton sidebar — nueva conversacion */
    [data-testid="stSidebar"] div.stButton > button {
        background: rgba(255,255,255,0.12) !important;
        color: #f0f8f2 !important;
        border: 1px solid rgba(255,255,255,0.3) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] div.stButton > button:hover {
        background: rgba(255,255,255,0.22) !important;
    }

    .stExpander { border: 1px solid var(--line) !important; border-radius: 8px !important; }
    .empty-chat {
        text-align: center; color: #5f6f63; padding: 2.5rem 1rem;
        font-size: 0.95rem; border: 2px dashed #dce8df; border-radius: 12px;
        background: rgba(255,255,255,0.6);
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────
# Cache
# ─────────────────────────────────────────────────────────────

@st.cache_resource(show_spinner="Inicializando agente conversacional de Manuelita S.A. ...")
def get_contextual_agent(provider: str, _gemini_key: str = ""):
    if _gemini_key:
        os.environ["GEMINI_API_KEY"] = _gemini_key
    from src.langchain_app.memory import ContextualAgent
    return ContextualAgent(provider=provider, window_size=MEMORY_WINDOW, verbose=False)


@st.cache_resource(show_spinner="Cargando corpus de Manuelita S.A. ...")
def get_qa_legacy(provider: str, _gemini_key: str = ""):
    if _gemini_key:
        os.environ["GEMINI_API_KEY"] = _gemini_key
    from src.langchain_app.qa_system import ManuelitaQASystem
    return ManuelitaQASystem(provider=provider, model_name=MODEL_NAME, gemini_api_key=_gemini_key)


# ─────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────

def render_sidebar() -> tuple:
    with st.sidebar:
        st.markdown("## 🌱 Manuelita S.A.")
        st.markdown("**Agente Conversacional IA**")
        st.divider()

        st.markdown("#### Motor de IA")
        provider_map = {
            "🖥️ Local (HuggingFace + Ollama)": "local",
            "🤖 Ollama (nomic-embed-text)": "ollama",
            "✨ Google Gemini (API)": "gemini",
        }
        default_idx = {"local": 0, "ollama": 1, "gemini": 2}.get(PROVIDER, 0)
        label = st.radio("Proveedor:", list(provider_map.keys()),
                         index=default_idx, label_visibility="collapsed")
        provider = provider_map[label]

        gemini_key = GEMINI_API_KEY
        if provider == "gemini":
            if not GEMINI_API_KEY:
                gemini_key = st.text_input("API Key de Gemini", type="password",
                                           placeholder="Obtén tu key en aistudio.google.com")
            else:
                st.success("✅ `" + GEMINI_MODEL + "`")
                st.caption("Capa gratuita · AI Studio")
        elif provider == "local":
            st.info("Embeddings: `paraphrase-multilingual-MiniLM-L12-v2`\nLLM: `" + OLLAMA_MODEL + "`")
            st.caption("Requiere `ollama serve`")
        else:
            st.info("Embeddings: `nomic-embed-text`\nLLM: `" + OLLAMA_MODEL + "`")
            st.caption("Requiere `ollama serve`")

        st.divider()
        st.markdown("#### Memoria de conversación")
        st.caption("Ventana: últimos **" + str(MEMORY_WINDOW) + " turnos**")
        if st.button("🔄 Nueva conversación", use_container_width=True):
            st.session_state["chat_messages"] = []
            st.session_state["turn_count"] = 0
            key = "_agent_" + provider
            if key in st.session_state:
                st.session_state[key].reset()
            st.rerun()

        st.divider()
        st.markdown("#### Corpus")
        st.caption("📄 Perfil corporativo oficial")
        st.caption("📊 Datos financieros Supersociedades")
        st.caption("♻️ Informes de sostenibilidad")
        st.caption("🔗 LinkedIn · YouTube · OSINT")
        st.divider()
        model_lbl = GEMINI_MODEL if provider == "gemini" else OLLAMA_MODEL
        st.markdown("**Modelo** `" + model_lbl + "`")
        st.markdown("**Router** HybridRouter")
        st.markdown("**Memoria** ConversationBufferWindowMemory")
        st.markdown("**Framework** LangChain")
        st.divider()
        st.caption("Universidad Autónoma de Occidente · 2026")
        st.caption("Módulo 2 · Agente Conversacional")

    return provider, gemini_key


# ─────────────────────────────────────────────────────────────
# Header
# ─────────────────────────────────────────────────────────────

def render_header(provider: str, turn_count: int) -> None:
    model_lbl = GEMINI_MODEL if provider == "gemini" else OLLAMA_MODEL
    motor_lbl = "Google Gemini API" if provider == "gemini" else "Ollama local"
    turnos_txt = str(turn_count) + " turno" + ("s" if turn_count != 1 else "")
    st.markdown(
        '<div class="main-header">'
        '<div class="header-logo">🌱</div>'
        '<div class="header-text">'
        '<h1>Manuelita S.A. — Agente Conversacional</h1>'
        '<p>Pregunta sobre la empresa en lenguaje natural — el agente elige la herramienta más adecuada</p>'
        '<div class="header-chips">'
        '<span class="chip chip-gold">🤖 ' + model_lbl + '</span>'
        '<span class="chip">' + motor_lbl + '</span>'
        '<span class="chip">HybridRouter</span>'
        '<span class="chip chip-mem">💬 ' + turnos_txt + '</span>'
        '</div></div></div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
# Chat
# ─────────────────────────────────────────────────────────────

def _badge(tool: str, enriched: bool) -> str:
    parts = []
    if tool == "rag":
        parts.append('<span class="sbadge sbadge-rag">🔍 RAG · ChromaDB</span>')
    elif tool == "estructurado":
        parts.append('<span class="sbadge sbadge-struct">⚡ Datos Estructurados</span>')
    if enriched:
        parts.append('<span class="sbadge sbadge-enrich">🔗 contexto inyectado</span>')
    return " ".join(parts)


def render_chat_history(messages: list) -> None:
    if not messages:
        st.markdown(
            '<div class="empty-chat">👋 ¡Hola! Escribe una pregunta o elige un ejemplo para comenzar.</div>',
            unsafe_allow_html=True,
        )
        return

    html = []
    for msg in messages:
        if msg["role"] == "user":
            html.append(
                '<div class="msg-row-user">'
                '<div class="bubble-user">' + msg["content"] + '</div>'
                '</div>'
            )
        else:
            badge  = _badge(msg.get("tool", "rag"), msg.get("enriched", False))
            tiempo = msg.get("tiempo_s", 0)
            t_str  = '<span style="font-size:0.65rem;color:#9aa8a0;margin-left:0.5rem">' + str(tiempo) + 's</span>'
            html.append(
                '<div class="msg-row-assistant">'
                '<div class="avatar">🌱</div>'
                '<div>'
                '<div class="bubble-bot">' + msg["content"] + '</div>'
                '<div style="margin-top:0.25rem">' + badge + t_str + '</div>'
                '</div></div>'
            )

    st.markdown("\n".join(html), unsafe_allow_html=True)


def render_chat_tab(agent, provider: str) -> None:
    if "chat_messages" not in st.session_state:
        st.session_state["chat_messages"] = []
    if "turn_count" not in st.session_state:
        st.session_state["turn_count"] = 0
    if "pending_q" not in st.session_state:
        st.session_state["pending_q"] = ""

    if st.session_state.get("_prov") != provider:
        st.session_state["_prov"] = provider
        st.session_state["chat_messages"] = []
        st.session_state["turn_count"] = 0

    msgs = st.session_state["chat_messages"]

    # Chips de ejemplos
    st.markdown("**Prueba con alguna de estas preguntas:**")
    cols = st.columns(4)
    for i, q in enumerate(EXAMPLE_QUESTIONS):
        if cols[i % 4].button(q, key="ex_" + str(i), use_container_width=True):
            st.session_state["pending_q"] = q

    st.divider()

    # Historial
    render_chat_history(msgs)

    # Input
    st.markdown("")
    with st.form("chat_form", clear_on_submit=True):
        c1, c2 = st.columns([5, 1])
        with c1:
            q = st.text_input(
                "Pregunta:",
                value=st.session_state.pop("pending_q", ""),
                placeholder="Ej: ¿Cuál es la meta de carbono de Manuelita para 2030?",
                label_visibility="collapsed",
            )
        with c2:
            send = st.form_submit_button("Enviar ▶", type="primary", use_container_width=True)

    if send and q.strip():
        msgs.append({"role": "user", "content": q})
        with st.spinner("Pensando..."):
            try:
                res = agent.chat(q)
                answer   = res["answer"]
                tool     = res.get("tool", "rag")
                enriched = res.get("enriched", False)
                tiempo   = res.get("tiempo_s", 0)
            except Exception as exc:
                answer, tool, enriched, tiempo = "Error: " + str(exc), "rag", False, 0

        msgs.append({"role": "assistant", "content": answer,
                     "tool": tool, "enriched": enriched, "tiempo_s": tiempo})
        st.session_state["turn_count"] = agent.memory.turn_count()
        st.rerun()

    # Metricas
    if msgs:
        n_rag    = sum(1 for m in msgs if m.get("role") == "assistant" and m.get("tool") == "rag")
        n_struct = sum(1 for m in msgs if m.get("role") == "assistant" and m.get("tool") == "estructurado")
        n_enrich = sum(1 for m in msgs if m.get("role") == "assistant" and m.get("enriched"))
        st.divider()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Turnos",          st.session_state.get("turn_count", 0))
        m2.metric("RAG",             n_rag)
        m3.metric("Estructurado",    n_struct)
        m4.metric("Con contexto 🔗", n_enrich)


# ─────────────────────────────────────────────────────────────
# Tabs Modulo 1
# ─────────────────────────────────────────────────────────────

def render_summary_tab(qa) -> None:
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


def render_faq_tab(qa) -> None:
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


# ─────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────

def main() -> None:
    provider, gemini_key = render_sidebar()

    turn_count = st.session_state.get("turn_count", 0)
    render_header(provider, turn_count)

    # Cargar agente
    try:
        agent = get_contextual_agent(provider=provider, _gemini_key=gemini_key)
    except Exception as exc:
        st.error("❌ Error al iniciar el agente: " + str(exc))
        if "ollama" in str(exc).lower() or "connection" in str(exc).lower():
            st.info("Verifica que Ollama esté corriendo: `ollama serve`")
        elif "gemini" in str(exc).lower() or "api" in str(exc).lower():
            st.info("Verifica que `GEMINI_API_KEY` sea válida en tu `.env`")
        st.stop()

    # Info cards
    model_lbl = GEMINI_MODEL if provider == "gemini" else OLLAMA_MODEL
    st.markdown(
        '<div class="info-grid">'
        '<div class="info-card"><div class="info-label">Proveedor</div><div class="info-value">' + provider.upper() + '</div></div>'
        '<div class="info-card"><div class="info-label">Modelo</div><div class="info-value">' + model_lbl + '</div></div>'
        '<div class="info-card"><div class="info-label">Router</div><div class="info-value">HybridRouter</div></div>'
        '<div class="info-card"><div class="info-label">Memoria</div><div class="info-value">' + str(MEMORY_WINDOW) + ' turnos</div></div>'
        '</div>',
        unsafe_allow_html=True,
    )

    # Tabs
    tab_chat, tab_resumen, tab_faq = st.tabs([
        "💬 Chat Conversacional",
        "📝 Resumen Ejecutivo",
        "❓ Preguntas Frecuentes",
    ])

    with tab_chat:
        render_chat_tab(agent, provider)

    with tab_resumen:
        try:
            qa = get_qa_legacy(provider=provider, _gemini_key=gemini_key)
            render_summary_tab(qa)
        except Exception:
            st.info("El módulo de Resumen requiere el sistema Q&A del Módulo 1.")

    with tab_faq:
        try:
            qa = get_qa_legacy(provider=provider, _gemini_key=gemini_key)
            render_faq_tab(qa)
        except Exception:
            st.info("El módulo de FAQ requiere el sistema Q&A del Módulo 1.")


if __name__ == "__main__":
    main()
