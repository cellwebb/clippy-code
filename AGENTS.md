# AGENTS.md

This file provides guidance for AI coding agents working with the CLIppy codebase.

## Quick Start

CLIppy is a model-agnostic CLI coding agent built with Python 3.10+. The project uses `uv` for package management and follows modern Python best practices.

### Essential Commands

```bash
# Development setup
make dev              # Install with dev dependencies
python -m clippy -i   # Run in interactive mode

# Testing & Quality
make test             # Run pytest
make check            # Run format, lint, and type-check
make all              # Run all checks and tests

# Single commands for specific tasks
uv run pytest tests/test_file.py -v  # Run specific test file
uv run ruff format .                  # Format code
uv run mypy src/clippy               # Type check
```

### Project Structure

```
src/clippy/
├── cli.py           # CLI entry point, argument parsing
├── agent.py         # Core agent loop, conversation management
├── providers.py     # LLM provider abstraction (Anthropic, OpenAI)
├── tools.py         # Tool definitions (JSON schemas)
├── executor.py      # Tool execution implementations
└── permissions.py   # Permission system (3 levels)
```

## Architecture Overview

### Provider Abstraction Pattern

**Key Insight**: The codebase is model-agnostic. All LLM interactions go through an abstraction layer.

- `LLMProvider` (ABC) defines the interface
- `AnthropicProvider` and `OpenAIProvider` implement it
- `ProviderFactory` creates provider instances
- All responses are normalized to `LLMResponse` dataclass

**When modifying**: Changes to agent logic should never directly import `anthropic` or `openai`. Always work through the `LLMProvider` interface.

### Agent Execution Flow

1. User input → CLI (`cli.py`)
2. CLI creates `ClippyAgent` with provider, permissions, executor
3. Agent runs loop (max 25 iterations):
   - Add user message to history
   - Call LLM via provider
   - Process response (text + tool use blocks)
   - For each tool use: check permissions → get approval → execute → add result
   - Continue until no more tool use
4. Return final response

**Key file**: `agent.py:_run_agent_loop()` - This is the heart of the system.

### Tool System

Tools have 3 parts (always modify all 3 together):

1. **Definition** (`tools.py`): JSON schema describing the tool
2. **Permission** (`permissions.py`): What permission level (AUTO_APPROVE, REQUIRE_APPROVAL, DENY)
3. **Execution** (`executor.py`): Implementation that returns `(success: bool, message: str, result: Any)`

**Example workflow to add a tool**:
- Add schema to `TOOLS` list in `tools.py`
- Add `ActionType` enum in `permissions.py`
- Add mapping in `action_map` (both `agent.py` and `executor.py`)
- Implement `_tool_name()` method in `executor.py`
- Add to appropriate permission set in `PermissionConfig`

### Permission System

3-level security model in `permissions.py`:

- **AUTO_APPROVE**: Read-only ops (read_file, list_directory, search_files, get_file_info)
- **REQUIRE_APPROVAL**: Destructive ops (write_file, delete_file, create_directory, execute_command)
- **DENY**: Blocked operations

The `PermissionManager` checks permissions before execution. Agent asks user for approval if needed.

## Code Style & Standards

### Type Safety
- **Required**: Type hints on all function signatures
- **Check with**: `uv run mypy src/clippy`
- Use Python 3.10+ syntax: `str | None` instead of `Optional[str]`
- Use `tuple[bool, str, Any]` not `Tuple[bool, str, Any]`

### Formatting
- **Line length**: 100 characters max
- **Tool**: Ruff (replaces Black + Flake8 + isort)
- **Run**: `uv run ruff format .` before committing
- **Config**: See `pyproject.toml` for rules

### Docstrings
- Use Google-style docstrings for public functions
- Include Args, Returns, Raises sections
- Keep concise but informative

### Testing
- Tests live in `tests/` directory
- Use pytest for all tests
- Mock external API calls (don't hit real Anthropic/OpenAI APIs)
- Name pattern: `test_*.py` for files, `test_*` for functions
- Run specific test: `uv run pytest tests/test_file.py::test_function -v`

## Common Development Tasks

### Adding Support for a New LLM Provider

1. Create class in `providers.py` inheriting from `LLMProvider`
2. Implement required methods:
   - `__init__(api_key)` - Initialize client
   - `create_message()` - Call API and return `LLMResponse`
   - `get_default_model()` - Return default model string
   - `convert_tools_to_provider_format()` - Convert CLIppy schema to provider's format
   - `convert_messages_to_provider_format()` - Convert conversation history
3. Register in `ProviderFactory.PROVIDERS` dict
4. Add optional dependency to `pyproject.toml`:
   ```toml
   [project.optional-dependencies]
   provider_name = ["provider-sdk>=1.0.0"]
   ```
5. Update CLI choices in `cli.py:create_parser()`

**Reference implementation**: See `OpenAIProvider` for conversion examples

### Modifying the Agent Loop

- **File**: `agent.py`
- **Method**: `_run_agent_loop()`
- **Important**: The loop has a 25-iteration limit to prevent infinite loops
- **State**: Conversation history stored in `self.conversation_history`
- **Format**: Messages follow Anthropic's format (multi-part content blocks)
- **Interrupts**: Handle `InterruptedException` for Ctrl+C support

### Adding a New Tool

**Complete checklist**:

1. Add tool definition to `TOOLS` in `tools.py`:
```python
{
    "name": "your_tool",
    "description": "What it does",
    "input_schema": {
        "type": "object",
        "properties": {...},
        "required": [...]
    }
}
```

2. Add action type to `permissions.py`:
```python
class ActionType(str, Enum):
    YOUR_TOOL = "your_tool"
```

3. Add to `action_map` in TWO places:
   - `agent.py:_handle_tool_use()`
   - `executor.py:execute()`

4. Implement in `executor.py`:
```python
def _your_tool(self, param: str) -> tuple[bool, str, Any]:
    """Execute your tool."""
    try:
        # Implementation
        return True, "Success message", result
    except Exception as e:
        return False, f"Error: {e}", None
```

5. Add to permission config in `permissions.py`:
```python
class PermissionConfig(BaseModel):
    auto_approve: Set[ActionType] = {
        # Add here if read-only
    }
    require_approval: Set[ActionType] = {
        # Add here if destructive
    }
```

6. Write tests in `tests/test_executor.py` or new file

### Modifying Conversation Handling

**Important**: Conversation history must remain provider-agnostic.

- Store in standardized format (Anthropic-style with content blocks)
- Each provider converts during `create_message()` call
- Tool results are added as user messages with `tool_result` type
- Format: `{"role": "user", "content": [{"type": "tool_result", "tool_use_id": "...", "content": "...", "is_error": false}]}`

### Working with Permissions

To change default permissions, modify `PermissionConfig` in `permissions.py`:

```python
class PermissionConfig(BaseModel):
    auto_approve: Set[ActionType] = {
        ActionType.READ_FILE,
        # Add more here
    }
    require_approval: Set[ActionType] = {
        ActionType.WRITE_FILE,
        # Add more here
    }
    deny: Set[ActionType] = set()  # Usually empty
```

## Configuration & Environment

### Environment Variables

```bash
CLIPPY_PROVIDER=anthropic       # or "openai"
CLIPPY_MODEL=model-name         # Optional, uses provider default if unset
CLIPPY_MAX_TOKENS=4096          # Response token limit

ANTHROPIC_API_KEY=sk-...        # For Anthropic provider
OPENAI_API_KEY=sk-...           # For OpenAI provider
```

### Config Files Checked (in order)

1. `.env` in current directory
2. `~/.clippy.env` in user home
3. System environment variables

## Important Implementation Details

### Iteration Limit
- Agent loop has **25 iteration maximum** to prevent infinite loops
- Defined in `agent.py:_run_agent_loop()`
- If you're debugging "incomplete task" issues, check if hitting this limit

### Command Timeout
- Shell commands timeout after **30 seconds**
- Defined in `executor.py:_execute_command()`
- Uses `subprocess.run()` with `timeout=30`

### File Operations
- All file writes create parent directories automatically via `Path(path).parent.mkdir(parents=True, exist_ok=True)`
- Uses UTF-8 encoding by default
- Paths use `pathlib.Path` for cross-platform compatibility

### Response Format
- All executor methods return `tuple[bool, str, Any]`:
  - `success`: Whether operation succeeded
  - `message`: Human-readable status message
  - `result`: Actual result data (or None)

### Message History
- Tool results must include `tool_use_id` matching the original tool use
- Messages alternate between "user" and "assistant" roles
- Content can be string or list of content blocks

## Version Management

**Critical**: Two files must stay in sync:
- `pyproject.toml` - `version = "x.y.z"`
- `src/clippy/__version__.py` - `__version__ = "x.y.z"`

Use Makefile commands to keep them synchronized:
```bash
make bump-patch   # 0.1.0 -> 0.1.1
make bump-minor   # 0.1.0 -> 0.2.0
make bump-major   # 0.1.0 -> 1.0.0
```

## Testing Strategy

### Unit Tests
- Test individual components in isolation
- Mock external dependencies (API calls, file system when appropriate)
- Focus on edge cases and error handling

### Integration Tests
- Test end-to-end workflows
- Use real file system in temp directories
- Mock LLM API calls to avoid costs and ensure reproducibility

### Running Tests
```bash
uv run pytest -v                    # All tests, verbose
uv run pytest -k "test_provider"    # Tests matching pattern
uv run pytest --cov=clippy          # With coverage
```

## Troubleshooting

### "ModuleNotFoundError" for anthropic/openai
- Install with extras: `uv pip install -e ".[all-providers]"`
- Or install specific: `uv pip install -e ".[openai]"`

### Type checking failures
- Run `uv run mypy src/clippy` to see errors
- Common issues:
  - Missing return type hints
  - Using `Optional[X]` instead of `X | None`
  - Incorrect tuple syntax

### Tests failing
- Ensure you're in the project root
- Run `make dev` to install all dev dependencies
- Check that you're not hitting real APIs (should be mocked)

## Key Design Decisions

1. **Why standardize on Anthropic's format internally?**
   - Cleaner schema design (flat structure)
   - More expressive content blocks
   - Better multi-turn conversation support

2. **Why 3-level permissions instead of 2?**
   - AUTO_APPROVE: Reduces friction for safe ops
   - REQUIRE_APPROVAL: Gives users control over risky ops
   - DENY: Allows hard blocks for security policies

3. **Why max 25 iterations?**
   - Prevents infinite loops and runaway costs
   - Empirically sufficient for most tasks
   - Users can restart if needed

4. **Why separate tools.py, executor.py, and permissions.py?**
   - **tools.py**: What LLM sees (interface)
   - **executor.py**: How it's implemented (execution)
   - **permissions.py**: Who can do what (policy)
   - Clear separation of concerns

## Contributing Guidelines

When submitting changes:

1. **Format and lint**: Run `make check` before committing
2. **Type check**: Ensure `mypy` passes
3. **Test**: Add tests for new functionality
4. **Document**: Update docstrings and this file if needed
5. **Commit message**: Follow conventional commits:
   - `feat:` for new features
   - `fix:` for bug fixes
   - `docs:` for documentation
   - `refactor:` for code improvements
   - `test:` for test additions

## Additional Resources

- **Anthropic Tool Use Docs**: https://docs.anthropic.com/claude/docs/tool-use
- **OpenAI Function Calling**: https://platform.openai.com/docs/guides/function-calling
- **Pydantic Models**: https://docs.pydantic.dev/
- **Rich Terminal**: https://rich.readthedocs.io/

## Quick Reference Card

| Task | Command |
|------|---------|
| Run agent | `python -m clippy -i` |
| Run tests | `make test` |
| Format code | `make format` |
| Type check | `make type-check` |
| All checks | `make check` |
| Run single test | `uv run pytest tests/test_file.py::test_name -v` |
| Install deps | `make dev` |
| Clean build | `make clean` |
