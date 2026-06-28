# ────────────────────────────────────────────────────────────────
#  app.py  –  Streamlit UI for Multimodal Agentic RAG (MoE)
#  Run: python -m streamlit run app.py
# ────────────────────────────────────────────────────────────────

import os
import re
import time
import tempfile

import streamlit as st

from agent import create_session, ingest_document, list_ingested_documents, query_agent

# ── Page config ──────────────────────────────────────────────────
st.set_page_config(
    page_title="SNTI Document Intelligence",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .badge-text   { background:#1E88E5;color:#fff;padding:3px 12px;border-radius:12px;font-size:0.75rem;font-weight:700;display:inline-block;margin-bottom:8px; }
    .badge-visual { background:#43A047;color:#fff;padding:3px 12px;border-radius:12px;font-size:0.75rem;font-weight:700;display:inline-block;margin-bottom:8px; }
    .badge-synth  { background:#F9A825;color:#fff;padding:3px 12px;border-radius:12px;font-size:0.75rem;font-weight:700;display:inline-block;margin-bottom:8px; }
    section[data-testid="stSidebar"] { min-width:280px; max-width:300px; }
    </style>
    """,
    unsafe_allow_html=True,
)


# ════════════════════════════════════════════════════════════════
#  BADGE EXTRACTION  (robust — handles both newline and same-line)
# ════════════════════════════════════════════════════════════════

# Maps badge label → CSS class
_BADGES = [
    ("🔵 Text Expert",     "badge-text"),
    ("🟢 Visual Expert",   "badge-visual"),
    ("🟡 Synthesis Expert","badge-synth"),
]

def _extract_badge(raw: str) -> tuple[str, str]:
    """Return (badge_html, answer_body) from a raw router response.

    Handles all three separator styles the LLM might produce:
      • "🔵 Text Expert\\nAnswer..."          (badge on own line)
      • "🔵 Text Expert\\n\\nAnswer..."       (badge + blank line)
      • "🔵 Text Expert | Answer..."          (badge + pipe separator)
      • "🔵 Text Expert Answer..."            (badge fused with answer)
    """
    for label, css in _BADGES:
        if not raw.startswith(label):
            continue
        # Strip the label then any leading whitespace / pipe / newlines
        remainder = raw[len(label):]
        remainder = re.sub(r"^[\s|]+", "", remainder)
        badge_html = f'<span class="{css}">{label}</span><br>'
        return badge_html, remainder.strip()
    # No badge found — return as-is
    return "", raw


def _stream_words(text: str, delay: float = 0.035):
    """Yield text word by word to create a typewriter streaming effect.

    delay=0.035s ≈ 28 words/second — fast enough to feel snappy,
    slow enough that the streaming is clearly visible.
    For long responses (>300 words) the delay is halved automatically.
    """
    words = text.split(" ")
    if len(words) > 300:
        delay = delay / 2
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        time.sleep(delay)



if "session_id" not in st.session_state:
    st.session_state.session_id = create_session()

if "messages" not in st.session_state:
    # Each message: {"role": "user"|"assistant", "content": str, "raw": str}
    st.session_state.messages = []

if "ingested" not in st.session_state:
    st.session_state.ingested = []


# ════════════════════════════════════════════════════════════════
#  SIDEBAR
# ════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🏭 SNTI Doc Intelligence")
    st.caption("Multimodal Agentic RAG · Mixture of Experts")
    st.divider()

    # ── Upload & ingest ─────────────────────────────────────────
    st.subheader("📁 Upload Documents")
    uploaded_files = st.file_uploader(
        "PDF, PPTX, or DOCX",
        type=["pdf", "pptx", "docx"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )

    if uploaded_files:
        if st.button("⚙️ Ingest Documents", use_container_width=True, type="primary"):
            progress = st.progress(0, text="Starting…")
            for idx, uf in enumerate(uploaded_files):
                ext = uf.name.rsplit(".", 1)[-1]
                progress.progress(idx / len(uploaded_files), text=f"Processing {uf.name}…")
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
                    tmp.write(uf.read())
                    tmp_path = tmp.name
                try:
                    ingest_document(tmp_path)
                    st.session_state.ingested.append(uf.name)
                    st.success(f"✓ {uf.name}")
                except Exception as e:
                    st.error(f"✗ {uf.name}: {e}")
                finally:
                    os.unlink(tmp_path)
            progress.progress(1.0, text="Done!")

            # Clear conversation so old answers don't bleed into
            # questions about the newly ingested document
            st.session_state.messages = []
            st.session_state.session_id = create_session()
            st.toast("📄 New document ingested — conversation reset.", icon="✅")
            st.rerun()

    st.divider()

    # ── Knowledge base ──────────────────────────────────────────
    st.subheader("📋 Knowledge Base")
    if st.button("Refresh document list", use_container_width=True):
        with st.spinner("Fetching…"):
            result = list_ingested_documents()
        if result.get("documents"):
            st.caption(f"{result['count']} document(s) available:")
            for doc in result["documents"]:
                st.markdown(f"&nbsp;&nbsp;• `{doc}`", unsafe_allow_html=True)
        else:
            st.info("No documents ingested yet.")

    if st.session_state.ingested:
        st.caption("Ingested this session:")
        for name in st.session_state.ingested:
            st.markdown(f"&nbsp;&nbsp;• {name}", unsafe_allow_html=True)

    st.divider()

    # ── Controls ────────────────────────────────────────────────
    st.subheader("⚙️ Controls")
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.session_id = create_session()
        st.rerun()

    st.divider()
    st.subheader("Expert legend")
    st.markdown(
        "🔵 **Text Expert** — prose & written content  \n"
        "🟢 **Visual Expert** — diagrams & figures  \n"
        "🟡 **Synthesis Expert** — cross-document analysis"
    )


# ════════════════════════════════════════════════════════════════
#  MAIN CHAT AREA
# ════════════════════════════════════════════════════════════════
st.title("Ask your documents")
st.caption(
    "The router classifies your query and delegates to the right expert. "
    "Follow-up questions are automatically given context from previous answers."
)

# ── Render history ───────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)

# ── Chat input ───────────────────────────────────────────────────
if prompt := st.chat_input("Ask anything about your uploaded documents…"):

    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        with st.spinner("Routing to expert…"):
            try:
                raw_answer = query_agent(prompt, st.session_state.session_id)
                badge_html, answer_body = _extract_badge(raw_answer)
                error_display = None
            except Exception as e:
                err = str(e)
                badge_html, answer_body = "", ""
                if any(x in err for x in ["503", "UNAVAILABLE", "high demand",
                                           "temporarily unavailable", "429",
                                           "RESOURCE_EXHAUSTED", "quota"]):
                    error_display = (
                        "⚠️ **The AI model is temporarily overloaded.** "
                        "This usually clears in 30–60 seconds — please try again."
                    )
                else:
                    error_display = f"❌ **Unexpected error:** {err}"

        if error_display:
            # Errors shown immediately — no streaming
            st.markdown(error_display)
            display = error_display
        else:
            # Show expert badge chip instantly, then stream the answer body
            if badge_html:
                st.markdown(badge_html, unsafe_allow_html=True)
            streamed = st.write_stream(_stream_words(answer_body))
            display = badge_html + streamed

    st.session_state.messages.append({"role": "assistant", "content": display})