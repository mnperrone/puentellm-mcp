# Integración de Lingma con Entornos de Desarrollo (IDEs)

Esta guía explica cómo integrar Lingma con diferentes entornos de desarrollo para mejorar la productividad y facilitar el trabajo con el protocolo Model Context Protocol (MCP).

## Requisitos Generales

Antes de configurar la integración con cualquier IDE, asegúrate de tener instalado lo siguiente:

- Python 3.10 o superior
- [ModelContextProtocol SDK](https://github.com/modelcontextprotocol/sdk) (para el soporte MCP)
- [Ollama](https://ollama.com/) (si planeas usar modelos LLM locales)
- [Lingma](https://lingma.io/) (la última versión estable)

## Integración con PyCharm

### Configuración Paso a Paso

1. **Instala el plugin de MCP para PyCharm**
   - Ve a `File > Settings > Plugins`
   - Busca "Model Context Protocol" e instala el plugin
   - Reinicia PyCharm

2. **Configura el servidor MCP de Lingma**
   - Ve a `File > Settings > Tools > Model Context Protocol`
   - Haz clic en "Add" para crear una nueva configuración
   - Completa los siguientes campos:
     - Name: Lingma Server
     - Type: Custom
     - Host: localhost
     - Port: 8080 (o el puerto que estés usando)
     - Path: / (deja vacío)
     - Command: python -m modelcontextprotocol.servers.filesystem (ajusta según tu instalación)
     - Working Directory: $ProjectFileDir$ (variable de entorno de PyCharm)

3. **Habilita la integración con LLM**
   - En la misma sección de MCP, habilita la opción "Use LLM for code suggestions"
   - Selecciona el modelo LLM que desees desde el menú desplegable (descargará automáticamente modelos si no están presentes)

4. **Configura accesos directos de teclado**
   - Ve a `File > Settings > Keymap`
   - Busca acciones relacionadas con MCP y asigna combinaciones de teclas convenientes
   - Recomendamos asignar un acceso rápido para "Send to MCP" y "Get Code Suggestions"

5. **Prueba la integración**
   - Abre un archivo de código en PyCharm
   - Selecciona un fragmento de código y presiona el acceso directo para enviar al MCP
   - Deberías ver sugerencias o análisis del código generados por Lingma

### Características Destacadas en PyCharm

- Comentarios inteligentes sobre el código seleccionado
- Sugerencias contextuales basadas en MCP
- Integración con el sistema de versiones para mostrar cambios antes/después
- Soporte para múltiples servidores MCP simultáneamente

## Integración con Visual Studio Code

### Extensión Recomendada

Para usar Lingma con Visual Studio Code, recomendamos instalar la extensión oficial "Model Context Protocol".

### Pasos de Configuración

1. **Instala la extensión de MCP**
   - Abre VSCode
   - Ve a la pestaña de extensiones (Ctrl+Shift+X)
   - Busca "Model Context Protocol" e instálala

2. **Configura el servidor MCP de Lingma**
   - Una vez instalada la extensión, abre el comando palanca (Ctrl+Shift+P)
   - Busca "MCP: Add Server" y selecciona esta opción
   - Ingresa la siguiente información:
     - Server name: Lingma
     - Server type: custom
     - Host: localhost
     - Port: 8080
     - Command: python -m modelcontextprotocol.servers.filesystem (ajusta según tu instalación)
     - Working directory: ${workspaceFolder}

3. **Activa el servidor MCP**
   - Usa el comando palanca (Ctrl+Shift+P) y busca "MCP: Start Server"
   - Selecciona "Lingma" de la lista

4. **Usa las características de la extensión**
   - La extensión añade varias acciones visibles en el editor:
     - Un botón en la barra lateral izquierda para herramientas MCP
     - Acciones contextuales cuando seleccionas código
     - Panel de información MCP en el lado derecho

5. **Personaliza la integración**
   - Puedes personalizar el comportamiento de la integración editando el archivo `.vscode/settings.json` en tu proyecto
   - Ejemplo de configuración:
     ```json
     {
       "mcp.defaultServer": "Lingma",
       "mcp.showSuggestionsOnSelection": true,
       "mcp.suggestionDelay": 500
     }
     ```

## Integración con Otros IDEs

### Sublime Text

1. Instala el paquete MCP para Sublime Text desde Package Control
2. Crea un nuevo archivo de configuración MCP en `Preferences > Package Settings > Model Context Protocol > Settings - User`
3. Añade la configuración para Lingma:
   ```json
   {
     "servers": {
       "lingma": {
         "type": "custom",
         "command": "python -m modelcontextprotocol.servers.filesystem",
         "port": 8080,
         "working_dir": "$folder"
       }
     }
   ```
4. Reinicia Sublime Text

### Vim/Neovim

1. Si usas coc.nvim, instala el cliente MCP:
   ```bash
   :CocInstall coc-mcp
   ```
2. Configura el servidor Lingma en tu `coc-settings.json`:
   ```json
   {
     "mcp.servers": {
       "lingma": {
         "type": "custom",
         "command": "python -m modelcontextprotocol.servers.filesystem",
         "port": 8080,
         "rootPatterns": [".git"]
       }
     }
   ```

## Uso de la Integración

### Funcionalidades Comunes Disponibles

Independientemente del IDE que uses, deberías poder acceder a las siguientes funcionalidades:

1. **Selección de Servidor MCP**
   - Muestra una lista de servidores MCP disponibles
   - Permite cambiar entre distintos servidores y configuraciones

2. **Listado de Herramientas Disponibles**
   - Muestra todas las herramientas/handlers disponibles en el servidor MCP activo
   - Incluye descripciones y parámetros esperados

3. **Ejecución de Herramientas MCP**
   - Desde el menú de herramientas, puedes ejecutar comandos específicos
   - Algunas herramientas pueden requerir argumentos adicionales

4. **Visualización de Estado**
   - Iconos de estado (activo/inactivo/error/loading) para cada servidor MCP
   - Información detallada sobre servidores MCP en la interfaz

5. **Logging y Diagnóstico**
   - Registros detallados de todas las operaciones MCP
   - Sistema de logs persistente para auditoría y depuración

## Personalización Avanzada

### Archivo de Configuración Global

Puedes personalizar aún más la integración creando un archivo `~/.lingma/mcp_integration_config.json` con opciones avanzadas:

```json
{
  "default_server": "lingma-local",
  "auto_connect": true,
  "log_level": "debug",
  "tool_suggestions": {
    "show_on_hover": true,
    "max_suggestions": 5
  },
  "ui": {
    "status_bar": true,
    "icon_theme": "material"
  }
}
```

### Extensiones y Plugins Adicionales

Considera instalar estas extensiones complementarias según tus necesidades:

- **MCP File Browser**: Para navegar por archivos usando el servidor MCP filesystem
- **MCP Git Integration**: Para obtener contexto adicional de git durante las sesiones MCP
- **MCP Terminal**: Para ejecutar comandos en terminal a través de MCP

## Solución de Problemas Comunes

### Problemas Conocidos y Soluciones

| Problema | Posible Causa | Solución |
|---------|----------------|----------|
| No puedo conectar al servidor MCP | El servidor no está corriendo | Asegúrate de que el servidor MCP esté iniciado | 
| Las herramientas no aparecen | Error en la conexión MCP | Vuelve a cargar la configuración del servidor | 
| Errores de permisos | Falta de privilegios | Ejecuta el IDE como usuario con permisos adecuados | 
| Rendimiento lento | Red lenta o servidor sobrecargado | Considera usar servidores MCP locales o optimizar consultas grandes | 

### Soporte Técnico

Si encuentras problemas técnicos o quieres contribuir a la mejora de la integración con IDEs, visita el repositorio oficial:

https://github.com/lingma/lingma-mcp-integration

También puedes contactar con nuestro equipo de soporte técnico en support@lingma.io.