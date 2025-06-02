# Ejecución de Pruebas en el Sistema PuenteLLM-MCP

## Descripción

Este documento explica cómo ejecutar las pruebas del sistema PuenteLLM-MCP desde diferentes entornos de desarrollo (IDEs) y mediante línea de comandos.

## Requisitos Previos

1. Python 3.10+ instalado
2. Dependencias del proyecto:
   ```bash
   pip install -r requirements.txt
   ```
3. Archivos de prueba:
   - test_config.json
   - test_requirements.txt
   - test_script.py
   - test_mcp_connection.py
   - test_config_validation.py

## Ejecución desde Línea de Comandos

### Ejecutar Todas las Pruebas

```bash
python -m unittest discover -v
```

### Ejecutar una Prueba Específica

```bash
python test_mcp_connection.py -v
```

### Ejecutar con Logging Persistente

```bash
python run_tests.py --log-file ~/.puentellm-mcp/test_logs/latest_run.log
```

## Ejecución desde PyCharm

### Configuración

1. Abrir `File > Settings > Tools > Python Integrated Tools`
2. Establecer `Default test runner` como `Unittest`
3. Ir a `Run > Edit Configurations`
4. Añadir nueva configuración con:
   - Script: `run_tests.py`
   - Parámetros: `--log-file ~/.puentellm-mcp/test_logs/pycharm_run.log`

### Ejecutar

1. Abrir cualquier archivo de prueba en el editor
2. Hacer clic derecho en el editor
3. Seleccionar `Run 'Unittest in <nombre_archivo>'`

## Ejecución desde Visual Studio Code

### Configuración

1. Instalar extensión `Python` y `Pylance` si no están presentes
2. Abrir paleta de comandos (`Ctrl+Shift+P`)
3. Buscar `Python: Configure Tests`
4. Seleccionar `Unittest`
5. Seleccionar directorio donde están las pruebas

### Ejecutar

1. Abrir `View > Command Palette` (`Ctrl+Shift+P`)
2. Buscar y seleccionar `Python: Run All Unit Tests`
3. Para ejecutar una prueba específica, hacer clic en los botones "Run Test" que aparecen sobre cada método de prueba

## Resultados de las Pruebas

Los resultados se mostrarán en la consola o en el panel de salida del IDE. Las pruebas exitosas se marcarán con ✅, mientras que los fallos o errores se marcarán con ❌.

## Logs y Depuración

- Los logs detallados se guardan en `~/.puentellm-mcp/test_logs/`
- Para depurar una prueba:
  - Colocar puntos de interrupción en el código
  - En PyCharm: Botón derecho > `Debug...`
  - En VSCode: Presionar el botón "Debug Test" que aparece sobre el método de prueba

## Integración Continua

Para integrar estas pruebas en un pipeline de CI/CD:

```yaml
# Ejemplo para GitHub Actions
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      - name: Run tests
        run: |
          python -m unittest discover -v
          python run_tests.py --log-file test_logs/ci_run.log