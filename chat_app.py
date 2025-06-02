import tkinter as tk
import customtkinter as ctk
import threading
import json
from tkinter import filedialog, messagebox
from pathlib import Path
import time
from mcp_manager import MCPManager
from mcp_sdk_bridge import MCPSDKBridge
import asyncio
from ui_helpers import display_message, log_to_chat_on_ui_thread
from llm_bridge import LLMBridge
from llm_mcp_handler import LLMMCPHandler
from app_config import AppConfig
import strictjson
from mcp_config_window import MCPConfigWindow
from llm_providers.llm_exception import LLMConnectionError


class ChatApp:
    def __init__(self):
        # Inicialización de atributos para evitar errores
        self.mcp_menu_popup = None
        self.assistant_response_active = False
        self.window = ctk.CTk()
        self.window.title("LLM - MCP Bridge Chat")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        try:
            icon_path = Path(__file__).parent / "assets" / "icons" / "icono.ico"
            if icon_path.exists():
                try:
                    self.window.iconbitmap(str(icon_path))
                except Exception as e:
                    print(f"[Advertencia] No se pudo establecer el icono: {e}")
            else:
                print(f"[Advertencia] El icono no existe en: {icon_path}")
        except Exception as e:
            print(f"[Advertencia] No se pudo cargar el icono: {e}")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Estilo visual
        self.window.tk_setPalette(
            background="#2c3e50",
            foreground="#ecf0f1",
            activeBackground="#34495e",
            activeForeground="#ecf0f1",
            highlightBackground="#2c3e50",
            highlightColor="#3498db",
            selectBackground="#3498db",
            selectForeground="#ecf0f1"
        )
        self.window.config(menu=None)

        # Inicialización MCP y configuración
        self.ollama_stop_event = threading.Event()
        self.mcp_manager = MCPManager(lambda msg, tag: None)  # Placeholder logger
        # Inicializar llm_menu_popup para evitar AttributeError
        self.llm_menu_popup = None
        self.config = AppConfig()
        self.llm_model = self.config.get('llm_model') or "llama3"
        self.provider = self.config.get('llm_provider', 'ollama')

        # Selector de backend
        self.provider = "ollama"  # Por defecto
        self.sdk_bridge = MCPSDKBridge()

        # --- Interfaz gráfica ---
        self.menu_frame = ctk.CTkFrame(self.window, height=40)
        self.menu_frame.pack(fill=tk.X, padx=0, pady=0)

        self.btn_mcp = ctk.CTkButton(self.menu_frame, text="MCP", width=80, command=self.toggle_mcp_menu)
        self.btn_llm = ctk.CTkButton(self.menu_frame, text="LLM", width=80, command=self.toggle_llm_menu)
        self.btn_mcp.pack(side=tk.LEFT, padx=(10, 0), pady=5)
        self.btn_llm.pack(side=tk.LEFT, padx=(5, 0), pady=5)

        # Menú de selección de backend
        self.backend_var = ctk.StringVar(value=self.provider)
        self.backend_menu = ctk.CTkOptionMenu(
            self.menu_frame,
            values=["ollama", "openai_compatible", "qwen"],
            command=self.on_backend_change,
            variable=self.backend_var
        )
        self.backend_menu.pack(side=tk.LEFT, padx=5, pady=5)

        # --- Campos dinámicos de configuración ---
        self.fields_frame = ctk.CTkFrame(self.window)
        self.fields_frame.pack(fill=tk.X, padx=10, pady=5)

        # Campo: Modelo LLM
        self.model_label = ctk.CTkLabel(self.fields_frame, text="Modelo:")
        self.model_entry = ctk.CTkEntry(self.fields_frame, width=300)
        self.model_entry.insert(0, self.llm_model)

        # Campo: API Key
        self.api_key_label = ctk.CTkLabel(self.fields_frame, text="API Key:")
        self.api_key_entry = ctk.CTkEntry(self.fields_frame, width=300, show="*")

        # Campo: URL Base
        self.base_url_label = ctk.CTkLabel(self.fields_frame, text="URL Base:")
        self.base_url_entry = ctk.CTkEntry(self.fields_frame, width=300)
        self.base_url_entry.insert(0, "https://api.groq.com/openai/v1")  # Ejemplo

        # Posicionar los campos inicialmente
        self.model_label.pack(pady=2)
        self.model_entry.pack(pady=2)

        # Ocultar los campos no necesarios por defecto
        if self.provider != "ollama":
            self.api_key_label.pack(pady=2)
            self.api_key_entry.pack(pady=2)
            if self.provider == "openai_compatible":
                self.base_url_label.pack(pady=2)
                self.base_url_entry.pack(pady=2)

        # --- Área de chat ---
        self.chat_frame = ctk.CTkFrame(self.window)
        self.chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        self.chat_text = ctk.CTkTextbox(self.chat_frame, wrap=tk.WORD, state="disabled")
        self.chat_text.pack(fill=tk.BOTH, expand=True)

        # --- Entrada de texto ---
        self.input_frame = ctk.CTkFrame(self.window)
        self.input_frame.pack(fill=tk.X, padx=10, pady=5)

        self.input_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Escribe tu mensaje...")
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind("<Return>", lambda e: self.send_message())

        self.send_button = ctk.CTkButton(self.input_frame, text="Enviar", width=80, command=self.send_message)
        self.send_button.pack(side=tk.RIGHT)

        # Inicializar LLM bridge después de crear los widgets para asegurar que chat_text esté disponible
        self.llm_bridge = self._init_llm_bridge()
        self.llm_mcp_handler = LLMMCPHandler(self.mcp_manager, self.sdk_bridge, None, None)

        # --- Estado MCP ---
        self.mcp_status_frame = ctk.CTkFrame(self.window, height=30)
        self.mcp_status_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.mcp_status_icon = ctk.CTkLabel(self.mcp_status_frame, text="⬤", font=("Arial", 20), width=20)
        self.mcp_status_icon.pack(side=tk.LEFT, padx=(10, 5))
        self.mcp_status_label = ctk.CTkLabel(self.mcp_status_frame, text="MCPs: Cargando...", anchor="w", font=("Arial", 12))
        self.mcp_status_label.pack(side=tk.LEFT, padx=5)
        self.mcp_details_btn = ctk.CTkButton(self.mcp_status_frame, text="Detalles", width=60, command=self.show_mcp_details, font=("Arial", 10))
        self.mcp_details_btn.pack(side=tk.RIGHT, padx=10)

        # Eventos
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Estado MCP
        self.mcp_status_frame = ctk.CTkFrame(self.window, height=30)
        self.mcp_status_frame.pack(fill=tk.X, padx=10, pady=(10, 0))
        self.mcp_status_icon = ctk.CTkLabel(self.mcp_status_frame, text="⬤", font=("Arial", 20), width=20)
        self.mcp_status_icon.pack(side=tk.LEFT, padx=(10, 5))
        self.mcp_status_label = ctk.CTkLabel(self.mcp_status_frame, text="MCPs: Cargando...", anchor="w", font=("Arial", 12))
        self.mcp_status_label.pack(side=tk.LEFT, padx=5)
        self.mcp_details_btn = ctk.CTkButton(self.mcp_status_frame, text="Detalles", width=60, command=self.show_mcp_details, font=("Arial", 10))
        self.mcp_details_btn.pack(side=tk.RIGHT, padx=10)

        # Tags de estilo
        self.chat_text.tag_config("user", foreground="#2ecc71")
        self.chat_text.tag_config("assistant", foreground="#3498db")
        self.chat_text.tag_config("loading", foreground="#7f8c8d")
        self.chat_text.tag_config("error", foreground="#e74c3c")
        self.chat_text.tag_config("system", foreground="#f39c12")
        self.chat_text.tag_config("mcp_comm", foreground="#8e44ad")

        # Iniciar MCP
        if self.mcp_manager.load_config():
            self.start_all_mcp_servers_ui(auto_start=True)
        else:
            log_to_chat_on_ui_thread(self.window, self.chat_text, "No se pudo cargar config MCP. Usa menú 'MCP > Cargar...'", "error")

        self.update_mcp_status_label()
        log_to_chat_on_ui_thread(self.window, self.chat_text, f"Bienvenido. LLM: {self.llm_model}. MCPs: {', '.join(self.mcp_manager.get_active_server_names()) or 'Ninguno'}", "system")
        self.window.after(100, self.input_entry.focus_set)

        # Actualizar logger a tiempo real
        self.mcp_manager.logger = lambda msg, tag: log_to_chat_on_ui_thread(self.window, self.chat_text, msg, tag)
        if self.llm_bridge:
            self.llm_bridge.chat_text = self.chat_text
            self.llm_bridge.window = self.window
        if self.llm_mcp_handler:
            self.llm_mcp_handler.window = self.window
            self.llm_mcp_handler.chat_text = self.chat_text
        self.mcp_config_window = None

    def _init_llm_bridge(self):
        """Inicializa o reinicia el LLMBridge según el backend actual."""
        try:
            self.llm_bridge = LLMBridge(self.llm_model, self.chat_text, self.window, provider=self.provider)
        except LLMConnectionError as e:
            log_to_chat_on_ui_thread(self.window, self.chat_text, f"Error al inicializar el modelo: {str(e)}", "error")
            raise

    def hide_api_fields(self):
        self.api_key_label.pack_forget()
        self.api_key_entry.pack_forget()
        self.base_url_label.pack_forget()
        self.base_url_entry.pack_forget()

    def show_api_fields(self):
        self.api_key_label.pack(pady=2)
        self.api_key_entry.pack(pady=2)

    def show_base_url_field(self):
        self.base_url_label.pack(pady=2)
        self.base_url_entry.pack(pady=2)

    def hide_base_url_field(self):
        self.base_url_label.pack_forget()
        self.base_url_entry.pack_forget()

    def on_backend_change(self, selected_backend):
        """Cambia el proveedor de LLM y ajusta los campos visibles"""
        self.provider = selected_backend
        self._init_llm_bridge()
        log_to_chat_on_ui_thread(self.window, self.chat_text, f"Proveedor de LLM cambiado a: {selected_backend}", "system")
        # Mostrar u ocultar campos dinámicos
        if selected_backend == "ollama":
            self.hide_api_fields()
        elif selected_backend == "openai_compatible":
            self.show_api_fields()
            self.show_base_url_field()
        elif selected_backend == "qwen":
            self.show_api_fields()
            self.hide_base_url_field()

    def send_message(self):
        user_input = self.input_entry.get().strip()
        if not user_input or self.assistant_response_active:
            return

        display_message(self.chat_text, user_input, "user", new_line_before_message=True)
        self.input_entry.delete(0, tk.END)
        self.window.update()

        self.assistant_response_active = True
        self.chat_text.configure(state='normal')
        current_content_end = self.chat_text.index('end-1c')
        if current_content_end != '1.0':
            if self.chat_text.get(f"{current_content_end} linestart", current_content_end).strip() != "":
                self.chat_text.insert(tk.END, "\n")
        self.current_assistant_content_start_idx = self.chat_text.index(tk.END)
        self.chat_text.insert(tk.END, "Procesando respuesta...", "loading")
        self.chat_text.insert(tk.END, "\n", "loading")
        self.chat_text.configure(state='disabled')
        self.chat_text.see(tk.END)

        self.ollama_stop_event.clear()
        system_prompt = self.get_base_system_prompt().strip()

        def is_greeting(text):
            greetings = ["hola", "buenas", "buenos días", "buenas tardes", "buenas noches", "qué tal", "saludos"]
            return any(g in text.lower() for g in greetings) and len(text.split()) <= 4

        def clean_llm_response(text):
            lines = text.strip().split("\n")
            for i, line in enumerate(lines):
                if line.strip().endswith("?") and i < len(lines) - 1:
                    return "\n".join(lines[:i + 1])
            return text.strip()

        def on_llm_chunk(content, full_response=None):
            try:
                if content:
                    self._append_to_assistant_message(content)
                elif full_response:
                    if "MCP_COMMAND_JSON:" in full_response:
                        mcp_json = full_response.split("MCP_COMMAND_JSON:", 1)[-1].strip()
                        parsed = self.try_parse_json(mcp_json)
                        if parsed:
                            self.llm_mcp_handler.handle_mcp_command_from_llm(str(parsed), self._on_mcp_result_for_llm)
                        else:
                            self.llm_mcp_handler.handle_mcp_command_from_llm(full_response, self._on_mcp_result_for_llm)
                    else:
                        cleaned = clean_llm_response(full_response.strip())
                        display_message(self.chat_text, cleaned, "assistant", True, False)
                self.assistant_response_active = False
            except Exception as e:
                display_message(self.chat_text, f"Error procesando respuesta LLM: {e}", "error", True, False)
                self.assistant_response_active = False

        # Comprobación de inicialización de llm_bridge
        if not self.llm_bridge:
            display_message(self.chat_text, "App Error: El modelo LLM no está inicializado. Revisa la configuración o vuelve a seleccionar el modelo.", "error", True, False)
            self.assistant_response_active = False
            return

        try:
            self.llm_bridge.process_user_input(user_input, system_prompt, on_llm_chunk)
        except Exception as e:
            display_message(self.chat_text, f"Error al enviar mensaje al LLM: {e}", "error", True, False)
            self.assistant_response_active = False

    def stop_ollama_response(self):
        self.llm_bridge.stop_response()
        log_to_chat_on_ui_thread(self.window, self.chat_text, "Respuesta interrumpida por el usuario.", "system")
        self.assistant_response_active = False

    def change_llm_model_dialog(self):
        new_model = self.prompt_for_llm_model()
        if new_model:
            self.llm_model = new_model
            self.config.set('llm_model', new_model)
            self.config.set('llm_provider', self.provider)
            self._init_llm_bridge()
            log_to_chat_on_ui_thread(self.window, self.chat_text, f"Modelo LLM cambiado a: {new_model}", "system")

    def prompt_for_llm_model(self):
        models = self.get_ollama_models()
        default_model = "smollm2:1.7b" if "smollm2" in models or "smollm2:1.7b" in models else (models[0] if models else "llama3")
        if not models:
            dialog = ctk.CTkInputDialog(
                text="No se detectaron modelos Ollama instalados.\nIngresa el nombre del modelo (ej: llama3, mistral, etc):",
                title="Seleccionar modelo LLM"
            )
            model = dialog.get_input()
            return model.strip() if model and model.strip() else default_model

        var = ctk.StringVar(value=default_model)
        selector = ctk.CTkToplevel(self.window)
        selector.title("Seleccionar modelo LLM (Ollama)")
        selector.geometry("350x180")
        ctk.CTkLabel(selector, text="Selecciona el modelo LLM a usar:").pack(pady=10)
        combo = ctk.CTkComboBox(selector, values=models, variable=var, width=220)
        combo.pack(pady=10)

        def on_ok():
            selector.selected = var.get()
            selector.destroy()

        btn = ctk.CTkButton(selector, text="Seleccionar", command=on_ok)
        btn.pack(pady=10)
        selector.selected = None
        selector.grab_set()
        selector.wait_window()
        return selector.selected or default_model

    def get_ollama_models(self):
        # Solo permitir los modelos válidos definidos
        modelos_validos = ["smollm2:1.7b", "phi3:latest", "mistral:latest"]
        return modelos_validos

    def start_ollama_service(self):
        import subprocess
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if 'ollama' in proc.info['name'].lower():
                    log_to_chat_on_ui_thread(self.window, self.chat_text, "Ollama ya está corriendo.", "system")
                    return
            subprocess.Popen(["ollama", "serve"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log_to_chat_on_ui_thread(self.window, self.chat_text, "Ollama iniciado en segundo plano.", "system")
        except Exception as e:
            log_to_chat_on_ui_thread(self.window, self.chat_text, f"Error al iniciar Ollama: {e}", "error")

    def get_base_system_prompt(self):
        return (
            "Eres un asistente conversacional. Responde solo en español, de forma breve y directa. "
            "En este contexto, MCP significa 'Model Context Protocol', un protocolo para conectar modelos de lenguaje con herramientas externas."
        )

    def on_closing(self):
        self.window.destroy()

    def update_mcp_status_label(self):
        active_servers = self.mcp_manager.get_active_server_names()
        running_servers = [s for s in active_servers if self.mcp_manager.is_server_running(s)]
        total_active = len(active_servers)
        total_running = len(running_servers)
        status_text = f"{total_running}/{total_active} servidores MCP activos." if total_active else "No hay servidores MCP configurados."

        icon_color = "green" if total_running == total_active and total_active > 0 else "gray" if total_active == 0 else "red"
        self.mcp_status_label.configure(text=status_text, text_color=icon_color)
        self.mcp_status_icon.configure(text_color=icon_color)
        self.window.after(5000, self.update_mcp_status_label)

    def show_mcp_details(self):
        details_window = ctk.CTkToplevel(self.window)
        details_window.title("Detalles Técnicos de Servidores MCP")
        details_window.geometry("600x400")
        main_frame = ctk.CTkFrame(details_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(main_frame, text="Detalles técnicos de servidores MCP", font=("Arial", 16, "bold")).pack(pady=5)
        details_text = ctk.CTkTextbox(main_frame, wrap=tk.WORD, state='disabled')
        details_text.pack(fill="both", expand=True, padx=5, pady=5)
        info = ""
        for server_name, config in self.mcp_manager.servers_config.get("mcpServers", {}).items():
            info += f"=== {server_name} ===\n"
            info += f"Habilitado: {config.get('enabled', True)}\n"
            info += f"Comando: {config.get('command')}\n"
            info += f"Argumentos: {', '.join(config.get('args', []))}\n"
            info += f"Puerto: {config.get('port')}\n"
            info += f"Ruta: {config.get('path', 'No especificada')}\n"
            is_running = self.mcp_manager.is_server_running(server_name)
            info += f"Estado: {'Activo' if is_running else 'Inactivo'}\n"
            if is_running:
                process = self.mcp_manager.active_processes.get(server_name)
                if process:
                    try:
                        import psutil
                        if process and psutil.pid_exists(process.pid):
                            p = psutil.Process(process.pid)
                            info += f"PID: {process.pid}\n"
                            info += f"Memoria usada: {p.memory_info().rss / 1024:.2f} KB\n"
                            info += f"Tiempo de ejecución: {time.time() - p.create_time():.2f} segundos\n"
                        else:
                            info += "    (No se pudo obtener info de memoria/tiempo)\n"
                    except Exception:
                        info += "    (No se pudo obtener info de memoria/tiempo)\n"
            info += "-" * 50 + "\n"

        details_text.configure(state='normal')
        details_text.insert(tk.END, info)
        details_text.configure(state='disabled')

    def load_mcp_config_dialog(self):
        filepath = filedialog.askopenfilename(title="Seleccionar mcp_servers.json", filetypes=(("JSON", "*.json"), ("Todos", "*.*")))
        if filepath:
            self.mcp_manager.stop_all_servers()
            if self.mcp_manager.load_config(filepath):
                log_to_chat_on_ui_thread(self.window, self.chat_text, f"Nueva config MCP cargada: {filepath}", "system")
                self.start_all_mcp_servers_ui(auto_start=True)
            else:
                messagebox.showerror("Error", f"No se pudo cargar la configuración desde {filepath}")
                log_to_chat_on_ui_thread(self.window, self.chat_text, f"Error al cargar MCP desde {filepath}", "error")
        self.update_mcp_status_label()

    def start_all_mcp_servers_ui(self, auto_start=False):
        server_configs = self.mcp_manager.servers_config.get("mcpServers", {})
        if not server_configs:
            log_to_chat_on_ui_thread(self.window, self.chat_text, "No hay MCPs configurados.", "system")
            return

        any_started = False
        for name, cfg in server_configs.items():
            if cfg.get("enabled", True) and not self.mcp_manager.is_server_running(name):
                if self.mcp_manager.start_server(name):
                    any_started = True

        if any_started:
            log_to_chat_on_ui_thread(self.window, self.chat_text, "Servidores MCP habilitados iniciados.", "system")
        elif not auto_start:
            log_to_chat_on_ui_thread(self.window, self.chat_text, "No se iniciaron nuevos MCPs.", "system")
        self.update_mcp_status_label()

    def try_parse_json(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                return strictjson.loads(text)
            except Exception:
                return None

    def _on_mcp_result_for_llm(self, mcp_result):
        if mcp_result is not None:
            display_message(self.chat_text, str(mcp_result), "assistant", True, False)
        else:
            display_message(self.chat_text, "No se obtuvo respuesta del servidor MCP.", "error", True, False)

    def _append_to_assistant_message(self, text_chunk):
        if not self.window.winfo_exists() or not self.chat_text.winfo_exists():
            return
        display_message(self.chat_text, text_chunk, "assistant_content", False, True)

    def toggle_mcp_menu(self):
        # Evita abrir múltiples menús
        if self.mcp_menu_popup and self.mcp_menu_popup.winfo_exists():
            self.mcp_menu_popup.focus()
            return
        self.mcp_menu_popup = ctk.CTkToplevel(self.window)
        self.mcp_menu_popup.title("Opciones MCP")
        self.mcp_menu_popup.geometry("200x180")
        self.mcp_menu_popup.transient(self.window)
        self.mcp_menu_popup.grab_set()
        btn_frame = ctk.CTkFrame(self.mcp_menu_popup)
        btn_frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        ctk.CTkButton(btn_frame, text="Cargar Configuración", command=self.load_mcp_config_dialog).pack(pady=5)
        ctk.CTkButton(btn_frame, text="Guardar Configuración", command=lambda: self.mcp_manager.save_config()).pack(pady=5)
        ctk.CTkButton(btn_frame, text="Configurar Servidores", command=self.show_mcp_config_window).pack(pady=5)
        ctk.CTkButton(btn_frame, text="Cerrar", command=self.mcp_menu_popup.destroy).pack(pady=5)
        self.mcp_menu_popup.protocol("WM_DELETE_WINDOW", lambda: self.mcp_menu_popup.destroy())
        # self.mcp_menu_popup.bind("<FocusOut>", lambda e: self.mcp_menu_popup.destroy())  # Eliminado para evitar cierre inmediato

    def toggle_llm_menu(self):
        # Evita abrir múltiples menús
        if hasattr(self, 'llm_menu_popup') and self.llm_menu_popup and self.llm_menu_popup.winfo_exists():
            self.llm_menu_popup.focus()
            return
        self.llm_menu_popup = ctk.CTkToplevel(self.window)
        self.llm_menu_popup.title("Opciones LLM")
        self.llm_menu_popup.geometry("300x200")
        frame = ctk.CTkFrame(self.llm_menu_popup)
        frame.pack(fill=ctk.BOTH, expand=True, padx=10, pady=10)
        ctk.CTkButton(frame, text="Cambiar modelo LLM", command=self.change_llm_model_dialog).pack(pady=5)
        ctk.CTkButton(frame, text="Guardar configuración", command=self.config.save_config).pack(pady=5)
        ctk.CTkButton(frame, text="Cerrar", command=self.llm_menu_popup.destroy).pack(pady=5)

    def show_mcp_config_window(self):
        # Abre la ventana de configuración MCP
        window = MCPConfigWindow(self.window, self.mcp_manager)
        window.grab_set()  # Hace modal la ventana
