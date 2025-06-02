import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

class ServerStatusIndicator:
    """
    Clase que representa un indicador visual del estado de un servidor.
    Muestra un círculo coloreado que indica el estado (activo, inactivo, error) y permite interactuar con él.
    """
    
    def __init__(self, parent, server_name, mcp_manager, chat_app):
        """
        Inicializa un nuevo indicador de estado de servidor.
        
        Args:
            parent: Widget padre donde se mostrará el indicador
            server_name (str): Nombre del servidor
            mcp_manager: Instancia de MCPManager
            chat_app: Instancia de la aplicación principal
        """
        self.parent = parent
        self.server_name = server_name
        self.mcp_manager = mcp_manager
        self.chat_app = chat_app
        self.is_active = False
        self.has_error = False
        
        # Crear el marco para el indicador
        self.frame = ctk.CTkFrame(parent, fg_color="transparent")
        
        # Indicador visual (círculo)
        self.canvas = tk.Canvas(
            self.frame,
            width=20,
            height=20,
            bg="gray",
            highlightthickness=0,
            relief='flat'
        )
        self.indicator = self.canvas.create_oval(2, 2, 18, 18, fill="gray", outline="gray")
        self.canvas.pack(side=tk.LEFT, padx=5)
        
        # Texto con el nombre del servidor
        self.label = ctk.CTkLabel(self.frame, text=server_name, width=150, anchor="w")
        self.label.pack(side=tk.LEFT, padx=5)
        
        # Botón de detalles
        self.details_btn = ctk.CTkButton(
            self.frame,
            text="Detalles",
            width=60,
            height=20,
            command=self.show_details,
            font=("Arial", 10)
        )
        self.details_btn.pack(side=tk.RIGHT, padx=5)
        
        # Botón de acción (iniciar/detener)
        self.action_btn = ctk.CTkButton(
            self.frame,
            text="Iniciar",
            width=60,
            height=20,
            command=self.toggle_server,
            font=("Arial", 10)
        )
        self.action_btn.pack(side=tk.RIGHT, padx=5)
        
        # Vincular eventos
        self.canvas.bind("<Enter>", self.on_hover)
        self.canvas.bind("<Leave>", self.on_leave)
        self.canvas.bind("<Button-1>", self.toggle_server)
        self.label.bind("<Enter>", self.on_hover)
        self.label.bind("<Leave>", self.on_leave)
        self.label.bind("<Button-1>", self.show_details)
        
        # Actualizar estado inicial
        self.update_status()
    
    def pack(self, **kwargs):
        """Empaqueta el indicador en el widget padre."""
        self.frame.pack(**kwargs)
    
    def grid(self, **kwargs):
        """Coloca el indicador usando el sistema grid."""
        self.frame.grid(**kwargs)
    
    def place(self, **kwargs):
        """Coloca el indicador usando el sistema place."""
        self.frame.place(**kwargs)
    
    def update_status(self):
        """Actualiza el estado del indicador basado en el servidor real."""
        try:
            is_running = self.mcp_manager.is_server_running(self.server_name)
            
            if is_running:
                self.set_active()
                self.action_btn.configure(text="Detener")
            else:
                self.set_inactive()
                self.action_btn.configure(text="Iniciar")
            
            # Verificar si hay errores recientes
            # Esto podría mejorarse para revisar logs o mensajes de error
            self.has_error = False  # En una implementación completa, esto se actualizaría según el estado real
            
        except Exception as e:
            print(f"Error actualizando estado del servidor {self.server_name}: {e}")
            self.set_error()
    
    def set_active(self):
        """Establece el indicador como activo (verde)."""
        self.is_active = True
        self.has_error = False
        self.canvas.itemconfig(self.indicator, fill="#2ecc71", outline="#27ae60")  # Verde claro y borde verde oscuro
    
    def set_inactive(self):
        """Establece el indicador como inactivo (gris)."""
        self.is_active = False
        self.has_error = False
        self.canvas.itemconfig(self.indicator, fill="#95a5a6", outline="#7f8c8d")  # Gris claro y borde gris medio
    
    def set_error(self):
        """Establece el indicador como con error (rojo)."""
        self.is_active = False
        self.has_error = True
        self.canvas.itemconfig(self.indicator, fill="#e74c3c", outline="#c0392b")  # Rojo claro y borde rojo oscuro
    
    def on_hover(self, event=None):
        """Manejador cuando el ratón está sobre el indicador."""
        self.label.configure(text_color="#3498db")  # Cambiar color del texto a azul
    
    def on_leave(self, event=None):
        """Manejador cuando el ratón sale del indicador."""
        # Restaurar color original del texto
        if self.is_active and not self.has_error:
            self.label.configure(text_color="#ecf0f1")
        elif self.has_error:
            self.label.configure(text_color="#e74c3c")
        else:
            self.label.configure(text_color="#95a5a6")
    
    def toggle_server(self, event=None):
        """Inicia o detiene el servidor según su estado actual."""
        try:
            if self.mcp_manager.is_server_running(self.server_name):
                success = self.mcp_manager.stop_server(self.server_name)
                action = "detenido"
            else:
                success = self.mcp_manager.start_server(self.server_name)
                action = "iniciado"
            
            if success:
                # Mostrar mensaje en el chat
                msg = f"Servidor '{self.server_name}' {action} correctamente."
                display_message(self.chat_app.chat_text, msg, "system", new_line_before_message=True)
                
                # Actualizar estado después de un breve retraso
                self.chat_app.window.after(1000, self.update_status)
            else:
                # Mostrar mensaje de error
                msg = f"No se pudo {action} el servidor '{self.server_name}'."
                display_message(self.chat_app.chat_text, msg, "error", new_line_before_message=True)
                self.chat_app.window.after(1000, self.update_status)
                
        except Exception as e:
            error_msg = f"Error al intentar {action} el servidor '{self.server_name}': {str(e)}"
            display_message(self.chat_app.chat_text, error_msg, "error", new_line_before_message=True)
            self.chat_app.window.after(1000, self.update_status)
    
    def show_details(self, event=None):
        """Muestra detalles sobre el servidor."""
        try:
            details = self.mcp_manager.get_server_details(self.server_name)
            
            if not details:
                display_message(
                    self.chat_app.chat_text,
                    f"No hay detalles disponibles para el servidor '{self.server_name}'.",
                    "system",
                    new_line_before_message=True
                )
                return
            
            # Formatear los detalles para mostrarlos
            info = (
                f"Detalles del servidor '{details['name']}':\n"
                f"Tipo: {details['config'].get('type', 'Desconocido')}\n"
                f"Estado: {details['status']}\n"
                f"Comando: {details['config'].get('command', 'N/A')}\n"
                f"Puerto: {details['config'].get('port', 'N/A')}\n"
                f"Habilitado: {'Sí' if details['config'].get('enabled', True) else 'No'}\n"
                f"Activo: {'Sí' if details['is_running'] else 'No'}\n"
            )
            
            # Agregar validación si está disponible
            if 'validation' in details:
                validation = details['validation']
                if validation.get('errors') or validation.get('warnings'):
                    info += "\nValidación de configuración:\n"
                    
                if validation.get('errors'):
                    info += "Errores:\n"
                    for error in validation['errors']:
                        info += f"• {error}\n"
                
                if validation.get('warnings'):
                    info += "Advertencias:\n"
                    for warning in validation['warnings']:
                        info += f"• {warning}\n"
            
            # Mostrar en el chat
            display_message(
                self.chat_app.chat_text,
                info,
                "system",
                new_line_before_message=True
            )
            
        except Exception as e:
            error_msg = f"Error mostrando detalles del servidor '{self.server_name}': {str(e)}"
            display_message(
                self.chat_app.chat_text,
                error_msg,
                "error",
                new_line_before_message=True
            )
    
    def destroy(self):
        """Destruye el widget y libera recursos."""
        self.frame.destroy()

# Nuevo diálogo para gestión de servidores MCP
class MCPConfigWindow:
    """
    Ventana de configuración de servidores MCP.
    Permite ver y modificar la configuración de múltiples servidores MCP.
    """
    
    def __init__(self, parent, mcp_manager, chat_app):
        """
        Inicializa una nueva ventana de configuración.
        
        Args:
            parent: Ventana padre
            mcp_manager: Instancia de MCPManager
            chat_app: Instancia de la aplicación principal
        """
        # Crear ventana emergente
        self.window = ctk.CTkToplevel(parent)
        self.window.title("Configuración de Servidores MCP")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        
        # Asegurar que esta ventana esté siempre al frente
        self.window.transient(parent)
        self.window.grab_set()
        
        self.mcp_manager = mcp_manager
        self.chat_app = chat_app
        
        # Frame principal
        self.main_frame = ctk.CTkFrame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(
            self.main_frame,
            text="Gestión de Servidores MCP",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 5))
        
        # Frame para botones de control
        control_frame = ctk.CTkFrame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Botón para agregar servidor
        add_btn = ctk.CTkButton(
            control_frame,
            text="Agregar Servidor",
            command=self.add_server,
            width=120
        )
        add_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para eliminar servidor
        remove_btn = ctk.CTkButton(
            control_frame,
            text="Eliminar Servidor",
            command=self.remove_server,
            width=120,
            fg_color="transparent",
            border_width=2,
            hover_color="#444444"
        )
        remove_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para cargar configuración
        load_btn = ctk.CTkButton(
            control_frame,
            text="Cargar Configuración",
            command=self.load_config,
            width=120
        )
        load_btn.pack(side=tk.RIGHT, padx=5)
        
        # Botón para guardar configuración
        save_btn = ctk.CTkButton(
            control_frame,
            text="Guardar Configuración",
            command=self.save_config,
            width=120
        )
        save_btn.pack(side=tk.RIGHT, padx=5)
        
        # Frame para búsqueda
        search_frame = ctk.CTkFrame(self.main_frame)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filter_servers())
        
        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="Buscar servidores...",
            textvariable=self.search_var,
            width=300
        )
        search_entry.pack(side=tk.RIGHT, padx=5)
        
        ctk.CTkLabel(search_frame, text="Filtrar por tipo:", width=100).pack(side=tk.RIGHT, padx=5)
        
        # Frame para filtros
        filter_frame = ctk.CTkFrame(self.main_frame)\n        filter_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Variables para los filtros
        self.type_filters = {
            'all': tk.BooleanVar(value=True),
            'local': tk.BooleanVar(value=True),
            'npm': tk.BooleanVar(value=True),
            'remote': tk.BooleanVar(value=True)
        }
        
        # Crear controles de filtro
        for server_type, var in self.type_filters.items():
            cb = ctk.CTkCheckBox(
                filter_frame,
                text=server_type.capitalize(),
                variable=var,
                command=self.filter_servers,
                width=100
            )
            cb.pack(side=tk.LEFT, padx=5)
        
        # Frame para lista de servidores
        servers_frame = ctk.CTkFrame(self.main_frame)
        servers_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas para scroll
        self.canvas = tk.Canvas(servers_frame, highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(
            servers_frame,
            orientation="vertical",
            command=self.canvas.yview
        )
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Frame para contenedor de servidores
        self.servers_container = ctk.CTkFrame(self.canvas)
        self.servers_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        # Crear ventana en el canvas
        self.canvas_window = self.canvas.create_window((0, 0), window=self.servers_container, anchor="nw", width=self.canvas.winfo_width())
        
        # Vincular eventos de scroll
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind("<Configure>", self.on_canvas_configure)
        
        # Cargar servidores
        self.server_indicators = []
        self.original_servers = []
        self.load_servers()
    
    def on_canvas_configure(self, event):
        """Ajusta el ancho del contenedor al tamaño del canvas."""
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def load_servers(self):
        """Carga los servidores desde el MCPManager."""
        try:
            # Limpiar servidores existentes
            for indicator in self.server_indicators:
                indicator.destroy()
            self.server_indicators.clear()
            
            # Obtener servidores originales
            servers = self.mcp_manager.servers_config.get('mcpServers', {})
            self.original_servers = list(servers.keys())
            
            # Crear indicadores para cada servidor
            for name in self.original_servers:
                config = servers[name]
                indicator = ServerStatusIndicator(
                    self.servers_container,
                    name,
                    self.mcp_manager,
                    self.chat_app
                )
                indicator.pack(fill=tk.X, pady=2)
                self.server_indicators.append(indicator)
            
            # Aplicar filtrado inicial
            self.filter_servers()
            
        except Exception as e:
            print(f"Error cargando servidores: {e}")
            messagebox.showerror(
                "Error",
                f"No se pudieron cargar los servidores MCP: {str(e)}"
            )
    
    def filter_servers(self, event=None):
        """Filtra los servidores según el término de búsqueda y los tipos seleccionados."""
        try:
            # Eliminar todos los widgets del contenedor
            for widget in self.servers_container.winfo_children():
                widget.pack_forget()
                widget.destroy()
            
            # Obtener filtro de búsqueda
            search_term = self.search_var.get().lower()
            
            # Determinar qué tipos están seleccionados
            active_types = [t for t, var in self.type_filters.items() if var.get()]
            
            # Si 'all' está seleccionado, incluir todos los tipos
            if 'all' in active_types:
                active_types = ['local', 'npm', 'remote']
            
            # Filtrar y mostrar servidores
            filtered = []
            for indicator in self.server_indicators:
                server_name = indicator.server_name.lower()
                server_config = self.mcp_manager.servers_config["mcpServers"].get(indicator.server_name, {})
                server_type = server_config.get('type', 'local').lower()
                
                # Aplicar filtros
                matches_search = not search_term or search_term in server_name
                matches_type = not active_types or server_type in active_types
                
                if matches_search and matches_type:
                    indicator.pack(fill=tk.X, pady=2)
                    filtered.append(indicator)
                else:
                    indicator.frame.pack_forget()
            
            # Actualizar región de scroll
            self.servers_container.update_idletasks()
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))
            
        except Exception as e:
            print(f"Error filtrando servidores: {e}")
    
    def add_server(self):
        """Añade un nuevo servidor con configuración predeterminada."""
        try:
            # Mostrar diálogo para obtener el nombre
            dialog = ctk.CTkToplevel(self.window)
            dialog.title("Añadir Servidor MCP")
            dialog.geometry("400x150")
            dialog.resizable(False, False)
            
            # Centrar la ventana
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Frame principal
            main_frame = ctk.CTkFrame(dialog)
            main_frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            # Campo para el nombre
            name_label = ctk.CTkLabel(main_frame, text="Nombre del servidor:")
            name_label.pack(anchor="w", padx=5, pady=(10, 0))
            
            name_entry = ctk.CTkEntry(main_frame, placeholder_text="my-server")
            name_entry.pack(fill="x", padx=5, pady=(0, 10))
            
            # Campo para el tipo
            type_label = ctk.CTkLabel(main_frame, text="Tipo de servidor:")
            type_label.pack(anchor="w", padx=5, pady=(10, 0))
            
            type_options = ["local", "npm", "remote"]
            type_var = tk.StringVar(value=type_options[0])
            
            type_menu = ctk.CTkOptionMenu(
                main_frame,
                variable=type_var,
                values=type_options
            )
            type_menu.pack(fill="x", padx=5, pady=(0, 10))
            
            # Campo para el comando
            cmd_label = ctk.CTkLabel(main_frame, text="Comando:")
            cmd_label.pack(anchor="w", padx=5, pady=(10, 0))
            
            cmd_entry = ctk.CTkEntry(main_frame, placeholder_text="python -m my_module")
            cmd_entry.pack(fill="x", padx=5, pady=(0, 10))
            
            # Campo para el puerto
            port_label = ctk.CTkLabel(main_frame, text="Puerto:")
            port_label.pack(anchor="w", padx=5, pady=(10, 0))
            
            port_entry = ctk.CTkEntry(main_frame, placeholder_text="8080")
            port_entry.pack(fill="x", padx=5, pady=(0, 10))
            
            result = [None]  # Usar lista para permitir modificación en funciones internas
            
            def on_ok():
                name = name_entry.get().strip()
                server_type = type_var.get().strip()
                command = cmd_entry.get().strip()
                port = port_entry.get().strip()
                
                if not name:
                    messagebox.showerror("Error", "El nombre del servidor no puede estar vacío.")
                    return
                
                if name in self.mcp_manager.servers_config["mcpServers"]:
                    messagebox.showerror("Error", f"Ya existe un servidor con el nombre '{name}'.")
                    return
                
                if not command:
                    messagebox.showerror("Error", "El comando no puede estar vacío.")
                    return
                
                if not port:
                    messagebox.showerror("Error", "El puerto no puede estar vacío.")
                    return
                
                try:
                    port = int(port)
                    if not 1 <= port <= 65535:
                        raise ValueError("Puerto fuera de rango")
                except ValueError:
                    messagebox.showerror("Error", "El puerto debe ser un número entre 1 y 65535.")
                    return
                
                # Crear configuración básica
                config = {
                    "command": command,
                    "type": server_type,
                    "port": port,
                    "enabled": True
                }
                
                # Añadir servidor
                success = self.mcp_manager.add_server(name, config)
                if success:
                    # Guardar configuración
                    self.mcp_manager.save_config()
                    # Recargar servidores
                    self.load_servers()
                    # Cerrar diálogo
                    result[0] = True
                    dialog.destroy()
                else:
                    messagebox.showerror(
                        "Error",
                        f"No se pudo añadir el servidor '{name}'.\n\n"
                        "Verifique que el nombre sea único y la configuración sea válida."
                    )
            
            def on_cancel():
                result[0] = False
                dialog.destroy()
            
            # Botones
            btn_frame = ctk.CTkFrame(main_frame)
            btn_frame.pack(pady=(20, 0))
            
            ok_btn = ctk.CTkButton(btn_frame, text="Aceptar", command=on_ok, width=120)
            cancel_btn = ctk.CTkButton(
                btn_frame,
                text="Cancelar",
                command=on_cancel,
                width=120,
                fg_color="transparent",
                border_width=2,
                hover_color="#444444"
            )
            
            ok_btn.pack(side=tk.RIGHT, padx=5)
            cancel_btn.pack(side=tk.RIGHT, padx=5)
            
            # Esperar hasta que se cierre la ventana
            dialog.wait_window()
            
            # Si se creó correctamente, recargar la lista
            if result[0]:
                self.filter_servers()
            
        except Exception as e:
            print(f"Error añadiendo servidor: {e}")
            messagebox.showerror("Error", f"No se pudo añadir el servidor: {str(e)}")
    
    def remove_server(self):
        """Elimina un servidor seleccionado."""
        try:
            # Obtener servidores activos
            active_servers = self.mcp_manager.get_active_server_names()
            servers = list(self.mcp_manager.servers_config["mcpServers"].keys())
            
            if not servers:
                messagebox.showinfo("Información", "No hay servidores para eliminar.")
                return
            
            # Mostrar diálogo para seleccionar servidor
            dialog = ctk.CTkToplevel(self.window)
            dialog.title("Eliminar Servidor MCP")
            dialog.geometry("400x150")
            dialog.resizable(False, False)
            
            # Centrar la ventana
            dialog.update_idletasks()
            x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
            y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
            dialog.geometry(f"+{x}+{y}")
            
            # Frame principal
            main_frame = ctk.CTkFrame(dialog)
            main_frame.pack(padx=20, pady=20, fill="both", expand=True)
            
            # Seleccionar servidor
            server_var = tk.StringVar()
            server_menu = ctk.CTkOptionMenu(
                main_frame,
                variable=server_var,
                values=servers,
                width=300
            )
            server_menu.pack(pady=10)
            
            result = [None]  # Usar lista para permitir modificación
            
            def on_ok():
                selected_server = server_var.get()
                if not selected_server:
                    messagebox.showwarning("Advertencia", "Por favor, seleccione un servidor.")
                    return
                
                # Confirmar eliminación
                if messagebox.askyesno(
                    "Confirmar Eliminación",
                    f"¿Está seguro de eliminar el servidor '{selected_server}'?\n"
                    "Esta acción no se puede deshacer."
                ):
                    # Eliminar servidor
                    success = self.mcp_manager.remove_server(selected_server)
                    if success:
                        # Guardar configuración
                        self.mcp_manager.save_config()
                        # Recargar servidores
                        self.load_servers()
                        # Cerrar diálogo
                        result[0] = True
                        dialog.destroy()
                    else:
                        messagebox.showerror(
                            "Error",
                            f"No se pudo eliminar el servidor '{selected_server}'."
                        )
            
            def on_cancel():
                result[0] = False
                dialog.destroy()
            
            # Botones
            btn_frame = ctk.CTkFrame(main_frame)
            btn_frame.pack(pady=(10, 0))
            
            ok_btn = ctk.CTkButton(btn_frame, text="Eliminar", command=on_ok, width=120, fg_color="red", hover_color="#cc0000")
            cancel_btn = ctk.CTkButton(
                btn_frame,
                text="Cancelar",
                command=on_cancel,
                width=120,
                fg_color="transparent",
                border_width=2,
                hover_color="#444444"
            )
            
            ok_btn.pack(side=tk.RIGHT, padx=5)
            cancel_btn.pack(side=tk.RIGHT, padx=5)
            
            # Esperar hasta que se cierre la ventana
            dialog.wait_window()
            
            # Si se eliminó correctamente, recargar la lista
            if result[0]:
                self.filter_servers()
            
        except Exception as e:
            print(f"Error eliminando servidor: {e}")
            messagebox.showerror("Error", f"No se pudo eliminar el servidor: {str(e)}")
    
    def load_config(self):
        """Carga una configuración desde un archivo."""
        try:
            # Abrir diálogo para seleccionar archivo
            file_path = filedialog.askopenfilename(
                title="Seleccionar Archivo de Configuración",
                initialdir=os.path.expanduser('~'),
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            
            if not file_path:
                return  # Usuario canceló
            
            # Cargar configuración
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Validar y cargar configuración
            validated_config = self.mcp_manager.validate_config_file(file_path)
            if not validated_config:
                messagebox.showerror(
                    "Error",
                    f"No se pudo validar la configuración en {file_path}.\n"
                    "Verifique que sea un archivo válido con configuración MCP correcta."
                )
                return
            
            # Preguntar si desea sobreescribir
            response = messagebox.askyesno(
                "Confirmar Carga",
                "¿Desea sobreescribir la configuración actual con la del archivo seleccionado?\n"
                "(Se perderán los cambios no guardados)",
                icon=messagebox.WARNING
            )
            
            if not response:
                return
            
            # Sobreescribir configuración
            self.mcp_manager.servers_config = validated_config
            # Guardar la nueva configuración
            self.mcp_manager.save_config()
            # Recargar servidores
            self.load_servers()
            # Mostrar mensaje
            messagebox.showinfo(
                "Éxito",
                f"Configuración cargada exitosamente desde {os.path.basename(file_path)}.\n"
                f"{len(validated_config['mcpServers'])} servidores MCP cargados."
            )
            
        except Exception as e:
            print(f"Error cargando configuración: {e}")
            messagebox.showerror(
                "Error",
                f"No se pudo cargar la configuración: {str(e)}"
            )
    
    def save_config(self):
        """Guarda la configuración actual en un archivo."""
        try:
            # Abrir diálogo para seleccionar ubicación
            file_path = filedialog.asksaveasfilename(
                title="Guardar Archivo de Configuración",
                initialdir=os.path.expanduser('~'),
                defaultextension=".json",
                filetypes=[("Archivos JSON", "*.json"), ("Todos los archivos", "*.*")]
            )
            
            if not file_path:
                return  # Usuario canceló
            
            # Guardar configuración
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.mcp_manager.servers_config, f, indent=2)
            
            # Mostrar mensaje
            messagebox.showinfo(
                "Éxito",
                f"Configuración guardada exitosamente en {os.path.basename(file_path)}."
            )
            
        except Exception as e:
            print(f"Error guardando configuración: {e}")
            messagebox.showerror(
                "Error",
                f"No se pudo guardar la configuración: {str(e)}"
            )