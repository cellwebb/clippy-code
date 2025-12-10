# clippy-code Use Cases & Recipes

A collection of real-world scenarios and workflows demonstrating how to effectively use clippy-code for different development tasks.

## 🚀 Getting Starters

### Complete Project Scaffolding

**Scenario**: You need to create a new Python project from scratch with all the modern best practices.

```bash
clippy "Create a complete Python project structure with:
- Modern pyproject.toml with uv
- src/ layout with proper imports
- pytest setup with coverage
- GitHub Actions CI/CD
- pre-commit hooks
- README with installation instructions
- Type hints and docstrings
- CLI entry point
- Example module with functions
Make it production-ready with proper packaging."
```

**Result**: A fully scaffolded project ready for development and deployment.

---

## 🔧 Development Workflows

### Code Review & Refactoring

**Scenario**: You have an existing codebase and want to improve code quality and security.

```bash
clippy "Perform a comprehensive code review of the src/ directory:
1. Identify security vulnerabilities
2. Find performance bottlenecks
3. Suggest design pattern improvements
4. Check for code duplication
5. Verify proper error handling
6. Ensure good type coverage
7. Recommend refactoring opportunities

Focus on the authentication and database modules first."
```

**Alternative - Use Subagents for Parallel Review**:
```bash
clippy "Create a parallel code review workflow:
- Use code_review subagent for security analysis
- Use power_analysis subagent for architecture review
- Use refactor subagent for improvement suggestions
Each should focus on different aspects and provide actionable recommendations."
```

### Test Generation

**Scenario**: An existing project lacks sufficient test coverage.

```bash
clippy "Generate comprehensive test suite for the user_management module:
1. Unit tests for all public functions
2. Edge case testing (null inputs, invalid data)
3. Integration tests for database operations
4. Mock external dependencies
5. Parameterized tests for different scenarios
6. Performance tests for critical functions
Target 90% code coverage."
```

### Debugging & Issue Resolution

**Scenario**: You're encountering a mysterious bug in production.

```bash
clippy "Help debug this issue:
Users are reporting authentication failures after the recent deployment.
The error logs show 'Invalid token' but tokens are valid in development.
Please:
1. Review the auth.py module
2. Check environment variable handling
3. Examine the recent git changes
4. Suggest debugging strategies
5. Provide potential fixes
6. Create regression tests to prevent this"
```

---

## 🌐 Web Development

### Full-Stack Application Setup

**Scenario**: Create a complete web application with modern tech stack.

```bash
clippy "Create a full-stack web application:
Frontend:
- React with TypeScript
- Tailwind CSS for styling
- React Router for navigation
- Axios for API calls
- Form validation with react-hook-form

Backend:
- FastAPI with Python
- SQLAlchemy for database
- JWT authentication
- Swagger documentation
- CORS configuration

DevOps:
- Docker for containerization
- docker-compose for local development
- GitHub Actions for CI/CD
- Environment-based configuration

Project should be production-ready with proper error handling."
```

### API Development

**Scenario**: Build a RESTful API with proper documentation and testing.

```bash
clippy "Create a REST API for a task management system:
1. FastAPI backend with SQLAlchemy models
2. Full CRUD operations for tasks
3. User authentication and authorization
4. Query parameters for filtering/sorting
5. Pagination support
6. API versioning
7. OpenAPI documentation
8. Comprehensive test suite
9. Request validation and error handling
10. Rate limiting middleware"
```

---

## 📊 Data Science & Analytics

### Data Analysis Pipeline

**Scenario**: Build an automated data analysis workflow.

```bash
clippy "Create a data analysis pipeline for sales data:
1. Data ingestion from multiple CSV/JSON sources
2. Automated data cleaning and validation
3. Exploratory data analysis with visualizations
4. Statistical analysis and hypothesis testing
5. Machine learning model for sales forecasting
6. Automated report generation in HTML/PDF
7. Dashboard with Plotly Dash
8. Scheduled execution with cron/Airflow
9. Error handling and logging
10. Docker containerization
Use pandas, matplotlib, seaborn, scikit-learn, and plotly."
```

### Machine Learning Project

**Scenario**: End-to-end ML project with MLOps best practices.

```bash
clippy "Build a complete ML project for customer churn prediction:
1. Feature engineering pipeline
2. Model training with cross-validation
3. Hyperparameter optimization
4. Model interpretability with SHAP
5. Model monitoring and drift detection
6. A/B testing framework
7. Model serving with FastAPI
8. CI/CD for model retraining
9. Experiment tracking with MLflow
10. Documentation and reproducibility"
```

---

## 🛠️ DevOps & Automation

### CI/CD Pipeline Setup

**Scenario**: Automate the entire software delivery lifecycle.

```bash
clippy "Create a comprehensive CI/CD pipeline:
1. GitHub Actions workflow for testing
2. Automated code quality checks (ruff, mypy, pylint)
3. Security vulnerability scanning
4. Automated testing (unit, integration, e2e)
5. Docker multi-stage builds
6. Deployment to staging/production
7. Rollback mechanisms
8. Monitoring and alerting
9 Database migrations
10. Infrastructure as Code with Terraform"
```

### Infrastructure Automation

**Scenario**: Automate infrastructure provisioning and management.

```bash
clippy "Create infrastructure automation scripts:
1. Terraform modules for AWS resources
2. Ansible playbooks for server configuration
3. Docker compose for local development
4. Kubernetes manifests for production
5. Monitoring setup with Prometheus/Grafana
6. Log aggregation with ELK stack
7. Backup and disaster recovery
8. Security hardening scripts
9. Cost optimization recommendations
10. Documentation for all infrastructure"
```

---

## 🤖 Advanced clippy-code Features

### Subagent Orchestration

**Scenario**: Complex project requiring multiple specialized AI agents.

```bash
clippy "Create a subagent workflow for codebase modernization:
1. Use power_analysis subagent to analyze architecture
2. Use code_review subagent for security audit
3. Use refactor subagent for code improvements
4. Use testing subagent to generate comprehensive tests
5. Use documentation subagent to update all documentation
Execute in parallel where possible, with proper result aggregation."
```

### MCP Integration

**Scenario**: Extend capabilities with external tools and services.

```bash
clippy "Set up MCP integration for enhanced development:
1. Configure Context7 for search and retrieval
2. Add database tools for direct data access
3. Integrate Git operations through MCP
4. Set up code quality tools
5. Add deployment and monitoring tools
Configure all in ~/.clippy/mcp.json with proper API keys."
```

---

## 🔍 Specialized Scenarios

### Migration Project

**Scenario**: Modernize a legacy codebase.

```bash
clippy "Plan and execute a legacy Python project migration:
1. Analyze current codebase structure
2. Create migration roadmap with phases
3. Update from setup.py to pyproject.toml
4. Migrate from legacy testing to pytest
5. Add type hints throughout codebase
6. Update dependencies to modern versions
7. Refactor legacy patterns to modern equivalents
8. Add proper error handling and logging
9. Create comprehensive test suite
10. Update documentation and README
Provide migration scripts and validation steps."
```

### Performance Optimization

**Scenario**: Profile and optimize a slow application.

```bash
clippy "Optimize application performance:
1. Profile application bottlenecks
2. Identify database query optimization opportunities
3. Suggest caching strategies
4. Recommend async/await implementations
5. Optimize algorithmic complexity
6. Add performance monitoring
7. Create performance test suite
8. Optimize Docker images
9. Suggest infrastructure improvements
10. Document optimization decisions"
```

### Security Hardening

**Scenario**: Strengthen application security posture.

```bash
clippy "Perform comprehensive security hardening:
1. Security audit of authentication system
2. Implement proper input validation
3. Add CSRF and XSS protection
4. Secure database against injection attacks
5. Implement rate limiting and throttling
6. Add security headers and CORS
7. Encrypt sensitive data at rest
8. Implement secure logging practices
9. Add security monitoring and alerts
10. Create security documentation and checklists"
```

---

## 📝 Documentation Projects

### API Documentation

**Scenario**: Create comprehensive API documentation.

```bash
clippy "Generate complete API documentation:
1. Auto-generate OpenAPI specification
2. Create interactive API documentation
3. Add code examples for each endpoint
4. Document authentication flows
5. Add error response documentation
6. Create client SDK examples
7. Add troubleshooting guide
8. Document rate limiting
9. Create changelog template
10. Set up documentation CI/CD"
```

### Developer Documentation

**Scenario**: Improve project onboarding and developer experience.

```bash
clippy "Create comprehensive developer documentation:
1. Detailed setup instructions for all environments
2. Architecture decision records (ADRs)
3. Code style and contribution guidelines
4. Database schema documentation
5. API reference documentation
6. Testing guidelines and strategies
7. Deployment procedures
8. Troubleshooting FAQ
9. Performance tuning guide
10. Development best practices"
```

---

## 🎯 Quick Reference Recipes

### Common Tasks

| Task | Command | Notes |
|------|---------|-------|
| **Add logging** | `clippy "Add structured logging to main.py with JSON output and log levels"` | Good for debugging and monitoring |
| **Generate configs** | `clippy "Create configuration management with environment variables and validation"` | Use pydantic for type safety |
| **Add Docker** | `clippy "Add Docker with multi-stage build and proper .dockerignore"` | Include development and production configurations |
| **Setup testing** | `clippy "Add pytest with coverage, fixtures, and parameterized tests"` | Target 80%+ code coverage |
| **Git hooks** | `clippy "Setup pre-commit hooks with linting, formatting, and security checks"` | Ensures code quality across team |
| **API docs** | `clippy "Add Swagger/OpenAPI documentation with examples"` | Auto-generate from FastAPI routes |
| **Error handling** | `clippy "Add comprehensive error handling with custom exceptions and logging"` | Include error codes and recovery strategies |
| **Performance** | `clippy "Add caching layer with Redis and proper cache invalidation"` | Consider cache hit ratios and TTLs |

### Development Workflows

**Feature Development Workflow**:
```bash
clippy "Help implement a new user feature:
1. Create feature branch with proper naming
2. Add model changes and migrations
3. Implement API endpoints
4. Create comprehensive tests
5. Update documentation
6. Add monitoring and logging
7. Create deployment checklist"
```

**Bug Fixing Workflow**:
```bash
clippy "Debug and fix production bug:
1. Reproduce issue locally
2. Analyze logs and error patterns
3. Identify root cause
4. Implement fix with tests
5. Verify regression is prevented
6. Document the fix and lessons learned"
```

---

## 💡 Pro Tips

### Effective Prompting

1. **Be Specific**: Include technologies, frameworks, and constraints
2. **Provide Context**: Mention existing codebase structure and goals
3. **Request Tests**: Always ask for comprehensive test coverage
4. **Include Security**: Mention security requirements explicitly
5. **Ask for Documentation**: Request inline docs and README updates

### Advanced Techniques

1. **Use Subagents**: Delegate specialized tasks to appropriate subagent types
2. **Parallel Execution**: Run independent tasks concurrently for faster results
3. **Iterative Development**: Build solutions incrementally with feedback
4. **Template Requests**: Ask for templates you can customize
5. **Best Practices**: Request industry standards and patterns

### Troubleshooting Common Issues

1. **Environment Problems**: Ask for Docker setup or environment validation
2. **Dependency Conflicts**: Request dependency resolution and pinning
3. **Performance Issues**: Ask for profiling and optimization strategies
4. **Integration Problems**: Request debugging and logging improvements
5. **Deployment Challenges**: Seek automation and CI/CD solutions

---

## 🚀 Getting Started with These Recipes

1. **Choose a recipe** that matches your current project needs
2. **Customize the prompt** with your specific requirements
3. **Review the output** carefully before applying changes
4. **Test incrementally** and validate each step
5. **Iterate and refine** based on results
6. **Share your successes** and new recipes with the community!

Have a great use case or recipe? Contribute it to help others benefit from your experience! 🎉