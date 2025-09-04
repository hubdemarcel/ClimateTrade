"""
ClimaTrade Centralized Logging System

This module provides a comprehensive, production-ready logging system for the ClimaTrade AI project.

## Features

- **Centralized Configuration**: Single configuration system for all logging
- **Environment-Specific Settings**: Different configurations for development, testing, staging, and production
- **Structured Logging**: JSON format for better log analysis and monitoring
- **Log Rotation**: Automatic log rotation with configurable size limits and retention
- **Compression**: Optional gzip compression for rotated log files
- **Multiple Handlers**: Console, file, and custom handlers support
- **Performance Optimization**: Buffered and asynchronous logging options
- **Backward Compatibility**: Drop-in replacement for existing logging calls

## Quick Start

### Basic Setup

```python
from utils.logging import setup_logging, get_logger

# Setup centralized logging
setup_logging()

# Get a logger for your module
logger = get_logger(__name__)
logger.info("Application started")
```

### Environment-Specific Configuration

```python
from utils.logging import setup_logging, Environment

# Setup for production
setup_logging('production')

# Or with custom configuration
from utils.logging import LogConfig
config = LogConfig(
    environment=Environment.PRODUCTION,
    level='WARNING',
    enable_structured_logging=True,
    enable_json_format=True
)
setup_logging(config)
```

### Advanced Configuration

```python
from utils.logging import LogConfig, Environment, setup_logging

config = LogConfig(
    environment=Environment.DEVELOPMENT,
    level='DEBUG',
    log_dir='custom_logs',
    max_file_size=50*1024*1024,  # 50MB
    backup_count=10,
    enable_compression=True,
    enable_structured_logging=True
)

setup_logging(config)
```

## Configuration Options

### LogConfig Parameters

- `environment`: Environment type (DEVELOPMENT, TESTING, STAGING, PRODUCTION)
- `level`: Base logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `log_dir`: Directory for log files
- `app_name`: Application name for log file naming
- `enable_structured_logging`: Enable structured JSON logging
- `enable_json_format`: Use JSON format for logs
- `enable_console_logging`: Enable console output
- `console_level`: Logging level for console output
- `enable_file_logging`: Enable file logging
- `file_level`: Logging level for file output
- `max_file_size`: Maximum log file size before rotation (bytes)
- `backup_count`: Number of backup files to keep
- `enable_rotation`: Enable log rotation
- `enable_compression`: Compress rotated log files
- `buffer_size`: Buffer size for performance optimization
- `flush_interval`: Flush interval for buffered logging

### Environment Overrides

Each environment has specific default overrides:

- **DEVELOPMENT**: DEBUG level, colored console output, no JSON format
- **TESTING**: INFO level, structured logging enabled
- **STAGING**: WARNING level, structured logging enabled
- **PRODUCTION**: WARNING level, optimized for performance and monitoring

## Usage Examples

### Basic Logging

```python
from utils.logging import get_logger

logger = get_logger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### Structured Logging

```python
from utils.logging import get_logger

logger = get_logger(__name__)

# Structured data will be included in JSON logs
logger.info("User login", extra={
    'user_id': 12345,
    'ip_address': '192.168.1.1',
    'user_agent': 'Mozilla/5.0...'
})

# Exception logging
try:
    risky_operation()
except Exception as e:
    logger.error("Operation failed", exc_info=True, extra={
        'operation': 'risky_operation',
        'error_code': 'OP_FAILED'
    })
```

### Custom Handlers

```python
from utils.logging import get_logger
import logging

# Create custom handler
custom_handler = logging.StreamHandler()
custom_handler.setLevel(logging.ERROR)

# Get logger with custom handler
logger = get_logger(__name__, extra_handlers=[custom_handler])
```

## Log Format Examples

### Console Format (Development)

```
2024-01-15 10:30:45 - my_module - INFO - User logged in
```

### JSON Format (Production)

```json
{
  "timestamp": "2024-01-15T10:30:45.123456Z",
  "level": "INFO",
  "logger": "my_module",
  "message": "User logged in",
  "module": "my_module",
  "function": "login",
  "line": 42,
  "process": 1234,
  "thread": 5678,
  "user_id": 12345,
  "ip_address": "192.168.1.1"
}
```

## Migration Guide

### From basicConfig

**Before:**

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
```

**After:**

```python
from utils.logging import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)
```

### From File Handlers

**Before:**

```python
import logging

logger = logging.getLogger(__name__)
handler = logging.FileHandler('app.log')
logger.addHandler(handler)
```

**After:**

```python
from utils.logging import get_logger

logger = get_logger(__name__)  # File logging configured automatically
```

## Performance Considerations

- Use buffered logging for high-volume applications
- Enable compression for production environments
- Configure appropriate log levels to reduce overhead
- Use asynchronous handlers for non-blocking logging

## Monitoring and Analysis

The structured JSON format enables easy integration with monitoring tools:

- **ELK Stack**: Elasticsearch, Logstash, Kibana
- **Splunk**: Enterprise log analysis
- **Grafana + Loki**: Cloud-native logging
- **Datadog**: Application monitoring
- **Custom dashboards**: JSON format supports custom analytics

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check log levels and handler configuration
2. **Permission errors**: Ensure write permissions for log directory
3. **Performance issues**: Adjust buffer size and flush intervals
4. **Large log files**: Configure appropriate rotation settings

### Debug Mode

Enable debug logging to troubleshoot configuration issues:

```python
import logging
logging.getLogger('utils.logging').setLevel(logging.DEBUG)
```

## API Reference

### Functions

- `setup_logging(config=None)`: Setup the logging system
- `get_logger(name, level=None, extra_handlers=None)`: Get a configured logger
- `update_logging_config(new_config)`: Update global configuration

### Classes

- `LogConfig`: Configuration class
- `LoggerFactory`: Logger factory class
- `LogManager`: Central management class
- `StructuredFormatter`: JSON formatter
- `ConsoleFormatter`: Colored console formatter
- `RotatingFileHandler`: Enhanced file handler with compression

## Version History

- **1.0.0**: Initial release with full feature set
  - Centralized configuration
  - Environment-specific settings
  - Structured JSON logging
  - Log rotation and compression
  - Performance optimizations
  - Backward compatibility
    """
