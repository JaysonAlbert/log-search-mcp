"""Configuration models for the log search MCP server."""
from typing import Optional
from pydantic import BaseModel, Field


class ServerConfig(BaseModel):
    """Configuration for a single application server."""
    
    name: str = Field(..., description="Unique name for the server")
    hostname: str = Field(..., description="Server hostname or IP address")
    port: int = Field(22, description="SSH port (default: 22)")
    username: str = Field(..., description="SSH username")
    private_key_path: Optional[str] = Field(None, description="Path to private key file")
    password: Optional[str] = Field(None, description="SSH password (use key-based auth preferred)")
    app_name: str = Field(..., description="Application name for log file paths")
    log_paths: Optional[list[str]] = Field(None, description="Custom log file paths (overrides default paths)")
    timeout: int = Field(30, description="SSH connection timeout in seconds")
    
    class Config:
        """Pydantic configuration."""
        frozen = True  # Make instances immutable


class LogSearchConfig(BaseModel):
    """Configuration for log search operations."""
    
    servers: dict[str, ServerConfig] = Field(default_factory=dict, description="Configured servers")
    default_timeout: int = Field(30, description="Default search timeout in seconds")
    max_results: int = Field(100, description="Maximum number of results to return per search")
    
    class Config:
        """Pydantic configuration."""
        frozen = True