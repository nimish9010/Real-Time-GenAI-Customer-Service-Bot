"""
modules/sentiment.py -- Task 5: Sentiment Analysis Integration.
"""

from typing import Dict, Any, List
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import google.generativeai as genai
import config


class SentimentAnalyzer:
    def __init__(self):
        self.analyzer = SentimentIntensityAnalyzer()
        self._configure_genai()
        self.sentiment_history = []
        self.conversation_history = []

    def _configure_genai(self):
        import os
        api_key = os.environ.get("GOOGLE_API_KEY", config.GOOGLE_API_KEY)
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(config.GEMINI_TEXT_MODEL)
        else:
            self.model = None

    def analyze(self, text: str) -> Dict[str, Any]:
        scores = self.analyzer.polarity_scores(text)
        compound = scores["compound"]
        label = self._get_label(compound)
        emoji_map = {"Very Negative":"😢","Negative":"😟","Slightly Negative":"😕","Neutral":"😐","Slightly Positive":"🙂","Positive":"😊","Very Positive":"😄"}
        color_map = {"Very Negative":"#e74c3c","Negative":"#e67e22","Slightly Negative":"#f39c12","Neutral":"#95a5a6","Slightly Positive":"#2ecc71","Positive":"#27ae60","Very Positive":"#1abc9c"}
        result = {"compound": compound, "positive": scores["pos"], "negative": scores["neg"], "neutral": scores["neu"], "label": label, "emoji": emoji_map.get(label,"😐"), "color": color_map.get(label,"#95a5a6"), "confidence": abs(compound)}
        self.sentiment_history.append({"text": text[:100], "sentiment": result.copy(), "index": len(self.sentiment_history)})
        return result

    def _get_label(self, compound: float) -> str:
        t = config.SENTIMENT_THRESHOLDS
        if compound <= t["very_negative"]: return "Very Negative"
        elif compound <= t["negative"]: return "Negative"
        elif compound <= t["neutral_low"]: return "Slightly Negative"
        elif compound <= t["neutral_high"]: return "Neutral"
        elif compound <= t["positive"]: return "Slightly Positive"
        elif compound <= t["very_positive"]: return "Positive"
        else: return "Very Positive"

    def get_empathetic_prefix(self, sentiment: Dict) -> str:
        prefixes = {"Very Negative":"I can sense you're going through a tough time. ","Negative":"I understand this might be frustrating. ","Slightly Negative":"I hear your concern. ","Neutral":"","Slightly Positive":"","Positive":"Great to hear from you! ","Very Positive":"I love your enthusiasm! "}
        return prefixes.get(sentiment["label"], "")

    def get_tone_instruction(self, sentiment: Dict) -> str:
        instructions = {"Very Negative":"Be extra empathetic, patient, and supportive.","Negative":"Be understanding and solution-focused.","Slightly Negative":"Be reassuring and helpful.","Neutral":"Be friendly and informative.","Slightly Positive":"Be friendly and engaging.","Positive":"Match their positive energy.","Very Positive":"Be enthusiastic and celebrate with them."}
        return instructions.get(sentiment["label"], "Be friendly and helpful.")

    def generate_adaptive_response(self, user_message: str, adapt_tone: bool = True) -> Dict:
        sentiment = self.analyze(user_message)
        self._configure_genai()
        if not self.model:
            return {"response": "API key not configured.", "sentiment": sentiment}
        history = ""
        if self.conversation_history:
            recent = self.conversation_history[-6:]
            history = "\n".join([f"{'User' if m['role']=='user' else 'Assistant'}: {m['text']}" for m in recent])
        tone = self.get_tone_instruction(sentiment) if adapt_tone else "Be friendly."
        prefix = self.get_empathetic_prefix(sentiment) if adapt_tone else ""
        prompt = f"You are a helpful, emotionally intelligent AI assistant.\nTONE: {tone}\nSENTIMENT: {sentiment['label']}\n"
        if history:
            prompt += f"HISTORY:\n{history}\n"
        prompt += f"USER: {user_message}\nRESPONSE:"
        try:
            response = self.model.generate_content(prompt)
            answer = prefix + response.text
            self.conversation_history.append({"role":"user","text":user_message})
            self.conversation_history.append({"role":"assistant","text":answer})
            return {"response": answer, "sentiment": sentiment}
        except Exception as e:
            return {"response": f"Error: {str(e)}", "sentiment": sentiment}

    def get_sentiment_summary(self) -> Dict:
        if not self.sentiment_history:
            return {"count":0,"avg_compound":0,"distribution":{}}
        compounds = [s["sentiment"]["compound"] for s in self.sentiment_history]
        labels = [s["sentiment"]["label"] for s in self.sentiment_history]
        dist = {}
        for l in labels: dist[l] = dist.get(l,0)+1
        trend = "improving" if len(compounds)>2 and compounds[-1]>compounds[0] else "declining" if len(compounds)>2 and compounds[-1]<compounds[0] else "stable"
        return {"count":len(self.sentiment_history),"avg_compound":sum(compounds)/len(compounds),"min_compound":min(compounds),"max_compound":max(compounds),"distribution":dist,"trend":trend}

    def clear_history(self):
        self.sentiment_history = []
        self.conversation_history = []
