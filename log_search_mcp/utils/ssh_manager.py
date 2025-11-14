"""SSH connection manager for remote server operations."""
import asyncio
import logging
from typing import Optional
from pathlib import Path

import asyncssh

from log_search_mcp.models.config import ServerConfig


logger = logging.getLogger(__name__)


class SSHConnectionManager:
    """Manages SSH connections to remote servers."""
    
    def __init__(self):
        self._connections: dict[str, asyncssh.SSHClientConnection] = {}
    
    async def connect(self, server_config: ServerConfig) -> asyncssh.SSHClientConnection:
        """Establish SSH connection to a server."""
        server_name = server_config.name
        
        if server_name in self._connections:
            # Check if connection is still alive
            try:
                conn = self._connections[server_name]
                if not conn.is_closing():
                    return conn
            except Exception:
                # Connection is dead, remove it
                del self._connections[server_name]
        
        # Create new connection
        connection_kwargs = {
            "host": server_config.hostname,
            "port": server_config.port,
            "username": server_config.username,
            "connect_timeout": server_config.timeout,
        }
        
        # Add authentication method
        if server_config.private_key_path:
            connection_kwargs["client_keys"] = [server_config.private_key_path]
        elif server_config.password:
            connection_kwargs["password"] = server_config.password
        else:
            raise ValueError("Either private_key_path or password must be provided")
        
        try:
            conn = await asyncssh.connect(**connection_kwargs)
            self._connections[server_name] = conn
            logger.info(f"Connected to server: {server_name}")
            return conn
        except asyncssh.Error as e:
            logger.error(f"Failed to connect to {server_name}: {e}")
            raise ConnectionError(f"Failed to connect to {server_name}: {e}")
    
    async def execute_command(
        self, 
        server_config: ServerConfig, 
        command: str,
        timeout: Optional[int] = None
    ) -> str:
        """Execute a command on the remote server."""
        conn = await self.connect(server_config)
        
        try:
            result = await asyncio.wait_for(
                conn.run(command, check=True),
                timeout=timeout or server_config.timeout
            )
            return result.stdout
        except asyncio.TimeoutError:
            logger.error(f"Command timeout on {server_config.name}: {command}")
            raise TimeoutError(f"Command execution timed out on {server_config.name}")
        except asyncssh.Error as e:
            logger.error(f"Command failed on {server_config.name}: {e}")
            raise RuntimeError(f"Command failed on {server_config.name}: {e}")
    
    async def close_connection(self, server_name: str) -> None:
        """Close connection to a specific server."""
        if server_name in self._connections:
            try:
                await self._connections[server_name].close()
            except Exception:
                pass  # Ignore errors during close
            del self._connections[server_name]
            logger.info(f"Closed connection to server: {server_name}")
    
    async def close_all(self) -> None:
        """Close all SSH connections."""
        for server_name in list(self._connections.keys()):
            await self.close_connection(server_name)
    
    def get_connection_status(self) -> dict[str, str]:
        """Get status of all connections."""
        status = {}
        for server_name, conn in self._connections.items():
            status[server_name] = "connected" if not conn.is_closing() else "disconnected"
        return status