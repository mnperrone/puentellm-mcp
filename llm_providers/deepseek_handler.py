# llm_providers/deepseek_handler.py

from openai import OpenAI
from .llm_exception import LLMConnectionError

class DeepSeekHandler:
    def __init__(self, api_key=None, base_url="https://api.deepseek.com", model=None):
        if not api_key:
            raise ValueError("API key is required for DeepSeek")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model or "deepseek-chat"

        try:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
        except Exception as e:
            raise LLMConnectionError(f"Failed to initialize DeepSeek client: {e}")

    def generate(self, prompt):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            raise LLMConnectionError(f"Error communicating with DeepSeek API: {e}")

    def stream(self, messages):
        """
        Provides a streaming response from the DeepSeek API.
        """
        try:
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield {"message": {"content": chunk.choices[0].delta.content}}
        except Exception as e:
            raise LLMConnectionError(f"Error streaming from DeepSeek API: {e}")

    def list_models(self):
        """Returns the configured model for compatibility."""
        return [{"name": self.model}]
