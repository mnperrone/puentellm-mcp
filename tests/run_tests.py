#!/usr/bin/env python3
"""
Script principal para ejecutar todos los tests de PuenteLLM-MCP
"""

import os
import sys
import subprocess
import json
from pathlib import Path

def run_test_file(test_file):
    """Ejecuta un archivo de test específico"""
    print(f"\n🧪 Ejecutando {test_file}...")
    print("="*50)
    
    try:
        result = subprocess.run([sys.executable, test_file], 
                              capture_output=True, text=True, cwd=Path(__file__).parent)
        
        if result.returncode == 0:
            print(f"✅ {test_file} - ÉXITO")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ {test_file} - FALLO")
            if result.stdout:
                print("STDOUT:", result.stdout)
            if result.stderr:
                print("STDERR:", result.stderr)
        
        return result.returncode == 0
    
    except Exception as e:
        print(f"❌ Error ejecutando {test_file}: {e}")
        return False

def main():
    """Función principal que ejecuta todos los tests"""
    print("🚀 Iniciando Test Suite de PuenteLLM-MCP")
    print("="*60)
    
    # Cambiar al directorio de tests
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    # Lista de tests a ejecutar
    test_files = [
        "test_basic_structure.py",
        "test_core_functionality.py"
    ]
    
    # Verificar que los archivos de test existen
    existing_tests = []
    for test_file in test_files:
        if Path(test_file).exists():
            existing_tests.append(test_file)
        else:
            print(f"⚠️  Test no encontrado: {test_file}")
    
    if not existing_tests:
        print("❌ No se encontraron archivos de test para ejecutar")
        sys.exit(1)
    
    print(f"📋 Tests a ejecutar: {len(existing_tests)}")
    for test in existing_tests:
        print(f"   • {test}")
    
    # Ejecutar tests
    results = []
    for test_file in existing_tests:
        success = run_test_file(test_file)
        results.append((test_file, success))
    
    # Resumen final
    print(f"\n{'='*60}")
    print("📊 RESUMEN FINAL")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)
    failed_tests = total_tests - passed_tests
    
    print(f"Total de test suites: {total_tests}")
    print(f"✅ Éxitos: {passed_tests}")
    print(f"❌ Fallos: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 ¡Todos los tests pasaron exitosamente!")
        sys.exit(0)
    else:
        print(f"\n💥 {failed_tests} test suite(s) fallaron:")
        for test_file, success in results:
            if not success:
                print(f"   • {test_file}")
        sys.exit(1)

if __name__ == "__main__":
    main()