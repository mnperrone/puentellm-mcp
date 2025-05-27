import threading
import subprocess
import json
import os
import sys
from pathlib import Path
import time

MCP_CONFIG_FILE = "mcp_servers.json"

class MCPManager:
    def __init__(self, app_logger_func):
        self.servers_config = {}
        self.active_processes = {}
        self.server_ports = {}
        self.logger = app_logger_func
        self._stop_events = {}

    def get_default_config_path(self):
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
        return Path(application_path) / MCP_CONFIG_FILE

    def _get_default_mcp_config_with_paths(self):
        try:
            home_dir = Path.home()
            downloads_dir = home_dir / "Downloads"
            documents_dir = home_dir / "Documents"
            default_paths_to_check = [home_dir, downloads_dir, documents_dir]
            resolved_paths = [str(p.resolve()) for p in default_paths_to_check if p.exists() and p.is_dir()]
            if not resolved_paths:
                resolved_paths.append(str(home_dir / "TYPE_VALID_PATH_HERE_1"))
                resolved_paths.append(str(home_dir / "TYPE_VALID_PATH_HERE_2"))
            elif len(resolved_paths) == 1:
                resolved_paths.append(str(resolved_paths[0] / "TYPE_ANOTHER_VALID_PATH_HERE"))
        except Exception as e:
            self.logger(f"Error obteniendo rutas por defecto: {e}. Usando placeholders.", "warning")
            resolved_paths = ["C:/TYPE_VALID_PATH_1_HERE", "C:/TYPE_VALID_PATH_2_HERE"]
        config_template = {
            "mcpServers": {
                "filesystem": {
                    "command": "npx",
                    "args": ["-y", "@modelcontextprotocol/server-filesystem"] + resolved_paths,
                    "enabled": True, "port": 8080
                }}}
        return config_template

    def load_config(self, config_path=None):
        path_to_load = Path(config_path) if config_path else self.get_default_config_path()
        try:
            if not path_to_load.exists():
                self.logger(f"Archivo de configuración MCP no encontrado en {path_to_load}. Creando uno por defecto.", "system")
                default_config_with_paths = self._get_default_mcp_config_with_paths()
                with open(path_to_load, 'w') as f: json.dump(default_config_with_paths, f, indent=4)
                self.servers_config = default_config_with_paths
                self.logger(f"Configuración por defecto creada en {path_to_load}. Revísala.", "system")
            else:
                with open(path_to_load, 'r') as f: self.servers_config = json.load(f)
                self.logger(f"Configuración MCP cargada desde {path_to_load}.", "system")
            base_port = 8080
            self.server_ports = {}
            for name, config_data in self.servers_config.get("mcpServers", {}).items():
                if config_data.get("enabled", True):
                    self.server_ports[name] = config_data.get("port", base_port); base_port +=1
            return True
        except Exception as e:
            self.logger(f"Error al cargar o crear la configuración MCP ({path_to_load}): {e}", "error")
            self.servers_config = {"mcpServers": {}}; return False

    def get_active_server_names(self):
        return [name for name, config in self.servers_config.get("mcpServers", {}).items() if config.get("enabled", True)]

    def start_server(self, server_name):
        if server_name in self.active_processes and self.active_processes[server_name].poll() is None:
            self.logger(f"Servidor MCP '{server_name}' ya está activo.", "system"); return True
        config_data = self.servers_config.get("mcpServers", {}).get(server_name)
        if not config_data or not config_data.get("enabled", True):
            self.logger(f"Servidor MCP '{server_name}' no encontrado o deshabilitado.", "error"); return False
        try:
            command_executable = config_data["command"]
            if os.name == 'nt' and command_executable.lower() == 'npx': command_executable = 'npx.cmd'
            command_list = [command_executable] + config_data["args"]
            self.logger(f"Iniciando servidor MCP '{server_name}': {' '.join(command_list)}", "system")
            preexec_fn = os.setsid if os.name != 'nt' else None
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
            process = subprocess.Popen(
                command_list, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, bufsize=1, universal_newlines=True, preexec_fn=preexec_fn, creationflags=creationflags)
            self.active_processes[server_name] = process
            self._stop_events[server_name] = threading.Event()
            threading.Thread(target=self._log_pipe, args=(process.stderr, f"{server_name}-stderr", "mcp_stderr_log", self._stop_events[server_name]), daemon=True).start()
            self.logger(f"Servidor MCP '{server_name}' iniciado (PID: {process.pid}). Esperando inicialización...", "system")
            threading.Timer(2.5, lambda: self.check_server_startup(server_name, process)).start()
            return True
        except FileNotFoundError:
            self.logger(f"Error al iniciar '{server_name}': Comando '{command_executable}' no encontrado.", "error"); return False
        except Exception as e:
            self.logger(f"Error al iniciar el servidor MCP '{server_name}': {e}", "error")
            if server_name in self.active_processes: self.active_processes.pop(server_name, None)
            return False

    def check_server_startup(self, server_name, process):
        if process.poll() is not None:
            self.logger(f"El servidor MCP '{server_name}' terminó inesperadamente (código: {process.returncode}).", "error")
            if server_name in self.active_processes and self.active_processes[server_name] == process:
                self.active_processes.pop(server_name)
            if server_name in self._stop_events:
                 self._stop_events[server_name].set()
                 self._stop_events.pop(server_name, None)
        else:
             self.logger(f"Servidor MCP '{server_name}' (PID: {process.pid}) parece estar activo.", "system")

    def _log_pipe(self, pipe, pipe_name, tag, stop_event):
        try:
            while not stop_event.is_set():
                try:
                    if stop_event.is_set(): break
                    line = pipe.readline()
                    if not line: break
                    if stop_event.is_set(): break
                    log_line = line.strip()
                    self.logger(f"[{pipe_name}] {log_line}", tag)
                except ValueError: break
                except Exception as e_read:
                    if stop_event.is_set(): break
                    self.logger(f"Error de lectura en {pipe_name}: {e_read}", "error")
                    break
        except Exception as e_outer:
            if not stop_event.is_set():
                 self.logger(f"Excepción externa en _log_pipe para {pipe_name}: {e_outer}", "error")
        finally:
            pass

    def stop_server(self, server_name, log_not_active=True):
        process = self.active_processes.get(server_name)
        stop_event = self._stop_events.get(server_name)
        if stop_event:
            stop_event.set()
        if process and process.poll() is None:
            self.logger(f"Deteniendo servidor MCP '{server_name}' (PID: {process.pid})...", "system")
            try:
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], check=False, capture_output=True)
                else:
                    try: os.killpg(os.getpgid(process.pid), subprocess.signal.SIGTERM)
                    except ProcessLookupError: pass
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.logger(f"Servidor '{server_name}' no respondió a SIGTERM/taskkill, forzando...", "warning")
                try:
                    if os.name == 'nt':
                        subprocess.run(['taskkill', '/F', '/T', '/PID', str(process.pid)], check=False, capture_output=True)
                    else:
                        try: os.killpg(os.getpgid(process.pid), subprocess.signal.SIGKILL)
                        except ProcessLookupError: pass
                    process.wait(timeout=3)
                except Exception as e_kill:
                    self.logger(f"Error al forzar detención de '{server_name}': {e_kill}", "error")
            except Exception as e:
                self.logger(f"Error al detener servidor '{server_name}': {e}", "error")
            finally:
                status_msg = "detenido" if process.poll() is not None else "podría no haberse detenido"
                self.logger(f"Servidor MCP '{server_name}' {status_msg}.", "system")
                if server_name in self._stop_events: self._stop_events.pop(server_name, None)
            self.active_processes.pop(server_name, None); return True
        if server_name in self._stop_events: self._stop_events.pop(server_name, None)
        if log_not_active: self.logger(f"Servidor MCP '{server_name}' no estaba activo.", "system")
        return False

    def stop_all_servers(self):
        self.logger("Intentando detener todos los servidores MCP activos...", "system")
        active_names = list(self.active_processes.keys())
        if not active_names: self.logger("No hay MCPs activos para detener.", "system"); return
        for server_name in active_names:
            if server_name in self._stop_events:
                self._stop_events[server_name].set()
        for name in active_names:
            self.stop_server(name, log_not_active=False)
        self.logger("Órdenes de detención enviadas a MCPs activos.", "system")

    def send_command_to_mcp(self, server_name, method, params):
        if server_name not in self.active_processes or self.active_processes[server_name].poll() is not None:
            self.logger(f"Servidor MCP '{server_name}' no activo. Intentando iniciar...", "mcp_comm")
            if not self.start_server(server_name): return {"error": {"code": -1, "message": f"MCP '{server_name}' no pudo iniciarse."}}
            time.sleep(3)
        process = self.active_processes.get(server_name)
        if not process or process.poll() is not None:
             return {"error": {"code": -1, "message": f"MCP '{server_name}' no disponible."}}
        request_id = f"{server_name}-{threading.get_ident()}-{time.time()}"
        json_rpc_request = {"jsonrpc": "2.0", "method": method, "params": params if params is not None else {}, "id": request_id}
        request_str = json.dumps(json_rpc_request)
        self.logger(f"-> {server_name}: {request_str}", "mcp_comm")
        try:
            process.stdin.write(request_str + '\n'); process.stdin.flush()
            response_lines = []; timeout_duration = 15
            def read_mcp_line(proc, lines):
                try: line = proc.stdout.readline(); lines.append(line) if line else None
                except Exception as e: self.logger(f"Error leyendo stdout de {server_name}: {e}", "error")
            read_thread = threading.Thread(target=read_mcp_line, args=(process, response_lines)); read_thread.start(); read_thread.join(timeout=timeout_duration)
            if not response_lines:
                self.logger(f"Timeout ({timeout_duration}s) en {server_name} para '{method}'.", "error")
                return {"error": {"code": -2, "message": f"Timeout en {server_name}"}}
            response_str = response_lines[0].strip()
            try:
                response_json = json.loads(response_str)
                log_detail = json.dumps(response_json) if len(json.dumps(response_json))<200 else f"JSON (id: {response_json.get('id')}, keys: {list(response_json.keys())})"
                self.logger(f"<- {server_name}: {log_detail}", "mcp_comm")
                if "error" in response_json and response_json.get("id")==request_id:
                    self.logger(f"Error JSON-RPC de {server_name}: {response_json['error']}", "mcp_comm")
                elif response_json.get("id")!=request_id:
                    self.logger(f"ID de respuesta de {server_name} ({response_json.get('id')}) no coincide ({request_id}).", "warning")
                return response_json
            except json.JSONDecodeError:
                self.logger(f"Respuesta no JSON de {server_name}: {response_str}", "error"); return {"error": {"code":-3, "message":"Respuesta no JSON", "data":response_str}}
        except Exception as e:
            self.logger(f"Excepción en comunicación con {server_name}: {e}", "error"); return {"error": {"code":-4, "message":str(e)}}
