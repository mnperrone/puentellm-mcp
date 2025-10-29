# llm_config_window.py

import customtkinter as ctk
from tkinter import messagebox
from llm_providers import get_llm_handler
from app_config import AppConfig

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
        
        # Crear la interfaz
        self.create_ui()
        
        # Cargar proveedores
        self.load_providers()
        
        # Cargar configuración inicial si existe
        if self.current_provider in self.provider_configs:
            config = self.provider_configs[self.current_provider]
            self.api_key_entry.insert(0, config.get('api_key', ''))
            self.base_url_entry.insert(0, config.get('base_url', ''))

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
        
        # API Key (fila 3)
        ctk.CTkLabel(self.config_frame, text="API Key:").grid(row=3, column=0, sticky="w", padx=10, pady=5)
        self.api_key_entry = ctk.CTkEntry(self.config_frame, width=300, show="*")
        self.api_key_entry.grid(row=3, column=1, sticky="ew", padx=10, pady=5)
        
        # Auto-space option (fila 4)
        self.auto_space_var = ctk.BooleanVar(value=self.config.get('auto_space_model_output', False))
        self.auto_space_checkbox = ctk.CTkCheckBox(
            self.config_frame,
            text="Intentar corregir espacios faltantes en la salida del modelo (auto-space)",
            variable=self.auto_space_var
        )
        self.auto_space_checkbox.grid(row=4, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # Modelo (fila 5) - Inicialmente oculto
        self.model_label = ctk.CTkLabel(self.config_frame, text="Modelo:")
        self.model_label.grid(row=5, column=0, sticky="w", padx=10, pady=5)
        self.model_label.grid_remove()  # Ocultar inicialmente
        
        self.model_menu = ctk.CTkOptionMenu(
            self.config_frame,
            variable=self.model_var,
            values=["Primero prueba la conexión"],
            state="disabled"
        )
        self.model_menu.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        self.model_menu.grid_remove()  # Ocultar inicialmente
        
        # Frame de botones (fila 5)
        self.button_frame = ctk.CTkFrame(self.config_frame, fg_color="transparent")
        self.button_frame.grid(row=6, column=0, columnspan=2, sticky="e", pady=10)
        
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

    def load_providers(self):
        """Carga la lista de proveedores disponibles"""
        # Lista estática de proveedores soportados
        providers = ["openrouter", "ollama", "openai", "anthropic"]
        
        # Crear menú desplegable de proveedores
        self.provider_menu = ctk.CTkOptionMenu(
            self.config_frame,
            variable=self.provider_var,
            values=providers,
            command=self.on_provider_select
        )
        self.provider_menu.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        # Seleccionar el proveedor guardado o el primero de la lista
        if self.current_provider in providers:
            self.provider_menu.set(self.current_provider)
            self.on_provider_select(self.current_provider)
        else:
            self.provider_menu.set(providers[0])
            self.on_provider_select(providers[0])

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
        # Asegurarse de que el menú de modelos esté en la fila correcta (5)
        self.model_menu.grid(row=5, column=1, sticky="ew", padx=10, pady=5)
        self.model_menu.grid_remove()  # Ocultar inicialmente
        
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

    def save_config(self):
        """Guarda la configuración del proveedor"""
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
            
        api_key = self.api_key_entry.get().strip()
        base_url = self.base_url_entry.get().strip().rstrip('/')

        if not api_key and selection != "ollama":  # Ollama no requiere API key
            messagebox.showerror("Error", "La API Key es obligatoria para este proveedor")
            return

        # Validar reachability de base_url para proveedores remotos (simple check)
        if selection != "ollama" and base_url:
            try:
                import requests
                try:
                    # Use HEAD first to be lightweight; fall back to GET if not allowed
                    resp = requests.head(base_url, timeout=5, allow_redirects=True)
                    status = getattr(resp, 'status_code', None)
                    if status is None or (status >= 400 and status not in (401,403)):
                        # try GET as fallback
                        resp = requests.get(base_url, timeout=5)
                        status = getattr(resp, 'status_code', None)

                    if status and status >= 400 and status not in (401,403):
                        # If 4xx/5xx and not auth errors, warn user and ask to continue
                        if not messagebox.askyesno("URL no accesible", f"La URL '{base_url}' respondió con código {status}. ¿Deseas guardar igual? "):
                            return
                except requests.RequestException as re:
                    # Connectivity issue - ask user whether to continue saving
                    if not messagebox.askyesno("No se puede verificar la URL", f"No se pudo verificar la URL '{base_url}': {str(re)}\n¿Deseas guardar igual?"):
                        return
            except Exception:
                # If requests isn't available or any other error, allow save but log nothing here
                pass

        try:
            # Guardar la configuración
            config_data = {
                "api_key": api_key,
                "base_url": base_url,
                "model": model,
            }
            
            # Actualizar la configuración
            self.provider_configs[selection] = config_data
            self.config.set('llm_provider_configs', self.provider_configs)
            
            # Guardar la configuración actual siempre
            self.config.set('llm_provider', selection)
            self.config.set('llm_model', config_data.get('model', ''))
            self.config.set('api_key', config_data.get('api_key', ''))
            self.config.set('base_url', config_data.get('base_url', ''))
            
            # También guardar en las variables específicas del proveedor
            if config_data.get('api_key'):
                self.config.set(f'{selection}_api_key', config_data['api_key'])
            if config_data.get('base_url'):
                self.config.set(f'{selection}_base_url', config_data['base_url'])
            
            # Guardar los cambios
            self.config.save_config()

            # Guardar la preferencia global de auto-space en AppConfig
            try:
                self.config.set('auto_space_model_output', bool(self.auto_space_var.get()))
            except Exception:
                pass
            
            # Notificar que la configuración se guardó correctamente
            # Mostrar un resumen breve (proveedor, modelo, base_url, clave guardada)
            try:
                masked_key = (config_data.get('api_key')[:6] + '...' ) if config_data.get('api_key') else 'No'
            except Exception:
                masked_key = 'Sí'
            summary = (
                f"Proveedor: {selection}\n"
                f"Modelo: {config_data.get('model', '')}\n"
                f"URL base: {config_data.get('base_url', '')}\n"
                f"API Key guardada: { 'Sí (parcialmente ocultada)' if config_data.get('api_key') else 'No' }\n"
                f"Archivo de configuración: {self.config.config_path if hasattr(self.config, 'config_path') else 'N/A'}"
            )
            messagebox.showinfo("Éxito", f"Configuración guardada correctamente\n\n{summary}")
            
            # Si se proporcionó un callback, llamarlo con la configuración actualizada
            if callable(self.on_config_saved):
                self.on_config_saved(selection, config_data)
                
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la configuración: {str(e)}")
            import traceback
            traceback.print_exc()

    def test_connection(self):
        """Prueba la conexión con el proveedor LLM"""
        try:
            # Obtener el proveedor seleccionado
            selection = self.provider_var.get()
            if not selection or selection == "Select a provider":
                messagebox.showerror("Error", "Por favor selecciona un proveedor")
                return
                
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
                # Mostrar mensaje de éxito
                self.after(0, lambda: messagebox.showinfo(
                    "Conexión exitosa",
                    f"Conexión con {provider} establecida correctamente\n"
                    f"{message}"
                ))
                
                # Cargar modelos disponibles
                self.after(0, lambda: self.load_models(provider, api_key, base_url))
            else:
                # Mostrar mensaje de error
                self.after(0, lambda: messagebox.showerror(
                    "Error de conexión",
                    f"No se pudo conectar con {provider}:\n{message}"
                ))
                
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
