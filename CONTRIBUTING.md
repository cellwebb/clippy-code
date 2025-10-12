# Contributing to CLIppy

Thank you for your interest in contributing to CLIppy! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Modern Python package manager
- An Anthropic API key

### Getting Started

1. **Fork and clone the repository**

```bash
git clone https://github.com/yourusername/clippy.git
cd clippy
```

2. **Set up the development environment**

```bash
# Create a virtual environment
uv venv

# Activate it
source .venv/bin/activate  # Unix/macOS
# or
.venv\Scripts\activate     # Windows

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

3. **Set up your API key**

```bash
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

4. **Verify the setup**

```bash
# Run CLIppy in development mode
python -m clippy "list files in the current directory"
```

## Development Workflow

### Code Style

We use modern Python tooling:

- **ruff** for formatting and linting
- **mypy** for type checking
- **pytest** for testing

```bash
# Format your code
uv run ruff format .

# Check for linting issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Type check
uv run mypy src/clippy
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=clippy --cov-report=html

# Run specific test file
uv run pytest tests/test_permissions.py

# Run with verbose output
uv run pytest -v
```

### Making Changes

1. **Create a new branch**

```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**

- Write clean, documented code
- Add type hints to all functions
- Follow the existing code style
- Add docstrings to public functions and classes

3. **Test your changes**

```bash
# Run tests
uv run pytest

# Test the CLI manually
python -m clippy -i
```

4. **Commit your changes**

```bash
git add .
git commit -m "feat: add your feature description"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

5. **Push and create a pull request**

```bash
git push origin feature/your-feature-name
```

Then open a pull request on GitHub.

## Project Structure

```
clippy/
├── src/clippy/          # Main package source
│   ├── __init__.py      # Package initialization
│   ├── __main__.py      # CLI entry point
│   ├── agent.py         # AI agent implementation
│   ├── cli.py           # CLI interface
│   ├── executor.py      # Action execution engine
│   ├── permissions.py   # Permission system
│   └── tools.py         # Tool definitions
├── tests/               # Test suite (to be added)
├── docs/                # Additional documentation (to be added)
├── pyproject.toml       # Project configuration
├── LICENSE              # MIT License
├── README.md            # Project overview
├── QUICKSTART.md        # Quick start guide
└── CONTRIBUTING.md      # This file
```

## Adding New Features

### Adding a New Tool

1. Define the tool in `src/clippy/tools.py`:

```python
{
    "name": "your_tool",
    "description": "What your tool does",
    "input_schema": {
        "type": "object",
        "properties": {
            "param": {
                "type": "string",
                "description": "Parameter description"
            }
        },
        "required": ["param"]
    }
}
```

2. Add the action type in `src/clippy/permissions.py`:

```python
class ActionType(str, Enum):
    YOUR_TOOL = "your_tool"
```

3. Implement the executor in `src/clippy/executor.py`:

```python
def _your_tool(self, param: str) -> tuple[bool, str, Any]:
    """Execute your tool."""
    # Implementation here
    return True, "Success message", result
```

4. Update the action map in `src/clippy/agent.py`

5. Add tests for your tool

### Adding New Permissions

Modify `src/clippy/permissions.py` to add new permission levels or action types.

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Mock external API calls (Anthropic API)

Example test structure:

```python
def test_permission_check():
    """Test permission checking logic."""
    manager = PermissionManager()
    level = manager.check_permission(ActionType.READ_FILE)
    assert level == PermissionLevel.AUTO_APPROVE
```

## Documentation

- Update README.md for user-facing changes
- Update QUICKSTART.md for new workflows
- Add docstrings to all public functions
- Update type hints

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md (when we add it)
3. Create a git tag: `git tag v0.2.0`
4. Push the tag: `git push origin v0.2.0`
5. Build and publish:

```bash
uv build
uv publish
```

## Getting Help

- Open an issue on GitHub
- Join discussions in the repository
- Read the documentation

## Code of Conduct

- Be respectful and inclusive
- Provide constructive feedback
- Focus on what is best for the community
- Show empathy towards others

## License

By contributing to CLIppy, you agree that your contributions will be licensed under the MIT License.
