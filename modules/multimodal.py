"""
modules/multimodal.py -- Task 2: Multi-Modal Chatbot.
Handles image understanding and text+image conversations via Google Gemini.
"""

from typing import List, Dict, Any, Optional
from PIL import Image

import google.generativeai as genai
import config


class MultiModalChat:
    """Multi-modal chatbot supporting text and image inputs via Gemini."""

    def __init__(self):
        self._configure_genai()
        self.conversation_history = []

    def _configure_genai(self):
        import os
        api_key = os.environ.get("GOOGLE_API_KEY", config.GOOGLE_API_KEY)
        if api_key:
            genai.configure(api_key=api_key)
            self.text_model = genai.GenerativeModel(config.GEMINI_TEXT_MODEL)
            self.vision_model = genai.GenerativeModel(config.GEMINI_VISION_MODEL)
        else:
            self.text_model = None
            self.vision_model = None

    def analyze_image(self, image, prompt=None):
        """Analyze an image with optional text prompt using Gemini Vision."""
        self._configure_genai()
        if not self.vision_model:
            return "API key not configured. Please set GOOGLE_API_KEY."

        if not prompt:
            prompt = (
                "Describe this image in detail. Include what you see, "
                "key objects or elements, colors and mood, any text visible, "
                "and the context or setting."
            )

        try:
            response = self.vision_model.generate_content([prompt, image])
            return response.text
        except Exception as e:
            return f"Error analyzing image: {str(e)}"

    def chat_with_image(self, image, prompt):
        """Send image + text prompt to Gemini for analysis."""
        self._configure_genai()
        if not self.vision_model:
            return "API key not configured. Please set GOOGLE_API_KEY."

        system_prompt = (
            "You are a helpful multi-modal AI assistant. Analyze the provided image "
            "in the context of the user's question. Be detailed and insightful."
        )

        try:
            full_prompt = f"{system_prompt}\n\nUser question: {prompt}"
            response = self.vision_model.generate_content([full_prompt, image])
            result = response.text

            self.conversation_history.append({"role": "user", "text": prompt, "has_image": True})
            self.conversation_history.append({"role": "assistant", "text": result, "has_image": False})

            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def generate_response(self, text):
        """Generate a text-only response using Gemini."""
        self._configure_genai()
        if not self.text_model:
            return "API key not configured. Please set GOOGLE_API_KEY."

        try:
            history_context = ""
            if self.conversation_history:
                recent = self.conversation_history[-6:]
                parts = []
                for msg in recent:
                    role = "User" if msg["role"] == "user" else "Assistant"
                    content = msg.get("text", "")
                    if msg.get("has_image"):
                        content += " [Image was shared]"
                    parts.append(f"{role}: {content}")
                history_context = "\n".join(parts)

            prompt_text = "You are a helpful multi-modal AI assistant.\n\n"
            if history_context:
                prompt_text += f"Previous conversation:\n{history_context}\n\n"
            prompt_text += f"User: {text}\n\nAssistant:"

            response = self.text_model.generate_content(prompt_text)
            result = response.text

            self.conversation_history.append({"role": "user", "text": text, "has_image": False})
            self.conversation_history.append({"role": "assistant", "text": result, "has_image": False})

            return result
        except Exception as e:
            return f"Error: {str(e)}"

    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
