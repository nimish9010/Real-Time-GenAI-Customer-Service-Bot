"""
modules/medical_qa.py -- Task 3: Medical Q&A Chatbot using MedQuAD.
Handles dataset loading, medical entity recognition, and retrieval-based QA.
"""

import os
import re
import json
from typing import List, Dict, Any, Optional
from pathlib import Path

import google.generativeai as genai
import config
from modules.vector_store import VectorStore
from utils.helpers import chunk_text, clean_text, generate_doc_id


# Medical entity patterns for basic NER
MEDICAL_PATTERNS = {
    "symptoms": [
        r"\b(pain|ache|fever|cough|fatigue|nausea|vomiting|dizziness|headache|"
        r"swelling|rash|itching|bleeding|numbness|tingling|weakness|shortness of breath|"
        r"chest pain|abdominal pain|back pain|joint pain|muscle pain|sore throat|"
        r"runny nose|congestion|diarrhea|constipation|insomnia|anxiety|depression)\b"
    ],
    "diseases": [
        r"\b(diabetes|cancer|hypertension|asthma|arthritis|alzheimer|parkinson|"
        r"epilepsy|hepatitis|tuberculosis|pneumonia|bronchitis|influenza|malaria|"
        r"HIV|AIDS|stroke|heart disease|kidney disease|liver disease|anemia|"
        r"osteoporosis|fibromyalgia|lupus|multiple sclerosis|COPD|obesity)\b"
    ],
    "treatments": [
        r"\b(surgery|chemotherapy|radiation|therapy|medication|antibiotic|vaccine|"
        r"transplant|dialysis|insulin|physical therapy|rehabilitation|treatment|"
        r"prescription|dosage|drug|medicine|remedy|supplement|vitamin)\b"
    ],
    "body_parts": [
        r"\b(heart|lung|liver|kidney|brain|stomach|intestine|bone|muscle|skin|"
        r"blood|eye|ear|nose|throat|spine|joint|nerve|artery|vein)\b"
    ],
}


class MedicalQAEngine:
    """Medical Q&A engine using MedQuAD dataset with vector retrieval."""

    def __init__(self):
        self.vector_store = VectorStore()
        self.collection_name = config.COLLECTION_MEDICAL
        self._configure_genai()
        self.qa_pairs = []

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
        """Load the built-in sample MedQuAD data."""
        sample_path = config.MEDICAL_DATA_DIR / "sample_medquad.json"
        if sample_path.exists():
            with open(sample_path, "r", encoding="utf-8") as f:
                self.qa_pairs = json.load(f)
            return len(self.qa_pairs)
        return 0

    def load_from_xml_directory(self, directory: str):
        """Parse MedQuAD XML files from a directory."""
        from bs4 import BeautifulSoup

        qa_pairs = []
        xml_dir = Path(directory)

        if not xml_dir.exists():
            return 0

        for xml_file in xml_dir.glob("**/*.xml"):
            try:
                with open(xml_file, "r", encoding="utf-8", errors="ignore") as f:
                    soup = BeautifulSoup(f.read(), "lxml-xml")

                for qa in soup.find_all("QAPair"):
                    question_tag = qa.find("Question")
                    answer_tag = qa.find("Answer")
                    if question_tag and answer_tag:
                        question = clean_text(question_tag.get_text())
                        answer = clean_text(answer_tag.get_text())
                        if question and answer and len(answer) > 20:
                            qtype = question_tag.get("qtype", "general")
                            focus = ""
                            focus_tag = qa.find("Focus") or qa.find("QAPair")
                            if focus_tag and focus_tag.get("fid"):
                                focus = focus_tag.get("fid", "")

                            qa_pairs.append({
                                "question": question,
                                "answer": answer,
                                "qtype": qtype,
                                "focus": focus,
                                "source": xml_file.name,
                            })
            except Exception:
                continue

        self.qa_pairs = qa_pairs
        return len(qa_pairs)

    def build_index(self):
        """Index all loaded QA pairs into ChromaDB."""
        if not self.qa_pairs:
            return 0

        documents = []
        metadatas = []
        ids = []

        for i, qa in enumerate(self.qa_pairs):
            doc = f"Question: {qa['question']}\nAnswer: {qa['answer']}"
            documents.append(doc)
            metadatas.append({
                "qtype": qa.get("qtype", "general"),
                "focus": qa.get("focus", ""),
                "source": qa.get("source", "sample"),
                "question": qa["question"][:200],
            })
            ids.append(generate_doc_id(doc, f"medical_{i}"))

        return self.vector_store.add_documents(
            self.collection_name, documents=documents, metadatas=metadatas, ids=ids
        )

    def extract_medical_entities(self, text: str) -> Dict[str, List[str]]:
        """Extract medical entities from text using regex patterns."""
        entities = {}
        text_lower = text.lower()

        for entity_type, patterns in MEDICAL_PATTERNS.items():
            found = set()
            for pattern in patterns:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                found.update(matches)
            if found:
                entities[entity_type] = sorted(list(found))

        return entities

    def retrieve_answer(self, question: str, top_k: int = 5) -> Dict[str, Any]:
        """Retrieve relevant medical answers using vector search + Gemini."""
        results = self.vector_store.query(
            self.collection_name, question, n_results=top_k
        )

        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]

        entities = self.extract_medical_entities(question)

        if not documents:
            return {
                "answer": "I couldn't find relevant medical information for your question. "
                          "Please try rephrasing or ask about a specific condition, symptom, or treatment.",
                "sources": [],
                "entities": entities,
                "disclaimer": True,
            }

        context = "\n\n---\n\n".join(documents[:3])
        sources = [m.get("source", "MedQuAD") for m in metadatas[:3]]
        qtypes = [m.get("qtype", "") for m in metadatas[:3]]

        self._configure_genai()
        if not self.model:
            return {
                "answer": "API key not configured. Raw context:\n\n" + context[:500],
                "sources": sources,
                "entities": entities,
                "disclaimer": True,
            }

        prompt = f"""You are a medical information assistant. Based on the following medical
knowledge base entries, provide a clear, accurate, and helpful answer to the patient's question.

IMPORTANT GUIDELINES:
- Be factual and cite the source information
- Use clear, patient-friendly language
- Mention relevant medical entities (symptoms, conditions, treatments)
- Always recommend consulting a healthcare professional
- Do NOT diagnose — only provide information

MEDICAL KNOWLEDGE BASE:
{context}

DETECTED ENTITIES: {json.dumps(entities) if entities else "None detected"}

PATIENT QUESTION: {question}

MEDICAL INFORMATION:"""

        try:
            response = self.model.generate_content(prompt)
            answer = response.text
        except Exception as e:
            answer = f"Error generating response: {str(e)}"

        return {
            "answer": answer,
            "sources": list(set(sources)),
            "entities": entities,
            "question_types": list(set(qtypes)),
            "disclaimer": True,
        }

    def get_stats(self):
        """Get medical knowledge base statistics."""
        stats = self.vector_store.get_collection_stats(self.collection_name)
        stats["loaded_qa_pairs"] = len(self.qa_pairs)
        return stats
