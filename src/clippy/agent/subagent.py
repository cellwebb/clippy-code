"""Subagent implementation for specialized task execution."""

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from ..executor import ActionExecutor
from ..permissions import PermissionManager
from ..providers import LLMProvider
from .conversation import create_system_prompt, get_token_count
from .loop import run_agent_loop

if TYPE_CHECKING:
    from .core import ClippyAgent

logger = logging.getLogger(__name__)


class SubAgentConsoleWrapper:
    """
    Console wrapper that prefixes all output with subagent indicator.

    This makes it clear when messages/tool calls are from a subagent vs main agent.
    """

    def __init__(self, wrapped_console: Any, subagent_name: str, subagent_type: str):
        """
        Initialize console wrapper.

        Args:
            wrapped_console: The original console to wrap
            subagent_name: Name of the subagent
            subagent_type: Type of the subagent
        """
        self._console = wrapped_console
        self._subagent_name = subagent_name
        self._subagent_type = subagent_type
        self._prefix = f"[dim cyan]\\[{subagent_type}:{subagent_name}][/dim cyan] "

    def print(self, *args: Any, **kwargs: Any) -> None:
        """Print with subagent prefix."""
        # Add prefix to the first argument if it's a string
        if args and isinstance(args[0], str):
            prefixed_args = (self._prefix + args[0],) + args[1:]
            self._console.print(*prefixed_args, **kwargs)
        else:
            self._console.print(self._prefix, *args, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Delegate all other attributes to wrapped console."""
        return getattr(self._console, name)


@dataclass
class SubAgentResult:
    """Result from a subagent execution."""

    success: bool
    output: str  # Final response from subagent
    error: str | None  # Error message if failed
    iterations_used: int  # How many iterations the subagent took
    tokens_used: dict[str, int] = field(default_factory=dict)  # Token usage statistics
    tools_executed: list[str] = field(default_factory=list)  # List of tools used
    execution_time: float = 0.0  # Time in seconds
    metadata: dict[str, Any] = field(default_factory=dict)  # Additional metadata


@dataclass
class SubAgentConfig:
    """Configuration for a subagent instance."""

    name: str
    task: str
    subagent_type: str = "general"
    system_prompt: str | None = None
    allowed_tools: list[str] | str | None = None  # Can be list, "all", or None
    model: str | None = None
    max_iterations: int = 25
    timeout: int | float = 300
    context: dict[str, Any] = field(default_factory=dict)


class SubAgentStatus:
    """Status of a subagent execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    INTERRUPTED = "interrupted"


class SubAgent:
    """
    A specialized agent instance for handling specific subtasks.

    Attributes:
        config: Configuration for this subagent
        parent_agent: Reference to the main agent (for context if needed)
        status: Current execution status
        result: Result of execution (available after completion)
        start_time: When execution started
        end_time: When execution ended
    """

    def __init__(
        self,
        config: SubAgentConfig,
        parent_agent: "ClippyAgent",
        permission_manager: PermissionManager,
        executor: ActionExecutor,
    ) -> None:
        """
        Initialize a SubAgent instance.

        Args:
            config: Configuration for this subagent
            parent_agent: Reference to the main agent
            permission_manager: Permission manager instance
            executor: Action executor instance
        """
        self.config = config
        self.parent_agent = parent_agent
        self.permission_manager = permission_manager
        self.executor = executor

        # Execution state
        self.status = SubAgentStatus.PENDING
        self.result: SubAgentResult | None = None
        self.start_time: float | None = None
        self.end_time: float | None = None
        self.interrupted = False

        # Create isolated provider (use same credentials as parent)
        self.provider = LLMProvider(
            api_key=parent_agent.api_key,
            base_url=parent_agent.base_url,
            provider_config=parent_agent.provider_config,
        )

        # Determine model to use
        self.model = config.model or parent_agent.model

        # Create console wrapper for prefixed output
        self.console = SubAgentConsoleWrapper(
            wrapped_console=parent_agent.console,
            subagent_name=config.name,
            subagent_type=config.subagent_type,
        )

        # Isolated conversation history
        self.conversation_history: list[dict[str, Any]] = []

        # Initialize system prompt
        self._initialize_system_prompt()

    def _initialize_system_prompt(self) -> None:
        """Initialize the conversation with system prompt."""
        # Use custom system prompt if provided, otherwise use type-specific prompt
        if self.config.system_prompt:
            system_prompt = self.config.system_prompt
        else:
            # Import here to avoid circular imports
            from .subagent_types import get_subagent_config

            type_config = get_subagent_config(self.config.subagent_type)
            system_prompt = type_config.get("system_prompt", create_system_prompt())

        # Add context information if provided
        if self.config.context:
            context_str = "\n\nContext:\n"
            for key, value in self.config.context.items():
                context_str += f"- {key}: {value}\n"
            system_prompt += context_str

        self.conversation_history.append({"role": "system", "content": system_prompt})

    def run(self) -> SubAgentResult:
        """
        Execute the subagent's task.

        Returns:
            SubAgentResult with execution details
        """
        if self.status != SubAgentStatus.PENDING:
            raise RuntimeError(f"SubAgent is not in PENDING state: {self.status}")

        self.status = SubAgentStatus.RUNNING
        self.start_time = time.time()

        try:
            logger.info(f"Starting subagent '{self.config.name}' with task: {self.config.task}")

            # Print start indicator
            self.console.print(
                f"[bold cyan]╭─ Starting Subagent: {self.config.name} "
                f"({self.config.subagent_type})[/bold cyan]"
            )
            self.console.print(f"[cyan]│[/cyan] Task: {self.config.task}")
            self.console.print("[cyan]╰─[/cyan]")

            # Add task to conversation
            self.conversation_history.append({"role": "user", "content": self.config.task})

            # Execute the agent loop with timeout
            response = self._run_with_timeout()

            self.end_time = time.time()
            execution_time = self.end_time - self.start_time

            # Create result
            self.result = SubAgentResult(
                success=True,
                output=response,
                error=None,
                iterations_used=self._get_iteration_count(),
                execution_time=execution_time,
                metadata={
                    "subagent_name": self.config.name,
                    "subagent_type": self.config.subagent_type,
                    "model": self.model,
                },
            )
            self.status = SubAgentStatus.COMPLETED

            logger.info(
                f"Subagent '{self.config.name}' completed successfully in {execution_time:.2f}s"
            )

            # Print completion indicator
            self.console.print(
                f"[bold green]✓ Subagent Complete: {self.config.name}[/bold green] "
                f"[dim]({execution_time:.2f}s, {self.result.iterations_used} iterations)[/dim]"
            )

            return self.result

        except TimeoutError:
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time
            self.status = SubAgentStatus.TIMEOUT

            self.result = SubAgentResult(
                success=False,
                output="",
                error=f"Subagent exceeded timeout limit of {self.config.timeout}s",
                iterations_used=self._get_iteration_count(),
                execution_time=execution_time,
                metadata={
                    "subagent_name": self.config.name,
                    "subagent_type": self.config.subagent_type,
                    "failure_reason": "timeout",
                },
            )

            logger.warning(f"Subagent '{self.config.name}' timed out after {execution_time:.2f}s")

            # Print timeout indicator
            self.console.print(
                f"[bold yellow]⏱ Subagent Timeout: {self.config.name}[/bold yellow] "
                f"[dim](exceeded {self.config.timeout}s limit)[/dim]"
            )

            return self.result

        except Exception as e:
            self.end_time = time.time()
            execution_time = self.end_time - self.start_time
            self.status = SubAgentStatus.FAILED

            self.result = SubAgentResult(
                success=False,
                output="",
                error=str(e),
                iterations_used=self._get_iteration_count(),
                execution_time=execution_time,
                metadata={
                    "subagent_name": self.config.name,
                    "subagent_type": self.config.subagent_type,
                    "failure_reason": "exception",
                    "exception_type": type(e).__name__,
                },
            )

            logger.error(f"Subagent '{self.config.name}' failed: {e}")

            # Print error indicator
            self.console.print(
                f"[bold red]✗ Subagent Failed: {self.config.name}[/bold red] "
                f"[dim]({type(e).__name__}: {str(e)})[/dim]"
            )

            return self.result

    def _run_with_timeout(self) -> str:
        """Run the agent loop with timeout."""
        import concurrent.futures

        # Use ThreadPoolExecutor to run with timeout
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(self._run_agent_loop)

            try:
                # Wait for completion with timeout
                return future.result(timeout=self.config.timeout)
            except concurrent.futures.TimeoutError:
                # Cancel the future if it's still running
                future.cancel()
                self.interrupted = True
                raise TimeoutError()

    def _run_agent_loop(self) -> str:
        """Run the agent loop with custom parameters."""
        # Use max_iterations from config (already incorporates type defaults via SubAgentManager)
        max_iterations = self.config.max_iterations

        # Convert "all" to None for allowed_tools (None means all tools)
        allowed_tools_config = self.config.allowed_tools
        if allowed_tools_config == "all":
            allowed_tools: list[str] | None = None
        elif isinstance(allowed_tools_config, str):
            allowed_tools = [allowed_tools_config]
        else:
            allowed_tools = allowed_tools_config

        return run_agent_loop(
            conversation_history=self.conversation_history,
            provider=self.provider,
            model=self.model,
            permission_manager=self.permission_manager,
            executor=self.executor,
            console=self.console,  # Use wrapped console with subagent prefix
            auto_approve_all=False,  # Never auto-approve for subagents
            approval_callback=None,  # Subagents don't use approval callbacks
            check_interrupted=lambda: self.interrupted,
            mcp_manager=self.parent_agent.mcp_manager,
            max_iterations=max_iterations,
            allowed_tools=allowed_tools,
            parent_agent=self.parent_agent,
        )

    def _get_iteration_count(self) -> int:
        """Estimate the number of iterations used."""
        # Count assistant messages (excluding system) as a proxy for iterations
        return sum(1 for msg in self.conversation_history if msg["role"] == "assistant")

    def get_status(self) -> str:
        """Get current execution status."""
        return self.status

    def interrupt(self) -> None:
        """Interrupt the subagent's execution."""
        logger.info(f"Interrupting subagent '{self.config.name}'")
        self.interrupted = True
        self.status = SubAgentStatus.INTERRUPTED

    def get_result(self) -> SubAgentResult | None:
        """Get the final result (available after completion)."""
        return self.result

    def get_token_count(self) -> dict[str, Any]:
        """
        Get token usage statistics for the subagent conversation.

        Returns:
            Dictionary with token usage information
        """
        return get_token_count(self.conversation_history, self.model, self.parent_agent.base_url)
