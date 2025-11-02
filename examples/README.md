# clippy-code Examples

This directory contains real-world examples and use cases for clippy-code.

## 📁 Directory Structure

```
examples/
├── README.md                    # This file
├── web_development/            # Web development examples
│   ├── flask_app/              # Flask application setup
│   ├── react_project/          # React project creation
│   └── node_api/               # Node.js API project
├── data_science/               # Data science workflows
│   ├── analysis_pipeline/      # Complete data analysis pipeline
│   ├── machine_learning/       # ML model development with MLOps
│   └── data_visualization/     # Plotting and visualization
├── cli_tools/                  # Command-line tool development
│   ├── python_cli/             # Professional Python CLI tools
│   ├── shell_scripts/          # Practical shell scripts
│   └── shell_automation.md     # Complete automation workflows
├── devops/                     # DevOps and automation
│   ├── docker_projects/        # Complete Docker projects
│   ├── kubernetes/             # Kubernetes manifests
│   └── ci_cd/                  # CI/CD pipeline configs
├── api_development/            # API development examples
│   ├── rest_apis/              # Complete REST API with FastAPI
│   ├── graphql/                # GraphQL schemas
│   └── api_documentation/      # API docs generation
└── advanced/                   # Advanced clippy-code features
    ├── subagent_workflows/     # Subagent delegation patterns
    ├── parallel_tasks/         # Parallel execution examples
    └── mcp_integrations/        # MCP server setups
```

## 🚀 Quick Start with Examples

Each example directory contains:

1. **Scenario description** - What problem we're solving
2. **Step-by-step instructions** - How to use clippy-code
3. **Expected output** - What you should get
4. **Tips & variations** - Customization options

## 🔧 Modern Python Development with uv & pyproject.toml

All examples use **modern Python packaging** with:
- **`pyproject.toml`** - Single configuration file (no more `requirements.txt`)
- **`uv`** - Fast dependency management (10x faster than pip)
- **`hatch`** - Modern build backend
- **Lock files** - Reproducible builds

### Quick Setup
```bash
# Install uv (once)
curl -LsSf https://astral.sh/uv/install.sh | sh

# In any example directory:
uv sync                    # Install dependencies
uv run python script.py     # Run scripts
uv add package-name         # Add new dependency
uv add --dev pytest         # Add dev dependency
```

### Benefits
- ⚡ **10x faster** dependency resolution than pip
- 🔒 **Lock files** for reproducible environments  
- 📦 **Single source of truth** in `pyproject.toml`
- 🚀 **Modern toolchain** with Python version management
- 🛠️ **Integrated** with existing tools (pytest, black, ruff)
## 📋 How to Use These Examples

```bash
# Navigate to an example directory
cd examples/web_development/flask_app

# Run the example
clippy -f create_flask_app.md

# Or copy-paste commands from individual examples
clippy "Create a Flask app with user authentication"
```

## 🎯 Featured Examples

### 🌐 Flask Web App
```bash
cd examples/web_development/flask_app
clippy "Create a complete Flask app with user auth, database, and templates"
```

### 📊 Data Analysis Pipeline
```bash
cd examples/data_science/analysis_pipeline
clippy "Create a complete data cleaning and visualization pipeline with pandas, matplotlib, and automated reporting"
```

### 🤖 Machine Learning
```bash
cd examples/data_science/machine_learning
clippy "Build a complete ML pipeline with feature engineering, model training, and MLOps"
```

### 🛠️ CLI Tool
```bash
cd examples/cli_tools/python_cli
clippy "Create a professional CLI tool with argparse, rich output, and packaging"
```

### 🔧 Shell Automation
```bash
cd examples/cli_tools
clippy "Create shell automation scripts for deployment and system maintenance"
```

### 🚀 REST API
```bash
cd examples/api_development/rest_apis
clippy "Create a complete REST API with FastAPI, authentication, and testing"
```

### 🐳 Docker Project
```bash
cd examples/devops/docker_projects
clippy "Create a complete Docker project with multi-stage builds, Docker Compose, and CI/CD"
```

Looking for something specific? Browse the directories above or create your own examples and contribute!