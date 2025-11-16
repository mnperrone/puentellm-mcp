import sys
from chat_app import ChatApp
import customtkinter as ctk
from assets.logging import PersistentLogger

if __name__ == "__main__":
    logger = PersistentLogger(log_dir="logs")
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    try:
        app = ChatApp()
        if app.window.winfo_exists():
            # Inicializar estado MCP de forma segura después de que todo esté listo
            if hasattr(app, 'mcp_status_label'):
                app.window.after(1000, app.update_mcp_status_label)
                app.mcp_status_after_id = app.window.after(2000, lambda: app.update_mcp_status_label())
    except Exception as e:
        try:
            logger.log(f"Error al iniciar la aplicación: {e}")
        except Exception:
            print(f"Error al iniciar la aplicación: {e}")
        sys.exit(1)
    try:
        app.window.mainloop()
    except Exception as e:
        if hasattr(app, 'mcp_manager') and hasattr(app.mcp_manager, 'logger'):
            app.mcp_manager.logger(f"Error durante la ejecución de la aplicación: {e}", "error")
        else:
            logger.log(f"Error durante la ejecución de la aplicación: {e}")

