import unittest
from assets.logging import PersistentLogger
import json
import os
from mcp_manager import MCPManager

def validate_server_config(server_name, server_config):
    """
    Valida la configuración de un servidor MCP específico.
    
    Args:
        server_name: Nombre del servidor
        server_config: Diccionario con la configuración del servidor
    Returns:
        Tuple (bool, str): (Éxito, mensaje)
    """
    logger = PersistentLogger().logger
    logger.info(f"Validando configuración para servidor '{server_name}'")
    
    # Validaciones específicas según el tipo de servidor
    server_type = server_config.get('type')
    if not server_type or server_type not in ['local', 'remote', 'npm']:
        return False, f"Tipo de servidor '{server_type}' es inválido o no está definido."

    common_fields = {'enabled': bool, 'auto_restart': bool}
    type_specific_fields = {
        'local': {'workdir': str, 'command': str, 'args': list, 'port': int},
        'npm': {'workdir': str, 'command': str, 'args': list, 'port': int},
        'remote': {'url': str}
    }

    required_fields = {**common_fields, **type_specific_fields.get(server_type, {})}

    for field, field_type in required_fields.items():
        if field not in server_config:
            return False, f"Falta campo '{field}' en servidor '{server_name}' de tipo '{server_type}'"
        if not isinstance(server_config[field], field_type):
            return False, f"Tipo inválido para '{field}' en servidor '{server_name}', se esperaba {field_type}"

    # Validaciones adicionales
    if server_type in ['local', 'npm']:
        if not os.path.exists(server_config['workdir']):
            return False, f"Directorio de trabajo no existe para servidor '{server_name}': {server_config['workdir']}"
    
    if server_type == 'remote':
        # La prueba de conexión se puede hacer por separado, aquí solo validamos la presencia y tipo de URL
        pass
    
    logger.info(f"Configuración validada exitosamente para servidor '{server_name}'")
    return True, ""

class TestMCPConfiguration(unittest.TestCase):
    """Pruebas para validar la configuración de los servidores MCP."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.logger = PersistentLogger().logger
        self.logger.info("Iniciando test de validación de configuración MCP")
        self.config_path = "tests/test_config.json"
        self.mcp_manager = MCPManager(self.logger)
    
    def test_load_and_validate_config(self):
        """Prueba que se pueda cargar y validar la configuración MCP."""
        self.logger.info("Probando carga y validación de configuración MCP")
        result = self.mcp_manager.load_config(self.config_path)
        self.assertTrue(result, "No se pudo cargar la configuración")
        
        servers = self.mcp_manager.servers_config.get('mcpServers', {})
        self.assertGreater(len(servers), 0, "No hay servidores definidos en la configuración")
        
        for server_name, server_config in servers.items():
            with self.subTest(server=server_name):
                validation_result, validation_message = validate_server_config(server_name, server_config)
                self.assertTrue(validation_result, validation_message)
    
    def test_invalid_configurations(self):
        """Prueba que se detecten correctamente las configuraciones inválidas."""
        invalid_configs = [
            {
                "invalid_server": {
                    "type": "unknown",  # Tipo desconocido
                    "enabled": True,
                    "auto_restart": False,
                    "workdir": ".",
                    "command": "python",
                    "args": ["-m", "modelcontextprotocol.servers.filesystem"]
                }
            },
            {
                "invalid_server": {
                    "type": "local",  # Tipo válido pero directorio inválido
                    "enabled": True,
                    "auto_restart": False,
                    "workdir": "/path/to/nowhere",  # Directorio inexistente
                    "command": "python",
                    "args": ["-m", "modelcontextprotocol.servers.filesystem"]
                }
            },
            {
                "invalid_server": {
                    "type": "remote",  # Tipo válido pero sin URL
                    "enabled": True,
                    "auto_restart": False
                }
            }
        ]
        
        for config in invalid_configs:
            with self.subTest(config=config):
                self.mcp_manager.servers_config = config
                validation_result, validation_message = validate_server_config(
                    list(config.keys())[0], 
                    list(config.values())[0]
                )
                self.assertFalse(validation_result, "Se esperaba una validación fallida")
                self.assertIsNotNone(validation_message, "Se esperaba un mensaje de error")
                self.logger.warning(f"Prueba de configuración inválida pasada: {validation_message}")

if __name__ == '__main__':
    unittest.main()