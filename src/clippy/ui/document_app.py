"""Main DocumentApp class for the document UI."""

import io
import os
import queue
import sys
from typing import Any

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Static

from ..models import get_model_config, list_available_models
from ..permissions import ActionType
from .styles import DOCUMENT_APP_CSS
from .utils import strip_ansi_codes
from .widgets import (
    ApprovalBackdrop,
    ApprovalDialog,
    DocumentHeader,
    DocumentRibbon,
    DocumentStatusBar,
    ErrorPanel,
)


class DocumentApp(App[None]):
    """Simplified document mode - works like interactive mode."""

    CSS = DOCUMENT_APP_CSS

    BINDINGS = [Binding("ctrl+q", "quit", "Quit")]

    def __init__(self, agent: Any, auto_approve: bool = False) -> None:
        super().__init__()
        self.agent = agent
        self.auto_approve = auto_approve
        self.approval_queue: queue.Queue[str] = queue.Queue()
        self.waiting_for_approval = False
        self.current_approval_dialog: ApprovalDialog | None = None
        self.current_approval_backdrop: ApprovalBackdrop | None = None
        self.current_error_panel: ErrorPanel | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="top-bar"):
            yield DocumentHeader(id="header")
            with Horizontal(id="toolbar"):
                yield Button("Send", id="submit-btn")
                yield Button("Status", id="status-btn")
                yield Button("Models", id="models-btn")
                yield Button("Help", id="help-btn")
                yield Button("Reset", id="reset-btn")
                yield Button("Quit", id="quit-btn")
            yield DocumentRibbon(id="ribbon")
        with Vertical(id="document-container"):
            yield RichLog(id="conversation-log", markup=True, wrap=True, highlight=False)
            yield Static("[👀📎] Thinking...", id="thinking-indicator")
            with Horizontal(id="input-container"):
                yield Static("[bold]\\[You] ➜[/bold] ", id="input-prompt", markup=True)
                yield Input(id="user-input", placeholder="Type your message...")
        yield DocumentStatusBar()

    def on_mount(self) -> None:
        self.query_one("#user-input", Input).focus()
        self.update_status_bar()

    def show_thinking(self) -> None:
        """Show the thinking indicator."""
        try:
            indicator = self.query_one("#thinking-indicator", Static)
            indicator.add_class("visible")
        except Exception:
            pass

    def hide_thinking(self) -> None:
        """Hide the thinking indicator."""
        try:
            indicator = self.query_one("#thinking-indicator", Static)
            indicator.remove_class("visible")
        except Exception:
            pass

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        self.action_submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "submit-btn":
            self.action_submit()
        elif button_id == "reset-btn":
            self.action_reset()
        elif button_id == "help-btn":
            self.show_help()
        elif button_id == "status-btn":
            self.show_status()
        elif button_id == "models-btn":
            self.show_models()
        elif button_id == "quit-btn":
            self.exit()
        elif button_id == "approval-allow":
            self.handle_approval_response("allow")
        elif button_id == "approval-yes":
            self.handle_approval_response("y")
        elif button_id == "approval-no":
            self.handle_approval_response("n")
        elif button_id == "approval-stop":
            self.handle_approval_response("stop")
        elif button_id == "error-ok":
            if self.current_error_panel:
                self.current_error_panel.remove()
                self.current_error_panel = None
        elif button_id == "error-retry":
            if self.current_error_panel:
                self.current_error_panel.remove()
                self.current_error_panel = None
            # TODO: Implement retry logic for the last failed operation
            # This would require tracking the last operation that failed

    def handle_approval_response(self, response: str) -> None:
        """Handle approval response from UI buttons."""
        if self.waiting_for_approval and self.current_approval_dialog:
            # Remove the approval dialog and backdrop
            try:
                if self.current_approval_backdrop:
                    self.current_approval_backdrop.remove()
                    self.current_approval_backdrop = None
            except Exception:
                pass

            self.current_approval_dialog = None
            self.approval_queue.put(response)
            self.waiting_for_approval = False

    def show_error_panel(
        self, error_message: str, error_details: dict[str, Any] | None = None
    ) -> None:
        """Show an enhanced error panel for MCP and other errors."""
        # Hide any existing error panel
        if self.current_error_panel:
            try:
                self.current_error_panel.remove()
            except Exception:
                pass

        # Create new error panel
        self.current_error_panel = ErrorPanel(error_message, error_details, id="error-panel")

        # Mount the error panel
        self.mount(self.current_error_panel)

    def show_mcp_error(
        self,
        error_message: str,
        server_id: str | None = None,
        tool_name: str | None = None,
        original_error: str | None = None,
    ) -> None:
        """Show an MCP-specific error panel with enhanced context."""
        error_details = {}
        if server_id:
            error_details["server_id"] = server_id
        if tool_name:
            error_details["tool_name"] = tool_name
        if original_error:
            error_details["original_error"] = original_error

        # Add MCP-specific context to error message
        if server_id:
            enhanced_message = f"MCP Server Error ({server_id}): {error_message}"
        else:
            enhanced_message = f"MCP Error: {error_message}"

        self.show_error_panel(enhanced_message, error_details)

    def update_status_bar(self) -> None:
        status_bar = self.query_one(DocumentStatusBar)
        try:
            status = self.agent.get_token_count()
            status_bar.update_status(
                status.get("model", "unknown"),
                status.get("message_count", 0),
                status.get("total_tokens", 0),
            )
        except Exception:
            status_bar.update_status("unknown", 0, 0)

    def request_approval(
        self, tool_name: str, tool_input: dict[str, Any], diff_content: str | None = None
    ) -> bool:
        """Request approval with enhanced UI."""
        from ..agent import InterruptedExceptionError

        conv_log = self.query_one("#conversation-log", RichLog)

        # Show what's being approved in conversation log
        input_lines = [f"  {k}: {v}" for k, v in tool_input.items()]
        input_text = "\n".join(input_lines)

        def write_prompt() -> None:
            conv_log.write(f"\n[bold cyan]→ {tool_name}[/bold cyan]")
            if input_text:
                conv_log.write(f"[cyan]{input_text}[/cyan]")

            # Mention that diff preview is available in the approval dialog
            # to avoid duplicate display of the same information
            if diff_content is not None:
                conv_log.write(
                    "[bold yellow]Preview of changes:[/bold yellow] "
                    "See approval dialog below for details"
                )
            else:
                conv_log.write("[yellow]⚠ Approve? Check approval dialog below[/yellow]")

        self.call_from_thread(write_prompt)

        # Hide input container while waiting for approval
        def hide_input() -> None:
            try:
                input_container = self.query_one("#input-container")
                input_container.display = False
            except Exception:
                pass

        self.call_from_thread(hide_input)

        # Create backdrop and dialog for centered modal display
        self.current_approval_backdrop = ApprovalBackdrop()
        self.current_approval_dialog = ApprovalDialog(
            tool_name, tool_input, diff_content, id="approval-dialog"
        )

        # Mount backdrop with dialog from main thread to avoid event loop issues
        def mount_modal() -> None:
            if self.current_approval_backdrop and self.current_approval_dialog:
                self.mount(self.current_approval_backdrop)
                self.current_approval_backdrop.mount(self.current_approval_dialog)

        self.call_from_thread(mount_modal)

        self.waiting_for_approval = True

        # Block until we get a response
        response = self.approval_queue.get()
        self.waiting_for_approval = False

        # Show input container again
        def show_input() -> None:
            try:
                input_container = self.query_one("#input-container")
                input_container.display = True
            except Exception:
                pass

        self.call_from_thread(show_input)

        if response == "stop":
            raise InterruptedExceptionError()
        elif response == "allow":
            # Check if this is an MCP tool
            from ..mcp.naming import is_mcp_tool, parse_mcp_qualified_name

            if is_mcp_tool(tool_name):
                # Trust the MCP server
                try:
                    server_id, _ = parse_mcp_qualified_name(tool_name)
                    if hasattr(self.agent, "mcp_manager") and self.agent.mcp_manager:
                        self.agent.mcp_manager.set_trusted(server_id, True)
                        conv_log.write(
                            f"[green]✓ Trusted MCP server '{server_id}' for this session[/green]"
                        )
                        conv_log.write(
                            f"[green]All tools from '{server_id}' will be auto-approved[/green]"
                        )
                    else:
                        conv_log.write("[yellow]⚠ MCP manager not available[/yellow]")
                except Exception as e:
                    conv_log.write(f"[yellow]⚠ Error trusting server: {e}[/yellow]")
                return True
            else:
                # Auto-approve this tool type for non-MCP tools
                from ..permissions import PermissionLevel

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
                    "grep": ActionType.GREP,  # Dedicated action type for grep
                    "edit_file": ActionType.EDIT_FILE,  # Add mapping for edit_file tool
                }

                action_type = action_map.get(tool_name)
                if action_type:
                    # Update permission for this action type to AUTO_APPROVE
                    self.agent.permission_manager.update_permission(
                        action_type, PermissionLevel.AUTO_APPROVE
                    )
                    conv_log.write(f"[green]Auto-approving {tool_name} for this session[/green]")
                    return True
                else:
                    # Fallback to regular approval
                    return True

        return response == "y"

    def action_submit(self) -> None:
        conv_log = self.query_one("#conversation-log", RichLog)
        user_input_widget = self.query_one("#user-input", Input)
        user_input = user_input_widget.value.strip()

        if not user_input:
            return

        # Check if waiting for approval
        if self.waiting_for_approval:
            response = user_input.lower()
            if response in ["y", "n", "stop", "allow", "a"]:
                # Convert shorthand responses
                if response == "a":
                    response = "allow"
                self.approval_queue.put(response)
                user_input_widget.value = ""
                return

        # Show user input
        conv_log.write(f"[bold][You] ➜[/bold] {user_input}")
        conv_log.write("")
        user_input_widget.value = ""

        # Handle commands
        if user_input.lower() in ["/exit", "/quit"]:
            self.exit()
            return
        elif user_input.lower() in ["/reset", "/clear", "/new"]:
            self.action_reset()
            return
        elif user_input.lower() == "/help":
            self.show_help()
            return
        elif user_input.lower() == "/status":
            self.show_status()
            return
        elif user_input.lower() == "/compact":
            # Compact conversation history
            conv_log.write("[cyan]Compacting conversation...[/cyan]")
            success, message, stats = self.agent.compact_conversation()

            if success:
                conv_log.write(
                    f"[green]✓ Conversation Compacted[/green]\n"
                    f"[cyan]Token Reduction:[/cyan] {stats['tokens_saved']:,} tokens saved "
                    f"({stats['reduction_percent']:.1f}%)\n"
                    f"[cyan]Messages:[/cyan] {stats['messages_before']} → "
                    f"{stats['messages_after']} (summarized {stats['messages_summarized']})"
                )
            else:
                conv_log.write(f"[yellow]⚠ Cannot Compact: {message}[/yellow]")
            return
        elif user_input.lower().startswith("/model"):
            self.handle_model_command(user_input)
            return
        elif user_input.lower().startswith("/auto"):
            self.handle_auto_command(user_input)
            return
        elif user_input.lower().startswith("/mcp"):
            self.handle_mcp_command(user_input)
            return

        # Run agent in thread (non-blocking)
        self.run_worker(self.run_agent_async(user_input), exclusive=True)

    def handle_auto_command(self, user_input: str) -> None:
        """Handle auto-approval related commands."""
        conv_log = self.query_one("#conversation-log", RichLog)
        parts = user_input.split(maxsplit=1)

        if len(parts) == 1:
            # Just /auto without subcommand
            conv_log.write("[yellow]Use /auto list, /auto revoke <action>, or /auto clear[/yellow]")
            return

        subcommand = parts[1].strip()

        if subcommand == "list":
            # List auto-approved actions
            conv_log.write("[bold]Auto-approved actions in this session:[/bold]")
            auto_approved_actions = []
            for action_type in ActionType:
                if self.agent.permission_manager.config.can_auto_execute(action_type):
                    auto_approved_actions.append(action_type.value)

            if auto_approved_actions:
                for action in auto_approved_actions:
                    conv_log.write(f"• [green]{action}[/green]")
            else:
                conv_log.write("[dim]No actions auto-approved[/dim]")
        elif subcommand.startswith("revoke "):
            # Revoke auto-approval for an action
            from ..permissions import PermissionLevel

            action_to_revoke = subcommand.split(" ", 1)[1].strip()
            # Find the action type
            action_type = None
            for at in ActionType:
                if at.value == action_to_revoke:
                    action_type = at
                    break

            if action_type:
                # Set back to REQUIRE_APPROVAL
                self.agent.permission_manager.update_permission(
                    action_type, PermissionLevel.REQUIRE_APPROVAL
                )
                conv_log.write(f"[green]Revoked auto-approval for {action_to_revoke}[/green]")
            else:
                conv_log.write(f"[red]Unknown action type: {action_to_revoke}[/red]")
        elif subcommand == "clear":
            # Clear all auto-approvals
            from ..permissions import PermissionLevel

            revoked_count = 0
            for action_type in ActionType:
                if self.agent.permission_manager.config.can_auto_execute(action_type):
                    self.agent.permission_manager.update_permission(
                        action_type, PermissionLevel.REQUIRE_APPROVAL
                    )
                    revoked_count += 1

            conv_log.write(f"[green]Cleared {revoked_count} auto-approved actions[/green]")
        else:
            conv_log.write("[yellow]Use /auto list, /auto revoke <action>, or /auto clear[/yellow]")

    def handle_mcp_command(self, user_input: str) -> None:
        """Handle MCP commands in document mode."""
        conv_log = self.query_one("#conversation-log", RichLog)
        parts = user_input.split(maxsplit=1)

        if len(parts) == 1:
            # Just /mcp without subcommand
            conv_log.write(
                "[yellow]Use /mcp list, /mcp tools, /mcp status, /mcp refresh, /mcp allow, "
                "or /mcp revoke[/yellow]"
            )
            return

        subcommand_with_args = parts[1]
        subcommand_parts = subcommand_with_args.strip().split(maxsplit=1)
        subcommand = subcommand_parts[0].lower()
        subcommand_args = subcommand_parts[1] if len(subcommand_parts) > 1 else ""

        # Get MCP manager from agent
        mcp_manager = getattr(self.agent, "mcp_manager", None)
        if mcp_manager is None:
            conv_log.write("[yellow]⚠ MCP functionality not available[/yellow]")
            conv_log.write("[dim]Make sure the agent was initialized with MCP support.[/dim]")
            return

        if subcommand == "list":
            self._handle_mcp_list(mcp_manager, conv_log)
        elif subcommand == "tools":
            self._handle_mcp_tools(mcp_manager, conv_log, subcommand_args)
        elif subcommand == "status":
            self._handle_mcp_status(mcp_manager, conv_log)
        elif subcommand == "refresh":
            self._handle_mcp_refresh(mcp_manager, conv_log)
        elif subcommand == "allow":
            self._handle_mcp_allow(mcp_manager, conv_log, subcommand_args)
        elif subcommand == "revoke":
            self._handle_mcp_revoke(mcp_manager, conv_log, subcommand_args)
        else:
            conv_log.write(f"[red]Unknown MCP command: {subcommand}[/red]")
            conv_log.write(
                "[dim]Available commands: list, tools, status, refresh, allow, revoke[/dim]"
            )

    def _handle_mcp_list(self, mcp_manager: Any, conv_log: RichLog) -> None:
        """Handle /mcp list command."""
        servers = mcp_manager.list_servers()

        if not servers:
            conv_log.write("[yellow]No MCP servers configured[/yellow]")
            conv_log.write("[dim]Add servers to mcp.json to use MCP functionality.[/dim]")
            return

        conv_log.write("\n📎 [bold]Configured MCP Servers:[/bold]")
        for server in servers:
            status = (
                "[green]connected[/green]" if server["connected"] else "[red]disconnected[/red]"
            )
            conv_log.write(
                f"• [cyan]{server['server_id']:20}[/cyan] - {status} "
                f"({server['tools_count']} tools)"
            )
        conv_log.write("")

    def _handle_mcp_tools(self, mcp_manager: Any, conv_log: RichLog, server_arg: str) -> None:
        """Handle /mcp tools command."""
        if server_arg:
            # List tools for specific server
            tools = mcp_manager.list_tools(server_arg)
            if not tools:
                conv_log.write(f"[yellow]No tools found for server '{server_arg}'[/yellow]")
                return
        else:
            # List tools for all servers
            tools = mcp_manager.list_tools()
            if not tools:
                conv_log.write("[yellow]No MCP tools available[/yellow]")
                return

        conv_log.write("\n📎 [bold]Available MCP Tools:[/bold]")
        current_server = None
        for tool in tools:
            if tool["server_id"] != current_server:
                current_server = tool["server_id"]
                conv_log.write(f"\n[bold]Server: {current_server}[/bold]")
            conv_log.write(f"  • [cyan]{tool['name']}[/cyan] - {tool['description']}")
        conv_log.write("")

    def _handle_mcp_status(self, mcp_manager: Any, conv_log: RichLog) -> None:
        """Handle /mcp status command - detailed diagnostics."""
        conv_log.write("\n📎 [bold]MCP Server Status:[/bold]\n")

        servers = mcp_manager.list_servers()
        if not servers:
            conv_log.write("[yellow]No MCP servers configured[/yellow]")
            return

        for server in servers:
            server_id = server["server_id"]
            connected = server["connected"]
            tools_count = server["tools_count"]
            trusted = mcp_manager.is_trusted(server_id)

            # Status line
            status_symbol = "✓" if connected else "✗"
            status_color = "green" if connected else "red"
            status_text = "connected" if connected else "disconnected"

            conv_log.write(f"\n[bold]{status_symbol} {server_id}[/bold]")
            conv_log.write(f"  Connection: [{status_color}]{status_text}[/{status_color}]")
            conv_log.write(
                f"  Trusted: [{'green' if trusted else 'yellow'}]"
                f"{'yes' if trusted else 'no'}[/{'green' if trusted else 'yellow'}]"
            )
            conv_log.write(f"  Tools: [cyan]{tools_count}[/cyan]")

            # Show tools for this server
            if tools_count > 0:
                tools = mcp_manager.list_tools(server_id)
                conv_log.write("  Available tools:")
                for tool in tools[:5]:  # Show first 5 tools
                    conv_log.write(f"    • {tool['name']}")
                if tools_count > 5:
                    conv_log.write(f"    ... and {tools_count - 5} more")

        conv_log.write("")

    def _handle_mcp_refresh(self, mcp_manager: Any, conv_log: RichLog) -> None:
        """Handle /mcp refresh command."""
        conv_log.write("[cyan]Refreshing MCP server connections...[/cyan]")
        try:
            # Stop and restart are now synchronous
            mcp_manager.stop()
            mcp_manager.start()

            # Refresh and show updated status
            self._handle_mcp_list(mcp_manager, conv_log)
        except Exception as e:
            conv_log.write(f"[red]✗ Error refreshing MCP servers: {e}[/red]")

    def _handle_mcp_allow(self, mcp_manager: Any, conv_log: RichLog, server_arg: str) -> None:
        """Handle /mcp allow command."""
        if not server_arg:
            conv_log.write("[red]Usage: /mcp allow <server_id>[/red]")
            return

        server_id = server_arg.strip()
        mcp_manager.set_trusted(server_id, True)
        conv_log.write(
            f"[green]✓ Marked MCP server '{server_id}' as trusted for this session[/green]"
        )

    def _handle_mcp_revoke(self, mcp_manager: Any, conv_log: RichLog, server_arg: str) -> None:
        """Handle /mcp revoke command."""
        if not server_arg:
            conv_log.write("[red]Usage: /mcp revoke <server_id>[/red]")
            return

        server_id = server_arg.strip()
        mcp_manager.set_trusted(server_id, False)
        conv_log.write(f"[green]✓ Revoked trust for MCP server '{server_id}'[/green]")

    async def run_agent_async(self, user_input: str) -> None:
        """Run agent in thread, write output directly to log."""
        import asyncio

        conv_log = self.query_one("#conversation-log", RichLog)

        # Add a blank line before agent response for visual separation
        conv_log.write("")

        # Show thinking indicator
        self.show_thinking()

        # Create a custom stdout that writes to the log
        class LogWriter:
            def __init__(self, app: DocumentApp):
                self.app = app
                self.line_buffer = ""

            def write(self, text: str) -> int:
                # Accumulate text until we get a newline
                self.line_buffer += text
                if "\n" in self.line_buffer:
                    # Split into lines
                    lines = self.line_buffer.split("\n")
                    # All but the last element are complete lines
                    for line in lines[:-1]:
                        if line.strip():
                            clean_text = strip_ansi_codes(line)
                            if clean_text:
                                # Hide thinking indicator when output arrives
                                self.app.call_from_thread(self.app.hide_thinking)

                                # Write the line
                                self.app.call_from_thread(
                                    lambda t=clean_text: self.app.query_one(
                                        "#conversation-log", RichLog
                                    ).write(t)
                                )

                                # Show thinking indicator again after tool results
                                # (agent will make another LLM call after executing tools)
                                if clean_text.startswith("✓") or clean_text.startswith("✗"):
                                    self.app.call_from_thread(self.app.show_thinking)
                    # Keep the last element as the new buffer
                    self.line_buffer = lines[-1]
                return len(text)

            def flush(self) -> None:
                # Don't flush incomplete lines - wait for the newline
                # This prevents [📎] from being written separately from the content
                pass

            def isatty(self) -> bool:
                return False

        # Create a console that writes directly to the log
        class LiveConsole(Console):
            def __init__(self, app: DocumentApp):
                super().__init__(force_terminal=False, no_color=True, markup=False)
                self.app = app

            def print(self, *args: Any, **kwargs: Any) -> None:
                # Capture output
                output = io.StringIO()
                temp_console = Console(
                    file=output, force_terminal=False, no_color=True, markup=False
                )
                temp_console.print(*args, **kwargs)
                text = output.getvalue().strip()
                if text:
                    clean_text = strip_ansi_codes(text)
                    # Write to log from main thread
                    self.app.call_from_thread(
                        lambda: self.app.query_one("#conversation-log", RichLog).write(clean_text)
                    )

        log_writer = LogWriter(self)
        live_console = LiveConsole(self)

        old_console = self.agent.console
        old_stdout = sys.stdout
        old_approval_callback = getattr(self.agent, "approval_callback", None)

        self.agent.console = live_console
        sys.stdout = log_writer  # Redirect stdout to capture provider's print() calls
        if not self.auto_approve:
            self.agent.approval_callback = self.request_approval

        def run_in_thread() -> None:
            self.agent.run(user_input, auto_approve_all=self.auto_approve)

        try:
            await asyncio.to_thread(run_in_thread)
        except Exception as err:
            error_msg = str(err)
            # Write directly since we're in async context, not a separate thread
            conv_log.write(f"\n[red]Error: {error_msg}[/red]")
        finally:
            log_writer.flush()  # Flush any remaining buffer
            sys.stdout = old_stdout
            self.agent.console = old_console
            self.agent.approval_callback = old_approval_callback
            self.hide_thinking()  # Hide thinking indicator when done
            self.update_status_bar()

    def action_reset(self) -> None:
        self.agent.reset_conversation()
        conv_log = self.query_one("#conversation-log", RichLog)
        conv_log.clear()
        conv_log.write("[green]✓ Conversation reset[/green]\n")
        self.update_status_bar()

    def show_help(self) -> None:
        conv_log = self.query_one("#conversation-log", RichLog)
        current_model = self.agent.model
        current_provider = self.agent.base_url or "OpenAI"

        conv_log.write("\n📎 [bold]Document Mode Help[/bold]\n")
        conv_log.write("")
        conv_log.write("[bold]🎯 Basic Usage[/bold]")
        conv_log.write("• Type your message in the input field and press Enter to send")
        conv_log.write("• Click the [bold]Send[/bold] button or press Enter to send messages")
        conv_log.write("• Responses appear in the document area with Clippy's paperclip 📎")
        conv_log.write("")
        conv_log.write("[bold]⚡ Commands[/bold]")
        conv_log.write("• /[bold]help[/bold] - Show this help message")
        conv_log.write("• /[bold]status[/bold] - Show current session and token usage")
        conv_log.write(
            "• /[bold]reset[/bold] or /[bold]clear[/bold] or /[bold]new[/bold] - Reset conversation"
        )
        conv_log.write("• /[bold]compact[/bold] - Reduce token usage in long conversations")
        conv_log.write("• /[bold]model list[/bold] - Show available model presets")
        conv_log.write("• /[bold]model <name>[/bold] - Switch to a specific model")
        conv_log.write("• /[bold]auto list[/bold] - List auto-approved actions")
        conv_log.write("• /[bold]auto revoke <action>[/bold] - Revoke auto-approval for action")
        conv_log.write("• /[bold]auto clear[/bold] - Clear all auto-approved actions")
        conv_log.write("• /[bold]mcp list[/bold] - List configured MCP servers")
        conv_log.write("• /[bold]mcp tools [server][/bold] - List tools from MCP servers")
        conv_log.write("• /[bold]mcp refresh[/bold] - Refresh MCP server connections")
        conv_log.write("• /[bold]mcp allow <server>[/bold] - Trust an MCP server for this session")
        conv_log.write("• /[bold]mcp revoke <server>[/bold] - Revoke trust for an MCP server")
        conv_log.write("• /[bold]quit[/bold] or /[bold]exit[/bold] - Exit clippy-code")
        conv_log.write("")
        conv_log.write("[bold]⌨️ Keyboard Shortcuts[/bold]")
        conv_log.write("• [bold]Enter[/bold] - Send message")
        conv_log.write("• [bold]Ctrl+Q[/bold] - Quit application")
        conv_log.write("• [bold]Ctrl+C[/bold] - Interrupt current operation")
        conv_log.write("")
        conv_log.write("[bold]🔘 Toolbar Buttons[/bold]")
        conv_log.write("• [bold]Send[/bold] - Send your current message")
        conv_log.write("• [bold]Status[/bold] - View current session information")
        conv_log.write("• [bold]Models[/bold] - Browse and switch between models")
        conv_log.write("• [bold]Help[/bold] - Show this help message")
        conv_log.write("• [bold]Reset[/bold] - Clear conversation history")
        conv_log.write("• [bold]Quit[/bold] - Exit the application")
        conv_log.write("")
        conv_log.write("[bold]✅ Approval System[/bold]")
        conv_log.write("• When a tool requires approval, you'll see a yellow warning")
        conv_log.write(
            "• Type [bold]y[/bold] (yes), [bold]n[/bold] (no), or [bold]stop[/bold] to interrupt"
        )
        conv_log.write(
            "• Type [bold]a[/bold] or [bold]allow[/bold] to approve and auto-approve future calls"
        )
        conv_log.write("• File operations (write, delete) and commands need approval")
        conv_log.write("• Read operations are auto-approved")
        conv_log.write("")
        conv_log.write("[bold]🤖 Current Session[/bold]")
        conv_log.write(f"• Model: [cyan]{current_model}[/cyan]")
        conv_log.write(f"• Provider: [cyan]{current_provider}[/cyan]")
        conv_log.write("• Mode: Document Mode (Word-like interface)")
        conv_log.write("")
        conv_log.write("[bold]💡 Tips[/bold]")
        conv_log.write("• The status bar shows current model, message count, and tokens")
        conv_log.write("• Scroll through the conversation using your mouse or arrow keys")
        conv_log.write("• Paperclip appears when Clippy is thinking about your request")
        conv_log.write("• Diff previews show exact changes before file operations")
        conv_log.write("")
        conv_log.write("[dim]Made with ❤️ by the clippy-code team[/dim]\n")

    def show_status(self) -> None:
        conv_log = self.query_one("#conversation-log", RichLog)
        status = self.agent.get_token_count()

        conv_log.write("\n📎 [bold]Session Status[/bold]\n")

        if "error" in status:
            conv_log.write("[bold red]⚠ Error counting tokens[/bold red]")
            conv_log.write(status["error"])
            conv_log.write("")
            conv_log.write("[bold]Session Info:[/bold]")
            conv_log.write(f"• Model: [cyan]{status['model']}[/cyan]")
            conv_log.write(f"• Provider: [cyan]{status.get('base_url') or 'OpenAI'}[/cyan]")
            conv_log.write(f"• Messages: [cyan]{status['message_count']}[/cyan]")
        else:
            provider = status.get("base_url") or "OpenAI"
            usage_bar_length = 20
            usage_filled = int((status["usage_percent"] / 100) * usage_bar_length)
            usage_bar = "█" * usage_filled + "░" * (usage_bar_length - usage_filled)
            usage_pct = f"{status['usage_percent']:.1f}%"

            conv_log.write("[bold]Current Session:[/bold]")
            conv_log.write(f"• Model: [cyan]{status['model']}[/cyan]")
            conv_log.write(f"• Provider: [cyan]{provider}[/cyan]")
            conv_log.write(f"• Messages: [cyan]{status['message_count']}[/cyan]")
            conv_log.write("")
            conv_log.write("[bold]Token Usage:[/bold]")
            conv_log.write(f"• Context: [cyan]{status['total_tokens']:,}[/cyan] tokens")
            conv_log.write(f"• Usage: [{usage_bar}] [cyan]{usage_pct}[/cyan]")
            conv_log.write("")

            # Build message breakdown
            conv_log.write("[bold]Message Breakdown:[/bold]")
            if status["system_messages"] > 0:
                msg = (
                    f"• System: [cyan]{status['system_messages']}[/cyan] messages, "
                    f"[cyan]{status['system_tokens']:,}[/cyan] tokens"
                )
                conv_log.write(msg)
            if status["user_messages"] > 0:
                msg = (
                    f"• User: [cyan]{status['user_messages']}[/cyan] messages, "
                    f"[cyan]{status['user_tokens']:,}[/cyan] tokens"
                )
                conv_log.write(msg)
            if status["assistant_messages"] > 0:
                msg = (
                    f"• Assistant: [cyan]{status['assistant_messages']}[/cyan] messages, "
                    f"[cyan]{status['assistant_tokens']:,}[/cyan] tokens"
                )
                conv_log.write(msg)
            if status["tool_messages"] > 0:
                msg = (
                    f"• Tool: [cyan]{status['tool_messages']}[/cyan] messages, "
                    f"[cyan]{status['tool_tokens']:,}[/cyan] tokens"
                )
                conv_log.write(msg)

            if status["message_count"] == 0:
                conv_log.write("• [dim]No messages yet[/dim]")

            conv_log.write("")
            conv_log.write("[dim]💡 Usage % is estimated for ~128k context window[/dim]")

        conv_log.write("")

    def show_models(self) -> None:
        conv_log = self.query_one("#conversation-log", RichLog)
        models = list_available_models()
        current_model = self.agent.model
        current_provider = self.agent.base_url or "OpenAI"

        conv_log.write("\n📎 [bold]Available Model Presets[/bold]\n")

        for name, desc in models:
            if name == current_model:
                conv_log.write(f"• [green]★ {name:20}[/green] - {desc} [dim](current)[/dim]")
            else:
                conv_log.write(f"• [cyan]{name:20}[/cyan] - {desc}")

        conv_log.write("")
        conv_log.write("[bold]Current Configuration:[/bold]")
        conv_log.write(f"• Model: [cyan]{current_model}[/cyan]")
        conv_log.write(f"• Provider: [cyan]{current_provider}[/cyan]")
        conv_log.write("")
        conv_log.write("[bold]Usage:[/bold]")
        conv_log.write("• /[bold]model list[/bold] - Show this model list")
        conv_log.write("• /[bold]model <name>[/bold] - Switch to specific model")
        conv_log.write("• /[bold]model <provider>/<model>[/bold] - Custom provider")
        conv_log.write("")
        conv_log.write(
            "[dim]💡 Some models may require specific API keys in your environment[/dim]\n"
        )

    def handle_model_command(self, user_input: str) -> None:
        conv_log = self.query_one("#conversation-log", RichLog)
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1 or parts[1].lower() == "list":
            self.show_models()
        else:
            model_name = parts[1].strip()
            config = get_model_config(model_name)
            if config:
                api_key = os.getenv(config.api_key_env) or "not-set"
                success, message = self.agent.switch_model(
                    model=config.model_id, base_url=config.base_url, api_key=api_key
                )
            else:
                success, message = self.agent.switch_model(model=model_name)
            conv_log.write(f"[green]✓ {message}[/green]" if success else f"[red]✗ {message}[/red]")
            conv_log.write("")
        self.update_status_bar()


def run_document_mode(agent: Any, auto_approve: bool = False) -> None:
    """Run the document mode interface."""
    app = DocumentApp(agent, auto_approve)
    app.run()
