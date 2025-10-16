"""Simplified document UI that works like interactive mode."""

import os
import queue
import re
from typing import Any

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Static, TextArea

from .models import get_model_config, list_available_models
from .permissions import ActionType


def convert_rich_to_textual_markup(text: str) -> str:
    """Convert Rich markup to Textual markup."""
    text = text.replace("[bold cyan]", "[bold blue]")
    text = text.replace("[/bold cyan]", "[/bold blue]")
    text = text.replace("[cyan]", "[blue]")
    text = text.replace("[/cyan]", "[/blue]")
    return text


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI codes and convert markup."""
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)
    text = re.sub(r"[\u2500-\u257F]", "", text)
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    # text = re.sub(r"^\[📎\]\s*", "", text)
    text = convert_rich_to_textual_markup(text)
    return text.strip()


class DocumentHeader(Static):
    """Document header."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.update(
            "📎 clippy - 📄 Document Mode\n"
            "Type directly, press Enter to send • Type 'y'/'n'/'stop' when prompted"
        )


class DocumentRibbon(Vertical):
    """Microsoft Word-style ribbon."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def compose(self) -> ComposeResult:
        # Tab row (removed for cleaner look)

        # Ribbon content with groups
        with Horizontal(classes="ribbon-content"):
            # Clipboard group
            with Vertical(classes="ribbon-group"):
                yield Static("📋 Paste", classes="ribbon-item")
                yield Static("Clipboard", classes="ribbon-group-label")

            # Font group
            with Vertical(classes="ribbon-group"):
                yield Static("🗛 Bold  Italic  Underline", classes="ribbon-item")
                yield Static("Font", classes="ribbon-group-label")

            # Paragraph group
            with Vertical(classes="ribbon-group"):
                yield Static("≡ Bullets  Numbering  Align", classes="ribbon-item")
                yield Static("Paragraph", classes="ribbon-group-label")

            # Styles group
            with Vertical(classes="ribbon-group"):
                yield Static("✎ Heading  Normal  Title", classes="ribbon-item")
                yield Static("Styles", classes="ribbon-group-label")


class DocumentStatusBar(Static):
    """Status bar."""

    def update_status(self, model: str, messages: int, tokens: int = 0) -> None:
        self.update(f"Model: {model} | Messages: {messages} | Tokens: {tokens:,}")

    def update_message(self, message: str) -> None:
        self.update(message)


class DiffDisplay(TextArea):
    """TextArea widget specialized for displaying diffs with syntax highlighting."""

    def __init__(self, diff_content: str, **kwargs: Any) -> None:
        # Set the content and make it read-only
        super().__init__(diff_content, language="diff", theme="monokai", read_only=True, **kwargs)
        self.diff_content = diff_content
        self.show_line_numbers = True


class ApprovalBackdrop(Container):
    """Semi-transparent backdrop for modal dialogs."""

    pass


class ApprovalDialog(Container):
    """Dialog for approval requests with diff display."""

    def __init__(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        diff_content: str | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.tool_name = tool_name
        self.tool_input = tool_input
        self.diff_content = diff_content

    def compose(self) -> ComposeResult:
        # Title bar
        yield Static("⚠️  APPROVAL REQUIRED  ⚠️", id="approval-title")

        # Scrollable content area
        with Vertical(id="approval-content"):
            # Show tool name
            yield Static(f"→ {self.tool_name}", id="approval-tool-name")

            # Show tool input
            input_lines = [f"  {k}: {v}" for k, v in self.tool_input.items()]
            input_text = "\n".join(input_lines)
            if input_text:
                yield Static(input_text, id="approval-tool-input")

            # Display diff if available
            if self.diff_content:
                yield Static("Preview of changes:", id="diff-preview-header")
                if self.diff_content == "":
                    yield Static(
                        "No changes (content identical)",
                        id="diff-no-changes",
                    )
                else:
                    # Create a scrollable diff display
                    diff_display = DiffDisplay(self.diff_content, id="diff-display")
                    yield diff_display
            elif self.tool_name in ["write_file", "edit_file"]:
                yield Static(
                    "No preview available for this change",
                    id="diff-preview-unavailable",
                )

        # Approval buttons - always at bottom, outside scrollable area
        with Horizontal(id="approval-buttons"):
            yield Button("✓ Yes", id="approval-yes", variant="success")
            yield Button("✓ Yes (Allow All)", id="approval-allow", variant="primary")
            yield Button("✗ No", id="approval-no", variant="error")
            yield Button("⊗ Stop", id="approval-stop", variant="warning")


class DocumentApp(App[None]):
    """Simplified document mode - works like interactive mode."""

    CSS = """
    Screen {
        background: #f0f0f0;
    }
    #top-bar {
        dock: top;
        height: auto;
    }
    #header {
        height: 3;
        background: #2b579a;
        color: white;
        padding: 0 1;
        text-align: center;
        content-align: center middle;
    }
    #ribbon {
        height: 3;
        background: #f5f5f5;
        border-bottom: solid #d0d0d0;
        padding: 0;
        margin: 0;
    }
    .ribbon-tabs {
        height: 1;
        background: #f5f5f5;
        color: #555555;
        padding: 0 1;
        text-align: left;
    }
    .ribbon-content {
        height: 3;
        background: white;
        padding: 0 1;
        margin: 0;
    }
    .ribbon-group {
        width: auto;
        height: 1fr;
        border-right: solid #e0e0e0;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    .ribbon-item {
        width: auto;
        height: 1;
        color: #333333;
        text-align: left;
        padding: 0 1;
    }
    .ribbon-group-label {
        width: auto;
        height: 1;
        color: #666666;
        text-align: center;
        text-style: italic;
    }
    #toolbar {
        height: 1;
        background: #f0f0f0;
        padding: 0 1;
        margin: 0;
    }
    #toolbar Button {
        margin: 0 1;
        width: 12;
        height: 1fr;
        background: #f0f0f0;
        color: #333333;
        border: none;
        text-style: bold;
        content-align: center middle;
    }
    #toolbar Button:hover {
        background: #e6e6e6;
    }
    #document-container {
        layout: vertical;
        background: white;
        color: #000000;
        border: solid #d0d0d0;
        margin: 1 2;
        padding: 2 4;
        height: 1fr;
        width: 1fr;
        overflow-y: auto;
    }
    #conversation-log {
        height: auto;
        background: white;
        color: #000000;
        border: none;
        padding: 0;
        scrollbar-size: 0 0;
    }
    #thinking-indicator {
        display: none;
        height: auto;
        background: white;
        color: #999999;
        padding: 1 0 0 0;
        text-style: italic;
    }
    #thinking-indicator.visible {
        display: block;
    }
    #input-container {
        height: auto;
        background: white;
        border: none;
        padding: 1 0 0 0;
    }
    #input-prompt {
        width: auto;
        height: 1;
        background: white;
        color: #000000;
        padding: 0;
        margin: 0;
    }
    #user-input {
        width: 1fr;
        background: white;
        color: #000000;
        border: none;
        height: 1;
        padding: 0;
        margin: 0;
    }
    DocumentStatusBar {
        dock: bottom;
        height: 1;
        background: #1e3c72;
        color: white;
        text-align: center;
    }
    ApprovalBackdrop {
        width: 100%;
        height: 100%;
        background: rgba(0, 0, 0, 0.5);
        layer: overlay;
        align: center middle;
    }
    #approval-dialog {
        width: 85%;
        height: auto;
        max-height: 70%;
        max-width: 120;
        background: #fffef0;
        border: thick #ff9500;
        padding: 0 2 1 2;
        margin: 2 4;
    }
    #approval-title {
        width: 100%;
        height: auto;
        background: #ff9500;
        color: #000000;
        text-align: center;
        text-style: bold;
        padding: 1 0;
        margin: 0;
    }
    #approval-content {
        width: 100%;
        height: auto;
        max-height: 25;
        overflow-y: auto;
        padding: 1 0;
    }
    #approval-tool-name {
        color: #0066cc;
        text-style: bold;
        padding: 0 0 1 0;
    }
    #approval-tool-input {
        color: #666666;
        padding: 0 0 1 0;
    }
    #diff-preview-header {
        color: #ff9500;
        text-style: bold;
        padding: 1 0 0 0;
    }
    #diff-display {
        height: auto;
        max-height: 12;
        border: solid #cccccc;
        background: #1e1e1e;
        padding: 0;
        margin: 0 0 1 0;
    }
    #approval-buttons {
        width: 100%;
        height: auto;
        align: center middle;
        padding: 1 0 0 0;
        background: #fffef0;
    }
    #approval-buttons Button {
        margin: 0 1;
        min-width: 14;
        height: 3;
    }
    """

    BINDINGS = [Binding("ctrl+q", "quit", "Quit")]

    def __init__(self, agent: Any, auto_approve: bool = False) -> None:
        super().__init__()
        self.agent = agent
        self.auto_approve = auto_approve
        self.approval_queue: queue.Queue[str] = queue.Queue()
        self.waiting_for_approval = False
        self.current_approval_dialog: ApprovalDialog | None = None
        self.current_approval_backdrop: ApprovalBackdrop | None = None

    def compose(self) -> ComposeResult:
        with Vertical(id="top-bar"):
            yield Static(
                "📎 clippy - 📄 Document Mode\n"
                "Type directly, press Enter to send • Type 'y'/'n'/'stop' when prompted",
                id="header",
            )
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
        from .agent import InterruptedExceptionError

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
            # Auto-approve this tool type
            from .permissions import ActionType, PermissionLevel

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
            from .permissions import PermissionLevel

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
            from .permissions import PermissionLevel

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

    async def run_agent_async(self, user_input: str) -> None:
        """Run agent in thread, write output directly to log."""
        import asyncio
        import io
        import sys

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
        conv_log.write("• /[bold]quit[/bold] or /[bold]exit[/bold] - Exit code-with-clippy")
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
        conv_log.write("[dim]Made with ❤️ by the code-with-clippy team[/dim]\n")

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
