#!/usr/bin/env python3
"""
Test básico simplificado para verificar estructura y funcionalidad principal
"""

import unittest
import os
import sys
import json
from pathlib import Path

# Agregar el directorio raíz al path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestBasicStructure(unittest.TestCase):
    """Tests básicos de estructura del proyecto"""
    
    def setUp(self):
        """Configuración inicial"""
        self.project_root = project_root
    
    def test_main_files_exist(self):
        """Verifica que los archivos principales existan"""
        essential_files = [
            "desktop_app.py",
            "chat_app.py", 
            "README.md",
            "LICENSE"
        ]
        
        for file_name in essential_files:
            file_path = self.project_root / file_name
            self.assertTrue(file_path.exists(), f"Archivo esencial no encontrado: {file_name}")
    
    def test_config_json_valid(self):
        """Verifica que app_config.json sea JSON válido"""
        config_file = self.project_root / "app_config.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.assertIsInstance(config, dict)
            except json.JSONDecodeError:
                self.fail("app_config.json no es JSON válido")
    
    def test_mcp_config_json_valid(self):
        """Verifica que mcp_servers.json sea JSON válido"""
        config_file = self.project_root / "mcp_servers.json"
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.assertIsInstance(config, dict)
                    if 'mcpServers' in config:
                        self.assertIsInstance(config['mcpServers'], dict)
            except json.JSONDecodeError:
                self.fail("mcp_servers.json no es JSON válido")
    
    def test_env_example_exists(self):
        """Verifica que .env.example exista"""
        env_file = self.project_root / ".env.example"
        self.assertTrue(env_file.exists(), ".env.example no encontrado")
    
    def test_python_version(self):
        """Verifica versión de Python"""
        version = sys.version_info
        self.assertGreaterEqual(version.major, 3)
        self.assertGreaterEqual(version.minor, 10)
    
    def test_readme_content(self):
        """Verifica que README tenga contenido básico"""
        readme_file = self.project_root / "README.md"
        if readme_file.exists():
            with open(readme_file, 'r', encoding='utf-8') as f:
                content = f.read()
                self.assertIn("PuenteLLM-MCP", content)
                self.assertIn("Instalación", content)
                self.assertIn("Testing", content)

if __name__ == '__main__':
    unittest.main(verbosity=2)