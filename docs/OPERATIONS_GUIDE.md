# ClimaTrade AI Operations Guide

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Deployment Procedures](#deployment-procedures)
4. [Monitoring and Alerting](#monitoring-and-alerting)
5. [Backup and Recovery](#backup-and-recovery)
6. [Security Operations](#security-operations)
7. [Performance Management](#performance-management)
8. [Incident Response](#incident-response)
9. [Compliance and Auditing](#compliance-and-auditing)
10. [Capacity Planning](#capacity-planning)

## Overview

This comprehensive operations guide provides detailed procedures for managing ClimaTrade AI in production environments. It covers deployment, monitoring, maintenance, security, and incident response procedures.

### Target Audience

- **System Administrators**: Infrastructure management and deployment
- **DevOps Engineers**: CI/CD, monitoring, and automation
- **Site Reliability Engineers (SREs)**: Reliability, performance, and incident response
- **Security Officers**: Security operations and compliance

### Key Responsibilities

- Ensure system availability and performance
- Monitor system health and respond to alerts
- Perform regular maintenance and updates
- Manage backups and disaster recovery
- Maintain security posture
- Coordinate incident response

## System Architecture

### Production Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (nginx)                     │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                 API Gateway (traefik)                   │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │               Application Layer                     │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │  │
│  │  │  │    API      │  │ Data Pipeline│  │ Backtesting │  │  │  │
│  │  │  │  Service    │  │             │  │             │  │  │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │  │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │  │
│  │  │  │   Agents    │  │   Web UI    │  │  Monitoring │  │  │  │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘  │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └─────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │    Data Layer       │
                    │  ┌─────────────┐    │
                    │  │ PostgreSQL  │    │
                    │  │  Cluster     │    │
                    │  └─────────────┘    │
                    │  ┌─────────────┐    │
                    │  │   Redis     │    │
                    │  │   Cluster   │    │
                    │  └─────────────┘    │
                    └─────────────────────┘
```

### Component Specifications

#### API Service

- **Technology**: Python FastAPI
- **CPU**: 2 cores minimum, 4 cores recommended
- **Memory**: 2GB minimum, 4GB recommended
- **Storage**: 10GB for logs and temporary files
- **Scaling**: Horizontal pod autoscaling based on CPU/memory

#### Data Pipeline

- **Technology**: Python with async processing
- **CPU**: 4 cores minimum, 8 cores recommended
- **Memory**: 4GB minimum, 8GB recommended
- **Storage**: 100GB for data processing
- **Scaling**: Based on queue depth and processing load

#### Backtesting Service

- **Technology**: Python with parallel processing
- **CPU**: 8 cores minimum, 16 cores recommended
- **Memory**: 8GB minimum, 16GB recommended
- **Storage**: 500GB for results and models
- **Scaling**: Based on job queue and computational load

#### Database (PostgreSQL)

- **CPU**: 4 cores minimum, 8 cores recommended
- **Memory**: 8GB minimum, 16GB recommended
- **Storage**: 500GB minimum, 1TB recommended
- **High Availability**: Multi-AZ deployment with read replicas

#### Redis Cache

- **Memory**: 4GB minimum, 8GB recommended
- **Persistence**: AOF and RDB enabled
- **Clustering**: 3-node cluster for high availability

## Deployment Procedures

### Pre-Deployment Checklist

#### Infrastructure Preparation

```bash
#!/bin/bash
# pre-deployment-check.sh

echo "🔍 Pre-deployment infrastructure check"

# Check Kubernetes cluster
echo "Checking Kubernetes cluster..."
kubectl cluster-info
kubectl get nodes
kubectl get storageclass

# Verify required tools
echo "Checking required tools..."
which kubectl
which helm
which docker

# Check cloud resources
echo "Checking cloud resources..."
aws ec2 describe-instances --filters "Name=tag:Environment,Values=production"
aws rds describe-db-instances --db-instance-identifier climatetrade-prod
aws elasticache describe-cache-clusters --cache-cluster-id climatetrade-redis

# Verify SSL certificates
echo "Checking SSL certificates..."
openssl x509 -in /etc/ssl/certs/climatetrade.crt -text -noout | grep "Not After"

# Check DNS configuration
echo "Checking DNS configuration..."
nslookup api.climatetrade.ai
nslookup app.climatetrade.ai

echo "✅ Pre-deployment checks completed"
```

#### Application Preparation

```bash
#!/bin/bash
# pre-deployment-app-check.sh

echo "🔍 Pre-deployment application check"

# Verify application build
echo "Checking application build..."
docker build -t climatetrade/api:latest -f docker/api/Dockerfile .
docker build -t climatetrade/data-pipeline:latest -f docker/data-pipeline/Dockerfile .
docker build -t climatetrade/backtesting:latest -f docker/backtesting/Dockerfile .

# Run security scan
echo "Running security scan..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    clair-scanner --ip $(hostname -i) climatetrade/api:latest

# Check configuration files
echo "Validating configuration files..."
python -c "
from config.validator import ConfigurationValidator
validator = ConfigurationValidator('production')
success = validator.run_all_validations()
exit(0 if success else 1)
"

# Run smoke tests
echo "Running smoke tests..."
python -m pytest tests/smoke/ -v

echo "✅ Application pre-deployment checks completed"
```

### Production Deployment

#### Blue-Green Deployment Strategy

```bash
#!/bin/bash
# blue-green-deploy.sh

ENVIRONMENT=${1:-production}
NEW_VERSION=${2:-latest}

echo "🚀 Starting blue-green deployment to $ENVIRONMENT"

# Determine current active environment
CURRENT_ACTIVE=$(kubectl get ingress climatetrade-ingress -o jsonpath='{.spec.rules[0].http.paths[0].backend.service.name}' | cut -d'-' -f2)

if [ "$CURRENT_ACTIVE" = "blue" ]; then
    NEW_ACTIVE="green"
    OLD_ACTIVE="blue"
else
    NEW_ACTIVE="blue"
    OLD_ACTIVE="green"
fi

echo "Current active: $CURRENT_ACTIVE"
echo "New active: $NEW_ACTIVE"

# Deploy to new environment
echo "Deploying to $NEW_ACTIVE environment..."
kubectl set image deployment/climatetrade-api-$NEW_ACTIVE api=climatetrade/api:$NEW_VERSION
kubectl set image deployment/climatetrade-data-pipeline-$NEW_ACTIVE data-pipeline=climatetrade/data-pipeline:$NEW_VERSION
kubectl set image deployment/climatetrade-backtesting-$NEW_ACTIVE backtesting=climatetrade/backtesting:$NEW_VERSION

# Wait for deployment to be ready
echo "Waiting for $NEW_ACTIVE deployment to be ready..."
kubectl wait --for=condition=available --timeout=600s deployment/climatetrade-api-$NEW_ACTIVE
kubectl wait --for=condition=available --timeout=600s deployment/climatetrade-data-pipeline-$NEW_ACTIVE
kubectl wait --for=condition=available --timeout=600s deployment/climatetrade-backtesting-$NEW_ACTIVE

# Run health checks on new environment
echo "Running health checks on $NEW_ACTIVE..."
curl -f https://$NEW_ACTIVE-api.climatetrade.ai/health || exit 1

# Switch traffic to new environment
echo "Switching traffic to $NEW_ACTIVE..."
kubectl patch ingress climatetrade-ingress --type='json' \
    -p="[{'op': 'replace', 'path': '/spec/rules/0/http/paths/0/backend/service/name', 'value': 'climatetrade-api-$NEW_ACTIVE'}]"

# Wait for traffic switch
sleep 30

# Verify new environment is handling traffic
echo "Verifying traffic switch..."
NEW_REQUESTS=$(curl -s https://api.climatetrade.ai/metrics | grep "http_requests_total" | awk '{print $2}')
sleep 60
NEW_REQUESTS_AFTER=$(curl -s https://api.climatetrade.ai/metrics | grep "http_requests_total" | awk '{print $2}')

if [ "$NEW_REQUESTS_AFTER" -gt "$NEW_REQUESTS" ]; then
    echo "✅ Traffic successfully switched to $NEW_ACTIVE"

    # Scale down old environment
    echo "Scaling down $OLD_ACTIVE environment..."
    kubectl scale deployment climatetrade-api-$OLD_ACTIVE --replicas=0
    kubectl scale deployment climatetrade-data-pipeline-$OLD_ACTIVE --replicas=0
    kubectl scale deployment climatetrade-backtesting-$OLD_ACTIVE --replicas=0

    echo "✅ Blue-green deployment completed successfully"
else
    echo "❌ Traffic switch verification failed, rolling back..."

    # Rollback traffic
    kubectl patch ingress climatetrade-ingress --type='json' \
        -p="[{'op': 'replace', 'path': '/spec/rules/0/http/paths/0/backend/service/name', 'value': 'climatetrade-api-$OLD_ACTIVE'}]"

    exit 1
fi
```

#### Rolling Deployment Strategy

```bash
#!/bin/bash
# rolling-deploy.sh

SERVICE_NAME=$1
NEW_IMAGE=$2
NAMESPACE=${3:-climatetrade}

echo "🔄 Starting rolling deployment for $SERVICE_NAME"

# Get current deployment info
CURRENT_REPLICAS=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.replicas}')
CURRENT_IMAGE=$(kubectl get deployment $SERVICE_NAME -n $NAMESPACE -o jsonpath='{.spec.template.spec.containers[0].image}')

echo "Current replicas: $CURRENT_REPLICAS"
echo "Current image: $CURRENT_IMAGE"
echo "New image: $NEW_IMAGE"

# Update deployment image
kubectl set image deployment/$SERVICE_NAME -n $NAMESPACE app=$NEW_IMAGE

# Monitor rollout status
echo "Monitoring rollout progress..."
kubectl rollout status deployment/$SERVICE_NAME -n $NAMESPACE --timeout=600s

# Check rollout success
if [ $? -eq 0 ]; then
    echo "✅ Rolling deployment successful"

    # Verify service health
    echo "Verifying service health..."
    kubectl exec -n $NAMESPACE deployment/$SERVICE_NAME -- curl -f http://localhost/health || echo "⚠️ Health check failed"

    # Check metrics
    echo "Checking performance metrics..."
    PREVIOUS_CPU=$(kubectl top pods -n $NAMESPACE -l app=$SERVICE_NAME --no-headers | awk '{sum+=$2} END {print sum/NR}')
    PREVIOUS_MEMORY=$(kubectl top pods -n $NAMESPACE -l app=$SERVICE_NAME --no-headers | awk '{sum+=$3} END {print sum/NR}')

    echo "Average CPU usage: $PREVIOUS_CPU"
    echo "Average memory usage: $PREVIOUS_MEMORY"

else
    echo "❌ Rolling deployment failed"

    # Rollback deployment
    echo "Rolling back to previous image..."
    kubectl rollout undo deployment/$SERVICE_NAME -n $NAMESPACE

    exit 1
fi
```

### Post-Deployment Verification

```bash
#!/bin/bash
# post-deployment-verify.sh

echo "🔍 Post-deployment verification"

# Check all pods are running
echo "Checking pod status..."
kubectl get pods -n climatetrade

# Verify service endpoints
echo "Checking service endpoints..."
SERVICES=("climatetrade-api" "climatetrade-data-pipeline" "climatetrade-backtesting" "climatetrade-agents")
for service in "${SERVICES[@]}"; do
    kubectl get endpoints $service -n climatetrade
done

# Test API endpoints
echo "Testing API endpoints..."
curl -f https://api.climatetrade.ai/health
curl -f https://api.climatetrade.ai/v1/weather/London

# Check database connectivity
echo "Checking database connectivity..."
kubectl exec -n climatetrade deployment/climatetrade-api -- python -c "
import psycopg2
conn = psycopg2.connect(os.getenv('DATABASE_URL'))
conn.close()
print('Database connection successful')
"

# Verify monitoring
echo "Checking monitoring setup..."
curl -f https://monitoring.climatetrade.ai/-/healthy

# Check logs
echo "Checking application logs..."
kubectl logs -n climatetrade --tail=50 deployment/climatetrade-api

echo "✅ Post-deployment verification completed"
```

## Monitoring and Alerting

### Monitoring Stack Setup

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - 'alert_rules.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets:
            - alertmanager:9093

scrape_configs:
  - job_name: 'climatetrade-api'
    static_configs:
      - targets: ['climatetrade-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s

  - job_name: 'climatetrade-data-pipeline'
    static_configs:
      - targets: ['climatetrade-data-pipeline:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'climatetrade-backtesting'
    static_configs:
      - targets: ['climatetrade-backtesting:8000']
    metrics_path: '/metrics'
    scrape_interval: 60s

  - job_name: 'kubernetes-pods'
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_path]
        action: replace
        target_label: __metrics_path__
        regex: (.+)
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_port]
        action: replace
        target_label: __address__
        regex: ([^:]+)(?::\d+)?;(\d+)
        replacement: $1:$2
```

#### Alert Rules

```yaml
# alert_rules.yml
groups:
  - name: climatetrade
    rules:
      # Service availability alerts
      - alert: ServiceDown
        expr: up == 0
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: 'Service {{ $labels.job }} is down'
          description: 'Service {{ $labels.job }} has been down for more than 5 minutes'

      # Performance alerts
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: 'High CPU usage on {{ $labels.instance }}'
          description: 'CPU usage is above 80% for 10 minutes'

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'High memory usage on {{ $labels.instance }}'
          description: 'Memory usage is above 90%'

      # Application-specific alerts
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: 'High error rate detected'
          description: 'Error rate is {{ $value }}% which is above 5%'

      - alert: DatabaseConnectionPoolExhausted
        expr: db_connections_active > 50
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: 'Database connection pool nearly exhausted'
          description: 'Active connections: {{ $value }}'

      # Business logic alerts
      - alert: TradingAgentUnhealthy
        expr: trading_agent_health_status == 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: 'Trading agent is unhealthy'
          description: 'Trading agent has been unhealthy for 5 minutes'

      - alert: DataPipelineLag
        expr: data_pipeline_queue_size > 1000
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: 'Data pipeline has high queue backlog'
          description: 'Queue size: {{ $value }} messages'
```

### Alert Response Procedures

#### Critical Alert Response

```bash
#!/bin/bash
# critical-alert-response.sh

ALERT_NAME=$1
INSTANCE=$2

echo "🚨 CRITICAL ALERT: $ALERT_NAME on $INSTANCE"

# Log alert details
echo "$(date): CRITICAL ALERT - $ALERT_NAME - $INSTANCE" >> /var/log/alerts.log

# Immediate actions based on alert type
case $ALERT_NAME in
    "ServiceDown")
        echo "Service down detected, attempting restart..."
        kubectl rollout restart deployment/$INSTANCE
        ;;

    "DatabaseConnectionPoolExhausted")
        echo "Database connection pool exhausted, scaling up..."
        kubectl scale deployment climatetrade-api --replicas=5
        ;;

    "HighErrorRate")
        echo "High error rate detected, investigating..."
        kubectl logs --tail=100 deployment/$INSTANCE
        ;;

    *)
        echo "Unknown critical alert: $ALERT_NAME"
        ;;
esac

# Notify on-call engineer
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"🚨 CRITICAL ALERT: $ALERT_NAME on $INSTANCE\"}" \
    $SLACK_CRITICAL_WEBHOOK

# Escalate if not resolved in 5 minutes
sleep 300
if kubectl get pods -l app=$INSTANCE | grep -q "Running"; then
    echo "✅ Alert resolved automatically"
else
    echo "❌ Alert not resolved, manual intervention required"
    # Trigger pager duty or similar
fi
```

#### Warning Alert Response

```bash
#!/bin/bash
# warning-alert-response.sh

ALERT_NAME=$1
INSTANCE=$2

echo "⚠️ WARNING ALERT: $ALERT_NAME on $INSTANCE"

# Log warning
echo "$(date): WARNING ALERT - $ALERT_NAME - $INSTANCE" >> /var/log/alerts.log

# Automated responses for warnings
case $ALERT_NAME in
    "HighCPUUsage")
        echo "High CPU usage, checking for scaling needs..."
        CURRENT_CPU=$(kubectl top pods -l app=$INSTANCE --no-headers | awk '{sum+=$2} END {print sum/NR}')
        if (( $(echo "$CURRENT_CPU > 80" | bc -l) )); then
            kubectl scale deployment $INSTANCE --replicas=+1
        fi
        ;;

    "HighMemoryUsage")
        echo "High memory usage, checking for memory leaks..."
        kubectl exec deployment/$INSTANCE -- python -c "
        import tracemalloc
        tracemalloc.start()
        # Add memory profiling logic
        "
        ;;

    "DataPipelineLag")
        echo "Data pipeline lag detected, scaling up..."
        kubectl scale deployment climatetrade-data-pipeline --replicas=+2
        ;;
esac

# Send notification
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"⚠️ WARNING: $ALERT_NAME on $INSTANCE\"}" \
    $SLACK_WARNING_WEBHOOK
```

### Monitoring Dashboards

#### Grafana Dashboard Setup

```json
// grafana-dashboard.json
{
  "dashboard": {
    "title": "ClimaTrade AI Production Monitoring",
    "tags": ["climatetrade", "production"],
    "timezone": "UTC",
    "refresh": "30s",
    "panels": [
      {
        "title": "System Overview",
        "type": "row"
      },
      {
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error rate (%)"
          }
        ]
      },
      {
        "title": "Database Performance",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(pg_stat_database_xact_commit[5m])",
            "legendFormat": "Transactions/sec"
          },
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active connections"
          }
        ]
      },
      {
        "title": "Resource Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(container_cpu_usage_seconds_total[5m]) * 100",
            "legendFormat": "CPU %"
          },
          {
            "expr": "container_memory_usage_bytes / 1024 / 1024",
            "legendFormat": "Memory (MB)"
          }
        ]
      },
      {
        "title": "Trading Metrics",
        "type": "graph",
        "targets": [
          {
            "expr": "trading_agent_active_positions",
            "legendFormat": "Active positions"
          },
          {
            "expr": "rate(trading_agent_trades_total[5m])",
            "legendFormat": "Trades/min"
          }
        ]
      }
    ]
  }
}
```

## Backup and Recovery

### Automated Backup Strategy

#### Database Backup

```bash
#!/bin/bash
# automated-db-backup.sh

BACKUP_DIR="/backups/database/$(date +%Y%m%d)"
TIMESTAMP=$(date +%H%M%S)
BACKUP_NAME="climatetrade_backup_${TIMESTAMP}"

# Create backup directory
mkdir -p $BACKUP_DIR

# Full database backup
echo "Creating full database backup..."
pg_dump -h $DB_HOST -U $DB_USER -d $DB_NAME \
    --no-password \
    --format=directory \
    --compress=9 \
    --jobs=4 \
    --file=$BACKUP_DIR/$BACKUP_NAME

# Verify backup
echo "Verifying backup..."
pg_restore --list $BACKUP_DIR/$BACKUP_NAME > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backup verification successful"
else
    echo "❌ Backup verification failed"
    exit 1
fi

# Compress backup
echo "Compressing backup..."
tar -czf $BACKUP_DIR/${BACKUP_NAME}.tar.gz -C $BACKUP_DIR $BACKUP_NAME

# Upload to cloud storage
echo "Uploading to cloud storage..."
aws s3 cp $BACKUP_DIR/${BACKUP_NAME}.tar.gz \
    s3://climatetrade-backups/database/ \
    --storage-class STANDARD_IA \
    --sse AES256

# Clean up local backup
rm -rf $BACKUP_DIR

# Send notification
curl -X POST -H 'Content-type: application/json' \
    --data "{\"text\":\"✅ Database backup completed: $BACKUP_NAME\"}" \
    $SLACK_BACKUP_WEBHOOK

echo "✅ Automated database backup completed"
```

#### Configuration Backup

```bash
#!/bin/bash
# config-backup.sh

BACKUP_DIR="/backups/config/$(date +%Y%m%d)"
TIMESTAMP=$(date +%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup Kubernetes configurations
echo "Backing up Kubernetes configurations..."
kubectl get all -n climatetrade -o yaml > $BACKUP_DIR/kubernetes-all.yml
kubectl get secrets -n climatetrade -o yaml > $BACKUP_DIR/secrets.yml
kubectl get configmaps -n climatetrade -o yaml > $BACKUP_DIR/configmaps.yml

# Backup application configurations
echo "Backing up application configurations..."
cp -r /app/config $BACKUP_DIR/
cp /app/docker-compose*.yml $BACKUP_DIR/
cp /app/.env* $BACKUP_DIR/

# Backup SSL certificates
echo "Backing up SSL certificates..."
cp /etc/ssl/certs/climatetrade* $BACKUP_DIR/

# Create encrypted archive
echo "Creating encrypted backup archive..."
tar -czf - $BACKUP_DIR | openssl enc -aes-256-cbc -salt -out $BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz.enc -k $BACKUP_ENCRYPTION_KEY

# Upload to secure storage
echo "Uploading to secure storage..."
aws s3 cp $BACKUP_DIR/config_backup_${TIMESTAMP}.tar.gz.enc \
    s3://climatetrade-backups/config/ \
    --sse AES256

# Clean up
rm -rf $BACKUP_DIR

echo "✅ Configuration backup completed"
```

### Disaster Recovery

#### Recovery Time Objective (RTO) and Recovery Point Objective (RPO)

- **RTO**: 4 hours for critical systems, 24 hours for non-critical
- **RPO**: 1 hour for database, 24 hours for configurations

#### Disaster Recovery Plan

```bash
#!/bin/bash
# disaster-recovery.sh

echo "🚨 INITIATING DISASTER RECOVERY PROCEDURE"

# Phase 1: Assessment
echo "Phase 1: Assessing damage..."
kubectl get nodes
kubectl get pods -A
aws rds describe-db-instances --db-instance-identifier climatetrade-prod

# Phase 2: Data Recovery
echo "Phase 2: Recovering data..."
LATEST_BACKUP=$(aws s3 ls s3://climatetrade-backups/database/ | sort | tail -1 | awk '{print $4}')
aws s3 cp s3://climatetrade-backups/database/$LATEST_BACKUP /tmp/
./restore-database.sh /tmp/$LATEST_BACKUP

# Phase 3: Infrastructure Recovery
echo "Phase 3: Recovering infrastructure..."
kubectl apply -f k8s/infrastructure/
kubectl apply -f k8s/secrets/
kubectl apply -f k8s/configmaps/

# Phase 4: Application Recovery
echo "Phase 4: Recovering applications..."
kubectl apply -f k8s/database/
kubectl apply -f k8s/cache/
kubectl apply -f k8s/api/
kubectl apply -f k8s/data-pipeline/
kubectl apply -f k8s/backtesting/
kubectl apply -f k8s/agents/
kubectl apply -f k8s/web/

# Phase 5: Verification
echo "Phase 5: Verifying recovery..."
./post-deployment-verify.sh

# Phase 6: Service Restoration
echo "Phase 6: Restoring services..."
kubectl apply -f k8s/ingress/
kubectl apply -f k8s/monitoring/

echo "✅ Disaster recovery completed"
```

## Security Operations

### Security Monitoring

#### Log Analysis

```bash
#!/bin/bash
# security-log-analysis.sh

echo "🔒 Analyzing security logs"

# Check for suspicious activities
echo "Checking for failed authentication attempts..."
grep "authentication failed" /var/log/climatetrade/auth.log | tail -20

# Check for unusual access patterns
echo "Checking for unusual access patterns..."
awk '{print $1}' /var/log/climatetrade/access.log | sort | uniq -c | sort -nr | head -10

# Check for potential security breaches
echo "Checking for potential security breaches..."
grep -i "sql injection\|xss\|csrf" /var/log/climatetrade/security.log

# Monitor privileged access
echo "Monitoring privileged access..."
grep "sudo\|su\|root" /var/log/climatetrade/auth.log

# Check for anomalous network traffic
echo "Checking for anomalous network traffic..."
netstat -tuln | grep LISTEN

echo "✅ Security log analysis completed"
```

#### Vulnerability Scanning

```bash
#!/bin/bash
# vulnerability-scan.sh

echo "🔍 Running vulnerability scan"

# Scan Docker images
echo "Scanning Docker images..."
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
    clair-scanner --ip $(hostname -i) climatetrade/api:latest

# Scan running containers
echo "Scanning running containers..."
docker ps --format "table {{.Names}}\t{{.Image}}" | tail -n +2 | \
while read name image; do
    echo "Scanning $name ($image)..."
    docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
        clair-scanner --ip $(hostname -i) $image
done

# Scan dependencies
echo "Scanning Python dependencies..."
safety check --full-report

# Scan infrastructure
echo "Scanning infrastructure..."
kube-hunter

echo "✅ Vulnerability scan completed"
```

### Access Control

#### User Access Management

```bash
#!/bin/bash
# access-review.sh

echo "👥 Reviewing user access"

# Check active sessions
echo "Active user sessions:"
who

# Check sudo access
echo "Users with sudo access:"
getent group sudo | cut -d: -f4 | tr ',' '\n'

# Check SSH access
echo "SSH authorized keys:"
find /home -name "authorized_keys" -exec wc -l {} \; 2>/dev/null

# Check database users
echo "Database users:"
psql -c "SELECT usename FROM pg_user;"

# Check Kubernetes RBAC
echo "Kubernetes RBAC:"
kubectl get clusterrolebindings
kubectl get rolebindings -n climatetrade

echo "✅ Access review completed"
```

### Incident Response

#### Security Incident Response Plan

```bash
#!/bin/bash
# security-incident-response.sh

echo "🚨 SECURITY INCIDENT DETECTED"

# 1. Isolate affected systems
echo "Step 1: Isolating affected systems..."
kubectl cordon $(kubectl get nodes -o name | grep affected-node)

# 2. Preserve evidence
echo "Step 2: Preserving evidence..."
kubectl logs --all-containers=true --timestamps > incident_logs_$(date +%Y%m%d_%H%M%S).log
tcpdump -i any -w incident_traffic_$(date +%Y%m%d_%H%M%S).pcap &

# 3. Assess the breach
echo "Step 3: Assessing the breach..."
# Check for unauthorized access
grep "Failed password" /var/log/auth.log
# Check for modified files
find /app -mtime -1 -type f
# Check network connections
netstat -tuln

# 4. Contain the breach
echo "Step 4: Containing the breach..."
# Block suspicious IPs
iptables -A INPUT -s SUSPICIOUS_IP -j DROP
# Disable compromised accounts
passwd -l compromised_user
# Stop affected services
kubectl scale deployment affected-service --replicas=0

# 5. Eradicate the threat
echo "Step 5: Eradicating the threat..."
# Remove malware
clamscan -r /app --remove
# Update passwords
# Patch vulnerabilities

# 6. Recover systems
echo "Step 6: Recovering systems..."
# Restore from clean backup
./disaster-recovery.sh
# Verify system integrity

# 7. Lessons learned
echo "Step 7: Documenting lessons learned..."
# Update incident response plan
# Implement preventive measures

echo "✅ Security incident response completed"
```

## Performance Management

### Performance Monitoring

#### Application Performance Monitoring

```python
# performance_monitor.py
import time
import psutil
import threading
from prometheus_client import Gauge, Histogram, Counter

# Metrics
CPU_USAGE = Gauge('cpu_usage_percent', 'CPU usage percentage')
MEMORY_USAGE = Gauge('memory_usage_bytes', 'Memory usage in bytes')
DISK_IO = Counter('disk_io_total', 'Disk I/O operations')
NETWORK_IO = Counter('network_io_total', 'Network I/O bytes')

class PerformanceMonitor:
    def __init__(self):
        self.monitoring = False
        self.thread = None

    def start_monitoring(self):
        """Start performance monitoring"""
        self.monitoring = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()

    def stop_monitoring(self):
        """Stop performance monitoring"""
        self.monitoring = False
        if self.thread:
            self.thread.join()

    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            # CPU monitoring
            cpu_percent = psutil.cpu_percent(interval=1)
            CPU_USAGE.set(cpu_percent)

            # Memory monitoring
            memory = psutil.virtual_memory()
            MEMORY_USAGE.set(memory.used)

            # Disk I/O monitoring
            disk_io = psutil.disk_io_counters()
            if disk_io:
                DISK_IO.inc(disk_io.read_count + disk_io.write_count)

            # Network I/O monitoring
            net_io = psutil.net_io_counters()
            if net_io:
                NETWORK_IO.inc(net_io.bytes_sent + net_io.bytes_recv)

            time.sleep(60)  # Monitor every minute

# Usage
monitor = PerformanceMonitor()
monitor.start_monitoring()
```

#### Database Performance Tuning

```sql
-- Performance monitoring queries
CREATE OR REPLACE FUNCTION get_performance_stats()
RETURNS TABLE (
    metric text,
    value numeric,
    description text
) AS $$
BEGIN
    RETURN QUERY
    SELECT
        'active_connections'::text,
        count(*)::numeric,
        'Number of active database connections'::text
    FROM pg_stat_activity
    WHERE state = 'active'

    UNION ALL

    SELECT
        'cache_hit_ratio'::text,
        round(
            sum(blks_hit) * 100.0 / (sum(blks_hit) + sum(blks_read)), 2
        ),
        'Database cache hit ratio percentage'::text
    FROM pg_stat_database

    UNION ALL

    SELECT
        'slow_queries'::text,
        count(*)::numeric,
        'Number of queries running longer than 1 second'::text
    FROM pg_stat_activity
    WHERE state = 'active'
    AND now() - query_start > interval '1 second'

    UNION ALL

    SELECT
        'dead_tuples_ratio'::text,
        round(
            sum(n_dead_tup) * 100.0 / (sum(n_live_tup) + sum(n_dead_tup)), 2
        ),
        'Dead tuples ratio percentage'::text
    FROM pg_stat_user_tables;
END;
$$ LANGUAGE plpgsql;

-- Performance tuning recommendations
CREATE OR REPLACE FUNCTION performance_recommendations()
RETURNS TABLE (
    recommendation text,
    priority text,
    impact text
) AS $$
BEGIN
    RETURN QUERY
    -- Check if autovacuum is enabled
    SELECT
        'Enable autovacuum'::text,
        'HIGH'::text,
        'Improves database performance by automatically cleaning up dead tuples'::text
    WHERE NOT (SELECT setting::boolean FROM pg_settings WHERE name = 'autovacuum');

    -- Check work_mem setting
    SELECT
        'Increase work_mem'::text,
        'MEDIUM'::text,
        'Improves query performance for complex operations'::text
    WHERE (SELECT setting::integer FROM pg_settings WHERE name = 'work_mem') < 4096;

    -- Check shared_buffers
    SELECT
        'Increase shared_buffers'::text,
        'HIGH'::text,
        'Improves overall database performance'::text
    WHERE (SELECT setting::integer FROM pg_settings WHERE name = 'shared_buffers') < 128 * 1024;

    -- Check for missing indexes
    SELECT
        'Create missing indexes'::text,
        'MEDIUM'::text,
        'Improves query performance'::text
    WHERE EXISTS (
        SELECT 1 FROM pg_stat_user_tables
        WHERE n_tup_ins > 1000 AND idx_scan = 0
    );
END;
$$ LANGUAGE plpgsql;
```

### Capacity Planning

#### Resource Usage Forecasting

```python
# capacity_planning.py
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
import matplotlib.pyplot as plt

class CapacityPlanner:
    def __init__(self):
        self.metrics_history = []

    def collect_metrics(self):
        """Collect current system metrics"""
        metrics = {
            'timestamp': pd.Timestamp.now(),
            'cpu_usage': psutil.cpu_percent(),
            'memory_usage': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'network_connections': len(psutil.net_connections())
        }
        self.metrics_history.append(metrics)

    def forecast_capacity(self, days_ahead=30):
        """Forecast future capacity needs"""
        if len(self.metrics_history) < 7:  # Need at least a week of data
            return None

        df = pd.DataFrame(self.metrics_history)
        df['days'] = (df['timestamp'] - df['timestamp'].min()).dt.days

        forecasts = {}

        for metric in ['cpu_usage', 'memory_usage', 'disk_usage']:
            # Simple linear regression for forecasting
            X = df[['days']]
            y = df[metric]

            model = LinearRegression()
            model.fit(X, y)

            # Forecast for future days
            future_days = np.array(range(len(df), len(df) + days_ahead)).reshape(-1, 1)
            forecast = model.predict(future_days)

            forecasts[metric] = {
                'current': y.iloc[-1],
                'predicted': forecast[-1],
                'trend': 'increasing' if forecast[-1] > y.iloc[-1] else 'decreasing',
                'days_to_capacity': self._days_to_threshold(forecast, 90)
            }

        return forecasts

    def _days_to_threshold(self, forecast, threshold):
        """Calculate days until threshold is reached"""
        for i, value in enumerate(forecast):
            if value >= threshold:
                return i
        return None

    def generate_report(self):
        """Generate capacity planning report"""
        forecasts = self.forecast_capacity()

        if not forecasts:
            return "Insufficient data for capacity planning"

        report = "# Capacity Planning Report\n\n"
        report += f"Generated: {pd.Timestamp.now()}\n\n"

        for metric, data in forecasts.items():
            report += f"## {metric.replace('_', ' ').title()}\n"
            report += f"- Current: {data['current']:.1f}%\n"
            report += f"- Predicted (30 days): {data['predicted']:.1f}%\n"
            report += f"- Trend: {data['trend']}\n"

            if data['days_to_capacity']:
                report += f"- Days to 90% capacity: {data['days_to_capacity']}\n"

            report += "\n"

        # Recommendations
        report += "## Recommendations\n\n"

        for metric, data in forecasts.items():
            if data['predicted'] > 80:
                report += f"- **URGENT**: Scale up {metric} resources\n"
            elif data['predicted'] > 70:
                report += f"- **WARNING**: Monitor {metric} closely\n"

        return report

# Usage
planner = CapacityPlanner()

# Collect metrics daily
# This would typically run as a cron job
planner.collect_metrics()

# Generate weekly report
report = planner.generate_report()
print(report)
```

This operations guide provides comprehensive procedures for managing ClimaTrade AI in production, covering deployment, monitoring, security, and maintenance operations.
