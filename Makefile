.PHONY: help install dev clean run test cov format lint type-check check all bump-patch bump-minor bump-major

# Python interpreter (can be overridden with: make PYTHON=python3.12 bump-patch)
PYTHON ?= python3

# Default target
help:
	@echo "clippy-code Development Commands"
	@echo ""
	@echo "Setup:"
	@echo "  make install      Install package in editable mode"
	@echo "  make dev          Install with dev dependencies"
	@echo "  make clean        Remove build artifacts and caches"
	@echo ""
	@echo "Running:"
	@echo "  make run          Run clippy-code in interactive mode"
	@echo ""
	@echo "Testing:"
	@echo "  make test         Run tests with pytest"
	@echo "  make cov          Run tests with coverage report"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format       Autofix and format code with ruff"
	@echo "  make lint         Lint code with ruff"
	@echo "  make type-check   Run type checking with mypy"
	@echo "  make check        Run all checks (format, lint, type-check)"
	@echo ""
	@echo "Development:"
	@echo "  make all          Run all checks and tests"
	@echo "  make build        Build package distributions"
	@echo "  make publish      Publish to PyPI"
	@echo ""
	@echo "Version Management:"
	@echo "  make bump-patch   Bump patch version (0.1.0 -> 0.1.1)"
	@echo "  make bump-minor   Bump minor version (0.1.0 -> 0.2.0)"
	@echo "  make bump-major   Bump major version (0.1.0 -> 1.0.0)"

# Installation
install:
	uv pip install -e .

dev:
	uv pip install -e ".[dev]"

# Cleaning
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Running
run:
	@$(PYTHON) -m clippy

# Testing
test:
	uv run pytest -v

cov:
	uv run pytest --cov=clippy --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Code quality
format:
	uv run ruff check . --fix
	uv run ruff format .

lint:
	uv run ruff check .

type-check:
	uv run mypy src/clippy

# Combined checks
check: format lint type-check
	@echo ""
	@echo "✓ All checks passed!"

# Run everything
all: check test
	@echo ""
	@echo "✓ All checks and tests passed!"

# Building and publishing
build:
	uv build

publish: build
	uv publish

# Quick development cycle
watch-test:
	uv run ptw

# Show installed packages
list:
	uv pip list

# Update dependencies
update:
	uv pip install --upgrade -e ".[dev]"

# Version management
bump-patch:
	@echo "Bumping patch version..."
	@$(PYTHON) -c "import re; \
	content = open('pyproject.toml').read(); \
	match = re.search(r'version = \"(\d+)\.(\d+)\.(\d+)\"', content); \
	major, minor, patch = match.groups(); \
	new_version = f'{major}.{minor}.{int(patch)+1}'; \
	new_content = re.sub(r'version = \"\d+\.\d+\.\d+\"', f'version = \"{new_version}\"', content); \
	open('pyproject.toml', 'w').write(new_content); \
	version_content = open('src/clippy/__version__.py').read(); \
	new_version_content = re.sub(r'__version__ = \"\d+\.\d+\.\d+\"', f'__version__ = \"{new_version}\"', version_content); \
	open('src/clippy/__version__.py', 'w').write(new_version_content); \
	print(f'Version bumped to {new_version}')"
	@echo "Updating uv.lock file..."
	@uv lock

bump-minor:
	@echo "Bumping minor version..."
	@$(PYTHON) -c "import re; \
	content = open('pyproject.toml').read(); \
	match = re.search(r'version = \"(\d+)\.(\d+)\.(\d+)\"', content); \
	major, minor, patch = match.groups(); \
	new_version = f'{major}.{int(minor)+1}.0'; \
	new_content = re.sub(r'version = \"\d+\.\d+\.\d+\"', f'version = \"{new_version}\"', content); \
	open('pyproject.toml', 'w').write(new_content); \
	version_content = open('src/clippy/__version__.py').read(); \
	new_version_content = re.sub(r'__version__ = \"\d+\.\d+\.\d+\"', f'__version__ = \"{new_version}\"', version_content); \
	open('src/clippy/__version__.py', 'w').write(new_version_content); \
	print(f'Version bumped to {new_version}')"
	@echo "Updating uv.lock file..."
	@uv lock

bump-major:
	@echo "Bumping major version..."
	@$(PYTHON) -c "import re; \
	content = open('pyproject.toml').read(); \
	match = re.search(r'version = \"(\d+)\.(\d+)\.(\d+)\"', content); \
	major, minor, patch = match.groups(); \
	new_version = f'{int(major)+1}.0.0'; \
	new_content = re.sub(r'version = \"\d+\.\d+\.\d+\"', f'version = \"{new_version}\"', content); \
	open('pyproject.toml', 'w').write(new_content); \
	version_content = open('src/clippy/__version__.py').read(); \
	new_version_content = re.sub(r'__version__ = \"\d+\.\d+\.\d+\"', f'__version__ = \"{new_version}\"', version_content); \
	open('src/clippy/__version__.py', 'w').write(new_version_content); \
	print(f'Version bumped to {new_version}')"
	@echo "Updating uv.lock file..."
	@uv lock
	print(f'Version bumped to {new_version}')"
