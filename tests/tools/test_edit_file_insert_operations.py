"""Tests for edit_file insert operations: insert_before and insert_after."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager
from clippy.tools.edit_file import edit_file


@pytest.fixture
def executor() -> ActionExecutor:
    """Create an executor instance."""
    manager = PermissionManager()
    return ActionExecutor(manager)


@pytest.fixture
def executor_direct() -> ActionExecutor:
    """Create an executor for direct _edit_file calls."""
    config = PermissionConfig(
        auto_approve=set(),
        require_approval=set(),
        deny=set(),
    )
    manager = PermissionManager(config)
    return ActionExecutor(manager)


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


# ============================================================================
# BASIC INSERT_BEFORE OPERATIONS
# ============================================================================


def test_edit_file_insert_before_by_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting before a line using pattern matching."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "content": "Inserted line",
            "pattern": "Line 2",
        },
    )

    assert success is True
    assert "Successfully performed insert_before operation" in message
    expected = "Line 1\nInserted line\nLine 2\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_insert_before_at_beginning(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting before the first line of a file."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "content": "First line",
            "pattern": "Line 1",
        },
    )

    assert success is True
    assert "Successfully performed insert_before operation" in message
    expected = "First line\nLine 1\nLine 2\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_insert_before_pattern_not_found(executor: ActionExecutor, temp_dir: str) -> None:
    """Test insert_before when pattern is not found."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "content": "Test content",
            "pattern": "Non-existent line",
        },
    )

    assert success is False
    assert "Pattern 'Non-existent line' not found in file" in message


# ============================================================================
# BASIC INSERT_AFTER OPERATIONS
# ============================================================================


def test_edit_file_insert_after_by_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting after a line using pattern matching."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_after",
            "content": "Inserted line",
            "pattern": "Line 2",
        },
    )

    assert success is True
    assert "Successfully performed insert_after operation" in message
    expected = "Line 1\nLine 2\nInserted line\nLine 3\n"
    assert test_file.read_text() == expected


def test_edit_file_insert_after_at_end(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting after the last line of a file."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_after",
            "content": "Last line",
            "pattern": "Line 3",
        },
    )

    assert success is True, f"Operation failed: {message}"
    assert "Successfully performed insert_after operation" in message
    expected = "Line 1\nLine 2\nLine 3\nLast line\n"
    assert test_file.read_text() == expected


# ============================================================================
# SUBSTRING MATCHING
# ============================================================================


def test_edit_file_insert_with_substring_match(executor: ActionExecutor, temp_dir: str) -> None:
    """Test inserting using substring pattern matching (case-sensitive)."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nTest line content\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "content": "Before test",
            "pattern": "Test line",  # Exact substring match (case-sensitive)
        },
    )

    assert success is True
    assert "Successfully performed insert_before operation" in message
    expected = "Line 1\nBefore test\nTest line content\nLine 3\n"
    assert test_file.read_text() == expected


def test_insert_operations_with_substring_match(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert operations with substring pattern matching."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello_world():\n    pass\n\ndef test_function():\n    pass\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_before",
        content="def new_function():\n    pass\n",
        pattern="hello_world",
    )

    assert success
    content = test_file.read_text()
    expected = (
        "def new_function():\n    pass\n"
        "def hello_world():\n    pass\n\n"
        "def test_function():\n    pass\n"
    )
    assert content == expected


# ============================================================================
# INDENTATION INHERITANCE
# ============================================================================


def test_insert_before_with_inherit_indent(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert_before with indentation inheritance."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    print('hello')\n    return None\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_before",
        content="print('before hello')",
        pattern="    print\\('hello'\\)",
        inherit_indent=True,
    )

    assert success
    content = test_file.read_text()
    expected = "def hello():\n    print('before hello')\n    print('hello')\n    return None\n"
    assert content == expected


def test_insert_after_with_inherit_indent(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert_after with indentation inheritance."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    print('hello')\n    return None\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_after",
        content="print('after hello')",
        pattern="    print\\('hello'\\)",
        inherit_indent=True,
    )

    assert success
    content = test_file.read_text()
    expected = "def hello():\n    print('hello')\n    print('after hello')\n    return None\n"
    assert content == expected


def test_insert_before_without_inherit_indent(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert_before without indentation inheritance."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    print('hello')\n    return None\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_before",
        content="print('no indent')",
        pattern="    print\\('hello'\\)",
        inherit_indent=False,
    )

    assert success
    content = test_file.read_text()
    expected = "def hello():\nprint('no indent')\n    print('hello')\n    return None\n"
    assert content == expected


# ============================================================================
# MULTILINE CONTENT
# ============================================================================


def test_insert_operations_with_multiline_content(
    executor_direct: ActionExecutor, tmp_path
) -> None:
    """Test insert operations with multi-line content."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    pass\n\ndef world():\n    pass\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_before",
        content="def helper():\n    # This is a helper function\n    return True\n",
        pattern="def world\\(\\):",
        inherit_indent=False,
    )

    assert success
    content = test_file.read_text()
    assert "def helper():\n    # This is a helper function\n    return True\n" in content


# ============================================================================
# ERROR CASES
# ============================================================================


def test_edit_file_insert_requires_pattern(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that insert operations require a pattern."""
    test_file = Path(temp_dir) / "edit_test.txt"
    test_file.write_text("Line 1\nLine 2\nLine 3\n")

    success, message, content = executor.execute(
        "edit_file",
        {
            "path": str(test_file),
            "operation": "insert_before",
            "content": "Test content",
            "pattern": "",
        },
    )

    assert success is False
    assert "Pattern is required for insert_before operation" in message


def test_insert_before_ambiguous_pattern_fails(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert_before fails when pattern is ambiguous (matches multiple times)."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    pass\n\ndef hello():\n    pass\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_before",
        content="def new_function():\n    pass\n",
        pattern="def hello():",  # Exact string match (will match twice)
    )

    assert not success
    assert "found 2 times" in message
    content = test_file.read_text()
    assert content == "def hello():\n    pass\n\ndef hello():\n    pass\n"


def test_insert_after_ambiguous_pattern_fails(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert_after fails when pattern is ambiguous (matches multiple times)."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    pass\n\ndef hello():\n    pass\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_after",
        content="def new_function():\n    pass\n",
        pattern="def hello():",  # Exact string match (will match twice)
    )

    assert not success
    assert "found 2 times" in message
    content = test_file.read_text()
    assert content == "def hello():\n    pass\n\ndef hello():\n    pass\n"


# ============================================================================
# EOL STYLE PRESERVATION
# ============================================================================


def test_insert_operations_consistent_eol_style(executor_direct: ActionExecutor, tmp_path) -> None:
    """Test insert operations maintain consistent EOL style."""
    test_file = tmp_path / "test.py"
    test_file.write_text("def hello():\n    pass\n\ndef world():\n    pass\n")

    success, message, result = edit_file(
        str(test_file),
        "insert_before",
        content="def new_function():\n    pass\n",
        pattern="def world\\(\\):",
    )

    assert success
    content = test_file.read_text()
    assert "\n" in content
    assert "\r\n" not in content
    assert content.count("\n") == content.count("\n") + content.count("\r\n")
