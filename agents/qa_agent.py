import os
from typing import List, Dict, Any
from tools.memory_tool import MemoryManager
from tools.model_router import ModelRouter

class QAAgent:
    """
    Agent that answers questions over uploaded papers using ChromaDB semantic retrieval (RAG).
    Ensures answers are grounded in retrieved source context, citing papers and sections.
    """
    def __init__(self, provider: str = None, host: str = None, db_path="data/chroma_db", collection_name="research_memories"):
        self.memory = MemoryManager(db_path=db_path, collection_name=collection_name)
        self.router = ModelRouter(provider=provider, host=host)

    def run(self, query: str, history: List[Dict[str, str]] = None) -> str:
        """
        Retrieves relevant sections, formats prompt with history & context, and gets LLM response.
        """
        if not query or not query.strip():
            return "Please provide a valid question."
            
        # 1. Query ChromaDB for section chunks
        chunks = self.memory.search_chunks(query, limit=5)
        
        if not chunks:
            context_str = "No specific research paper context found in vector memory."
        else:
            context_str = ""
            for idx, chunk in enumerate(chunks, 1):
                context_str += (
                    f"--- Source {idx} ---\n"
                    f"Paper Title: {chunk['title']}\n"
                    f"Section: {chunk['section'].upper()}\n"
                    f"Content:\n{chunk['content']}\n\n"
                )
                
        # 2. Format history if any
        history_str = ""
        if history:
            for turn in history:
                role = "User" if turn["role"] == "user" else "Assistant"
                history_str += f"{role}: {turn['content']}\n"
                
        prompt = (
            "You are an expert research QA assistant. Answer the user's question based strictly on the provided research paper context below. "
            "You MUST cite the source paper title and section name for every claim you make based on the sources.\n\n"
            "If the context does not contain the answer, state that the information is not present in the uploaded papers, "
            "but try to provide a general helpful answer if possible, clearly distinguishing it from paper evidence.\n\n"
            f"--- Conversation History ---\n{history_str}\n"
            f"--- Research Source Context ---\n{context_str}\n"
            f"User Question: {query}\n\n"
            "Answer (include citations in format '[Paper Title - Section]'):"
        )
        
        # Route QA as 'basic' unless history/query is highly complex
        task_type = "basic"
        if len(query) > 200 or (history and len(history) > 4):
            task_type = "complex"
            
        return self.router.generate_content(prompt, task_type=task_type)
