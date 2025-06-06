import json
import threading
import asyncio
import os  # Añadido para verificar la existencia de archivos
from ui_helpers import log_to_chat_on_ui_thread
import re  # Para mejor procesamiento del JSON
from assets.logging import PersistentLogger

class LLMMCPHandler:
    """
    Clase para manejar la interacción entre el LLM (Lenguaje Large Model) y los servidores MCP.
    Incluye soporte para MCP (Model Context Protocol) y manejo de errores mejorado.
    """
    def __init__(self, mcp_manager, sdk_bridge, window, chat_text):
        """
        Inicializa una nueva instancia del manejador LLM-MCP.
        Args:
            mcp_manager: Instancia de MCPManager
            sdk_bridge: Instancia de MCPSDKBridge
            window: Ventana principal de la aplicación
            chat_text: Widget de texto donde mostrar los mensajes
        """
        self.mcp_manager = mcp_manager
        self.sdk_bridge = sdk_bridge
        self.window = window
        self.chat_text = chat_text
        self.logger = PersistentLogger()
        self._is_closing = False

    def handle_mcp_command_from_llm(self, llm_response_text, callback):
        """Maneja un comando MCP generado por el LLM."""
        command_prefix = "MCP_COMMAND_JSON:"
        
        try:
            # Extraer el JSON usando expresiones regulares para mayor robustez
            json_match = re.search(r'\{(?:[^{}]|(?R))*\}|$$$(?:[^$$]|(?R))*$$', llm_response_text)
            if not json_match:
                raise ValueError(f"No se encontró JSON válido en la respuesta del LLM: '{llm_response_text[:200]}...'")
            
            json_str_part = json_match.group(0)
            
            # Validar que el JSON tenga las claves necesarias
            mcp_cmd_data = json.loads(json_str_part)
            required_keys = ['server', 'method']
            missing_keys = [key for key in required_keys if key not in mcp_cmd_data]
            
            if missing_keys:
                raise ValueError(f"Faltan claves requeridas en el comando MCP: {missing_keys}")
            
            log_to_chat_on_ui_thread(self.window, self.chat_text, f"LLM -> MCP: {json_str_part}", "mcp_comm")
            
            server = mcp_cmd_data.get('server')
            method = mcp_cmd_data.get('method')
            params = mcp_cmd_data.get('params')
            
            # Verificar si el servidor está configurado
            config = self.mcp_manager.servers_config.get("mcpServers", {}).get(server)
            if not config:
                raise ValueError(f"No se encontró configuración para el servidor '{server}'")
            
            if not config.get('enabled', False):
                raise ValueError(f"El servidor '{server}' está deshabilitado en la configuración")
            
            # Encontrar el script del servidor
            script_path = None
            for arg in config.get("args", []):
                if isinstance(arg, str) and (arg.endswith('.py') or arg.endswith('.js')):
                    script_path = arg
                    break
            
            if not script_path or not os.path.exists(script_path):
                raise ValueError(f"No se encontró script .py/.js para {server} en args: {config.get('args')}")
            
            # Ejecutar el comando MCP en un hilo separado
            def run_sdk_tool():
                try:
                    # Usar el SDK Bridge para ejecutar el comando MCP
                    loop = asyncio.new_event_loop()
                    tools = loop.run_until_complete(self.sdk_bridge.connect(script_path))
                    
                    # Encontrar la herramienta especificada
                    tool_obj = next((t for t in tools if t.name == method), None)
                    if not tool_obj:
                        raise ValueError(f"No se encontró la herramienta '{method}' en el SDK para {server}")
                    
                    # Ejecutar la herramienta
                    result = loop.run_until_complete(self.sdk_bridge.call_tool(tool_obj, params or {}))
                    result_content = getattr(result, 'content', str(result))
                    
                    log_to_chat_on_ui_thread(self.window, self.chat_text, f"MCP -> LLM: Resultado de {method}: {result_content}", "system")
                    callback(result_content)
                except Exception as e:
                    error_msg = f"Error ejecutando herramienta MCP {server}.{method}: {str(e)}"
                    log_to_chat_on_ui_thread(self.window, self.chat_text, error_msg, "error")
                    callback(f"{{\"error\": \"{error_msg}\"}}")
            
            # Ejecutar en hilo separado para no bloquear la UI
            threading.Thread(target=run_sdk_tool, daemon=True).start()
            
        except json.JSONDecodeError as e:
            error_msg = f"Error decodificando JSON del LLM: {str(e)}. JSON: '{json_str_part[:200]}...'"
            log_to_chat_on_ui_thread(self.window, self.chat_text, error_msg, "error")
            callback(f"{{\"error\": \"{error_msg}\"}}")
        except ValueError as e:
            error_msg = str(e)
            log_to_chat_on_ui_thread(self.window, self.chat_text, error_msg, "error")
            callback(f"{{\"error\": \"{error_msg}\"}}")
        except Exception as e:
            error_msg = f"Error inesperado procesando comando MCP: {str(e)}"
            log_to_chat_on_ui_thread(self.window, self.chat_text, error_msg, "error")
            callback(f"{{\"error\": \"{error_msg}\"}}")

