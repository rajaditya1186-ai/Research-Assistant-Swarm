import os
import fitz
import asyncio
from dotenv import load_dotenv
from agents.coordinator_agent import run_swarm_async

def create_sample_paper(pdf_path):
    doc = fitz.open()
    page = doc.new_page()
    content = (
        "Title: Swarm Intelligence in Agentic Workflows\n\n"
        "Abstract:\n"
        "This paper introduces a framework for orchestrating multiple agentic systems "
        "collaborating in a swarm pattern. We discuss how distributed problem-solving "
        "techniques can be applied to large language model (LLM) agents to enhance "
        "efficiency, reliability, and code generation quality.\n\n"
        "1. Introduction:\n"
        "Agentic systems are transforming automated reasoning. While single-agent setups "
        "perform well on simple tasks, complex software engineering tasks require multi-agent "
        "coordination, task division, and cross-verification.\n\n"
        "2. Methodology:\n"
        "Our swarm framework employs a coordinator agent that assigns sub-tasks to specialized "
        "worker agents (e.g., Code Writer, Tester, Analyst). The agents run in parallel and "
        "verify each other's outputs before compiling a final result.\n\n"
        "3. Results:\n"
        "Experiments show that the Swarm approach reduces error rates in complex coding tasks "
        "by 34% compared to a single-agent baseline. Output consistency and adherence to style "
        "guidelines also see significant improvement.\n\n"
        "4. Conclusion:\n"
        "We presented a scalable swarm architecture. Future research will explore dynamically "
        "spawning new agent roles based on runtime performance metrics."
    )
    page.insert_text((50, 50), content)
    doc.save(pdf_path)
    doc.close()
    print(f"Created sample paper PDF at: {pdf_path}")

async def test_coordinator():
    load_dotenv(override=True)
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set.")
        return
        
    pdf_path = "paper.pdf"
    create_sample_paper(pdf_path)
    
    try:
        print("Starting ADK Swarm execution via Sequential Coordinator...")
        state = await run_swarm_async(pdf_path=pdf_path, api_key=api_key)
        
        print("\n=== Swarm Execution Completed! State Keys Generated ===")
        print(list(state.keys()))
        
        print("\n--- Summary (SummaryAgent) ---")
        print(state.get("summary", "None")[:400])
        
        print("\n--- Gaps (GapAgent) ---")
        print(state.get("gaps", "None")[:400])
        
        print("\n--- Citations (CitationAgent) ---")
        print(state.get("citations", "None")[:400])
        
        print("\n--- Related Papers (SearchAgent) ---")
        print(state.get("related_papers", "None")[:400])
        print("========================================================\n")
        
        # Verify required outputs
        required_keys = ["summary", "gaps", "citations", "related_papers"]
        missing = [k for k in required_keys if k not in state]
        
        if not missing:
            print("SUCCESS: ADK Multi-Agent Coordinator Swarm verified successfully!")
        else:
            print(f"FAILURE: Missing expected state output keys: {missing}")
            
    except Exception as e:
        print(f"ERROR: Coordinator test run failed: {str(e)}")
    finally:
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Cleaned up {pdf_path}")

if __name__ == "__main__":
    asyncio.run(test_coordinator())
