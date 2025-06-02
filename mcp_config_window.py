import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import json
import os
from ui_helpers import create_standard_dialog
import tkinter as tk

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
        self.geometry("600x400")
        self.resizable(True, True)

        # Crear UI
        self.create_ui()
        
        # Cargar configuración actual
        self.load_current_config()
    
    def create_ui(self):
        """Crea la interfaz de usuario."""
        # Frame principal con scroll
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Treeview para mostrar servidores
        self.servers_tree = ttk.Treeview(main_frame, columns=("Nombre", "Comando", "Puerto", "Habilitado"), show="headings")
        self.servers_tree.heading("Nombre", text="Nombre")
        self.servers_tree.heading("Comando", text="Comando")
        self.servers_tree.heading("Puerto", text="Puerto")
        self.servers_tree.heading("Habilitado", text="Habilitado")
        self.servers_tree.column("Nombre", width=100)
        self.servers_tree.column("Comando", width=200)
        self.servers_tree.column("Puerto", width=50)
        self.servers_tree.column("Habilitado", width=70)
        self.servers_tree.pack(fill=tk.BOTH, expand=True)
        
        # Botones de acción
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Añadir", command=self.add_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Editar", command=self.edit_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Eliminar", command=self.delete_server).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Probar Conexión", command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Guardar", command=self.save_config).pack(side=tk.RIGHT, padx=5)
        
    def load_current_config(self):
        """Carga la configuración actual de servidores MCP."""
        self.servers = self.mcp_manager.servers_config.get("mcpServers", {})
        for name, config in self.servers.items():
            self.servers_tree.insert("", tk.END, values=(
                name,
                config.get("command", ""),
                config.get("port", ""),
                "Sí" if config.get("enabled", True) else "No"
            ))
    
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
        AddServerDialog(self, self, server_name, self.servers[server_name])

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
            if server_name in self.servers:
                del self.servers[server_name]
    
    def test_connection(self):
        """Prueba la conexión al servidor seleccionado."""
        selected = self.servers_tree.selection()
        if not selected:
            messagebox.showwarning("Probar Conexión", "Por favor, seleccione un servidor para probar la conexión.")
            return
        
        item = self.servers_tree.item(selected[0])
        server_name = item["values"][0]
        config = self.servers[server_name]
        
        # Obtener la URL del servidor
        if "path" in config:
            server_url = config["path"]
        elif "port" in config:
            server_url = f"http://localhost:{config['port']}"
        else:
            messagebox.showerror("Error", "No se pudo determinar la URL del servidor.")
            return
        
        try:
            import requests
            # Probar conexión al endpoint /capabilities
            url = f"{server_url.rstrip('/')}/capabilities"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                capabilities = response.json()
                status = "Activo"
                message = f"Servidor MCP '{server_name}' está activo y disponible.\n\nCapacidades:\n{json.dumps(capabilities, indent=2)}"
            else:
                status = "Inactivo"
                message = f"El servidor MCP '{server_name}' no respondió correctamente.\nEstado: {response.status_code} {response.reason}"
        except requests.exceptions.ConnectionError:
            status = "Error"
            message = f"No se pudo conectar con el servidor MCP '{server_name}'.\nEl servidor no está respondiendo."
        except Exception as e:
            status = "Error"
            message = f"Ocurrió un error al probar la conexión con el servidor MCP '{server_name}':\n{str(e)}"
        
        # Mostrar resultado
        title = f"Estado del Servidor MCP: {status}"
        messagebox.showinfo(title, message)
    
    def save_config(self):
        """Guarda la configuración actual."""
        # Actualizar la configuración en el MCPManager
        self.mcp_manager.servers_config["mcpServers"] = self.servers
        
        # Guardar en archivo
        config_path = self.mcp_manager.get_default_config_path()
        try:
            with open(config_path, 'w') as f:
                json.dump(self.mcp_manager.servers_config, f, indent=2)
            
            # Recargar la configuración y reiniciar los servidores
            self.mcp_manager.load_config()
            self.mcp_manager.stop_all_servers()
            self.mcp_manager.start_all_servers()
            
            messagebox.showinfo("Guardar Configuración", "Configuración guardada y servidores reiniciados correctamente.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar la configuración: {e}")

class AddServerDialog:
    """
    Diálogo para añadir o editar un servidor MCP.
    """
    def __init__(self, parent, config_window, server_name=None, server_config=None):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Ventana padre
            config_window: Instancia de MCPConfigWindow
            server_name: Nombre del servidor (para edición)
            server_config: Configuración del servidor (para edición)
        """
        self.parent = parent
        self.config_window = config_window
        self.server_name = server_name
        self.server_config = server_config or {}
        
        # Crear ventana de diálogo
        title = "Editar Servidor" if server_name else "Añadir Servidor"
        self.dialog = create_standard_dialog(parent, title, "400x300")
        
        # Crear UI
        self.create_ui()
    
    def create_ui(self):
        """Crea la interfaz de usuario."""
        frame = ttk.Frame(self.dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Nombre del servidor
        ttk.Label(frame, text="Nombre:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(frame, width=40)
        self.name_entry.grid(row=0, column=1, pady=5)
        if self.server_name:
            self.name_entry.insert(0, self.server_name)
        
        # Comando
        ttk.Label(frame, text="Comando:").grid(row=1, column=0, sticky="w", pady=5)
        self.command_entry = ttk.Entry(frame, width=40)
        self.command_entry.grid(row=1, column=1, pady=5)
        self.command_entry.insert(0, self.server_config.get("command", ""))
        
        # Argumentos
        ttk.Label(frame, text="Argumentos:").grid(row=2, column=0, sticky="w", pady=5)
        self.args_text = tk.Text(frame, height=4, width=30)
        self.args_text.grid(row=2, column=1, pady=5)
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
        ttk.Button(btn_frame, text="Cancelar", command=self.dialog.destroy).pack(side=tk.LEFT, padx=5)
    
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
            self.config_window.servers[self.server_name] = config
            # Actualizar la fila en el treeview
            item = self.config_window.servers_tree.selection()[0]
            self.config_window.servers_tree.item(item, values=(name, command, port, "Sí" if config["enabled"] else "No"))
        else:
            # Añadir nuevo servidor
            if name in self.config_window.servers:
                if not messagebox.askyesno("Confirmar", f"Ya existe un servidor con el nombre '{name}'. ¿Desea sobrescribirlo?"):
                    return
            self.config_window.servers[name] = config
            # Añadir nueva fila al treeview
            self.config_window.servers_tree.insert("", tk.END, values=(name, command, port, "Sí" if config["enabled"] else "No"))
        
        self.dialog.destroy()

