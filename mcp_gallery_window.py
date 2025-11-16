"""
Interfaz gráfica para la Galería de Servidores MCP
Ventana Tkinter que permite navegar, instalar y gestionar servidores MCP.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import requests
import io
import threading
from typing import Dict
from mcp_gallery_manager import MCPGalleryManager


class MCPGalleryWindow:
    def __init__(self, parent_window=None, config_dir=None, parent=None, mcp_manager=None, app_config=None, chat_app=None):
        """
        Inicializa la ventana de la galería MCP.
        
        Args:
            parent_window: Ventana padre (opcional)
            config_dir: Directorio de configuración personalizado
            parent: Ventana padre alternativa (para compatibilidad)
            mcp_manager: Instancia de MCPManager (opcional)
            app_config: Configuración de la aplicación (opcional)
            chat_app: Aplicación principal (opcional)
        """
        # Compatibilidad con diferentes formas de pasar parent
        self.parent = parent if parent is not None else parent_window
        self.parent_window = parent_window if parent_window is not None else parent
        
        # Usar mcp_manager pasado o crear uno nuevo
        if mcp_manager:
            self.gallery_manager = MCPGalleryManager(config_dir, mcp_manager=mcp_manager)
        else:
            self.gallery_manager = MCPGalleryManager(config_dir)
            
        self.app_config = app_config
        self.chat_app = chat_app
        self.logger = self.gallery_manager.logger  # Acceso al logger
        
        # Variables de estado
        self.servers_data = []
        self.filtered_servers = []
        self.server_cards = {}
        self.icons_cache = {}
        
        self._create_window()
        self._create_widgets()
        self._load_servers()
    
    def _create_window(self):
        """Crea y configura la ventana principal."""
        self.window = tk.Toplevel(self.parent_window) if self.parent_window else tk.Tk()
        self.window.title("Galería de Servidores MCP")
        self.window.geometry("900x700")
        self.window.minsize(800, 600)
        
        # Configurar el tema
        self.window.configure(bg='#f9f9f9')
        
        # Centrar en pantalla
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (self.window.winfo_width() // 2)
        y = (self.window.winfo_screenheight() // 2) - (self.window.winfo_height() // 2)
        self.window.geometry(f"+{x}+{y}")
        
        # Configurar el icono (si existe)
        try:
            # Intentar cargar icono desde assets
            icon_path = "assets/icons/mcp_gallery.ico"
            self.window.iconbitmap(icon_path)
        except (tk.TclError, FileNotFoundError, OSError):
            pass  # Ignorar si no existe el icono
    
    def _create_widgets(self):
        """Crea todos los widgets de la interfaz."""
        
        # === HEADER ===
        header_frame = tk.Frame(self.window, bg='#2c3e50', height=80)
        header_frame.pack(fill='x', padx=0, pady=0)
        header_frame.pack_propagate(False)
        
        # Título
        title_label = tk.Label(
            header_frame, 
            text="🧩 Galería de Servidores MCP",
            font=('Segoe UI', 18, 'bold'),
            fg='white',
            bg='#2c3e50'
        )
        title_label.pack(side='left', padx=20, pady=20)
        
        # Botón refresh a la derecha
        refresh_btn = tk.Button(
            header_frame,
            text="🔄 Actualizar",
            font=('Segoe UI', 10),
            command=self._refresh_servers,
            bg='#3498db',
            fg='white',
            relief='flat',
            padx=15,
            pady=5
        )
        refresh_btn.pack(side='right', padx=20, pady=25)
        
        # === BARRA DE BÚSQUEDA ===
        search_frame = tk.Frame(self.window, bg='#f9f9f9')
        search_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            search_frame, 
            text="🔍 Buscar:",
            font=('Segoe UI', 10),
            bg='#f9f9f9'
        ).pack(side='left')
        
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self._on_search_change)
        
        self.search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Segoe UI', 10),
            width=40
        )
        self.search_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        # === ÁREA DE CONTENIDO CON SCROLL ===
        self._create_scrollable_area()
        
        # === STATUS BAR ===
        self.status_frame = tk.Frame(self.window, bg='#ecf0f1', height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Listo",
            font=('Segoe UI', 9),
            bg='#ecf0f1',
            fg='#2c3e50'
        )
        self.status_label.pack(side='left', padx=10, pady=5)
    
    def _create_scrollable_area(self):
        """Crea el área de scroll para las tarjetas de servidores."""
        
        # Frame contenedor principal
        main_frame = tk.Frame(self.window, bg='#f9f9f9')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Canvas y scrollbar
        self.canvas = tk.Canvas(main_frame, bg='#f9f9f9', highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient='vertical', command=self.canvas.yview)
        
        self.scrollable_frame = tk.Frame(self.canvas, bg='#f9f9f9')
        
        # Configurar scroll
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all'))
        )
        
        # Crear window en canvas y configurar para que se expanda horizontalmente
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Configurar ancho del scrollable_frame para que coincida con el canvas
        def _configure_scroll_region(event=None):
            self.canvas.configure(scrollregion=self.canvas.bbox('all'))
            # Hacer que el scrollable_frame tenga el mismo ancho que el canvas
            canvas_width = self.canvas.winfo_width()
            if canvas_width > 1:  # Solo si el canvas tiene un tamaño válido
                self.canvas.itemconfig(self.canvas_window, width=canvas_width)
        
        self.canvas.bind('<Configure>', _configure_scroll_region)
        self.scrollable_frame.bind('<Configure>', _configure_scroll_region)
        
        # Pack components
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Bind mouse wheel
        self._bind_mousewheel()
    
    def _bind_mousewheel(self):
        """Configura el scroll con la rueda del ratón."""
        def _on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        def _bind_to_mousewheel(event):
            self.canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        def _unbind_from_mousewheel(event):
            self.canvas.unbind_all("<MouseWheel>")
        
        self.canvas.bind('<Enter>', _bind_to_mousewheel)
        self.canvas.bind('<Leave>', _unbind_from_mousewheel)
    
    def _load_servers(self):
        """Carga los servidores disponibles desde la API."""
        self._update_status("Cargando servidores...")
        
        print("[DEBUG] _load_servers iniciado")
        
        def load_in_thread():
            try:
                print("[DEBUG] Iniciando fetch_available_servers...")
                self.servers_data = self.gallery_manager.fetch_available_servers()
                print(f"[DEBUG] Servidores obtenidos: {len(self.servers_data)}")
                print("[DEBUG] Programando callback _on_servers_loaded...")
                self.window.after(0, self._on_servers_loaded)
                print("[DEBUG] Callback programado")
            except Exception as e:
                print(f"[DEBUG] Error en load_in_thread: {e}")
                import traceback
                traceback.print_exc()
                self.window.after(0, lambda: self._show_error(f"Error cargando servidores: {e}"))
        
        print("[DEBUG] Iniciando thread...")
        # Intentar carga síncrona primero para debug
        try:
            print("[DEBUG] Intentando carga síncrona...")
            self.servers_data = self.gallery_manager.fetch_available_servers()
            print(f"[DEBUG] Carga síncrona exitosa: {len(self.servers_data)} servidores")
            self._on_servers_loaded()
        except Exception as e:
            print(f"[DEBUG] Carga síncrona falló: {e}")
            # Si falla la síncrona, intentar asíncrona
            threading.Thread(target=load_in_thread, daemon=True).start()
    
    def _on_servers_loaded(self):
        """Callback cuando se cargan los servidores."""
        print("[DEBUG] _on_servers_loaded llamado")
        print(f"[DEBUG] servers_data tiene {len(self.servers_data)} elementos")
        
        self.filtered_servers = self.servers_data.copy()
        print(f"[DEBUG] filtered_servers copiado: {len(self.filtered_servers)} elementos")
        
        print("[DEBUG] Iniciando _render_server_cards...")
        self._render_server_cards()
        print("[DEBUG] _render_server_cards completado")
        
        self._update_status(f"Cargados {len(self.servers_data)} servidores")
        print(f"[DEBUG] Status actualizado: Cargados {len(self.servers_data)} servidores")
    
    def _render_server_cards(self):
        """Renderiza las tarjetas de servidores en la interfaz."""
        print("[DEBUG] _render_server_cards iniciado")
        
        # Limpiar tarjetas existentes
        print("[DEBUG] Limpiando widgets existentes...")
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.server_cards.clear()
        print("[DEBUG] Widgets limpiados")
        
        if not self.filtered_servers:
            print("[DEBUG] No hay servidores filtrados, mostrando mensaje")
            no_results_label = tk.Label(
                self.scrollable_frame,
                text="No se encontraron servidores",
                font=('Segoe UI', 12),
                bg='#f9f9f9',
                fg='#7f8c8d'
            )
            no_results_label.pack(pady=50)
            return
        
        print(f"[DEBUG] Creando {len(self.filtered_servers)} tarjetas...")
        # Crear tarjetas
        for i, server in enumerate(self.filtered_servers):
            # Obtener ID de manera robusta
            server_id = server.get('id') or server.get('name', f'server_{i}')
            print(f"[DEBUG] Creando tarjeta {i+1}/{len(self.filtered_servers)}: {server_id}")
            try:
                card = self._create_server_card(server, i)
                self.server_cards[server_id] = card
                print(f"[DEBUG] Tarjeta {server_id} creada exitosamente")
            except Exception as e:
                print(f"[DEBUG] Error creando tarjeta {server_id}: {e}")
                import traceback
                traceback.print_exc()
        
        print(f"[DEBUG] Todas las tarjetas creadas")
        
        # Forzar actualización del scroll region
        self.canvas.update_idletasks()
        bbox = self.canvas.bbox('all')
        self.canvas.configure(scrollregion=bbox)
        
        self.window.update_idletasks()
        print("[DEBUG] _render_server_cards completado")
    
    def _get_server_id(self, server: Dict) -> str:
        """Obtiene el ID del servidor de forma robusta."""
        return server.get('id') or server.get('name', 'unknown_server')
    
    def _create_server_card(self, server: Dict, index: int) -> tk.Frame:
        """
        Crea una tarjeta visual para un servidor MCP.
        
        Args:
            server: Datos del servidor
            index: Índice en la lista
            
        Returns:
            Frame de la tarjeta
        """
        # Frame principal de la tarjeta
        card_frame = tk.Frame(
            self.scrollable_frame,
            bg='white',
            relief='solid',
            bd=1,
            height=120  # Altura fija para asegurar espacio
        )
        card_frame.pack(fill='x', pady=5, padx=10, ipady=10)
        card_frame.pack_propagate(False)  # Mantener altura fija
        
        # Frame izquierdo para ícono
        left_frame = tk.Frame(card_frame, bg='white', width=60)
        left_frame.pack(side='left', padx=15, pady=10)
        left_frame.pack_propagate(False)
        
        # Ícono (placeholder por ahora, se carga async)
        icon_label = tk.Label(
            left_frame,
            text="📦",
            font=('Segoe UI', 24),
            bg='white'
        )
        icon_label.pack()
        
        # Frame central para información
        info_frame = tk.Frame(card_frame, bg='white')
        info_frame.pack(side='left', fill='both', expand=True, padx=10)
        
        # Nombre y versión
        title_frame = tk.Frame(info_frame, bg='white')
        title_frame.pack(fill='x', pady=(0, 5))
        
        # Limpiar y validar el nombre del servidor
        server_name = str(server.get('name', 'Servidor Desconocido')).strip()
        if not server_name:
            server_name = 'Servidor Desconocido'
        
        name_label = tk.Label(
            title_frame,
            text=server_name,
            font=('Segoe UI', 14, 'bold'),
            bg='white',
            fg='#2c3e50'
        )
        name_label.pack(side='left')
        
        # Limpiar y validar la versión
        server_version = str(server.get('version', '1.0.0')).strip()
        if not server_version:
            server_version = '1.0.0'
        
        version_label = tk.Label(
            title_frame,
            text=f"v{server_version}",
            font=('Segoe UI', 10),
            bg='white',
            fg='#7f8c8d'
        )
        version_label.pack(side='left', padx=(10, 0))
        
        # Descripción - limpiar y validar texto
        server_desc = str(server.get('description', 'Sin descripción disponible')).strip()
        if not server_desc:
            server_desc = 'Sin descripción disponible'
        
        desc_label = tk.Label(
            info_frame,
            text=server_desc,
            font=('Segoe UI', 10),
            bg='white',
            fg='#34495e',
            wraplength=400,
            justify='left'
        )
        desc_label.pack(fill='x', pady=(0, 5))
        
        # Tags - validar y limpiar
        tags_frame = tk.Frame(info_frame, bg='white')
        tags_frame.pack(fill='x', pady=(0, 5))
        
        # Obtener tags de forma segura
        server_tags = server.get('tags', [])
        if isinstance(server_tags, list):
            for tag in server_tags[:3]:  # Máximo 3 tags
                if tag and isinstance(tag, str) and tag.strip():
                    tag_text = str(tag).strip()
                    tag_label = tk.Label(
                        tags_frame,
                        text=f"#{tag_text}",
                        font=('Segoe UI', 8),
                        bg='#ecf0f1',
                        fg='#7f8c8d',
                        padx=6,
                        pady=2,
                        relief='solid',
                        bd=1
                    )
                    tag_label.pack(side='left', padx=(0, 5))
        
        # Frame derecho para botones - Mejorado layout
        right_frame = tk.Frame(card_frame, bg='#f8f9fa', relief='solid', bd=1)
        right_frame.pack(side='right', padx=10, pady=10, fill='y')
        
        # Configurar el ancho mínimo del frame
        right_frame.configure(width=160)
        right_frame.pack_propagate(False)  # Mantener el ancho fijo
        
        # Debug: Log información del frame
        server_id = self._get_server_id(server)
        print(f"[DEBUG] Frame derecho creado para {server_id}: configurado con width=160")
        
        # Determinar estado y botón
        status = self.gallery_manager.get_server_status(server)
        print(f"[DEBUG] Estado obtenido para {server_id}: {status}")
        self._create_action_button(right_frame, server, status)
        
        # Cargar ícono en background (deshabilitado por rendimiento)
        # self._load_server_icon(server, icon_label)
        
        return card_frame
    
    def _create_action_button(self, parent: tk.Frame, server: Dict, status: str):
        """Crea el botón de acción según el estado del servidor."""
        
        server_id = self._get_server_id(server)
        print(f"[DEBUG] _create_action_button llamado para {server_id} (estado: {status})")
        
        if status == "not_installed":
            btn_text = "Instalar"
            btn_color = "#27ae60"
            btn_command = lambda s=server: self._install_server(s)
        elif status == "update_available":
            btn_text = "Actualizar"  
            btn_color = "#f39c12"
            btn_command = lambda s=server: self._update_server(s)
        else:  # installed
            btn_text = "Instalado"
            btn_color = "#95a5a6"
            btn_command = lambda s=server: self._show_installed_options(s)

        print(f"[DEBUG] Creando botón '{btn_text}' con color {btn_color}")
        
        # Botón principal con tamaño fijo
        action_btn = tk.Button(
            parent,
            text=btn_text,
            font=('Segoe UI', 10, 'bold'),
            bg=btn_color,
            fg='white',
            relief='flat',
            width=12,  # Ancho en caracteres
            height=2,  # Alto en líneas
            command=btn_command,
            cursor='hand2',
            activebackground=btn_color,
            activeforeground='white'
        )
        action_btn.pack(pady=(5, 5), padx=5, fill='x')
        
        print(f"[DEBUG] Botón principal '{btn_text}' empaquetado")
        
        # Botón de detalles con tamaño fijo
        details_btn = tk.Button(
            parent,
            text="Detalles",
            font=('Segoe UI', 9),
            bg='#ecf0f1',
            fg='#2c3e50',
            relief='flat',
            width=12,
            height=1,
            command=lambda s=server: self._show_server_details(s),
            cursor='hand2'
        )
        details_btn.pack(pady=(0, 5), padx=5, fill='x')
        
        print(f"[DEBUG] Botón 'Detalles' empaquetado")
        
        # Debug: imprimir estado para verificar
        self.logger.info(f"Botón creado para {server_id}: {btn_text} (estado: {status})")
        print(f"[DEBUG] Finalizado _create_action_button para {server_id}")
    
    def _load_server_icon(self, server: Dict, icon_label: tk.Label):
        """Carga el ícono del servidor de forma asíncrona."""
        def load_icon():
            try:
                icon_url = server.get('icon', '')
                if not icon_url or icon_url in self.icons_cache:
                    return
                
                response = requests.get(icon_url, timeout=5)
                response.raise_for_status()
                
                # Procesar imagen
                image = Image.open(io.BytesIO(response.content))
                image = image.resize((40, 40), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                
                # Cachear y actualizar UI
                self.icons_cache[icon_url] = photo
                self.window.after(0, lambda: self._update_icon(icon_label, photo))
                
            except Exception as e:
                # Usar ícono por defecto si falla
                pass
        
        if server.get('icon'):
            threading.Thread(target=load_icon, daemon=True).start()
    
    def _update_icon(self, label: tk.Label, photo: ImageTk.PhotoImage):
        """Actualiza el ícono en la UI thread."""
        label.configure(image=photo, text="")
        label.image = photo  # Mantener referencia
    
    def _install_server(self, server: Dict):
        """Instala un servidor MCP."""
        def install():
            server_name = server.get('name', 'Servidor Desconocido')
            self._update_status(f"Instalando {server_name}...")
            success, message = self.gallery_manager.install_server(server)
            
            self.window.after(0, lambda: self._on_install_complete(success, message, server))
        
        threading.Thread(target=install, daemon=True).start()
    
    def _on_install_complete(self, success: bool, message: str, server: Dict):
        """Callback cuando completa la instalación."""
        if success:
            messagebox.showinfo("Instalación Exitosa", message)
            self._refresh_server_card(server)
        else:
            messagebox.showerror("Error de Instalación", message)
        
        self._update_status("Listo")
    
    def _update_server(self, server: Dict):
        """Actualiza un servidor MCP."""
        result = messagebox.askyesno(
            "Actualizar Servidor",
            f"¿Deseas actualizar {server['name']} a la versión {server['version']}?"
        )
        
        if result:
            self._install_server(server)  # La instalación sobrescribe la versión anterior
    
    def _show_installed_options(self, server: Dict):
        """Muestra opciones para servidores instalados."""
        server_name = server.get('name', 'Servidor Desconocido')
        
        # Crear ventana de diálogo simple
        dialog = tk.Toplevel(self.window)
        dialog.title("Servidor Instalado")
        dialog.geometry("400x200")
        dialog.transient(self.window)
        dialog.grab_set()
        
        # Centrar en pantalla
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Etiqueta principal
        info_label = tk.Label(
            dialog,
            text=f"{server_name} está instalado.",
            font=('Segoe UI', 12, 'bold'),
            bg='white'
        )
        info_label.pack(pady=(20, 30))
        
        # Frame para botones
        buttons_frame = tk.Frame(dialog, bg='white')
        buttons_frame.pack(pady=20)
        
        # Botón ver detalles
        details_btn = tk.Button(
            buttons_frame,
            text="ℹ️ Ver Detalles",
            font=('Segoe UI', 10, 'bold'),
            bg='#3498db',
            fg='white',
            relief='flat',
            width=15,
            height=2,
            command=lambda: (dialog.destroy(), self._show_server_details(server)),
            cursor='hand2'
        )
        details_btn.pack(side='left', padx=10)
        
        # Botón desinstalar
        uninstall_btn = tk.Button(
            buttons_frame,
            text="🗑️ Desinstalar",
            font=('Segoe UI', 10, 'bold'),
            bg='#e74c3c',
            fg='white',
            relief='flat',
            width=15,
            height=2,
            command=lambda: self._confirm_uninstall(server, dialog),
            cursor='hand2'
        )
        uninstall_btn.pack(side='left', padx=10)
        
        # Botón cancelar
        cancel_btn = tk.Button(
            buttons_frame,
            text="Cancelar",
            font=('Segoe UI', 10),
            bg='#95a5a6',
            fg='white',
            relief='flat',
            width=15,
            height=2,
            command=dialog.destroy,
            cursor='hand2'
        )
        cancel_btn.pack(side='left', padx=10)
    
    def _confirm_uninstall(self, server: Dict, dialog):
        """Confirma y procede con la desinstalación."""
        dialog.destroy()
        self._uninstall_server(server)
    
    def _uninstall_server(self, server: Dict):
        """Desinstala un servidor MCP."""
        def uninstall():
            server_name = server.get('name', 'Servidor Desconocido')
            server_id = self._get_server_id(server)
            self._update_status(f"Desinstalando {server_name}...")
            success, message = self.gallery_manager.uninstall_server(server_id)
            
            self.window.after(0, lambda: self._on_uninstall_complete(success, message, server))
        
        threading.Thread(target=uninstall, daemon=True).start()
    
    def _on_uninstall_complete(self, success: bool, message: str, server: Dict):
        """Callback cuando completa la desinstalación."""
        if success:
            messagebox.showinfo("Desinstalación Exitosa", message)
            self._refresh_server_card(server)
        else:
            messagebox.showerror("Error de Desinstalación", message)
        
        self._update_status("Listo")
    
    def _refresh_server_card(self, server: Dict):
        """Refresca una tarjeta específica de servidor."""
        server_id = self._get_server_id(server)
        # Buscar el índice del servidor
        for i, srv in enumerate(self.filtered_servers):
            srv_id = self._get_server_id(srv)
            if srv_id == server_id:
                # Recrear la tarjeta
                old_card = self.server_cards.get(server_id)
                if old_card:
                    old_card.destroy()
                
                # Crear nueva tarjeta en la misma posición
                new_card = self._create_server_card(server, i)
                self.server_cards[server_id] = new_card
                break
    
    def _show_server_details(self, server: Dict):
        """Muestra una ventana con detalles del servidor."""
        server_name = server.get('name', 'Servidor Desconocido')
        
        details_window = tk.Toplevel(self.window)
        details_window.title(f"Detalles: {server_name}")
        details_window.geometry("500x400")
        details_window.resizable(False, False)
        
        # Centrar ventana
        details_window.transient(self.window)
        details_window.grab_set()
        
        # Contenido
        text_widget = tk.Text(
            details_window,
            wrap='word',
            font=('Consolas', 10),
            padx=10,
            pady=10
        )
        text_widget.pack(fill='both', expand=True)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(details_window, command=text_widget.yview)
        scrollbar.pack(side='right', fill='y')
        text_widget.config(yscrollcommand=scrollbar.set)
        
        # Formatear detalles
        server_name = server.get('name', 'Servidor Desconocido')
        server_id = self._get_server_id(server)
        details_text = f"""SERVIDOR MCP: {server_name}

ID: {server_id}
Versión: {server.get('version', '1.0.0')}
Descripción: {server.get('description', 'Sin descripción disponible')}

Tags: {', '.join(server.get('tags', []))}

URLs:
  Manifest: {server.get('manifest_url', 'N/A')}
  Ícono: {server.get('icon', 'N/A')}
  Firma: {server.get('signature_url', 'N/A')}

Seguridad:
  Checksum: {server.get('checksum', 'N/A')}
  Versión mínima del cliente: {server.get('min_client_version', 'N/A')}

Estado: {self.gallery_manager.get_server_status(server)}
"""
        
        text_widget.insert('1.0', details_text)
        text_widget.config(state='disabled')
    
    def _on_search_change(self, *args):
        """Maneja cambios en la búsqueda."""
        search_term = self.search_var.get().lower()
        
        if not search_term:
            self.filtered_servers = self.servers_data.copy()
        else:
            self.filtered_servers = [
                server for server in self.servers_data
                if (search_term in server['name'].lower() or
                    search_term in server['description'].lower() or
                    any(search_term in tag.lower() for tag in server.get('tags', [])))
            ]
        
        self._render_server_cards()
        self._update_status(f"Mostrando {len(self.filtered_servers)} de {len(self.servers_data)} servidores")
    
    def _refresh_servers(self):
        """Refresca la lista de servidores desde la API."""
        self._update_status("Actualizando...")
        self._load_servers()
    
    def _update_status(self, message: str):
        """Actualiza el mensaje de estado."""
        self.status_label.config(text=message)
        self.window.update_idletasks()
    
    def _show_error(self, message: str):
        """Muestra un error al usuario."""
        messagebox.showerror("Error", message)
        self._update_status("Error")
    
    def show(self):
        """Muestra la ventana de la galería."""
        self.window.lift()
        self.window.focus_force()


def main():
    """Función principal para ejecutar la galería de forma independiente."""
    gallery = MCPGalleryWindow()
    gallery.show()
    gallery.window.mainloop()


if __name__ == "__main__":
    main()