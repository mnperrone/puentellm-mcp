# 🌉 **PuenteLLM-MCP**

<div align="center">

[![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-orange.svg)](https://modelcontextprotocol.io/)
[![GUI Framework](https://img.shields.io/badge/GUI-CustomTkinter-purple.svg)](https://github.com/TomSchimansky/CustomTkinter)

**Una aplicación de escritorio moderna que conecta modelos de lenguaje con capacidades extendidas a través del Protocolo de Contexto de Modelos (MCP)**

[🚀 Características](#-características-principales) • [📦 Instalación](#-instalación) • [🛠️ Uso](#️-uso) • [🧪 Testing](#-testing) • [📋 Configuración](#-configuración)

</div>

---

## 📖 **¿Qué es PuenteLLM-MCP?**

**PuenteLLM-MCP** es una aplicación de escritorio desarrollada en Python que actúa como puente inteligente entre:

- **🤖 Modelos de Lenguaje (LLM)** - Locales (Ollama) y remotos (OpenRouter, OpenAI, etc.)
- **🔧 Servidores MCP** - Para acceso seguro a archivos, datos y herramientas externas
- **👤 Usuario** - A través de una interfaz gráfica moderna y intuitiva

### **¿Qué es MCP?**
El **Protocolo de Contexto de Modelos (MCP)** es un estándar abierto que permite a las aplicaciones proporcionar contexto y capacidades a los modelos de lenguaje de manera unificada. Es como un "puerto USB-C" para IA que estandariza la comunicación entre LLMs y herramientas externas.

---

## ⭐ **Características principales**

### 🎯 **Core Features**
- **💬 Chat conversacional** con múltiples proveedores de LLM
- **🔗 Integración MCP** con el SDK oficial para máxima compatibilidad
- **🎛️ Gestión de servidores MCP** desde la interfaz (iniciar/detener/configurar)
- **🔄 Cambio de modelo en caliente** con persistencia de configuración
- **⏹️ Control de respuestas** con botón de parada durante la generación

### 🛡️ **Seguridad y Configuración**
- **🔐 Gestión segura de credenciales** con variables de entorno
- **⚙️ Configuración persistente** de preferencias y modelos
- **🌐 Soporte multi-proveedor** (Ollama, OpenRouter, OpenAI, Anthropic)
- **🔍 Búsqueda inteligente de modelos** con filtrado en tiempo real

### 🎨 **Experiencia de Usuario**
- **🖥️ Interfaz moderna** con CustomTkinter
- **📱 Diseño responsive** y tema adaptable
- **🚀 Arranque automático** de servicios (Ollama)
- **🎯 Respuestas optimizadas** con configuración automática

---

## 🛠️ **Instalación**

### **Prerrequisitos**
- **Python 3.10+** ([Descargar](https://python.org/downloads/))
- **[Ollama](https://ollama.com/)** (para modelos locales)
- **Node.js** (para algunos servidores MCP)

### **1. Clonar el repositorio**
```bash
git clone https://github.com/mnperrone/puentellm-mcp.git
cd puentellm-mcp
```

### **2. Crear entorno virtual**
```bash
python -m venv .venv
# En Windows:
.venv\Scripts\activate
# En macOS/Linux:
source .venv/bin/activate
```

### **3. Instalar dependencias**
```bash
pip install -r requirements.txt
```

### **4. Configurar credenciales (opcional)**
```bash
cp .env.example .env
# Editar .env con tus API keys para proveedores remotos
```

---

## 🚀 **Uso**

### **Iniciar la aplicación**
```bash
python desktop_app.py
```

### **Primera configuración**

1. **🔧 Configurar proveedor LLM:**
   - Ir a **"Configuración" → "Configuración LLM Remoto"**
   - Seleccionar proveedor (Ollama, OpenRouter, etc.)
   - Ingresar credenciales si es necesario
   - **Probar conexión** y seleccionar modelo

2. **⚙️ Configurar servidores MCP:**
   - Ir a **"Configuración" → "Configuración MCP"** 
   - Agregar/editar servidores MCP
   - Iniciar servidores necesarios

3. **💬 ¡Comenzar a chatear!**
   - Escribir en el campo de chat
   - Usar comandos MCP cuando estén disponibles
   - El LLM puede acceder a capacidades de los servidores MCP automáticamente

### **Búsqueda de modelos**
Con más de 340+ modelos disponibles en algunos proveedores:
- **🔍 Campo de búsqueda** inteligente en configuración
- **Filtrado en tiempo real** mientras escribes
- **Ejemplos:** `gpt-4`, `claude`, `free`, `deepseek`

---

## 🧪 **Testing**

### **Ejecutar tests**
```bash
cd tests
pip install -r requirements.txt
python run_tests.py
```

### **Tests disponibles**
- **✅ Validación de configuración** - Estructura y consistencia de config files
- **🔌 Conexiones MCP** - Verificación de conectividad con servidores
- **⚙️ Gestión de configuración** - Persistencia y carga de configuraciones
- **🧪 Handlers LLM** - Inicialización y comunicación con proveedores

### **Tests de integración**
```bash
# Test específico de configuración
python tests/test_config_validation.py

# Test de conexión MCP
python tests/test_mcp_connection.py
```

---

## 📋 **Configuración**

### **Estructura de archivos**
```
puentellm-mcp/
├── 📁 llm_providers/          # Handlers para diferentes LLM providers
├── 📁 tests/                  # Suite de testing
├── 📁 logs/                   # Logs de aplicación
├── 📄 app_config.json         # Configuración principal
├── 📄 .env                    # Credenciales (git-ignored)
├── 📄 mcp_servers.json        # Configuración de servidores MCP
└── 📄 desktop_app.py          # Punto de entrada principal
```

### **Variables de entorno**
Crear `.env` basado en `.env.example`:
```bash
# OpenRouter
OPENROUTER_API_KEY=your_api_key_here

# OpenAI
OPENAI_API_KEY=your_api_key_here

# Anthropic
ANTHROPIC_API_KEY=your_api_key_here
```

### **Configuración MCP**
El archivo `mcp_servers.json` define los servidores MCP disponibles:
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/ruta/permitida"]
    }
  }
}
```

---

## 🏗️ **Arquitectura**

### **Componentes principales**

| Componente | Descripción | Archivo |
|------------|-------------|---------|
| **🖥️ UI Principal** | Interfaz de usuario y orquestación | `desktop_app.py`, `chat_app.py` |
| **🤖 LLM Bridge** | Abstracción para múltiples proveedores | `llm_bridge.py` |
| **🔗 MCP Manager** | Gestión de servidores MCP | `mcp_manager.py` |
| **⚙️ Config Manager** | Persistencia de configuración | `app_config.py` |
| **🔐 Env Manager** | Gestión segura de credenciales | `env_manager.py` |

### **Flujo de datos**
```
Usuario → UI → LLM Bridge → Proveedor LLM
                ↓
         MCP Manager → Servidor MCP → Herramientas
```

---

## 🤝 **Contribuir**

1. **Fork** el repositorio
2. **Crear** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Crear** un Pull Request

---

## 📄 **Licencia**

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para detalles.

---

## 🆘 **Soporte**

- **📋 Issues:** [GitHub Issues](https://github.com/mnperrone/puentellm-mcp/issues)
- **💬 Discusiones:** [GitHub Discussions](https://github.com/mnperrone/puentellm-mcp/discussions)
- **📧 Email:** Contacto a través de GitHub

---

<div align="center">

**⭐ Si este proyecto te resulta útil, ¡no olvides darle una estrella!**

[🔝 Volver arriba](#-puentellm-mcp)

</div>

O instala todo de una vez con:
```bash
pip install customtkinter==5.2.2 ollama psutil mcp httpx "pydantic>=2.11.0,<3.0.0" pydantic-settings>=2.5.2 python-multipart>=0.0.9 sse-starlette>=1.6.1 starlette>=0.27 uvicorn>=0.31.1 strictjson darkdetect pywin32>=310
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

## Integración con OpenRouter — sanitización y manejo de rate-limits

Se ha añadido soporte mejorado para proveedores remotos tipo OpenRouter con dos mejoras importantes:

- Sanitización y "auto-space": algunos modelos (por ejemplo DeepSeek) devuelven tokens con marcadores subword o palabras concatenadas. El proyecto ahora incluye:
   - Un sanitizador conservador que reemplaza el marcador subword `▁`, elimina tokens de control entre `<...>` y colapsa espacios.
   - Una opción opt-in llamada `auto_space_model_output` que intenta insertar espacios en casos donde el modelo devuelva palabras concatenadas. La heurística es conservadora y utiliza una segmentación basada en un pequeño diccionario de alta frecuencia en español para evitar particiones incorrectas.
   - La opción puede activarse desde la UI en `Configuración de LLM Remoto` (casilla "Intentar corregir espacios faltantes en la salida del modelo (auto-space)") o por la variable de entorno `PUENTE_ENABLE_AUTO_SPACING=1`.

- Manejo de HTTP 429 (rate limits) en streaming:
   - El handler de OpenRouter ahora implementa reintentos explícitos para respuestas 429, respeta el header `Retry-After` cuando esté presente y aplica backoff exponencial con jitter. Esto reduce la probabilidad de fallos visibles para el usuario cuando el servicio responde temporalmente con rate limits.
   - Si tras varios reintentos el servidor sigue devolviendo 429, la app lanzará un error informativo: "OpenRouter rate limit (HTTP 429). Espera unos segundos o revisa tu cuota/API key."

Notas importantes:
- La autocorrección de espacios es conservadora; si observas divisiones erróneas o no deseadas, desactívala desde la UI o poniendo `PUENTE_ENABLE_AUTO_SPACING=0`.
- Si recibes muchos 429 frecuentemente, revisa la cuota/plan de la API key de OpenRouter, reduce la tasa de peticiones desde la app, o utiliza otro proveedor.


## Buenas prácticas y mantenimiento

- La interfaz de los handlers está unificada (`generate` y `stream`).
- El código está modularizado y documentado.
- Se recomienda mantener actualizados los requisitos en `requirements.txt` y revisar la documentación de cada proveedor MCP/LLM.

---

Para dudas, sugerencias o reportes, me puedes contactar en mnperrone@gmail.com
