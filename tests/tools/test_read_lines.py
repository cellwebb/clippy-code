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
        result1 = parse_line_range("-10", 5, "bottom")
        assert result1[0] is True and result1[2:] == (1, 5)  # Returns entire file

        result2 = parse_line_range("100-200", 100, "top")
        assert result2[0] is True and result2[2:] == (100, 100)  # Line 100 is valid

        assert parse_line_range("0-10", 100, "top")[0] is True  # 0 gets clamped to 1

        result3 = parse_line_range("50-30", 100, "top")
        assert result3[0] is True and result3[2:] == (30, 50)  # Reversed gets fixed

    def test_invalid_ranges(self):
        """Test handling of invalid range specifications."""
        # Invalid specifications default to full file
        assert parse_line_range("invalid", 100, "top") == (True, "", 1, 100)
        assert parse_line_range("abc-def", 100, "top") == (True, "", 1, 100)
        assert parse_line_range("", 100, "top") == (True, "", 1, 100)
