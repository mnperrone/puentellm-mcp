"""
Gestor de Servidores MCP Docker
Maneja la instalación, ejecución y gestión de servidores MCP como contenedores Docker.
"""

import json
import docker
import os
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from assets.logging import PersistentLogger

# Reducir verbosidad de los logs de Docker
logging.getLogger("docker").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)

# Importar nuestro helper de Docker
from docker_helper import DockerHelper


class DockerMCPManager:
    def __init__(self, config_dir: Optional[str] = None):
        """
        Inicializa el gestor de servidores MCP Docker.
        
        Args:
            config_dir: Directorio base para configuración
        """
        if config_dir is None:
            self.base_dir = Path.home() / ".config" / "puentellm-mcp"
        else:
            self.base_dir = Path(config_dir)
            
        self.docker_data_dir = self.base_dir / "docker-mcp"
        self.running_containers_file = self.base_dir / "running_docker_mcps.json"
        
        # Crear directorios si no existen
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.docker_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Logger
        log_dir = self.base_dir / "logs"
        log_dir.mkdir(exist_ok=True)
        self.logger = PersistentLogger(log_dir=str(log_dir))
        
        # Docker Helper para asegurar disponibilidad
        self.docker_helper = DockerHelper(self.logger)
        
        # Cliente Docker
        try:
            # Asegurar que Docker esté disponible antes de inicializar cliente
            if self.docker_helper.ensure_docker_running():
                # Intentar diferentes métodos de conexión para Windows
                self.docker_client = None
                
                # Método 1: Conexión predeterminada
                try:
                    self.docker_client = docker.from_env()
                    # Probar la conexión haciendo una llamada simple
                    self.docker_client.ping()
                    self.logger.info("Cliente Docker inicializado correctamente (método predeterminado)")
                except Exception:
                    pass  # Intentar siguiente método
                
                # Método 2: Conexión TCP si el predeterminado falla
                if self.docker_client is None:
                    try:
                        self.docker_client = docker.DockerClient(base_url='tcp://localhost:2375')
                        self.docker_client.ping()
                        self.logger.info("Cliente Docker inicializado correctamente (TCP)")
                    except Exception:
                        pass  # Intentar siguiente método
                
                # Método 3: Conexión con named pipe explícita para Windows
                if self.docker_client is None:
                    try:
                        self.docker_client = docker.DockerClient(base_url='npipe://./pipe/docker_engine')
                        self.docker_client.ping()
                        self.logger.info("Cliente Docker inicializado correctamente (named pipe)")
                    except Exception:
                        pass  # Último intento falló
                
                if self.docker_client is None:
                    self.logger.warning("No se pudo establecer conexión con Docker client")
                    self.logger.warning("Docker parece estar instalado pero el daemon no está accesible")
                    self.logger.info("Sugerencia: Verificar que Docker Desktop esté completamente iniciado")
                    # Solo mostrar último error si es necesario para debugging
                    # if last_error:
                    #     self.logger.debug(f"Último error: {last_error}")
                    self.logger.info("Docker MCP Manager funcionará con capacidades limitadas")
            else:
                self.docker_client = None
                self.logger.info("Docker no está disponible en el sistema")
        except Exception as e:
            self.docker_client = None
            self.logger.warning(f"Error inicializando cliente Docker: {e}")
            self.logger.info("Docker MCP Manager continuará funcionando con capacidades limitadas")
        
        # Cargar catálogo de servidores Docker
        self.docker_servers_catalog = self._load_docker_catalog()
    
    def _load_docker_catalog(self) -> List[Dict]:
        """Carga el catálogo de servidores MCP Docker."""
        try:
            catalog_path = os.path.join(os.path.dirname(__file__), "docker_mcp_servers.json")
            if os.path.exists(catalog_path):
                with open(catalog_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('docker_mcp_servers', [])
            return []
        except Exception as e:
            self.logger.error(f"Error cargando catálogo Docker: {e}")
            return []
    
    def check_docker_availability(self) -> bool:
        """Verifica si Docker está disponible y funcionando."""
        try:
            # Usar nuestro helper para verificar y asegurar Docker
            if not self.docker_helper.ensure_docker_running():
                return False
            
            if self.docker_client is None:
                # Intentar reconectar usando los mismos métodos que en __init__
                self.logger.debug("Intentando reconectar cliente Docker...")
                
                # Método 1: Conexión predeterminada
                try:
                    self.docker_client = docker.from_env()
                    self.docker_client.ping()
                    self.logger.info("Cliente Docker reconectado correctamente (método predeterminado)")
                except Exception:
                    # Método predeterminado falló, intentar siguiente método
                    pass
                
                # Método 2: Conexión TCP si el predeterminado falla
                if self.docker_client is None:
                    try:
                        self.docker_client = docker.DockerClient(base_url='tcp://localhost:2375')
                        self.docker_client.ping()
                        self.logger.info("Cliente Docker reconectado correctamente (TCP)")
                    except Exception:
                        # Método TCP falló, intentar siguiente método
                        pass
                
                # Método 3: Conexión con named pipe explícita para Windows
                if self.docker_client is None:
                    try:
                        self.docker_client = docker.DockerClient(base_url='npipe://./pipe/docker_engine')
                        self.docker_client.ping()
                        self.logger.info("Cliente Docker reconectado correctamente (named pipe)")
                    except Exception:
                        pass
            
            # Verificar que el cliente funciona
            if self.docker_client is not None:
                try:
                    self.docker_client.ping()
                    return True
                except Exception as e:
                    self.logger.debug(f"Error en ping Docker: {e}")
                    self.docker_client = None
            
            # Si llegamos aquí, no hay cliente disponible pero Docker está ejecutándose
            # Esto puede ser normal en algunos casos
            self.logger.warning("Docker está ejecutándose pero el cliente Python no puede conectar")
            return False
            
        except Exception as e:
            self.logger.error(f"Docker no está disponible: {e}")
            return False
    
    def get_available_docker_servers(self) -> List[Dict]:
        """Obtiene la lista de servidores MCP Docker disponibles."""
        if not self.check_docker_availability():
            self.logger.warning("Docker no está disponible")
            return []
        
        # Agregar información de estado de instalación
        for server in self.docker_servers_catalog:
            try:
                image_name = server['docker']['image']
                tag = server['docker'].get('tag', 'latest')
                full_image = f"{image_name}:{tag}"
                
                # Verificar si la imagen está descargada
                try:
                    self.docker_client.images.get(full_image)
                    server['installed'] = True
                except docker.errors.ImageNotFound:
                    server['installed'] = False
                
                # Verificar si hay un contenedor ejecutándose
                server['running'] = self._is_container_running(server['name'])
                
            except Exception as e:
                self.logger.error(f"Error verificando estado de {server['name']}: {e}")
                server['installed'] = False
                server['running'] = False
        
        return self.docker_servers_catalog
    
    def _is_container_running(self, server_name: str) -> bool:
        """Verifica si un contenedor MCP está ejecutándose."""
        try:
            container_name = f"mcp-{server_name}"
            container = self.docker_client.containers.get(container_name)
            return container.status == 'running'
        except docker.errors.NotFound:
            return False
        except Exception as e:
            self.logger.error(f"Error verificando contenedor {server_name}: {e}")
            return False
    
    def install_docker_server(self, server_name: str) -> Tuple[bool, str]:
        """
        Instala (hace pull) de un servidor MCP Docker.
        
        Args:
            server_name: Nombre del servidor a instalar
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.check_docker_availability():
            return False, "Docker no está disponible"
        
        # Buscar el servidor en el catálogo
        server_config = None
        for server in self.docker_servers_catalog:
            if server['name'] == server_name:
                server_config = server
                break
        
        if not server_config:
            return False, f"Servidor {server_name} no encontrado en el catálogo"
        
        try:
            image_name = server_config['docker']['image']
            tag = server_config['docker'].get('tag', 'latest')
            full_image = f"{image_name}:{tag}"
            
            self.logger.info(f"Descargando imagen Docker: {full_image}")
            
            # Hacer pull de la imagen
            self.docker_client.images.pull(image_name, tag=tag)
            
            self.logger.info(f"Imagen {full_image} descargada correctamente")
            return True, f"Servidor {server_name} instalado correctamente"
            
        except Exception as e:
            error_msg = f"Error instalando servidor {server_name}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def start_docker_server(self, server_name: str, env_vars: Dict[str, str] = None) -> Tuple[bool, str]:
        """
        Inicia un servidor MCP Docker como contenedor.
        
        Args:
            server_name: Nombre del servidor a iniciar
            env_vars: Variables de entorno adicionales
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.check_docker_availability():
            return False, "Docker no está disponible"
        
        # Buscar configuración del servidor
        server_config = None
        for server in self.docker_servers_catalog:
            if server['name'] == server_name:
                server_config = server
                break
        
        if not server_config:
            return False, f"Servidor {server_name} no encontrado"
        
        try:
            container_name = f"mcp-{server_name}"
            
            # Verificar si ya está ejecutándose
            if self._is_container_running(server_name):
                return False, f"El servidor {server_name} ya está ejecutándose"
            
            # Preparar configuración de Docker
            docker_config = server_config['docker']
            image_name = docker_config['image']
            tag = docker_config.get('tag', 'latest')
            full_image = f"{image_name}:{tag}"
            
            # Variables de entorno
            environment = docker_config.get('environment', {})
            if env_vars:
                environment.update(env_vars)
            
            # Puertos
            ports = {}
            if 'ports' in docker_config:
                for port_mapping in docker_config['ports']:
                    if ':' in port_mapping:
                        host_port, container_port = port_mapping.split(':')
                        ports[f"{container_port}/tcp"] = host_port
            
            # Volúmenes
            volumes = {}
            if 'volumes' in docker_config:
                for volume_mapping in docker_config['volumes']:
                    if ':' in volume_mapping:
                        host_path, container_path = volume_mapping.split(':')
                        # Crear directorio host si no existe
                        host_full_path = self.docker_data_dir / server_name / host_path.lstrip('./')
                        host_full_path.mkdir(parents=True, exist_ok=True)
                        volumes[str(host_full_path)] = {'bind': container_path, 'mode': 'rw'}
            
            # Crear y ejecutar contenedor
            container = self.docker_client.containers.run(
                full_image,
                name=container_name,
                environment=environment,
                ports=ports,
                volumes=volumes,
                detach=True,
                restart_policy={"Name": "unless-stopped"}
            )
            
            # Esperar un momento para que el contenedor inicie
            time.sleep(2)
            
            # Verificar que esté ejecutándose
            container.reload()
            if container.status == 'running':
                self._save_running_container(server_name, container.id)
                self.logger.info(f"Servidor MCP {server_name} iniciado como contenedor {container_name}")
                return True, f"Servidor {server_name} iniciado correctamente"
            else:
                return False, f"El contenedor {server_name} no pudo iniciarse"
                
        except Exception as e:
            error_msg = f"Error iniciando servidor {server_name}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def stop_docker_server(self, server_name: str) -> Tuple[bool, str]:
        """
        Detiene un servidor MCP Docker.
        
        Args:
            server_name: Nombre del servidor a detener
            
        Returns:
            Tupla (éxito, mensaje)
        """
        if not self.check_docker_availability():
            return False, "Docker no está disponible"
        
        try:
            container_name = f"mcp-{server_name}"
            
            # Obtener el contenedor
            container = self.docker_client.containers.get(container_name)
            
            # Detener el contenedor
            container.stop()
            
            # Remover de la lista de contenedores ejecutándose
            self._remove_running_container(server_name)
            
            self.logger.info(f"Servidor MCP {server_name} detenido")
            return True, f"Servidor {server_name} detenido correctamente"
            
        except docker.errors.NotFound:
            return False, f"Contenedor para {server_name} no encontrado"
        except Exception as e:
            error_msg = f"Error deteniendo servidor {server_name}: {str(e)}"
            self.logger.error(error_msg)
            return False, error_msg
    
    def get_container_logs(self, server_name: str, lines: int = 100) -> str:
        """
        Obtiene los logs de un contenedor MCP.
        
        Args:
            server_name: Nombre del servidor
            lines: Número de líneas de log a obtener
            
        Returns:
            Logs del contenedor
        """
        try:
            container_name = f"mcp-{server_name}"
            container = self.docker_client.containers.get(container_name)
            logs = container.logs(tail=lines).decode('utf-8')
            return logs
        except Exception as e:
            self.logger.error(f"Error obteniendo logs de {server_name}: {e}")
            return f"Error obteniendo logs: {str(e)}"
    
    def _save_running_container(self, server_name: str, container_id: str):
        """Guarda información de un contenedor en ejecución."""
        try:
            running_containers = self._load_running_containers()
            running_containers[server_name] = {
                'container_id': container_id,
                'started_at': time.time()
            }
            
            with open(self.running_containers_file, 'w', encoding='utf-8') as f:
                json.dump(running_containers, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Error guardando información de contenedor: {e}")
    
    def _remove_running_container(self, server_name: str):
        """Remueve información de un contenedor detenido."""
        try:
            running_containers = self._load_running_containers()
            if server_name in running_containers:
                del running_containers[server_name]
                
                with open(self.running_containers_file, 'w', encoding='utf-8') as f:
                    json.dump(running_containers, f, indent=2, ensure_ascii=False)
                    
        except Exception as e:
            self.logger.error(f"Error removiendo información de contenedor: {e}")
    
    def _load_running_containers(self) -> Dict:
        """Carga información de contenedores en ejecución."""
        try:
            if os.path.exists(self.running_containers_file):
                with open(self.running_containers_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            self.logger.error(f"Error cargando contenedores en ejecución: {e}")
            return {}
    
    def get_running_containers(self) -> Dict:
        """Obtiene lista de contenedores MCP en ejecución."""
        running = {}
        try:
            containers = self.docker_client.containers.list()
            for container in containers:
                if container.name.startswith('mcp-'):
                    server_name = container.name[4:]  # Remover prefijo 'mcp-'
                    running[server_name] = {
                        'container_id': container.id,
                        'status': container.status,
                        'ports': container.ports,
                        'image': container.image.tags[0] if container.image.tags else 'unknown'
                    }
        except Exception as e:
            self.logger.error(f"Error obteniendo contenedores en ejecución: {e}")
        
        return running
    
    def cleanup_stopped_containers(self) -> int:
        """
        Limpia contenedores MCP detenidos.
        
        Returns:
            Número de contenedores removidos
        """
        removed_count = 0
        try:
            # Obtener contenedores detenidos con nombre mcp-*
            containers = self.docker_client.containers.list(all=True, filters={'status': 'exited'})
            
            for container in containers:
                if container.name.startswith('mcp-'):
                    try:
                        container.remove()
                        removed_count += 1
                        self.logger.info(f"Contenedor removido: {container.name}")
                    except Exception as e:
                        self.logger.error(f"Error removiendo contenedor {container.name}: {e}")
                        
        except Exception as e:
            self.logger.error(f"Error en limpieza de contenedores: {e}")
        
        return removed_count