import os
from tools.pdf_tool import extract_text
from agents.summary_agent import SummaryAgent
from agents.citation_agent import CitationAgent
from agents.gap_analysis_agent import GapAnalysisAgent

class PDFAgent:
    """
    An agent that processes a PDF document, extracts its text, and delegates
    the text to SummaryAgent, GapAnalysisAgent, and CitationAgent to generate 
    a comprehensive structured summary, research gap analysis, and bibliography.
    """
    def __init__(self, provider: str = None, host: str = None):
        self.provider = provider
        self.host = host

    def run(self, pdf_path: str) -> str:
        """
        Extract text from the specified PDF path, summarize it, analyze gaps, and format citations.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found at: {pdf_path}")
            
        # Extract text from the PDF using pdf_tool
        text = extract_text(pdf_path)
        if not text or not text.strip():
            return "Error: The PDF is empty or text could not be extracted."
            
        # Delegate to SummaryAgent
        summary_agent = SummaryAgent(provider=self.provider, host=self.host)
        summary = summary_agent.run(text)
        
        # Delegate to GapAnalysisAgent
        gap_agent = GapAnalysisAgent(provider=self.provider, host=self.host)
        gaps = gap_agent.run(text)
        
        # Delegate to CitationAgent
        citation_agent = CitationAgent(provider=self.provider, host=self.host)
        citations = citation_agent.run(text)
        
        # Combine summary, gap analysis, and citations
        combined_output = (
            f"{summary}\n\n"
            f"--- \n"
            f"{gaps}\n\n"
            f"--- \n"
            f"## Recommended Citations\n\n"
            f"**APA:**\n"
            f"> {citations['apa']}\n\n"
            f"**IEEE:**\n"
            f"> {citations['ieee']}\n\n"
            f"**BibTeX:**\n"
            f"```bibtex\n{citations['bibtex']}\n```"
        )
        return combined_output


