"""Document UI module for clippy-code."""

from .document_app import DocumentApp, run_document_mode
from .styles import DOCUMENT_APP_CSS
from .utils import convert_rich_to_textual_markup, strip_ansi_codes
from .widgets import (
    ApprovalBackdrop,
    ApprovalDialog,
    DiffDisplay,
    DocumentHeader,
    DocumentRibbon,
    DocumentStatusBar,
)

__all__ = [
    # Main app
    "DocumentApp",
    "run_document_mode",
    # Widgets
    "DocumentHeader",
    "DocumentRibbon",
    "DocumentStatusBar",
    "DiffDisplay",
    "ApprovalBackdrop",
    "ApprovalDialog",
    # Styles
    "DOCUMENT_APP_CSS",
    # Utils
    "convert_rich_to_textual_markup",
    "strip_ansi_codes",
]
