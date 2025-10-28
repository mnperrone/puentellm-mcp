import unittest
from assets.logging import PersistentLogger

class TestBasicFunctionality(unittest.TestCase):
    """Prueba funcionalidad básica del sistema con logging persistente."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.logger = PersistentLogger().logger
        self.logger.info(f"Iniciando prueba: {self._testMethodName}")
        
    def tearDown(self):
        """Limpieza después de cada prueba."""
        self.logger.info(f"Finalizando prueba: {self._testMethodName}")
        
    def test_basic_server_status(self):
        """Prueba funcionalidad básica de estado de servidores."""
        from mcp_manager import MCPManager
        manager = MCPManager(self.logger)
        config_path = "tests/test_config.json"
        
        # Cargar configuración
        self.logger.info("Probando carga de configuración")
        result = manager.load_config(config_path)
        self.assertTrue(result, "No se pudo cargar la configuración")
        
        # Iniciar servidores
        self.logger.info("Probando inicio de servidores")
        manager.start_all_servers()
        
        # Verificar estado
        self.logger.info("Verificando estado de servidores")
        active_servers = manager.get_active_server_names()
        self.assertIn('filesystem', active_servers, "Servidor 'filesystem' no está activo")
        
        # Limpiar y salir
        self.logger.info("Limpiando recursos")
        manager.stop_all_servers()

if __name__ == '__main__':
    unittest.main()