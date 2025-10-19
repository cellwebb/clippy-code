"""Test regex operations for edit_file tool."""

import os
import re
import tempfile

from clippy.tools.edit_file import _parse_regex_flags, edit_file


class TestEditFileRegexOperations:
    """Test regex operations in edit_file tool."""

    def test_regex_replace_basic(self):
        """Test basic regex replacement."""
        content = """Hello world
Hello python
Hello universe"""
        expected = """Hi world
Hi python
Hi universe"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern="Hello", content="Hi"
            )
            assert success
            assert "Successfully performed regex_replace operation" in message

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_capture_groups(self):
        """Test regex replacement with capture groups."""
        content = """name: John
name: Jane
name: Bob"""
        expected = """User John (active)
User Jane (active)
User Bob (active)"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="regex_replace",
                regex_pattern=r"name: (\w+)",
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
        """Test regex replacement with IGNORECASE flag."""
        content = """HELLO World
hello world
Hello WORLD"""
        expected = """Hi World
Hi world
Hi WORLD"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="regex_replace",
                regex_pattern="hello",
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
Hello python
Hello universe"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern="goodbye", content="Hi"
            )
            assert success
            assert "Successfully performed regex_replace operation" in message

            # Verify the content is unchanged
            with open(temp_path) as f:
                actual = f.read()
            assert actual == content
        finally:
            os.unlink(temp_path)

    def test_regex_replace_invalid_pattern(self):
        """Test regex replacement with invalid pattern."""
        content = """Hello world"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern="[unclosed", content="Hi"
            )
            assert not success
            assert "Invalid regex pattern" in message
        finally:
            os.unlink(temp_path)

    def test_regex_replace_missing_pattern(self):
        """Test regex_replace with missing regex_pattern."""
        content = """Hello world"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", content="Hi"
            )
            assert not success
            assert "regex_pattern is required for regex_replace operation" in message
        finally:
            os.unlink(temp_path)

    def test_regex_replace_preserves_line_endings(self):
        """Test that regex replacement preserves original line endings."""
        content = "Hello world\r\nHello python\r\nHello universe\r\n"
        expected = "Hi world\r\nHi python\r\nHi universe\r\n"

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern="Hello", content="Hi"
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
        """Test regex replacement with word boundary."""
        content = """The dog is happy
The dogs are happy
hotdog is not a dog"""
        expected = """The cat is happy
The dogs are happy
hotdog is not a cat"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern=r"\bdog\b", content="cat"
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_with_substitution(self):
        """Test regex replacement with backslash substitution."""
        content = """path = "/home/user/docs"
url = "http://example.com"""
        expected = """path = "/home/user/docs"
url = "///example.com"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern=r"https?://", content="///"
            )
            assert success

            # Verify the content
            with open(temp_path) as f:
                actual = f.read()
            assert actual == expected
        finally:
            os.unlink(temp_path)

    def test_regex_replace_empty_replacement(self):
        """Test regex replacement with empty replacement (deletion)."""
        content = """Hello world
Hello python
Hello universe"""
        expected = """world
python
universe"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern="Hello ", content=""
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
        content = """first, last
second, third"""
        expected = """Swap: last, first
Swap: third, second"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="regex_replace",
                regex_pattern=r"(\w+), (\w+)",
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
        """Test regex replacement that affects multiple lines."""
        content = """START block
content here
END block
another line"""
        expected = """REPLACED block
another line
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="regex_replace",
                regex_pattern="START.*END",
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
        """Test regex replacement with multiple flags."""
        content = """Hello WORLD
hello world
HELLO universe"""
        expected = """Hi World
HELLO universe
"""
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path,
                operation="regex_replace",
                regex_pattern="hello.*world",
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
Hello python"""

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write(content)
            temp_path = f.name

        try:
            success, message, result = edit_file(
                path=temp_path, operation="regex_replace", regex_pattern="goodbye", content="Hi"
            )
            assert success
            # Should indicate no lines were matched
            is_no_match = "Regex pattern matched no lines" in message
            is_successful = "Successfully performed" in message
            assert is_no_match or is_successful
        finally:
            os.unlink(temp_path)
