# llm_providers/ollama_handler.py

import ollama
from .llm_exception import LLMConnectionError

class OllamaHandler:
    def __init__(self, model="llama3"):
        self.model = model
        try:
            self.client = ollama.Client()
        except Exception as e:
            raise LLMConnectionError(f"Failed to initialize Ollama client: {e}")

    def generate(self, prompt):
        try:
            response = self.client.generate(model=self.model, prompt=prompt)
            return response['response']
        except Exception as e:
            raise LLMConnectionError(f"Error communicating with Ollama: {e}")

    def stream(self, messages):
        """
        Provides a streaming response from the Ollama API.
        """
        try:
            stream = self.client.chat(
                model=self.model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                if chunk['message']['content']:
                    yield {"message": {"content": chunk['message']['content']}}
        except Exception as e:
            raise LLMConnectionError(f"Error streaming from Ollama: {e}")

    def list_models(self):
        """Returns a list of available models from the Ollama API."""
        try:
            return self.client.list()["models"]
        except Exception as e:
            raise LLMConnectionError(f"Could not fetch models from Ollama: {e}")
