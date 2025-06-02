import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import json

def prompt_tool_and_args(parent, tools, callback):
    """
    Muestra un diálogo para seleccionar una herramienta MCP y sus argumentos.
    Args:
        parent: Ventana padre.
        tools: Lista de herramientas disponibles (dict u objeto con 'name' y 'description').
        callback: Función a llamar con la herramienta seleccionada y sus argumentos.
    """
    dialog = ctk.CTkToplevel(parent)
    dialog.title("Seleccionar herramienta MCP")
    dialog.geometry("500x300")
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    main_frame = ctk.CTkFrame(dialog)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

    # Selector de herramienta
    tool_names = [t['name'] if isinstance(t, dict) else getattr(t, 'name', str(t)) for t in tools]
    tool_var = tk.StringVar(value=tool_names[0] if tool_names else "")
    ctk.CTkLabel(main_frame, text="Herramienta:").pack(anchor="w")
    tool_menu = ctk.CTkOptionMenu(main_frame, values=tool_names, variable=tool_var)
    tool_menu.pack(fill=tk.X, pady=5)

    # Campo de argumentos
    ctk.CTkLabel(main_frame, text="Argumentos (JSON):").pack(anchor="w", pady=(10,0))
    args_entry = ctk.CTkEntry(main_frame)
    args_entry.pack(fill=tk.X, pady=5)

    # Botones
    btn_frame = ctk.CTkFrame(main_frame)
    btn_frame.pack(fill=tk.X, pady=10)

    def on_ok():
        tool = tool_var.get()
        args_str = args_entry.get()
        try:
            args = json.loads(args_str) if args_str else {}
        except Exception as e:
            messagebox.showerror("Error", f"Argumentos JSON inválidos: {e}", parent=dialog)
            return
        dialog.destroy()
        callback(tool, args)

    def on_cancel():
        dialog.destroy()
        callback(None, None)

    ctk.CTkButton(btn_frame, text="Aceptar", command=on_ok).pack(side=tk.LEFT, padx=5)
    ctk.CTkButton(btn_frame, text="Cancelar", command=on_cancel).pack(side=tk.LEFT, padx=5)

    dialog.wait_window()
