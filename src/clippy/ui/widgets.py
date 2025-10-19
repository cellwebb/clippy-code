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
            "👀📎 clippy - 📄 Document Mode\n"
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


class ErrorPanel(Container):
    """Enhanced error panel for displaying MCP and other errors with details."""

    def __init__(
        self, error_message: str, error_details: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        super().__init__(**kwargs)
        self.error_message = error_message
        self.error_details = error_details or {}
        self.expanded = False

    def compose(self) -> ComposeResult:
        yield Static("❌ Error Occurred", id="error-title")

        with Vertical(id="error-content"):
            # Main error message
            yield Static(self.error_message, id="error-main-message")

            # Error details section (expandable)
            if self.error_details:
                yield Static("Error Details:", id="error-details-header")

                # Format error details
                detail_lines = []
                for key, value in self.error_details.items():
                    if key == "server_id":
                        detail_lines.append(f"  [bold]MCP Server:[/bold] {value}")
                    elif key == "tool_name":
                        detail_lines.append(f"  [bold]Tool:[/bold] {value}")
                    elif key == "original_error":
                        # Truncate very long error messages
                        error_str = str(value)
                        if len(error_str) > 200:
                            error_str = error_str[:197] + "..."
                        detail_lines.append(f"  [bold]Original Error:[/bold] {error_str}")
                    else:
                        detail_lines.append(f"  [bold]{key}:[/bold] {value}")

                if not self.expanded and len(detail_lines) > 5:
                    # Show truncated details
                    truncated_lines = detail_lines[:5]
                    for line in truncated_lines:
                        yield Static(line)
                    yield Static(
                        f"... and {len(detail_lines) - 5} more details", classes="truncated-hint"
                    )
                    yield Button("Show All Details", id="expand-error", variant="default")
                else:
                    # Show all details
                    for line in detail_lines:
                        yield Static(line)
                    if len(detail_lines) > 5:
                        yield Button("Show Fewer Details", id="collapse-error", variant="default")

            # Suggestions based on error type
            suggestions = self._generate_suggestions()
            if suggestions:
                yield Static("Suggestions:", id="suggestions-header")
                for suggestion in suggestions:
                    yield Static(f"  • {suggestion}", classes="suggestion")

        with Horizontal(id="error-buttons"):
            yield Button("OK", id="error-ok", variant="primary")
            yield Button("Retry", id="error-retry", variant="default")

    def _generate_suggestions(self) -> list[str]:
        """Generate helpful suggestions based on error type."""
        suggestions = []

        error_lower = self.error_message.lower()
        if "not connected" in error_lower or "connection" in error_lower:
            suggestions.append("Check if the MCP server is running")
            suggestions.append("Try refreshing the MCP server connections with /mcp refresh")
            if self.error_details.get("server_id"):
                suggestions.append(
                    f"Ensure server '{self.error_details['server_id']}' is properly configured"
                )

        if "not trusted" in error_lower:
            suggestions.append("Trust the server using /mcp allow <server-id>")
            suggestions.append("Check that you want to allow this MCP server to execute tools")

        if "not found" in error_lower:
            suggestions.append("Verify the MCP server configuration in mcp.json")
            suggestions.append("Check that the server command and arguments are correct")

        if "permission denied" in error_lower:
            suggestions.append("Check file permissions if this is a file operation")
            suggestions.append("Ensure the command can be executed in the current directory")

        if "timeout" in error_lower or "timed out" in error_lower:
            suggestions.append("The operation took too long to complete")
            suggestions.append("Try increasing the timeout in the MCP server configuration")

        return suggestions

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for error panel."""
        button_id = event.button.id

        if button_id == "expand-error":
            self.expanded = True
            self._refresh_content()
        elif button_id == "collapse-error":
            self.expanded = False
            self._refresh_content()
        elif button_id == "error-ok":
            self.remove()
        elif button_id == "error-retry":
            # Signal retry request to parent
            self.remove()

    def _refresh_content(self) -> None:
        """Refresh the error panel content after expansion state change."""
        content = self.query_one("#error-content", Vertical)
        content.remove_children()
        self._build_content(content)

    def _build_content(self, content: Vertical) -> None:
        """Build the content section of the error panel."""
        # Error details section
        if self.error_details:
            content.mount(Static("Error Details:", id="error-details-header"))

            # Format error details
            detail_lines = []
            for key, value in self.error_details.items():
                if key == "server_id":
                    detail_lines.append(f"  [bold]MCP Server:[/bold] {value}")
                elif key == "tool_name":
                    detail_lines.append(f"  [bold]Tool:[/bold] {value}")
                elif key == "original_error":
                    # Truncate very long error messages
                    error_str = str(value)
                    if len(error_str) > 200:
                        error_str = error_str[:197] + "..."
                    detail_lines.append(f"  [bold]Original Error:[/bold] {error_str}")
                else:
                    detail_lines.append(f"  [bold]{key}:[/bold] {value}")

            if not self.expanded and len(detail_lines) > 5:
                # Show truncated details
                truncated_lines = detail_lines[:5]
                for line in truncated_lines:
                    content.mount(Static(line))
                content.mount(
                    Static(
                        f"... and {len(detail_lines) - 5} more details", classes="truncated-hint"
                    )
                )
                content.mount(Button("Show All Details", id="expand-error", variant="default"))
            else:
                # Show all details
                for line in detail_lines:
                    content.mount(Static(line))
                if len(detail_lines) > 5:
                    content.mount(
                        Button("Show Fewer Details", id="collapse-error", variant="default")
                    )

        # Suggestions
        suggestions = self._generate_suggestions()
        if suggestions:
            content.mount(Static("Suggestions:", id="suggestions-header"))
            for suggestion in suggestions:
                content.mount(Static(f"  • {suggestion}", classes="suggestion"))


class ApprovalDialog(Container):
    """Enhanced dialog for approval requests with MCP support and truncation."""

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
        self.is_mcp_tool = tool_name.startswith("mcp__")
        self.expanded = {"input": True, "diff": False}
        self.max_input_lines = 8  # Truncate long inputs

    def compose(self) -> ComposeResult:
        # Title bar with enhanced icons for different tool types
        if self.is_mcp_tool:
            title = "🌐 MCP Tool Permission Required"
        else:
            title = "🛡️  Permission Required"
        yield Static(title, id="approval-title")

        # Scrollable content area
        with Vertical(id="approval-content"):
            # Main message with context-specific phrasing
            if self.is_mcp_tool:
                yield Static(
                    "Do you want to allow this MCP server to perform this action?",
                    id="approval-main-message",
                )
            else:
                yield Static(
                    "Do you want to allow this app to make changes?",
                    id="approval-main-message",
                )

            # Show tool name and MCP server info if applicable
            if self.is_mcp_tool:
                try:
                    from ..mcp.naming import parse_mcp_qualified_name

                    server_id, tool = parse_mcp_qualified_name(self.tool_name)
                    yield Static(
                        f"MCP Tool: [bold]{tool}[/bold] [dim](from {server_id})[/dim]",
                        id="approval-tool-name",
                    )
                except Exception:
                    yield Static(f"MCP Tool: {self.tool_name}", id="approval-tool-name")
            else:
                yield Static(f"Action: {self.tool_name}", id="approval-tool-name")

            # Show tool input with truncation and expand/collapse
            if self.tool_input:
                yield Static("Parameters:", id="input-section-header")

                # Format and potentially truncate input
                input_lines = []
                for k, v in self.tool_input.items():
                    value_str = str(v)
                    # Truncate very long values
                    if len(value_str) > 100:
                        value_str = value_str[:97] + "..."
                    input_lines.append(f"  [bold]{k}:[/bold] {value_str}")

                input_text = "\n".join(input_lines)

                # Show truncated or full input based on expansion state
                if len(input_lines) > self.max_input_lines and not self.expanded["input"]:
                    truncated_text = "\n".join(input_lines[: self.max_input_lines])
                    yield Static(truncated_text, id="approval-tool-input")
                    yield Static(
                        f"... and {len(input_lines) - self.max_input_lines} more parameters",
                        id="input-truncated",
                        classes="truncated-hint",
                    )
                    yield Button("Show All Parameters", id="expand-input", variant="default")
                else:
                    yield Static(input_text, id="approval-tool-input")
                    if len(input_lines) > self.max_input_lines:
                        yield Button(
                            "Show Fewer Parameters", id="collapse-input", variant="default"
                        )

            # Enhanced diff handling for MCP tools
            if self.diff_content is not None:
                if self.is_mcp_tool:
                    yield Static("MCP Tool Output Preview:", id="diff-section-header")
                else:
                    yield Static("File Changes Preview:", id="diff-section-header")

                if self.diff_content == "":
                    yield Static("No changes (content identical)", id="diff-no-changes")
                else:
                    # Show diff with expand/collapse for large diffs
                    diff_lines = self.diff_content.split("\n")
                    if len(diff_lines) > 20 and not self.expanded["diff"]:
                        truncated_diff = "\n".join(diff_lines[:20])
                        diff_display = DiffDisplay(truncated_diff, id="diff-display")
                        yield diff_display
                        yield Static(
                            f"... and {len(diff_lines) - 20} more lines",
                            id="diff-truncated",
                            classes="truncated-hint",
                        )
                        yield Button("Show Full Diff", id="expand-diff", variant="default")
                    else:
                        diff_display = DiffDisplay(self.diff_content, id="diff-display")
                        yield diff_display
                        if len(diff_lines) > 20:
                            yield Button("Show Fewer Lines", id="collapse-diff", variant="default")

            elif self.tool_name in ["write_file", "edit_file"]:
                yield Static(
                    "No preview available for this change",
                    id="diff-preview-unavailable",
                )
            elif self.is_mcp_tool:
                yield Static(
                    "No output preview available for this MCP tool",
                    id="mcp-preview-unavailable",
                )

        # Approval buttons - always at bottom, outside scrollable area
        with Horizontal(id="approval-buttons"):
            if self.is_mcp_tool:
                yield Button("Allow MCP Tool", id="approval-yes", variant="primary")
                yield Button("Trust Server & Allow All", id="approval-allow", variant="success")
            else:
                yield Button("Yes", id="approval-yes", variant="primary")
                yield Button("Yes (Allow All)", id="approval-allow", variant="success")
            yield Button("No", id="approval-no", variant="default")
            yield Button("Cancel", id="approval-stop", variant="error")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses for expand/collapse functionality."""
        button_id = event.button.id

        if button_id == "expand-input":
            self.expanded["input"] = True
            self._refresh_content()
        elif button_id == "collapse-input":
            self.expanded["input"] = False
            self._refresh_content()
        elif button_id == "expand-diff":
            self.expanded["diff"] = True
            self._refresh_content()
        elif button_id == "collapse-diff":
            self.expanded["diff"] = False
            self._refresh_content()

    def _refresh_content(self) -> None:
        """Refresh the dialog content after expansion state change."""
        # Remove existing content except buttons
        content = self.query_one("#approval-content", Vertical)
        content.remove_children()

        # Re-create the content
        self._build_content(content)

    def _build_content(self, content: Vertical) -> None:
        """Build the content section of the dialog."""

        # Main message
        if self.is_mcp_tool:
            content.mount(
                Static(
                    "Do you want to allow this MCP server to perform this action?",
                    id="approval-main-message",
                )
            )
        else:
            content.mount(
                Static(
                    "Do you want to allow this app to make changes?",
                    id="approval-main-message",
                )
            )

        # Tool name with MCP info
        if self.is_mcp_tool:
            try:
                from ..mcp.naming import parse_mcp_qualified_name

                server_id, tool = parse_mcp_qualified_name(self.tool_name)
                content.mount(
                    Static(
                        f"MCP Tool: [bold]{tool}[/bold] [dim](from {server_id})[/dim]",
                        id="approval-tool-name",
                    )
                )
            except Exception:
                content.mount(Static(f"MCP Tool: {self.tool_name}", id="approval-tool-name"))
        else:
            content.mount(Static(f"Action: {self.tool_name}", id="approval-tool-name"))

        # Tool input section
        if self.tool_input:
            content.mount(Static("Parameters:", id="input-section-header"))

            # Format and potentially truncate input
            input_lines = []
            for k, v in self.tool_input.items():
                value_str = str(v)
                # Truncate very long values
                if len(value_str) > 100:
                    value_str = value_str[:97] + "..."
                input_lines.append(f"  [bold]{k}:[/bold] {value_str}")

            input_text = "\n".join(input_lines)

            # Show truncated or full input based on expansion state
            if len(input_lines) > self.max_input_lines and not self.expanded["input"]:
                truncated_text = "\n".join(input_lines[: self.max_input_lines])
                content.mount(Static(truncated_text, id="approval-tool-input"))
                content.mount(
                    Static(
                        f"... and {len(input_lines) - self.max_input_lines} more parameters",
                        id="input-truncated",
                        classes="truncated-hint",
                    )
                )
                content.mount(Button("Show All Parameters", id="expand-input", variant="default"))
            else:
                content.mount(Static(input_text, id="approval-tool-input"))
                if len(input_lines) > self.max_input_lines:
                    content.mount(
                        Button("Show Fewer Parameters", id="collapse-input", variant="default")
                    )

        # Diff section
        if self.diff_content is not None:
            if self.is_mcp_tool:
                content.mount(Static("MCP Tool Output Preview:", id="diff-section-header"))
            else:
                content.mount(Static("File Changes Preview:", id="diff-section-header"))

            if self.diff_content == "":
                content.mount(Static("No changes (content identical)", id="diff-no-changes"))
            else:
                # Show diff with expand/collapse for large diffs
                diff_lines = self.diff_content.split("\n")
                if len(diff_lines) > 20 and not self.expanded["diff"]:
                    truncated_diff = "\n".join(diff_lines[:20])
                    content.mount(DiffDisplay(truncated_diff, id="diff-display"))
                    content.mount(
                        Static(
                            f"... and {len(diff_lines) - 20} more lines",
                            id="diff-truncated",
                            classes="truncated-hint",
                        )
                    )
                    content.mount(Button("Show Full Diff", id="expand-diff", variant="default"))
                else:
                    content.mount(DiffDisplay(self.diff_content, id="diff-display"))
                    if len(diff_lines) > 20:
                        content.mount(
                            Button("Show Fewer Lines", id="collapse-diff", variant="default")
                        )

        elif self.tool_name in ["write_file", "edit_file"]:
            content.mount(
                Static(
                    "No preview available for this change",
                    id="diff-preview-unavailable",
                )
            )
        elif self.is_mcp_tool:
            content.mount(
                Static(
                    "No output preview available for this MCP tool",
                    id="mcp-preview-unavailable",
                )
            )
