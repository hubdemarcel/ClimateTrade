"""
Logging Configuration Module

This module defines the configuration classes and enums for the centralized logging system.
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


class Environment(Enum):
    """Environment types for logging configuration."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class LogConfig:
    """
    Centralized logging configuration.

    This class defines all logging settings including levels, formats, handlers,
    and environment-specific configurations.
    """

    # Environment settings
    environment: Environment = Environment.DEVELOPMENT

    # Base logging level
    level: str = "INFO"

    # Log directory
    log_dir: str = "logs"

    # Application name for log identification
    app_name: str = "climatetrade"

    # Structured logging settings
    enable_structured_logging: bool = True
    enable_json_format: bool = True

    # Console logging settings
    enable_console_logging: bool = True
    console_level: str = "INFO"

    # File logging settings
    enable_file_logging: bool = True
    file_level: str = "DEBUG"
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

    # Log rotation settings
    enable_rotation: bool = True
    rotation_when: str = "midnight"
    rotation_interval: int = 1

    # Compression settings
    enable_compression: bool = True
    compression_method: str = "gzip"

    # Performance settings
    buffer_size: int = 1000
    flush_interval: float = 1.0

    # Custom format strings
    console_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s"
    structured_format: Dict[str, Any] = field(default_factory=lambda: {
        "timestamp": "%(asctime)s",
        "level": "%(levelname)s",
        "logger": "%(name)s",
        "message": "%(message)s",
        "module": "%(module)s",
        "function": "%(funcName)s",
        "line": "%(lineno)d",
        "process": "%(process)d",
        "thread": "%(thread)d"
    })

    # Environment-specific overrides
    env_overrides: Dict[Environment, Dict[str, Any]] = field(default_factory=lambda: {
        Environment.DEVELOPMENT: {
            "level": "DEBUG",
            "console_level": "DEBUG",
            "enable_structured_logging": False,
            "enable_json_format": False
        },
        Environment.TESTING: {
            "level": "DEBUG",
            "console_level": "INFO",
            "enable_structured_logging": True,
            "enable_json_format": True
        },
        Environment.STAGING: {
            "level": "INFO",
            "console_level": "WARNING",
            "enable_structured_logging": True,
            "enable_json_format": True
        },
        Environment.PRODUCTION: {
            "level": "WARNING",
            "console_level": "ERROR",
            "enable_structured_logging": True,
            "enable_json_format": True,
            "max_file_size": 100 * 1024 * 1024,  # 100MB
            "backup_count": 30
        }
    })

    def __post_init__(self):
        """Apply environment-specific overrides after initialization."""
        if self.environment in self.env_overrides:
            overrides = self.env_overrides[self.environment]
            for key, value in overrides.items():
                if hasattr(self, key):
                    setattr(self, key, value)

        # Set log directory based on environment
        if self.environment == Environment.PRODUCTION:
            self.log_dir = "/var/log/climatetrade"
        elif self.environment == Environment.TESTING:
            self.log_dir = "test_logs"
        else:
            self.log_dir = "logs"

        # Ensure log directory exists
        os.makedirs(self.log_dir, exist_ok=True)

    @classmethod
    def from_env(cls, env_var: str = "LOG_ENV") -> 'LogConfig':
        """
        Create configuration from environment variable.

        Args:
            env_var: Environment variable name containing the environment

        Returns:
            LogConfig: Configured logging configuration
        """
        env_value = os.getenv(env_var, "development").lower()
        try:
            environment = Environment(env_value)
        except ValueError:
            environment = Environment.DEVELOPMENT

        return cls(environment=environment)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'LogConfig':
        """
        Create configuration from dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            LogConfig: Configured logging configuration
        """
        # Convert string environment to enum
        if 'environment' in config_dict:
            if isinstance(config_dict['environment'], str):
                config_dict['environment'] = Environment(config_dict['environment'].lower())

        return cls(**config_dict)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dict[str, Any]: Configuration as dictionary
        """
        result = {}
        for key, value in self.__dict__.items():
            if key == 'environment':
                result[key] = value.value
            elif key == 'env_overrides':
                # Convert enum keys to strings
                result[key] = {env.value: overrides for env, overrides in value.items()}
            else:
                result[key] = value
        return result