"""Tests for the read_lines tool."""

from src.clippy.tools.read_lines import parse_line_range


class TestParseLineRange:
    """Test the parse_line_range function."""

    def test_basic_range(self):
        """Test basic range parsing."""
        assert parse_line_range("10-20", 100, "top") == (True, "", 10, 20)
        assert parse_line_range("5-15", 50, "top") == (True, "", 5, 15)

    def test_single_line(self):
        """Test single line specification."""
        assert parse_line_range("15", 100, "top") == (True, "", 15, 15)
        assert parse_line_range("1", 10, "top") == (True, "", 1, 1)

    def test_open_ranges(self):
        """Test open-ended ranges."""
        assert parse_line_range("10:", 100, "top") == (True, "", 10, 100)
        assert parse_line_range(":", 100, "top") == (True, "", 1, 100)

    def test_colon_syntax(self):
        """Test colon syntax for ranges."""
        assert parse_line_range("10:20", 100, "auto") == (True, "", 10, 20)
        assert parse_line_range("10:", 100, "auto") == (True, "", 10, 100)

    def test_offset_syntax(self):
        """Test offset syntax like '10+5'."""
        assert parse_line_range("10+5", 100, "top") == (True, "", 10, 15)
        assert parse_line_range("1+9", 100, "top") == (True, "", 1, 10)

    def test_bottom_numbering(self):
        """Test bottom-relative numbering."""
        assert parse_line_range("-10", 100, "bottom") == (True, "", 91, 100)
        assert parse_line_range("-1", 50, "bottom") == (True, "", 50, 50)
        assert parse_line_range("-20:", 100, "bottom") == (True, "", 1, 100)
        assert parse_line_range("-10-20", 100, "bottom") == (True, "", 81, 91)

    def test_auto_detect_bottom_numbering(self):
        """Test auto-detection of bottom numbering."""
        assert parse_line_range("-10", 100, "auto") == (True, "", 91, 100)
        assert parse_line_range("-5:", 100, "auto") == (True, "", 1, 100)

    def test_boundary_clamping(self):
        """Test that ranges are clamped to file boundaries."""
        # Out of bounds should fail in most cases
        assert parse_line_range("-10", 5, "bottom")[0] is False  # Too many lines from bottom
        assert parse_line_range("100-200", 100, "top")[0] is False  # Should fail - outside bounds
        assert parse_line_range("0-10", 100, "top")[0] is False  # 0 is out of bounds
        assert parse_line_range("50-30", 100, "top") == (True, "", 30, 50)  # Reversed gets fixed

    def test_invalid_ranges(self):
        """Test handling of invalid range specifications."""
        # Invalid specifications default to full file
        assert parse_line_range("invalid", 100, "top") == (True, "", 1, 100)
        assert parse_line_range("abc-def", 100, "top") == (True, "", 1, 100)
        assert parse_line_range("", 100, "top") == (True, "", 1, 100)
