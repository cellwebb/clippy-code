"""Microsoft Word-inspired document interface using Textual."""

import os
import re
from typing import Any

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.events import Key
from textual.message import Message
from textual.widgets import Button, Static, TextArea

from .models import get_model_config, list_available_models


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes, Rich markup, and box-drawing characters from text."""
    # Remove all ANSI escape sequences
    ansi_escape = re.compile(
        r"""
        \x1b     # ESC
        (?:      # 7-bit C1 Fe
            [@-Z\\-_]
        |        # or ESC [ ... (CSI sequence)
            \[
            [0-?]*  # Parameter bytes
            [ -/]*  # Intermediate bytes
            [@-~]   # Final byte
        )
    """,
        re.VERBOSE,
    )
    text = ansi_escape.sub("", text)

    # Remove Rich markup tags
    rich_markup = re.compile(r"\[/?[a-zA-Z0-9_ #.=]+\]")
    text = rich_markup.sub("", text)

    # Remove Unicode box-drawing characters
    text = re.sub(r"[\u2500-\u257F]", "", text)

    # Remove zero-width characters
    text = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f-\x9f]", "", text)

    # Remove paperclip emoji prefix (used in interactive mode)
    text = re.sub(r"^\[📎\]\s*", "", text)

    # Filter out "You" lines that the agent outputs
    lines = text.split("\n")
    cleaned_lines = []
    skip_next = False

    for i, line in enumerate(lines):
        line_stripped = line.strip()
        # Skip "You" header and the following user message line
        if line_stripped == "You" and i + 1 < len(lines):
            skip_next = True
            continue
        if skip_next:
            skip_next = False
            continue
        if line_stripped:
            cleaned_lines.append(line_stripped)

    text = "\n".join(cleaned_lines)
    return text


class DocumentTextArea(TextArea):
    """Custom TextArea that sends messages on Enter."""

    class SubmitMessage(Message):
        """Message sent when Enter is pressed."""

        pass

    def on_key(self, event: Key) -> None:
        """Handle key events."""
        # Simple Enter detection
        if event.name == "enter":
            # Always submit on Enter, regardless of modifiers
            # This avoids issues with different Textual versions
            self.post_message(self.SubmitMessage())
            event.prevent_default()
            event.stop()


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

    #document-area {
        background: white;
        color: #000000;
        border: solid #d0d0d0;
        margin: 1 2;
        padding: 2 4;
        height: 1fr;
        width: 1fr;
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
        self.input_start_position = 0

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

        yield DocumentTextArea(id="document-area", language="markdown")
        yield DocumentStatusBar()

    def on_mount(self) -> None:
        """Initialize the document."""
        text_area = self.query_one("#document-area", DocumentTextArea)
        text_area.focus()
        # Initialize with the prompt
        text_area.insert("[You] ➜ ")
        self.input_start_position = len(text_area.text)
        self.update_status_bar()

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

    def on_document_text_area_submit_message(self, message: DocumentTextArea.SubmitMessage) -> None:
        """Handle Enter key press from the text area."""
        self.action_submit()

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
        text_area = self.query_one("#document-area", DocumentTextArea)
        full_text = text_area.text

        # Get only the text after the last assistant response
        user_input = full_text[self.input_start_position :].strip()

        if not user_input:
            return

        # Handle commands
        if user_input.lower() in ["/exit", "/quit"]:
            self.exit()
            return
        elif user_input.lower() in ["/reset", "/clear", "/new"]:
            # For command responses, we want to show the command
            text_area.insert("\n\n")
            text_area.move_cursor_relative(rows=1)
            self.action_reset()
            return
        elif user_input.lower() == "/help":
            # For command responses, we want to show the command
            text_area.insert("\n\n")
            text_area.move_cursor_relative(rows=1)
            self.action_toggle_help()
            return
        elif user_input.lower() == "/status":
            # For command responses, we want to show the command
            text_area.insert("\n\n")
            text_area.move_cursor_relative(rows=1)
            self.action_show_status()
            return
        elif user_input.lower() == "/compact":
            # For command responses, we want to show the command
            text_area.insert("\n\n")
            text_area.move_cursor_relative(rows=1)
            self.handle_compact_command()
            return
        elif user_input.lower().startswith("/model"):
            # For command responses, we want to show the command
            text_area.insert("\n\n")
            text_area.move_cursor_relative(rows=1)
            self.handle_model_command(user_input)
            return

        # For regular messages, clear the input line and add spacing before response
        text_area.delete(
            (0, self.input_start_position),  # Start position
            (0, len(text_area.text)),  # End position
        )
        text_area.insert("\n\n")
        text_area.move_cursor_relative(rows=1)

        # Run the agent
        self.run_worker(self.run_agent_async(user_input), exclusive=True)

    def handle_compact_command(self) -> None:
        """Handle conversation compacting command."""
        text_area = self.query_one("#document-area", DocumentTextArea)
        status_bar = self.query_one(DocumentStatusBar)

        # Show compacting status in status bar
        status_bar.update_message("🔄 Compacting conversation...")

        try:
            success, message, stats = self.agent.compact_conversation()

            if success:
                status_text = f"""
📎 clippy - Conversation Compacted

Token Reduction:
  Before: {stats["before_tokens"]:,} tokens
  After:  {stats["after_tokens"]:,} tokens
  Saved:  {stats["tokens_saved"]:,} tokens ({stats["reduction_percent"]:.1f}%)

Messages:
  Before:      {stats["messages_before"]} messages
  After:       {stats["messages_after"]} messages
  Summarized:  {stats["messages_summarized"]} messages

The conversation history has been condensed while preserving recent context."""
            else:
                status_text = f"""
📎 clippy - Cannot Compact

{message}"""

            text_area.insert(status_text)
            text_area.insert("\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)
            self.update_status_bar()

        except Exception as e:
            text_area.insert(f"Error compacting conversation: {e}\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)
            status_bar.update_message("❌ Error occurred")

    def handle_model_command(self, command: str) -> None:
        """Handle model switching command."""
        text_area = self.query_one("#document-area", DocumentTextArea)
        status_bar = self.query_one(DocumentStatusBar)

        parts = command.split(maxsplit=1)
        if len(parts) == 1 or parts[1].lower() == "list":
            # Show available models
            models = list_available_models()
            model_list = "\n".join(f"  {name:20} - {desc}" for name, desc in models)
            current_model = self.agent.model
            current_provider = self.agent.base_url or "OpenAI"

            panel_content = f"""
📎 clippy - Available Models

{model_list}

Current: {current_model} ({current_provider})

Usage: /model <name>"""

            text_area.insert(panel_content)
            text_area.insert("\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)
        else:
            # Switch to specified model
            model_name = parts[1].strip()
            config = get_model_config(model_name)

            if config:
                # Use preset configuration
                # Load API key from environment variable specified in config
                api_key = os.getenv(config.api_key_env)

                if not api_key:
                    # Continue anyway - some providers like Ollama might not need a key
                    api_key = "not-set"

                success, message = self.agent.switch_model(
                    model=config.model_id, base_url=config.base_url, api_key=api_key
                )
            else:
                # Treat as custom model ID (keep current base_url and api_key)
                success, message = self.agent.switch_model(model=model_name)

            if success:
                text_area.insert(f"✓ Model switched to: {message}")
                status_bar.update_message(f"✓ Model switched to: {message}")
            else:
                text_area.insert(f"✗ Error: {message}")
                status_bar.update_message(f"✗ Error: {message}")

            text_area.insert("\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)
            self.update_status_bar()

    async def run_agent_async(self, user_input: str) -> None:
        """Run agent asynchronously."""
        text_area = self.query_one("#document-area", DocumentTextArea)
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

            plain_console = Console(
                file=output_buffer, force_terminal=False, no_color=True, legacy_windows=False
            )

            old_console = None
            if hasattr(self.agent, "console"):
                old_console = self.agent.console
                self.agent.console = plain_console

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

            # Clean output
            clean_output = (
                strip_ansi_codes(full_output) if full_output.strip() else "Task completed."
            )

            # Add assistant response
            text_area.insert(clean_output)
            text_area.insert("\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)

            # Update the position where next user input starts
            self.input_start_position = len(text_area.text)

            # Update status
            self.update_status_bar()

        except Exception as e:
            text_area.insert(f"Error: {e}\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)

            # Update status bar to show error
            status_bar.update_message("❌ Error occurred")

    def action_reset(self) -> None:
        """Reset conversation."""
        self.agent.reset_conversation()
        text_area = self.query_one("#document-area", DocumentTextArea)
        text_area.insert("✓ Conversation history reset")
        text_area.insert("\n\n[You] ➜ ")
        text_area.move_cursor_relative(rows=1)
        self.input_start_position = len(text_area.text)
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

    def action_show_status(self) -> None:
        """Show status information."""
        text_area = self.query_one("#document-area", DocumentTextArea)
        status_bar = self.query_one(DocumentStatusBar)

        try:
            status = self.agent.get_token_count()
            status_text = f"""
📎 clippy - Session Status

Model: {status.get("model", "unknown")}
Provider: {status.get("base_url") or "OpenAI"}
Messages: {status.get("message_count", 0)}
Tokens: {status.get("total_tokens", 0):,}
Context Usage: {status.get("usage_percent", 0):.1f}%"""
            text_area.insert(status_text)
            text_area.insert("\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)
        except Exception as e:
            text_area.insert(f"Error getting status: {e}\n\n[You] ➜ ")
            text_area.move_cursor_relative(rows=1)
            self.input_start_position = len(text_area.text)
            status_bar.update_message("❌ Error occurred")


def run_document_mode(agent: Any, auto_approve: bool = False) -> None:
    """Run the Textual document mode interface."""
    app = DocumentApp(agent, auto_approve)
    app.run()
