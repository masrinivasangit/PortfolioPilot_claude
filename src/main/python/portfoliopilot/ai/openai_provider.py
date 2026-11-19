# ai/openai_provider.py
from openai import OpenAI
from ai.provider import BaseAIProvider

class OpenAIModelProvider(BaseAIProvider):
    def __init__(self, api_key: str):
        super().__init__()
        # Securely arm the OpenAI client connection
        self.client = OpenAI(api_key=api_key)

    def prompt_inference(self, prompt: str) -> str:
        """Sends news payloads to ChatGPT to analyze market sentiment."""
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return "0.0" # Safe neutral sentiment fallback
