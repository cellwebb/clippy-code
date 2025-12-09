.PHONY: help install dev clean run test test-cov cov cov-term format lint type-check check all bump bump-patch bump-minor bump-major

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
	@echo "  make test-cov     Run tests with coverage report"
	@echo "  make cov          Show coverage report in browser"
	@echo "  make cov-term     Show coverage report in terminal"
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
	@echo "  make bump-patch   Bump patch version (0.1.0 -> 0.1.1) and create git tag"
	@echo "  make bump-minor   Bump minor version (0.1.0 -> 0.2.0) and create git tag"
	@echo "  make bump-major   Bump major version (0.1.0 -> 1.0.0) and create git tag"

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
	uv run pytest -q

test-cov:
	uv run pytest -q --cov=clippy --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

cov:
	@if [ -f htmlcov/index.html ]; then \
		echo "Coverage report available at: $$(pwd)/htmlcov/index.html"; \
		echo "Opening coverage report..."; \
		uv run python -c "import webbrowser; webbrowser.open('htmlcov/index.html')" 2>/dev/null || echo "Open the file manually: $$(pwd)/htmlcov/index.html"; \
	else \
		echo "No coverage report found. Run 'make test-cov' first to generate coverage data."; \
	fi

cov-term:
	@if [ -f .coverage ]; then \
		echo "Coverage report (terminal):"; \
		uv run python -c "import coverage; cov = coverage.Coverage(); cov.load(); cov.report()" 2>/dev/null || echo "Run 'make test-cov' to generate coverage data."; \
	else \
		echo "No coverage data found. Run 'make test-cov' first to generate coverage data."; \
	fi

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

# Version bumping
bump:
	@# Check for uncommitted changes before starting
	@if [ -n "$$(git status --porcelain)" ]; then \
		echo "Error: Git working directory is not clean"; \
		echo "Please commit or stash your changes first"; \
		git status --short; \
		exit 1; \
	fi
	@echo "Bumping $(VERSION) version..."
	@RESULT=$$(BUMP_KIND=$(VERSION) python -c "import os, re; from pathlib import Path; version_file = Path('src/clippy/__version__.py'); content = version_file.read_text(encoding='utf-8'); match = re.search(r'__version__ = \"([^\"]+)\"', content); old_version = match.group(1); parts = old_version.split('.'); major, minor, patch = map(int, parts); kind = os.environ['BUMP_KIND']; new_version = f'{major}.{minor}.{patch + 1}' if kind == 'patch' else f'{major}.{minor + 1}.0' if kind == 'minor' else f'{major + 1}.0.0'; version_file.write_text(content.replace(f'__version__ = \"{old_version}\"', f'__version__ = \"{new_version}\"', 1), encoding='utf-8'); print(old_version, new_version)") && \
	OLD_VERSION=$$(echo "$$RESULT" | awk '{print $$1}') && \
	NEW_VERSION=$$(echo "$$RESULT" | awk '{print $$2}') && \
	echo "Version bumped from $$OLD_VERSION to $$NEW_VERSION" && \
	uvx kittylog release $$NEW_VERSION --audience users --include-diff && \
	git add -A && \
	git commit -m "chore(version): bump version from $$OLD_VERSION to $$NEW_VERSION" && \
	git tag -a "v$$NEW_VERSION" -m "Release version $$NEW_VERSION" && \
	echo "✅ Created tag v$$NEW_VERSION" && \
	echo "📦 To publish: git push && git push --tags"

bump-patch: VERSION=patch
bump-patch: bump

bump-minor: VERSION=minor
bump-minor: bump

bump-major: VERSION=major
bump-major: bump