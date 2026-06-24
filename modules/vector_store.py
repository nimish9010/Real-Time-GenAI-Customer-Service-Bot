"""
modules/vector_store.py — Pure-Python SQLite-based vector database replacement for ChromaDB.
Provides a unified interface for creating, querying, and managing collections using standard sqlite3
and Google Gemini Embedding API.
"""

import sqlite3
import json
import math
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import config


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot_product = sum(x * y for x, y in zip(v1, v2))
    norm_v1 = sum(x * x for x in v1)
    norm_v2 = sum(x * x for x in v2)
    if norm_v1 == 0.0 or norm_v2 == 0.0:
        return 0.0
    return dot_product / (math.sqrt(norm_v1) * math.sqrt(norm_v2))


class SQLiteCollection:
    """Mock/wrapper class resembling ChromaDB Collection for backward compatibility."""

    def __init__(self, name: str, db_path: str):
        self.name = name
        self.db_path = db_path

    def count(self) -> int:
        """Get the number of documents in this collection."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents WHERE collection_name = ?", (self.name,))
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception:
            return 0


class VectorStore:
    """Wrapper around SQLite for persistent pure-Python vector storage using Gemini embeddings."""

    def __init__(self, persist_directory: str = None):
        """Initialize SQLite database client and schema."""
        persist_dir = Path(persist_directory or config.CHROMA_DB_DIR)
        persist_dir.mkdir(parents=True, exist_ok=True)
        self._db_path = persist_dir / "vector_store.sqlite"
        
        # Initialize schema
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                name TEXT PRIMARY KEY,
                metadata TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id TEXT PRIMARY KEY,
                collection_name TEXT,
                document TEXT,
                metadata TEXT,
                embedding TEXT,
                FOREIGN KEY(collection_name) REFERENCES collections(name) ON DELETE CASCADE
            )
        """)
        conn.commit()
        conn.close()

    def get_embedding(self, text_or_list, task_type="retrieval_document") -> Any:
        """Generate embeddings using google.generativeai.
        Can accept a single string or list of strings.
        """
        import google.generativeai as genai
        import time

        # Configure API key dynamically
        api_key = os.environ.get("GOOGLE_API_KEY", config.GOOGLE_API_KEY)
        if not api_key:
            raise ValueError("Google API key is not configured. Set GOOGLE_API_KEY environment variable.")
        genai.configure(api_key=api_key)

        is_list = isinstance(text_or_list, list)
        texts = text_or_list if is_list else [text_or_list]

        # Clean text inputs
        cleaned_texts = []
        for text in texts:
            if not text or not isinstance(text, str):
                cleaned_texts.append(" ")
            else:
                cleaned_texts.append(text)

        embeddings = []
        chunk_size = 50
        for i in range(0, len(cleaned_texts), chunk_size):
            batch = cleaned_texts[i : i + chunk_size]
            for attempt in range(3):
                try:
                    response = genai.embed_content(
                        model=config.GEMINI_EMBEDDING_MODEL,
                        content=batch,
                        task_type=task_type
                    )
                    embeddings.extend(response.get("embedding", []))
                    break
                except Exception as e:
                    if attempt == 2:
                        print(f"Error calling Gemini Embedding API: {e}")
                        # Return zero vectors as a fallback to avoid completely failing
                        embeddings.extend([[0.0] * 768 for _ in batch])
                    else:
                        time.sleep(1.0)

        if is_list:
            return embeddings
        else:
            return embeddings[0]

    def get_or_create_collection(self, name: str, metadata: dict = None) -> SQLiteCollection:
        """Get an existing collection or create a new one."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM collections WHERE name = ?", (name,))
            row = cursor.fetchone()
            if not row:
                meta = metadata or {"description": f"Collection: {name}"}
                cursor.execute(
                    "INSERT INTO collections (name, metadata) VALUES (?, ?)",
                    (name, json.dumps(meta))
                )
                conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error in get_or_create_collection: {e}")

        return SQLiteCollection(name, str(self._db_path))

    def add_documents(
        self,
        collection_name: str,
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None,
    ) -> int:
        """Add documents to a collection. Returns number of documents added."""
        if not documents:
            return 0

        # Ensure collection exists
        self.get_or_create_collection(collection_name)

        # Generate IDs if not provided
        if ids is None:
            import hashlib
            ids = [
                hashlib.md5(f"{collection_name}:{i}:{doc[:100]}".encode()).hexdigest()
                for i, doc in enumerate(documents)
            ]

        # Ensure metadatas match documents length
        if metadatas is None:
            metadatas = [{"source": "unknown"} for _ in documents]

        # Generate embeddings using Google Gemini API
        embeddings = self.get_embedding(documents, task_type="retrieval_document")

        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        
        total_added = 0
        try:
            # Query existing IDs to prevent duplicate inserts
            cursor.execute("SELECT id FROM documents WHERE collection_name = ?", (collection_name,))
            existing_ids = {row[0] for row in cursor.fetchall()}
            
            for doc, did, meta, emb in zip(documents, ids, metadatas, embeddings):
                if did not in existing_ids:
                    # Clean metadata (ensure all values are serializable and non-nested)
                    clean_meta = {}
                    for k, v in meta.items():
                        if v is None:
                            clean_meta[k] = ""
                        elif isinstance(v, (list, dict)):
                            clean_meta[k] = str(v)
                        else:
                            clean_meta[k] = str(v)
                    
                    cursor.execute(
                        """
                        INSERT INTO documents (id, collection_name, document, metadata, embedding)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (did, collection_name, doc, json.dumps(clean_meta), json.dumps(emb))
                    )
                    total_added += 1
            conn.commit()
        except Exception as e:
            print(f"Error adding documents: {e}")
            conn.rollback()
        finally:
            conn.close()

        return total_added

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Query a collection for similar documents using cosine similarity."""
        try:
            # Check if collection exists
            collections = self.list_collections()
            if collection_name not in collections:
                return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

            # Get documents from SQLite
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, document, metadata, embedding FROM documents WHERE collection_name = ?",
                (collection_name,)
            )
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

            # Get embedding for query text
            query_emb = self.get_embedding(query_text, task_type="retrieval_query")

            # Calculate cosine similarity and filter
            results = []
            for doc_id, doc, meta_json, emb_json in rows:
                meta = json.loads(meta_json) if meta_json else {}
                
                # Check where filter
                match = True
                if where:
                    for key, val in where.items():
                        if isinstance(val, dict):
                            if "$eq" in val:
                                target_val = val["$eq"]
                            else:
                                target_val = None
                        else:
                            target_val = val
                        
                        if target_val is not None:
                            if str(meta.get(key)) != str(target_val):
                                match = False
                                break
                if not match:
                    continue

                try:
                    emb = json.loads(emb_json)
                except Exception:
                    continue

                sim = cosine_similarity(query_emb, emb)
                # Cosine distance: smaller distance is better (more similar)
                distance = 1.0 - sim
                results.append((distance, doc_id, doc, meta))

            # Sort by distance (ascending)
            results.sort(key=lambda x: x[0])

            # Slice top results
            top_results = results[:n_results]

            if not top_results:
                return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

            # Build standard ChromaDB response format
            distances = [r[0] for r in top_results]
            ids = [r[1] for r in top_results]
            documents = [r[2] for r in top_results]
            metadatas = [r[3] for r in top_results]

            return {
                "documents": [documents],
                "metadatas": [metadatas],
                "distances": [distances],
                "ids": [ids]
            }

        except Exception as e:
            print(f"Query error: {e}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics about a collection."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            
            cursor.execute("SELECT metadata FROM collections WHERE name = ?", (collection_name,))
            row = cursor.fetchone()
            if not row:
                conn.close()
                return {"name": collection_name, "document_count": 0, "metadata": {}}
                
            metadata = json.loads(row[0]) if row[0] else {}
            
            cursor.execute("SELECT COUNT(*) FROM documents WHERE collection_name = ?", (collection_name,))
            count = cursor.fetchone()[0]
            conn.close()
            
            return {
                "name": collection_name,
                "document_count": count,
                "metadata": metadata,
            }
        except Exception:
            return {"name": collection_name, "document_count": 0, "metadata": {}}

    def delete_collection(self, collection_name: str) -> bool:
        """Delete an entire collection."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("DELETE FROM documents WHERE collection_name = ?", (collection_name,))
            cursor.execute("DELETE FROM collections WHERE name = ?", (collection_name,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    def list_collections(self) -> List[str]:
        """List all collection names."""
        try:
            conn = sqlite3.connect(str(self._db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM collections")
            names = [row[0] for row in cursor.fetchall()]
            conn.close()
            return names
        except Exception:
            return []
