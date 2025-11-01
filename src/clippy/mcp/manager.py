"""MCP Manager for handling connections to MCP servers."""

import asyncio
import logging
import os
import threading
from typing import Any

from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from rich.console import Console
from rich.markup import escape

from .config import Config
from .schema import map_mcp_to_openai
from .trust import TrustStore

logger = logging.getLogger(__name__)


class Manager:
    """Manages MCP server connections and tool execution."""

    def __init__(self, config: Config | None = None, console: Console | None = None) -> None:
        """
        Initialize the MCP Manager.

        Args:
            config: MCP configuration
            console: Rich console for output
        """
        self.config = config or Config(mcp_servers={})
        self.console = console
        self._stdio_contexts: dict[str, Any] = {}  # Server ID -> stdio context manager
        self._session_contexts: dict[str, Any] = {}  # Server ID -> session context manager
        self._sessions: dict[str, Any] = {}  # Server ID -> active session
        self._tools: dict[str, list[types.Tool]] = {}  # Server ID -> tools
        self._stderr_pipes: dict[str, tuple[int, int]] = {}  # Server ID -> (read_fd, write_fd)
        self._stderr_threads: dict[str, threading.Thread] = {}  # Server ID -> logging thread
        self._stderr_stop_events: dict[str, threading.Event] = {}  # Server ID -> stop event
        self._trust_store = TrustStore()
        # Track enabled servers
        self._enabled_servers: set[str] = set(self.config.mcp_servers.keys())

        # Create a persistent event loop in a background thread
        self._loop: asyncio.AbstractEventLoop | None = None
        self._loop_thread: threading.Thread | None = None
        self._loop_started = threading.Event()
        self._start_event_loop()

    def _start_event_loop(self) -> None:
        """Start a persistent event loop in a background thread."""

        def run_loop() -> None:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop_started.set()
            self._loop.run_forever()

        self._loop_thread = threading.Thread(target=run_loop, daemon=True)
        self._loop_thread.start()
        self._loop_started.wait()  # Wait for loop to be ready

    def _run_in_loop(self, coro: Any) -> Any:
        """Run a coroutine in the persistent event loop and wait for result."""
        if self._loop is None:
            raise RuntimeError("Event loop not started")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        try:
            return future.result(timeout=30.0)  # reasonable timeout to prevent hangs
        except Exception:
            # If the future is still pending, cancel it to prevent hanging
            if not future.done():
                future.cancel()
            raise

    def _start_stderr_logger(self, server_id: str, read_fd: int) -> None:
        """
        Start a thread that reads from stderr pipe and logs to logger.

        Args:
            server_id: Server identifier for log messages
            read_fd: File descriptor to read from
        """
        stop_event = threading.Event()
        self._stderr_stop_events[server_id] = stop_event

        def log_stderr() -> None:
            """Read from pipe and log to logger."""
            try:
                with os.fdopen(read_fd, "r", buffering=1) as stderr_file:
                    while not stop_event.is_set():
                        line = stderr_file.readline()
                        if not line:
                            break
                        if line.strip():
                            logger.debug(f"[MCP:{server_id}] {line.rstrip()}")
            except Exception as e:
                logger.debug(f"Error reading stderr from MCP server '{server_id}': {e}")

        thread = threading.Thread(target=log_stderr, daemon=True)
        thread.start()
        self._stderr_threads[server_id] = thread

    def start(self) -> None:
        """Start the MCP manager and initialize connections (synchronous wrapper)."""
        self._run_in_loop(self._async_start())

    async def _async_start(self) -> None:
        """Start the MCP manager and initialize connections (async implementation)."""
        # Initialize only enabled servers
        for server_id, server_config in self.config.mcp_servers.items():
            if server_id not in self._enabled_servers:
                continue  # Skip disabled servers
            try:
                # Create stdio transport parameters
                params = StdioServerParameters(
                    command=server_config.command,
                    args=server_config.args,
                    env=server_config.env,
                    cwd=server_config.cwd,
                )

                # Create a pipe for stderr capture
                # read_fd: we read from this to get stderr output
                # write_fd: MCP server process writes to this
                read_fd, write_fd = os.pipe()
                self._stderr_pipes[server_id] = (read_fd, write_fd)

                # Start a thread to read from stderr pipe and log it
                self._start_stderr_logger(server_id, read_fd)

                # Create and enter stdio client context to get streams
                # Redirect stderr to the write end of the pipe
                errlog = os.fdopen(write_fd, "w")
                stdio_context = stdio_client(params, errlog=errlog)
                self._stdio_contexts[server_id] = stdio_context
                read_stream, write_stream = await stdio_context.__aenter__()

                # Create ClientSession from streams
                session_context = ClientSession(read_stream, write_stream)
                self._session_contexts[server_id] = session_context

                # Enter the session context and keep session alive
                session = await session_context.__aenter__()
                self._sessions[server_id] = session

                # Initialize session with tools capability
                await session.initialize()

                # List available tools
                tools_result = await session.list_tools()
                self._tools[server_id] = tools_result.tools or []

                if self.console:
                    self.console.print(f"[green]✓ Connected to MCP server '{server_id}'[/green]")

            except Exception as e:
                logger.warning(f"Failed to connect to MCP server '{server_id}': {e}")
                if self.console:
                    error_msg = (
                        f"[yellow]⚠ Failed to connect to MCP server '{server_id}': "
                        f"{escape(str(e))}[/yellow]"
                    )
                    self.console.print(error_msg)

    def stop(self) -> None:
        """Stop the MCP manager and close connections (synchronous wrapper)."""
        try:
            self._run_in_loop(self._async_stop())
        finally:
            # Stop the event loop
            if self._loop:
                self._loop.call_soon_threadsafe(self._loop.stop)
            if self._loop_thread:
                self._loop_thread.join(timeout=5.0)

    async def _async_stop(self) -> None:
        """Stop the MCP manager and close connections (async implementation)."""
        # Close all sessions by calling __aexit__ on the context managers
        # Must close session contexts first, then stdio contexts
        for server_id in list(self._sessions.keys()):
            try:
                # Close session context first
                session_context = self._session_contexts.get(server_id)
                if session_context and hasattr(session_context, "__aexit__"):
                    await session_context.__aexit__(None, None, None)
            except (RuntimeError, Exception):
                # Suppress cleanup errors - these often happen during shutdown
                # when async context managers are entered/exited in different event loops
                pass

            try:
                # Then close stdio context
                stdio_context = self._stdio_contexts.get(server_id)
                if stdio_context and hasattr(stdio_context, "__aexit__"):
                    await stdio_context.__aexit__(None, None, None)
            except (RuntimeError, Exception):
                # Suppress cleanup errors
                pass

            # Stop stderr logging thread and close pipes
            if server_id in self._stderr_stop_events:
                self._stderr_stop_events[server_id].set()

            if server_id in self._stderr_threads:
                thread = self._stderr_threads[server_id]
                thread.join(timeout=1.0)

            if server_id in self._stderr_pipes:
                read_fd, write_fd = self._stderr_pipes[server_id]
                try:
                    os.close(read_fd)
                except OSError:
                    pass
                try:
                    os.close(write_fd)
                except OSError:
                    pass

        self._stdio_contexts.clear()
        self._session_contexts.clear()
        self._sessions.clear()
        self._tools.clear()
        self._stderr_pipes.clear()
        self._stderr_threads.clear()
        self._stderr_stop_events.clear()

    def list_servers(self) -> list[dict[str, Any]]:
        """
        List available MCP servers.

        Returns:
            List of server information
        """
        servers = []
        for server_id in self.config.mcp_servers.keys():
            connected = server_id in self._sessions
            enabled = server_id in self._enabled_servers
            servers.append(
                {
                    "server_id": server_id,
                    "connected": connected,
                    "enabled": enabled,
                    "tools_count": len(self._tools.get(server_id, [])),
                }
            )
        return servers

    def list_tools(self, server_id: str | None = None) -> list[dict[str, Any]]:
        """
        List tools available from MCP servers.

        Args:
            server_id: Optional specific server ID to list tools for

        Returns:
            List of tools
        """
        tools = []

        if server_id:
            # List tools for specific server
            if server_id in self._tools:
                for tool in self._tools[server_id]:
                    tools.append(
                        {"server_id": server_id, "name": tool.name, "description": tool.description}
                    )
        else:
            # List tools for all servers
            for sid, server_tools in self._tools.items():
                for tool in server_tools:
                    tools.append(
                        {"server_id": sid, "name": tool.name, "description": tool.description}
                    )

        return tools

    def get_all_tools_openai(self) -> list[dict[str, Any]]:
        """
        Get all MCP tools mapped to OpenAI format.

        Returns:
            List of OpenAI-style tool definitions
        """
        openai_tools = []

        for server_id, server_tools in self._tools.items():
            for tool in server_tools:
                try:
                    openai_tool = map_mcp_to_openai(tool, server_id)
                    openai_tools.append(openai_tool)
                except Exception as e:
                    logger.warning(
                        f"Failed to map MCP tool '{tool.name}' from server '{server_id}': {e}"
                    )
                    if self.console:
                        error_msg = (
                            f"[yellow]⚠ Failed to map MCP tool '{tool.name}' "
                            f"from server '{server_id}': {escape(str(e))}[/yellow]"
                        )
                        self.console.print(error_msg)

        return openai_tools

    def execute(
        self,
        server_id: str,
        tool_name: str,
        args: dict[str, Any],
        bypass_trust_check: bool = False,
    ) -> tuple[bool, str, Any]:
        """
        Execute an MCP tool call.

        Args:
            server_id: Server identifier
            tool_name: Tool name
            args: Tool arguments
            bypass_trust_check: If True, skip trust check (for user-approved calls)

        Returns:
            Tuple of (success: bool, message: str, result: Any)
        """
        # Check if server is configured
        if server_id not in self.config.mcp_servers:
            error_msg = f"MCP server '{server_id}' not configured"
            logger.error(f"MCP execution failed: {error_msg}")
            return False, error_msg, None

        # Check if we're connected to the server
        if server_id not in self._sessions:
            error_msg = f"Not connected to MCP server '{server_id}'"
            logger.error(f"MCP execution failed: {error_msg}")
            return False, error_msg, None

        # Check trust (unless bypassed by explicit user approval)
        if not bypass_trust_check and not self._trust_store.is_trusted(server_id):
            error_msg = f"MCP server '{server_id}' not trusted"
            logger.error(f"MCP execution failed: {error_msg}")
            return False, error_msg, None

        session = self._sessions[server_id]

        try:
            # Log the execution attempt
            logger.info(
                f"Executing MCP tool '{tool_name}' on server '{server_id}' with args: {args}"
            )

            # Execute tool call in the persistent event loop
            result = self._run_in_loop(self._execute_tool(session, tool_name, args))

            logger.info(f"Successfully executed MCP tool '{tool_name}' on server '{server_id}'")
            return True, f"Successfully executed MCP tool '{tool_name}'", result
        except Exception as e:
            # Log full exception details
            logger.error(
                f"Error executing MCP tool '{tool_name}' on server '{server_id}': "
                f"{type(e).__name__}: {e}",
                exc_info=True,
            )
            error_msg = f"Error executing MCP tool '{tool_name}': {type(e).__name__}: {str(e)}"
            return False, error_msg, None

    async def _execute_tool(self, session: Any, tool_name: str, args: dict[str, Any]) -> Any:
        """Execute a tool call asynchronously."""
        result = await session.call_tool(tool_name, args)
        return result

    def is_trusted(self, server_id: str) -> bool:
        """
        Check if a server is trusted.

        Args:
            server_id: Server identifier

        Returns:
            True if server is trusted
        """
        return self._trust_store.is_trusted(server_id)

    def set_trusted(self, server_id: str, trusted: bool) -> None:
        """
        Set server trust status.

        Args:
            server_id: Server identifier
            trusted: Trust status
        """
        self._trust_store.set_trusted(server_id, trusted)

    def is_enabled(self, server_id: str) -> bool:
        """
        Check if a server is enabled.

        Args:
            server_id: Server identifier

        Returns:
            True if server is enabled
        """
        return server_id in self._enabled_servers

    def set_enabled(self, server_id: str, enabled: bool) -> bool:
        """
        Enable or disable a server.

        Args:
            server_id: Server identifier
            enabled: Enable or disable status

        Returns:
            True if operation was successful
        """
        # Check if server exists in configuration
        if server_id not in self.config.mcp_servers:
            return False

        if enabled:
            self._enabled_servers.add(server_id)
        else:
            self._enabled_servers.discard(server_id)
            # Also disconnect if currently connected
            if server_id in self._sessions:
                try:
                    self._run_in_loop(self._disconnect_server(server_id))
                except Exception as e:
                    logger.warning(f"Error disconnecting disabled server '{server_id}': {e}")

        return True

    async def _disconnect_server(self, server_id: str) -> None:
        """
        Disconnect from a specific server.

        Args:
            server_id: Server identifier
        """
        try:
            # Close session context first
            session_context = self._session_contexts.get(server_id)
            if session_context and hasattr(session_context, "__aexit__"):
                await session_context.__aexit__(None, None, None)
        except (RuntimeError, Exception):
            # Suppress cleanup errors
            pass

        try:
            # Then close stdio context
            stdio_context = self._stdio_contexts.get(server_id)
            if stdio_context and hasattr(stdio_context, "__aexit__"):
                await stdio_context.__aexit__(None, None, None)
        except (RuntimeError, Exception):
            # Suppress cleanup errors
            pass

        # Clean up related resources
        self._sessions.pop(server_id, None)
        self._tools.pop(server_id, None)
        self._session_contexts.pop(server_id, None)
        self._stdio_contexts.pop(server_id, None)

        # Stop stderr logging and cleanup pipes
        if server_id in self._stderr_stop_events:
            self._stderr_stop_events[server_id].set()

        if server_id in self._stderr_threads:
            thread = self._stderr_threads[server_id]
            thread.join(timeout=1.0)
            self._stderr_threads.pop(server_id, None)

        if server_id in self._stderr_pipes:
            read_fd, write_fd = self._stderr_pipes[server_id]
            try:
                os.close(read_fd)
                os.close(write_fd)
            except OSError:
                pass
            self._stderr_pipes.pop(server_id, None)

    def list_enabled_servers(self) -> list[str]:
        """
        Get list of enabled server IDs.

        Returns:
            List of enabled server IDs
        """
        return sorted(list(self._enabled_servers))

    def list_disabled_servers(self) -> list[str]:
        """
        Get list of disabled server IDs.

        Returns:
            List of disabled server IDs
        """
        return sorted(list(set(self.config.mcp_servers.keys()) - self._enabled_servers))
