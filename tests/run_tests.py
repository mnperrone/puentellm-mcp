#!/usr/bin/env python3
"""Script para ejecutar las pruebas del sistema PuenteLLM-MCP con logging persistente."""
import os
import sys
import unittest
import argparse
from puentellm_mcp_assets.logging import setup_persistent_logging, setup_logging
import logging

def run_tests(log_file=None):
    """Ejecuta todas las pruebas del sistema."""
    # Configurar logging
    logger = setup_logging()
    
    # Si se proporciona un archivo de log, configurar logging persistente
    persistent_logger = None
    if log_file:
        persistent_logger = setup_persistent_logging(log_file)
        logger.info(f"Logging persistente activado. Logs se guardarán en {log_file}")
    
    # Descubrir y ejecutar pruebas
    try:
        logger.info("Descubriendo pruebas...")
        test_suite = unittest.defaultTestLoader.discover(start_dir='.', pattern="test_*.py")
        
        logger.info("Ejecutando pruebas...")
        result = unittest.TextTestRunner(verbosity=2).run(test_suite)
        
        # Registrar resultados
        total_tests = result.testsRun
        successes = len(result.successes) if hasattr(result, 'successes') else 0
        failures = len(result.failures) if hasattr(result, 'failures') else 0
        errors = len(result.errors) if hasattr(result, 'errors') else 0
        
        logger.info(f"Total de pruebas: {total_tests}")
        logger.info(f"Éxitos: {successes}")
        logger.info(f"Fallos: {failures}")
        logger.info(f"Errores: {errors}")
        
        return result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error al ejecutar pruebas: {e}", exc_info=True)
        if persistent_logger:
            persistent_logger.error(f"Error al ejecutar pruebas: {e}", exc_info=True)
        return False

if __name__ == '__main__':
    # Parsear argumentos de línea de comandos
    parser = argparse.ArgumentParser(description="Ejecutar pruebas del sistema PuenteLLM-MCP")
    parser.add_argument('--log-file', '-l', 
                        help="Ruta al archivo de log persistente", 
                        default="~/.puentellm-mcp/test_logs/system_test.log")
    args = parser.parse_args()
    
    # Expandir ~ a directorio home si está presente
    log_path = os.path.expanduser(args.log_file)
    log_dir = os.path.dirname(log_path)
    
    # Crear directorio para logs si no existe
    os.makedirs(log_dir, exist_ok=True)
    
    # Ejecutar pruebas
    success = run_tests(log_path)
    
    # Salir con código adecuado
    sys.exit(0 if success else 1)