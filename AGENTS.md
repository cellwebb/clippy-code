# AGENTS.md

This file provides guidance for AI coding agents working with the clippy-code codebase.

## Essential Commands

```bash
make dev              # Install with dev dependencies
make test             # Run pytest
make check            # Run format, lint, and type-check
python -m clippy -i   # Run in interactive mode
```

## Project Structure

```
src/clippy/
├── cli.py           # CLI entry point, argument parsing
├── agent.py         # Core agent loop (max 25 iterations)
├── providers.py     # OpenAI-compatible LLM provider (~100 lines)
├── tools.py         # Tool definitions (JSON schemas)
├── executor.py      # Tool execution implementations
└── permissions.py   # Permission system (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
```

## Core Architecture

### Provider Layer

All LLM interactions go through a single `LLMProvider` class (~100 lines total).

- Uses OpenAI SDK with native OpenAI format throughout (no conversions)
- Works with any OpenAI-compatible API: OpenAI, Cerebras, Together AI, Azure OpenAI, Ollama, llama.cpp, vLLM, Groq, etc.
- Configure alternate providers via `base_url` parameter
- Includes retry logic with exponential backoff (up to 3 attempts)
- Streams responses in real-time

### Agent Flow

1. User input → `ClippyAgent`
2. Loop (max 25 iterations): Call LLM → Process response → Execute tools → Add results → Repeat
3. Tool execution: Check permissions → Get approval if needed → Execute → Return `(success, message, result)`

### Tool System (3 parts - modify together)

1. **Definition** (`tools.py`): JSON schema
2. **Permission** (`permissions.py`): Permission level
3. **Execution** (`executor.py`): Implementation returning `tuple[bool, str, Any]`

### Permissions

- **AUTO_APPROVE**: read_file, list_directory, search_files, get_file_info
- **REQUIRE_APPROVAL**: write_file, delete_file, create_directory, execute_command
- **DENY**: Blocked operations

## Code Standards

- **Type hints required**: Use `str | None` not `Optional[str]`, `tuple[bool, str, Any]` not `Tuple`
- **Line length**: 100 chars max
- **Format**: Run `uv run ruff format .` before committing
- **Type check**: Run `uv run mypy src/clippy`
- **Docstrings**: Google-style with Args, Returns, Raises
- **Tests**: Mock external APIs, use pytest, pattern `test_*.py`

## Adding Features

### Using Alternate LLM Providers

CLIppy uses OpenAI format natively, so any OpenAI-compatible provider works out-of-the-box:

1. Set `OPENAI_BASE_URL` to the provider's API endpoint
2. Set `OPENAI_API_KEY` to your API key for that provider
3. Set `CLIPPY_MODEL` to the model name (if different from default)
4. No code changes needed!

Examples: OpenAI, Cerebras, Together AI, Azure OpenAI, Ollama, llama.cpp, vLLM, Groq, Mistral API

### New Tool (checklist):

1. Add tool definition to `TOOLS` in `tools.py` (JSON schema)
2. Add `ActionType` enum in `permissions.py`
3. Add to `action_map` in **both** `agent.py:_handle_tool_use()` and `executor.py:execute()`
4. Implement `_your_tool()` in `executor.py` returning `tuple[bool, str, Any]`
5. Add to appropriate permission set in `PermissionConfig` (permissions.py)
6. Write tests

## Configuration

Environment variables:
- `OPENAI_API_KEY`: API key for OpenAI or OpenAI-compatible provider (required)
- `OPENAI_BASE_URL`: Base URL for alternate providers (e.g., https://api.cerebras.ai/v1)
- `CLIPPY_MODEL`: Model identifier (default: gpt-4o)
- `CLIPPY_MAX_TOKENS`: Max tokens for responses (default: 4096)

Config files (priority order): `.env` → `~/.clippy.env` → system env

## Key Implementation Details

- **Agent loop**: 25 iteration max (prevents infinite loops)
- **Command timeout**: 30 seconds
- **File ops**: Auto-create parent dirs, UTF-8 encoding, use `pathlib.Path`
- **Executor returns**: `tuple[bool, str, Any]` (success, message, result)
- **Message format**: Uses OpenAI format natively throughout (no conversions)
- **Conversation**: Stores messages in OpenAI format with role and content fields
- **Streaming**: Responses are streamed in real-time to provide immediate feedback

## Version Management

Keep `pyproject.toml` and `src/clippy/__version__.py` in sync. Use: `make bump-patch|minor|major`

## Design Rationale

- **OpenAI format natively**: Single standard format, works with any OpenAI-compatible provider
- **No provider abstraction**: Simpler codebase (~100 lines vs 370+), easier to maintain
- **3 permission levels**: AUTO_APPROVE (safe ops), REQUIRE_APPROVAL (risky), DENY (blocked)
- **25 iteration max**: Prevents infinite loops, sufficient for most tasks
- **Retry logic**: Exponential backoff with 3 attempts for resilience against transient failures
- **Separate tools/executor/permissions**: Interface vs execution vs policy (separation of concerns)
