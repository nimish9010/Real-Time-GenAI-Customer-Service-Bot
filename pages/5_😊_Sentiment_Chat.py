"""
Page 5: Sentiment-Aware Chat — Real-time sentiment detection with adaptive responses.
"""

import streamlit as st
import sys
from pathlib import Path
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).parent.parent))
from modules.sentiment import SentimentAnalyzer

st.set_page_config(page_title="Sentiment Chat", page_icon="😊", layout="wide")

st.markdown("""
<style>
.sent-header { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 2rem; }
.sent-header h1 { color: white; margin: 0; }
.sent-header p { color: rgba(255,255,255,0.85); }
.sentiment-badge { display: inline-block; padding: 0.3rem 0.8rem; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }
.gauge-container { text-align: center; padding: 1rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="sent-header">
    <h1>😊 Sentiment-Aware Chatbot</h1>
    <p>Chat naturally — the AI detects your emotional tone and adapts its responses accordingly.</p>
</div>
""", unsafe_allow_html=True)

# ── Initialize ──
if "sent_analyzer" not in st.session_state:
    st.session_state.sent_analyzer = SentimentAnalyzer()
if "sent_messages" not in st.session_state:
    st.session_state.sent_messages = []
if "adapt_tone" not in st.session_state:
    st.session_state.adapt_tone = True

analyzer = st.session_state.sent_analyzer

# ── Sidebar ──
with st.sidebar:
    st.header("⚙️ Settings")
    st.session_state.adapt_tone = st.toggle("🎭 Adaptive Tone", value=st.session_state.adapt_tone)
    st.caption("When enabled, the AI adjusts its tone based on your detected sentiment.")

    st.divider()
    st.header("📊 Sentiment Analytics")

    summary = analyzer.get_sentiment_summary()
    if summary["count"] > 0:
        avg = summary["avg_compound"]
        label = "Positive" if avg > 0.05 else "Negative" if avg < -0.05 else "Neutral"

        # Gauge chart
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number", value=avg,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Average Sentiment", "font": {"color": "white"}},
            gauge={
                "axis": {"range": [-1, 1], "tickcolor": "white"},
                "bar": {"color": "#667eea"},
                "bgcolor": "#1a1a2e",
                "steps": [
                    {"range": [-1, -0.3], "color": "rgba(231,76,60,0.3)"},
                    {"range": [-0.3, 0.3], "color": "rgba(149,165,166,0.3)"},
                    {"range": [0.3, 1], "color": "rgba(46,204,113,0.3)"},
                ],
            },
            number={"font": {"color": "white"}},
        ))
        fig_gauge.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", font={"color": "white"}, height=200, margin=dict(t=50, b=0, l=30, r=30)
        )
        st.plotly_chart(fig_gauge, use_container_width=True)

        st.metric("Messages Analyzed", summary["count"])
        st.metric("Mood Trend", summary["trend"].capitalize())

        # Distribution
        if summary["distribution"]:
            st.subheader("Distribution")
            for label_name, count in summary["distribution"].items():
                pct = count / summary["count"] * 100
                st.progress(pct / 100, text=f"{label_name}: {count} ({pct:.0f}%)")
    else:
        st.info("Start chatting to see analytics")

    st.divider()
    if st.button("🧹 Clear All"):
        st.session_state.sent_messages = []
        analyzer.clear_history()
        st.rerun()

# ── Main Content ──
col_chat, col_analysis = st.columns([3, 1])

with col_chat:
    # Chat messages
    for msg in st.session_state.sent_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("sentiment"):
                s = msg["sentiment"]
                st.caption(f"{s['emoji']} {s['label']} (score: {s['compound']:.2f})")

    if prompt := st.chat_input("Type a message..."):
        st.session_state.sent_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Analyze and respond
        with st.chat_message("assistant"):
            with st.spinner("Analyzing sentiment & generating response..."):
                result = analyzer.generate_adaptive_response(prompt, st.session_state.adapt_tone)
            st.markdown(result["response"])
            s = result["sentiment"]
            st.caption(f"Detected: {s['emoji']} {s['label']} (score: {s['compound']:.2f})")

        st.session_state.sent_messages.append({
            "role": "user_sentiment", "content": prompt, "sentiment": result["sentiment"]
        })
        st.session_state.sent_messages.append({"role": "assistant", "content": result["response"]})
        st.rerun()

with col_analysis:
    st.subheader("📈 Sentiment Timeline")
    if analyzer.sentiment_history:
        compounds = [s["sentiment"]["compound"] for s in analyzer.sentiment_history]
        labels = [s["sentiment"]["label"] for s in analyzer.sentiment_history]
        colors = [s["sentiment"]["color"] for s in analyzer.sentiment_history]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            y=compounds, mode="lines+markers",
            line=dict(color="#667eea", width=2),
            marker=dict(color=colors, size=10, line=dict(width=1, color="white")),
            hovertext=[f"{l}: {c:.2f}" for l, c in zip(labels, compounds)],
        ))
        fig.add_hline(y=0, line_dash="dash", line_color="gray", opacity=0.5)
        fig.update_layout(
            template="plotly_dark", height=300, margin=dict(t=10, b=30, l=30, r=10),
            yaxis=dict(range=[-1.1, 1.1], title="Score"), xaxis=dict(title="Message #"),
            showlegend=False,
        )
        st.plotly_chart(fig, use_container_width=True)

        # Latest sentiment detail
        latest = analyzer.sentiment_history[-1]["sentiment"]
        st.markdown(f"### {latest['emoji']} {latest['label']}")
        mcol1, mcol2, mcol3 = st.columns(3)
        mcol1.metric("Positive", f"{latest['positive']:.0%}")
        mcol2.metric("Neutral", f"{latest['neutral']:.0%}")
        mcol3.metric("Negative", f"{latest['negative']:.0%}")
    else:
        st.info("Sentiment data will appear here as you chat.")
