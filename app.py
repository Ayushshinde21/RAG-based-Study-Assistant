import os
import tempfile
import html
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI RAG Study Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------------------------------------------------------
# Theme state
# -----------------------------------------------------------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "light"

_LIGHT_VARS = """
        --ivory: #faf9f3;
        --paper: #ffffff;
        --paper-2: #f5f4ee;
        --line: #e8e6dd;
        --line-strong: #dfe0d8;
        --ink: #1b1c19;
        --muted: #5b6b64;
        --soft: #7a8c84;
        --forest: #173f35;
        --forest-dark: #002920;
        --forest-text: #173f35;
        --sage: #caead7;
        --sage-2: #a6cfc1;
        --amber: #fae191;
        --amber-ink: #4d3e00;
        --coral: #e8895b;
        --shadow: rgba(27,28,25,.06);
"""

_DARK_VARS = """
        --ivory: #14171a;
        --paper: #1b1f22;
        --paper-2: #20252a;
        --line: #33393e;
        --line-strong: #40474d;
        --ink: #f2f1ea;
        --muted: #a9b3ae;
        --soft: #8b968f;
        --forest: #7fcbb0;
        --forest-dark: #b7e9d3;
        --forest-text: #101312;
        --sage: #23433a;
        --sage-2: #2c5347;
        --amber: #5c4e1f;
        --amber-ink: #fae191;
        --coral: #e8895b;
        --shadow: rgba(0,0,0,.35);
"""

_theme_vars = _DARK_VARS if st.session_state.theme == "dark" else _LIGHT_VARS

# Theme variables are injected via their own small style tag (kept separate
# from the big CSS block below so that block can stay a plain string, not an
# f-string — the big block is full of literal `{ }` CSS braces).
st.markdown(
    "<style>\n:root {\n" + _theme_vars + "\n}\n</style>",
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Academic Editorial Modern — Stitch-inspired theme
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Plus+Jakarta+Sans:wght@500;600;700&display=swap');

    html { font-size: 16px; }
    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        font-size: 15px;
        color: var(--ink);
        -webkit-font-smoothing: antialiased;
    }
    p, span, div, label, li { color: var(--ink); }
    .stApp { background: var(--ivory); color: var(--ink); transition: background .2s ease, color .2s ease; }
    .main .block-container { max-width: 1480px; padding: 5.5rem 2.5rem 3rem; }

    /* Hide Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: var(--paper-2);
        border-right: 1px solid rgba(192,200,196,.55);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }
    [data-testid="stSidebarContent"] { padding: 0 1rem 1rem; }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 9px;
        border: 1px solid transparent;
        background: transparent;
        color: var(--muted);
        text-align: left;
        justify-content: flex-start;
        min-height: 40px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--line);
        color: var(--ink);
        border-color: transparent;
    }
    [data-testid="stSidebar"] .new-lecture + div .stButton > button,
    .primary-btn button {
        background: var(--forest) !important;
        color: white !important;
        border: 1px solid var(--forest) !important;
        text-align: center !important;
        justify-content: center !important;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--sage) !important;
        color: var(--forest-dark) !important;
        border: 1px solid var(--sage-2) !important;
        font-weight: 600;
    }

    /* Top bar */
    .topbar {
        position: fixed; top: 0; left: 0; right: 0; height: 58px; z-index: 99;
        background: color-mix(in srgb, var(--ivory) 92%, transparent); backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(192,200,196,.42);
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 2.5rem;
    }
    .brand { display:flex; align-items:center; gap:10px; font-family:'Plus Jakarta Sans'; font-weight:700; }
    .brand-mark { width:30px; height:30px; border-radius:9px; background:var(--forest); color:#fff; display:grid; place-items:center; font-size:15px; }
    .brand-name { letter-spacing:-.02em; }
    .top-meta { display:flex; gap:8px; align-items:center; color:var(--muted); font-size:12px; }
    .status-pill { padding:6px 10px; border:1px solid var(--line); border-radius:999px; background:var(--paper); }

    /* Typography */
    .display { font-family:'Newsreader', serif; font-size:44px; line-height:1.1; font-weight:500; letter-spacing:-.025em; color:var(--ink); }
    .display-small { font-family:'Newsreader', serif; font-size:30px; line-height:1.2; font-weight:500; letter-spacing:-.015em; color:var(--ink); }
    .subtitle { color:var(--muted); font-size:15px; line-height:1.7; max-width:720px; }
    .eyebrow { color:var(--forest); text-transform:uppercase; letter-spacing:.11em; font-size:11px; font-weight:700; }

    /* Cards */
    .card {
        background:var(--paper); border:1px solid var(--line); border-radius:16px;
        padding:20px; box-shadow:none;
    }
    .card:hover { border-color: var(--sage-2); }
    .stat-card { min-height:116px; }
    .stat-label { font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--soft); font-weight:700; }
    .stat-value { font-family:'Newsreader'; font-size:32px; line-height:1.1; margin-top:10px; }
    .stat-note { font-size:11px; color:var(--muted); margin-top:5px; }

    .lecture-card { min-height:185px; position:relative; overflow:hidden; }
    .lecture-icon { width:44px; height:44px; border-radius:12px; background:var(--sage); display:grid; place-items:center; font-size:21px; }
    .lecture-title { font-family:'Plus Jakarta Sans'; font-weight:700; font-size:15px; margin-top:16px; color:var(--ink); }
    .lecture-meta { color:var(--soft); font-size:13px; margin-top:6px; }
    .progress-track { height:6px; background:var(--line); border-radius:999px; overflow:hidden; margin-top:15px; }
    .progress-fill { height:100%; background:var(--forest); border-radius:999px; }

    /* Upload */
    .upload-shell { background:var(--paper); border:1px dashed var(--line-strong); border-radius:18px; padding:42px 28px; text-align:center; }
    .upload-symbol { width:58px; height:58px; margin:0 auto 15px; border-radius:16px; background:var(--sage); display:grid; place-items:center; font-size:26px; }
    .upload-title { font-family:'Newsreader'; font-size:28px; }
    .upload-copy { color:var(--muted); font-size:13px; margin:6px auto 18px; }
    .format-row { display:flex; justify-content:center; gap:7px; flex-wrap:wrap; }
    .format-chip { border:1px solid var(--line); background:var(--paper-2); border-radius:999px; padding:5px 9px; font-size:10px; color:var(--muted); }

    /* Section header */
    .section-head { display:flex; align-items:end; justify-content:space-between; gap:20px; margin:30px 0 14px; }
    .section-head h2 { font-family:'Newsreader'; font-size:26px; font-weight:500; margin:0; }
    .section-head p { color:var(--muted); font-size:12px; margin:4px 0 0; }

    /* Workspace navigation */
    .workspace-nav { display:flex; gap:4px; border-bottom:1px solid var(--line); margin:12px 0 24px; }
    .workspace-note { font-size:13px; color:var(--muted); padding:9px 2px 11px; }

    /* Chat */
    .chat-bubble { padding:14px 16px; border:1px solid var(--line); border-radius:14px; margin:10px 0; line-height:1.7; font-size:15px; color:var(--ink); }
    .chat-user { background:var(--paper-2); margin-left:10%; }
    .chat-ai { background:var(--paper); margin-right:10%; }
    .source-chip { display:inline-block; margin-top:8px; margin-right:5px; padding:4px 8px; border-radius:999px; background:var(--amber); color:var(--amber-ink); font-size:10px; }
    .suggestion { border:1px solid var(--line); border-radius:10px; padding:9px 11px; color:var(--muted); background:var(--paper); font-size:12px; }

    /* Study note */
    .note { border-left:4px solid var(--forest); background:var(--paper); border-radius:0 14px 14px 0; border-top:1px solid var(--line); border-right:1px solid var(--line); border-bottom:1px solid var(--line); padding:18px 20px; margin:12px 0; }
    .note h4 { font-family:'Plus Jakarta Sans'; font-size:14px; margin:0 0 7px; }
    .note p { font-family:'Newsreader'; font-size:17px; line-height:1.65; margin:0; }

    /* Metrics */
    .metric-ring { border:1px solid var(--line); border-radius:16px; padding:18px; background:var(--paper); text-align:center; }
    .metric-number { font-family:'Newsreader'; font-size:34px; color:var(--forest); }
    .metric-label { font-size:12px; color:var(--muted); margin-top:3px; }

    /* Streamlit widgets */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background:var(--paper) !important; border-color:var(--line) !important; border-radius:9px !important;
        color:var(--ink) !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--soft) !important; opacity: 1; }
    .stMarkdown, .stCaption, [data-testid="stCaptionContainer"] { color: var(--muted); }
    .stSlider [data-baseweb="slider"] { color:var(--forest); }
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        border-radius:9px; border:1px solid var(--line); background:var(--paper); color:var(--ink);
        font-family:'Plus Jakarta Sans'; font-size:13px; min-height:38px;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color:var(--sage-2); color:var(--forest); }
    div[data-testid="stFileUploader"] section { border:1px dashed var(--line-strong); border-radius:14px; background:var(--paper-2); }
    div[data-testid="stFileUploader"] section, div[data-testid="stFileUploader"] small { color: var(--muted); }
    .stProgress > div > div > div > div { background:var(--forest); }

    /* Theme toggle */
    .theme-toggle-row .stButton > button {
        font-size: 12px; min-height: 34px;
    }

    /* Responsive */
    @media (max-width: 900px) {
        .main .block-container { padding: 5rem 1rem 2rem; }
        .topbar { padding:0 1rem; }
        .display { font-size:36px; }
        .chat-user { margin-left:0; }
        .chat-ai { margin-right:0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
def init_session():
    defaults = {
        "processed": False,
        "docs": None,
        "rag": None,
        "summary": None,
        "quiz": None,
        "chat_history": [],
        "transcript_path": None,
        "page": "Dashboard",
        "quiz_submitted": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------
def esc(value):
    return html.escape(str(value))


def set_page(name):
    st.session_state.page = name


def reset_app():
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()


# -----------------------------------------------------------------------------
# Top bar
# -----------------------------------------------------------------------------
lecture_state = "Lecture ready" if st.session_state.processed else "No lecture loaded"
st.markdown(
    f"""
    <div class="topbar">
        <div class="brand">
            <div class="brand-mark">✦</div>
            <div class="brand-name">AI RAG Study Assistant</div>
        </div>
        <div class="top-meta">
            <span class="status-pill">● {lecture_state}</span>
            <span class="status-pill">Study workspace</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### 🎓 AI RAG Study Assistant")
    st.caption("Academic Editorial Workspace")

    st.markdown('<div class="theme-toggle-row">', unsafe_allow_html=True)
    toggle_label = "☀️  Light mode" if st.session_state.theme == "dark" else "🌙  Dark mode"
    if st.button(toggle_label, use_container_width=True, key="theme_toggle"):
        st.session_state.theme = "light" if st.session_state.theme == "dark" else "dark"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("---")

    st.markdown('<div class="new-lecture"></div>', unsafe_allow_html=True)
    if st.button("＋  New Lecture", use_container_width=True, key="nav_new"):
        st.session_state.processed = False
        st.session_state.docs = None
        st.session_state.rag = None
        st.session_state.summary = None
        st.session_state.quiz = None
        st.session_state.chat_history = []
        st.session_state.page = "Dashboard"
        st.rerun()

    st.markdown("**WORKSPACE**")
    for label, icon in [
        ("Dashboard", "⌂"),
        ("My Lectures", "▣"),
    ]:
        is_active = st.session_state.page == label
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"nav_{label}",
                     type="primary" if is_active else "secondary"):
            set_page(label)
            st.rerun()

    st.markdown("**CURRENT LECTURE**")
    if st.session_state.processed:
        is_active = st.session_state.page == "Workspace"
        if st.button("●  Study workspace", use_container_width=True, key="current_lecture",
                     type="primary" if is_active else "secondary"):
            set_page("Workspace")
            st.rerun()
        st.caption(f"{len(st.session_state.docs or [])} indexed chunks")
    else:
        st.caption("Upload a lecture to begin.")

    st.markdown("---")

    if st.session_state.processed:
        if st.button("↻  Reset workspace", use_container_width=True, key="reset"):
            reset_app()

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("RAG Study Assistant • VIT Pune • Group 14")

# -----------------------------------------------------------------------------
# Processing function
# -----------------------------------------------------------------------------
def process_uploaded_file(source):
    """source is either a Streamlit UploadedFile or a YouTube URL string."""
    tmp_path = None
    audio_path = None
    is_url = isinstance(source, str)
    try:
        if not is_url:
            suffix = "." + source.name.split(".")[-1]
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(source.read())
                tmp_path = tmp.name

        with st.status("Building your study workspace...", expanded=True) as status:
            st.write("🎵 Extracting audio")
            from utils.audio_processor import get_audio_path
            audio_path = get_audio_path(source if is_url else tmp_path)

            st.write("📝 Transcribing lecture")
            from utils.transcriber import transcribe, save_transcript
            transcript = transcribe(audio_path)
            transcript_path = save_transcript(transcript, audio_path)
            st.session_state.transcript_path = transcript_path

            st.write("✂️ Chunking transcript")
            from core.chunker import chunk_from_file
            docs = chunk_from_file(transcript_path, method="semantic")
            st.session_state.docs = docs

            st.write("🔎 Building hybrid search index")
            from core.vector_store import build_vector_store, get_dense_retriever
            from core.bm25_index import build_bm25_retriever
            vector_store = build_vector_store(docs, reset=True)
            dense_retriever = get_dense_retriever(vector_store, k=10)
            bm25_retriever = build_bm25_retriever(docs, k=10)

            st.write("🤖 Initializing RAG engine")
            from core.rag_engine import RAGEngine
            st.session_state.rag = RAGEngine(dense_retriever, bm25_retriever)

            # Load the CrossEncoder reranker here, while the progress panel is
            # still showing, instead of paying its load time on the first
            # question a student asks in chat.
            st.write("🎯 Warming up reranker")
            import core.reranker  # noqa: F401 — import triggers model load

            # Summary generation is left for the first time the Summary tab is
            # opened (see render_summary_tab) so "Workspace ready" doesn't wait
            # on an LLM call the student may not need immediately.
            st.session_state.summary = None

            st.session_state.processed = True
            status.update(label="Workspace ready", state="complete", expanded=False)

        st.session_state.page = "Workspace"
        st.success("Your lecture is ready to study.")
        st.rerun()
    except Exception as e:
        st.error(f"Processing failed: {e}")
    finally:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        if audio_path and os.path.exists(audio_path) and audio_path != tmp_path:
            try:
                os.remove(audio_path)
            except Exception:
                pass


# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------
def greeting_for_now():
    hour = datetime.now().hour
    if hour < 12:
        return "Good morning 👋"
    elif hour < 17:
        return "Good afternoon 👋"
    return "Good evening 👋"


def render_dashboard():
    st.markdown('<div class="eyebrow">YOUR LEARNING SPACE</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="display">{greeting_for_now()}</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Bring your lectures into one calm workspace. Ask questions, build study notes, practice with quizzes, and inspect how well your RAG pipeline performs.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-head"><div><h2>Workspace overview</h2><p>Live information from the current session.</p></div></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    values = [
        (c1, "LECTURE STATUS", "Ready" if st.session_state.processed else "Empty", "Current workspace"),
        (c2, "INDEXED CHUNKS", len(st.session_state.docs or []), "Semantic chunks"),
        (c3, "QUESTIONS ASKED", len([m for m in st.session_state.chat_history if m["role"] == "user"]), "This session"),
        (c4, "QUIZ", len(st.session_state.quiz or []), "Questions generated"),
    ]
    for col, label, value, note in values:
        with col:
            st.markdown(
                f'<div class="card stat-card"><div class="stat-label">{esc(label)}</div><div class="stat-value">{esc(value)}</div><div class="stat-note">{esc(note)}</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="section-head"><div><h2>Bring your lecture to life</h2><p>Upload a recording and turn it into a searchable knowledge base.</p></div></div>', unsafe_allow_html=True)
    st.markdown(
        '''<div class="upload-shell">
            <div class="upload-symbol">↥</div>
            <div class="upload-title">Drop your lecture here</div>
            <div class="upload-copy">Upload a video or audio recording. The assistant will transcribe, chunk, index, and summarize it.</div>
            <div class="format-row">
                <span class="format-chip">MP4</span><span class="format-chip">MP3</span><span class="format-chip">WAV</span>
                <span class="format-chip">MKV</span><span class="format-chip">AVI</span><span class="format-chip">M4A</span>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )
    up_tab, url_tab = st.tabs(["Upload a file", "Paste a YouTube link"])

    with up_tab:
        uploaded = st.file_uploader(
            "Choose a lecture file",
            type=["mp4", "mp3", "wav", "mkv", "avi", "m4a"],
            label_visibility="collapsed",
            key="dashboard_upload",
        )
        if uploaded and not st.session_state.processed:
            if st.button("Process lecture  →", type="primary", use_container_width=True, key="process_dashboard"):
                process_uploaded_file(uploaded)

    with url_tab:
        yt_url = st.text_input(
            "YouTube URL",
            placeholder="https://www.youtube.com/watch?v=...",
            label_visibility="collapsed",
            key="dashboard_youtube_url",
        )
        if yt_url.strip() and not st.session_state.processed:
            if st.button("Process from link  →", type="primary", use_container_width=True, key="process_youtube"):
                process_uploaded_file(yt_url.strip())

    st.markdown('<div class="section-head"><div><h2>Study workflow</h2><p>Everything stays connected to the same indexed lecture.</p></div></div>', unsafe_allow_html=True)
    a, b, c = st.columns(3)
    workflow = [
        (a, "01", "Ask", "Chat with your lecture using hybrid retrieval."),
        (b, "02", "Understand", "Turn the transcript into structured study notes."),
        (c, "03", "Practice", "Generate questions and evaluate retrieval quality."),
    ]
    for col, num, title, copy in workflow:
        with col:
            st.markdown(f'<div class="card"><div class="eyebrow">{num}</div><h3 style="font-family:Newsreader;font-size:24px;margin:8px 0 4px">{title}</h3><p style="font-size:13px;color:#5b6b64;line-height:1.6">{copy}</p></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Workspace pages
# -----------------------------------------------------------------------------
def require_processed():
    if not st.session_state.processed or st.session_state.rag is None:
        st.warning("Upload and process a lecture first.")
        if st.button("Go to Dashboard →", key="go_dashboard"):
            set_page("Dashboard")
            st.rerun()
        return False
    return True


def render_workspace_header(title, description):
    st.markdown('<div class="eyebrow">ACTIVE LECTURE</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="display-small">{esc(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{esc(description)}</div>', unsafe_allow_html=True)


def render_sources(docs):
    """Real retrieved chunks, shown in an expander instead of fake chips."""
    if not docs:
        return
    with st.expander(f"📎 Sources used for this answer ({len(docs)} chunks)"):
        for i, doc in enumerate(docs, start=1):
            st.markdown(f"**Chunk {i}**")
            st.caption(doc.page_content[:400] + ("…" if len(doc.page_content) > 400 else ""))


def render_chat_tab():
    left, right = st.columns([1.8, 1], gap="large")

    with right:
        st.markdown('<div class="card"><div class="eyebrow">SUGGESTED QUESTIONS</div><h3 style="font-family:Newsreader;font-size:24px;margin:8px 0 14px">Study prompts</h3></div>', unsafe_allow_html=True)
        queued_prompt = None
        for prompt in [
            "Explain the core concept simply.",
            "What are the key points?",
            "Give me an example.",
            "What should I remember for an exam?",
        ]:
            if st.button(prompt, key=f"suggest_{prompt}", use_container_width=True):
                queued_prompt = prompt

        st.markdown(
            '<div class="card" style="margin-top:14px"><div class="eyebrow">RETRIEVAL</div>'
            '<h3 style="font-family:Newsreader;font-size:24px;margin:8px 0 6px">Knowledge base</h3>'
            '<p style="font-size:12px;color:#5b6b64">Your lecture is indexed using the existing dense + BM25 retrieval pipeline.</p>'
            '<div class="stat-note">Indexed chunks</div><div class="stat-value" style="font-size:28px">'
            + str(len(st.session_state.docs or [])) + '</div></div>',
            unsafe_allow_html=True,
        )

        if st.session_state.chat_history and st.button("Clear conversation", key="clear_chat", use_container_width=True):
            st.session_state.chat_history = []
            try:
                st.session_state.rag.reset_memory()
            except Exception:
                pass
            st.rerun()

    with left:
        chat_box = st.container(height=440)
        with chat_box:
            if not st.session_state.chat_history:
                st.markdown(
                    '<div class="card"><div class="eyebrow">START HERE</div>'
                    '<div class="display-small" style="font-size:27px;margin-top:8px">What would you like to understand?</div>'
                    '<p class="subtitle">Try a question about the main idea, a definition, an example, or the most important takeaway.</p></div>',
                    unsafe_allow_html=True,
                )
            for msg in st.session_state.chat_history:
                with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                    st.markdown(msg["content"])
                    if msg["role"] == "assistant" and msg.get("sources"):
                        render_sources(msg["sources"])

        typed_query = st.chat_input("Ask your lecture something...")
        query = queued_prompt or typed_query

        if query:
            with chat_box:
                with st.chat_message("user"):
                    st.markdown(query)
                with st.chat_message("assistant"):
                    with st.spinner("Retrieving lecture context..."):
                        token_gen, sources, save_fn = st.session_state.rag.prepare_stream(query)
                    answer = st.write_stream(token_gen)
                    save_fn(answer)
                    render_sources(sources)
            st.session_state.chat_history.append({"role": "user", "content": query})
            st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": sources})
            st.rerun()


def render_summary_tab():
    if st.session_state.summary is None:
        with st.spinner("Generating study summary..."):
            from features.summarizer import summarize
            st.session_state.summary = summarize(st.session_state.docs)

    summary = st.session_state.summary
    if summary:
        st.markdown(
            '<div class="card"><div class="eyebrow">SYNTHESIS</div>'
            '<div style="font-family:Newsreader;font-size:18px;line-height:1.75;margin-top:12px">',
            unsafe_allow_html=True,
        )
        st.markdown(summary)
        st.markdown('</div></div>', unsafe_allow_html=True)
        st.download_button("Download study notes", data=summary, file_name="lecture_summary.txt", mime="text/plain")
    else:
        st.info("No summary is available yet.")


def render_quiz_tab():
    c1, c2 = st.columns([2, 1])
    with c1:
        num_q = st.slider("Number of questions", 3, 10, 5)
    with c2:
        generate = st.button("Generate quiz  →", use_container_width=True, type="primary")
    if generate:
        with st.spinner("Generating questions..."):
            from features.quiz_generator import generate_quiz
            st.session_state.quiz = generate_quiz(st.session_state.docs, num_questions=num_q)
        st.session_state.quiz_submitted = False
        st.rerun()

    quiz = st.session_state.quiz
    if not quiz:
        return

    valid_quiz = [q for q in quiz if all(k in q for k in ("question", "options", "answer", "explanation"))]
    if len(valid_quiz) < len(quiz):
        st.warning(f"Skipped {len(quiz) - len(valid_quiz)} malformed question(s).")

    with st.form("quiz_form"):
        picks = {}
        for i, q in enumerate(valid_quiz):
            st.markdown(
                f'<div class="card" style="margin:12px 0"><div class="eyebrow">QUESTION {i+1}</div>'
                f'<div class="display-small" style="font-size:22px;margin:8px 0 12px">{esc(q["question"])}</div></div>',
                unsafe_allow_html=True,
            )
            options = q["options"]
            picks[i] = st.radio(
                f"q_{i}", list(options.keys()),
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                key=f"quiz_pick_{i}", label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Submit answers  →", use_container_width=True, type="primary")

    if submitted:
        st.session_state.quiz_submitted = True

    if st.session_state.get("quiz_submitted"):
        correct = sum(1 for i, q in enumerate(valid_quiz) if picks[i] == q["answer"])
        st.markdown(
            f'<div class="metric-ring" style="max-width:260px;margin-bottom:16px">'
            f'<div class="metric-number">{correct}/{len(valid_quiz)}</div>'
            f'<div class="metric-label">Correct answers</div></div>',
            unsafe_allow_html=True,
        )
        for i, q in enumerate(valid_quiz):
            is_right = picks[i] == q["answer"]
            if is_right:
                st.success(f"Q{i+1}: Correct")
            else:
                st.error(f"Q{i+1}: Your answer {picks[i]} — correct answer {q['answer']}")
            st.caption(q["explanation"])


def render_evaluation_tab():
    st.caption("Measure how faithfully and precisely your RAG system answers lecture questions.")
    with st.form("eval_form"):
        st.markdown('<div class="card"><div class="eyebrow">TEST SET</div><h3 style="font-family:Newsreader;font-size:24px;margin:8px 0">Add evaluation questions</h3>', unsafe_allow_html=True)
        q1 = st.text_input("Question 1")
        a1 = st.text_input("Expected answer 1")
        q2 = st.text_input("Question 2")
        a2 = st.text_input("Expected answer 2")
        q3 = st.text_input("Question 3")
        a3 = st.text_input("Expected answer 3")
        run_eval = st.form_submit_button("Run evaluation  →", use_container_width=True, type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    if run_eval:
        test_qa = []
        for q, a in [(q1, a1), (q2, a2), (q3, a3)]:
            if q.strip() and a.strip():
                test_qa.append({"question": q, "ground_truth": a})
        if not test_qa:
            st.warning("Please add at least one question and expected answer.")
            return
        try:
            with st.spinner("Running RAGAS evaluation..."):
                from features.evaluator import quick_evaluate
                scores = quick_evaluate(st.session_state.rag, test_qa)
        except Exception as e:
            st.error(f"Evaluation failed: {e}")
            return

        cols = st.columns(4)
        metrics = [
            ("Faithfulness", scores.get("faithfulness")),
            ("Answer Relevancy", scores.get("answer_relevancy")),
            ("Context Precision", scores.get("context_precision")),
            ("Context Recall", scores.get("context_recall")),
        ]
        for col, (name, score) in zip(cols, metrics):
            with col:
                display_score = f"{score:.3f}" if isinstance(score, (int, float)) else "N/A"
                st.markdown(f'<div class="metric-ring"><div class="metric-number">{display_score}</div><div class="metric-label">{esc(name)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-head"><div><h2>Vector index health</h2><p>Pipeline information available from the current app session.</p></div></div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        for col, label, value in [
            (a, "Indexed chunks", len(st.session_state.docs or [])),
            (b, "Retriever", "Dense + BM25"),
            (c, "Evaluation items", len(test_qa)),
        ]:
            with col:
                st.markdown(f'<div class="card"><div class="stat-label">{esc(label)}</div><div class="stat-value" style="font-size:26px">{esc(value)}</div></div>', unsafe_allow_html=True)


def render_workspace():
    if not require_processed():
        return
    render_workspace_header("Study Workspace", "Chat, review notes, practice, and check retrieval quality — all on the same indexed lecture.")

    tab_chat, tab_summary, tab_quiz, tab_eval = st.tabs(["💬 Chat", "≡ Summary", "✓ Quiz", "◉ Evaluation"])
    with tab_chat:
        render_chat_tab()
    with tab_summary:
        render_summary_tab()
    with tab_quiz:
        render_quiz_tab()
    with tab_eval:
        render_evaluation_tab()


def render_my_lectures():
    st.markdown('<div class="eyebrow">LIBRARY</div>', unsafe_allow_html=True)
    st.markdown('<div class="display-small">My Lectures</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">This version keeps lecture state in the active Streamlit session. Persistent multi-lecture history can be added later.</div>', unsafe_allow_html=True)
    if st.session_state.processed:
        st.markdown('<div class="card" style="margin-top:24px"><div class="lecture-icon">📚</div><div class="lecture-title">Current processed lecture</div><div class="lecture-meta">Indexed and ready for chat, summary, quiz and evaluation.</div></div>', unsafe_allow_html=True)
        if st.button("Open study workspace →", key="open_workspace_from_library"):
            set_page("Workspace")
            st.rerun()
    else:
        st.info("No lecture is loaded in this session. Start from Dashboard.")


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
page = st.session_state.page
if page == "Dashboard":
    render_dashboard()
elif page in ("Workspace", "Chat", "Summary", "Quiz", "Evaluation"):
    render_workspace()
elif page == "My Lectures":
    render_my_lectures()
else:
    render_dashboard()
