import os
import asyncio
from typing import Dict, Any
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


# ---------------------------------------------------------
# MCP Server Configuration
# ---------------------------------------------------------
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

def create_filesystem_mcp() -> McpToolset:
    uploads_abs_path = os.path.abspath("data/uploads")
    papers_abs_path = os.path.abspath("data/papers")
    os.makedirs(uploads_abs_path, exist_ok=True)
    os.makedirs(papers_abs_path, exist_ok=True)
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="npx.cmd",
                args=["-y", "@modelcontextprotocol/server-filesystem", uploads_abs_path, papers_abs_path],
            ),
        ),
        tool_filter=["list_directory", "read_file", "write_file"],
    )

def create_github_mcp() -> McpToolset | None:
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if github_token:
        return McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    command="npx.cmd",
                    args=["-y", "@modelcontextprotocol/server-github"],
                    env={"GITHUB_PERSONAL_ACCESS_TOKEN": github_token}
                ),
            ),
            tool_filter=["search_repositories"],
        )
    return None

# ---------------------------------------------------------
# 1. Custom Tools for ADK Agents
# ---------------------------------------------------------

def extract_pdf_text_tool(pdf_path: str) -> dict:
    """Extract text from the specified PDF file path.

    Args:
        pdf_path: The absolute file path to the PDF document.

    Returns:
        dict containing 'status' and 'text'.
    """
    from tools.pdf_tool import extract_text
    try:
        if not os.path.exists(pdf_path):
            return {"status": "error", "message": f"File not found: {pdf_path}"}
        txt = extract_text(pdf_path)
        return {"status": "success", "text": txt}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def arxiv_search_tool(query: str) -> dict:
    """Query arXiv for research papers related to the search query.

    Args:
        query: The 3 to 5 words search query string.

    Returns:
        dict containing 'status' and 'results'.
    """
    from agents.search_agent import SearchAgent
    try:
        agent = SearchAgent()
        results = agent.run(query, max_results=3)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def rag_search_tool(query: str) -> dict:
    """Query ChromaDB for relevant section chunks from previously analyzed papers.

    Args:
        query: The user's question or search query.

    Returns:
        dict containing 'status' and 'results'.
    """
    from tools.memory_tool import MemoryManager
    try:
        memory = MemoryManager()
        results = memory.search_chunks(query, limit=5)
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------------------------------------
# 2. Sub-agent Factory Functions
# ---------------------------------------------------------

def create_pdf_agent(model_name: str) -> Agent:
    tools_list = [extract_pdf_text_tool, create_filesystem_mcp()]
    gh = create_github_mcp()
    if gh:
        tools_list.append(gh)
    return Agent(
        name="pdf_agent",
        model=model_name,
        instruction=(
            "Use the extract_pdf_text_tool to extract text from the PDF file path "
            "provided in the state variable 'pdf_path'. Return only the extracted text. "
            "You are also equipped with Filesystem and GitHub MCP tools to list, read, or write "
            "files in the uploads/ or papers/ folders."
        ),
        tools=tools_list,
        output_key="extracted_text"
    )

from prompts.agent_prompts import SUMMARY_INSTRUCTION, GAP_INSTRUCTION, CITATION_INSTRUCTION, SEARCH_INSTRUCTION

def create_summary_agent(model_name: str) -> Agent:
    return Agent(
        name="summary_agent",
        model=model_name,
        instruction=f"{SUMMARY_INSTRUCTION}\n\nInput text to summarize:\n{{extracted_text}}",
        output_key="summary"
    )

def create_gap_agent(model_name: str) -> Agent:
    return Agent(
        name="gap_agent",
        model=model_name,
        instruction=f"{GAP_INSTRUCTION}\n\nInput paper text to analyze:\n{{extracted_text}}",
        output_key="gaps"
    )

def create_search_agent(model_name: str) -> Agent:
    tools_list = [arxiv_search_tool]
    gh = create_github_mcp()
    if gh:
        tools_list.append(gh)
    return Agent(
        name="search_agent",
        model=model_name,
        instruction=SEARCH_INSTRUCTION,
        tools=tools_list,
        output_key="related_papers"
    )

def create_citation_agent(model_name: str) -> Agent:
    return Agent(
        name="citation_agent",
        model=model_name,
        instruction=f"{CITATION_INSTRUCTION}\n\nInput paper text fragment:\n{{extracted_text}}",
        output_key="citations"
    )

def create_qa_agent(model_name: str) -> Agent:
    return Agent(
        name="qa_agent",
        model=model_name,
        instruction=(
            "You are an interactive QA agent. Your job is to answer the user's question. "
            "Use the rag_search_tool to retrieve relevant sections from previously stored research papers. "
            "You MUST cite the source paper title and section name for every claim you make. "
            "If the retrieved context does not contain the answer, state that it is not present in the papers, "
            "but you may provide general helpful reasoning if possible."
        ),
        tools=[rag_search_tool],
        output_key="qa_answer"
    )

# ---------------------------------------------------------
# 3. Sequential Coordinator Agent
# ---------------------------------------------------------

def create_coordinator_agent(model_name: str = "gemini-2.5-flash") -> SequentialAgent:
    return SequentialAgent(
        name="coordinator_agent",
        sub_agents=[
            create_pdf_agent(model_name),
            create_summary_agent(model_name),
            create_search_agent(model_name),
            create_citation_agent(model_name),
            create_gap_agent(model_name)
        ]
    )

# ---------------------------------------------------------
# 4. Programmatic Swarm Runner API
# ---------------------------------------------------------

async def run_swarm_async(pdf_path: str, api_key: str, model_name: str = "gemini-2.5-flash") -> Dict[str, Any]:
    """Runs the full ADK Multi-Agent sequential coordinator swarm on the PDF file."""
    # Ensure API Key is set in process environment
    os.environ["GEMINI_API_KEY"] = api_key
    
    session_service = InMemorySessionService()
    user_id = "user"
    session_id = "swarm_session"
    
    # Initialize session
    await session_service.create_session(app_name="app", user_id=user_id, session_id=session_id)
    
    # Inject file path into session state
    session = await session_service.get_session(app_name="app", user_id=user_id, session_id=session_id)
    session.state["pdf_path"] = pdf_path
    
    # Set up Runner and Coordinator Agent
    coordinator = create_coordinator_agent(model_name)
    runner = Runner(agent=coordinator, app_name="app", session_service=session_service)
    
    # Run the swarm pipeline
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=f"Process PDF: {pdf_path}")]),
    ):
        pass
        
    # Retrieve final session state containing all output keys
    final_session = await session_service.get_session(app_name="app", user_id=user_id, session_id=session_id)
    return final_session.state

async def run_qa_swarm_async(query: str, api_key: str, model_name: str = "gemini-2.5-flash") -> str:
    """Runs the ADK QA agent on the user query, utilizing the ChromaDB RAG search tool."""
    os.environ["GEMINI_API_KEY"] = api_key
    
    session_service = InMemorySessionService()
    user_id = "user"
    session_id = "qa_session"
    
    # Initialize session
    await session_service.create_session(app_name="app", user_id=user_id, session_id=session_id)
    
    # Set up Runner and QA Agent
    qa_agent = create_qa_agent(model_name)
    runner = Runner(agent=qa_agent, app_name="app", session_service=session_service)
    
    # Run the QA agent
    async for event in runner.run_async(
        user_id=user_id,
        session_id=session_id,
        new_message=types.Content(role="user", parts=[types.Part.from_text(text=query)]),
    ):
        pass
        
    final_session = await session_service.get_session(app_name="app", user_id=user_id, session_id=session_id)
    return final_session.state.get("qa_answer", "Error: QA Agent failed to generate an answer.")
