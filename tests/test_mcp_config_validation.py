import unittest
from pathlib import Path
from assets.logging import PersistentLogger
from mcp_manager import MCPManager

def setUpModule():
    """Configuración que se ejecuta antes de todas las pruebas."""
    # Configurar logging para las pruebas
    global logger, mcp_manager
    logger = PersistentLogger().logger
    logger.info("Iniciando configuración del módulo de pruebas")
    
    # Crear instancia de MCPManager
    mcp_manager = MCPManager(logger)
    
    # Cargar configuración de prueba
    config_path = Path(__file__).parent / "test_config.json"
    if not config_path.exists():
        logger.error(f"Archivo de configuración no encontrado: {config_path}")
        raise FileNotFoundError(f"Archivo de configuración no encontrado: {config_path}")
    
    if not mcp_manager.load_config(str(config_path)):
        logger.error("No se pudo cargar la configuración de prueba")
        raise RuntimeError("No se pudo cargar la configuración de prueba")
    
    logger.info("Configuración cargada exitosamente")

# ... (continuar con el resto del archivo)