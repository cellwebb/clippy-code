# clippy-code 👀📎

[![Python 3.10–3.14](https://img.shields.io/badge/python-3.10%E2%80%933.14-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)

> A production-ready, model-agnostic CLI coding agent with safety-first design

clippy-code is an AI-powered development assistant that works with any OpenAI-compatible API provider. It features robust permission controls, streaming responses, and multiple interface modes for different workflows.

![example](assets/example.png)

## 🚀 Quick Start

### Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Run clippy-code directly - no installation needed!
uvx clippy-code "create a hello world python script"

# Start interactive mode
uvx clippy-code
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
echo "GEMINI_API_KEY=your_api_key_here" > .env
echo "GROQ_API_KEY=your_api_key_here" > .env
echo "MINIMAX_API_KEY=your_api_key_here" > .env
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
echo "SYNTHETIC_API_KEY=your_api_key_here" > .env
echo "TOGETHER_API_KEY=your_api_key_here" > .env
echo "ZAI_API_KEY=your_api_key_here" > .env
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

clippy-code can dynamically discover and use tools from MCP (Model Context Protocol) servers. For detailed configuration and available servers, see [docs/MCP.md](docs/MCP.md).

Quick setup:

```bash
# Create the clippy directory
mkdir -p ~/.clippy

# Copy the example configuration
cp mcp.example.json ~/.clippy/mcp.json

# Edit it with your API keys
```

## Key Features

- **🌐 Broad Provider Support**: OpenAI, Anthropic, Cerebras, Groq, Mistral, Ollama, and many more
- **🛡️ Safety-First Design**: Three-tier permissions with interactive approval for risky operations
- **🔄 Multiple Interface Modes**: One-shot tasks, interactive REPL, and rich document mode
- **🤖 Advanced Agent Capabilities**: Streaming responses, context management, subagent delegation
- **🔌 Extensible Tool System**: Built-in file operations, command execution, and MCP integration
- **💻 Developer Experience**: Type-safe codebase, rich CLI, flexible configuration

## Available Tools

clippy-code provides smart file operations with validation for many file types:

| Tool | Description | Auto-Approved |
|------|-------------|---------------|
| `read_file` | Read file contents | ✅ |
| `write_file` | **Write files with syntax validation** | ❌ |
| `delete_file` | Delete files | ❌ |
| `list_directory` | List directory contents | ✅ |
| `create_directory` | Create directories | ❌ |
| `execute_command` | Run shell commands (output hidden by default, set `CLIPPY_SHOW_COMMAND_OUTPUT=true` to show) | ❌ |
| `search_files` | Search with glob patterns | ✅ |
| `get_file_info` | Get file metadata | ✅ |
| `read_files` | Read multiple files at once | ✅ |
| `grep` | Search patterns in files | ✅ |
| `read_lines` | Read specific lines from a file | ✅ |
| `edit_file` | Edit files by line (insert/replace/delete/append) | ❌ |
| `fetch_webpage` | Fetch content from web pages | ❌ |
| `find_replace` | Multi-file pattern replacement with regex | ❌ |

**write_file** includes syntax validation for Python, JSON, YAML, HTML, CSS, JavaScript, TypeScript, Markdown, Dockerfile, and XML.

## 🛡️ Intelligent Command Safety

clippy-code includes an **LLM-powered command safety agent** that provides intelligent analysis of shell commands before execution. When an LLM provider is available, every `execute_command` call is automatically analyzed for security risks.

### How It Works

The safety agent analyzes commands in full context (including working directory) and uses conservative security policies to protect against dangerous operations:

**🚫 Automatically Blocks:**
- Destructive operations (`rm -rf`, `shred`, recursive deletion)
- System file modifications (`/etc/`, `/boot/`, `/proc/`, `/sys/`)
- Software installation without consent (`pip install`, `apt-get`, `npm install`)
- Download and execute code (`curl | bash`, `wget | sh`)
- Network attacks (`nmap`, `netcat`)
- Privilege escalation (`sudo` unless clearly necessary)
- File system attacks (`dd` to block devices)

**✅ Allows Safe Operations:**
- File listing (`ls`, `find`)
- Basic command execution (`echo`, `cat`, `grep`)
- Development tools (`python script.py`, `npm run dev`)
- Safe file operations in user directories

### User Experience

When a command is blocked, users receive clear, contextual feedback:

```
User: rm -rf /tmp/old_project
AI: Command blocked by safety agent: Would delete entire filesystem - extremely dangerous

User: curl https://github.com/user/script.sh | bash  
AI: Command blocked by safety agent: Downloads and executes untrusted code
```

The agent is **context-aware** - the same command may be allowed in a user directory but blocked in system directories.

### Fallback Protection

If no LLM provider is available, the system falls back to pattern-based security checks. The safety agent **fails safely** - if the safety check fails for any reason, commands are blocked by default.

For detailed technical information, see [Command Safety Agent Documentation](docs/COMMAND_SAFETY_AGENT.md).

## Models & Configuration

### Supported Providers

clippy-code works with any OpenAI-compatible provider: Anthropic (including Claude Code OAuth), Chutes, Cerebras, Gemini, Groq, LM Studio, MiniMax, Mistral, Ollama, OpenAI, OpenRouter, Synthetic.new, Together AI, Z.AI, and more.

### Managing Models

```bash
# List available providers
/model list

# Save a model configuration
/model add cerebras qwen-3-coder-480b --name "q3c"

# Switch to a saved model
/model q3c
```

### Environment Variables

- Provider-specific API keys: `ANTHROPIC_API_KEY`, `CHUTES_API_KEY`, `CEREBRAS_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MINIMAX_API_KEY`, `MISTRAL_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `SYNTHETIC_API_KEY`, `TOGETHER_API_KEY`, `ZAI_API_KEY`, `CLAUDE_CODE_ACCESS_TOKEN` (OAuth), etc.
- `OPENAI_BASE_URL` - Optional base URL override for custom providers
- `CLIPPY_SHOW_COMMAND_OUTPUT` - Control whether to show output from `execute_command` tool (default: `false`, set to `true` to show output)
- `CLIPPY_COMMAND_TIMEOUT` - Default timeout for command execution in seconds (default: `300`)
- `CLIPPY_MAX_TOOL_RESULT_TOKENS` - Maximum number of tokens to allow in tool results (default: `10000`)

## Development

### Setting Up

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
uv run python -m clippy

# For normal usage, use uvx clippy-code
```

### Code Quality

```bash
# Format code
make format

# Run linting, type checking, and tests
make check
make test
```

### Adding Features

For detailed information about:
- **Adding new tools**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **MCP server integration**: See [docs/MCP_DOCUMENTATION.md](docs/MCP_DOCUMENTATION.md)
- **Subagent development**: See [docs/SUBAGENTS.md](docs/SUBAGENTS.md)

## Design Principles

- **OpenAI Compatibility**: Single standard API format works with any OpenAI-compatible provider
- **Safety First**: Three-tier permission system with user approval workflows
- **Type Safety**: Fully typed Python codebase with MyPy checking
- **Clean Code**: SOLID principles, modular design, Google-style docstrings
- **Streaming Responses**: Real-time output for immediate feedback

## Documentation

- [Quick Start Guide](QUICKSTART.md) - Getting started in 5 minutes
- [MCP Integration](docs/MCP.md) - Model Context Protocol setup and usage
- [Contributing Guide](CONTRIBUTING.md) - Development workflow and code standards
- [Agent Documentation](AGENTS.md) - Internal architecture for developers

---

Made with ❤️ by the clippy-code team
