"""Main MCP server implementation for log search."""
import asyncio
import logging
import sys
from typing import Any, Dict, List

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.lowlevel.server import NotificationOptions
from mcp.types import CallToolResult, TextContent
import mcp.server.stdio

from log_search_mcp.config.manager import ConfigManager
from log_search_mcp.tools.log_search import LogSearchTool
from log_search_mcp.utils.ssh_manager import SSHConnectionManager


logger = logging.getLogger(__name__)

# Global instances
config_manager = ConfigManager()
ssh_manager = SSHConnectionManager()
log_search_tool = LogSearchTool(config_manager, ssh_manager)

# Create the MCP server instance
server = Server("log-search-server", version="0.1.0")


@server.list_tools()
async def list_tools() -> list[Any]:
    """List available tools."""
    return [log_search_tool.get_search_tool()]


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    if name == "search_logs":
        server_name = arguments.get("server_name", "")
        pattern = arguments.get("pattern", "")
        time_range = arguments.get("time_range")
        max_results = arguments.get("max_results")
        
        if server_name.lower() == "all":
            results = await log_search_tool.search_all_logs(
                pattern, time_range, max_results
            )
        else:
            results = await log_search_tool.search_logs(
                server_name, pattern, time_range, max_results
            )
        
        # Create proper CallToolResult with TextContent
        text_content = "\n".join(results) if results else "No results found"
        return CallToolResult(
            content=[TextContent(type="text", text=text_content)]
        )
    
    raise ValueError(f"Unknown tool: {name}")


@server.list_resources()
async def list_resources() -> list[Any]:
    """List available resources (servers)."""
    server_names = config_manager.list_servers()
    return [{
        "uri": f"server://{name}",
        "name": name,
        "description": f"Server configuration for {name}",
        "mimeType": "application/json"
    } for name in server_names]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read server configuration resource."""
    if uri.startswith("server://"):
        server_name = uri[9:]  # Remove "server://" prefix
        try:
            server_config = config_manager.get_server(server_name)
            return server_config.model_dump_json(indent=2)
        except ValueError:
            raise ValueError(f"Server not found: {server_name}")
    
    raise ValueError(f"Unknown resource: {uri}")


async def main(config_path=None):
    """Main entry point for the MCP server."""
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Load configuration
    try:
        if config_path:
            config_manager.config_path = config_path
        config_manager.load_config()
        logger.info(f"Configuration loaded successfully from {config_manager.config_path}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        # Continue with default config
    
    # Start the server
    logger.info("Starting log search MCP server...")
    
    try:
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream=read_stream,
                write_stream=write_stream,
                initialization_options=server.create_initialization_options(
                    notification_options=NotificationOptions(resources_changed=False),
                    experimental_capabilities={}
                )
            )
    except Exception as e:
        logger.error(f"Failed to start MCP server: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise
    finally:
        await ssh_manager.close_all()
        logger.info("Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())