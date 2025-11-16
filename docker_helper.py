"""
Docker Helper - Utilidades para asegurar que Docker esté disponible
Maneja la verificación, inicio y gestión de Docker Desktop en Windows
"""

import subprocess
import time
import platform
import os
from typing import Optional, Tuple, List
import json


class DockerHelper:
    """Clase para gestionar Docker Desktop y sus servicios."""
    
    def __init__(self, logger=None):
        self.logger = logger
        self.system = platform.system()
        self.is_windows = self.system == "Windows"
        self.is_linux = self.system == "Linux"
        self.is_macos = self.system == "Darwin"
    
    def log(self, message: str, level: str = "info"):
        """Log con logger si está disponible, sino print."""
        if self.logger:
            getattr(self.logger, level, self.logger.info)(message)
        else:
            print(message)
    
    def run_command(self, cmd: List[str], check: bool = True, capture_output: bool = True, timeout: int = 30) -> Tuple[bool, str]:
        """
        Ejecuta un comando y devuelve (éxito, salida).
        
        Args:
            cmd: Lista de comandos a ejecutar
            check: Si debe fallar con error de retorno
            capture_output: Si debe capturar stdout/stderr
            timeout: Timeout en segundos
            
        Returns:
            Tupla (éxito, salida)
        """
        try:
            result = subprocess.run(
                cmd,
                check=check,
                capture_output=capture_output,
                text=True,
                timeout=timeout
            )
            return True, result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() if e.stderr else str(e)
            return False, error_msg
        except subprocess.TimeoutExpired:
            return False, f"Comando expiró después de {timeout} segundos"
        except FileNotFoundError:
            return False, f"Comando no encontrado: {' '.join(cmd)}"
        except Exception as e:
            return False, str(e)
    
    def is_docker_installed(self) -> bool:
        """Verifica si Docker está instalado."""
        success, output = self.run_command(["docker", "--version"], check=False)
        if success:
            self.log(f"✅ Docker instalado: {output}")
            return True
        else:
            self.log("❌ Docker no está instalado", "error")
            return False
    
    def is_docker_running(self) -> bool:
        """Verifica si Docker daemon está ejecutándose."""
        success, output = self.run_command(["docker", "info"], check=False, timeout=10)
        
        if success and any(keyword in output for keyword in ["Server:", "Containers:", "Images:"]):
            return True
        
        # Verificación adicional con ping
        success, _ = self.run_command(["docker", "system", "df"], check=False, timeout=5)
        return success
    
    def find_docker_desktop_executable(self) -> Optional[str]:
        """Encuentra la ruta del ejecutable Docker Desktop."""
        if self.is_windows:
            possible_paths = [
                r"C:\Program Files\Docker\Docker\Docker Desktop.exe",
                r"C:\Program Files (x86)\Docker\Docker\Docker Desktop.exe",
                os.path.expanduser(r"~\AppData\Local\Docker\Docker Desktop.exe")
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    return path
        
        elif self.is_macos:
            return "/Applications/Docker.app/Contents/MacOS/Docker Desktop"
        
        return None
    
    def start_docker_desktop(self) -> bool:
        """Inicia el daemon de Docker según el sistema operativo."""
        self.log("🔄 Intentando iniciar daemon de Docker...")
        
        if self.is_windows:
            return self._start_docker_windows()
        elif self.is_macos:
            return self._start_docker_macos()
        elif self.is_linux:
            return self._start_docker_linux()
        else:
            self.log("❌ Sistema operativo no soportado", "error")
            return False
    
    def _start_docker_windows(self) -> bool:
        """Inicia el daemon de Docker en Windows."""
        # Solo intentar iniciar el servicio Docker daemon
        self.log("📋 Intentando iniciar servicio Docker daemon...")
        success, output = self.run_command([
            "powershell", "-Command", 
            "Start-Service", "docker"
        ], check=False)
        
        if success:
            self.log("✅ Servicio Docker daemon iniciado correctamente")
            return self._wait_for_docker(timeout=60)
        else:
            self.log(f"❌ No se pudo iniciar el servicio Docker daemon: {output}", "error")
            return False
    
    def _start_docker_macos(self) -> bool:
        """Inicia Docker Desktop en macOS."""
        success, _ = self.run_command(["open", "-a", "Docker"], check=False)
        
        if success:
            self.log("🚀 Docker Desktop iniciado en macOS")
            return self._wait_for_docker(timeout=60)
        else:
            self.log("❌ No se pudo iniciar Docker Desktop en macOS", "error")
            return False
    
    def _start_docker_linux(self) -> bool:
        """Inicia Docker en Linux."""
        # En Linux, intentar iniciar el servicio systemd
        success, output = self.run_command([
            "sudo", "systemctl", "start", "docker"
        ], check=False)
        
        if success:
            self.log("🚀 Servicio Docker iniciado en Linux")
            return self._wait_for_docker(timeout=30)
        else:
            self.log(f"❌ No se pudo iniciar Docker en Linux: {output}", "error")
            return False
    
    def _wait_for_docker(self, timeout: int = 60) -> bool:
        """Espera a que Docker esté disponible."""
        self.log(f"⏳ Esperando a que Docker esté disponible (timeout: {timeout}s)...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.is_docker_running():
                elapsed = int(time.time() - start_time)
                self.log(f"✅ Docker está disponible después de {elapsed}s")
                return True
            
            time.sleep(2)
            self.log("🔄 Verificando Docker...", "debug")
        
        self.log(f"❌ Docker no estuvo disponible después de {timeout}s", "error")
        return False
    
    def ensure_docker_running(self) -> bool:
        """
        Garantiza que Docker esté ejecutándose.
        Intenta iniciarlo si no está disponible.
        
        Returns:
            True si Docker está disponible, False si no se pudo iniciar
        """
        # 1. Verificar si está instalado
        if not self.is_docker_installed():
            self.log("❌ Docker no está instalado. Descárgalo desde: https://docker.com/get-started", "error")
            return False
        
        # 2. Verificar si está ejecutándose
        if self.is_docker_running():
            self.log("✅ Docker ya está ejecutándose")
            return True
        
        # 3. Intentar iniciarlo
        self.log("🔍 Docker no está activo, intentando iniciar daemon...")
        return self.start_docker_desktop()
    
    def run_docker_command(self, *args, timeout: int = 30) -> Tuple[bool, str]:
        """
        Ejecuta un comando Docker asegurando que esté disponible.
        
        Args:
            *args: Argumentos para docker
            timeout: Timeout en segundos
            
        Returns:
            Tupla (éxito, salida)
        """
        if not self.ensure_docker_running():
            return False, "Docker no está disponible"
        
        cmd = ["docker"] + list(args)
        self.log(f"▶️  Ejecutando: {' '.join(cmd)}")
        
        return self.run_command(cmd, timeout=timeout)
    
    def get_docker_info(self) -> dict:
        """Obtiene información detallada de Docker."""
        success, output = self.run_docker_command("system", "info", "--format", "json")
        
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"raw_output": output}
        
        return {"error": output}
    
    def get_docker_version(self) -> dict:
        """Obtiene versión de Docker."""
        success, output = self.run_docker_command("version", "--format", "json")
        
        if success:
            try:
                return json.loads(output)
            except json.JSONDecodeError:
                return {"raw_output": output}
        
        return {"error": output}
    
    def list_docker_containers(self, all_containers: bool = True) -> List[dict]:
        """Lista contenedores Docker."""
        args = ["ps", "--format", "json"]
        if all_containers:
            args.insert(1, "-a")
        
        success, output = self.run_docker_command(*args)
        
        if success and output:
            try:
                # Docker puede devolver múltiples JSON objects separados por líneas
                containers = []
                for line in output.strip().split('\n'):
                    if line.strip():
                        containers.append(json.loads(line))
                return containers
            except json.JSONDecodeError:
                return [{"raw_output": output}]
        
        return []
    
    def check_mcp_docker_availability(self) -> bool:
        """Verifica si las imágenes MCP de Docker están disponibles."""
        success, output = self.run_docker_command("search", "mcp", "--limit", "5")
        
        if success and "mcp/" in output:
            self.log("✅ Imágenes MCP disponibles en Docker Hub")
            return True
        else:
            self.log("⚠️  No se encontraron imágenes MCP o hay problemas de conectividad")
            return False


# Funciones de conveniencia para importación simple
_docker_helper = None

def get_docker_helper(logger=None):
    """Obtiene instancia singleton de DockerHelper."""
    global _docker_helper
    if _docker_helper is None:
        _docker_helper = DockerHelper(logger)
    return _docker_helper

def ensure_docker_running(logger=None) -> bool:
    """Función de conveniencia para asegurar que Docker esté ejecutándose."""
    return get_docker_helper(logger).ensure_docker_running()

def run_docker_command(*args, timeout: int = 30, logger=None) -> Tuple[bool, str]:
    """Función de conveniencia para ejecutar comandos Docker."""
    return get_docker_helper(logger).run_docker_command(*args, timeout=timeout)

def is_docker_available(logger=None) -> bool:
    """Función de conveniencia para verificar disponibilidad de Docker."""
    helper = get_docker_helper(logger)
    return helper.is_docker_installed() and helper.is_docker_running()


# Script de prueba
if __name__ == "__main__":
    print("=== Docker Helper - Verificación de Entorno ===")
    
    helper = DockerHelper()
    
    print("\n🔍 Verificando Docker...")
    if helper.ensure_docker_running():
        print("\n📊 Información de Docker:")
        docker_info = helper.get_docker_info()
        if 'ServerVersion' in docker_info:
            print(f"   • Versión: {docker_info['ServerVersion']}")
        if 'Containers' in docker_info:
            print(f"   • Contenedores: {docker_info['Containers']}")
        if 'Images' in docker_info:
            print(f"   • Imágenes: {docker_info['Images']}")
        
        print("\n📦 Contenedores MCP:")
        containers = helper.list_docker_containers()
        mcp_containers = [c for c in containers if 'mcp' in c.get('Names', '').lower()]
        
        if mcp_containers:
            for container in mcp_containers:
                print(f"   • {container.get('Names', 'Unknown')} - {container.get('Status', 'Unknown')}")
        else:
            print("   • No hay contenedores MCP ejecutándose")
        
        print("\n🌐 Verificando disponibilidad MCP en Docker Hub...")
        helper.check_mcp_docker_availability()
        
        print("\n✅ Docker está completamente configurado y disponible!")
    else:
        print("\n❌ Docker no está disponible")
        print("💡 Sugerencias:")
        print("   1. Instala Docker Desktop desde: https://docker.com/get-started")
        print("   2. Asegúrate de que Docker Desktop esté ejecutándose")
        print("   3. Verifica que tu usuario tenga permisos para Docker")