# llm_providers/ollama_handler.py

import requests

class OllamaHandler:
    def __init__(self, model="llama3"):
        self.model = model
        self.base_url = "http://localhost:11434/api/generate"

    def generate(self, prompt):
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False
        }
        response = requests.post(self.base_url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "No response from model.")
        else:
            return f"Error: {response.status_code} - {response.text}"

    def stream(self, messages):
        """
        Simula un stream de respuesta para compatibilidad con LLMBridge.
        Devuelve un generador que produce un solo chunk con la respuesta completa.
        """
        # Extrae el prompt del último mensaje de usuario
        prompt = ""
        for msg in messages:
            if msg.get("role") == "user":
                prompt = msg.get("content", "")
        response = self.generate(prompt)
        yield {"message": {"content": response}}

