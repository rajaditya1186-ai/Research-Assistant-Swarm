from tools.memory_tool import MemoryManager

def run_test():
    print("Initializing MemoryManager...")
    # Initialize with a test collection path
    mm = MemoryManager(db_path="data/chroma_db_test", collection_name="test_collection")
    
    # 1. Add some mock paper summaries
    paper_1_summary = (
        "This paper discusses reinforcement learning applied to playing the game of Go (AlphaGo). "
        "It employs deep neural networks and Monte Carlo tree search to beat top professional players. "
        "The models are trained using supervised learning from human games followed by self-play."
    )
    paper_2_summary = (
        "This paper introduces a framework for orchestrating multiple autonomous agents in a swarm. "
        "It focuses on coordinating worker agents (testers, writers, coders) using a centralized "
        "coordinator to write and refine complex programming tasks, reducing error rates by 34%."
    )
    
    print("\nAdding mock papers to memory...")
    mm.add_paper(paper_id="paper_go", title="Mastering the Game of Go with Deep Neural Networks", summary=paper_1_summary, filename="alphago.pdf")
    mm.add_paper(paper_id="paper_swarm", title="Swarm Intelligence in Agentic Workflows", summary=paper_2_summary, filename="swarm.pdf")
    
    # 2. Retrieve all stored papers to verify insertion
    print("\nRetrieving all stored papers:")
    all_papers = mm.get_all_papers()
    for p in all_papers:
        print(f"- Title: {p['title']} (ID: {p['id']})")
        
    # 3. Query for similar papers
    query_text = "I am looking for research about multi-agent coordination, automated coders, and swarms."
    print(f"\nSearching for papers similar to: '{query_text}'")
    similar = mm.search_similar_papers(query_text, limit=1)
    
    if similar:
        print(f"Match found! Title: '{similar[0]['title']}'")
        print(f"Summary: {similar[0]['summary']}")
        
        if similar[0]["id"] == "paper_swarm":
            print("\nSUCCESS: Memory search returned the correct closest match!")
        else:
            print("\nFAILURE: Search did not return the expected swarm paper.")
    else:
        print("\nFAILURE: No matches returned.")

if __name__ == "__main__":
    run_test()
