# ai/gemini_provider.py
import os
from google import genai
from ai.provider import BaseAIProvider

class GeminiModelProvider(BaseAIProvider):
    def __init__(self, api_key: str = None):
        super().__init__()
        # Fallback cleanly to environment variables if main loop leaves it empty
        resolved_key = api_key or os.environ.get("GEMINI_API_KEY", "MOCK_KEY")
        self.client = genai.Client(api_key=resolved_key)
        self.model_name = "gemini-1.5-flash"

    def prompt_inference(self, prompt: str) -> str:
        """Sends news payloads to Gemini to analyze market sentiment."""
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )
            return response.text.strip()
        except Exception as e:
            return "1.0"  # Safe neutral multiplier fallback

    def generate_text(self, prompt: str) -> str:
        """Bridges interface naming mismatch called by NewsAnalystAgent."""
        return self.prompt_inference(prompt)
