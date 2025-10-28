# llm_config_window.py

import customtkinter as ctk
from tkinter import messagebox
from llm_providers import get_llm_handler
from app_config import AppConfig

class LLMConfigWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.config = AppConfig()

        self.title("Remote LLM Configuration")
        self.geometry("600x400")
        self.transient(parent)
        self.grab_set()

        self.provider_configs = self.config.get('llm_provider_configs', {})

        self.create_ui()
        self.load_providers()

    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        main_frame = ctk.CTkFrame(self)
        main_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_columnconfigure(1, weight=2)

        # Provider List
        provider_frame = ctk.CTkFrame(main_frame)
        provider_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        provider_frame.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(provider_frame, text="Providers", font=("Segoe UI", 12, "bold")).grid(row=0, column=0, pady=5)
        self.provider_list = ctk.CTkListbox(provider_frame, command=self.on_provider_select)
        self.provider_list.grid(row=1, column=0, sticky="nsew")

        # Config Frame
        self.config_frame = ctk.CTkFrame(main_frame)
        self.config_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        self.config_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.config_frame, text="API Key:").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        self.api_key_entry = ctk.CTkEntry(self.config_frame, show="*")
        self.api_key_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.config_frame, text="Base URL:").grid(row=1, column=0, sticky="w", padx=10, pady=5)
        self.base_url_entry = ctk.CTkEntry(self.config_frame)
        self.base_url_entry.grid(row=1, column=1, sticky="ew", padx=10, pady=5)

        ctk.CTkLabel(self.config_frame, text="Model:").grid(row=2, column=0, sticky="w", padx=10, pady=5)
        self.model_entry = ctk.CTkEntry(self.config_frame)
        self.model_entry.grid(row=2, column=1, sticky="ew", padx=10, pady=5)

        # Buttons
        button_frame = ctk.CTkFrame(self)
        button_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)

        self.save_button = ctk.CTkButton(button_frame, text="Save", command=self.save_config)
        self.save_button.pack(side="right", padx=5)

        self.test_button = ctk.CTkButton(button_frame, text="Test Connection", command=self.test_connection)
        self.test_button.pack(side="right", padx=5)

    def load_providers(self):
        providers = ["openai_compatible", "qwen", "deepseek", "openrouter", "huggingface"]
        for provider in providers:
            self.provider_list.insert("end", provider)
        self.provider_list.activate(0)
        self.on_provider_select()


    def on_provider_select(self, event=None):
        selection = self.provider_list.get()
        if not selection:
            return

        config = self.provider_configs.get(selection, {})
        self.api_key_entry.delete(0, "end")
        self.api_key_entry.insert(0, config.get("api_key", ""))
        self.base_url_entry.delete(0, "end")
        self.base_url_entry.insert(0, config.get("base_url", ""))
        self.model_entry.delete(0, "end")
        self.model_entry.insert(0, config.get("model", ""))

    def save_config(self):
        selection = self.provider_list.get()
        if not selection:
            return

        self.provider_configs[selection] = {
            "api_key": self.api_key_entry.get(),
            "base_url": self.base_url_entry.get(),
            "model": self.model_entry.get(),
        }
        self.config.set('llm_provider_configs', self.provider_configs)
        self.config.save_config()
        messagebox.showinfo("Success", "Configuration saved successfully.")
        self.destroy()

    def test_connection(self):
        selection = self.provider_list.get()
        if not selection:
            return

        api_key = self.api_key_entry.get()
        base_url = self.base_url_entry.get()
        model = self.model_entry.get()

        if not api_key:
            messagebox.showerror("Error", "API Key is required.")
            return

        try:
            handler = get_llm_handler(selection, api_key, base_url, model)
            # A simple generate call to test the connection
            handler.generate("Hello")
            messagebox.showinfo("Success", "Connection successful!")
        except Exception as e:
            messagebox.showerror("Connection Failed", str(e))
