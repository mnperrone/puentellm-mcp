# app_config.py

import json
from pathlib import Path
import os
from assets.logging import PersistentLogger

class AppConfig:
    def __init__(self):
        # Directorio de configuración en el home del usuario
        self.config_dir = os.path.join(os.path.expanduser('~'), '.puentellm-mcp')
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        self.config_path = os.path.join(self.config_dir, 'config.json')
        self.logger = PersistentLogger(log_dir=os.path.join(self.config_dir, 'logs'))
        self.default_config = {
            'llm_model': 'llama3',
        }
        self.config = self._load_config()

    def _load_config(self):
        """Carga la configuración desde config.json, crea por defecto si no existe o si está corrupto."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"[Config] Error leyendo {self.config_path}: {e}")
                self.config = self.default_config.copy()
                self.save_config()  # Sobrescribe el archivo corrupto con la config por defecto
                return self.config
        else:
            self.logger.info(f"[Config] Archivo de configuración no encontrado: {self.config_path}. Creando por defecto.")
            self.config = self.default_config.copy()  # Inicializa antes de guardar
            self.save_config()
            return self.config

    def save_config(self):
        """Guarda la configuración en config.json"""
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
