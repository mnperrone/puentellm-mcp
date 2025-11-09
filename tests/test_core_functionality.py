#!/usr/bin/env python3
"""
Test Suite Principal para PuenteLLM-MCP
Ejecuta todos los tests básicos para verificar funcionalidad core
"""

import unittest
import os
import sys
import json
from pathlib import Path

# Agregar el directorio raíz al path para imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

class TestCoreApplication(unittest.TestCase):
    """Tests básicos para verificar funcionalidad principal de la aplicación"""
    
    def setUp(self):
        """Configuración inicial para tests"""
        self.project_root = project_root
        self.config_file = self.project_root / "app_config.json"
        self.mcp_config_file = self.project_root / "mcp_servers.json"
        self.env_example_file = self.project_root / ".env.example"
    
    def test_project_structure(self):
        """Verifica que la estructura del proyecto sea correcta"""
        required_files = [
            "desktop_app.py",
            "chat_app.py", 
            "llm_bridge.py",
            "mcp_manager.py",
            "app_config.py",
            "env_manager.py",
            "README.md",
            "LICENSE"
        ]
        
        for file_name in required_files:
            file_path = self.project_root / file_name
            self.assertTrue(file_path.exists(), f"Archivo requerido no encontrado: {file_name}")
    
    def test_config_files_validity(self):
        """Verifica que los archivos de configuración sean válidos"""
        # Test app_config.json
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.assertIsInstance(config, dict)
                    # Verificar estructura básica
                    self.assertIn('llm_provider', config)
                    self.assertIn('llm_provider_configs', config)
            except json.JSONDecodeError as e:
                self.fail(f"app_config.json no es JSON válido: {e}")
        
        # Test mcp_servers.json
        if self.mcp_config_file.exists():
            try:
                with open(self.mcp_config_file, 'r', encoding='utf-8') as f:
                    mcp_config = json.load(f)
                    self.assertIsInstance(mcp_config, dict)
                    self.assertIn('mcpServers', mcp_config)
            except json.JSONDecodeError as e:
                self.fail(f"mcp_servers.json no es JSON válido: {e}")
    
    def test_env_example_exists(self):
        """Verifica que el archivo .env.example exista para configuración"""
        self.assertTrue(self.env_example_file.exists(), ".env.example no encontrado")
        
        # Verificar que contenga las variables importantes
        with open(self.env_example_file, 'r') as f:
            content = f.read()
            important_vars = ["OPENROUTER_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"]
            for var in important_vars:
                self.assertIn(var, content, f"Variable {var} no encontrada en .env.example")
    
    def test_llm_providers_structure(self):
        """Verifica que los providers de LLM tengan la estructura correcta"""
        providers_dir = self.project_root / "llm_providers"
        self.assertTrue(providers_dir.exists(), "Directorio llm_providers no encontrado")
        
        # Verificar archivos principales
        required_provider_files = [
            "__init__.py",
            "llm_exception.py",
            "ollama_handler.py",
            "openrouter_handler.py"
        ]
        
        for file_name in required_provider_files:
            file_path = providers_dir / file_name
            self.assertTrue(file_path.exists(), f"Provider file no encontrado: {file_name}")
    
    def test_app_config_import(self):
        """Verifica que AppConfig se pueda importar correctamente"""
        try:
            from app_config import AppConfig
            config = AppConfig()
            # Verificar que tenga métodos básicos
            self.assertTrue(hasattr(config, 'get'))
            self.assertTrue(hasattr(config, 'set'))
            # AppConfig usa save_config en lugar de save
            self.assertTrue(hasattr(config, 'save_config'))
        except ImportError as e:
            self.fail(f"No se pudo importar AppConfig: {e}")
    
    def test_env_manager_import(self):
        """Verifica que EnvManager se pueda importar correctamente"""
        try:
            from env_manager import EnvManager
            # Verificar que tenga métodos básicos
            self.assertTrue(hasattr(EnvManager, 'load_env_file'))
            self.assertTrue(hasattr(EnvManager, 'get_api_key'))
        except ImportError as e:
            self.fail(f"No se pudo importar EnvManager: {e}")
    
    def test_mcp_manager_import(self):
        """Verifica que MCPManager se pueda importar correctamente"""
        try:
            from mcp_manager import MCPManager
            manager = MCPManager()
            # Verificar que tenga métodos básicos
            self.assertTrue(hasattr(manager, 'start_server'))
            self.assertTrue(hasattr(manager, 'stop_server'))
        except ImportError as e:
            self.fail(f"No se pudo importar MCPManager: {e}")

class TestEnvironmentSetup(unittest.TestCase):
    """Tests para verificar que el entorno esté configurado correctamente"""
    
    def test_python_version(self):
        """Verifica que la versión de Python sea compatible"""
        import sys
        version = sys.version_info
        self.assertGreaterEqual(version.major, 3, "Se requiere Python 3.x")
        self.assertGreaterEqual(version.minor, 10, "Se requiere Python 3.10+")
    
    def test_critical_imports(self):
        """Verifica que las dependencias críticas estén disponibles"""
        critical_modules = [
            'customtkinter',
            'tkinter',
            'json',
            'pathlib',
            'os',
            'sys'
        ]
        
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError:
                self.fail(f"Módulo crítico no disponible: {module}")

if __name__ == '__main__':
    # Configurar el suite de tests
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Agregar las clases de test
    suite.addTests(loader.loadTestsFromTestCase(TestCoreApplication))
    suite.addTests(loader.loadTestsFromTestCase(TestEnvironmentSetup))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar resumen
    print(f"\n{'='*50}")
    print(f"RESUMEN DE TESTS")
    print(f"{'='*50}")
    print(f"Tests ejecutados: {result.testsRun}")
    print(f"Éxitos: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Fallos: {len(result.failures)}")
    print(f"Errores: {len(result.errors)}")
    
    if result.failures:
        print(f"\nFALLOS:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback.split('AssertionError: ')[-1].strip()}")
    
    if result.errors:
        print(f"\nERRORES:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback.split('Exception: ')[-1].strip()}")
    
    # Exit code
    sys.exit(0 if result.wasSuccessful() else 1)