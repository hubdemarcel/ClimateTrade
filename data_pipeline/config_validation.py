#!/usr/bin/env python3
"""
Configuration Validation Module

This module provides comprehensive validation for configuration files including:
- JSON configuration validation
- YAML configuration validation
- Environment variable validation
- Schema-based validation
- Environment-specific rules
"""

import logging
import os
import json
import re
from typing import Dict, List, Any, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import yaml

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    ENV = "env"
    TOML = "toml"


class Environment(Enum):
    """Deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ConfigValidationResult:
    """Configuration validation result."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    validated_config: Optional[Dict] = None


@dataclass
class ConfigSchema:
    """Configuration schema definition."""
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)
    field_types: Dict[str, type] = field(default_factory=dict)
    field_ranges: Dict[str, tuple] = field(default_factory=dict)
    field_patterns: Dict[str, str] = field(default_factory=dict)
    nested_schemas: Dict[str, 'ConfigSchema'] = field(default_factory=dict)
    environment_specific: Dict[str, Dict] = field(default_factory=dict)


class ConfigValidator:
    """Base configuration validator."""

    def __init__(self, schema: Optional[ConfigSchema] = None, environment: Environment = Environment.DEVELOPMENT):
        self.schema = schema or self._get_default_schema()
        self.environment = environment
        self.validation_errors = []
        self.validation_warnings = []
        self.validation_suggestions = []

    def _get_default_schema(self) -> ConfigSchema:
        """Get default configuration schema."""
        return ConfigSchema()

    def validate_config(self, config: Dict) -> ConfigValidationResult:
        """Validate configuration against schema."""
        self.validation_errors = []
        self.validation_warnings = []
        self.validation_suggestions = []

        # Validate required fields
        self._validate_required_fields(config)

        # Validate field types
        self._validate_field_types(config)

        # Validate field ranges
        self._validate_field_ranges(config)

        # Validate field patterns
        self._validate_field_patterns(config)

        # Validate nested configurations
        self._validate_nested_configs(config)

        # Validate environment-specific rules
        self._validate_environment_rules(config)

        # Validate cross-field dependencies
        self._validate_dependencies(config)

        is_valid = len(self.validation_errors) == 0

        return ConfigValidationResult(
            is_valid=is_valid,
            errors=self.validation_errors.copy(),
            warnings=self.validation_warnings.copy(),
            suggestions=self.validation_suggestions.copy(),
            validated_config=config if is_valid else None
        )

    def _validate_required_fields(self, config: Dict):
        """Validate required fields are present."""
        for field in self.schema.required_fields:
            if field not in config:
                self.validation_errors.append(f"Required field '{field}' is missing")
            elif config[field] is None or (isinstance(config[field], str) and not config[field].strip()):
                self.validation_errors.append(f"Required field '{field}' is empty")

    def _validate_field_types(self, config: Dict):
        """Validate field types."""
        for field, expected_type in self.schema.field_types.items():
            if field in config and config[field] is not None:
                value = config[field]
                if not isinstance(value, expected_type):
                    # Try type conversion for common cases
                    if expected_type == int and isinstance(value, str):
                        try:
                            config[field] = int(value)
                        except ValueError:
                            self.validation_errors.append(f"Field '{field}' must be an integer")
                    elif expected_type == float and isinstance(value, str):
                        try:
                            config[field] = float(value)
                        except ValueError:
                            self.validation_errors.append(f"Field '{field}' must be a number")
                    elif expected_type == bool and isinstance(value, str):
                        if value.lower() in ['true', 'false', '1', '0']:
                            config[field] = value.lower() in ['true', '1']
                        else:
                            self.validation_errors.append(f"Field '{field}' must be a boolean")
                    else:
                        self.validation_errors.append(f"Field '{field}' must be of type {expected_type.__name__}")

    def _validate_field_ranges(self, config: Dict):
        """Validate field value ranges."""
        for field, (min_val, max_val) in self.schema.field_ranges.items():
            if field in config and config[field] is not None:
                value = config[field]
                if isinstance(value, (int, float)):
                    if min_val is not None and value < min_val:
                        self.validation_errors.append(f"Field '{field}' value {value} is below minimum {min_val}")
                    if max_val is not None and value > max_val:
                        self.validation_errors.append(f"Field '{field}' value {value} is above maximum {max_val}")

    def _validate_field_patterns(self, config: Dict):
        """Validate field patterns using regex."""
        for field, pattern in self.schema.field_patterns.items():
            if field in config and config[field] is not None:
                value = str(config[field])
                if not re.match(pattern, value):
                    self.validation_errors.append(f"Field '{field}' value '{value}' does not match required pattern")

    def _validate_nested_configs(self, config: Dict):
        """Validate nested configuration objects."""
        for field, nested_schema in self.schema.nested_schemas.items():
            if field in config and isinstance(config[field], dict):
                nested_validator = ConfigValidator(nested_schema, self.environment)
                nested_result = nested_validator.validate_config(config[field])

                if not nested_result.is_valid:
                    self.validation_errors.extend([f"{field}.{error}" for error in nested_result.errors])
                if nested_result.warnings:
                    self.validation_warnings.extend([f"{field}.{warning}" for warning in nested_result.warnings])

    def _validate_environment_rules(self, config: Dict):
        """Validate environment-specific rules."""
        env_rules = self.schema.environment_specific.get(self.environment.value, {})

        for field, rules in env_rules.items():
            if field in config:
                value = config[field]

                # Environment-specific required fields
                if rules.get('required', False) and (value is None or (isinstance(value, str) and not value.strip())):
                    self.validation_errors.append(f"Field '{field}' is required in {self.environment.value} environment")

                # Environment-specific ranges
                if 'range' in rules:
                    min_val, max_val = rules['range']
                    if isinstance(value, (int, float)):
                        if min_val is not None and value < min_val:
                            self.validation_errors.append(
                                f"Field '{field}' value {value} is below {self.environment.value} minimum {min_val}")
                        if max_val is not None and value > max_val:
                            self.validation_errors.append(
                                f"Field '{field}' value {value} is above {self.environment.value} maximum {max_val}")

                # Environment-specific patterns
                if 'pattern' in rules:
                    if not re.match(rules['pattern'], str(value)):
                        self.validation_errors.append(
                            f"Field '{field}' does not match {self.environment.value} pattern")

    def _validate_dependencies(self, config: Dict):
        """Validate cross-field dependencies."""
        # This can be extended to check complex dependencies between fields
        pass


class DatabaseConfigValidator(ConfigValidator):
    """Validator for database configuration."""

    def _get_default_schema(self) -> ConfigSchema:
        return ConfigSchema(
            required_fields=['host', 'port', 'database', 'username', 'password'],
            optional_fields=['ssl_mode', 'connection_timeout', 'max_connections'],
            field_types={
                'host': str,
                'port': int,
                'database': str,
                'username': str,
                'password': str,
                'ssl_mode': str,
                'connection_timeout': int,
                'max_connections': int
            },
            field_ranges={
                'port': (1, 65535),
                'connection_timeout': (1, 300),
                'max_connections': (1, 1000)
            },
            field_patterns={
                'host': r'^[a-zA-Z0-9.-]+$',
                'database': r'^[a-zA-Z0-9_-]+$',
                'username': r'^[a-zA-Z0-9_-]+$'
            },
            environment_specific={
                'production': {
                    'ssl_mode': {'required': True, 'pattern': r'^(require|verify-full)$'},
                    'max_connections': {'range': (10, 500)}
                },
                'development': {
                    'max_connections': {'range': (1, 50)}
                }
            }
        )


class APIConfigValidator(ConfigValidator):
    """Validator for API configuration."""

    def _get_default_schema(self) -> ConfigSchema:
        return ConfigSchema(
            required_fields=['base_url', 'timeout'],
            optional_fields=['api_key', 'rate_limit', 'retry_attempts', 'headers'],
            field_types={
                'base_url': str,
                'timeout': int,
                'api_key': str,
                'rate_limit': int,
                'retry_attempts': int,
                'headers': dict
            },
            field_ranges={
                'timeout': (1, 300),
                'rate_limit': (1, 10000),
                'retry_attempts': (0, 10)
            },
            field_patterns={
                'base_url': r'^https?://[a-zA-Z0-9.-]+(?::\d+)?(?:/.*)?$'
            },
            nested_schemas={
                'headers': ConfigSchema(
                    field_types={'Authorization': str, 'Content-Type': str, 'User-Agent': str}
                )
            },
            environment_specific={
                'production': {
                    'api_key': {'required': True},
                    'rate_limit': {'range': (100, 10000)}
                },
                'testing': {
                    'timeout': {'range': (1, 30)}
                }
            }
        )


class LoggingConfigValidator(ConfigValidator):
    """Validator for logging configuration."""

    def _get_default_schema(self) -> ConfigSchema:
        return ConfigSchema(
            required_fields=['level', 'format'],
            optional_fields=['file_path', 'max_file_size', 'backup_count', 'console_output'],
            field_types={
                'level': str,
                'format': str,
                'file_path': str,
                'max_file_size': int,
                'backup_count': int,
                'console_output': bool
            },
            field_ranges={
                'max_file_size': (1024, 104857600),  # 1KB to 100MB
                'backup_count': (1, 100)
            },
            field_patterns={
                'level': r'^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$',
                'file_path': r'^/.*\.log$|^[a-zA-Z]:\\.*\.log$|^\./.*\.log$|^.*\.log$'
            },
            environment_specific={
                'production': {
                    'file_path': {'required': True},
                    'console_output': {'required': False}
                },
                'development': {
                    'console_output': {'required': True}
                }
            }
        )


class ConfigFileLoader:
    """Loads and validates configuration files."""

    def __init__(self):
        self.loaders = {
            ConfigFormat.JSON: self._load_json,
            ConfigFormat.YAML: self._load_yaml,
            ConfigFormat.ENV: self._load_env
        }

    def load_and_validate(self, file_path: Union[str, Path], format_type: ConfigFormat,
                         validator: ConfigValidator, environment: Environment = Environment.DEVELOPMENT) -> ConfigValidationResult:
        """Load configuration file and validate it."""
        file_path = Path(file_path)

        if not file_path.exists():
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"Configuration file not found: {file_path}"],
                warnings=[],
                suggestions=[f"Create configuration file at {file_path}"]
            )

        try:
            # Load configuration
            loader = self.loaders.get(format_type)
            if not loader:
                return ConfigValidationResult(
                    is_valid=False,
                    errors=[f"Unsupported configuration format: {format_type.value}"],
                    warnings=[],
                    suggestions=["Use JSON, YAML, or ENV format"]
                )

            config = loader(file_path)

            # Validate configuration
            validator.environment = environment
            result = validator.validate_config(config)

            return result

        except Exception as e:
            return ConfigValidationResult(
                is_valid=False,
                errors=[f"Failed to load configuration: {str(e)}"],
                warnings=[],
                suggestions=["Check file format and permissions"]
            )

    def _load_json(self, file_path: Path) -> Dict:
        """Load JSON configuration file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_yaml(self, file_path: Path) -> Dict:
        """Load YAML configuration file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except ImportError:
            raise ImportError("PyYAML is required for YAML configuration files")

    def _load_env(self, file_path: Path) -> Dict:
        """Load environment variables from file."""
        config = {}
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip()

                        # Try to convert to appropriate type
                        if value.lower() in ['true', 'false']:
                            config[key] = value.lower() == 'true'
                        elif value.isdigit():
                            config[key] = int(value)
                        elif re.match(r'^\d+\.\d+$', value):
                            config[key] = float(value)
                        else:
                            config[key] = value

        return config


class EnvironmentVariableValidator:
    """Validator for environment variables."""

    def __init__(self, required_vars: List[str] = None, optional_vars: Dict[str, Any] = None):
        self.required_vars = required_vars or []
        self.optional_vars = optional_vars or {}
        self.validation_errors = []
        self.validation_warnings = []

    def validate(self) -> ConfigValidationResult:
        """Validate environment variables."""
        self.validation_errors = []
        self.validation_warnings = []

        config = {}

        # Check required variables
        for var_name in self.required_vars:
            value = os.getenv(var_name)
            if value is None:
                self.validation_errors.append(f"Required environment variable '{var_name}' is not set")
            else:
                config[var_name] = self._parse_env_value(value)

        # Check optional variables
        for var_name, default_value in self.optional_vars.items():
            value = os.getenv(var_name)
            if value is None:
                config[var_name] = default_value
                self.validation_warnings.append(f"Using default value for optional variable '{var_name}': {default_value}")
            else:
                config[var_name] = self._parse_env_value(value)

        # Validate variable formats
        self._validate_env_formats(config)

        is_valid = len(self.validation_errors) == 0

        return ConfigValidationResult(
            is_valid=is_valid,
            errors=self.validation_errors.copy(),
            warnings=self.validation_warnings.copy(),
            suggestions=[],
            validated_config=config if is_valid else None
        )

    def _parse_env_value(self, value: str) -> Union[str, int, float, bool]:
        """Parse environment variable value to appropriate type."""
        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # Try integer
        if value.isdigit() or (value.startswith('-') and value[1:].isdigit()):
            return int(value)

        # Try float
        if re.match(r'^-?\d+\.\d+$', value):
            return float(value)

        # Default to string
        return value

    def _validate_env_formats(self, config: Dict):
        """Validate environment variable formats."""
        # Add specific validation rules as needed
        pass


# Convenience functions
def validate_database_config(config: Dict, environment: Environment = Environment.DEVELOPMENT) -> ConfigValidationResult:
    """Validate database configuration."""
    validator = DatabaseConfigValidator(environment=environment)
    return validator.validate_config(config)


def validate_api_config(config: Dict, environment: Environment = Environment.DEVELOPMENT) -> ConfigValidationResult:
    """Validate API configuration."""
    validator = APIConfigValidator(environment=environment)
    return validator.validate_config(config)


def validate_logging_config(config: Dict, environment: Environment = Environment.DEVELOPMENT) -> ConfigValidationResult:
    """Validate logging configuration."""
    validator = LoggingConfigValidator(environment=environment)
    return validator.validate_config(config)


def load_and_validate_config(file_path: Union[str, Path], format_type: ConfigFormat,
                           validator: ConfigValidator, environment: Environment = Environment.DEVELOPMENT) -> ConfigValidationResult:
    """Load and validate configuration file."""
    loader = ConfigFileLoader()
    return loader.load_and_validate(file_path, format_type, validator, environment)


def validate_environment_variables(required_vars: List[str] = None,
                                 optional_vars: Dict[str, Any] = None) -> ConfigValidationResult:
    """Validate environment variables."""
    validator = EnvironmentVariableValidator(required_vars, optional_vars)
    return validator.validate()


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test database configuration validation
    db_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'climatetrade',
        'username': 'user',
        'password': 'password123',
        'ssl_mode': 'require'
    }

    result = validate_database_config(db_config, Environment.PRODUCTION)
    print(f"Database config valid: {result.is_valid}")
    if not result.is_valid:
        print("Errors:", result.errors)

    # Test API configuration validation
    api_config = {
        'base_url': 'https://api.example.com',
        'timeout': 30,
        'rate_limit': 1000,
        'headers': {
            'Authorization': 'Bearer token123',
            'Content-Type': 'application/json'
        }
    }

    result = validate_api_config(api_config, Environment.PRODUCTION)
    print(f"API config valid: {result.is_valid}")
    if not result.is_valid:
        print("Errors:", result.errors)

    # Test environment variable validation
    result = validate_environment_variables(
        required_vars=['DATABASE_URL', 'API_KEY'],
        optional_vars={'DEBUG': False, 'LOG_LEVEL': 'INFO'}
    )
    print(f"Environment variables valid: {result.is_valid}")
    if not result.is_valid:
        print("Errors:", result.errors)