import os
import tempfile
import html
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
# Academic Editorial Modern — Stitch-inspired theme
# -----------------------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:opsz,wght@6..72,400;6..72,500;6..72,600&family=Plus+Jakarta+Sans:wght@500;600;700&display=swap');

    :root {
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
        --sage: #caead7;
        --sage-2: #a6cfc1;
        --amber: #fae191;
        --amber-ink: #4d3e00;
        --coral: #e8895b;
    }

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: var(--ivory); color: var(--ink); }
    .main .block-container { max-width: 1480px; padding: 5.5rem 2.5rem 3rem; }

    /* Hide Streamlit chrome */
    #MainMenu, footer { visibility: hidden; }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stToolbar"] { visibility: hidden; }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #f5f4ee;
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
        background: #e9e8e2;
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

    /* Top bar */
    .topbar {
        position: fixed; top: 0; left: 0; right: 0; height: 58px; z-index: 99;
        background: rgba(250,249,243,.92); backdrop-filter: blur(12px);
        border-bottom: 1px solid rgba(192,200,196,.42);
        display: flex; align-items: center; justify-content: space-between;
        padding: 0 2.5rem;
    }
    .brand { display:flex; align-items:center; gap:10px; font-family:'Plus Jakarta Sans'; font-weight:700; }
    .brand-mark { width:30px; height:30px; border-radius:9px; background:var(--forest); color:#fff; display:grid; place-items:center; font-size:15px; }
    .brand-name { letter-spacing:-.02em; }
    .top-meta { display:flex; gap:8px; align-items:center; color:var(--muted); font-size:12px; }
    .status-pill { padding:6px 10px; border:1px solid var(--line); border-radius:999px; background:#fff; }

    /* Typography */
    .display { font-family:'Newsreader', serif; font-size:44px; line-height:1.08; font-weight:500; letter-spacing:-.025em; color:var(--ink); }
    .display-small { font-family:'Newsreader', serif; font-size:30px; line-height:1.15; font-weight:500; letter-spacing:-.015em; }
    .subtitle { color:var(--muted); font-size:14px; line-height:1.65; max-width:720px; }
    .eyebrow { color:var(--forest); text-transform:uppercase; letter-spacing:.11em; font-size:10px; font-weight:700; }

    /* Cards */
    .card {
        background:var(--paper); border:1px solid var(--line); border-radius:16px;
        padding:20px; box-shadow:none;
    }
    .card:hover { border-color: #b9cec3; }
    .stat-card { min-height:116px; }
    .stat-label { font-size:11px; text-transform:uppercase; letter-spacing:.07em; color:var(--soft); font-weight:700; }
    .stat-value { font-family:'Newsreader'; font-size:32px; line-height:1.1; margin-top:10px; }
    .stat-note { font-size:11px; color:var(--muted); margin-top:5px; }

    .lecture-card { min-height:185px; position:relative; overflow:hidden; }
    .lecture-icon { width:44px; height:44px; border-radius:12px; background:#caead7; display:grid; place-items:center; font-size:21px; }
    .lecture-title { font-family:'Plus Jakarta Sans'; font-weight:700; font-size:15px; margin-top:16px; }
    .lecture-meta { color:var(--soft); font-size:12px; margin-top:6px; }
    .progress-track { height:6px; background:#e9e8e2; border-radius:999px; overflow:hidden; margin-top:15px; }
    .progress-fill { height:100%; background:var(--forest); border-radius:999px; }

    /* Upload */
    .upload-shell { background:#fff; border:1px dashed #bfc8c2; border-radius:18px; padding:42px 28px; text-align:center; }
    .upload-symbol { width:58px; height:58px; margin:0 auto 15px; border-radius:16px; background:#caead7; display:grid; place-items:center; font-size:26px; }
    .upload-title { font-family:'Newsreader'; font-size:28px; }
    .upload-copy { color:var(--muted); font-size:13px; margin:6px auto 18px; }
    .format-row { display:flex; justify-content:center; gap:7px; flex-wrap:wrap; }
    .format-chip { border:1px solid var(--line); background:#faf9f3; border-radius:999px; padding:5px 9px; font-size:10px; color:var(--muted); }

    /* Section header */
    .section-head { display:flex; align-items:end; justify-content:space-between; gap:20px; margin:30px 0 14px; }
    .section-head h2 { font-family:'Newsreader'; font-size:26px; font-weight:500; margin:0; }
    .section-head p { color:var(--muted); font-size:12px; margin:4px 0 0; }

    /* Workspace navigation */
    .workspace-nav { display:flex; gap:4px; border-bottom:1px solid var(--line); margin:12px 0 24px; }
    .workspace-note { font-size:12px; color:var(--muted); padding:9px 2px 11px; }

    /* Chat */
    .chat-bubble { padding:14px 16px; border:1px solid var(--line); border-radius:14px; margin:10px 0; line-height:1.65; font-size:14px; }
    .chat-user { background:#f1eee3; margin-left:10%; }
    .chat-ai { background:#fff; margin-right:10%; }
    .source-chip { display:inline-block; margin-top:8px; margin-right:5px; padding:4px 8px; border-radius:999px; background:#fae191; color:#4d3e00; font-size:10px; }
    .suggestion { border:1px solid var(--line); border-radius:10px; padding:9px 11px; color:var(--muted); background:#fff; font-size:12px; }

    /* Study note */
    .note { border-left:4px solid var(--forest); background:#fff; border-radius:0 14px 14px 0; border-top:1px solid var(--line); border-right:1px solid var(--line); border-bottom:1px solid var(--line); padding:18px 20px; margin:12px 0; }
    .note h4 { font-family:'Plus Jakarta Sans'; font-size:14px; margin:0 0 7px; }
    .note p { font-family:'Newsreader'; font-size:17px; line-height:1.65; margin:0; }

    /* Metrics */
    .metric-ring { border:1px solid var(--line); border-radius:16px; padding:18px; background:#fff; text-align:center; }
    .metric-number { font-family:'Newsreader'; font-size:34px; color:var(--forest); }
    .metric-label { font-size:11px; color:var(--muted); margin-top:3px; }

    /* Streamlit widgets */
    .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] > div {
        background:#fff !important; border-color:var(--line) !important; border-radius:9px !important;
        color:var(--ink) !important;
    }
    .stSlider [data-baseweb="slider"] { color:var(--forest); }
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        border-radius:9px; border:1px solid var(--line); background:#fff; color:var(--ink);
        font-family:'Plus Jakarta Sans'; font-size:12px; min-height:38px;
    }
    .stButton > button:hover, .stDownloadButton > button:hover { border-color:#9db9ac; color:var(--forest); }
    div[data-testid="stFileUploader"] section { border:1px dashed #bfc8c2; border-radius:14px; background:#faf9f3; }
    .stProgress > div > div > div > div { background:var(--forest); }

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
        ("Recent", "◷"),
        ("Favorites", "☆"),
    ]:
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"nav_{label}"):
            set_page(label)
            st.rerun()

    st.markdown("**CURRENT LECTURE**")
    if st.session_state.processed:
        if st.button("●  Active lecture", use_container_width=True, key="current_lecture"):
            set_page("Chat")
            st.rerun()
        st.caption(f"{len(st.session_state.docs or [])} indexed chunks")
    else:
        st.caption("Upload a lecture to begin.")

    st.markdown("**STUDY**")
    for label, icon in [
        ("Chat", "◌"),
        ("Summary", "≡"),
        ("Quiz", "✓"),
        ("Evaluation", "◉"),
    ]:
        if st.button(f"{icon}  {label}", use_container_width=True, key=f"study_{label}"):
            set_page(label)
            st.rerun()

    st.markdown("---")
    if st.button("⚙  Settings & Model", use_container_width=True, key="settings"):
        st.info("Settings panel can be connected to your model/provider configuration here.")

    if st.session_state.processed:
        if st.button("↻  Reset workspace", use_container_width=True, key="reset"):
            reset_app()

    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("RAG Study Assistant • VIT Pune • Group 14")

# -----------------------------------------------------------------------------
# Processing function
# -----------------------------------------------------------------------------
def process_uploaded_file(uploaded_file):
    tmp_path = None
    audio_path = None
    try:
        suffix = "." + uploaded_file.name.split(".")[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded_file.read())
            tmp_path = tmp.name

        with st.status("Building your study workspace...", expanded=True) as status:
            st.write("🎵 Extracting audio")
            from utils.audio_processor import get_audio_path
            audio_path = get_audio_path(tmp_path)

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

            st.write("📚 Generating study summary")
            from features.summarizer import summarize
            st.session_state.summary = summarize(docs)

            st.session_state.processed = True
            status.update(label="Workspace ready", state="complete", expanded=False)

        st.session_state.page = "Chat"
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
def render_dashboard():
    st.markdown('<div class="eyebrow">YOUR LEARNING SPACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="display">Good evening 👋</div>', unsafe_allow_html=True)
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
    uploaded = st.file_uploader(
        "Choose a lecture file",
        type=["mp4", "mp3", "wav", "mkv", "avi", "m4a"],
        label_visibility="collapsed",
        key="dashboard_upload",
    )
    if uploaded and not st.session_state.processed:
        if st.button("Process lecture  →", type="primary", use_container_width=True, key="process_dashboard"):
            process_uploaded_file(uploaded)

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
    st.markdown('<div class="workspace-nav"><span class="workspace-note">Chat</span><span class="workspace-note">Summary</span><span class="workspace-note">Quiz</span><span class="workspace-note">Evaluation</span></div>', unsafe_allow_html=True)


def render_chat():
    if not require_processed():
        return
    render_workspace_header("AI Lecture Chat", "Ask questions against the indexed lecture and inspect the retrieved context.")

    left, right = st.columns([1.8, 1], gap="large")
    with left:
        if not st.session_state.chat_history:
            st.markdown('<div class="card"><div class="eyebrow">START HERE</div><div class="display-small" style="font-size:27px;margin-top:8px">What would you like to understand?</div><p class="subtitle">Try a question about the main idea, a definition, an example, or the most important takeaway.</p></div>', unsafe_allow_html=True)
        for msg in st.session_state.chat_history:
            content = esc(msg["content"]).replace("\n", "<br>")
            if msg["role"] == "user":
                st.markdown(f'<div class="chat-bubble chat-user"><strong>You</strong><br>{content}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-bubble chat-ai"><strong>Assistant</strong><br>{content}<div><span class="source-chip">RAG answer</span><span class="source-chip">Lecture context</span></div></div>', unsafe_allow_html=True)

        with st.form("chat_form", clear_on_submit=True):
            query = st.text_input("Ask your lecture", placeholder="What is the main idea of this lecture?", label_visibility="collapsed")
            submitted = st.form_submit_button("Ask assistant  →", use_container_width=True, type="primary")
        if submitted and query.strip():
            with st.spinner("Thinking from your lecture..."):
                answer = st.session_state.rag.answer(query)
            st.session_state.chat_history.append({"role": "user", "content": query})
            st.session_state.chat_history.append({"role": "assistant", "content": answer})
            st.rerun()

        if st.session_state.chat_history:
            if st.button("Clear conversation", key="clear_chat"):
                st.session_state.chat_history = []
                try:
                    st.session_state.rag.reset_memory()
                except Exception:
                    pass
                st.rerun()

    with right:
        st.markdown('<div class="card"><div class="eyebrow">SUGGESTED QUESTIONS</div><h3 style="font-family:Newsreader;font-size:24px;margin:8px 0 14px">Study prompts</h3>', unsafe_allow_html=True)
        for prompt in [
            "Explain the core concept simply.",
            "What are the key points?",
            "Give me an example.",
            "What should I remember for an exam?",
        ]:
            st.markdown(f'<div class="suggestion" style="margin:7px 0">{esc(prompt)}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        st.markdown('<div class="card" style="margin-top:14px"><div class="eyebrow">RETRIEVAL</div><h3 style="font-family:Newsreader;font-size:24px;margin:8px 0 6px">Knowledge base</h3><p style="font-size:12px;color:#5b6b64">Your lecture is indexed using the existing dense + BM25 retrieval pipeline.</p><div class="stat-note">Indexed chunks</div><div class="stat-value" style="font-size:28px">' + str(len(st.session_state.docs or [])) + '</div></div>', unsafe_allow_html=True)


def render_summary():
    if not require_processed():
        return
    render_workspace_header("Lecture Summary", "Editorial study notes generated from the processed lecture.")
    summary = st.session_state.summary
    if summary:
        st.markdown('<div class="card"><div class="eyebrow">SYNTHESIS</div><div style="font-family:Newsreader;font-size:18px;line-height:1.75;margin-top:12px">' + summary.replace("\n", "<br>") + '</div></div>', unsafe_allow_html=True)
        st.download_button("Download study notes", data=summary, file_name="lecture_summary.txt", mime="text/plain")
    else:
        st.info("No summary is available yet.")


def render_quiz():
    if not require_processed():
        return
    render_workspace_header("Practice Quiz", "Test recall with questions generated from your lecture.")
    c1, c2 = st.columns([2, 1])
    with c1:
        num_q = st.slider("Number of questions", 3, 10, 5)
    with c2:
        generate = st.button("Generate quiz  →", use_container_width=True, type="primary")
    if generate:
        with st.spinner("Generating questions..."):
            from features.quiz_generator import generate_quiz
            st.session_state.quiz = generate_quiz(st.session_state.docs, num_questions=num_q)
        st.rerun()

    if st.session_state.quiz:
        for i, q in enumerate(st.session_state.quiz):
            if not all(k in q for k in ("question", "options", "answer", "explanation")):
                st.warning(f"Skipped malformed question {i + 1}")
                continue
            st.markdown(f'<div class="card" style="margin:12px 0"><div class="eyebrow">QUESTION {i+1}</div><div class="display-small" style="font-size:25px;margin:8px 0 16px">{esc(q["question"])}</div>', unsafe_allow_html=True)
            for key, val in q["options"].items():
                st.markdown(f'<div class="suggestion" style="margin:7px 0"><strong>{esc(key)}.</strong> {esc(val)}</div>', unsafe_allow_html=True)
            st.success(f'Answer: {q["answer"]}')
            st.info(q["explanation"])
            st.markdown('</div>', unsafe_allow_html=True)


def render_evaluation():
    if not require_processed():
        return
    render_workspace_header("RAGAS Evaluation", "Measure how faithfully and precisely your RAG system answers lecture questions.")
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
        with st.spinner("Running RAGAS evaluation..."):
            from features.evaluator import quick_evaluate
            scores = quick_evaluate(st.session_state.rag, test_qa)

        cols = st.columns(4)
        metrics = [
            ("Faithfulness", scores["faithfulness"]),
            ("Answer Relevancy", scores["answer_relevancy"]),
            ("Context Precision", scores["context_precision"]),
            ("Context Recall", scores["context_recall"]),
        ]
        for col, (name, score) in zip(cols, metrics):
            with col:
                st.markdown(f'<div class="metric-ring"><div class="metric-number">{score:.3f}</div><div class="metric-label">{esc(name)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="section-head"><div><h2>Vector index health</h2><p>Pipeline information available from the current app session.</p></div></div>', unsafe_allow_html=True)
        a, b, c = st.columns(3)
        for col, label, value in [
            (a, "Indexed chunks", len(st.session_state.docs or [])),
            (b, "Retriever", "Dense + BM25"),
            (c, "Evaluation items", len(test_qa)),
        ]:
            with col:
                st.markdown(f'<div class="card"><div class="stat-label">{esc(label)}</div><div class="stat-value" style="font-size:26px">{esc(value)}</div></div>', unsafe_allow_html=True)


def render_my_lectures():
    st.markdown('<div class="eyebrow">LIBRARY</div>', unsafe_allow_html=True)
    st.markdown('<div class="display-small">My Lectures</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">This version keeps lecture state in the active Streamlit session. Persistent multi-lecture history can be added later.</div>', unsafe_allow_html=True)
    if st.session_state.processed:
        st.markdown('<div class="card" style="margin-top:24px"><div class="lecture-icon">📚</div><div class="lecture-title">Current processed lecture</div><div class="lecture-meta">Indexed and ready for chat, summary, quiz and evaluation.</div></div>', unsafe_allow_html=True)
    else:
        st.info("No lecture is loaded in this session. Start from Dashboard.")


def render_simple_page(title, copy):
    st.markdown('<div class="eyebrow">WORKSPACE</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="display-small">{esc(title)}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtitle">{esc(copy)}</div>', unsafe_allow_html=True)
    st.markdown('<div class="card" style="margin-top:24px"><div class="display-small" style="font-size:25px">Coming next</div><p class="subtitle">This navigation item is ready in the new visual system. Its persistence/model settings can be connected without changing the RAG engine.</p></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Router
# -----------------------------------------------------------------------------
page = st.session_state.page
if page == "Dashboard":
    render_dashboard()
elif page == "Chat":
    render_chat()
elif page == "Summary":
    render_summary()
elif page == "Quiz":
    render_quiz()
elif page == "Evaluation":
    render_evaluation()
elif page == "My Lectures":
    render_my_lectures()
elif page in ("Recent", "Favorites", "Settings & Model"):
    render_simple_page(page, "A dedicated workspace area for your study workflow.")
else:
    render_dashboard()
