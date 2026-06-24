"""
Page 4: Research Expert — Search papers, get summaries, and explore concepts from arXiv.
Upgraded with high-fidelity telemetry, dynamic academic concept defilers, and custom styled visualizations.
"""

import streamlit as st
import sys
import json
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
import time

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.research_expert import ResearchExpert, ARXIV_CATEGORIES

st.set_page_config(page_title="arXiv Domain Research Expert", page_icon="📚", layout="wide")

# ── Premium Styles for Research Dashboard ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Space+Grotesk:wght@400;500;600;700&display=swap');

/* Font application */
* { font-family: 'Outfit', sans-serif; }
h1, h2, h3, .dashboard-title { font-family: 'Space Grotesk', sans-serif; }

/* Dashboard Header */
.research-header {
    background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
    padding: 2.5rem 2rem;
    border-radius: 24px;
    border: 1px solid rgba(79, 172, 254, 0.25);
    color: white;
    margin-bottom: 2rem;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
}

.research-header h1 {
    color: #4facfe;
    margin: 0;
    font-size: 2.6rem;
    font-weight: 700;
    text-shadow: 0 0 30px rgba(79, 172, 254, 0.2);
}

.research-header p {
    color: #cbd5e1;
    margin-top: 0.5rem;
    font-size: 1.1rem;
}

/* Styled paper cards */
.paper-card {
    background: rgba(18, 16, 45, 0.55);
    border: 1px solid rgba(79, 172, 254, 0.15);
    border-radius: 16px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    transition: all 0.3s ease;
    backdrop-filter: blur(10px);
}

.paper-card:hover {
    border-color: rgba(79, 172, 254, 0.4);
    box-shadow: 0 8px 24px rgba(79, 172, 254, 0.12);
    transform: translateY(-2px);
}

.paper-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #4facfe;
    margin-bottom: 0.5rem;
}

.paper-meta {
    font-size: 0.85rem;
    color: #94a3b8;
    margin-bottom: 0.8rem;
    line-height: 1.4;
}

/* Custom badges */
.cat-badge {
    display: inline-block;
    background: rgba(79, 172, 254, 0.12);
    color: #93c5fd;
    padding: 0.25rem 0.6rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
    margin-right: 0.4rem;
    border: 1px solid rgba(79, 172, 254, 0.15);
}

.score-badge {
    display: inline-block;
    background: rgba(56, 239, 125, 0.12);
    color: #68d391;
    padding: 0.25rem 0.6rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    border: 1px solid rgba(56, 239, 125, 0.2);
}

/* Concept definer console */
.concept-panel {
    background: rgba(30, 41, 59, 0.4);
    border: 1px solid rgba(79, 172, 254, 0.2);
    border-radius: 20px;
    padding: 2rem;
    margin-top: 1.5rem;
}

.concept-title {
    font-size: 1.2rem;
    font-weight: 700;
    color: #fff;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.markdown("""
<div class="research-header">
    <h1>📚 arXiv Advanced Domain Explorer</h1>
    <p>Perform deep semantic research, compile structured summaries, and decode complex scientific architectures using standard RAG connections.</p>
</div>
""", unsafe_allow_html=True)

# ── Initialize ──
if "research_engine" not in st.session_state:
    st.session_state.research_engine = ResearchExpert()
if "research_chat" not in st.session_state:
    st.session_state.research_chat = []
if "research_indexed" not in st.session_state:
    st.session_state.research_indexed = False

engine = st.session_state.research_engine

# ── Sidebar ──
with st.sidebar:
    st.header("📊 Research Corpus Center")

    if not st.session_state.research_indexed:
        st.warning("⚠️ Research index is not loaded.")
        if st.button("📥 Load Sample arXiv Data", type="primary", use_container_width=True):
            with st.spinner("Building scholarly vector space..."):
                count = engine.load_sample_data()
                if count > 0:
                    indexed = engine.build_index()
                    st.session_state.research_indexed = True
                    st.success(f"Successfully indexed {indexed} academic papers!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Error reading paper database.")
    else:
        stats = engine.get_stats()
        st.success(f"✅ Academic Database Active")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.metric("Papers Loaded", stats.get("loaded_papers", 0))
        with col_s2:
            st.metric("Vector Nodes", stats.get("document_count", 0))

    st.divider()
    
    # Concept Explainer in Sidebar
    st.header("💡 Academic Concept Definer")
    preset_concepts = [
        "Select Concept...",
        "Transformer Architectures",
        "Generative Diffusion Models",
        "FlashAttention mechanism",
        "Direct Preference Optimization (DPO)",
        "Parameter-Efficient Finetuning (LoRA)",
        "Retrieval-Augmented Generation (RAG)"
    ]
    selected_concept = st.selectbox("Quick-Explain Core Topics", preset_concepts)
    
    if selected_concept != "Select Concept..." and st.session_state.research_indexed:
        if st.button("🔍 Explain Concept Now", type="secondary", use_container_width=True):
            with st.spinner("Compiling academic explanation..."):
                explanation = engine.explain_concept(selected_concept)
                
            st.session_state.research_chat.append({
                "role": "user",
                "content": f"Explain the concept of {selected_concept} in detail."
            })
            st.session_state.research_chat.append({
                "role": "assistant",
                "content": explanation
            })
            st.rerun()

    st.divider()
    
    if st.button("🧹 Clear Research Dialogue", use_container_width=True):
        st.session_state.research_chat = []
        engine.clear_history()
        st.rerun()

# ── Main Page Tabs ──
tab_chat, tab_search, tab_viz = st.tabs([
    "💬 Scholar AI Dialogue", 
    "🔍 Advanced Semantic Search", 
    "📊 Scholarly Visualizations"
])

with tab_chat:
    st.subheader("🎓 Graduate-Level Research Companion")
    
    # Dialogues
    for msg in st.session_state.research_chat:
        avatar = "🎓" if msg["role"] == "assistant" else "🧑"
        with st.chat_message(msg["role"], avatar=avatar):
            st.markdown(msg["content"])

    # Chat Input
    if prompt := st.chat_input("Ask a complex research or algorithmic question..." if st.session_state.research_indexed else "Please activate the index first..."):
        if not st.session_state.research_indexed:
            st.warning("Please index the database in the sidebar to run semantic chats.")
        else:
            st.session_state.research_chat.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
                
            with st.chat_message("assistant", avatar="🎓"):
                with st.spinner("Scanning publications and synthesizing..."):
                    answer = engine.expert_chat(prompt)
                st.markdown(answer)
                
            st.session_state.research_chat.append({"role": "assistant", "content": answer})
            st.rerun()

with tab_search:
    st.subheader("🔍 Vector Semantic Search & Structured Summaries")
    
    search_query = st.text_input("🔍 Query the vector space", placeholder="e.g., contrastive representations zero shot CLIP")
    
    if search_query:
        if not st.session_state.research_indexed:
            st.warning("Please activate the database index first.")
        else:
            with st.spinner("Computing cosine distances..."):
                results = engine.search_papers(search_query, top_k=6)
                
            if results:
                st.markdown(f"Found **{len(results)}** matches sorted by relevance:")
                
                for i, paper in enumerate(results):
                    # Parse paper layout
                    st.markdown(f"""
                    <div class="paper-card">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div class="paper-title">📄 {paper['title']}</div>
                            <span class="score-badge">Relevance: {paper['relevance']:.1f}%</span>
                        </div>
                        <div class="paper-meta">
                            <strong>Authors:</strong> {paper['authors']}<br>
                            <strong>Categories:</strong> <span class="cat-badge">{paper['categories']}</span>
                        </div>
                        <div style="color: #cbd5e1; font-size: 0.95rem; line-height: 1.6; margin-bottom: 1rem;">
                            {paper['content']}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Actions inside columns
                    col_act1, col_act2, col_act3 = st.columns([1, 1, 3])
                    with col_act1:
                        if st.button(f"📝 AI Summarize", key=f"sum_btn_{i}"):
                            with st.spinner("Generating structured review..."):
                                summary = engine.summarize_paper(paper["content"])
                            st.info(f"**AI Structured Summary for {paper['title'][:50]}...**")
                            st.markdown(summary)
                    with col_act2:
                        if paper.get("arxiv_id"):
                            st.link_button("🔗 View on arXiv", f"https://arxiv.org/abs/{paper['arxiv_id']}")
                    st.markdown("---")
            else:
                st.info("No matching papers found. Try simpler query vectors.")

with tab_viz:
    st.subheader("📊 Scholarly Data Clusters & Analytics")
    
    if st.session_state.research_indexed and engine.papers:
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.markdown("### 📊 Distribution of Ingested Categories")
            dist = engine.get_category_distribution()
            if dist:
                # Custom cobalt template
                fig = px.bar(
                    x=list(dist.keys()), 
                    y=list(dist.values()), 
                    labels={"x": "arXiv Subcategory", "y": "Paper Frequency"},
                    color=list(dist.values()), 
                    color_continuous_scale="Tealgrn"
                )
                fig.update_layout(
                    template="plotly_dark", 
                    height=450, 
                    showlegend=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
        with col_g2:
            st.markdown("### ☁️ Scholarly Keyword Density Matrix")
            keywords = engine.get_all_keywords(top_n=30)
            if keywords:
                try:
                    from wordcloud import WordCloud
                    import matplotlib.pyplot as plt
                    
                    wc = WordCloud(
                        width=700, 
                        height=450, 
                        background_color="#0e1117",
                        colormap="GnBu", 
                        max_words=30
                    ).generate_from_frequencies(keywords)
                    
                    fig_wc, ax = plt.subplots(figsize=(8, 5))
                    ax.imshow(wc, interpolation="bilinear")
                    ax.axis("off")
                    fig_wc.patch.set_facecolor("#0e1117")
                    st.pyplot(fig_wc)
                except Exception:
                    # Fallback to interactive bar chart
                    fig_kw = px.bar(
                        x=list(keywords.keys())[:15],
                        y=list(keywords.values())[:15],
                        labels={"x": "Keyword", "y": "Occurrences"},
                        color=list(keywords.values())[:15],
                        color_continuous_scale="Purples"
                    )
                    fig_kw.update_layout(
                        template="plotly_dark",
                        height=450,
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_kw, use_container_width=True)
    else:
        st.info("Activate the scholarly index in the sidebar to generate visual analytics.")
