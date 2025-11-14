#!/usr/bin/env python3
"""Main entry point for the log search MCP server."""
import argparse
import asyncio
import sys
from pathlib import Path

from log_search_mcp.server import main as server_main


def main():
    """Synchronous entry point for the log search MCP server."""
    parser = argparse.ArgumentParser(description="Log Search MCP Server")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path("log_search_config.toml"),
        help="Path to configuration file (default: log_search_config.toml)"
    )
    
    args = parser.parse_args()
    
    try:
        asyncio.run(server_main(config_path=args.config))
    except KeyboardInterrupt:
        print("Server stopped by user", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
