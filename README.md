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

### **2. Instalar dependencias**
```bash
# Instalar paquetes principales (desde el directorio raíz)
pip install customtkinter==5.2.2 ollama psutil mcp httpx "pydantic>=2.11.0,<3.0.0" pydantic-settings>=2.5.2 python-multipart>=0.0.9 sse-starlette>=1.6.1 starlette>=0.27 uvicorn>=0.31.1 strictjson darkdetect python-dotenv requests

# O en Windows con pywin32:
pip install customtkinter==5.2.2 ollama psutil mcp httpx "pydantic>=2.11.0,<3.0.0" pydantic-settings>=2.5.2 python-multipart>=0.0.9 sse-starlette>=1.6.1 starlette>=0.27 uvicorn>=0.31.1 strictjson darkdetect pywin32>=310 python-dotenv requests
```

### **3. Configurar credenciales (opcional)**
```bash
cp .env.example .env
# Editar .env con tus API keys para proveedores remotos
```

> **💡 Nota:** El proyecto **no requiere entorno virtual** para funcionar. Las dependencias se pueden instalar directamente en el sistema Python.

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
python run_tests.py
```

> **💡 Nota:** Los tests usan las mismas dependencias del proyecto principal, no requieren instalaciones adicionales.

### **Tests disponibles**
- **✅ Validación de configuración** - Estructura y consistencia de config files
- **🔌 Conexiones MCP** - Verificación de conectividad con servidores
- **⚙️ Gestión de configuración** - Persistencia y carga de configuraciones
- **🧪 Handlers LLM** - Inicialización y comunicación con proveedores

### **Tests de integración**
```bash
# Test específico de configuración
python tests/test_basic_structure.py

# Test de funcionalidad core
python tests/test_core_functionality.py
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
