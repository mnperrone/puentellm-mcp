# app_config.py

import json
from pathlib import Path
import os
from assets.logging import PersistentLogger

class AppConfig:
    def __init__(self):
        # Directorio de configuración en la raíz del proyecto
        self.config_dir = Path(__file__).resolve().parent
        self.config_path = self.config_dir / 'app_config.json'
        
        # Crear un directorio de logs local si no existe
        log_dir = self.config_dir / 'logs'
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        self.logger = PersistentLogger(log_dir=log_dir)
        
        self.default_config = {
            'llm_model': '',  # Usuario debe seleccionar
            'llm_provider': '',  # Usuario debe seleccionar
            'sanitize_model_output': True,
            'auto_space_model_output': False,
            'llm_provider_configs': {
                # Solo guardamos modelo y URL base, NO api keys
                # Las API keys se manejan en variables de entorno
            }
        }
        self.config = self._load_config()

    def _load_config(self):
        """Carga la configuración desde app_config.json, usa por defecto si no existe o está corrupto."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    # Cargar la configuración existente y fusionarla con la por defecto
                    existing_config = json.load(f)
                    # Asegurarse de que las claves por defecto estén presentes si faltan
                    for key, value in self.default_config.items():
                        if key not in existing_config:
                            existing_config[key] = value
                    return existing_config
            except Exception as e:
                self.logger.error(f"[Config] Error leyendo {self.config_path}: {e}")
                # Si hay un error, simplemente usa la configuración por defecto sin sobreescribir
                return self.default_config.copy()
        else:
            self.logger.info(f"[Config] Archivo de configuración no encontrado: {self.config_path}. Creando por defecto.")
            self.config = self.default_config.copy()
            self.save_config()
            return self.config

    def save_config(self):
        """Guarda la configuración en app_config.json"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            self.logger.error(f"[Config] Error guardando {self.config_path}: {e}")

    def get(self, key, default=None):
        """Obtiene un valor de la configuración"""
        return self.config.get(key, default)

    def set(self, key, value):
        """Establece un valor en la configuración y guarda automáticamente"""
        self.config[key] = value
        self.save_config()

    def remove(self, key):
        if key in self.config:
            del self.config[key]
            self.save_config()