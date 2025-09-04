"""
ClimaTrade Centralized Logging System

This module provides centralized logging configuration and utilities for the ClimaTrade AI project.
It includes structured logging, log rotation, and environment-specific configurations.

Main Components:
- LoggerFactory: Creates configured loggers for different modules
- StructuredFormatter: JSON formatter for better log analysis
- LogManager: Central configuration and management
- Environment-specific handlers and formatters

Usage:
    from utils.logging import get_logger, setup_logging

    # Setup centralized logging
    setup_logging(environment='development')

    # Get a logger for your module
    logger = get_logger(__name__)
    logger.info("Application started")
"""

from .config import LogConfig, Environment
from .factory import LoggerFactory, get_logger
from .formatters import StructuredFormatter, ConsoleFormatter
from .handlers import RotatingFileHandler, EnvironmentHandler
from .manager import LogManager, setup_logging

__all__ = [
    'LogConfig',
    'Environment',
    'LoggerFactory',
    'get_logger',
    'StructuredFormatter',
    'ConsoleFormatter',
    'RotatingFileHandler',
    'EnvironmentHandler',
    'LogManager',
    'setup_logging'
]

__version__ = "1.0.0"