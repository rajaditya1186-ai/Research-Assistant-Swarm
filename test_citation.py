from agents.citation_agent import CitationAgent

def run_test():
    sample_paper_text = (
        "arXiv:2310.12345v1 [cs.CL] 19 Oct 2023\n"
        "Swarm Intelligence in Large Language Model Agent Workflows\n"
        "Aditya Raj, Antigravity AI Research Team\n"
        "Abstract: We introduce a framework for orchestrating multiple autonomous agents "
        "collaborating in a swarm pattern. By sharing a common state space and executing "
        "hierarchical tasks, the swarm achieves superior code-generation and debugging "
        "benchmarks compared to single-agent systems. We evaluate the system on the "
        "HumanEval dataset."
    )

    print("Instantiating CitationAgent...")
    agent = CitationAgent()
    
    print("Running CitationAgent...")
    citations = agent.run(sample_paper_text)
    
    print("\n--- Generated Citations ---")
    print("APA:")
    print(citations["apa"])
    print("\nIEEE:")
    print(citations["ieee"])
    print("\nBibTeX:")
    print(citations["bibtex"])
    print("---------------------------\n")

    # Verify formatting output
    if "Error" not in citations["apa"] and citations["bibtex"].startswith("@"):
        print("SUCCESS: CitationAgent verified successfully!")
    else:
        print("WARNING: Some citations might have failed to format correctly. Please inspect output.")

if __name__ == "__main__":
    run_test()
