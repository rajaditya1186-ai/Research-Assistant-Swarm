from agents.search_agent import SearchAgent

def test_search_agent():
    print("Instantiating SearchAgent...")
    agent = SearchAgent()
    
    query = "Transformers in healthcare"
    print(f"Running SearchAgent for query: '{query}'")
    results = agent.run(query, max_results=3)
    
    print(f"\nFound {len(results)} results:")
    for i, paper in enumerate(results, 1):
        print(f"\n--- Paper {i} ---")
        print(f"Title: {paper['title']}")
        print(f"Authors: {', '.join(paper['authors'])}")
        print(f"Summary: {paper['summary'][:300]}...")
        print("-----------------")

    if len(results) > 0:
        print("\nSUCCESS: SearchAgent verified successfully!")
    else:
        print("\nFAILURE: SearchAgent returned 0 results.")

if __name__ == "__main__":
    test_search_agent()
