# EAT Framework Production Deployment Guide

This guide provides comprehensive instructions for deploying the EAT Framework in production environments, from single-service deployments to enterprise-scale architectures.

## 🎯 Deployment Overview

EAT Framework supports multiple deployment patterns to match your organization's needs:

| Pattern | Use Case | Complexity | Scale |
|---------|----------|------------|-------|
| **Single Service** | Individual team, prototype | Low | 1-10 tools |
| **Multi-Service** | Department, business unit | Medium | 10-100 tools |
| **Enterprise** | Organization-wide | High | 100+ tools |
| **Federated** | Multi-organization | Very High | 1000+ tools |

## 🏗️ Architecture Patterns

### Pattern 1: Single Service Deployment

**Best for**: Individual teams, prototypes, or microservices with focused tool sets.

```yaml
# Architecture Overview
Components:
  - Static catalog hosting (Nginx/Apache)
  - MCP server (containerized)
  - Simple key management
  - Basic monitoring

Infrastructure:
  - Single VM or container cluster
  - CDN for catalog distribution
  - SSL certificate management
  - Log aggregation
```

#### Implementation Steps

**Step 1: Infrastructure Setup**
```bash
# Create directory structure
mkdir -p /opt/eat-framework/{catalogs,specs,keys,logs}

# Install dependencies
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx docker.io

# Configure Nginx
cat > /etc/nginx/sites-available/eat-catalog << 'EOF'
server {
    listen 80;
    server_name api.yourcompany.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.yourcompany.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/api.yourcompany.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.yourcompany.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    
    # Catalog endpoint
    location /.well-known/api-catalog {
        root /opt/eat-framework/catalogs;
        add_header Cache-Control "public, max-age=300";
        add_header Access-Control-Allow-Origin "*";
        try_files /api-catalog =404;
    }
    
    # DID document
    location /.well-known/did.json {
        root /opt/eat-framework/catalogs;
        add_header Cache-Control "public, max-age=3600";
        try_files /did.json =404;
    }
    
    # OpenAPI specs
    location /specs/ {
        root /opt/eat-framework;
        add_header Cache-Control "public, max-age=900";
        try_files $uri =404;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/eat-catalog /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx
```

**Step 2: SSL Certificate Setup**
```bash
# Obtain SSL certificate
certbot --nginx -d api.yourcompany.com

# Configure auto-renewal
echo "0 12 * * * /usr/bin/certbot renew --quiet" | crontab -
```

**Step 3: Key Generation and Management**
```bash
# Generate signing key pair
openssl genrsa -out /opt/eat-framework/keys/signing-key.pem 4096
openssl rsa -in /opt/eat-framework/keys/signing-key.pem -pubout -out /opt/eat-framework/keys/signing-key-pub.pem

# Secure key permissions
chmod 600 /opt/eat-framework/keys/signing-key.pem
chmod 644 /opt/eat-framework/keys/signing-key-pub.pem
chown www-data:www-data /opt/eat-framework/keys/signing-key-pub.pem
```

**Step 4: Create DID Document**
```bash
cat > /opt/eat-framework/catalogs/did.json << 'EOF'
{
  "@context": ["https://www.w3.org/ns/did/v1"],
  "id": "did:web:api.yourcompany.com",
  "verificationMethod": [
    {
      "id": "did:web:api.yourcompany.com#key-1",
      "type": "RsaVerificationKey2018",
      "controller": "did:web:api.yourcompany.com",
      "publicKeyPem": "-----BEGIN PUBLIC KEY-----\nYOUR_PUBLIC_KEY_HERE\n-----END PUBLIC KEY-----"
    }
  ],
  "service": [
    {
      "id": "did:web:api.yourcompany.com#catalog",
      "type": "EATCatalog",
      "serviceEndpoint": "https://api.yourcompany.com/.well-known/api-catalog"
    }
  ]
}
EOF
```

**Step 5: Deploy MCP Server**
```dockerfile
# Dockerfile for MCP server
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY server.py .
COPY config/ config/

EXPOSE 3001

CMD ["python", "server.py"]
```

```bash
# Build and run MCP server
docker build -t your-mcp-server .
docker run -d --name mcp-server -p 3001:3001 your-mcp-server
```

### Pattern 2: Multi-Service Deployment

**Best for**: Departments or business units with multiple services and teams.

```yaml
# Architecture Overview
Components:
  - Load balancer (HAProxy/AWS ALB)
  - Multiple MCP servers
  - Centralized catalog management
  - Distributed key management
  - Comprehensive monitoring

Infrastructure:
  - Multiple VMs or Kubernetes cluster
  - Service mesh (optional)
  - Central logging and monitoring
  - Backup and disaster recovery
```

#### Kubernetes Deployment

**Step 1: Namespace Setup**
```yaml
# namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: eat-framework
  labels:
    name: eat-framework
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: eat-config
  namespace: eat-framework
data:
  catalog-refresh-interval: "300"
  signature-verification: "true"
  log-level: "INFO"
```

**Step 2: Catalog Service**
```yaml
# catalog-service.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-service
  namespace: eat-framework
spec:
  replicas: 3
  selector:
    matchLabels:
      app: catalog-service
  template:
    metadata:
      labels:
        app: catalog-service
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        ports:
        - containerPort: 80
        volumeMounts:
        - name: catalog-data
          mountPath: /usr/share/nginx/html/.well-known
        - name: specs-data
          mountPath: /usr/share/nginx/html/specs
        - name: nginx-config
          mountPath: /etc/nginx/conf.d
      volumes:
      - name: catalog-data
        configMap:
          name: catalog-files
      - name: specs-data
        configMap:
          name: spec-files
      - name: nginx-config
        configMap:
          name: nginx-config
---
apiVersion: v1
kind: Service
metadata:
  name: catalog-service
  namespace: eat-framework
spec:
  selector:
    app: catalog-service
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP
```

**Step 3: MCP Server Deployment**
```yaml
# mcp-servers.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customer-mcp-server
  namespace: eat-framework
spec:
  replicas: 2
  selector:
    matchLabels:
      app: customer-mcp-server
  template:
    metadata:
      labels:
        app: customer-mcp-server
    spec:
      containers:
      - name: mcp-server
        image: your-registry/customer-mcp:latest
        ports:
        - containerPort: 3001
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: database-secrets
              key: customer-db-url
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: customer-mcp-service
  namespace: eat-framework
spec:
  selector:
    app: customer-mcp-server
  ports:
  - port: 3001
    targetPort: 3001
```

**Step 4: Ingress Configuration**
```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: eat-ingress
  namespace: eat-framework
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.yourcompany.com
    secretName: eat-tls
  rules:
  - host: api.yourcompany.com
    http:
      paths:
      - path: /.well-known
        pathType: Prefix
        backend:
          service:
            name: catalog-service
            port:
              number: 80
      - path: /specs
        pathType: Prefix
        backend:
          service:
            name: catalog-service
            port:
              number: 80
      - path: /mcp/customer
        pathType: Prefix
        backend:
          service:
            name: customer-mcp-service
            port:
              number: 3001
```

### Pattern 3: Enterprise Deployment

**Best for**: Large organizations with multiple business units and complex governance requirements.

```yaml
# Architecture Overview
Components:
  - API Gateway (Kong/AWS API Gateway)
  - Service mesh (Istio/Linkerd)
  - Multiple Kubernetes clusters
  - Enterprise key management (HSM)
  - Advanced monitoring and security

Infrastructure:
  - Multi-region deployment
  - Disaster recovery
  - Enterprise integration
  - Compliance and auditing
```

#### Enterprise Architecture

```yaml
# enterprise-deployment.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: eat-framework-enterprise
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/yourorg/eat-framework-enterprise
    targetRevision: HEAD
    path: charts/eat-framework
    helm:
      values: |
        global:
          environment: production
          region: us-west-2
        
        catalog:
          replicas: 5
          resources:
            requests:
              memory: 512Mi
              cpu: 500m
            limits:
              memory: 1Gi
              cpu: 1000m
          
          autoscaling:
            enabled: true
            minReplicas: 3
            maxReplicas: 10
            targetCPUUtilizationPercentage: 70
        
        mcpServers:
          customer:
            replicas: 3
            image: your-registry/customer-mcp:v2.1.0
          analytics:
            replicas: 2
            image: your-registry/analytics-mcp:v1.5.0
          notifications:
            replicas: 2
            image: your-registry/notifications-mcp:v1.2.0
        
        security:
          hsm:
            enabled: true
            provider: aws-cloudhsm
          
          rbac:
            enabled: true
          
          networkPolicies:
            enabled: true
        
        monitoring:
          prometheus:
            enabled: true
          grafana:
            enabled: true
          jaeger:
            enabled: true
        
        backup:
          enabled: true
          schedule: "0 2 * * *"
          retention: "30d"
  
  destination:
    server: https://kubernetes.default.svc
    namespace: eat-framework-production
  
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## 🔐 Security Configurations

### SSL/TLS Configuration

#### Modern SSL Configuration
```nginx
# /etc/nginx/snippets/ssl-eat.conf
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-CHACHA20-POLY1305:ECDHE-RSA-AES128-GCM-SHA256;
ssl_prefer_server_ciphers off;

ssl_session_timeout 1d;
ssl_session_cache shared:SSL:50m;
ssl_stapling on;
ssl_stapling_verify on;

# HSTS
add_header Strict-Transport-Security "max-age=63072000" always;

# OCSP stapling
resolver 8.8.8.8 8.8.4.4 valid=300s;
resolver_timeout 5s;
```

#### Certificate Management
```bash
#!/bin/bash
# certificate-renewal.sh

# Automated certificate renewal with validation
certbot renew --pre-hook "systemctl stop nginx" --post-hook "systemctl start nginx"

# Validate certificate
openssl x509 -in /etc/letsencrypt/live/api.yourcompany.com/fullchain.pem -text -noout | grep "Not After"

# Update monitoring
curl -X POST https://monitoring.yourcompany.com/webhook/cert-renewed \
  -H "Content-Type: application/json" \
  -d '{"service": "eat-framework", "status": "renewed", "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'"}'
```

### Key Management

#### Hardware Security Module (HSM) Integration
```python
# hsm_key_manager.py
import boto3
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

class HSMKeyManager:
    """
    Enterprise key management using AWS CloudHSM
    """
    
    def __init__(self, cluster_id, user_name, password):
        self.cluster_id = cluster_id
        self.session = self.create_hsm_session(user_name, password)
    
    def create_signing_key(self, key_label):
        """
        Generate signing key in HSM
        """
        # Generate key pair in HSM
        key_handle = self.session.generate_keypair(
            mechanism=CKM_RSA_PKCS_KEY_PAIR_GEN,
            public_key_template=[
                (CKA_CLASS, CKO_PUBLIC_KEY),
                (CKA_TOKEN, True),
                (CKA_MODULUS_BITS, 4096),
                (CKA_PUBLIC_EXPONENT, 65537),
                (CKA_LABEL, key_label),
            ],
            private_key_template=[
                (CKA_CLASS, CKO_PRIVATE_KEY),
                (CKA_TOKEN, True),
                (CKA_PRIVATE, True),
                (CKA_SENSITIVE, True),
                (CKA_EXTRACTABLE, False),
                (CKA_LABEL, key_label),
                (CKA_SIGN, True),
            ]
        )
        
        return key_handle
    
    def sign_catalog(self, catalog_json, key_handle):
        """
        Sign catalog using HSM-stored private key
        """
        # Hash catalog content
        catalog_hash = hashlib.sha256(catalog_json.encode()).hexdigest()
        
        # Create JWS payload
        payload = {
            "iss": f"did:web:{self.domain}",
            "iat": int(time.time()),
            "exp": int(time.time()) + 3600,
            "catalog_hash": f"sha256:{catalog_hash}"
        }
        
        # Sign using HSM
        signature = self.session.sign(key_handle, json.dumps(payload).encode())
        
        return self.create_jws_token(payload, signature)
```

## 📊 Monitoring and Observability

### Comprehensive Monitoring Stack

#### Prometheus Configuration
```yaml
# prometheus-config.yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "eat_framework_rules.yml"

scrape_configs:
  - job_name: 'eat-catalog-service'
    static_configs:
      - targets: ['catalog-service:80']
    metrics_path: /metrics
    scrape_interval: 30s
  
  - job_name: 'eat-mcp-servers'
    kubernetes_sd_configs:
      - role: pod
        namespaces:
          names:
            - eat-framework
    relabel_configs:
      - source_labels: [__meta_kubernetes_pod_label_app]
        action: keep
        regex: .*mcp-server
      - source_labels: [__meta_kubernetes_pod_annotation_prometheus_io_scrape]
        action: keep
        regex: true

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

#### Custom Metrics
```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
catalog_requests = Counter('eat_catalog_requests_total', 'Total catalog requests', ['status'])
tool_executions = Counter('eat_tool_executions_total', 'Total tool executions', ['tool_name', 'status'])
signature_verifications = Counter('eat_signature_verifications_total', 'Signature verifications', ['result'])
discovery_latency = Histogram('eat_discovery_duration_seconds', 'Discovery latency')
active_agents = Gauge('eat_active_agents', 'Number of active agents')

class EATMetrics:
    """
    Custom metrics collection for EAT Framework
    """
    
    @staticmethod
    def record_catalog_request(status_code):
        status = 'success' if 200 <= status_code < 300 else 'error'
        catalog_requests.labels(status=status).inc()
    
    @staticmethod
    def record_tool_execution(tool_name, success):
        status = 'success' if success else 'error'
        tool_executions.labels(tool_name=tool_name, status=status).inc()
    
    @staticmethod
    def record_signature_verification(valid):
        result = 'valid' if valid else 'invalid'
        signature_verifications.labels(result=result).inc()
    
    @staticmethod
    def observe_discovery_latency(duration_seconds):
        discovery_latency.observe(duration_seconds)
    
    @staticmethod
    def update_active_agents(count):
        active_agents.set(count)

# Start metrics server
start_http_server(8000)
```

#### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "title": "EAT Framework Overview",
    "panels": [
      {
        "title": "Catalog Requests",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(eat_catalog_requests_total[5m])",
            "legendFormat": "{{status}}"
          }
        ]
      },
      {
        "title": "Tool Execution Success Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "rate(eat_tool_executions_total{status=\"success\"}[5m]) / rate(eat_tool_executions_total[5m]) * 100",
            "legendFormat": "Success Rate %"
          }
        ]
      },
      {
        "title": "Discovery Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(eat_discovery_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(eat_discovery_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      }
    ]
  }
}
```

### Log Management

#### Structured Logging Configuration
```python
# logging_config.py
import json
import logging
from datetime import datetime

class EATJSONFormatter(logging.Formatter):
    """
    Custom JSON formatter for EAT Framework logs
    """
    
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add extra fields
        if hasattr(record, 'agent_id'):
            log_entry['agent_id'] = record.agent_id
        if hasattr(record, 'tool_name'):
            log_entry['tool_name'] = record.tool_name
        if hasattr(record, 'catalog_url'):
            log_entry['catalog_url'] = record.catalog_url
        
        return json.dumps(log_entry)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('/var/log/eat-framework/application.log')
    ]
)

# Add custom formatter
for handler in logging.root.handlers:
    handler.setFormatter(EATJSONFormatter())
```

## 🔄 CI/CD Pipeline

### GitOps Deployment Pipeline

#### GitHub Actions Workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy EAT Framework

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install -r requirements-dev.txt
    
    - name: Run tests
      run: |
        pytest tests/ --cov=eat --cov-report=xml
    
    - name: Security scan
      run: |
        bandit -r eat/
        safety check

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - uses: actions/checkout@v3
    
    - name: Build Docker images
      run: |
        docker build -t eat-catalog:${{ github.sha }} -f docker/Dockerfile.catalog .
        docker build -t eat-mcp-server:${{ github.sha }} -f docker/Dockerfile.mcp .
    
    - name: Push to registry
      run: |
        docker tag eat-catalog:${{ github.sha }} ${{ secrets.DOCKER_REGISTRY }}/eat-catalog:${{ github.sha }}
        docker tag eat-mcp-server:${{ github.sha }} ${{ secrets.DOCKER_REGISTRY }}/eat-mcp-server:${{ github.sha }}
        docker push ${{ secrets.DOCKER_REGISTRY }}/eat-catalog:${{ github.sha }}
        docker push ${{ secrets.DOCKER_REGISTRY }}/eat-mcp-server:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to staging
      run: |
        kubectl set image deployment/catalog-service nginx=${{ secrets.DOCKER_REGISTRY }}/eat-catalog:${{ github.sha }} -n eat-framework-staging
        kubectl rollout status deployment/catalog-service -n eat-framework-staging
    
    - name: Run integration tests
      run: |
        pytest tests/integration/ --env=staging
    
    - name: Deploy to production
      if: success()
      run: |
        kubectl set image deployment/catalog-service nginx=${{ secrets.DOCKER_REGISTRY }}/eat-catalog:${{ github.sha }} -n eat-framework-production
        kubectl rollout status deployment/catalog-service -n eat-framework-production
```

#### Catalog Generation Pipeline
```yaml
# .github/workflows/catalog-update.yml
name: Update Tool Catalog

on:
  push:
    paths:
      - 'specs/**/*.yaml'
      - 'specs/**/*.yml'

jobs:
  update-catalog:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Install EAT CLI
      run: pip install eat-framework
    
    - name: Generate catalog
      run: |
        eat-gen generate specs/ --output catalog.json
    
    - name: Sign catalog
      env:
        SIGNING_KEY: ${{ secrets.CATALOG_SIGNING_KEY }}
      run: |
        echo "$SIGNING_KEY" > signing-key.pem
        eat-gen sign catalog.json --key signing-key.pem --output api-catalog
        rm signing-key.pem
    
    - name: Validate catalog
      run: |
        eat-gen validate api-catalog
    
    - name: Deploy catalog
      run: |
        aws s3 cp api-catalog s3://your-catalog-bucket/.well-known/api-catalog
        aws cloudfront create-invalidation --distribution-id ${{ secrets.CLOUDFRONT_DISTRIBUTION_ID }} --paths "/.well-known/api-catalog"
```

## 🚀 Performance Optimization

### Caching Strategy

#### Multi-Level Caching
```yaml
# caching-config.yaml
caching:
  levels:
    # Level 1: CDN/Edge caching
    cdn:
      provider: cloudflare
      ttl:
        catalog: 300s  # 5 minutes
        specs: 900s    # 15 minutes
        did_document: 3600s  # 1 hour
      
    # Level 2: Application caching
    application:
      provider: redis
      ttl:
        parsed_catalogs: 900s
        verified_signatures: 3600s
        tool_metadata: 1800s
      
    # Level 3: Browser caching
    browser:
      cache_control:
        catalog: "public, max-age=300"
        specs: "public, max-age=900"
        static_assets: "public, max-age=86400"
```

#### Redis Configuration
```yaml
# redis-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: redis-config
data:
  redis.conf: |
    maxmemory 2gb
    maxmemory-policy allkeys-lru
    save 900 1
    save 300 10
    save 60 10000
    
    # Enable compression
    rdbcompression yes
    
    # Security
    requirepass ${REDIS_PASSWORD}
    
    # Performance
    tcp-keepalive 300
    timeout 0
```

### Load Balancing

#### HAProxy Configuration
```haproxy
# haproxy.cfg
global
    daemon
    maxconn 4096
    log stdout local0

defaults
    mode http
    timeout connect 5000ms
    timeout client 50000ms
    timeout server 50000ms
    option httplog

frontend eat_frontend
    bind *:443 ssl crt /etc/ssl/certs/eat-framework.pem
    redirect scheme https if !{ ssl_fc }
    
    # Route to catalog service
    acl is_catalog path_beg /.well-known
    acl is_specs path_beg /specs
    use_backend catalog_backend if is_catalog
    use_backend catalog_backend if is_specs
    
    # Route to MCP servers
    acl is_mcp path_beg /mcp
    use_backend mcp_backend if is_mcp

backend catalog_backend
    balance roundrobin
    option httpchk GET /.well-known/api-catalog
    server catalog1 10.0.1.10:80 check
    server catalog2 10.0.1.11:80 check
    server catalog3 10.0.1.12:80 check

backend mcp_backend
    balance roundrobin
    option httpchk GET /health
    server mcp1 10.0.2.10:3001 check
    server mcp2 10.0.2.11:3001 check
    server mcp3 10.0.2.12:3001 check
```

## 📋 Operational Procedures

### Health Checks

#### Comprehensive Health Monitoring
```python
# health_check.py
import aiohttp
import asyncio
import time
from typing import Dict, List

class EATHealthChecker:
    """
    Comprehensive health checking for EAT Framework
    """
    
    def __init__(self, catalog_url: str):
        self.catalog_url = catalog_url
        self.health_status = {}
    
    async def check_catalog_availability(self) -> Dict:
        """
        Check catalog endpoint availability and response time
        """
        start_time = time.time()
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.catalog_url, timeout=10) as response:
                    response_time = time.time() - start_time
                    
                    return {
                        "status": "healthy" if response.status == 200 else "unhealthy",
                        "response_time": response_time,
                        "status_code": response.status,
                        "content_length": len(await response.text())
                    }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "response_time": time.time() - start_time
            }
    
    async def check_signature_verification(self) -> Dict:
        """
        Verify catalog signature and key resolution
        """
        try:
            # Download and verify catalog
            catalog = await self.download_catalog()
            signature_valid = await self.verify_signature(catalog)
            
            return {
                "status": "healthy" if signature_valid else "unhealthy",
                "signature_valid": signature_valid,
                "key_resolution": "success"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }
    
    async def check_mcp_servers(self) -> Dict:
        """
        Check health of all MCP servers listed in catalog
        """
        catalog = await self.download_catalog()
        mcp_servers = self.extract_mcp_servers(catalog)
        
        results = {}
        for server_url in mcp_servers:
            try:
                health_endpoint = f"{server_url}/health"
                async with aiohttp.ClientSession() as session:
                    async with session.get(health_endpoint, timeout=5) as response:
                        results[server_url] = {
                            "status": "healthy" if response.status == 200 else "unhealthy",
                            "response_time": response.headers.get("X-Response-Time", "unknown")
                        }
            except Exception as e:
                results[server_url] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return results
    
    async def run_health_check(self) -> Dict:
        """
        Run comprehensive health check
        """
        checks = await asyncio.gather(
            self.check_catalog_availability(),
            self.check_signature_verification(),
            self.check_mcp_servers(),
            return_exceptions=True
        )
        
        return {
            "timestamp": time.time(),
            "catalog_availability": checks[0],
            "signature_verification": checks[1],
            "mcp_servers": checks[2],
            "overall_status": self.calculate_overall_status(checks)
        }
```

### Backup and Recovery

#### Automated Backup Strategy
```bash
#!/bin/bash
# backup-eat-framework.sh

BACKUP_DIR="/opt/backups/eat-framework"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="$BACKUP_DIR/$TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_PATH"

# Backup catalog files
cp -r /opt/eat-framework/catalogs "$BACKUP_PATH/"

# Backup specifications
cp -r /opt/eat-framework/specs "$BACKUP_PATH/"

# Backup configuration
cp -r /etc/nginx/sites-available/eat-catalog "$BACKUP_PATH/"

# Backup keys (encrypted)
gpg --cipher-algo AES256 --compress-algo 1 --s2k-mode 3 \
    --s2k-digest-algo SHA512 --s2k-count 65536 --force-mdc \
    --symmetric --output "$BACKUP_PATH/keys.gpg" \
    /opt/eat-framework/keys/

# Create backup manifest
cat > "$BACKUP_PATH/manifest.json" << EOF
{
  "timestamp": "$TIMESTAMP",
  "backup_type": "full",
  "components": [
    "catalogs",
    "specifications", 
    "configuration",
    "keys"
  ],
  "retention_policy": "30d"
}
EOF

# Compress backup
tar -czf "$BACKUP_DIR/eat-framework-$TIMESTAMP.tar.gz" -C "$BACKUP_DIR" "$TIMESTAMP"
rm -rf "$BACKUP_PATH"

# Upload to cloud storage
aws s3 cp "$BACKUP_DIR/eat-framework-$TIMESTAMP.tar.gz" \
    s3://your-backup-bucket/eat-framework/

# Clean old backups (keep 30 days)
find "$BACKUP_DIR" -name "eat-framework-*.tar.gz" -mtime +30 -delete

echo "Backup completed: eat-framework-$TIMESTAMP.tar.gz"
```

---

This deployment guide provides the foundation for running EAT Framework at any scale, from single-service deployments to enterprise-grade architectures with comprehensive monitoring, security, and operational procedures.