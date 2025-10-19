"""Test block operations for edit_file tool."""

import os
import tempfile

from clippy.tools.edit_file import _find_block_bounds, edit_file


class TestEditFileBlockOperations:
    """Test block operations in edit_file tool."""

    def test_block_replace_basic(self):
        """Test basic block replacement."""
        content = """# START
def old_function():
    print("Old implementation")
    return True
# END
"""
        expected = """# START
def new_function():
    print("New implementation")
    return False
# END
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content='def new_function():\n    print("New implementation")\n    return False',
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success
            assert "Successfully performed block_replace operation" in message

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_delete_basic(self):
        """Test basic block deletion."""
        content = """Line before block
# START
def old_function():
    print("Old implementation")
    return True
# END
Line after block
"""
        expected = """Line before block
# START
# END
Line after block
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_delete",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success
            assert "Successfully performed block_delete operation" in message

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_replace_missing_start_pattern(self):
        """Test block_replace with missing start pattern."""
        content = """# END
Some content
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="New content",
                end_pattern="# END",
            )
            assert not success
            assert "Both start_pattern and end_pattern are required" in message
        finally:
            os.unlink(temp_path)

    def test_block_replace_missing_end_pattern(self):
        """Test block_replace with missing end pattern."""
        content = """# START
Some content
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="New content",
                start_pattern="# START",
            )
            assert not success
            assert "Both start_pattern and end_pattern are required" in message
        finally:
            os.unlink(temp_path)

    def test_block_replace_block_not_found(self):
        """Test block_replace when block is not found."""
        content = """# START
Some content
# OTHER END
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="New content",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert not success
            assert "Block with start_pattern '# START' and end_pattern '# END' not found" in message
        finally:
            os.unlink(temp_path)

    def test_block_delete_missing_start_pattern(self):
        """Test block_delete with missing start pattern."""
        content = """# END
Some content
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="block_delete", end_pattern="# END"
            )
            assert not success
            assert "Both start_pattern and end_pattern are required" in message
        finally:
            os.unlink(temp_path)

    def test_block_delete_block_not_found(self):
        """Test block_delete when block is not found."""
        content = """# START
Some content
# OTHER END
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_delete",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert not success
            assert "Block with start_pattern '# START' and end_pattern '# END' not found" in message
        finally:
            os.unlink(temp_path)

    def test_find_block_bounds_simple(self):
        """Test _find_block_bounds helper function."""
        lines = [
            "Line 1\n",
            "# START\n",
            "Content line 1\n",
            "Content line 2\n",
            "# END\n",
            "Line 6\n",
        ]

        bounds = _find_block_bounds(lines, "# START", "# END")
        assert bounds == (1, 4)

    def test_find_block_bounds_no_start(self):
        """Test _find_block_bounds when start pattern is missing."""
        lines = ["Line 1\n", "Content line 1\n", "# END\n", "Line 4\n"]

        bounds = _find_block_bounds(lines, "# START", "# END")
        assert bounds is None

    def test_find_block_bounds_no_end(self):
        """Test _find_block_bounds when end pattern is missing."""
        lines = ["Line 1\n", "# START\n", "Content line 1\n", "Content line 2\n", "Line 5\n"]

        bounds = _find_block_bounds(lines, "# START", "# END")
        assert bounds is None

    def test_find_block_bounds_multiple_matches(self):
        """Test _find_block_bounds with multiple potential matches."""
        lines = [
            "Line 1\n",
            "# START\n",
            "Content line 1\n",
            "# END\n",
            "# START\n",
            "Content line 2\n",
            "# END\n",
            "Line 8\n",
        ]

        bounds = _find_block_bounds(lines, "# START", "# END")
        # Should return the first matching block
        assert bounds == (1, 3)

    def test_find_block_bounds_start_appears_after_end(self):
        """Test _find_block_bounds when start pattern appears after end pattern."""
        lines = ["Line 1\n", "# END\n", "# START\n", "Content line 1\n", "# END\n", "Line 6\n"]

        bounds = _find_block_bounds(lines, "# START", "# END")
        assert bounds == (2, 4)

    def test_block_replace_empty_content(self):
        """Test block replacement with empty content (effectively deletion)."""
        content = """# START
def old_function():
    pass
# END
"""
        expected = """# START

# END
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_replace_single_line_block(self):
        """Test block replacement with single-line block."""
        content = """# START
# END"""
        expected = """# START
NEW LINE
# END"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="NEW LINE",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_replace_preserves_line_endings(self):
        """Test that block replacement preserves original line endings."""
        content = "# START\r\nContent line\r\n# END\r\n"
        expected = "# START\r\nNEW CONTENT\r\n# END\r\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="NEW CONTENT",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path, "rb") as f:
                actual = f.read()
            assert actual == expected.encode()
        finally:
            os.unlink(temp_path)

    def test_block_delete_with_single_line_between_markers(self):
        """Test block_delete when there's only a single line between markers."""
        content = """# START
single line
# END
other content"""
        expected = """# START
# END
other content"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_delete",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_replace_content_with_newlines(self):
        """Test block replacement with content that has newlines at start/end."""
        content = """# START
old content
# END"""
        expected = """# START

new content with leading/trailing newlines
# END"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="\nnew content with leading/trailing newlines\n",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_replace_adjacent_markers(self):
        """Test block_replace when markers are adjacent (empty block)."""
        content = """# START# END"""
        expected = """# STARTNEW CONTENT# END
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_replace",
                content="NEW CONTENT",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_block_delete_adjacent_markers(self):
        """Test block_delete when markers are adjacent (empty block)."""
        content = """# START# END
other content"""
        expected = """# START# END
other content"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="block_delete",
                start_pattern="# START",
                end_pattern="# END",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)
