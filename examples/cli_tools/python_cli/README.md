# Professional CLI Tool Development Example

## 🎯 Scenario

Create a professional-grade command-line interface tool for project management with:
- Argument parsing with subcommands
- Configuration file support
- Rich terminal output with progress bars
- Error handling and logging
- Tab completion support
- Man page generation
- Installation and packaging
- Testing framework

## 🚀 Quick Start

```bash
# Navigate to this directory
cd examples/cli_tools/python_cli

# Create the complete CLI tool
clippy "Create a professional Python CLI tool for project management with argparse, rich output, configuration files, progress bars, tab completion, man pages, and proper packaging"
```

## 📁 Expected Project Structure

```
python_cli/
├── src/
│   └── projman/
│       ├── __init__.py
│       ├── cli.py                  # Main CLI entry point
│       ├── commands/
│       │   ├── __init__.py
│       │   ├── init.py             # Project initialization
│       │   ├── status.py           # Project status
│       │   ├── build.py            # Build commands
│       │   ├── deploy.py           # Deployment commands
│       │   └── config.py           # Configuration management
│       ├── core/
│       │   ├── __init__.py
│       │   ├── project.py          # Project model
│       │   ├── config.py           # Configuration handling
│       │   └── utils.py            # Utility functions
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── console.py          # Rich console setup
│       │   ├── progress.py         # Progress bars
│       │   └── tables.py           # Table formatting
│       └── templates/
│           ├── python_project/     # Project templates
│           ├── web_project/
│           └── cli_project/
├── tests/
│   ├── test_cli.py                 # CLI tests
│   ├── test_commands/
│   └── fixtures/
├── docs/
│   ├── usage.md                    # Usage documentation
│   └── projman.1                  # Man page
├── scripts/
│   ├── install.sh                  # Installation script
│   └── completion.sh               # Tab completion script
├── pyproject.toml                  # Modern packaging with uv
├── README.md                       # This file
└── LICENSE                         # License file
├── README.md                       # This file
└── LICENSE                         # License file
```

## 🛠️ Step-by-Step Commands

### 1. Create Package Structure and Setup
```bash
clippy "Create modern Python package structure with pyproject.toml and uv dependency management, proper src layout, hatch build backend, and CLI tool configuration"
```

### 2. Build Core CLI Framework
```bash
clippy "Create main CLI entry point with argparse, subcommands, error handling, and rich terminal output using click or argparse with rich integration"
```

### 3. Implement Project Management Commands
```bash
clippy "Create CLI subcommands for project initialization, status checking, building, and deployment with proper argument parsing and validation"
```

### 4. Add Configuration System
```bash
clippy "Create configuration management system with YAML/JSON config files, environment variable support, and default values with validation"
```

### 5. Build Rich User Interface
```bash
clippy "Create rich terminal interface with progress bars, colored output, tables, tree views, and status indicators using rich library"
```

### 6. Add Tab Completion
```bash
clippy "Implement bash/zsh tab completion for CLI commands with dynamic completion for files, projects, and options"
```

### 7. Generate Documentation
```bash
clippy "Create man page, help text, and usage documentation with proper formatting and examples"
```

### 8. Create Installation Scripts
```bash
clippy "Create installation scripts, setup.py, and pyproject.toml for proper package distribution and installation"
```

## 💡 Advanced Features

### Plugin System
```bash
clippy "Add plugin architecture with dynamic loading, hook system, and third-party extension support"
```

### Remote Operations
```bash
clippy "Add remote project management with SSH integration, Git operations, and cloud deployment"
```

### Web Interface
```bash
clippy "Add web dashboard companion for project management with API endpoints and real-time updates"
```

## 🔍 CLI Tool Validation

```bash
# ✅ CLI argument parsing validated
clippy "Create argparse configuration with subcommands and proper validation"

# ✅ Bash scripts validated
clippy "Create installation script with proper error handling and validation"

# ✅ Package configuration validated
clippy "Create pyproject.toml with proper metadata and dependencies"
```

## 📝 Example CLI Development Session

```
$ clippy
> Create a professional CLI tool for project management with rich output and tab completion

🤖 I'll create a comprehensive CLI tool for project management.

📋 Plan:
1. Set up modern Python package structure
2. Build CLI framework with argparse
3. Implement subcommands for project operations
4. Add rich terminal interface
5. Create configuration system
6. Add tab completion and documentation
7. Set up packaging and installation

🎯 Setting up package structure...

✅ Successfully wrote to pyproject.toml
✅ Created src/projman/ package structure
✅ Set up modern packaging with setuptools

🤖 Building CLI framework...

✅ Successfully wrote to src/projman/cli.py
Main entry point with argparse, subcommands, and rich output

🤖 Implementing project commands...

✅ Successfully wrote to src/projman/commands/init.py
✅ Successfully wrote to src/projman/commands/status.py
✅ Successfully wrote to src/projman/commands/build.py

🤖 Adding rich UI components...

✅ Successfully wrote to src/projman/ui/console.py
✅ Successfully wrote to src/projman/ui/progress.py
✅ Successfully wrote to src/projman/ui/tables.py

🎉 Professional CLI tool created!
Install: `pip install -e .`
Run: `projman --help`
Test: `projman init myproject`
```

## 🧪 Using the CLI Tool

```bash
# Install the CLI tool with uv
uv sync

# Or install in development mode
pip install -e .

# Initialize a new project
projman init myproject --template python

# Check project status
projman status --verbose

# Build the project
projman build --format wheel --output dist/

# Deploy to staging
projman deploy --env staging --yes

# Show help
projman --help
projman build --help

# Use tab completion
projman build --[TAB]  # Shows options: --format, --output, --clean, etc.
```

## 📋 CLI Commands Reference

### projman init
```bash
Initialize a new project
Usage: projman init [OPTIONS] PROJECT_NAME

Options:
  --template TEXT    Project template [python|web|cli|data]
  --path TEXT        Custom directory path
  --git              Initialize git repository
  --virtual-env      Create virtual environment
  --help             Show help message
```

### projman status
```bash
Show project status and information
Usage: projman status [OPTIONS]

Options:
  --verbose          Show detailed information
  --json             Output in JSON format
  --watch            Watch for changes
  --help             Show help message
```

### projman build
```bash
Build the project
Usage: projman build [OPTIONS]

Options:
  --format TEXT      Build format [wheel|sdist|docker]
  --output TEXT      Output directory
  --clean            Clean build directory first
  --parallel         Parallel build
  --help             Show help message
```

### projman deploy
```bash
Deploy the project
Usage: projman deploy [OPTIONS]

Options:
  --env TEXT         Target environment [staging|production]
  --host TEXT        Remote host
  --yes             Skip confirmation prompts
  --rollback         Rollback to previous version
  --help             Show help message
```

## 🎨 Rich Terminal Examples

### Colored Output
```
✅ Project initialized successfully
⚠️  Configuration file missing, using defaults
❌ Build failed: missing dependencies
🔄 Deploying to production...
📊 Build statistics: 120 files, 45 MB
```

### Progress Bars
```
Building project: ████████████████ 100% [00:03]
Uploading files:  ██████████░░░░░░  60% [00:02]
Running tests:    ████████████████ 100% [00:15]
```

### Tables and Lists
```
Project Status
================================================
Name:        myproject
Type:        Python CLI Tool
Version:     1.0.0
Environment: development
Git:         clean (3 commits ahead)
Build:       ✓ passed (2 min ago)
Test:        ✓ 98% coverage
Deploy:      staged (v1.2.0)
================================================
```

### Tree View
```
myproject/
├── src/
│   ├── __init__.py
│   ├── main.py
│   └── utils.py
├── tests/
│   ├── test_main.py
│   └── test_utils.py
├── docs/
│   └── README.md
├── requirements.txt
├── setup.py
└── README.md (3 files, 2 directories)
```

## 📦 Modern Python Packaging with uv

### pyproject.toml Structure
```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "projman"
version = "1.0.0"
description = "Professional project management CLI tool"
readme = "README.md"
license = "MIT"
authors = [
    {name = "Your Name", email = "your.email@example.com"}
]
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "rich>=13.0.0",
    "requests>=2.28.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
    "black>=23.0.0",
    "pre-commit>=3.0.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "factory-boy>=3.2.0",
]

[project.scripts]
projman = "projman.cli:main"

[project.urls]
Homepage = "https://github.com/username/projman"
Documentation = "https://projman.readthedocs.io"
Repository = "https://github.com/username/projman.git"
Changelog = "https://github.com/username/projman/blob/main/CHANGELOG.md"

[tool.hatch.version]
path = "src/projman/__about__.py"

[tool.hatch.build.targets.sdist]
include = [
    "/src",
    "/tests",
    "pyproject.toml",
    "README.md",
]

[tool.hatch.build.targets.wheel]
packages = ["src/projman"]

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP"]

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "--cov=src/projman --cov-report=html --cov-report=term-missing"
```

### Development Workflow with uv
```bash
# Initialize project
uv init projman --python 3.11

# Add dependencies
uv add click rich requests pyyaml

# Add development dependencies
uv add --dev pytest pytest-cov ruff mypy black pre-commit

# Install dependencies
uv sync

# Run development scripts
uv run python -m projman.cli --help
uv run pytest tests/

# Build package
uv build

# Publish to PyPI
uv publish --token pypi-...
```

### Benefits of uv + pyproject.toml
- **Fast dependency resolution** - Much faster than pip
- **Lock files** - Reproducible builds
- **Modern standard** - Single source of truth for project metadata
- **Better caching** - Efficient package management
- **Python version management** - Integrated toolchain
## 🔧 Configuration System

### Config File Format (~/.projman/config.yaml)
```yaml
# Global projman configuration
default_template: python
default_git: true
default_virtual_env: true

build:
  default_format: wheel
  clean_before_build: true
  parallel_builds: 4

deploy:
  default_host: staging.example.com
  rollback_enabled: true
  health_check_url: /health

ui:
  colors: true
  progress_bars: true
  unicode_symbols: true
  table_style: grid

projects:
  myproject:
    template: python
    git_repo: git@github.com:user/myproject.git
    deploy_host: production.example.com
```

### Environment Variables
```bash
# Override config with environment variables
export PROJMAN_TEMPLATE=web
export PROJMAN_COLORS=false
export PROJMAN_PARALLEL_BUILDS=8
```

## 📋 Tab Completion

### Bash Completion
```bash
# Installation
scripts/completion.sh install bash

# Usage
projman [TAB]          # Shows: init, status, build, deploy, config
projman build --[TAB]   # Shows: --format, --output, --clean, etc.
projman deploy --[TAB]  # Shows: --env, --host, --yes, --rollback
```

### ZSH Completion
```bash
# Installation
scripts/completion.sh install zsh

# Usage with descriptions
projman [TAB]
init        Initialize new project
status      Show project status
build       Build project
deploy      Deploy project
config      Manage configuration
```

## 📦 Package Installation

### From Source
```bash
# Clone and install
git clone https://github.com/user/projman.git
cd projman
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### From PyPI
```bash
# Install from package index
pip install projman

# Install specific version
pip install projman==1.2.0
```

### System-wide Installation
```bash
# Installation script
sudo ./scripts/install.sh

# Manual installation
sudo python setup.py install
```

## 📚 Documentation and Help

### Built-in Help
```bash
# General help
projman --help

# Command-specific help
projman init --help
projman build --help

# Configuration help
projman config --help
```

### Man Page
```bash
# View man page
man projman

# Install man page
sudo cp docs/projman.1 /usr/share/man/man1/
sudo mandb
```

### Web Documentation
```bash
# Serve docs locally
mkdocs serve

# Build documentation
mkdocs build
```

## 🧪 Testing the CLI Tool

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_cli.py::test_init_command

# Test with coverage
pytest --cov=projman --cov-report=html

# Test CLI commands
python -m projman.cli --help
python -m projman.cli init test-project --dry-run

# Integration tests
pytest tests/integration/
```

## 🚀 Distribution and Release

### Building Packages
```bash
# Build source and wheel distributions
python -m build

# Build only wheel
python -m build --wheel
```

### Publishing to PyPI
```bash
# Upload to test PyPI
python -m twine upload --repository testpypi dist/*

# Upload to production PyPI
python -m twine upload dist/*
```

### Version Management
```bash
# Bump version
bump2version patch  # 1.2.0 -> 1.2.1
bump2version minor  # 1.2.0 -> 1.3.0
bump2version major  # 1.2.0 -> 2.0.0

# Create release tag
git tag -a v1.2.0 -m "Release version 1.2.0"
git push origin v1.2.0
```

## 🔧 Advanced CLI Design Patterns

### Command Chaining
```bash
# Chain multiple commands
projman init myapp && projman build && projman deploy --env staging

# Pipeline mode
git add . | projman build --from-stdin | projman deploy --env staging
```

### Plugin Architecture
```bash
# List available plugins
projman plugin list

# Install plugin
projman plugin install projman-docker

# Use plugin commands
projman docker build
projman docker run
```

### Remote Operations
```bash
# Remote project initialization
projman init --remote user@host:/opt/projects/myapp

# Remote deployment
projman deploy --host production.example.com --port 2222

# Sync with remote
projman sync --remote origin --push-only
```

## 🎯 Best Practices Demonstrated

- **User Experience**: Rich output, progress bars, helpful error messages
- **Extensibility**: Plugin system, hook architecture, configuration
- **Professional Quality**: Proper testing, documentation, packaging
- **Cross-platform**: Works on Linux, macOS, Windows
- **Standards Compliant**: Follows CLI best practices and conventions
- **Modern Tooling**: pyproject.toml, rich, pytest, type hints

## 🔧 Common CLI Development Issues

### Argument Parsing Issues
```bash
# Fix conflicting arguments
clippy "Resolve argparse conflicts between global and subcommand options"

# Handle complex validation
clippy "Add custom argument validation with clear error messages"
```

### Output Formatting Issues
```bash
# Fix terminal output issues
clippy "Fix rich output formatting for different terminal sizes"

# Handle color support
clippy "Implement proper color support detection and graceful fallback"
```

### Installation Issues
```bash
# Fix packaging problems
clippy "Resolve package installation and dependency issues"

# Fix entry point problems
clippy "Fix CLI entry point configuration in setup.py"
```

## 💡 Inspired By Popular CLI Tools

- **GitHub CLI**: Rich output, authentication, Git integration
- **Docker CLI**: Container operations, resource management
- **kubectl**: Complex resource management, configuration
- **pip**: Package management, dependency resolution
- **pytest**: Configuration, plugins, detailed output