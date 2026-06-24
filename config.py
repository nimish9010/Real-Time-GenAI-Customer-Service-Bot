"""
config.py — Central configuration for the AI Chatbot Suite.
Loads environment variables and defines shared constants.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ───────────────────────────────────────────────────────────────
load_dotenv()

# ── API Keys ────────────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ── Paths ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
MEDICAL_DATA_DIR = DATA_DIR / "medical"
ARXIV_DATA_DIR = DATA_DIR / "arxiv"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
MEDICAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
ARXIV_DATA_DIR.mkdir(parents=True, exist_ok=True)
CHROMA_DB_DIR.mkdir(exist_ok=True)

# ── Gemini Models ───────────────────────────────────────────────────────────
GEMINI_TEXT_MODEL = "gemini-flash-latest"
GEMINI_VISION_MODEL = "gemini-flash-latest"
GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"

# ── ChromaDB Collections ───────────────────────────────────────────────────
COLLECTION_KNOWLEDGE_BASE = "knowledge_base"
COLLECTION_MEDICAL = "medical_qa"
COLLECTION_ARXIV = "arxiv_papers"

# ── Supported Languages ────────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "en": {"name": "English",  "flag": "🇺🇸", "greeting": "Hello!", "formality": "casual"},
    "es": {"name": "Spanish",  "flag": "🇪🇸", "greeting": "¡Hola!", "formality": "formal"},
    "fr": {"name": "French",   "flag": "🇫🇷", "greeting": "Bonjour!", "formality": "formal"},
    "de": {"name": "German",   "flag": "🇩🇪", "greeting": "Hallo!", "formality": "formal"},
    "hi": {"name": "Hindi",    "flag": "🇮🇳", "greeting": "नमस्ते!", "formality": "respectful"},
    "ja": {"name": "Japanese", "flag": "🇯🇵", "greeting": "こんにちは!", "formality": "very_formal"},
    "zh": {"name": "Chinese",  "flag": "🇨🇳", "greeting": "你好!", "formality": "respectful"},
    "ar": {"name": "Arabic",   "flag": "🇸🇦", "greeting": "مرحبا!", "formality": "formal"},
}

# ── Sentiment Thresholds ────────────────────────────────────────────────────
SENTIMENT_THRESHOLDS = {
    "very_negative": -0.6,
    "negative": -0.2,
    "neutral_low": -0.05,
    "neutral_high": 0.05,
    "positive": 0.2,
    "very_positive": 0.6,
}
