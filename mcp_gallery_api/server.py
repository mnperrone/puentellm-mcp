"""
Servidor API para la Galería de Servidores MCP
FastAPI server que actúa como catálogo centralizado de servidores MCP.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import json
from pathlib import Path
from typing import Dict, List, Optional
import uvicorn
from pydantic import BaseModel


# Modelos de datos
class MCPServer(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    manifest_url: str
    version: str
    min_client_version: str
    checksum: str
    signature_url: str
    tags: List[str]


class MCPServerDetails(MCPServer):
    """Modelo extendido para detalles del servidor"""
    author: Optional[str] = None
    repository: Optional[str] = None
    homepage: Optional[str] = None
    license: Optional[str] = None
    capabilities: Optional[List[str]] = None
    dependencies: Optional[Dict] = None
    launch_config: Optional[Dict] = None


class MCPGalleryAPI:
    def __init__(self, data_dir: str = None):
        """
        Inicializa la API de la galería MCP.
        
        Args:
            data_dir: Directorio donde están los datos de la galería
        """
        if data_dir is None:
            self.data_dir = Path(__file__).parent
        else:
            self.data_dir = Path(data_dir)
        
        self.gallery_file = self.data_dir / "gallery.json"
        self.static_dir = self.data_dir / "static"
        
        # Crear directorios necesarios
        self.static_dir.mkdir(exist_ok=True)
        (self.static_dir / "manifests").mkdir(exist_ok=True)
        (self.static_dir / "signatures").mkdir(exist_ok=True)
        (self.static_dir / "icons").mkdir(exist_ok=True)
        
        # Inicializar FastAPI
        self.app = FastAPI(
            title="MCP Gallery API",
            description="API centralizada para la galería de servidores MCP",
            version="1.0.0"
        )
        
        # Configurar CORS
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # En producción, especificar dominios exactos
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # Cargar datos
        self._load_gallery_data()
        
        # Configurar rutas
        self._setup_routes()
        self._setup_static_files()
    
    def _load_gallery_data(self):
        """Carga los datos de la galería desde el archivo JSON."""
        try:
            if self.gallery_file.exists():
                with open(self.gallery_file, 'r', encoding='utf-8') as f:
                    self.gallery_data = json.load(f)
            else:
                # Crear archivo de ejemplo si no existe
                self._create_example_gallery()
        except Exception as e:
            print(f"Error cargando datos de galería: {e}")
            self.gallery_data = []
    
    def _create_example_gallery(self):
        """Crea un archivo de galería de ejemplo."""
        # Usar los datos del archivo fallback como base
        fallback_file = self.data_dir.parent / "gallery_fallback.json"
        if fallback_file.exists():
            try:
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    self.gallery_data = json.load(f)
                    
                # Guardar en el archivo de galería
                with open(self.gallery_file, 'w', encoding='utf-8') as f:
                    json.dump(self.gallery_data, f, indent=2, ensure_ascii=False)
                    
                print(f"Creado archivo de galería de ejemplo: {self.gallery_file}")
                return
            except Exception as e:
                print(f"Error copiando fallback: {e}")
        
        # Datos mínimos si no hay fallback
        self.gallery_data = [
            {
                "id": "weather-server",
                "name": "Weather Server",
                "description": "Servidor MCP para consultar información del clima",
                "icon": "https://example.com/icons/weather.png",
                "manifest_url": f"http://localhost:8000/static/manifests/weather-server.json",
                "version": "1.0.0",
                "min_client_version": "1.0.0",
                "checksum": "sha256:placeholder",
                "signature_url": f"http://localhost:8000/static/signatures/weather-server.sig",
                "tags": ["weather", "api"]
            }
        ]
        
        with open(self.gallery_file, 'w', encoding='utf-8') as f:
            json.dump(self.gallery_data, f, indent=2, ensure_ascii=False)
    
    def _setup_routes(self):
        """Configura las rutas de la API."""
        
        @self.app.get("/")
        async def root():
            """Endpoint raíz con información de la API."""
            return {
                "name": "MCP Gallery API",
                "version": "1.0.0",
                "description": "API centralizada para la galería de servidores MCP",
                "endpoints": {
                    "list_servers": "/mcps",
                    "get_server": "/mcps/{server_id}",
                    "static_files": "/static/",
                    "health": "/health"
                },
                "total_servers": len(self.gallery_data)
            }
        
        @self.app.get("/health")
        async def health_check():
            """Endpoint de salud del servicio."""
            return {"status": "healthy", "servers_loaded": len(self.gallery_data)}
        
        @self.app.get("/mcps", response_model=List[MCPServer])
        async def list_mcps():
            """
            Obtiene la lista de todos los servidores MCP disponibles.
            
            Returns:
                Lista de servidores MCP con información básica
            """
            return self.gallery_data
        
        @self.app.get("/mcps/{server_id}")
        async def get_mcp(server_id: str):
            """
            Obtiene detalles extendidos de un servidor MCP específico.
            
            Args:
                server_id: ID del servidor MCP
                
            Returns:
                Detalles completos del servidor
                
            Raises:
                HTTPException: Si el servidor no se encuentra
            """
            for server in self.gallery_data:
                if server["id"] == server_id:
                    # Devolver datos básicos con información adicional simulada
                    extended_info = server.copy()
                    extended_info.update({
                        "author": "MCP Community",
                        "repository": f"https://github.com/mcp-servers/{server_id}",
                        "homepage": f"https://mcp-servers.com/{server_id}",
                        "license": "MIT",
                        "capabilities": ["tools", "resources", "prompts"],
                        "dependencies": {"python": ">=3.8"},
                        "launch_config": {
                            "command": "python",
                            "args": [f"{server_id}.py"],
                            "env": {}
                        }
                    })
                    return extended_info
            
            raise HTTPException(status_code=404, detail=f"Servidor '{server_id}' no encontrado")
        
        @self.app.post("/mcps")
        async def add_mcp(server: MCPServer):
            """
            Añade un nuevo servidor MCP a la galería.
            
            Args:
                server: Datos del nuevo servidor
                
            Returns:
                Confirmación de la operación
            """
            # Verificar que no exista ya
            for existing in self.gallery_data:
                if existing["id"] == server.id:
                    raise HTTPException(status_code=400, detail=f"Servidor '{server.id}' ya existe")
            
            # Añadir a la lista
            server_dict = server.dict()
            self.gallery_data.append(server_dict)
            
            # Guardar en archivo
            try:
                with open(self.gallery_file, 'w', encoding='utf-8') as f:
                    json.dump(self.gallery_data, f, indent=2, ensure_ascii=False)
                return {"message": f"Servidor '{server.id}' añadido exitosamente"}
            except Exception as e:
                # Revertir cambio en memoria
                self.gallery_data.pop()
                raise HTTPException(status_code=500, detail=f"Error guardando servidor: {e}")
        
        @self.app.delete("/mcps/{server_id}")
        async def remove_mcp(server_id: str):
            """
            Elimina un servidor MCP de la galería.
            
            Args:
                server_id: ID del servidor a eliminar
                
            Returns:
                Confirmación de la operación
            """
            for i, server in enumerate(self.gallery_data):
                if server["id"] == server_id:
                    removed_server = self.gallery_data.pop(i)
                    
                    # Guardar cambios
                    try:
                        with open(self.gallery_file, 'w', encoding='utf-8') as f:
                            json.dump(self.gallery_data, f, indent=2, ensure_ascii=False)
                        return {"message": f"Servidor '{server_id}' eliminado exitosamente"}
                    except Exception as e:
                        # Revertir cambio
                        self.gallery_data.insert(i, removed_server)
                        raise HTTPException(status_code=500, detail=f"Error eliminando servidor: {e}")
            
            raise HTTPException(status_code=404, detail=f"Servidor '{server_id}' no encontrado")
        
        @self.app.get("/search")
        async def search_mcps(q: str = "", tags: str = ""):
            """
            Busca servidores MCP por nombre, descripción o tags.
            
            Args:
                q: Término de búsqueda
                tags: Tags separados por coma
                
            Returns:
                Lista de servidores que coinciden con la búsqueda
            """
            results = self.gallery_data.copy()
            
            # Filtrar por término de búsqueda
            if q:
                q_lower = q.lower()
                results = [
                    server for server in results
                    if (q_lower in server["name"].lower() or
                        q_lower in server["description"].lower())
                ]
            
            # Filtrar por tags
            if tags:
                search_tags = [tag.strip().lower() for tag in tags.split(",")]
                results = [
                    server for server in results
                    if any(tag in [t.lower() for t in server.get("tags", [])] for tag in search_tags)
                ]
            
            return results
    
    def _setup_static_files(self):
        """Configura el servido de archivos estáticos."""
        # Montar directorio estático
        self.app.mount("/static", StaticFiles(directory=str(self.static_dir)), name="static")
        
        # Crear algunos archivos de ejemplo si no existen
        self._create_example_static_files()
    
    def _create_example_static_files(self):
        """Crea archivos estáticos de ejemplo."""
        
        # Manifest de ejemplo para weather-server
        manifest_example = {
            "name": "weather-server",
            "version": "1.0.0",
            "description": "Servidor MCP para consultar información del clima",
            "main": "weather.py",
            "capabilities": {
                "tools": [
                    {
                        "name": "get_weather",
                        "description": "Obtiene el clima actual de una ciudad",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "city": {
                                    "type": "string",
                                    "description": "Nombre de la ciudad"
                                }
                            },
                            "required": ["city"]
                        }
                    }
                ]
            },
            "launch": {
                "command": "python",
                "args": ["weather.py"]
            }
        }
        
        manifest_file = self.static_dir / "manifests" / "weather-server.json"
        if not manifest_file.exists():
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest_example, f, indent=2, ensure_ascii=False)
        
        # Archivo de firma de ejemplo
        signature_file = self.static_dir / "signatures" / "weather-server.sig"
        if not signature_file.exists():
            signature_file.write_text("-----BEGIN PGP SIGNATURE-----\nExample signature\n-----END PGP SIGNATURE-----")


def create_app(data_dir: str = None) -> FastAPI:
    """
    Factory function para crear la aplicación FastAPI.
    
    Args:
        data_dir: Directorio de datos personalizado
        
    Returns:
        Instancia configurada de FastAPI
    """
    gallery_api = MCPGalleryAPI(data_dir)
    return gallery_api.app


def main():
    """Función principal para ejecutar el servidor."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Servidor API para la Galería MCP")
    parser.add_argument("--host", default="127.0.0.1", help="Host a usar")
    parser.add_argument("--port", type=int, default=8000, help="Puerto a usar")
    parser.add_argument("--data-dir", help="Directorio de datos personalizado")
    parser.add_argument("--reload", action="store_true", help="Habilitar recarga automática")
    
    args = parser.parse_args()
    
    # Crear aplicación
    app = create_app(args.data_dir)
    
    # Configurar logging
    print(f"🚀 Iniciando MCP Gallery API en http://{args.host}:{args.port}")
    print(f"📊 Documentación disponible en http://{args.host}:{args.port}/docs")
    
    # Ejecutar servidor
    uvicorn.run(
        "mcp_gallery_api.server:create_app" if args.reload else app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        factory=args.reload
    )


if __name__ == "__main__":
    main()