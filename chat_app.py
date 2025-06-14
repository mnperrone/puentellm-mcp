import tkinter as tk
import customtkinter as ctk
import threading
import json
from tkinter import filedialog, messagebox, ttk
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
    def init_llm(self):
        """Inicializa el puente LLM según el proveedor configurado"""
        try:
            if self.provider == "ollama":
                from llm_bridge import LLMBridge
                self.llm_bridge = LLMBridge(
                    model=self.llm_model,
                    chat_text=self.chat_display,
                    window=self.window,
                    provider=self.provider
                )
                # Configurar el callback para manejar las respuestas del LLM
                self.llm_bridge.set_response_callback(self._handle_llm_response)
                
                self.llm_handler = LLMMCPHandler(
                    mcp_manager=self.mcp_manager,
                    sdk_bridge=self.sdk_bridge,
                    window=self.window,
                    chat_text=self.chat_display
                )
                
                # Inicializar el estado de procesamiento
                self.processing_message_id = None
                self.assistant_response_active = False
                
                return True
            else:
                raise ValueError(f"Proveedor no soportado: {self.provider}")
        except Exception as e:
            error_msg = f"Error al inicializar el LLM: {str(e)}"
            self.log_message(error_msg, "error")
            messagebox.showerror("Error de inicialización", error_msg)
            return False
            
    def __init__(self):
        # Inicialización de atributos para evitar errores
        self.mcp_menu_popup = None
        self.assistant_response_active = False
        self.llm_running = False
        self.dark_mode = False
        self.llm_bridge = None  # Se inicializará en init_llm
        self.llm_handler = None  # Se inicializará en init_llm
        
        # Inicializar ventana principal
        self.window = ctk.CTk()
        self.window.title("LLM - MCP Bridge Chat")
        
        # Obtener dimensiones de la pantalla
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        
        # Establecer tamaño de ventana (80% del ancho y 80% del alto de la pantalla)
        width = int(screen_width * 0.8)
        height = int(screen_height * 0.8)
        
        # Posicionar la ventana en el centro
        x = (screen_width // 2) - (width // 2)
        y = (screen_height // 2) - (height // 2)
        
        self.window.geometry(f"{width}x{height}+{x}+{y}")
        self.window.minsize(800, 600)  # Tamaño mínimo para mantener usabilidad
        self.window.resizable(True, True)
        
        # Cargar icono
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

        # Inicialización MCP y configuración
        self.ollama_stop_event = threading.Event()
        self.mcp_manager = MCPManager(lambda msg, tag: self.log_message(msg, tag))
        self.llm_menu_popup = None
        self.config = AppConfig()
        self.llm_model = self.config.get('llm_model') or "llama3:latest"
        self.provider = self.config.get('llm_provider', 'ollama')
        self.sdk_bridge = MCPSDKBridge()
        
        # Configuración de tema
        self.setup_theme()
        
        # Crear interfaz de usuario
        self.setup_ui()
        
        # Inicializar LLM
        self.init_llm()
        
        # Cargar configuración
        self.load_config()
    
    def setup_theme(self):
        """Configura el tema claro/oscuro de la aplicación"""
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        ctk.set_default_color_theme("blue")
    
    def toggle_theme(self):
        """Alterna entre modo claro y oscuro"""
        self.dark_mode = not self.dark_mode
        ctk.set_appearance_mode("dark" if self.dark_mode else "light")
        self.theme_toggle.configure(text="☀️ Modo claro" if self.dark_mode else "🌙 Modo oscuro")
    
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Configurar el grid
        self.window.grid_columnconfigure(0, weight=1)
        self.window.grid_rowconfigure(1, weight=1)
        
        # Crear la barra superior
        self.create_top_bar()
        
        # Crear el diseño principal
        self.create_main_layout()
    
    def create_top_bar(self):
        """Crea la barra superior con controles de LLM"""
        top_frame = ctk.CTkFrame(self.window, height=50, corner_radius=0)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        top_frame.grid_columnconfigure(1, weight=1)  # Para que el estado MCP empuje los controles a la izquierda
        
        # Selector de modelo LLM
        ctk.CTkLabel(top_frame, text="🧠 Modelo LLM:").pack(side=tk.LEFT, padx=(10, 5), pady=10)
        
        self.llm_combo = ctk.CTkComboBox(
            top_frame,
            values=["llama3:latest", "smollm2:1.7b", "phi3:latest", "mistral:latest"],
            width=200
        )
        self.llm_combo.set(self.llm_model)
        self.llm_combo.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Botón de control LLM
        self.llm_control_button = ctk.CTkButton(
            top_frame,
            text="▶️ Iniciar LLM",
            command=self.toggle_llm,
            width=120
        )
        self.llm_control_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Botón de configuración LLM remoto
        self.remote_llm_button = ctk.CTkButton(
            top_frame,
            text="⚙️ Configurar LLM remoto",
            command=self.open_remote_llm_config,
            width=180
        )
        self.remote_llm_button.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Selector de proveedor
        self.provider_combo = ctk.CTkComboBox(
            top_frame,
            values=["ollama", "openai_compatible", "qwen"],
            command=self.on_backend_change,
            width=150
        )
        self.provider_combo.set(self.provider)
        self.provider_combo.pack(side=tk.LEFT, padx=5, pady=10)
        
        # Botón de tema
        # Botón de tema
        self.theme_toggle = ctk.CTkButton(
            top_frame,
            text="🌙 Modo oscuro",
            command=self.toggle_theme,
            width=120
        )
        self.theme_toggle.pack(side=tk.RIGHT, padx=10, pady=10)
        
        # Estado de MCP
        mcp_status_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        mcp_status_frame.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Icono de estado MCP
        self.mcp_status_icon = ctk.CTkLabel(
            mcp_status_frame,
            text="🔄",
            font=("Segoe UI", 14)
        )
        self.mcp_status_icon.pack(side=tk.LEFT, padx=(10, 0))
        
        # Etiqueta de estado MCP
        self.mcp_status_label = ctk.CTkLabel(
            mcp_status_frame,
            text="MCP: Cargando...",
            font=("Segoe UI", 12)
        )
        self.mcp_status_label.pack(side=tk.LEFT, padx=5)
        
        # Iniciar actualización periódica del estado
        self.update_mcp_status_label()
    
    def create_main_layout(self):
        """Crea el diseño principal de la aplicación"""
        main_frame = ctk.CTkFrame(self.window)
        main_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        main_frame.grid_columnconfigure(0, weight=3)
        main_frame.grid_columnconfigure(1, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)
        
        # Marco izquierdo (chat)
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        left_frame.grid_columnconfigure(0, weight=1)
        left_frame.grid_rowconfigure(0, weight=1)  # Hace que el área de chat ocupe todo el espacio disponible
        left_frame.grid_rowconfigure(1, weight=0)  # Hace que el área de entrada ocupe solo el espacio necesario
        
        # Configurar el área de chat - Marco contenedor con borde
        chat_container = ctk.CTkFrame(left_frame, corner_radius=5)
        chat_container.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
        chat_container.grid_columnconfigure(0, weight=1)
        chat_container.grid_rowconfigure(0, weight=1)
        
        # Área de visualización del chat
        self.chat_display = ctk.CTkTextbox(
            chat_container,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            height=10,  # Altura inicial, se expandirá
            fg_color=("#f0f0f0", "#1a1a1a"),  # Fondo claro/oscuro según tema
            text_color=("#000000", "#ffffff"),  # Texto oscuro en modo claro, claro en modo oscuro
            border_width=1,
            border_color=("#c4c4c4", "#4a4a4a"),
            corner_radius=5
        )
        self.chat_display.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        
        # Barra de desplazamiento vertical
        scrollbar = ctk.CTkScrollbar(chat_container, command=self.chat_display.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.chat_display.configure(yscrollcommand=scrollbar.set)
        
        # Área de entrada de mensajes
        input_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        input_frame.grid(row=1, column=0, sticky="ew", pady=(0, 5))
        input_frame.grid_columnconfigure(0, weight=1)
        input_frame.grid_rowconfigure(0, weight=0)
        
        # Campo de entrada con borde redondeado
        self.input_entry = ctk.CTkEntry(
            input_frame, 
            placeholder_text="Escribe tu mensaje aquí...",
            corner_radius=15,
            border_width=1,
            border_color=("#c4c4c4", "#4a4a4a"),
            height=40
        )
        self.input_entry.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        self.input_entry.bind("<Return>", lambda e: self.send_message())
        
        # Botón de enviar con estilo mejorado
        self.send_button = ctk.CTkButton(
            input_frame,
            text="Enviar",
            command=self.send_message,
            width=100,
            height=40,
            corner_radius=15,
            fg_color=("#4a90e2", "#2a5d9e"),
            hover_color=("#3a7bc8", "#1e4b7b")
        )
        self.send_button.grid(row=0, column=1, sticky="ew")
        
        # Marco derecho (logs y estado)
        right_frame = ctk.CTkFrame(main_frame)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.grid_columnconfigure(0, weight=1)
        right_frame.grid_rowconfigure(1, weight=1)
        
        # Pestañas para logs y estado
        self.tabview = ctk.CTkTabview(right_frame)
        self.tabview.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Pestaña de logs
        self.logs_tab = self.tabview.add("📝 Logs")
        self.log_display = ctk.CTkTextbox(
            self.logs_tab,
            wrap=tk.WORD,
            font=("Consolas", 10),
            state=tk.DISABLED
        )
        self.log_display.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        # Pestaña de estado MCP
        self.mcp_tab = self.tabview.add("🔌 MCP")
        
        # Lista de servidores MCP
        mcp_frame = ctk.CTkFrame(self.mcp_tab)
        mcp_frame.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        
        ctk.CTkLabel(
            mcp_frame,
            text="🟢 Servidores MCP activos:",
            font=("Segoe UI", 12, "bold")
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.mcp_status_list = ctk.CTkTextbox(
            mcp_frame,
            wrap=tk.WORD,
            font=("Consolas", 10),
            height=100,
            state=tk.DISABLED
        )
        self.mcp_status_list.pack(expand=True, fill=tk.BOTH, pady=(0, 5))
        
        self.add_server_button = ctk.CTkButton(
            mcp_frame,
            text="➕ Agregar servidor MCP",
            command=self.show_mcp_config
        )
        self.add_server_button.pack(fill=tk.X, pady=5)

    def log_message(self, message, tag=None):
        """Muestra un mensaje en el área de logs"""
        self.log_display.configure(state=tk.NORMAL)
        self.log_display.insert(tk.END, f"{message}\n", tag)
        self.log_display.see(tk.END)
        self.log_display.configure(state=tk.DISABLED)
    
    def update_mcp_status(self):
        """Actualiza la lista de servidores MCP activos"""
        self.mcp_status_list.configure(state=tk.NORMAL)
        self.mcp_status_list.delete(1.0, tk.END)
        
        # Obtener información de los servidores MCP
        servers = self.mcp_manager.get_servers()
        for name, server in servers.items():
            status = "🟢" if server.get("active", False) else "🔴"
            self.mcp_status_list.insert(tk.END, f"{status} {name}\n")
        
        self.mcp_status_list.configure(state=tk.DISABLED)
    
    def toggle_llm(self):
        """Inicia o detiene el modelo LLM"""
        if not self.llm_running:
            self.start_llm()
        else:
            self.stop_llm()
    
    def check_ollama_service(self):
        """Verifica si el servicio Ollama está en ejecución"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except (requests.RequestException, ConnectionError):
            return False

    def _start_ollama_service(self):
        """Inicia el servicio Ollama en segundo plano"""
        try:
            import subprocess
            import sys
            import os
            import time
            
            self.log_message("Iniciando servicio Ollama, por favor espere...", "info")
            
            # Comando para ejecutar Ollama en segundo plano
            if sys.platform == 'win32':
                subprocess.Popen(
                    'start /B /MIN ollama serve',
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            else:
                with open(os.devnull, 'w') as devnull:
                    subprocess.Popen(
                        ['nohup', 'ollama', 'serve'],
                        stdout=devnull,
                        stderr=devnull,
                        start_new_session=True
                    )
            
            # Esperar a que el servicio esté disponible
            max_attempts = 15
            for i in range(max_attempts):
                if self.check_ollama_service():
                    self.log_message("✅ Servicio Ollama iniciado correctamente", "info")
                    return True
                time.sleep(1)
                if i % 5 == 4:  # Actualizar cada 5 segundos
                    self.log_message(f"Esperando que el servicio Ollama esté listo... ({i+1}/{max_attempts})", "info")
            
            return False
            
        except Exception as e:
            self.log_message(f"Error al iniciar Ollama: {str(e)}", "error")
            return False
    
    def _check_ollama_model(self, model):
        """Verifica si el modelo de Ollama está disponible"""
        try:
            models = self.llm_bridge.list_models()
            
            if not models:
                self.log_message("No se encontraron modelos instalados en Ollama", "warning")
                return False
                
            # Verificar el tipo de datos devuelto por list_models()
            first_item = models[0] if models else None
            
            # Manejar diferentes formatos de respuesta
            if isinstance(first_item, str):
                # Formato de lista simple de strings
                model_found = any(m.strip().startswith(model) for m in models)
            elif isinstance(first_item, dict):
                # Formato de lista de diccionarios
                model_found = any(
                    str(m.get('name', '')).strip().startswith(model) or 
                    str(m.get('model', '')).strip().startswith(model)
                    for m in models
                )
            else:
                self.log_message(f"Formato de modelos no reconocido: {type(first_item)}", "error")
                return False
            
            if not model_found:
                if messagebox.askyesno(
                    "Modelo no encontrado",
                    f"El modelo '{model}' no está instalado. ¿Deseas descargarlo ahora?\n\n"
                    "Nota: La descarga puede tardar varios minutos dependiendo de tu conexión a internet."
                ):
                    self.log_message(f"Iniciando descarga del modelo '{model}'...", "info")
                    self.llm_bridge.pull_model(model)
                    self.log_message(f"✅ Modelo descargado correctamente", "success")
                    return True
                return False
                
            return True
            
        except Exception as e:
            error_msg = f"Error al verificar el modelo: {str(e)}"
            self.log_message(error_msg, "error")
            return False
    
    def start_llm(self):
        """Inicia el modelo LLM seleccionado"""
        model = self.llm_combo.get()
        if not model:
            messagebox.showerror("Error", "Por favor selecciona un modelo LLM")
            return False
            
        if self.llm_running:
            self.log_message("El modelo LLM ya está en ejecución", "info")
            return True
            
        try:
            # Verificar servicio Ollama si es el proveedor seleccionado
            if self.provider == "ollama":
                if not self.check_ollama_service():
                    if not messagebox.askyesno(
                        "Servicio Ollama no encontrado",
                        "El servicio Ollama no está en ejecución. ¿Deseas intentar iniciarlo automáticamente?\n\n"
                        "Nota: Esta operación puede tardar unos segundos."
                    ):
                        return False
                    
                    self.log_message("Iniciando servicio Ollama...", "info")
                    if not self._start_ollama_service():
                        raise Exception("No se pudo iniciar el servicio Ollama. Por favor, verifica que Ollama esté instalado y configurado correctamente.")
            
            # Inicializar el puente LLM
            self.log_message(f"Inicializando modelo {model}...", "info")
            if not self.init_llm():
                raise Exception("No se pudo inicializar el modelo. Verifica la configuración y la conexión.")
            
            # Verificar si el modelo está disponible
            if self.provider == "ollama":
                self.log_message(f"Verificando disponibilidad del modelo {model}...", "info")
                if not self._check_ollama_model(model):
                    return False
            
            # Marcar como en ejecución
            self.llm_running = True
            
            # Actualizar la interfaz
            if hasattr(self, 'llm_control_button'):
                self.llm_control_button.configure(text="⏹️ Detener LLM")
            
            # Actualizar la configuración
            self.config.set('llm_model', model)
            self.config.set('llm_provider', self.provider)
            self.config.save_config()
            
            self.log_message(f"✅ Modelo {model} listo para usar", "success")
            return True
            
        except Exception as e:
            self.llm_running = False
            
            # Restaurar el botón de control
            if hasattr(self, 'llm_control_button'):
                self.llm_control_button.configure(text="▶️ Iniciar LLM")
            
            # Mostrar mensaje de error al usuario
            error_msg = f"No se pudo iniciar el modelo: {str(e)}"
            self.log_message(f"❌ {error_msg}", "error")
            messagebox.showerror("Error al iniciar el modelo", error_msg)
            return False
    
    def stop_llm(self):
        """Detiene el modelo LLM actual"""
        try:
            if not self.llm_running:
                self.log_message("El modelo ya está detenido", "info")
                return True
                
            self.log_message("Deteniendo el modelo, por favor espera...", "info")
            
            # Actualizar el estado primero para evitar nuevas solicitudes
            was_running = self.llm_running
            self.llm_running = False
            
            # Limpiar recursos del puente LLM
            if self.llm_bridge:
                try:
                    self.llm_bridge.stop()
                    self.log_message("Recursos del modelo liberados", "info")
                except Exception as e:
                    self.log_message(f"Advertencia al liberar recursos: {str(e)}", "warning")
                finally:
                    self.llm_bridge = None
            
            # Limpiar el manejador
            self.llm_handler = None
            
            # Actualizar la interfaz
            if hasattr(self, 'llm_control_button'):
                self.llm_control_button.configure(text="▶️ Iniciar LLM")
            
            self.log_message("✅ Modelo detenido correctamente", "success")
            return True
            
        except Exception as e:
            # Restaurar el estado si ocurrió un error
            self.llm_running = was_running if 'was_running' in locals() else False
            
            error_msg = f"No se pudo detener el modelo correctamente: {str(e)}"
            self.log_message(f"❌ {error_msg}", "error")
            messagebox.showerror("Error al detener el modelo", error_msg)
            
            # Intentar restaurar la interfaz
            if hasattr(self, 'llm_control_button'):
                self.llm_control_button.configure(text="⏹️ Detener LLM")
                
            return False
    
    def send_message(self):
        """Envía un mensaje al chat"""
        message = self.input_entry.get().strip()
        if not message:
            return
        
        # Clear the input field first
        self.input_entry.delete(0, tk.END)
        
        # Mostrar el mensaje del usuario
        self.display_message(message, "user")
        
        # Procesar la respuesta con el LLM
        self.process_user_message(message)
    
    def display_message(self, message, sender="assistant"):
        """Muestra un mensaje en el área de chat con formato según el remitente"""
        try:
            self.chat_display.configure(state=tk.NORMAL)
            
            # Configurar formato según el remitente
            if sender == "user":
                prefix = "Tú: "
                tag = "user_message"
            elif sender == "error":
                prefix = "Error: "
                tag = "error_message"
            else:  # assistant
                prefix = "Asistente: "
                tag = "assistant_message"
            
            # Configurar los tags si no existen
            if not hasattr(self, 'tags_configured'):
                self.chat_display.tag_configure("bold", font=("Segoe UI", 11, "bold"))
                self.chat_display.tag_configure("user_message", foreground="#2b2b2b")
                self.chat_display.tag_configure("assistant_message", foreground="#1a5fb4")
                self.chat_display.tag_configure("error_message", foreground="#ff4444")
                self.tags_configured = True
            
            # Insertar el mensaje con el prefijo apropiado
            self.chat_display.insert("end", f"{prefix}", ("bold", tag))
            self.chat_display.insert("end", f"{message}\n\n", tag)
            
            # Desplazarse al final y deshabilitar edición
            self.chat_display.see("end")
            self.chat_display.configure(state=tk.DISABLED)
            
        except Exception as e:
            # Si falla el formato, mostrar el mensaje sin formato
            try:
                self.chat_display.configure(state=tk.NORMAL)
                self.chat_display.insert("end", f"{prefix}{message}\n\n")
                self.chat_display.see("end")
                self.chat_display.configure(state=tk.DISABLED)
            except Exception as e2:
                print(f"Error al mostrar mensaje de error: {e2}")

    def process_user_message(self, message):
        """Procesa el mensaje del usuario y genera una respuesta"""
        try:
            if not self.llm_running:
                self.display_message("El modelo LLM no está en ejecución. Por favor inicia el modelo primero.", "error")
                return
            
            # Mostrar mensaje de "procesando"
            self.chat_display.configure(state=tk.NORMAL)
            start_pos = self.chat_display.index("end-1c")  # Guardar posición antes de insertar
            self.chat_display.insert(tk.END, "Procesando tu mensaje...\n\n", "assistant")
            end_pos = self.chat_display.index("end-1c")    # Guardar posición después de insertar
            self.chat_display.see(tk.END)
            self.chat_display.configure(state=tk.DISABLED)
            
            # Guardar las posiciones del mensaje de procesamiento
            self.processing_message_start = start_pos
            self.processing_message_end = end_pos
            self.assistant_response_active = True
            
            # Obtener la respuesta del LLM
            self.get_llm_response(message)
            
        except Exception as e:
            error_msg = f"Error al procesar el mensaje: {str(e)}"
            self.log_message(error_msg, "error")
            self.display_message(error_msg, "error")

    def get_llm_response(self, message):
        """Obtiene una respuesta del modelo LLM"""
        if not self.llm_running or self.llm_bridge is None:
            self.display_message("Error: El modelo LLM no está listo para responder.", "error")
            return
            
        try:
            # Iniciar la generación de la respuesta en un hilo separado
            threading.Thread(
                target=self.llm_bridge.generate_response,
                args=(message,),
                daemon=True
            ).start()
            
        except Exception as e:
            error_msg = f"Error al obtener respuesta del LLM: {str(e)}"
            self.log_message(error_msg, "error")
            self.display_message("Lo siento, ocurrió un error al procesar tu mensaje.", "error")

    def _handle_llm_response(self, response_text):
        """Maneja la respuesta del LLM y la muestra en el chat"""
        try:
            # Asegurarse de que estamos en el hilo de la interfaz de usuario
            if not self.window.winfo_exists():
                return
            
            # Programar la actualización de la interfaz en el hilo principal
            self.window.after(0, self._process_llm_response, response_text)
                
        except Exception as e:
            error_msg = f"Error al procesar la respuesta del LLM: {str(e)}"
            self.log_message(error_msg, "error")
            self.window.after(0, self.display_message, "Lo siento, ocurrió un error al procesar la respuesta.", "error")
    
    def _process_llm_response(self, response_text):
        """Procesa la respuesta del LLM en el hilo de la interfaz de usuario"""
        try:
            # Eliminar el mensaje de "procesando" si existe
            if hasattr(self, 'processing_message_start') and hasattr(self, 'processing_message_end'):
                self.chat_display.configure(state=tk.NORMAL)
                # Eliminar el mensaje de procesando usando las posiciones guardadas
                self.chat_display.delete(self.processing_message_start, self.processing_message_end)
                self.chat_display.see("end")
                self.chat_display.configure(state=tk.DISABLED)
                # Limpiar las variables de seguimiento
                delattr(self, 'processing_message_start')
                delattr(self, 'processing_message_end')
            
            # Marcar que ya no hay una respuesta en proceso
            self.assistant_response_active = False
            
            # Verificar si la respuesta es un error
            if not response_text or response_text.startswith("Error:"):
                if not response_text:
                    response_text = "Error: No se recibió respuesta del modelo"
                self.display_message(response_text, "error")
                return
                
            # Verificar si la respuesta contiene un comando MCP
            if response_text.strip().startswith("MCP_COMMAND_JSON:"):
                if self.llm_handler:
                    self.llm_handler.handle_mcp_command_from_llm(
                        response_text,
                        self._handle_mcp_command_response
                    )
            else:
                # Mostrar la respuesta normal del asistente
                self.chat_display.configure(state=tk.NORMAL)
                # Insertar la respuesta del asistente
                self.chat_display.insert("end", "Asistente: ", ("assistant_message", "bold"))
                self.chat_display.insert("end", f"{response_text}\n\n", "assistant_message")
                self.chat_display.see("end")
                self.chat_display.configure(state=tk.DISABLED)
                
            # Asegurarse de que el chat se desplace hacia abajo
            self.chat_display.see("end")
                
        except Exception as e:
            error_msg = f"Error al procesar la respuesta del LLM: {str(e)}"
            self.log_message(error_msg, "error")
            self.display_message("Lo siento, ocurrió un error al procesar la respuesta.", "error")
            error_msg = f"Error al procesar la respuesta del LLM: {str(e)}"
            self.log_message(error_msg, "error")
            self.display_message("Lo siento, ocurrió un error al procesar la respuesta.", "error")
    
    def _handle_mcp_command_response(self, success, response, error=None):
        """Maneja la respuesta de un comando MCP"""
        if success:
            self.display_message(f"Comando MCP ejecutado con éxito: {response}", "info")
        else:
            error_msg = f"Error al ejecutar comando MCP: {error}"
            self.display_message(error_msg, "error")
            self.log_message(error_msg, "error")
    
    def open_remote_llm_config(self):
        """Abre el diálogo de configuración de LLM remoto"""
        dialog = ctk.CTkToplevel(self.window)
        dialog.title("⚙️ Configurar LLM remoto")
        dialog.geometry("500x300")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Configuración de la API
        ctk.CTkLabel(dialog, text="🔑 API Key:").pack(pady=(10, 0), padx=10, anchor=tk.W)
        api_key_entry = ctk.CTkEntry(dialog, width=400, show="*")
        api_key_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # URL del endpoint
        ctk.CTkLabel(dialog, text="🌐 URL del endpoint:").pack(pady=(5, 0), padx=10, anchor=tk.W)
        endpoint_entry = ctk.CTkEntry(dialog, width=400)
        endpoint_entry.pack(padx=10, pady=(0, 10), fill=tk.X)
        
        # Botones
        button_frame = ctk.CTkFrame(dialog)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        def save_config():
            # Aquí iría la lógica para guardar la configuración
            api_key = api_key_entry.get()
            endpoint = endpoint_entry.get()
            self.log_message(f"Configuración de LLM remoto guardada - Endpoint: {endpoint}", "info")
            dialog.destroy()
        
        ctk.CTkButton(
            button_frame,
            text="💾 Guardar",
            command=save_config
        ).pack(side=tk.RIGHT, padx=5)
        
        ctk.CTkButton(
            button_frame,
            text="❌ Cancelar",
            command=dialog.destroy
        ).pack(side=tk.RIGHT, padx=5)
    
    def show_mcp_config(self):
        """Muestra la ventana de configuración de MCP"""
        MCPConfigWindow(self.window, self.mcp_manager, self)
    
    def on_backend_change(self, choice):
        """Se ejecuta cuando se cambia el proveedor de LLM"""
        self.provider = choice
        self.config.set('llm_provider', choice)
        self.config.save_config()
        self.log_message(f"Proveedor cambiado a: {choice}", "info")
    
    def load_config(self):
        """Carga la configuración guardada"""
        try:
            # Cargar configuración del modelo
            model = self.config.get('llm_model')
            if model:
                self.llm_combo.set(model)
            
            # Cargar configuración del proveedor
            provider = self.config.get('llm_provider')
            if provider:
                self.provider_combo.set(provider)
            
            self.log_message("Configuración cargada correctamente", "info")
            
        except Exception as e:
            self.log_message(f"Error al cargar la configuración: {str(e)}", "error")
    
    def update_mcp_status_label(self):
        """Actualiza la etiqueta de estado de los servidores MCP"""
        try:
            active_servers = self.mcp_manager.get_active_server_names()
            running_servers = [s for s in active_servers if self.mcp_manager.is_server_running(s)]
            total_active = len(active_servers)
            total_running = len(running_servers)
            
            if total_active > 0:
                status_text = f"MCP: {total_running}/{total_active} servidores activos"
                icon_color = "green" if total_running == total_active else "orange"
            else:
                status_text = "MCP: No hay servidores configurados"
                icon_color = "gray"
                
            if hasattr(self, 'mcp_status_label') and hasattr(self, 'mcp_status_icon'):
                self.mcp_status_label.configure(text=status_text, text_color=icon_color)
                self.mcp_status_icon.configure(text_color=icon_color)
            
            # Programar próxima actualización
            self.window.after(5000, self.update_mcp_status_label)
            
        except Exception as e:
            self.log_message(f"Error actualizando estado MCP: {str(e)}", "error")
            # Reintentar después de un tiempo incluso si hay error
            self.window.after(10000, self.update_mcp_status_label)
    
    def on_closing(self):
        """Maneja el cierre de la aplicación"""
        try:
            if self.llm_running:
                self.stop_llm()
            
            # Guardar configuración
            self.config.set('llm_model', self.llm_combo.get())
            self.config.set('llm_provider', self.provider_combo.get())
            self.config.save_config()
            
            # Cancelar la actualización periódica del estado MCP
            if hasattr(self, 'mcp_status_after_id'):
                self.window.after_cancel(self.mcp_status_after_id)
            
            self.window.quit()
            self.window.destroy()
            
        except Exception as e:
            print(f"Error al cerrar la aplicación: {str(e)}")
            self.window.quit()
            self.window.destroy()


if __name__ == "__main__":
    app = ChatApp()
    app.window.mainloop()
