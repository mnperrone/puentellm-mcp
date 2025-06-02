# Integración de Lingma con Servidores MCP

Este documento describe cómo se ha integrado Lingma con los servidores MCP en este proyecto y las funcionalidades que ofrece.

## Arquitectura General

La integración entre Lingma (el asistente de IA) y los servidores MCP se ha implementado mediante un sistema modular que permite:
- Comunicación bidireccional entre el LLM (Lenguaje Modelo Grande) y los servidores MCP
- Ejecución de comandos MCP basados en solicitudes del usuario
- Visualización del estado de los servidores MCP en la interfaz de usuario
- Registro persistente de actividades para depuración y auditoría
- Configuración flexible de múltiples tipos de servidores MCP

## Componentes Clave

### 1. MCPManager

`MCPManager` es la clase central que gestiona la configuración y ejecución de servidores MCP. Sus principales características incluyen:

- **Soporte para múltiples tipos de servidores**: Local, NPM y Remoto
- **Gestión de procesos**: Iniciar, detener y monitorear servidores MCP
- **Validación de configuración**: Verifica que la configuración de cada servidor sea válida antes de iniciar
- **Persistencia**: Guarda y carga la configuración desde archivos JSON
- **Monitoreo de salida**: Captura y registra la salida de los servidores MCP

### 2. MCPSDKBridge

`MCPSDKBridge` actúa como intermediario entre el LLM y los servidores MCP, permitiendo:

- **Listar herramientas disponibles**
- **Ejecutar herramientas específicas**
- **Manejo de errores** durante la ejecución de herramientas
- **Integración con el sistema de logging** para registrar todas las interacciones

### 3. LLMMCPHandler

`LLMMCPHandler` facilita la interacción entre el LLM y los servidores MCP:

- **Traducción de solicitudes del LLM a comandos MCP**
- **Selección dinámica del servidor** según el tipo de comando
- **Manejo de respuestas** y presentación al usuario
- **Soporte específico para diferentes tipos de servidores** (Local, NPM, Remoto)

### 4. Sistema de Logging Persistente

El sistema de logging (`PersistentLogger`) proporciona:

- **Registro en archivo** de todas las actividades
- **Visualización en tiempo real** en la interfaz de usuario
- **Historial de logs** con rotación automática
- **Visor de logs** para inspeccionar registros históricos
- **Niveles de log** (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Funcionalidades Implementadas

### 1. Soporte para Múltiples Tipos de Servidores

Se han implementado tres tipos de servidores MCP:

#### a) Servidores Locales (`local`)

- Se inician directamente desde la aplicación
- Utilizan Python/Node.js para ejecutar los servicios
- Ideal para desarrollo y pruebas
- Comunicación a través del SDK o HTTP

#### b) Paquetes NPM (`npm`)

- Permiten ejecutar paquetes NPM como servidores MCP
- Usan `npx` para ejecutar comandos
- Útiles para herramientas basadas en Node.js
- Comunicación principalmente a través de HTTP

#### c) Servidores Remotos (`remote`)

- Conexión a servidores MCP ya en ejecución
- Solo requieren URL y credenciales si es necesario
- Ideal para producción o cuando los servidores están en máquinas separadas
- Comunicación a través de HTTP/HTTPS

### 2. Interfaz Gráfica para Gestión de Servidores

Se ha implementado una ventana de configuración (`MCPConfigWindow`) que permite:

- Ver el estado actual de todos los servidores
- Editar la configuración de cada servidor
- Agregar nuevos servidores
- Eliminar servidores existentes
- Activar/desactivar servidores
- Filtrar por tipo de servidor
- Buscar servidores por nombre
- Cargar/guardar configuraciones desde/hacia archivos

### 3. Indicadores Visuales de Estado

Los indicadores visuales (implementados en `ServerStatusIndicator`) muestran:

- Estado general de los servidores (Activo/Inactivo/Error)
- Número de servidores activos vs inactivos
- Estado individual de cada servidor (con color verde/gris/rojo)
- Detalles de configuración de cada servidor
- Botones para iniciar/detener servidores directamente desde la UI

### 4. Integración con la Aplicación Principal

La integración con la aplicación principal incluye:

- **Indicador global** en la barra superior mostrando el estado general
- **Actualización automática** del estado cada 5 segundos
- **Botón de detalles** para mostrar información específica de cada servidor
- **Manejo de errores** y retroalimentación visual cuando hay problemas
- **Historial de logs** accesible desde el menú de la aplicación

## Uso de la Integración

### Para Usuarios

1. **Ver estado de servidores**: El indicador en la parte superior muestra el estado general (verde = todos activos, rojo = algunos inactivos, gris = sin servidores)
2. **Iniciar/detener servidores**: Hacer clic en "Detalles" para abrir la ventana de configuración y usar los botones "Iniciar/Detener"
3. **Consultar logs**: Desde el menú MCP, seleccionar "Ver Logs" para ver todo el registro de actividades
4. **Limpiar logs**: Opción disponible en el menú de logs para mantener el sistema limpio

### Para Desarrolladores

1. **Agregar nuevo servidor**: Modificar el archivo de configuración `mcp_servers.json` o usar la interfaz gráfica
2. **Extender tipos de servidores**: Crear nuevas clases que implementen la interfaz base de servidor
3. **Personalizar logging**: Ajustar la configuración en `app_config.py`
4. **Añadir nuevas herramientas MCP**: Extender las capacidades del SDK o implementar nuevos endpoints HTTP

## Mejoras Futuras Potenciales

1. **Autodetección de servidores MCP** disponibles en la red local
2. **Integración con IDEs**: Extensiones para VSCode, PyCharm u otros editores que usen los servidores MCP
3. **Sistema de alertas proactivas** cuando un servidor falla
4. **Exportación de logs** a formatos estándar para auditorías
5. **Filtrado avanzado** de logs por servidor, nivel de severidad o rango de fechas
6. **Monitorización de rendimiento** para medir tiempos de respuesta de cada servidor
7. **Integración con sistemas de CI/CD** para despliegue automático de servidores MCP

## Consideraciones Técnicas

1. **Seguridad**: La comunicación con servidores remotos debe asegurar canales seguros (HTTPS)
2. **Compatibilidad**: Mantener consistencia en los comandos MCP independientemente del tipo de servidor
3. **Escalabilidad**: El diseño permite añadir fácilmente nuevos tipos de servidores
4. **Depuración**: Los logs persistentes facilitan la identificación de problemas
5. **Flexibilidad**: La configuración modular permite adaptarse a distintos entornos

## Referencias

- [Model Context Protocol](https://modelcontextprotocol.org/) - Sitio oficial del protocolo MCP
- [SDK de MCP](https://github.com/modelcontextprotocol/sdk) - Repositorio del SDK de MCP
- [Documentación de ModelContextProtocol](https://docs.modelcontextprotocol.org/) - Documentación técnica

Este documento proporciona una visión general de la integración actual. Para detalles específicos de implementación, consultar el código fuente correspondiente.