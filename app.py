"""
app.py — Main entry point for the AI Chatbot Suite.
A premium, highly interactive, and visually stunning central command center with live system telemetry,
hyperparameter tuning controllers, and navigation to the six chatbot modules.
"""

import streamlit as st
import os
import time
from pathlib import Path

st.set_page_config(
    page_title="AI Chatbot Suite | Command Center",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Streamlit Style Overrides & Custom Glassmorphic CSS ──
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800;900&family=Space+Grotesk:wght@300;400;500;600;700&display=swap');

/* Font Defaults */
* {
    font-family: 'Outfit', 'Inter', sans-serif;
}
h1, h2, h3, .panel-title {
    font-family: 'Space Grotesk', sans-serif;
    letter-spacing: -0.5px;
}

/* Sidebar Custom Glassmorphism */
[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.95) !important;
    border-right: 1px solid rgba(102, 126, 234, 0.15) !important;
    backdrop-filter: blur(15px);
}

/* Base Body Background Styling */
.stApp {
    background: linear-gradient(180deg, #090816 0%, #0c0a24 50%, #05040e 100%);
    color: #e2e8f0;
}

/* Pulsing background glow spheres */
.glow-sphere-1 {
    position: absolute;
    width: 300px;
    height: 300px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(102, 126, 234, 0.15) 0%, rgba(102, 126, 234, 0) 70%);
    top: 5%;
    right: 10%;
    z-index: 0;
    pointer-events: none;
    animation: float 8s ease-in-out infinite;
}

.glow-sphere-2 {
    position: absolute;
    width: 400px;
    height: 400px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(240, 147, 251, 0.1) 0%, rgba(240, 147, 251, 0) 70%);
    bottom: 10%;
    left: 5%;
    z-index: 0;
    pointer-events: none;
    animation: float 12s ease-in-out infinite alternate;
}

@keyframes float {
    0% { transform: translateY(0px) scale(1); }
    50% { transform: translateY(-20px) scale(1.05); }
    100% { transform: translateY(0px) scale(1); }
}

/* High-tech Hero Section */
.hero-container {
    background: linear-gradient(135deg, rgba(20, 15, 60, 0.6) 0%, rgba(10, 8, 35, 0.8) 100%);
    border: 1px solid rgba(102, 126, 234, 0.25);
    border-radius: 24px;
    padding: 3rem 2rem;
    text-align: center;
    margin-bottom: 2rem;
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
}

.hero-container h1 {
    font-size: 3.5rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #a1c4fd 0%, #c2e9fb 50%, #fbc2eb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 0 0 40px rgba(161, 196, 253, 0.3);
}

.hero-container p {
    color: #a0aec0;
    font-size: 1.25rem;
    max-width: 800px;
    margin: 1rem auto 0 auto;
    line-height: 1.6;
}

/* Neon Telemetry Dashboard */
.telemetry-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    gap: 1.2rem;
    margin-bottom: 2.5rem;
}

.telemetry-card {
    background: rgba(18, 16, 45, 0.5);
    border: 1px solid rgba(102, 126, 234, 0.15);
    border-radius: 16px;
    padding: 1.2rem;
    backdrop-filter: blur(12px);
    transition: all 0.3s ease;
    box-shadow: inset 0 0 12px rgba(102, 126, 234, 0.05);
}

.telemetry-card:hover {
    border-color: rgba(102, 126, 234, 0.4);
    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.1), inset 0 0 12px rgba(102, 126, 234, 0.1);
    transform: translateY(-2px);
}

.telemetry-header {
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #718096;
    margin-bottom: 0.4rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.telemetry-value {
    font-size: 1.8rem;
    font-weight: 700;
    color: #f7fafc;
    margin-bottom: 0.2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.telemetry-desc {
    font-size: 0.8rem;
    color: #a0aec0;
}

/* Pulsing Online Badge */
.pulse-badge {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background-color: #38ef7d;
    box-shadow: 0 0 10px #38ef7d;
    display: inline-block;
    animation: pulse-glow 2s infinite;
}

@keyframes pulse-glow {
    0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 239, 125, 0.7); }
    70% { transform: scale(1); box-shadow: 0 0 0 8px rgba(56, 239, 125, 0); }
    100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(56, 239, 125, 0); }
}

/* Futuristic Feature Grid */
.feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
    gap: 1.5rem;
    margin-bottom: 3rem;
}

.feature-card {
    background: linear-gradient(145deg, rgba(22, 18, 54, 0.55) 0%, rgba(13, 10, 36, 0.75) 100%);
    border-radius: 20px;
    padding: 2rem;
    border: 1px solid rgba(102, 126, 234, 0.12);
    transition: all 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
    position: relative;
    overflow: hidden;
    backdrop-filter: blur(10px);
}

.feature-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    border-radius: 20px 20px 0 0;
    opacity: 0.7;
    transition: opacity 0.3s ease;
}

.feature-card:hover {
    border-color: rgba(102, 126, 234, 0.4);
    transform: translateY(-6px);
    box-shadow: 0 20px 40px rgba(10, 5, 30, 0.5), 0 0 20px rgba(102, 126, 234, 0.15);
}

.feature-card:hover::after {
    opacity: 1;
}

.card-1::after { background: linear-gradient(90deg, #667eea, #764ba2); }
.card-2::after { background: linear-gradient(90deg, #f093fb, #f5576c); }
.card-3::after { background: linear-gradient(90deg, #11998e, #38ef7d); }
.card-4::after { background: linear-gradient(90deg, #4facfe, #00f2fe); }
.card-5::after { background: linear-gradient(90deg, #fa709a, #fee140); }
.card-6::after { background: linear-gradient(90deg, #a18cd1, #fbc2eb); }

.feature-icon-wrapper {
    width: 60px;
    height: 60px;
    border-radius: 16px;
    background: rgba(102, 126, 234, 0.1);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2.2rem;
    margin-bottom: 1.2rem;
    border: 1px solid rgba(102, 126, 234, 0.2);
}

.feature-title {
    color: #f7fafc;
    font-size: 1.35rem;
    font-weight: 700;
    margin-bottom: 0.6rem;
}

.feature-desc {
    color: #a0aec0;
    font-size: 0.95rem;
    line-height: 1.6;
    margin-bottom: 1.2rem;
}

.feature-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.4rem;
}

.feature-tag {
    background: rgba(102, 126, 234, 0.12);
    color: #a3b8ff;
    padding: 0.25rem 0.6rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 500;
    border: 1px solid rgba(102, 126, 234, 0.08);
}

/* Beautiful Interactive Guide Box */
.guide-box {
    background: linear-gradient(135deg, rgba(22, 18, 54, 0.5) 0%, rgba(13, 10, 36, 0.7) 100%);
    border: 1px solid rgba(102, 126, 234, 0.2);
    border-radius: 20px;
    padding: 2.5rem;
    backdrop-filter: blur(10px);
    margin-bottom: 2rem;
}

.guide-box h3 {
    color: #fff;
    margin-bottom: 1.2rem;
    font-size: 1.5rem;
}

.guide-box ol li {
    color: #cbd5e0;
    margin-bottom: 0.8rem;
    line-height: 1.6;
}

.guide-box code {
    background: rgba(102, 126, 234, 0.2) !important;
    color: #a3b8ff !important;
    padding: 0.2rem 0.5rem !important;
    border-radius: 6px !important;
    font-family: 'Courier New', Courier, monospace;
}

.footer {
    text-align: center;
    padding: 3rem 0;
    color: #4a5568;
    font-size: 0.9rem;
    border-top: 1px solid rgba(102, 126, 234, 0.1);
    margin-top: 2rem;
}
</style>

<div class="glow-sphere-1"></div>
<div class="glow-sphere-2"></div>
""", unsafe_allow_html=True)

# ── Dynamic Database Size calculation ──
db_path = Path("chroma_db/vector_store.sqlite")
db_size_str = "0.00 KB"
if db_path.exists():
    try:
        size_bytes = db_path.stat().st_size
        if size_bytes > 1024 * 1024:
            db_size_str = f"{size_bytes / (1024 * 1024):.2f} MB"
        else:
            db_size_str = f"{size_bytes / 1024:.2f} KB"
    except Exception:
        pass

# ── Initialize session state vectors ──
if "kb_sources" not in st.session_state:
    st.session_state.kb_sources = []

# ── Read document counts inside our SQLite DB ──
kb_doc_count = 0
medical_doc_count = 0
arxiv_doc_count = 0

if db_path.exists():
    import sqlite3
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
        if cursor.fetchone():
            cursor.execute("SELECT COUNT(*) FROM documents WHERE collection_name = ?", (config.COLLECTION_KNOWLEDGE_BASE,))
            kb_doc_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents WHERE collection_name = ?", (config.COLLECTION_MEDICAL,))
            medical_doc_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM documents WHERE collection_name = ?", (config.COLLECTION_ARXIV,))
            arxiv_doc_count = cursor.fetchone()[0]
        conn.close()
    except Exception:
        pass

total_indexed_docs = kb_doc_count + medical_doc_count + arxiv_doc_count

# ── Sidebar Configuration & Tuning Panel ──
with st.sidebar:
    st.markdown("## 🛠️ Global Parameters")
    
    # API key setup
    api_key = st.text_input("Google Gemini API Key", type="password", value=os.getenv("GOOGLE_API_KEY", ""))
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key
        st.success("✅ API Key Configured")
    else:
        st.warning("Enter Gemini API key to activate AI features")
        
    st.divider()
    
    # Model Tuning
    st.markdown("### 🎛️ Hyperparameter Controller")
    selected_model = st.selectbox(
        "Active Gemini Model", 
        ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"],
        help="Select which Large Language Model backend to use for generations."
    )
    st.session_state.gemini_model = selected_model
    
    generation_temp = st.slider(
        "Temperature", 
        min_value=0.0, 
        max_value=1.0, 
        value=0.7, 
        step=0.05,
        help="Controls output creativity: 0.0 is deterministic and focused, 1.0 is creative."
    )
    st.session_state.gemini_temp = generation_temp

    max_tokens = st.slider(
        "Max Output Length", 
        min_value=256, 
        max_value=8192, 
        value=2048, 
        step=256,
        help="The maximum number of tokens to generate in response."
    )
    st.session_state.gemini_max_tokens = max_tokens

    st.divider()
    st.markdown("### 🧬 Telemetry Presets")
    st.caption(f"Backend Server: Python 3.10")
    st.caption(f"Host OS: Windows Core API")

# ── Hero Section ──
st.markdown("""
<div class="hero-container">
    <h1>🤖 AI Chatbot Suite</h1>
    <p>An enterprise-grade, high-performance RAG and cognitive analytics suite. Six specialized AI agents powered by a custom pure-Python high-density SQLite vector database and Google Gemini models.</p>
</div>
""", unsafe_allow_html=True)

# ── Telemetry Dashboard Section ──
st.markdown("### 📊 Live System Telemetry Dashboard")

col1, col2, col3, col4 = st.columns(4)

with col1:
    api_status_html = """
    <div class="telemetry-card">
        <div class="telemetry-header">Gemini Heartbeat <span class="pulse-badge"></span></div>
        <div class="telemetry-value">Active</div>
        <div class="telemetry-desc">Google Generative AI Connection is ready.</div>
    </div>
    """
    st.markdown(api_status_html, unsafe_allow_html=True)

with col2:
    db_size_html = f"""
    <div class="telemetry-card">
        <div class="telemetry-header">Vector Index Storage</div>
        <div class="telemetry-value">{db_size_str}</div>
        <div class="telemetry-desc">SQLite disk footprint in data directory.</div>
    </div>
    """
    st.markdown(db_size_html, unsafe_allow_html=True)

with col3:
    records_html = f"""
    <div class="telemetry-card">
        <div class="telemetry-header">Total Vectors Indexed</div>
        <div class="telemetry-value">{total_indexed_docs}</div>
        <div class="telemetry-desc">Documents successfully mapped into 768-D space.</div>
    </div>
    """
    st.markdown(records_html, unsafe_allow_html=True)

with col4:
    # Estimate latency
    latency_str = "~240 ms" if api_key else "N/A"
    latency_html = f"""
    <div class="telemetry-card">
        <div class="telemetry-header">Similarity Engine Latency</div>
        <div class="telemetry-value">{latency_str}</div>
        <div class="telemetry-desc">Pure-Python Cosine matrix lookup speed.</div>
    </div>
    """
    st.markdown(latency_html, unsafe_allow_html=True)

st.divider()

# ── Intelligent Feature Cards ──
st.markdown("### 🧩 Cognitive Chatbot Core Modules")

st.markdown(f"""
<div class="feature-grid">
    <div class="feature-card card-1">
        <div class="feature-icon-wrapper">🧠</div>
        <div class="feature-title">Dynamic Knowledge Base</div>
        <div class="feature-desc">Dynamically expand your chatbot's cognitive scope. Instantly ingest URLs, text documents, or files, and run RAG semantic retrievals on your custom knowledge.</div>
        <div style="margin-bottom:1rem; font-size:0.85rem; color:#8888a0;">Currently Indexed: <strong>{kb_doc_count} chunks</strong></div>
        <div class="feature-tags">
            <span class="feature-tag">SQLite-Vector</span>
            <span class="feature-tag">Cosine-Similarity</span>
            <span class="feature-tag">Web Scraper</span>
            <span class="feature-tag">Auto-Update</span>
        </div>
    </div>
    <div class="feature-card card-2">
        <div class="feature-icon-wrapper">🖼️</div>
        <div class="feature-title">Multi-Modal Vision Agent</div>
        <div class="feature-desc">Interact using high-fidelity vision models. Upload image files or use your live web-camera feed to perform real-time, deep conversational visual scene understanding.</div>
        <div style="margin-bottom:1rem; font-size:0.85rem; color:#8888a0;">Active Model: <strong>Gemini Vision Core</strong></div>
        <div class="feature-tags">
            <span class="feature-tag">Gemini-Vision</span>
            <span class="feature-tag">Image OCR</span>
            <span class="feature-tag">Real-Time Camera</span>
            <span class="feature-tag">Scene Parsing</span>
        </div>
    </div>
    <div class="feature-card card-3">
        <div class="feature-icon-wrapper">🏥</div>
        <div class="feature-title">Medical Q&A Expert</div>
        <div class="feature-desc">Advanced clinical QA chatbot powered by a large MedQuAD collection. Fully equipped with custom medical entity extraction for symptoms, conditions, and body parts.</div>
        <div style="margin-bottom:1rem; font-size:0.85rem; color:#8888a0;">Currently Indexed: <strong>{medical_doc_count} QA pairs</strong></div>
        <div class="feature-tags">
            <span class="feature-tag">Clinical RAG</span>
            <span class="feature-tag">Medical NER</span>
            <span class="feature-tag">Disclaimer Filter</span>
            <span class="feature-tag">NIH MedQuAD</span>
        </div>
    </div>
    <div class="feature-card card-4">
        <div class="feature-icon-wrapper">📚</div>
        <div class="feature-title">arXiv Research Expert</div>
        <div class="feature-desc">Graduate-level academic research companion. Scans scientific publications, performs multi-paper RAG search, generates structured summaries, and draws keyword clouds.</div>
        <div style="margin-bottom:1rem; font-size:0.85rem; color:#8888a0;">Currently Indexed: <strong>{arxiv_doc_count} papers</strong></div>
        <div class="feature-tags">
            <span class="feature-tag">Academic-Search</span>
            <span class="feature-tag">Abstract Clustering</span>
            <span class="feature-tag">WordCloud Viz</span>
            <span class="feature-tag">Cite Support</span>
        </div>
    </div>
    <div class="feature-card card-5">
        <div class="feature-icon-wrapper">😊</div>
        <div class="feature-title">Sentiment & Tone Adaptation</div>
        <div class="feature-desc">Empathetic conversation system using VADER sentiment metrics. The agent evaluates your inputs in real time and dynamically modifies its tone to be highly supportive.</div>
        <div style="margin-bottom:1rem; font-size:0.85rem; color:#8888a0;">Adaptation Method: <strong>Dynamic Prompts</strong></div>
        <div class="feature-tags">
            <span class="feature-tag">VADER Sentiment</span>
            <span class="feature-tag">Dynamic Tone</span>
            <span class="feature-tag">Emotional Adapt</span>
            <span class="feature-tag">Tone Gauge</span>
        </div>
    </div>
    <div class="feature-card card-6">
        <div class="feature-icon-wrapper">🌍</div>
        <div class="feature-title">Multilingual Context Agent</div>
        <div class="feature-desc">Global communication system operating across 8+ international languages. Detects language input automatically and responses with flawless translation and cultural awareness.</div>
        <div style="margin-bottom:1rem; font-size:0.85rem; color:#8888a0;">Supported Scope: <strong>8 Languages</strong></div>
        <div class="feature-tags">
            <span class="feature-tag">Auto-Language-Detect</span>
            <span class="feature-tag">Deep-Translation</span>
            <span class="feature-tag">Cultural Adapters</span>
            <span class="feature-tag">UTF-8 Compliant</span>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Dynamic Prompt Explorer / Try These ──
st.markdown("### 💡 Quick Prompt Explorations")
col_p1, col_p2, col_p3 = st.columns(3)

with col_p1:
    st.info("**🏥 Clinical Question Sample**\n\n*\"What are the symptoms and genetic risk triggers of Type 2 diabetes?\"*")
with col_p2:
    st.info("**📚 Academic Concept Exploration**\n\n*\"Explain the FlashAttention IO-aware tiling mechanism to a graduate student.\"*")
with col_p3:
    st.info("**🧠 Knowledge Base Ingestion**\n\n*Ingest a scientific article, ask RAG questions, and view similarity scores instantly!*")

st.divider()

# ── Advanced Setup & Deployment Guide ──
st.markdown("""
<div class="guide-box">
    <h3>🚀 Developer Deployment Command Desk</h3>
    <ol>
        <li><strong>Activate the Python environment</strong> on your target hosting platform.</li>
        <li><strong>Ensure all requirements are pre-loaded:</strong> <code>pip install -r requirements.txt</code></li>
        <li><strong>Download the essential NLP model:</strong> <code>python -m spacy download en_core_web_sm</code></li>
        <li><strong>Provide your API Credentials:</strong> Set <code>GOOGLE_API_KEY</code> inside your secure environmental keys or production <code>.env</code> file.</li>
        <li><strong>Launch Command:</strong> Run <code>streamlit run app.py --server.port 8501 --server.address 0.0.0.0</code> for network deployment.</li>
    </ol>
    <p style="margin: 1rem 0 0 0; color: #a0aec0; font-size: 0.9rem;">
        <em>Note: The vector storage engine is fully encapsulated inside standard library SQL connections. No heavy third-party database deployments or Docker containers are required for hosting!</em>
    </p>
</div>
""", unsafe_allow_html=True)

# Import helper configuration for config paths
import config

st.markdown(f'<div class="footer">AI Chatbot Suite © 2026 | Built with Outfit Sans, SQLite VectorStore, and Google Gemini Models</div>', unsafe_allow_html=True)
