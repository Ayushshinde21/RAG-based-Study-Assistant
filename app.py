import os
import tempfile
import html
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Campus Study Desk | AI Study Assistant",
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
        --ivory: #f4f8f6;
        --paper: #ffffff;
        --paper-2: #eaf4f1;
        --line: #dce9e4;
        --line-strong: #bfd6ce;
        --ink: #173336;
        --muted: #587271;
        --soft: #78918e;
        --forest: #087f73;
        --forest-dark: #075f57;
        --forest-text: #ffffff;
        --sage: #d9f4e9;
        --sage-2: #9ed8c5;
        --amber: #fff0c8;
        --amber-ink: #795514;
        --coral: #ed8b61;
        --shadow: rgba(17, 74, 66, .075);
"""

_DARK_VARS = """
        --ivory: #101b1c;
        --paper: #182626;
        --paper-2: #203332;
        --line: #304746;
        --line-strong: #46635f;
        --ink: #eef9f5;
        --muted: #b3cbc4;
        --soft: #8da9a2;
        --forest: #69d9bd;
        --forest-dark: #a2f0d8;
        --forest-text: #102c29;
        --sage: #244b43;
        --sage-2: #3b7568;
        --amber: #4c4022;
        --amber-ink: #ffe5a0;
        --coral: #ffad83;
        --shadow: rgba(0, 0, 0, .24);
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
# Student-first study dashboard theme
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

    html { font-size: 16px; }
    .stApp, .stApp button, .stApp input, .stApp textarea {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        font-size: 15px;
        color: var(--ink);
        background: var(--ivory);
        -webkit-font-smoothing: antialiased;
        transition: background .2s ease, color .2s ease;
    }
    [data-testid="stIconMaterial"], .material-symbols-rounded {
        font-family: 'Material Symbols Rounded' !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown li, label,
    [data-testid="stWidgetLabel"] p { color: var(--ink); }
    .stCaption, [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p { color: var(--muted); }
    .main .block-container { max-width: 1450px; padding: 5.2rem 2.4rem 3.2rem; }

    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; }

    /* Navigation */
    [data-testid="stSidebar"] {
        background: var(--paper);
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1.1rem; }
    [data-testid="stSidebarContent"] { padding: 0 1rem 1rem; }
    [data-testid="stSidebar"] h3 {
        font-family: 'Plus Jakarta Sans', sans-serif;
        letter-spacing: -.04em;
        font-size: 19px;
    }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 12px;
        border: 1px solid transparent;
        background: transparent;
        color: var(--muted);
        text-align: left;
        justify-content: flex-start;
        min-height: 43px;
        font-family: 'Plus Jakarta Sans', sans-serif;
        font-size: 13px;
        font-weight: 600;
        transition: background .15s ease, border-color .15s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: var(--paper-2);
        color: var(--ink);
        border-color: var(--line);
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--sage) !important;
        color: var(--forest-dark) !important;
        border: 1px solid var(--sage-2) !important;
        font-weight: 700;
    }
    .nav-label {
        color: var(--soft); text-transform: uppercase; letter-spacing: .12em;
        font-size: 10px; font-weight: 800; margin: 20px 0 7px;
    }

    /* Top bar */
    .topbar {
        position: fixed; top: 0; left: 0; right: 0; height: 58px; z-index: 99;
        background: color-mix(in srgb, var(--ivory) 92%, transparent);
        backdrop-filter: blur(14px); border-bottom: 1px solid var(--line);
        display: flex; align-items: center; justify-content: flex-end;
        padding: 0 2.4rem; pointer-events: none;
    }
    .top-meta { display:flex; gap:8px; align-items:center; color:var(--muted); font-size:12px; pointer-events:auto; }
    .status-pill {
        padding: 6px 11px; border: 1px solid var(--line); border-radius: 999px;
        background: var(--paper); box-shadow: 0 2px 8px var(--shadow);
    }

    /* Typography */
    .display {
        font-family: 'Plus Jakarta Sans', sans-serif; font-size: 38px; line-height: 1.16;
        font-weight: 800; letter-spacing: -.055em; color: var(--ink);
    }
    .display-small {
        font-family: 'Plus Jakarta Sans', sans-serif; font-size: 27px; line-height: 1.25;
        font-weight: 800; letter-spacing: -.04em; color: var(--ink);
    }
    .subtitle { color: var(--muted); font-size: 14px; line-height: 1.75; max-width: 760px; }
    .eyebrow { color: var(--forest); text-transform: uppercase; letter-spacing: .13em; font-size: 10px; font-weight: 800; }
    .section-head { display:flex; align-items:end; justify-content:space-between; gap:20px; margin: 30px 0 14px; }
    .section-head h2 { font-family:'Plus Jakarta Sans',sans-serif; font-size:21px; font-weight:800; letter-spacing:-.035em; margin:0; color:var(--ink); }
    .section-head p { color:var(--muted); font-size:12px; margin:5px 0 0; }

    /* Alternate concept: ocean-toned campus study desk */
    .student-hero {
        position: relative; overflow: hidden; display: flex; align-items: center;
        justify-content: space-between; gap: 28px; padding: 31px 34px; min-height: 270px;
        border-radius: 22px; color: #fff;
        background: linear-gradient(118deg, #103e45 0%, #08786f 58%, #159784 100%);
        box-shadow: 0 16px 34px rgba(8, 95, 83, .18);
        margin: 10px 0 8px;
    }
    .student-hero:after { content:''; position:absolute; width:290px; height:290px; right:185px; top:-205px; border:1px solid rgba(255,255,255,.12); border-radius:50%; box-shadow:0 0 0 28px rgba(255,255,255,.035), 0 0 0 58px rgba(255,255,255,.025); }
    .hero-content { position: relative; z-index: 2; max-width: 690px; }
    .hero-kicker { display: inline-flex; gap: 7px; align-items: center; padding: 7px 11px; border-radius: 999px; border: 1px solid rgba(255,255,255,.24); background: rgba(255,255,255,.1); color: #dcfff3; font-size: 10px; font-weight: 800; text-transform: uppercase; letter-spacing: .1em; }
    .hero-title { margin: 14px 0 11px; color: #fff; font-family: 'Plus Jakarta Sans', sans-serif; font-size: clamp(30px, 3.3vw, 42px); font-weight: 800; letter-spacing: -.055em; line-height: 1.12; }
    .hero-copy { color: #dcf5ed; font-size: 14px; line-height: 1.75; max-width: 590px; margin: 0; }
    .hero-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 22px; }
    .hero-meta span { padding: 7px 10px; border: 1px solid rgba(255,255,255,.2); background: rgba(255,255,255,.09); border-radius: 9px; color: #fff; font-size: 11px; font-weight: 600; }
    .hero-art { position: relative; z-index: 2; width: 280px; min-width: 255px; display: flex; align-items: center; justify-content: center; }
    .hero-board { width: 252px; padding: 17px; border-radius: 17px; background: #fffdf7; color: #173c3b; box-shadow: 0 16px 32px rgba(4, 49, 47, .2); transform: rotate(1.5deg); }
    .hero-board-top { display:flex; justify-content:space-between; align-items:center; gap:10px; padding-bottom:12px; border-bottom:1px solid #e4ebe6; }
    .hero-board-label { font-size:10px; font-weight:800; letter-spacing:.09em; color:#66827b; }
    .hero-board-badge { white-space:nowrap; padding:5px 8px; border-radius:999px; background:#fff0c8; color:#805a12; font-size:9px; font-weight:800; }
    .hero-step { display:flex; align-items:center; gap:10px; margin-top:13px; }
    .hero-step-num { flex:0 0 30px; width:30px; height:30px; display:grid; place-items:center; border-radius:9px; background:#d9f4e9; color:#087568; font-size:10px; font-weight:800; }
    .hero-step-num.gold { background:#fff0c8; color:#805a12; }
    .hero-step-num.coral { background:#ffe4d7; color:#a84f2f; }
    .hero-step-copy { min-width:0; }
    .hero-step-copy strong { display:block; font-size:11px; color:#173c3b; }
    .hero-step-copy small { display:block; margin-top:2px; font-size:9px; color:#6b817b; }
    .hero-board-footer { display:flex; align-items:center; gap:8px; margin-top:15px; padding-top:12px; border-top:1px solid #e4ebe6; color:#087568; font-size:9px; font-weight:800; }
    .hero-board-dot { width:7px; height:7px; border-radius:50%; background:#16a085; box-shadow:0 0 0 4px #d9f4e9; }

    /* Cards and student stats */
    .card, .st-key-summary_card, .st-key-continue_card,
    [data-testid="stForm"], [data-testid="stVerticalBlockBorderWrapper"] {
        background: var(--paper); border: 1px solid var(--line); border-radius: 18px;
        box-shadow: 0 5px 18px var(--shadow);
    }
    .card { padding: 20px; }
    .st-key-summary_card, .st-key-continue_card { padding: 22px 24px; }
    .card:hover { border-color: var(--sage-2); }
    .stat-card { min-height: 124px; padding: 19px 20px; }
    .stat-label { font-size:10px; text-transform:uppercase; letter-spacing:.09em; color:var(--soft); font-weight:800; }
    .stat-value { font-family:'Plus Jakarta Sans',sans-serif; font-size:30px; line-height:1.15; font-weight:800; letter-spacing:-.04em; margin-top:12px; color:var(--ink); }
    .stat-note { font-size:11px; color:var(--muted); margin-top:5px; }
    .card-copy { font-size:13px; color:var(--muted); line-height:1.7; }
    .card-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:20px; font-weight:800; letter-spacing:-.035em; margin:8px 0 4px; color:var(--ink); }
    .lecture-icon { width:46px; height:46px; border-radius:14px; background:var(--sage); display:grid; place-items:center; font-size:22px; }
    .lecture-title { font-family:'Plus Jakarta Sans',sans-serif; font-weight:800; font-size:15px; margin-top:14px; color:var(--ink); overflow-wrap:anywhere; }
    .lecture-meta { color:var(--soft); font-size:12px; line-height:1.7; margin:6px 0 10px; }
    .source-chip { display:inline-block; margin-left:6px; padding:4px 9px; border-radius:999px; background:var(--amber); color:var(--amber-ink); font-size:10px; font-weight:700; }

    /* Upload area */
    .upload-shell { background:var(--paper); border:1px solid var(--line); border-radius:20px; padding:24px 26px; margin-bottom:14px; box-shadow:0 5px 18px var(--shadow); }
    .upload-title { font-family:'Plus Jakarta Sans',sans-serif; font-size:22px; font-weight:800; letter-spacing:-.03em; color:var(--ink); }
    .upload-copy { color:var(--muted); font-size:13px; line-height:1.7; margin:6px 0 15px; max-width:800px; }
    .format-row { display:flex; gap:7px; flex-wrap:wrap; }
    .format-chip { border:1px solid var(--line); background:var(--paper-2); border-radius:8px; padding:5px 9px; font-size:11px; font-weight:700; color:var(--muted); }
    .workflow-number { display:grid; place-items:center; width:36px; height:36px; border-radius:11px; background:var(--sage); color:var(--forest-dark); font-size:12px; font-weight:800; }

    /* Evaluation metrics */
    .metric-ring { border:1px solid var(--line); border-radius:17px; padding:18px; background:var(--paper); text-align:center; box-shadow:0 5px 18px var(--shadow); }
    .metric-number { font-family:'Plus Jakarta Sans',sans-serif; font-size:32px; font-weight:800; letter-spacing:-.04em; color:var(--forest); }
    .metric-label { font-size:11px; color:var(--muted); margin-top:4px; }

    /* Inputs and buttons */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background:var(--paper) !important; border-color:var(--line) !important; border-radius:11px !important; color:var(--ink) !important;
    }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color:var(--soft) !important; opacity:1; }
    .stSlider [data-baseweb="slider"] { color:var(--forest); }
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        border-radius:11px; border:1px solid var(--line); background:var(--paper); color:var(--ink);
        font-family:'Plus Jakarta Sans',sans-serif; font-size:12px; font-weight:700; min-height:41px;
        transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color:var(--sage-2); color:var(--forest); box-shadow:0 4px 12px var(--shadow); }
    .stButton > button:active { transform:translateY(1px); }
    .stButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background:var(--forest) !important; color:var(--forest-text) !important; border:1px solid var(--forest) !important;
    }
    .stButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover { filter:brightness(1.08); color:var(--forest-text) !important; }
    [data-testid="stSidebar"] .st-key-nav_new .stButton > button[kind="primary"] {
        background:var(--forest) !important; color:var(--forest-text) !important; border:1px solid var(--forest) !important;
        justify-content:center !important; font-weight:800;
    }
    [data-testid="stSidebar"] .st-key-nav_new .stButton > button[kind="primary"]:hover { color:var(--forest-text) !important; background:var(--forest) !important; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { color:var(--forest-dark) !important; background:var(--sage) !important; }
    div[data-testid="stFileUploader"] section { border:1px dashed var(--line-strong); border-radius:14px; background:var(--paper-2); }
    div[data-testid="stFileUploader"] section, div[data-testid="stFileUploader"] small { color:var(--muted); }
    .stProgress > div > div > div > div { background:var(--forest); }

    /* Tabs, expandable information, and chat */
    .stTabs [data-baseweb="tab"] { color:var(--muted); font-size:12px; font-weight:700; }
    .stTabs [aria-selected="true"] { color:var(--forest) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color:var(--forest); height:3px; }
    .stTabs [data-baseweb="tab-border"] { background-color:var(--line); }
    [data-testid="stExpander"] details { background:var(--paper); border:1px solid var(--line); border-radius:13px; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color:var(--ink); }
    [data-testid="stChatMessage"] { background:var(--paper); border:1px solid var(--line); border-radius:15px; padding:12px 14px; }
    .stButton button p, .stDownloadButton button p, .stFormSubmitButton button p,
    [data-testid="stPopover"] button p, [data-testid="stFileUploader"] button p { color:inherit !important; }
    [data-baseweb="popover"] > div, [data-testid="stPopoverBody"] { background:var(--paper) !important; color:var(--ink) !important; border:1px solid var(--line); }
    [data-testid="stPopoverBody"] p, [data-testid="stPopoverBody"] span { color:var(--ink) !important; }
    [data-baseweb="menu"], [data-baseweb="menu"] li { background:var(--paper) !important; color:var(--ink) !important; }
    [data-testid="stToast"], [data-testid="stToast"] * { background:var(--paper) !important; color:var(--ink) !important; }
    [data-testid="stToast"] { border:1px solid var(--line); border-radius:12px; }
    [data-testid="stFileUploaderDropzoneInstructions"] span, [data-testid="stFileUploaderDropzoneInstructions"] small { color:var(--muted) !important; }
    [data-testid="stFileUploaderFileName"] { color:var(--ink) !important; }
    [data-testid="stFileUploader"] button { background:var(--paper) !important; color:var(--ink) !important; border:1px solid var(--line) !important; }
    [data-testid="stBottom"], [data-testid="stBottom"] > div { background:var(--ivory) !important; }
    [data-testid="stChatInput"] { background:var(--paper) !important; border:1px solid var(--line); border-radius:13px; }
    [data-testid="stChatInput"] textarea { color:var(--ink) !important; background:transparent !important; }
    [data-testid="stChatInput"] textarea::placeholder { color:var(--soft) !important; }
    [data-testid="stSliderThumbValue"], [data-testid="stTickBarMin"], [data-testid="stTickBarMax"] { color:var(--ink) !important; }

    @media (max-width: 900px) {
        .main .block-container { padding:5rem 1rem 2rem; }
        .topbar { padding:0 1rem; }
        .display { font-size:31px; }
        .display-small { font-size:24px; }
        .student-hero { padding:25px 23px; min-height:unset; }
        .hero-art { width:230px; min-width:215px; }
        .hero-board { width:215px; padding:14px; }
    }
    @media (max-width: 620px) {
        .student-hero { display:block; padding:24px 20px; }
        .hero-art { display:none; }
        .hero-title { font-size:32px; }
        .hero-meta span { font-size:10px; }
        .section-head { margin-top:24px; }
        .upload-shell { padding:20px; }
        .top-meta { gap:5px; font-size:10px; }
        .status-pill { padding:5px 8px; }
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
        "current_lecture_id": None,
        "just_processed": False,
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
    keep = {"theme": st.session_state.get("theme", "light")}
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    for k, v in keep.items():
        st.session_state[k] = v
    st.rerun()


# -----------------------------------------------------------------------------
# Top bar
# -----------------------------------------------------------------------------
lecture_state = "Lecture ready" if st.session_state.processed else "No lecture loaded"
st.markdown(
    f"""
    <div class="topbar">
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
    st.caption("Your personal study space")

    is_dark = st.session_state.theme == "dark"
    if st.button(
        "Light mode" if is_dark else "Dark mode",
        icon=":material/light_mode:" if is_dark else ":material/dark_mode:",
        use_container_width=True, key="theme_toggle",
    ):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()

    st.markdown("---")

    if st.button("New Lecture", icon=":material/add:", use_container_width=True,
                 key="nav_new", type="primary"):
        st.session_state.processed = False
        st.session_state.docs = None
        st.session_state.rag = None
        st.session_state.summary = None
        st.session_state.quiz = None
        st.session_state.chat_history = []
        st.session_state.current_lecture_id = None
        st.session_state.page = "Dashboard"
        st.rerun()

    st.markdown('<div class="nav-label">Your space</div>', unsafe_allow_html=True)
    for label, icon in [
        ("Dashboard", ":material/home:"),
        ("My Lectures", ":material/library_books:"),
    ]:
        is_active = st.session_state.page == label
        if st.button(label, icon=icon, use_container_width=True, key=f"nav_{label}",
                     type="primary" if is_active else "secondary"):
            set_page(label)
            st.rerun()

    st.markdown('<div class="nav-label">Study session</div>', unsafe_allow_html=True)
    if st.session_state.processed:
        is_active = st.session_state.page == "Workspace"
        if st.button("Study workspace", icon=":material/school:", use_container_width=True,
                     key="current_lecture", type="primary" if is_active else "secondary"):
            set_page("Workspace")
            st.rerun()
        st.caption(f"{len(st.session_state.docs or [])} indexed chunks")
    else:
        st.caption("Add your first lecture to get started.")

    st.markdown("---")

    if st.session_state.processed:
        if st.button("Reset workspace", icon=":material/refresh:", use_container_width=True, key="reset"):
            reset_app()

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Made for focused learning • VIT Pune • Group 14")

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
            from utils.transcriber import transcribe_with_timestamps, save_transcript
            segments = transcribe_with_timestamps(audio_path)
            transcript_path = save_transcript(segments, audio_path)
            st.session_state.transcript_path = transcript_path

            st.write("✂️ Chunking transcript")
            from core.chunker import chunk_from_file
            docs = chunk_from_file(transcript_path, method="semantic")
            st.session_state.docs = docs

            st.write("🔎 Building hybrid search index")
            from core.vector_store import (
                build_vector_store, get_dense_retriever,
                new_collection_name, register_lecture,
            )
            from core.bm25_index import build_bm25_retriever

            # Each lecture gets its own collection instead of one shared
            # collection that gets wiped on every upload — so past lectures
            # survive and can be reopened from "My Lectures".
            collection_name = new_collection_name()
            vector_store = build_vector_store(docs, reset=True, collection_name=collection_name)
            dense_retriever = get_dense_retriever(vector_store, k=10)
            bm25_retriever = build_bm25_retriever(docs, k=10)

            lecture_title = os.path.splitext(os.path.basename(audio_path))[0]
            lecture_id = register_lecture(
                title=lecture_title,
                collection_name=collection_name,
                num_chunks=len(docs),
                transcript_path=transcript_path,
            )
            st.session_state.current_lecture_id = lecture_id

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
        # st.success() right before st.rerun() is never visible; the toast is
        # shown on the next run instead (see render_workspace).
        st.session_state.just_processed = True
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
    st.markdown('<div class="eyebrow">CAMPUS STUDY DESK</div>', unsafe_allow_html=True)
    st.markdown(
        f'''<div class="student-hero">
            <div class="hero-content">
                <div class="hero-kicker">✦ CAMPUS STUDY DESK · {esc(greeting_for_now())}</div>
                <div class="hero-title">Learn it once.<br>Remember it better.</div>
                <p class="hero-copy">Bring your class recordings into one space. Get lecture-based answers, make revision notes, and practise the topics before your next test.</p>
                <div class="hero-meta"><span>01 · Understand</span><span>02 · Revise</span><span>03 · Practise</span></div>
            </div>
            <div class="hero-art" aria-hidden="true">
                <div class="hero-board">
                    <div class="hero-board-top"><span class="hero-board-label">YOUR STUDY ROUTINE</span><span class="hero-board-badge">3 steps</span></div>
                    <div class="hero-step"><span class="hero-step-num">01</span><div class="hero-step-copy"><strong>Capture the lecture</strong><small>Video, audio, or YouTube</small></div></div>
                    <div class="hero-step"><span class="hero-step-num gold">02</span><div class="hero-step-copy"><strong>Understand the ideas</strong><small>Ask questions and revise</small></div></div>
                    <div class="hero-step"><span class="hero-step-num coral">03</span><div class="hero-step-copy"><strong>Check your learning</strong><small>Practise with a quiz</small></div></div>
                    <div class="hero-board-footer"><span class="hero-board-dot"></span> YOUR LEARNING, IN ONE PLACE</div>
                </div>
            </div>
        </div>''',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="section-head"><div><h2>Your learning at a glance</h2><p>A quick look at what is ready in this session.</p></div></div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    values = [
        (c1, "LECTURE", "Ready" if st.session_state.processed else "Not added", "Current study session"),
        (c2, "LEARNING NOTES", len(st.session_state.docs or []), "Lecture chunks indexed"),
        (c3, "YOUR QUESTIONS", len([m for m in st.session_state.chat_history if m["role"] == "user"]), "Asked in this session"),
        (c4, "PRACTICE QUIZ", len(st.session_state.quiz or []), "Questions available"),
    ]
    for col, label, value, note in values:
        with col:
            st.markdown(
                f'<div class="card stat-card"><div class="stat-label">{esc(label)}</div><div class="stat-value">{esc(value)}</div><div class="stat-note">{esc(note)}</div></div>',
                unsafe_allow_html=True,
            )

    if st.session_state.processed:
        st.markdown('<div class="section-head"><div><h2>Pick up where you left off</h2><p>Your lecture is ready for active revision.</p></div></div>', unsafe_allow_html=True)
        with st.container(key="continue_card"):
            st.markdown(
                '<div class="eyebrow">CURRENT STUDY SESSION</div>'
                '<div class="display-small" style="margin:7px 0 8px">Your lecture is ready ✨</div>'
                f'<div class="card-copy">{len(st.session_state.docs or [])} indexed chunks are available. Ask questions, review the key ideas, or generate a quiz before your next class or exam.</div>',
                unsafe_allow_html=True,
            )
            st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)
            if st.button("Continue studying  →", type="primary", key="continue_btn"):
                set_page("Workspace")
                st.rerun()
    else:
        st.markdown('<div class="section-head"><div><h2>Start with a lecture</h2><p>Upload a class recording or use a YouTube lecture to build your study space.</p></div></div>', unsafe_allow_html=True)
        st.markdown(
            '''<div class="upload-shell">
                <div class="upload-title">📚 Add your first lecture</div>
                <div class="upload-copy">We will transcribe the recording, organize the content into searchable sections, and prepare it for question answering, revision notes, and quizzes.</div>
                <div class="format-row">
                    <span class="format-chip">MP4 video</span><span class="format-chip">MP3 audio</span><span class="format-chip">WAV</span>
                    <span class="format-chip">MKV</span><span class="format-chip">AVI</span><span class="format-chip">M4A</span>
                </div>
            </div>''',
            unsafe_allow_html=True,
        )
        up_tab, url_tab = st.tabs(["📁 Upload a recording", "▶ Use YouTube"])

        with up_tab:
            uploaded = st.file_uploader(
                "Choose a lecture file",
                type=["mp4", "mp3", "wav", "mkv", "avi", "m4a"],
                label_visibility="collapsed",
                key="dashboard_upload",
            )
            if uploaded and st.button("Create my study space  →", type="primary", use_container_width=True, key="process_dashboard"):
                process_uploaded_file(uploaded)

        with url_tab:
            yt_url = st.text_input(
                "YouTube URL",
                placeholder="Paste a lecture link, e.g. https://www.youtube.com/watch?v=...",
                label_visibility="collapsed",
                key="dashboard_youtube_url",
            )
            if yt_url.strip() and st.button("Build study space from link  →", type="primary", use_container_width=True, key="process_youtube"):
                process_uploaded_file(yt_url.strip())

    st.markdown('<div class="section-head"><div><h2>Choose your next study move</h2><p>Choose a study approach that matches what you need today.</p></div></div>', unsafe_allow_html=True)
    a, b, c = st.columns(3, gap="medium")
    workflow = [
        (a, "01", "Ask your lecture", "Get plain-language explanations, examples, and answers based on the material you uploaded.", "💬"),
        (b, "02", "Review key ideas", "Turn long recordings into structured notes that are easier to revisit before class or exams.", "📝"),
        (c, "03", "Test yourself", "Generate a practice quiz, submit your answers, and learn from the explanations.", "🎯"),
    ]
    for col, num, title, copy, icon in workflow:
        with col:
            st.markdown(
                f'<div class="card" style="height:100%"><div class="workflow-number">{num}</div><div class="card-title" style="margin-top:14px">{icon} {title}</div><p class="card-copy">{copy}</p></div>',
                unsafe_allow_html=True,
            )


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
            ts = doc.metadata.get("start_time_str")
            label = f"**Chunk {i} — around {ts}**" if ts else f"**Chunk {i}**"
            st.markdown(label)
            st.caption(doc.page_content[:400] + ("…" if len(doc.page_content) > 400 else ""))


def render_chat_tab():
    left, right = st.columns([1.8, 1], gap="large")

    with right:
        st.markdown('<div class="card"><div class="eyebrow">SUGGESTED QUESTIONS</div><div class="card-title" style="margin-bottom:6px">Study prompts</div></div>', unsafe_allow_html=True)
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
            '<div class="card-title">Knowledge base</div>'
            '<p class="card-copy">Your lecture is indexed using the existing dense + BM25 retrieval pipeline.</p>'
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
        chat_box = st.container(height=580)
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
        # Keyed container so the card actually wraps the summary content
        # (separate st.markdown calls can't open/close one HTML div).
        with st.container(key="summary_card"):
            st.markdown('<div class="eyebrow">YOUR REVISION NOTES</div>', unsafe_allow_html=True)
            st.markdown(summary)
        d1, d2, _ = st.columns([1, 1, 3])
        with d1:
            st.download_button("Download .txt", data=summary, file_name="lecture_summary.txt",
                               mime="text/plain", use_container_width=True)
        with d2:
            st.download_button("Download .md", data=summary, file_name="lecture_summary.md",
                               mime="text/markdown", use_container_width=True)
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
        # Clear old answers so a new quiz doesn't inherit stale radio selections
        for key in [k for k in st.session_state.keys() if k.startswith("quiz_pick_")]:
            del st.session_state[key]
        st.session_state.quiz_submitted = False
        st.rerun()

    quiz = st.session_state.quiz
    if not quiz:
        return

    valid_quiz = [q for q in quiz if all(k in q for k in ("question", "options", "answer", "explanation"))]
    if len(valid_quiz) < len(quiz):
        st.warning(f"Skipped {len(quiz) - len(valid_quiz)} malformed question(s).")

    with st.form("quiz_form", border=False):
        picks = {}
        for i, q in enumerate(valid_quiz):
            st.markdown(
                f'<div class="card" style="margin:12px 0 4px"><div class="eyebrow">QUESTION {i+1}</div>'
                f'<div class="display-small" style="font-size:22px;margin:8px 0 4px">{esc(q["question"])}</div></div>',
                unsafe_allow_html=True,
            )
            options = q["options"]
            picks[i] = st.radio(
                f"q_{i}", list(options.keys()),
                format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                index=None,  # nothing preselected, so unanswered != "A"
                key=f"quiz_pick_{i}", label_visibility="collapsed",
            )
        submitted = st.form_submit_button("Submit answers  →", use_container_width=True, type="primary")

    if submitted:
        unanswered = [i + 1 for i in range(len(valid_quiz)) if picks[i] is None]
        if unanswered:
            st.session_state.quiz_submitted = False
            st.warning("Please answer every question first. Missing: " + ", ".join(f"Q{n}" for n in unanswered))
        else:
            st.session_state.quiz_submitted = True

    if st.session_state.get("quiz_submitted") and all(picks[i] is not None for i in range(len(valid_quiz))):
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
    import pandas as pd

    st.caption("Advanced check: measure how accurately the assistant uses your lecture content to answer questions.")
    with st.form("eval_form"):
        st.markdown(
            '<div class="eyebrow">TEST SET</div>'
            '<div class="card-title" style="margin-bottom:6px">Add evaluation questions</div>'
            '<p class="card-copy">Add as many rows as you like. Rows with an empty cell are ignored.</p>',
            unsafe_allow_html=True,
        )
        edited = st.data_editor(
            pd.DataFrame({"question": [""] * 3, "ground_truth": [""] * 3}),
            num_rows="dynamic",
            use_container_width=True,
            hide_index=True,
            column_config={
                "question": st.column_config.TextColumn("Question", width="medium"),
                "ground_truth": st.column_config.TextColumn("Expected answer", width="large"),
            },
            key="eval_editor",
        )
        run_eval = st.form_submit_button("Run evaluation  →", use_container_width=True, type="primary")

    if run_eval:
        test_qa = []
        for _, row in edited.iterrows():
            q = str(row.get("question") or "").strip()
            a = str(row.get("ground_truth") or "").strip()
            if q and a:
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
    if st.session_state.get("just_processed"):
        st.session_state.just_processed = False
        st.toast("Your lecture is ready to study.", icon="✅")
    render_workspace_header("Your Study Workspace", "Ask questions, revise the lecture, and practise what you have learned — all in one place.")

    tab_chat, tab_summary, tab_quiz, tab_eval = st.tabs(["💬 Ask AI", "📝 Revision notes", "🎯 Practice quiz", "⚙ AI quality"])
    with tab_chat:
        render_chat_tab()
    with tab_summary:
        render_summary_tab()
    with tab_quiz:
        render_quiz_tab()
    with tab_eval:
        render_evaluation_tab()


def open_lecture(lecture: dict):
    """Reopen a previously processed lecture without re-running the pipeline —
    loads its existing Chroma collection and rebuilds BM25 from the same
    chunks (BM25's retriever only lives in memory, so it can't be persisted
    the way the vector store can)."""
    from core.vector_store import load_vector_store, get_all_docs_from_store, get_dense_retriever
    from core.bm25_index import build_bm25_retriever
    from core.rag_engine import RAGEngine

    with st.spinner(f"Opening “{lecture['title']}”..."):
        vector_store = load_vector_store(lecture["collection_name"])
        docs = get_all_docs_from_store(vector_store)
        dense_retriever = get_dense_retriever(vector_store, k=10)
        bm25_retriever = build_bm25_retriever(docs, k=10)

        st.session_state.docs = docs
        st.session_state.rag = RAGEngine(dense_retriever, bm25_retriever)
        st.session_state.transcript_path = lecture.get("transcript_path")
        st.session_state.current_lecture_id = lecture["id"]
        st.session_state.summary = None
        st.session_state.quiz = None
        st.session_state.quiz_submitted = False
        st.session_state.chat_history = []
        st.session_state.processed = True

    set_page("Workspace")
    st.rerun()


def render_my_lectures():
    from core.vector_store import list_lectures, delete_lecture

    st.markdown('<div class="eyebrow">YOUR LEARNING LIBRARY</div>', unsafe_allow_html=True)
    st.markdown('<div class="display-small">My Lecture Library</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">All your processed class recordings in one place. Reopen a lecture whenever you want to revise.</div>', unsafe_allow_html=True)

    lectures = list_lectures()
    if not lectures:
        st.info("Your library is empty for now. Add a lecture from the Dashboard to start building your revision library.")
        return

    st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
    grid = st.columns(2, gap="medium")
    for idx, lecture in enumerate(lectures):
        is_current = lecture["id"] == st.session_state.current_lecture_id
        with grid[idx % 2]:
            with st.container(border=True):
                st.markdown(
                    '<div class="lecture-icon">📚</div>'
                    f'<div class="lecture-title">{esc(lecture["title"])}'
                    + (' <span class="source-chip">Currently open</span>' if is_current else '')
                    + '</div>'
                    f'<div class="lecture-meta">{esc(lecture["num_chunks"])} indexed chunks · processed {esc(lecture["created_at"][:16].replace("T", " "))}</div>',
                    unsafe_allow_html=True,
                )
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("Open →", key=f"open_{lecture['id']}", use_container_width=True,
                                 disabled=is_current):
                        open_lecture(lecture)
                with c2:
                    # Deleting is permanent, so ask for confirmation first
                    with st.popover("Delete", use_container_width=True):
                        st.caption("This permanently removes the lecture and its index.")
                        if st.button("Yes, delete", key=f"confirm_delete_{lecture['id']}",
                                     type="primary", use_container_width=True):
                            delete_lecture(lecture["id"])
                            if is_current:
                                st.session_state.processed = False
                                st.session_state.current_lecture_id = None
                            st.rerun()


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