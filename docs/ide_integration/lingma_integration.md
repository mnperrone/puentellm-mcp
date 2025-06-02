# Integración de Lingma con IDEs

## Descripción

Este documento explica cómo integrar Lingma, el asistente inteligente para desarrolladores, con diferentes entornos de desarrollo integrado (IDEs) para mejorar la productividad y facilitar el desarrollo del sistema PuenteLLM-MCP.

## Requisitos Comunes

1. Python 3.10+ instalado
2. Extensiones necesarias:
   - `Python` (Microsoft)
   - `Pylance` (Microsoft)
   - `Jupyter` (Microsoft) - opcional
   - `Git` (por defecto en VSCode)
3. Archivos de configuración:
   - `.vscode/launch.json` - Configuración de depuración
   - `.vscode/settings.json` - Ajustes específicos del proyecto
   - `.vscode/tasks.json` - Definiciones de tareas

## Integración con PyCharm

### Configuración Inicial

1. Abrir el proyecto en PyCharm
2. Ir a `File > Settings > Plugins`
3. Instalar los siguientes plugins si no están presentes:
   - `Python Community Edition` o `Python Professional`
   - `Git`
   - `Markdown`
4. Ir a `File > Settings > Project: <nombre_proyecto> > Python Interpreter`
5. Asegurarse de que esté seleccionada la versión correcta de Python
6. Instalar dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
7. Configurar el plugin Git:
   - `File > Settings > Version Control > Git`
   - Seleccionar el ejecutable git
   - Especificar la ubicación del repositorio

### Ejecución de Tareas

1. Para ejecutar pruebas:
   - `Run > Run...`
   - Seleccionar `test_script.py` o cualquier otro archivo de prueba
2. Para depurar:
   - Colocar puntos de interrupción
   - `Run > Debug...`
3. Para ejecutar comandos personalizados:
   - `Tools > Run Python Console...`
   - `Tools > Run Unit Tests...

### Ventajas

- Soporte nativo para Python
- Excelente soporte para debugging
- Integración con herramientas de testing
- Soporte para versiones de Python múltiples
- Búsqueda avanzada de símbolos y referencias

## Integración con Visual Studio Code

### Configuración Inicial

1. Abrir el proyecto en VSCode
2. Instalar las siguientes extensiones si no están presentes:
   ```bash
   code --install-extension ms-python.python
   code --install-extension ms-python.vscode-pylance
   code --install-extension ms-toolsai.jupyter
   code --install-extension streetsidesoftware.code-spell-checker
   code --install-extension dbaeumer.vscode-eslint
   code --install-extension github.github-vscode-theme
   ```
3. Configurar el intérprete de Python:
   - Ctrl+Shift+P > "Select Python Interpreter"
   - Elegir el entorno virtual adecuado
4. Cargar configuraciones del proyecto:
   - El archivo `.vscode/launch.json` se carga automáticamente cuando se abre el panel de depuración
   - El archivo `.vscode/tasks.json` se usa para definir tareas reutilizables

### Ejecución de Tareas

1. Para ejecutar pruebas:
   - Abra el explorador de pruebas (icono de matraz en la barra lateral)
   - Haga clic en "Run All" o "Run Test" junto a cada prueba
2. Para depurar:
   - Presione `F5` o haga clic en el botón de play con pausa
   - Puede usar puntos de interrupción visuales
3. Para ejecutar comandos personalizados:
   - `Ctrl+Shift+P` > "Tasks: Run Task"
   - Seleccione una tarea predefinida o cree una nueva

### Ventajas

- Liviano y rápido
- Extensible mediante plugins
- Soporte nativo para Jupyter Notebooks
- Integración con GitHub y repositorios
- Soporte para múltiples lenguajes

## Recomendaciones Generales

- Mantener una estructura consistente de directorios
- Usar archivos README.md descriptivos
- Documentar todos los scripts de utilidad
- Configurar atajos de teclado personalizados
- Utilizar snippets para código repetido
- Implementar formatores automáticos (Black, isort, etc.)
- Configurar linting (pylint, flake8, etc.)
- Establecer un sistema de templates para nuevas pruebas