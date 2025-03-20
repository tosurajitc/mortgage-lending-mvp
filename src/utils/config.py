"""
Configuration management utilities for the Mortgage Lending Assistant.

This module provides functionality to load, validate, and access application configuration.
"""

import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Default configuration files
APP_CONFIG_PATH = "config/app_config.json"
AGENT_CONFIG_PATH = "config/agent_config.json"
SECURITY_CONFIG_PATH = "config/security_config.json"
LOGGING_CONFIG_PATH = "config/logging_config.json"


class ConfigurationError(Exception):
    """Exception raised for configuration errors."""
    pass


class ConfigManager:
    """
    Manages application configuration.
    
    This class provides a centralized way to access configuration settings
    from various configuration files and environment variables.
    """
    
    def __init__(self, app_config_path: str = APP_CONFIG_PATH):
        """
        Initialize the configuration manager.
        
        Args:
            app_config_path: Path to the main application configuration file
        """
        logger.info(f"Initializing configuration manager with {app_config_path}")
        
        self.app_config_path = app_config_path
        self.config_cache = {}
        
        # Load the main application configuration
        self.app_config = self._load_config(app_config_path)
        
        # Cache the config
        self.config_cache[app_config_path] = self.app_config
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """
        Load a configuration file.
        
        Args:
            config_path: Path to the configuration file
            
        Returns:
            Configuration dictionary
            
        Raises:
            ConfigurationError: If the configuration file cannot be loaded
        """
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            logger.info(f"Loaded configuration from {config_path}")
            return config
        except FileNotFoundError:
            error_msg = f"Configuration file not found: {config_path}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in configuration file {config_path}: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"Error loading configuration from {config_path}: {str(e)}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
    
    def get_app_config(self) -> Dict[str, Any]:
        """
        Get the main application configuration.
        
        Returns:
            Application configuration dictionary
        """
        return self.app_config
    
    def get_agent_config(self, agent_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get agent configuration.
        
        Args:
            agent_type: Optional agent type to get configuration for
            
        Returns:
            Agent configuration dictionary
        """
        if AGENT_CONFIG_PATH not in self.config_cache:
            self.config_cache[AGENT_CONFIG_PATH] = self._load_config(AGENT_CONFIG_PATH)
        
        agent_config = self.config_cache[AGENT_CONFIG_PATH]
        
        if agent_type is not None:
            # Return configuration for a specific agent type
            if agent_type in agent_config:
                return agent_config[agent_type]
            else:
                logger.warning(f"Configuration for agent type {agent_type} not found")
                return {}
        
        return agent_config
    
    def get_security_config(self) -> Dict[str, Any]:
        """
        Get security configuration.
        
        Returns:
            Security configuration dictionary
        """
        if SECURITY_CONFIG_PATH not in self.config_cache:
            self.config_cache[SECURITY_CONFIG_PATH] = self._load_config(SECURITY_CONFIG_PATH)
        
        return self.config_cache[SECURITY_CONFIG_PATH]
    
    def get_logging_config(self) -> Dict[str, Any]:
        """
        Get logging configuration.
        
        Returns:
            Logging configuration dictionary
        """
        if LOGGING_CONFIG_PATH not in self.config_cache:
            try:
                self.config_cache[LOGGING_CONFIG_PATH] = self._load_config(LOGGING_CONFIG_PATH)
            except ConfigurationError:
                # Fall back to default logging configuration in app_config
                logging_config = self.app_config.get("logging", {})
                self.config_cache[LOGGING_CONFIG_PATH] = logging_config
        
        return self.config_cache[LOGGING_CONFIG_PATH]
    
    def get_value(self, key_path: str, default: Any = None) -> Any:
        """
        Get a configuration value using a dot-notation path.
        
        Args:
            key_path: Dot-notation path to the configuration value
            default: Default value to return if not found
            
        Returns:
            Configuration value
        """
        # Split the key path into parts
        parts = key_path.split('.')
        
        # Start with the main app config
        config = self.app_config
        
        # Navigate the path
        for part in parts[:-1]:
            if part in config:
                config = config[part]
            else:
                return default
        
        # Get the final value
        return config.get(parts[-1], default)
    
    def get_azure_config(self, service: Optional[str] = None) -> Dict[str, Any]:
        """
        Get Azure service configuration.
        
        Args:
            service: Optional Azure service name
            
        Returns:
            Azure configuration dictionary
        """
        azure_config = self.app_config.get("azure", {})
        
        if service is not None:
            # Return configuration for a specific Azure service
            if service in azure_config:
                return azure_config[service]
            else:
                logger.warning(f"Configuration for Azure service {service} not found")
                return {}
        
        return azure_config
    
    def get_environment_variable(self, var_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get an environment variable.
        
        Args:
            var_name: Name of the environment variable
            default: Default value to return if not found
            
        Returns:
            Environment variable value
        """
        return os.environ.get(var_name, default)
    
    def get_connection_string(self, service_name: str) -> str:
        """
        Get a connection string for a service.
        
        Args:
            service_name: Name of the service
            
        Returns:
            Connection string
            
        Raises:
            ConfigurationError: If the connection string cannot be found
        """
        # First check if it's defined as an environment variable
        env_var_name = f"{service_name.upper()}_CONNECTION_STRING"
        conn_string = self.get_environment_variable(env_var_name)
        
        if conn_string:
            return conn_string
        
        # Check in Azure configuration
        azure_config = self.get_azure_config(service_name)
        if "connection_string" in azure_config:
            return azure_config["connection_string"]
        
        # If not found, try to construct it from endpoint and key
        if "endpoint" in azure_config:
            endpoint = azure_config["endpoint"]
            
            # Get the key from environment variable
            key_env_var = f"AZURE_{service_name.upper()}_KEY"
            key = self.get_environment_variable(key_env_var)
            
            if key:
                # Different services have different connection string formats
                if service_name == "openai":
                    return f"endpoint={endpoint};key={key}"
                elif service_name == "cosmos_db":
                    return f"AccountEndpoint={endpoint};AccountKey={key};"
                elif service_name == "document_intelligence":
                    return f"endpoint={endpoint};key={key}"
        
        # If we couldn't construct a connection string, raise an error
        error_msg = f"Could not find or construct connection string for {service_name}"
        logger.error(error_msg)
        raise ConfigurationError(error_msg)
    
    def validate_configuration(self) -> bool:
        """
        Validate the application configuration.
        
        Returns:
            True if the configuration is valid, False otherwise
        """
        try:
            # Check for required configuration sections
            required_sections = ["application", "azure", "logging"]
            for section in required_sections:
                if section not in self.app_config:
                    logger.error(f"Required configuration section '{section}' is missing")
                    return False
            
            # Check for required Azure services
            required_azure_services = ["openai", "document_intelligence", "cosmos_db"]
            azure_config = self.app_config.get("azure", {})
            for service in required_azure_services:
                if service not in azure_config:
                    logger.error(f"Required Azure service configuration '{service}' is missing")
                    return False
            
            # Additional validation could be added here
            
            logger.info("Configuration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {str(e)}")
            return False
    
    def is_development_mode(self) -> bool:
        """
        Check if the application is running in development mode.
        
        Returns:
            True if in development mode, False otherwise
        """
        env = self.app_config.get("application", {}).get("environment", "").lower()
        return env == "development"
    
    def is_mock_mode(self) -> bool:
        """
        Check if the application is running in mock mode.
        
        Returns:
            True if in mock mode, False otherwise
        """
        return self.get_environment_variable("USE_MOCK_SERVICES", "false").lower() == "true"


# Singleton instance
_config_manager = None


def get_config_manager() -> ConfigManager:
    """
    Get the singleton config manager instance.
    
    Returns:
        Config manager instance
    """
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager