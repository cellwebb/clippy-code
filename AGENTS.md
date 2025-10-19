# AGENTS.md

This file provides guidance for AI coding agents working with the clippy-code codebase.

## Essential Commands

```bash
make dev              # Install with dev dependencies
make test             # Run pytest
make check            # Run format, lint, and type-check
python -m clippy -i   # Run in interactive mode
python -m clippy -d   # Run in document mode (Word-like TUI)
```

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
- **REQUIRE_APPROVAL**: write_file, delete_file, create_directory, execute_command, edit_file
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
- `CLIPPY_MODEL`: Model identifier (default: gpt-4o)
- `CLIPPY_MCP_CONFIG`: Path to MCP configuration file (optional)

MCP Configuration:

Create an `mcp.json` file in your home directory (`~/.clippy/mcp.json`), project directory, or specify via `CLIPPY_MCP_CONFIG`. See [MCP_DOCUMENTATION.md](docs/MCP_DOCUMENTATION.md) for detailed configuration.

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
