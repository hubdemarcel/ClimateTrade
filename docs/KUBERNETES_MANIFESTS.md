# ClimaTrade AI Kubernetes Manifests

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Namespace](#namespace)
4. [Secrets and ConfigMaps](#secrets-and-configmaps)
5. [Database Deployment](#database-deployment)
6. [Cache Deployment](#cache-deployment)
7. [API Service Deployment](#api-service-deployment)
8. [Data Pipeline Deployment](#data-pipeline-deployment)
9. [Backtesting Service Deployment](#backtesting-service-deployment)
10. [Agents Service Deployment](#agents-service-deployment)
11. [Web Interface Deployment](#web-interface-deployment)
12. [Ingress Configuration](#ingress-configuration)
13. [Monitoring and Logging](#monitoring-and-logging)
14. [Horizontal Pod Autoscaling](#horizontal-pod-autoscaling)
15. [Backup and Recovery](#backup-and-recovery)
16. [Security Policies](#security-policies)

## Overview

This document provides comprehensive Kubernetes manifests for deploying ClimaTrade AI in production environments. The manifests are designed for high availability, scalability, and security.

### Architecture

```
┌─────────────────┐    ┌─────────────────┐
│   Ingress       │    │   Cert Manager  │
│   (nginx)       │    │   (letsencrypt) │
└─────────────────┘    └─────────────────┘
          │                       │
          └───────────────────────┘
                  │
        ┌─────────────────┐
        │   Services      │
        │                 │
        │ • API Gateway   │
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
        │ • Persistent    │
        │   Volumes       │
        └─────────────────┘
```

## Prerequisites

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

## Namespace

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

## Secrets and ConfigMaps

### Database Secrets

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

### API Secrets

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

### External Service Secrets

```yaml
# k8s/secrets/external-services.yml
apiVersion: v1
kind: Secret
metadata:
  name: climatetrade-external-secret
  namespace: climatetrade
type: Opaque
data:
  polygon-rpc-url: <base64-encoded-rpc-url>
  matic-rpc-url: <base64-encoded-matic-url>
  etherscan-api-key: <base64-encoded-etherscan-key>
  coingecko-api-key: <base64-encoded-coingecko-key>
```

### Application ConfigMap

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

## Database Deployment

### PostgreSQL StatefulSet

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

### PostgreSQL Service

```yaml
# k8s/database/postgresql-service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-postgresql
  namespace: climatetrade
spec:
  selector:
    app: climatetrade-postgresql
  ports:
    - port: 5432
      targetPort: 5432
  clusterIP: None # Headless service for StatefulSet
```

### PostgreSQL Init ConfigMap

```yaml
# k8s/database/postgresql-init-config.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: postgresql-init-config
  namespace: climatetrade
data:
  01-init.sql: |
    -- Create extensions
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

    -- Create database roles
    CREATE ROLE climatetrade_readonly;
    CREATE ROLE climatetrade_readwrite;

    -- Grant permissions
    GRANT CONNECT ON DATABASE climatetrade TO climatetrade_readonly;
    GRANT CONNECT ON DATABASE climatetrade TO climatetrade_readwrite;
    GRANT USAGE ON SCHEMA public TO climatetrade_readonly;
    GRANT USAGE ON SCHEMA public TO climatetrade_readwrite;

    -- Set up monitoring
    CREATE EXTENSION IF NOT EXISTS pg_stat_monitor;
```

## Cache Deployment

### Redis Deployment

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

### Redis Service

```yaml
# k8s/cache/redis-service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-redis
  namespace: climatetrade
spec:
  selector:
    app: climatetrade-redis
  ports:
    - port: 6379
      targetPort: 6379
```

### Redis PVC

```yaml
# k8s/cache/redis-pvc.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: redis-pvc
  namespace: climatetrade
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
  storageClassName: fast-ssd
```

## API Service Deployment

### API Deployment

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

### API Service

```yaml
# k8s/api/api-service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-api
  namespace: climatetrade
  labels:
    app: climatetrade-api
spec:
  selector:
    app: climatetrade-api
  ports:
    - port: 80
      targetPort: 8000
      name: http
  type: ClusterIP
```

## Data Pipeline Deployment

### Data Pipeline Deployment

```yaml
# k8s/data-pipeline/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-data-pipeline
  namespace: climatetrade
spec:
  replicas: 1
  selector:
    matchLabels:
      app: climatetrade-data-pipeline
  template:
    metadata:
      labels:
        app: climatetrade-data-pipeline
    spec:
      containers:
        - name: data-pipeline
          image: climatetrade/data-pipeline:latest
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
          volumeMounts:
            - name: data-storage
              mountPath: /app/data
            - name: logs
              mountPath: /app/logs
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
                - python
                - -c
                - "from data_pipeline.validation_framework import create_validator; print('OK')"
            initialDelaySeconds: 60
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: data-storage
          persistentVolumeClaim:
            claimName: data-pipeline-pvc
        - name: logs
          emptyDir: {}
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
```

### Data Pipeline Service

```yaml
# k8s/data-pipeline/service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-data-pipeline
  namespace: climatetrade
spec:
  selector:
    app: climatetrade-data-pipeline
  ports:
    - port: 80
      targetPort: 8000
      name: http
  type: ClusterIP
```

### Data Pipeline PVC

```yaml
# k8s/data-pipeline/pvc.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pipeline-pvc
  namespace: climatetrade
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 100Gi
  storageClassName: standard
```

## Backtesting Service Deployment

### Backtesting Deployment

```yaml
# k8s/backtesting/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-backtesting
  namespace: climatetrade
spec:
  replicas: 1
  selector:
    matchLabels:
      app: climatetrade-backtesting
  template:
    metadata:
      labels:
        app: climatetrade-backtesting
    spec:
      containers:
        - name: backtesting
          image: climatetrade/backtesting:latest
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
          volumeMounts:
            - name: results-storage
              mountPath: /app/results
            - name: logs
              mountPath: /app/logs
          resources:
            requests:
              memory: '2Gi'
              cpu: '1000m'
            limits:
              memory: '4Gi'
              cpu: '2000m'
          livenessProbe:
            exec:
              command:
                - python
                - -c
                - "from backtesting_framework.core.backtesting_engine import BacktestingEngine; print('OK')"
            initialDelaySeconds: 60
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8001
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: results-storage
          persistentVolumeClaim:
            claimName: backtesting-results-pvc
        - name: logs
          emptyDir: {}
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
```

### Backtesting Service

```yaml
# k8s/backtesting/service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-backtesting
  namespace: climatetrade
spec:
  selector:
    app: climatetrade-backtesting
  ports:
    - port: 80
      targetPort: 8001
      name: http
  type: ClusterIP
```

### Backtesting PVC

```yaml
# k8s/backtesting/pvc.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backtesting-results-pvc
  namespace: climatetrade
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 200Gi
  storageClassName: fast-ssd
```

## Agents Service Deployment

### Agents Deployment

```yaml
# k8s/agents/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-agents
  namespace: climatetrade
spec:
  replicas: 1
  selector:
    matchLabels:
      app: climatetrade-agents
  template:
    metadata:
      labels:
        app: climatetrade-agents
    spec:
      containers:
        - name: agents
          image: climatetrade/agents:latest
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
            - name: POLYGON_WALLET_PRIVATE_KEY
              valueFrom:
                secretKeyRef:
                  name: climatetrade-api-secret
                  key: polygon-wallet-private-key
            - name: OPENAI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: climatetrade-api-secret
                  key: openai-api-key
            - name: POLYMARKET_API_KEY
              valueFrom:
                secretKeyRef:
                  name: climatetrade-api-secret
                  key: polymarket-api-key
            - name: POLYMARKET_SECRET
              valueFrom:
                secretKeyRef:
                  name: climatetrade-api-secret
                  key: polymarket-secret
          volumeMounts:
            - name: logs
              mountPath: /app/logs
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
                - python
                - -c
                - "from agents.application.trade import TradingAgent; print('OK')"
            initialDelaySeconds: 60
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: 8002
            initialDelaySeconds: 30
            periodSeconds: 10
      volumes:
        - name: logs
          emptyDir: {}
      securityContext:
        runAsUser: 1001
        runAsGroup: 1001
```

### Agents Service

```yaml
# k8s/agents/service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-agents
  namespace: climatetrade
spec:
  selector:
    app: climatetrade-agents
  ports:
    - port: 80
      targetPort: 8002
      name: http
  type: ClusterIP
```

## Web Interface Deployment

### Web Deployment

```yaml
# k8s/web/deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: climatetrade-web
  namespace: climatetrade
spec:
  replicas: 2
  selector:
    matchLabels:
      app: climatetrade-web
  template:
    metadata:
      labels:
        app: climatetrade-web
    spec:
      containers:
        - name: web
          image: climatetrade/web:latest
          ports:
            - containerPort: 80
              name: http
          env:
            - name: API_URL
              value: 'http://climatetrade-api'
          resources:
            requests:
              memory: '128Mi'
              cpu: '100m'
            limits:
              memory: '256Mi'
              cpu: '200m'
          livenessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 30
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 80
            initialDelaySeconds: 5
            periodSeconds: 5
      securityContext:
        runAsUser: 101
        runAsGroup: 101
```

### Web Service

```yaml
# k8s/web/service.yml
apiVersion: v1
kind: Service
metadata:
  name: climatetrade-web
  namespace: climatetrade
spec:
  selector:
    app: climatetrade-web
  ports:
    - port: 80
      targetPort: 80
      name: http
  type: ClusterIP
```

## Ingress Configuration

### NGINX Ingress

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

### Certificate Issuer

```yaml
# k8s/ingress/cert-issuer.yml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@climatetrade.ai
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
      - http01:
          ingress:
            class: nginx
```

## Monitoring and Logging

### Prometheus ServiceMonitor

```yaml
# k8s/monitoring/prometheus-servicemonitor.yml
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: climatetrade-servicemonitor
  namespace: climatetrade
  labels:
    team: backend
spec:
  selector:
    matchLabels:
      app: climatetrade-api
  endpoints:
    - port: http
      path: /metrics
      interval: 30s
      scrapeTimeout: 10s
```

### Fluent Bit ConfigMap

```yaml
# k8s/logging/fluent-bit-config.yml
apiVersion: v1
kind: ConfigMap
metadata:
  name: fluent-bit-config
  namespace: climatetrade
data:
  fluent-bit.conf: |
    [SERVICE]
        Flush         5
        Log_Level     info
        Daemon        off

    [INPUT]
        Name              tail
        Path              /var/log/containers/*climatetrade*.log
        Parser            docker
        Tag               climatetrade.*
        Refresh_Interval  5

    [OUTPUT]
        Name  elasticsearch
        Match climatetrade.*
        Host  elasticsearch.climatetrade.svc.cluster.local
        Port  9200
        Index climatetrade
        Type  climatetrade_logs
```

### Fluent Bit DaemonSet

```yaml
# k8s/logging/fluent-bit-ds.yml
apiVersion: apps/v1
kind: DaemonSet
metadata:
  name: fluent-bit
  namespace: climatetrade
spec:
  selector:
    matchLabels:
      app: fluent-bit
  template:
    metadata:
      labels:
        app: fluent-bit
    spec:
      containers:
        - name: fluent-bit
          image: fluent/fluent-bit:1.9
          volumeMounts:
            - name: config
              mountPath: /fluent-bit/etc/
            - name: logs
              mountPath: /var/log/containers
              readOnly: true
          resources:
            requests:
              memory: '64Mi'
              cpu: '50m'
            limits:
              memory: '128Mi'
              cpu: '100m'
      volumes:
        - name: config
          configMap:
            name: fluent-bit-config
        - name: logs
          hostPath:
            path: /var/log/containers
```

## Horizontal Pod Autoscaling

### API HPA

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

### Backtesting HPA

```yaml
# k8s/hpa/backtesting-hpa.yml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: climatetrade-backtesting-hpa
  namespace: climatetrade
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: climatetrade-backtesting
  minReplicas: 1
  maxReplicas: 5
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 70
```

## Backup and Recovery

### Database Backup CronJob

```yaml
# k8s/backup/db-backup-cronjob.yml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: climatetrade-db-backup
  namespace: climatetrade
spec:
  schedule: '0 2 * * *' # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: backup
              image: postgres:13-alpine
              command:
                - /bin/sh
                - -c
                - |
                  pg_dump -h climatetrade-postgresql -U climatetrade climatetrade_prod > /backup/backup_$(date +%Y%m%d_%H%M%S).sql
              env:
                - name: PGPASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: climatetrade-db-secret
                      key: password
              volumeMounts:
                - name: backup-storage
                  mountPath: /backup
          volumes:
            - name: backup-storage
              persistentVolumeClaim:
                claimName: backup-pvc
          restartPolicy: OnFailure
```

### Backup PVC

```yaml
# k8s/backup/backup-pvc.yml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: backup-pvc
  namespace: climatetrade
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 500Gi
  storageClassName: standard
```

## Security Policies

### Network Policies

```yaml
# k8s/security/network-policy.yml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: climatetrade-network-policy
  namespace: climatetrade
spec:
  podSelector:
    matchLabels:
      app: climatetrade-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              app: climatetrade-web
      ports:
        - protocol: TCP
          port: 8000
    - from:
        - namespaceSelector:
            matchLabels:
              name: ingress-nginx
      ports:
        - protocol: TCP
          port: 8000
  egress:
    - to:
        - podSelector:
            matchLabels:
              app: climatetrade-postgresql
      ports:
        - protocol: TCP
          port: 5432
    - to:
        - podSelector:
            matchLabels:
              app: climatetrade-redis
      ports:
        - protocol: TCP
          port: 6379
    - to: []
      ports:
        - protocol: TCP
          port: 443
        - protocol: TCP
          port: 80
```

### Pod Security Standards

```yaml
# k8s/security/pod-security-policy.yml
apiVersion: policy/v1beta1
kind: PodSecurityPolicy
metadata:
  name: climatetrade-psp
spec:
  privileged: false
  allowPrivilegeEscalation: false
  requiredDropCapabilities:
    - ALL
  allowedCapabilities:
    - NET_BIND_SERVICE
  runAsUser:
    rule: MustRunAsNonRoot
  seLinux:
    rule: RunAsAny
  supplementalGroups:
    rule: MustRunAs
    ranges:
      - min: 1
        max: 65535
  fsGroup:
    rule: MustRunAs
    ranges:
      - min: 1
        max: 65535
  readOnlyRootFilesystem: true
  volumes:
    - 'configMap'
    - 'emptyDir'
    - 'persistentVolumeClaim'
    - 'secret'
```

### RBAC Configuration

```yaml
# k8s/security/rbac.yml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: climatetrade-pod-reader
  namespace: climatetrade
rules:
  - apiGroups: ['']
    resources: ['pods', 'pods/log']
    verbs: ['get', 'list', 'watch']

---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: climatetrade-pod-reader-binding
  namespace: climatetrade
subjects:
  - kind: ServiceAccount
    name: climatetrade-service-account
    namespace: climatetrade
roleRef:
  kind: Role
  name: climatetrade-pod-reader
  apiGroup: rbac.authorization.k8s.io

---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: climatetrade-service-account
  namespace: climatetrade
```

## Deployment Instructions

### Deploy All Components

```bash
# Create namespace
kubectl apply -f k8s/namespace.yml

# Deploy secrets and configmaps
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/configmaps/

# Deploy database
kubectl apply -f k8s/database/

# Deploy cache
kubectl apply -f k8s/cache/

# Deploy application services
kubectl apply -f k8s/api/
kubectl apply -f k8s/data-pipeline/
kubectl apply -f k8s/backtesting/
kubectl apply -f k8s/agents/
kubectl apply -f k8s/web/

# Deploy ingress
kubectl apply -f k8s/ingress/

# Deploy monitoring and security
kubectl apply -f k8s/monitoring/
kubectl apply -f k8s/security/
kubectl apply -f k8s/hpa/
kubectl apply -f k8s/backup/
```

### Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n climatetrade

# Check services
kubectl get services -n climatetrade

# Check ingress
kubectl get ingress -n climatetrade

# Check HPA
kubectl get hpa -n climatetrade

# Test application
curl https://api.climatetrade.ai/health
curl https://app.climatetrade.ai/
```

### Troubleshooting

```bash
# Check pod logs
kubectl logs -n climatetrade deployment/climatetrade-api

# Check pod events
kubectl describe pod -n climatetrade <pod-name>

# Check resource usage
kubectl top pods -n climatetrade

# Check network policies
kubectl describe networkpolicy -n climatetrade
```

This comprehensive Kubernetes manifest collection provides a production-ready deployment for ClimaTrade AI with high availability, security, monitoring, and scalability features.
