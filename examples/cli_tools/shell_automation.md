# Shell Automation Example

## 🎯 Scenario

Create powerful shell automation scripts using clippy-code to:
- Automate repetitive development tasks
- Create deployment scripts
- Build file management utilities
- System monitoring and maintenance
- Backup and restoration scripts
- Development environment setup
- CI/CD pipeline scripts
- Log analysis and reporting

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/cli_tools

# Create shell automation scripts
clippy "Create a comprehensive shell automation script for development environment setup, deployment, and system maintenance"
```

## 📁 Expected Project Structure

```
shell_automation/
├── scripts/
│   ├── dev_setup.sh              # Development environment setup
│   ├── deployment.sh             # Application deployment
│   ├── backup.sh                 # Backup automation
│   ├── cleanup.sh                # System cleanup
│   ├── monitor.sh                # System monitoring
│   └── health_check.sh           # Health monitoring
├── templates/
│   ├── systemd/                  # Systemd service templates
│   ├── nginx/                    # Nginx configuration templates
│   └── docker/                   # Docker compose templates
├── utils/
│   ├── logging.sh                # Logging utilities
│   ├── notifications.sh          # Notification system
│   └── validation.sh             # Input validation
├── config/
│   ├── dev.env                   # Development environment config
│   ├── prod.env                  # Production environment config
│   └── backup.conf               # Backup configuration
├── tests/
│   ├── test_scripts.sh           # Test shell scripts
│   └── integration/              # Integration tests
├── README.md                     # This file
└── Makefile                      # Build and deployment automation
```

## 🛠️ Step-by-Step Commands

### 1. Create Development Environment Setup Script
```bash
clippy "Create a comprehensive dev_setup.sh script that installs dependencies, sets up configurations, and initializes development tools"
```

### 2. Build Deployment Automation
```bash
clippy "Create deployment.sh script with zero-downtime deployment, rollback capabilities, and environment-specific configurations"
```

### 3. Implement Backup System
```bash
clippy "Create backup.sh script with automated database backups, file system backups, and retention policies"
```

### 4. Add System Monitoring
```bash
clippy "Create monitor.sh script with CPU, memory, disk monitoring, alerts, and performance metrics collection"
```

### 5. Create Health Check System
```bash
clippy "Create health_check.sh script with service health monitoring, dependency checking, and automated recovery"
```

### 6. Build Cleanup Utilities
```bash
clippy "Create cleanup.sh script for log rotation, temporary file cleanup, disk space management, and maintenance tasks"
```

### 7. Add Notification System
```bash
clippy "Create notification system with email, Slack, and webhook integrations for alerts and status updates"
```

### 8. Create Test Framework
```bash
clippy "Create test framework for shell scripts with unit tests, integration tests, and validation"
```

## 💡 Advanced Features

### Multi-Environment Support
```bash
clippy "Add environment-specific configuration management with secure secret handling and validation"
```

### Rollback System
```bash
clippy "Implement automatic rollback system with version tracking, health validation, and recovery procedures"
```

### CI/CD Integration
```bash
clippy "Add GitHub Actions/Jenkins integration with automated testing, deployment, and monitoring"
```

## 🔍 Shell Script Validation

```bash
# ✅ Bash scripts validated for syntax
clippy "Create shell scripts with proper error handling, parameter validation, and security fixes"

# ✅ Configuration files validated
clippy "Create environment configurations with proper variable validation and defaults"
```

## 📝 Example Shell Scripts

### Development Environment Setup (dev_setup.sh)
```bash
#!/bin/bash

# Development Environment Setup Script
# This script sets up a complete development environment

set -euo pipefail  # Exit on error, treat unset variables as error

# Configuration
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly LOG_FILE="$PROJECT_ROOT/logs/setup.log"

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Logging function
log() {
    local level="$1"
    shift
    local message="$*"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    echo "[$timestamp] [$level] $message" | tee -a "$LOG_FILE"
}

info() {
    log "INFO" "${GREEN}$message${NC}"
}

warn() {
    log "WARN" "${YELLOW}$message${NC}"
}

error() {
    log "ERROR" "${RED}$message${NC}"
}

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."
    
    # Check for required commands
    local required_commands=("git" "python3" "docker" "npm" "make")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "$cmd is not installed. Please install it first."
            exit 1
        fi
    done
    
    info "All prerequisites are satisfied."
}

# Install Python dependencies
setup_python() {
    info "Setting up Python environment..."
    
    cd "$PROJECT_ROOT"
    
    # Create virtual environment if it doesn't exist
    if [[ ! -d "venv" ]]; then
        info "Creating Python virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    
    info "Python environment setup completed."
}

# Setup Node.js dependencies
setup_nodejs() {
    info "Setting up Node.js environment..."
    
    cd "$PROJECT_ROOT"
    if [[ -f "package.json" ]]; then
        npm ci  # Use ci for clean installs in CI/CD
        info "Node.js dependencies installed."
    else
        warn "No package.json found, skipping Node.js setup."
    fi
}

# Initialize Git configuration
setup_git() {
    info "Setting up Git hooks and configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Install pre-commit hooks
    if command -v pre-commit &> /dev/null; then
        pre-commit install
        info "Pre-commit hooks installed."
    fi
    
    # Set up Git hooks
    if [[ -d ".git/hooks" ]]; then
        cp scripts/hooks/* .git/hooks/
        chmod +x .git/hooks/*
        info "Git hooks installed."
    fi
}

# Setup development services
setup_services() {
    info "Setting up development services..."
    
    cd "$PROJECT_ROOT"
    
    # Start Docker development services
    if [[ -f "docker-compose.dev.yml" ]]; then
        docker-compose -f docker-compose.dev.yml up -d
        info "Development services started."
    fi
    
    # Initialize database if needed
    if [[ -f "scripts/init_db.py" ]]; then
        python3 scripts/init_db.py
        info "Database initialized."
    fi
}

# Create development configuration
setup_config() {
    info "Creating development configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Copy configuration files
    if [[ -f "config/dev.env.example" ]]; then
        cp config/dev.env.example config/dev.env
        info "Development configuration created."
    fi
    
    # Set up environment variables
    local env_file=".env"
    if [[ ! -f "$env_file" ]]; then
        cat > "$env_file" << EOF
# Development Environment
DEBUG=true
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/devdb
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=dev-secret-key-change-in-production
EOF
        info "Environment file created."
    fi
}

# Validate setup
validate_setup() {
    info "Validating development setup..."
    
    cd "$PROJECT_ROOT"
    
    # Run tests
    if command -v pytest &> /dev/null; then
        pytest tests/ --tb=short
        info "Tests passed successfully."
    fi
    
    # Check service health
    if command -v curl &> /dev/null; then
        if curl -f http://localhost:8000/health &> /dev/null; then
            info "Application is healthy."
        else
            warn "Application health check failed."
        fi
    fi
}

# Main setup function
main() {
    info "Starting development environment setup..."
    
    # Create logs directory
    mkdir -p logs
    
    check_prerequisites
    setup_python
    setup_nodejs
    setup_git
    setup_services
    setup_config
    validate_setup
    
    info "Development environment setup completed successfully!"
    info "Run 'make dev' to start development server"
    info "Run 'make test' to run tests"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTION]"
        echo "Setup development environment"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --skip-tests   Skip validation tests"
        echo "  --dry-run      Show what would be done without executing"
        exit 0
        ;;
    --skip-tests)
        info "Skipping validation tests"
        validate_setup() { :; }
        main
        ;;
    --dry-run)
        info "Dry run mode - showing what would be done:"
        echo "1. Check prerequisites (git, python3, docker, npm, make)"
        echo "2. Setup Python virtual environment"
        echo "3. Install Python dependencies"
        echo "4. Setup Node.js dependencies"
        echo "5. Install Git hooks and pre-commit"
        echo "6. Start development services"
        echo "7. Create configuration files"
        echo "8. Run validation tests"
        ;;
    *)
        main
        ;;
esac
```

### Deployment Automation (deployment.sh)
```bash
#!/bin/bash

# Automated Deployment Script
# Supports zero-downtime deployment with rollback

set -euo pipefail

readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
readonly CONFIG_DIR="$PROJECT_ROOT/config"
readonly LOG_DIR="$PROJECT_ROOT/logs"
readonly DEPLOYMENT_LOG="$LOG_DIR/deployment.log"

# Load configuration
load_config() {
    local env="${DEPLOYMENT_ENV:-staging}"
    local config_file="$CONFIG_DIR/${env}.env"
    
    if [[ -f "$config_file" ]]; then
        set -a
        source "$config_file"
        set +a
        echo "Loaded configuration from $config_file"
    else
        echo "Error: Configuration file $config_file not found"
        exit 1
    fi
}

# Pre-deployment checks
pre_deploy_checks() {
    echo "Running pre-deployment checks..."
    
    # Check application health
    if ! curl -f "$HEALTH_CHECK_URL" &> /dev/null; then
        echo "Error: Application is not healthy before deployment"
        exit 1
    fi
    
    # Check database connectivity
    if ! pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER"; then
        echo "Error: Database is not accessible"
        exit 1
    fi
    
    # Validate configuration
    python3 -c "import yaml; yaml.safe_load(open('$CONFIG_FILE'))"
    
    echo "Pre-deployment checks passed"
}

# Build application
build_application() {
    echo "Building application..."
    
    cd "$PROJECT_ROOT"
    
    # Run tests
    pytest tests/ --tb=short
    
    # Build Docker image
    docker build -t "$IMAGE_NAME:$BUILD_NUMBER" .
    docker tag "$IMAGE_NAME:$BUILD_NUMBER" "$IMAGE_NAME:latest"
    
    echo "Application built successfully"
}

# Deploy with zero-downtime
deploy_application() {
    echo "Deploying application..."
    
    # Create backup
    ./scripts/backup.sh create
    
    # Deploy new version
    if [[ "$DEPLOYMENT_STRATEGY" == "blue-green" ]]; then
        deploy_blue_green
    else
        deploy_rolling
    fi
    
    echo "Application deployed successfully"
}

# Blue-green deployment
deploy_blue_green() {
    echo "Starting blue-green deployment..."
    
    local current_color=$(docker service inspect --format '{{range .Spec.TaskTemplate.ContainerSpec.Labels}}{{.}}{{end}}' "$SERVICE_NAME" | grep -o 'color=[a-z]*' | cut -d= -f2)
    local new_color=$([[ "$current_color" == "blue" ]] && echo "green" || echo "blue")
    
    # Deploy to inactive environment
    docker service create \
        --name "${SERVICE_NAME}-${new_color}" \
        --label "color=${new_color}" \
        --network "$NETWORK_NAME" \
        --replicas 3 \
        "$IMAGE_NAME:$BUILD_NUMBER"
    
    # Wait for health check
    wait_for_service "${SERVICE_NAME}-${new_color}"
    
    # Switch traffic
    docker service update \
        --publish-add 80:80 \
        --label "color=${new_color}" \
        "$SERVICE_NAME"
    
    # Remove old environment
    docker service rm "${SERVICE_NAME}-${current_color}"
}

# Rolling deployment
deploy_rolling() {
    echo "Starting rolling deployment..."
    
    docker service update \
        --image "$IMAGE_NAME:$BUILD_NUMBER" \
        --update-parallelism 1 \
        --update-delay 10s \
        --update-failure-action rollback \
        "$SERVICE_NAME"
    
    wait_for_service "$SERVICE_NAME"
}

# Wait for service to be healthy
wait_for_service() {
    local service_name="$1"
    local max_attempts=30
    local attempt=1
    
    echo "Waiting for service $service_name to be healthy..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if docker service ps "$service_name" --format '{{.CurrentState}}' | grep -q "Running"; then
            echo "Service $service_name is healthy"
            return 0
        fi
        
        echo "Attempt $attempt/$max_attempts: Service not ready yet"
        sleep 10
        ((attempt++))
    done
    
    echo "Error: Service $service_name failed to become healthy"
    return 1
}

# Post-deployment verification
post_deploy_verification() {
    echo "Running post-deployment verification..."
    
    # Wait for application to be ready
    sleep 30
    
    # Health check
    if ! curl -f "$HEALTH_CHECK_URL" &> /dev/null; then
        echo "Error: Application health check failed after deployment"
        rollback_deployment
        exit 1
    fi
    
    # Run smoke tests
    python3 scripts/smoke_tests.py
    
    echo "Post-deployment verification passed"
}

# Rollback deployment
rollback_deployment() {
    echo "Rolling back deployment..."
    
    # Restore from backup
    ./scripts/backup.sh restore latest
    
    # Redeploy previous version
    local previous_image=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep "$IMAGE_NAME" | head -2 | tail -1)
    docker service update --image "$previous_image" "$SERVICE_NAME"
    
    echo "Deployment rolled back"
}

# Cleanup old images
cleanup() {
    echo "Cleaning up old Docker images..."
    
    # Remove old images (keep last 5)
    docker images --format "{{.Repository}}:{{.Tag}}" | grep "$IMAGE_NAME" | tail -n +6 | xargs -r docker rmi
    
    echo "Cleanup completed"
}

# Notify deployment status
notify() {
    local status="$1"
    local message="Deployment $status for environment $DEPLOYMENT_ENV, build $BUILD_NUMBER"
    
    # Send to Slack
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"$message\"}" \
            "$SLACK_WEBHOOK_URL"
    fi
    
    # Send email
    if [[ -n "${NOTIFICATION_EMAIL:-}" ]]; then
        echo "$message" | mail -s "Deployment Notification" "$NOTIFICATION_EMAIL"
    fi
}

# Main deployment function
main() {
    local start_time=$(date +%s)
    
    echo "Starting deployment at $(date)"
    mkdir -p "$LOG_DIR"
    
    load_config
    pre_deploy_checks
    build_application
    deploy_application
    post_deploy_verification
    cleanup
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    echo "Deployment completed successfully in ${duration}s"
    notify "SUCCESS"
    
    # Update deployment metrics
    echo "$BUILD_NUMBER,$(date),$duration,SUCCESS" >> "$LOG_DIR/deployment_metrics.csv"
}

# Error handling
trap 'notify "FAILED"; exit 1' ERR

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [OPTION]"
        echo "Automated deployment with zero-downtime and rollback"
        echo ""
        echo "Options:"
        echo "  --help, -h      Show this help message"
        echo "  --rollback      Rollback to previous version"
        echo "  --status        Show deployment status"
        echo "  --config=ENV    Use specific environment config"
        ;;
    --rollback)
        rollback_deployment
        ;;
    --status)
        docker service ps "$SERVICE_NAME"
        ;;
    --config=*)
        DEPLOYMENT_ENV="${1#*=}"
        main
        ;;
    *)
        main
        ;;
esac
```

## 🔧 Advanced Automation Techniques

### Configuration Management
```bash
# Load environment-specific configuration
load_environment_config() {
    local env="$1"
    local config_file="$CONFIG_DIR/${env}.yaml"
    
    # Validate YAML syntax
    python3 -c "import yaml; yaml.safe_load(open('$config_file'))" || {
        echo "Error: Invalid configuration in $config_file"
        exit 1
    }
    
    # Extract configuration values
    DATABASE_URL=$(yq eval '.database.url' "$config_file")
    REDIS_URL=$(yq eval '.redis.url' "$config_file")
}
```

### Health Monitoring
```bash
# Comprehensive health checking
health_check() {
    local services=("$@")
    local all_healthy=true
    
    for service in "${services[@]}"; do
        local health_url="http://localhost:${service//[^0-9]/}/health"
        
        if curl -f -s "$health_url" > /dev/null; then
            echo "✅ $service is healthy"
        else
            echo "❌ $service is unhealthy"
            all_healthy=false
        fi
    done
    
    [[ "$all_healthy" == true ]]
}
```

### Backup Automation
```bash
# Automated backup system
create_backup() {
    local backup_dir="$BACKUP_ROOT/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$backup_dir"
    
    # Database backup
    pg_dump "$DATABASE_URL" > "$backup_dir/database.sql"
    
    # File backup
    rsync -av --exclude='*.log' "$APP_ROOT/" "$backup_dir/files/"
    
    # Compress backup
    tar -czf "$backup_dir.tar.gz" -C "$BACKUP_ROOT" "$(basename "$backup_dir")"
    rm -rf "$backup_dir"
    
    echo "Backup created: $backup_dir.tar.gz"
}
```

## 📊 Integration with Development Tools

### Git Hooks Integration
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running pre-commit checks..."

# Run linter
if ! make lint; then
    echo "Linting failed. Please fix issues before committing."
    exit 1
fi

# Run tests
if ! make test; then
    echo "Tests failed. Please fix issues before committing."
    exit 1
fi

# Check for sensitive data
if grep -r "password\|secret\|token" --include="*.py" --include="*.yaml" --exclude-dir=tests . | grep -v "env\|example"; then
    echo "Potential sensitive data found. Please review."
    exit 1
fi

echo "Pre-commit checks passed."
```

### Makefile Integration
```makefile
.PHONY: clean test lint dev deploy backup

dev: ## Start development environment
	./scripts/dev_setup.sh
	docker-compose -f docker-compose.dev.yml up -d
	@echo "Development environment started"

test: ## Run tests
	@echo "Running tests..."
	pytest tests/ -v --cov=src

lint: ## Run linter
	@echo "Running linter..."
	ruff check src/
	ruff format src/

deploy: ## Deploy application
	./scripts/deployment.sh --config=production

backup: ## Create backup
	./scripts/backup.sh create

ci: ## Run CI pipeline
	@echo "Running CI pipeline..."
	make lint
	make test
	make security-scan
```

## 🧪 Testing Shell Scripts

### Unit Testing Shell Scripts
```bash
#!/bin/bash
# tests/test_scripts.sh

set -euo pipefail

# Import functions to test
source ../utils/logging.sh
source ../utils/validation.sh

# Test logging functions
test_logging() {
    echo "Testing logging functions..."
    
    local test_log=$(mktemp)
    
    log "INFO" "Test message" > "$test_log"
    
    if grep -q "INFO.*Test message" "$test_log"; then
        echo "✅ Log test passed"
    else
        echo "❌ Log test failed"
        return 1
    fi
    
    rm "$f"
}

# Test validation functions
test_validation() {
    echo "Testing validation functions..."
    
    if validate_email "test@example.com"; then
        echo "✅ Email validation test passed"
    else
        echo "❌ Email validation test failed"
        return 1
    fi
    
    if ! validate_email "invalid-email"; then
        echo "✅ Invalid email test passed"
    else
        echo "❌ Invalid email test failed"
        return 1
    fi
}

# Run all tests
main() {
    test_logging
    test_validation
    echo "All tests passed!"
}

main "$@"
```

## 📈 Monitoring and Alerting

### System Monitoring Script
```bash
#!/bin/bash
# scripts/monitor.sh

check_disk_space() {
    local threshold=90
    local usage=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [[ $usage -gt $threshold ]]; then
        send_alert "Disk usage is at ${usage}% on $(hostname)"
    fi
}

check_memory_usage() {
    local threshold=80
    local usage=$(free | awk 'NR==2{printf "%.0f", $3*100/$2}')
    
    if [[ $usage -gt $threshold ]]; then
        send_alert "Memory usage is at ${usage}% on $(hostname)"
    fi
}

check_service_health() {
    local services=("nginx" "postgresql" "redis")
    
    for service in "${services[@]}"; do
        if ! systemctl is-active --quiet "$service"; then
            send_alert "Service $service is down on $(hostname)"
        fi
    done
}

send_alert() {
    local message="$1"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Log alert
    echo "[$timestamp] ALERT: $message" >> /var/log/monitoring.log
    
    # Send to monitoring system
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"alert\":\"$message\",\"timestamp\":\"$timestamp\"}" \
        "$MONITORING_WEBHOOK_URL"
}

# Main monitoring loop
main() {
    while true; do
        check_disk_space
        check_memory_usage
        check_service_health
        sleep 300  # Check every 5 minutes
    done
}

main
```

## 🎯 Best Practices Demonstrated

- **Error Handling**: Comprehensive error checking with traps
- **Logging**: Structured logging with timestamps and levels
- **Configuration**: Environment-specific configuration management
- **Validation**: Input validation and pre-flight checks
- **Idempotency**: Scripts can be run multiple times safely
- **Rollback**: Automated rollback capability
- **Testing**: Unit tests for shell scripts
- **Security**: Secure handling of secrets and sensitive data
- **Documentation**: Clear help text and comments
- **Modularity**: Reusable functions and modules

That's a mighty fine shell automation setup! With these scripts, you'll be able to automate everything from development setup to production deployment with proper error handling, monitoring, and rollback capabilities! 🚀📎