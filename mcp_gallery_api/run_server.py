#!/usr/bin/env python3
"""
Script para ejecutar la API de galería MCP de prueba
"""

import sys
import os
from pathlib import Path

# Añadir el directorio padre al path para poder importar módulos
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def main():
    """Ejecuta el servidor de API de galería MCP"""
    
    # Verificar dependencias
    try:
        import uvicorn
        import fastapi
    except ImportError as e:
        print(f"❌ Falta dependencia: {e}")
        print("💡 Instala las dependencias con: pip install -r mcp_gallery_api/requirements.txt")
        return 1
    
    # Directorio actual como directorio de datos
    current_dir = Path(__file__).parent
    
    print("🚀 Iniciando MCP Gallery API...")
    print(f"📁 Directorio de datos: {current_dir}")
    print(f"🌐 URL: http://localhost:8000")
    print(f"📚 Documentación: http://localhost:8000/docs")
    print("⏹️  Presiona Ctrl+C para detener")
    print("-" * 50)
    
    try:
        # Importar y crear la app
        from mcp_gallery_api.server import create_app
        app = create_app(str(current_dir))
        
        # Ejecutar servidor
        uvicorn.run(
            app,
            host="127.0.0.1", 
            port=8000,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\n👋 Servidor detenido")
        return 0
    except Exception as e:
        print(f"❌ Error ejecutando servidor: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())