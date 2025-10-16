"""Utility functions for the document UI."""

import re


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
