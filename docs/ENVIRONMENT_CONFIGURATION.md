# ClimaTrade AI Environment Configuration Guide

## Table of Contents

1. [Overview](#overview)
2. [Configuration Management](#configuration-management)
3. [Development Environment](#development-environment)
4. [Staging Environment](#staging-environment)
5. [Production Environment](#production-environment)
6. [Configuration Templates](#configuration-templates)
7. [Security Configuration](#security-configuration)
8. [Environment Variables Reference](#environment-variables-reference)
9. [Configuration Validation](#configuration-validation)

## Overview

This guide provides comprehensive configuration requirements for ClimaTrade AI across all environments. Proper configuration management ensures consistent, secure, and maintainable deployments.

### Configuration Principles

- **Environment-specific settings**: Different configurations for dev/staging/production
- **Secret management**: Secure handling of API keys and credentials
- **Validation**: Configuration validation at startup
- **Documentation**: All settings are documented with examples
- **Version control**: Configuration templates are version controlled

## Configuration Management

### Configuration Hierarchy

```
Environment Variables (highest priority)
├── .env files
├── config/*.json files
├── Default values (lowest priority)
```

### Configuration Files Structure

```
config/
├── development.json
├── staging.json
├── production.json
├── validation_rules.json
└── templates/
    ├── database.json
    ├── api.json
    ├── security.json
    └── monitoring.json
```

### Environment Detection

```python
# config/environment.py
import os

class Environment:
    DEVELOPMENT = 'development'
    STAGING = 'staging'
    PRODUCTION = 'production'

def get_current_environment():
    """Detect current environment from multiple sources"""
    # Priority: env var > .env file > default
    env = os.getenv('CLIMATRADE_ENV')
    if env:
        return env

    # Check for environment-specific files
    if os.path.exists('.env.production'):
        return Environment.PRODUCTION
    elif os.path.exists('.env.staging'):
        return Environment.STAGING
    else:
        return Environment.DEVELOPMENT
```

## Development Environment

### Core Configuration

```json
// config/development.json
{
  "environment": "development",
  "debug": true,
  "log_level": "DEBUG",
  "database": {
    "type": "sqlite",
    "path": "./data/climatetrade.db",
    "migrations_enabled": true,
    "backup_enabled": false
  },
  "api": {
    "timeout": 30,
    "retry_attempts": 3,
    "rate_limit": 100
  },
  "features": {
    "backtesting_enabled": true,
    "real_trading_enabled": false,
    "data_validation_enabled": true
  }
}
```

### Environment Variables

```bash
# .env.development
# Database Configuration
DATABASE_URL=sqlite:///data/climatetrade.db
DATABASE_DEBUG=true

# API Configuration
WEATHER_API_TIMEOUT=30
POLYMARKET_API_TIMEOUT=30
MAX_API_RETRIES=3

# Logging
LOG_LEVEL=DEBUG
LOG_FILE=logs/development.log

# Development Features
ENABLE_DEBUG_MODE=true
ENABLE_HOT_RELOAD=true
ENABLE_DETAILED_LOGGING=true

# Test Configuration
TEST_DATABASE_URL=sqlite:///data/test.db
ENABLE_MOCK_APIS=true
```

### Development Tools Configuration

```json
// config/development_tools.json
{
  "profiling": {
    "enabled": true,
    "memory_profiling": true,
    "cpu_profiling": true
  },
  "testing": {
    "mock_external_apis": true,
    "use_test_database": true,
    "enable_coverage": true
  },
  "development": {
    "auto_reload": true,
    "debug_toolbar": true,
    "cors_enabled": true
  }
}
```

## Staging Environment

### Core Configuration

```json
// config/staging.json
{
  "environment": "staging",
  "debug": false,
  "log_level": "INFO",
  "database": {
    "type": "postgresql",
    "host": "staging-db.climatetrade.internal",
    "port": 5432,
    "database": "climatetrade_staging",
    "ssl_mode": "require",
    "migrations_enabled": true,
    "backup_enabled": true
  },
  "api": {
    "timeout": 60,
    "retry_attempts": 5,
    "rate_limit": 1000
  },
  "monitoring": {
    "enabled": true,
    "metrics_endpoint": "/metrics",
    "health_check_endpoint": "/health"
  },
  "features": {
    "backtesting_enabled": true,
    "real_trading_enabled": false,
    "data_validation_enabled": true
  }
}
```

### Environment Variables

```bash
# .env.staging
# Database Configuration
DATABASE_URL=postgresql://climatetrade_staging:password@staging-db.climatetrade.internal:5432/climatetrade_staging
DATABASE_SSL_MODE=require
DATABASE_CONNECTION_POOL_SIZE=10

# Redis Configuration
REDIS_URL=redis://staging-redis.climatetrade.internal:6379/0
REDIS_PASSWORD=staging_redis_password

# API Configuration
WEATHER_API_TIMEOUT=60
POLYMARKET_API_TIMEOUT=60
MAX_API_RETRIES=5
API_RATE_LIMIT=1000

# Security
JWT_SECRET=staging_jwt_secret_key_here
API_KEY_SECRET=staging_api_key_secret
ENCRYPTION_KEY=staging_encryption_key_32_chars

# Monitoring
PROMETHEUS_METRICS_ENABLED=true
HEALTH_CHECK_ENABLED=true
LOG_LEVEL=INFO

# External Services
POLYGON_RPC_URL=https://polygon-rpc.com/
MATIC_RPC_URL=https://matic-mumbai.chainstacklabs.com
```

### Staging Validation Rules

```json
// config/staging_validation.json
{
  "database": {
    "required_fields": ["host", "port", "database", "username", "password"],
    "ssl_required": true,
    "connection_timeout": 30
  },
  "security": {
    "jwt_secret_min_length": 32,
    "api_key_required": true,
    "encryption_key_length": 32
  },
  "monitoring": {
    "health_checks_required": true,
    "metrics_required": true
  }
}
```

## Production Environment

### Core Configuration

```json
// config/production.json
{
  "environment": "production",
  "debug": false,
  "log_level": "WARNING",
  "database": {
    "type": "postgresql",
    "host": "prod-db-cluster.climatetrade.internal",
    "port": 5432,
    "database": "climatetrade_prod",
    "ssl_mode": "verify-full",
    "ssl_cert": "/etc/ssl/certs/climatetrade.crt",
    "migrations_enabled": false,
    "backup_enabled": true,
    "read_replicas": [
      "prod-db-replica-1.climatetrade.internal",
      "prod-db-replica-2.climatetrade.internal"
    ]
  },
  "cache": {
    "redis_cluster": [
      "prod-redis-1.climatetrade.internal:6379",
      "prod-redis-2.climatetrade.internal:6379",
      "prod-redis-3.climatetrade.internal:6379"
    ],
    "ttl": 3600
  },
  "api": {
    "timeout": 120,
    "retry_attempts": 10,
    "rate_limit": 10000,
    "circuit_breaker_enabled": true
  },
  "monitoring": {
    "enabled": true,
    "metrics_endpoint": "/metrics",
    "health_check_endpoint": "/health",
    "alerting_enabled": true,
    "log_aggregation": "elasticsearch"
  },
  "security": {
    "https_required": true,
    "hsts_enabled": true,
    "csp_enabled": true,
    "rate_limiting_enabled": true
  },
  "features": {
    "backtesting_enabled": true,
    "real_trading_enabled": true,
    "data_validation_enabled": true,
    "auto_scaling_enabled": true
  }
}
```

### Environment Variables

```bash
# .env.production
# Database Configuration
DATABASE_URL=postgresql://climatetrade_prod:secure_password@prod-db-cluster.climatetrade.internal:5432/climatetrade_prod
DATABASE_SSL_MODE=verify-full
DATABASE_SSL_CERT=/etc/ssl/certs/climatetrade.crt
DATABASE_SSL_KEY=/etc/ssl/private/climatetrade.key
DATABASE_SSL_ROOT_CERT=/etc/ssl/certs/ca.crt
DATABASE_CONNECTION_POOL_SIZE=50
DATABASE_MAX_CONNECTIONS=100

# Redis Cluster Configuration
REDIS_URL=redis://prod-redis-cluster.climatetrade.internal:6379/0
REDIS_PASSWORD=production_redis_secure_password
REDIS_SSL=true
REDIS_SSL_CERT=/etc/ssl/certs/redis.crt

# API Configuration
WEATHER_API_TIMEOUT=120
POLYMARKET_API_TIMEOUT=120
MAX_API_RETRIES=10
API_RATE_LIMIT=10000
CIRCUIT_BREAKER_ENABLED=true
CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=60

# Security Configuration
JWT_SECRET=production_jwt_secret_64_chars_minimum_secure_random
API_KEY_SECRET=production_api_key_secret_32_chars
ENCRYPTION_KEY=production_encryption_key_32_chars_secure
OAUTH_CLIENT_SECRET=production_oauth_secret
SSL_CERT_PATH=/etc/ssl/certs/climatetrade.crt
SSL_KEY_PATH=/etc/ssl/private/climatetrade.key

# External Services
POLYGON_RPC_URL=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_KEY
MATIC_RPC_URL=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY
ETHERSCAN_API_KEY=production_etherscan_api_key
COINGECKO_API_KEY=production_coingecko_api_key

# Monitoring and Alerting
PROMETHEUS_METRICS_ENABLED=true
GRAFANA_URL=https://monitoring.climatetrade.ai
ALERTMANAGER_URL=https://alerts.climatetrade.ai
LOGSTASH_HOST=logstash.climatetrade.internal
LOGSTASH_PORT=5044

# Load Balancing
LOAD_BALANCER_ENDPOINT=https://api.climatetrade.ai
HEALTH_CHECK_ENDPOINT=https://api.climatetrade.ai/health
METRICS_ENDPOINT=https://api.climatetrade.ai/metrics

# Feature Flags
ENABLE_REAL_TRADING=true
ENABLE_AUTO_SCALING=true
ENABLE_CIRCUIT_BREAKER=true
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true

# Performance Tuning
MAX_WORKERS=8
MEMORY_LIMIT=2GB
CPU_LIMIT=4
REQUEST_TIMEOUT=300
```

### Production Security Configuration

```json
// config/production_security.json
{
  "ssl": {
    "enabled": true,
    "cert_path": "/etc/ssl/certs/climatetrade.crt",
    "key_path": "/etc/ssl/private/climatetrade.key",
    "ca_cert_path": "/etc/ssl/certs/ca.crt",
    "min_tls_version": "1.2",
    "cipher_suites": [
      "ECDHE-RSA-AES256-GCM-SHA384",
      "ECDHE-RSA-AES128-GCM-SHA256"
    ]
  },
  "authentication": {
    "jwt_enabled": true,
    "oauth_enabled": true,
    "api_keys_enabled": true,
    "mfa_required": true
  },
  "authorization": {
    "rbac_enabled": true,
    "permissions_model": "role_based",
    "audit_logging": true
  },
  "network_security": {
    "firewall_enabled": true,
    "ddos_protection": true,
    "waf_enabled": true,
    "vpn_required": true
  },
  "data_protection": {
    "encryption_at_rest": true,
    "encryption_in_transit": true,
    "data_masking": true,
    "backup_encryption": true
  }
}
```

## Configuration Templates

### Database Configuration Template

```json
// config/templates/database.json
{
  "development": {
    "type": "sqlite",
    "path": "./data/climatetrade.db",
    "debug": true,
    "migrations_enabled": true
  },
  "staging": {
    "type": "postgresql",
    "host": "${DATABASE_HOST}",
    "port": 5432,
    "database": "climatetrade_staging",
    "username": "${DATABASE_USER}",
    "password": "${DATABASE_PASSWORD}",
    "ssl_mode": "require"
  },
  "production": {
    "type": "postgresql",
    "host": "${DATABASE_HOST}",
    "port": 5432,
    "database": "climatetrade_prod",
    "username": "${DATABASE_USER}",
    "password": "${DATABASE_PASSWORD}",
    "ssl_mode": "verify-full",
    "ssl_cert": "${SSL_CERT_PATH}",
    "ssl_key": "${SSL_KEY_PATH}",
    "ssl_root_cert": "${SSL_CA_CERT_PATH}",
    "connection_pool_size": 50,
    "max_connections": 100,
    "read_replicas": ["${REPLICA_1_HOST}", "${REPLICA_2_HOST}"]
  }
}
```

### API Configuration Template

```json
// config/templates/api.json
{
  "development": {
    "timeout": 30,
    "retry_attempts": 3,
    "rate_limit": 100,
    "debug": true
  },
  "staging": {
    "timeout": 60,
    "retry_attempts": 5,
    "rate_limit": 1000,
    "circuit_breaker_enabled": false
  },
  "production": {
    "timeout": 120,
    "retry_attempts": 10,
    "rate_limit": 10000,
    "circuit_breaker_enabled": true,
    "circuit_breaker_failure_threshold": 5,
    "circuit_breaker_recovery_timeout": 60
  }
}
```

### Security Configuration Template

```json
// config/templates/security.json
{
  "development": {
    "https_required": false,
    "jwt_secret": "dev_jwt_secret_not_secure",
    "api_key_required": false,
    "encryption_enabled": false
  },
  "staging": {
    "https_required": true,
    "jwt_secret": "${JWT_SECRET}",
    "api_key_required": true,
    "encryption_enabled": true,
    "rate_limiting_enabled": true
  },
  "production": {
    "https_required": true,
    "hsts_enabled": true,
    "csp_enabled": true,
    "jwt_secret": "${JWT_SECRET}",
    "api_key_required": true,
    "encryption_enabled": true,
    "rate_limiting_enabled": true,
    "audit_logging_enabled": true,
    "mfa_required": true
  }
}
```

## Security Configuration

### Secret Management

```python
# config/secrets.py
import os
from cryptography.fernet import Fernet
import boto3
from azure.keyvault import KeyVaultClient
from google.cloud import secretmanager

class SecretManager:
    def __init__(self, provider='local'):
        self.provider = provider
        self._setup_provider()

    def _setup_provider(self):
        if self.provider == 'aws':
            self.client = boto3.client('secretsmanager')
        elif self.provider == 'azure':
            # Azure Key Vault setup
            pass
        elif self.provider == 'gcp':
            self.client = secretmanager.SecretManagerServiceClient()
        else:
            # Local encryption
            key = os.getenv('ENCRYPTION_KEY')
            if not key:
                key = Fernet.generate_key()
            self.fernet = Fernet(key)

    def get_secret(self, name):
        """Retrieve secret from configured provider"""
        if self.provider == 'aws':
            response = self.client.get_secret_value(SecretId=name)
            return response['SecretString']
        elif self.provider == 'local':
            encrypted = os.getenv(name)
            if encrypted:
                return self.fernet.decrypt(encrypted.encode()).decode()
        return None

    def set_secret(self, name, value):
        """Store secret in configured provider"""
        if self.provider == 'aws':
            self.client.put_secret_value(
                SecretId=name,
                SecretString=value
            )
        elif self.provider == 'local':
            encrypted = self.fernet.encrypt(value.encode()).decode()
            # Store encrypted value in environment or config
            return encrypted
```

### Environment Variable Encryption

```python
# config/encrypted_env.py
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class EncryptedEnvironment:
    def __init__(self, master_password=None):
        self.master_password = master_password or os.getenv('MASTER_PASSWORD')
        self.salt = os.getenv('ENCRYPTION_SALT', 'default_salt').encode()
        self.key = self._derive_key()

    def _derive_key(self):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self.master_password.encode()))

    def encrypt_value(self, value):
        """Encrypt environment variable value"""
        f = Fernet(self.key)
        return f.encrypt(value.encode()).decode()

    def decrypt_value(self, encrypted_value):
        """Decrypt environment variable value"""
        f = Fernet(self.key)
        return f.decrypt(encrypted_value.encode()).decode()

    def load_encrypted_env(self, env_file='.env.encrypted'):
        """Load and decrypt environment variables"""
        if not os.path.exists(env_file):
            return

        with open(env_file, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, encrypted_value = line.split('=', 1)
                    decrypted_value = self.decrypt_value(encrypted_value.strip())
                    os.environ[key] = decrypted_value
```

## Environment Variables Reference

### Core System Variables

| Variable         | Description       | Development   | Staging   | Production   |
| ---------------- | ----------------- | ------------- | --------- | ------------ |
| `CLIMATRADE_ENV` | Environment name  | `development` | `staging` | `production` |
| `DEBUG`          | Enable debug mode | `true`        | `false`   | `false`      |
| `LOG_LEVEL`      | Logging level     | `DEBUG`       | `INFO`    | `WARNING`    |

### Database Variables

| Variable                        | Description              | Example                               |
| ------------------------------- | ------------------------ | ------------------------------------- |
| `DATABASE_URL`                  | Database connection URL  | `postgresql://user:pass@host:5432/db` |
| `DATABASE_SSL_MODE`             | SSL mode for connections | `require`, `verify-full`              |
| `DATABASE_CONNECTION_POOL_SIZE` | Connection pool size     | `10`, `50`                            |
| `DATABASE_MAX_CONNECTIONS`      | Maximum connections      | `20`, `100`                           |

### API Variables

| Variable                 | Description                   | Example        |
| ------------------------ | ----------------------------- | -------------- |
| `WEATHER_API_TIMEOUT`    | Weather API timeout (seconds) | `30`, `120`    |
| `POLYMARKET_API_TIMEOUT` | Polymarket API timeout        | `30`, `120`    |
| `MAX_API_RETRIES`        | Maximum API retry attempts    | `3`, `10`      |
| `API_RATE_LIMIT`         | API rate limit per minute     | `100`, `10000` |

### Security Variables

| Variable              | Description               | Example                 |
| --------------------- | ------------------------- | ----------------------- |
| `JWT_SECRET`          | JWT signing secret        | `64-char-random-string` |
| `API_KEY_SECRET`      | API key encryption secret | `32-char-random-string` |
| `ENCRYPTION_KEY`      | Data encryption key       | `32-char-random-string` |
| `OAUTH_CLIENT_SECRET` | OAuth client secret       | `secure-random-string`  |

### External Service Variables

| Variable          | Description          | Example                                   |
| ----------------- | -------------------- | ----------------------------------------- |
| `POLYGON_RPC_URL` | Polygon RPC endpoint | `https://polygon-rpc.com/`                |
| `MATIC_RPC_URL`   | Matic RPC endpoint   | `https://matic-mumbai.chainstacklabs.com` |
| `REDIS_URL`       | Redis connection URL | `redis://host:6379/0`                     |
| `REDIS_PASSWORD`  | Redis password       | `secure-redis-password`                   |

### Monitoring Variables

| Variable                     | Description               | Example                          |
| ---------------------------- | ------------------------- | -------------------------------- |
| `PROMETHEUS_METRICS_ENABLED` | Enable Prometheus metrics | `true`, `false`                  |
| `GRAFANA_URL`                | Grafana dashboard URL     | `https://monitoring.example.com` |
| `ALERTMANAGER_URL`           | Alertmanager URL          | `https://alerts.example.com`     |
| `LOGSTASH_HOST`              | Logstash host             | `logstash.example.com`           |

## Configuration Validation

### Configuration Validator

```python
# config/validator.py
import jsonschema
import os
from typing import Dict, Any, List

class ConfigurationValidator:
    def __init__(self):
        self.schemas = self._load_schemas()

    def _load_schemas(self):
        """Load JSON schemas for validation"""
        return {
            'database': {
                'type': 'object',
                'required': ['type'],
                'properties': {
                    'type': {'enum': ['sqlite', 'postgresql', 'mysql']},
                    'host': {'type': 'string'},
                    'port': {'type': 'integer', 'minimum': 1, 'maximum': 65535},
                    'database': {'type': 'string'},
                    'username': {'type': 'string'},
                    'password': {'type': 'string'}
                }
            },
            'api': {
                'type': 'object',
                'properties': {
                    'timeout': {'type': 'integer', 'minimum': 1, 'maximum': 300},
                    'retry_attempts': {'type': 'integer', 'minimum': 0, 'maximum': 20},
                    'rate_limit': {'type': 'integer', 'minimum': 1}
                }
            },
            'security': {
                'type': 'object',
                'properties': {
                    'jwt_secret': {'type': 'string', 'minLength': 32},
                    'api_key_required': {'type': 'boolean'},
                    'encryption_enabled': {'type': 'boolean'}
                }
            }
        }

    def validate_config(self, config: Dict[str, Any], config_type: str) -> List[str]:
        """Validate configuration against schema"""
        if config_type not in self.schemas:
            return [f"Unknown configuration type: {config_type}"]

        try:
            jsonschema.validate(config, self.schemas[config_type])
            return []
        except jsonschema.ValidationError as e:
            return [f"Validation error in {config_type}: {e.message}"]
        except Exception as e:
            return [f"Configuration validation failed: {str(e)}"]

    def validate_environment_variables(self) -> List[str]:
        """Validate required environment variables"""
        errors = []
        required_vars = {
            'CLIMATRADE_ENV': ['development', 'staging', 'production'],
            'DATABASE_URL': None,
            'JWT_SECRET': None
        }

        for var, allowed_values in required_vars.items():
            value = os.getenv(var)
            if not value:
                errors.append(f"Missing required environment variable: {var}")
            elif allowed_values and value not in allowed_values:
                errors.append(f"Invalid value for {var}: {value}. Allowed: {allowed_values}")

        return errors

    def validate_all(self, config: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate entire configuration"""
        results = {}

        # Validate individual config sections
        for section_name, section_config in config.items():
            if section_name in self.schemas:
                results[section_name] = self.validate_config(section_config, section_name)

        # Validate environment variables
        results['environment'] = self.validate_environment_variables()

        # Cross-validation
        results['cross_validation'] = self._validate_cross_dependencies(config)

        return results

    def _validate_cross_dependencies(self, config: Dict[str, Any]) -> List[str]:
        """Validate cross-section dependencies"""
        errors = []

        # Database and security cross-validation
        if config.get('database', {}).get('type') == 'postgresql':
            if not config.get('security', {}).get('encryption_enabled', False):
                errors.append("PostgreSQL requires encryption to be enabled")

        # Production-specific validations
        if os.getenv('CLIMATRADE_ENV') == 'production':
            if not config.get('monitoring', {}).get('enabled', False):
                errors.append("Monitoring must be enabled in production")
            if not config.get('security', {}).get('https_required', False):
                errors.append("HTTPS must be required in production")

        return errors
```

### Configuration Loader with Validation

```python
# config/loader.py
import json
import os
from pathlib import Path
from .validator import ConfigurationValidator

class ConfigurationLoader:
    def __init__(self, config_dir='config'):
        self.config_dir = Path(config_dir)
        self.validator = ConfigurationValidator()
        self.config = {}

    def load_config(self, environment=None):
        """Load and validate configuration for environment"""
        if not environment:
            environment = os.getenv('CLIMATRADE_ENV', 'development')

        # Load base configuration
        config_file = self.config_dir / f"{environment}.json"
        if config_file.exists():
            with open(config_file, 'r') as f:
                self.config = json.load(f)

        # Load environment-specific overrides
        env_file = f".env.{environment}"
        if os.path.exists(env_file):
            self._load_env_file(env_file)

        # Validate configuration
        validation_results = self.validator.validate_all(self.config)

        # Report validation errors
        all_errors = []
        for section, errors in validation_results.items():
            if errors:
                all_errors.extend(errors)
                print(f"Configuration errors in {section}:")
                for error in errors:
                    print(f"  - {error}")

        if all_errors:
            raise ValueError(f"Configuration validation failed: {all_errors}")

        return self.config

    def _load_env_file(self, env_file):
        """Load environment variables from file"""
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key] = value

    def get(self, key, default=None):
        """Get configuration value"""
        keys = key.split('.')
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default

        return value if value is not None else default
```

### Usage Example

```python
# config/__init__.py
from .loader import ConfigurationLoader

# Global configuration instance
config_loader = ConfigurationLoader()
config = config_loader.load_config()

# Usage throughout application
database_url = config.get('database.url')
jwt_secret = config.get('security.jwt_secret')
api_timeout = config.get('api.timeout', 30)
```

This comprehensive environment configuration guide ensures that ClimaTrade AI can be properly configured for development, staging, and production environments with appropriate security, performance, and monitoring settings.
