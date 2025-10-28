# llm_providers/openai_compatible_handler.py

from openai import OpenAI

class OpenAICompatibleHandler:
    def __init__(self, api_key=None, base_url=None, model=None):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model or "llama3-8b-8192"

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

    def generate(self, prompt):
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}]
            )
            return completion.choices[0].message.content
        except Exception as e:
            return f"Error al comunicarse con el modelo: {e}"

    def stream(self, messages):
        """
        Simula un stream de respuesta para compatibilidad con LLMBridge.
        Devuelve un generador que produce un solo chunk con la respuesta completa.
        """
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
        response = self.generate(prompt)
        yield {"message": {"content": response}}

    def list_models(self):
        """Returns the configured model for compatibility."""
        return [{"name": self.model}]
