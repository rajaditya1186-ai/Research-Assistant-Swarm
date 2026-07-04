import arxiv
from typing import List, Dict, Any

class SearchAgent:
    """
    An agent that queries arXiv for research papers and returns 
    structured information (title, authors, summary, links).
    """
    def __init__(self):
        self.client = arxiv.Client()

    def run(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Execute search on arXiv and return a list of paper metadata dicts.
        """
        if not query or not query.strip():
            return []
            
        print(f"SearchAgent: Querying arXiv for '{query}' (limit: {max_results})...")
        
        search = arxiv.Search(
            query=query,
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance
        )
        
        results = []
        try:
            for result in self.client.results(search):
                paper_info = {
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "summary": result.summary,
                    "pdf_url": result.pdf_url,
                    "entry_id": result.entry_id
                }
                results.append(paper_info)
        except Exception as e:
            print(f"SearchAgent Error: Failed to fetch results from arXiv. Details: {str(e)}")
            
        return results

    def format_results_markdown(self, results: List[Dict[str, Any]]) -> str:
        """
        Helper method to format the list of dictionaries into a clean markdown string.
        """
        if not results:
            return "No results found."
            
        markdown_output = ""
        for i, paper in enumerate(results, 1):
            authors_str = ", ".join(paper["authors"])
            markdown_output += (
                f"### {i}. {paper['title']}\n"
                f"**Authors:** {authors_str}\n"
                f"**PDF Link:** [{paper['pdf_url']}]({paper['pdf_url']})\n\n"
                f"**Summary:**\n{paper['summary']}\n"
                f"---\n\n"
            )
        return markdown_output
