"""Real-world edit_file tests based on actual LLM usage patterns and failures.

These tests simulate common patterns that LLMs generate when using edit_file,
including common mistakes and edge cases found in production logs.
"""

from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionManager


@pytest.fixture
def executor() -> ActionExecutor:
    """Create an executor instance."""
    manager = PermissionManager()
    return ActionExecutor(manager)


@pytest.fixture
def sample_python_file(tmp_path: Path) -> Path:
    """Create a realistic Python file with common patterns."""
    file_path = tmp_path / "example.py"
    content = '''"""Example module with common Python patterns."""

from typing import Optional
from .widgets import (
    DocumentHeader,
    DocumentStatusBar,
    ApprovalDialog,
)
from .styles import DOCUMENT_APP_CSS
from .utils import convert_rich_to_textual_markup, strip_ansi_codes


class DocumentApp:
    """Main document application."""

    def __init__(self) -> None:
        self.current_error_panel: ErrorPanel | None = None
        self.current_modal_backdrop: ModalBackdrop | None = None
        self.current_model_manager: ModelManager | None = None

    def show_models(self) -> None:
        """Display available models."""
        conv_log = self.query_one("#conversation-log", RichLog)
        models = list_available_models()
        current_model = self.agent.model
        current_provider = self.agent.base_url or "OpenAI"

        # Format model list
        model_text = "\\n".join([f"- {m}" for m in models])
        conv_log.write(model_text)

    def mount_dialog(self) -> None:
        """Mount a dialog backdrop."""
        # Mount backdrop with dialog
        self.mount(self.current_modal_backdrop)
        self.current_modal_backdrop.mount(self.current_model_manager)


class ErrorPanel:
    """Error display panel."""

    def __init__(self) -> None:
        self.current_error_panel: ErrorPanel | None = None
        self.error_message: str = ""


class ModalBackdrop:
    """Modal backdrop widget."""

    def __init__(self) -> None:
        self.current_error_panel: ErrorPanel | None = None


class ModelManager:
    """Model management widget."""

    def __init__(self) -> None:
        self.current_error_panel: ErrorPanel | None = None


__all__ = [
    "DocumentApp",
    "ErrorPanel",
    "ModalBackdrop",
    "ModelManager",
]
'''
    file_path.write_text(content)
    return file_path


# ============================================================================
# IMPORT STATEMENT TESTS
# ============================================================================


def test_match_import_with_parenthesis_literal(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test matching import statement with opening parenthesis (exact string match)."""
    # With exact string matching, no escaping needed - just match the literal text
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": "from .widgets import (",
            "content": "from .widgets import DocumentHeader,",
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert "from .widgets import DocumentHeader," in content
    assert "from .widgets import (" not in content


def test_match_import_line_without_over_escaping(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test matching import with exact string (no escaping needed)."""
    # Exact string matching - no escaping of dots or other characters
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": "from .styles import DOCUMENT_APP_CSS",
            "content": "from .styles import DOCUMENT_APP_CSS, MODAL_CSS",
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert "from .styles import DOCUMENT_APP_CSS, MODAL_CSS" in content


def test_match_import_with_anchors_to_avoid_multiple_matches(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test using exact string to match the exact line."""
    # With exact string matching, no anchors needed - just match the exact text
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": "from typing import Optional",
            "content": "from typing import Optional, List",
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert "from typing import Optional, List" in content


# ============================================================================
# TYPE ANNOTATION TESTS (MULTIPLE MATCHES PROBLEM)
# ============================================================================


def test_match_type_annotation_fails_without_context(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test that matching ambiguous pattern fails with multiple matches."""
    # This should fail because the pattern appears 4 times
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": "self.current_error_panel: ErrorPanel | None = None",
            "content": "self.current_error_panel: ErrorPanel | None = None  # Updated",
        },
    )

    assert success is False
    assert "found 4 times" in message
    assert "expected exactly one match" in message


# ============================================================================
# SPECIAL CHARACTER ESCAPING TESTS
# ============================================================================


def test_match_brackets_in_string_literal(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test matching string with special characters (no escaping needed)."""
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": 'model_text = "\\n".join([f"- {m}" for m in models])',
            "content": 'model_text = ", ".join([f"{m}" for m in models])',
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert 'model_text = ", ".join([f"{m}" for m in models])' in content


def test_match_query_selector_with_hash(executor: ActionExecutor, sample_python_file: Path) -> None:
    """Test matching CSS selector with # (no escaping needed)."""
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": 'self.query_one("#conversation-log", RichLog)',
            "content": 'self.query_one("#conv-log", RichLog)',
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert 'self.query_one("#conv-log", RichLog)' in content


# ============================================================================
# __ALL__ EXPORT TESTS
# ============================================================================


def test_match_all_export_list(executor: ActionExecutor, sample_python_file: Path) -> None:
    """Test matching __all__ list with proper escaping."""
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": r"__all__ = \[",
            "content": "__all__: list[str] = [",
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert "__all__: list[str] = [" in content


# ============================================================================
# BLOCK OPERATION TESTS
# ============================================================================


def test_block_replace_with_indented_comments(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test block replace with indented comment markers (exact string matching)."""
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "block_replace",
            "start_pattern": "# Mount backdrop with dialog",
            "end_pattern": "self.current_modal_backdrop.mount(self.current_model_manager)",
            "content": """self.backdrop = Backdrop()
        self.mount(self.backdrop)
        self.backdrop.mount(ModelDialog())""",
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert "self.backdrop = Backdrop()" in content
    assert "self.backdrop.mount(ModelDialog())" in content


# ============================================================================
# COMMON FAILURE SCENARIOS
# ============================================================================


def test_pattern_not_found_gives_clear_error(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test that pattern not found gives a clear error message."""
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": "this pattern does not exist",
            "content": "replacement",
        },
    )

    assert success is False
    assert "Pattern 'this pattern does not exist' not found in file" in message


def test_invalid_regex_gives_clear_error(
    executor: ActionExecutor, sample_python_file: Path
) -> None:
    """Test that pattern not found gives a clear error (no regex errors anymore)."""
    # With exact string matching, there are no regex compilation errors
    # This test now just checks pattern not found behavior
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "replace",
            "pattern": "unclosed[bracket",  # This is now just a literal string
            "content": "replacement",
        },
    )

    assert success is False
    # Pattern should not be found (it's a valid string, just not in the file)
    assert "not found" in message


def test_delete_multiple_matching_lines(executor: ActionExecutor, sample_python_file: Path) -> None:
    """Test deleting all lines matching a pattern (delete allows multiple)."""
    # Delete operation can match multiple lines
    success, message, _ = executor.execute(
        "edit_file",
        {
            "path": str(sample_python_file),
            "operation": "delete",
            "pattern": "self.current_error_panel: ErrorPanel | None = None",
        },
    )

    assert success is True
    content = sample_python_file.read_text()
    assert "self.current_error_panel: ErrorPanel | None = None" not in content
