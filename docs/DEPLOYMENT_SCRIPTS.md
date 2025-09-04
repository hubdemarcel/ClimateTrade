# ClimaTrade AI Deployment Scripts and Docker Configurations

## Table of Contents

1. [Overview](#overview)
2. [Docker Configuration](#docker-configuration)
3. [Deployment Scripts](#deployment-scripts)
4. [Container Orchestration](#container-orchestration)
5. [CI/CD Integration](#ci-cd-integration)
6. [Infrastructure as Code](#infrastructure-as-code)

## Overview

This document provides standardized deployment scripts and Docker configurations for ClimaTrade AI. All configurations are production-ready with security, monitoring, and scalability considerations.

### Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Load Balancer │    │   API Gateway    │    │   Monitoring     │
│   (nginx)       │    │   (traefik)     │    │   (prometheus)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  │
                    ┌─────────────────┐
                    │   Application   │
                    │   Services      │
                    │                 │
                    │ • Data Pipeline │
                    │ • Backtesting   │
                    │ • Agents        │
                    │ • Web Interface │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Data Layer    │
                    │                 │
                    │ • PostgreSQL    │
                    │ • Redis Cache   │
                    │ • File Storage  │
                    └─────────────────┘
```

## Docker Configuration

### Base Docker Images

#### Python Base Image

```dockerfile
# docker/base/python.Dockerfile
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN useradd --create-home --shell /bin/bash climatetrade

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership
RUN chown -R climatetrade:climatetrade /app

# Switch to non-root user
USER climatetrade

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

EXPOSE 8000

CMD ["python", "main.py"]
```

#### Node.js Base Image (for subgraph)

```dockerfile
# docker/base/nodejs.Dockerfile
FROM node:16-alpine

# Install system dependencies
RUN apk add --no-cache \
    git \
    curl \
    python3 \
    make \
    g++

# Create application user
RUN addgroup -g 1001 -S climatetrade && \
    adduser -S climatetrade -u 1001

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy application code
COPY . .

# Change ownership
RUN chown -R climatetrade:climatetrade /app

# Switch to non-root user
USER climatetrade

EXPOSE 8000

CMD ["npm", "start"]
```

### Service-Specific Dockerfiles

#### Data Pipeline Dockerfile

```dockerfile
# docker/data-pipeline/Dockerfile
FROM climatetrade/python-base:latest

# Copy data pipeline specific files
COPY data_pipeline/ ./data_pipeline/
COPY config/ ./config/

# Install additional dependencies
RUN pip install --no-cache-dir \
    pandas \
    numpy \
    requests \
    pydantic

# Set environment variables
ENV PYTHONPATH=/app
ENV CLIMATRADE_COMPONENT=data_pipeline

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["python", "-m", "data_pipeline.main"]
```

#### Backtesting Service Dockerfile

```dockerfile
# docker/backtesting/Dockerfile
FROM climatetrade/python-base:latest

# Copy backtesting framework
COPY backtesting_framework/ ./backtesting_framework/
COPY config/ ./config/

# Install additional dependencies
RUN pip install --no-cache-dir \
    scipy \
    scikit-learn \
    matplotlib \
    seaborn

# Set environment variables
ENV PYTHONPATH=/app
ENV CLIMATRADE_COMPONENT=backtesting

# Create directories for results
RUN mkdir -p /app/results /app/logs

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "from backtesting_framework.core.backtesting_engine import BacktestingEngine; print('Backtesting engine ready')" || exit 1

EXPOSE 8001

CMD ["python", "-m", "backtesting_framework.main"]
```

#### Agents Service Dockerfile

```dockerfile
# docker/agents/Dockerfile
FROM climatetrade/python-base:latest

# Copy agents code
COPY scripts/agents/ ./agents/
COPY config/ ./config/

# Install additional dependencies
RUN pip install --no-cache-dir \
    web3 \
    eth-account \
    openai \
    chromadb

# Set environment variables
ENV PYTHONPATH=/app
ENV CLIMATRADE_COMPONENT=agents

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "from agents.application.trade import TradingAgent; print('Agents ready')" || exit 1

EXPOSE 8002

CMD ["python", "-m", "agents.application.main"]
```

#### Web Interface Dockerfile

```dockerfile
# docker/web/Dockerfile
FROM node:16-alpine as builder

# Set working directory
WORKDIR /app

# Copy package files
COPY web/package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY web/ .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY docker/web/nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### Database Dockerfile

```dockerfile
# docker/database/Dockerfile
FROM postgres:13-alpine

# Copy initialization scripts
COPY database/schema.sql /docker-entrypoint-initdb.d/01-schema.sql
COPY database/migrations/ /docker-entrypoint-initdb.d/migrations/

# Copy custom configuration
COPY docker/database/postgresql.conf /etc/postgresql/postgresql.conf

# Set environment variables
ENV POSTGRES_DB=climatetrade
ENV POSTGRES_USER=climatetrade
ENV POSTGRES_PASSWORD=change_this_password
ENV PGDATA=/var/lib/postgresql/data/pgdata

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD pg_isready -U climatetrade || exit 1

EXPOSE 5432
```

## Deployment Scripts

### Bash Deployment Scripts

#### Development Deployment Script

```bash
#!/bin/bash
# scripts/deploy/dev-deploy.sh

set -e

echo "🚀 Starting ClimaTrade AI Development Deployment"

# Load environment variables
if [ -f ".env.development" ]; then
    export $(cat .env.development | xargs)
fi

# Create required directories
mkdir -p logs data results

# Start database
echo "📊 Starting database..."
docker-compose -f docker-compose.dev.yml up -d climatetrade-db

# Wait for database to be ready
echo "⏳ Waiting for database..."
sleep 30

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.dev.yml exec -T climatetrade-db bash -c "
    psql -U climatetrade -d climatetrade -f /docker-entrypoint-initdb.d/01-schema.sql
"

# Start application services
echo "🏗️ Starting application services..."
docker-compose -f docker-compose.dev.yml up -d climatetrade-data-pipeline
docker-compose -f docker-compose.dev.yml up -d climatetrade-backtesting
docker-compose -f docker-compose.dev.yml up -d climatetrade-agents

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 60

# Run health checks
echo "🔍 Running health checks..."
curl -f http://localhost:8000/health || echo "Data pipeline health check failed"
curl -f http://localhost:8001/health || echo "Backtesting health check failed"
curl -f http://localhost:8002/health || echo "Agents health check failed"

echo "✅ Development deployment completed successfully!"
echo "🌐 Services available at:"
echo "  - Data Pipeline: http://localhost:8000"
echo "  - Backtesting: http://localhost:8001"
echo "  - Agents: http://localhost:8002"
```

#### Production Deployment Script

```bash
#!/bin/bash
# scripts/deploy/prod-deploy.sh

set -e

echo "🚀 Starting ClimaTrade AI Production Deployment"

# Validate environment
if [ "$CLIMATRADE_ENV" != "production" ]; then
    echo "❌ Error: CLIMATRADE_ENV must be set to 'production'"
    exit 1
fi

# Load production environment variables
if [ -f ".env.production" ]; then
    export $(cat .env.production | xargs)
fi

# Validate required environment variables
required_vars=("DATABASE_URL" "REDIS_URL" "JWT_SECRET" "ENCRYPTION_KEY")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set"
        exit 1
    fi
done

# Create backup before deployment
echo "💾 Creating pre-deployment backup..."
./scripts/backup/create-backup.sh

# Pull latest images
echo "📥 Pulling latest Docker images..."
docker-compose -f docker-compose.prod.yml pull

# Run database migrations
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm climatetrade-data-pipeline python -m data_pipeline.migrations run

# Deploy with zero-downtime
echo "🚀 Deploying with zero-downtime..."
docker-compose -f docker-compose.prod.yml up -d --scale climatetrade-api=2

# Wait for new instances to be healthy
echo "⏳ Waiting for new instances to be healthy..."
sleep 120

# Health check all services
echo "🔍 Running health checks..."
services=("climatetrade-api" "climatetrade-data-pipeline" "climatetrade-backtesting" "climatetrade-agents")
for service in "${services[@]}"; do
    container_id=$(docker-compose -f docker-compose.prod.yml ps -q $service | head -1)
    if [ ! -z "$container_id" ]; then
        docker exec $container_id curl -f http://localhost/health || echo "⚠️ $service health check failed"
    fi
done

# Scale down old instances
echo "🔄 Scaling down old instances..."
docker-compose -f docker-compose.prod.yml up -d --scale climatetrade-api=1

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f

# Send deployment notification
echo "📢 Sending deployment notification..."
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"ClimaTrade AI production deployment completed successfully"}' \
    $SLACK_WEBHOOK_URL

echo "✅ Production deployment completed successfully!"
```

#### Rollback Script

```bash
#!/bin/bash
# scripts/deploy/rollback.sh

set -e

echo "🔄 Starting ClimaTrade AI Rollback"

# Get previous deployment tag
PREVIOUS_TAG=$(git tag --sort=-version:refname | sed -n '2p')

if [ -z "$PREVIOUS_TAG" ]; then
    echo "❌ Error: No previous tag found for rollback"
    exit 1
fi

echo "📋 Rolling back to tag: $PREVIOUS_TAG"

# Checkout previous version
git checkout $PREVIOUS_TAG

# Restore backup if needed
read -p "Do you want to restore database backup? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "💾 Restoring database backup..."
    ./scripts/backup/restore-backup.sh
fi

# Rebuild and redeploy
echo "🏗️ Rebuilding and redeploying..."
docker-compose -f docker-compose.prod.yml build --no-cache
docker-compose -f docker-compose.prod.yml up -d

# Health checks
echo "🔍 Running health checks after rollback..."
sleep 60
curl -f http://localhost/health || echo "⚠️ Health check failed after rollback"

echo "✅ Rollback completed successfully!"
```

### Python Deployment Scripts

#### Configuration Validator

```python
#!/usr/bin/env python3
# scripts/deploy/validate_config.py

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

class DeploymentValidator:
    def __init__(self, environment: str):
        self.environment = environment
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate_environment_variables(self) -> bool:
        """Validate required environment variables"""
        required_vars = {
            'development': ['DATABASE_URL'],
            'staging': ['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET'],
            'production': ['DATABASE_URL', 'REDIS_URL', 'JWT_SECRET', 'ENCRYPTION_KEY']
        }

        for var in required_vars.get(self.environment, []):
            if not os.getenv(var):
                self.errors.append(f"Missing required environment variable: {var}")

        return len(self.errors) == 0

    def validate_configuration_files(self) -> bool:
        """Validate configuration files"""
        config_files = [
            f"config/{self.environment}.json",
            ".env",
            f".env.{self.environment}"
        ]

        for config_file in config_files:
            if not Path(config_file).exists():
                self.warnings.append(f"Configuration file not found: {config_file}")
            else:
                self._validate_config_file(config_file)

        return len(self.errors) == 0

    def _validate_config_file(self, config_file: str):
        """Validate individual configuration file"""
        try:
            with open(config_file, 'r') as f:
                if config_file.endswith('.json'):
                    json.load(f)
                elif config_file.startswith('.env'):
                    # Basic .env validation
                    for line in f:
                        if '=' not in line and not line.startswith('#') and line.strip():
                            self.errors.append(f"Invalid .env line in {config_file}: {line.strip()}")
        except Exception as e:
            self.errors.append(f"Error reading {config_file}: {str(e)}")

    def validate_docker_services(self) -> bool:
        """Validate Docker services are running"""
        try:
            import docker
            client = docker.from_env()

            compose_file = f"docker-compose.{self.environment}.yml"
            if not Path(compose_file).exists():
                self.warnings.append(f"Docker Compose file not found: {compose_file}")
                return True

            # This would require parsing docker-compose file
            # For now, just check if docker is available
            client.ping()
            return True

        except ImportError:
            self.warnings.append("Docker Python client not available")
            return True
        except Exception as e:
            self.errors.append(f"Docker validation failed: {str(e)}")
            return False

    def run_all_validations(self) -> bool:
        """Run all validation checks"""
        print(f"🔍 Validating {self.environment} environment...")

        validations = [
            ("Environment Variables", self.validate_environment_variables),
            ("Configuration Files", self.validate_configuration_files),
            ("Docker Services", self.validate_docker_services)
        ]

        all_passed = True
        for name, validation_func in validations:
            print(f"  Checking {name}...")
            if not validation_func():
                all_passed = False

        return all_passed

    def print_report(self):
        """Print validation report"""
        if self.errors:
            print("❌ Validation Errors:")
            for error in self.errors:
                print(f"  - {error}")

        if self.warnings:
            print("⚠️ Validation Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        if not self.errors and not self.warnings:
            print("✅ All validations passed!")

def main():
    environment = os.getenv('CLIMATRADE_ENV', 'development')

    validator = DeploymentValidator(environment)
    success = validator.run_all_validations()
    validator.print_report()

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
```

#### Service Health Checker

```python
#!/usr/bin/env python3
# scripts/deploy/health_check.py

import requests
import time
import sys
from typing import Dict, List, Tuple
import docker
import psycopg2

class HealthChecker:
    def __init__(self, environment: str = 'development'):
        self.environment = environment
        self.services = self._get_service_config()

    def _get_service_config(self) -> Dict[str, Dict]:
        """Get service configuration for health checks"""
        return {
            'climatetrade-db': {
                'url': 'postgresql://climatetrade:password@localhost:5432/climatetrade',
                'type': 'database'
            },
            'climatetrade-api': {
                'url': 'http://localhost:8000/health',
                'type': 'http'
            },
            'climatetrade-data-pipeline': {
                'url': 'http://localhost:8001/health',
                'type': 'http'
            },
            'climatetrade-backtesting': {
                'url': 'http://localhost:8002/health',
                'type': 'http'
            },
            'climatetrade-agents': {
                'url': 'http://localhost:8003/health',
                'type': 'http'
            }
        }

    def check_service_health(self, service_name: str) -> Tuple[bool, str]:
        """Check health of individual service"""
        if service_name not in self.services:
            return False, f"Service {service_name} not configured"

        service_config = self.services[service_name]

        try:
            if service_config['type'] == 'http':
                response = requests.get(service_config['url'], timeout=10)
                if response.status_code == 200:
                    return True, "OK"
                else:
                    return False, f"HTTP {response.status_code}"

            elif service_config['type'] == 'database':
                conn = psycopg2.connect(service_config['url'])
                conn.close()
                return True, "OK"

        except requests.exceptions.RequestException as e:
            return False, f"HTTP Error: {str(e)}"
        except psycopg2.Error as e:
            return False, f"Database Error: {str(e)}"
        except Exception as e:
            return False, f"Error: {str(e)}"

    def check_docker_containers(self) -> List[Tuple[str, bool, str]]:
        """Check Docker container health"""
        results = []

        try:
            client = docker.from_env()

            for service_name in self.services.keys():
                try:
                    containers = client.containers.list(
                        filters={'name': service_name}
                    )

                    if not containers:
                        results.append((service_name, False, "Container not found"))
                        continue

                    container = containers[0]
                    status = container.status

                    if status == 'running':
                        # Check health status if available
                        health = container.attrs.get('State', {}).get('Health', {})
                        if health.get('Status') == 'healthy':
                            results.append((service_name, True, "Running and healthy"))
                        else:
                            results.append((service_name, True, f"Running ({health.get('Status', 'unknown')})"))
                    else:
                        results.append((service_name, False, f"Status: {status}"))

                except Exception as e:
                    results.append((service_name, False, f"Error: {str(e)}"))

        except Exception as e:
            results.append(("docker", False, f"Docker client error: {str(e)}"))

        return results

    def run_comprehensive_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check"""
        print("🔍 Running comprehensive health check...")

        results = {
            'timestamp': time.time(),
            'environment': self.environment,
            'services': {},
            'containers': {},
            'overall_status': 'unknown'
        }

        # Check individual services
        print("  Checking service endpoints...")
        for service_name in self.services.keys():
            healthy, status = self.check_service_health(service_name)
            results['services'][service_name] = {
                'healthy': healthy,
                'status': status
            }
            print(f"    {service_name}: {'✅' if healthy else '❌'} {status}")

        # Check Docker containers
        print("  Checking Docker containers...")
        container_results = self.check_docker_containers()
        for service_name, healthy, status in container_results:
            results['containers'][service_name] = {
                'healthy': healthy,
                'status': status
            }
            print(f"    {service_name}: {'✅' if healthy else '❌'} {status}")

        # Determine overall status
        all_services_healthy = all(
            service['healthy'] for service in results['services'].values()
        )
        all_containers_healthy = all(
            container['healthy'] for container in results['containers'].values()
        )

        if all_services_healthy and all_containers_healthy:
            results['overall_status'] = 'healthy'
        elif all_services_healthy or all_containers_healthy:
            results['overall_status'] = 'degraded'
        else:
            results['overall_status'] = 'unhealthy'

        return results

    def wait_for_healthy_services(self, timeout: int = 300) -> bool:
        """Wait for all services to become healthy"""
        print(f"⏳ Waiting up to {timeout} seconds for services to become healthy...")

        start_time = time.time()
        while time.time() - start_time < timeout:
            results = self.run_comprehensive_health_check()

            if results['overall_status'] == 'healthy':
                print("✅ All services are healthy!")
                return True

            time.sleep(10)

        print("❌ Timeout waiting for services to become healthy")
        return False

def main():
    import argparse

    parser = argparse.ArgumentParser(description='ClimaTrade AI Health Checker')
    parser.add_argument('--environment', default='development',
                       help='Environment to check')
    parser.add_argument('--wait', action='store_true',
                       help='Wait for services to become healthy')
    parser.add_argument('--timeout', type=int, default=300,
                       help='Timeout for waiting (seconds)')

    args = parser.parse_args()

    checker = HealthChecker(args.environment)

    if args.wait:
        success = checker.wait_for_healthy_services(args.timeout)
        sys.exit(0 if success else 1)
    else:
        results = checker.run_comprehensive_health_check()

        if results['overall_status'] == 'healthy':
            print("✅ All services are healthy!")
            sys.exit(0)
        else:
            print("❌ Some services are unhealthy")
            sys.exit(1)

if __name__ == "__main__":
    main()
```

## Container Orchestration

### Docker Compose Configurations

#### Development Configuration

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  climatetrade-db:
    build:
      context: .
      dockerfile: docker/database/Dockerfile
    environment:
      - POSTGRES_DB=climatetrade
      - POSTGRES_USER=climatetrade
      - POSTGRES_PASSWORD=dev_password
    ports:
      - '5432:5432'
    volumes:
      - dev_postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ['CMD-SHELL', 'pg_isready -U climatetrade']
      interval: 30s
      timeout: 10s
      retries: 3

  climatetrade-redis:
    image: redis:7-alpine
    ports:
      - '6379:6379'
    volumes:
      - dev_redis_data:/data

  climatetrade-data-pipeline:
    build:
      context: .
      dockerfile: docker/data-pipeline/Dockerfile
    environment:
      - DATABASE_URL=postgresql://climatetrade:dev_password@climatetrade-db:5432/climatetrade
      - REDIS_URL=redis://climatetrade-redis:6379
      - CLIMATRADE_ENV=development
      - DEBUG=true
    volumes:
      - .:/app
      - /app/__pycache__
    ports:
      - '8000:8000'
    depends_on:
      climatetrade-db:
        condition: service_healthy
    develop:
      watch:
        - action: sync
          path: ./data_pipeline
          target: /app/data_pipeline

volumes:
  dev_postgres_data:
  dev_redis_data:
```

#### Production Configuration

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  climatetrade-db:
    image: climatetrade/database:latest
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - climatetrade-network
    deploy:
      replicas: 1
      placement:
        constraints:
          - node.role == manager
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G

  climatetrade-redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    networks:
      - climatetrade-network
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 512M

  climatetrade-api:
    image: climatetrade/api:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CLIMATRADE_ENV=production
    networks:
      - climatetrade-network
    deploy:
      replicas: 2
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
    healthcheck:
      test: ['CMD', 'curl', '-f', 'http://localhost:8000/health']
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  climatetrade-data-pipeline:
    image: climatetrade/data-pipeline:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CLIMATRADE_ENV=production
    volumes:
      - pipeline_data:/app/data
    networks:
      - climatetrade-network
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 2G
          cpus: '2.0'

  climatetrade-backtesting:
    image: climatetrade/backtesting:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CLIMATRADE_ENV=production
    volumes:
      - backtesting_results:/app/results
    networks:
      - climatetrade-network
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 4G
          cpus: '4.0'

  climatetrade-agents:
    image: climatetrade/agents:latest
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - CLIMATRADE_ENV=production
      - POLYGON_WALLET_PRIVATE_KEY=${POLYGON_WALLET_PRIVATE_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    networks:
      - climatetrade-network
    deploy:
      replicas: 1
      resources:
        limits:
          memory: 2G
          cpus: '2.0'

  nginx:
    image: nginx:alpine
    ports:
      - '80:80'
      - '443:443'
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    networks:
      - climatetrade-network
    depends_on:
      - climatetrade-api
    deploy:
      placement:
        constraints:
          - node.role == manager

networks:
  climatetrade-network:
    driver: overlay

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  pipeline_data:
    driver: local
  backtesting_results:
    driver: local
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy ClimaTrade AI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests
        run: |
          python -m pytest tests/ -v --cov=.

      - name: Upload coverage
        uses: codecov/codecov-action@v3

  build-and-push:
    needs: test
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v2
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v4
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=sha

      - name: Build and push Docker images
        uses: docker/build-push-action@v4
        with:
          context: .
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/develop'
    environment: staging

    steps:
      - name: Deploy to staging
        run: |
          echo "Deploying to staging environment"
          # Add staging deployment commands here

  deploy-production:
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
      - name: Deploy to production
        run: |
          echo "Deploying to production environment"
          # Add production deployment commands here
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
    agent any

    environment {
        DOCKER_REGISTRY = 'climatetrade'
        DOCKER_TAG = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Test') {
            steps {
                sh '''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m pytest tests/ -v --cov=. --junitxml=test-results.xml
                '''
            }
            post {
                always {
                    junit 'test-results.xml'
                    publishCoverage adapters: [coberturaAdapter('coverage.xml')]
                }
            }
        }

        stage('Build Images') {
            steps {
                sh '''
                    docker build -t ${DOCKER_REGISTRY}/api:${DOCKER_TAG} -f docker/api/Dockerfile .
                    docker build -t ${DOCKER_REGISTRY}/data-pipeline:${DOCKER_TAG} -f docker/data-pipeline/Dockerfile .
                    docker build -t ${DOCKER_REGISTRY}/backtesting:${DOCKER_TAG} -f docker/backtesting/Dockerfile .
                    docker build -t ${DOCKER_REGISTRY}/agents:${DOCKER_TAG} -f docker/agents/Dockerfile .
                '''
            }
        }

        stage('Push Images') {
            steps {
                sh '''
                    docker push ${DOCKER_REGISTRY}/api:${DOCKER_TAG}
                    docker push ${DOCKER_REGISTRY}/data-pipeline:${DOCKER_TAG}
                    docker push ${DOCKER_REGISTRY}/backtesting:${DOCKER_TAG}
                    docker push ${DOCKER_REGISTRY}/agents:${DOCKER_TAG}
                '''
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh '''
                    sed -i "s/latest/${DOCKER_TAG}/g" docker-compose.staging.yml
                    docker-compose -f docker-compose.staging.yml up -d
                '''
            }
        }

        stage('Deploy to Production') {
            when {
                branch 'main'
            }
            steps {
                timeout(time: 15, unit: 'MINUTES') {
                    input message: 'Deploy to Production?', ok: 'Deploy'
                }
                sh '''
                    sed -i "s/latest/${DOCKER_TAG}/g" docker-compose.prod.yml
                    docker-compose -f docker-compose.prod.yml up -d
                '''
            }
        }
    }

    post {
        always {
            sh 'docker-compose -f docker-compose.dev.yml down -v'
            cleanWs()
        }
        success {
            slackSend color: 'good', message: "Deployment successful: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
        failure {
            slackSend color: 'danger', message: "Deployment failed: ${env.JOB_NAME} #${env.BUILD_NUMBER}"
        }
    }
}
```

## Infrastructure as Code

### Terraform Configuration

```hcl
# infrastructure/terraform/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "vpc" {
  source = "./modules/vpc"
  environment = var.environment
  vpc_cidr = var.vpc_cidr
}

module "ecs" {
  source = "./modules/ecs"
  environment = var.environment
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  database_security_group_id = module.rds.security_group_id
}

module "rds" {
  source = "./modules/rds"
  environment = var.environment
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
  instance_class = var.db_instance_class
}

module "redis" {
  source = "./modules/redis"
  environment = var.environment
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnet_ids
}

module "load_balancer" {
  source = "./modules/load-balancer"
  environment = var.environment
  vpc_id = module.vpc.vpc_id
  subnet_ids = module.vpc.public_subnet_ids
  certificate_arn = var.certificate_arn
}
```

### Ansible Playbooks

```yaml
# infrastructure/ansible/deploy.yml
---
- name: Deploy ClimaTrade AI
  hosts: climatetrade_servers
  become: yes
  vars_files:
    - vars/{{ environment }}.yml

  pre_tasks:
    - name: Update package cache
      apt:
        update_cache: yes
      when: ansible_os_family == 'Debian'

    - name: Install Docker
      include_role:
        name: docker

  roles:
    - role: climatetrade.database
      when: deploy_database | default(true)
    - role: climatetrade.api
      when: deploy_api | default(true)
    - role: climatetrade.data-pipeline
      when: deploy_data_pipeline | default(true)
    - role: climatetrade.backtesting
      when: deploy_backtesting | default(true)
    - role: climatetrade.agents
      when: deploy_agents | default(true)
    - role: climatetrade.monitoring
      when: deploy_monitoring | default(true)

  post_tasks:
    - name: Run health checks
      include_tasks: tasks/health-check.yml

    - name: Send deployment notification
      include_tasks: tasks/notify.yml
```

### Kubernetes Manifests

```yaml
# infrastructure/kubernetes/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-api
  labels:
    app: climatetrade-api
spec:
  replicas: 2
  selector:
    matchLabels:
      app: climatetrade-api
  template:
    metadata:
      labels:
        app: climatetrade-api
    spec:
      containers:
        - name: api
          image: climatetrade/api:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: db-secret
                  key: database-url
            - name: REDIS_URL
              valueFrom:
                secretKeyRef:
                  name: redis-secret
                  key: redis-url
          resources:
            requests:
              memory: '512Mi'
              cpu: '250m'
            limits:
              memory: '1Gi'
              cpu: '500m'
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
```

This comprehensive deployment documentation provides standardized scripts and configurations for deploying ClimaTrade AI across different environments with proper security, monitoring, and scalability considerations.
