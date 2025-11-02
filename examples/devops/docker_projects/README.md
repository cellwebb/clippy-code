# Docker Project Setup Example

## 🎯 Scenario

Create a complete Docker project setup for a Python web application with:
- Multi-stage Dockerfile build
- Docker Compose orchestration
- Development and production configurations
- Database containerization
- Volume management and persistence
- Network configuration
- Health checks and monitoring
- CI/CD integration

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/devops/docker_projects

# Create the complete Docker project
clippy "Create a complete Docker project for a Python web app with multi-stage Dockerfile, Docker Compose, database container, volume management, health checks, and CI/CD integration"
```

## 📁 Expected Project Structure

```
docker_projects/
├── src/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # Flask/FastAPI application
│   │   ├── models.py            # Database models
│   │   ├── requirements.txt     # Python dependencies
│   │   └── Dockerfile           # Application Dockerfile
├── docker/
│   ├── nginx/
│   │   ├── Dockerfile           # Nginx Dockerfile
│   │   └── nginx.conf           # Nginx configuration
│   ├── postgres/
│   │   ├── Dockerfile           # Postgres Dockerfile
│   │   └── init.sql             # Database initialization
│   └── redis/
│       └── redis.conf           # Redis configuration
├── docker-compose/
│   ├── docker-compose.yml       # Development environment
│   ├── docker-compose.prod.yml  # Production environment
│   ├── docker-compose.test.yml  # Testing environment
│   └── .env.example             # Environment variables
├── scripts/
│   ├── build.sh                 # Build automation
│   ├── deploy.sh                # Deployment script
│   ├── backup.sh                # Database backup
│   └── health_check.sh          # Health monitoring
├── kubernetes/
│   ├── namespace.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── monitoring/
│   ├── prometheus.yml           # Prometheus config
│   ├── grafana/
│   │   └── dashboards/
│   └── alertmanager.yml
├── tests/
│   ├── integration/
│   ├── unit/
│   └── docker_test.py
├── .dockerignore                # Docker ignore file
├── docker-compose.override.yml  # Local overrides
├── Makefile                     # Build automation
├── README.md                    # This file
└── LICENSE                      # License file
```

## 🛠️ Step-by-Step Commands

### 1. Create Application Structure
```bash
clippy "Create Python web application structure with Flask/FastAPI, SQLAlchemy models, and requirements.txt with proper dependencies"
```

### 2. Build Multi-stage Dockerfile
```bash
clippy "Create multi-stage Dockerfile with Python base image, dependency installation, application code, and optimized production stage"
```

### 3. Setup Docker Compose Development
```bash
clippy "Create docker-compose.yml with application, PostgreSQL, Redis, and Nginx services with proper networking and volume management"
```

### 4. Configure Production Environment
```bash
clippy "Create docker-compose.prod.yml with production optimizations, security settings, and performance tuning"
```

### 5. Add Nginx Reverse Proxy
```bash
clippy "Create Nginx configuration with SSL termination, load balancing, static file serving, and security headers"
```

### 6. Setup Database Persistence
```bash
clippy "Configure PostgreSQL with persistent volumes, initialization scripts, backup procedures, and connection pooling"
```

### 7. Add Monitoring Stack
```bash
clippy "Setup Prometheus, Grafana, and AlertManager for application monitoring with custom metrics and alerts"
```

### 8. Create CI/CD Pipeline
```bash
clippy "Create GitHub Actions workflow for automated building, testing, and deployment to Docker Registry"
```

## 💡 Advanced Features

### Kubernetes Deployment
```bash
clippy "Create Kubernetes manifests for production deployment with horizontal pod autoscaling and rolling updates"
```

### Service Mesh Integration
```bash
clippy "Add Istio service mesh with traffic management, security policies, and observability"
```

### Auto-scaling and Load Testing
```bash
clippy "Implement auto-scaling policies and load testing with Locust integration"
```

## 🔍 Docker Configuration Validation

```bash
# ✅ Dockerfile syntax validated
clippy "Create optimized multi-stage Dockerfile with proper layer caching and security best practices"

# ✅ Docker Compose files validated
clippy "Create docker-compose.yml with proper service definitions, networks, and volumes"

# ✅ Environment files validated
clippy "Create .env configuration with proper variable naming and validation"
```

## 📝 Example Docker Project Session

```
$ clippy
> Create a complete Docker project for Python web app with database and monitoring

🤖 I'll create a comprehensive Docker project with web application, database, and monitoring stack.

📋 Plan:
1. Create Flask web application with database models
2. Build optimized multi-stage Dockerfile
3. Setup Docker Compose with multiple services
4. Configure Nginx reverse proxy
5. Add PostgreSQL with persistence
6. Setup monitoring with Prometheus/Grafana
7. Create CI/CD pipeline
8. Add Kubernetes deployment files

🎯 Creating web application...

✅ Successfully wrote to src/app/main.py
✅ Successfully wrote to src/app/models.py
✅ Successfully wrote to src/app/requirements.txt

🤖 Building Docker configuration...

✅ Successfully wrote to src/app/Dockerfile
Multi-stage build with Python 3.11-slim, optimizations, and security hardening

🤖 Setting up Docker Compose...

✅ Successfully wrote to docker-compose/docker-compose.yml
Services: app, postgres, redis, nginx with proper networking

🤖 Adding production configuration...

✅ Successfully wrote to docker-compose/docker-compose.prod.yml
Production optimizations: secrets, resource limits, health checks

🎉 Complete Docker project created!
Start: `docker-compose -f docker-compose/docker-compose.yml up -d`
Monitor: `docker-compose -f docker-compose/docker-compose.yml logs -f`
Health: `curl http://localhost/health`
```

## 🐳 Docker Commands and Workflows

### Development Workflow
```bash
# Start development environment
docker-compose -f docker-compose/docker-compose.yml up -d

# View logs
docker-compose -f docker-compose/docker-compose.yml logs -f app

# Execute commands in container
docker-compose -f docker-compose/docker-compose.yml exec app bash

# Stop services
docker-compose -f docker-compose/docker-compose.yml down
```

### Production Deployment
```bash
# Deploy to production
docker-compose -f docker-compose/docker-compose.prod.yml up -d

# Scale application
docker-compose -f docker-compose/docker-compose.prod.yml up -d --scale app=3

# Update with zero downtime
docker-compose -f docker-compose/docker-compose.prod.yml pull
docker-compose -f docker-compose/docker-compose.prod.yml up -d --no-deps app
```

### Database Management
```bash
# Create database backup
docker-compose exec postgres pg_dump -U postgres appdb > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres appdb < backup.sql

# Run migrations
docker-compose exec app python manage.py migrate
```

## 📋 Docker Compose Services

### Application Service
```yaml
app:
  build: 
    context: ./src/app
    target: production
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/appdb
    - REDIS_URL=redis://redis:6379/0
    - FLASK_ENV=production
  depends_on:
    - postgres
    - redis
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
  restart: unless-stopped
```

### Database Service
```yaml
postgres:
  image: postgres:15
  environment:
    - POSTGRES_DB=appdb
    - POSTGRES_USER=postgres
    - POSTGRES_PASSWORD=password
  volumes:
    - postgres_data:/var/lib/postgresql/data
    - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Nginx Reverse Proxy
```yaml
nginx:
  build: ./docker/nginx
  ports:
    - "80:80"
    - "443:443"
  volumes:
    - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
    - static_files:/var/www/static
  depends_on:
    - app
  restart: unless-stopped
```

## 🔧 Dockerfile Optimization

### Multi-stage Build
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Security hardening
RUN adduser --disabled-password --gecos '' appuser

# Copy pip packages
COPY --from=builder /root/.local /home/appuser/.local

# Copy application code
WORKDIR /app
COPY --chown=appuser:appuser . .

# Set environment
ENV PATH=/home/appuser/.local/bin:$PATH
ENV PYTHONPATH=/app

# Health check
HEALTHCHECK --interval=30s --timeout=3s \
  CMD curl -f http://localhost:5000/health || exit 1

USER appuser
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]
```

## 📊 Monitoring and Observability

### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'app'
    static_configs:
      - targets: ['app:5000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']
```

### Grafana Dashboard
```json
{
  "dashboard": {
    "title": "Application Monitoring",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow
```yaml
name: Docker CI/CD

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
    
    - name: Run tests
      run: |
        docker-compose -f docker-compose/docker-compose.test.yml up --abort-on-container-exit
        
    - name: Build Docker image
      run: |
        docker build -t myapp:${{ github.sha }} ./src/app/
        
  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to production
      run: |
        echo "Deploying to production..."
        docker-compose -f docker-compose/docker-compose.prod.yml up -d
```

## 🎯 Environment Configuration

### Development (.env)
```bash
# Application settings
FLASK_ENV=development
DEBUG=true
SECRET_KEY=dev-secret-key

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/appdb_dev

# Redis
REDIS_URL=redis://localhost:6379/0

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

### Production (.env.prod)
```bash
# Application settings
FLASK_ENV=production
DEBUG=false
SECRET_KEY=${RANDOM_SECRET_KEY}

# Database (using Docker secrets)
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/appdb

# Redis
REDIS_URL=redis://redis:6379/0

# Security
SSL_ENABLED=true
ALLOWED_HOSTS=example.com,www.example.com

# Monitoring
PROMETHEUS_ENABLED=true
JAEGER_ENABLED=true
```

## 🔧 Security Best Practices

### Container Security
```bash
# Scan images for vulnerabilities
docker scan myapp:latest

# Use minimal base image
FROM python:3.11-alpine vs python:3.11-slim

# Run as non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Read-only filesystem
docker run --read-only --tmpfs /tmp myapp

# Resource limits
docker run --memory=512m --cpus=1.0 myapp
```

### Network Security
```yaml
# Isolate services in custom networks
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # No internet access

# Service isolation
app:
  networks:
    - frontend
    - backend
postgres:
  networks:
    - backend  # Only accessible from backend
```

## 📈 Performance Optimization

### Build Optimization
```dockerfile
# Leverage layer caching
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code last
COPY . .

# Use .dockerignore
echo "__pycache__/
.pytest_cache/
.git/
*.pyc
" > .dockerignore
```

### Runtime Optimization
```yaml
# Resource limits
app:
  deploy:
    resources:
      limits:
        cpus: '0.50'
        memory: 512M
      reservations:
        cpus: '0.25'
        memory: 256M

# Health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

## 🔍 Troubleshooting and Debugging

### Common Issues
```bash
# Container won't start
docker-compose logs app
docker-compose ps

# Port conflicts
docker-compose down
lsof -i :5000

# Database connection issues
docker-compose exec postgres psql -U postgres -l
docker network ls
docker network inspect docker_projects_default

# Memory issues
docker stats
docker system prune -a
```

### Debugging Commands
```bash
# Interactive shell in container
docker-compose exec app bash

# Inspect container
docker inspect docker_projects_app_1

# View network configuration
docker-compose exec app ip addr show

# Monitor resource usage
docker-compose exec app top
```

## 🧪 Testing Docker Services

### Integration Tests
```python
import pytest
import docker
import requests

class TestDockerSetup:
    def setup_method(self):
        self.client = docker.from_env()
        
    def test_app_health(self):
        """Test application health endpoint"""
        response = requests.get('http://localhost:5000/health')
        assert response.status_code == 200
        
    def test_database_connection(self):
        """Test database connectivity"""
        container = self.client.containers.get('docker_projects_postgres_1')
        exit_code, output = container.exec_run('pg_isready -U postgres')
        assert exit_code == 0
        
    def test_redis_connection(self):
        """Test Redis connectivity"""
        container = self.client.containers.get('docker_projects_redis_1')
        exit_code, output = container.exec_run('redis-cli ping')
        assert b'PONG' in output
```

## 📚 Advanced Docker Patterns

### Service Discovery
```yaml
# Use Docker's internal DNS
app:
  environment:
    - DATABASE_URL=postgresql://postgres:password@postgres:5432/appdb
    - REDIS_URL=redis://redis:6379/0
    # Docker automatically resolves service names to IPs
```

### Blue-Green Deployment
```bash
# Deploy new version
docker-compose -f docker-compose.green.yml up -d

# Switch traffic
docker-compose -f docker-compose.blue.yml down
```

### Rolling Updates
```bash
# Update with rolling restart
docker-compose up -d --no-deps app
docker-compose up -d --scale app=3 --no-deps app
```

## 🎯 Production Checklist

- [ ] Multi-stage builds optimized for size
- [ ] Security scanning with Docker Scout
- [ ] Health checks for all services
- [ ] Resource limits and reservations
- [ ] Persistent volumes for data
- [ ] Backup and restore procedures
- [ ] Monitoring and alerting
- [ ] Log aggregation
- [ ] SSL/TLS termination
- [ ] Network segmentation
- [ ] Secrets management
- [ ] Auto-scaling policies

## 💡 Real-world Use Cases

This Docker project setup is perfect for:

- **Web Applications**: Django, Flask, FastAPI applications
- **Microservices**: Service-oriented architecture
- **Data Processing**: ETL pipelines and batch jobs
- **API Gateway**: Reverse proxy and load balancing
- **Development Environments**: Consistent dev/prod parity
- **CI/CD Pipelines**: Automated testing and deployment

That's a mighty fine Docker setup! With all these components, you'll have a production-ready containerized application in no time! 🐳✨