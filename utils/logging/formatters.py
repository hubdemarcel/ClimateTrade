"""
Logging Formatters Module

This module provides custom formatters for different logging needs including
structured JSON logging and colored console output.
"""

import json
import logging
import sys
from datetime import datetime
from typing import Dict, Any, Optional


class StructuredFormatter(logging.Formatter):
    """
    Structured JSON formatter for better log analysis.

    This formatter outputs logs in JSON format with consistent structure,
    making it easier to parse and analyze logs with tools like ELK stack.
    """

    def __init__(self,
                 fmt_dict: Optional[Dict[str, str]] = None,
                 datefmt: Optional[str] = None):
        """
        Initialize the structured formatter.

        Args:
            fmt_dict: Dictionary defining the log format structure
            datefmt: Date format string
        """
        super().__init__()
        self.fmt_dict = fmt_dict or {
            "timestamp": "%(asctime)s",
            "level": "%(levelname)s",
            "logger": "%(name)s",
            "message": "%(message)s",
            "module": "%(module)s",
            "function": "%(funcName)s",
            "line": "%(lineno)d",
            "process": "%(process)d",
            "thread": "%(thread)d"
        }
        self.datefmt = datefmt or "%Y-%m-%dT%H:%M:%S.%fZ"

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record as JSON.

        Args:
            record: Log record to format

        Returns:
            str: JSON formatted log entry
        """
        # Create the basic log entry
        log_entry = {
            "timestamp": datetime.utcnow().strftime(self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process": record.process,
            "thread": record.thread
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, '__dict__'):
            for key, value in record.__dict__.items():
                if key not in ['name', 'msg', 'args', 'levelname', 'levelno',
                             'pathname', 'filename', 'module', 'exc_info',
                             'exc_text', 'stack_info', 'lineno', 'funcName',
                             'created', 'msecs', 'relativeCreated', 'thread',
                             'threadName', 'processName', 'process', 'message']:
                    log_entry[key] = value

        return json.dumps(log_entry, default=str, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    """
    Enhanced console formatter with colors and better readability.

    This formatter provides colored output for console logging with
    configurable colors for different log levels.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
        'RESET': '\033[0m'        # Reset
    }

    def __init__(self,
                 fmt: Optional[str] = None,
                 datefmt: Optional[str] = None,
                 use_colors: bool = True):
        """
        Initialize the console formatter.

        Args:
            fmt: Format string
            datefmt: Date format string
            use_colors: Whether to use ANSI colors
        """
        self.use_colors = use_colors and self._supports_color()
        self.fmt = fmt or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        self.datefmt = datefmt or "%H:%M:%S"

        super().__init__(fmt=self.fmt, datefmt=self.datefmt)

    def _supports_color(self) -> bool:
        """
        Check if the terminal supports ANSI colors.

        Returns:
            bool: True if colors are supported
        """
        # Check if output is a TTY and not Windows without colorama
        if hasattr(sys.stdout, 'isatty'):
            return sys.stdout.isatty()
        return False

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record with optional colors.

        Args:
            record: Log record to format

        Returns:
            str: Formatted log entry
        """
        # Get the original formatted message
        message = super().format(record)

        if self.use_colors:
            level_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            reset_color = self.COLORS['RESET']

            # Color the level name
            colored_level = f"{level_color}{record.levelname}{reset_color}"
            message = message.replace(record.levelname, colored_level)

        return message


class CompactFormatter(logging.Formatter):
    """
    Compact formatter for high-volume logging.

    This formatter provides a more compact format suitable for high-volume
    logging scenarios where readability is less critical than brevity.
    """

    def __init__(self, datefmt: Optional[str] = None):
        """
        Initialize the compact formatter.

        Args:
            datefmt: Date format string
        """
        fmt = "%(asctime)s|%(levelname)s|%(name)s|%(message)s"
        datefmt = datefmt or "%Y%m%d %H%M%S"
        super().__init__(fmt=fmt, datefmt=datefmt)

    def format(self, record: logging.LogRecord) -> str:
        """
        Format the log record in compact format.

        Args:
            record: Log record to format

        Returns:
            str: Compact formatted log entry
        """
        return super().format(record)