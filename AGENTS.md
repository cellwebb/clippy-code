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
├── providers.py     # LLM provider abstraction
├── tools.py         # Tool definitions (JSON schemas)
├── executor.py      # Tool execution implementations
└── permissions.py   # Permission system (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
```

## Core Architecture

### Provider Abstraction

All LLM interactions go through `LLMProvider` interface. Never directly import `anthropic` or `openai` in agent logic.

- `LLMProvider` (ABC) → `AnthropicProvider`, `OpenAIProvider`
- `ProviderFactory` creates instances
- All responses normalized to `LLMResponse` dataclass

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

### New LLM Provider

1. Create class in `providers.py` inheriting from `LLMProvider`
2. Implement: `__init__`, `create_message()`, `get_default_model()`, `convert_tools_to_provider_format()`, `convert_messages_to_provider_format()`
3. Register in `ProviderFactory.PROVIDERS`
4. Add optional dependency to `pyproject.toml`
5. Update CLI choices in `cli.py`

See `OpenAIProvider` for reference implementation.

### New Tool (checklist):

1. Add tool definition to `TOOLS` in `tools.py` (JSON schema)
2. Add `ActionType` enum in `permissions.py`
3. Add to `action_map` in **both** `agent.py:_handle_tool_use()` and `executor.py:execute()`
4. Implement `_your_tool()` in `executor.py` returning `tuple[bool, str, Any]`
5. Add to appropriate permission set in `PermissionConfig` (permissions.py)
6. Write tests

## Configuration

Environment variables: `CLIPPY_PROVIDER` (anthropic|openai), `CLIPPY_MODEL`, `CLIPPY_MAX_TOKENS`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`

Config files (priority order): `.env` → `~/.clippy.env` → system env

## Key Implementation Details

- **Agent loop**: 25 iteration max (prevents infinite loops)
- **Command timeout**: 30 seconds
- **File ops**: Auto-create parent dirs, UTF-8 encoding, use `pathlib.Path`
- **Executor returns**: `tuple[bool, str, Any]` (success, message, result)
- **Message format**: Tool results need matching `tool_use_id`, alternating "user"/"assistant" roles
- **Conversation**: Store in Anthropic-style format, providers convert on API call

## Version Management

Keep `pyproject.toml` and `src/clippy/__version__.py` in sync. Use: `make bump-patch|minor|major`

## Design Rationale

- **Anthropic format internally**: Cleaner schema, better multi-turn support
- **3 permission levels**: AUTO_APPROVE (safe ops), REQUIRE_APPROVAL (risky), DENY (blocked)
- **25 iteration max**: Prevents infinite loops, sufficient for most tasks
- **Separate tools/executor/permissions**: Interface vs execution vs policy (separation of concerns)
