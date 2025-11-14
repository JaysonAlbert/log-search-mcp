"""Configuration management for the log search MCP server."""
import logging
from pathlib import Path
from typing import Optional

import toml

from log_search_mcp.models.config import LogSearchConfig, ServerConfig


logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration loading, validation, and persistence."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = Path(config_path) if config_path else Path("log_search_config.toml")
        self._config: Optional[LogSearchConfig] = None
    
    def load_config(self) -> LogSearchConfig:
        """Load configuration from TOML file."""
        if not self.config_path.exists():
            logger.info(f"Configuration file not found at {self.config_path}, creating default")
            self._config = LogSearchConfig()
            self.save_config()
            return self._config
        
        try:
            config_data = toml.load(self.config_path)
            servers = {}
            
            # Parse server configurations
            for server_name, server_data in config_data.get("servers", {}).items():
                # Handle log_paths as list if it's a string (comma-separated)
                if "log_paths" in server_data and isinstance(server_data["log_paths"], str):
                    server_data["log_paths"] = [path.strip() for path in server_data["log_paths"].split(",")]
                # Handle file_age_limit if present
                if "file_age_limit" in server_data and isinstance(server_data["file_age_limit"], str):
                    server_data["file_age_limit"] = int(server_data["file_age_limit"])
                servers[server_name] = ServerConfig(name=server_name, **server_data)
            
            # Create main config
            self._config = LogSearchConfig(
                servers=servers,
                default_timeout=config_data.get("default_timeout", 30),
                max_results=config_data.get("max_results", 100)
            )
            
            logger.info(f"Loaded configuration from {self.config_path}")
            return self._config
            
        except Exception as e:
            logger.error(f"Failed to load configuration from {self.config_path}: {e}")
            raise ValueError(f"Invalid configuration file: {e}")
    
    def save_config(self) -> None:
        """Save current configuration to TOML file."""
        if self._config is None:
            raise ValueError("No configuration loaded")
        
        config_data = {
            "default_timeout": self._config.default_timeout,
            "max_results": self._config.max_results,
            "servers": {}
        }
        
        for server_name, server_config in self._config.servers.items():
            server_data = server_config.model_dump(exclude={"name"})
            config_data["servers"][server_name] = server_data
        
        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.config_path, "w") as f:
            toml.dump(config_data, f)
        
        logger.info(f"Saved configuration to {self.config_path}")
    
    def get_config(self) -> LogSearchConfig:
        """Get current configuration, loading if necessary."""
        if self._config is None:
            return self.load_config()
        return self._config
    
    def add_server(self, server_config: ServerConfig) -> None:
        """Add a new server configuration."""
        config = self.get_config()
        if server_config.name in config.servers:
            raise ValueError(f"Server '{server_config.name}' already exists")
        
        # Create new config with added server
        new_servers = config.servers.copy()
        new_servers[server_config.name] = server_config
        
        self._config = LogSearchConfig(
            servers=new_servers,
            default_timeout=config.default_timeout,
            max_results=config.max_results
        )
        
        self.save_config()
        logger.info(f"Added server configuration: {server_config.name}")
    
    def remove_server(self, server_name: str) -> None:
        """Remove a server configuration."""
        config = self.get_config()
        if server_name not in config.servers:
            raise ValueError(f"Server '{server_name}' not found")
        
        # Create new config without the server
        new_servers = config.servers.copy()
        del new_servers[server_name]
        
        self._config = LogSearchConfig(
            servers=new_servers,
            default_timeout=config.default_timeout,
            max_results=config.max_results
        )
        
        self.save_config()
        logger.info(f"Removed server configuration: {server_name}")
    
    def update_server(self, server_config: ServerConfig) -> None:
        """Update an existing server configuration."""
        config = self.get_config()
        if server_config.name not in config.servers:
            raise ValueError(f"Server '{server_config.name}' not found")
        
        # Create new config with updated server
        new_servers = config.servers.copy()
        new_servers[server_config.name] = server_config
        
        self._config = LogSearchConfig(
            servers=new_servers,
            default_timeout=config.default_timeout,
            max_results=config.max_results
        )
        
        self.save_config()
        logger.info(f"Updated server configuration: {server_config.name}")
    
    def list_servers(self) -> list[str]:
        """List all configured server names."""
        config = self.get_config()
        return list(config.servers.keys())
    
    def get_server(self, server_name: str) -> ServerConfig:
        """Get configuration for a specific server."""
        config = self.get_config()
        if server_name not in config.servers:
            raise ValueError(f"Server '{server_name}' not found")
        return config.servers[server_name]