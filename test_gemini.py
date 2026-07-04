import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

def test_gemini_connection():
    # Load environment variables
    load_dotenv(override=True)
    
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: GEMINI_API_KEY is not set in the environment or .env file.")
        return
        
    print("Initializing GenAI Client...")
    client = genai.Client(api_key=api_key)
    
    models = ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
    
    print("\nTesting multiple models:")
    for model_name in models:
        print(f"\n--- Testing {model_name} ---")
        try:
            response = client.models.generate_content(
                model=model_name,
                contents="Hello, respond with 'OK'."
            )
            print(f"SUCCESS: {model_name} is active. Response: '{response.text.strip()}'")
        except APIError as api_err:
            print(f"FAILED: {model_name} returned API error: {api_err.message} (status code: {api_err.code})")
        except Exception as e:
            print(f"FAILED: {model_name} returned error: {str(e)}")

if __name__ == "__main__":
    test_gemini_connection()
