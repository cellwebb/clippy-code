"""Tests for the document UI functionality."""

from unittest.mock import Mock, patch

from clippy.document_ui import (
    DocumentTextArea,
    strip_ansi_codes,
)


def test_strip_ansi_codes_removes_ansi_sequences() -> None:
    """Test that strip_ansi_codes removes ANSI escape sequences."""
    text_with_ansi = "\x1b[31mRed Text\x1b[0m"
    cleaned = strip_ansi_codes(text_with_ansi)
    assert cleaned == "Red Text"


def test_strip_ansi_codes_removes_rich_markup() -> None:
    """Test that strip_ansi_codes removes Rich markup."""
    text_with_rich = "[bold]Bold Text[/bold]"
    cleaned = strip_ansi_codes(text_with_rich)
    assert cleaned == "Bold Text"


def test_strip_ansi_codes_removes_paperclip_prefix() -> None:
    """Test that strip_ansi_codes removes paperclip emoji prefix."""
    text_with_prefix = "[📎] Hello World"
    cleaned = strip_ansi_codes(text_with_prefix)
    assert cleaned == "Hello World"


def test_document_text_area_submit_message() -> None:
    """Test that DocumentTextArea creates SubmitMessage on Enter key."""
    text_area = DocumentTextArea(id="document-area", language="markdown")

    # Create a mock event for Enter key
    event = Mock()
    event.name = "enter"
    event.prevent_default = Mock()
    event.stop = Mock()

    # Mock post_message to track calls
    with patch.object(text_area, "post_message") as mock_post:
        text_area.on_key(event)

        # Verify SubmitMessage was posted
        mock_post.assert_called_once()

        # Verify event methods were called
        event.prevent_default.assert_called_once()
        event.stop.assert_called_once()


def test_document_text_area_does_not_submit_on_other_keys() -> None:
    """Test that DocumentTextArea only submits on Enter key."""
    text_area = DocumentTextArea(id="document-area", language="markdown")

    # Create a mock event for a different key
    event = Mock()
    event.name = "a"

    # Mock post_message to track calls
    with patch.object(text_area, "post_message") as mock_post:
        text_area.on_key(event)

        # SubmitMessage should not be posted
        mock_post.assert_not_called()
