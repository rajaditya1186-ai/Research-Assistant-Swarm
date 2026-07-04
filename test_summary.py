import os
from dotenv import load_dotenv
from agents.summary_agent import SummaryAgent

def run_test():
    load_dotenv()
    
    sample_text = (
        "Project DeepMind AlphaGo developed an AI to play Go. The method used a combination "
        "of deep neural networks (policy and value networks) and Monte Carlo tree search. "
        "The neural networks were trained on a dataset of 30 million moves from human games, "
        "followed by self-play reinforcement learning. AlphaGo defeated the 18-time world champion "
        "Lee Sedol 4-1 in 2016. However, the system requires significant computational resources "
        "and is restricted only to games with perfect information."
    )
    
    print("Instantiating SummaryAgent...")
    agent = SummaryAgent()
    
    print("Running SummaryAgent on sample text...")
    summary = agent.run(sample_text)
    
    print("\n--- SummaryAgent Output ---")
    print(summary)
    print("---------------------------\n")
    
    # Simple validation
    required_sections = ["Objective", "Method", "Dataset", "Results", "Limitations"]
    missing = [sec for sec in required_sections if sec.lower() not in summary.lower()]
    
    if not missing:
        print("SUCCESS: SummaryAgent successfully produced all required sections!")
    else:
        print(f"FAILURE: Missing sections: {missing}")

if __name__ == "__main__":
    run_test()
