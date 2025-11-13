"""Tests for the think tool."""

from clippy.tools.think import TOOL_SCHEMA, think


def test_think_success():
    """Test that think tool returns success with the provided thought."""
    thought = "I need to think about this problem step by step."
    success, message, result = think(thought)

    assert success is True
    assert message == "Thinking completed successfully"
    assert result == thought


def test_think_empty_thought():
    """Test that think tool works with empty thought."""
    thought = ""
    success, message, result = think(thought)

    assert success is True
    assert message == "Thinking completed successfully"
    assert result == thought


def test_think_long_thought():
    """Test that think tool works with long thoughts."""
    thought = (
        "This is a very long thought that spans multiple lines and contains detailed reasoning "
        "about the problem at hand. It should still work correctly because the think tool is "
        "designed to handle any length of thought without issues."
    )
    success, message, result = think(thought)

    assert success is True
    assert message == "Thinking completed successfully"
    assert result == thought


def test_think_tool_schema():
    """Test that the think tool has the correct schema."""
    assert TOOL_SCHEMA["type"] == "function"
    assert TOOL_SCHEMA["function"]["name"] == "think"
    assert "thought" in TOOL_SCHEMA["function"]["parameters"]["properties"]
    assert "thought" in TOOL_SCHEMA["function"]["parameters"]["required"]
    assert isinstance(
        TOOL_SCHEMA["function"]["parameters"]["properties"]["thought"]["description"],
        str,
    )
