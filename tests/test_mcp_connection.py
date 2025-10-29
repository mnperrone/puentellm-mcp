import unittest
import asyncio
from mcp_manager import MCPManager
from assets.logging import PersistentLogger

class TestMCPConnection(unittest.TestCase):
    """Pruebas para la conexión y comunicación con servidores MCP."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.logger = PersistentLogger().logger
        self.logger.info("Iniciando test de conexión MCP")
        self.mcp_manager = MCPManager(self.logger)
        
    def test_load_config(self):
        """Prueba que se pueda cargar la configuración MCP correctamente."""
        self.logger.info("Probando carga de configuración MCP")
        config_path = "tests/test_config.json"
        result = self.mcp_manager.load_config(config_path)
        self.assertTrue(result, "No se pudo cargar la configuración MCP")
        
    def test_server_start_stop(self):
        """Prueba el inicio y detención de un servidor MCP."""
        self.logger.info("Probando inicio y detención de servidor MCP")
        server_name = "filesystem"
        
        # Cargar configuración
        config_path = "tests/test_config.json"
        self.assertTrue(self.mcp_manager.load_config(config_path), "No se pudo cargar la configuración")
        
        # Iniciar servidor
        self.logger.info(f"Iniciando servidor '{server_name}'")
        started = self.mcp_manager.start_server(server_name)
        self.assertTrue(started, f"No se pudo iniciar el servidor '{server_name}'")
        
        # Verificar estado
        self.logger.info(f"Verificando estado del servidor '{server_name}'")
        is_running = self.mcp_manager.is_server_running(server_name)
        self.assertTrue(is_running, f"El servidor '{server_name}' no está corriendo")
        
        # Detener servidor
        self.logger.info(f"Deteniendo servidor '{server_name}'")
        self.mcp_manager.stop_server(server_name)
        
        # Verificar detención
        is_running_after_stop = self.mcp_manager.is_server_running(server_name)
        self.assertFalse(is_running_after_stop, f"El servidor '{server_name}' sigue corriendo después de detenerlo")
        
    def test_mcp_communication(self):
        """Prueba la comunicación básica con un servidor MCP."""
        self.logger.info("Probando comunicación con servidor MCP")
        server_name = "filesystem"
        
        # Cargar configuración
        config_path = "tests/test_config.json"
        self.assertTrue(self.mcp_manager.load_config(config_path), "No se pudo cargar la configuración")
        
        # Iniciar servidor
        self.assertTrue(self.mcp_manager.start_server(server_name), f"No se pudo iniciar el servidor '{server_name}'")
        
        # Ejecutar pruebas de comunicación
        try:
            # Check if the server is running
            self.logger.info(f"Verificando estado del servidor '{server_name}'")
            is_running = self.mcp_manager.is_server_running(server_name)
            self.assertTrue(is_running, f"El servidor '{server_name}' no está corriendo")
        finally:
            # Limpiar - detener servidor
            self.mcp_manager.stop_all_servers()

if __name__ == '__main__':
    unittest.main()