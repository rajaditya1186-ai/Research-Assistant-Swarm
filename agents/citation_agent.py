import os
from typing import Dict
from tools.model_router import ModelRouter

class CitationAgent:
    """
    An agent that analyzes paper text, extracts bibliographic metadata,
    and generates citations in APA, IEEE, and BibTeX formats using ModelRouter.
    """
    def __init__(self, provider: str = None, host: str = None):
        self.router = ModelRouter(provider=provider, host=host)

    def run(self, text: str) -> Dict[str, str]:
        """
        Analyze the text, extract bibliographic info, and return a dictionary 
        with 'apa', 'ieee', and 'bibtex' formatted citations.
        """
        if not text or not text.strip():
            return {
                "apa": "Error: Empty text provided.",
                "ieee": "Error: Empty text provided.",
                "bibtex": "Error: Empty text provided."
            }

        # We only need the first part of the text (like the first 4000 characters) 
        # to find the title, authors, and publishing details.
        sample_header = text[:4000]

        from prompts.agent_prompts import CITATION_INSTRUCTION
        prompt = f"{CITATION_INSTRUCTION}\n\n--- Document Header Text ---\n{sample_header}"

        output_text = self.router.generate_content(prompt, task_type="citation")

        # Helper parser to extract sections
        def extract_section(marker_start, marker_end, default_val=""):
            try:
                start_idx = output_text.find(marker_start)
                if start_idx == -1:
                    return default_val
                start_idx += len(marker_start)
                end_idx = output_text.find(marker_end, start_idx)
                if end_idx == -1:
                    return output_text[start_idx:].strip()
                return output_text[start_idx:end_idx].strip()
            except Exception:
                return default_val

        apa_citation = extract_section("[START_APA]", "[END_APA]", "APA citation generation failed.")
        ieee_citation = extract_section("[START_IEEE]", "[END_IEEE]", "IEEE citation generation failed.")
        bibtex_citation = extract_section("[START_BIBTEX]", "[END_BIBTEX]", "BibTeX citation generation failed.")

        return {
            "apa": apa_citation,
            "ieee": ieee_citation,
            "bibtex": bibtex_citation
        }
