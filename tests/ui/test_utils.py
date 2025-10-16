"""Tests for UI utility functions."""

from clippy.ui import convert_rich_to_textual_markup, strip_ansi_codes


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


def test_strip_ansi_codes_preserves_paperclip_prefix() -> None:
    """Test that strip_ansi_codes preserves paperclip emoji prefix."""
    text_with_prefix = "[📎] Hello World"
    cleaned = strip_ansi_codes(text_with_prefix)
    assert cleaned == "[📎] Hello World"


def test_strip_ansi_codes_removes_box_drawing_characters() -> None:
    """Test that strip_ansi_codes removes box drawing characters."""
    text_with_box = "┌─────┐\n│Text │\n└─────┘"
    cleaned = strip_ansi_codes(text_with_box)
    # Box drawing characters should be removed
    assert "─" not in cleaned
    assert "│" not in cleaned
    assert "┌" not in cleaned


def test_convert_rich_to_textual_markup_multiple_colors() -> None:
    """Test conversion with multiple color markups in one string."""
    text = "[cyan]Info:[/cyan] [bold cyan]Important[/bold cyan]"
    converted = convert_rich_to_textual_markup(text)
    assert converted == "[blue]Info:[/blue] [bold blue]Important[/bold blue]"


def test_strip_ansi_codes_with_control_characters() -> None:
    """Test that strip_ansi_codes removes control characters."""
    text_with_control = "Hello\x00\x08\x0b\x0cWorld"
    cleaned = strip_ansi_codes(text_with_control)
    # Control characters should be removed, but the text preserved
    assert "Hello" in cleaned
    assert "World" in cleaned
    assert "\x00" not in cleaned
    assert "\x08" not in cleaned
