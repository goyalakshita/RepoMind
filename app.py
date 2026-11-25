
import streamlit as st
import os
import json
import tempfile
from pathlib import Path

from core.rag_pipeline import RAGPipeline
from core.repository_history import RepositoryHistory
from core.repository_loader import (
    clone_github_repository,
    extract_zip_file,
    load_local_repository
)


# ==================================================
# PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="RepoMind | AI Repository Assistant",
    page_icon="🧠",
    layout="wide"
)


# ==================================================
# SESSION STATE AND PERSISTENT HISTORY
# ==================================================

defaults = {
    "pipeline": None,
    "repository_path": None,
    "repository_name": None,
    "repository_id": None,
    "indexed": False,
    "index_stats": None,
    "chat_history": []
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


repository_history = RepositoryHistory()

CHAT_HISTORY_FILE = Path("data/chat_history.json")
CHAT_HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)


def load_chat_history(repository_id):
    """Load the saved conversation for one repository."""

    if not repository_id or not CHAT_HISTORY_FILE.exists():
        return []

    try:
        with CHAT_HISTORY_FILE.open("r", encoding="utf-8") as file:
            all_chats = json.load(file)

        return all_chats.get(repository_id, [])

    except (json.JSONDecodeError, OSError):
        return []


def save_chat_history(repository_id, chats):
    """Persist conversation history separately for each repository."""

    if not repository_id:
        return

    all_chats = {}

    if CHAT_HISTORY_FILE.exists():
        try:
            with CHAT_HISTORY_FILE.open("r", encoding="utf-8") as file:
                all_chats = json.load(file)
        except (json.JSONDecodeError, OSError):
            all_chats = {}

    all_chats[repository_id] = chats

    temporary_path = CHAT_HISTORY_FILE.with_suffix(".tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(all_chats, file, indent=4, ensure_ascii=False)

    os.replace(temporary_path, CHAT_HISTORY_FILE)


def register_loaded_repository(
    path,
    source_type,
    source_reference=None
):
    """Save a newly loaded repository and make it the active workspace."""

    path = str(Path(path).resolve())

    record = repository_history.add_repository(
        name=Path(path).name,
        repository_path=path,
        source_type=source_type,
        source_reference=source_reference
    )

    st.session_state.repository_path = path
    st.session_state.repository_name = record["name"]
    st.session_state.repository_id = record["id"]
    st.session_state.indexed = record.get("indexed", False)
    st.session_state.index_stats = record.get("index_stats")
    st.session_state.chat_history = load_chat_history(record["id"])
    st.session_state.pipeline = None

    return record


def open_saved_repository(repository_id):
    """Restore a repository selected from persistent history."""

    record = repository_history.get_repository(repository_id)

    if not record:
        raise ValueError("The selected repository was not found in history.")

    repository_path = record.get("path")

    if not repository_path or not Path(repository_path).is_dir():
        raise ValueError(
            "The saved repository folder is no longer available. "
            "Please load the repository again."
        )

    st.session_state.repository_path = repository_path
    st.session_state.repository_name = record["name"]
    st.session_state.repository_id = record["id"]
    st.session_state.indexed = record.get("indexed", False)
    st.session_state.index_stats = record.get("index_stats")
    st.session_state.chat_history = load_chat_history(record["id"])
    st.session_state.pipeline = None


def get_active_pipeline():
    """Create the RAG pipeline and select the active repository."""

    if st.session_state.pipeline is None:
        st.session_state.pipeline = RAGPipeline()

    pipeline = st.session_state.pipeline

    if pipeline.repository_id != st.session_state.repository_id:
        pipeline.select_repository(st.session_state.repository_id)

    return pipeline


# ==================================================
# CUSTOM DESIGN
# ==================================================

st.markdown("""
<style>

/* ---------- GLOBAL ---------- */

.stApp {
    background:
        radial-gradient(ellipse at 15% 0%, #31216b55, transparent 38%),
        radial-gradient(ellipse at 90% 20%, #164e6350, transparent 35%),
        linear-gradient(135deg, #0b1020, #11152b 55%, #1b1235);
    color: #f1f5f9;
}

.block-container {
    max-width: 1500px !important;
    padding: 2rem 3rem 3rem;
}

h1, h2, h3, p, label {
    color: #f1f5f9;
}

hr {
    border-color: #34345c !important;
}

/* ---------- SIDEBAR ---------- */

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #10172b, #201746);
    border-right: 1px solid #39315f;
}

[data-testid="stSidebar"] * {
    color: #e2e8f0;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #c4b5fd !important;
}

/* ---------- HERO ---------- */

.hero-card {
    background: linear-gradient(
        115deg,
        #31216e,
        #542b91 55%,
        #164e70
    );
    border: 1px solid #7962d5;
    border-radius: 24px;
    padding: 34px 38px;
    margin-bottom: 26px;
    box-shadow: 0 12px 45px #00000035;
}

.hero-title {
    font-size: 43px;
    font-weight: 900;
    letter-spacing: -1px;
    color: #ffffff;
    margin: 0;
}

.hero-subtitle {
    color: #ddd6fe;
    font-size: 16px;
    margin-top: 9px;
}

.hero-tag {
    display: inline-block;
    margin-top: 17px;
    padding: 7px 14px;
    border-radius: 30px;
    background: #ffffff20;
    color: #a5f3fc;
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}

/* ---------- SECTION HEADINGS ---------- */

.section-heading {
    font-size: 22px;
    font-weight: 800;
    color: #f8fafc;
    margin: 8px 0 15px;
}

.section-caption {
    color: #a5b4fc;
    font-size: 13px;
    margin-top: -8px;
    margin-bottom: 17px;
}

/* ---------- DASHBOARD CARDS ---------- */

[data-testid="stVerticalBlockBorderWrapper"] {
    background: linear-gradient(145deg, #1b2340, #171a32) !important;
    border: 1px solid #393b70 !important;
    border-radius: 17px !important;
    box-shadow: 0 7px 22px #00000020;
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, #29245b, #1c2945);
    border: 1px solid #6555a8;
    border-radius: 16px;
    padding: 19px;
    min-height: 112px;
}

[data-testid="stMetricLabel"] {
    color: #c4b5fd !important;
    font-weight: 600;
}

[data-testid="stMetricValue"] {
    color: #67e8f9 !important;
    font-weight: 900;
}

/* ---------- BUTTONS ---------- */

.stButton button {
    background: linear-gradient(100deg, #7c3aed, #4f46e5);
    color: white !important;
    border: 1px solid #8b5cf6;
    border-radius: 11px;
    min-height: 43px;
    font-weight: 700;
    transition: 0.2s ease;
}

.stButton button:hover {
    background: linear-gradient(100deg, #9333ea, #0891b2);
    border-color: #a78bfa;
    box-shadow: 0 5px 20px #7c3aed55;
    transform: translateY(-1px);
}

/* ---------- INPUTS ---------- */

.stTextInput input,
.stTextArea textarea {
    background: #101a30 !important;
    color: #f8fafc !important;
    border: 1px solid #4b4b80 !important;
    border-radius: 10px !important;
}

.stTextInput input::placeholder,
.stTextArea textarea::placeholder {
    color: #94a3b8 !important;
}

[data-baseweb="select"] > div {
    background: #17213a !important;
    border-color: #56518d !important;
    color: white !important;
}

/* ---------- ALERTS ---------- */

[data-testid="stAlert"] {
    background: #202746 !important;
    border: 1px solid #6255a1 !important;
    border-radius: 12px !important;
    color: #e2e8f0 !important;
}

[data-testid="stAlert"] p {
    color: #e2e8f0 !important;
}

/* ---------- EXPANDERS ---------- */

[data-testid="stExpander"] {
    background: #1a2340;
    border: 1px solid #4b4780;
    border-radius: 12px;
}

/* ---------- FILE UPLOADER ---------- */

[data-testid="stFileUploader"] {
    background: #17213a;
    border: 1px dashed #8173d5;
    border-radius: 12px;
    padding: 12px;
}

/* ---------- CHAT ---------- */

.chat-question {
    background: linear-gradient(110deg, #35216e, #263b65);
    border: 1px solid #7762c9;
    border-radius: 15px;
    padding: 17px;
    color: #f8fafc;
    margin: 12px 0;
}

.chat-answer {
    background: #17243a;
    border: 1px solid #256b79;
    border-radius: 15px;
    padding: 20px;
    color: #e2e8f0;
    margin: 12px 0;
}

/* ---------- FOOTER ---------- */

.footer {
    text-align: center;
    color: #929ac5;
    padding: 25px 0 10px;
    font-size: 13px;
}

/* ==========================================
   FINAL DARK THEME FIXES
   ========================================== */

/* Remove white top toolbar */
[data-testid="stHeader"] {
    background: #0b1020 !important;
}

[data-testid="stToolbar"] {
    background: transparent !important;
}

/* Fix all Streamlit alert boxes */
[data-testid="stAlert"] {
    background: #202746 !important;
    border: 1px solid #6255a1 !important;
    border-radius: 12px !important;
}

[data-testid="stAlert"] > div {
    background: #202746 !important;
}

[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: #e2e8f0 !important;
}

/* Success messages */
[data-testid="stAlert"][kind="success"] {
    background: #123b38 !important;
    border-color: #10b981 !important;
}

/* Information messages */
[data-testid="stAlert"][kind="info"] {
    background: #172c4a !important;
    border-color: #38bdf8 !important;
}

/* Warning messages */
[data-testid="stAlert"][kind="warning"] {
    background: #49351c !important;
    border-color: #f59e0b !important;
}

/* Fix text input backgrounds */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background-color: #101a30 !important;
    color: #ffffff !important;
    border: 1px solid #6555a8 !important;
    caret-color: white !important;
}

/* Fix input placeholder visibility */
[data-testid="stTextInput"] input::placeholder,
[data-testid="stTextArea"] textarea::placeholder {
    color: #a5b4fc !important;
    opacity: 1 !important;
}

/* Fix bordered dashboard containers */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #171c35 !important;
    border: 1px solid #51478c !important;
    border-radius: 17px !important;
}

/* Keep text inside cards readable */
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] label {
    color: #e2e8f0;
}

/* Fix sidebar inputs */
[data-testid="stSidebar"] input {
    background: #101a30 !important;
    color: white !important;
}

/* Fix file uploader text */
[data-testid="stFileUploader"] {
    background: #17213a !important;
    color: white !important;
}

/* Fix expander content */
[data-testid="stExpander"] {
    background: #1a2340 !important;
    color: white !important;
}

[data-testid="stExpander"] p {
    color: #e2e8f0 !important;
}

</style>
""", unsafe_allow_html=True)


# ==================================================
# SIDEBAR - REPOSITORY INPUT AND HISTORY
# ==================================================

with st.sidebar:

    st.markdown("## 🧠 RepoMind")
    st.caption("AI Repository Intelligence")

    st.divider()

    st.markdown("### ⚙️ Load a Repository")

    source_type = st.radio(
        "Choose repository source",
        ["GitHub URL", "ZIP Upload", "Local Folder"]
    )

    if source_type == "GitHub URL":

        github_url = st.text_input(
            "GitHub repository URL",
            placeholder="https://github.com/user/repository"
        )

        if st.button("🔗 Clone Repository", use_container_width=True):

            if not github_url.strip():
                st.error("Please enter a GitHub URL.")

            else:
                try:
                    with st.spinner("Cloning repository..."):
                        destination = Path("data/repositories")
                        destination.mkdir(parents=True, exist_ok=True)

                        path = clone_github_repository(
                            github_url,
                            str(destination)
                        )

                        register_loaded_repository(
                            path,
                            source_type="github",
                            source_reference=github_url
                        )

                    st.success("Repository cloned and saved to history!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Clone failed: {error}")

    elif source_type == "ZIP Upload":

        uploaded_file = st.file_uploader(
            "Upload repository ZIP",
            type=["zip"]
        )

        if st.button("📦 Extract Repository", use_container_width=True):

            if uploaded_file is None:
                st.error("Please upload a ZIP file.")

            else:
                zip_path = None

                try:
                    with st.spinner("Extracting repository..."):
                        destination = Path("data/repositories")
                        destination.mkdir(parents=True, exist_ok=True)

                        with tempfile.NamedTemporaryFile(
                            suffix=".zip",
                            delete=False
                        ) as temp_file:
                            temp_file.write(uploaded_file.getvalue())
                            zip_path = temp_file.name

                        path = extract_zip_file(
                            zip_path,
                            str(destination)
                        )

                        register_loaded_repository(
                            path,
                            source_type="zip",
                            source_reference=uploaded_file.name
                        )

                    st.success("Repository extracted and saved to history!")
                    st.rerun()

                except Exception as error:
                    st.error(f"Extraction failed: {error}")

                finally:
                    if zip_path and os.path.exists(zip_path):
                        os.unlink(zip_path)

    elif source_type == "Local Folder":

        local_path = st.text_input(
            "Local repository path",
            placeholder="C:/Users/Name/Desktop/Project"
        )

        if st.button("📂 Load Local Folder", use_container_width=True):

            try:
                path = load_local_repository(local_path)

                register_loaded_repository(
                    path,
                    source_type="local"
                )

                st.success("Local repository loaded and saved to history!")
                st.rerun()

            except Exception as error:
                st.error(f"Unable to load folder: {error}")

    st.divider()

    st.markdown("### 🕘 Repository History")

    saved_repositories = repository_history.get_repositories()

    if saved_repositories:
        repository_lookup = {
            repository["id"]: repository
            for repository in saved_repositories
        }

        selected_history_id = st.selectbox(
            "Previously loaded repositories",
            options=list(repository_lookup.keys()),
            format_func=lambda repository_id: (
                f"{repository_lookup[repository_id]['name']} "
                f"{'✓' if repository_lookup[repository_id].get('indexed') else '·'}"
            ),
            index=None,
            placeholder="Choose a saved repository",
            key="history_repository_selector"
        )

        if st.button(
            "↩️ Open Selected Repository",
            use_container_width=True,
            disabled=selected_history_id is None
        ):
            try:
                open_saved_repository(selected_history_id)
                st.success("Saved repository opened!")
                st.rerun()
            except Exception as error:
                st.error(f"Unable to open repository: {error}")

        st.caption(f"{len(saved_repositories)} repositories in history")

    else:
        st.info("Your loaded repositories will appear here.")

    st.divider()

    st.markdown("### 📌 Current Workspace")

    if st.session_state.repository_path:
        st.success(st.session_state.repository_name)
        st.caption(st.session_state.repository_path)

        if st.session_state.indexed:
            st.markdown("🟢 **Indexed and ready**")
        else:
            st.markdown("🟡 **Waiting for indexing**")
    else:
        st.info("No repository selected yet.")

    st.divider()

    st.caption("Powered by Python · ChromaDB · Gemini")


# ==================================================
# HERO SECTION
# ==================================================

st.markdown("""
<div class="hero-card">
    <div class="hero-title">🧠 RepoMind</div>
    <div class="hero-subtitle">
        Understand your codebase. Ask questions. Build smarter.
    </div>
    <div class="hero-tag">
        ✦ AI-POWERED REPOSITORY INTELLIGENCE
    </div>
</div>
""", unsafe_allow_html=True)


# ==================================================
# DASHBOARD OVERVIEW
# ==================================================

st.markdown(
    '<div class="section-heading">✨ Your Workspace</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-caption">'
    'An overview of your repository analysis.'
    '</div>',
    unsafe_allow_html=True
)

metric1, metric2, metric3 = st.columns(3)

if st.session_state.index_stats:

    stats = st.session_state.index_stats

    metric1.metric(
        "📁 Files Processed",
        stats["files_processed"]
    )

    metric2.metric(
        "🧩 Code Chunks",
        stats["chunks_created"]
    )

    metric3.metric(
        "🗄️ Stored in ChromaDB",
        stats["chunks_stored"]
    )

else:

    metric1.metric("📁 Files Processed", "—")
    metric2.metric("🧩 Code Chunks", "—")
    metric3.metric("🗄️ Stored in ChromaDB", "—")


st.markdown("<br>", unsafe_allow_html=True)


# ==================================================
# REPOSITORY AND INDEXING WORKSPACE
# ==================================================

left_col, right_col = st.columns([1, 1])

with left_col:

    with st.container(border=True):

        st.markdown("### 📂 Repository Information")

        if st.session_state.repository_path:

            st.markdown(
                f"**{st.session_state.repository_name}**"
            )

            st.caption(st.session_state.repository_path)

            st.markdown(
                "🟢 Repository loaded successfully."
            )

        else:

            st.markdown("**No repository loaded**")

            st.caption(
                "Choose GitHub, ZIP Upload or Local Folder "
                "from the sidebar to get started."
            )

with right_col:

    with st.container(border=True):

        st.markdown("### 🔍 Repository Indexing")

        st.caption(
            "Parse code, generate embeddings and store them in ChromaDB."
        )

        if st.session_state.repository_path:

            if st.session_state.indexed:
                st.success("Repository is indexed and ready.")

            else:
                st.info("Repository is ready for indexing.")

            if st.button(
                "🚀 Start Repository Indexing",
                use_container_width=True
            ):

                try:
                    with st.spinner(
                        "Loading models and indexing repository..."
                    ):

                        if st.session_state.pipeline is None:
                            st.session_state.pipeline = RAGPipeline()

                        pipeline = st.session_state.pipeline

                        result = pipeline.index_repository(
                            repository_path=st.session_state.repository_path,
                            repository_id=st.session_state.repository_id,
                            repository_name=st.session_state.repository_name
                        )

                        st.session_state.indexed = True
                        st.session_state.index_stats = result

                    st.success("Indexing completed successfully!")

                    st.rerun()

                except Exception as error:

                    st.session_state.indexed = False
                    st.session_state.index_stats = None

                    st.error(f"Indexing failed: {error}")

        else:

            st.warning("Load a repository first.")


# ==================================================
# AI CHAT WORKSPACE
# ==================================================

st.markdown("<br>", unsafe_allow_html=True)

st.markdown(
    '<div class="section-heading">💬 Ask RepoMind</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="section-caption">'
    'Ask questions about functions, classes and project structure.'
    '</div>',
    unsafe_allow_html=True
)

with st.container(border=True):

    if st.session_state.indexed:

        st.markdown("### ✨ Talk to your codebase")

        question = st.text_area(
            "Your question",
            placeholder=(
                "For example:\n"
                "• Explain the overall architecture of this project.\n"
                "• How does authentication work?\n"
                "• Which function handles database connections?"
            ),
            height=115,
            key="repo_question"
        )

        if st.button(
            "✦ Ask RepoMind",
            use_container_width=True
        ):

            if not question.strip():

                st.warning("Please enter a question.")

            else:

                try:
                    with st.spinner(
                        "Searching repository and generating your answer..."
                    ):

                        pipeline = get_active_pipeline()

                        response = pipeline.ask_question(question)

                    st.session_state.chat_history.append({
                        "question": question,
                        "answer": response["answer"],
                        "sources": response["sources"]
                    })

                    save_chat_history(
                        st.session_state.repository_id,
                        st.session_state.chat_history
                    )

                    st.rerun()

                except Exception as error:

                    if (
                        "503" in str(error)
                        or "high demand" in str(error).lower()
                    ):

                        st.warning(
                            "Gemini is temporarily experiencing high demand. "
                            "Your indexed repository is safe. Please try again shortly."
                        )

                    else:

                        st.error(f"Unable to generate answer: {error}")

    else:

        st.markdown("### 🔒 Your AI assistant is waiting")

        st.info(
            "Load and index a repository to unlock RepoMind's "
            "question-answering capabilities."
        )


# ==================================================
# CHAT HISTORY AND SOURCE REFERENCES
# ==================================================

if st.session_state.chat_history:

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown(
        '<div class="section-heading">🧠 Conversation</div>',
        unsafe_allow_html=True
    )

    for index, chat in enumerate(
        reversed(st.session_state.chat_history)
    ):

        st.markdown(
            f"""
            <div class="chat-question">
                <strong>🙋 Your question</strong><br><br>
                {chat["question"]}
            </div>
            """,
            unsafe_allow_html=True
        )

        with st.container(border=True):

            st.markdown("### 🤖 RepoMind's Answer")

            st.markdown(chat["answer"])

            st.markdown("---")

            st.markdown("#### 📄 Source References")

            if chat["sources"]:

                for source in chat["sources"]:

                    file_path = source.get("file_path") or "Unknown file"
                    name = source.get("name") or "Unknown symbol"

                    with st.expander(
                        f"📁 {file_path}  ·  {name}"
                    ):

                        st.write(f"**File:** {file_path}")
                        st.write(f"**Function/Class:** {name}")

                        if source.get("start_line") is not None:
                            st.write(
                                f"**Lines:** "
                                f"{source['start_line']} - "
                                f"{source['end_line']}"
                            )

            else:

                st.caption("No source references were returned.")

    if st.button("🗑️ Clear Conversation"):
        st.session_state.chat_history = []
        save_chat_history(
            st.session_state.repository_id,
            st.session_state.chat_history
        )
        st.rerun()


# ==================================================
# FOOTER
# ==================================================

st.markdown("""
<div class="footer">
    <strong>RepoMind</strong> · AI-powered Repository Intelligence
    <br><br>
    Built with Python · Streamlit · ChromaDB · Sentence Transformers · Gemini
</div>
""", unsafe_allow_html=True)
