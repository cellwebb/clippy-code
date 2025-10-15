"""Simplified document UI that works like interactive mode."""

import os
import queue
import re
from typing import Any

from rich.console import Console
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Static

from .models import get_model_config, list_available_models


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
    """

    BINDINGS = [Binding("ctrl+q", "quit", "Quit")]

    def __init__(self, agent: Any, auto_approve: bool = False) -> None:
        super().__init__()
        self.agent = agent
        self.auto_approve = auto_approve
        self.approval_queue: queue.Queue[str] = queue.Queue()
        self.waiting_for_approval = False

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
            yield Static("[📎] Thinking...", id="thinking-indicator")
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

    def request_approval(self, tool_name: str, tool_input: dict[str, Any]) -> bool:
        """Simple approval - just like CLI."""
        from .agent import InterruptedExceptionError

        conv_log = self.query_one("#conversation-log", RichLog)

        # Show what's being approved
        input_lines = [f"  {k}: {v}" for k, v in tool_input.items()]
        input_text = "\n".join(input_lines)

        # Write approval prompt to the log
        def write_prompt() -> None:
            conv_log.write(f"\n[bold cyan]→ {tool_name}[/bold cyan]")
            if input_text:
                conv_log.write(f"[cyan]{input_text}[/cyan]")
            conv_log.write("[yellow]⚠ Approve? Type 'y' (yes), 'n' (no), or 'stop'[/yellow]")

        self.call_from_thread(write_prompt)

        self.waiting_for_approval = True

        # Block until we get a response
        response = self.approval_queue.get()
        self.waiting_for_approval = False

        if response == "stop":
            raise InterruptedExceptionError()

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
            if response in ["y", "n", "stop"]:
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

        # Run agent in thread (non-blocking)
        self.run_worker(self.run_agent_async(user_input), exclusive=True)

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
