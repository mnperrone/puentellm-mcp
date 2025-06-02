import unittest
from puentellm_mcp_assets.logging import setup_logging
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
    logger = setup_logging()
    logger.info(f"Validando configuración para servidor '{server_name}'")
    
    # Verificar que el servidor tenga los campos necesarios
    required_fields = {
        'type': ['local', 'remote', 'npm'],  # Tipos soportados
        'enabled': bool,  # Debe ser booleano
        'auto_restart': bool,  # Debe ser booleano
        'workdir': str,  # Directorio de trabajo
        'command': str,  # Comando a ejecutar
        'args': list,  # Argumentos del comando
        'port': int,  # Puerto del servidor
        'url': str  # URL para servidores remotos
    }
    
    for field, field_type in required_fields.items():
        if field not in server_config:
            logger.error(f"Servidor '{server_name}' no tiene el campo requerido '{field}'")
            return False, f"Falta campo '{field}' en servidor '{server_name}'"
        
        # Si el campo es una lista, verificar que tenga elementos
        if isinstance(field_type, list):
            if server_config[field] not in field_type:
                logger.error(f"Valor inválido para '{field}' en servidor '{server_name}': {server_config[field]}")
                return False, f"Valor inválido para '{field}' en servidor '{server_name}'"
        else:
            if not isinstance(server_config[field], field_type):
                logger.error(f"Tipo inválido para '{field}' en servidor '{server_name}': {type(server_config[field])}")
                return False, f"Tipo inválido para '{field}' en servidor '{server_name}'"
    
    # Validaciones específicas según el tipo de servidor
    server_type = server_config['type']
    
    if server_type == 'local' or server_type == 'npm':
        if not os.path.exists(server_config['workdir']):
            logger.error(f"Directorio de trabajo no existe para servidor '{server_name}': {server_config['workdir']}")
            return False, f"Directorio de trabajo no existe para servidor '{server_name}'"
    
    if server_type == 'remote':
        try:
            import requests
            response = requests.get(server_config['url'])
            response.raise_for_status()
        except Exception as e:
            logger.error(f"No se pudo conectar al servidor remoto '{server_name}': {e}")
            return False, f"No se pudo conectar al servidor remoto '{server_name}'"
    
    logger.info(f"Configuración validada exitosamente para servidor '{server_name}'")
    return True, ""

class TestMCPConfiguration(unittest.TestCase):
    """Pruebas para validar la configuración de los servidores MCP."""
    
    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.logger = setup_logging()
        self.logger.info("Iniciando test de validación de configuración MCP")
        self.config_path = "test_config.json"
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
                    "type": "remote",  # Tipo válido pero URL inválida
                    "enabled": True,
                    "auto_restart": False,
                    "url": "http://localhost:9999"  # Puerto probablemente cerrado
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