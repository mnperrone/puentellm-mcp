"""
Gestor de la Galería de Servidores MCP
Maneja la instalación, verificación y gestión de servidores MCP desde una API centralizada.
"""

import json
import hashlib
import requests
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from assets.logging import PersistentLogger
from jsonschema import validate, ValidationError

# Importar el gestor de Docker MCP
try:
    from docker_mcp_manager import DockerMCPManager
except ImportError:
    DockerMCPManager = None


class MCPGalleryManager:
    def __init__(self, config_dir: Optional[str] = None, mcp_manager=None, external_logger=None):
        """
        Inicializa el gestor de la galería MCP.
        
        Args:
            config_dir: Directorio base para configuración. Si es None, usa ~/.config/puentellm-mcp
            mcp_manager: Instancia de MCPManager existente (opcional)
            external_logger: Logger externo a usar (por ejemplo, de la aplicación principal)
        """
        if config_dir is None:
            # Auto-detectar directorio: si estamos en el proyecto y ya hay archivos, usarlo
            project_dir = Path(__file__).parent
            project_installed_file = project_dir / "installed_servers.json"
            
            if project_installed_file.exists():
                self.base_dir = project_dir
            else:
                self.base_dir = Path.home() / ".config" / "puentellm-mcp"
        else:
            self.base_dir = Path(config_dir)
            
        # Usar mcp_manager pasado o crear uno nuevo
        self.mcp_manager = mcp_manager
            
        self.mcps_dir = self.base_dir / "mcps"
        self.installed_servers_file = self.base_dir / "installed_servers.json"
        self.public_keys_dir = self.base_dir / "public_keys"
        
        # Crear directorios si no existen
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.mcps_dir.mkdir(parents=True, exist_ok=True)
        self.public_keys_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger: usar externo si está disponible, sino crear uno propio
        if external_logger:
            self.logger = external_logger
            self.logger.info("MCPGalleryManager usando logger externo")
        else:
            log_dir = self.base_dir / "logs"
            log_dir.mkdir(exist_ok=True)
            self.logger = PersistentLogger(log_dir=str(log_dir))
        
        # Rutas de archivos de datos
        self.fallback_data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gallery_fallback.json")
        self.extended_gallery_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gallery_extended.json")
        self.schema_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server_schema.json")
        
        # API endpoints
        self.official_api_url = "https://registry.modelcontextprotocol.io/v0/servers"
        self.fallback_api_url = os.environ.get("MCP_REGISTRY_FALLBACK_URL", "http://localhost:8000")  # Configurable desde .env
        
        # Inicializar gestor de Docker MCP si está disponible
        self.docker_manager = None
        if DockerMCPManager:
            try:
                self.docker_manager = DockerMCPManager(str(self.base_dir))
                self.logger.info("Gestor de Docker MCP inicializado")
            except Exception as e:
                self.logger.warning(f"No se pudo inicializar gestor Docker MCP: {e}")
        else:
            self.logger.info("Gestor Docker MCP no disponible")
        
    def get_installed_servers(self) -> Dict:
        """Obtiene la lista de servidores instalados localmente."""
        try:
            if self.installed_servers_file.exists():
                with open(self.installed_servers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.logger.error(f"Error leyendo servidores instalados: {e}")
        return {}
    
    def save_installed_servers(self, installed_servers: Dict):
        """Guarda la lista de servidores instalados."""
        try:
            with open(self.installed_servers_file, 'w', encoding='utf-8') as f:
                json.dump(installed_servers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Error guardando servidores instalados: {e}")
    
    def fetch_available_servers(self) -> List[Dict]:
        """
        Obtiene la lista de servidores disponibles desde múltiples fuentes.
        
        Returns:
            Lista de servidores MCP disponibles en formato normalizado
        """
        all_servers = []
        
        try:
            # 1. Obtener desde API oficial
            self.logger.info("Obteniendo lista de servidores MCP desde API oficial...")
            response = requests.get(self.official_api_url, timeout=15)
            response.raise_for_status()
            
            official_data = response.json()
            official_servers = self._normalize_official_api_response(official_data)
            all_servers.extend(official_servers)
            self.logger.info(f"Obtenidos {len(official_servers)} servidores desde API oficial")
            
        except requests.RequestException as e:
            self.logger.error(f"Error obteniendo servidores desde API oficial: {e}")
        except Exception as e:
            self.logger.error(f"Error procesando respuesta de API oficial: {e}")
            
        try:
            # 2. Cargar galería extendida local
            if os.path.exists(self.extended_gallery_path):
                with open(self.extended_gallery_path, 'r', encoding='utf-8') as f:
                    extended_data = json.load(f)
                    if 'servers' in extended_data:
                        # Normalizar servidores de galería extendida
                        extended_servers = []
                        for server in extended_data['servers']:
                            # Agregar estructura _original necesaria para instalación
                            normalized_server = server.copy()
                            normalized_server["_original"] = server
                            extended_servers.append(normalized_server)
                        
                        all_servers.extend(extended_servers)
                        self.logger.info(f"Cargados {len(extended_servers)} servidores desde galería extendida")
        except Exception as e:
            self.logger.error(f"Error cargando galería extendida: {e}")

        # 3. Agregar servidores Docker si están disponibles
        if self.docker_manager and self.docker_manager.check_docker_availability():
            try:
                docker_servers = self.docker_manager.get_available_docker_servers()
                # Marcar servidores Docker con tipo especial
                for server in docker_servers:
                    server['installation_type'] = 'docker'
                    server['docker_available'] = True
                all_servers.extend(docker_servers)
                self.logger.info(f"Agregados {len(docker_servers)} servidores Docker MCP")
            except Exception as e:
                self.logger.error(f"Error obteniendo servidores Docker: {e}")

        # 4. Si no hay servidores, usar fallback
        if not all_servers:
            all_servers = self._get_fallback_servers()
        
        # Eliminar duplicados por nombre
        unique_servers = {}
        for server in all_servers:
            if 'name' in server:
                unique_servers[server['name']] = server
        
        final_servers = list(unique_servers.values())
        self.logger.info(f"Total de servidores únicos disponibles: {len(final_servers)}")
        return final_servers

    def _get_fallback_servers(self) -> List[Dict]:
        """Carga servidores desde el archivo fallback local."""
        try:
            fallback_path = os.path.join(os.path.dirname(__file__), "gallery_fallback.json")
            if os.path.exists(fallback_path):
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    fallback_data = json.load(f)
                    servers = fallback_data.get('servers', [])
                    self.logger.info(f"Cargados {len(servers)} servidores desde archivo fallback")
                    return servers
            else:
                self.logger.warning("Archivo fallback no encontrado")
                return []
        except Exception as e:
            self.logger.error(f"Error cargando servidores fallback: {e}")
            return []

    def _normalize_official_api_response(self, api_data: Dict) -> List[Dict]:
        """
        Convierte la respuesta de la API oficial al formato esperado por la UI.
        
        Args:
            api_data: Respuesta de la API oficial con formato {"servers": [...], "metadata": {...}}
            
        Returns:
            Lista de servidores en formato normalizado
        """
        normalized_servers = []
        
        for item in api_data.get("servers", []):
            server_data = item.get("server", {})
            meta_data = item.get("_meta", {}).get("io.modelcontextprotocol.registry/official", {})
            
            # Solo incluir servidores activos y latest
            if meta_data.get("status") != "active" or not meta_data.get("isLatest", False):
                continue
                
            # Extraer ID limpio del nombre
            server_id = self._extract_server_id(server_data.get("name", ""))
            
            # Extraer tags desde diferentes fuentes
            tags = self._extract_tags(server_data)
            
            # Determinar manifest URL
            manifest_url = self._extract_manifest_url(server_data)
            
            # Generar ícono basado en tags o tipo
            icon_url = self._generate_icon_url(tags, server_id)
            
            normalized_server = {
                "id": server_id,
                "name": self._clean_server_name(server_data.get("name", "")),
                "description": server_data.get("description", ""),
                "icon": icon_url,
                "manifest_url": manifest_url,
                "version": server_data.get("version", "1.0.0"),
                "min_client_version": "1.0.0",  # Valor por defecto
                "checksum": "",  # No disponible en API oficial
                "signature_url": "",  # No disponible en API oficial
                "tags": tags,
                "_original": server_data  # Mantener datos originales para instalación
            }
            
            normalized_servers.append(normalized_server)
            
        return normalized_servers

    def _extract_server_id(self, server_name: str) -> str:
        """Extrae un ID limpio del nombre del servidor."""
        if not server_name:
            return "unknown"
        
        # Para nombres como "ai.company/server-name", usar "server-name"
        if "/" in server_name:
            return server_name.split("/")[-1]
        
        # Para nombres como "company.server", usar "server"  
        if "." in server_name:
            return server_name.split(".")[-1]
            
        return server_name.lower().replace(" ", "-")

    def _clean_server_name(self, server_name: str) -> str:
        """Limpia el nombre del servidor para mostrar en UI."""
        if "/" in server_name:
            return server_name.split("/")[-1].replace("-", " ").title()
        return server_name

    def _extract_tags(self, server_data: Dict) -> List[str]:
        """Extrae tags del servidor basado en descripción y datos."""
        tags = []
        
        description = server_data.get("description", "").lower()
        name = server_data.get("name", "").lower()
        
        # Tags basados en palabras clave en descripción y nombre
        tag_keywords = {
            "filesystem": ["file", "folder", "directory", "filesystem"],
            "weather": ["weather", "clima", "meteorol"],
            "github": ["github", "git"],
            "database": ["database", "sql", "postgres", "mysql", "sqlite"],
            "api": ["api", "rest", "http"],
            "search": ["search", "query", "find"],
            "analytics": ["analytics", "analysis", "statistics"],
            "commerce": ["commerce", "stripe", "payment", "merchant"],
            "network": ["network", "pcap", "packet"],
            "memory": ["memory", "context", "conversation"]
        }
        
        for tag, keywords in tag_keywords.items():
            if any(keyword in description or keyword in name for keyword in keywords):
                tags.append(tag)
        
        # Tags desde packages
        packages = server_data.get("packages", [])
        for package in packages:
            if package.get("registryType") == "npm":
                tags.append("nodejs")
            elif package.get("registryType") == "pypi":
                tags.append("python")
            elif package.get("registryType") == "oci":
                tags.append("docker")
                
        # Tags desde remotes
        remotes = server_data.get("remotes", [])
        if remotes:
            tags.append("remote")
            
        return list(set(tags)) if tags else ["general"]

    def _extract_manifest_url(self, server_data: Dict) -> str:
        """Extrae la URL del manifest desde packages o remotes."""
        # Prioridad: remotes > packages
        remotes = server_data.get("remotes", [])
        if remotes:
            return remotes[0].get("url", "")
            
        packages = server_data.get("packages", [])
        if packages:
            package = packages[0]
            registry_type = package.get("registryType", "")
            identifier = package.get("identifier", "")
            
            if registry_type == "npm":
                return f"https://registry.npmjs.org/{identifier}"
            elif registry_type == "pypi":
                return f"https://pypi.org/project/{identifier}/"
                
        return ""

    def _generate_icon_url(self, tags: List[str], server_id: str) -> str:
        """Genera URL de ícono basado en tags."""
        # Mapeo de tags a iconos genéricos
        icon_mapping = {
            "filesystem": "📁",
            "weather": "🌤️", 
            "github": "🐙",
            "database": "🗄️",
            "api": "🔗",
            "search": "🔍",
            "analytics": "📊",
            "commerce": "🛒",
            "network": "🌐",
            "memory": "🧠",
            "python": "🐍",
            "nodejs": "📗",
            "docker": "🐳"
        }
        
        for tag in tags:
            if tag in icon_mapping:
                # Retornar data URL con emoji como ícono
                return f"data:text/plain;charset=utf-8,{icon_mapping[tag]}"
                
        return "data:text/plain;charset=utf-8,⚙️"  # Ícono por defecto

    def fetch_mcp_details(self, server_id: str) -> Optional[Dict]:
        """
        Obtiene los detalles específicos de un servidor MCP desde la API oficial.
        
        Args:
            server_id: ID del servidor (se busca en la cache o API)
            
        Returns:
            Diccionario con detalles extendidos del servidor o None si no se encuentra
        """
        try:
            # Primero intentar desde la API oficial usando el endpoint específico
            # Nota: La API oficial no tiene endpoint por ID individual, así que 
            # buscamos en la lista completa y filtramos
            self.logger.info(f"Obteniendo detalles para servidor: {server_id}")
            
            servers = self.fetch_available_servers()
            for server in servers:
                if server.get("id") == server_id:
                    # Enriquecer con detalles adicionales si están disponibles
                    original_data = server.get("_original", {})
                    
                    detailed_info = {
                        **server,
                        "installation_methods": self._get_installation_methods(original_data),
                        "requirements": self._get_requirements(original_data),
                        "environment_variables": self._get_environment_variables(original_data),
                        "repository_info": original_data.get("repository", {}),
                        "remotes_info": original_data.get("remotes", []),
                        "packages_info": original_data.get("packages", [])
                    }
                    
                    return detailed_info
                    
            self.logger.warning(f"Servidor {server_id} no encontrado")
            return None
            
        except Exception as e:
            self.logger.error(f"Error obteniendo detalles de {server_id}: {e}")
            return None

    def _get_installation_methods(self, server_data: Dict) -> List[Dict]:
        """Extrae los métodos de instalación disponibles."""
        methods = []
        
        # Desde packages
        for package in server_data.get("packages", []):
            registry_type = package.get("registryType", "")
            identifier = package.get("identifier", "")
            version = package.get("version", "")
            runtime_hint = package.get("runtimeHint", "")
            
            method = {
                "type": "package",
                "registry": registry_type,
                "identifier": identifier,
                "version": version,
                "command": self._generate_install_command(registry_type, identifier, version, runtime_hint),
                "runtime_hint": runtime_hint,
                "transport": package.get("transport", {})
            }
            methods.append(method)
            
        # Desde remotes
        for remote in server_data.get("remotes", []):
            method = {
                "type": "remote",
                "url": remote.get("url", ""),
                "transport_type": remote.get("type", ""),
                "headers": remote.get("headers", [])
            }
            methods.append(method)
            
        return methods

    def _generate_install_command(self, registry_type: str, identifier: str, version: str, runtime_hint: str) -> str:
        """Genera el comando de instalación basado en el tipo de registro."""
        if registry_type == "npm":
            if runtime_hint == "npx":
                return f"npx {identifier}@{version}"
            else:
                return f"npm install -g {identifier}@{version}"
        elif registry_type == "pypi":
            return f"pip install {identifier}=={version}"
        elif registry_type == "oci":
            return f"docker pull {identifier}"
        else:
            return f"# Manual installation required for {identifier}"

    def _get_requirements(self, server_data: Dict) -> List[str]:
        """Extrae los requisitos del servidor."""
        requirements = []
        
        for package in server_data.get("packages", []):
            registry_type = package.get("registryType", "")
            if registry_type == "npm":
                requirements.append("Node.js >= 14")
            elif registry_type == "pypi":
                requirements.append("Python >= 3.8")
            elif registry_type == "oci":
                requirements.append("Docker")
                
        return list(set(requirements))

    def _get_environment_variables(self, server_data: Dict) -> List[Dict]:
        """Extrae las variables de entorno requeridas."""
        env_vars = []
        
        for package in server_data.get("packages", []):
            for env_var in package.get("environmentVariables", []):
                env_vars.append({
                    "name": env_var.get("name", ""),
                    "description": env_var.get("description", ""),
                    "required": env_var.get("isRequired", False),
                    "secret": env_var.get("isSecret", False),
                    "default": env_var.get("default", "")
                })
                
        for remote in server_data.get("remotes", []):
            for header in remote.get("headers", []):
                if header.get("isSecret", False):
                    env_vars.append({
                        "name": header.get("name", ""),
                        "description": header.get("description", ""),
                        "required": True,
                        "secret": True,
                        "default": ""
                    })
                    
        return env_vars
    
    def _get_fallback_servers(self) -> List[Dict]:
        """Datos de fallback si la API no está disponible."""
        fallback_file = Path(__file__).parent / "gallery_fallback.json"
        if fallback_file.exists():
            try:
                with open(fallback_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.error(f"Error leyendo fallback: {e}")
        
        # Datos de ejemplo si no hay fallback
        return [
            {
                "id": "weather-server",
                "name": "Weather Server",
                "description": "Servidor MCP para consultar información del clima",
                "icon": "https://example.com/icons/weather.png",
                "manifest_url": "https://example.com/manifests/weather-server.json",
                "version": "1.0.0",
                "min_client_version": "1.0.0",
                "checksum": "sha256:placeholder",
                "signature_url": "https://example.com/signatures/weather-server.sig",
                "tags": ["weather", "api"]
            }
        ]
    
    def verify_checksum(self, content: bytes, expected_checksum: str) -> bool:
        """
        Verifica el checksum de un archivo descargado.
        
        Args:
            content: Contenido del archivo en bytes
            expected_checksum: Checksum esperado en formato "algoritmo:hash"
            
        Returns:
            True si el checksum coincide, False en caso contrario
        """
        try:
            if ":" not in expected_checksum:
                self.logger.error(f"Formato de checksum inválido: {expected_checksum}")
                return False
                
            algorithm, expected_hash = expected_checksum.split(":", 1)
            
            if algorithm not in hashlib.algorithms_available:
                self.logger.error(f"Algoritmo de hash no soportado: {algorithm}")
                return False
                
            hasher = hashlib.new(algorithm)
            hasher.update(content)
            actual_hash = hasher.hexdigest()
            
            matches = actual_hash == expected_hash
            if matches:
                self.logger.info(f"Checksum verificado correctamente: {algorithm}")
            else:
                self.logger.error(f"Checksum no coincide. Esperado: {expected_hash}, Obtenido: {actual_hash}")
                
            return matches
            
        except Exception as e:
            self.logger.error(f"Error verificando checksum: {e}")
            return False
    
    def verify_pgp_signature(self, content: bytes, signature_url: str, public_key_file: Optional[str] = None) -> Tuple[bool, str]:
        """
        Verifica la firma PGP de un archivo.
        
        Args:
            content: Contenido del archivo a verificar
            signature_url: URL de la firma PGP
            public_key_file: Archivo de clave pública (opcional, usa mcp.gpg por defecto)
            
        Returns:
            Tupla (verificado, mensaje)
        """
        try:
            # Descargar firma
            success, sig_content, msg = self.download_file(signature_url)
            if not success:
                return False, f"Error descargando firma: {msg}"
            
            # Determinar archivo de clave pública
            if public_key_file is None:
                public_key_file = self.public_keys_dir / "mcp.gpg"
            else:
                public_key_file = Path(public_key_file)
            
            if not public_key_file.exists():
                return False, f"Archivo de clave pública no encontrado: {public_key_file}"
            
            # Crear archivos temporales
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Guardar contenido y firma en archivos temporales
                content_file = temp_path / "content.tmp"
                signature_file = temp_path / "signature.sig"
                
                content_file.write_bytes(content)
                signature_file.write_bytes(sig_content)
                
                # Intentar verificación con diferentes métodos
                
                # Método 1: Usar pgpy (si está disponible)
                success, message = self._verify_with_pgpy(content_file, signature_file, public_key_file)
                if success is not None:
                    return success, message
                
                # Método 2: Usar gpg command line (si está disponible)
                success, message = self._verify_with_gpg_cli(content_file, signature_file, public_key_file)
                if success is not None:
                    return success, message
                
                return False, "No hay herramientas de verificación PGP disponibles"
                
        except Exception as e:
            return False, f"Error verificando firma PGP: {e}"
    
    def _verify_with_pgpy(self, content_file: Path, signature_file: Path, public_key_file: Path) -> Tuple[Optional[bool], str]:
        """Verificación usando la librería pgpy de Python."""
        try:
            import pgpy
            
            # Cargar clave pública
            with open(public_key_file, 'rb') as kf:
                public_key, _ = pgpy.PGPKey.from_blob(kf.read())
            
            # Cargar firma
            with open(signature_file, 'rb') as sf:
                signature = pgpy.PGPSignature.from_blob(sf.read())
            
            # Verificar
            with open(content_file, 'rb') as cf:
                content = cf.read()
            
            # Crear mensaje PGP
            message = pgpy.PGPMessage.new(content)
            
            # Verificar firma
            if public_key.verify(message, signature):
                return True, "Firma PGP verificada correctamente"
            else:
                return False, "Firma PGP inválida"
                
        except ImportError:
            return None, "pgpy no disponible"
        except Exception as e:
            return False, f"Error en verificación pgpy: {e}"
    
    def _verify_with_gpg_cli(self, content_file: Path, signature_file: Path, public_key_file: Path) -> Tuple[Optional[bool], str]:
        """Verificación usando gpg command line."""
        try:
            # Verificar si gpg está disponible
            result = subprocess.run(['gpg', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode != 0:
                return None, "gpg no disponible"
            
            # Importar clave pública temporalmente
            import_result = subprocess.run(
                ['gpg', '--import', str(public_key_file)],
                capture_output=True, text=True, timeout=10
            )
            
            # Verificar firma
            verify_result = subprocess.run([
                'gpg', '--verify', str(signature_file), str(content_file)
            ], capture_output=True, text=True, timeout=10)
            
            if verify_result.returncode == 0:
                return True, "Firma PGP verificada con gpg"
            else:
                return False, f"Verificación gpg falló: {verify_result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Timeout en verificación gpg"
        except FileNotFoundError:
            return None, "gpg no encontrado en PATH"
        except Exception as e:
            return False, f"Error en verificación gpg: {e}"
    
    def verify_integrity(self, content: bytes, server_info: Dict) -> Tuple[bool, Dict[str, bool], str]:
        """
        Verificación completa de integridad de un archivo.
        
        Args:
            content: Contenido del archivo
            server_info: Información del servidor con checksums y URLs de firma
            
        Returns:
            Tupla (éxito_general, detalles_verificación, mensaje)
        """
        verification_results = {
            "checksum_verified": False,
            "signature_verified": False,
            "has_checksum": False,
            "has_signature": False
        }
        
        messages = []
        overall_success = True
        
        # Verificar checksum si está disponible
        checksum = server_info.get("checksum", "")
        if checksum and checksum != "placeholder":
            verification_results["has_checksum"] = True
            if self.verify_checksum(content, checksum):
                verification_results["checksum_verified"] = True
                messages.append("✓ Checksum verificado")
            else:
                verification_results["checksum_verified"] = False
                messages.append("✗ Checksum inválido")
                overall_success = False
        else:
            messages.append("⚠ Sin checksum disponible")
        
        # Verificar firma PGP si está disponible
        signature_url = server_info.get("signature_url", "")
        if signature_url and signature_url != "":
            verification_results["has_signature"] = True
            success, msg = self.verify_pgp_signature(content, signature_url)
            verification_results["signature_verified"] = success
            if success:
                messages.append("✓ Firma PGP verificada")
            else:
                messages.append(f"✗ Firma PGP inválida: {msg}")
                # No marcar como fallo general si solo falla la firma
                # (el checksum puede ser suficiente)
        else:
            messages.append("⚠ Sin firma PGP disponible")
        
        # Criterio de éxito: al menos checksum O firma válida
        if not verification_results["checksum_verified"] and not verification_results["signature_verified"]:
            if verification_results["has_checksum"] or verification_results["has_signature"]:
                overall_success = False
            else:
                # No hay ningún mecanismo de verificación
                messages.append("⚠ Instalando sin verificación de integridad")
                overall_success = True  # Permitir instalación
        
        return overall_success, verification_results, " | ".join(messages)
        """
        Verifica el checksum de un archivo descargado.
        
        Args:
            content: Contenido del archivo en bytes
            expected_checksum: Checksum esperado en formato "algoritmo:hash"
            
        Returns:
            True si el checksum coincide, False en caso contrario
        """
        try:
            if ":" not in expected_checksum:
                self.logger.error(f"Formato de checksum inválido: {expected_checksum}")
                return False
                
            algorithm, expected_hash = expected_checksum.split(":", 1)
            
            if algorithm not in hashlib.algorithms_available:
                self.logger.error(f"Algoritmo de hash no soportado: {algorithm}")
                return False
                
            hasher = hashlib.new(algorithm)
            hasher.update(content)
            actual_hash = hasher.hexdigest()
            
            matches = actual_hash == expected_hash
            if matches:
                self.logger.info(f"Checksum verificado correctamente: {algorithm}")
            else:
                self.logger.error(f"Checksum no coincide. Esperado: {expected_hash}, Obtenido: {actual_hash}")
                
            return matches
            
        except Exception as e:
            self.logger.error(f"Error verificando checksum: {e}")
            return False
    
    def download_file(self, url: str, timeout: int = 30) -> Tuple[bool, Optional[bytes], str]:
        """
        Descarga un archivo desde una URL.
        
        Args:
            url: URL del archivo a descargar
            timeout: Timeout en segundos
            
        Returns:
            Tupla (éxito, contenido, mensaje)
        """
        try:
            self.logger.info(f"Descargando: {url}")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            return True, response.content, "Descarga exitosa"
            
        except requests.RequestException as e:
            error_msg = f"Error descargando {url}: {e}"
            self.logger.error(error_msg)
            return False, None, error_msg
        except Exception as e:
            error_msg = f"Error inesperado descargando {url}: {e}"
            self.logger.error(error_msg)
            return False, None, error_msg
    
    def install_server(self, server_info: Dict) -> Tuple[bool, str]:
        """
        Instala un servidor MCP según la información de la API oficial.
        
        Args:
            server_info: Información del servidor desde fetch_available_servers()
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            server_id = server_info.get("id") or server_info.get("name", "unknown_server")
            version = server_info.get("version", "1.0.0")
            
            self.logger.info(f"Iniciando instalación de {server_id} v{version}")
            
            # Verificar si ya está instalado con la misma versión
            installed_servers = self.get_installed_servers()
            if server_id in installed_servers:
                installed_version = installed_servers[server_id].get("version", "")
                if installed_version == version:
                    return False, f"El servidor {server_id} v{version} ya está instalado"
            
            # Obtener datos originales para instalación
            original_data = server_info.get("_original", {})
            
            # Determinar método de instalación
            packages_data = original_data.get("packages", [])
            remotes = original_data.get("remotes", [])
            
            # Transformar packages si está en formato de gallery_extended.json
            packages = []
            if isinstance(packages_data, dict):
                # Formato gallery_extended.json: {"npm": {"package": "...", "version": "..."}}
                for registry_type, package_info in packages_data.items():
                    if registry_type == "npm":
                        packages.append({
                            "registryType": "npm",
                            "identifier": package_info.get("package", ""),
                            "version": package_info.get("version", "latest")
                        })
                    elif registry_type == "pypi":
                        packages.append({
                            "registryType": "pypi", 
                            "identifier": package_info.get("package", ""),
                            "version": package_info.get("version", "latest")
                        })
            elif isinstance(packages_data, list):
                # Formato API oficial (lista de diccionarios)
                packages = packages_data
            
            if packages:
                # Instalación vía package manager (npm, pip, docker)
                return self._install_package_server(server_info, packages)
            elif remotes:
                # Servidor remoto (SSE, HTTP, etc.)
                return self._install_remote_server(server_info, remotes)
            elif server_info.get("manifest_url", "").startswith("file://"):
                # Servidor local
                return self._install_local_server(server_info, installed_servers)
            else:
                return False, "No se encontró método de instalación válido"
                
        except Exception as e:
            error_msg = f"Error instalando {server_info.get('id', 'unknown')}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def _install_package_server(self, server_info: Dict, packages: List[Dict]) -> Tuple[bool, str]:
        """Instala un servidor desde un package manager."""
        try:
            server_id = server_info.get("id") or server_info.get("name", "unknown_server")
            package = packages[0]  # Usar el primer paquete disponible
            
            registry_type = package.get("registryType", "")
            identifier = package.get("identifier", "")
            version = package.get("version", "")
            
            # Verificar disponibilidad del comando antes de ejecutar
            if registry_type == "npm":
                # Verificar si npm está disponible (usar npm.cmd en Windows)
                import platform
                npm_cmd = "npm.cmd" if platform.system() == "Windows" else "npm"
                
                try:
                    result = subprocess.run([npm_cmd, "--version"], capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        return False, "npm no está instalado o no está en el PATH del sistema"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    return False, "npm no está disponible. Por favor instale Node.js y npm primero."
                
                cmd = [npm_cmd, "install", "-g", f"{identifier}@{version}"]
                
            elif registry_type == "pypi":
                # Verificar si pip está disponible
                try:
                    result = subprocess.run(["pip", "--version"], capture_output=True, text=True, timeout=10)
                    if result.returncode != 0:
                        return False, "pip no está instalado o no está en el PATH del sistema"
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    return False, "pip no está disponible. Por favor instale Python y pip primero."
                
                cmd = ["pip", "install", f"{identifier}=={version}"]
                
            elif registry_type == "oci":
                cmd = ["docker", "pull", identifier]
            else:
                return False, f"Tipo de registro no soportado: {registry_type}"
                
            self.logger.info(f"Ejecutando: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Registrar instalación exitosa
                self._register_installation(server_info, {
                    "install_method": "package",
                    "registry_type": registry_type,
                    "identifier": identifier,
                    "package_version": version,
                    "transport": package.get("transport", {}),
                    "environment_variables": package.get("environmentVariables", [])
                })
                return True, f"Servidor {server_id} instalado exitosamente vía {registry_type}"
            else:
                error_msg = f"Error en instalación: {result.stderr}"
                self.logger.error(error_msg)
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            return False, "La instalación excedió el tiempo límite (5 minutos)"
        except Exception as e:
            return False, f"Error ejecutando instalación: {str(e)}"

    def _install_remote_server(self, server_info: Dict, remotes: List[Dict]) -> Tuple[bool, str]:
        """Instala/registra un servidor remoto."""
        try:
            server_id = server_info.get("id") or server_info.get("name", "unknown_server")
            remote = remotes[0]  # Usar el primer remoto disponible
            
            # Los servidores remotos no requieren instalación local,
            # solo registrar su configuración
            self._register_installation(server_info, {
                "install_method": "remote",
                "url": remote.get("url", ""),
                "transport_type": remote.get("type", ""),
                "headers": remote.get("headers", [])
            })
            
            return True, f"Servidor remoto {server_id} registrado exitosamente"
            
        except Exception as e:
            return False, f"Error registrando servidor remoto: {str(e)}"
            
    def _register_installation(self, server_info: Dict, install_details: Dict):
        """Registra una instalación exitosa en el archivo de servidores instalados."""
        installed_servers = self.get_installed_servers()
        
        server_id = server_info.get("id") or server_info.get("name", "unknown_server")
        installed_servers[server_id] = {
            "id": server_id,
            "name": server_info.get("name", "Servidor Desconocido"),
            "description": server_info.get("description", ""),
            "version": server_info.get("version", "1.0.0"),
            "installed_at": datetime.now().isoformat(),
            "install_details": install_details,
            "tags": server_info.get("tags", [])
        }
        
        self.save_installed_servers(installed_servers)
        self.logger.info(f"Instalación de {server_id} registrada exitosamente")

    def validate_manifest_schema(self, manifest_data: Dict) -> Tuple[bool, str]:
        """
        Valida un manifest contra el esquema JSON oficial de MCP.
        
        Args:
            manifest_data: Datos del manifest a validar
            
        Returns:
            Tupla (es_válido, mensaje)
        """
        try:
            # Cargar el esquema JSON oficial
            schema_file = Path(__file__).parent / "mcp_server_schema.json"
            
            if not schema_file.exists():
                return False, "Esquema de validación no encontrado"
                
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = json.load(f)
            
            # Validar contra el esquema
            validate(instance=manifest_data, schema=schema)
            
            return True, "Manifest válido según esquema oficial MCP"
            
        except ValidationError as e:
            error_msg = f"Error de validación del manifest: {e.message}"
            self.logger.error(error_msg)
            return False, error_msg
            
        except FileNotFoundError:
            error_msg = "Archivo de esquema MCP no encontrado"
            self.logger.error(error_msg)
            return False, error_msg
            
        except Exception as e:
            error_msg = f"Error validando manifest: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg

    def download_and_validate_manifest(self, manifest_url: str) -> Tuple[bool, Optional[Dict], str]:
        """
        Descarga y valida un manifest desde una URL.
        
        Args:
            manifest_url: URL del manifest a descargar
            
        Returns:
            Tupla (éxito, datos_del_manifest, mensaje)
        """
        try:
            # Descargar manifest
            success, content, msg = self.download_file(manifest_url)
            if not success:
                return False, None, f"Error descargando manifest: {msg}"
            
            # Parsear JSON
            try:
                manifest_data = json.loads(content.decode('utf-8'))
            except json.JSONDecodeError as e:
                return False, None, f"Manifest no es un JSON válido: {str(e)}"
            
            # Validar esquema
            valid, validation_msg = self.validate_manifest_schema(manifest_data)
            if not valid:
                return False, None, validation_msg
            
            return True, manifest_data, "Manifest descargado y validado exitosamente"
            
        except Exception as e:
            error_msg = f"Error procesando manifest: {str(e)}"
            self.logger.error(error_msg)
            return False, None, error_msg

    def _install_local_server(self, server_info: Dict, installed_servers: Dict) -> Tuple[bool, str]:
        """
        Instala un servidor MCP local que ya está en el proyecto.
        
        Args:
            server_info: Información del servidor
            installed_servers: Registro de servidores instalados
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            server_id = server_info.get("id") or server_info.get("name", "unknown_server")
            version = server_info.get("version", "1.0.0")
            
            # Para servidores locales, verificar si el archivo existe
            manifest_url = server_info.get("manifest_url", "")
            local_path = manifest_url.replace("file://", "")
            
            # Intentar encontrar el archivo en el proyecto
            project_root = self.base_dir.parent
            possible_paths = [
                project_root / local_path,
                project_root / f"{server_id}.py",
                project_root / "weather-server-python" / "weather.py"
            ]
            
            server_file = None
            for path in possible_paths:
                if path.exists():
                    server_file = path
                    break
            
            if not server_file:
                return False, f"No se encontró el archivo del servidor local: {local_path}"
            
            # Crear directorio del servidor
            server_dir = self.mcps_dir / server_id
            server_dir.mkdir(parents=True, exist_ok=True)
            
            # Crear un manifest básico para el servidor local
            manifest_data = {
                "name": server_id,
                "version": version,
                "description": server_info["description"],
                "type": "local",
                "source_file": str(server_file),
                "capabilities": {
                    "tools": [
                        {
                            "name": "local_server_tool",
                            "description": "Herramientas del servidor local"
                        }
                    ]
                }
            }
            
            # Guardar manifest
            manifest_file = server_dir / "manifest.json"
            with open(manifest_file, 'w', encoding='utf-8') as f:
                json.dump(manifest_data, f, indent=2, ensure_ascii=False)
            
            # Actualizar registro
            installed_servers[server_id] = {
                "version": version,
                "installed_at": datetime.now().isoformat(),
                "type": "local",
                "source_file": str(server_file),
                "checksum_validated": False,  # No aplica para servidores locales
                "signature_verified": False,
                "has_checksum": False,
                "has_signature": False,
                "verification_message": "Servidor local - verificación no requerida"
            }
            
            self.save_installed_servers(installed_servers)
            
            success_msg = f"Servidor local {server_id} v{version} configurado correctamente"
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error configurando servidor local {server_info.get('id', 'unknown')}: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def uninstall_server(self, server_id: str) -> Tuple[bool, str]:
        """
        Desinstala un servidor MCP.
        
        Args:
            server_id: ID del servidor a desinstalar
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            installed_servers = self.get_installed_servers()
            
            if server_id not in installed_servers:
                # Verificar si está en mcp_servers.json pero no en installed_servers
                try:
                    if self.base_dir.name == "puentellm-mcp" and "Repositorios" in str(self.base_dir):
                        mcp_servers_file = self.base_dir / "mcp_servers.json"
                    else:
                        script_dir = Path(__file__).parent
                        mcp_servers_file = script_dir / "mcp_servers.json"
                    
                    if mcp_servers_file.exists():
                        with open(mcp_servers_file, 'r', encoding='utf-8') as f:
                            mcp_config = json.load(f)
                        
                        mcp_servers = mcp_config.get("mcpServers", {})
                        if server_id in mcp_servers:
                            # Remover de mcp_servers.json
                            del mcp_servers[server_id]
                            with open(mcp_servers_file, 'w', encoding='utf-8') as f:
                                json.dump(mcp_config, f, indent=4, ensure_ascii=False)
                            
                            success_msg = f"Servidor {server_id} removido de la configuración"
                            self.logger.info(success_msg)
                            return True, success_msg
                
                except Exception as e:
                    self.logger.error(f"Error verificando mcp_servers.json: {e}")
                
                return False, f"El servidor {server_id} no está instalado"
            
            # Eliminar directorio del servidor
            server_dir = self.mcps_dir / server_id
            if server_dir.exists():
                shutil.rmtree(server_dir)
            
            # Actualizar registro de instalaciones
            del installed_servers[server_id]
            self.save_installed_servers(installed_servers)
            
            # También remover de mcp_servers.json si existe
            try:
                if self.base_dir.name == "puentellm-mcp" and "Repositorios" in str(self.base_dir):
                    mcp_servers_file = self.base_dir / "mcp_servers.json"
                else:
                    script_dir = Path(__file__).parent
                    mcp_servers_file = script_dir / "mcp_servers.json"
                
                if mcp_servers_file.exists():
                    with open(mcp_servers_file, 'r', encoding='utf-8') as f:
                        mcp_config = json.load(f)
                    
                    mcp_servers = mcp_config.get("mcpServers", {})
                    if server_id in mcp_servers:
                        del mcp_servers[server_id]
                        with open(mcp_servers_file, 'w', encoding='utf-8') as f:
                            json.dump(mcp_config, f, indent=4, ensure_ascii=False)
                        self.logger.info(f"Servidor {server_id} también removido de mcp_servers.json")
            
            except Exception as e:
                self.logger.warning(f"Error removiendo de mcp_servers.json: {e}")
            
            success_msg = f"Servidor {server_id} desinstalado correctamente"
            self.logger.info(success_msg)
            return True, success_msg
            
        except Exception as e:
            error_msg = f"Error desinstalando servidor {server_id}: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_server_status(self, server_info: Dict) -> str:
        """
        Obtiene el estado de un servidor (no instalado, instalado, actualizable).
        
        Args:
            server_info: Información del servidor desde la API
            
        Returns:
            Estado del servidor: 'not_installed', 'installed', 'update_available'
        """
        # Obtener ID de manera robusta
        server_id = server_info.get("id") or server_info.get("name", "unknown_server")
        
        # Verificar en el registro de instalaciones de la galería
        installed_servers = self.get_installed_servers()
        if server_id in installed_servers:
            installed_version = installed_servers[server_id].get("version", "")
            current_version = server_info.get("version", "1.0.0")
            
            # Comparación simple de versiones
            if installed_version != current_version:
                return "update_available"
            return "installed"
        
        # Verificar si el servidor está configurado en mcp_servers.json
        try:
            # El archivo mcp_servers.json está en el directorio del proyecto, no en config
            # Si base_dir es el directorio del proyecto, usar directamente
            # Si base_dir es ~/.config/puentellm-mcp, buscar en el directorio del script
            if self.base_dir.name == "puentellm-mcp" and "Repositorios" in str(self.base_dir):
                mcp_servers_file = self.base_dir / "mcp_servers.json"
            else:
                # Para el caso ~/.config/puentellm-mcp, asumir el archivo está junto al script
                script_dir = Path(__file__).parent
                mcp_servers_file = script_dir / "mcp_servers.json"
            
            self.logger.debug(f"Verificando archivo MCP: {mcp_servers_file}")
            
            if mcp_servers_file.exists():
                with open(mcp_servers_file, 'r', encoding='utf-8') as f:
                    mcp_config = json.load(f)
                    
                # Verificar si hay un servidor con ID similar o si es un servidor local conocido
                mcp_servers = mcp_config.get("mcpServers", {})
                self.logger.debug(f"Servidores en config: {list(mcp_servers.keys())}")
                self.logger.debug(f"Buscando servidor: {server_id}")
                
                # Primero verificar directamente
                if server_id in mcp_servers:
                    self.logger.debug(f"Servidor {server_id} encontrado directamente")
                    return "installed"
                
                # Mapear algunos IDs conocidos (galería ID -> mcp_servers.json ID)
                id_mappings = {
                    "weather-server-local": "weather-server-python",
                    "file-manager": "filesystem",  # file-manager de galería = filesystem en config
                }
                
                mapped_id = id_mappings.get(server_id, server_id)
                self.logger.debug(f"Mapped ID: {server_id} -> {mapped_id}")
                if mapped_id in mcp_servers:
                    self.logger.debug(f"Servidor encontrado por mapeo: {mapped_id}")
                    return "installed"
                    
                # Mapear al revés (mcp_servers.json ID -> galería ID)  
                reverse_mappings = {v: k for k, v in id_mappings.items()}
                reverse_mapped = reverse_mappings.get(server_id, server_id)
                self.logger.debug(f"Reverse mapped: {server_id} -> {reverse_mapped}")
                if reverse_mapped in mcp_servers:
                    self.logger.debug(f"Servidor encontrado por mapeo reverso: {reverse_mapped}")
                    return "installed"
                    
                # Verificar por patrones comunes
                for mcp_id in mcp_servers.keys():
                    if (server_id.replace("-", "").lower() in mcp_id.lower() or
                        mcp_id.lower() in server_id.replace("-", "").lower()):
                        self.logger.debug(f"Servidor encontrado por patrón: {server_id} ~ {mcp_id}")
                        return "installed"
                        
        except Exception as e:
            self.logger.error(f"Error verificando mcp_servers.json: {e}")
        
        
        return "not_installed"
    
    def sync_installed_servers_to_config(self):
        """
        Sincroniza los servidores instalados desde la galería con mcp_servers.json.
        
        Returns:
            int: Número de servidores sincronizados
        """
        try:
            installed_servers = self.get_installed_servers()
            
            if not installed_servers:
                self.logger.debug("No hay servidores instalados para sincronizar")
                return 0
            
            # Buscar el archivo mcp_servers.json
            if self.base_dir.name == "puentellm-mcp" and "Repositorios" in str(self.base_dir):
                mcp_servers_file = self.base_dir / "mcp_servers.json"
            else:
                script_dir = Path(__file__).parent
                mcp_servers_file = script_dir / "mcp_servers.json"
            
            if not mcp_servers_file.exists():
                self.logger.warning(f"Archivo mcp_servers.json no encontrado en {mcp_servers_file}")
                return 0
            
            # Cargar configuración actual
            with open(mcp_servers_file, 'r', encoding='utf-8') as f:
                mcp_config = json.load(f)
            
            mcp_servers = mcp_config.get("mcpServers", {})
            synced_count = 0
            
            for server_id, server_data in installed_servers.items():
                # Verificar si ya está configurado
                if server_id not in mcp_servers:
                    # Configurar según el método de instalación
                    install_method = server_data.get("install_details", {}).get("install_method")
                    
                    if install_method == "remote":
                        # Servidor remoto (SSE o HTTP)
                        url = server_data.get("install_details", {}).get("url", "")
                        if url:
                            # Encontrar un puerto disponible (empezando desde 8081)
                            used_ports = {config.get("port") for config in mcp_servers.values() if config.get("port")}
                            port = 8081
                            while port in used_ports:
                                port += 1
                            
                            mcp_servers[server_id] = {
                                "command": "curl",
                                "args": ["-X", "POST", url],
                                "enabled": True,
                                "type": "remote",
                                "url": url,
                                "port": port
                            }
                            synced_count += 1
                            self.logger.info(f"Servidor remoto {server_id} sincronizado a mcp_servers.json")
                    
                    elif install_method == "package":
                        # Servidor de paquete (npm, pip, etc.)
                        package_data = server_data.get("install_details", {})
                        package_manager = package_data.get("package_manager", "npx")
                        package_name = package_data.get("package_name", server_id)
                        
                        # Encontrar un puerto disponible
                        used_ports = {config.get("port") for config in mcp_servers.values() if config.get("port")}
                        port = 8080
                        while port in used_ports:
                            port += 1
                        
                        if package_manager == "npx":
                            mcp_servers[server_id] = {
                                "command": "npx",
                                "args": ["-y", package_name],
                                "enabled": True,
                                "type": "package",
                                "port": port
                            }
                        elif package_manager == "pip":
                            mcp_servers[server_id] = {
                                "command": "python",
                                "args": ["-m", package_name],
                                "enabled": True,
                                "type": "package",
                                "port": port
                            }
                        
                        synced_count += 1
                        self.logger.info(f"Servidor de paquete {server_id} sincronizado a mcp_servers.json")
            
            if synced_count > 0:
                # Guardar la configuración actualizada
                with open(mcp_servers_file, 'w', encoding='utf-8') as f:
                    json.dump(mcp_config, f, indent=4, ensure_ascii=False)
                
                self.logger.info(f"Sincronizados {synced_count} servidores a mcp_servers.json")
            
            return synced_count
            
        except Exception as e:
            self.logger.error(f"Error sincronizando servidores instalados: {e}")
            return 0

    def set_api_base_url(self, url: str):
        """Configura la URL base de la API."""
        self.api_base_url = url.rstrip('/')
    
    def install_public_key(self, key_content: str, key_name: str = "mcp.gpg") -> Tuple[bool, str]:
        """
        Instala una clave pública para verificación de firmas.
        
        Args:
            key_content: Contenido de la clave pública PGP
            key_name: Nombre del archivo de clave
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            key_file = self.public_keys_dir / key_name
            
            # Validar formato básico de clave PGP
            if not ("BEGIN PGP PUBLIC KEY" in key_content and "END PGP PUBLIC KEY" in key_content):
                return False, "Formato de clave pública inválido"
            
            # Guardar clave
            key_file.write_text(key_content, encoding='utf-8')
            
            self.logger.info(f"Clave pública instalada: {key_name}")
            return True, f"Clave pública '{key_name}' instalada correctamente"
            
        except Exception as e:
            error_msg = f"Error instalando clave pública: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def list_public_keys(self) -> List[Dict[str, str]]:
        """
        Lista las claves públicas instaladas.
        
        Returns:
            Lista de información de claves
        """
        keys = []
        
        try:
            for key_file in self.public_keys_dir.glob("*.gpg"):
                try:
                    content = key_file.read_text(encoding='utf-8')
                    
                    # Extraer información básica de la clave
                    key_info = {
                        "name": key_file.name,
                        "path": str(key_file),
                        "size": len(content),
                        "installed": key_file.stat().st_mtime
                    }
                    
                    # Intentar extraer más información si es posible
                    try:
                        import re
                        # Buscar UID en la clave
                        uid_match = re.search(r'Comment:\s*(.+)', content)
                        if uid_match:
                            key_info["comment"] = uid_match.group(1)
                    except Exception:
                        # No se pudo extraer el comentario de la clave; esto es opcional y no crítico
                        pass
                    
                    keys.append(key_info)
                    
                except Exception as e:
                    self.logger.warning(f"Error leyendo clave {key_file}: {e}")
                    
        except Exception as e:
            self.logger.error(f"Error listando claves: {e}")
        
        return keys
    
    def remove_public_key(self, key_name: str) -> Tuple[bool, str]:
        """
        Elimina una clave pública.
        
        Args:
            key_name: Nombre del archivo de clave
            
        Returns:
            Tupla (éxito, mensaje)
        """
        try:
            key_file = self.public_keys_dir / key_name
            
            if not key_file.exists():
                return False, f"Clave '{key_name}' no encontrada"
            
            key_file.unlink()
            
            self.logger.info(f"Clave pública eliminada: {key_name}")
            return True, f"Clave '{key_name}' eliminada correctamente"
            
        except Exception as e:
            error_msg = f"Error eliminando clave pública: {e}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_installation_stats(self) -> Dict:
        """
        Obtiene estadísticas de instalaciones.
        
        Returns:
            Diccionario con estadísticas
        """
        try:
            installed_servers = self.get_installed_servers()
            
            stats = {
                "total_installed": len(installed_servers),
                "verified_checksum": 0,
                "verified_signature": 0,
                "unverified": 0,
                "keys_installed": len(self.list_public_keys()),
                "disk_usage_mb": 0
            }
            
            # Analizar servidores instalados
            for server_id, info in installed_servers.items():
                if info.get("checksum_validated", False):
                    stats["verified_checksum"] += 1
                if info.get("signature_verified", False):
                    stats["verified_signature"] += 1
                if not info.get("checksum_validated", False) and not info.get("signature_verified", False):
                    stats["unverified"] += 1
            
            # Calcular uso de disco
            try:
                total_size = 0
                for server_dir in self.mcps_dir.iterdir():
                    if server_dir.is_dir():
                        total_size += sum(f.stat().st_size for f in server_dir.rglob('*') if f.is_file())
                stats["disk_usage_mb"] = round(total_size / (1024 * 1024), 2)
            except Exception as e:
                self.logger.warning(f"Error calculando uso de disco: {e}")
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error calculando estadísticas: {e}")
            return {"error": str(e)}