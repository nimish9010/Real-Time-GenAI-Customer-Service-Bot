"""
modules/research_expert.py -- Task 4: arXiv Domain Expert Chatbot.
Handles paper loading, indexing, semantic search, summarization, and concept explanation.
"""

import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

import google.generativeai as genai
import config
from modules.vector_store import VectorStore
from utils.helpers import chunk_text, clean_text, generate_doc_id, extract_keywords


# arXiv CS category mappings
ARXIV_CATEGORIES = {
    "cs.AI": "Artificial Intelligence",
    "cs.CL": "Computation and Language (NLP)",
    "cs.CV": "Computer Vision",
    "cs.LG": "Machine Learning",
    "cs.DS": "Data Structures and Algorithms",
    "cs.CR": "Cryptography and Security",
    "cs.DB": "Databases",
    "cs.DC": "Distributed Computing",
    "cs.HC": "Human-Computer Interaction",
    "cs.IR": "Information Retrieval",
    "cs.IT": "Information Theory",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.NI": "Networking",
    "cs.PL": "Programming Languages",
    "cs.RO": "Robotics",
    "cs.SE": "Software Engineering",
    "cs.SI": "Social and Information Networks",
    "physics": "Physics",
    "math": "Mathematics",
    "stat": "Statistics",
    "econ": "Economics",
    "q-bio": "Quantitative Biology",
}


class ResearchExpert:
    """Domain expert chatbot for scientific research papers."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.collection_name = config.COLLECTION_ARXIV
        self._configure_genai()
        self.papers = []
        self.conversation_history = []

    def _configure_genai(self):
        """Configure Google Generative AI with dynamic configurations."""
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

    def load_sample_data(self):
        """Load built-in sample arXiv data."""
        sample_path = config.ARXIV_DATA_DIR / "sample_arxiv.json"
        if sample_path.exists():
            with open(sample_path, "r", encoding="utf-8") as f:
                self.papers = json.load(f)
            return len(self.papers)
        return 0

    def load_arxiv_data(self, file_path: str, category_filter: str = None, max_papers: int = 1000):
        """Load arXiv data from JSONL file with optional category filtering."""
        papers = []
        path = Path(file_path)

        if not path.exists():
            return 0

        try:
            with open(path, "r", encoding="utf-8") as f:
                for line in f:
                    if len(papers) >= max_papers:
                        break
                    try:
                        paper = json.loads(line.strip())
                        if category_filter:
                            categories = paper.get("categories", "")
                            if category_filter.lower() not in categories.lower():
                                continue
                        papers.append({
                            "id": paper.get("id", ""),
                            "title": clean_text(paper.get("title", "")),
                            "abstract": clean_text(paper.get("abstract", "")),
                            "authors": paper.get("authors", ""),
                            "categories": paper.get("categories", ""),
                            "doi": paper.get("doi", ""),
                            "journal_ref": paper.get("journal-ref", ""),
                            "update_date": paper.get("update_date", ""),
                        })
                    except json.JSONDecodeError:
                        continue
        except Exception:
            return 0

        self.papers = papers
        return len(papers)

    def build_index(self):
        """Index all loaded papers into ChromaDB."""
        if not self.papers:
            return 0

        documents = []
        metadatas = []
        ids = []

        for paper in self.papers:
            doc = f"Title: {paper['title']}\n\nAbstract: {paper['abstract']}"
            documents.append(doc)
            metadatas.append({
                "arxiv_id": paper.get("id", ""),
                "title": paper["title"][:200],
                "authors": str(paper.get("authors", ""))[:200],
                "categories": paper.get("categories", ""),
                "doi": paper.get("doi", ""),
                "update_date": paper.get("update_date", ""),
            })
            ids.append(generate_doc_id(doc, f"arxiv_{paper.get('id', '')}"))

        return self.vector_store.add_documents(
            self.collection_name, documents=documents, metadatas=metadatas, ids=ids
        )

    def search_papers(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Semantic search across indexed papers."""
        results = self.vector_store.query(self.collection_name, query, n_results=top_k)

        papers = []
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(documents, metadatas, distances):
            relevance = max(0, (1 - dist)) * 100
            papers.append({
                "content": doc,
                "title": meta.get("title", "Unknown"),
                "authors": meta.get("authors", ""),
                "categories": meta.get("categories", ""),
                "arxiv_id": meta.get("arxiv_id", ""),
                "relevance": relevance,
            })

        return papers

    def summarize_paper(self, paper_content: str) -> str:
        """Generate a structured summary of a paper using Gemini."""
        self._configure_genai()
        if not self.model:
            return "API key not configured."

        prompt = f"""Provide a structured summary of this research paper. Include:

1. **Main Objective**: What problem does this paper address?
2. **Methodology**: What approach or methods are used?
3. **Key Findings**: What are the main results?
4. **Significance**: Why is this work important?
5. **Key Terms**: List 5 important technical terms from the paper.

PAPER:
{paper_content}

STRUCTURED SUMMARY:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def explain_concept(self, concept: str, context: str = "") -> str:
        """Explain a scientific concept, optionally using paper context."""
        self._configure_genai()
        if not self.model:
            return "API key not configured."

        # Search for related papers for context
        if not context:
            results = self.search_papers(concept, top_k=3)
            if results:
                context = "\n\n".join([r["content"] for r in results[:3]])

        context_section = f"RESEARCH CONTEXT:\n{context}\n" if context else ""

        prompt = f"""You are an expert research assistant. Explain the following concept
in a clear, comprehensive way suitable for a graduate student.

Use the provided research context to ground your explanation with specific examples.
Include:
1. A clear definition
2. How it works (mechanism/process)
3. Real-world applications
4. Related concepts

{context_section}

CONCEPT TO EXPLAIN: {concept}

EXPLANATION:"""

        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error: {str(e)}"

    def expert_chat(self, question: str) -> str:
        """Handle expert-level questions with follow-up support."""
        self._configure_genai()
        if not self.model:
            return "API key not configured."

        # Search for relevant papers
        results = self.search_papers(question, top_k=5)
        context = ""
        sources = []
        if results:
            context = "\n\n---\n\n".join([r["content"] for r in results[:3]])
            sources = [r["title"] for r in results[:3]]

        # Build conversation context
        history = ""
        if self.conversation_history:
            recent = self.conversation_history[-4:]
            parts = [f"{'User' if m['role'] == 'user' else 'Expert'}: {m['text']}" for m in recent]
            history = "\n".join(parts)

        history_section = f"CONVERSATION HISTORY:\n{history}\n" if history else ""
        papers_section = f"RELEVANT RESEARCH PAPERS:\n{context}\n" if context else ""
        refs = json.dumps(sources) if sources else "None found"

        prompt = f"""You are a domain expert in scientific research. Answer the user's question
using the provided research papers as context. Be thorough, accurate, and cite specific papers
when relevant.

If this is a follow-up question, use the conversation history to maintain context.

{history_section}

{papers_section}

REFERENCED PAPERS: {refs}

USER QUESTION: {question}

EXPERT ANSWER:"""

        try:
            response = self.model.generate_content(prompt)
            answer = response.text

            self.conversation_history.append({"role": "user", "text": question})
            self.conversation_history.append({"role": "assistant", "text": answer})

            return answer
        except Exception as e:
            return f"Error: {str(e)}"

    def get_category_distribution(self) -> Dict[str, int]:
        """Get distribution of paper categories."""
        dist = {}
        for paper in self.papers:
            cats = paper.get("categories", "").split()
            for cat in cats:
                cat = cat.strip()
                if cat:
                    dist[cat] = dist.get(cat, 0) + 1
        return dict(sorted(dist.items(), key=lambda x: x[1], reverse=True)[:20])

    def get_all_keywords(self, top_n: int = 50) -> Dict[str, int]:
        """Extract top keywords across all papers."""
        all_text = " ".join([p.get("abstract", "") for p in self.papers])
        keywords = extract_keywords(all_text, top_n=top_n)
        freq = {}
        text_lower = all_text.lower()
        for kw in keywords:
            freq[kw] = text_lower.count(kw)
        return freq

    def get_stats(self):
        stats = self.vector_store.get_collection_stats(self.collection_name)
        stats["loaded_papers"] = len(self.papers)
        return stats

    def clear_history(self):
        self.conversation_history = []
