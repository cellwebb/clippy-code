"""Test dynamic MCP command completion based on server availability."""

from unittest.mock import Mock

from prompt_toolkit.document import Document

from clippy.cli.completion import ClippyCommandCompleter


def test_mcp_command_completion_no_manager():
    """Test that /mcp command doesn't appear when agent has no MCP manager."""
    agent = Mock()
    agent.mcp_manager = None

    completer = ClippyCommandCompleter(agent)

    # Check that 'mcp' is not in base commands
    assert "mcp" not in completer.base_commands

    # Check actual completions
    doc = Document("/m")
    completions = completer.get_completions(doc, None)
    mcp_completions = [c for c in completions if "mcp" in str(c.display)]

    assert len(mcp_completions) == 0


def test_mcp_command_completion_no_servers():
    """Test that /mcp command doesn't appear when MCP manager exists but has no servers."""
    agent = Mock()
    agent.mcp_manager = Mock()
    agent.mcp_manager.list_servers.return_value = []

    completer = ClippyCommandCompleter(agent)

    # Check that 'mcp' is not in base commands
    assert "mcp" not in completer.base_commands

    # Check actual completions
    doc = Document("/m")
    completions = completer.get_completions(doc, None)
    mcp_completions = [c for c in completions if "mcp" in str(c.display)]

    assert len(mcp_completions) == 0


def test_mcp_command_completion_with_servers():
    """Test that /mcp command appears when MCP manager has servers."""
    agent = Mock()
    agent.mcp_manager = Mock()
    agent.mcp_manager.list_servers.return_value = [
        {"server_id": "test-server", "connected": True, "tools_count": 5}
    ]

    completer = ClippyCommandCompleter(agent)

    # Check that 'mcp' is in base commands
    assert "mcp" in completer.base_commands
    assert completer.base_commands["mcp"]["description"] == "MCP server management"
    assert "subcommands" in completer.base_commands["mcp"]
    assert set(completer.base_commands["mcp"]["subcommands"]) == {
        "list",
        "tools",
        "refresh",
        "allow",
        "revoke",
        "enable",
        "disable",
    }

    # Check actual completions
    doc = Document("/m")
    completions = completer.get_completions(doc, None)
    mcp_completions = [c for c in completions if "mcp" in str(c.display)]

    assert len(mcp_completions) == 1
    assert "mcp" in str(mcp_completions[0].display)


def test_mcp_command_completion_manager_error():
    """Test that /mcp command doesn't appear when MCP manager raises an error."""
    agent = Mock()
    agent.mcp_manager = Mock()
    agent.mcp_manager.list_servers.side_effect = Exception("Connection error")

    completer = ClippyCommandCompleter(agent)

    # Check that 'mcp' is not in base commands
    assert "mcp" not in completer.base_commands

    # Check actual completions
    doc = Document("/m")
    completions = completer.get_completions(doc, None)
    mcp_completions = [c for c in completions if "mcp" in str(c.display)]

    assert len(mcp_completions) == 0


def test_mcp_completion_still_works_for_other_commands():
    """Test that other commands still work correctly regardless of MCP status."""
    agent = Mock()
    agent.mcp_manager = None

    completer = ClippyCommandCompleter(agent)

    # Check that other commands are still available
    assert "help" in completer.base_commands
    assert "model" in completer.base_commands
    assert "auto" in completer.base_commands
    assert "subagent" in completer.base_commands

    # Check completions for '/m' should still show model command
    doc = Document("/m")
    completions = completer.get_completions(doc, None)

    assert len(completions) > 0
    # Should include model command but not mcp
    model_completions = [c for c in completions if "model" in str(c.display)]
    mcp_completions = [c for c in completions if "mcp" in str(c.display)]

    assert len(model_completions) == 1
    assert len(mcp_completions) == 0
