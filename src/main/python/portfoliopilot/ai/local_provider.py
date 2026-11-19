from ai.provider import BaseAIProvider

class LocalOllamaModelProvider(BaseAIProvider):
    def prompt_inference(self, prompt: str) -> str:
        # local inference engines (Ollama/Llama.cpp) endpoint pipelines map here
        return "Local LLM inference complete."
