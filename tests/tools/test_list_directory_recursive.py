"""Tests for the list_directory tool with recursive mode and .gitignore handling."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from clippy.executor import ActionExecutor


@pytest.fixture
def temp_dir_with_gitignore() -> Generator[str, None, None]:
    """Create a temporary directory with a .gitignore file for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create .gitignore file
        gitignore_content = """
# Ignore virtual environments
.venv/
venv/

# Ignore git directories
.git/

# Ignore node modules
node_modules/

# Ignore specific directories
__pycache__/

# Ignore specific files
*.log
*.tmp
"""
        gitignore_path = Path(tmpdir) / ".gitignore"
        gitignore_path.write_text(gitignore_content.strip())

        # Create some test files and directories
        (Path(tmpdir) / "file1.txt").touch()
        (Path(tmpdir) / "file2.log").touch()  # This should be ignored
        (Path(tmpdir) / "file3.tmp").touch()  # This should be ignored

        # Create directories that should be ignored
        venv_dir = Path(tmpdir) / ".venv"
        venv_dir.mkdir()
        (venv_dir / "pyvenv.cfg").touch()
        (venv_dir / "bin").mkdir()
        (venv_dir / "bin" / "python").touch()

        git_dir = Path(tmpdir) / ".git"
        git_dir.mkdir()
        (git_dir / "config").touch()
        (git_dir / "HEAD").touch()

        node_modules_dir = Path(tmpdir) / "node_modules"
        node_modules_dir.mkdir()
        (node_modules_dir / "package.json").touch()

        # Create a directory that should NOT be ignored
        subdir = Path(tmpdir) / "subdir"
        subdir.mkdir()
        (subdir / "subfile.txt").touch()

        # Create nested directory with pycache
        nested_dir = Path(tmpdir) / "nested"
        nested_dir.mkdir()
        pycache_dir = nested_dir / "__pycache__"
        pycache_dir.mkdir()
        (pycache_dir / "module.cpython-39.pyc").touch()
        (nested_dir / "normal_file.py").touch()

        yield tmpdir


def test_list_directory_recursive_with_gitignore(
    executor: ActionExecutor, temp_dir_with_gitignore: str
) -> None:
    """Test recursive listing with .gitignore filtering."""
    # List the directory recursively
    success, message, content = executor.execute(
        "list_directory", {"path": temp_dir_with_gitignore, "recursive": True}
    )

    assert success is True
    assert "Successfully listed" in message

    # Convert content to lines for easier checking
    lines = content.split("\n")

    # Should include normal files and directories
    assert "file1.txt" in lines
    assert "subdir/" in lines
    assert "subdir/subfile.txt" in lines
    assert "nested/" in lines
    assert "nested/normal_file.py" in lines

    # Should NOT include ignored directories in the normal listing
    assert ".git/" not in lines
    assert ".venv/" not in lines
    assert "node_modules/" not in lines
    assert "__pycache__/" not in lines

    # Should include skip notes for ignored directories
    assert "[skipped .git/ due to .gitignore]" in lines
    assert "[skipped .venv/ due to .gitignore]" in lines
    assert "[skipped node_modules/ due to .gitignore]" in lines
    assert "[skipped nested/__pycache__/ due to .gitignore]" in lines

    # Should NOT include ignored files
    assert "file2.log" not in lines
    assert "file3.tmp" not in lines

    # Should NOT include contents of ignored directories
    assert ".git/config" not in lines
    assert ".git/HEAD" not in lines
    assert ".venv/pyvenv.cfg" not in lines
    assert ".venv/bin/python" not in lines
    assert "node_modules/package.json" not in lines
    assert "nested/__pycache__/module.cpython-39.pyc" not in lines


def test_list_directory_non_recursive(
    executor: ActionExecutor, temp_dir_with_gitignore: str
) -> None:
    """Test non-recursive listing still works as expected."""
    # List the directory non-recursively
    success, message, content = executor.execute(
        "list_directory", {"path": temp_dir_with_gitignore, "recursive": False}
    )

    assert success is True
    assert "Successfully listed" in message

    # Convert content to lines for easier checking
    lines = content.split("\n")

    # Should include top-level items
    assert "file1.txt" in lines
    assert "file2.log" in lines  # Non-recursive mode should show all files
    assert "file3.tmp" in lines
    assert ".venv/" in lines
    assert ".git/" in lines
    assert "node_modules/" in lines
    assert "subdir/" in lines
    assert "nested/" in lines


def test_list_directory_with_special_note(
    executor: ActionExecutor, temp_dir_with_gitignore: str
) -> None:
    """Test that ignored directories show a special note in recursive mode."""
    # List the directory recursively
    success, message, content = executor.execute(
        "list_directory", {"path": temp_dir_with_gitignore, "recursive": True}
    )

    assert success is True

    # Check that the content includes notes about skipped directories
    assert "[skipped .git/ due to .gitignore]" in content
    assert "[skipped .venv/ due to .gitignore]" in content
    assert "[skipped node_modules/ due to .gitignore]" in content
