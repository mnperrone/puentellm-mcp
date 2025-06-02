import customtkinter as ctk
from assets.logging import PersistentLogger
import tkinter as tk

# Helpers para mostrar mensajes y actualizar la UI

def display_message(chat_text, message, tag, new_line_before_message=False, new_line_after_message=True, is_chunk_of_assistant_response=False):
    """
    Muestra un mensaje en el chat con el formato adecuado y crea el tag si no existe.
    Args:
        chat_text: Widget CTkTextbox donde mostrar el mensaje
        message (str): Mensaje a mostrar
        tag (str): Etiqueta para colorear el mensaje
        new_line_before_message (bool): Añadir salto de línea antes del mensaje
        new_line_after_message (bool): Añadir salto de línea después del mensaje
        is_chunk_of_assistant_response (bool): Si es un chunk parcial del asistente
    """
    try:
        if not chat_text or not hasattr(chat_text, 'winfo_exists') or not chat_text.winfo_exists():
            print(f"[ERROR] No se puede mostrar mensaje: Widget chat_text no válido")
            return
        # Validar que el tag exista
        if tag not in chat_text.tag_names():
            if tag == "user":
                chat_text.tag_config("user", foreground="#2ecc71")
            elif tag == "assistant":
                chat_text.tag_config("assistant", foreground="#3498db")
            elif tag == "loading":
                chat_text.tag_config("loading", foreground="#7f8c8d")
            elif tag == "error":
                chat_text.tag_config("error", foreground="#e74c3c")
            elif tag == "system":
                chat_text.tag_config("system", foreground="#f39c12")
            elif tag == "mcp_comm":
                chat_text.tag_config("mcp_comm", foreground="#8e44ad")
            elif tag == "mcp_stdout_log":
                chat_text.tag_config("mcp_stdout_log", foreground="#616A6B")
            elif tag == "mcp_stderr_log":
                chat_text.tag_config("mcp_stderr_log", foreground="#A93226")
            else:
                chat_text.tag_config(tag, foreground="#000000")
        # Manejo de saltos de línea
        if new_line_before_message:
            chat_text.insert(ctk.END, "\n", tag)
        chat_text.configure(state='normal')
        chat_text.insert(ctk.END, message, tag)
        if new_line_after_message:
            chat_text.insert(ctk.END, "\n", tag)
        chat_text.configure(state='disabled')
        chat_text.see(ctk.END)
    except Exception as e:
        print(f"[ERROR] display_message: {e}")

def log_to_chat_on_ui_thread(window, chat_text, message, tag):
    try:
        if window.winfo_exists():
            window.after(0, display_message, chat_text, message, tag, True)
    except Exception:
        pass

def create_standard_dialog(parent, title, size="400x300"):
    """
    Crea un diálogo estándar con configuración común.
    
    Args:
        parent: Ventana padre
        title: Título del diálogo
        size: Tamaño del diálogo (anchoxalto)
    
    Returns:
        La ventana de diálogo creada
    """
    dialog = tk.Toplevel(parent)
    dialog.title(title)
    dialog.geometry(size)
    dialog.resizable(True, True)
    
    # Centrar el diálogo en la ventana principal
    if parent and hasattr(parent, 'winfo_rootx') and hasattr(parent, 'winfo_rooty'):
        x = parent.winfo_rootx() + (parent.winfo_width() // 2) - (int(size.split('x')[0]) // 2)
        y = parent.winfo_rooty() + (parent.winfo_height() // 2) - (int(size.split('x')[1]) // 2)
        dialog.geometry(f"+{x}+{y}")
    
    # Hacer que el diálogo sea modal
    dialog.transient(parent)
    dialog.grab_set()
    
    return dialog
