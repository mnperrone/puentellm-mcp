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
from ui_helpers import display_message, log_to_chat_on_ui_thread, show_error_with_details
import traceback
from llm_bridge import LLMBridge
from llm_mcp_handler import LLMMCPHandler
from app_config import AppConfig
import strictjson
from mcp_config_window import MCPConfigWindow
from llm_config_window import LLMConfigWindow
from llm_providers.llm_exception import LLMConnectionError


class ChatApp:
    def init_llm(self):
        """Inicializa el puente LLM según el proveedor configurado"""
        print("\n=== Starting LLM Initialization ===")
        try:
            # Cargar configuración
            print("Loading configuration...")
            self.provider = self.config.get('llm_provider', 'ollama')
            # No sobrescribimos self.llm_model aquí porque ya fue configurado en __init__
            
            # Log the attempt
            print(f"Attempting to initialize LLM with provider: {self.provider}, model: {self.llm_model}")
            
            # Cargar configuración específica del proveedor
            print("Loading provider configuration...")
            provider_configs = self.config.get('llm_provider_configs', {})
            provider_config = provider_configs.get(self.provider, {})
            print(f"Provider config found: {bool(provider_config)}")
            
            # Obtener credenciales específicas del proveedor
            print("Getting provider credentials...")
            api_key = provider_config.get('api_key') or self.config.get(f'{self.provider}_api_key')
            base_url = provider_config.get('base_url') or self.config.get(f'{self.provider}_base_url')
            print(f"API key found: {bool(api_key)}")
            print(f"Base URL found: {bool(base_url)}")
            
            # Inicializar el manejador de LLM según el proveedor
            if self.provider == "ollama":
                from llm_bridge import LLMBridge
                print(f"Creating LLM Bridge with model={self.llm_model}, provider={self.provider}")
                self.llm_bridge = LLMBridge(
                    model=self.llm_model,
                    chat_text=self.chat_display,
                    window=self.window,
                    provider=self.provider
                )
                
                # Si hay un modelo configurado, verificar si está disponible
                if self.llm_model and not self._check_ollama_model(self.llm_model):
                    self.llm_model = 'llama3'  # Modelo predeterminado
                    self.config.set('llm_model', self.llm_model)
                    self.config.save_config()
                
                print("LLM initialization completed successfully")
                
                # Configurar el callback para manejar las respuestas del LLM
                self.llm_bridge.set_response_callback(self._handle_llm_response)
                
                self.llm_handler = LLMMCPHandler(
                    mcp_manager=self.mcp_manager,
                    llm_bridge=self.llm_bridge,
                    log_callback=self.log_message
                )
                
                # Configurar el manejador MCP
                self.llm_bridge.set_mcp_handler(self.llm_handler)
                
                self.llm_running = True
                self.log_message(f"LLM inicializado con el modelo: {self.llm_model}", "info")
                
            elif (self.provider in provider_configs) or api_key or base_url:
                print(f"\n=== Initializing Remote LLM Provider ===")
                print(f"Provider: {self.provider}")
                print(f"Model: {self.llm_model}")
                print(f"API Key present: {bool(api_key)}")
                print(f"Base URL present: {bool(base_url)}")
                
                # Soporte para proveedores remotos definidos en provider_configs
                # o configurados directamente mediante claves como <provider>_api_key / <provider>_base_url
                from llm_bridge import LLMBridge
                from llm_providers.openrouter_handler import OpenRouterHandler

                try:
                    # Primero verificar la conexión con OpenRouter
                    print("Testing OpenRouter connection (skipped verification)...")
                    # Create handler without forcing a network check at init to avoid
                    # hard failures on transient DNS/network issues. Real requests will
                    # fail later with descriptive errors if the network is unreachable.
                    test_handler = OpenRouterHandler(
                        api_key=api_key,
                        base_url=base_url,
                        model=self.llm_model,
                        verify_on_init=False
                    )
                    print("OpenRouter connection test successful")
                    
                    # Si la conexión es exitosa, configurar el puente
                    print("Configuring LLM Bridge...")
                    self.llm_bridge = LLMBridge(
                        model=self.llm_model,
                        chat_text=self.chat_display,
                        window=self.window,
                        provider=self.provider,
                        api_key=api_key,
                        base_url=base_url
                    )
                    print("Remote LLM Bridge initialized successfully")
                except Exception as e:
                    error_msg = f"Error initializing remote LLM: {str(e)}"
                    print(error_msg)
                    raise Exception(error_msg)

                # Configurar el callback para manejar las respuestas del LLM
                self.llm_bridge.set_response_callback(self._handle_llm_response)

                print("Setting up LLMMCPHandler...")
                try:
                    self.llm_handler = LLMMCPHandler(
                        mcp_manager=self.mcp_manager,
                        llm_bridge=self.llm_bridge,
                        log_callback=self.log_message
                    )

                    # Configurar el manejador MCP
                    print("Setting MCP handler...")
                    self.llm_bridge.set_mcp_handler(self.llm_handler)

                    self.llm_running = True
                    self.log_message(f"LLM remoto configurado: {self.provider} - {self.llm_model}", "info")
                    print("LLM initialization completed successfully")
                    return True
                except Exception as e:
                    error_msg = f"Error en la configuración final del LLM: {str(e)}"
                    print(error_msg)
                    self.log_message(error_msg, "error")
                    return False
                
            else:
                self.log_message(f"Proveedor no configurado: {self.provider}", "error")
                self.llm_running = False
        except Exception as e:
            error_msg = f"Error al inicializar el LLM: {str(e)}"
            self.log_message(error_msg, "error")
            print(f"LLM initialization error: {error_msg}")  # Print to console too
            
            # Obtener traceback completo
            tb = traceback.format_exc()
            print(f"Full traceback:\n{tb}")  # Print traceback to console
            
            # Guardar traceback en archivo local para diagnóstico
            try:
                import pathlib
                out_path = pathlib.Path(__file__).resolve().parent / '.last_llm_init_traceback.log'
                print(f"Attempting to save traceback to: {out_path}")
                with open(out_path, 'w', encoding='utf-8') as _f:
                    _f.write(f"Error message: {error_msg}\n\nFull traceback:\n{tb}")
                self.log_message(f"Traceback guardado en: {out_path}", "info")
                print(f"Traceback saved successfully to {out_path}")
            except Exception as log_error:
                print(f"Failed to save traceback: {log_error}")
                self.log_message(f"No se pudo guardar el traceback: {log_error}", "error")
            # Mostrar diálogo con detalles
            try:
                show_error_with_details(self.window, "Error de inicialización", error_msg, tb)
            except Exception:
                # Fallback simple
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
        
        # Cargar configuración
        self.load_config()
        
        # Inicializar LLM después de cargar la configuración
        # y asegurarse de que la interfaz esté lista
        self.window.after(100, self.init_llm)
    
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

        # Configure grid columns to layout widgets
        top_frame.grid_columnconfigure(0, weight=0) # Provider Label
        top_frame.grid_columnconfigure(1, weight=1) # Provider Combo
        top_frame.grid_columnconfigure(2, weight=0) # Model Label
        top_frame.grid_columnconfigure(3, weight=1) # Model Combo
        top_frame.grid_columnconfigure(4, weight=0) # Configure Button
        top_frame.grid_columnconfigure(5, weight=0) # Start/Stop Button
        top_frame.grid_columnconfigure(6, weight=2) # Spacer
        top_frame.grid_columnconfigure(7, weight=0) # MCP Status
        top_frame.grid_columnconfigure(8, weight=0) # Theme Toggle

        # Provider Selector
        ctk.CTkLabel(top_frame, text="Proveedor:").grid(row=0, column=0, padx=(10, 5), pady=10)
        self.provider_combo = ctk.CTkComboBox(
            top_frame,
            values=["ollama", "openai_compatible", "qwen", "deepseek", "openrouter", "huggingface"],
            command=self.on_provider_change,
            width=150
        )
        self.provider_combo.set(self.provider)
        self.provider_combo.grid(row=0, column=1, padx=5, pady=10)

        # Model Selector
        ctk.CTkLabel(top_frame, text="Modelo:").grid(row=0, column=2, padx=(10, 5), pady=10)
        self.llm_combo = ctk.CTkComboBox(top_frame, values=[], width=200)
        if self.provider == "openrouter":
            self.llm_combo.configure(values=[self.llm_model])
            self.llm_combo.configure(state="readonly")
        self.llm_combo.set(self.llm_model)
        self.llm_combo.grid(row=0, column=3, padx=5, pady=10)

        # Remote LLM Config Button
        self.remote_llm_button = ctk.CTkButton(
            top_frame, text="⚙️", command=self.open_remote_llm_config, width=40
        )
        self.remote_llm_button.grid(row=0, column=4, padx=5, pady=10)

        # LLM Control Button
        self.llm_control_button = ctk.CTkButton(
            top_frame, text="▶️ Iniciar", command=self.toggle_llm, width=100
        )
        self.llm_control_button.grid(row=0, column=5, padx=5, pady=10)

        # Spacer
        ctk.CTkFrame(top_frame, fg_color="transparent").grid(row=0, column=6)

        # MCP Status
        mcp_status_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        mcp_status_frame.grid(row=0, column=7, padx=5, pady=5)
        self.mcp_status_icon = ctk.CTkLabel(mcp_status_frame, text="🔄", font=("Segoe UI", 14))
        self.mcp_status_icon.pack(side=tk.LEFT, padx=(10, 0))
        self.mcp_status_label = ctk.CTkLabel(mcp_status_frame, text="MCP: ...", font=("Segoe UI", 12))
        self.mcp_status_label.pack(side=tk.LEFT, padx=5)

        # Theme Toggle Button
        self.theme_toggle = ctk.CTkButton(
            top_frame, text="🌙", command=self.toggle_theme, width=40
        )
        self.theme_toggle.grid(row=0, column=8, padx=10, pady=10)

        self.update_mcp_status_label()
        self.on_provider_change(self.provider) # Initial UI setup
    
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
        if not hasattr(self, 'log_display') or self.log_display is None:
            print(f"[LOG] {message}")  # Fallback a consola si log_display no está disponible
            return
            
        try:
            self.log_display.configure(state=tk.NORMAL)
            self.log_display.insert(tk.END, f"{message}\n", tag)
            self.log_display.see(tk.END)
            self.log_display.configure(state=tk.DISABLED)
        except Exception as e:
            print(f"Error al mostrar mensaje en el log: {e}")
            print(f"[LOG] {message}")  # Fallback a consola en caso de error
    
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
        print("\n=== Starting LLM ===")
        # Aseguramos que estamos usando el modelo correcto de la configuración
        model = self.config.get('llm_model')
        if not model:
            model = self.llm_combo.get()
        print(f"Selected model: {model}")
        
        if not model:
            print("No model selected")
            messagebox.showerror("Error", "Por favor selecciona un modelo LLM")
            return False
            
        if self.llm_running:
            print("LLM is already running")
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
            print(f"Attempting to initialize model {model}")
            self.log_message(f"Inicializando modelo {model}...", "info")
            
            try:
                init_result = self.init_llm()
                if not init_result:
                    error_msg = "No se pudo inicializar el modelo. Verifica la configuración y la conexión."
                    print(f"Initialization failed: init_llm returned False")
                    raise Exception(error_msg)
                
                # Verificar que el LLM Bridge se configuró correctamente
                if not hasattr(self, 'llm_bridge') or self.llm_bridge is None:
                    raise Exception("LLM Bridge no se inicializó correctamente")
                    
                # Verificar que el handler está configurado
                if not hasattr(self, 'llm_handler') or self.llm_handler is None:
                    raise Exception("LLM Handler no se inicializó correctamente")
                    
            except Exception as e:
                error_msg = f"Error de inicialización: {str(e)}"
                print(f"Detailed initialization error: {error_msg}")
                self.log_message(error_msg, "error")
                raise Exception(error_msg)
                
            print("LLM initialization successful")
            
            # Verificar si el modelo está disponible
            if self.provider == "ollama":
                print(f"Checking Ollama model availability: {model}")
                self.log_message(f"Verificando disponibilidad del modelo {model}...", "info")
                if not self._check_ollama_model(model):
                    print("Ollama model check failed")
                    return False
                print("Ollama model check passed")
            
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
            error_msg = "Error: El modelo LLM no está listo para responder."
            print(error_msg)  # Print to console for debugging
            self.display_message(error_msg, "error")
            return
            
        try:
            print(f"Attempting to generate response for message: {message[:50]}...")
            if not hasattr(self.llm_bridge, 'generate_response'):
                raise AttributeError("LLM Bridge does not have generate_response method")
                
            # Log the current state
            print(f"LLM Bridge state - Provider: {self.llm_bridge.provider}, Model: {self.llm_bridge.model}")
            print(f"Handler initialized: {self.llm_bridge.handler is not None}")
            
            # Iniciar la generación de la respuesta en un hilo separado
            threading.Thread(
                target=self.llm_bridge.generate_response,
                args=(message,),
                daemon=True
            ).start()
            print("Response generation thread started")
            
        except Exception as e:
            error_msg = f"Error al obtener respuesta del LLM: {str(e)}"
            print(f"Error details: {error_msg}")  # Print to console for debugging
            self.log_message(error_msg, "error")
            
            # Get and log the full traceback
            import traceback
            tb = traceback.format_exc()
            print(f"Full traceback:\n{tb}")
            
            # Save the error details
            try:
                with open('.last_llm_response_error.log', 'w', encoding='utf-8') as f:
                    f.write(f"Error message: {error_msg}\n\nFull traceback:\n{tb}")
            except Exception as log_error:
                print(f"Failed to save error log: {log_error}")
                
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
            # Handle structured stream events ({'content':..., 'final': bool}) or legacy string
            is_struct = isinstance(response_text, dict)

            # If it's a structured event
            if is_struct:
                content = response_text.get('content', '')
                final = bool(response_text.get('final', False))

                # If first chunk (we haven't started streaming), insert header
                if not hasattr(self, '_assistant_streaming_active') or not self._assistant_streaming_active:
                    # Start streaming presentation
                    self._assistant_streaming_active = True
                    self.chat_display.configure(state=tk.NORMAL)
                    self.chat_display.insert("end", "Asistente: ", ("assistant_message", "bold"))
                    if content:
                        self.chat_display.insert("end", content, "assistant_message")
                    self.chat_display.configure(state=tk.DISABLED)
                    self.chat_display.see("end")
                else:
                    # Append chunk to existing assistant message
                    if content:
                        self.chat_display.configure(state=tk.NORMAL)
                        self.chat_display.insert("end", content, "assistant_message")
                        self.chat_display.configure(state=tk.DISABLED)
                        self.chat_display.see("end")

                if final:
                    # Finish streaming: add spacing and reset flags
                    self.chat_display.configure(state=tk.NORMAL)
                    self.chat_display.insert("end", "\n\n", "assistant_message")
                    self.chat_display.configure(state=tk.DISABLED)
                    self.chat_display.see("end")
                    self._assistant_streaming_active = False
                    self.assistant_response_active = False

            else:
                # Legacy single-string responses (non-streaming)
                # Marcar que ya no hay una respuesta en proceso
                self.assistant_response_active = False

                # Verificar si la respuesta es un error
                if not response_text or (isinstance(response_text, str) and response_text.startswith("Error:")):
                    if not response_text:
                        response_text = "Error: No se recibió respuesta del modelo"
                    self.display_message(response_text, "error")
                    return

                # Verificar si la respuesta contiene un comando MCP
                if isinstance(response_text, str) and response_text.strip().startswith("MCP_COMMAND_JSON:"):
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
        def on_config_saved(provider, config):
            """Callback que se llama cuando se guarda la configuración"""
            try:
                # First, validate the provided credentials by attempting a test connection
                api_key = config.get('api_key')
                base_url = config.get('base_url')
                model = config.get('model')

                # Try provider-specific verification where available
                try:
                    if provider == 'openrouter':
                        from llm_providers.openrouter_handler import OpenRouterHandler
                        # This will raise on failure when verify_on_init=True
                        OpenRouterHandler(api_key=api_key, base_url=base_url, model=model, verify_on_init=True)
                    else:
                        # Generic path: ask the provider handler to verify if it supports verification
                        from llm_providers import get_llm_handler
                        handler = get_llm_handler(provider_name=provider, api_key=api_key, base_url=base_url, model=model)
                        if hasattr(handler, '_verify_connection'):
                            handler._verify_connection()
                except Exception as verify_err:
                    msg = f"No se pudo verificar la conexión para el proveedor {provider}: {verify_err}"
                    self.log_message(msg, 'error')
                    messagebox.showerror('Error de conexión', msg)
                    return

                # If verification passed, persist configuration
                self.config.set('llm_provider', provider)
                if model:
                    self.config.set('llm_model', model)

                # Guardar la API key y URL base específicas del proveedor
                if api_key:
                    self.config.set(f'{provider}_api_key', api_key)
                if base_url:
                    self.config.set(f'{provider}_base_url', base_url)

                self.config.save_config()

                # Reiniciar el manejador de LLM con la nueva configuración
                self.init_llm()

                # Actualizar la interfaz
                self.update_model_ui()

                self.log_message(f"Configuración de {provider} guardada correctamente", "info")
            except Exception as e:
                error_msg = f"Error al actualizar la configuración: {str(e)}"
                self.log_message(error_msg, "error")
                messagebox.showerror("Error", error_msg)
        
        # Abrir la ventana de configuración con el callback
        LLMConfigWindow(self.window, on_config_saved=on_config_saved)
        
    def update_model_ui(self):
        """Actualiza la interfaz de usuario con el modelo actual"""
        current_model = self.config.get('llm_model', '')
        if current_model and hasattr(self, 'llm_combo'):
            self.llm_combo.set(current_model)
    
    def show_mcp_config(self):
        """Muestra la ventana de configuración de MCP"""
        MCPConfigWindow(self.window, self.mcp_manager, self)
    
    def on_provider_change(self, choice):
        """Handles the logic when the LLM provider is changed."""
        self.provider = choice
        provider_configs = self.config.get('llm_provider_configs', {})

        if choice == "openrouter":
            # For OpenRouter, use the configured model or default to mistral
            model = self.config.get('llm_model') or "mistralai/mistral-7b-instruct:free"
            self.llm_combo.configure(values=[model])
            self.llm_combo.set(model)
            self.llm_combo.configure(state="readonly")
            self.remote_llm_button.configure(state="normal")

        elif choice == "ollama":
            self.llm_combo.configure(state="normal")
            self.remote_llm_button.configure(state="disabled")
            try:
                # This should ideally be done in a non-blocking way
                # For now, let's assume llm_bridge can fetch models
                if not self.llm_bridge:
                    self.init_llm()
                ollama_models = self.llm_bridge.handler.list_models()
                model_names = [m['name'] for m in ollama_models]
                self.llm_combo.configure(values=model_names)
                if self.llm_model not in model_names and model_names:
                    self.llm_combo.set(model_names[0])
                else:
                    self.llm_combo.set(self.llm_model)
            except Exception as e:
                self.log_message(f"Could not fetch Ollama models: {e}", "error")
                self.llm_combo.configure(values=["ollama model not found"])
                self.llm_combo.set("ollama model not found")
        else:
            self.llm_combo.configure(state="readonly")
            self.remote_llm_button.configure(state="normal")
            provider_config = provider_configs.get(choice, {})
            model = provider_config.get("model", "default-model")
            self.llm_combo.configure(values=[model])
            self.llm_combo.set(model)

        self.config.set('llm_provider', choice)
        self.config.save_config()
        self.log_message(f"Provider changed to: {choice}", "info")
    
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
