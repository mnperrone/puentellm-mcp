# llm_config_window.py

import customtkinter as ctk
from tkinter import messagebox
from llm_providers import get_llm_handler
from app_config import AppConfig
from env_manager import env_manager

class LLMConfigWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_config_saved=None):
        super().__init__(parent)
        self.parent = parent
        self.config = AppConfig()
        self.on_config_saved = on_config_saved  # Callback para cuando se guarda la configuración

        self.title("Configuración de LLM Remoto")
        self.geometry("600x500")
        self.transient(parent)
        self.grab_set()

        # Cargar configuraciones existentes
        self.provider_configs = self.config.get('llm_provider_configs', {})
        
        # Configuración actual del proveedor
        self.current_provider = self.config.get('llm_provider', 'ollama')
        self.selected_provider = None  # Proveedor actualmente seleccionado en la UI

        # Inicializar variables de la interfaz
        self.provider_var = ctk.StringVar()
        self.model_var = ctk.StringVar()
        
        # Variables para el sistema de búsqueda/filtrado
        self.all_models = []  # Lista completa de modelos disponibles
        self.filtered_models = []  # Lista filtrada según búsqueda
        
        # Crear la interfaz
        self.create_ui()
        
        # Cargar proveedores
        self.load_providers()
        
        # Cargar configuración inicial si existe
        if self.current_provider:
            # Cargar credenciales desde variables de entorno
            api_key = env_manager.get_api_key(self.current_provider)
            base_url = env_manager.get_base_url(self.current_provider)
            
            # Fallback a configuración JSON si no hay variables de entorno
            if not api_key and self.current_provider in self.provider_configs:
                config = self.provider_configs[self.current_provider]
                api_key = config.get('api_key', '')
            
            if not base_url and self.current_provider in self.provider_configs:
                config = self.provider_configs[self.current_provider]
                base_url = config.get('base_url', '')
            
            # Llenar campos
            if api_key:
                self.api_key_entry.insert(0, api_key)
            if base_url:
                self.base_url_entry.insert(0, base_url)

        # Cargar proveedores
        self.load_providers()
        
    def create_ui(self):
        # Configuración del grid principal
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Frame principal
        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(0, weight=1)

        # Frame de configuración
        self.config_frame = ctk.CTkFrame(main_frame)
        self.config_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.config_frame.grid_columnconfigure(1, weight=1)
        
        # Título
        ctk.CTkLabel(
            self.config_frame,
            text="Configuración de LLM Remoto",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=10)
        
        # Proveedor (fila 1)
        ctk.CTkLabel(self.config_frame, text="Proveedor:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        # URL Base (fila 2)
        ctk.CTkLabel(self.config_frame, text="URL Base:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.base_url_entry = ctk.CTkEntry(self.config_frame, width=300)
        self.base_url_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)
        self.base_url_entry.bind("<KeyRelease>", self.on_field_change)
        
        # API Key (fila 3)
        ctk.CTkLabel(self.config_frame, text="API Key:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.api_key_entry = ctk.CTkEntry(self.config_frame, width=300, show="*")
        self.api_key_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        self.api_key_entry.bind("<KeyRelease>", self.on_field_change)
        
        # Auto-space option (fila 4)
        self.auto_space_var = ctk.BooleanVar(value=self.config.get('auto_space_model_output', False))
        self.auto_space_checkbox = ctk.CTkCheckBox(
            self.config_frame,
            text="Intentar corregir espacios faltantes en la salida del modelo (auto-space)",
            variable=self.auto_space_var
        )
        self.auto_space_checkbox.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Modelo (fila 5) - Siempre visible pero deshabilitado hasta probar conexión
        self.model_label = ctk.CTkLabel(self.config_frame, text="Modelo:")
        self.model_label.grid(row=5, column=0, sticky="w", padx=10, pady=5)
        
        # Campo de búsqueda de modelos (fila 5, col 1)
        self.search_var = ctk.StringVar()
        self.search_entry = ctk.CTkEntry(
            self.config_frame,
            textvariable=self.search_var,
            placeholder_text="🔍 Buscar modelo... (ej: gpt-4, claude, mistral)",
            state="disabled"
        )
        self.search_entry.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        
        # Eventos específicos para detectar cambios en el texto
        self.search_entry.bind("<KeyRelease>", self.on_search_input_change)
        self.search_entry.bind("<Button-1>", lambda e: self.after(10, self.on_search_input_change))
        self.search_entry.bind("<Control-v>", lambda e: self.after(10, self.on_search_input_change))
        self.search_entry.bind("<Control-x>", lambda e: self.after(10, self.on_search_input_change))
        
        # Dropdown de modelos (fila 6)
        self.model_menu = ctk.CTkOptionMenu(
            self.config_frame,
            variable=self.model_var,
            values=["Primero prueba la conexión"],
            state="disabled"
        )
        self.model_menu.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.model_menu.grid_remove()  # Ocultar inicialmente
        
        # Info sobre el modelo seleccionado (fila 7)
        self.model_info_label = ctk.CTkLabel(
            self.config_frame,
            text="💡 Prueba la conexión primero para cargar los modelos disponibles",
            font=("Arial", 10),
            text_color="gray"
        )
        self.model_info_label.grid(row=7, column=0, columnspan=2, sticky="w", padx=10, pady=(0, 5))
        
        # Frame de botones (fila 8)
        self.button_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.button_frame.grid(row=8, column=0, columnspan=2, sticky="e", pady=10)
        
        # Botón de prueba de conexión
        self.test_button = ctk.CTkButton(
            self.button_frame,
            text="Probar Conexión",
            command=self.test_connection
        )
        self.test_button.pack(side="right", padx=5)
        
        # Botón de guardar
        self.save_button = ctk.CTkButton(
            self.button_frame,
            text="Guardar",
            command=self.save_config,
            state="disabled"
        )
        self.save_button.pack(side="right", padx=5)

    def on_field_change(self, event=None):
        """Se ejecuta cuando el usuario modifica los campos de entrada"""
        # Deshabilitar el botón de guardar hasta que se pruebe la conexión nuevamente
        self.save_button.configure(state="disabled")

    def on_search_input_change(self, event=None):
        """Se ejecuta cuando el usuario modifica el contenido del campo de búsqueda"""
        # Obtener el texto actual directamente del widget
        try:
            search_text = self.search_entry.get().lower().strip()
            
            # Verificar que tengamos modelos para buscar
            if not hasattr(self, 'all_models') or not self.all_models:
                return
            
            # Filtrar modelos
            if not search_text:
                self.filtered_models = self.all_models.copy()
            else:
                self.filtered_models = [
                    model for model in self.all_models
                    if search_text in model.lower()
                ]
            
            # Actualizar el dropdown inmediatamente
            self.update_model_dropdown()
            
        except Exception as e:
            print(f"Error en búsqueda de modelos: {e}")
        
    def update_model_dropdown(self):
        """Actualiza el dropdown con los modelos filtrados"""
        if not hasattr(self, 'filtered_models'):
            return
            
        if self.filtered_models:
            # Mostrar los modelos filtrados en el dropdown
            current_selection = self.model_var.get()
            self.model_menu.configure(values=self.filtered_models, state="normal")
            
            # Si el modelo actual no está en los filtrados, seleccionar el primero
            if current_selection not in self.filtered_models:
                self.model_var.set(self.filtered_models[0])
                # Forzar la actualización visual
                self.model_menu.set(self.filtered_models[0])
            
            # Actualizar el contador
            total_models = len(self.all_models)
            filtered_count = len(self.filtered_models)
            
            if filtered_count == total_models:
                count_text = f"✅ {total_models} modelos disponibles. Selecciona uno:"
            else:
                count_text = f"🔍 Mostrando {filtered_count} de {total_models} modelos. Selecciona uno:"
                
            self.model_info_label.configure(text=count_text, text_color="green")
        else:
            # No hay modelos que coincidan con la búsqueda
            self.model_menu.configure(values=["No se encontraron modelos"], state="disabled")
            self.model_info_label.configure(
                text="❌ No se encontraron modelos con ese criterio de búsqueda",
                text_color="orange"
            )

    def load_providers(self):
        """Carga la lista de proveedores disponibles"""
        # Lista estática de proveedores soportados
        providers = ["openrouter", "ollama", "openai", "anthropic"]
        
        # Crear menú desplegable de proveedores
        self.provider_menu = ctk.CTkOptionMenu(
            self.config_frame,
            variable=self.provider_var,
            values=providers,
            command=self.on_provider_select_and_disable_save
        )
        self.provider_menu.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Seleccionar el proveedor guardado o el primero de la lista
        if self.current_provider in providers:
            self.provider_menu.set(self.current_provider)
            self.on_provider_select(self.current_provider)
        else:
            self.provider_menu.set(providers[0])
            self.on_provider_select(providers[0])

    def on_provider_select_and_disable_save(self, selection):
        """Maneja la selección de proveedor y deshabilita el botón guardar"""
        self.on_provider_select(selection)
        self.save_button.configure(state="disabled")

    def on_provider_select(self, selection=None, *args):
        """Maneja la selección de un proveedor"""
        if not selection or selection == "Select a provider":
            self.selected_provider = None
            return
            
        # Guardar el proveedor seleccionado
        self.selected_provider = selection
        
        # Cargar configuración guardada si existe
        config = self.provider_configs.get(selection, {})
        
        # Actualizar campos
        self.api_key_entry.delete(0, "end")
        self.api_key_entry.insert(0, config.get("api_key", ""))
        
        # Establecer URL base por defecto para OpenRouter si no hay configuración guardada
        default_urls = {
            "openrouter": "https://openrouter.ai/api/v1",
            "ollama": "http://localhost:11434"
        }
        
        # Si hay una URL guardada, usarla. Si no, usar la predeterminada si existe
        saved_url = config.get("base_url", "")
        default_url = default_urls.get(selection, "")
        url_to_use = saved_url if saved_url else default_url
        
        # Actualizar el campo de URL base
        self.base_url_entry.delete(0, "end")
        self.base_url_entry.insert(0, url_to_use)
        
        # Asegurarse de que el campo de URL base esté habilitado
        self.base_url_entry.configure(state="normal")
        
        # Si es Ollama, ocultar el campo de API Key
        if selection == "ollama":
            self.api_key_entry.delete(0, "end")
            self.api_key_entry.configure(placeholder_text="No se requiere para Ollama", state="disabled")
        else:
            self.api_key_entry.configure(state="normal")
        
        # Inicializar menú de modelos como deshabilitado
        if hasattr(self, 'model_menu'):
            self.model_menu.destroy()
            
        self.model_var = ctk.StringVar(value="Primero prueba la conexión")
        self.model_menu = ctk.CTkOptionMenu(
            self.config_frame,
            variable=self.model_var,
            values=["Primero prueba la conexión"],
            state="disabled"
        )
        # El menú de modelos debe estar en la fila 6 (después del campo de búsqueda)
        self.model_menu.grid(row=6, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        self.model_menu.grid_remove()  # Ocultar inicialmente
        
        # Resetear también el sistema de búsqueda
        self.all_models = []
        self.filtered_models = []
        self.search_var.set("")
        self.search_entry.configure(state="disabled")
        
        # Habilitar el botón de prueba de conexión
        self.test_button.configure(state="normal")

    def load_models(self, provider, api_key, base_url):
        """Carga los modelos disponibles para un proveedor después de una conexión exitosa"""
        try:
            # Configurar un valor predeterminado mientras se cargan los modelos
            self.model_menu.configure(values=["Cargando modelos..."], state="disabled")
            self.model_var.set("")
            
            # Obtener configuración guardada para este proveedor
            saved_config = self.provider_configs.get(provider, {})
            
            # Si es Ollama, cargar modelos locales
            if provider == "ollama":
                try:
                    from llm_bridge import LLMBridge
                    bridge = LLMBridge(
                        model="",
                        chat_text=None,
                        window=None,
                        provider=provider,
                        api_key=api_key,
                        base_url=base_url
                    )
                    models = bridge.list_models() or []
                    model_names = [m.get('name', '') for m in models if isinstance(m, dict) and 'name' in m]
                    
                    if model_names:
                        self.model_menu.configure(values=model_names, state="normal")
                        
                        # Establecer el modelo guardado o el primero de la lista
                        saved_model = saved_config.get("model")
                        if saved_model and saved_model in model_names:
                            self.model_var.set(saved_model)
                        else:
                            self.model_var.set(model_names[0])
                    else:
                        self.model_menu.configure(values=["No se encontraron modelos"], state="disabled")
                        
                except Exception as e:
                    print(f"Error cargando modelos de Ollama: {e}")
                    self.model_menu.configure(values=[f"Error: {str(e)[:50]}"], state="disabled")
            
            # Para proveedores remotos, cargar modelos disponibles
            else:
                try:
                    from llm_bridge import LLMBridge
                    bridge = LLMBridge(
                        model="",
                        chat_text=None,
                        window=None,
                        provider=provider,
                        api_key=api_key,
                        base_url=base_url
                    )
                    
                    # Obtener la lista de modelos disponibles
                    models = bridge.list_models() or []
                    
                    # Verificar si la respuesta es una lista de diccionarios o una lista de strings
                    if models and isinstance(models[0], dict) and 'id' in models[0]:
                        model_names = [m.get('id', '') for m in models if isinstance(m, dict) and 'id' in m]
                    else:
                        model_names = [str(m) for m in models] if models else []
                    
                    if model_names:
                        # Ordenar los modelos alfabéticamente
                        model_names.sort()
                        
                        # Actualizar el menú desplegable con los modelos
                        self.model_menu.configure(values=model_names, state="normal")
                        
                        # Establecer el modelo guardado o el primero de la lista
                        saved_model = saved_config.get("model")
                        if saved_model and saved_model in model_names:
                            self.model_var.set(saved_model)
                        else:
                            self.model_var.set(model_names[0])
                        
                        # Habilitar el botón de guardar
                        self.save_button.configure(state="normal" if self.model_var.get() else "disabled")
                        return True
                    else:
                        self.model_menu.configure(values=["No se encontraron modelos"], state="disabled")
                        return False
                except Exception as e:
                    messagebox.showerror("Error", f"Error al cargar modelos: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    print(f"Error inesperado al cargar modelos: {e}")
                    self.model_menu.configure(values=[f"Error: {str(e)[:50]}"], state="disabled")
                    return False
                    
        except Exception as e:
            print(f"Error inesperado en load_models: {e}")
            import traceback
            traceback.print_exc()
            self.model_menu.configure(values=["Error al cargar modelos"], state="disabled")
            return False

    def clean_duplicate_keys(self, config):
        """Limpia las claves duplicadas del archivo de configuración.
        
        Args:
            config (dict): El diccionario de configuración a limpiar
            
        Returns:
            dict: El diccionario de configuración limpio
        """
        # Lista de claves redundantes que pueden duplicarse
        redundant_keys = [
            'openrouter_api_key', 'openrouter_base_url', 'openrouter_model',
            'ollama_api_key', 'ollama_base_url', 'ollama_model',
            'api_key', 'base_url', 'model',  # Claves genéricas
            'llm_provider', 'llm_model'  # Claves globales que podrían duplicarse
        ]
        
        # Eliminar claves redundantes que no sean necesarias
        for key in redundant_keys:
            if key in config and key != 'llm_provider' and key != 'llm_model':
                del config[key]
                
        # Asegurarse de que llm_provider_configs existe
        if 'llm_provider_configs' not in config:
            config['llm_provider_configs'] = {}
            
        # Limpiar configuraciones de proveedores vacías
        if 'llm_provider_configs' in config:
            # Eliminar proveedores sin configuración
            config['llm_provider_configs'] = {
                k: v for k, v in config['llm_provider_configs'].items() 
                if v and isinstance(v, dict) and v.get('api_key')
            }
            
        return config

    def save_config(self):
        """Guarda la configuración del proveedor"""
        try:
            if not hasattr(self, 'provider_var') or not self.provider_var.get():
                messagebox.showerror("Error", "No se ha seleccionado ningún proveedor")
                return
                
            selection = self.provider_var.get()
            if selection == "Select a provider":
                messagebox.showerror("Error", "Por favor selecciona un proveedor")
                return
                
            # Obtener el modelo del menú o del campo de entrada, según corresponda
            if hasattr(self, 'model_entry'):  # Si es un campo de entrada
                model = self.model_var.get().strip()
            else:  # Si es un menú desplegable
                model = self.model_var.get()
                
            if not model or model == "Selecciona un proveedor primero" or "Error" in model:
                messagebox.showerror("Error", "Por favor ingresa o selecciona un modelo válido")
                return
            
            # Obtener API key y URL base
            api_key = self.api_key_entry.get().strip()
            base_url = self.base_url_entry.get().strip()
            
            # Validar campos obligatorios según el proveedor
            if selection == "openrouter" and not api_key:
                messagebox.showerror("Error", "La API Key es obligatoria para OpenRouter")
                return
                
            if selection != "ollama" and not base_url:
                messagebox.showerror("Error", f"La URL base es obligatoria para {selection}")
                return
            
            # Validar la URL base si se proporciona
            if base_url:
                try:
                    import requests
                    # Asegurarse de que la URL tenga el protocolo
                    if not base_url.startswith(('http://', 'https://')):
                        base_url = f'http://{base_url}'
                    
                    # Probar la conexión
                    resp = requests.head(base_url, timeout=5, allow_redirects=True)
                    status = getattr(resp, 'status_code', None)
                    
                    if status and status >= 400 and status not in (401, 403):
                        # Si hay un error que no sea de autenticación, preguntar si desea continuar
                        if not messagebox.askyesno(
                            "URL no accesible", 
                            f"La URL '{base_url}' respondió con código {status}. ¿Deseas guardar igual?"
                        ):
                            return
                            
                except requests.RequestException as re:
                    # Si hay un error de conexión, preguntar si desea continuar
                    if not messagebox.askyesno(
                        "No se puede verificar la URL", 
                        f"No se pudo verificar la URL '{base_url}': {str(re)}\n¿Deseas guardar igual?"
                    ):
                        return
            
            # Limpiar claves duplicadas
            self.config.config = self.clean_duplicate_keys(self.config.config)
            
            # Asegurarse de que existe la sección de configuraciones de proveedores
            if 'llm_provider_configs' not in self.config.config:
                self.config.config['llm_provider_configs'] = {}
            
            # Actualizar la configuración del proveedor
            self.config.config['llm_provider_configs'][selection] = {
                "api_key": api_key,
                "base_url": base_url.rstrip('/') if base_url else '',
                "model": model,
            }
            
            # Actualizar proveedor y modelo actual
            self.config.config['llm_provider'] = selection
            self.config.config['llm_model'] = model
            
            # Limpiar claves duplicadas nuevamente por seguridad
            self.config.config = self.clean_duplicate_keys(self.config.config)
            
            # Guardar la configuración
            self.config.save_config()
            
            # Guardar la preferencia global de auto-space
            try:
                self.config.set('auto_space_model_output', bool(self.auto_space_var.get()))
            except Exception as e:
                print(f"Error al guardar preferencia de auto-space: {e}")
            
            # Mostrar resumen de la configuración guardada
            try:
                masked_key = (api_key[:6] + '...') if api_key else 'No'
            except Exception:
                masked_key = 'Sí'
                
            summary = (
                f"Proveedor: {selection}\n"
                f"Modelo: {model}\n"
                f"URL base: {base_url}\n"
                f"API Key guardada: {'Sí (parcialmente ocultada)' if api_key else 'No'}\n"
                f"Archivo de configuración: {getattr(self.config, 'config_path', 'N/A')}"
            )
            messagebox.showinfo("Éxito", f"Configuración guardada correctamente\n\n{summary}")
            
            # Llamar al callback si existe
            if hasattr(self, 'on_config_saved') and callable(self.on_config_saved):
                self.on_config_saved(selection, {
                    "api_key": api_key,
                    "base_url": base_url,
                    "model": model,
                })
            
            # Cerrar la ventana
            self.destroy()
            
        except Exception as e:
            # En caso de error, mostrar mensaje y limpiar claves redundantes
            error_msg = str(e)
            messagebox.showerror("Error", f"Error al guardar la configuración: {error_msg}")
            
            # Registrar el error completo
            import traceback
            traceback.print_exc()
            
            # Limpiar claves redundantes en caso de error
            try:
                if hasattr(self, 'provider_var') and self.provider_var.get():
                    provider = self.provider_var.get()
                    redundant_keys = [
                        f"{provider}_api_key",
                        f"{provider}_base_url",
                        f"{provider}_model",
                        'api_key',
                        'base_url',
                        'model'
                    ]
                    
                    # Eliminar claves redundantes
                    for key in set(redundant_keys):
                        if key in self.config.config:
                            del self.config.config[key]
                    
                    # Guardar los cambios
                    self.config.save_config()
            except Exception as cleanup_error:
                print(f"Error durante la limpieza: {cleanup_error}")
                
            # Obtener los valores de la interfaz
            base_url = self.base_url_entry.get().strip()
            api_key = self.api_key_entry.get().strip()
            
            # Mostrar el campo de modelo después de probar la conexión
            self.model_label.grid()  # Mostrar la etiqueta del modelo
            self.model_menu.grid()   # Mostrar el menú de modelos
            
            # Usar el proveedor seleccionado
            provider = self.selected_provider
            if not provider:
                messagebox.showerror("Error", "No se pudo determinar el proveedor seleccionado")
                return
                
            # Solo validar API key si es necesario (no requerida para Ollama)
            if not api_key and selection != "ollama":  # Ollama no requiere API key
                messagebox.showerror("Error", "La API Key es obligatoria para este proveedor")
                return
                
            # Validar URL base para proveedores que la requieren
            if selection != "ollama" and not base_url:
                messagebox.showerror("Error", "La URL base es obligatoria para este proveedor")
                return
            
            # Mostrar mensaje de espera
            self.test_button.configure(state="disabled", text="Probando...")
            self.save_button.configure(state="disabled")
            self.update()
            
            # Probar conexión en segundo plano (el modelo puede estar vacío en esta etapa)
            self.after(100, lambda: self._test_connection_async(selection, api_key, base_url, ""))
            
        except Exception as e:
            self.test_button.configure(state="normal", text="Probar Conexión")
            messagebox.showerror("Error", f"Error al probar la conexión: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def test_connection(self):
        """Prueba la conexión con el proveedor seleccionado"""
        try:
            # Validar que se haya seleccionado un proveedor
            if not hasattr(self, 'provider_var') or not self.provider_var.get():
                messagebox.showerror("Error", "Por favor, selecciona un proveedor primero")
                return
                
            provider = self.provider_var.get()
            if provider == "Select a provider":
                messagebox.showerror("Error", "Por favor, selecciona un proveedor válido")
                return
            
            # Obtener los valores de la interfaz
            api_key = self.api_key_entry.get().strip()
            base_url = self.base_url_entry.get().strip()
            
            # Validar campos requeridos según el proveedor
            if provider == "openrouter" and not api_key:
                messagebox.showerror("Error", "La API Key es obligatoria para OpenRouter")
                return
                
            if provider != "ollama" and not base_url:
                messagebox.showerror("Error", f"La URL base es obligatoria para {provider}")
                return
            
            # Deshabilitar botones durante la prueba
            self.test_button.configure(state="disabled", text="Probando...")
            self.save_button.configure(state="disabled")
            self.update()
            
            # Ejecutar prueba de conexión en segundo plano
            self.after(100, lambda: self._test_connection_async(provider, api_key, base_url, ""))
            
        except Exception as e:
            # Re-habilitar botones en caso de error
            self.test_button.configure(state="normal", text="Probar Conexión")
            messagebox.showerror("Error", f"Error al probar la conexión: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def _test_connection_async(self, provider, api_key, base_url, model):
        """Método auxiliar para probar la conexión en segundo plano"""
        try:
            from llm_bridge import LLMBridge
            
            # Configurar las variables de entorno necesarias
            import os
            
            # Obtener el proveedor seleccionado de la interfaz
            current_provider = self.provider_var.get()
            if not current_provider or current_provider == "Select a provider":
                self.after(0, lambda: messagebox.showerror("Error", "No se ha seleccionado ningún proveedor"))
                return
            
            # Limpiar variables de entorno previas
            for key in ['OPENROUTER_API_KEY', 'OPENROUTER_API_BASE', 'OLLAMA_API_BASE', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']:
                if key in os.environ:
                    del os.environ[key]
            
            # Configurar las variables para el proveedor actual
            if current_provider == "openrouter":
                if api_key:
                    os.environ['OPENROUTER_API_KEY'] = api_key
                if base_url:
                    os.environ['OPENROUTER_API_BASE'] = base_url
            elif current_provider == "ollama":
                if base_url:
                    os.environ['OLLAMA_API_BASE'] = base_url
            elif current_provider == "openai":
                if api_key:
                    os.environ['OPENAI_API_KEY'] = api_key
                if base_url:
                    os.environ['OPENAI_API_BASE'] = base_url
            elif current_provider == "anthropic":
                if api_key:
                    os.environ['ANTHROPIC_API_KEY'] = api_key
                if base_url:
                    os.environ['ANTHROPIC_API_BASE'] = base_url
            
            # Crear instancia del bridge para probar la conexión
            bridge = LLMBridge(
                model=model or "",
                chat_text=None,
                window=None,
                provider=current_provider,  # Usar current_provider en lugar del parámetro provider
                api_key=api_key,
                base_url=base_url
            )
            
            # Probar la conexión
            success = False
            message = ""
            
            try:
                # Intentar listar modelos para probar la conexión
                models = bridge.list_models()
                success = True
                message = f"Conexión exitosa. {len(models)} modelos disponibles."
            except Exception as e:
                success = False
                message = f"Error al conectar con {provider}: {str(e)}"
            
            if success:
                # Cargar modelos disponibles y actualizar UI
                self.after(0, lambda: self._update_models_success(provider, api_key, base_url, models))
                
                # Habilitar el botón de guardar
                self.after(0, lambda: self.save_button.configure(state="normal"))
            else:
                # Mostrar mensaje de error
                self.after(0, lambda: messagebox.showerror(
                    "Error de conexión",
                    f"No se pudo conectar con {provider}:\n{message}"
                ))
                
                # Mantener el botón de guardar deshabilitado
                self.after(0, lambda: self.save_button.configure(state="disabled"))
                
        except Exception as e:
            # Mostrar mensaje de error detallado
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                error_msg = "API Key inválida o sin permisos"
            elif "404" in error_msg:
                error_msg = f"No se encontró el endpoint. Verifica la URL base: {base_url}"
            elif "ConnectionError" in error_msg:
                error_msg = f"No se pudo conectar al servidor. Verifica la URL: {base_url}"
            
            # Mostrar mensaje de error
            self.after(0, lambda: messagebox.showerror(
                "Error de conexión",
                f"Error al conectar con {provider}:\n{error_msg}"
            ))
            
            # Registrar el error completo en la consola
            import traceback
            traceback.print_exc()
            
        finally:
            # Restaurar el botón de prueba
            self.after(0, lambda: self.test_button.configure(
                state="normal",
                text="Probar Conexión"
            ))
    
    def _update_models_success(self, provider, api_key, base_url, models):
        """Actualiza la UI después de una conexión exitosa"""
        try:
            # Mostrar mensaje de éxito
            messagebox.showinfo(
                "Conexión exitosa",
                f"Conexión con {provider} establecida correctamente\n"
                f"Se encontraron {len(models)} modelos disponibles."
            )
            
            # Procesar modelos según el proveedor
            if provider == "openrouter":
                # Para OpenRouter, models puede ser una lista de IDs (strings) o una lista de diccionarios
                if models and isinstance(models[0], str):
                    # Si ya es una lista de IDs de modelos
                    model_names = models
                else:
                    # Si es una lista de diccionarios
                    model_names = [m.get('id', '') for m in models if isinstance(m, dict) and m.get('id')]
            else:
                # Para otros proveedores (como Ollama)
                if isinstance(models, list) and models:
                    if isinstance(models[0], dict):
                        model_names = [m.get('name', m.get('id', '')) for m in models]
                    else:
                        model_names = models
                else:
                    model_names = ["Modelo por defecto"]
            
            # Actualizar el sistema de modelos
            if model_names:
                # Guardar lista completa de modelos
                self.all_models = sorted(model_names)  # Ordenar alfabéticamente
                self.filtered_models = self.all_models.copy()
                
                # Habilitar el campo de búsqueda
                self.search_entry.configure(state="normal")
                
                # Limpiar cualquier búsqueda previa
                self.search_entry.delete(0, "end")
                
                # Mostrar el menú de modelos (en caso de que estuviera oculto)
                self.model_menu.grid()
                
                # Actualizar el dropdown con todos los modelos inicialmente
                self.update_model_dropdown()
                
                # Seleccionar modelo actual si existe en la lista
                current_model = self.config.get('llm_model', '')
                if current_model and current_model in model_names:
                    self.model_var.set(current_model)
                else:
                    self.model_var.set(self.all_models[0])
                
                # Habilitar el botón de guardar
                self.save_button.configure(state="normal")
            else:
                self.model_menu.configure(values=["No hay modelos disponibles"], state="disabled")
                self.model_info_label.configure(
                    text="⚠️ No se encontraron modelos disponibles",
                    text_color="orange"
                )
                
        except Exception as e:
            print(f"Error updating models UI: {e}")
            self.model_info_label.configure(
                text="❌ Error cargando modelos. Verifica la configuración.",
                text_color="red"
            )
