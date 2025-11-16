"""
Utilidades para la gestión de la API de Galería MCP
"""

import json
import hashlib
import requests
from pathlib import Path
from typing import Dict, List
import shutil


class GalleryDataManager:
    """Gestor de datos para la galería MCP"""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.gallery_file = data_dir / "gallery.json"
        self.static_dir = data_dir / "static"
    
    def import_from_github(self, repo_url: str, manifest_path: str = "manifest.json") -> Dict:
        """
        Importa un servidor MCP desde un repositorio de GitHub.
        
        Args:
            repo_url: URL del repositorio de GitHub
            manifest_path: Ruta al manifest dentro del repo
            
        Returns:
            Datos del servidor importado
        """
        try:
            # Extraer info del repo
            if "github.com" not in repo_url:
                raise ValueError("Solo se soportan repositorios de GitHub")
            
            # Convertir a URL de API
            repo_path = repo_url.replace("https://github.com/", "").replace(".git", "")
            api_url = f"https://api.github.com/repos/{repo_path}/contents/{manifest_path}"
            
            # Descargar manifest
            response = requests.get(api_url)
            response.raise_for_status()
            
            # Decodificar contenido base64
            import base64
            content = base64.b64decode(response.json()["content"]).decode('utf-8')
            manifest = json.loads(content)
            
            # Crear entrada de servidor
            server_data = self._manifest_to_server(manifest, repo_url)
            
            return server_data
            
        except Exception as e:
            raise Exception(f"Error importando desde GitHub: {e}")
    
    def _manifest_to_server(self, manifest: Dict, repo_url: str) -> Dict:
        """Convierte un manifest MCP a formato de servidor de galería."""
        
        server_id = manifest.get("name", "unknown-server")
        
        return {
            "id": server_id,
            "name": manifest.get("description", server_id.title()),
            "description": manifest.get("description", "Servidor MCP"),
            "icon": "https://github.com/favicon.ico",  # Icono por defecto
            "manifest_url": f"https://raw.githubusercontent.com/{repo_url.split('/')[-2:]}/main/manifest.json",
            "version": manifest.get("version", "1.0.0"),
            "min_client_version": "1.0.0",
            "checksum": "sha256:placeholder",  # Se calcularía en un proceso real
            "signature_url": "",
            "tags": manifest.get("tags", ["community"]),
            "repository": repo_url,
            "capabilities": list(manifest.get("capabilities", {}).keys())
        }
    
    def validate_server_data(self, server: Dict) -> List[str]:
        """
        Valida los datos de un servidor MCP.
        
        Args:
            server: Datos del servidor a validar
            
        Returns:
            Lista de errores encontrados (vacía si es válido)
        """
        errors = []
        required_fields = ["id", "name", "description", "version", "manifest_url"]
        
        for field in required_fields:
            if field not in server or not server[field]:
                errors.append(f"Campo requerido faltante: {field}")
        
        # Validar formato de versión
        version = server.get("version", "")
        if version and not self._is_valid_version(version):
            errors.append(f"Formato de versión inválido: {version}")
        
        # Validar URLs
        for url_field in ["manifest_url", "signature_url", "icon"]:
            url = server.get(url_field, "")
            if url and not self._is_valid_url(url):
                errors.append(f"URL inválida en {url_field}: {url}")
        
        return errors
    
    def _is_valid_version(self, version: str) -> bool:
        """Valida formato de versión semántica básica."""
        import re
        pattern = r'^\d+\.\d+\.\d+$'
        return bool(re.match(pattern, version))
    
    def _is_valid_url(self, url: str) -> bool:
        """Valida formato de URL básico."""
        return url.startswith(("http://", "https://"))
    
    def calculate_checksum(self, content: bytes, algorithm: str = "sha256") -> str:
        """Calcula el checksum de contenido."""
        hasher = hashlib.new(algorithm)
        hasher.update(content)
        return f"{algorithm}:{hasher.hexdigest()}"
    
    def backup_gallery(self) -> Path:
        """Crea una copia de seguridad de la galería."""
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = self.data_dir / f"gallery_backup_{timestamp}.json"
        
        if self.gallery_file.exists():
            shutil.copy2(self.gallery_file, backup_file)
            return backup_file
        
        raise FileNotFoundError("No hay archivo de galería para respaldar")
    
    def restore_gallery(self, backup_file: Path):
        """Restaura la galería desde un backup."""
        if not backup_file.exists():
            raise FileNotFoundError(f"Archivo de backup no encontrado: {backup_file}")
        
        shutil.copy2(backup_file, self.gallery_file)


class ServerValidator:
    """Validador de servidores MCP"""
    
    @staticmethod
    def validate_manifest(manifest_url: str) -> tuple[bool, str]:
        """
        Valida que un manifest MCP sea accesible y válido.
        
        Args:
            manifest_url: URL del manifest a validar
            
        Returns:
            Tupla (es_válido, mensaje)
        """
        try:
            response = requests.get(manifest_url, timeout=10)
            response.raise_for_status()
            
            # Verificar que es JSON válido
            manifest = response.json()  # Necesario para validación posterior
            
            # Verificar campos básicos requeridos
            required = ["name", "version"]
            for field in required:
                if field not in manifest:
                    return False, f"Campo requerido faltante en manifest: {field}"
            
            return True, "Manifest válido"
            
        except requests.RequestException as e:
            return False, f"Error accediendo al manifest: {e}"
        except json.JSONDecodeError:
            return False, "El manifest no es un JSON válido"
        except Exception as e:
            return False, f"Error validando manifest: {e}"
    
    @staticmethod
    def check_server_health(manifest_url: str) -> tuple[bool, Dict]:
        """
        Verifica el estado de salud de un servidor MCP.
        
        Returns:
            Tupla (saludable, info_salud)
        """
        health_info = {
            "manifest_accessible": False,
            "manifest_valid": False,
            "response_time": 0,
            "last_check": None
        }
        
        try:
            from datetime import datetime
            import time
            
            start_time = time.time()
            
            # Verificar acceso al manifest
            response = requests.get(manifest_url, timeout=5)
            response.raise_for_status()
            
            health_info["response_time"] = time.time() - start_time
            health_info["manifest_accessible"] = True
            
            # Validar contenido
            manifest = response.json()
            health_info["manifest_valid"] = True
            
            health_info["last_check"] = datetime.now().isoformat()
            
            return True, health_info
            
        except Exception as e:
            health_info["error"] = str(e)
            health_info["last_check"] = datetime.now().isoformat()
            return False, health_info