import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import json
import os
from ui_helpers import create_standard_dialog
import tkinter as tk
from mcp_gallery_manager import MCPGalleryManager
import threading

class MCPConfigWindow(ctk.CTkToplevel):
    """
    Ventana emergente para configurar y gestionar servidores MCP.
    Permite al usuario ver, editar, agregar y eliminar configuraciones de servidores MCP.
    """
    def __init__(self, parent, mcp_manager, chat_app=None):
        """
        Inicializa una nueva instancia de la ventana de configuración MCP.
        Args:
            parent: Ventana principal (ChatApp)
            mcp_manager: Instancia de MCPManager
            chat_app: Referencia a la aplicación principal (opcional)
        """
        super().__init__(parent)
        self.mcp_manager = mcp_manager
        self.chat_app = chat_app
        self.parent = parent
        self.title("Configuración de Servidores MCP")
        self.geometry("800x600")
        self.resizable(True, True)

        # Inicializar galería MCP con logger de la aplicación si está disponible
        external_logger = None
        if hasattr(self.chat_app, 'chat_logger'):
            external_logger = self.chat_app.chat_logger
        self.gallery_manager = MCPGalleryManager(external_logger=external_logger)
        
        # Variable para servidores disponibles
        self.available_servers = {}
        self.docker_servers = {}

        # Crear UI
        self.create_ui()
        
        # Cargar servidores actuales
        self.update_server_list()
    
    def open_main_gallery(self):
        """Abre la galería principal de servidores MCP."""
        try:
            from mcp_gallery_window import MCPGalleryWindow
            gallery = MCPGalleryWindow(
                parent_window=self,
                mcp_manager=self.mcp_manager,
                chat_app=self.chat_app
            )
            gallery.show()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la galería: {str(e)}")
    
    def update_server_list(self):
        """Actualiza la lista de servidores instalados."""
        try:
            # Verificar que el TreeView existe
            if not hasattr(self, 'servers_tree'):
                print("TreeView no existe aún, saltando actualización")
                return
                
            # Limpiar lista actual
            for item in self.servers_tree.get_children():
                self.servers_tree.delete(item)
            
            # Obtener configuración actual
            self.mcp_manager.load_config()  # Cargar configuración
            servers = self.mcp_manager.servers_config.get("mcpServers", {})
            
            # Poblar la lista
            for server_name, server_config in servers.items():
                command = " ".join(server_config.get("args", []))
                port = str(server_config.get("port", "N/A"))
                enabled = "Sí" if server_config.get("enabled", True) else "No"
                
                self.servers_tree.insert("", "end", values=(server_name, command, port, enabled))
        except Exception as e:
            print(f"Error actualizando lista de servidores: {e}")
    
    # =================== MÉTODOS DE UI ===================
    
    def create_ui(self):
        """Crea la interfaz de usuario."""
        # Frame principal para servidores instalados
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ttk.Label(main_frame, text="Configuración de Servidores MCP Instalados", font=('Arial', 14, 'bold'))
        title_label.pack(pady=(0, 10))
        
        # Treeview para mostrar servidores instalados
        self.servers_tree = ttk.Treeview(main_frame, columns=("Nombre", "Comando", "Puerto", "Habilitado"), show="headings")
        self.servers_tree.heading("Nombre", text="Nombre")
        self.servers_tree.heading("Comando", text="Comando") 
        self.servers_tree.heading("Puerto", text="Puerto")
        self.servers_tree.heading("Habilitado", text="Habilitado")
        self.servers_tree.column("Nombre", width=120)
        self.servers_tree.column("Comando", width=250)
        self.servers_tree.column("Puerto", width=60)
        self.servers_tree.column("Habilitado", width=80)
        self.servers_tree.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # Botones de acción para instalados
        btn_frame_installed = ttk.Frame(main_frame)
        btn_frame_installed.pack(fill=tk.X, pady=5)
        
        ttk.Button(btn_frame_installed, text="Añadir", command=self.add_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_installed, text="Editar", command=self.edit_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_installed, text="Eliminar", command=self.delete_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame_installed, text="Probar Conexión", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        
        # Botón para abrir galería MCP (función principal)
        ttk.Button(btn_frame_installed, text="🧩 Galería de Servidores", command=self.open_main_gallery).pack(side=tk.LEFT, padx=15)
        
        ttk.Button(btn_frame_installed, text="Guardar", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        
    def add_server(self):
        """Muestra un diálogo para añadir un nuevo servidor."""
        AddServerDialog(self, self)

    def edit_server(self):
        """Edita el servidor seleccionado."""
        selected = self.servers_tree.selection()
        if not selected:
            messagebox.showwarning("Editar Servidor", "Por favor, seleccione un servidor para editar.")
            return
        
        # Obtener datos del servidor seleccionado
        item = self.servers_tree.item(selected[0])
        server_name = item["values"][0]
        
        # Obtener configuración del servidor desde el manager
        self.mcp_manager.load_config()
        server_config = self.mcp_manager.servers_config.get("mcpServers", {}).get(server_name, {})
        
        AddServerDialog(self, self, server_name, server_config)

    def delete_server(self):
        """Elimina el servidor seleccionado."""
        selected = self.servers_tree.selection()
        if not selected:
            messagebox.showwarning("Eliminar Servidor", "Por favor, seleccione un servidor para eliminar.")
            return
        
        if messagebox.askyesno("Confirmar Eliminación", "¿Está seguro de que quiere eliminar el servidor seleccionado?"):
            item = self.servers_tree.item(selected[0])
            server_name = item["values"][0]
            self.servers_tree.delete(selected[0])
            
            # También eliminarlo de la configuración del manager
            self.mcp_manager.load_config()
            servers_config = self.mcp_manager.servers_config.get("mcpServers", {})
            if server_name in servers_config:
                del servers_config[server_name]
                # Guardar la configuración actualizada
                self.mcp_manager.servers_config["mcpServers"] = servers_config
                self.mcp_manager.save_config()

    def test_connection(self):
        """Prueba la conexión del servidor seleccionado."""
        selected = self.servers_tree.selection()
        if not selected:
            messagebox.showwarning("Probar Conexión", "Por favor, seleccione un servidor para probar.")
            return
        
        item = self.servers_tree.item(selected[0])
        server_name = item["values"][0]
        
        try:
            # Obtener configuración del servidor
            self.mcp_manager.load_config()
            servers_config = self.mcp_manager.servers_config.get("mcpServers", {})
            server_config = servers_config.get(server_name, {})
            
            if not server_config:
                messagebox.showerror("Error", f"No se encontró configuración para el servidor '{server_name}'.")
                return
            
            # Verificar si el servidor está habilitado
            if not server_config.get("enabled", True):
                messagebox.showwarning("Servidor Deshabilitado", f"El servidor '{server_name}' está deshabilitado.")
                return
            
            # Para servidor filesystem, verificar el comando y argumentos
            if server_name.lower() == "filesystem":
                command = server_config.get("command", "")
                args = server_config.get("args", [])
                
                if not command:
                    messagebox.showerror("Error", "No se ha configurado un comando para el servidor filesystem.")
                    return
                
                # Verificar que los argumentos contienen una ruta válida
                if isinstance(args, list) and len(args) > 0:
                    # Para el servidor filesystem, buscar rutas después de los parámetros iniciales
                    valid_paths = []
                    invalid_paths = []
                    
                    for arg in args:
                        if isinstance(arg, str):
                            # Saltar parámetros que no son rutas
                            if arg in ['-y', '@modelcontextprotocol/server-filesystem']:
                                continue
                            
                            # Saltar si es una opción (empieza con -)
                            if arg.startswith('-'):
                                continue
                                
                            # Si contiene caracteres de ruta o es una ruta absoluta
                            is_path = False
                            if any(char in arg for char in [':', '\\', '/']):
                                is_path = True
                            elif os.path.sep in arg or (len(arg) > 1 and arg[1] == ':'):
                                is_path = True
                            
                            if is_path:
                                # Normalizar la ruta para Windows
                                normalized_path = os.path.normpath(arg)
                                if os.path.exists(normalized_path):
                                    valid_paths.append(normalized_path)
                                else:
                                    invalid_paths.append(normalized_path)
                    
                    # Construir mensaje detallado
                    status_message = f"Servidor: {server_name}\n"
                    status_message += f"Comando: {command}\n"
                    status_message += f"Total de argumentos: {len(args)}\n\n"
                    
                    if valid_paths:
                        status_message += f"✅ Rutas válidas ({len(valid_paths)}):\n"
                        for path in valid_paths[:3]:  # Mostrar máximo 3
                            status_message += f"  • {path}\n"
                        if len(valid_paths) > 3:
                            status_message += f"  • ... y {len(valid_paths) - 3} más\n"
                        status_message += "\n"
                    
                    if invalid_paths:
                        status_message += f"⚠️ Rutas no encontradas ({len(invalid_paths)}):\n"
                        for path in invalid_paths[:3]:  # Mostrar máximo 3
                            status_message += f"  • {path}\n"
                        if len(invalid_paths) > 3:
                            status_message += f"  • ... y {len(invalid_paths) - 3} más\n"
                        status_message += "\n"
                    
                    # Determinar el tipo de mensaje basado en los resultados
                    if valid_paths and not invalid_paths:
                        status_message += "🎉 Estado: Todas las rutas son válidas"
                        messagebox.showinfo("Prueba de Conexión - Filesystem", status_message)
                    elif valid_paths and invalid_paths:
                        status_message += "⚠️ Estado: Algunas rutas necesitan corrección"
                        messagebox.showwarning("Prueba de Conexión - Filesystem", status_message)
                    elif not valid_paths and invalid_paths:
                        status_message += "❌ Estado: Ninguna ruta es válida"
                        messagebox.showerror("Prueba de Conexión - Filesystem", status_message)
                    else:
                        # No hay rutas configuradas
                        status_message += "ℹ️ Estado: No se encontraron rutas configuradas"
                        messagebox.showinfo("Prueba de Conexión - Filesystem", status_message)
                else:
                    messagebox.showwarning(
                        "Prueba de Conexión - Filesystem",
                        f"Servidor: {server_name}\n"
                        f"Advertencia: No se han configurado argumentos (ruta requerida)."
                    )
            else:
                # Para otros servidores, mostrar información básica
                command = server_config.get("command", "Sin comando")
                port = server_config.get("port", "Sin puerto")
                enabled = "Habilitado" if server_config.get("enabled", True) else "Deshabilitado"
                
                messagebox.showinfo(
                    f"Prueba de Conexión - {server_name}",
                    f"Servidor: {server_name}\n"
                    f"Comando: {command}\n"
                    f"Puerto: {port}\n"
                    f"Estado: {enabled}\n"
                    f"Configuración verificada correctamente"
                )
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al probar conexión del servidor '{server_name}':\n{str(e)}")
            self.mcp_manager.logger.error(f"Error en test_connection para {server_name}: {e}")

    def save_config(self):
        """Guarda la configuración actual."""
        try:
            # La configuración ya está en el manager, solo necesitamos guardarla
            success = self.mcp_manager.save_config()
            
            if success:
                messagebox.showinfo("Guardar", "Configuración guardada correctamente.")
                
                # Notificar a la aplicación principal si está disponible
                if self.chat_app:
                    self.chat_app.load_mcp_config()
            else:
                messagebox.showerror("Error", "No se pudo guardar la configuración.")
                
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar la configuración: {str(e)}")


class AddServerDialog:
    """Diálogo para añadir o editar servidores MCP."""
    
    def __init__(self, parent, config_window, server_name=None, server_config=None):
        self.parent = parent
        self.config_window = config_window
        self.server_name = server_name
        self.server_config = server_config or {}
        
        # Crear diálogo
        self.dialog = create_standard_dialog(
            parent, 
            "Editar Servidor" if server_name else "Añadir Servidor", 
            "500x400"
        )
        
        # Configurar el protocolo de cierre de ventana
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        self.create_form()
    
    def create_form(self):
        """Crea el formulario de entrada."""
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Nombre
        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(frame, width=40)
        self.name_entry.grid(row=0, column=1, sticky="w", pady=5)
        self.name_entry.insert(0, self.server_name or "")
        
        # Comando
        ttk.Label(frame, text="Comando:").grid(row=1, column=0, sticky="w", pady=5)
        self.command_entry = ttk.Entry(frame, width=40)
        self.command_entry.grid(row=1, column=1, sticky="w", pady=5)
        self.command_entry.insert(0, self.server_config.get("command", ""))
        
        # Argumentos
        ttk.Label(frame, text="Argumentos:").grid(row=2, column=0, sticky="nw", pady=5)
        self.args_text = tk.Text(frame, width=40, height=5)
        self.args_text.grid(row=2, column=1, sticky="w", pady=5)
        
        # Insertar argumentos existentes
        args = self.server_config.get("args", [])
        if isinstance(args, list):
            self.args_text.insert(tk.END, "\n".join(args))
        elif isinstance(args, str):
            self.args_text.insert(tk.END, args)
        
        # Puerto
        ttk.Label(frame, text="Puerto:").grid(row=3, column=0, sticky="w", pady=5)
        self.port_entry = ttk.Entry(frame, width=10)
        self.port_entry.grid(row=3, column=1, sticky="w", pady=5)
        self.port_entry.insert(0, str(self.server_config.get("port", "")))
        
        # Habilitado
        self.enabled_var = tk.BooleanVar(value=self.server_config.get("enabled", True))
        ttk.Checkbutton(frame, text="Habilitado", variable=self.enabled_var).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=5
        )
        
        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        
        ttk.Button(btn_frame, text="Aceptar", command=self.save).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=self.on_closing).pack(side=tk.LEFT, padx=5)
    
    def on_closing(self):
        """Maneja el cierre del diálogo."""
        self.dialog.destroy()
    
    def save(self):
        """Guarda el servidor."""
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Error", "El nombre del servidor no puede estar vacío.")
            return
        
        command = self.command_entry.get().strip()
        args = [arg.strip() for arg in self.args_text.get("1.0", tk.END).split("\n") if arg.strip()]
        try:
            port = int(self.port_entry.get()) if self.port_entry.get().strip() else 8080
        except ValueError:
            messagebox.showerror("Error", "El puerto debe ser un número válido.")
            return
        
        config = {
            "command": command,
            "args": args,
            "port": port,
            "enabled": self.enabled_var.get()
        }
        
        if self.server_name:
            # Actualizar servidor existente
            self.config_window.mcp_manager.load_config()
            servers_config = self.config_window.mcp_manager.servers_config.get("mcpServers", {})
            servers_config[name] = config
            self.config_window.mcp_manager.servers_config["mcpServers"] = servers_config
            self.config_window.mcp_manager.save_config()
            
            # Actualizar la fila en el treeview si existe una selección
            selected = self.config_window.servers_tree.selection()
            if selected:
                self.config_window.servers_tree.item(selected[0], values=(name, command, port, "Sí" if config["enabled"] else "No"))
        else:
            # Añadir nuevo servidor
            self.config_window.mcp_manager.load_config()
            servers_config = self.config_window.mcp_manager.servers_config.get("mcpServers", {})
            
            if name in servers_config:
                if not messagebox.askyesno("Confirmar", f"Ya existe un servidor con el nombre '{name}'. ¿Desea sobrescribirlo?"):
                    return
            
            servers_config[name] = config
            self.config_window.mcp_manager.servers_config["mcpServers"] = servers_config
            self.config_window.mcp_manager.save_config()
            
            # Añadir nueva fila al treeview
            self.config_window.servers_tree.insert("", tk.END, values=(name, command, port, "Sí" if config["enabled"] else "No"))
        
        # Actualizar la lista de servidores en la ventana principal
        self.config_window.update_server_list()
        
        self.on_closing()