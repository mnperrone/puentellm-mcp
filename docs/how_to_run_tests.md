# Cómo Ejecutar las Pruebas del Sistema PuenteLLM-MCP

Este documento explica cómo ejecutar y validar las pruebas del sistema PuenteLLM-MCP.

## Requisitos Previos

Antes de ejecutar las pruebas, asegúrate de tener instalado lo siguiente:

- Python 3.10 o superior
- [Ollama](https://ollama.com/) (para el soporte de LLM)
- [ModelContextProtocol SDK](https://github.com/modelcontextprotocol/sdk) (para el soporte MCP)
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) (para la interfaz gráfica)
- [StrictJSON](https://pypi.org/project/strictjson/) (para validación robusta de JSON)

### Instalación de Dependencias

Puedes instalar las dependencias necesarias usando pip:

```bash
pip install -r requirements.txt
```

## Estructura del Directorio de Pruebas

```
puentellm-mcp-tests/
├── docs/                      # Documentación
├── assets/                    # Recursos gráficos (iconos, imágenes)
│   └── icons/
│       └── server_status/     # Iconos de estado de servidores
├── test_mcp_connection.py     # Pruebas de conexión MCP
├── test_mcp_config_validation.py # Pruebas de validación de configuración MCP
├── test_script.py             # Script de prueba básico
├── run_tests.py               # Ejecutor de pruebas
└── requirements.txt           # Requisitos del entorno de pruebas
```

## Archivos de Configuración

El archivo `test_config.json` contiene la configuración para los servidores MCP utilizados en las pruebas. Puedes modificar este archivo para ajustar la configuración según tus necesidades.

Ejemplo de configuración:

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "python",
      "type": "local",
      "port": 8083,
      "enabled": true,
      "auto_restart": false,
      "workdir": ".",  // Directorio actual
      "args": ["-m", "modelcontextprotocol.servers.filesystem"]  // Argumentos adicionales
    },
    "browser": {
      "command": "playwright",
      "type": "npm",
      "port": 8084,
      "enabled": true,
      "auto_restart": false,
      "workdir": ".",
      "args": ["--target", "browser"]  // Argumentos adicionales
    },
    "remote-test": {
      "url": "http://localhost:8085",
      "type": "remote",
      "enabled": false,  // Por defecto los servidores remotos están deshabilitados
      "auto_restart": false
    }
  }
}
```

## Ejecución de Pruebas

### Ejecutar Todas las Pruebas

Para ejecutar todas las pruebas del sistema, simplemente ejecuta:

```bash
python run_tests.py
```

Este script descubrirá y ejecutará automáticamente todas las pruebas definidas en archivos que comienzan con `test_`. El resultado se registrará tanto en consola como en archivos de log.

### Ejecutar una Prueba Específica

Si deseas ejecutar solo un conjunto específico de pruebas, puedes hacerlo directamente con Python:

```bash
python -m unittest test_mcp_connection.py
```

## Tipos de Pruebas

### Pruebas de Conexión MCP

Las pruebas en `test_mcp_connection.py` verifican que los servidores MCP puedan iniciarse correctamente y mantener una conexión estable.

### Pruebas de Validación de Configuración MCP

Las pruebas en `test_mcp_config_validation.py` verifican que la configuración de los servidores MCP se cargue y valide correctamente.

### Prueba Funcional Básica

El script `test_script.py` ejecuta un escenario básico de uso del sistema para verificar su funcionamiento integral.

## Registro de Logs

Todas las pruebas generan logs detallados que se almacenan en el directorio `~/.puentellm-mcp/test_logs/`. Estos logs incluyen información sobre:

- Inicio y fin de cada prueba
- Estado de los servidores MCP
- Errores detectados durante la ejecución
- Resultados detallados de cada operación

## Mantenimiento y Actualización

Para actualizar o añadir nuevas pruebas:

1. Modifica los archivos existentes o crea nuevos archivos de prueba siguiendo el patrón `test_*.py`
2. Asegúrate de que las nuevas pruebas estén bien documentadas
3. Agrega cualquier dependencia adicional a `requirements.txt` si es necesario
4. Ejecuta `run_tests.py` para validar todos los cambios

## Solución de Problemas Comunes

### Problemas Conocidos y Soluciones

| Problema | Posible Causa | Solución |
|---------|----------------|----------|
| No puedo conectar al servidor MCP | El servidor no está corriendo | Asegúrate de que el servidor MCP esté iniciado | 
| Las herramientas no aparecen | Error en la conexión MCP | Vuelve a cargar la configuración del servidor | 
| Errores de permisos | Falta de privilegios | Ejecuta el IDE como usuario con permisos adecuados | 
| Rendimiento lento | Red lenta o servidor sobrecargado | Considera usar servidores MCP locales o optimizar consultas grandes | 

### Soporte Técnico

Para soporte técnico adicional o ayuda con errores específicos, consulta la documentación oficial del [Model Context Protocol](https://modelcontextprotocol.org/) o contacta al equipo de desarrollo.