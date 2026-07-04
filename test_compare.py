import asyncio
from agents.compare_agent import CompareAgent

def run_test():
    db_path = "data/chroma_db_test"
    collection_name = "test_collection"
    
    print("Instantiating CompareAgent...")
    # Initialize with our test database setup
    agent = CompareAgent(db_path=db_path, collection_name=collection_name)
    
    # Define a new current paper to compare
    current_title = "Hierarchical Multi-Agent Programming Systems with Code Verification"
    current_summary = (
        "This paper presents a hierarchical multi-agent framework where coding sub-agents write code "
        "and a verification agent runs unit tests and static syntax checkers to ensure correctness. "
        "It evaluates on complex coding datasets and shows a 45% reduction in syntax errors. "
        "It directly extends static coordination setups by introducing runtime feedback loops "
        "and code verification."
    )
    
    print(f"Comparing current paper: '{current_title}' with stored papers in memory...")
    comparison = agent.run(
        current_title=current_title,
        current_summary=current_summary,
        exclude_id="paper_current",
        limit=2
    )
    
    print("\n--- CompareAgent Output ---")
    print(comparison)
    print("---------------------------\n")
    
    # Validate structure
    required_sections = ["Commonalities", "Distinct Features", "Synthesis"]
    missing = [sec for sec in required_sections if sec.lower() not in comparison.lower()]
    
    if not missing:
        print("SUCCESS: CompareAgent comparative analysis verified successfully!")
    else:
        print(f"FAILURE: Missing comparative report sections: {missing}")

if __name__ == "__main__":
    run_test()
