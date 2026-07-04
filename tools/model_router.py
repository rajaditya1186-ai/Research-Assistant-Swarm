import os
import requests
import json
from google import genai

class ModelRouter:
    """
    Unified LLM router supporting local Ollama models (gemma3:12b, llama3.1:8b)
    and cloud Gemini 2.5 Flash. Applies the project routing strategy
    and is dynamically configurable from env or the UI sidebar settings.
    """
    def __init__(self, provider: str = None, host: str = None):
        # Provider can be: 'Ollama Only', 'Gemini Only', or 'Hybrid (Routed)'
        self.provider = provider or os.getenv("LLM_PROVIDER", "Ollama Only")
        self.host = host or os.getenv("OLLAMA_HOST", "http://localhost:11434")
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.local_primary = os.getenv("OLLAMA_PRIMARY_MODEL", "gemma3:12b")
        self.local_fallback = os.getenv("OLLAMA_FALLBACK_MODEL", "llama3.1:8b")
        
    def generate_content(self, prompt: str, task_type: str = "basic") -> str:
        """
        Routes the instruction according to provider settings and task types:
        - Basic tasks (summaries, citations, basic Q&A) go to Ollama in Hybrid mode.
        - Complex tasks (gap analysis, comparative reviews) go to Gemini 2.5 Flash in Hybrid mode.
        - 'Ollama Only' and 'Gemini Only' override task routing and force the chosen provider.
        """
        active_provider = self.provider
        
        # Apply hybrid routing rules
        if self.provider == "Hybrid (Routed)":
            if task_type in ["gaps", "comparison", "complex", "literature_review"]:
                active_provider = "Gemini Only"
            else:
                active_provider = "Ollama Only"
                
        if active_provider == "Gemini Only":
            return self._call_gemini(prompt)
        else:
            return self._call_ollama(prompt)
            
    def _call_gemini(self, prompt: str) -> str:
        if not self.gemini_key:
            return "Error: Gemini API Key is missing. Please configure it in settings."
        try:
            client = genai.Client(api_key=self.gemini_key)
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt
            )
            return response.text
        except Exception as e:
            return f"Gemini API Error: {str(e)}"
            
    def _call_ollama(self, prompt: str) -> str:
        # Loop through primary then fallback model
        for model in [self.local_primary, self.local_fallback]:
            try:
                url = f"{self.host}/api/generate"
                payload = {
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                }
                headers = {"Content-Type": "application/json"}
                # Use a short timeout of 3 seconds for local service checks
                response = requests.post(url, data=json.dumps(payload), headers=headers, timeout=3)
                if response.status_code == 200:
                    return response.json().get("response", "")
            except Exception as e:
                print(f"ModelRouter: Local connection failed for {model}. Details: {str(e)}")
                continue
                
        # Graceful fallback: If Ollama fails but Gemini API Key is configured, fall back to Gemini
        if self.gemini_key:
            print("ModelRouter Warning: Ollama unreachable. Gracefully falling back to Gemini 2.5 Flash.")
            return self._call_gemini(prompt)
            
        return (
            "Error: Could not connect to local Ollama host at the specified OLLAMA_HOST address. "
            "Please verify that the local Ollama service is active and the host matches, or "
            "configure a Gemini API Key and switch the LLM Provider to 'Gemini Only' in the sidebar."
        )
