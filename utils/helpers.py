"""
utils/helpers.py — Shared utility functions for text processing, formatting, etc.
"""

import re
import hashlib
from typing import List, Dict, Any


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Split text into overlapping chunks for vector database ingestion."""
    if not text or not text.strip():
        return []

    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk.strip())
        start += chunk_size - overlap

    return chunks if chunks else [text.strip()]


def clean_text(text: str) -> str:
    """Remove HTML tags, LaTeX commands, and extra whitespace."""
    if not text:
        return ""
    # Remove HTML tags
    text = re.sub(r"<[^>]+>", " ", text)
    # Remove LaTeX commands (basic)
    text = re.sub(r"\\[a-zA-Z]+\{([^}]*)\}", r"\1", text)
    text = re.sub(r"\\[a-zA-Z]+", "", text)
    # Remove special characters but keep basic punctuation
    text = re.sub(r"[{}$^_~]", "", text)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def generate_doc_id(text: str, source: str = "") -> str:
    """Generate a deterministic document ID from content."""
    content = f"{source}:{text[:200]}"
    return hashlib.md5(content.encode()).hexdigest()


def format_sources(results: Dict[str, Any]) -> str:
    """Format ChromaDB query results into a readable source list."""
    if not results or not results.get("documents"):
        return "No sources found."

    sources = []
    documents = results["documents"][0] if results["documents"] else []
    metadatas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(documents)
    distances = results["distances"][0] if results.get("distances") else [0] * len(documents)

    for i, (doc, meta, dist) in enumerate(zip(documents, metadatas, distances)):
        source_name = meta.get("source", "Unknown")
        relevance = max(0, 1 - dist) * 100
        preview = doc[:150] + "..." if len(doc) > 150 else doc
        sources.append(f"**Source {i+1}** ({source_name}) — {relevance:.0f}% relevant\n> {preview}")

    return "\n\n".join(sources)


def truncate_text(text: str, max_length: int = 200) -> str:
    """Truncate text to max_length, adding ellipsis if truncated."""
    if not text:
        return ""
    if len(text) <= max_length:
        return text
    return text[:max_length].rsplit(" ", 1)[0] + "..."


def extract_keywords(text: str, top_n: int = 10) -> List[str]:
    """Extract simple keywords from text by frequency (stopword-filtered)."""
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
        "have", "has", "had", "do", "does", "did", "will", "would", "could",
        "should", "may", "might", "can", "shall", "to", "of", "in", "for",
        "on", "with", "at", "by", "from", "as", "into", "through", "during",
        "before", "after", "above", "below", "between", "and", "but", "or",
        "not", "no", "nor", "so", "yet", "both", "each", "few", "more",
        "most", "other", "some", "such", "than", "too", "very", "just",
        "about", "up", "out", "if", "then", "that", "this", "these", "those",
        "it", "its", "we", "our", "they", "their", "he", "she", "his", "her",
        "which", "what", "when", "where", "who", "whom", "how", "all", "also",
        "i", "me", "my", "you", "your", "us", "them",
    }

    words = re.findall(r"\b[a-zA-Z]{3,}\b", text.lower())
    filtered = [w for w in words if w not in stopwords]

    freq = {}
    for w in filtered:
        freq[w] = freq.get(w, 0) + 1

    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]
