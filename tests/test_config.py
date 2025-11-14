"""Tests for configuration management."""
import tempfile
from pathlib import Path

import pytest

from log_search_mcp.config.manager import ConfigManager
from log_search_mcp.models.config import ServerConfig


class TestConfigManager:
    """Test configuration manager functionality."""
    
    def test_load_config_file_not_found(self):
        """Test loading configuration when file doesn't exist."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "nonexistent.toml"
            manager = ConfigManager(config_path)
            
            # Should create default config when file doesn't exist
            config = manager.load_config()
            
            assert config is not None
            assert config.servers == {}
            assert config.default_timeout == 30
            assert config.max_results == 100
    
    def test_save_and_load_config(self):
        """Test saving and loading configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            manager = ConfigManager(config_path)
            
            # Create initial config
            initial_config = manager.load_config()
            
            # Add a server
            server_config = ServerConfig(
                name="test-server",
                hostname="test.example.com",
                username="testuser",
                app_name="testapp"
            )
            manager.add_server(server_config)
            
            # Create new manager and load config
            new_manager = ConfigManager(config_path)
            loaded_config = new_manager.load_config()
            
            assert loaded_config.servers["test-server"].hostname == "test.example.com"
            assert loaded_config.servers["test-server"].username == "testuser"
            assert loaded_config.servers["test-server"].app_name == "testapp"
    
    def test_add_remove_server(self):
        """Test adding and removing servers."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            manager = ConfigManager(config_path)
            manager.load_config()
            
            # Add server
            server_config = ServerConfig(
                name="test-server",
                hostname="test.example.com",
                username="testuser",
                app_name="testapp"
            )
            manager.add_server(server_config)
            
            assert "test-server" in manager.list_servers()
            assert manager.get_server("test-server").hostname == "test.example.com"
            
            # Remove server
            manager.remove_server("test-server")
            assert "test-server" not in manager.list_servers()
            
            # Try to remove non-existent server
            with pytest.raises(ValueError, match="Server 'nonexistent' not found"):
                manager.remove_server("nonexistent")
    
    def test_update_server(self):
        """Test updating server configuration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "test_config.toml"
            manager = ConfigManager(config_path)
            manager.load_config()
            
            # Add initial server
            server_config = ServerConfig(
                name="test-server",
                hostname="test.example.com",
                username="testuser",
                app_name="testapp"
            )
            manager.add_server(server_config)
            
            # Update server
            updated_config = ServerConfig(
                name="test-server",
                hostname="updated.example.com",
                username="testuser",
                app_name="testapp"
            )
            manager.update_server(updated_config)
            
            assert manager.get_server("test-server").hostname == "updated.example.com"
            
            # Try to update non-existent server
            with pytest.raises(ValueError, match="Server 'nonexistent' not found"):
                nonexistent_config = ServerConfig(
                    name="nonexistent",
                    hostname="test.example.com",
                    username="testuser",
                    app_name="testapp"
                )
                manager.update_server(nonexistent_config)
    
    def test_server_config_validation(self):
        """Test server configuration validation."""
        # Test valid configuration
        valid_config = ServerConfig(
            name="test-server",
            hostname="test.example.com",
            username="testuser",
            app_name="testapp"
        )
        assert valid_config.name == "test-server"
        
        # Test missing required fields
        with pytest.raises(ValueError):
            ServerConfig(
                name="test-server",
                # Missing hostname, username, app_name
            )