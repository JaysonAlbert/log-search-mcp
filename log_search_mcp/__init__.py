"""MCP server for searching application logs across multiple servers using SSH."""
# Import only the models to avoid dependency issues in basic testing
from .models.config import ServerConfig, LogSearchConfig

__version__ = "0.1.0"
__all__ = ["ServerConfig", "LogSearchConfig"]