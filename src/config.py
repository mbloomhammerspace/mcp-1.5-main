"""
Configuration management for the Federated Storage MCP Service.
"""

import os
import yaml
import json
from typing import Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class HammerspaceConfig:
    """Configuration for Hammerspace API connection."""
    base_url: str
    username: str
    password: str
    verify_ssl: bool = True
    timeout: int = 30


class ConfigManager:
    """Manages configuration for the MCP service."""
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_file: Path to the main configuration file. If None, will search for config files.
        """
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Try to find config file in common locations
            possible_configs = [
                "config.json",
                "config/config.yaml", 
                "config/config.json",
                "config.yaml"
            ]
            
            for config_path in possible_configs:
                if Path(config_path).exists():
                    self.config_file = Path(config_path)
                    break
            else:
                # Default fallback
                self.config_file = Path("config/config.yaml")
        
        self.config = {}
        self.active_config_file = Path("config/active_hammerspace.txt")
    
    def load_config(self) -> bool:
        """Load configuration from file.
        
        Returns:
            True if configuration loaded successfully, False otherwise
        """
        try:
            if self.config_file.exists():
                # Determine file type and load accordingly
                if self.config_file.suffix.lower() == '.json':
                    with open(self.config_file, 'r') as f:
                        self.config = json.load(f) or {}
                else:
                    with open(self.config_file, 'r') as f:
                        self.config = yaml.safe_load(f) or {}
                
                # Load the active Hammerspace configuration
                self._load_active_hammerspace_config()
                
                return True
            else:
                print(f"Configuration file not found: {self.config_file}")
                return False
                
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def _load_active_hammerspace_config(self):
        """Load the active Hammerspace configuration from the multi-config system."""
        try:
            if self.active_config_file.exists():
                active_config_name = self.active_config_file.read_text().strip()
                if active_config_name:
                    # Load the active configuration
                    config_dir = Path("config/hammerspace_configs")
                    config_file = config_dir / f"{active_config_name}.yaml"
                    
                    if config_file.exists():
                        with open(config_file, 'r') as f:
                            active_config = yaml.safe_load(f)
                        
                        # Update the main config with the active Hammerspace config
                        if "hammerspace" not in self.config:
                            self.config["hammerspace"] = {}
                        
                        # Merge the active config into the hammerspace section
                        for key, value in active_config.items():
                            if key != "name" and key != "description" and key != "created" and key != "last_modified":
                                self.config["hammerspace"][key] = value
                        
                        print(f"Loaded active Hammerspace configuration: {active_config_name}")
                    else:
                        print(f"Active configuration file not found: {config_file}")
                else:
                    print("No active configuration name found")
            else:
                print("Active configuration file not found, using default config")
                
        except Exception as e:
            print(f"Error loading active Hammerspace configuration: {e}")
    
    def get_config(self) -> Dict[str, Any]:
        """Get the current configuration.
        
        Returns:
            Configuration dictionary
        """
        return self.config
    
    def get_hammerspace_config(self) -> HammerspaceConfig:
        """Get Hammerspace-specific configuration.
        
        Returns:
            HammerspaceConfig object
        """
        # First try to get credentials from WebUI shared storage
        try:
            import sys
            sys.path.append('..')
            from shared_config import shared_config
            
            webui_credentials = shared_config.get_hammerspace_credentials()
            if webui_credentials and webui_credentials.get("username") and webui_credentials.get("password"):
                print("Using Hammerspace credentials from WebUI configuration")
                return HammerspaceConfig(
                    base_url=webui_credentials.get("base_url", ""),
                    username=webui_credentials.get("username", ""),
                    password=webui_credentials.get("password", ""),
                    verify_ssl=bool(webui_credentials.get("verify_ssl", False)),
                    timeout=int(webui_credentials.get("timeout", 30))
                )
        except Exception as e:
            print(f"Could not load WebUI credentials: {e}")
        
        # Fallback to local configuration
        print("Using local Hammerspace configuration")
        hammerspace_config = self.config.get("hammerspace", {})
        return HammerspaceConfig(
            base_url=hammerspace_config.get("base_url", ""),
            username=hammerspace_config.get("username", ""),
            password=hammerspace_config.get("password", ""),
            verify_ssl=hammerspace_config.get("verify_ssl", True),
            timeout=hammerspace_config.get("timeout", 30)
        )
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """Get MCP-specific configuration.
        
        Returns:
            MCP configuration dictionary
        """
        return self.config.get("mcp", {})
    
    def get_dev_config(self) -> Dict[str, Any]:
        """Get development-specific configuration.
        
        Returns:
            Development configuration dictionary
        """
        return self.config.get("development", {})
    
    def save_config(self) -> bool:
        """Save configuration to file.
        
        Returns:
            True if configuration saved successfully, False otherwise
        """
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False
    
    def reload_config(self) -> bool:
        """Reload configuration from file.
        
        Returns:
            True if configuration reloaded successfully, False otherwise
        """
        return self.load_config()


# Global configuration instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get the global configuration instance.
    
    Returns:
        Configuration manager instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


def reload_config() -> bool:
    """Reload the global configuration.
    
    Returns:
        True if configuration reloaded successfully, False otherwise
    """
    global _config_instance
    if _config_instance:
        return _config_instance.reload_config()
    return False 