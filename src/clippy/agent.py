"""AI agent with OpenAI-compatible LLM support."""

import json
import os
from typing import Any

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from .executor import ActionExecutor
from .permissions import ActionType, PermissionManager
from .providers import LLMProvider
from .tools import TOOLS


class InterruptedException(Exception):
    """Exception raised when user interrupts execution."""

    pass


class ClippyAgent:
    """AI coding agent powered by OpenAI-compatible LLMs."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ):
        """
        Initialize the ClippyAgent.

        Args:
            permission_manager: Permission manager instance
            executor: Action executor instance
            api_key: API key for OpenAI-compatible provider
            model: Model identifier to use
            base_url: Base URL for OpenAI-compatible API (for alternate providers)
        """
        self.permission_manager = permission_manager
        self.executor = executor

        # Create provider (OpenAI-compatible)
        self.provider = LLMProvider(api_key=api_key, base_url=base_url)

        # Set model (use provider default if not specified)
        self.model = model or self.provider.get_default_model()

        self.console = Console()
        self.conversation_history: list[dict[str, Any]] = []
        self.interrupted = False

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        return """You are clippy-code, a helpful CLI coding assistant. You help users with software development tasks.

You have access to tools to read files, write code, execute commands, and more. Use these tools to help users accomplish their goals.

Important guidelines:
- Always read files before modifying them to understand the context
- Be cautious with destructive operations (deleting files, overwriting code)
- Explain your reasoning before taking significant actions
- When writing code, follow best practices and the existing code style
- If you're unsure about something, ask the user for clarification

You are running in a CLI environment. Be concise but informative in your responses."""

    def run(self, user_message: str, auto_approve_all: bool = False) -> str:
        """
        Run the agent with a user message.

        Args:
            user_message: The user's request
            auto_approve_all: If True, auto-approve all actions (dangerous!)

        Returns:
            The final response from the agent
        """
        self.interrupted = False

        # Initialize with system message if first run
        if not self.conversation_history:
            self.conversation_history.append(
                {"role": "system", "content": self._create_system_prompt()}
            )

        # Add user message
        self.conversation_history.append({"role": "user", "content": user_message})

        # Show user message
        self.console.print(
            Panel(user_message, title="[bold blue]You[/bold blue]", border_style="blue")
        )

        try:
            response = self._run_agent_loop(auto_approve_all)
            return response
        except InterruptedException:
            return "Execution interrupted by user."

    def _run_agent_loop(self, auto_approve_all: bool = False) -> str:
        """Run the main agent loop."""
        max_iterations = 25  # Prevent infinite loops

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

            # Build assistant message for history
            assistant_message: dict[str, Any] = {
                "role": "assistant",
            }

            # Add content if present
            if response.get("content"):
                assistant_message["content"] = response["content"]

            # Add tool calls if present
            if response.get("tool_calls"):
                assistant_message["tool_calls"] = response["tool_calls"]

            # Add to conversation history
            self.conversation_history.append(assistant_message)

            # Display text response if present
            if response.get("content"):
                self.console.print(
                    Panel(
                        Markdown(response["content"]),
                        title="[bold green]CLIppy[/bold green]",
                        border_style="green",
                    )
                )

            # Handle tool calls
            has_tool_calls = False
            if response.get("tool_calls"):
                has_tool_calls = True
                for tool_call in response["tool_calls"]:
                    # Parse tool arguments (JSON string -> dict)
                    try:
                        tool_input = json.loads(tool_call["function"]["arguments"])
                    except json.JSONDecodeError as e:
                        self.console.print(
                            f"[bold red]Error parsing tool arguments: {e}[/bold red]"
                        )
                        self._add_tool_result(
                            tool_call["id"],
                            False,
                            f"Error parsing tool arguments: {e}",
                            None,
                        )
                        continue

                    success = self._handle_tool_use(
                        tool_call["function"]["name"],
                        tool_input,
                        tool_call["id"],
                        auto_approve_all,
                    )
                    if not success:
                        # Tool execution failed or was denied
                        continue

            # If no tool calls, we're done
            if not has_tool_calls:
                return response.get("content", "")

            # Check finish reason
            if response.get("finish_reason") == "stop":
                return response.get("content", "")

        return "Maximum iterations reached. Task may be incomplete."

    def _handle_tool_use(
        self, tool_name: str, tool_input: dict[str, Any], tool_use_id: str, auto_approve_all: bool
    ) -> bool:
        """
        Handle a tool use request.

        Returns:
            True if the tool was executed successfully, False otherwise
        """
        # Map tool names to action types
        action_map = {
            "read_file": ActionType.READ_FILE,
            "write_file": ActionType.WRITE_FILE,
            "delete_file": ActionType.DELETE_FILE,
            "list_directory": ActionType.LIST_DIR,
            "create_directory": ActionType.CREATE_DIR,
            "execute_command": ActionType.EXECUTE_COMMAND,
            "search_files": ActionType.SEARCH_FILES,
            "get_file_info": ActionType.GET_FILE_INFO,
        }

        action_type = action_map.get(tool_name)
        if not action_type:
            self._add_tool_result(tool_use_id, False, f"Unknown tool: {tool_name}", None)
            return False

        # Show what the agent wants to do
        self._display_tool_request(tool_name, tool_input)

        # Check if we need approval
        needs_approval = (
            not auto_approve_all
            and not self.permission_manager.config.can_auto_execute(action_type)
        )

        if self.permission_manager.config.is_denied(action_type):
            self.console.print("[bold red]✗ Action denied by policy[/bold red]")
            self._add_tool_result(tool_use_id, False, "Action denied by policy", None)
            return False

        if needs_approval:
            approved = self._ask_approval(tool_name, tool_input)
            if not approved:
                self.console.print("[bold yellow]⊘ Action rejected by user[/bold yellow]")
                self._add_tool_result(tool_use_id, False, "Action rejected by user", None)
                return False

        # Execute the tool
        success, message, result = self.executor.execute(tool_name, tool_input)

        # Show result
        if success:
            self.console.print(f"[bold green]✓ {message}[/bold green]")
        else:
            self.console.print(f"[bold red]✗ {message}[/bold red]")

        # Add result to conversation
        self._add_tool_result(tool_use_id, success, message, result)

        return success

    def _display_tool_request(self, tool_name: str, tool_input: dict[str, Any]):
        """Display what tool the agent wants to use."""
        input_str = "\n".join(f"  {k}: {v}" for k, v in tool_input.items())
        self.console.print(f"\n[bold cyan]→ {tool_name}[/bold cyan]")
        self.console.print(f"[cyan]{input_str}[/cyan]")

    def _ask_approval(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Ask user for approval to execute an action."""
        try:
            response = input("\n[?] Approve this action? [y/N/stop]: ").strip().lower()
            if response == "stop":
                self.interrupted = True
                raise InterruptedException()
            return response == "y"
        except (KeyboardInterrupt, EOFError):
            self.interrupted = True
            raise InterruptedException()

    def _add_tool_result(self, tool_use_id: str, success: bool, message: str, result: Any):
        """Add a tool result to the conversation history."""
        content = message
        if result:
            content += f"\n\n{result}"

        # Add error prefix if failed (OpenAI doesn't have is_error flag)
        if not success:
            content = f"ERROR: {content}"

        # Add tool result message (OpenAI format)
        self.conversation_history.append(
            {
                "role": "tool",
                "tool_call_id": tool_use_id,
                "content": content,
            }
        )

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.interrupted = False
