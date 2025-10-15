# Simplified Migration: OpenAI-Only

## Decision

**Remove Anthropic support entirely** - Standardize on OpenAI SDK/format for maximum simplicity and ecosystem compatibility.

## Why This Is Better

### Complexity Reduction

- **No conversion logic** - Zero transformations between formats
- **No abstraction layers** - Direct use of OpenAI SDK
- **No provider factory** - Just one provider
- **Simpler codebase** - ~50% less code in providers.py

### Ecosystem Benefits

- Works with: OpenAI, Cerebras, Together AI, Azure OpenAI, Ollama, llama.cpp, vLLM, Groq, Mistral API, etc.
- Users can swap providers via base URL without code changes
- Better documentation (everyone knows OpenAI format)

---

## Migration Steps (Simplified)

### 1. Update Tool Definitions

**File:** `src/clippy/tools.py`

```python
# FROM (Anthropic format):
TOOLS = [
    {
        "name": "read_file",
        "description": "Read the contents of a file",
        "input_schema": {
            "type": "object",
            "properties": {...},
            "required": [...]
        }
    }
]

# TO (OpenAI format):
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file",
            "parameters": {
                "type": "object",
                "properties": {...},
                "required": [...]
            }
        }
    }
]
```

---

### 2. Simplify providers.py

**File:** `src/clippy/providers.py`

```python
"""OpenAI-based LLM provider."""

from typing import Any
from openai import OpenAI


class LLMProvider:
    """OpenAI-compatible LLM provider."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None, **kwargs):
        """
        Initialize OpenAI-compatible provider.

        Args:
            api_key: API key for authentication
            base_url: Base URL for API (e.g., https://api.cerebras.ai/v1)
            **kwargs: Additional arguments passed to OpenAI client
        """
        client_kwargs = {"api_key": api_key}
        if base_url:
            client_kwargs["base_url"] = base_url

        self.client = OpenAI(**client_kwargs)

    def create_message(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        max_tokens: int,
        model: str,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Create a chat completion.

        Args:
            messages: OpenAI-format messages (includes system message)
            tools: OpenAI-format tool definitions
            max_tokens: Maximum tokens for response
            model: Model identifier
            **kwargs: Additional provider-specific parameters

        Returns:
            OpenAI message dict from response.choices[0].message
        """
        response = self.client.chat.completions.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages,
            tools=tools if tools else None,
            **kwargs,
        )

        return {
            "role": response.choices[0].message.role,
            "content": response.choices[0].message.content,
            "tool_calls": response.choices[0].message.tool_calls,
            "finish_reason": response.choices[0].finish_reason,
        }

    def get_default_model(self) -> str:
        """Get the default model."""
        return "gpt-5-codex"
```

**That's it!** No ContentBlock, no LLMResponse, no conversions, no factory pattern.

---

### 3. Update ClippyAgent

**File:** `src/clippy/agent.py`

#### 3.1 Simplify initialization

```python
def __init__(
    self,
    permission_manager: PermissionManager,
    executor: ActionExecutor,
    api_key: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
):
    """Initialize the ClippyAgent."""
    self.permission_manager = permission_manager
    self.executor = executor

    # Create provider (OpenAI-compatible)
    self.provider = LLMProvider(api_key=api_key, base_url=base_url)
    self.model = model or os.getenv("CLIPPY_MODEL") or self.provider.get_default_model()

    self.console = Console()
    self.conversation_history: list[dict[str, Any]] = []
    self.interrupted = False
```

#### 3.2 Update conversation history (OpenAI format)

```python
def run(self, user_message: str, auto_approve_all: bool = False) -> str:
    """Run the agent with a user message."""
    self.interrupted = False

    # Initialize with system message if first run
    if not self.conversation_history:
        self.conversation_history.append({
            "role": "system",
            "content": self._create_system_prompt()
        })

    # Add user message
    self.conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # ... rest of logic
```

#### 3.3 Update response handling

```python
def _run_agent_loop(self, auto_approve_all: bool = False) -> str:
    """Run the main agent loop."""
    max_iterations = 25

    for iteration in range(max_iterations):
        if self.interrupted:
            raise InterruptedException()

        # Call provider (returns OpenAI message dict)
        response = self.provider.create_message(
            messages=self.conversation_history,
            tools=TOOLS,
            max_tokens=int(os.getenv("CLIPPY_MAX_TOKENS", "4096")),
            model=self.model,
        )

        # Add assistant message to history
        assistant_message = {
            "role": "assistant",
            "content": response.get("content"),
        }
        if response.get("tool_calls"):
            assistant_message["tool_calls"] = response["tool_calls"]

        self.conversation_history.append(assistant_message)

        # Display text response if present
        if response.get("content"):
            self.console.print(
                Panel(
                    Markdown(response["content"]),
                    title="[bold green]clippy-code[/bold green]",
                    border_style="green",
                )
            )

        # Handle tool calls
        if response.get("tool_calls"):
            for tool_call in response["tool_calls"]:
                import json

                success = self._handle_tool_use(
                    tool_call["function"]["name"],
                    json.loads(tool_call["function"]["arguments"]),
                    tool_call["id"],
                    auto_approve_all,
                )
        else:
            # No tool calls, we're done
            return response.get("content", "")

        # Check finish reason
        if response.get("finish_reason") == "stop":
            return response.get("content", "")

    return "Maximum iterations reached. Task may be incomplete."
```

#### 3.4 Update tool result handling

```python
def _add_tool_result(self, tool_use_id: str, success: bool, message: str, result: Any):
    """Add a tool result to the conversation history."""
    content = message
    if result:
        content += f"\n\n{result}"

    # Add error prefix if failed
    if not success:
        content = f"ERROR: {content}"

    # Add tool result message (OpenAI format)
    self.conversation_history.append({
        "role": "tool",
        "tool_call_id": tool_use_id,
        "content": content,
    })
```

---

### 4. Update CLI

**File:** `src/clippy/cli.py`

```python
def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="clippy-code - A CLI coding agent powered by OpenAI-compatible LLMs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "prompt",
        nargs="*",
        help="The task or question for clippy-code (one-shot mode)",
    )

    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start in interactive mode (REPL)",
    )

    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Auto-approve all actions (use with caution!)",
    )

    parser.add_argument(
        "--model",
        type=str,
        help="Model to use (e.g., gpt-5-codex, llama3.1-8b)",
    )

    parser.add_argument(
        "--base-url",
        type=str,
        help="Base URL for OpenAI-compatible API (e.g., https://api.cerebras.ai/v1)",
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to custom permission config file",
    )

    return parser


def main():
    """Main entry point for clippy-code."""
    # Load environment variables
    load_env()

    # Parse arguments
    parser = create_parser()
    args = parser.parse_args()

    # Get API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        console = Console()
        console.print(
            "[bold red]Error:[/bold red] OPENAI_API_KEY not found in environment.\n\n"
            "Please set your API key:\n"
            "  1. Create a .env file in the current directory, or\n"
            "  2. Create a .clippy.env file in your home directory, or\n"
            "  3. Set the OPENAI_API_KEY environment variable\n\n"
            "Example .env file:\n"
            "  OPENAI_API_KEY=your_api_key_here\n"
            "  OPENAI_BASE_URL=https://api.cerebras.ai/v1  # Optional, for alternate providers"
        )
        sys.exit(1)

    # Create permission manager
    permission_manager = PermissionManager(PermissionConfig())

    # Create executor and agent
    executor = ActionExecutor(permission_manager)
    agent = ClippyAgent(
        permission_manager=permission_manager,
        executor=executor,
        api_key=api_key,
        model=args.model,
        base_url=args.base_url or os.getenv("OPENAI_BASE_URL"),
    )

    # Run in appropriate mode
    if args.interactive or not args.prompt:
        run_interactive(agent, args.yes)
    else:
        prompt = " ".join(args.prompt)
        run_one_shot(agent, prompt, args.yes)
```

---

### 5. Update Documentation

**File:** `CLAUDE.md`

Update to reflect OpenAI-only approach:

- Remove references to `--provider` flag
- Update environment variables (remove `CLIPPY_PROVIDER`, `ANTHROPIC_API_KEY`)
- Update examples to show different providers via `--base-url`
- Update architecture section

---

## Files to Delete

- Remove `anthropic` from dependencies in `pyproject.toml`

---

## Files to Update

1. ✅ `SIMPLIFIED_MIGRATION.md` (this file)
2. `src/clippy/tools.py` - Update tool format
3. `src/clippy/providers.py` - Simplify to OpenAI-only
4. `src/clippy/agent.py` - Use OpenAI format throughout
5. `src/clippy/cli.py` - Remove provider selection, simplify
6. `tests/` - Update all tests
7. `CLAUDE.md` - Update documentation
8. `README.md` - Update if exists
9. `pyproject.toml` - Remove anthropic dependency

---

## Benefits

### Code Reduction

- **providers.py**: ~370 lines → ~50 lines (87% reduction)
- **agent.py**: Simpler message handling
- **cli.py**: Remove provider selection logic
- **Overall**: ~40% less code

### Maintenance

- No format conversions to maintain
- No abstraction layer bugs
- Easier for contributors to understand

### User Experience

- Simpler configuration (just API key + optional base URL)
- Better error messages (native OpenAI errors)
- More providers supported out-of-box

---

## Migration Effort

- **Phase 1 (Tools):** 15 minutes
- **Phase 2 (Providers):** 30 minutes (mostly deletion!)
- **Phase 3 (Agent):** 1 hour
- **Phase 4 (CLI):** 30 minutes
- **Phase 5 (Tests):** 1 hour
- **Phase 6 (Docs):** 30 minutes
- **Total:** ~4 hours (half the original estimate!)

---

## Example Usage After Migration

```bash
# OpenAI
export OPENAI_API_KEY=sk-...
clippy "list all Python files"

# Cerebras
export OPENAI_API_KEY=csk-...
export OPENAI_BASE_URL=https://api.cerebras.ai/v1
export CLIPPY_MODEL=llama3.1-8b
clippy "list all Python files"

# Ollama (local)
export OPENAI_BASE_URL=http://localhost:11434/v1
export CLIPPY_MODEL=llama2
clippy -i  # Interactive mode

# Together AI
clippy --base-url https://api.together.xyz/v1 --model meta-llama/Llama-3-8b-chat-hf "your task"
```

One simple interface, infinite providers! 🚀
