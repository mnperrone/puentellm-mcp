import tkinter as tk
import customtkinter as ctk
import threading
import json
import os
import sys
from tkinter import filedialog, messagebox
from pathlib import Path
import time
from mcp_manager import MCPManager
from mcp_sdk_bridge import MCPSDKBridge
import asyncio
from ui_helpers import display_message, log_to_chat_on_ui_thread
from dialogs import prompt_tool_and_args
from llm_bridge import LLMBridge
from llm_mcp_handler import LLMMCPHandler
from app_config import AppConfig
import functools
import strictjson
from assets.logging import setup_persistent_logging

class ChatApp:
    def __init__(self):
        setup_persistent_logging()
        self.window = ctk.CTk()
        self.window.title("LLM - MCP Bridge Chat")
        self.window.geometry("800x600")
        self.window.resizable(True, True)
        try:
            icon_path = Path(__file__).parent / "assets" / "icons" / "icono.ico"
            if icon_path.exists():
                try:
                    self.window.iconbitmap(str(icon_path))
                except Exception as e:
                    print(f"[Advertencia] No se pudo establecer el icono: {e}")
            else:
                print(f"[Advertencia] El icono no existe en: {icon_path}")
        except Exception as e:
            print(f"[Advertencia] No se pudo cargar el icono: {e}")
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.tk_setPalette(
            background="#2c3e50",
            foreground="#ecf0f1",
            activeBackground="#34495e",
            activeForeground="#ecf0f1",
            highlightBackground="#2c3e50",
            highlightColor="#3498db",
            selectBackground="#3498db",
            selectForeground="#ecf0f1"
        )
        self.window.config(menu=None)
        self.ollama_thread = None
        self.ollama_stop_event = threading.Event()
        def _dummy_logger(*args, **kwargs):
            pass
        self.mcp_manager = MCPManager(_dummy_logger)
        self.config = AppConfig()
        self.llm_model = self.config.get('llm_model') or self.prompt_for_llm_model()
        self.config.set('llm_model', self.llm_model)
        self.ollama_response_started_flag = False
        self.assistant_response_active = False
        self.sdk_bridge = MCPSDKBridge()
        self.llm_bridge = None
        self.llm_mcp_handler = None

        self.persistent_logger = setup_persistent_logging(self)
        
        self.menu_frame = ctk.CTkFrame(self.window, height=40)
        self.menu_frame.pack(fill=tk.X, padx=0, pady=0)
        self.btn_mcp = ctk.CTkButton(self.menu_frame, text="MCP", width=80, command=self.toggle_mcp_menu)
        self.btn_llm = ctk.CTkButton(self.menu_frame, text="LLM", width=80, command=self.toggle_llm_menu)
        self.btn_mcp.pack(side=tk.LEFT, padx=(10,0), pady=5)
        self.btn_llm.pack(side=tk.LEFT, padx=(5,0), pady=5)
        self.mcp_menu_popup = None
        self.llm_menu_popup = None
        
        self.mcp_status_frame = ctk.CTkFrame(self.window, height=30)
        self.mcp_status_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        
        self.mcp_status_icon = ctk.CTkLabel(self.mcp_status_frame, text="⬤", font=("Arial", 20), width=20)
        self.mcp_status_icon.pack(side=tk.LEFT, padx=(10,5))
        
        self.mcp_status_label = ctk.CTkLabel(self.mcp_status_frame, text="MCPs: Cargando...", anchor="w", font=("Arial", 12))
        self.mcp_status_label.pack(side=tk.LEFT, padx=5)
        
        self.mcp_details_btn = ctk.CTkButton(self.mcp_status_frame, text="Detalles", width=60, command=self.show_mcp_details, font=("Arial", 10))
        self.mcp_details_btn.pack(side=tk.RIGHT, padx=10)
        
        self.base_font = ("Arial", 12)
        self.chat_text = ctk.CTkTextbox(self.window, wrap=tk.WORD, state='disabled', font=self.base_font)
        self.chat_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.input_frame = ctk.CTkFrame(self.window)
        self.input_entry = ctk.CTkEntry(self.input_frame, width=650, font=self.base_font) 
        self.send_btn = ctk.CTkButton(self.input_frame, text="Enviar", command=self.send_message)
        self.stop_btn = ctk.CTkButton(self.input_frame, text="Detener respuesta", command=self.stop_ollama_response)
        self.input_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        self.send_btn.pack(side=tk.LEFT, padx=5)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        self.input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        self.chat_text.tag_config("user", foreground="#2ecc71") 
        self.chat_text.tag_config("assistant", foreground="#3498db") 
        self.chat_text.tag_config("loading", foreground="#7f8c8d") 
        self.chat_text.tag_config("error", foreground="#e74c3c") 
        self.chat_text.tag_config("system", foreground="#f39c12") 
        self.chat_text.tag_config("mcp_comm", foreground="#8e44ad") 
        self.chat_text.tag_config("mcp_stdout_log", foreground="#616A6B") 
        self.chat_text.tag_config("mcp_stderr_log", foreground="#A93226") 

        self.input_entry.bind("<Return>", lambda event: self.send_message()); self.window.protocol("WM_DELETE_WINDOW", self.on_closing) 
        if self.mcp_manager.load_config(): self.start_all_mcp_servers_ui(auto_start=True)
        else: log_to_chat_on_ui_thread(self.window, self.chat_text, "No se pudo cargar config MCP. Usa menú 'MCP > Cargar...'", "error")
        self.update_mcp_status_label() 
        log_to_chat_on_ui_thread(self.window, self.chat_text, f"Bienvenido. LLM: {self.llm_model}. MCPs: {', '.join(self.mcp_manager.get_active_server_names()) or 'Ninguno' }.", "system")
        self.window.after(100, self.input_entry.focus_set)

        self.llm_bridge = LLMBridge(self.llm_model, self.chat_text, self.window)
        self.llm_mcp_handler = LLMMCPHandler(self.mcp_manager, self.sdk_bridge, self.window, self.chat_text)
        self.mcp_manager.logger = lambda msg, tag: (self.persistent_logger.log_to_ui(msg, tag), log_to_chat_on_ui_thread(self.window, self.chat_text, msg, tag))
        if self.llm_bridge:
            self.llm_bridge.chat_text = self.chat_text
            self.llm_bridge.window = self.window
        if self.llm_mcp_handler:
            self.llm_mcp_handler.window = self.window
            self.llm_mcp_handler.chat_text = self.chat_text

    def update_mcp_status_label(self):
        active_servers = self.mcp_manager.get_active_server_names()
        running_servers = [s for s in active_servers if self.mcp_manager.is_server_running(s)]
        inactive_servers = [s for s in active_servers if not self.mcp_manager.is_server_running(s)]
        
        total_active = len(active_servers)
        total_running = len(running_servers)
        total_inactive = len(inactive_servers)
        
        if total_active == 0:
            status_text = "No hay servidores MCP configurados. Use 'MCP > Configurar' para añadir servidores."
        elif total_running == total_active:
            status_text = f"Todos los servidores MCP están activos ({total_running}/{total_active})."
        elif total_inactive == total_active:
            status_text = "Todos los servidores MCP están inactivos."
        else:
            status_text = f"{total_running}/{total_active} servidores MCP activos. {total_inactive} inactivos."
        
        if total_active == 0:
            icon_color = "gray"
            icon_tooltip = "Sin servidores MCP configurados"
        elif total_inactive == 0:
            icon_color = "green"
            icon_tooltip = f"Todos los servidores MCP están activos: {', '.join(running_servers)}"
        else:
            icon_color = "red"
            icon_tooltip = f"Servidores inactivos: {', '.join(inactive_servers)}. Servidores activos: {', '.join(running_servers)}"
        
        self.mcp_status_label.configure(text=status_text, text_color=icon_color)
        self.mcp_status_icon.configure(text_color=icon_color)
        
        self.window.after(5000, self.update_mcp_status_label)

    def show_mcp_details(self):
        import importlib
        psutil = importlib.util.find_spec("psutil")
        psutil_available = psutil is not None
        if psutil_available:
            import psutil
        active_servers = self.mcp_manager.get_active_server_names()
        if not active_servers:
            log_to_chat_on_ui_thread(self.window, self.chat_text, "No hay servidores MCP configurados.", "system")
            return
        message = "Estado detallado de servidores MCP:\n\n"
        for server_name, config in self.mcp_manager.servers_config['mcpServers'].items():
            is_running = self.mcp_manager.is_server_running(server_name)
            status = "✅ Activo" if is_running else "❌ Inactivo"
            server_type = config.get('type', 'Desconocido')
            port = config.get('port', 'N/A')
            command = config.get('command', 'N/A')
            message += f"• {server_name}: {status} | Tipo: {server_type} | Puerto: {port} | Comando: {command}\n"
            if is_running:
                process = self.mcp_manager.active_processes.get(server_name)
                try:
                    import psutil
                    if process and psutil.pid_exists(process.pid):
                        p = psutil.Process(process.pid)
                        mem_kb = p.memory_info().rss / 1024
                        runtime = time.time() - p.create_time()
                        message += f"    Memoria usada: {mem_kb:.2f} KB\n    Tiempo de ejecución: {runtime:.2f} segundos\n"
                    else:
                        message += "    (No se pudo obtener info de memoria/tiempo)\n"
                except Exception:
                    message += "    (No se pudo obtener info de memoria/tiempo)\n"
        log_to_chat_on_ui_thread(self.window, self.chat_text, message, "system")

    def on_closing(self):
        self.window.destroy()

    def prompt_for_llm_model(self):
        dialog = ctk.CTkInputDialog(
            text="No se encontró un modelo LLM configurado. Ingresa el nombre del modelo (ej: llama3, mistral, etc):",
            title="Seleccionar modelo LLM"
        )
        model = dialog.get_input()
        if not model or not model.strip():
            model = "llama3"
        return model.strip()

    def toggle_mcp_menu(self):
        if not hasattr(self, 'mcp_menu_popup') or self.mcp_menu_popup is None or not self.mcp_menu_popup.winfo_exists():
            self.mcp_menu_popup = ctk.CTkToplevel(self.window)
            self.mcp_menu_popup.title("Opciones MCP")
            self.mcp_menu_popup.geometry("220x160")
            ctk.CTkButton(
                self.mcp_menu_popup,
                text="Cargar Configuración MCP",
                command=self.load_mcp_config_dialog
            ).pack(fill=tk.X, padx=10, pady=5)
            ctk.CTkButton(
                self.mcp_menu_popup,
                text="Iniciar MCPs Habilitados",
                command=lambda: self.start_all_mcp_servers_ui(auto_start=False)
            ).pack(fill=tk.X, padx=10, pady=5)
            ctk.CTkButton(
                self.mcp_menu_popup,
                text="Detener MCPs Activos",
                command=self.mcp_manager.stop_all_servers
            ).pack(fill=tk.X, padx=10, pady=5)
            ctk.CTkButton(
                self.mcp_menu_popup,
                text="Cerrar",
                command=self.mcp_menu_popup.destroy
            ).pack(fill=tk.X, padx=10, pady=5)
            self.mcp_menu_popup.protocol("WM_DELETE_WINDOW", self.mcp_menu_popup.destroy)
        else:
            self.mcp_menu_popup.destroy()
            self.mcp_menu_popup = None

    def load_mcp_config_dialog(self):
        filepath = filedialog.askopenfilename(title="Seleccionar mcp_servers.json", filetypes=(("JSON", "*.json"), ("Todos", "*.*")))
        if filepath:
            self.mcp_manager.stop_all_servers()
            if self.mcp_manager.load_config(filepath):
                log_to_chat_on_ui_thread(self.window, self.chat_text, f"Nueva config MCP cargada: {filepath}", "system")
                self.start_all_mcp_servers_ui(auto_start=True)
            else:
                messagebox.showerror("Error", f"No se pudo cargar la configuración desde {filepath}")
                log_to_chat_on_ui_thread(self.window, self.chat_text, f"Error al cargar MCP desde {filepath}", "error")
        self.update_mcp_status_label()

    def toggle_llm_menu(self):
        if not hasattr(self, 'llm_menu_popup') or self.llm_menu_popup is None or not self.llm_menu_popup.winfo_exists():
            self.llm_menu_popup = ctk.CTkToplevel(self.window)
            self.llm_menu_popup.title("Opciones LLM")
            self.llm_menu_popup.geometry("220x120")
            ctk.CTkButton(self.llm_menu_popup, text="Cambiar Modelo LLM", command=self.prompt_for_llm_model).pack(fill=tk.X, padx=10, pady=5)
            ctk.CTkButton(self.llm_menu_popup, text="Cerrar", command=self.llm_menu_popup.destroy).pack(fill=tk.X, padx=10, pady=5)
            self.llm_menu_popup.protocol("WM_DELETE_WINDOW", self.llm_menu_popup.destroy)
        else:
            self.llm_menu_popup.destroy()
            self.llm_menu_popup = None

    def send_message(self):
        user_input = self.input_entry.get().strip()
        if not user_input or self.assistant_response_active:
            return
        display_message(self.chat_text, user_input, "user", new_line_before_message=True)
        self.input_entry.delete(0, tk.END)
        self.window.update()
        self.assistant_response_active = True
        self.chat_text.configure(state='normal')
        current_content_end = self.chat_text.index('end-1c')
        if current_content_end != '1.0':
            if self.chat_text.get(f"{current_content_end} linestart", current_content_end).strip() != "":
                self.chat_text.insert(tk.END, "\n")
        self.current_assistant_content_start_idx = self.chat_text.index(tk.END)
        self.chat_text.insert(tk.END, "Procesando respuesta...", "loading")
        self.chat_text.insert(tk.END, "\n", "loading")
        self.chat_text.configure(state='disabled')
        self.chat_text.see(tk.END)
        self.ollama_stop_event.clear()
        system_prompt = self.get_base_system_prompt().strip() if hasattr(self, 'get_base_system_prompt') else ""
        def on_llm_chunk(content, full_response=None):
            try:
                if content:

