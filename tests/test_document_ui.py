"""Tests for the document UI functionality."""

from clippy.document_ui import convert_rich_to_textual_markup, strip_ansi_codes


def test_strip_ansi_codes_removes_ansi_sequences() -> None:
    """Test that strip_ansi_codes removes ANSI escape sequences."""
    text_with_ansi = "\x1b[31mRed Text\x1b[0m"
    cleaned = strip_ansi_codes(text_with_ansi)
    assert cleaned == "Red Text"


def test_strip_ansi_codes_preserves_and_converts_rich_markup() -> None:
    """Test that strip_ansi_codes preserves Rich markup but converts it to Textual format."""
    text_with_rich = "[bold]Bold Text[/bold]"
    cleaned = strip_ansi_codes(text_with_rich)
    # Should preserve markup but convert to Textual format
    assert cleaned == "[bold]Bold Text[/bold]"


def test_convert_rich_to_textual_markup() -> None:
    """Test that convert_rich_to_textual_markup properly converts Rich colors to Textual colors."""
    # Test cyan conversion
    text = "[bold cyan]→ tool_name[/bold cyan]\n[cyan]tool input[/cyan]"
    converted = convert_rich_to_textual_markup(text)
    assert converted == "[bold blue]→ tool_name[/bold blue]\n[blue]tool input[/blue]"

    # Test green conversion
    text = "[bold green]✓ Success message[/bold green]"
    converted = convert_rich_to_textual_markup(text)
    assert converted == "[bold green]✓ Success message[/bold green]"

    # Test red conversion
    text = "[bold red]✗ Error message[/bold red]"
    converted = convert_rich_to_textual_markup(text)
    assert converted == "[bold red]✗ Error message[/bold red]"

    # Test yellow conversion
    text = "[bold yellow]⊘ Warning message[/bold yellow]"
    converted = convert_rich_to_textual_markup(text)
    assert converted == "[bold yellow]⊘ Warning message[/bold yellow]"


def test_strip_ansi_codes_removes_paperclip_prefix() -> None:
    """Test that strip_ansi_codes removes paperclip emoji prefix."""
    text_with_prefix = "[📎] Hello World"
    cleaned = strip_ansi_codes(text_with_prefix)
    assert cleaned == "Hello World"
