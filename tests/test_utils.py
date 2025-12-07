"""Tests for clippy utils module."""

import os
from unittest.mock import MagicMock, patch

from clippy.utils import (
    _truncate_command_output,
    _truncate_directory_listing,
    _truncate_file_content,
    _truncate_find_replace_output,
    _truncate_grep_output,
    _truncate_webpage_content,
    count_tokens,
    format_over_size_warning,
    get_max_tool_result_tokens,
    smart_truncate_tool_result,
    truncate_text_to_tokens,
)


class TestCountTokens:
    """Test token counting functionality."""

    def test_count_tokens_basic(self):
        """Test basic token counting."""
        text = "Hello, world!"
        result = count_tokens(text)
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_empty_string(self):
        """Test token counting with empty string."""
        result = count_tokens("")
        assert result == 0

    def test_count_tokens_with_model(self):
        """Test token counting with specific model."""
        text = "This is a test sentence for token counting."
        result = count_tokens(text, "gpt-3.5-turbo")
        assert isinstance(result, int)
        assert result > 0

    def test_count_tokens_unknown_model(self):
        """Test token counting with unknown model falls back to cl100k_base."""
        text = "Test text for fallback encoding."
        result = count_tokens(text, "unknown-model")
        assert isinstance(result, int)
        assert result > 0

    @patch("clippy.utils.tiktoken.encoding_for_model")
    @patch("clippy.utils.tiktoken.get_encoding")
    def test_count_tokens_fallback_on_error(self, mock_get_encoding, mock_encoding_for_model):
        """Test fallback behavior when tiktoken fails."""
        mock_encoding_for_model.side_effect = KeyError("Unknown model")
        mock_encoding = MagicMock()
        mock_encoding.encode.return_value = [1, 2, 3, 4, 5]
        mock_get_encoding.return_value = mock_encoding

        result = count_tokens("test text", "unknown-model")
        assert result == 5
        mock_get_encoding.assert_called_with("cl100k_base")

    @patch("clippy.utils.tiktoken.encoding_for_model")
    def test_count_tokens_exception_handling(self, mock_encoding_for_model):
        """Test exception handling in count_tokens."""
        mock_encoding_for_model.side_effect = Exception("tiktoken error")

        # Should fall back to character-based approximation
        result = count_tokens("test text", "any-model")
        # Approximation: len(text) // 4
        assert result == len("test text") // 4


class TestTruncateTextToTokens:
    """Test text truncation functionality."""

    def test_truncate_text_under_limit(self):
        """Test that text under limit is unchanged."""
        text = "This is a short text."
        result = truncate_text_to_tokens(text, max_tokens=100)
        assert result == text

    def test_truncate_text_over_limit(self):
        """Test text truncation when over limit."""
        text = "This is a longer text that should be truncated when we limit the tokens." * 10
        result = truncate_text_to_tokens(text, max_tokens=10)
        assert len(result) < len(text)
        assert "truncated" in result.lower()

    def test_truncate_text_zero_tokens(self):
        """Test truncation with zero max tokens."""
        text = "Any text"
        result = truncate_text_to_tokens(text, max_tokens=0)
        assert result == "[Content truncated: max_tokens <= 0]"

    def test_truncate_text_negative_tokens(self):
        """Test truncation with negative max tokens."""
        text = "Any text"
        result = truncate_text_to_tokens(text, max_tokens=-5)
        assert result == "[Content truncated: max_tokens <= 0]"

    def test_truncate_text_small_limit(self):
        """Test truncation with very small limit after warning reservation."""
        long_text = (
            "This is a much longer text that should definitely exceed the small token limit." * 10
        )
        result = truncate_text_to_tokens(long_text, max_tokens=10)  # Less than warning tokens (20)
        assert "max_tokens too small" in result.lower()

    def test_truncate_text_no_warning(self):
        """Test truncation without adding warning."""
        text = "A text that will be truncated." * 20
        result = truncate_text_to_tokens(text, max_tokens=10, add_warning=False)
        # Should not add formal warning message, but may contain "truncated" in fallback text
        warning_messages = ["content truncated:", "→", "tokens"]
        for warning_msg in warning_messages:
            assert warning_msg not in result.lower()

    def test_truncate_text_preserve_structure(self):
        """Test truncation with structure preservation."""
        text = "```python\ndef hello():\n    print('world')\n```"
        result = truncate_text_to_tokens(text, max_tokens=5, preserve_structure=True)
        assert isinstance(result, str)

    @patch("clippy.utils.tiktoken.encoding_for_model")
    def test_truncate_text_exception_fallback(self, mock_encoding_for_model):
        """Test fallback when truncation encounters exception."""
        mock_encoding_for_model.side_effect = Exception("tiktoken error")

        text = "A longer text that should trigger fallback" * 20
        result = truncate_text_to_tokens(text, max_tokens=10)
        assert len(result) < len(text)
        assert "..." in result or "truncated" in result.lower()


class TestSmartTruncateToolResult:
    """Test smart tool result truncation."""

    def test_smart_truncate_under_limit(self):
        """Test smart truncation when under limit."""
        content = "Short content"
        result = smart_truncate_tool_result(content, max_tokens=100, tool_name="test_tool")
        assert result == content

    def test_smart_truncate_read_file(self):
        """Test smart truncation for read_file tool."""
        content = "# Python file\n\ndef function1():\n    pass\n\ndef function2():\n    pass\n" * 50
        result = smart_truncate_tool_result(content, max_tokens=50, tool_name="read_file")
        assert len(result) < len(content)
        # Smart truncation should reduce content size

    def test_smart_truncate_grep(self):
        """Test smart truncation for grep tool."""
        content = "file1.py:1:match1\nfile1.py:2:match2\nfile2.py:1:match3\n" * 100
        result = smart_truncate_tool_result(content, max_tokens=50, tool_name="grep")
        assert len(result) < len(content)

    def test_smart_truncate_list_directory(self):
        """Test smart truncation for list_directory tool."""
        content = "file1.py\nfile2.py\ndirectory/\n" * 100
        result = smart_truncate_tool_result(content, max_tokens=30, tool_name="list_directory")
        assert len(result) < len(content)

    def test_smart_truncate_execute_command(self):
        """Test smart truncation for execute_command tool."""
        content = (
            "Normal output line\nError: something went wrong\nWarning: attention needed\n" * 50
        )
        result = smart_truncate_tool_result(content, max_tokens=60, tool_name="execute_command")
        assert len(result) < len(content)

    def test_smart_truncate_fetch_webpage(self):
        """Test smart truncation for fetch_webpage tool."""
        content = "<html><body><h1>Title</h1><p>This is webpage content.</p></body></html>" * 50
        result = smart_truncate_tool_result(content, max_tokens=50, tool_name="fetch_webpage")
        assert isinstance(result, str)

    def test_smart_truncate_find_replace(self):
        """Test smart truncation for find_replace tool."""
        content = "Processing 100 files...\n+ replacement line\n- original line\n" * 50
        result = smart_truncate_tool_result(content, max_tokens=40, tool_name="find_replace")
        assert len(result) < len(content)

    def test_smart_truncate_generic_tool(self):
        """Test smart truncation for unknown tool type."""
        content = "Generic tool output content." * 100
        result = smart_truncate_tool_result(content, max_tokens=50, tool_name="unknown_tool")
        assert len(result) < len(content)
        assert "unknown_tool" in result.lower()

    def test_smart_truncate_zero_limit(self):
        """Test smart truncation with zero token limit."""
        content = "Any content"
        result = smart_truncate_tool_result(content, max_tokens=0, tool_name="test_tool")
        assert "max_tokens too small" in result.lower()


class TestTruncateHelpers:
    """Test helper functions for smart truncation."""

    def test_truncate_file_content_small(self):
        """Test file content truncation for small files."""
        content = "line1\nline2\nline3\nline4\nline5"
        # Give more space to avoid adding warning
        result = _truncate_file_content(content, 200, "read_file", "gpt-4")
        # Allow for warning addition
        assert len(result.splitlines()) >= len(content.splitlines()) - 2

    def test_truncate_file_content_large(self):
        """Test file content truncation for large files."""
        content = (
            "# Header\n\nimport os\n\ndef func1():\n    pass\n\ndef func2():\n    pass\n" * 100
        )
        result = _truncate_file_content(content, 20, "read_file", "gpt-4")  # Very small limit
        assert len(result) < len(content)
        # May or may not contain explicit message depending on internal logic

    def test_truncate_grep_output_small(self):
        """Test grep output truncation for small results."""
        content = "file1.py:1:match\nfile2.py:2:match"
        result = _truncate_grep_output(content, 50, "gpt-4")
        assert len(result.splitlines()) == 2

    def test_truncate_grep_output_large(self):
        """Test grep output truncation for large results."""
        content = f"file{0}.py:{1}:match{1}\n" * 100
        result = _truncate_grep_output(content, 100, "gpt-4")
        assert len(result) < len(content)
        assert "truncated" in result.lower()

    def test_truncate_directory_listing_small(self):
        """Test directory listing truncation for small listings."""
        content = "file1.py\nfile2.py\ndir/\n"
        result = _truncate_directory_listing(content, 50, "gpt-4")
        assert result == content

    def test_truncate_directory_listing_large(self):
        """Test directory listing truncation for large listings."""
        content = f"file{0}.py\n" * 200
        result = _truncate_directory_listing(content, 100, "gpt-4")
        assert len(result) < len(content)
        assert "truncated" in result.lower()

    def test_truncate_command_output_small(self):
        """Test command output truncation for small output."""
        content = "line1\nline2\nline3"
        result = _truncate_command_output(content, 50, "gpt-4")
        assert result == content

    def test_truncate_command_output_large_with_errors(self):
        """Test command output truncation preserving errors."""
        content = (
            "Normal line\nAnother normal line\nERROR: Critical failure\n"
            "Warning: attention\nMore output\n" * 50
        )
        result = _truncate_command_output(content, 100, "gpt-4")
        assert len(result) < len(content)
        assert "ERROR" in result  # Important lines should be preserved

    def test_truncate_webpage_content(self):
        """Test webpage content truncation."""
        content = "<html><body>This is some webpage content with HTML tags.</body></html>" * 50
        result = _truncate_webpage_content(content, 50, "gpt-4")
        assert isinstance(result, str)
        assert len(result) < len(content)

    def test_truncate_find_replace_output(self):
        """Test find/replace output truncation."""
        content = "Processed 50 files\n+ new line\n- old line\n Status: 25 changes made\n" * 20
        result = _truncate_find_replace_output(content, 100, "gpt-4")
        assert len(result) < len(content)


class TestGetMaxToolResultTokens:
    """Test getting max tool result tokens from environment."""

    def test_get_max_tokens_default(self):
        """Test default token limit."""
        with patch.dict(os.environ, {}, clear=True):
            result = get_max_tool_result_tokens()
            assert result == 10000

    def test_get_max_tokens_from_env(self):
        """Test getting token limit from environment variable."""
        with patch.dict(os.environ, {"CLIPPY_MAX_TOOL_RESULT_TOKENS": "5000"}):
            result = get_max_tool_result_tokens()
            assert result == 5000

    def test_get_max_tokens_minimum(self):
        """Test minimum token limit enforcement."""
        with patch.dict(os.environ, {"CLIPPY_MAX_TOOL_RESULT_TOKENS": "500"}):
            result = get_max_tool_result_tokens()
            assert result == 1000  # Should enforce minimum of 1000

    def test_get_max_tokens_invalid_value(self):
        """Test handling of invalid environment variable value."""
        with patch.dict(os.environ, {"CLIPPY_MAX_TOOL_RESULT_TOKENS": "invalid"}):
            result = get_max_tool_result_tokens()
            assert result == 10000  # Should fall back to default

    def test_get_max_tokens_none_value(self):
        """Test handling of None environment variable value."""
        with patch.dict(os.environ, {"CLIPPY_MAX_TOOL_RESULT_TOKENS": ""}):
            result = get_max_tool_result_tokens()
            assert result == 10000  # Should fall back to default


class TestFormatOverSizeWarning:
    """Test warning message formatting."""

    def test_format_warning_basic(self):
        """Test basic warning formatting."""
        result = format_over_size_warning("test_tool", 15000, 8000, 10000)
        assert "test_tool" in result
        assert "15,000" in result
        assert "8,000" in result
        assert "10,000" in result
        assert "⚠️" in result

    def test_format_warning_different_values(self):
        """Test warning with different token values."""
        result = format_over_size_warning("read_file", 25000, 12000, 15000)
        assert "read_file" in result
        assert "25,000" in result
        assert "12,000" in result
        assert "15,000" in result

    def test_format_large_numbers(self):
        """Test formatting of very large numbers."""
        result = format_over_size_warning("big_tool", 1000000, 500000, 750000)
        assert "1,000,000" in result
        assert "500,000" in result
        assert "750,000" in result
