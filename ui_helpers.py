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


def show_error_with_details(parent, title, short_message, details):
    """
    Show an error messagebox with a small dialog to view full details (traceback, logs).
    """
    try:
        # First show a short error message
        import tkinter.messagebox as messagebox
        messagebox.showerror(title, short_message, parent=parent)

        # Create a dialog with the details
        dialog = create_standard_dialog(parent, f"{title} - Detalles", size="700x400")
        dialog_frame = tk.Frame(dialog)
        dialog_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        text = tk.Text(dialog_frame, wrap=tk.NONE)
        text.insert(tk.END, details)
        text.configure(state=tk.DISABLED)
        text.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        # Scrollbars
        v = tk.Scrollbar(dialog_frame, orient=tk.VERTICAL, command=text.yview)
        h = tk.Scrollbar(dialog_frame, orient=tk.HORIZONTAL, command=text.xview)
        text.configure(yscrollcommand=v.set, xscrollcommand=h.set)
        v.pack(side=tk.RIGHT, fill=tk.Y)
        h.pack(side=tk.BOTTOM, fill=tk.X)

        # Buttons
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(fill=tk.X, padx=6, pady=6)

        def copy_and_close():
            try:
                parent.clipboard_clear()
                parent.clipboard_append(details)
            except Exception:
                pass
            dialog.destroy()

        copy_btn = ctk.CTkButton(btn_frame, text="Copiar detalles", command=copy_and_close)
        copy_btn.pack(side=tk.RIGHT, padx=6)

        close_btn = ctk.CTkButton(btn_frame, text="Cerrar", command=dialog.destroy)
        close_btn.pack(side=tk.RIGHT)

    except Exception as e:
        # Fall back to a simple messagebox if anything fails
        try:
            import tkinter.messagebox as messagebox
            messagebox.showerror(title, f"{short_message}\n(Además, error al mostrar detalles: {e})", parent=parent)
        except Exception:
            print(f"{title}: {short_message}\nDetails:\n{details}")
