# 🧩 Galería de Servidores MCP

Sistema completo de galería para servidores MCP con instalación automática ("un click install") y verificación de integridad, inspirado en Docker Desktop, Cursor y hub.mcp.dev.

## 🚀 Características Principales

### ✨ Cliente Tkinter (MCP Gallery)
- **Interfaz visual moderna** con scroll y tarjetas para cada servidor
- **Instalación automática** con un solo clic
- **Verificación de integridad** con checksums SHA256 y firmas PGP
- **Búsqueda y filtrado** por nombre, descripción y tags
- **Gestión completa** de servidores (instalar, actualizar, desinstalar)

### 🌐 API Centralizada (FastAPI)
- **Endpoint `/mcps`** para listar todos los servidores disponibles
- **Endpoint `/mcps/{id}`** para detalles específicos de cada servidor
- **Archivos estáticos** para manifests, firmas e íconos
- **Búsqueda avanzada** con filtros por tags y términos
- **API RESTful completa** con documentación automática

### 🔐 Verificación de Integridad
- **Checksums SHA256** para validar integridad de archivos
- **Firmas PGP** para verificación de autenticidad (opcional)
- **Validación automática** antes de cada instalación
- **Informes detallados** de verificación

## 📁 Estructura de Archivos

```
puentellm-mcp/
├── mcp_gallery_manager.py          # Gestor principal de la galería
├── mcp_gallery_window.py           # Interfaz gráfica Tkinter  
├── gallery_fallback.json           # Datos de fallback si API no disponible
├── mcp_gallery_api/                # Servidor API FastAPI
│   ├── server.py                   # Servidor principal
│   ├── utils.py                    # Utilidades
│   ├── requirements.txt            # Dependencias de la API
│   ├── run_server.py              # Script para ejecutar API
│   ├── gallery.json               # Base de datos de servidores
│   └── static/                    # Archivos estáticos
│       ├── manifests/             # Manifests de servidores
│       ├── signatures/            # Firmas PGP
│       └── icons/                 # Íconos de servidores
└── ~/.config/puentellm-mcp/       # Datos del usuario
    ├── mcps/                      # Servidores instalados
    ├── installed_servers.json     # Registro de instalaciones
    └── public_keys/               # Claves públicas PGP
```

## 🛠️ Instalación y Configuración

### Dependencias Principales
```bash
# Para el cliente Tkinter (incluidas en el proyecto principal)
pip install customtkinter pillow requests

# Para el servidor API (opcional, solo si ejecutas la API)
pip install -r mcp_gallery_api/requirements.txt
```

### Configuración de API (Opcional)
Si deseas ejecutar tu propia instancia de la API:

1. **Instala dependencias de la API:**
```bash
cd mcp_gallery_api
pip install -r requirements.txt
```

2. **Ejecuta el servidor:**
```bash
python run_server.py
```

3. **Accede a la documentación:**
- API: http://localhost:8000
- Docs: http://localhost:8000/docs

## 🎮 Uso de la Galería

### Desde la Aplicación Principal
1. Abre PuenteLLM MCP
2. Haz clic en el botón **🧩** en la barra superior
3. Navega por los servidores disponibles
4. Haz clic en **"Instalar"** para cualquier servidor

### Prueba de la Galería
```bash
# Probar solo la interfaz gráfica
python mcp_gallery_window.py
```

## 📋 Gestión de Servidores

### Estados de Servidores
- **🟢 No instalado**: Disponible para instalación
- **🟡 Actualizable**: Versión más nueva disponible  
- **🔵 Instalado**: Versión actual instalada

### Operaciones Disponibles
- **Instalar**: Descarga y configura un servidor MCP
- **Actualizar**: Actualiza a la versión más reciente
- **Desinstalar**: Elimina completamente un servidor
- **Detalles**: Muestra información completa del servidor

### Verificación de Seguridad
Cada instalación incluye:
- ✅ Validación de checksum SHA256
- ✅ Verificación de firma PGP (si disponible)  
- ✅ Validación de formato de manifest
- ✅ Registro de verificaciones realizadas

## 🔧 Configuración Avanzada

### URL de API Personalizada
```python
from mcp_gallery_manager import MCPGalleryManager

manager = MCPGalleryManager()
manager.set_api_base_url("https://tu-api.com")
```

### Claves PGP Personalizadas
```python
# Instalar clave pública
key_content = "-----BEGIN PGP PUBLIC KEY-----..."
manager.install_public_key(key_content, "mi_clave.gpg")

# Listar claves instaladas
keys = manager.list_public_keys()
```

### Directorios Personalizados
```python
# Usar directorio personalizado para datos
manager = MCPGalleryManager("/path/to/custom/config")
```

## 📊 Monitoreo y Estadísticas

### Estadísticas de Instalación
```python
stats = manager.get_installation_stats()
print(f"Servidores instalados: {stats['total_installed']}")
print(f"Verificados con checksum: {stats['verified_checksum']}")
print(f"Verificados con firma: {stats['verified_signature']}")
print(f"Uso de disco: {stats['disk_usage_mb']} MB")
```

## 🐛 Solución de Problemas

### Error: "API no disponible"
- La galería funciona con datos de fallback locales
- Verifica conexión a internet
- Comprueba que la API esté ejecutándose (si es local)

### Error: "Falla verificación de integridad"  
- El servidor puede tener un checksum incorrecto
- Verifica que el manifest no esté corrupto
- Intenta con otro servidor para confirmar

### Error: "No se puede instalar PGP"
```bash
# En Windows, instalar GPG
choco install gnupg
# o descargar desde: https://gnupg.org/download/

# En Linux/Mac
sudo apt install gnupg   # Ubuntu/Debian
brew install gnupg       # Mac
```

### Problemas de Permisos
- Verifica permisos de escritura en `~/.config/puentellm-mcp/`
- En Windows, ejecuta como administrador si es necesario

## 📚 API Reference

### Cliente Python
```python
from mcp_gallery_manager import MCPGalleryManager
from mcp_gallery_window import MCPGalleryWindow

# Gestor programático
manager = MCPGalleryManager()
servers = manager.fetch_available_servers()
success, msg = manager.install_server(servers[0])

# Interfaz gráfica
gallery = MCPGalleryWindow()
gallery.show()
```

### API REST
```http
GET /mcps                    # Lista todos los servidores
GET /mcps/{server_id}        # Detalles de un servidor
GET /search?q=weather        # Buscar servidores
POST /mcps                   # Añadir nuevo servidor
DELETE /mcps/{server_id}     # Eliminar servidor
```

## 🤝 Contribuir

### Añadir un Servidor a la Galería
1. Crea un manifest JSON válido
2. Calcula el checksum SHA256
3. (Opcional) Genera firma PGP
4. Añade entrada al `gallery.json`
5. Envía PR con los archivos estáticos

### Ejemplo de Entrada
```json
{
  "id": "mi-servidor",
  "name": "Mi Servidor MCP",
  "description": "Descripción detallada",
  "icon": "https://example.com/icon.png",
  "manifest_url": "https://example.com/manifest.json",
  "version": "1.0.0",
  "min_client_version": "1.0.0",
  "checksum": "sha256:abc123...",
  "signature_url": "https://example.com/signature.sig",
  "tags": ["categoria", "funcionalidad"]
}
```

## 🎯 Roadmap

- [ ] **Soporte para dependencias automáticas** (npm, pip, etc.)
- [ ] **Categorías y colecciones** de servidores
- [ ] **Ratings y reviews** de la comunidad  
- [ ] **Actualizaciones automáticas** en background
- [ ] **Integración con GitHub** para import directo
- [ ] **Soporte para Docker** containers
- [ ] **Plugin de VS Code** para gestión

## 📄 Licencia

Este sistema es parte de PuenteLLM MCP y sigue la misma licencia del proyecto principal.

---

**¿Necesitas ayuda?** Abre un issue en el repositorio o consulta la documentación principal de PuenteLLM MCP.