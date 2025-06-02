# llm_providers/qwen_handler.py

from dashscope import Generation

class QwenHandler:
    def __init__(self, api_key=None, model="qwen-max"):
        Generation.api_key = api_key
        self.model = model

    def generate(self, prompt):
        try:
            response = Generation.call(
                model=self.model,
                prompt=prompt
            )
            return response.output.text
        except Exception as e:
            return f"Error al comunicarse con Qwen: {e}"

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
