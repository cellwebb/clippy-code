"""Tests for UI widget components."""

from clippy.ui.widgets import (
    ApprovalDialog,
    DiffDisplay,
    DocumentHeader,
    DocumentRibbon,
    DocumentStatusBar,
)


def test_document_header_initialization() -> None:
    """Test that DocumentHeader initializes correctly."""
    header = DocumentHeader()
    # DocumentHeader is a Static widget that should initialize without errors
    assert header is not None
    assert isinstance(header, DocumentHeader)


def test_document_status_bar_update_status() -> None:
    """Test that DocumentStatusBar can update its status."""
    status_bar = DocumentStatusBar()
    # Method should execute without errors
    status_bar.update_status("gpt-4o", 5, 1000)
    assert status_bar is not None


def test_document_status_bar_update_message() -> None:
    """Test that DocumentStatusBar can update with a message."""
    status_bar = DocumentStatusBar()
    # Method should execute without errors
    status_bar.update_message("Test message")
    assert status_bar is not None


def test_diff_display_initialization() -> None:
    """Test that DiffDisplay initializes with diff content."""
    diff_content = "+++ file.txt\n+Added line\n-Removed line"
    diff_display = DiffDisplay(diff_content)
    assert diff_display.diff_content == diff_content
    assert diff_display.read_only is True
    assert diff_display.show_line_numbers is True


def test_approval_dialog_initialization() -> None:
    """Test that ApprovalDialog initializes with tool info."""
    tool_name = "write_file"
    tool_input = {"path": "/tmp/test.txt", "content": "Hello"}
    dialog = ApprovalDialog(tool_name, tool_input)

    assert dialog.tool_name == tool_name
    assert dialog.tool_input == tool_input
    assert dialog.diff_content is None


def test_approval_dialog_with_diff() -> None:
    """Test that ApprovalDialog can include diff content."""
    tool_name = "edit_file"
    tool_input = {"path": "/tmp/test.txt"}
    diff_content = "+Added line\n-Removed line"
    dialog = ApprovalDialog(tool_name, tool_input, diff_content)

    assert dialog.tool_name == tool_name
    assert dialog.tool_input == tool_input
    assert dialog.diff_content == diff_content


def test_document_ribbon_initialization() -> None:
    """Test that DocumentRibbon initializes correctly."""
    ribbon = DocumentRibbon()
    # The ribbon should be a Vertical container
    assert ribbon is not None
    assert isinstance(ribbon, DocumentRibbon)
