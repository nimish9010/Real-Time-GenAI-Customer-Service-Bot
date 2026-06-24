"""
modules/knowledge_base.py — Task 1: Dynamic Knowledge Base Expansion.
Manages document ingestion, periodic updates, and RAG-based querying.
"""

import time
import requests
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

import google.generativeai as genai
import config
from modules.vector_store import VectorStore
from utils.helpers import chunk_text, clean_text, generate_doc_id


class KnowledgeBaseManager:
    """Manages a dynamically expanding knowledge base with ChromaDB + Gemini."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.collection_name = config.COLLECTION_KNOWLEDGE_BASE
        self._configure_genai()

    def _configure_genai(self):
        """Configure Google Generative AI with dynamic session configurations."""
        import os
        api_key = os.environ.get("GOOGLE_API_KEY", config.GOOGLE_API_KEY)
        if api_key:
            genai.configure(api_key=api_key)
            
            # Read dynamic configurations from Streamlit session state if available
            model_name = config.GEMINI_TEXT_MODEL
            generation_config = None
            
            try:
                import streamlit as st
                if "gemini_model" in st.session_state:
                    model_name = st.session_state.gemini_model
                if "gemini_temp" in st.session_state or "gemini_max_tokens" in st.session_state:
                    generation_config = {
                        "temperature": st.session_state.get("gemini_temp", 0.7),
                        "max_output_tokens": st.session_state.get("gemini_max_tokens", 2048),
                    }
            except Exception:
                pass
                
            self.model = genai.GenerativeModel(model_name, generation_config=generation_config)
        else:
            self.model = None

    def add_from_text(self, text: str, source: str = "manual_input") -> int:
        """Add plain text content to the knowledge base."""
        cleaned = clean_text(text)
        chunks = chunk_text(cleaned, chunk_size=300, overlap=30)
        if not chunks:
            return 0

        ids = [generate_doc_id(chunk, source) for chunk in chunks]
        metadatas = [
            {"source": source, "added_at": str(int(time.time())), "type": "text"}
            for _ in chunks
        ]
        return self.vector_store.add_documents(
            self.collection_name, documents=chunks, metadatas=metadatas, ids=ids
        )

    def add_from_url(self, url: str) -> Dict[str, Any]:
        """Scrape a URL and add its content to the knowledge base."""
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; KnowledgeBot/1.0)"}
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()

            text = soup.get_text(separator="\n", strip=True)
            title = soup.title.string if soup.title else url

            if len(text) < 50:
                return {"success": False, "error": "Page has too little content", "added": 0}

            added = self.add_from_text(text, source=url)
            return {"success": True, "title": title, "added": added, "chars": len(text)}

        except Exception as e:
            return {"success": False, "error": str(e), "added": 0}

    def add_from_file(self, file_content: str, filename: str) -> int:
        """Add content from an uploaded file."""
        return self.add_from_text(file_content, source=filename)

    def query(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """RAG query: retrieve relevant context, then generate answer with Gemini."""
        # Retrieve relevant documents
        results = self.vector_store.query(self.collection_name, question, n_results=top_k)

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        if not documents:
            return {
                "answer": "I don't have enough information in my knowledge base to answer that question. "
                          "Try adding more documents or URLs to expand my knowledge!",
                "sources": [],
                "context_used": False,
            }

        # Build context from retrieved documents
        context_parts = []
        sources = []
        for doc, meta in zip(documents, metadatas):
            context_parts.append(doc)
            sources.append(meta.get("source", "Unknown"))

        context = "\n\n---\n\n".join(context_parts)

        # Generate answer using Gemini
        self._configure_genai()
        if not self.model:
            return {
                "answer": "⚠️ Google API key not configured. Please set GOOGLE_API_KEY in your .env file.",
                "sources": sources,
                "context_used": True,
            }

        prompt = f"""Based on the following context from my knowledge base, answer the user's question.
If the context doesn't contain enough information, say so honestly.
Always be helpful and provide a comprehensive answer.

CONTEXT:
{context}

USER QUESTION: {question}

ANSWER:"""

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            answer = f"Error generating response: {str(e)}"

        return {
            "answer": answer,
            "sources": list(set(sources)),
            "context_used": True,
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get knowledge base statistics."""
        return self.vector_store.get_collection_stats(self.collection_name)

    def clear(self) -> bool:
        """Clear the entire knowledge base."""
        return self.vector_store.delete_collection(self.collection_name)

    def check_update_needed(self, sources: List[str], last_update: float, interval_hours: float) -> bool:
        """Check if periodic update is needed based on interval."""
        elapsed = time.time() - last_update
        return elapsed >= (interval_hours * 3600)

    def periodic_update(self, urls: List[str]) -> Dict[str, Any]:
        """Run periodic update by re-scraping configured URLs."""
        results = {"total_added": 0, "successes": 0, "failures": 0, "details": []}
        for url in urls:
            result = self.add_from_url(url)
            if result["success"]:
                results["successes"] += 1
                results["total_added"] += result["added"]
            else:
                results["failures"] += 1
            results["details"].append({"url": url, **result})
        return results
