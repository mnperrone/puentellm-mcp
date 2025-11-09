# env_manager.py
"""
Manejo de variables de entorno para credenciales sensibles
"""

import os
from pathlib import Path
from typing import Optional, Dict

class EnvManager:
    def __init__(self):
        self.env_file = Path(__file__).parent / '.env'
        self.load_env_file()
    
    def load_env_file(self):
        """Carga variables desde el archivo .env si existe"""
        if self.env_file.exists():
            try:
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            os.environ[key] = value
            except Exception as e:
                print(f"Warning: Could not load .env file: {e}")
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """Obtiene la API key para un proveedor específico"""
        provider_upper = provider.upper()
        return os.environ.get(f'{provider_upper}_API_KEY')
    
    def get_base_url(self, provider: str) -> Optional[str]:
        """Obtiene la URL base para un proveedor específico"""
        provider_upper = provider.upper()
        return os.environ.get(f'{provider_upper}_BASE_URL')
    
    def set_api_key(self, provider: str, api_key: str):
        """Establece la API key en variables de entorno (solo en memoria)"""
        provider_upper = provider.upper()
        os.environ[f'{provider_upper}_API_KEY'] = api_key
    
    def set_base_url(self, provider: str, base_url: str):
        """Establece la URL base en variables de entorno (solo en memoria)"""
        provider_upper = provider.upper()
        os.environ[f'{provider_upper}_BASE_URL'] = base_url
    
    def get_provider_config(self, provider: str) -> Dict[str, Optional[str]]:
        """Obtiene toda la configuración de un proveedor"""
        return {
            'api_key': self.get_api_key(provider),
            'base_url': self.get_base_url(provider)
        }
    
    def save_to_env_file(self, provider: str, api_key: str = None, base_url: str = None):
        """Guarda credenciales al archivo .env"""
        try:
            # Leer contenido existente
            existing_lines = []
            if self.env_file.exists():
                with open(self.env_file, 'r', encoding='utf-8') as f:
                    existing_lines = f.readlines()
            
            # Crear diccionario de variables existentes
            existing_vars = {}
            non_var_lines = []
            for line in existing_lines:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    existing_vars[key.strip()] = value.strip()
                else:
                    non_var_lines.append(line)
            
            # Actualizar variables
            provider_upper = provider.upper()
            if api_key:
                existing_vars[f'{provider_upper}_API_KEY'] = api_key
            if base_url:
                existing_vars[f'{provider_upper}_BASE_URL'] = base_url
            
            # Escribir archivo actualizado
            with open(self.env_file, 'w', encoding='utf-8') as f:
                # Escribir comentarios y líneas no variables
                for line in non_var_lines:
                    if line.strip():
                        f.write(f"{line}\n")
                
                # Escribir variables por proveedor
                providers_written = set()
                for key, value in existing_vars.items():
                    if '_API_KEY' in key or '_BASE_URL' in key:
                        provider_name = key.split('_')[0]
                        if provider_name not in providers_written:
                            f.write(f"\n# {provider_name.title()}\n")
                            providers_written.add(provider_name)
                    f.write(f"{key}={value}\n")
            
            # Actualizar variables en memoria también
            if api_key:
                self.set_api_key(provider, api_key)
            if base_url:
                self.set_base_url(provider, base_url)
                
        except Exception as e:
            print(f"Error saving to .env file: {e}")
            # Fallback: al menos configurar en memoria
            if api_key:
                self.set_api_key(provider, api_key)
            if base_url:
                self.set_base_url(provider, base_url)

# Instancia global
env_manager = EnvManager()