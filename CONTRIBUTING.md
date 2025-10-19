# Contributing to clippy-code

Thank you for your interest in contributing to clippy-code! This guide will help you get started.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) - Modern Python package manager
- An OpenAI-compatible API key (OpenAI, Cerebras, Together AI, Groq, DeepSeek, etc.)

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

For OpenAI (default provider):

```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

For other providers:

```bash
# Cerebras
echo "CEREBRAS_API_KEY=your_key_here" > .env

# Together AI
echo "TOGETHER_API_KEY=your_key_here" > .env

# Groq
echo "GROQ_API_KEY=your_key_here" > .env

# DeepSeek
echo "DEEPSEEK_API_KEY=your_key_here" > .env
```

4. **Verify the setup**

```bash
# Run clippy-code in development mode
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
src/clippy/
├── cli/
│   ├── main.py         # Main entry point
│   ├── parser.py       # Argument parsing
│   ├── oneshot.py      # One-shot mode implementation
│   └── repl.py         # Interactive REPL mode
├── agent/
│   ├── core.py         # Core agent implementation
│   ├── loop.py         # Agent loop logic
│   ├── conversation.py # Conversation utilities
│   └── tool_handler.py # Tool calling handler
├── mcp/                # MCP (Model Context Protocol) integration
│   ├── __init__.py
│   ├── config.py       # MCP configuration loading
│   ├── errors.py       # MCP error handling
│   ├── manager.py      # MCP server connection manager
│   ├── naming.py       # MCP tool naming utilities
│   ├── schema.py       # MCP schema conversion
│   ├── transports.py   # MCP transport layer
│   ├── trust.py        # MCP trust system
│   └── types.py        # MCP type definitions
├── tools/
│   ├── __init__.py     # Tool implementations and exports
│   ├── catalog.py      # Tool catalog for merging built-in and MCP tools
│   ├── create_directory.py
│   ├── delete_file.py
│   ├── edit_file.py
│   ├── execute_command.py
│   ├── get_file_info.py
│   ├── grep.py
│   ├── list_directory.py
│   ├── read_file.py
│   ├── read_files.py
│   ├── search_files.py
│   └── write_file.py
├── ui/
|   ├── document_app.py # Textual-based document mode interface
|   ├── styles.py       # CSS styling for document mode
|   ├── widgets.py      # Custom UI widgets
|   └── utils.py        # UI utility functions
├── providers.py     # OpenAI-compatible LLM provider (~100 lines)
├── executor.py      # Tool execution implementations
├── permissions.py   # Permission system (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
├── models.py        # Model configuration loading and presets
├── models.yaml      # Model presets for different providers
├── prompts.py       # System prompts for the agent
└── diff_utils.py    # Diff generation utilities
```

## Adding New Features

### Adding a New Tool

1. Create a new tool implementation file in `src/clippy/tools/`:

```python
# src/clippy/tools/your_tool.py
from typing import Any

TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "your_tool",
        "description": "What your tool does",
        "parameters": {
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
}

def your_tool(param: str) -> tuple[bool, str, Any]:
    """Execute your tool.

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    # Implementation here
    return True, "Success message", result
```

2. Add the tool to `src/clippy/tools/__init__.py`:

```python
from .your_tool import your_tool, TOOL_SCHEMA as YOUR_TOOL_SCHEMA

__all__ = [
    # existing tools...
    "your_tool",
]

TOOLS: list[dict[str, Any]] = [
    # existing tools...
    YOUR_TOOL_SCHEMA,
]
```

The tool catalog (`tools/catalog.py`) automatically discovers and includes all tools from the tools module.

4. Add the action type in `src/clippy/permissions.py`:

```python
class ActionType(str, Enum):
    # existing actions...
    YOUR_TOOL = "your_tool"

# In PermissionConfig class
class PermissionConfig(BaseModel):
    auto_approve: set[ActionType] = {
        # existing auto-approved actions...
    }
    require_approval: set[ActionType] = {
        # existing require approval actions...
        ActionType.YOUR_TOOL,
    }
```

5. Add the tool execution to `src/clippy/executor.py`:

```python
# In execute method
if tool_name == "your_tool":
    return your_tool(tool_input["param"])
```

6. Add tests for your tool in `tests/tools/test_your_tool.py`

### Adding New Permissions

Modify `src/clippy/permissions.py` to add new permission levels or action types.

## Testing Guidelines

- Write tests for all new features
- Maintain or improve code coverage
- Test edge cases and error conditions
- Mock external API calls

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

1. Update version in `pyproject.toml` and `src/clippy/__version__.py`
2. Update CHANGELOG.md (when we add it)
3. Create a git tag: `git tag v1.2.1`
4. Push the tag: `git push origin v1.2.1`
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

By contributing to clippy-code, you agree that your contributions will be licensed under the MIT License.
