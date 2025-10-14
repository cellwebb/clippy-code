"""Microsoft Word-inspired document interface using Textual."""

import os
import re
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Input, RichLog, Static

from .models import get_model_config, list_available_models


def convert_rich_to_textual_markup(text: str) -> str:
    """Convert Rich markup to Textual markup for better visibility in document mode."""
    # Convert Rich color markup to Textual markup
    # For tool calls, make them more prominent
    text = text.replace("[bold cyan]→", "[bold blue]→")  # Make arrow more prominent
    text = text.replace("[/bold cyan]", "[/bold blue]")  # Fix closing tag
    text = text.replace("[cyan]", "[blue]")  # Make cyan brighter
    text = text.replace("[/cyan]", "[/blue]")  # Fix closing tag
    text = text.replace("[bold green]", "[bold green]")  # Make green more visible
    text = text.replace("[/bold green]", "[/bold green]")  # Fix closing tag
    text = text.replace("[green]", "[green]")  # Make green more visible
    text = text.replace("[/green]", "[/green]")  # Fix closing tag
    text = text.replace("[bold red]", "[bold red]")  # Make red more visible
    text = text.replace("[/bold red]", "[/bold red]")  # Fix closing tag
    text = text.replace("[red]", "[red]")  # Make red more visible
    text = text.replace("[/red]", "[/red]")  # Fix closing tag
    text = text.replace("[bold yellow]", "[bold yellow]")  # Make yellow more visible
    text = text.replace("[/bold yellow]", "[/bold yellow]")  # Fix closing tag
    text = text.replace("[yellow]", "[yellow]")  # Make yellow more visible
    text = text.replace("[/yellow]", "[/yellow]")  # Fix closing tag
    text = text.replace("[bold blue]", "[bold blue]")  # Make blue more visible
    text = text.replace("[/bold blue]", "[/bold blue]")  # Fix closing tag
    text = text.replace("[blue]", "[blue]")  # Make blue more visible
    text = text.replace("[/blue]", "[/blue]")  # Fix closing tag
    text = text.replace("[dim]", "[dim]")  # Make dim text more visible
    text = text.replace("[/dim]", "[/dim]")  # Fix closing tag

    # Handle panel titles and borders (used in API error display)
    text = text.replace("[bold red]Error[/bold red]", "[bold red]Error[/bold red]")

    return text


def strip_ansi_codes(text: str) -> str:
    """Remove terminal control codes and box-drawing characters while preserving markup."""
    # Remove ANSI escape sequences (like \x1b[31m)
    text = re.sub(r"\x1b\[[0-9;]*m", "", text)

    # Remove Unicode box-drawing characters
    text = re.sub(r"[\u2500-\u257F]", "", text)

    # Remove zero-width characters
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Remove paperclip emoji prefix (used in interactive mode)
    text = re.sub(r"^\[📎\]\s*", "", text)

    # Convert Rich markup to Textual markup for better visibility
    text = convert_rich_to_textual_markup(text)

    # No longer filtering out "You" lines or user messages
    # They should be preserved in document mode

    return text.strip()


class DocumentHeader(Static):
    """Word-like document header."""

    def compose(self) -> ComposeResult:
        yield Static("📎 clippy - 📄 Document Mode", classes="doc-title")
        yield Static(
            "Type directly in the document, press Enter to send message",
            classes="doc-commands",
        )


class DocumentStatusBar(Static):
    """Status bar showing model info."""

    def update_status(self, model: str, messages: int, tokens: int = 0) -> None:
        """Update status bar with model info."""
        self.update(f"Model: {model} | Messages: {messages} | Tokens: {tokens:,}")

    def update_message(self, message: str) -> None:
        """Update status bar with a simple message."""
        self.update(message)


class DocumentApp(App[None]):
    """A Textual app that looks like Microsoft Word."""

    CSS = """
    Screen {
        background: #f0f0f0;
    }

    DocumentHeader {
        dock: top;
        height: 4;
        background: #2b579a;
        color: white;
        padding: 1;
    }

    .doc-title {
        text-align: center;
        text-style: bold;
        color: white;
    }

    .doc-commands {
        text-align: center;
        color: #e0e0e0;
    }

    #toolbar {
        dock: top;
        height: 3;
        background: #f0f0f0;
        border-bottom: solid #d0d0d0;
        padding: 0 1;
        margin-top: 4;
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

    #toolbar Button:focus {
        background: #e6e6e6;
    }

    #toolbar Button.-active {
        background: #2b579a;
        color: white;
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
    }

    #conversation-log {
        height: auto;
        min-height: 0;
        background: white;
        color: #000000;
        border: none;
        padding: 0;
        margin: 0;
    }

    #input-container {
        height: 1;
        background: white;
        border: none;
        padding: 0;
        margin: 0;
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

    #user-input:focus {
        border: none;
        background: white;
    }

    DocumentStatusBar {
        dock: bottom;
        height: 1;
        background: #1e3c72;
        color: white;
        text-align: center;
    }

    #help-panel {
        background: #ffffcc;
        border: round #cccc99;
        padding: 1 2;
        margin: 2 4;
    }

    #models-panel {
        background: #e6f3ff;
        border: round #99ccff;
        padding: 1 2;
        margin: 2 4;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit"),
    ]

    def __init__(self, agent: Any, auto_approve: bool = False) -> None:
        super().__init__()
        self.agent = agent
        self.auto_approve = auto_approve
        self.help_visible = False
        self.models_visible = False

    def compose(self) -> ComposeResult:
        """Compose the document UI."""
        yield DocumentHeader()

        # Toolbar with Word-like buttons (ribbon style)
        with Horizontal(id="toolbar"):
            yield Button("Send", id="submit-btn", variant="default")
            yield Button("Reset", id="reset-btn", variant="default")
            yield Button("Help", id="help-btn", variant="default")
            yield Button("Status", id="status-btn", variant="default")
            yield Button("Models", id="models-btn", variant="default")
            yield Button("Quit", id="quit-btn", variant="default")

        # Document container with conversation display and input below it
        with Vertical(id="document-container"):
            yield RichLog(id="conversation-log", markup=True, wrap=True, highlight=False)
            with Horizontal(id="input-container"):
                yield Static("[bold]\\[You] ➜[/bold] ", id="input-prompt", markup=True)
                yield Input(id="user-input", placeholder="Enter text here")

        yield DocumentStatusBar()

    def on_mount(self) -> None:
        """Initialize the document."""
        user_input = self.query_one("#user-input", Input)

        # Focus the input (prompt is now part of the input container)
        user_input.focus()
        self.update_status_bar()

    def on_input_submitted(self, _event: Input.Submitted) -> None:
        """Handle when user presses Enter in the input field."""
        self.action_submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id

        if button_id == "submit-btn":
            self.action_submit()
        elif button_id == "reset-btn":
            self.action_reset()
        elif button_id == "help-btn":
            self.action_toggle_help()
        elif button_id == "status-btn":
            self.action_show_status()
        elif button_id == "models-btn":
            self.action_toggle_models()
        elif button_id == "quit-btn":
            self.exit()

    def update_status_bar(self) -> None:
        """Update status bar."""
        status_bar = self.query_one(DocumentStatusBar)
        try:
            status = self.agent.get_token_count()
            model = status.get("model", "unknown")
            messages = status.get("message_count", 0)
            tokens = status.get("total_tokens", 0)
            status_bar.update_status(model, messages, tokens)
        except Exception:
            status_bar.update_status("unknown", 0, 0)

    def action_submit(self) -> None:
        """Submit the message to the agent."""
        conv_log = self.query_one("#conversation-log", RichLog)
        user_input_widget = self.query_one("#user-input", Input)

        user_input = user_input_widget.value.strip()

        if not user_input:
            return

        # Show what user typed with prompt (add blank line before if not first message)
        conv_log.write(f"[bold][You] ➜[/bold] {user_input}")
        conv_log.write("")  # Add blank line after user message

        # Clear the input
        user_input_widget.value = ""

        # Handle commands
        if user_input.lower() in ["/exit", "/quit"]:
            self.exit()
            return
        elif user_input.lower() in ["/reset", "/clear", "/new"]:
            self.action_reset()
            return
        elif user_input.lower() == "/help":
            self.action_toggle_help()
            return
        elif user_input.lower() == "/status":
            self.action_show_status()
            return
        elif user_input.lower() == "/compact":
            self.handle_compact_command()
            return
        elif user_input.lower().startswith("/model"):
            self.handle_model_command(user_input)
            return

        # Run the agent
        self.run_worker(self.run_agent_async(user_input), exclusive=True)

    def handle_model_command(self, user_input: str) -> None:
        """Handle model switching command."""
        conv_log = self.query_one("#conversation-log", RichLog)

        # Handle model switching
        parts = user_input.split(maxsplit=1)
        if len(parts) == 1 or parts[1].lower() == "list":
            # Show available models
            models = list_available_models()
            current_model = self.agent.model
            current_provider = self.agent.base_url or "OpenAI"

            conv_log.write("\n[bold]Available Model Presets:[/bold]\n")
            for name, desc in models:
                conv_log.write(f"  [blue]{name:20}[/blue] - {desc}")
            conv_log.write(f"\n[bold]Current:[/bold] {current_model} ({current_provider})")
            conv_log.write("\n[dim]Usage: /model <name>[/dim]")
            conv_log.write("")  # Add blank line after
        else:
            # Switch to specified model
            model_name = parts[1].strip()
            config = get_model_config(model_name)

            if config:
                # Use preset configuration
                api_key = os.getenv(config.api_key_env)

                if not api_key:
                    conv_log.write(
                        f"[yellow]⚠ Warning: {config.api_key_env} not set in environment[/yellow]"
                    )
                    conv_log.write("[dim]The model may fail if it requires authentication.[/dim]")
                    # Continue anyway - some providers like Ollama might not need a key
                    api_key = "not-set"

                success, message = self.agent.switch_model(
                    model=config.model_id, base_url=config.base_url, api_key=api_key
                )
            else:
                # Treat as custom model ID (keep current base_url and api_key)
                success, message = self.agent.switch_model(model=model_name)

            if success:
                conv_log.write(f"[green]✓ {message}[/green]")
                # Update status bar to reflect new model
                self.update_status_bar()
            else:
                conv_log.write(f"[red]✗ {message}[/red]")
            conv_log.write("")  # Add blank line after

    def handle_compact_command(self) -> None:
        """Handle compact command."""
        conv_log = self.query_one("#conversation-log", RichLog)

        # Show compacting message
        conv_log.write("[cyan]Compacting conversation...[/cyan]")
        conv_log.write("")  # Add blank line after

    def action_show_status(self) -> None:
        """Show status information."""
        conv_log = self.query_one("#conversation-log", RichLog)
        status_bar = self.query_one(DocumentStatusBar)

        try:
            status = self.agent.get_token_count()

            conv_log.write("\n[bold]📎 clippy - Session Status[/bold]\n")
            conv_log.write(f"[bold]Model:[/bold] {status.get('model', 'unknown')}")
            conv_log.write(f"[bold]Provider:[/bold] {status.get('base_url') or 'OpenAI'}")
            conv_log.write(f"[bold]Messages:[/bold] {status.get('message_count', 0)}")
            conv_log.write(f"[bold]Tokens:[/bold] {status.get('total_tokens', 0):,}")
            conv_log.write(f"[bold]Context Usage:[/bold] {status.get('usage_percent', 0):.1f}%")
            conv_log.write("")  # Add blank line after
        except Exception as e:
            conv_log.write(f"[red]Error getting status: {e}[/red]")
            conv_log.write("")  # Add blank line after
            status_bar.update_message("❌ Error occurred")

    async def run_agent_async(self, user_input: str) -> None:
        """Run agent asynchronously."""
        conv_log = self.query_one("#conversation-log", RichLog)
        status_bar = self.query_one(DocumentStatusBar)

        try:
            # Show processing status in status bar
            status_bar.update_message("💡 Thinking...")

            import io
            from contextlib import redirect_stderr, redirect_stdout

            from rich.console import Console

            # Capture agent output
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()

            # Create console that preserves markup
            markup_console = Console(
                file=output_buffer,
                force_terminal=False,
                no_color=False,  # Keep colors for markup
                markup=True,
                legacy_windows=False,
            )

            old_console = None
            if hasattr(self.agent, "console"):
                old_console = self.agent.console
                self.agent.console = markup_console

            try:
                with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                    self.agent.run(user_input, auto_approve_all=self.auto_approve)
            finally:
                if old_console:
                    self.agent.console = old_console

            # Get output
            response = output_buffer.getvalue()
            errors = error_buffer.getvalue()

            full_output = response
            if errors.strip():
                full_output += "\n" + errors

            # Clean output but preserve markup
            clean_output = (
                strip_ansi_codes(full_output) if full_output.strip() else "Task completed."
            )

            # Add assistant response to conversation log
            if clean_output:
                for line in clean_output.split("\n"):
                    conv_log.write(line)
                conv_log.write("")  # Add blank line after agent response

            # Update status
            self.update_status_bar()

        except Exception as e:
            conv_log.write(f"[red]Error: {e}[/red]")
            conv_log.write("")  # Add blank line after

            # Update status bar to show error
            status_bar.update_message("❌ Error occurred")

    def action_reset(self) -> None:
        """Reset conversation."""
        self.agent.reset_conversation()
        conv_log = self.query_one("#conversation-log", RichLog)

        conv_log.write("[green]✓ Conversation history reset[/green]")
        conv_log.write("")  # Add blank line after
        self.update_status_bar()

    def action_toggle_help(self) -> None:
        """Toggle help panel."""
        if self.help_visible:
            try:
                help_panel = self.query_one("#help-panel")
                help_panel.remove()
            except Exception:
                pass
            self.help_visible = False
        else:
            help_content = Static(
                """📎 clippy - Document Mode Help

 shortcuts:
• Enter        - Send message to clippy
• Ctrl+Q       - Quit application

 toolbar buttons:
• Send   - Submit your message
• Reset  - Clear conversation history
• Help   - Show/hide this help panel
• Status - Display session information
• Models - Show model switching options
• Quit   - Exit clippy

 slash commands:
• /exit, /quit     - Exit clippy
• /reset, /clear, /new - Reset conversation history
• /help           - Show this help message
• /status         - Show session information
• /compact        - Summarize conversation to reduce context usage
• /model list     - Show available models
• /model <name>   - Switch to a different model""",
                id="help-panel",
            )
            self.mount(help_content)
            self.help_visible = True

    def action_toggle_models(self) -> None:
        """Toggle models panel."""
        if self.models_visible:
            try:
                models_panel = self.query_one("#models-panel")
                models_panel.remove()
            except Exception:
                pass
            self.models_visible = False
        else:
            models = list_available_models()
            model_list = "\n".join(f"• {name:20} - {desc}" for name, desc in models)
            current_model = self.agent.model
            current_provider = self.agent.base_url or "OpenAI"

            models_content = Static(
                f"""📎 clippy - Available Models

{model_list}

Current Model: {current_model}
Provider: {current_provider}

To switch models:
1. Type "/model <name>" and press Enter
2. Or use the Models button to close this panel""",
                id="models-panel",
            )
            self.mount(models_content)
            self.models_visible = True


def run_document_mode(agent: Any, auto_approve: bool = False) -> None:
    """Run the Textual document mode interface."""
    app = DocumentApp(agent, auto_approve)
    app.run()
