from chat_app import ChatApp
import customtkinter as ctk

if __name__ == "__main__":
    ctk.set_appearance_mode("System")
    ctk.set_default_color_theme("blue")
    app = ChatApp()
    try:
        if app.window.winfo_exists():
            app.mcp_status_after_id = app.mcp_status_label.after(1000, app.update_mcp_status_label)
    except:
        pass
    app.window.mainloop()