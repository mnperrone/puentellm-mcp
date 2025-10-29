# llm_providers/huggingface_handler.py

from huggingface_hub import InferenceClient
from .llm_exception import LLMConnectionError

class HuggingFaceHandler:
    def __init__(self, api_key=None, model=None):
        if not api_key:
            raise ValueError("API key is required for HuggingFace")

        self.api_key = api_key
        self.model = model or "mistralai/Mistral-7B-Instruct-v0.2"

        try:
            self.client = InferenceClient(token=self.api_key)
        except Exception as e:
            raise LLMConnectionError(f"Failed to initialize HuggingFace client: {e}")

    def generate(self, prompt):
        try:
            response = self.client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                max_tokens=1024,
            )
            return response.choices[0].message.content
        except Exception as e:
            raise LLMConnectionError(f"Error communicating with HuggingFace API: {e}")

    def stream(self, messages):
        """
        Provides a streaming response from the HuggingFace API.
        """
        try:
            stream = self.client.chat_completion(
                messages=messages,
                model=self.model,
                max_tokens=1024,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"message": {"content": chunk.choices[0].delta.content}}
        except Exception as e:
            raise LLMConnectionError(f"Error streaming from HuggingFace API: {e}")

    def list_models(self):
        """Returns the configured model for compatibility."""
        return [{"name": self.model}]
