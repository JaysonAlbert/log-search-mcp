"""Log search tools for the MCP server."""
import asyncio
import logging
import re
from datetime import datetime, timedelta
from typing import List, Optional

from mcp import Tool

from log_search_mcp.config.manager import ConfigManager
from log_search_mcp.models.config import ServerConfig
from log_search_mcp.utils.ssh_manager import SSHConnectionManager


logger = logging.getLogger(__name__)


class LogSearchTool:
    """Tool for searching logs on remote servers."""
    
    def __init__(self, config_manager: ConfigManager, ssh_manager: SSHConnectionManager):
        self.config_manager = config_manager
        self.ssh_manager = ssh_manager
    
    def _build_grep_command(
        self,
        pattern: str,
        server_config: ServerConfig,
        time_range: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> str:
        """Build grep command for searching logs."""
        # Use custom log paths if specified, otherwise use default paths
        if server_config.log_paths:
            log_files = server_config.log_paths
        else:
            log_files = [
                f"/opt/logs/{server_config.app_name}/{server_config.app_name}.log",
                f"/opt/logs/{server_config.app_name}/{server_config.app_name}.bee.log"
            ]
        
        # Build grep command with pattern and files
        grep_cmd = f"grep -n -E '{pattern}' {' '.join(log_files)}"
        
        # Add time range filtering if specified
        if time_range:
            time_filter = self._parse_time_range(time_range)
            if time_filter:
                grep_cmd += f" | {time_filter}"
        
        # Add result limiting
        if max_results:
            grep_cmd += f" | head -n {max_results}"
        
        # Add error handling
        command = f"{grep_cmd} 2>/dev/null || true"
        return command
    
    def _parse_time_range(self, time_range: str) -> Optional[str]:
        """Parse time range string and build awk filter for time range matching."""
        # Support formats like "1h", "30m", "2d", "2024-01-01 to 2024-01-02"
        time_range = time_range.lower().strip()
        
        # Relative time ranges
        if time_range.endswith('h'):
            hours = int(time_range[:-1])
            cutoff_time = datetime.now() - timedelta(hours=hours)
            cutoff_timestamp = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
            # Use awk to compare timestamps - match lines with timestamp >= cutoff_time
            return f"awk 'match($0, /[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}/) {{ timestamp = substr($0, RSTART, RLENGTH); if (timestamp >= \"{cutoff_timestamp}\") print }}'"
        
        elif time_range.endswith('m'):
            minutes = int(time_range[:-1])
            cutoff_time = datetime.now() - timedelta(minutes=minutes)
            cutoff_timestamp = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
            return f"awk 'match($0, /[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}/) {{ timestamp = substr($0, RSTART, RLENGTH); if (timestamp >= \"{cutoff_timestamp}\") print }}'"
        
        elif time_range.endswith('d'):
            days = int(time_range[:-1])
            # Use full timestamp comparison so "1d" means last 24 hours (not only the cutoff date)
            cutoff_time = datetime.now() - timedelta(days=days)
            cutoff_timestamp = cutoff_time.strftime("%Y-%m-%d %H:%M:%S")
            # Use awk to compare timestamps - match lines with timestamp >= cutoff_time
            return f"awk 'match($0, /[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}/) {{ timestamp = substr($0, RSTART, RLENGTH); if (timestamp >= \"{cutoff_timestamp}\") print }}'"
        
        # Absolute time range
        elif ' to ' in time_range:
            start_str, end_str = time_range.split(' to ', 1)
            try:
                start_time = datetime.fromisoformat(start_str.strip())
                end_time = datetime.fromisoformat(end_str.strip())
                start_timestamp = start_time.strftime("%Y-%m-%d %H:%M:%S")
                end_timestamp = end_time.strftime("%Y-%m-%d %H:%M:%S")
                # Use awk for precise time range matching
                return f"awk 'match($0, /[0-9]{{4}}-[0-9]{{2}}-[0-9]{{2}} [0-9]{{2}}:[0-9]{{2}}:[0-9]{{2}}/) {{ timestamp = substr($0, RSTART, RLENGTH); if (timestamp >= \"{start_timestamp}\" && timestamp <= \"{end_timestamp}\") print }}'"
            except ValueError:
                logger.warning(f"Invalid time range format: {time_range}")
                return None
        
        return None
    
    async def search_logs(
        self,
        server_name: str,
        pattern: str,
        time_range: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[str]:
        """Search logs on a specific server."""
        try:
            server_config = self.config_manager.get_server(server_name)
            config = self.config_manager.get_config()
            
            # Use provided max_results or default from config
            max_results = max_results or config.max_results
            
            command = self._build_grep_command(pattern, server_config, time_range, max_results)
            logger.info(f"Executing command on {server_name}: {command}")
            
            result = await self.ssh_manager.execute_command(
                server_config, 
                command, 
                timeout=config.default_timeout
            )
            
            if not result.strip():
                return [f"No results found for pattern '{pattern}' on {server_name}"]
            
            # Parse and format results
            lines = result.strip().split('\n')
            formatted_results = []
            
            for line in lines:
                if line.strip():
                    # Add server name prefix to each result line
                    formatted_results.append(f"[{server_name}] {line}")
            
            return formatted_results[:max_results]
            
        except Exception as e:
            logger.error(f"Log search failed on {server_name}: {e}")
            return [f"Error searching logs on {server_name}: {str(e)}"]
    
    async def search_all_logs(
        self,
        pattern: str,
        time_range: Optional[str] = None,
        max_results: Optional[int] = None
    ) -> List[str]:
        """Search logs on all configured servers concurrently."""
        server_names = self.config_manager.list_servers()
        
        if not server_names:
            return ["No servers configured"]
        
        # Search all servers concurrently
        tasks = []
        for server_name in server_names:
            task = self.search_logs(server_name, pattern, time_range, max_results)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine and format results
        all_results = []
        for i, result in enumerate(results):
            server_name = server_names[i]
            
            if isinstance(result, Exception):
                all_results.append(f"[{server_name}] Error: {str(result)}")
            else:
                all_results.extend(result)
        
        return all_results
    
    def get_search_tool(self) -> Tool:
        """Get the MCP tool for log search."""
        return Tool(
            name="search_logs",
            description="Search application logs on remote servers using grep patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "server_name": {
                        "type": "string",
                        "description": "Name of the server to search (use 'all' for all servers)"
                    },
                    "pattern": {
                        "type": "string",
                        "description": "Grep pattern to search for in logs"
                    },
                    "time_range": {
                        "type": "string",
                        "description": "Time range filter (e.g., '1h', '30m', '2d', '2024-01-01 to 2024-01-02')",
                        "nullable": True
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return per server",
                        "nullable": True
                    }
                },
                "required": ["server_name", "pattern"]
            }
        )