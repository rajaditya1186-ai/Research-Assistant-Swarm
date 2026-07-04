import os
from tools.model_router import ModelRouter

class SummaryAgent:
    """
    An agent that takes raw text input and utilizes ModelRouter to generate 
    a highly structured summary with five specific sections:
    - Objective
    - Method
    - Dataset
    - Results
    - Limitations
    """
    def __init__(self, provider: str = None, host: str = None):
        self.router = ModelRouter(provider=provider, host=host)

    def run(self, text: str) -> str:
        """
        Summarize raw text into a structured outline.
        """
        if not text or not text.strip():
            return "Error: Empty text provided to SummaryAgent."
            
        from prompts.agent_prompts import SUMMARY_INSTRUCTION
        prompt = f"{SUMMARY_INSTRUCTION}\n\n--- Extracted Text ---\n{text}"
        
        return self.router.generate_content(prompt, task_type="summary")
