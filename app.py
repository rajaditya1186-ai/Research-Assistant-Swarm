import os
import streamlit as st
import asyncio
from dotenv import load_dotenv
from agents.coordinator_agent import run_swarm_async
from tools.memory_tool import MemoryManager
from agents.compare_agent import CompareAgent
from agents.search_agent import SearchAgent
from tools.security_tool import validate_file_signature, mask_pii_emails, check_prompt_injection


# Load environment variables from .env file (override to detect runtime updates)
load_dotenv(override=True)

def generate_citation_graph_html(current_title: str, related_titles: list, similar_papers: list) -> str:
    """
    Generates a highly interactive, animated, glassmorphic Vis.js graph
    showing the current paper at the center, related papers from arXiv (purple),
    and similar papers retrieved from vector database memory (green).
    """
    import json
    # Nodes configuration
    nodes = [{
        "id": 1,
        "label": current_title[:45] + ("..." if len(current_title) > 45 else ""),
        "title": current_title,
        "color": {"background": "#6366f1", "border": "#818cf8"},
        "font": {"color": "#ffffff", "size": 15, "face": "Outfit", "multi": "md"},
        "shadow": {"enabled": True, "color": "rgba(99, 102, 241, 0.4)", "size": 10}
    }]
    edges = []
    
    node_id = 2
    # Add related papers (arXiv nodes)
    for title in related_titles:
        if not title.strip():
            continue
        clean_title = title.strip()
        nodes.append({
            "id": node_id,
            "label": clean_title[:35] + ("..." if len(clean_title) > 35 else ""),
            "title": clean_title,
            "color": {"background": "#1e1b4b", "border": "#a78bfa"},
            "font": {"color": "#c084fc", "size": 12, "face": "Outfit"},
            "shadow": {"enabled": True, "color": "rgba(167, 139, 250, 0.2)", "size": 5}
        })
        edges.append({
            "from": 1,
            "to": node_id,
            "label": "cites",
            "font": {"color": "#a78bfa", "size": 10, "face": "Outfit"},
            "color": {"color": "rgba(167, 139, 250, 0.45)"},
            "length": 140
        })
        node_id += 1
        
    # Add similar papers (ChromaDB memory nodes)
    for paper in similar_papers:
        title = paper.get("title", "Memory Paper")
        nodes.append({
            "id": node_id,
            "label": title[:35] + ("..." if len(title) > 35 else ""),
            "title": title,
            "color": {"background": "#022c22", "border": "#34d399"},
            "font": {"color": "#34d399", "size": 12, "face": "Outfit"},
            "shadow": {"enabled": True, "color": "rgba(52, 211, 153, 0.2)", "size": 5}
        })
        edges.append({
            "from": 1,
            "to": node_id,
            "label": "compares",
            "font": {"color": "#34d399", "size": 10, "face": "Outfit"},
            "color": {"color": "rgba(52, 211, 153, 0.45)"},
            "length": 140
        })
        node_id += 1
        
    nodes_json = json.dumps(nodes)
    edges_json = json.dumps(edges)
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            html, body {{ margin: 0; padding: 0; background-color: #080a10; overflow: hidden; height: 100%; }}
            #network {{ width: 100%; height: 100%; }}
        </style>
        <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    </head>
    <body>
        <div id="network"></div>
        <script>
            var nodes = new vis.DataSet({nodes_json});
            var edges = new vis.DataSet({edges_json});
            var container = document.getElementById('network');
            var data = {{ nodes: nodes, edges: edges }};
            var options = {{
                nodes: {{
                    shape: 'box',
                    margin: 12,
                    shapeProperties: {{ borderRadius: 8 }},
                    borderWidth: 2
                }},
                edges: {{
                    width: 2,
                    arrows: {{ to: {{ enabled: true, scaleFactor: 0.8 }} }}
                }},
                physics: {{
                    barnesHut: {{
                        gravitationalConstant: -1800,
                        centralGravity: 0.25,
                        springLength: 120,
                        springConstant: 0.04
                    }},
                    stabilization: {{ iterations: 150 }}
                }},
                interaction: {{ hover: true, tooltipDelay: 100 }}
            }};
            var network = new vis.Network(container, data, options);
        </script>
    </body>
    </html>
    """
    return html

# App configuration
st.set_page_config(
    page_title="Research Assistant Swarm - PDF Summarizer",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Premium UI Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');
    
    /* Reset & Custom Backgrounds */
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
        background-color: #080a10 !important;
        background-image: 
            radial-gradient(at 0% 0%, rgba(99, 102, 241, 0.12) 0px, transparent 50%),
            radial-gradient(at 50% 0%, rgba(168, 85, 247, 0.07) 0px, transparent 50%),
            radial-gradient(at 100% 0%, rgba(244, 114, 182, 0.07) 0px, transparent 50%) !important;
        background-attachment: fixed !important;
        color: #e2e8f0;
    }
    
    [data-testid="stHeader"] {
        background-color: transparent !important;
    }
    
    /* Hide default Streamlit footer for professional look */
    footer {
        visibility: hidden !important;
        height: 0px !important;
        padding: 0px !important;
    }
    
    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Title Gradient */
    .hero-title {
        background: linear-gradient(135deg, #a5b4fc 0%, #c084fc 50%, #f472b6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.2rem;
        font-weight: 800;
        margin-bottom: 0.1rem;
        text-shadow: 0 10px 40px rgba(165, 180, 252, 0.08);
    }
    
    .hero-subtitle {
        color: #94a3b8;
        font-size: 1.1rem;
        margin-bottom: 2.2rem;
        font-weight: 400;
        line-height: 1.6;
    }
    
    /* Sleek Card Panels */
    .css-card {
        background: rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 15px 35px -10px rgba(0, 0, 0, 0.4);
        backdrop-filter: blur(12px);
        margin-bottom: 20px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    .css-card:hover {
        border-color: rgba(168, 85, 247, 0.3);
        box-shadow: 0 20px 40px -10px rgba(168, 85, 247, 0.12);
        transform: translateY(-2px);
    }
    
    /* Accent borders */
    .accent-border {
        border-left: 4px solid #818cf8;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: #04060b !important;
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    .sidebar-brand {
        font-family: 'Outfit', sans-serif;
        font-size: 1.2rem;
        font-weight: 700;
        color: #a5b4fc;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    
    /* Status indicators */
    .system-status {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 10px 14px;
        margin-bottom: 8px;
        font-size: 0.85rem;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
    }
    
    /* Custom buttons styling */
    div.stButton > button {
        background: linear-gradient(135deg, #4f46e5 0%, #7e22ce 100%) !important;
        color: #f8fafc !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.2) !important;
        width: 100% !important;
    }
    
    div.stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(126, 34, 206, 0.4) !important;
        background: linear-gradient(135deg, #4338ca 0%, #6b21a8 100%) !important;
    }
    
    /* Custom Download Button Styling */
    div.stDownloadButton > button {
        background: linear-gradient(135deg, #059669 0%, #10b981 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 10px !important;
        padding: 10px 24px !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        font-size: 0.95rem !important;
        letter-spacing: 0.01em !important;
        transition: all 0.25s ease !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2) !important;
        width: 100% !important;
    }
    
    div.stDownloadButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 18px rgba(16, 185, 129, 0.4) !important;
        background: linear-gradient(135deg, #047857 0%, #059669 100%) !important;
    }
    
    /* Input Fields Styling */
    .stTextInput input, .stTextArea textarea {
        background-color: rgba(10, 15, 30, 0.7) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        color: #f1f5f9 !important;
        border-radius: 10px !important;
        padding: 10px 14px !important;
        font-family: 'Plus Jakarta Sans', sans-serif !important;
        transition: all 0.2s ease !important;
    }
    
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 10px rgba(99, 102, 241, 0.2) !important;
    }
    
    /* File Uploader styling */
    .stFileUploader section {
        background-color: rgba(15, 23, 42, 0.3) !important;
        border: 2px dashed rgba(99, 102, 241, 0.25) !important;
        border-radius: 12px !important;
        padding: 24px !important;
        transition: all 0.25s ease !important;
    }
    
    .stFileUploader section:hover {
        border-color: #8b5cf6 !important;
        background-color: rgba(15, 23, 42, 0.5) !important;
    }
    
    /* Tab Menu styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 16px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 24px;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #94a3b8 !important;
        background-color: transparent !important;
        border: none !important;
        padding: 12px 20px !important;
        transition: all 0.25s ease !important;
        border-radius: 4px 4px 0 0;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        color: #a78bfa !important;
        background-color: rgba(255, 255, 255, 0.02) !important;
    }
    
    .stTabs [aria-selected="true"] {
        color: #818cf8 !important;
        border-bottom: 2px solid #818cf8 !important;
    }
    
    /* Codeblock styling */
    code {
        color: #f472b6 !important;
        background: rgba(0, 0, 0, 0.3) !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.9rem !important;
        border-radius: 4px;
        padding: 2px 6px;
    }
    
    pre {
        background: rgba(10, 15, 30, 0.6) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px !important;
        padding: 14px !important;
    }
    
    pre code {
        background: transparent !important;
        color: #e2e8f0 !important;
        padding: 0 !important;
    }
    
    div[data-testid="stExpander"] {
        background-color: rgba(15, 23, 42, 0.25) !important;
        border: 1px solid rgba(255, 255, 255, 0.06) !important;
        border-radius: 12px !important;
        margin-bottom: 12px !important;
        padding: 4px !important;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
    }
    
    div[data-testid="stExpander"] > details {
        border: none !important;
    }
    
    div[data-testid="stExpander"] summary {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #e2e8f0 !important;
    }
    
    /* Section headers inside cards */
    .section-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: #a5b4fc;
        margin-top: 24px;
        margin-bottom: 12px;
        padding-bottom: 6px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* Swarm Live Monitor Animations */
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.8; }
        100% { transform: scale(1.15); opacity: 1; }
    }
    
    /* Swarm Pipeline Layout (Sidebar) */
    .swarm-pipeline-container {
        background: rgba(15, 23, 42, 0.65);
        border: 1px solid rgba(99, 102, 241, 0.15);
        border-radius: 12px;
        padding: 16px;
        margin-top: 20px;
        backdrop-filter: blur(8px);
    }
    
    .swarm-pipeline-container h4 {
        margin-top: 0;
        margin-bottom: 16px;
        font-size: 0.9rem;
        color: #a5b4fc;
        letter-spacing: 0.05em;
        text-transform: uppercase;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
        padding-bottom: 8px;
    }
    
    .swarm-node {
        display: flex;
        align-items: center;
        gap: 12px;
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.04);
        border-radius: 8px;
        padding: 8px 12px;
        transition: all 0.25s ease;
    }
    
    .swarm-node:hover {
        background: rgba(99, 102, 241, 0.06);
        border-color: rgba(99, 102, 241, 0.25);
        transform: translateX(2px);
    }
    
    .swarm-node-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #64748b;
        box-shadow: 0 0 6px #64748b;
        flex-shrink: 0;
    }
    
    .swarm-node.active .swarm-node-dot {
        background-color: #10b981;
        box-shadow: 0 0 8px #10b981;
        animation: pulse 1s infinite alternate;
    }
    
    .swarm-node.idle .swarm-node-dot {
        background-color: #818cf8;
        box-shadow: 0 0 8px #818cf8;
    }
    
    .swarm-node-content {
        display: flex;
        flex-direction: column;
    }
    
    .node-title {
        font-size: 0.85rem;
        font-weight: 600;
        color: #e2e8f0;
    }
    
    .node-desc {
        font-size: 0.7rem;
        color: #94a3b8;
    }
    
    .swarm-node-arrow {
        text-align: center;
        color: #4f46e5;
        font-size: 0.8rem;
        margin: 4px 0;
        opacity: 0.6;
    }
</style>
""", unsafe_allow_html=True)

# Application Header
st.markdown('<div class="hero-title">ScholarSwarm AI</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">An Orchestrated Multi-Agent Intelligence Hub for Literature Synthesis, Critical Gap Analysis, and Vector-Based Academic Memory</div>', unsafe_allow_html=True)

# Sidebar configurations
with st.sidebar:
    st.markdown('<div class="sidebar-brand">🧬 ScholarSwarm Hub</div>', unsafe_allow_html=True)
    st.markdown("### ⚙️ Settings")
    
    # API Key management
    env_key = os.getenv("GEMINI_API_KEY")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=env_key if env_key else "",
        type="password",
        help="Provide your Gemini API key if not configured in the .env file."
    )
    
    # Save Key Helper
    if api_key_input and api_key_input != env_key:
        if st.button("Save to .env"):
            with open(".env", "a") as f:
                f.write(f"\nGEMINI_API_KEY={api_key_input}")
            st.success("API Key appended to .env!")
            
    # Model Selection
    model_name = st.selectbox(
        "Model",
        options=["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"],
        index=0,
        help="Choose a Gemini model. If one model experiences high demand (503 error), try selecting an alternative model."
    )
    
    # LLM Provider Selection
    llm_provider = st.selectbox(
        "LLM Provider",
        options=["Ollama Only", "Gemini Only", "Hybrid (Routed)"],
        index=0,
        help="Ollama runs models locally. Gemini uses Google Cloud. Hybrid routes simple tasks to Ollama and complex reasoning to Gemini."
    )
    os.environ["LLM_PROVIDER"] = llm_provider
    
    if llm_provider in ["Ollama Only", "Hybrid (Routed)"]:
        ollama_host = st.text_input("Ollama Host", value=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        ollama_primary = st.text_input("Primary Local Model", value=os.getenv("OLLAMA_PRIMARY_MODEL", "gemma3:12b"))
        ollama_fallback = st.text_input("Fallback Local Model", value=os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b"))
        
        os.environ["OLLAMA_HOST"] = ollama_host
        os.environ["OLLAMA_PRIMARY_MODEL"] = ollama_primary
        os.environ["OLLAMA_FALLBACK_MODEL"] = ollama_fallback
    
    # Pipeline Mode Selection
    pipeline_mode = st.selectbox(
        "Pipeline Mode",
        options=["Direct API (REST - Recommended)", "ADK Swarm (Websockets - Experimental)"],
        index=0,
        help="Direct API uses stable REST endpoints (recommended). ADK Swarm uses the Google Agent Development Kit over WebSockets."
    )
    
    st.markdown("---")
    st.markdown("### 🧬 Swarm Architecture")
    st.markdown("""
    <div class="swarm-pipeline-container">
        <div class="swarm-node idle">
            <div class="swarm-node-dot"></div>
            <div class="swarm-node-content">
                <span class="node-title">Coordinator Agent</span>
                <span class="node-desc">Orchestrates sequence</span>
            </div>
        </div>
        <div class="swarm-node-arrow">↓</div>
        <div class="swarm-node idle">
            <div class="swarm-node-dot"></div>
            <div class="swarm-node-content">
                <span class="node-title">PDF Agent</span>
                <span class="node-desc">Extracts & Sanitizes Text</span>
            </div>
        </div>
        <div class="swarm-node-arrow">↓</div>
        <div class="swarm-node idle">
            <div class="swarm-node-dot"></div>
            <div class="swarm-node-content">
                <span class="node-title">Summary Agent</span>
                <span class="node-desc">Literature Synthesis</span>
            </div>
        </div>
        <div class="swarm-node-arrow">↓</div>
        <div class="swarm-node idle">
            <div class="swarm-node-dot"></div>
            <div class="swarm-node-content">
                <span class="node-title">Search Agent</span>
                <span class="node-desc">arXiv Context Finder</span>
            </div>
        </div>
        <div class="swarm-node-arrow">↓</div>
        <div class="swarm-node idle">
            <div class="swarm-node-dot"></div>
            <div class="swarm-node-content">
                <span class="node-title">Citation Agent</span>
                <span class="node-desc">Formulates Bibliography</span>
            </div>
        </div>
        <div class="swarm-node-arrow">↓</div>
        <div class="swarm-node idle">
            <div class="swarm-node-dot"></div>
            <div class="swarm-node-content">
                <span class="node-title">Gap Agent</span>
                <span class="node-desc">Identifies Research Gaps</span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #64748b; font-size: 0.8rem;'>Created by Antigravity AI</div>", unsafe_allow_html=True)

# Main content tabs
tab1, tab2, tab3 = st.tabs(["📄 PDF Summarizer", "🔍 arXiv Search Swarm", "💬 Swarm QA Assistant"])

with tab1:
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown('<div class="css-card accent-border"><h3>📥 Upload Documents</h3>', unsafe_allow_html=True)
        uploaded_files = st.file_uploader(
            "Choose files (PDF, TXT, DOCX)", 
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            help="Upload one or more research papers, articles, or documentation files."
        )
        
        st.markdown("---")
        summarize_button = st.button("🚀 Analyze Documents", disabled=not uploaded_files)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="css-card"><h3>🔬 Swarm Analysis Hub</h3>', unsafe_allow_html=True)
        
        if not summarize_button and not uploaded_files:
            st.info("Upload one or more research papers and click 'Analyze Documents' to trigger the agent swarm.")
            
        if uploaded_files:
            # Check API Key if Gemini is needed
            final_api_key = api_key_input or env_key
            if llm_provider != "Ollama Only" and not final_api_key:
                st.error("Missing Gemini API Key. Please provide one in the sidebar settings or .env file.")
                summarize_button = False
            
            # ADK Swarm requires Gemini/Websockets; auto-force Direct API if Ollama-only
            if llm_provider == "Ollama Only" and pipeline_mode.startswith("ADK Swarm"):
                st.warning("⚠️ ADK Swarm requires a Gemini API Key to orchestrate workers. Switching pipeline automatically to Direct API for local Ollama processing.")
                pipeline_mode = "Direct API (REST - Recommended)"
                
            if summarize_button:
                # Create uploads directory if not exists
                os.makedirs("data/uploads", exist_ok=True)
                
                # List to store results of all analyzed documents
                analyzed_papers = []
                temp_paths = []
                
                try:
                    # Thread-safe sync helper to run our async ADK runner in Streamlit
                    def run_swarm_sync_wrapper(path: str, key: str, model: str):
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        if loop.is_running():
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, run_swarm_async(path, key, model))
                                return future.result()
                        else:
                            return loop.run_until_complete(run_swarm_async(path, key, model))

                    # Helper function to generate monitor HTML
                    def draw_swarm_monitor(steps_status, active_file=""):
                        html_code = f"""
                        <div style="background: rgba(15, 23, 42, 0.4); border: 1px solid rgba(99, 102, 241, 0.15); border-radius: 12px; padding: 20px; margin-bottom: 20px; backdrop-filter: blur(8px);">
                            <h4 style="margin: 0 0 4px 0; color: #a5b4fc; font-family: 'Outfit', sans-serif; font-size: 1.1rem; display: flex; align-items: center; gap: 8px;">
                                <span>🤖</span> ScholarSwarm Live Orchestrator
                            </h4>
                            <p style="margin: 0 0 16px 0; font-size: 0.85rem; color: #94a3b8;">
                                Active Document: <code style="color: #f472b6; font-size: 0.8rem; background: rgba(0,0,0,0.2); padding: 2px 6px; border-radius: 4px;">{active_file}</code>
                            </p>
                            <div style="display: flex; flex-direction: column; gap: 12px;">
                        """
                        for step_name, status in steps_status.items():
                            if status == "success":
                                status_icon = "🟢"
                                status_badge = '<span style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.2); padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Completed</span>'
                                text_color = "#e2e8f0"
                            elif status == "running":
                                status_icon = "⚡"
                                status_badge = '<span style="background: rgba(139, 92, 246, 0.15); color: #8b5cf6; border: 1px solid rgba(139, 92, 246, 0.2); padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; animation: pulse 1s infinite alternate;">Active</span>'
                                text_color = "#f8fafc"
                            elif status == "error":
                                status_icon = "🔴"
                                status_badge = '<span style="background: rgba(239, 68, 68, 0.15); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.2); padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Failed</span>'
                                text_color = "#ef4444"
                            else: # pending
                                status_icon = "⚫"
                                status_badge = '<span style="background: rgba(255, 255, 255, 0.05); color: #64748b; border: 1px solid rgba(255, 255, 255, 0.05); padding: 2px 8px; border-radius: 20px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase;">Pending</span>'
                                text_color = "#64748b"
                                
                            html_code += f"""
                            <div style="display: flex; align-items: center; justify-content: space-between; padding: 10px 14px; background: rgba(255, 255, 255, 0.01); border: 1px solid rgba(255, 255, 255, 0.03); border-radius: 8px;">
                                <div style="display: flex; align-items: center; gap: 10px; color: {text_color}; font-size: 0.9rem; font-weight: 500;">
                                    <span style="font-size: 1.1rem; line-height: 1;">{status_icon}</span>
                                    <span>{step_name}</span>
                                </div>
                                {status_badge}
                            </div>
                            """
                        html_code += "</div></div>"
                        return html_code.replace("\n", " ")

                    # Direct API function (REST-based, highly stable)
                    def run_direct_api_pipeline(path: str, key: str, model: str, steps_status: dict, monitor_placeholder):
                        # 1. Extract text from PDF
                        steps_status["PDF Extraction Agent"] = "running"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        from tools.pdf_tool import extract_text
                        extracted_txt = extract_text(path)
                        if not extracted_txt or not extracted_txt.strip():
                            steps_status["PDF Extraction Agent"] = "error"
                            monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                            raise ValueError("The PDF text could not be extracted or is empty.")
                        steps_status["PDF Extraction Agent"] = "success"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        
                        # 2. Run SummaryAgent
                        steps_status["Summary Agent"] = "running"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        from agents.summary_agent import SummaryAgent
                        summary_agent = SummaryAgent(provider=llm_provider, host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
                        sum_out = summary_agent.run(extracted_txt)
                        steps_status["Summary Agent"] = "success"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        
                        # 3. Generate search query using ModelRouter and run SearchAgent
                        steps_status["Search Agent"] = "running"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        query_prompt = (
                            "Analyze the following text fragment and generate an optimal search query of 3 to 5 words to find related papers on arXiv. "
                            "Return ONLY the 3 to 5 words search query text, nothing else.\n\n"
                            f"{extracted_txt[:2000]}"
                        )
                        try:
                            from tools.model_router import ModelRouter
                            router = ModelRouter(provider=llm_provider, host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
                            search_query_text = router.generate_content(query_prompt, task_type="basic").strip()
                        except Exception:
                            search_query_text = os.path.basename(path).replace(".pdf", "")[:50]
                        
                        from agents.search_agent import SearchAgent
                        search_agent = SearchAgent()
                        results = search_agent.run(search_query_text, max_results=3)
                        related_papers_out = search_agent.format_results_markdown(results)
                        steps_status["Search Agent"] = "success"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        
                        # 4. Run CitationAgent
                        steps_status["Citation Agent"] = "running"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        from agents.citation_agent import CitationAgent
                        citation_agent = CitationAgent(provider=llm_provider, host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
                        citations_dict = citation_agent.run(extracted_txt)
                        citations_raw_out = (
                            f"[START_APA]\n{citations_dict.get('apa', '')}\n[END_APA]\n"
                            f"[START_IEEE]\n{citations_dict.get('ieee', '')}\n[END_IEEE]\n"
                            f"[START_BIBTEX]\n{citations_dict.get('bibtex', '')}\n[END_BIBTEX]"
                        )
                        steps_status["Citation Agent"] = "success"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        
                        # 5. Run GapAnalysisAgent
                        steps_status["Gap Agent"] = "running"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        from agents.gap_analysis_agent import GapAnalysisAgent
                        gap_agent = GapAnalysisAgent(provider=llm_provider, host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
                        gaps_out = gap_agent.run(extracted_txt)
                        steps_status["Gap Agent"] = "success"
                        monitor_placeholder.markdown(draw_swarm_monitor(steps_status, os.path.basename(path)), unsafe_allow_html=True)
                        
                        return {
                            "summary": sum_out,
                            "gaps": gaps_out,
                            "related_papers": related_papers_out,
                            "citations": citations_raw_out
                        }

                    # Loop through and process each uploaded file
                    for idx, uploaded_file in enumerate(uploaded_files, 1):
                        st.write(f"⚙️ **Processing file {idx} of {len(uploaded_files)}**: `{uploaded_file.name}`")
                        
                        # Save uploaded file temporarily
                        temp_path = os.path.join("data/uploads", uploaded_file.name)
                        temp_paths.append(temp_path)
                        with open(temp_path, "wb") as f:
                            f.write(uploaded_file.getbuffer())
                            
                        # Security Step 1: File signature validation
                        if not validate_file_signature(temp_path):
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            raise ValueError(f"🔒 Security Alert: File signature validation failed for '{uploaded_file.name}'!")
                        
                        # Create empty placeholder for live step logging
                        monitor_placeholder = st.empty()
                        steps_status = {
                            "PDF Extraction Agent": "pending",
                            "Summary Agent": "pending",
                            "Search Agent": "pending",
                            "Citation Agent": "pending",
                            "Gap Agent": "pending"
                        }
                        
                        # Execute chosen pipeline with fallback
                        summary = ""
                        gaps = ""
                        related_papers = ""
                        citations_raw = ""
                        
                        if pipeline_mode.startswith("Direct API"):
                            try:
                                res = run_direct_api_pipeline(temp_path, final_api_key, model_name, steps_status, monitor_placeholder)
                                summary = res["summary"]
                                gaps = res["gaps"]
                                related_papers = res["related_papers"]
                                citations_raw = res["citations"]
                            except Exception as direct_err:
                                st.warning(f"⚠️ Direct API Pipeline failed for '{uploaded_file.name}': {str(direct_err)}")
                                st.info("🔄 Falling back to the ADK Swarm Runner...")
                                steps_status = {
                                    "PDF Extraction Agent": "running",
                                    "Summary Agent": "running",
                                    "Search Agent": "running",
                                    "Citation Agent": "running",
                                    "Gap Agent": "running"
                                }
                                monitor_placeholder.markdown(draw_swarm_monitor(steps_status, uploaded_file.name), unsafe_allow_html=True)
                                state = run_swarm_sync_wrapper(temp_path, final_api_key, model_name)
                                summary = state.get("summary", "Summary not generated.")
                                gaps = state.get("gaps", "Gaps analysis not generated.")
                                related_papers = state.get("related_papers", "No related papers found.")
                                citations_raw = state.get("citations", "")
                                
                                # Set all to success
                                steps_status = {k: "success" for k in steps_status}
                                monitor_placeholder.markdown(draw_swarm_monitor(steps_status, uploaded_file.name), unsafe_allow_html=True)
                        else:
                            try:
                                steps_status = {
                                    "PDF Extraction Agent": "running",
                                    "Summary Agent": "running",
                                    "Search Agent": "running",
                                    "Citation Agent": "running",
                                    "Gap Agent": "running"
                                }
                                monitor_placeholder.markdown(draw_swarm_monitor(steps_status, uploaded_file.name), unsafe_allow_html=True)
                                state = run_swarm_sync_wrapper(temp_path, final_api_key, model_name)
                                summary = state.get("summary", "Summary not generated.")
                                gaps = state.get("gaps", "Gaps analysis not generated.")
                                related_papers = state.get("related_papers", "No related papers found.")
                                citations_raw = state.get("citations", "")
                                
                                # Set all to success
                                steps_status = {k: "success" for k in steps_status}
                                monitor_placeholder.markdown(draw_swarm_monitor(steps_status, uploaded_file.name), unsafe_allow_html=True)
                            except Exception as swarm_err:
                                st.warning(f"⚠️ ADK Swarm Runner failed for '{uploaded_file.name}': {str(swarm_err)}")
                                st.info("🔄 Falling back to the robust Direct API Pipeline...")
                                steps_status = {
                                    "PDF Extraction Agent": "pending",
                                    "Summary Agent": "pending",
                                    "Search Agent": "pending",
                                    "Citation Agent": "pending",
                                    "Gap Agent": "pending"
                                }
                                res = run_direct_api_pipeline(temp_path, final_api_key, model_name, steps_status, monitor_placeholder)
                                summary = res["summary"]
                                gaps = res["gaps"]
                                related_papers = res["related_papers"]
                                citations_raw = res["citations"]
                        
                        # Store in ChromaDB memory bank
                        paper_id = uploaded_file.name.replace(".pdf", "").replace(".docx", "").replace(".txt", "").replace(" ", "_").lower()
                        paper_title = os.path.splitext(uploaded_file.name)[0]
                        try:
                            memory_mgr = MemoryManager()
                            memory_mgr.add_paper(
                                paper_id=paper_id,
                                title=paper_title,
                                summary=summary,
                                filename=uploaded_file.name
                            )
                            st.info(f"💾 Added '{paper_title}' to vector memory bank.")
                        except Exception as mem_e:
                            st.warning(f"Could not store paper in memory: {str(mem_e)}")
                            
                        # Save result data
                        analyzed_papers.append({
                            "name": uploaded_file.name,
                            "title": paper_title,
                            "id": paper_id,
                            "summary": summary,
                            "gaps": gaps,
                            "related_papers": related_papers,
                            "citations_raw": citations_raw
                        })
                    
                    st.success("ADK Swarm Analysis Complete for all documents!")
                    
                    # Parse citations helper
                    def extract_section(text, marker_start, marker_end, default_val=""):
                        try:
                            start_idx = text.find(marker_start)
                            if start_idx == -1: return default_val
                            start_idx += len(marker_start)
                            end_idx = text.find(marker_end, start_idx)
                            if end_idx == -1: return text[start_idx:].strip()
                            return text[start_idx:end_idx].strip()
                        except Exception:
                            return default_val

                    # Render document outputs in clean expanders
                    st.markdown("---")
                    st.markdown("### 🔬 Swarm Synthesis Results")
                    
                    for idx, paper in enumerate(analyzed_papers, 1):
                        with st.expander(f"📄 Document {idx}: {paper['name']}", expanded=(idx == 1)):
                            apa_cit = extract_section(paper["citations_raw"], "[START_APA]", "[END_APA]", "APA citation failed.")
                            ieee_cit = extract_section(paper["citations_raw"], "[START_IEEE]", "[END_IEEE]", "IEEE citation failed.")
                            bib_cit = extract_section(paper["citations_raw"], "[START_BIBTEX]", "[END_BIBTEX]", "BibTeX citation failed.")
                            
                            st.markdown('<div class="section-title">📝 Structured Literature Summary</div>', unsafe_allow_html=True)
                            st.markdown(paper["summary"])
                            
                            st.markdown('<div class="section-title">🔍 Identified Research Gaps & Limitations</div>', unsafe_allow_html=True)
                            st.markdown(paper["gaps"])
                            
                            st.markdown('<div class="section-title">🔗 Related Literature (from arXiv)</div>', unsafe_allow_html=True)
                            st.markdown(paper["related_papers"])
                            
                            st.markdown('<div class="section-title">🕸️ Citation & Influence Graph</div>', unsafe_allow_html=True)
                            try:
                                mem_mgr = MemoryManager()
                                similar_papers = mem_mgr.search_similar_papers(
                                    query_summary=paper["summary"],
                                    exclude_id=paper["id"],
                                    limit=3
                                )
                                import re
                                related_titles = re.findall(r"### \d+\.\s+(.+)", paper["related_papers"])
                                graph_html = generate_citation_graph_html(paper["title"], related_titles, similar_papers)
                                st.components.v1.html(graph_html, height=430)
                            except Exception as graph_e:
                                st.warning(f"Could not load citation graph: {str(graph_e)}")
                            
                            st.markdown('<div class="section-title">📋 Academic Citations</div>', unsafe_allow_html=True)
                            citation_tabs = st.tabs(["APA", "IEEE", "BibTeX"])
                            with citation_tabs[0]:
                                st.code(apa_cit, language="text")
                            with citation_tabs[1]:
                                st.code(ieee_cit, language="text")
                            with citation_tabs[2]:
                                st.code(bib_cit, language="bibtex")
                                
                            # Single report download block
                            full_report = (
                                f"# Research Assistant Swarm Analysis Report\n"
                                f"Document: {paper['name']}\n\n"
                                f"{paper['summary']}\n\n"
                                f"--- \n"
                                f"{paper['gaps']}\n\n"
                                f"--- \n"
                                f"## Citations\n\n"
                                f"APA:\n{apa_cit}\n\n"
                                f"IEEE:\n{ieee_cit}\n\n"
                                f"BibTeX:\n{bib_cit}\n"
                            )
                            st.download_button(
                                label="📥 Download Analysis Report (.txt)",
                                data=full_report,
                                file_name=f"analysis_{paper['title']}.txt",
                                mime="text/plain",
                                key=f"dl_{paper['id']}"
                            )
                                
                    # Unified Comparative Analysis
                    st.markdown("---")
                    st.markdown("### 🔍 Comparative Memory Synthesis")
                    try:
                        mem_mgr = MemoryManager()
                        all_past_papers = mem_mgr.get_all_papers()
                        
                        if len(all_past_papers) < 2:
                            st.info("Upload multiple papers or compile database records to enable comparative memory comparison.")
                        else:
                            st.write(f"Found {len(all_past_papers)} papers in database memory.")
                            selected_comp_title = st.selectbox(
                                "Select a paper to compare others against:",
                                options=[p["title"] for p in all_past_papers],
                                index=0
                            )
                            
                            selected_paper = [p for p in all_past_papers if p["title"] == selected_comp_title][0]
                            compare_button = st.button("🔄 Synthesize Similarities & Novelty")
                            if compare_button:
                                with st.spinner("Analyzing similarities and differences with past papers..."):
                                    compare_agent = CompareAgent(provider=llm_provider, host=os.getenv("OLLAMA_HOST", "http://localhost:11434"))
                                    comparison_report = compare_agent.run(
                                        current_title=selected_paper["title"],
                                        current_summary=selected_paper["summary"],
                                        exclude_id=selected_paper["id"],
                                        limit=3
                                    )
                                st.markdown(comparison_report)
                    except Exception as comp_e:
                        st.error(f"Error initializing memory comparison: {str(comp_e)}")
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
                finally:
                    # Clean up all temporary files
                    for path in temp_paths:
                        if os.path.exists(path):
                            os.remove(path)
                            
        st.markdown('</div>', unsafe_allow_html=True)


with tab2:
    st.markdown('<div class="css-card accent-border"><h3>🔍 Search arXiv Research Papers</h3>', unsafe_allow_html=True)
    
    search_col1, search_col2 = st.columns([3, 1])
    with search_col1:
        search_query = st.text_input(
            "Search Query",
            placeholder="e.g. Transformers in healthcare, Swarm intelligence, Reinforcement learning...",
            value="Transformers in healthcare"
        )
    with search_col2:
        max_results = st.slider("Max Results", min_value=1, max_value=10, value=5)
        
    search_button = st.button("Search arXiv", key="arxiv_search_btn")
    st.markdown('</div>', unsafe_allow_html=True)
    
    if search_button:
        # Security Step 4: Prompt injection check on user search query
        if check_prompt_injection(search_query):
            st.error("🔒 Security Alert: Prompt injection attempt detected in search query! (Forbidden command phrases like 'ignore instructions' or 'reveal api key' were found).")
        else:
            clean_query = mask_pii_emails(search_query)
            with st.spinner("Querying arXiv..."):
                search_agent = SearchAgent()
                results = search_agent.run(clean_query, max_results=max_results)
                
            if not results:
                st.warning("No papers found matching the query.")
            else:
                st.success(f"Found {len(results)} relevant research papers!")
                for idx, paper in enumerate(results, 1):
                    st.markdown(f"""
                    <div class="css-card">
                        <h4 style="margin:0 0 8px 0; color:#e2e8f0; font-size:1.2rem;">{idx}. {paper['title']}</h4>
                        <p style="margin:0 0 6px 0; font-size:0.9rem; color:#94a3b8;"><b>Authors:</b> {', '.join(paper['authors'])}</p>
                        <p style="margin:0 0 12px 0; font-size:0.9rem;"><a href="{paper['pdf_url']}" target="_blank" style="color: #6366f1; text-decoration: none; font-weight: 600;">📥 View PDF on arXiv</a></p>
                        <div style="border-top: 1px solid rgba(255,255,255,0.05); padding-top:10px;">
                            <p style="margin:0; font-size:0.95rem; line-height:1.5; color:#cbd5e1;"><b>Summary:</b><br>{paper['summary']}</p>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)


with tab3:
    st.markdown('<div class="css-card accent-border"><h3>💬 Swarm QA Assistant</h3>', unsafe_allow_html=True)
    st.write("Ask questions about previously uploaded and indexed research papers. The Swarm QA Agent will semantically query ChromaDB vector segments and generate answers with precise paper and section citations.")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Session state for chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
        
    # Render previous messages
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            
    # Input user query
    if user_query := st.chat_input("Ask a question about the papers (e.g. 'Compare the datasets used in these papers'):"):
        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)
        st.session_state.messages.append({"role": "user", "content": user_query})
        
        # Security scan on user query
        if check_prompt_injection(user_query):
            response_content = "🔒 Security Alert: Prompt injection attempt detected in query!"
            with st.chat_message("assistant"):
                st.error(response_content)
            st.session_state.messages.append({"role": "assistant", "content": response_content})
        else:
            clean_query = mask_pii_emails(user_query)
            
            with st.spinner("Swarm QA Agent is retrieving context and generating answer..."):
                final_api_key = api_key_input or env_key
                # Check chosen pipeline mode
                if pipeline_mode.startswith("Direct API"):
                    try:
                        from agents.qa_agent import QAAgent
                        qa_agent = QAAgent(provider=llm_provider, host=os.getenv("OLLAMA_HOST"))
                        # Pass past conversation history
                        response_content = qa_agent.run(clean_query, history=st.session_state.messages[:-1])
                    except Exception as e:
                        response_content = f"Error running direct QA pipeline: {str(e)}"
                else:
                    # ADK Swarm Websocket Mode
                    try:
                        from agents.coordinator_agent import run_qa_swarm_async
                        # Async helper wrapper
                        def run_qa_swarm_sync_wrapper(query: str, key: str, model: str):
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                                
                            if loop.is_running():
                                import concurrent.futures
                                with concurrent.futures.ThreadPoolExecutor() as executor:
                                    future = executor.submit(asyncio.run, run_qa_swarm_async(query, key, model))
                                    return future.result()
                            else:
                                return loop.run_until_complete(run_qa_swarm_async(query, key, model))
                                
                        response_content = run_qa_swarm_sync_wrapper(clean_query, final_api_key, model_name)
                    except Exception as e:
                        response_content = f"Error running ADK QA swarm: {str(e)}"
                        
            # Display assistant message
            with st.chat_message("assistant"):
                st.markdown(response_content)
            st.session_state.messages.append({"role": "assistant", "content": response_content})

