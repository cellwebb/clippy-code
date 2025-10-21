"""Test regex operations for edit_file tool."""

import os
import re
import tempfile

from clippy.tools.edit_file import _parse_regex_flags, edit_file


class TestEditFileRegexOperations:
    """Test regex operations in edit_file tool."""

    def test_regex_replace_basic(self):
        """Test basic regex replacement on a single line."""
        content = """Hello world"""
        expected = """Hi world
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern="Hello", content="Hi"
            )
            assert success
            assert "Successfully performed replace operation" in message

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_capture_groups(self):
        """Test regex replacement with capture groups on a single line."""
        content = """name: John"""
        expected = """User John (active)
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="replace",
                pattern=r"name: (\w+)",
                content=r"User \1 (active)",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_ignorecase_flag(self):
        """Test regex replacement with IGNORECASE flag on a single line."""
        content = """HELLO World"""
        expected = """Hi World
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="replace",
                pattern="hello",
                content="Hi",
                regex_flags=["IGNORECASE"],
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_no_matches(self):
        """Test regex replacement when pattern matches no lines."""
        content = """Hello world
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern="goodbye", content="Hi"
            )
            assert success is False
            assert "not found in file" in message

            # Verify the content is unchanged
            with open(temp_path) as f:
                actual = f.read()
            assert actual == content
        finally:
            os.unlink(temp_path)

    def test_regex_replace_invalid_pattern(self):
        """Test regex replacement with invalid pattern."""
        content = """Hello world
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern="[unclosed", content="Hi"
            )
            assert not success
            # Invalid regex patterns result in "not found" message
            assert "not found in file" in message
        finally:
            os.unlink(temp_path)

    def test_regex_replace_missing_pattern(self):
        """Test regex_replace with missing regex_pattern."""
        content = """Hello world
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(path=temp_path, operation="replace", content="Hi")
            assert not success
            assert "Pattern is required for replace operation" in message
        finally:
            os.unlink(temp_path)

    def test_regex_replace_preserves_line_endings(self):
        """Test that regex replacement preserves original line endings."""
        content = "Hello world\r\n"
        expected = "Hi world\r\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern="Hello", content="Hi"
            )
            assert success

            # Verify the content
            with open(temp_path, "rb") as f:
                actual = f.read()
            assert actual == expected.encode()
        finally:
            os.unlink(temp_path)

    def test_parse_regex_flags_basic(self):
        """Test _parse_regex_flags helper function."""
        flags = _parse_regex_flags(["IGNORECASE", "MULTILINE"])
        assert flags == re.IGNORECASE | re.MULTILINE

    def test_parse_regex_flags_empty(self):
        """Test _parse_regex_flags with empty list."""
        flags = _parse_regex_flags([])
        assert flags == 0

    def test_parse_regex_flags_invalid_flag(self):
        """Test _parse_regex_flags with invalid flag."""
        flags = _parse_regex_flags(["INVALID_FLAG", "IGNORECASE"])
        # Should only include valid flags
        assert flags == re.IGNORECASE

    def test_parse_regex_flags_case_insensitive(self):
        """Test _parse_regex_flags is case insensitive."""
        flags1 = _parse_regex_flags(["IGNORECASE", "MULTILINE"])
        flags2 = _parse_regex_flags(["ignorecase", "multiline"])
        assert flags1 == flags2

    def test_regex_replace_with_word_boundary(self):
        """Test regex replacement with word boundary on a single line."""
        content = """The dog is happy
"""
        expected = """The cat is happy
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern=r"\bdog\b", content="cat"
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_substitution(self):
        """Test regex replacement with backslash substitution on a single line."""
        content = """url = "http://example.com"
"""
        expected = """url = "///example.com"
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern=r"https?://", content="///"
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_empty_replacement(self):
        """Test regex replacement with empty replacement (deletion within line)."""
        content = """Hello world"""
        expected = """world
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern="Hello ", content=""
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_groups_in_replacement(self):
        """Test regex replacement using numbered groups in replacement."""
        content = """first, last"""
        expected = """Swap: last, first
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="replace",
                pattern=r"(\w+), (\w+)",
                content="Swap: \\2, \\1",
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_multiline_pattern(self):
        """Test regex replacement within a single line with DOTALL flag."""
        content = """START block END block
"""
        expected = """REPLACED block
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="replace",
                pattern="START.*END",
                content="REPLACED",
                regex_flags=["DOTALL"],
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_multiple_flags(self):
        """Test regex replacement with multiple flags on a single line."""
        content = """Hello WORLD
"""
        expected = """Hi World
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="replace",
                pattern="hello.*world",
                content="Hi World",
                regex_flags=["IGNORECASE", "DOTALL"],
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_no_changes_message(self):
        """Test regex replacement when pattern matches no lines returns appropriate message."""
        content = """Hello world
"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="replace", pattern="goodbye", content="Hi"
            )
            # Pattern not found should fail
            assert success is False
            assert "not found in file" in message
        finally:
            os.unlink(temp_path)
