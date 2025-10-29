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
    def __init__(self, model, chat_text, window, provider="ollama", api_key=None, base_url=None):
        self.model = model
        self.chat_text = chat_text
        self.window = window
        self.stop_event = threading.Event()
        self.assistant_response_active = False
        self.provider = provider
        self.api_key = api_key
        self.base_url = base_url
        self.handler = None
        self.logger = PersistentLogger()  # Logger persistente para registrar eventos y errores
        self.ollama_process = None        # Para gestión futura de procesos Ollama
        self.response_callback = None     # Callback opcional para respuestas
        self._init_handler()

    def _init_handler(self):
        """Inicializa el handler según el proveedor y modelo, con manejo de errores detallado"""
        try:
            # Registro de valores de inicialización
            self.logger.info(f"Initializing LLM handler - Provider: {self.provider}, Model: {self.model}")
            
            # Configurar las variables de entorno necesarias
            if self.api_key:
                self.logger.info(f"Setting API key for {self.provider}")
                os.environ[f"{self.provider.upper()}_API_KEY"] = self.api_key
            if self.base_url and self.provider != "ollama":
                self.logger.info(f"Setting base URL for {self.provider}: {self.base_url}")
                os.environ[f"{self.provider.upper()}_API_BASE"] = self.base_url
            
            self.logger.info("Getting LLM handler...")
            self.handler = get_llm_handler(
                provider_name=self.provider,
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url
            )
            self.logger.info("LLM handler initialized successfully")
        except Exception as e:
            error_msg = f"Error initializing LLM handler: {str(e)}"
            self.logger.error(error_msg)
            self.logger.error(f"Provider: {self.provider}")
            self.logger.error(f"Model: {self.model}")
            self.logger.error(f"Base URL: {self.base_url}")
            
            # Mostrar el error en el chat si es posible
            if self.window and self.chat_text and hasattr(self.window, 'after'):
                self.window.after(0, display_message, self.chat_text, f"Error inicializando LLMBridge: {str(e)}", "error")
            
            self.handler = None
            raise LLMConnectionError(error_msg)

    def set_model(self, model):
        """Actualiza el modelo y vuelve a inicializar el handler"""
        self.model = model
        self._init_handler()

    # Compatibility helpers used by the GUI (legacy API)
    def set_response_callback(self, cb):
        """Compatibility: store a response callback provided by the UI."""
        self.response_callback = cb

    def set_mcp_handler(self, handler):
        """Compatibility: store an MCP handler reference (not used directly here)."""
        self.mcp_handler = handler

    def generate_response(self, user_input, system_prompt=""):
        """Compatibility wrapper used by the UI to start a response generation.

        This will start the process_user_input in a background thread and forward
        chunks to the stored response_callback (if any).
        """
        callback = None
        if hasattr(self, 'response_callback') and self.response_callback:
            # Wrap the stored callback to accept a single argument (content)
            def _cb(content):
                try:
                    # forward chunks and final full response
                    self.response_callback(content)
                except Exception:
                    pass
            callback = _cb
        else:
            # fallback no-op
            def callback(x):
                return

        # Use empty system prompt if none provided
        try:
            self.process_user_input(user_input, system_prompt or "", callback)
        except Exception:
            # swallow to avoid crashing UI thread; real errors are logged
            pass

    def pull_model(self, model_name):
        """Attempt to pull a model (best-effort).

        If the provider handler exposes a `pull_model` method, call it.
        For Ollama this may trigger a download.
        """
        try:
            if self.handler and hasattr(self.handler, 'pull_model'):
                return self.handler.pull_model(model_name)
            # No-op if unsupported
            return None
        except Exception as e:
            self.logger.error(f"Error pulling model {model_name}: {e}")
            raise

    def stop(self):
        """Stop any ongoing generation and release resources."""
        try:
            self.stop_response()
            # If handler exposes stop/close, call it
            if self.handler and hasattr(self.handler, 'close'):
                try:
                    self.handler.close()
                except Exception:
                    pass
        except Exception:
            pass

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

    def list_models(self):
        """Obtiene la lista de modelos disponibles del proveedor actual."""
        try:
            if not self.handler:
                self._init_handler()
            return self.handler.list_models()
        except Exception as e:
            self.logger.error(f"Error al listar modelos: {str(e)}")
            return []

    def process_user_input(self, user_input, system_prompt, callback, previous_mcp_response_json=None):
        print(f"\n=== Processing User Input ===")
        print(f"System prompt: {system_prompt[:50]}...")
        print(f"User input: {user_input[:50]}...")
        print(f"Has previous MCP response: {bool(previous_mcp_response_json)}")
        
        messages = [{"role": "system", "content": system_prompt}]
        if previous_mcp_response_json:
            messages.append({"role": "user", "content": (
                f"Esta es una respuesta JSON de un servidor MCP. Interprétala para mí en español conversacional. "
                f"No intentes ejecutar otro comando MCP ahora. Respuesta MCP JSON:\n{previous_mcp_response_json}" )})
        else:
            messages.append({"role": "user", "content": user_input})

        print("Messages prepared for LLM")
        self.assistant_response_active = True
        self.stop_event.clear()

        # Si usamos Ollama local, verificamos si está corriendo
        if self.provider == "ollama" and not self._is_ollama_running():
            error = LLMConnectionError("Ollama no está corriendo. Por favor, inicia el servicio Ollama.")
            print(f"Error: Ollama not running")
            self._show_error_and_stop(error)
            return

        print("Provider checks passed, proceeding with generation...")

        def run():
            print("\n=== Starting Message Generation ===")
            try:
                print("Initializing handler if needed...")
                full_response = ""
                streamed = False
                for chunk in self.handler.stream(messages):
                    if self.stop_event.is_set():
                        break
                    content = chunk.get('message', {}).get('content', '')
                    if content:
                        streamed = True
                        full_response += content
                        # Send structured chunk event to the UI (content + final flag)
                        if self.window.winfo_exists():
                            self.window.after(0, callback, {"content": content, "final": False})
                    # Detener si se detecta un comando MCP
                    if "MCP_COMMAND_JSON:" in full_response and (content.endswith("}") or content.endswith("}\n")):
                        break

                # After streaming, send a final event. If we streamed, final event will indicate completion
                # without sending the full response again. If there was no streaming, send the full response as final.
                if self.window.winfo_exists():
                    if streamed:
                        # Inform UI that stream finished
                        self.window.after(0, callback, {"content": "", "final": True})
                    else:
                        # Non-streamed providers: send the full response once as final
                        self.window.after(0, callback, {"content": full_response, "final": True})
            except Exception as e:
                self._show_error_and_stop(f"Error procesando entrada: {str(e)}")
            finally:
                self.assistant_response_active = False

        threading.Thread(target=run, daemon=True).start()

