class BaseAIProvider:
    def __init__(self):
        pass

    def prompt_inference(self, prompt: str) -> str:
        raise NotImplementedError("AI Provider must implement prompt_inference logic.")
