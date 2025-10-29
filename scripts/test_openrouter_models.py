import sys
import os
import json

# Añadir el directorio raíz al path de Python
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from llm_providers.openrouter_handler import OpenRouterHandler
from app_config import AppConfig

def main():
    # Cargar la configuración para obtener la API key
    config = AppConfig()
    
    # Mostrar la configuración actual
    print("\n=== Current Configuration ===")
    print(f"Config path: {config.config_path}")
    print(f"Config content: {json.dumps(config.config, indent=2)}")
    
    # Intentar obtener la API key de varias ubicaciones posibles
    api_key = (
        config.get('api_key') or
        config.get('openrouter_api_key') or
        config.get('llm_provider_configs', {}).get('openrouter', {}).get('api_key')
    )
    print(f"\nAPI Key from config: {'*' * len(api_key) if api_key else 'None'}")
    
    if not api_key:
        print("\nNo API key found in config. Please configure your OpenRouter API key first.")
        return
    
    print("\n=== Testing OpenRouter Connection ===")
    # Crear una instancia del handler
    handler = OpenRouterHandler(api_key=api_key)
    
    # Intentar listar los modelos
    print("\n=== Fetching Available Models ===")
    handler.list_models()

if __name__ == "__main__":
    main()