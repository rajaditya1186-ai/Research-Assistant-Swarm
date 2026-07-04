from agents.gap_analysis_agent import GapAnalysisAgent

def run_test():
    sample_paper_text = (
        "Paper Title: Multi-Agent Software Development using LLMs\n"
        "Abstract: We present an automated coding workflow using three LLM agents. "
        "The system writes Python code, writes test suites, and runs them. "
        "We evaluate our system on 50 simple algorithm coding problems.\n"
        "Discussion of Limitations and Future Work:\n"
        "Our current evaluation only covers Python algorithms. We did not test other "
        "programming languages like Rust, Java, or Javascript. Furthermore, the dataset "
        "is limited to simple algorithms and does not cover full-scale system architecture "
        "or GUI applications. We did not run any user studies to verify if developers find "
        "the tool helpful. Future work could integrate static analysis tools to verify "
        "syntax before compiling and explore security vulnerability scanning."
    )

    print("Instantiating GapAnalysisAgent...")
    agent = GapAnalysisAgent()
    
    print("Running GapAnalysisAgent...")
    gaps = agent.run(sample_paper_text)
    
    print("\n--- Identified Research Gaps ---")
    print(gaps)
    print("---------------------------------\n")

    if "Research Gaps" in gaps:
        print("SUCCESS: GapAnalysisAgent verified successfully!")
    else:
        print("FAILURE: GapAnalysisAgent output is missing 'Research Gaps' header.")

if __name__ == "__main__":
    run_test()
