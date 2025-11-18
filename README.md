# clippy-code 👀📎

[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

> A production-ready, model-agnostic CLI coding agent with safety-first design

clippy-code is an AI-powered development assistant that works with any OpenAI-compatible API provider. It features robust permission controls, streaming responses, and multiple interface modes for different workflows.

## 🚀 Quick Start

### Installation

#### Option 1: UVX (Recommended - Run Without Installation)

```bash
# Run directly without installation
uvx clippy-code "create a hello world python script"

# Start interactive mode
uvx clippy-code

# Note: First run may be slower as it downloads and caches the tool
```

#### Option 2: UV Tool Install

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install clippy-code from PyPI
uv tool install clippy-code
```

### Setup API Keys

clippy-code supports multiple LLM providers through OpenAI-compatible APIs:

```bash
# OpenAI (default)
echo "OPENAI_API_KEY=your_api_key_here" > .env

# Or choose from many supported providers:
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
echo "MISTRAL_API_KEY=your_api_key_here" > .env
echo "CEREBRAS_API_KEY=your_api_key_here" > .env
echo "GROQ_API_KEY=your_api_key_here" > .env
```

### Basic Usage

```bash
# One-shot mode - execute a single task
clippy "create a hello world python script"

# Interactive mode - REPL-style conversations
clippy

# Specify a model
clippy --model gpt-4 "refactor main.py to use async/await"

# Auto-approve all actions (use with caution!)
clippy -y "write unit tests for utils.py"
```

## 🔧 MCP Integration (Optional)

clippy-code can dynamically discover and use tools from MCP (Model Context Protocol) servers. To use MCP servers, create an `mcp.json` configuration file:

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

MCP tools will automatically be available in interactive mode, with appropriate approval prompts to maintain safety.

## Key Features

### 🌐 **Supported Providers**

- **Anthropic** • **Chutes** • **Cerebras** • **Gemini** • **Groq** • **LM Studio** • **MiniMax**
- **Mistral** • **Ollama** • **OpenAI** • **OpenRouter** • **Synthetic.new** • **Together AI** • **Z.AI**

### 🛡️ **Safety-First Design**

- **Three-tier permissions**: Auto-approve read operations, require confirmation for writes, and block destructive actions
- **Interactive approval flow**: Clear prompts showing exact changes before execution with yes/no/allow-all options
- **Session-based trust**: Grant temporary auto-approval for specific actions without compromising safety
- **MCP server trust system**: Explicit approval required before external tools can access your codebase

### 🔧 **Flexible Interface Modes**

- **One-shot mode**: Execute single tasks and exit (`clippy "create a script"`)
- **Interactive REPL**: Multi-turn conversations with slash commands for model switching, context management, and permission control
- **Document mode**: Microsoft Word-like TUI interface for a richer development experience (`clippy -d`)

### 🤖 **Advanced Agent Capabilities**

- **Streaming responses**: Real-time output with progress indicators for immediate feedback
- **Context management**: Automatic conversation compaction to stay within token limits while preserving important history
- **Dynamic model switching**: Change providers and models mid-conversation without losing context
- **Subagent delegation**: Spawn specialized agents for focused tasks (code review, testing, refactoring) with isolated contexts

### 🔌 **Extensible Tool System**

- **Built-in file operations**: Read, write, edit, search with glob patterns and grep-like content search
- **Command execution**: Run shell commands with configurable timeouts and output capture
- **MCP integration**: Dynamically discover and use tools from external Model Context Protocol servers
- **Easy tool development**: Add new capabilities with simple declarative schemas and type-safe implementations

### 💻 **Developer Experience**

- **Production-ready**: Comprehensive error handling with retry logic, exponential backoff, and graceful degradation
- **Type-safe codebase**: Full MyPy type checking for reliability and IDE support
- **Rich CLI**: Syntax highlighting, progress spinners, and formatted output using rich and prompt_toolkit
- **Flexible configuration**: Environment files, CLI arguments, and saved model configurations for any workflow

## Architecture Overview

### System Architecture

clippy-code follows a layered architecture with clear separation of concerns:

```text
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
│  (Tool Definitions, Execution, Permissions)         │
└─────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│               Provider Layer                        │
│  (OpenAI-compatible API Abstraction)                │
└─────────────────────────────────────────────────────┘
```

### Core Components

```text
src/clippy/
├── agent/
│   ├── core.py                 # Core agent implementation
│   ├── loop.py                 # Agent loop logic
│   ├── conversation.py         # Conversation utilities
│   ├── tool_handler.py         # Tool calling handler
│   ├── subagent.py             # Subagent implementation
│   ├── subagent_manager.py     # Subagent lifecycle management
│   ├── subagent_types.py       # Subagent type configurations
│   ├── subagent_cache.py       # Result caching system
│   ├── subagent_chainer.py     # Hierarchical execution chaining
│   ├── subagent_config_manager.py # Subagent configuration management
│   ├── utils.py                # Agent helper utilities
│   └── errors.py               # Agent-specific exceptions
├── cli/
│   ├── completion.py           # Command completion utilities
│   ├── commands.py             # High-level CLI commands
│   ├── main.py                 # Main entry point
│   ├── oneshot.py              # One-shot mode implementation
│   ├── parser.py               # Argument parsing
│   ├── repl.py                 # Interactive REPL mode
│   └── setup.py                # Initial setup helpers
├── tools/
│   ├── __init__.py             # Tool registrations
│   ├── catalog.py              # Tool catalog for built-in and MCP tools
│   ├── create_directory.py
│   ├── delete_file.py
│   ├── delegate_to_subagent.py
│   ├── edit_file.py
│   ├── execute_command.py
│   ├── get_file_info.py
│   ├── grep.py
│   ├── list_directory.py
│   ├── read_file.py
│   ├── read_files.py
│   ├── run_parallel_subagents.py
│   ├── search_files.py
│   └── write_file.py
├── mcp/
│   ├── config.py               # MCP configuration loading
│   ├── errors.py               # MCP error handling
│   ├── manager.py              # MCP server connection manager
│   ├── naming.py               # MCP tool naming utilities
│   ├── schema.py               # MCP schema conversion
│   ├── transports.py           # MCP transport layer
│   ├── trust.py                # MCP trust system
│   └── types.py                # MCP type definitions
├── diff_utils.py               # Diff generation utilities
├── executor.py                 # Tool execution implementations
├── models.py                   # Model configuration loading and management
├── permissions.py              # Permission system (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
├── prompts.py                  # System prompts for the agent
├── providers.py                # OpenAI-compatible LLM provider
├── providers.yaml              # Provider preset definitions
├── __main__.py                 # Module entry point
└── __version__.py              # Version helper
```

## Configuration & Models

### Environment Variables

- Provider-specific API keys: `ANTHROPIC_API_KEY`, `CHUTES_API_KEY`, `CEREBRAS_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`, `OPENAI_API_KEY`, etc.
- `OPENAI_BASE_URL` - Optional base URL override

### Provider-Based Model System

clippy-code uses a flexible provider-based system. Instead of maintaining a fixed list of models, you:

1. **Choose from available providers** (defined in `providers.yaml`): Anthropic, Chutes, Cerebras, Gemini, Groq, LM Studio, MiniMax, Mistral, Ollama, OpenAI, OpenRouter, Synthetic, Together AI, Z.AI
2. **Save your favorite model configurations** using `/model add`
3. **Switch between saved models** anytime with `/model <name>`

The default model is **GPT-5** from OpenAI.

#### Managing Models

```bash
# List your saved models
/model list

# Try a model without saving
/model use cerebras qwen-3-coder-480b

# Save a model
/model add cerebras qwen-3-coder-480b --name "q3c"

# Switch to a saved model
/model q3c

# Set a model as default
/model default q3c

# Remove a saved model
/model remove q3c
```

Saved models are stored in `~/.clippy/models.json` and persist across sessions. The system automatically creates this file when you add your first model.

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

clippy-code has access to these tools with **smart file validation**:

| Tool               | Description                                       | Auto-Approved | Validation Features                                                     |
| ------------------ | ------------------------------------------------- | ------------- | ----------------------------------------------------------------------- |
| `read_file`        | Read file contents                                | ✅            | -                                                                       |
| `write_file`       | **Write files with syntax validation**            | ❌            | **✅ Python, JSON, YAML, XML, HTML, CSS, JS, TS, Markdown, Dockerfile** |
| `delete_file`      | Delete files                                      | ❌            | -                                                                       |
| `list_directory`   | List directory contents                           | ✅            | -                                                                       |
| `create_directory` | Create directories                                | ❌            | -                                                                       |
| `execute_command`  | Run shell commands                                | ❌            | -                                                                       |
| `search_files`     | Search with glob patterns                         | ✅            | -                                                                       |
| `get_file_info`    | Get file metadata                                 | ✅            | -                                                                       |
| `read_files`       | Read multiple files at once                       | ✅            | -                                                                       |
| `grep`             | Search patterns in files                          | ✅            | -                                                                       |
| `edit_file`        | Edit files by line (insert/replace/delete/append) | ❌            | -                                                                       |

#### 🔥 Enhanced write_file Features

- **🛡️ Syntax Validation**: Automatic validation for 12+ file types
- **🚫 Binary Detection**: Prevents binary files from being written as text
- **⚡ Performance Smart**: Large files (>1MB) skip validation automatically
- **💡 Helpful Errors**: Specific error messages with actionable guidance
- **🔧 Override Option**: `skip_validation=True` for binary files or intentional syntax errors

**Supported File Types:**

- 🐍 **Python**: AST syntax checking with detailed error messages
- 📄 **JSON/YAML**: Structure validation with line numbers on errors
- 🌐 **HTML/CSS**: Tag balancing and syntax checking
- 📱 **JavaScript/TypeScript**: Node.js-based validation when available
- 📝 **Markdown**: Link and header validation
- 🐳 **Dockerfile**: Instruction validation
- 📦 **XML**: Well-formedness checking

For detailed information about MCP integration, see [docs/MCP_DOCUMENTATION.md](docs/MCP_DOCUMENTATION.md).

## Design Principles

- **OpenAI Compatibility**: Single standard API format works with any OpenAI-compatible provider
- **Safety First**: Three-tier permission system with user approval workflows
- **Type Safety**: Fully typed Python codebase with MyPy checking
- **Clean Code**: SOLID principles, modular design, Google-style docstrings
- **Streaming Responses**: Real-time output for immediate feedback
- **Error Handling**: Retry logic with exponential backoff, graceful degradation

## Extensibility

### Adding New LLM Providers

clippy-code works with any OpenAI-compatible API provider. Add new providers by updating `providers.yaml`:

```yaml
providers:
  provider_name:
    base_url: https://api.provider.com/v1
    api_key_env: PROVIDER_API_KEY
    description: "Provider Name"
```

Then users can add their own model configurations:

```bash
/model add provider_name model-id --name "my-model" --desc "My custom model"
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

**Product Thinking**:

- Safety controls with user approval systems
- Maintainable and extensible design patterns
- Developer productivity focus

---

Made with ❤️ by the clippy-code team
