"""AI agent with OpenAI-compatible LLM support."""

import json
import logging
from pathlib import Path
from typing import Any

import tiktoken
from rich.console import Console
from rich.panel import Panel

from .executor import ActionExecutor
from .permissions import ActionType, PermissionManager
from .providers import LLMProvider
from .tools import TOOLS

logger = logging.getLogger(__name__)


class InterruptedExceptionError(Exception):
    """Exception raised when user interrupts execution."""

    pass


class ClippyAgent:
    """AI coding assistant powered by OpenAI-compatible LLMs - here to help you with
    that paperclip!."""

    def __init__(
        self,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
        approval_callback: Any = None,
    ) -> None:
        """
        Initialize the ClippyAgent.

        Args:
            permission_manager: Permission manager instance
            executor: Action executor instance
            api_key: API key for OpenAI-compatible provider
            model: Model identifier to use
            base_url: Base URL for OpenAI-compatible API (for alternate providers)
            approval_callback: Optional callback function for approval requests
                             (used in document mode). Should accept (tool_name, tool_input)
                             and return bool (True for approve, False for deny).
                             Can raise InterruptedExceptionError to stop execution.
        """
        self.permission_manager = permission_manager
        self.executor = executor

        # Store credentials for provider recreation
        self.api_key = api_key
        self.base_url = base_url

        # Create provider (OpenAI-compatible)
        self.provider = LLMProvider(api_key=api_key, base_url=base_url)

        # Set model (use provider default if not specified)
        self.model = model or self.provider.get_default_model()

        self.console = Console()
        self.conversation_history: list[dict[str, Any]] = []
        self.interrupted = False
        self.approval_callback = approval_callback

    def _create_system_prompt(self) -> str:
        """Create the system prompt for the agent."""
        base_prompt = """You are Clippy, the helpful Microsoft Office assistant! It looks like
you're trying to code something. I'm here to assist you with that.

You have access to various tools to help with software development tasks. Just like
the classic Clippy, you'll do your best to be friendly, helpful, and a bit quirky.

Important guidelines:
- Always read files before modifying them to understand the context
- Be cautious with destructive operations (deleting files, overwriting code)
- Explain your reasoning before taking significant actions
- When writing code, follow best practices and the existing code style
- If you're unsure about something, ask the user for clarification

You are running in a CLI environment. Be concise but informative in your responses,
and remember to be helpful!

Clippy's Classic Style:
- Use friendly, helpful language with a touch of enthusiasm
- Make observations like classic Clippy ("It looks like you're trying to...")
- Offer assistance proactively ("Would you like me to help you with...")
- Include paperclip-themed emojis (📎) to enhance the experience, but never at
  the start of your message
- Ask questions about what the user wants to do
- Provide clear explanations of your actions

Examples of how Clippy talks:
- "Hi there! It looks like you're trying to read a file. 📎 Would you like me
  to help you with that?"
- "I see you're working on a Python project! 📎 Let me help you find the files
  you need."
- "Would you like me to explain what I'm doing in simpler terms? 📎"
- "It seems like you're trying to create a new directory. 📎 I can help you
  with my paperclip-shaped tools!"
- "I noticed you're working with JSON data. 📎 Would you like some help
  parsing it?"

Available Tools:
- read_file: Read the contents of a file
- write_file: Write content to a file
- delete_file: Delete a file
- list_directory: List contents of a directory
- create_directory: Create a new directory
- execute_command: Execute shell commands
- search_files: Search for files with patterns
- get_file_info: Get file metadata
- read_files: Read the contents of multiple files at once

Remember to be helpful, friendly, and a bit quirky like the classic Microsoft Office
assistant Clippy! Include paperclip emojis (📎) in your responses to enhance the Clippy
experience, but never at the beginning of your messages since there's already a paperclip
emoji automatically added. You can include them elsewhere in your messages or at the end.
Focus on being genuinely helpful while maintaining Clippy's distinctive personality."""

        # Check for agent documentation files in order of preference
        agent_docs = ["AGENTS.md", "agents.md", "agent.md", "AGENT.md"]
        for doc_file in agent_docs:
            doc_path = Path(doc_file)
            if doc_path.exists():
                try:
                    agents_content = doc_path.read_text(encoding="utf-8")
                    # Append the agent documentation content to the system prompt
                    return f"{base_prompt}\n\nPROJECT DOCUMENTATION:\n{agents_content}"
                except Exception as e:
                    logger.warning(f"Failed to read {doc_file}: {e}")
                    # Continue to next file if reading fails
                    continue

        # Return base prompt if no documentation files exist
        return base_prompt

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

        try:
            response = self._run_agent_loop(auto_approve_all)
            return response
        except InterruptedExceptionError:
            return "Execution interrupted by user."

    def _run_agent_loop(self, auto_approve_all: bool = False) -> str:
        """Run the main agent loop."""
        max_iterations = 25  # Prevent infinite loops

        for iteration in range(max_iterations):
            if self.interrupted:
                raise InterruptedExceptionError()

            # Call provider (returns OpenAI message dict)
            try:
                response = self.provider.create_message(
                    messages=self.conversation_history,
                    tools=TOOLS,
                    model=self.model,
                )
            except Exception as e:
                # Handle API errors gracefully
                error_message = self._format_api_error(e)
                self.console.print(
                    Panel(
                        f"[bold red]API Error:[/bold red]\n\n{error_message}",
                        title="[bold red]Error[/bold red]",
                        border_style="red",
                    )
                )
                logger.error(f"API error in agent loop: {type(e).__name__}: {e}", exc_info=True)
                raise

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
            # (content was already streamed by the provider)
            if not has_tool_calls:
                content = response.get("content", "")
                return content if isinstance(content, str) else ""

            # Check finish reason
            # (content was already streamed by the provider)
            if response.get("finish_reason") == "stop":
                content = response.get("content", "")
                return content if isinstance(content, str) else ""

        # Max iterations reached - display warning
        self.console.print(
            Panel(
                "[bold yellow]⚠ Maximum Iterations Reached[/bold yellow]\n\n"
                "The agent has reached the maximum number of iterations (25) and has stopped.\n"
                "The task may be incomplete.\n\n"
                "[dim]This limit prevents infinite loops. You can:\n"
                "• Continue with a new request\n"
                "• Break down the task into smaller steps\n"
                "• Use /reset to start fresh[/dim]",
                title="[bold yellow]Iteration Limit[/bold yellow]",
                border_style="yellow",
            )
        )
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
            "read_files": ActionType.READ_FILE,  # Uses the same permission as read_file
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

    def _display_tool_request(self, tool_name: str, tool_input: dict[str, Any]) -> None:
        """Display what tool the agent wants to use."""
        input_str = "\n".join(f"  {k}: {v}" for k, v in tool_input.items())
        self.console.print(f"\n[bold cyan]→ {tool_name}[/bold cyan]")
        self.console.print(f"[cyan]{input_str}[/cyan]")

    def _ask_approval(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Ask user for approval to execute an action."""
        # Use callback if provided (for document mode)
        if self.approval_callback:
            try:
                result = self.approval_callback(tool_name, tool_input)
                return bool(result)  # Ensure we return a bool
            except InterruptedExceptionError:
                self.interrupted = True
                raise

        # Default behavior: use input() (for interactive mode)
        try:
            response = input("\n[?] Approve this action? [y/N/stop]: ").strip().lower()
            if response == "stop":
                self.interrupted = True
                raise InterruptedExceptionError()
            return response == "y"
        except (KeyboardInterrupt, EOFError):
            self.interrupted = True
            raise InterruptedExceptionError()

    def _add_tool_result(self, tool_use_id: str, success: bool, message: str, result: Any) -> None:
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

    def _format_api_error(self, error: Exception) -> str:
        """Format API errors into user-friendly messages."""
        try:
            from openai import (
                APIConnectionError,
                APITimeoutError,
                AuthenticationError,
                BadRequestError,
                InternalServerError,
                RateLimitError,
            )

            if isinstance(error, AuthenticationError):
                return (
                    "Authentication failed. Please check your API key.\n\n"
                    "Set OPENAI_API_KEY in your environment or .env file."
                )
            elif isinstance(error, RateLimitError):
                return (
                    "Rate limit exceeded. The API has throttled your requests.\n\n"
                    "The system will automatically retry with exponential backoff."
                )
            elif isinstance(error, APIConnectionError):
                return (
                    "Connection error. Failed to connect to the API.\n\n"
                    "Check your internet connection or base URL settings."
                )
            elif isinstance(error, APITimeoutError):
                return (
                    "Request timeout. The API took too long to respond.\n\n"
                    "The system will automatically retry."
                )
            elif isinstance(error, BadRequestError):
                return f"Bad request. The API rejected the request.\n\nDetails: {str(error)}"
            elif isinstance(error, InternalServerError):
                return (
                    "Server error. The API encountered an internal error.\n\n"
                    "The system will automatically retry."
                )
            else:
                return f"{type(error).__name__}: {str(error)}"
        except ImportError:
            return f"{type(error).__name__}: {str(error)}"

    def reset_conversation(self) -> None:
        """Reset the conversation history."""
        self.conversation_history = []
        self.interrupted = False

    def switch_model(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
    ) -> tuple[bool, str]:
        """
        Switch to a different model or provider.

        Args:
            model: New model identifier (if None, keeps current)
            base_url: New base URL (if None, keeps current)
            api_key: New API key (if None, keeps current)

        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Update base_url if provided
            new_base_url = base_url if base_url is not None else self.base_url

            # Update model if provided
            new_model = model if model is not None else self.model

            # Update API key if provided
            new_api_key = api_key if api_key is not None else self.api_key

            # Create new provider with updated settings
            self.provider = LLMProvider(api_key=new_api_key, base_url=new_base_url)

            # Update instance variables
            self.base_url = new_base_url
            self.model = new_model
            self.api_key = new_api_key

            # Build success message
            provider_info = f" ({new_base_url})" if new_base_url else " (OpenAI)"
            message = f"Switched to model: {new_model}{provider_info}"

            return True, message

        except Exception as e:
            return False, f"Failed to switch model: {e}"

    def get_token_count(self) -> dict[str, Any]:
        """
        Get token usage statistics for the current conversation.

        Returns:
            Dictionary with token usage information including:
            - total_tokens: Total tokens in conversation history
            - usage_percent: Percentage of typical context window used (estimate)
            - message_count: Number of messages in history
        """
        try:
            # Try to get the appropriate encoding for the model
            # Default to cl100k_base which works for GPT-4, GPT-3.5-turbo, etc.
            try:
                encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Fall back to cl100k_base for unknown models
                encoding = tiktoken.get_encoding("cl100k_base")

            # Count tokens in conversation history
            total_tokens = 0
            for message in self.conversation_history:
                # Count tokens in role
                total_tokens += len(encoding.encode(message.get("role", "")))

                # Count tokens in content
                if message.get("content"):
                    total_tokens += len(encoding.encode(message["content"]))

                # Count tokens in tool calls (if present)
                if message.get("tool_calls"):
                    for tool_call in message["tool_calls"]:
                        total_tokens += len(encoding.encode(json.dumps(tool_call)))

                # Add overhead for message formatting (~4 tokens per message)
                total_tokens += 4

            # Estimate context window (most models have 128k, some have 8k-32k)
            # This is a rough estimate
            estimated_context_window = 128000  # Conservative estimate
            usage_percent = (total_tokens / estimated_context_window) * 100

            return {
                "total_tokens": total_tokens,
                "usage_percent": usage_percent,
                "message_count": len(self.conversation_history),
                "model": self.model,
                "base_url": self.base_url,
            }

        except Exception as e:
            # Return error info if token counting fails
            return {
                "error": str(e),
                "message_count": len(self.conversation_history),
                "model": self.model,
                "base_url": self.base_url,
            }

    def compact_conversation(self, keep_recent: int = 4) -> tuple[bool, str, dict[str, Any]]:
        """
        Compact the conversation history by summarizing older messages.

        This helps manage context window limits by condensing older conversation
        history into a summary while keeping recent messages intact.

        Args:
            keep_recent: Number of recent messages to keep intact (default: 4)

        Returns:
            Tuple of (success: bool, message: str, stats: dict)
            Stats include before/after token counts and reduction percentage
        """
        # Need at least system + user + assistant + keep_recent messages to compact
        min_messages = 3 + keep_recent
        if len(self.conversation_history) <= min_messages:
            return (
                False,
                f"Conversation too short to compact (need >{min_messages} messages)",
                {},
            )

        # Get token count before compaction
        before_stats = self.get_token_count()
        if "error" in before_stats:
            return False, f"Error counting tokens: {before_stats['error']}", {}

        before_tokens = before_stats["total_tokens"]

        try:
            # Separate conversation parts
            system_msg = self.conversation_history[0]  # Keep system prompt
            recent_msgs = self.conversation_history[-keep_recent:]  # Keep recent messages
            to_summarize = self.conversation_history[1:-keep_recent]  # Messages to compact

            if not to_summarize:
                return False, "No messages to compact", {}

            # Create summarization prompt
            summary_request = {
                "role": "user",
                "content": """Please create a concise summary of the conversation so far.
Focus on:
- Key tasks and requests made
- Important decisions and outcomes
- Relevant code changes or file operations
- Any ongoing context needed for future requests

Keep the summary brief but informative (aim for 200-400 words).""",
            }

            # Build temporary conversation for summarization
            summarization_conversation = [system_msg] + to_summarize + [summary_request]

            # Call LLM to create summary
            response = self.provider.create_message(
                messages=summarization_conversation,
                tools=[],  # No tools needed for summarization
                model=self.model,
            )

            summary_content = response.get("content", "")
            if not summary_content:
                return False, "Failed to generate summary", {}

            # Create new conversation history
            summary_msg = {
                "role": "assistant",
                "content": f"[CONVERSATION SUMMARY]\n\n{summary_content}\n\n[END SUMMARY]",
            }

            # Rebuild conversation: system + summary + recent messages
            self.conversation_history = [system_msg, summary_msg] + recent_msgs

            # Get token count after compaction
            after_stats = self.get_token_count()
            after_tokens = after_stats["total_tokens"]

            # Calculate reduction
            tokens_saved = before_tokens - after_tokens
            reduction_percent = (tokens_saved / before_tokens) * 100 if before_tokens > 0 else 0

            stats = {
                "before_tokens": before_tokens,
                "after_tokens": after_tokens,
                "tokens_saved": tokens_saved,
                "reduction_percent": reduction_percent,
                "messages_before": before_stats["message_count"],
                "messages_after": len(self.conversation_history),
                "messages_summarized": len(to_summarize),
            }

            success_msg = (
                f"Conversation compacted: {before_tokens:,} → {after_tokens:,} tokens "
                f"({reduction_percent:.1f}% reduction)"
            )

            return True, success_msg, stats

        except Exception as e:
            logger.error(f"Error during conversation compaction: {e}", exc_info=True)
            return False, f"Error compacting conversation: {e}", {}
