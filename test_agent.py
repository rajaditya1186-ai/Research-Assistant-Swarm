import os
import fitz
from dotenv import load_dotenv
from agents.pdf_agent import PDFAgent

def create_sample_paper(pdf_path):
    # Programmatically create a sample research paper PDF using PyMuPDF
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
    
    # Write the content to the page
    page.insert_text((50, 50), content)
    doc.save(pdf_path)
    doc.close()
    print(f"Created temporary paper PDF at: {pdf_path}")

def run_test():
    load_dotenv()
    pdf_path = "paper.pdf"
    
    try:
        # Create paper.pdf
        create_sample_paper(pdf_path)
        
        # Instantiate PDFAgent and run it
        print("Instantiating PDFAgent...")
        agent = PDFAgent()
        
        print(f"Running agent on {pdf_path}...")
        paper_summary = agent.run(pdf_path)
        
        print("\n--- Summary Output (Full) ---")
        print(paper_summary)
        print("-----------------------------\n")
        
        print("SUCCESS: PDFAgent run test completed successfully!")
        
    except Exception as e:
        print(f"ERROR: Test failed: {str(e)}")
        
    finally:
        # Clean up
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
            print(f"Cleaned up {pdf_path}")

if __name__ == "__main__":
    run_test()
