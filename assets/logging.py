import os
import sys
import logging
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

class PersistentLogger:
    """
    Clase para registrar logs persistentes en archivo y mostrarlos en la interfaz de usuario.
    Combina el registro en archivo con la visualización en tiempo real en la aplicación.
    """
    
    def __init__(self, log_dir="logs", max_log_files=10):
        """
        Inicializa el sistema de logging persistente.
        
        Args:
            log_dir (str): Directorio donde se guardarán los archivos de log
            max_log_files (int): Número máximo de archivos de log a mantener
        """
        self.log_dir = log_dir
        self.max_log_files = max_log_files
        self.setup_logging()
        self.ui_log_widgets = []  # Lista de widgets donde mostrar los logs
        
    def setup_logging(self):
        """Configura el sistema de logging con rotación de archivos."""
        # Crear directorio de logs si no existe
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        
        # Limpiar logs antiguos si exceden el límite
        self.cleanup_old_logs()
        
        # Configurar el nombre del archivo de log actual
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"puentellm-mcp_{timestamp}.log"
        self.log_path = os.path.join(self.log_dir, log_filename)
        
        # Configurar el logging
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s [%(levelname)s] %(message)s',
            handlers=[
                logging.FileHandler(self.log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)  # Mantiene el logging estándar
            ]
        )
        
        self.logger = logging.getLogger('PuenteLLM-MCP')
        self.logger.info("Logger persistente iniciado. Archivo de log: %s", self.log_path)
    
    def cleanup_old_logs(self):
        """Limpia los archivos de log más antiguos si exceden el límite."""
        try:
            # Obtener lista de archivos de log ordenados por fecha de modificación
            log_files = [(os.path.getmtime(os.path.join(self.log_dir, f)), os.path.join(self.log_dir, f)) 
                        for f in os.listdir(self.log_dir) if f.endswith('.log')]
            log_files.sort()
            while len(log_files) > self.max_log_files:
                oldest_log = log_files.pop(0)[1]
                try:
                    os.remove(oldest_log)
                    print(f"Archivo de log antiguo eliminado: {oldest_log}")
                except Exception as e:
                    print(f"Error al eliminar archivo de log antiguo {oldest_log}: {str(e)}")
        except Exception as e:
            print(f"Error limpiando logs antiguos: {str(e)}")

    def get_current_log_path(self):
        """Devuelve la ruta del archivo de log actual."""
        return self.log_path
    
    def add_ui_log_widget(self, widget):
        """
        Añade un widget de UI donde se mostrarán los mensajes de log.
        
        Args:
            widget: Widget CTkTextbox u otro compatible donde mostrar los logs
        """
        if widget not in self.ui_log_widgets:
            self.ui_log_widgets.append(widget)
    
    def remove_ui_log_widget(self, widget):
        """Remueve un widget de UI para logging."""
        if widget in self.ui_log_widgets:
            self.ui_log_widgets.remove(widget)
    
    def log_to_ui(self, message, tag="system"):
        """
        Muestra un mensaje de log en todos los widgets de UI registrados.
        
        Args:
            message (str): Mensaje a mostrar
            tag (str): Etiqueta para colorear el mensaje (ej: 'system', 'error', 'loading', etc.)
        """
        for widget in self.ui_log_widgets:
            try:
                display_message(widget, message, tag, new_line_before_message=True)
            except Exception as e:
                self.logger.error("Error mostrando log en UI: %s", str(e))
    
    def debug(self, message, *args, **kwargs):
        """Registra un mensaje de nivel DEBUG."""
        self.logger.debug(message, *args, **kwargs)
        self.log_to_ui(f"DEBUG: {message % args if args else message}", "loading")
    
    def info(self, message, *args, **kwargs):
        """Registra un mensaje de nivel INFO."""
        self.logger.info(message, *args, **kwargs)
        self.log_to_ui(f"INFO: {message % args if args else message}", "system")
    
    def warning(self, message, *args, **kwargs):
        """Registra un mensaje de nivel WARNING."""
        self.logger.warning(message, *args, **kwargs)
        self.log_to_ui(f"WARNING: {message % args if args else message}", "system")
    
    def error(self, message, *args, **kwargs):
        """Registra un mensaje de nivel ERROR."""
        self.logger.error(message, *args, **kwargs)
        self.log_to_ui(f"ERROR: {message % args if args else message}", "error")
    
    def critical(self, message, *args, **kwargs):
        """Registra un mensaje de nivel CRITICAL."""
        self.logger.critical(message, *args, **kwargs)
        self.log_to_ui(f"CRITICAL: {message % args if args else message}", "error")
    
    def exception(self, message, *args, exc_info=True, **kwargs):
        """Registra una excepción."""
        self.logger.exception(message, *args, exc_info=exc_info, **kwargs)
        self.log_to_ui(f"EXCEPTION: {message % args if args else message}", "error")
    
    def log_to_chat(self, chat_text, message, tag="system"):
        """
        Registra un mensaje tanto en el log como en la interfaz de chat.
        
        Args:
            chat_text: Widget CTkTextbox del chat
            message (str): Mensaje a registrar
            tag (str): Etiqueta para colorear el mensaje
        """
        self.logger.info(message)
        try:
            display_message(chat_text, message, tag, new_line_before_message=True)
        except Exception as e:
            self.logger.error("Error mostrando mensaje en chat: %s", str(e))
    
    def show_log_viewer(self, parent_window):
        """
        Muestra un visor de logs en una ventana emergente.
        
        Args:
            parent_window: Ventana principal desde donde se muestra
        """
        viewer = ctk.CTkToplevel(parent_window)
        viewer.title("Visor de Logs - PuenteLLM-MCP")
        viewer.geometry("800x600")
        viewer.resizable(True, True)
        
        # Frame principal
        main_frame = ctk.CTkFrame(viewer)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_label = ctk.CTkLabel(main_frame, text="Registro de Actividad (Logs)", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 5))
        
        # Frame para botones de control
        control_frame = ctk.CTkFrame(main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 5))
        
        # Botón para seleccionar archivo de log
        select_btn = ctk.CTkButton(control_frame, text="Seleccionar Log", command=lambda: self.select_log_file(viewer, log_text))
        select_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para limpiar logs
        clear_btn = ctk.CTkButton(control_frame, text="Limpiar Logs", command=lambda: self.clear_logs(log_text))
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        # Botón para mostrar configuración
        config_btn = ctk.CTkButton(control_frame, text="Mostrar Configuración", command=lambda: self.show_config(log_text))
        config_btn.pack(side=tk.RIGHT, padx=5)
        
        # Botón para mostrar historial de logs
        history_btn = ctk.CTkButton(control_frame, text="Historial de Logs", command=lambda: self.show_log_history(log_text))
        history_btn.pack(side=tk.RIGHT, padx=5)
        
        # Cuadro de texto para mostrar logs
        log_text = ctk.CTkTextbox(main_frame, wrap=tk.NONE, state='disabled', font=("Courier New", 12))
        log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Scrollbars
        v_scrollbar = ctk.CTkScrollbar(main_frame, orientation="vertical", command=log_text.yview)
        h_scrollbar = ctk.CTkScrollbar(main_frame, orientation="horizontal", command=log_text.xview)
        
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        log_text.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Mostrar el contenido del log actual
        self.display_log_content(log_text, self.log_path)
    
    def select_log_file(self, parent, log_text):
        """
        Abre un diálogo para seleccionar y mostrar un archivo de log específico.
        
        Args:
            parent: Ventana padre para el diálogo
            log_text: Widget CTkTextbox donde mostrar el contenido
        """
        filepath = filedialog.askopenfilename(
            title="Seleccionar archivo de log",
            initialdir=self.log_dir,
            filetypes=(("Archivos de log", "*.log"), ("Todos los archivos", "*.*"))
        )
        if filepath and os.path.isfile(filepath):
            self.display_log_content(log_text, filepath)
    
    def display_log_content(self, log_text, filepath):
        """
        Muestra el contenido de un archivo de log en un widget de texto.
        
        Args:
            log_text: Widget CTkTextbox donde mostrar el contenido
            filepath (str): Ruta al archivo de log
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                content = file.read()
                log_text.configure(state='normal')
                log_text.delete('1.0', tk.END)
                log_text.insert(tk.END, content)
                log_text.configure(state='disabled')
                log_text.see(tk.END)
                
                # Aplicar colores según el nivel de log
                self.apply_log_colors(log_text)
        except Exception as e:
            self.logger.error("Error leyendo archivo de log: %s", str(e))
            log_text.configure(state='normal')
            log_text.delete('1.0', tk.END)
            log_text.insert(tk.END, f"Error leyendo archivo de log: {str(e)}")
            log_text.configure(state='disabled')
    
    def apply_log_colors(self, log_text):
        """
        Aplica colores diferentes a cada nivel de log en el widget de texto.
        
        Args:
            log_text: Widget CTkTextbox donde aplicar los colores
        """
        try:
            # Configurar tags para cada nivel de log
            log_text.tag_configure('debug', foreground='#7f8c8d')     # Gris
            log_text.tag_configure('info', foreground='#3498db')      # Azul
            log_text.tag_configure('warning', foreground='#f39c12')   # Naranja
            log_text.tag_configure('error', foreground='#e74c3c')     # Rojo
            log_text.tag_configure('critical', foreground='#c0392b')  # Rojo oscuro
            
            start_index = '1.0'
            while True:
                line = log_text.get(start_index, log_text.index(f'{start_index} lineend'))
                if not line:
                    break
                
                # Detectar nivel de log
                if '[DEBUG]' in line:
                    log_text.tag_add('debug', start_index, f'{start_index} lineend')
                elif '[INFO]' in line:
                    log_text.tag_add('info', start_index, f'{start_index} lineend')
                elif '[WARNING]' in line:
                    log_text.tag_add('warning', start_index, f'{start_index} lineend')
                elif '[ERROR]' in line or '[CRITICAL]' in line:
                    log_text.tag_add('error', start_index, f'{start_index} lineend')
                
                # Avanzar a la siguiente línea
                next_index = log_text.index(f'{start_index} + 1line')
                if next_index == start_index:
                    break
                start_index = next_index
        except Exception as e:
            self.logger.error("Error aplicando colores a logs: %s", str(e))
    
    def clear_logs(self, log_text=None):
        """Limpia todos los archivos de log y restablece el sistema de logging."""
        try:
            # Cerrar el manejador de archivo actual
            for handler in self.logger.handlers:
                if isinstance(handler, logging.FileHandler):
                    handler.close()
                    
            # Eliminar todos los archivos de log
            for filename in os.listdir(self.log_dir):
                if filename.endswith('.log'):
                    os.remove(os.path.join(self.log_dir, filename))
                    self.logger.info("Archivo de log eliminado: %s", filename)
            
            # Reiniciar el sistema de logging
            self.setup_logging()
            
            if log_text:
                log_text.configure(state='normal')
                log_text.delete('1.0', tk.END)
                log_text.insert(tk.END, "Logs limpiados exitosamente. Nuevo archivo de log creado.")
                log_text.configure(state='disabled')
                
            return True
        except Exception as e:
            self.logger.error("Error limpiando logs: %s", str(e))
            if log_text:
                log_text.configure(state='normal')
                log_text.delete('1.0', tk.END)
                log_text.insert(tk.END, f"Error limpiando logs: {str(e)}")
                log_text.configure(state='disabled')
            return False
    
    def show_log_history(self, log_text):
        """
        Muestra la historia de archivos de log disponibles.
        
        Args:
            log_text: Widget CTkTextbox donde mostrar la historia
        """
        try:
            log_files = sorted(
                [f for f in os.listdir(self.log_dir) if f.endswith('.log')],
                reverse=True
            )
            
            if not log_files:
                log_text.configure(state='normal')
                log_text.delete('1.0', tk.END)
                log_text.insert(tk.END, "No hay archivos de log previos.")
                log_text.configure(state='disabled')
                return
            
            log_text.configure(state='normal')
            log_text.delete('1.0', tk.END)
            log_text.insert(tk.END, "Archivos de log históricos encontrados:\n\n")
            
            for i, filename in enumerate(log_files):
                file_path = os.path.join(self.log_dir, filename)
                size = os.path.getsize(file_path)
                mod_time = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
                log_text.insert(tk.END, f"{i+1}. {filename} | Tamaño: {size/1024:.1f} KB | Última modificación: {mod_time}\n")
                
                # Hacer que sea clickable
                def create_callback(fp=file_path):
                    return lambda: self.display_log_content(log_text, fp)
                
                button = ctk.CTkButton(
                    log_text, 
                    text="Ver", 
                    width=50, 
                    height=20,
                    command=create_callback(),
                    font=("Arial", 10)
                )
                log_text.window_create(tk.END, window=button)
                log_text.insert(tk.END, '\n')
            
            log_text.configure(state='disabled')
        except Exception as e:
            self.logger.error("Error mostrando historia de logs: %s", str(e))
            if log_text:
                log_text.configure(state='normal')
                log_text.delete('1.0', tk.END)
                log_text.insert(tk.END, f"Error mostrando historia de logs: {str(e)}")
                log_text.configure(state='disabled')
    
    def show_config(self, log_text):
        """
        Muestra la configuración actual del sistema de logging.
        
        Args:
            log_text: Widget CTkTextbox donde mostrar la configuración
        """
        try:
            log_text.configure(state='normal')
            log_text.delete('1.0', tk.END)
            log_text.insert(tk.END, "Configuración Actual del Sistema de Logging\n\n")
            log_text.insert(tk.END, f"Directorio de logs: {self.log_dir}\n")
            log_text.insert(tk.END, f"Número máximo de archivos de log: {self.max_log_files}\n")
            log_text.insert(tk.END, f"Archivo de log actual: {os.path.basename(self.log_path)}\n")
            log_text.insert(tk.END, "\nNiveles de log habilitados:\n")
            log_text.insert(tk.END, "- DEBUG: Mensajes detallados para depuración\n")
            log_text.insert(tk.END, "- INFO: Información general sobre operaciones\n")
            log_text.insert(tk.END, "- WARNING: Advertencias que no impiden la ejecución\n")
            log_text.insert(tk.END, "- ERROR: Errores que afectan la funcionalidad\n")
            log_text.insert(tk.END, "- CRITICAL: Errores críticos que requieren atención inmediata\n")
            log_text.configure(state='disabled')
        except Exception as e:
            self.logger.error("Error mostrando configuración de logging: %s", str(e))
            if log_text:
                log_text.configure(state='normal')
                log_text.delete('1.0', tk.END)
                log_text.insert(tk.END, f"Error mostrando configuración de logging: {str(e)}")
                log_text.configure(state='disabled')

# Funciones auxiliares para integración con la aplicación principal
def setup_persistent_logging(chat_app):
    """
    Configura el logging persistente en la aplicación principal.
    
    Args:
        chat_app: Instancia de ChatApp
    """
    # Crear carpeta de logs si no existe
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    # Crear logger persistente
    logger = PersistentLogger(log_dir)
    
    # Agregar el chat_text como destino para los logs
    logger.add_ui_log_widget(chat_app.chat_text)
    
    # Reemplazar las funciones de logging en la aplicación
    original_logger = chat_app.mcp_manager.logger
    chat_app.mcp_manager.logger = lambda msg, tag: (logger.log_to_ui(msg, tag), original_logger(msg, tag))
    
    # Añadir opción al menú de la aplicación para ver logs
    def show_log_viewer():
        logger.show_log_viewer(chat_app.window)
    
    # Asegurarse de que exista el menú MCP
    if hasattr(chat_app, 'btn_mcp') and chat_app.btn_mcp:
        # Crear un submenú para opciones adicionales
        log_menu = ctk.CTkMenu(chat_app.window)
        log_menu.add_command(label="Ver Logs", command=show_log_viewer)
        log_menu.add_command(label="Limpiar Logs", command=lambda: logger.clear_logs())
        log_menu.add_command(label="Mostrar Configuración", command=lambda: logger.show_config(None))
        
        # Añadir opción al menú MCP
        def toggle_log_menu(event=None):
            try:
                log_menu.tk_popup(event.x_root, event.y_root, 0)
            finally:
                log_menu.grab_release()
        
        chat_app.btn_mcp.bind('<Button-3>', toggle_log_menu)  # Click derecho en botón MCP
        
    return logger

