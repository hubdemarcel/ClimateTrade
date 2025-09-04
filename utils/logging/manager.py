"""
Log Manager Module

This module provides the main interface for setting up and managing
the centralized logging system.
"""

import atexit
import logging
import signal
import sys
from typing import Optional, Dict, Any, Union
from .config import LogConfig, Environment
from .factory import LoggerFactory, setup_factory, update_global_config


class LogManager:
    """
    Central log management class.

    This class provides methods for configuring, monitoring, and managing
    the logging system across the application.
    """

    def __init__(self, config: Optional[LogConfig] = None):
        """
        Initialize the log manager.

        Args:
            config: Logging configuration
        """
        self.config = config or LogConfig()
        self.factory = LoggerFactory(self.config)
        self._initialized = False
        self._shutdown_handlers = []

        # Register cleanup handlers
        atexit.register(self.shutdown)
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def setup(self, config: Optional[LogConfig] = None) -> 'LogManager':
        """
        Setup the logging system.

        Args:
            config: New configuration (uses existing if None)

        Returns:
            LogManager: Self for method chaining
        """
        if config:
            self.config = config
            self.factory.update_config(config)

        # Setup the global factory
        setup_factory(self.config)

        # Configure root logger
        self._configure_root_logger()

        # Setup environment-specific handlers
        self._setup_environment_handlers()

        self._initialized = True
        return self

    def _configure_root_logger(self):
        """Configure the root logger with basic settings."""
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.config.level))

        # Remove existing handlers
        root_logger.handlers.clear()

        # Add handlers based on configuration
        if self.config.enable_console_logging:
            console_handler = self._create_console_handler()
            root_logger.addHandler(console_handler)

        if self.config.enable_file_logging:
            file_handler = self._create_file_handler()
            root_logger.addHandler(file_handler)

    def _create_console_handler(self):
        """Create console handler."""
        from .formatters import ConsoleFormatter, StructuredFormatter
        from .handlers import BufferedHandler

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

        # Wrap in buffered handler for better performance
        if self.config.buffer_size > 0:
            from .handlers import BufferedHandler
            handler = BufferedHandler(handler, self.config.buffer_size, self.config.flush_interval)

        return handler

    def _create_file_handler(self):
        """Create file handler with rotation."""
        from .handlers import RotatingFileHandler, StructuredFormatter

        log_file = f"{self.config.log_dir}/{self.config.app_name}.log"

        handler = RotatingFileHandler(
            filename=log_file,
            maxBytes=self.config.max_file_size,
            backupCount=self.config.backup_count,
            compress=self.config.enable_compression
        )

        if self.config.enable_structured_logging and self.config.enable_json_format:
            formatter = StructuredFormatter()
        else:
            formatter = logging.Formatter(self.config.file_format)

        handler.setFormatter(formatter)
        handler.setLevel(getattr(logging, self.config.file_level))
        return handler

    def _setup_environment_handlers(self):
        """Setup environment-specific handlers."""
        from .handlers import EnvironmentHandler

        if self.config.environment == Environment.PRODUCTION:
            # Add additional production handlers
            self._setup_production_handlers()
        elif self.config.environment == Environment.TESTING:
            # Add testing-specific handlers
            self._setup_testing_handlers()

    def _setup_production_handlers(self):
        """Setup production-specific handlers."""
        # Could add syslog, remote logging, etc.
        pass

    def _setup_testing_handlers(self):
        """Setup testing-specific handlers."""
        # Could add test result logging, etc.
        pass

    def get_logger(self, name: str, level: Optional[str] = None):
        """
        Get a configured logger.

        Args:
            name: Logger name
            level: Override level

        Returns:
            logging.Logger: Configured logger
        """
        return self.factory.get_logger(name, level)

    def update_config(self, new_config: LogConfig):
        """
        Update the logging configuration.

        Args:
            new_config: New configuration
        """
        self.config = new_config
        self.factory.update_config(new_config)
        self.setup()

    def add_shutdown_handler(self, handler):
        """
        Add a shutdown handler.

        Args:
            handler: Function to call on shutdown
        """
        self._shutdown_handlers.append(handler)

    def shutdown(self):
        """Shutdown the logging system gracefully."""
        # Call shutdown handlers
        for handler in self._shutdown_handlers:
            try:
                handler()
            except Exception:
                pass

        # Flush all handlers
        logging.shutdown()

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.shutdown()
        sys.exit(0)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.

        Returns:
            Dict[str, Any]: Logging statistics
        """
        return {
            "initialized": self._initialized,
            "environment": self.config.environment.value,
            "level": self.config.level,
            "console_logging": self.config.enable_console_logging,
            "file_logging": self.config.enable_file_logging,
            "structured_logging": self.config.enable_structured_logging,
            "json_format": self.config.enable_json_format,
            "log_directory": self.config.log_dir,
            "max_file_size": self.config.max_file_size,
            "backup_count": self.config.backup_count
        }


# Global manager instance
_manager: Optional[LogManager] = None


def setup_logging(config: Optional[Union[LogConfig, Dict[str, Any], str]] = None) -> LogManager:
    """
    Setup the centralized logging system.

    Args:
        config: Configuration object, dict, or environment string

    Returns:
        LogManager: The configured log manager
    """
    global _manager

    # Convert config to LogConfig object
    if config is None:
        log_config = LogConfig()
    elif isinstance(config, LogConfig):
        log_config = config
    elif isinstance(config, dict):
        log_config = LogConfig.from_dict(config)
    elif isinstance(config, str):
        # Assume it's an environment name
        from .config import Environment
        try:
            env = Environment(config.lower())
            log_config = LogConfig(environment=env)
        except ValueError:
            log_config = LogConfig()
    else:
        log_config = LogConfig()

    if _manager is None:
        _manager = LogManager(log_config)
    else:
        _manager.update_config(log_config)

    return _manager.setup()


def get_log_manager() -> Optional[LogManager]:
    """
    Get the global log manager instance.

    Returns:
        LogManager: Global manager instance or None
    """
    return _manager


def update_logging_config(new_config: Union[LogConfig, Dict[str, Any]]):
    """
    Update the global logging configuration.

    Args:
        new_config: New configuration
    """
    global _manager
    if _manager is None:
        setup_logging(new_config)
    else:
        if isinstance(new_config, dict):
            new_config = LogConfig.from_dict(new_config)
        _manager.update_config(new_config)