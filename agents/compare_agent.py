import os
from typing import List, Dict, Any
from tools.memory_tool import MemoryManager
from tools.model_router import ModelRouter

class CompareAgent:
    """
    An agent that performs comparative research analysis between a current 
    paper summary and previously stored papers using vector similarity search 
    and ModelRouter.
    """
    def __init__(self, provider: str = None, host: str = None, db_path="data/chroma_db", collection_name="research_memories"):
        self.memory = MemoryManager(db_path=db_path, collection_name=collection_name)
        self.router = ModelRouter(provider=provider, host=host)

    def run(self, current_title: str, current_summary: str, exclude_id: str = "", limit: int = 3) -> str:
        """
        Search vector database for similar papers, then ask ModelRouter to generate 
        a comparative report.
        """
        # 1. Retrieve similar papers from vector memory
        similar_papers = self.memory.search_similar_papers(
            query_summary=current_summary,
            exclude_id=exclude_id,
            limit=limit
        )
        
        if not similar_papers:
            return (
                "## Comparative Analysis\n\n"
                "No previous papers were found in the database to compare against. "
                "Analyze more papers to populate the memory bank!"
            )
            
        # 2. Formulate context details for the comparator prompt
        similar_context = ""
        for idx, paper in enumerate(similar_papers, 1):
            similar_context += (
                f"### Previous Paper {idx}: {paper['title']}\n"
                f"**Summary:**\n{paper['summary']}\n\n"
            )
            
        from prompts.agent_prompts import COMPARE_INSTRUCTION_TEMPLATE
        prompt = COMPARE_INSTRUCTION_TEMPLATE.format(
            current_title=current_title,
            current_summary=current_summary,
            similar_context=similar_context
        )
        
        return self.router.generate_content(prompt, task_type="comparison")
