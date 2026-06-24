"""
Page 1: Dynamic Knowledge Base — Add sources, auto-update, and query your knowledge base.
"""

import streamlit as st
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.knowledge_base import KnowledgeBaseManager

st.set_page_config(page_title="Knowledge Base", page_icon="🧠", layout="wide")

# ── Custom CSS ──
st.markdown("""
<style>
.kb-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; }
.kb-header h1 { color: white; margin: 0; }
.kb-header p { color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; }
.stat-card { background: linear-gradient(135deg, #1a1a2e, #16213e); padding: 1.2rem; border-radius: 12px; text-align: center; border: 1px solid rgba(102,126,234,0.3); }
.stat-card h3 { color: #667eea; margin: 0; font-size: 2rem; }
.stat-card p { color: #a0a0b0; margin: 0.3rem 0 0 0; font-size: 0.85rem; }
.source-tag { display: inline-block; background: rgba(102,126,234,0.15); color: #667eea; padding: 0.25rem 0.75rem; border-radius: 20px; font-size: 0.8rem; margin: 0.2rem; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="kb-header">
    <h1>🧠 Dynamic Knowledge Base</h1>
    <p>Add documents, URLs, and text to expand your chatbot's knowledge. Query it with natural language.</p>
</div>
""", unsafe_allow_html=True)

# ── Initialize ──
if "kb_manager" not in st.session_state:
    st.session_state.kb_manager = KnowledgeBaseManager()
if "kb_chat" not in st.session_state:
    st.session_state.kb_chat = []
if "kb_sources" not in st.session_state:
    st.session_state.kb_sources = []
if "kb_last_update" not in st.session_state:
    st.session_state.kb_last_update = 0

kb = st.session_state.kb_manager

# ── Sidebar: Source Management ──
with st.sidebar:
    st.header("📥 Add Knowledge")

    tab1, tab2, tab3 = st.tabs(["🔗 URL", "📄 File", "✏️ Text"])

    with tab1:
        url = st.text_input("Enter URL to scrape", placeholder="https://example.com/article")
        if st.button("Add URL", key="add_url", type="primary"):
            if url:
                with st.spinner("Scraping URL..."):
                    result = kb.add_from_url(url)
                if result["success"]:
                    st.success(f"Added {result['added']} chunks from {result.get('title', url)}")
                    st.session_state.kb_sources.append(url)
                else:
                    st.error(f"Failed: {result['error']}")
            else:
                st.warning("Please enter a URL")

    with tab2:
        uploaded = st.file_uploader("Upload a text file", type=["txt", "md", "csv"])
        if uploaded and st.button("Ingest File", type="primary"):
            content = uploaded.read().decode("utf-8", errors="ignore")
            with st.spinner("Processing file..."):
                added = kb.add_from_file(content, uploaded.name)
            st.success(f"Added {added} chunks from {uploaded.name}")

    with tab3:
        text_input = st.text_area("Paste text content", height=150, placeholder="Paste any text here...")
        source_name = st.text_input("Source name", value="manual_input")
        if st.button("Add Text", type="primary"):
            if text_input:
                with st.spinner("Processing..."):
                    added = kb.add_from_text(text_input, source_name)
                st.success(f"Added {added} chunks")
            else:
                st.warning("Please enter some text")

    st.divider()

    # Auto-Update Settings
    st.header("🔄 Auto-Update")
    update_interval = st.number_input("Update interval (hours)", min_value=0.5, max_value=168.0, value=24.0, step=0.5)

    if st.session_state.kb_sources:
        st.write("**Configured Sources:**")
        for src in st.session_state.kb_sources:
            st.markdown(f'<span class="source-tag">{src[:40]}...</span>', unsafe_allow_html=True)

        if st.button("🔄 Update Now"):
            with st.spinner("Updating from all sources..."):
                result = kb.periodic_update(st.session_state.kb_sources)
            st.session_state.kb_last_update = time.time()
            st.success(f"Updated! Added {result['total_added']} new chunks.")

    if st.button("🗑️ Clear Knowledge Base", type="secondary"):
        kb.clear()
        st.session_state.kb_chat = []
        st.session_state.kb_sources = []
        st.rerun()

# ── Main Content ──
col1, col2, col3 = st.columns(3)
stats = kb.get_stats()

with col1:
    st.markdown(f'<div class="stat-card"><h3>{stats["document_count"]}</h3><p>Documents Indexed</p></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card"><h3>{len(st.session_state.kb_sources)}</h3><p>Sources Added</p></div>', unsafe_allow_html=True)
with col3:
    last_update = "Never" if st.session_state.kb_last_update == 0 else time.strftime("%H:%M:%S", time.localtime(st.session_state.kb_last_update))
    st.markdown(f'<div class="stat-card"><h3>{last_update}</h3><p>Last Updated</p></div>', unsafe_allow_html=True)

st.divider()

# ── Chat Interface ──
st.subheader("💬 Ask Your Knowledge Base")

for msg in st.session_state.kb_chat:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📎 Sources"):
                for src in msg["sources"]:
                    st.caption(f"• {src}")

if prompt := st.chat_input("Ask a question about your knowledge base..."):
    st.session_state.kb_chat.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("Searching knowledge base..."):
            result = kb.query(prompt)
        st.markdown(result["answer"])
        if result.get("sources"):
            with st.expander("📎 Sources"):
                for src in result["sources"]:
                    st.caption(f"• {src}")

    st.session_state.kb_chat.append({
        "role": "assistant", "content": result["answer"], "sources": result.get("sources", [])
    })
