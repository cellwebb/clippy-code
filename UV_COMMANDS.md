# UV Command Reference for CLIppy

Quick reference for common `uv` commands used in CLIppy development.

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

## Project Setup

```bash
# Clone and navigate to project
git clone https://github.com/yourusername/clippy.git
cd clippy

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# Install project in editable mode
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"
```

## Running CLIppy

```bash
# Run CLIppy directly (after uv tool install)
clippy "your task here"

# Run in development (from source)
python -m clippy "your task here"

# Interactive mode
python -m clippy -i

# With auto-approve (careful!)
python -m clippy -y "your task"
```

## Development Commands

### Running Tools

```bash
# Format code
uv run ruff format .

# Check formatting without changes
uv run ruff format --check .

# Lint code
uv run ruff check .

# Auto-fix linting issues
uv run ruff check --fix .

# Type checking
uv run mypy src/clippy
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest tests/test_permissions.py

# Run specific test
uv run pytest tests/test_permissions.py::test_default_permissions

# Run with coverage
uv run pytest --cov=clippy

# Generate HTML coverage report
uv run pytest --cov=clippy --cov-report=html

# Watch mode (requires pytest-watch)
uv run ptw
```

### Package Management

```bash
# Add a new dependency
uv pip install package-name
# Then manually add to pyproject.toml

# Add a dev dependency
uv pip install --dev package-name
# Then manually add to [project.optional-dependencies]

# Update all dependencies
uv pip install --upgrade -e ".[dev]"

# Show installed packages
uv pip list

# Show outdated packages
uv pip list --outdated
```

## Building and Publishing

```bash
# Build the package
uv build

# This creates:
# - dist/clippy_ai-0.1.0.tar.gz (source distribution)
# - dist/clippy_ai-0.1.0-py3-none-any.whl (wheel)

# Publish to TestPyPI (for testing)
uv publish --index-url https://test.pypi.org/simple/

# Publish to PyPI (production)
uv publish

# Install from TestPyPI to test
uv pip install --index-url https://test.pypi.org/simple/ clippy-ai
```

## Tools Installation

```bash
# Install CLIppy as a global tool
uv tool install clippy-ai

# Install from local source as tool
uv tool install .

# Update tool
uv tool upgrade clippy-ai

# Uninstall tool
uv tool uninstall clippy-ai

# List installed tools
uv tool list
```

## Python Version Management

```bash
# Install a specific Python version
uv python install 3.12

# List available Python versions
uv python list

# Use specific Python version for project
echo "3.12" > .python-version

# Create venv with specific version
uv venv --python 3.12
```

## Virtual Environment Management

```bash
# Create virtual environment
uv venv

# Create with specific name
uv venv my-venv

# Remove virtual environment
rm -rf .venv

# Activate (manual)
source .venv/bin/activate  # Unix/macOS
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

## Troubleshooting

```bash
# Clear uv cache
uv cache clean

# Reinstall all dependencies fresh
rm -rf .venv
uv venv
uv pip install -e ".[dev]"

# Check for issues
uv pip check

# Show dependency tree
uv pip tree

# Export requirements
uv pip freeze > requirements.txt
```

## Common Workflows

### Starting Development

```bash
git clone https://github.com/yourusername/clippy.git
cd clippy
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### Before Committing

```bash
uv run ruff format .
uv run ruff check --fix .
uv run mypy src/clippy
uv run pytest
```

### Creating a Release

```bash
# Update version in pyproject.toml
# Update CHANGELOG.md

git add .
git commit -m "chore: bump version to 0.2.0"
git tag v0.2.0
git push origin main
git push origin v0.2.0

uv build
uv publish
```

## Resources

- [uv Documentation](https://github.com/astral-sh/uv)
- [pyproject.toml spec](https://packaging.python.org/en/latest/specifications/pyproject-toml/)
- [Python Packaging Guide](https://packaging.python.org/)
