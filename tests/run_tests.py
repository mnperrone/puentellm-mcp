#!/usr/bin/env python3
"""Script para ejecutar las pruebas del sistema PuenteLLM-MCP con logging persistente."""
import os
import sys
import unittest
import argparse
from assets.logging import PersistentLogger
import logging

def run_tests(log_file=None):
    """Ejecuta todas las pruebas del sistema."""
    # Configurar logging
    logger = PersistentLogger(log_dir=os.path.dirname(log_file)).logger
    logger.info(f"Logging persistente activado. Logs se guardarán en {log_file}")
    
    # Descubrir y ejecutar pruebas
    try:
        logger.info("Descubriendo pruebas...")
        test_loader = unittest.TestLoader()
        test_suite = test_loader.discover(start_dir='tests', pattern="test_*.py")
        
        logger.info("Ejecutando pruebas...")
        result = unittest.TextTestRunner(verbosity=2).run(test_suite)
        
        # Registrar resultados
        total_tests = result.testsRun
        failures = len(result.failures)
        errors = len(result.errors)
        successes = total_tests - failures - errors
        
        logger.info(f"Total de pruebas: {total_tests}")
        logger.info(f"Éxitos: {successes}")
        logger.info(f"Fallos: {failures}")
        logger.info(f"Errores: {errors}")
        
        return result.wasSuccessful()
    except Exception as e:
        logger.error(f"Error al ejecutar pruebas: {e}", exc_info=True)
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