"""
Logger Factory Module

This module provides factory functions for creating configured loggers
with consistent settings across the application.
"""

import logging
from typing import Optional, Dict, Any
from .config import LogConfig, Environment
from .formatters import StructuredFormatter, ConsoleFormatter
from .handlers import RotatingFileHandler, EnvironmentHandler


class LoggerFactory:
    """
    Factory for creating configured loggers.

    This factory creates loggers with consistent configuration based on
    the provided LogConfig and optional overrides.
    """

    def __init__(self, config: LogConfig):
        """
        Initialize the logger factory.

        Args:
            config: Logging configuration
        """
        self.config = config
        self._loggers: Dict[str, logging.Logger] = {}

    def get_logger(self,
                   name: str,
                   level: Optional[str] = None,
                   extra_handlers: Optional[list] = None) -> logging.Logger:
        """
        Get or create a configured logger.

        Args:
            name: Logger name (usually __name__)
            level: Override logging level for this logger
            extra_handlers: Additional handlers to add

        Returns:
            logging.Logger: Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]

        # Create logger
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level or self.config.level))

        # Remove existing handlers to avoid duplicates
        logger.handlers.clear()

        # Add console handler if enabled
        if self.config.enable_console_logging:
            console_handler = self._create_console_handler()
            logger.addHandler(console_handler)

        # Add file handler if enabled
        if self.config.enable_file_logging:
            file_handler = self._create_file_handler(name)
            logger.addHandler(file_handler)

        # Add extra handlers
        if extra_handlers:
            for handler in extra_handlers:
                logger.addHandler(handler)

        # Cache the logger
        self._loggers[name] = logger
        return logger

    def _create_console_handler(self) -> logging.Handler:
        """Create console handler with appropriate formatter."""
        handler = logging.StreamHandler()

        if self.config.enable_structured_logging and self.config.enable_json_format:
            formatter = StructuredFormatter()
        else:
            formatter = ConsoleFormatter(
                fmt=self.config.console_format,
                use_colors=(self.config.environment == Environment.DEVELOPMENT)
            )

        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config.console_level))
        return handler

    def _create_file_handler(self, logger_name: str) -> logging.Handler:
        """Create file handler with rotation and compression."""
        # Create log filename based on logger name
        safe_name = logger_name.replace('.', '_').replace('/', '_')
        log_file = f"{self.config.log_dir}/{self.config.app_name}_{safe_name}.log"

        handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            compress=self.config.enable_compression,
            compression_method=self.config.compression_method
        )

        if self.config.enable_structured_logging and self.config.enable_json_format:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(self.config.file_format)

        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config.file_level))
        return handler

    def update_config(self, new_config: LogConfig):
        """
        Update the factory configuration.

        Args:
            new_config: New logging configuration
        """
        self.config = new_config
        # Clear cached loggers so they get recreated with new config
        self._loggers.clear()


# Global factory instance
_factory: Optional[LoggerFactory] = None


def setup_factory(config: Optional[LogConfig] = None):
    """
    Setup the global logger factory.

    Args:
        config: Logging configuration (uses default if None)
    """
    global _factory
    if config is None:
        config = LogConfig()
    _factory = LoggerFactory(config)


def get_logger(name: str,
               level: Optional[str] = None,
               extra_handlers: Optional[list] = None) -> logging.Logger:
    """
    Get a configured logger from the global factory.

    Args:
        name: Logger name (usually __name__)
        level: Override logging level
        extra_handlers: Additional handlers

    Returns:
        logging.Logger: Configured logger instance
    """
    global _factory
    if _factory is None:
        setup_factory()
    return _factory.get_logger(name, level, extra_handlers)


def update_global_config(new_config: LogConfig):
    """
    Update the global factory configuration.

    Args:
        new_config: New logging configuration
    """
    global _factory
    if _factory is None:
        setup_factory(new_config)
    else:
        _factory.update_config(new_config)


def get_factory() -> Optional[LoggerFactory]:
    """
    Get the global logger factory instance.

    Returns:
        LoggerFactory: Global factory instance or None
    """
    return _factory