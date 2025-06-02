# Iconos de Estado de Servidores MCP

Este directorio contiene los iconos utilizados para representar visualmente el estado de los servidores MCP en la interfaz gráfica del sistema PuenteLLM-MCP.

## Contenido

- `active.png` - Icono para servidor activo
- `inactive.png` - Icono para servidor inactivo
- `error.png` - Icono para servidor con errores
- `loading.gif` - Animación para servidor cargando

## Uso

Los iconos se deben ubicar en este directorio y ser referenciados desde el código a través de las funciones en `ui_helpers.py`. La función `update_server_status_icon()` se encarga de cargar y mostrar estos iconos según el estado actual de cada servidor.

## Requisitos Gráficos

- Todos los iconos deben tener un tamaño estándar de 20x20 píxeles
- El formato recomendado es PNG, excepto para animaciones que debe usarse GIF
- Deben usar una paleta de colores coherente con el resto de la aplicación
- Se recomienda utilizar estilos vectoriales para permitir escalado sin pérdida de calidad

## Licencia

Todos los iconos deben estar bajo una licencia compatible con GPLv3 o superior, o ser creados por el equipo de desarrollo con derechos de uso completos.