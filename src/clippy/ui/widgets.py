"""Widget components for the document UI."""

from typing import Any

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Button, Static, TextArea


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
        # Title bar with Windows-style shield icon
        yield Static("🛡️  Permission Required", id="approval-title")

        # Scrollable content area
        with Vertical(id="approval-content"):
            # Main message with Windows-style phrasing
            yield Static(
                "Do you want to allow this app to make changes?", id="approval-main-message"
            )

            # Show tool name as the "program name"
            yield Static(f"Action: {self.tool_name}", id="approval-tool-name")

            # Show tool input in a bordered box
            input_lines = [f"  {k}: {v}" for k, v in self.tool_input.items()]
            input_text = "\n".join(input_lines)
            if input_text:
                yield Static(input_text, id="approval-tool-input")

            # Display diff if available
            if self.diff_content:
                yield Static("Show details ▼", id="diff-preview-header")
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
            yield Button("Yes", id="approval-yes", variant="primary")
            yield Button("Yes (Allow All)", id="approval-allow", variant="success")
            yield Button("No", id="approval-no", variant="default")
            yield Button("Cancel", id="approval-stop", variant="error")
