# ClimaTrade AI Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Quick Start](#quick-start)
4. [Environment Configuration](#environment-configuration)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Deployment Scripts](#deployment-scripts)
8. [CI/CD Pipelines](#ci-cd-pipelines)
9. [Infrastructure as Code](#infrastructure-as-code)
10. [Monitoring and Maintenance](#monitoring-and-maintenance)
11. [Troubleshooting](#troubleshooting)
12. [Security Best Practices](#security-best-practices)
13. [Operations Guide](#operations-guide)

## Overview

ClimaTrade AI is a comprehensive weather-informed trading intelligence system for Polymarket. This deployment guide provides unified instructions for setting up all components of the system across different environments.

### Architecture Components

- **Database**: SQLite/PostgreSQL-based data storage with migration system
- **Data Pipeline**: Weather data ingestion and validation framework
- **Backtesting Framework**: Strategy testing and optimization
- **Agents**: AI-powered trading agents with Docker support
- **Resolution Subgraph**: Historical market resolution data
- **Web Interface**: Dashboard and user interface

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

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows 10+
- **Python**: 3.8+ (3.9 recommended)
- **Node.js**: 16+ (for subgraph development)
- **Docker**: 20.10+ (for containerized deployment)
- **Docker Compose**: 2.0+ (for multi-service deployment)
- **Kubernetes**: 1.24+ (for production deployment)

### Network Requirements

- Internet access for weather API calls
- Polygon RPC endpoint access
- Polymarket API access (if using live trading)

### Hardware Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Storage**: 50GB free space for data and models
- **CPU**: Multi-core processor for parallel processing

### Kubernetes Cluster Requirements

- **Kubernetes Version**: 1.24+
- **Nodes**: Minimum 3 nodes for high availability
- **Resources**:
  - CPU: 8 cores total
  - Memory: 16GB total
  - Storage: 100GB SSD

### Required Tools

```bash
# Install kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/

# Install Helm
curl https://get.helm.sh/helm-v3.11.0-linux-amd64.tar.gz -o helm.tar.gz
tar -zxvf helm.tar.gz
sudo mv linux-amd64/helm /usr/local/bin/

# Install kustomize
curl -s "https://raw.githubusercontent.com/kubernetes-sigs/kustomize/master/hack/install_kustomize.sh" | bash
sudo mv kustomize /usr/local/bin/
```

## Quick Start

### Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd climatetrade

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install core dependencies
pip install -r requirements.txt

# Set up database
cd database
python setup_database.py
python migrations/migration_manager.py apply

# Start resolution subgraph (optional)
cd ../scripts/resolution-subgraph
docker compose up -d

# Run basic validation
cd ../../data_pipeline
python -c "from validation_framework import create_validator; print('Validation framework ready')"
```

### Docker Deployment

```bash
# Build and run agents
cd scripts/agents
./scripts/bash/build-docker.sh
./scripts/bash/run-docker.sh

# Or use docker-compose for full stack
docker compose -f docker-compose.prod.yml up -d
```

## Environment Configuration

### Development Environment

**Database Configuration:**

```bash
# Use local SQLite database
DATABASE_URL="sqlite:///data/climatetrade.db"
DEBUG=true
LOG_LEVEL=DEBUG
```

**API Configuration:**

```bash
# Use test endpoints and limited rate limits
WEATHER_API_TIMEOUT=30
POLYMARKET_API_TIMEOUT=30
MAX_API_CALLS_PER_MINUTE=60
```

### Staging Environment

**Database Configuration:**

```bash
# Use dedicated staging database
DATABASE_URL="postgresql://user:password@staging-db:5432/climatetrade"
DEBUG=false
LOG_LEVEL=INFO
```

**Security Configuration:**

```bash
# Enable basic security features
ENABLE_HTTPS=true
API_KEY_REQUIRED=true
RATE_LIMITING_ENABLED=true
```

### Production Environment

**Database Configuration:**

```bash
# Use production database cluster
DATABASE_URL="postgresql://user:password@prod-db-cluster:5432/climatetrade"
DEBUG=false
LOG_LEVEL=WARNING
BACKUP_ENABLED=true
```

**Security Configuration:**

```bash
# Full security configuration
ENABLE_HTTPS=true
API_KEY_REQUIRED=true
RATE_LIMITING_ENABLED=true
ENCRYPTION_ENABLED=true
AUDIT_LOGGING_ENABLED=true
```

## Docker Deployment

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

## Kubernetes Deployment

### Cluster Setup

```bash
# Create cluster (using k3s for simplicity)
curl -sfL https://get.k3s.io | sh -

# Verify cluster
kubectl get nodes
kubectl get pods -A

# Install NGINX Ingress Controller
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm install nginx-ingress ingress-nginx/ingress-nginx

# Install cert-manager for SSL
helm repo add jetstack https://charts.jetstack.io
helm install cert-manager jetstack/cert-manager --version v1.11.0 --set installCRDs=true
```

### Namespace

```yaml
# k8s/namespace.yml
apiVersion: v1
kind: Namespace
metadata:
  name: climatetrade
  labels:
    name: climatetrade
    environment: production
```

### Secrets and ConfigMaps

#### Database Secrets

```yaml
# k8s/secrets/database-secret.yml
apiVersion: v1
kind: Secret
metadata:
  name: climatetrade-db-secret
  namespace: climatetrade
type: Opaque
data:
  # Base64 encoded values
  username: Y2xpbWF0ZXRyYWRl # climatetrade
  password: c2VjdXJlX2RiX3Bhc3N3b3Jk # secure_db_password
  database: Y2xpbWF0ZXRyYWRlX3Byb2Q= # climatetrade_prod
  host: Y2xpbWF0ZXRyYWRlLWRiLmNsaW1hdGV0cmFkZS5zdmMuY2x1c3Rlci5sb2NhbA== # climatetrade-db.climatetrade.svc.cluster.local
```

#### API Secrets

```yaml
# k8s/secrets/api-secret.yml
apiVersion: v1
kind: Secret
metadata:
  name: climatetrade-api-secret
  namespace: climatetrade
type: Opaque
data:
  jwt-secret: <base64-encoded-jwt-secret>
  encryption-key: <base64-encoded-encryption-key>
  polygon-wallet-private-key: <base64-encoded-private-key>
  openai-api-key: <base64-encoded-openai-key>
  polymarket-api-key: <base64-encoded-polymarket-key>
  polymarket-secret: <base64-encoded-polymarket-secret>
```

#### Application ConfigMap

```yaml
# k8s/configmaps/app-config.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: climatetrade-config
  namespace: climatetrade
data:
  ENVIRONMENT: 'production'
  LOG_LEVEL: 'INFO'
  DEBUG: 'false'
  API_TIMEOUT: '120'
  MAX_API_RETRIES: '10'
  API_RATE_LIMIT: '10000'
  REDIS_CACHE_TTL: '3600'
  DATABASE_CONNECTION_POOL_SIZE: '50'
  DATABASE_MAX_CONNECTIONS: '100'
  BACKTESTING_MAX_PARALLEL: '4'
  AGENTS_MAX_CONCURRENT_TRADES: '10'
  MONITORING_METRICS_ENABLED: 'true'
  HEALTH_CHECK_ENABLED: 'true'
```

### Database Deployment

#### PostgreSQL StatefulSet

```yaml
# k8s/database/postgresql-statefulset.yml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: climatetrade-postgresql
  namespace: climatetrade
spec:
  serviceName: climatetrade-postgresql
  replicas: 1
  selector:
    matchLabels:
      app: climatetrade-postgresql
  template:
    metadata:
      labels:
        app: climatetrade-postgresql
    spec:
      containers:
        - name: postgresql
          image: postgres:13-alpine
          ports:
            - containerPort: 5432
              name: postgresql
          env:
            - name: POSTGRES_DB
              valueFrom:
                secretKeyRef:
                  name: climatetrade-db-secret
                  key: database
            - name: POSTGRES_USER
              valueFrom:
                secretKeyRef:
                  name: climatetrade-db-secret
                  key: username
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: climatetrade-db-secret
                  key: password
            - name: PGDATA
              value: /var/lib/postgresql/data/pgdata
          volumeMounts:
            - name: postgresql-data
              mountPath: /var/lib/postgresql/data
            - name: postgresql-init
              mountPath: /docker-entrypoint-initdb.d
          resources:
            requests:
              memory: '1Gi'
              cpu: '500m'
            limits:
              memory: '2Gi'
              cpu: '1000m'
          livenessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - climatetrade
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - pg_isready
                - -U
                - climatetrade
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: postgresql-init
          configMap:
            name: postgresql-init-config
  volumeClaimTemplates:
    - metadata:
      name: postgresql-data
    spec:
      accessModes: ['ReadWriteOnce']
      resources:
        requests:
          storage: 50Gi
      storageClassName: fast-ssd
```

### Cache Deployment

#### Redis Deployment

```yaml
# k8s/cache/redis-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-redis
  namespace: climatetrade
spec:
  replicas: 1
  selector:
    matchLabels:
      app: climatetrade-redis
  template:
    metadata:
      labels:
        app: climatetrade-redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
              name: redis
          command: ['redis-server']
          args:
            [
              '--appendonly',
              'yes',
              '--maxmemory',
              '512mb',
              '--maxmemory-policy',
              'allkeys-lru',
            ]
          volumeMounts:
            - name: redis-data
              mountPath: /data
          resources:
            requests:
              memory: '256Mi'
              cpu: '100m'
            limits:
              memory: '512Mi'
              cpu: '200m'
          livenessProbe:
            exec:
              command:
                - redis-cli
                - ping
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            exec:
              command:
                - redis-cli
                - ping
            initialDelaySeconds: 5
            periodSeconds: 5
      volumes:
        - name: redis-data
          persistentVolumeClaim:
            claimName: redis-pvc
```

### API Service Deployment

#### API Deployment

```yaml
# k8s/api/api-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-api
  namespace: climatetrade
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
              name: http
          env:
            - name: ENVIRONMENT
              valueFrom:
                configMapKeyRef:
                  name: climatetrade-config
                  key: ENVIRONMENT
            - name: DATABASE_URL
              value: postgresql://$(DB_USER):$(DB_PASSWORD)@climatetrade-postgresql:5432/$(DB_NAME)
            - name: REDIS_URL
              value: redis://climatetrade-redis:6379
            - name: JWT_SECRET
              valueFrom:
                secretKeyRef:
                  name: climatetrade-api-secret
                  key: jwt-secret
            - name: ENCRYPTION_KEY
              valueFrom:
                secretKeyRef:
                  name: climatetrade-api-secret
                  key: encryption-key
          envFrom:
            - configMapRef:
                name: climatetrade-config
          volumeMounts:
            - name: logs
              mountPath: /app/logs
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
            timeoutSeconds: 5
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
            timeoutSeconds: 3
      volumes:
        - name: logs
          emptyDir: {}
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
        fsGroup: 1001
```

### Ingress Configuration

#### NGINX Ingress

```yaml
# k8s/ingress/ingress.yml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: climatetrade-ingress
  namespace: climatetrade
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/force-ssl-redirect: 'true'
    nginx.ingress.kubernetes.io/proxy-body-size: '50m'
    nginx.ingress.kubernetes.io/proxy-read-timeout: '300'
    nginx.ingress.kubernetes.io/proxy-send-timeout: '300'
    cert-manager.io/cluster-issuer: 'letsencrypt-prod'
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - api.climatetrade.ai
        - app.climatetrade.ai
      secretName: climatetrade-tls
  rules:
    - host: api.climatetrade.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: climatetrade-api
                port:
                  number: 80
    - host: app.climatetrade.ai
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: climatetrade-web
                port:
                  number: 80
```

### Horizontal Pod Autoscaling

#### API HPA

```yaml
# k8s/hpa/api-hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: climatetrade-api-hpa
  namespace: climatetrade
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: climatetrade-api
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Percent
          value: 50
          periodSeconds: 60
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


if __name__ == "__main__":
    main()
```

## CI/CD Pipelines

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
                sh ''''
                    python -m venv venv
                    . venv/bin/activate
                    pip install -r requirements.txt
                    python -m pytest tests/ -v --cov=. --junitxml=test-results.xml
                ''''
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
                sh ''''
                    docker build -t ${DOCKER_REGISTRY}/api:${DOCKER_TAG} -f docker/api/Dockerfile .
                    docker build -t ${DOCKER_REGISTRY}/data-pipeline:${DOCKER_TAG} -f docker/data-pipeline/Dockerfile .
                    docker build -t ${DOCKER_REGISTRY}/backtesting:${DOCKER_TAG} -f docker/backtesting/Dockerfile .
                    docker build -t ${DOCKER_REGISTRY}/agents:${DOCKER_TAG} -f docker/agents/Dockerfile .
                ''''
            }
        }

        stage('Push Images') {
            steps {
                sh ''''
                    docker push ${DOCKER_REGISTRY}/api:${DOCKER_TAG}
                    docker push ${DOCKER_REGISTRY}/data-pipeline:${DOCKER_TAG}
                    docker push ${DOCKER_REGISTRY}/backtesting:${DOCKER_TAG}
                    docker push ${DOCKER_REGISTRY}/agents:${DOCKER_TAG}
                ''''
            }
        }

        stage('Deploy to Staging') {
            when {
                branch 'develop'
            }
            steps {
                sh ''''
                    sed -i "s/latest/${DOCKER_TAG}/g" docker-compose.staging.yml
                    docker-compose -f docker-compose.staging.yml up -d
                ''''
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
                sh ''''
                    sed -i "s/latest/${DOCKER_TAG}/g" docker-compose.prod.yml
                    docker-compose -f docker-compose.prod.yml up -d
                ''''
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

## Monitoring and Maintenance

### Health Checks

```python
# health_check.py
from database.connection import get_db_connection
from data_pipeline.validation_framework import create_validator

def perform_health_check():
    """Perform comprehensive system health check"""
    checks = {
        'database': check_database_health(),
        'data_pipeline': check_data_pipeline_health(),
        'agents': check_agents_health(),
        'subgraph': check_subgraph_health()
    }

    return all(checks.values()), checks

def check_database_health():
    """Check database connectivity and integrity"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM weather_data")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False
```

### Backup Procedures

```bash
# Daily backup script
# scripts/backup/daily-backup.sh
#!/bin/bash
BACKUP_DIR="/backups/$(date +%Y%m%d)"
mkdir -p $BACKUP_DIR

# Database backup
sqlite3 /data/climatetrade.db ".backup '$BACKUP_DIR/climatetrade.db'"

# Configuration backup
cp -r /config $BACKUP_DIR/

# Logs backup
cp -r /logs $BACKUP_DIR/

# Compress backup
tar -czf $BACKUP_DIR.tar.gz $BACKUP_DIR
```

### Log Management

```python
# logging_config.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    """Configure comprehensive logging"""
    logger = logging.getLogger('climatetrade')
    logger.setLevel(logging.INFO)

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/climatetrade.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )

    # Console handler
    console_handler = logging.StreamHandler()

    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
```

### Performance Monitoring

```python
# metrics_collector.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Metrics definitions
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['method', 'endpoint'])
ACTIVE_CONNECTIONS = Gauge('active_connections', 'Number of active connections')

def track_request_time(method, endpoint):
    """Decorator to track request timing"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            duration = time.time() - start_time

            REQUEST_COUNT.labels(method=method, endpoint=endpoint).inc()
            REQUEST_LATENCY.labels(method=method, endpoint=endpoint).observe(duration)

            return result
        return wrapper
    return decorator
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**

   ```bash
   # Check database file permissions
   ls -la data/climatetrade.db

   # Verify SQLite installation
   sqlite3 --version

   # Test database connection
   python -c "import sqlite3; conn = sqlite3.connect('data/climatetrade.db'); print('Connection successful')"
   ```

2. **API Rate Limiting**

   ```python
   # Implement exponential backoff
   import time
   import requests

   def api_call_with_retry(url, max_retries=3):
       for attempt in range(max_retries):
           try:
               response = requests.get(url)
               response.raise_for_status()
               return response.json()
           except requests.exceptions.RequestException as e:
               if attempt < max_retries - 1:
                   wait_time = 2 ** attempt
                   time.sleep(wait_time)
               else:
                   raise e
   ```

3. **Memory Issues**

   ```python
   # Monitor memory usage
   import psutil
   import os

   def check_memory_usage():
       process = psutil.Process(os.getpid())
       memory_usage = process.memory_info().rss / 1024 / 1024  # MB
       print(f"Memory usage: {memory_usage:.2f} MB")

       if memory_usage > 1000:  # 1GB threshold
           # Implement memory cleanup
           gc.collect()
   ```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with verbose output
python main.py --verbose --debug

# Enable database query logging
export SQLALCHEMY_ECHO=True
```

## Security Best Practices

### API Key Management

```python
# secure_config.py
import os
from cryptography.fernet import Fernet

class SecureConfig:
    def __init__(self):
        self.key = os.getenv('ENCRYPTION_KEY')
        self.cipher = Fernet(self.key)

    def encrypt_api_key(self, api_key):
        """Encrypt API key for storage"""
        return self.cipher.encrypt(api_key.encode()).decode()

    def decrypt_api_key(self, encrypted_key):
        """Decrypt API key for use"""
        return self.cipher.decrypt(encrypted_key.encode()).decode()
```

### Network Security

```yaml
# nginx.conf for API gateway
server {
    listen 443 ssl http2;
    server_name api.climatetrade.ai;

    ssl_certificate /etc/ssl/certs/climatetrade.crt;
    ssl_certificate_key /etc/ssl/private/climatetrade.key;

    # Rate limiting
    limit_req zone=api burst=10 nodelay;

    # CORS configuration
    add_header 'Access-Control-Allow-Origin' 'https://dashboard.climatetrade.ai';
    add_header 'Access-Control-Allow-Methods' 'GET, POST, PUT, DELETE, OPTIONS';
    add_header 'Access-Control-Allow-Headers' 'Authorization, Content-Type';

    location /api/ {
        proxy_pass http://climatetrade-api:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Data Encryption

```python
# data_encryption.py
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
import os

class DataEncryption:
    def __init__(self, password):
        self.salt = os.urandom(16)
        self.key = self._derive_key(password, self.salt)

    def _derive_key(self, password, salt):
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return kdf.derive(password.encode())

    def encrypt_data(self, data):
        """Encrypt sensitive data"""
        iv = os.urandom(16)
        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        encryptor = cipher.encryptor()

        # Pad data to block size
        block_size = 16
        padding_length = block_size - (len(data) % block_size)
        padded_data = data + (chr(padding_length) * padding_length)

        encrypted = encryptor.update(padded_data.encode()) + encryptor.finalize()
        return iv + encrypted

    def decrypt_data(self, encrypted_data):
        """Decrypt sensitive data"""
        iv = encrypted_data[:16]
        encrypted = encrypted_data[16:]

        cipher = Cipher(algorithms.AES(self.key), modes.CBC(iv))
        decryptor = cipher.decryptor()

        decrypted_padded = decryptor.update(encrypted) + decryptor.finalize()

        # Remove padding
        padding_length = ord(decrypted_padded[-1])
        decrypted = decrypted_padded[:-padding_length]

        return decrypted.decode()
```

## Operations Guide

This section is a placeholder for the merged content from the operations and troubleshooting guides.

```
