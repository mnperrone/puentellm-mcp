import threading
from ui_helpers import display_message
import psutil
import os
import subprocess
from assets.logging import PersistentLogger

# Importamos el selector dinámico de LLMs
from llm_providers import get_llm_handler
from llm_providers.llm_exception import LLMConnectionError  # Creamos esta clase más adelante


class LLMBridge:
    def __init__(self, model, chat_text, window, provider="ollama"):
        self.model = model
        self.chat_text = chat_text
        self.window = window
        self.stop_event = threading.Event()
        self.assistant_response_active = False
        self.provider = provider
        self.handler = None
        self.logger = PersistentLogger()  # Logger persistente para registrar eventos y errores
        self.ollama_process = None        # Para gestión futura de procesos Ollama
        self.response_callback = None     # Callback opcional para respuestas
        self._init_handler()

    def _init_handler(self):
        """Inicializa el handler según el proveedor y modelo, con manejo de errores detallado"""
        try:
            self.handler = get_llm_handler(
                provider_name=self.provider,
                model=self.model
            )
        except Exception as e:
            # Mostrar el error en el chat si es posible
            if self.window and self.chat_text and hasattr(self.window, 'after'):
                self.window.after(0, display_message, self.chat_text, f"Error inicializando LLMBridge: {str(e)}", "error")
            self.handler = None
            raise LLMConnectionError(str(e))

    def set_model(self, model):
        """Actualiza el modelo y vuelve a inicializar el handler"""
        self.model = model
        self._init_handler()

    def set_provider(self, provider):
        """Cambia el proveedor de LLM (ej: ollama, openai_compatible, qwen)"""
        self.provider = provider
        self._init_handler()

    def _is_ollama_running(self):
        """Verifica si el proceso de Ollama está activo (usado solo para mensajes informativos)"""
        if os.name == 'nt':  # Windows
            try:
                for proc in psutil.process_iter(['name']):
                    if 'ollama' in proc.info['name'].lower():
                        return True
                return False
            except Exception:
                return False
        else:  # Linux/Mac
            try:
                result = subprocess.run(['pgrep', '-f', 'ollama'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return result.returncode == 0
            except Exception:
                return False

    def _show_error_and_stop(self, error):
        """Muestra un mensaje de error y detiene la respuesta."""
        try:
            if self.window.winfo_exists():
                self.window.after(0, display_message, self.chat_text, f"Error: {str(error)}", "error")
            self.stop_event.set()
            self.assistant_response_active = False
        except Exception:
            pass

    def stop_response(self):
        self.stop_event.set()
        self.assistant_response_active = False

    def process_user_input(self, user_input, system_prompt, callback, previous_mcp_response_json=None):
        messages = [{"role": "system", "content": system_prompt}]
        if previous_mcp_response_json:
            messages.append({"role": "user", "content": (
                f"Esta es una respuesta JSON de un servidor MCP. Interprétala para mí en español conversacional. "
                f"No intentes ejecutar otro comando MCP ahora. Respuesta MCP JSON:\n{previous_mcp_response_json}" )})
        else:
            messages.append({"role": "user", "content": user_input})

        self.assistant_response_active = True
        self.stop_event.clear()

        # Si usamos Ollama local, verificamos si está corriendo
        if self.provider == "ollama" and not self._is_ollama_running():
            error = LLMConnectionError("Ollama no está corriendo. Por favor, inicia el servicio Ollama.")
            self._show_error_and_stop(error)
            return

        def run():
            try:
                full_response = ""
                for chunk in self.handler.stream(messages):
                    if self.stop_event.is_set():
                        break
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        full_response += content
                        if self.window.winfo_exists():
                            self.window.after(0, callback, content)
                    # Detener si se detecta un comando MCP
                    if "MCP_COMMAND_JSON:" in full_response and (content.endswith("}") or content.endswith("}\n")):
                        break
                if self.window.winfo_exists():
                    self.window.after(0, callback, None, full_response)
            except Exception as e:
                self._show_error_and_stop(f"Error procesando entrada: {str(e)}")
            finally:
                self.assistant_response_active = False

        threading.Thread(target=run, daemon=True).start()

