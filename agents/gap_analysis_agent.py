import os
from tools.model_router import ModelRouter

class GapAnalysisAgent:
    """
    An agent that performs a critical review of a research paper's text 
    to identify research gaps (limitations, future directions, missing benchmarks, 
    and unexplored problems).
    """
    def __init__(self, provider: str = None, host: str = None):
        self.router = ModelRouter(provider=provider, host=host)

    def run(self, text: str) -> str:
        """
        Analyze the document text and extract research gaps.
        """
        if not text or not text.strip():
            return "Error: Empty text provided to GapAnalysisAgent."

        from prompts.agent_prompts import GAP_INSTRUCTION
        prompt = f"{GAP_INSTRUCTION}\n\n--- Research Paper Text ---\n{text}"

        return self.router.generate_content(prompt, task_type="gaps")
