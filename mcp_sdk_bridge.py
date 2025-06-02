import asyncio
from typing import Optional, Dict, Any, List, Union
from contextlib import AsyncExitStack
import json
import re
import logging

from mcp import ClientSession, StdioServerParameters, Tool
from mcp.client.stdio import stdio_client
from assets.logging import PersistentLogger

class MCPSDKBridge:
    """
    Puente entre el LLM y los servidores MCP.
    Esta clase proporciona métodos para interactuar con servidores MCP,
    incluyendo listar herramientas disponibles y ejecutar comandos específicos.
    """
    
    def __init__(self, mcp_manager: Optional[object] = None, logger: Optional[object] = None):
        """
        Inicializa el puente MCP.
        Args:
            mcp_manager: Instancia de MCPManager para gestionar servidores (opcional)
            logger: Logger persistente o función para registrar mensajes (opcional)
        """
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.tools_cache: List[Tool] = []
        self.stdio = None
        self.write = None
        self.mcp_manager = mcp_manager
        self.logger = logger if logger else PersistentLogger()
        self._tools_cache: Dict[str, List[Tool]] = {}

    async def connect(self, server_script_path: str) -> List[Tool]:
        """
        Conecta al servidor MCP especificado por la ruta del script.
        
        Args:
            server_script_path (str): Ruta al script del servidor MCP (.py o .js)
            
        Returns:
            List[Tool]: Lista de herramientas disponibles en el servidor MCP
            
        Raises:
            ValueError: Si el tipo de archivo no es compatible
            RuntimeError: Si hay un error al conectar con el servidor
        """
        try:
            is_python = server_script_path.endswith('.py')
            is_js = server_script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("El script del servidor debe ser .py o .js")
            
            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )
            
            # Usar un contexto asíncrono para mantener activa la conexión
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            )
            self.stdio, self.write = stdio_transport
            
            # Crear una nueva sesión para cada conexión
            self.session = await self.exit_stack.enter_async_context(
                ClientSession(self.stdio, self.write)
            )
            
            # Inicializar la sesión
            await self.session.initialize()
            
            # Obtener las herramientas disponibles
            response = await self.session.list_tools()
            self.tools_cache = response.tools
            
            self.logger.info(f"Conectado exitosamente a {server_script_path} con {len(self.tools_cache)} herramientas disponibles")
            return self.tools_cache
            
        except Exception as e:
            self.logger.error(f"Error conectando al servidor MCP: {str(e)}", exc_info=True)
            raise RuntimeError(f"No se pudo conectar al servidor MCP: {str(e)}") from e

    async def list_tools(self) -> List[Tool]:
        """
        Devuelve la lista de herramientas disponibles en el servidor MCP actual.
        
        Returns:
            List[Tool]: Lista de herramientas disponibles
            
        Raises:
            RuntimeError: Si no hay una sesión MCP activa
        """
        if self.session is None:
            raise RuntimeError("La sesión MCP no está inicializada")
        
        response = await self.session.list_tools()
        self.tools_cache = response.tools
        return self.tools_cache

    async def call_tool(self, tool_name: str, args: dict) -> Any:
        """
        Llama a una herramienta específica en el servidor MCP.
        
        Args:
            tool_name (str): Nombre de la herramienta a llamar
            args (dict): Argumentos para la herramienta
            
        Returns:
            Any: Resultado de la ejecución de la herramienta
            
        Raises:
            RuntimeError: Si no hay una sesión MCP activa
            ValueError: Si la herramienta no existe o hay un error en la ejecución
        """
        if self.session is None:
            raise RuntimeError("La sesión MCP no está inicializada")
        
        try:
            result = await self.session.call_tool(tool_name, args)
            self.logger.info(f"Herramienta '{tool_name}' ejecutada exitosamente")
            return result
        except Exception as e:
            self.logger.error(f"Error ejecutando herramienta '{tool_name}': {str(e)}", exc_info=True)
            raise ValueError(f"Error ejecutando herramienta '{tool_name}': {str(e)}") from e

