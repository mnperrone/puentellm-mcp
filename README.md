# Puente LLM - MCP (Desktop Chat App)

Aplicación de escritorio en Python (Tkinter + CustomTkinter) que actúa como puente entre modelos de lenguaje (LLM, usando Ollama) y servidores MCP (Model Context Protocol). Permite interactuar con LLMs y acceder a capacidades extendidas a través de servidores MCP, todo desde una interfaz gráfica moderna y fácil de usar.

## Características principales
- **Chat conversacional** con modelos LLM locales vía Ollama.
- **Integración con servidores MCP** (Model Context Protocol) para acceder a archivos, datos y herramientas externas de forma segura y estandarizada.
- **Gestión de servidores MCP**: iniciar, detener y cargar configuraciones desde la interfaz.
- **Cambio de modelo LLM** en caliente.
- **Botón para detener la respuesta** del LLM si es demasiado larga.
- **Respuestas siempre en español** y comportamiento configurable del asistente.

## ¿Qué es MCP?
MCP (Model Context Protocol) es un protocolo abierto que estandariza cómo las aplicaciones proporcionan contexto y capacidades a los modelos de lenguaje. Permite conectar LLMs con diferentes fuentes de datos y herramientas de manera unificada, como si fuera un "puerto USB-C" para IA. **No tiene relación con Minecraft ni videojuegos.**

## Requisitos
- Python 3.10+
- [Ollama](https://ollama.com/) instalado y corriendo localmente
- Node.js (para servidores MCP tipo filesystem)

### Dependencias Python
Instala las dependencias principales con:
```bash
pip install customtkinter ollama
```

## Estructura del proyecto
```
chat_app.py        # Lógica de la interfaz y chat
mcp_manager.py     # Gestión de servidores MCP
desktop_app.py     # Punto de entrada principal
mcp_servers.json   # Configuración de servidores MCP
```

## Uso
1. **Inicia Ollama** en tu máquina (por ejemplo, `ollama serve`).
2. Ejecuta la app:
   ```bash
   python desktop_app.py
   ```
3. Escribe tu mensaje en el campo inferior y presiona Enter o el botón "Enviar".
4. Usa el menú MCP para cargar o gestionar servidores MCP.
5. Cambia el modelo LLM desde el menú LLM si lo deseas.
6. Si la respuesta es muy larga, puedes interrumpirla con el botón "Detener respuesta".

## Personalización
- Edita `mcp_servers.json` para agregar o modificar servidores MCP.
- El comportamiento del asistente se puede ajustar en el método `get_base_system_prompt` de `chat_app.py`.

## Notas
- El foco del cursor se posiciona automáticamente en el campo de entrada al iniciar la app.
- El asistente responde solo en español y de forma concisa.
- El proyecto no requiere carpetas `.venv` ni `.idea` para funcionar.

## Licencia
MIT
