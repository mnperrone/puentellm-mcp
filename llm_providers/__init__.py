# llm_providers/__init__.py

def get_llm_handler(provider_name, api_key=None, base_url=None, model=None):
    """
    Retorna el handler correspondiente al proveedor de LLM especificado.
    """
    if provider_name == "ollama":
        from .ollama_handler import OllamaHandler
        return OllamaHandler(model=model)

    elif provider_name == "openai_compatible":
        from .openai_compatible_handler import OpenAICompatibleHandler
        return OpenAICompatibleHandler(api_key=api_key, base_url=base_url, model=model)

    elif provider_name == "qwen":
        from .qwen_handler import QwenHandler
        return QwenHandler(api_key=api_key, model=model)

    else:
        raise ValueError(f"Proveedor no soportado: {provider_name}")