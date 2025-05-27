import tkinter as tk
import customtkinter as ctk
import threading
import ollama
import json
import os
import sys
from tkinter import filedialog, messagebox
from pathlib import Path
import time
from mcp_manager import MCPManager

class ChatApp:
    def __init__(self):
        self.ollama_thread = None
        self.ollama_stop_event = threading.Event()

        self.window = ctk.CTk(); self.window.title("Puente LLM - MCP"); self.window.geometry("990x570") 
        self.mcp_manager = MCPManager(self.log_to_chat_on_ui_thread); self.llm_model = "mistral" 
        self.ollama_response_started_flag = False; self.assistant_response_active = False 
        self.menubar = tk.Menu(self.window)
        self.mcp_menu = tk.Menu(self.menubar, tearoff=0)
        self.mcp_menu.add_command(label="Cargar Configuración MCP...", command=self.load_mcp_config_dialog)
        self.mcp_menu.add_separator()
        self.mcp_menu.add_command(label="Iniciar MCPs Habilitados", command=lambda: self.start_all_mcp_servers_ui(auto_start=False))
        self.mcp_menu.add_command(label="Detener MCPs Activos", command=self.mcp_manager.stop_all_servers)
        self.menubar.add_cascade(label="MCP", menu=self.mcp_menu)
        self.llm_menu = tk.Menu(self.menubar, tearoff=0)
        self.llm_menu.add_command(label="Cambiar Modelo LLM", command=self.change_llm_model_dialog)
        self.menubar.add_cascade(label="LLM", menu=self.llm_menu); self.window.config(menu=self.menubar)
        self.mcp_status_frame = ctk.CTkFrame(self.window, height=30); self.mcp_status_frame.pack(fill=tk.X, padx=10, pady=(10,0))
        self.mcp_status_label = ctk.CTkLabel(self.mcp_status_frame, text="MCPs: Cargando...", anchor="w"); self.mcp_status_label.pack(side=tk.LEFT, padx=10)
        self.base_font = ("Arial", 12)
        self.chat_text = ctk.CTkTextbox(self.window, wrap=tk.WORD, state='disabled', font=self.base_font); self.chat_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
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
        else: self.log_to_chat_on_ui_thread("No se pudo cargar config MCP. Usa menú 'MCP > Cargar...'", "error")
        self.update_mcp_status_label() 
        self.log_to_chat_on_ui_thread(f"Bienvenido. LLM: {self.llm_model}. MCPs: {', '.join(self.mcp_manager.get_active_server_names()) or 'Ninguno' }.", "system")
        self.window.after(100, self.input_entry.focus_set)

    def log_to_chat_on_ui_thread(self, message, tag):
        try:
            if self.window.winfo_exists():
                self.window.after(0, self.display_message, message, tag, True)
        except Exception: pass

    def display_message(self, message, tag, new_line_before_message=True, is_chunk_of_assistant_response=False):
        if getattr(self, '_is_closing', False): return
        if not self.window.winfo_exists() or not self.chat_text.winfo_exists(): return
        self.chat_text.configure(state='normal')
        current_content_end = self.chat_text.index('end-1c') 
        if new_line_before_message and current_content_end != '1.0':
            if self.chat_text.get(f"{current_content_end} linestart", current_content_end).strip() != "":
                 self.chat_text.insert(tk.END, "\n")
        prefix = ""
        if tag == "assistant" and is_chunk_of_assistant_response:
            prefix = "Ollama: "
        elif not is_chunk_of_assistant_response: 
            if tag == "user": prefix = "Tú: "
            elif tag == "assistant": prefix = "Ollama: " 
            elif tag == "system": prefix = "Sistema: "
            elif tag == "error": prefix = "App Error: " 
            elif tag == "mcp_comm": prefix = "MCP Comm: "
            elif tag == "mcp_stdout_log" or tag == "mcp_stderr_log": prefix = "" 
        self.chat_text.insert(tk.END, f"{prefix}{message}", tag)
        if not is_chunk_of_assistant_response: self.chat_text.insert(tk.END, "\n\n", tag) 
        self.chat_text.configure(state='disabled'); self.chat_text.see(tk.END)

    def update_mcp_status_label(self):
        config_mcp_names = self.mcp_manager.servers_config.get("mcpServers", {}).keys()
        active_processes_count = len([p for p in self.mcp_manager.active_processes.values() if p.poll() is None])
        status_text = f"MCPs Config: {len(list(config_mcp_names))} (Activos: {active_processes_count})"
        if config_mcp_names: status_text += f" | {', '.join(config_mcp_names)}"
        else: status_text += " | Ninguno (Carga una config)"
        self.mcp_status_label.configure(text=status_text)
        last_fixed_index = 3 
        while self.mcp_menu.index(tk.END) is not None and self.mcp_menu.index(tk.END) > last_fixed_index :
            self.mcp_menu.delete(tk.END)
        if config_mcp_names: self.mcp_menu.add_separator() 
        for server_name in config_mcp_names:
            is_active = server_name in self.mcp_manager.active_processes and self.mcp_manager.active_processes[server_name].poll() is None
            server_config = self.mcp_manager.servers_config["mcpServers"][server_name]; is_enabled_in_config = server_config.get("enabled", True)
            submenu_label = f"{server_name}"
            if not is_enabled_in_config: submenu_label += " (deshab.)"
            elif is_active: submenu_label += " (activo)"
            server_submenu = tk.Menu(self.mcp_menu, tearoff=0)
            if is_enabled_in_config:
                if is_active: server_submenu.add_command(label=f"Detener {server_name}", command=lambda s=server_name: (self.mcp_manager.stop_server(s), self.update_mcp_status_label()))
                else: server_submenu.add_command(label=f"Iniciar {server_name}", command=lambda s=server_name: (self.mcp_manager.start_server(s), self.update_mcp_status_label()))
            else: server_submenu.add_command(label="Habilitar en JSON y recargar", state="disabled") 
            server_submenu.add_command(label="Ver config (log)", command=lambda cfg=server_config: self.log_to_chat_on_ui_thread(json.dumps(cfg, indent=2), "system"))
            self.mcp_menu.add_cascade(label=submenu_label, menu=server_submenu)
        if hasattr(self, 'mcp_status_after_id'): self.mcp_status_label.after_cancel(self.mcp_status_after_id)
        if self.window.winfo_exists(): self.mcp_status_after_id = self.mcp_status_label.after(3000, self.update_mcp_status_label) 

    def load_mcp_config_dialog(self):
        filepath = filedialog.askopenfilename(title="Seleccionar mcp_servers.json", filetypes=(("JSON","*.json"),("Todos","*.*")))
        if filepath:
            self.mcp_manager.stop_all_servers() 
            if self.mcp_manager.load_config(filepath):
                self.log_to_chat_on_ui_thread(f"Nueva config MCP cargada: {filepath}", "system")
                self.start_all_mcp_servers_ui(auto_start=True) 
            else: messagebox.showerror("Error", f"No se pudo cargar config desde {filepath}"); self.log_to_chat_on_ui_thread(f"Error cargando config MCP: {filepath}", "error")
        self.update_mcp_status_label()

    def start_all_mcp_servers_ui(self, auto_start=False): 
        server_configs = self.mcp_manager.servers_config.get("mcpServers", {})
        if not server_configs:
            msg = "No hay MCPs configurados."; 
            if not auto_start: messagebox.showinfo("MCP", msg); self.log_to_chat_on_ui_thread(msg, "system")
            return
        any_started = False
        for name, cfg in server_configs.items():
            if cfg.get("enabled", True) and not (name in self.mcp_manager.active_processes and self.mcp_manager.active_processes[name].poll() is None):
                if self.mcp_manager.start_server(name): any_started = True
        log_msg = ""
        if any_started: log_msg = "Intentando iniciar MCPs habilitados."
        elif not auto_start : log_msg = "No se iniciaron nuevos MCPs (ya activos o deshabilitados)."
        if log_msg: self.log_to_chat_on_ui_thread(log_msg, "system")
        self.update_mcp_status_label()

    def change_llm_model_dialog(self):
        dialog = ctk.CTkInputDialog(text=f"LLM actual: {self.llm_model}\nNuevo modelo:", title="Cambiar LLM")
        new_model = dialog.get_input()
        if new_model and new_model.strip(): self.llm_model = new_model.strip(); self.log_to_chat_on_ui_thread(f"LLM cambiado a: {self.llm_model}", "system")
        else: self.log_to_chat_on_ui_thread("Cambio de LLM cancelado o vacío.", "system")

    def send_message(self):
        user_input = self.input_entry.get().strip()
        if not user_input or self.assistant_response_active:
            return
        self.display_message(user_input, "user", new_line_before_message=True)
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
        self.chat_text.insert(tk.END, "\n\n", "loading")
        self.chat_text.configure(state='disabled'); self.chat_text.see(tk.END)
        self.ollama_response_started_flag = False
        self.ollama_stop_event.clear()
        self.ollama_thread = threading.Thread(target=self.process_user_input_with_llm, args=(user_input,), daemon=True)
        self.ollama_thread.start()

    def stop_ollama_response(self):
        if self.ollama_thread and self.ollama_thread.is_alive():
            self.ollama_stop_event.set()
            self.log_to_chat_on_ui_thread("Respuesta de Ollama interrumpida por el usuario.", "system")
            self.assistant_response_active = False

    def _clear_assistant_processing_message(self):
        if getattr(self, '_is_closing', False): return
        if not self.chat_text.winfo_exists(): return
        self.chat_text.configure(state='normal')
        try:
            self.chat_text.tag_remove('loading', '1.0', tk.END)
            start = '1.0'
            while True:
                idx = self.chat_text.search('Procesando respuesta...', start, stopindex=tk.END)
                if not idx:
                    break
                end_idx = self.chat_text.index(f"{idx} + {len('Procesando respuesta...')} chars")
                after = self.chat_text.get(end_idx, f"{end_idx} + 2 chars")
                if after == '\n\n':
                    self.chat_text.delete(idx, f"{end_idx} + 2 chars")
                else:
                    self.chat_text.delete(idx, end_idx)
                start = idx
        except Exception:
            pass
        self.chat_text.configure(state='disabled')

    def _append_to_assistant_message(self, text_chunk):
        if getattr(self, '_is_closing', False): return
        if not self.window.winfo_exists() or not self.chat_text.winfo_exists(): return
        if not self.ollama_response_started_flag:
            if self.window.winfo_exists():
                self.window.after(0, self._clear_assistant_processing_message)
            self.ollama_response_started_flag = True
            if self.window.winfo_exists():
                self.window.after(20, self.display_message, text_chunk, "assistant", True, True)
        else:
            self.display_message(text_chunk, "assistant_content", False, True)

    def get_base_system_prompt(self):
        mcp_definition = (
            "IMPORTANTE: En este contexto, 'MCP' significa 'Model Context Protocol', "
            "un protocolo abierto que estandariza cómo las aplicaciones proporcionan contexto a los modelos de lenguaje (LLM). "
            "NO tiene relación con Minecraft ni con ningún videojuego.\n"
            "Responde siempre en base a esta definición cuando se te pregunte por MCP o servidores MCP.\n"
        )
        instrucciones = (
            "INSTRUCCIONES IMPORTANTES:\n"
            "- Si el usuario solo te saluda (por ejemplo: 'hola', 'buenas', 'buenos días', 'qué tal'), responde únicamente con un saludo breve y una pregunta amable sobre cómo puedes ayudarlo, sin dar información adicional ni contexto sobre MCP.\n"
            "- Si el usuario hace una pregunta, responde solo a lo que se te pregunta, de forma concisa y directa, sin agregar información no solicitada.\n"
            "- Responde siempre en español natural.\n"
        )
        active_mcp_servers = [name for name, proc in self.mcp_manager.active_processes.items() if proc.poll() is None]
        mcp_info = "Servidores MCP activos: " + (', '.join(active_mcp_servers) if active_mcp_servers else "Ninguno") + "."
        mcp_instruction = (
            "Para interactuar con un servidor MCP, genera una línea de texto con el siguiente formato EXACTO (sin texto adicional antes o después en esa línea):\n"
            "MCP_COMMAND_JSON: {\"server\": \"<nombre_del_servidor>\", \"method\": \"<nombre_del_metodo>\", \"params\": <parametros_json_o_null>}\n"
            "Ejemplo para listar archivos: MCP_COMMAND_JSON: {\"server\": \"filesystem\", \"method\": \"listFiles\", \"params\": {\"path\": \".\"}}\n"
            "Para conocer las capacidades de un servidor (ej. 'filesystem'), usa: MCP_COMMAND_JSON: {\"server\": \"filesystem\", \"method\": \"mcp.getCapabilities\", \"params\": {}}\n"
            "Interpreta las respuestas JSON de los MCPs para el usuario en español conversacional. No muestres el JSON crudo al usuario a menos que se te pida explícitamente."
        )
        return (
            f"Eres un asistente conversacional que SOLO responde en español. Responde de manera natural y directa.\n"
            f"{instrucciones}"
            f"{mcp_definition}"
            f"{mcp_info}\n{mcp_instruction}"
        )

    def process_user_input_with_llm(self, user_input, previous_mcp_response_json=None):
        system_prompt = self.get_base_system_prompt()
        messages = [{"role": "system", "content": system_prompt}]
        if previous_mcp_response_json:
            messages.append({"role": "user", "content": (
                f"Esta es una respuesta JSON de un servidor MCP. Interprétala para mí en español conversacional. "
                f"No intentes ejecutar otro comando MCP ahora. Respuesta MCP JSON:\n{json.dumps(previous_mcp_response_json, indent=2)}" )})
        else:
            messages.append({"role": "user", "content": user_input})
        try:
            response_stream = ollama.chat(model=self.llm_model, messages=messages, stream=True)
            full_llm_response = ""
            def stream_chunk_to_ui(content):
                if self.window.winfo_exists():
                    self.window.after(0, self._append_to_assistant_message, content)
            for chunk in response_stream:
                if self.ollama_stop_event.is_set():
                    break
                content = chunk.get('message', {}).get('content', '')
                if content:
                    full_llm_response += content
                    stream_chunk_to_ui(content)
                if "MCP_COMMAND_JSON:" in full_llm_response and (content.endswith("}") or content.endswith("}\n") or ("done" in chunk and chunk["done"])):
                    break
            if self.ollama_stop_event.is_set():
                if self.window.winfo_exists():
                    self.window.after(0, self._finalize_assistant_message)
                return
            if self.window.winfo_exists():
                self.window.after(0, self._finalize_assistant_message)
            if "MCP_COMMAND_JSON:" in full_llm_response:
                self.handle_mcp_command_from_llm(full_llm_response)
        except Exception as e:
            if self.window.winfo_exists():
                self.window.after(0, self._clear_assistant_processing_message)
                self.window.after(0, self.display_message, f"Error con Ollama: {e}", "error", False, True)
                self.window.after(0, self._finalize_assistant_message)

    def handle_mcp_command_from_llm(self, llm_response_text):
        command_prefix = "MCP_COMMAND_JSON:"; json_str_part = ""
        try:
            for line in llm_response_text.splitlines():
                if command_prefix in line: json_str_part = line.split(command_prefix, 1)[1].strip(); break 
            
            if not json_str_part:
                self.log_to_chat_on_ui_thread(f"LLM intentó MCP pero formato no reconocido: '{llm_response_text[:200]}...'", "error")
                if self.window.winfo_exists(): self.window.after(0, self._finalize_assistant_message); return

            if "<" in json_str_part and ">" in json_str_part and \
               ("nombre_del_servidor" in json_str_part or "nombre_del_metodo" in json_str_part or "parametros_json_o_null" in json_str_part):
                self.log_to_chat_on_ui_thread(f"LLM proporcionó un ejemplo de comando MCP, no se ejecutará: {json_str_part}", "system")
                self.ollama_response_started_flag = True 
                if self.window.winfo_exists(): self.window.after(0, self._finalize_assistant_message)
                return

            last_brace = json_str_part.rfind('}'); 
            if last_brace != -1: json_str_part = json_str_part[:last_brace+1]
            else: raise json.JSONDecodeError("JSON del LLM incompleto, no se encontró '}' final.", json_str_part, 0)
            
            self.log_to_chat_on_ui_thread(f"LLM -> MCP: {json_str_part}", "mcp_comm")
            mcp_cmd_data = json.loads(json_str_part)
            server, method, params = mcp_cmd_data.get("server"), mcp_cmd_data.get("method"), mcp_cmd_data.get("params")
            if not server or not method: 
                self.log_to_chat_on_ui_thread("MCP de LLM inválido (falta server/method).", "error")
                if self.window.winfo_exists(): self.window.after(0, self._finalize_assistant_message); return
            
            mcp_response = self.mcp_manager.send_command_to_mcp(server, method, params)
            if mcp_response is None: mcp_response = {"error": {"code": -99, "message": "Respuesta None del MCP Manager."}}
            
            self.log_to_chat_on_ui_thread(f"MCP ({server}) -> LLM: {json.dumps(mcp_response)}", "mcp_comm") 
            
            if isinstance(mcp_response, dict) and "error" in mcp_response:
                error_msg = mcp_response["error"].get("message", str(mcp_response["error"]))
                self.display_message(f"Error desde MCP '{server}': {error_msg}", "assistant", True, False)
                self.ollama_response_started_flag = True 
                if self.window.winfo_exists(): self.window.after(0, self._finalize_assistant_message)
                return
            
            self.display_message("Interpretando respuesta MCP...", "assistant", True, False)
            if not self.chat_text.winfo_exists():
                self.assistant_response_active = False; return
            
            self.chat_text.configure(state='normal')
            ollama_prefix_actual_end = self.chat_text.index(tk.END + " -1c -2 chars")
            self.chat_text.delete(ollama_prefix_actual_end, tk.END + " -1c")
            self.current_assistant_content_start_idx = self.chat_text.index(tk.END + " -1c")
            self.chat_text.insert(self.current_assistant_content_start_idx, "Interpretando respuesta MCP...", "loading")
            self.chat_text.insert(tk.END, "\n\n", "loading")
            self.chat_text.configure(state='disabled'); self.chat_text.see(tk.END)
            
            self.ollama_response_started_flag = False 
            threading.Thread(target=self.process_user_input_with_llm, args=(None, mcp_response), daemon=True).start()

        except json.JSONDecodeError as e: 
            self.log_to_chat_on_ui_thread(f"Error decodificando JSON de MCP del LLM: {e} (String: '{json_str_part}')", "error")
            if self.window.winfo_exists(): self.window.after(0, self._finalize_assistant_message) 
        except Exception as e_gen: 
            self.log_to_chat_on_ui_thread(f"Error manejando comando MCP de LLM: {type(e_gen).__name__}: {e_gen}", "error")
            if self.window.winfo_exists(): self.window.after(0, self._finalize_assistant_message)

    def _finalize_assistant_message(self):
        self.assistant_response_active = False
        if getattr(self, '_is_closing', False): return
        if self.window.winfo_exists() and self.chat_text.winfo_exists():
            self.chat_text.configure(state='normal')
            self.chat_text.see(tk.END)
            self.chat_text.configure(state='disabled')

    def on_closing(self):
        self._is_closing = True
        self.log_to_chat_on_ui_thread("Cerrando y deteniendo MCPs...", "system")
        try:
            if self.input_entry.winfo_exists():
                self.input_entry.configure(state="disabled")
                self.input_entry.unbind("<Return>")
            if self.send_btn.winfo_exists():
                self.send_btn.configure(state="disabled")
            if self.stop_btn.winfo_exists():
                self.stop_btn.configure(state="disabled")
        except Exception:
            pass
        if hasattr(self, 'mcp_status_after_id'):
            try:
                if self.window.winfo_exists():
                    self.mcp_status_label.after_cancel(self.mcp_status_after_id)
            except: pass
        for event in list(self.mcp_manager._stop_events.values()):
            event.set()
        self.mcp_manager.stop_all_servers()

        def destroy_widgets_and_window():
            try:
                if self.window.winfo_exists():
                    for widget in self.window.winfo_children():
                        try:
                            if widget.winfo_exists():
                                try:
                                    widget.unbind_all("<Configure>")
                                    widget.unbind_all("<Destroy>")
                                except: pass
                                widget.destroy()
                        except: pass
                    self.window.destroy()
            except: pass

        if self.window.winfo_exists():
            self.window.after(100, destroy_widgets_and_window)
