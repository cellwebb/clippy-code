"""AI agent with model-agnostic LLM support."""

import os
from typing import List, Dict, Any, Optional
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown

from .tools import TOOLS
from .executor import ActionExecutor
from .permissions import PermissionManager, ActionType
from .providers import LLMProvider, ProviderFactory, ContentBlockType


class InterruptedException(Exception):
    """Exception raised when user interrupts execution."""
    pass


class ClippyAgent:
    """AI coding agent with model-agnostic LLM support."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        provider: Optional[LLMProvider] = None,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the ClippyAgent.

        Args:
            permission_manager: Permission manager instance
            executor: Action executor instance
            provider: Pre-configured LLM provider (optional)
            provider_name: Name of provider to use if provider not given (e.g., "anthropic", "openai")
            api_key: API key for the provider
            model: Model identifier to use
        """
        self.permission_manager = permission_manager
        self.executor = executor

        # Create or use provided provider
        if provider:
            self.provider = provider
        else:
            # Default to anthropic if not specified
            provider_name = provider_name or os.getenv("CLIPPY_PROVIDER", "anthropic")
            self.provider = ProviderFactory.create_provider(
                provider_name=provider_name,
                api_key=api_key
            )

        # Set model (use provider default if not specified)
        self.model = model or os.getenv("CLIPPY_MODEL") or self.provider.get_default_model()

        self.console = Console()
        self.conversation_history: List[Dict[str, Any]] = []
        self.interrupted = False

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        return """You are CLIppy, a helpful CLI coding assistant. You help users with software development tasks.

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

        # Add user message to history
        self.conversation_history.append({"role": "user", "content": user_message})

        # Show user message
        self.console.print(Panel(user_message, title="[bold blue]You[/bold blue]", border_style="blue"))

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

            # Call LLM provider
            response = self.provider.create_message(
                messages=self.conversation_history,
                system=self._create_system_prompt(),
                tools=TOOLS,
                max_tokens=int(os.getenv("CLIPPY_MAX_TOKENS", "4096")),
                model=self.model,
            )

            # Process response - convert content blocks back to original format for conversation history
            assistant_content = []
            for block in response.content:
                if block.type == ContentBlockType.TEXT:
                    assistant_content.append({"type": "text", "text": block.text})
                elif block.type == ContentBlockType.TOOL_USE:
                    assistant_content.append({
                        "type": "tool_use",
                        "name": block.name,
                        "input": block.input,
                        "id": block.id
                    })

            assistant_message = {"role": "assistant", "content": assistant_content}
            self.conversation_history.append(assistant_message)

            # Handle response content
            has_tool_use = False
            text_response = ""

            for block in response.content:
                if block.type == ContentBlockType.TEXT:
                    text_response += block.text
                    # Show agent's thinking/response
                    self.console.print(Panel(
                        Markdown(block.text),
                        title="[bold green]CLIppy[/bold green]",
                        border_style="green"
                    ))
                elif block.type == ContentBlockType.TOOL_USE:
                    has_tool_use = True
                    success = self._handle_tool_use(
                        block.name, block.input, block.id, auto_approve_all
                    )
                    if not success:
                        # Tool execution failed or was denied
                        continue

            # If no tool use, we're done
            if not has_tool_use:
                return text_response

            # Check stop reason
            if response.stop_reason == "end_turn":
                return text_response

        return "Maximum iterations reached. Task may be incomplete."

    def _handle_tool_use(
        self, tool_name: str, tool_input: Dict[str, Any], tool_use_id: str, auto_approve_all: bool
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

        # Check permission
        permission = self.permission_manager.check_permission(action_type)

        # Show what the agent wants to do
        self._display_tool_request(tool_name, tool_input)

        # Check if we need approval
        needs_approval = not auto_approve_all and not self.permission_manager.config.can_auto_execute(action_type)

        if self.permission_manager.config.is_denied(action_type):
            self.console.print(f"[bold red]✗ Action denied by policy[/bold red]")
            self._add_tool_result(tool_use_id, False, "Action denied by policy", None)
            return False

        if needs_approval:
            approved = self._ask_approval(tool_name, tool_input)
            if not approved:
                self.console.print(f"[bold yellow]⊘ Action rejected by user[/bold yellow]")
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

    def _display_tool_request(self, tool_name: str, tool_input: Dict[str, Any]):
        """Display what tool the agent wants to use."""
        input_str = "\n".join(f"  {k}: {v}" for k, v in tool_input.items())
        self.console.print(f"\n[bold cyan]→ {tool_name}[/bold cyan]")
        self.console.print(f"[cyan]{input_str}[/cyan]")

    def _ask_approval(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
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

    def _add_tool_result(
        self, tool_use_id: str, success: bool, message: str, result: Any
    ):
        """Add a tool result to the conversation history."""
        content = message
        if result:
            content += f"\n\n{result}"

        # Create tool result message
        tool_result = {
            "role": "user",
            "content": [
                {
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": content,
                    "is_error": not success,
                }
            ],
        }
        self.conversation_history.append(tool_result)

    def reset_conversation(self):
        """Reset the conversation history."""
        self.conversation_history = []
        self.interrupted = False
