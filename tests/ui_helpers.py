import tkinter as tk
from puentellm_mcp_assets.logging import setup_logging

# Configurar el logger
logger = setup_logging()

# Diccionario para mantener referencias a las imágenes (para evitar que se recolecten por el garbage collector)
image_references = {}

def display_message(chat_text, message, tag, new_line_before_message=True, is_chunk_of_assistant_response=False):
    """
    Muestra un mensaje en el área de chat con el formato adecuado.
    
    Args:
        chat_text: Widget CTkTextbox donde se mostrará el mensaje
        message: Contenido del mensaje
        tag: Etiqueta de estilo ('user', 'assistant', 'loading', 'error', 'system', 'mcp_comm')
        new_line_before_message: Si True, añade una nueva línea antes del mensaje
        is_chunk_of_assistant_response: Si True, indica que es un fragmento de respuesta del asistente
    """
    if not chat_text.winfo_exists(): return
    try:
        chat_text.configure(state='normal')
        current_content_end = chat_text.index('end-1c')
        
        # Añadir una nueva línea si es necesario
        if new_line_before_message and current_content_end != '1.0':
            if chat_text.get(f"{current_content_end} linestart", current_content_end).strip() != "":
                chat_text.insert(tk.END, "\n")
        
        # Determinar el prefijo según la etiqueta y tipo de mensaje
        prefix = ""
        if tag == "assistant" and is_chunk_of_assistant_response:
            prefix = "Ollama: "
        elif not is_chunk_of_assistant_response:
            if tag == "user": 
                prefix = "Tú: "
            elif tag == "assistant": 
                prefix = "Ollama: " 
            elif tag == "system": 
                prefix = "Sistema: "
            elif tag == "error": 
                prefix = "App Error: "
            elif tag in ["mcp_stdout_log", "mcp_stderr_log"]:
                prefix = ""  # Sin prefijo para logs MCP
        
        # Insertar el mensaje con su prefijo
        chat_text.insert(tk.END, f"{prefix}{message}", tag)
        
        # Añadir salto de línea adicional si no es un fragmento de respuesta
        if not is_chunk_of_assistant_response:
            chat_text.insert(tk.END, "\n\n", tag)
        
        chat_text.configure(state='disabled')
        chat_text.see(tk.END)
        
        # Registrar el mensaje en los logs
        log_tag = {
            "user": "usuario",
            "assistant": "asistente",
            "loading": "cargando",
            "error": "error",
            "system": "sistema",
            "mcp_comm": "comunicación MCP",
            "mcp_stdout_log": "log MCP stdout",
            "mcp_stderr_log": "log MCP stderr"
        }.get(tag, tag)
        
        logger.info(f"[{log_tag}] {prefix}{message}")
        
    except Exception as e:
        logger.error(f"Error al mostrar mensaje en UI: {e}", exc_info=True)

def log_to_chat_on_ui_thread(window, chat_text, message, tag="system"):
    """
    Registra un mensaje en el chat desde el hilo principal de la UI.
    
    Args:
        window: Ventana principal de la aplicación
        chat_text: Widget CTkTextbox para mostrar mensajes
        message: Contenido del mensaje
        tag: Etiqueta de estilo ('user', 'assistant', 'loading', 'error', 'system', 'mcp_comm')
    """
    try:
        if window.winfo_exists():
            window.after(0, display_message, chat_text, message, tag, True)
            
        # Registrar el mensaje en los logs
        log_tag = {
            "user": "usuario",
            "assistant": "asistente",
            "loading": "cargando",
            "error": "error",
            "system": "sistema",
            "mcp_comm": "comunicación MCP",
            "mcp_stdout_log": "log MCP stdout",
            "mcp_stderr_log": "log MCP stderr"
        }.get(tag, tag)
        
        logger.info(f"[log_to_chat] [{log_tag}] {message}")
        
    except Exception as e:
        logger.error(f"Error al registrar mensaje en log: {e}", exc_info=True)

def update_server_status_icon(icon_label, status="active"):
    """
    Actualiza el icono de estado de un servidor MCP.
    
    Args:
        icon_label: Label donde se mostrará el icono
        status: Estado del servidor ('active', 'inactive', 'error', 'loading')
    """
    try:
        # Ruta relativa a los iconos de estado
        icon_path = Path(__file__).parent / "assets" / "icons" / "server_status"
        
        # Seleccionar el icono según el estado
        icon_file = {
            "active": "active.png",
            "inactive": "inactive.png",
            "error": "error.png",
            "loading": "loading.gif"
        }.get(status, "inactive.png")
        
        # Verificar si la imagen ya está cargada
        if icon_file in image_references:
            icon_image = image_references[icon_file]
        else:
            # Cargar la imagen
            icon_image = tk.PhotoImage(file=icon_path / icon_file)
            # Guardar una referencia para evitar que sea eliminada
            image_references[icon_file] = icon_image
        
        # Actualizar el label con el nuevo icono
        icon_label.configure(image=icon_image)
        icon_label.image = icon_image  # Mantener una referencia
        
        # Registrar la actualización en los logs
        logger.info(f"Icono de estado actualizado a '{status}'")
        
    except Exception as e:
        logger.error(f"Error al actualizar icono de estado: {e}", exc_info=True)
        # Usar un icono por defecto en caso de error
        icon_label.configure(image="")
        icon_label.image = None

def get_status_tooltip(status="active"):
    """
    Devuelve el texto del tooltip para un estado MCP específico.
    
    Args:
        status: Estado del servidor ('active', 'inactive', 'error', 'loading')
    """
    return {
        "active": "Servidor activo o en funcionamiento",
        "inactive": "Servidor inactivo o detenido",
        "error": "Servidor con errores o fallos",
        "loading": "Servidor en proceso de carga o inicialización"
    }.get(status, "Desconocido")

def setup_ui_with_persistent_logging(window, chat_text):
    """
    Configura la interfaz de usuario con soporte para logging persistente.
    
    Args:
        window: Ventana principal de la aplicación
        chat_text: Widget CTkTextbox para mostrar mensajes
    """
    try:
        # Configurar logging
        logger.info("Configurando UI con soporte para logging persistente")
        
        # Crear directorio para logs si no existe
        log_dir = Path.home() / '.puentellm-mcp' / 'test_logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializar configuración de logging persistente
        from puentellm_mcp_assets.logging import setup_persistent_logging
        persistent_logger = setup_persistent_logging(log_dir / 'ui_tests.log')
        
        # Extender funcionalidad de display_message para incluir logging
        original_display_message = globals()["display_message"]
        
        def extended_display_message(*args, **kwargs):
            # Llamar a la función original
            result = original_display_message(*args, **kwargs)
            
            # Registrar en log persistente
            if len(args) >= 3:
                message = args[2] if isinstance(args[2], str) else str(args[2])
                tag = args[3] if len(args) > 3 and isinstance(args[3], str) else "unknown"
                logger.debug(f"[UI] [{tag}] {message}")
            
            return result
        
        # Reemplazar la función original con la extendida
        globals()["display_message"] = extended_display_message
        
        # Registrar éxito
        logger.info("UI configurada exitosamente con soporte para logging persistente")
        return True
        
    except Exception as e:
        logger.error(f"Error al configurar UI con logging persistente: {e}", exc_info=True)
        return False