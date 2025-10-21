# AGENTS.md

This file provides guidance for AI coding agents working with the clippy-code codebase.

## Essential Commands

```bash
make dev              # Install with dev dependencies
make test             # Run pytest
make check            # Run format, lint, and type-check
make run              # Launch interactive mode through the Makefile
make format           # Autofix and format code with ruff
make lint             # Static analysis with ruff
make type-check       # Run mypy against src/clippy
python -m clippy -i   # Run in interactive mode
python -m clippy -d   # Run in document mode (Word-like TUI)
```

## Development Workflow Tips

- Prefer the `make` targets above for consistent formatting, linting, and type checks.
- Run `make check` and `make test` before finishing a task to catch regressions early.
- Use `make format` if a change requires ruff autofixes prior to committing or submitting.
- Reference `README.md` for installation guidance and `CONTRIBUTING.md` for contributor workflow details.

## Project Structure

```
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
│   ├── main.py                 # Main entry point
│   ├── parser.py               # Argument parsing
│   ├── oneshot.py              # One-shot mode implementation
│   ├── repl.py                 # Interactive REPL mode
│   ├── commands.py             # High-level CLI commands
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
├── ui/
│   ├── document_app.py         # Textual-based document mode interface
│   ├── styles.py               # CSS styling for document mode
│   ├── utils.py                # UI utility functions
│   └── widgets.py              # Custom UI widgets
├── diff_utils.py               # Diff generation utilities
├── executor.py                 # Tool execution implementations
├── models.py                   # Model configuration loading and presets
├── models.yaml                 # Model presets for different providers
├── permissions.py              # Permission system (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
├── prompts.py                  # System prompts for the agent
├── providers.py                # OpenAI-compatible LLM provider
├── providers.yaml              # Model/provider preset definitions
├── __main__.py                 # Module entry point
└── __version__.py              # Version helper
```

## Core Architecture

### Provider Layer

All LLM interactions go through a single `LLMProvider` class (~100 lines total).

- Uses OpenAI SDK with native OpenAI format throughout (no conversions)
- Works with any OpenAI-compatible API: OpenAI, Cerebras, Together AI, Azure OpenAI, Ollama, llama.cpp, vLLM, Groq, etc.
- Configure alternate providers via `base_url` parameter
- Includes retry logic with exponential backoff (up to 3 attempts)
- Streams responses in real-time
- Shows loading spinner during processing

### Agent Flow

1. User input → `ClippyAgent`
2. Loop (max 50 iterations): Call LLM → Process response → Execute tools → Add results → Repeat
3. Tool execution: Check permissions → Get approval if needed → Execute → Return `(success, message, result)`
4. **Subagent Delegation** (optional): Agent can spawn specialized subagents for complex subtasks
   - Sequential or parallel execution
   - Context isolation and specialized prompting
   - Result caching and chaining support

### Tool System (3 parts + MCP integration)

1. **Definition** (`tools/__init__.py`): Tool implementations with co-located schemas
2. **Catalog** (`tools/catalog.py`): Merges built-in and MCP tools
3. **Permission** (`permissions.py`): Permission level
4. **Execution** (`executor.py`): Implementation returning `tuple[bool, str, Any]`
5. **MCP Integration** (`mcp/`): Dynamic tool discovery from external servers

Individual tool implementations are located in `src/clippy/tools/` directory with each tool having its own file and co-located schema.

### Models System

- Model configurations are defined in `models.yaml` with presets for different providers
- Supports OpenAI, Cerebras, Ollama, Together AI, Groq, and DeepSeek
- Users can switch models in interactive/document mode using `/model <name>` command
- Each provider can specify its own API key environment variable

### Permissions

- **AUTO_APPROVE**: read_file, list_directory, search_files, get_file_info, grep, read_files
- **REQUIRE_APPROVAL**: write_file, delete_file, create_directory, execute_command, edit_file, delegate_to_subagent, run_parallel_subagents
- **DENY**: Blocked operations (empty by default)

## Code Standards

- **Type hints required**: Use `str | None` not `Optional[str]`, `tuple[bool, str, Any]` not `Tuple`
- **Line length**: 100 chars max
- **Format**: Run `uv run ruff format .` before committing
- **Type check**: Run `uv run mypy src/clippy`
- **Docstrings**: Google-style with Args, Returns, Raises
- **Tests**: Mock external APIs, use pytest, pattern `test_*.py`

## Adding Features

### Using Alternate LLM Providers

clippy-code uses OpenAI format natively, so any OpenAI-compatible provider works out-of-the-box:

1. Set provider-specific API key environment variable (OPENAI_API_KEY, CEREBRAS_API_KEY, etc.)
2. Use model presets from `models.yaml` or specify custom model/base_url
3. No code changes needed!

Examples: OpenAI, Cerebras, Together AI, Azure OpenAI, Ollama, llama.cpp, vLLM, Groq, Mistral API

### New Tool (checklist):

1. Create a new tool implementation file in `src/clippy/tools/` (e.g., `your_tool.py`)
2. Add the tool to `src/clippy/tools/__init__.py` (both import and export)
3. Add `ActionType` enum in `permissions.py`
4. Add to appropriate permission set in `PermissionConfig` (permissions.py)
5. Add tool execution to `executor.py:execute()`
6. Add to `action_map` in `agent/tool_handler.py:_handle_tool_use()`
7. Write tests in `tests/tools/test_your_tool.py`

### UI Modes

### Subagent System

clippy-code includes a powerful subagent system for complex task decomposition and parallel execution:

#### Available Subagent Types

- **general**: General-purpose tasks with all tools available
- **code_review**: Read-only code analysis and review
- **testing**: Test generation and execution
- **refactor**: Code refactoring and improvement
- **documentation**: Documentation generation and updates
- **fast_general**: Quick tasks using faster models (gpt-3.5-turbo)
- **power_analysis**: Deep analysis using powerful models (claude-3-opus)

#### Subagent Features

- **Task Delegation**: Main agent can delegate complex subtasks to specialized subagents
- **Parallel Execution**: Multiple subagents can work on independent tasks concurrently
- **Context Isolation**: Each subagent has its own conversation history and specialized prompting
- **Result Caching**: Avoid re-executing identical tasks with intelligent caching
- **Hierarchical Chaining**: Subagents can spawn their own subagents (with depth limits)
- **Model Selection**: Different subagent types can use different optimized models

#### Using Subagents

The main agent can use two tools for subagent management:

1. **delegate_to_subagent**: Create a single specialized subagent
2. **run_parallel_subagents**: Create and run multiple subagents in parallel

Example usage:

```python
# Single subagent delegation
{
    "task": "Review all Python files for security issues",
    "subagent_type": "code_review",
    "context": {"focus": "security", "exclude_patterns": ["test_*.py"]}
}

# Parallel subagent execution
{
    "subagents": [
        {"task": "Write unit tests for auth module", "subagent_type": "testing"},
        {"task": "Generate API documentation", "subagent_type": "documentation"},
        {"task": "Refactor database queries", "subagent_type": "refactor"}
    ],
    "max_concurrent": 3
}
```

#### Subagent Configuration

Subagent behavior can be customized via environment variables:

- `CLIPPY_MAX_CONCURRENT_SUBAGENTS`: Maximum parallel subagents (default: 3)
- `CLIPPY_SUBAGENT_TIMEOUT`: Default timeout in seconds (default: 300)
- `CLIPPY_SUBAGENT_CACHE_ENABLED`: Enable result caching (default: true)
- `CLIPPY_SUBAGENT_CACHE_SIZE`: Maximum cache entries (default: 100)
- `CLIPPY_SUBAGENT_CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `CLIPPY_MAX_SUBAGENT_DEPTH`: Maximum nesting depth (default: 3)

### Conversation Management

### MCP Integration

clippy-code supports the Model Context Protocol (MCP) for dynamically discovering and using external tools. MCP enables extending the agent's capabilities without modifying the core codebase.

Key MCP features:

- **Dynamic Tool Discovery**: Automatically discovers tools from configured MCP servers
- **Trust System**: Secure approval workflow for external tools
- **Schema Mapping**: Converts MCP tool schemas to OpenAI-compatible format
- **Error Handling**: Graceful handling of connection and execution failures

MCP configuration:

Create an `mcp.json` file in your home directory (`~/.clippy/mcp.json`) or project directory:

```json
{
  "mcp_servers": {
    "context7": {
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp", "--api-key", "${CTX7_API_KEY}"]
    }
  }
}
```

Available MCP commands in interactive/document mode:

- `/mcp list` - Show configured MCP servers and connection status
- `/mcp tools [server]` - List available tools from MCP servers
- `/mcp refresh` - Refresh connections to MCP servers
- `/mcp allow <server>` - Trust an MCP server (auto-approve its tools)
- `/mcp revoke <server>` - Revoke trust for an MCP server

MCP tools integrate seamlessly with clippy-code's permission system. By default, MCP tools require approval before execution, but trusted servers have their tools auto-approved.

## Configuration

Environment variables:

- `OPENAI_API_KEY`: API key for OpenAI or OpenAI-compatible provider (required for OpenAI)
- `CEREBRAS_API_KEY`: API key for Cerebras provider
- `TOGETHER_API_KEY`: API key for Together AI provider
- `GROQ_API_KEY`: API key for Groq provider
- `DEEPSEEK_API_KEY`: API key for DeepSeek provider
- `OPENAI_BASE_URL`: Base URL for alternate providers (e.g., https://api.cerebras.ai/v1)

### Subagent Configuration

- `CLIPPY_MAX_CONCURRENT_SUBAGENTS`: Maximum parallel subagents (default: 3)
- `CLIPPY_SUBAGENT_TIMEOUT`: Default timeout in seconds (default: 300)
- `CLIPPY_SUBAGENT_CACHE_ENABLED`: Enable result caching (default: true)
- `CLIPPY_SUBAGENT_CACHE_SIZE`: Maximum cache entries (default: 100)
- `CLIPPY_SUBAGENT_CACHE_TTL`: Cache TTL in seconds (default: 3600)
- `CLIPPY_MAX_SUBAGENT_DEPTH`: Maximum nesting depth (default: 3)

MCP Configuration:

Create an `mcp.json` file in your home directory (`~/.clippy/mcp.json`) or project directory (`.clippy/mcp.json`). See [MCP_DOCUMENTATION.md](docs/MCP_DOCUMENTATION.md) for detailed configuration.

For detailed MCP configuration and usage, see [MCP_DOCUMENTATION.md](MCP_DOCUMENTATION.md).

## Key Implementation Details

- **Agent loop**: 50 iteration max (prevents infinite loops)
- **Command timeout**: 30 seconds
- **File ops**: Auto-create parent dirs, UTF-8 encoding, use `pathlib.Path`
- **Executor returns**: `tuple[bool, str, Any]` (success, message, result)
- **Message format**: Uses OpenAI format natively throughout (no conversions)
- **Conversation**: Stores messages in OpenAI format with role and content fields
- **Streaming**: Responses are streamed in real-time to provide immediate feedback
- **Gitignore support**: Recursive directory listing respects .gitignore patterns
- **Model switching**: Users can switch models/providers during interactive sessions

## Version Management

Keep `pyproject.toml` and `src/clippy/__version__.py` in sync. Use: `make bump-patch|minor|major`

## Design Rationale

- **OpenAI format natively**: Single standard format, works with any OpenAI-compatible provider
- **No provider abstraction**: Simpler codebase (~100 lines vs 370+), easier to maintain
- **3 permission levels**: AUTO_APPROVE (safe ops), REQUIRE_APPROVAL (risky), DENY (blocked)
- **50 iteration max**: Prevents infinite loops, sufficient for most tasks
- **Retry logic**: Exponential backoff with 3 attempts for resilience against transient failures
- **Separate tools/executor/permissions**: Interface vs execution vs policy (separation of concerns)
- **Document mode**: Provides a more intuitive interface for longer coding tasks
- **Model presets**: Makes it easy to switch between different providers and models
