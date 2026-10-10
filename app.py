import os
# --- Stability fixes for Windows native crashes (no UI impact) ---------------
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE")   # duplicate OpenMP runtime
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
try:
    import torch  # noqa: F401  load torch DLLs first, before ctranslate2/chromadb
except Exception:
    pass
try:
    # Import the chunking stack at startup, BEFORE Whisper loads its native
    # libraries, so the DLLs don't clash mid-processing.
    import numpy  # noqa: F401
    import langchain_text_splitters  # noqa: F401
    import langchain_experimental.text_splitter  # noqa: F401
except Exception:
    pass
import gc
import re
import json
import math
import tempfile
import html
from urllib.parse import urlparse, parse_qs
from datetime import datetime, time as dtime, timedelta
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="AI Study Assistant | Learn Smarter with AI",
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
        --bg: #f8fafc;
        --paper: #ffffff;
        --paper-2: #f1f5f9;
        --line: #e2e8f0;
        --line-strong: #cbd5e1;
        --ink: #0f172a;
        --muted: #64748b;
        --soft: #94a3b8;
        --primary: #2563eb;
        --primary-hover: #1d4ed8;
        --primary-text: #ffffff;
        --primary-soft: #eff6ff;
        --primary-soft-2: #bfdbfe;
        --primary-ink: #2563eb;
        --emerald-bg: #ecfdf5;  --emerald-ink: #059669;
        --blue-bg: #eff6ff;     --blue-ink: #2563eb;
        --indigo-bg: #eef2ff;   --indigo-ink: #4f46e5;
        --amber-bg: #fffbeb;    --amber-ink: #d97706;
        --rose-bg: #fff1f2;     --rose-ink: #e11d48;
        --shadow: rgba(15, 23, 42, .07);
"""

_DARK_VARS = """
        --bg: #020617;
        --paper: #0f172a;
        --paper-2: #1e293b;
        --line: #1e293b;
        --line-strong: #334155;
        --ink: #f1f5f9;
        --muted: #94a3b8;
        --soft: #64748b;
        --primary: #3b82f6;
        --primary-hover: #2563eb;
        --primary-text: #ffffff;
        --primary-soft: #172554;
        --primary-soft-2: #1e40af;
        --primary-ink: #60a5fa;
        --emerald-bg: #052e24;  --emerald-ink: #34d399;
        --blue-bg: #172554;     --blue-ink: #60a5fa;
        --indigo-bg: #1e1b4b;   --indigo-ink: #818cf8;
        --amber-bg: #2e2208;    --amber-ink: #fbbf24;
        --rose-bg: #2a0f17;     --rose-ink: #fb7185;
        --shadow: rgba(0, 0, 0, .4);
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
# EdTech workspace theme (slate surfaces, royal-blue / indigo accents)
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

    html { font-size: 16px; }
    .stApp, .stApp button, .stApp input, .stApp textarea {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .stApp {
        font-size: 15px; color: var(--ink); background: var(--bg);
        -webkit-font-smoothing: antialiased; transition: background .2s ease, color .2s ease;
    }
    [data-testid="stIconMaterial"], .material-symbols-rounded { font-family: 'Material Symbols Rounded' !important; }
    .stMarkdown, .stMarkdown p, .stMarkdown li, label,
    [data-testid="stWidgetLabel"] p { color: var(--ink); }
    .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p { color: var(--muted); }

    /* Full-width app shell */
    [data-testid="stMainBlockContainer"], .main .block-container {
        max-width: 100% !important; padding: 0 0 3rem !important;
    }
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; pointer-events: none; }
    [data-testid="stHeader"] > * { pointer-events: auto; }
    [data-testid="stToolbar"] { visibility: hidden; }
    .st-key-page_body { width: 100%; max-width: 1280px; margin: 0 auto; padding: 1.8rem 2rem 1rem; }

    /* Top bar */
    .st-key-topbar { background: var(--paper); border-bottom: 1px solid var(--line); padding: .85rem 1.8rem; }
    .st-key-topbar [data-testid="stHorizontalBlock"] { align-items: center; }
    .status-pill {
        display: inline-flex; align-items: center; gap: 8px; padding: 6px 13px; border-radius: 999px;
        font-size: 12px; font-weight: 600; border: 1px solid var(--line);
    }
    .status-pill.ok { background: var(--emerald-bg); color: var(--emerald-ink); border-color: var(--emerald-ink); }
    .status-pill.idle { background: var(--paper-2); color: var(--muted); }
    .status-pill .dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }
    .status-pill.ok .dot { animation: pulse 1.8s ease-in-out infinite; }
    @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: .35; } }
    .engine-chip { display: inline-flex; gap: 7px; align-items: center; padding: 7px 12px; border-radius: 10px; background: var(--paper-2); color: var(--muted); font-size: 12px; font-weight: 600; }

    /* Sidebar */
    [data-testid="stSidebar"] { background: var(--paper); border-right: 1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0; }
    [data-testid="stSidebarContent"] { padding: 0 1rem 1rem; }
    .brand { display: flex; align-items: center; gap: 12px; padding: 18px 8px 16px; margin: 0 -4px 14px; border-bottom: 1px solid var(--line); }
    .brand-logo {
        width: 40px; height: 40px; border-radius: 12px; display: grid; place-items: center; font-size: 20px;
        background: linear-gradient(45deg, #2563eb, #4f46e5); box-shadow: 0 6px 14px rgba(37, 99, 235, .25);
    }
    .brand-name { font-weight: 800; font-size: 17px; line-height: 1.2; background: linear-gradient(90deg, #2563eb, #4f46e5); -webkit-background-clip: text; background-clip: text; color: transparent; }
    .brand-sub { font-size: 11px; color: var(--soft); font-weight: 500; margin-top: 1px; }
    [data-testid="stSidebar"] hr { border-color: var(--line); margin: 14px 0; }
    [data-testid="stSidebar"] .stButton > button {
        border-radius: 12px; border: 1px solid transparent; background: transparent; color: var(--muted);
        text-align: left; justify-content: flex-start; min-height: 46px; font-size: 14px; font-weight: 500;
        transition: background .15s ease, color .15s ease;
    }
    [data-testid="stSidebar"] .stButton > button:hover { background: var(--paper-2); color: var(--ink); border-color: transparent; box-shadow: none; }
    [data-testid="stSidebar"] .stButton > button[kind="primary"] {
        background: var(--primary-soft) !important; color: var(--primary-ink) !important;
        border: 1px solid transparent !important; font-weight: 600; box-shadow: none;
    }
    [data-testid="stSidebar"] .stButton > button[kind="primary"]:hover { filter: brightness(.97); color: var(--primary-ink) !important; }
    .st-key-reset .stButton > button { color: var(--rose-ink) !important; }
    .st-key-reset .stButton > button:hover { background: var(--rose-bg) !important; }
    .nav-label { color: var(--soft); text-transform: uppercase; letter-spacing: .1em; font-size: 11px; font-weight: 600; margin: 20px 4px 7px; }

    /* Typography */
    .page-title { font-size: 26px; font-weight: 800; letter-spacing: -.03em; color: var(--ink); line-height: 1.2; }
    .page-sub { color: var(--muted); font-size: 13px; margin-top: 4px; }
    .sec-title { font-size: 18px; font-weight: 700; color: var(--ink); margin: 0; letter-spacing: -.01em; }
    .sec-sub { font-size: 12px; color: var(--muted); margin-top: 3px; }
    .section-gap { height: 26px; }
    .eyebrow { color: var(--primary-ink); text-transform: uppercase; letter-spacing: .1em; font-size: 11px; font-weight: 700; }

    /* Welcome banner */
    .st-key-hero_card {
        position: relative; overflow: hidden; border-radius: 24px; padding: 38px 42px 36px;
        background: linear-gradient(90deg, #2563eb 0%, #4f46e5 52%, #1d4ed8 100%);
        box-shadow: 0 18px 38px rgba(37, 99, 235, .18);
    }
    .st-key-hero_card:after { content: '🎓'; position: absolute; right: 10px; bottom: -48px; font-size: 270px; line-height: 1; opacity: .12; pointer-events: none; }
    .st-key-hero_card > * { position: relative; z-index: 2; }
    .hero-content { max-width: 640px; }
    .hero-pill { display: inline-flex; gap: 7px; align-items: center; padding: 5px 13px; border-radius: 999px; background: rgba(255,255,255,.14); color: #fff; font-size: 12px; font-weight: 600; }
    .hero-title { margin: 16px 0 10px; color: #fff; font-size: clamp(28px, 3.2vw, 40px); font-weight: 800; letter-spacing: -.035em; line-height: 1.15; }
    .hero-copy { color: #dbeafe; font-size: 15px; line-height: 1.7; margin: 0 0 6px; }
    .st-key-hero_card [data-testid="stHorizontalBlock"] { gap: .7rem; }
    .st-key-hero_continue .stButton > button {
        background: #fff !important; color: #2563eb !important; border: none !important;
        font-weight: 700; min-height: 46px; padding: 0 22px; border-radius: 12px; box-shadow: 0 8px 18px rgba(0, 20, 90, .22);
    }
    .st-key-hero_continue .stButton > button:hover { background: #eff6ff !important; color: #2563eb !important; }
    .st-key-hero_continue .stButton > button:disabled { opacity: .65; }
    .st-key-hero_upload .stButton > button {
        background: rgba(29, 78, 216, .6) !important; color: #fff !important; border: 1px solid rgba(255,255,255,.25) !important;
        font-weight: 700; min-height: 46px; padding: 0 22px; border-radius: 12px;
    }
    .st-key-hero_upload .stButton > button:hover { background: #1d4ed8 !important; color: #fff !important; }

    /* Cards */
    [data-testid="stVerticalBlockBorderWrapper"], [data-testid="stForm"], .card {
        background: var(--paper); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 1px 3px var(--shadow);
    }
    .card { padding: 20px; }
    [data-testid="stForm"] { padding: 18px 20px; }
    .stat-card { padding: 20px; display: flex; align-items: center; justify-content: space-between; gap: 10px; min-height: 108px; }
    .stat-label { font-size: 12px; font-weight: 500; color: var(--muted); }
    .stat-value { font-size: 20px; font-weight: 700; margin-top: 4px; }
    .stat-note { font-size: 10px; color: var(--soft); margin-top: 3px; }
    .stat-icon { width: 48px; height: 48px; border-radius: 12px; display: grid; place-items: center; font-size: 22px; flex: 0 0 48px; }
    .t-emerald { background: var(--emerald-bg); color: var(--emerald-ink); }
    .t-blue { background: var(--blue-bg); color: var(--blue-ink); }
    .t-indigo { background: var(--indigo-bg); color: var(--indigo-ink); }
    .t-amber { background: var(--amber-bg); color: var(--amber-ink); }
    .t-rose { background: var(--rose-bg); color: var(--rose-ink); }

    /* Ingestion center */
    .chip { display: inline-block; padding: 4px 10px; border-radius: 8px; background: var(--paper-2); color: var(--muted); font-size: 12px; font-weight: 500; margin-left: 6px; }
    .yt-head { display: flex; align-items: center; gap: 9px; font-weight: 600; font-size: 14px; margin-bottom: 6px; }
    .yt-icon { width: 32px; height: 32px; border-radius: 9px; background: var(--rose-bg); color: var(--rose-ink); display: grid; place-items: center; font-size: 14px; }
    .st-key-yt_box { background: var(--paper-2); border: 1px solid var(--line); border-radius: 16px; padding: 20px; height: 100%; }
    div[data-testid="stFileUploader"] section { border: 2px dashed var(--line-strong); border-radius: 16px; background: var(--paper-2); padding: 1.3rem; transition: border-color .15s ease; }
    div[data-testid="stFileUploader"] section:hover { border-color: var(--primary); }
    div[data-testid="stFileUploader"] section, div[data-testid="stFileUploader"] small { color: var(--muted); }

    /* Study tool cards */
    [class*="st-key-tool_"] {
        position: relative; background: var(--paper); border: 1px solid var(--line); border-radius: 16px;
        padding: 22px; box-shadow: 0 1px 3px var(--shadow); transition: box-shadow .18s ease, border-color .18s ease;
    }
    [class*="st-key-tool_"]:hover { box-shadow: 0 10px 26px var(--shadow); border-color: var(--primary-soft-2); }
    .tool-icon { width: 48px; height: 48px; border-radius: 12px; display: grid; place-items: center; font-size: 22px; margin-bottom: 16px; transition: background .18s ease, color .18s ease; }
    [class*="st-key-tool_"]:hover .tool-icon { background: var(--hov) !important; color: #fff !important; }
    .tool-title { font-weight: 700; font-size: 14px; margin-bottom: 4px; color: var(--ink); }
    .tool-copy { font-size: 12px; color: var(--muted); line-height: 1.6; }

    /* Lecture cards */
    .lec-banner { position: relative; height: 128px; border-radius: 12px; display: grid; place-items: center; font-size: 42px; margin-bottom: 14px; }
    .grad0 { background: linear-gradient(135deg, #2563eb, #4f46e5); }
    .grad1 { background: linear-gradient(135deg, #4f46e5, #7c3aed); }
    .grad2 { background: linear-gradient(135deg, #0ea5e9, #2563eb); }
    .grad3 { background: linear-gradient(135deg, #0d9488, #2563eb); }
    .lec-badge { position: absolute; top: 10px; left: 10px; padding: 4px 10px; border-radius: 8px; background: rgba(0,0,0,.55); color: #fff; font-size: 10px; font-weight: 600; }
    .lec-active { position: absolute; top: 10px; right: 10px; padding: 4px 10px; border-radius: 8px; background: #10b981; color: #fff; font-size: 10px; font-weight: 700; }
    .lec-meta { font-size: 12px; color: var(--soft); margin-bottom: 6px; }
    .lec-title { font-weight: 700; font-size: 15px; color: var(--ink); overflow-wrap: anywhere; line-height: 1.35; margin-bottom: 8px; }
    .lec-foot { font-size: 11px; color: var(--soft); padding-top: 8px; }

    /* Buttons and inputs */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        border-radius: 12px; border: 1px solid var(--line); background: var(--paper); color: var(--ink);
        font-size: 13px; font-weight: 600; min-height: 42px;
        transition: transform .15s ease, border-color .15s ease, box-shadow .15s ease, background .15s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color: var(--primary-soft-2); color: var(--primary-ink); box-shadow: 0 4px 12px var(--shadow); }
    .stButton > button:focus-visible { outline: 3px solid var(--primary-soft-2); outline-offset: 1px; }
    .stButton > button:active { transform: translateY(1px); }
    .stButton > button:disabled { opacity: .5; cursor: not-allowed; }
    .stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"], .stFormSubmitButton > button[kind="primary"] {
        background: var(--primary) !important; color: var(--primary-text) !important; border: 1px solid var(--primary) !important;
        box-shadow: 0 4px 12px rgba(37, 99, 235, .22);
    }
    .stButton > button[kind="primary"]:hover, .stDownloadButton > button[kind="primary"]:hover, .stFormSubmitButton > button[kind="primary"]:hover {
        background: var(--primary-hover) !important; color: var(--primary-text) !important;
    }
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background: var(--paper) !important; border-color: var(--line-strong) !important; border-radius: 12px !important; color: var(--ink) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus { border-color: var(--primary) !important; box-shadow: 0 0 0 3px var(--primary-soft-2) !important; }
    .stTextInput input::placeholder, .stTextArea textarea::placeholder { color: var(--soft) !important; opacity: 1; }
    .stSlider [data-baseweb="slider"] { color: var(--primary); }
    .stProgress > div > div > div > div { background: var(--primary); }

    /* Workspace header and segmented tabs */
    .st-key-ws_header { background: var(--paper); border: 1px solid var(--line); border-radius: 16px; padding: 18px 22px; box-shadow: 0 1px 3px var(--shadow); margin-bottom: 22px; }
    .st-key-ws_header [data-testid="stHorizontalBlock"] { align-items: center; }
    .ws-title { font-size: 21px; font-weight: 800; letter-spacing: -.02em; color: var(--ink); margin: 3px 0; overflow-wrap: anywhere; }
    .ws-sub { font-size: 12px; color: var(--muted); }
    .st-key-ws_tab_radio [role="radiogroup"] { gap: 4px; flex-wrap: wrap; background: var(--paper-2); padding: 4px; border-radius: 12px; width: fit-content; max-width: 100%; margin-left: auto; }
    .st-key-ws_tab_radio label { padding: 8px 14px; border-radius: 9px; cursor: pointer; margin: 0 !important; transition: background .15s ease; }
    .st-key-ws_tab_radio label > div:first-child { display: none; }
    .st-key-ws_tab_radio label p { font-size: 12px; font-weight: 600; color: var(--muted); }
    .st-key-ws_tab_radio label:hover p { color: var(--ink); }
    .st-key-ws_tab_radio label:has(input:checked) { background: var(--paper); box-shadow: 0 1px 3px var(--shadow); }
    .st-key-ws_tab_radio label:has(input:checked) p { color: var(--primary-ink); }

    .st-key-ws_chat, .st-key-ws_notes, .st-key-ws_eval { width: 100%; max-width: 56rem; margin: 0 auto; }
    .st-key-ws_quiz { width: 100%; max-width: 48rem; margin: 0 auto; }

    /* Chat */
    .st-key-chat_card { background: var(--paper); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 1px 3px var(--shadow); overflow: hidden; gap: 0; }
    .st-key-chat_card [data-testid="stVerticalBlock"] { gap: .5rem; }
    .st-key-chat_pills { border-top: 1px solid var(--line); background: var(--paper-2); padding: 10px 16px; }
    .st-key-chat_pills [data-testid="stHorizontalBlock"] { align-items: center; gap: .5rem; }
    .suggest-label { font-size: 12px; font-weight: 600; color: var(--soft); }
    [class*="st-key-suggest_"] .stButton > button, .st-key-clear_chat .stButton > button {
        border-radius: 999px; background: var(--paper); border: 1px solid var(--line-strong); font-size: 11px; font-weight: 500;
        min-height: 32px; padding: 4px 12px; line-height: 1.3;
    }
    [class*="st-key-suggest_"] .stButton > button:hover { border-color: var(--primary); color: var(--primary-ink); }
    .bot-row { display: flex; gap: 12px; align-items: flex-start; }
    .bot-avatar { width: 32px; height: 32px; border-radius: 10px; background: var(--primary); display: grid; place-items: center; flex: 0 0 32px; font-size: 15px; }
    .bot-bubble { background: var(--paper-2); border-radius: 16px; padding: 14px 16px; max-width: 36rem; font-size: 14px; line-height: 1.65; color: var(--ink); }
    .bot-bubble b { color: var(--primary-ink); }
    [data-testid="stChatMessage"] { background: var(--paper-2); border: none; border-radius: 16px; padding: 12px 14px; margin-bottom: 8px; line-height: 1.7; }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) { background: var(--primary); }
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) p,
    [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) .stMarkdown { color: #fff; }
    [data-testid="stChatMessageAvatarAssistant"] { background: var(--primary) !important; color: #fff !important; }
    [data-testid="stChatInput"] { background: var(--paper-2) !important; border: 1px solid var(--line-strong); border-radius: 12px; }
    [data-testid="stChatInput"] textarea { color: var(--ink) !important; background: transparent !important; }
    [data-testid="stChatInput"] textarea::placeholder { color: var(--soft) !important; }
    [data-testid="stChatInputSubmitButton"] { background: var(--primary) !important; color: #fff !important; border-radius: 10px; }
    [data-testid="stBottom"], [data-testid="stBottom"] > div { background: var(--bg) !important; }
    .stSpinner > div > i, [data-testid="stSpinner"] i { border-top-color: var(--primary) !important; }

    /* Notes, quiz, evaluation */
    .st-key-summary_card { background: var(--paper); border: 1px solid var(--line); border-radius: 16px; box-shadow: 0 1px 3px var(--shadow); padding: 32px 36px; line-height: 1.85; font-size: 14px; }
    .st-key-summary_card h1, .st-key-summary_card h2, .st-key-summary_card h3 { color: var(--ink); letter-spacing: -.02em; }
    .st-key-summary_card h2, .st-key-summary_card h3 { margin-top: 1.3rem; padding-bottom: .3rem; border-bottom: 1px solid var(--line); }
    [class*="st-key-quiz_pick_"] [role="radiogroup"] { gap: 8px; }
    [class*="st-key-quiz_pick_"] label { background: var(--paper); border: 1px solid var(--line-strong); border-radius: 12px; padding: 11px 14px; width: 100%; margin: 0 !important; transition: border-color .15s ease, background .15s ease; }
    [class*="st-key-quiz_pick_"] label:hover { border-color: var(--primary); background: var(--paper-2); }
    [class*="st-key-quiz_pick_"] label:has(input:checked) { border-color: var(--primary); background: var(--primary-soft); }
    .st-key-quiz_wrap .stFormSubmitButton > button, .st-key-quiz_wrap [data-testid="stFormSubmitButton"] button {
        background: #059669 !important; border-color: #059669 !important; color: #fff !important; min-height: 46px; padding: 0 24px;
        box-shadow: 0 8px 18px rgba(5, 150, 105, .22);
    }
    .st-key-quiz_wrap .stFormSubmitButton > button:hover { background: #047857 !important; }
    .st-key-quiz_wrap .stElementContainer:has(.stFormSubmitButton), .st-key-quiz_wrap [data-testid="stFormSubmitButton"] { display: flex; justify-content: flex-end; }
    .m-tile { background: var(--paper-2); border: 1px solid var(--line); border-radius: 12px; padding: 16px; }
    .m-label { font-size: 12px; color: var(--soft); }
    .m-value { font-size: 26px; font-weight: 800; margin-top: 4px; letter-spacing: -.02em; }
    .m-note { font-size: 10px; color: var(--muted); margin-top: 4px; }
    .metric-ring { border: 1px solid var(--line); border-radius: 16px; padding: 18px; background: var(--paper); text-align: center; box-shadow: 0 1px 3px var(--shadow); }
    .metric-number { font-size: 32px; font-weight: 800; letter-spacing: -.04em; color: var(--primary-ink); }
    .metric-label { font-size: 11px; color: var(--muted); margin-top: 4px; }

    /* Tabs, expanders, popovers, menus */
    .stTabs [data-baseweb="tab"] { color: var(--muted); font-size: 12px; font-weight: 600; }
    .stTabs [aria-selected="true"] { color: var(--primary-ink) !important; }
    .stTabs [data-baseweb="tab-highlight"] { background-color: var(--primary); height: 3px; }
    .stTabs [data-baseweb="tab-border"] { background-color: var(--line); }
    [data-testid="stExpander"] details { background: var(--paper); border: 1px solid var(--line); border-radius: 12px; }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary p { color: var(--ink); }
    .stButton button p, .stDownloadButton button p, .stFormSubmitButton button p,
    [data-testid="stPopover"] button p, [data-testid="stFileUploader"] button p { color: inherit !important; }
    [data-baseweb="popover"] > div, [data-testid="stPopoverBody"] { background: var(--paper) !important; color: var(--ink) !important; border: 1px solid var(--line); }
    [data-testid="stPopoverBody"] p, [data-testid="stPopoverBody"] span { color: var(--ink) !important; }
    [data-baseweb="menu"], [data-baseweb="menu"] li { background: var(--paper) !important; color: var(--ink) !important; }
    [data-testid="stToast"], [data-testid="stToast"] * { background: var(--paper) !important; color: var(--ink) !important; }
    [data-testid="stToast"] { border: 1px solid var(--line); border-radius: 12px; }
    [data-testid="stFileUploaderDropzoneInstructions"] span, [data-testid="stFileUploaderDropzoneInstructions"] small { color: var(--muted) !important; }
    [data-testid="stFileUploaderFileName"] { color: var(--ink) !important; }
    [data-testid="stFileUploader"] button { background: var(--paper) !important; color: var(--ink) !important; border: 1px solid var(--line-strong) !important; }
    [data-testid="stSliderThumbValue"], [data-testid="stTickBarMin"], [data-testid="stTickBarMax"] { color: var(--ink) !important; }

    @media (max-width: 900px) {
        .st-key-page_body { padding: 1.2rem 1rem .5rem; }
        .st-key-topbar { padding: .7rem 1rem; }
        .st-key-hero_card { padding: 26px 22px; }
        .st-key-hero_card:after { font-size: 150px; }
        .st-key-summary_card { padding: 22px; }
        .st-key-ws_tab_radio [role="radiogroup"] { margin-left: 0; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# -----------------------------------------------------------------------------
# State
# -----------------------------------------------------------------------------
WORKSPACE_TABS = ["💬 Ask AI", "📝 Revision notes", "🎯 Practice quiz", "⚙ AI quality"]
WORKSPACE_PAGES = ("Workspace", "Chat", "Summary", "Quiz", "Evaluation")

STUDY_PROMPTS = [
    "Explain the core concept simply.",
    "What are the key points?",
    "Give me an example.",
    "What should I remember for an exam?",
]


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
        "ws_tab": WORKSPACE_TABS[0],
        "eval_scores": None,
        "summary_error": None,
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


def start_new_lecture():
    """Clear the current lecture so the Dashboard is ready for a new upload."""
    st.session_state.processed = False
    st.session_state.docs = None
    st.session_state.rag = None
    st.session_state.summary = None
    st.session_state.quiz = None
    st.session_state.chat_history = []
    st.session_state.current_lecture_id = None
    st.session_state.eval_scores = None
    st.session_state.summary_error = None
    st.session_state.quiz_submitted = False
    st.session_state.page = "Dashboard"


def go_to_tool(tab_label):
    """Callback for dashboard tool cards: open the Study Workspace on a tab."""
    st.session_state.ws_tab = tab_label
    st.session_state.page = "Workspace"


# -----------------------------------------------------------------------------
# Lecture list + custom titles (rename)
# -----------------------------------------------------------------------------
# Renamed titles are stored in a small JSON file next to the app and applied
# whenever lectures are loaded, so the new name shows everywhere. If you later
# add a rename_lecture() to core/vector_store.py, call it instead of
# save_title_override().
TITLE_OVERRIDES_FILE = "lecture_titles.json"


def load_title_overrides():
    try:
        with open(TITLE_OVERRIDES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def save_title_override(lecture_id, new_title):
    data = load_title_overrides()
    data[str(lecture_id)] = new_title
    with open(TITLE_OVERRIDES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def remove_title_override(lecture_id):
    data = load_title_overrides()
    if data.pop(str(lecture_id), None) is not None:
        with open(TITLE_OVERRIDES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


def get_lectures():
    try:
        from core.vector_store import list_lectures
        lectures = list_lectures() or []
    except Exception:
        return []
    overrides = load_title_overrides()
    out = []
    for lec in lectures:
        lec = dict(lec)
        custom = overrides.get(str(lec.get("id")))
        if custom:
            lec["title"] = custom
        out.append(lec)
    return out


def parse_created(lecture):
    raw = str(lecture.get("created_at", "")).strip().replace("Z", "")
    try:
        return datetime.fromisoformat(raw)
    except ValueError:
        return None


LECTURES = get_lectures()


def current_lecture():
    for lec in LECTURES:
        if lec.get("id") == st.session_state.current_lecture_id:
            return lec
    return None


def fmt_created(lecture):
    return str(lecture.get("created_at", ""))[:16].replace("T", " ")


# -----------------------------------------------------------------------------
# Validation and error helpers
# -----------------------------------------------------------------------------
ALLOWED_EXTENSIONS = ["mp4", "mp3", "wav", "mkv", "avi", "m4a"]
_YT_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be", "www.youtu.be"}


def validate_youtube_url(url):
    """Return (ok, message). Accepts links to a single YouTube video only."""
    url = (url or "").strip()
    if not url:
        return False, "Paste a YouTube link first."
    if len(url) > 500 or re.search(r"\s", url):
        return False, "That doesn't look like a valid YouTube link."
    try:
        parsed = urlparse(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return False, "That doesn't look like a valid URL."
    if parsed.scheme not in ("http", "https"):
        return False, "The link must start with http:// or https://."
    if host not in _YT_HOSTS:
        return False, "Only YouTube links are supported (youtube.com or youtu.be)."
    if host.endswith("youtu.be"):
        has_video = bool(parsed.path.strip("/"))
    else:
        has_video = bool(parse_qs(parsed.query).get("v")) or parsed.path.startswith(("/shorts/", "/embed/", "/live/"))
    if not has_video:
        return False, "That link doesn't point to a specific YouTube video."
    return True, ""


def validate_upload(uploaded):
    """Return (ok, message) for a Streamlit UploadedFile."""
    name = getattr(uploaded, "name", "") or ""
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXTENSIONS:
        return False, "Unsupported file type. Please upload one of: " + ", ".join(e.upper() for e in ALLOWED_EXTENSIONS) + "."
    if getattr(uploaded, "size", 1) == 0:
        return False, "This file is empty."
    return True, ""


def redact_secrets(text):
    """Remove any configured secret values from an error message before showing it."""
    text = str(text)
    for name, value in os.environ.items():
        if value and len(value) >= 8 and any(t in name.upper() for t in ("KEY", "TOKEN", "SECRET", "PASSWORD")):
            text = text.replace(value, "[hidden]")
    return text


def friendly_error(exc):
    msg = redact_secrets(exc)
    low = msg.lower()
    if isinstance(exc, ImportError):
        return f"A required package is missing ({getattr(exc, 'name', None) or 'unknown'}). Install the project requirements and try again."
    if "403" in msg or "forbidden" in low:
        return "The download was refused (HTTP 403). Try a different video, or upload the recording as a file instead."
    if "api key" in low or "api_key" in low or "401" in msg or "unauthorized" in low:
        return "The AI service rejected the request. Check that your API keys are configured."
    if "rate limit" in low or "429" in msg or "quota" in low:
        return "The AI service rate limit or quota was reached. Please wait a moment and try again."
    return msg or exc.__class__.__name__


def valid_quiz_items(quiz):
    """Only questions with text, 2+ options, an answer that is one of the options, and an explanation."""
    good = []
    for q in quiz or []:
        try:
            opts = q["options"]
            if (isinstance(q.get("question"), str) and q["question"].strip() and isinstance(opts, dict)
                    and len(opts) >= 2 and q.get("answer") in opts and str(q.get("explanation", "")).strip()):
                good.append(q)
        except Exception:
            continue
    return good


def metric_value(score):
    if isinstance(score, (int, float)) and not isinstance(score, bool) and not math.isnan(score):
        return f"{score * 100:.1f}%"
    return None


# -----------------------------------------------------------------------------
# Sidebar
# -----------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-logo">🎓</div>'
        '<div><div class="brand-name">AI Study Assistant</div>'
        '<div class="brand-sub">Learn Smarter with AI</div></div></div>',
        unsafe_allow_html=True,
    )

    on_workspace = st.session_state.page in WORKSPACE_PAGES

    if st.button("Dashboard", icon=":material/dashboard:", use_container_width=True, key="nav_Dashboard",
                 type="primary" if st.session_state.page == "Dashboard" else "secondary"):
        set_page("Dashboard")
        st.rerun()
    if st.button("Study Workspace", icon=":material/menu_book:", use_container_width=True, key="current_lecture",
                 type="primary" if on_workspace else "secondary"):
        set_page("Workspace")
        st.rerun()
    if st.button("My Lectures", icon=":material/library_books:", use_container_width=True, key="nav_My Lectures",
                 type="primary" if st.session_state.page == "My Lectures" else "secondary"):
        set_page("My Lectures")
        st.rerun()

    st.markdown('<div class="nav-label">Quick Actions</div>', unsafe_allow_html=True)
    if st.button("New Lecture", icon=":material/add_circle:", use_container_width=True,
                 key="nav_new", type="primary"):
        start_new_lecture()
        st.rerun()
    if st.button("Reset Workspace", icon=":material/refresh:", use_container_width=True, key="reset",
                 help="Clears this session only. Your saved lectures are kept."):
        reset_app()

    st.markdown("---")
    is_dark = st.session_state.theme == "dark"
    if st.button(
        "Light mode" if is_dark else "Dark mode",
        icon=":material/light_mode:" if is_dark else ":material/dark_mode:",
        use_container_width=True, key="theme_toggle",
    ):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()
    if st.session_state.processed:
        st.caption(f"{len(st.session_state.docs or [])} indexed chunks in this session")
    st.caption("Made for focused learning • VIT Pune • Group 14")

# -----------------------------------------------------------------------------
# Top bar
# -----------------------------------------------------------------------------
with st.container(key="topbar"):
    tb1, tb2, tb3 = st.columns([5, 2.4, 1.6], gap="small")
    with tb1:
        if st.session_state.processed:
            cur = current_lecture()
            label = f"Lecture ready: {cur['title']}" if cur else "Lecture ready"
            st.markdown(f'<span class="status-pill ok"><span class="dot"></span>{esc(label)}</span>', unsafe_allow_html=True)
        else:
            st.markdown('<span class="status-pill idle"><span class="dot"></span>No lecture loaded</span>', unsafe_allow_html=True)
    with tb2:
        st.markdown('<span class="engine-chip">⚙ Hybrid retrieval: Dense + BM25</span>', unsafe_allow_html=True)
    with tb3:
        st.button("Upload Lecture", icon=":material/upload:", key="top_upload", type="primary",
                  use_container_width=True, on_click=set_page, args=("Dashboard",))

# -----------------------------------------------------------------------------
# Processing function
# -----------------------------------------------------------------------------
def process_uploaded_file(source):
    """source is either a Streamlit UploadedFile or a YouTube URL string.
    Nothing is saved or shown as ready unless every stage succeeds."""
    is_url = isinstance(source, str)
    ok, problem = validate_youtube_url(source) if is_url else validate_upload(source)
    if not ok:
        st.error(problem)
        return

    tmp_path = None
    audio_path = None
    vector_store = None
    lecture_id = None
    stage = "starting"
    try:
        if not is_url:
            ext = "." + source.name.rsplit(".", 1)[-1].lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
                tmp.write(source.getvalue())
                tmp_path = tmp.name

        with st.status("Building your study workspace...", expanded=True) as status:
            try:
                stage = "audio extraction"
                st.write("🎵 Extracting audio")
                from utils.audio_processor import get_audio_path
                audio_path = get_audio_path(source if is_url else tmp_path)
                if not audio_path or not os.path.exists(audio_path):
                    raise RuntimeError("No audio could be extracted from this source.")

                stage = "transcription"
                st.write("📝 Transcribing lecture")
                from utils.transcriber import transcribe_with_timestamps, save_transcript
                segments = transcribe_with_timestamps(audio_path)
                if not segments:
                    raise RuntimeError("The transcription came back empty. The recording may be silent or unreadable.")
                transcript_path = save_transcript(segments, audio_path)

                # Release transcription memory before the embedding model loads.
                del segments
                gc.collect()
                try:
                    import torch
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                except Exception:
                    pass

                stage = "chunking"
                st.write("✂️ Chunking transcript")
                from core.chunker import chunk_from_file
                docs = chunk_from_file(transcript_path, method="semantic")
                if not docs:
                    raise RuntimeError("No text chunks could be created from the transcript.")

                stage = "indexing"
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

                stage = "RAG engine setup"
                st.write("🤖 Initializing RAG engine")
                from core.rag_engine import RAGEngine
                rag = RAGEngine(dense_retriever, bm25_retriever)

                # Load the CrossEncoder reranker here, while the progress panel is
                # still showing, instead of paying its load time on the first
                # question a student asks in chat.
                st.write("🎯 Warming up reranker")
                import core.reranker  # noqa: F401 — import triggers model load

                # The lecture is only registered (saved to the library) once
                # everything above has succeeded.
                stage = "saving to your library"
                lecture_title = os.path.splitext(os.path.basename(audio_path))[0]
                lecture_id = register_lecture(
                    title=lecture_title,
                    collection_name=collection_name,
                    num_chunks=len(docs),
                    transcript_path=transcript_path,
                )
            except Exception:
                status.update(label="Processing failed", state="error", expanded=True)
                raise

            # Success: only now is the session state updated.
            st.session_state.docs = docs
            st.session_state.rag = rag
            st.session_state.transcript_path = transcript_path
            st.session_state.current_lecture_id = lecture_id
            # Summary generation is left for the first time the Summary tab is
            # opened (see render_summary_tab) so "Workspace ready" doesn't wait
            # on an LLM call the student may not need immediately.
            st.session_state.summary = None
            st.session_state.summary_error = None
            st.session_state.quiz = None
            st.session_state.quiz_submitted = False
            st.session_state.chat_history = []
            st.session_state.eval_scores = None
            st.session_state.processed = True
            status.update(label="Workspace ready", state="complete", expanded=False)

        st.session_state.page = "Workspace"
        # st.success() right before st.rerun() is never visible; the toast is
        # shown on the next run instead (see render_workspace).
        st.session_state.just_processed = True
        st.rerun()
    except Exception as e:
        if lecture_id is None and vector_store is not None:
            # Best effort: don't leave an unregistered index behind.
            try:
                vector_store.delete_collection()
            except Exception:
                pass
        st.error(f"Processing failed during {stage}. {friendly_error(e)}")
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
# Shared lecture card
# -----------------------------------------------------------------------------
def open_lecture_or_workspace(lecture, is_current):
    if is_current and st.session_state.processed:
        set_page("Workspace")
        st.rerun()
    else:
        open_lecture(lecture)


def lecture_card_top(lecture, idx, is_current):
    active = '<span class="lec-active">Active</span>' if is_current and st.session_state.processed else ""
    return (
        f'<div class="lec-banner grad{idx % 4}"><span class="lec-badge">Lecture</span>{active}📚</div>'
        f'<div class="lec-meta">🧩 {esc(lecture.get("num_chunks", 0))} chunks</div>'
        f'<div class="lec-title">{esc(lecture.get("title", "Untitled lecture"))}</div>'
    )


# -----------------------------------------------------------------------------
# Dashboard
# -----------------------------------------------------------------------------
def render_dashboard_hero():
    with st.container(key="hero_card"):
        st.markdown(
            f'''<div class="hero-content">
                <span class="hero-pill">✨ {esc(datetime.now().strftime("%A, %b %d, %Y"))}</span>
                <div class="hero-title">Welcome back, Scholar! 🚀</div>
                <p class="hero-copy">Your AI study companion is ready. Upload a new recording or YouTube link to instantly generate smart summaries, interactive quizzes, and RAG knowledge chunks.</p>
            </div>''',
            unsafe_allow_html=True,
        )
        b1, b2, _ = st.columns([1.2, 1.4, 3])
        with b1:
            with st.container(key="hero_continue"):
                st.button("▶  Continue Studying", key="hero_continue_btn", use_container_width=True,
                          disabled=not st.session_state.processed, on_click=set_page, args=("Workspace",))
        with b2:
            with st.container(key="hero_upload"):
                if st.button("＋  Upload New Lecture", key="hero_upload_btn", use_container_width=True):
                    start_new_lecture()
                    st.rerun()


def render_ingestion_center():
    with st.container(border=True):
        st.markdown(
            '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;margin-bottom:14px">'
            '<div><div class="sec-title">Quick Ingestion Center</div>'
            '<div class="sec-sub">Drop your lecture audio/video files or paste a YouTube URL below</div></div>'
            '<div><span class="chip">MP3</span><span class="chip">WAV</span><span class="chip">MP4</span>'
            '<span class="chip">M4A</span><span class="chip">MKV</span><span class="chip">AVI</span><span class="chip">YouTube</span></div></div>',
            unsafe_allow_html=True,
        )
        left, right = st.columns(2, gap="medium")
        with left:
            uploaded = st.file_uploader(
                "Choose a lecture file",
                type=ALLOWED_EXTENSIONS,
                label_visibility="collapsed",
                key="dashboard_upload",
            )
            if uploaded:
                file_ok, file_msg = validate_upload(uploaded)
                if not file_ok:
                    st.warning(file_msg)
                if st.button("Process Lecture  →", type="primary", use_container_width=True,
                             key="process_dashboard", disabled=not file_ok):
                    process_uploaded_file(uploaded)
        with right:
            with st.container(key="yt_box"):
                st.markdown(
                    '<div class="yt-head"><span class="yt-icon">▶</span>Use YouTube URL</div>'
                    '<div class="sec-sub" style="margin-bottom:10px">Paste a link to a single lecture video to index it.</div>',
                    unsafe_allow_html=True,
                )
                yt_url = st.text_input(
                    "YouTube URL",
                    placeholder="https://www.youtube.com/watch?v=...",
                    label_visibility="collapsed",
                    key="dashboard_youtube_url",
                )
                if yt_url.strip():
                    yt_ok, yt_msg = validate_youtube_url(yt_url)
                    if not yt_ok:
                        st.warning(yt_msg)
                    if st.button("Process Lecture  →", type="primary", use_container_width=True,
                                 key="process_youtube", disabled=not yt_ok):
                        process_uploaded_file(yt_url.strip())


def render_dashboard_stats():
    ready = st.session_state.processed
    n_chunks = len(st.session_state.docs or [])
    n_questions = len([m for m in st.session_state.chat_history if m["role"] == "user"])
    n_quiz = len(valid_quiz_items(st.session_state.quiz))
    cards = [
        ("Lecture Status", "Ready" if ready else "No Lecture Loaded", "Active session loaded" if ready else "Upload or reopen a lecture", "emerald", "✅"),
        ("Indexed Chunks", f"{n_chunks} Chunks", "Vector embeddings active" if ready else "Nothing indexed yet", "blue", "🧩"),
        ("Questions Asked", f"{n_questions} Queries", "AI chat session stats", "indigo", "💬"),
        ("Quiz Questions", f"{n_quiz} Generated", "Ready for practice" if n_quiz else "No quiz generated yet", "amber", "🏅"),
    ]
    cols = st.columns(4, gap="medium")
    for col, (label, value, note, tone, icon) in zip(cols, cards):
        value_color = f"var(--{tone}-ink)" if (ready or tone != "emerald") else "var(--muted)"
        with col:
            st.markdown(
                f'<div class="card stat-card"><div><div class="stat-label">{esc(label)}</div>'
                f'<div class="stat-value" style="color:{value_color}">{esc(value)}</div>'
                f'<div class="stat-note">{esc(note)}</div></div>'
                f'<div class="stat-icon t-{tone}">{icon}</div></div>',
                unsafe_allow_html=True,
            )


def render_dashboard_tools():
    st.markdown(
        '<div style="display:flex;justify-content:space-between;align-items:baseline;margin-bottom:14px">'
        '<div class="sec-title">Interactive Study Tools</div>'
        '<div class="sec-sub">Based on your active lecture</div></div>',
        unsafe_allow_html=True,
    )
    ready = st.session_state.processed
    tools = [
        ("🤖", "blue", "#2563eb", "AI Lecture Chat", "Ask questions and get answers with the lecture chunks they came from.", WORKSPACE_TABS[0]),
        ("📄", "indigo", "#4f46e5", "Smart Study Summary", "Review structured revision notes and download them.", WORKSPACE_TABS[1]),
        ("❓", "amber", "#d97706", "Practice Quiz", "Generate multiple-choice questions and check your score.", WORKSPACE_TABS[2]),
        ("📊", "emerald", "#059669", "RAG Evaluation", "Measure answer quality with your own test questions.", WORKSPACE_TABS[3]),
    ]
    cols = st.columns(4, gap="medium")
    for i, (icon, tone, hov, title, copy, tab) in enumerate(tools):
        with cols[i]:
            with st.container(key=f"tool_{i}"):
                st.markdown(
                    f'<div class="tool-icon t-{tone}" style="--hov:{hov}">{icon}</div>'
                    f'<div class="tool-title">{esc(title)}</div><div class="tool-copy">{esc(copy)}</div>',
                    unsafe_allow_html=True,
                )
                st.button("Open  →", key=f"tool_btn_{i}", use_container_width=True, disabled=not ready,
                          on_click=go_to_tool, args=(tab,),
                          help=None if ready else "Process or open a lecture first")
    if not ready:
        st.caption("The study tools unlock once a lecture is processed or reopened from your library.")


def render_dashboard_lectures():
    hl, hr = st.columns([4, 1.2])
    with hl:
        st.markdown('<div class="sec-title">Recent Lectures</div><div class="sec-sub">Reopen a lecture to keep studying.</div>', unsafe_allow_html=True)
    with hr:
        if LECTURES:
            st.button("View All Library  →", key="dash_view_all", use_container_width=True,
                      on_click=set_page, args=("My Lectures",))
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    if not LECTURES:
        st.markdown(
            '<div class="card" style="text-align:center;padding:34px 20px">'
            '<div style="font-size:38px">📭</div><div class="sec-title" style="margin-top:8px">No lectures yet</div>'
            '<div class="sec-sub">Lectures you process will appear here so you can reopen them any time.</div></div>',
            unsafe_allow_html=True,
        )
        return

    cols = st.columns(3, gap="medium")
    for idx, lecture in enumerate(LECTURES[:3]):
        is_current = lecture.get("id") == st.session_state.current_lecture_id
        with cols[idx]:
            with st.container(border=True):
                st.markdown(lecture_card_top(lecture, idx, is_current), unsafe_allow_html=True)
                f1, f2 = st.columns([1, 1.15])
                with f1:
                    st.markdown(f'<div class="lec-foot">{esc(fmt_created(lecture))}</div>', unsafe_allow_html=True)
                with f2:
                    if st.button("Open Studio  →", key=f"dash_open_{lecture['id']}", use_container_width=True):
                        open_lecture_or_workspace(lecture, is_current)


def render_dashboard():
    render_dashboard_hero()
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_ingestion_center()
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_dashboard_stats()
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_dashboard_tools()
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)
    render_dashboard_lectures()


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
    queued_prompt = None
    with st.container(key="ws_chat"):
        with st.container(key="chat_card"):
            chat_box = st.container(height=520, border=False)
            with chat_box:
                if not st.session_state.chat_history:
                    st.markdown(
                        '<div class="bot-row"><div class="bot-avatar">🤖</div><div class="bot-bubble">'
                        '<b>AI Study Assistant</b><br>Hello! I\'ve indexed your current lecture. You can ask me any question '
                        'about the concepts, definitions, or examples discussed in it.</div></div>',
                        unsafe_allow_html=True,
                    )
                for msg in st.session_state.chat_history:
                    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
                        st.markdown(msg["content"])
                        if msg["role"] == "assistant" and msg.get("sources"):
                            render_sources(msg["sources"])

            with st.container(key="chat_pills"):
                pcols = st.columns([0.8, 1.5, 1.4, 1.2, 1.7, 0.8])
                with pcols[0]:
                    st.markdown('<div class="suggest-label">Suggested:</div>', unsafe_allow_html=True)
                for i, prompt in enumerate(STUDY_PROMPTS):
                    with pcols[i + 1]:
                        if st.button(prompt, key=f"suggest_{prompt}", use_container_width=True):
                            queued_prompt = prompt
                with pcols[5]:
                    if st.button("Clear", key="clear_chat", use_container_width=True,
                                 disabled=not st.session_state.chat_history,
                                 help="Clear the conversation"):
                        st.session_state.chat_history = []
                        try:
                            st.session_state.rag.reset_memory()
                        except Exception:
                            pass
                        st.rerun()

            typed_query = st.chat_input("Ask anything about this lecture...")
            query = queued_prompt or typed_query

            if query:
                answer = None
                sources = []
                with chat_box:
                    with st.chat_message("user"):
                        st.markdown(query)
                    with st.chat_message("assistant"):
                        try:
                            with st.spinner("Retrieving lecture context..."):
                                token_gen, sources, save_fn = st.session_state.rag.prepare_stream(query)
                            answer = st.write_stream(token_gen)
                            if not answer or not str(answer).strip():
                                raise RuntimeError("The model returned an empty answer.")
                            save_fn(answer)
                            render_sources(sources)
                        except Exception as e:
                            answer = None
                            st.error(f"Couldn't answer that question. {friendly_error(e)}")
                # Only successful answers are added to the conversation.
                if answer is not None:
                    st.session_state.chat_history.append({"role": "user", "content": query})
                    st.session_state.chat_history.append({"role": "assistant", "content": answer, "sources": sources})
                    st.rerun()


def render_summary_tab():
    with st.container(key="ws_notes"):
        if st.session_state.summary is None and st.session_state.summary_error is None:
            try:
                with st.spinner("Generating study summary..."):
                    from features.summarizer import summarize
                    result = summarize(st.session_state.docs)
                if result and str(result).strip():
                    st.session_state.summary = result
                else:
                    st.session_state.summary_error = "The summarizer returned an empty summary."
            except Exception as e:
                st.session_state.summary_error = friendly_error(e)

        summary = st.session_state.summary
        with st.container(border=True):
            h1, h2, h3 = st.columns([3, 1.1, 1.1])
            with h1:
                st.markdown('<div class="sec-title">Structured Revision Notes</div><div class="sec-sub">Generated from your lecture, with markdown formatting</div>', unsafe_allow_html=True)
            if summary:
                with h2:
                    st.download_button("Download .txt", data=summary, file_name="lecture_summary.txt",
                                       mime="text/plain", use_container_width=True)
                with h3:
                    st.download_button("Download .md", data=summary, file_name="lecture_summary.md",
                                       mime="text/markdown", use_container_width=True, type="primary")
        st.markdown('<div style="height:6px"></div>', unsafe_allow_html=True)
        if summary:
            # Keyed container so the card actually wraps the summary content
            # (separate st.markdown calls can't open/close one HTML div).
            with st.container(key="summary_card"):
                st.markdown('<div class="eyebrow">YOUR REVISION NOTES</div>', unsafe_allow_html=True)
                st.markdown(summary)
        else:
            st.error(f"Couldn't generate the summary. {st.session_state.summary_error or ''}")
            if st.button("Try again", key="summary_retry", type="primary"):
                st.session_state.summary_error = None
                st.rerun()


def render_quiz_tab():
    with st.container(key="ws_quiz"):
        with st.container(border=True):
            q1, q2, q3 = st.columns([2.2, 1.7, 1.3])
            with q1:
                st.markdown('<div class="sec-title">Interactive Practice Quiz</div><div class="sec-sub">Questions are generated from your lecture</div>', unsafe_allow_html=True)
            with q2:
                num_q = st.slider("Number of questions", 3, 10, 5)
            with q3:
                st.markdown('<div style="height:26px"></div>', unsafe_allow_html=True)
                generate = st.button("Regenerate Quiz" if st.session_state.quiz else "Generate Quiz",
                                     use_container_width=True, type="primary")
        if generate:
            new_quiz = None
            try:
                with st.spinner("Generating questions..."):
                    from features.quiz_generator import generate_quiz
                    new_quiz = generate_quiz(st.session_state.docs, num_questions=num_q)
            except Exception as e:
                st.error(f"Couldn't generate the quiz. {friendly_error(e)}")
            if new_quiz is not None:
                if not valid_quiz_items(new_quiz):
                    st.error("The model didn't return any usable questions. Please try again.")
                else:
                    st.session_state.quiz = new_quiz
                    # Clear old answers so a new quiz doesn't inherit stale radio selections
                    for key in [k for k in st.session_state.keys() if k.startswith("quiz_pick_")]:
                        del st.session_state[key]
                    st.session_state.quiz_submitted = False
                    st.rerun()

        quiz = st.session_state.quiz
        if not quiz:
            st.caption("Choose how many questions you want and press Generate Quiz.")
            return

        valid_quiz = valid_quiz_items(quiz)
        if len(valid_quiz) < len(quiz):
            st.warning(f"Skipped {len(quiz) - len(valid_quiz)} malformed question(s).")
        if not valid_quiz:
            return

        with st.container(key="quiz_wrap"):
            with st.form("quiz_form", border=False):
                picks = {}
                for i, q in enumerate(valid_quiz):
                    st.markdown(
                        f'<div class="card" style="margin:12px 0 6px"><div class="eyebrow">QUESTION {i+1}</div>'
                        f'<div style="font-size:18px;font-weight:700;margin-top:8px;color:var(--ink)">{esc(q["question"])}</div></div>',
                        unsafe_allow_html=True,
                    )
                    options = q["options"]
                    picks[i] = st.radio(
                        f"q_{i}", list(options.keys()),
                        format_func=lambda k, opts=options: f"{k}. {opts[k]}",
                        index=None,  # nothing preselected, so unanswered != "A"
                        key=f"quiz_pick_{i}", label_visibility="collapsed",
                    )
                submitted = st.form_submit_button("Submit & Calculate Score  →", type="primary")

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
                f'<div class="metric-ring" style="max-width:260px;margin:8px 0 16px">'
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

    saved = st.session_state.eval_scores
    scores = saved["scores"] if saved and isinstance(saved.get("scores"), dict) else {}
    n_items = saved["n"] if saved else None

    with st.container(key="ws_eval"):
        with st.container(border=True):
            st.markdown(
                '<div class="sec-title">RAG Evaluation &amp; Vector Index Health</div>'
                '<div class="sec-sub" style="margin-bottom:16px">'
                + (f"Calculated from {n_items} test question(s) in your latest run." if saved
                   else "Not evaluated yet. Add test questions with expected answers below and run an evaluation.")
                + '</div>',
                unsafe_allow_html=True,
            )
            tiles = [
                ("Faithfulness", "faithfulness", "emerald", "Answers grounded in retrieved context"),
                ("Answer Relevancy", "answer_relevancy", "blue", "Alignment with the question"),
                ("Context Precision", "context_precision", "indigo", "Quality of top-ranked chunks"),
                ("Context Recall", "context_recall", "amber", "Coverage of needed information"),
            ]
            for col, (name, key, tone, note) in zip(st.columns(4, gap="small"), tiles):
                value = metric_value(scores.get(key)) if saved else None
                if saved:
                    shown, color, sub = (value, f"var(--{tone}-ink)", note) if value else ("N/A", "var(--soft)", "Not returned by the evaluator")
                else:
                    shown, color, sub = "—", "var(--soft)", "Not evaluated yet"
                with col:
                    st.markdown(
                        f'<div class="m-tile"><div class="m-label">{esc(name)}</div>'
                        f'<div class="m-value" style="color:{color}">{esc(shown)}</div><div class="m-note">{esc(sub)}</div></div>',
                        unsafe_allow_html=True,
                    )

            st.markdown('<div style="height:18px"></div><div class="sec-title" style="font-size:15px">Test Set Query Editor</div>'
                        '<p class="sec-sub" style="margin-bottom:8px">Each row needs both a question and its expected answer. Incomplete rows are ignored.</p>',
                        unsafe_allow_html=True)
            with st.form("eval_form", border=False):
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
                run_eval = st.form_submit_button("Run Evaluation  →", use_container_width=True, type="primary")

        if run_eval:
            test_qa, incomplete = [], 0
            for _, row in edited.iterrows():
                q = str(row.get("question") or "").strip()
                a = str(row.get("ground_truth") or "").strip()
                if q and a:
                    test_qa.append({"question": q, "ground_truth": a})
                elif q or a:
                    incomplete += 1
            if incomplete:
                st.warning(f"{incomplete} incomplete row(s) were ignored (both a question and an expected answer are needed).")
            if not test_qa:
                st.warning("Please add at least one question and expected answer.")
            else:
                new_scores = None
                try:
                    with st.spinner("Running RAGAS evaluation..."):
                        from features.evaluator import quick_evaluate
                        new_scores = quick_evaluate(st.session_state.rag, test_qa)
                except Exception as e:
                    st.error(f"Evaluation failed. {friendly_error(e)}")
                if new_scores is not None:
                    if isinstance(new_scores, dict) and new_scores:
                        st.session_state.eval_scores = {"scores": new_scores, "n": len(test_qa)}
                        st.rerun()
                    else:
                        st.error("The evaluator didn't return any metrics.")

        st.markdown('<div style="height:10px"></div><div class="sec-title">Vector index health</div>'
                    '<div class="sec-sub" style="margin-bottom:10px">Pipeline information available from the current app session.</div>',
                    unsafe_allow_html=True)
        for col, label, value in zip(
            st.columns(3, gap="small"),
            ["Indexed chunks", "Retriever", "Evaluation items"],
            [len(st.session_state.docs or []), "Dense + BM25", n_items if n_items is not None else "—"],
        ):
            with col:
                st.markdown(f'<div class="card"><div class="stat-label">{esc(label)}</div><div class="stat-value" style="font-size:22px">{esc(value)}</div></div>', unsafe_allow_html=True)


def render_workspace():
    if not require_processed():
        return
    if st.session_state.get("just_processed"):
        st.session_state.just_processed = False
        st.toast("Your lecture is ready to study.", icon="✅")

    cur = current_lecture()
    title = cur["title"] if cur else "Your Study Workspace"
    sub = f"{len(st.session_state.docs or [])} chunks indexed" + (f" • processed {fmt_created(cur)}" if cur and fmt_created(cur) else "")

    # Section switcher (replaces st.tabs so the Dashboard's tool cards can open a
    # specific section, and only the active section runs on each rerun).
    if st.session_state.ws_tab not in WORKSPACE_TABS:
        st.session_state.ws_tab = WORKSPACE_TABS[0]
    with st.container(key="ws_header"):
        hl, hr = st.columns([1.1, 1.5])
        with hl:
            st.markdown(
                f'<div class="eyebrow">📖 Active lecture</div><div class="ws-title">{esc(title)}</div>'
                f'<div class="ws-sub">{esc(sub)}</div>',
                unsafe_allow_html=True,
            )
        with hr:
            choice = st.radio(
                "Workspace section", WORKSPACE_TABS,
                index=WORKSPACE_TABS.index(st.session_state.ws_tab),
                key="ws_tab_radio", horizontal=True, label_visibility="collapsed",
            )
    st.session_state.ws_tab = choice

    if choice == WORKSPACE_TABS[0]:
        render_chat_tab()
    elif choice == WORKSPACE_TABS[1]:
        render_summary_tab()
    elif choice == WORKSPACE_TABS[2]:
        render_quiz_tab()
    else:
        render_evaluation_tab()


def open_lecture(lecture: dict):
    """Reopen a previously processed lecture without re-running the pipeline —
    loads its existing Chroma collection and rebuilds BM25 from the same
    chunks (BM25's retriever only lives in memory, so it can't be persisted
    the way the vector store can)."""
    title = lecture.get("title", "this lecture")
    try:
        from core.vector_store import load_vector_store, get_all_docs_from_store, get_dense_retriever
        from core.bm25_index import build_bm25_retriever
        from core.rag_engine import RAGEngine

        with st.spinner(f"Opening “{title}”..."):
            vector_store = load_vector_store(lecture["collection_name"])
            docs = get_all_docs_from_store(vector_store)
            if not docs:
                raise RuntimeError("The saved index for this lecture is empty or missing.")
            dense_retriever = get_dense_retriever(vector_store, k=10)
            bm25_retriever = build_bm25_retriever(docs, k=10)
            rag = RAGEngine(dense_retriever, bm25_retriever)
    except Exception as e:
        st.error(f"Couldn't open “{title}”. {friendly_error(e)} The saved index may be missing or corrupted; "
                 "you can delete this lecture and process it again.")
        return

    st.session_state.docs = docs
    st.session_state.rag = rag
    st.session_state.transcript_path = lecture.get("transcript_path")
    st.session_state.current_lecture_id = lecture["id"]
    st.session_state.summary = None
    st.session_state.summary_error = None
    st.session_state.quiz = None
    st.session_state.quiz_submitted = False
    st.session_state.chat_history = []
    st.session_state.eval_scores = None
    st.session_state.processed = True

    set_page("Workspace")
    st.rerun()


# -----------------------------------------------------------------------------
# My Lectures: filters + rename
# -----------------------------------------------------------------------------
DATE_PRESETS = ["Any time", "Today", "Last 7 days", "Last 30 days", "Custom range"]
SORT_OPTIONS = ["Newest first", "Oldest first", "Title A → Z", "Title Z → A", "Most chunks", "Fewest chunks"]


def _reset_library_filters():
    st.session_state.lib_search = ""
    st.session_state.lib_preset = DATE_PRESETS[0]
    st.session_state.lib_time = (dtime(0, 0), dtime(23, 59))
    st.session_state.lib_sort = SORT_OPTIONS[0]
    st.session_state.pop("lib_chunks", None)
    st.session_state.pop("lib_dates", None)


def filter_lectures(lectures):
    """Renders the filter panel and returns (filtered_and_sorted_list, filters_active)."""
    max_chunks = max([int(l.get("num_chunks", 0) or 0) for l in lectures] + [1])
    parsed = [parse_created(l) for l in lectures]
    known = [p for p in parsed if p]

    with st.container(border=True):
        r1 = st.columns([2.4, 1.3, 1.3], gap="small")
        with r1[0]:
            query = st.text_input("Search", placeholder="🔍  Search lectures by title...",
                                  label_visibility="collapsed", key="lib_search").strip().lower()
        with r1[1]:
            preset = st.selectbox("Date", DATE_PRESETS, key="lib_preset", label_visibility="collapsed")
        with r1[2]:
            sort_by = st.selectbox("Sort", SORT_OPTIONS, key="lib_sort", label_visibility="collapsed")

        r2 = st.columns([1.5, 1.5, 1], gap="medium")
        date_from = date_to = None
        with r2[0]:
            if preset == "Custom range":
                lo = min(p.date() for p in known) if known else datetime.now().date()
                hi = max(p.date() for p in known) if known else datetime.now().date()
                picked = st.date_input("Date range", value=(lo, hi), key="lib_dates")
                if isinstance(picked, (tuple, list)):
                    if len(picked) == 2:
                        date_from, date_to = picked
                    elif len(picked) == 1:
                        date_from = date_to = picked[0]
                else:
                    date_from = date_to = picked
            else:
                st.caption("Date: " + preset)
        with r2[1]:
            t_from, t_to = st.slider("Time of day", value=(dtime(0, 0), dtime(23, 59)),
                                     format="HH:mm", key="lib_time")
        with r2[2]:
            if max_chunks > 1:
                c_min, c_max = st.slider("Chunks", 0, max_chunks, (0, max_chunks), key="lib_chunks")
            else:
                c_min, c_max = 0, max_chunks
        st.button("Reset filters", key="lib_reset", on_click=_reset_library_filters)

    today = datetime.now().date()
    if preset == "Today":
        date_from, date_to = today, today
    elif preset == "Last 7 days":
        date_from, date_to = today - timedelta(days=6), today
    elif preset == "Last 30 days":
        date_from, date_to = today - timedelta(days=29), today

    time_active = (t_from, t_to) != (dtime(0, 0), dtime(23, 59))
    chunks_active = (c_min, c_max) != (0, max_chunks)
    active = bool(query) or preset != DATE_PRESETS[0] or time_active or chunks_active

    result = []
    for lec, created in zip(lectures, parsed):
        if query and query not in str(lec.get("title", "")).lower():
            continue
        n = int(lec.get("num_chunks", 0) or 0)
        if not (c_min <= n <= c_max):
            continue
        if date_from or time_active:
            if created is None:
                continue
            if date_from and not (date_from <= created.date() <= (date_to or date_from)):
                continue
            if time_active and not (t_from <= created.time().replace(second=0, microsecond=0) <= t_to):
                continue
        result.append((lec, created))

    far_past = datetime.min
    keyfuncs = {
        "Newest first": (lambda x: x[1] or far_past, True),
        "Oldest first": (lambda x: x[1] or far_past, False),
        "Title A → Z": (lambda x: str(x[0].get("title", "")).lower(), False),
        "Title Z → A": (lambda x: str(x[0].get("title", "")).lower(), True),
        "Most chunks": (lambda x: int(x[0].get("num_chunks", 0) or 0), True),
        "Fewest chunks": (lambda x: int(x[0].get("num_chunks", 0) or 0), False),
    }
    fn, rev = keyfuncs[sort_by]
    result.sort(key=fn, reverse=rev)
    return [lec for lec, _ in result], active


def render_my_lectures():
    from core.vector_store import delete_lecture

    hl, hr = st.columns([3, 1.1])
    with hl:
        st.markdown('<div class="page-title">My Lectures Library</div>'
                    '<div class="page-sub">All your processed class recordings in one place. Reopen a lecture whenever you want to revise.</div>',
                    unsafe_allow_html=True)
    with hr:
        if st.button("＋  Add New Lecture", key="library_add", type="primary", use_container_width=True):
            start_new_lecture()
            st.rerun()
    st.markdown('<div style="height:12px"></div>', unsafe_allow_html=True)

    if not LECTURES:
        st.markdown(
            '<div class="card" style="text-align:center;padding:38px 24px">'
            '<div style="font-size:44px">📭</div>'
            '<div class="sec-title" style="margin-top:8px">Your library is empty for now</div>'
            '<div class="sec-sub">Add a lecture from the Dashboard to start building your revision library.</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Go to Dashboard  →", key="library_empty_dashboard", type="primary"):
            set_page("Dashboard")
            st.rerun()
        return

    shown, filters_active = filter_lectures(LECTURES)
    st.caption(f"Showing {len(shown)} of {len(LECTURES)} lecture(s)" + (" • filters applied" if filters_active else ""))
    if not shown:
        st.info("No lectures match your filters.")
        return

    grid = st.columns(3, gap="medium")
    for idx, lecture in enumerate(shown):
        lid = lecture["id"]
        is_current = lid == st.session_state.current_lecture_id
        with grid[idx % 3]:
            with st.container(border=True):
                st.markdown(
                    lecture_card_top(lecture, idx, is_current)
                    + f'<div class="lec-foot">Processed {esc(fmt_created(lecture))}</div>',
                    unsafe_allow_html=True,
                )
                c1, c2, c3 = st.columns([1.5, 1, 1])
                with c1:
                    if st.button("Open →", key=f"open_{lid}", use_container_width=True):
                        open_lecture_or_workspace(lecture, is_current)
                with c2:
                    with st.popover("Rename", use_container_width=True):
                        new_title = st.text_input("New name", value=str(lecture.get("title", "")),
                                                  key=f"rename_input_{lid}", max_chars=120)
                        if st.button("Save name", key=f"rename_save_{lid}", type="primary",
                                     use_container_width=True):
                            cleaned = " ".join(new_title.split())
                            if not cleaned:
                                st.error("The name can't be empty.")
                            else:
                                try:
                                    save_title_override(lid, cleaned)
                                except Exception as e:
                                    st.error(f"Couldn't rename this lecture. {friendly_error(e)}")
                                else:
                                    st.rerun()
                with c3:
                    # Deleting is permanent, so ask for confirmation first
                    with st.popover("Delete", use_container_width=True):
                        st.caption("This permanently removes the lecture and its index.")
                        if st.button("Yes, delete", key=f"confirm_delete_{lid}",
                                     type="primary", use_container_width=True):
                            try:
                                delete_lecture(lid)
                            except Exception as e:
                                st.error(f"Couldn't delete this lecture. {friendly_error(e)}")
                            else:
                                remove_title_override(lid)
                                if is_current:
                                    start_new_lecture()
                                    st.session_state.page = "My Lectures"
                                st.rerun()


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
page = st.session_state.page
with st.container(key="page_body"):
    if page == "Dashboard":
        render_dashboard()
    elif page in WORKSPACE_PAGES:
        render_workspace()
    elif page == "My Lectures":
        render_my_lectures()
    else:
        render_dashboard()