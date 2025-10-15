# clippy-code 📎

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

> A production-ready, model-agnostic CLI coding agent with safety-first design

clippy-code is an AI-powered development assistant that works with any OpenAI-compatible API provider. It features robust permission controls, streaming responses, and multiple interface modes for different workflows.

## Quick Start

### Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install clippy-code from PyPI
uv tool install clippy-code

# Or install from source
git clone https://github.com/yourusername/clippy.git
cd clippy
uv pip install -e .
```

### Setup API Keys

clippy-code supports multiple LLM providers through OpenAI-compatible APIs:

```bash
# OpenAI (default)
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Cerebras
echo "CEREBRAS_API_KEY=your_api_key_here" > .env

# For local models like Ollama, you typically don't need an API key
# Just set the base URL:
export OPENAI_BASE_URL=http://localhost:11434/v1
```

### Basic Usage

```bash
# One-shot mode - execute a single task
clippy "create a hello world python script"

# Interactive mode - REPL-style conversations
clippy -i

# Document mode - Word-inspired TUI interface
clippy -d

# Specify a model
clippy --model gpt-5 "refactor main.py to use async/await"

# Auto-approve all actions (use with caution!)
clippy -y "write unit tests for utils.py"
```

## Features

### Three Interface Modes

1. **One-shot mode**: `clippy "your task"` - Execute single task and exit
2. **Interactive mode**: `clippy -i` - REPL-style multi-turn conversations with slash commands
3. **Document mode**: `clippy -d` - Word-inspired TUI with toolbar buttons

### Permission System

clippy-code implements safety-first design with a three-tier permission system:

**Auto-approved actions** (read-only operations):

- read_file, list_directory, search_files, get_file_info, grep

**Require approval** (potentially destructive operations):

- write_file, delete_file, create_directory, execute_command, edit_file

**Blocked actions** (currently empty but configurable)

When clippy-code wants to perform a risky action, you'll see a prompt:

```
→ write_file
  path: example.py
  content: print("Hello, World!")

[?] Approve this action? [y/N/stop]:
```

Options:

- `y` - Approve and execute
- `N` - Reject (default)
- `stop` - Stop execution entirely

### Slash Commands (Interactive/Document Mode)

- `/reset`, `/clear`, `/new` - Reset conversation history
- `/status` - Show token usage and session info
- `/compact` - Summarize conversation to reduce context usage
- `/model list` - Show available models
- `/model <name>` - Switch model/provider
- `/help` - Show help message
- `/exit`, `/quit` - Exit clippy-code

### Supported Providers

Works with any OpenAI-compatible API out of the box:

- OpenAI
- Cerebras
- Together AI
- Ollama
- Groq
- DeepSeek
- Azure OpenAI
- llama.cpp
- vLLM

Switch providers with the `/model` command or CLI arguments.

## Architecture Overview

### System Architecture

clippy-code follows a layered architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────┐
│                   CLI Layer                         │
│  (Argument Parsing, User Interaction, Display)      │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                  Agent Layer                        │
│  (Conversation Management, Response Processing)     │
└─────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│               Tool System                           │
│  (Tool Definitions, Execution, Permissions)        │
└─────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│               Provider Layer                        │
│  (OpenAI-compatible API Abstraction)               │
└─────────────────────────────────────────────────────┘
```

### Core Components

```
src/clippy/
├── cli.py           # CLI entry point, argument parsing
├── agent.py         # Core agent loop (max 25 iterations)
├── providers.py     # OpenAI-compatible LLM provider with retry logic
├── tools.py         # Tool definitions (JSON schemas)
├── executor.py      # Tool execution implementations
├── permissions.py   # Permission system (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
├── models.py        # Model configuration loading and presets
├── models.yaml      # Model presets for different providers
└── document_ui.py   # Textual-based document mode interface
```

## Configuration & Models

### Environment Variables

- `CLIPPY_MODEL` - Model identifier (default: gpt-5)
- `OPENAI_BASE_URL` - Base URL for alternate providers
- Provider-specific API keys: `OPENAI_API_KEY`, `CEREBRAS_API_KEY`, etc.

### Available Models

**OpenAI**: gpt-5 (default), gpt-4-turbo, gpt-4, gpt-3.5-turbo

**Cerebras**: cerebras (default), qwen-3-coder-480b

**Ollama**: ollama (default), ollama-codellama, ollama-mistral, ollama-qwen

**Together AI**: together-llama-8b (default), together-llama-70b

**Groq**: groq (default), groq-mixtral

**DeepSeek**: deepseek (default), deepseek-chat

See all available models with `/model list` in interactive mode.

## Development Workflow

### Setting Up Development Environment

```bash
# Clone and enter repository
git clone https://github.com/yourusername/clippy.git
cd clippy

# Create virtual environment with uv
uv venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in editable mode with dev dependencies
uv pip install -e ".[dev]"

# Run clippy in development
python -m clippy
```

### Code Quality Tools

```bash
# Auto-format code
uv run ruff format .

# Lint and check for issues
uv run ruff check .

# Fix auto-fixable issues
uv run ruff check --fix .

# Type checking
uv run mypy src/clippy
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage reporting
uv run pytest --cov=clippy --cov-report=html

# Run specific test file
uv run pytest tests/test_permissions.py
```

Testing philosophy:

- Unit tests for individual components
- Integration tests for workflows
- Mock external APIs for reliability
- Aim for >80% code coverage

### Available Tools

clippy-code has access to these tools:

| Tool               | Description                                       | Auto-Approved |
| ------------------ | ------------------------------------------------- | ------------- |
| `read_file`        | Read file contents                                | ✅            |
| `write_file`       | Write/modify entire files                         | ❌            |
| `delete_file`      | Delete files                                      | ❌            |
| `list_directory`   | List directory contents                           | ✅            |
| `create_directory` | Create directories                                | ❌            |
| `execute_command`  | Run shell commands                                | ❌            |
| `search_files`     | Search with glob patterns                         | ✅            |
| `get_file_info`    | Get file metadata                                 | ✅            |
| `read_files`       | Read multiple files at once                       | ✅            |
| `grep`             | Search patterns in files                          | ✅            |
| `edit_file`        | Edit files by line (insert/replace/delete/append) | ❌            |

## Design Principles

- **OpenAI Compatibility**: Single standard API format works with any OpenAI-compatible provider
- **Safety First**: Three-tier permission system with user approval workflows
- **Type Safety**: Fully typed Python codebase with MyPy checking
- **Clean Code**: SOLID principles, modular design, Google-style docstrings
- **Streaming Responses**: Real-time output for immediate feedback
- **Error Handling**: Retry logic with exponential backoff, graceful degradation

## Extensibility

### Adding New LLM Providers

clippy-code works with any OpenAI-compatible API provider. Add new providers by updating `models.yaml`:

```yaml
provider_name:
  base_url: https://api.provider.com/v1
  api_key_env: PROVIDER_API_KEY
  default_model: provider-default
  models:
    provider-default:
      model_id: provider-model-name
      description: Provider Model Description
```

### Adding New Tools

Tools follow a declarative pattern with three components:

1. **Definition** (`tools.py`): JSON schema in OpenAI format
2. **Permission** (`permissions.py`): Add to `ActionType` enum and permission config
3. **Execution** (`executor.py`): Implement method returning `tuple[bool, str, Any]`

Add to `action_map` in both `agent.py:_handle_tool_use()` and `executor.py:execute()` methods.

## Skills Demonstrated

This project showcases proficiency in:

**Software Engineering**:

- SOLID principles and clean architecture
- Dependency injection and separation of concerns
- API design with intuitive interfaces

**Python Development**:

- Modern Python features (type hints, dataclasses, enums)
- Packaging with pyproject.toml and optional dependencies
- CLI development with argparse, prompt_toolkit, rich

**System Design**:

- Layered architecture with clear module boundaries
- Error handling and graceful degradation
- Configuration management (environment, CLI, defaults)

**Product Thinking**:

- Multiple interface modes for different workflows
- Safety controls with user approval systems
- Maintainable and extensible design patterns

---

**Note**: This is a portfolio project demonstrating software engineering best practices while being functional for end-users.
