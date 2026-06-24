"""
Page 6: Multilingual Chatbot — Auto-detect language and respond in 8+ languages.
"""

import streamlit as st
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.multilingual import MultilingualEngine
import config

st.set_page_config(page_title="Multilingual Chat", page_icon="🌍", layout="wide")

st.markdown("""
<style>
.ml-header { background: linear-gradient(135deg, #a18cd1 0%, #fbc2eb 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; }
.ml-header h1 { color: white; margin: 0; }
.ml-header p { color: rgba(255,255,255,0.85); }
.lang-card { display: inline-flex; align-items: center; gap: 0.5rem; background: rgba(161,140,209,0.15); padding: 0.5rem 1rem; border-radius: 12px; margin: 0.3rem; font-size: 0.9rem; }
.lang-flag { font-size: 1.3rem; }
.translation-box { background: rgba(255,255,255,0.05); border: 1px solid rgba(161,140,209,0.3); padding: 0.8rem; border-radius: 10px; margin: 0.5rem 0; font-size: 0.85rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="ml-header">
    <h1>🌍 Multilingual Chatbot</h1>
    <p>Chat in any of 8 supported languages. Auto-detection, seamless translation, and culturally adapted responses.</p>
</div>
""", unsafe_allow_html=True)

# ── Initialize ──
if "ml_engine" not in st.session_state:
    st.session_state.ml_engine = MultilingualEngine()
if "ml_messages" not in st.session_state:
    st.session_state.ml_messages = []

engine = st.session_state.ml_engine

# ── Sidebar ──
with st.sidebar:
    st.header("🌐 Language Settings")

    response_mode = st.radio("Response Language", ["Auto (match input)", "Manual selection"])
    selected_lang = None
    if response_mode == "Manual selection":
        langs = config.SUPPORTED_LANGUAGES
        options = {f"{v['flag']} {v['name']}": k for k, v in langs.items()}
        choice = st.selectbox("Select language", list(options.keys()))
        selected_lang = options[choice]

    st.divider()
    st.header("🗣️ Supported Languages")
    for code, info in config.SUPPORTED_LANGUAGES.items():
        st.markdown(f'<div class="lang-card"><span class="lang-flag">{info["flag"]}</span> {info["name"]} <span style="color:#888;font-size:0.75rem">({code})</span></div>', unsafe_allow_html=True)

    st.divider()
    st.header("💡 Try These")
    st.caption("• Hello, how are you?")
    st.caption("• ¿Cómo estás hoy?")
    st.caption("• Bonjour, comment allez-vous?")
    st.caption("• आप कैसे हैं?")
    st.caption("• こんにちは、元気ですか？")
    st.caption("• 你好，你好吗？")

    st.divider()
    if st.button("🧹 Clear Chat"):
        st.session_state.ml_messages = []
        engine.clear_history()
        st.rerun()

# ── Chat Interface ──
for msg in st.session_state.ml_messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("detected"):
            d = msg["detected"]
            st.caption(f"{d['flag']} Detected: {d['name']}")
        if msg.get("translated"):
            st.markdown(f'<div class="translation-box">🔄 <strong>Translation:</strong> {msg["translated"]}</div>', unsafe_allow_html=True)

if prompt := st.chat_input("Type in any language..."):
    # Show user message with detection
    st.session_state.ml_messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process
    with st.chat_message("assistant"):
        with st.spinner("Processing..."):
            result = engine.process_multilingual_query(prompt, response_lang=selected_lang)

        # Show detection info
        d = result["detected"]
        st.caption(f"{d['flag']} Input detected as: **{d['name']}**")

        # Show translation if input was non-English
        if result.get("translated_input"):
            st.markdown(f'<div class="translation-box">🔄 <strong>English translation:</strong> {result["translated_input"]}</div>', unsafe_allow_html=True)

        # Show response
        st.markdown(result["response"])

        # Show cultural context
        culture = result.get("cultural_context", {})
        if culture:
            with st.expander("🌐 Cultural Context"):
                st.write(f"**Style:** {culture.get('style', 'N/A')}")
                st.write(f"**Greeting:** {culture.get('greeting', 'N/A')}")
                st.write(f"**Response Language:** {config.SUPPORTED_LANGUAGES.get(result['response_language'], {}).get('name', result['response_language'])}")

    st.session_state.ml_messages.append({
        "role": "assistant",
        "content": result["response"],
        "detected": result["detected"],
        "translated": result.get("translated_input"),
    })
