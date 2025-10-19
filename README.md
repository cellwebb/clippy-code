# clippy-code 👀📎

[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue.svg)](https://www.python.org/downloads/)
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

# Groq
echo "GROQ_API_KEY=your_api_key_here" > .env

# For local models like Ollama, you typically don't need an API key
# Just set the base URL:
export OPENAI_BASE_URL=http://localhost:11434/v1
```

### MCP Configuration

clippy-code can dynamically discover and use tools from MCP (Model Context Protocol) servers. MCP enables external services to expose tools that can be used by the agent without requiring changes to the core codebase.

To use MCP servers, create an `mcp.json` configuration file in your project root or home directory:

```json
{
  "mcp_servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    },
    "perplexity-ask": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }
    }
  }
}
```

See [MCP_DOCUMENTATION.md](MCP_DOCUMENTATION.md) for detailed information about MCP configuration and usage.

MCP tools will automatically be available in interactive and document modes, with appropriate approval prompts to maintain safety.

clippy-code supports multiple LLM providers through OpenAI-compatible APIs:

```bash
# OpenAI (default)
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Cerebras
echo "CEREBRAS_API_KEY=your_api_key_here" > .env

# Groq
echo "GROQ_API_KEY=your_api_key_here" > .env

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

- read_file, list_directory, search_files, get_file_info, grep, read_files

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
- `a` or `allow` - Approve and auto-approve this action type for the session

### Slash Commands (Interactive/Document Mode)

- `/reset`, `/clear`, `/new` - Reset conversation history
- `/status` - Show token usage and session info
- `/compact` - Summarize conversation to reduce context usage
- `/model list` - Show available models
- `/model <name>` - Switch model/provider
- `/auto list` - List auto-approved actions
- `/auto revoke <action>` - Revoke auto-approval for an action
- `/auto clear` - Clear all auto-approvals
- `/mcp list` - List configured MCP servers
- `/mcp tools [server]` - List tools available from MCP servers
- `/mcp refresh` - Refresh tool catalogs from MCP servers
- `/mcp allow <server>` - Mark an MCP server as trusted for this session
- `/mcp revoke <server>` - Revoke trust for an MCP server
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

## Configuration & Models

### Environment Variables

- `CLIPPY_MODEL` - Model identifier (default: gpt-5)
- `OPENAI_BASE_URL` - Base URL for alternate providers
- Provider-specific API keys: `OPENAI_API_KEY`, `CEREBRAS_API_KEY`, etc.

### Available Models

**OpenAI**: gpt-4o (default), gpt-4o-mini, gpt-5

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

For detailed information about MCP integration, see [MCP_DOCUMENTATION.md](docs/MCP_DOCUMENTATION.md).

clippy-code can dynamically discover and use tools from MCP (Model Context Protocol) servers. MCP enables external services to expose tools that can be used by the agent without requiring changes to the core codebase.

To use MCP servers, create an `mcp.json` configuration file in your home directory (`~/.clippy/mcp.json`), project directory, or specify via `CLIPPY_MCP_CONFIG` environment variable:

```json
{
  "mcp_servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    },
    "perplexity-ask": {
      "command": "npx",
      "args": ["-y", "server-perplexity-ask"],
      "env": { "PERPLEXITY_API_KEY": "${PERPLEXITY_API_KEY}" }
    }
  }
}
```

MCP tools will automatically be available in interactive and document modes, with appropriate approval prompts to maintain safety.

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

Tools follow a declarative pattern with four components:

1. **Definition & Implementation** (`tools/your_tool.py`): Co-located schema and implementation
2. **Catalog Integration** (`tools/catalog.py`): Tool gets automatically included
3. **Permission** (`permissions.py`): Add to `ActionType` enum and permission config
4. **Execution** (`executor.py`): Implement method returning `tuple[bool, str, Any]`

The steps are:

1. Create a tool file in `src/clippy/tools/` (e.g., `your_tool.py`) with:
   - `TOOL_SCHEMA` constant defining the tool's JSON schema
   - Implementation function (e.g., `def your_tool(...) -> tuple[bool, str, Any]`)
2. Add the tool export to `src/clippy/tools/__init__.py`
3. Add the action type in `src/clippy/permissions.py`
4. Add the tool execution to `src/clippy/executor.py`
5. Add the tool to the action maps in `src/clippy/agent/tool_handler.py`
6. Add tests for your tool in `tests/tools/test_your_tool.py`

The tool catalog (`tools/catalog.py`) automatically discovers and includes all tools from the tools module.

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

**UI/UX Design**:

- Multiple interface modes for different workflows
- Textual-based TUI with custom styling
- Intuitive command system and user workflows

**Product Thinking**:

- Safety controls with user approval systems
- Maintainable and extensible design patterns
- Developer productivity focus

---

Made with ❤️ by the clippy-code team
