# Puente LLM - MCP (Desktop Chat App)

Aplicación de escritorio en Python (Tkinter + CustomTkinter) que actúa como puente entre modelos de lenguaje (LLM, usando Ollama) y servidores MCP (Model Context Protocol). Permite interactuar con LLMs y acceder a capacidades extendidas a través de servidores MCP, todo desde una interfaz gráfica moderna y fácil de usar.

## Características principales
- **Chat conversacional** con modelos LLM locales vía Ollama.
- **Integración con servidores MCP** (Model Context Protocol) para acceder a archivos, datos y herramientas externas de forma segura y estandarizada.
- **Gestión de servidores MCP**: iniciar, detener y cargar configuraciones desde la interfaz.
- **Descubrimiento y ejecución de herramientas MCP** usando el SDK oficial (no comandos manuales).
- **Cambio de modelo LLM** en caliente, con persistencia de la última selección.
- **Botón para detener la respuesta** del LLM si es demasiado larga.
- **Respuestas siempre en español** y comportamiento configurable del asistente.
- **Arranque del servicio Ollama** desde el menú de la app.
- **Configuración persistente** de preferencias y modelo LLM.
- **Arquitectura modular**: UI, diálogos, LLM, MCP SDK y configuración desacoplados en módulos independientes.

## ¿Qué es MCP?
MCP (Model Context Protocol) es un protocolo abierto que estandariza cómo las aplicaciones proporcionan contexto y capacidades a los modelos de lenguaje. Permite conectar LLMs con diferentes fuentes de datos y herramientas de manera unificada, como si fuera un "puerto USB-C" para IA. 

## Requisitos
- Python 3.10+
- [Ollama](https://ollama.com/) instalado y corriendo localmente
- Node.js (para servidores MCP tipo filesystem)

### Dependencias Python
Instala las dependencias principales con:
```bash
pip install customtkinter ollama psutil
```

## Estructura del proyecto
```
chat_app.py        # Lógica principal de la app y orquestación de módulos
ui_helpers.py      # Utilidades de UI y logging en el chat
dialogs.py         # Diálogos para herramientas y argumentos
llm_bridge.py      # Abstracción y manejo de LLM/Ollama
llm_mcp_handler.py # Manejo de comandos MCP generados por el LLM
mcp_sdk_bridge.py  # Integración con el SDK oficial de MCP
mcp_manager.py     # Gestión de procesos de servidores MCP
app_config.py      # Persistencia de configuración y preferencias
last_llm_model.txt # Archivo de persistencia del último modelo LLM usado
mcp_servers.json   # Configuración de servidores MCP
LICENSE            # Licencia MIT
README.md          # Este archivo
```

## Uso
1. **Inicia Ollama** en tu máquina (o usa el menú LLM > Iniciar servicio Ollama).
2. Ejecuta la app:
   ```bash
   python desktop_app.py
   ```
3. Escribe tu mensaje en el campo inferior y presiona Enter o el botón "Enviar".
4. Usa el menú MCP para cargar o gestionar servidores MCP, descubrir y ejecutar herramientas vía SDK.
5. Cambia el modelo LLM desde el menú LLM si lo deseas.
6. Si la respuesta es muy larga, puedes interrumpirla con el botón "Detener respuesta".

## Personalización
- Edita `mcp_servers.json` para agregar o modificar servidores MCP.
- El comportamiento del asistente se puede ajustar en el método `get_base_system_prompt` de `chat_app.py`.
- Puedes ampliar la persistencia de configuración en `app_config.py`.

## Notas
- El foco del cursor se posiciona automáticamente en el campo de entrada al iniciar la app.
- El asistente responde solo en español y de forma concisa.
- El proyecto no requiere carpetas `.venv` ni `.idea` para funcionar.

## Pruebas del sistema PuenteLLM-MCP

Este directorio contiene pruebas unitarias y scripts de prueba para el sistema PuenteLLM-MCP.

### Estructura del directorio de pruebas

```
tests/
├── test_mcp_config_validation.py    # Pruebas para validación de configuración MCP
├── test_mcp_connection.py          # Pruebas para conexión con servidores MCP
├── run_tests.py                    # Script para ejecutar todas las pruebas
├── test_config.json                # Archivo de configuración de prueba
├── test_script.py                  # Script de prueba para uso directo de las funciones
└── requirements.txt                # Requisitos para las pruebas
```

### Configuración de pruebas

1. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configurar archivos de prueba**:
   - El archivo `test_config.json` define la configuración básica de servidores MCP para pruebas
   - Asegúrate de que los comandos y rutas en el archivo de configuración sean válidos para tu entorno

3. **Ejecutar pruebas**:
   ```bash
   python run_tests.py
   ```

### Tipos de pruebas

#### 1. Validación de configuración (`test_mcp_config_validation.py`)

Estas pruebas verifican que la configuración de los servidores MCP sea correcta:
- Campos requeridos por tipo de servidor
- Valores válidos para tipos, puertos, comandos
- Validación de configuraciones al añadir o actualizar servidores

#### 2. Conexión con servidores (`test_mcp_connection.py`)

Estas pruebas verifican la capacidad de conexión con distintos tipos de servidores MCP:
- Carga correcta de la configuración
- Inicio y detención de servidores locales
- Inicio y detención de servidores NPM
- Conexión a servidores remotos
- Obtención y validación de lista de servidores

## Proveedores de LLM soportados

- **Ollama** (local, por defecto)
- **OpenAI Compatible** (API compatible, configurable)
- **Qwen** (Dashscope)

Todos los handlers de LLM implementan los métodos `generate(prompt)` y `stream(messages)` para compatibilidad total con el flujo de la app.

## Carpeta llm_providers

Contiene los módulos para cada proveedor de LLM:
- `ollama_handler.py`: Handler para Ollama local
- `openai_compatible_handler.py`: Handler para APIs OpenAI compatibles
- `qwen_handler.py`: Handler para Qwen/Dashscope
- `llm_exception.py`: Excepciones personalizadas para errores de conexión LLM
- `__init__.py`: Selector dinámico de handler según proveedor

## Buenas prácticas y mantenimiento

- La interfaz de los handlers está unificada (`generate` y `stream`).
- El código está modularizado y documentado.
- Se recomienda mantener actualizados los requisitos en `requirements.txt` y revisar la documentación de cada proveedor MCP/LLM.

---

Para dudas, sugerencias o reportes, me puedes contactar en mnperrone@gmail.com
