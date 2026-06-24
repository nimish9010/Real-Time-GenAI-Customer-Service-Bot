"""
Page 2: Multi-Modal Chatbot — Chat with text and images using Gemini Vision.
"""

import streamlit as st
import sys
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.multimodal import MultiModalChat

st.set_page_config(page_title="Multi-Modal Chat", page_icon="🖼️", layout="wide")

st.markdown("""
<style>
.mm-header { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; }
.mm-header h1 { color: white; margin: 0; }
.mm-header p { color: rgba(255,255,255,0.85); margin: 0.5rem 0 0 0; }
.image-badge { display: inline-block; background: rgba(240,147,251,0.15); color: #f093fb; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.75rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="mm-header">
    <h1>🖼️ Multi-Modal Chatbot</h1>
    <p>Chat with text and images. Upload images for AI-powered visual analysis using Google Gemini.</p>
</div>
""", unsafe_allow_html=True)

# ── Initialize ──
if "mm_chat" not in st.session_state:
    st.session_state.mm_chat = MultiModalChat()
if "mm_messages" not in st.session_state:
    st.session_state.mm_messages = []
if "mm_current_image" not in st.session_state:
    st.session_state.mm_current_image = None

chat = st.session_state.mm_chat

# ── Sidebar ──
with st.sidebar:
    st.header("🖼️ Image Input")

    upload_tab, camera_tab = st.tabs(["📁 Upload", "📷 Camera"])

    with upload_tab:
        uploaded_file = st.file_uploader("Upload an image", type=["png", "jpg", "jpeg", "gif", "webp"])
        if uploaded_file:
            image = Image.open(uploaded_file)
            st.session_state.mm_current_image = image
            st.image(image, caption="Uploaded Image", use_container_width=True)

    with camera_tab:
        camera_photo = st.camera_input("Take a photo")
        if camera_photo:
            image = Image.open(camera_photo)
            st.session_state.mm_current_image = image

    if st.session_state.mm_current_image:
        st.success("✅ Image ready for analysis")
        if st.button("🗑️ Remove Image"):
            st.session_state.mm_current_image = None
            st.rerun()

    st.divider()

    if st.button("🧹 Clear Conversation"):
        st.session_state.mm_messages = []
        st.session_state.mm_current_image = None
        chat.clear_history()
        st.rerun()

    st.markdown("### 💡 Try asking:")
    st.caption("• 'What's in this image?'")
    st.caption("• 'Describe the colors and mood'")
    st.caption("• 'What text do you see?'")
    st.caption("• 'Compare this with...'")

# ── Chat Area ──
for msg in st.session_state.mm_messages:
    with st.chat_message(msg["role"]):
        if msg.get("image"):
            st.image(msg["image"], width=300)
        st.markdown(msg["content"])

if prompt := st.chat_input("Type a message or ask about an image..."):
    has_image = st.session_state.mm_current_image is not None

    # Show user message
    with st.chat_message("user"):
        if has_image:
            st.image(st.session_state.mm_current_image, width=200)
            st.markdown(f"{prompt} 📷")
        else:
            st.markdown(prompt)

    user_msg = {"role": "user", "content": prompt}
    if has_image:
        user_msg["image"] = st.session_state.mm_current_image
    st.session_state.mm_messages.append(user_msg)

    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing..." if has_image else "Thinking..."):
            if has_image:
                response = chat.chat_with_image(st.session_state.mm_current_image, prompt)
                st.session_state.mm_current_image = None  # Clear after use
            else:
                response = chat.generate_response(prompt)
        st.markdown(response)

    st.session_state.mm_messages.append({"role": "assistant", "content": response})
