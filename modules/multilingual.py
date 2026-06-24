"""
modules/multilingual.py -- Task 6: Multi-language Support.
Language detection, translation, and culturally appropriate responses.
"""

from typing import Dict, Any, Optional
from langdetect import detect, DetectorFactory
from deep_translator import GoogleTranslator
import google.generativeai as genai
import config

# Make langdetect deterministic
DetectorFactory.seed = 0


class MultilingualEngine:
    """Multilingual chatbot engine with auto-detection and cultural adaptation."""

    def __init__(self):
        self._configure_genai()
        self.conversation_history = []
        self.current_language = "en"

    def _configure_genai(self):
        import os
        api_key = os.environ.get("GOOGLE_API_KEY", config.GOOGLE_API_KEY)
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.GEMINI_TEXT_MODEL)
        else:
            self.model = None

    def detect_language(self, text: str) -> Dict[str, Any]:
        """Auto-detect the language of input text."""
        try:
            code = detect(text)
            lang_info = config.SUPPORTED_LANGUAGES.get(code, {
                "name": code.upper(), "flag": "🌐", "greeting": "Hello!", "formality": "casual"
            })
            return {"code": code, "name": lang_info["name"], "flag": lang_info["flag"],
                    "supported": code in config.SUPPORTED_LANGUAGES}
        except Exception:
            return {"code": "en", "name": "English", "flag": "🇺🇸", "supported": True}

    def translate(self, text: str, source: str = "auto", target: str = "en") -> str:
        """Translate text between languages."""
        if source == target:
            return text
        try:
            translator = GoogleTranslator(source=source, target=target)
            return translator.translate(text)
        except Exception:
            return text

    def get_cultural_context(self, lang_code: str) -> Dict[str, str]:
        """Get cultural norms for response adaptation."""
        contexts = {
            "en": {"greeting": "Hello!", "closing": "Have a great day!", "style": "Direct and friendly"},
            "es": {"greeting": "¡Hola!", "closing": "¡Que tengas un buen día!", "style": "Warm and personal"},
            "fr": {"greeting": "Bonjour!", "closing": "Bonne journée!", "style": "Polite and formal"},
            "de": {"greeting": "Hallo!", "closing": "Einen schönen Tag noch!", "style": "Precise and structured"},
            "hi": {"greeting": "नमस्ते!", "closing": "धन्यवाद!", "style": "Respectful, use honorifics"},
            "ja": {"greeting": "こんにちは!", "closing": "よろしくお願いします!", "style": "Very polite, formal"},
            "zh": {"greeting": "你好!", "closing": "谢谢!", "style": "Respectful and concise"},
            "ar": {"greeting": "مرحبا!", "closing": "مع السلامة!", "style": "Formal and respectful"},
        }
        return contexts.get(lang_code, contexts["en"])

    def process_multilingual_query(self, text: str, response_lang: str = None) -> Dict[str, Any]:
        """Full pipeline: detect -> translate -> respond -> translate back."""
        # Detect input language
        detected = self.detect_language(text)
        input_lang = detected["code"]
        target_lang = response_lang or input_lang

        # Translate to English for processing (if not English)
        english_text = text
        if input_lang != "en":
            english_text = self.translate(text, source=input_lang, target="en")

        # Get cultural context for response language
        culture = self.get_cultural_context(target_lang)

        # Generate response in target language using Gemini
        self._configure_genai()
        if not self.model:
            return {"response": "API key not configured.", "detected": detected,
                    "translated_input": english_text, "response_language": target_lang}

        lang_name = config.SUPPORTED_LANGUAGES.get(target_lang, {}).get("name", target_lang)

        # Build conversation context
        history = ""
        if self.conversation_history:
            recent = self.conversation_history[-4:]
            nl = "\n"
            history = nl.join([f"{'User' if m['role']=='user' else 'Assistant'}: {m['text']}" for m in recent])

        history_section = f"Conversation history:\n{history}\n" if history else ""

        prompt = f"""You are a multilingual AI assistant. Respond in {lang_name}.

Cultural style: {culture['style']}
Response language: {lang_name}

{history_section}

User message (original: {detected['name']}): {english_text}

Respond directly in {lang_name}. Be culturally appropriate and natural:"""

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            answer = f"Error: {str(e)}"

        self.conversation_history.append({"role": "user", "text": english_text, "lang": input_lang})
        self.conversation_history.append({"role": "assistant", "text": answer, "lang": target_lang})
        self.current_language = target_lang

        return {
            "response": answer,
            "detected": detected,
            "translated_input": english_text if input_lang != "en" else None,
            "response_language": target_lang,
            "cultural_context": culture,
        }

    def get_supported_languages(self):
        return config.SUPPORTED_LANGUAGES

    def clear_history(self):
        self.conversation_history = []
