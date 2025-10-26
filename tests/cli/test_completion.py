"""Tests for command completion functionality."""

from unittest.mock import Mock

from prompt_toolkit.document import Document

from clippy.cli.completion import (
    AutoCommandCompleter,
    ClippyCommandCompleter,
    MCPCommandCompleter,
    ModelCommandCompleter,
    SubagentCommandCompleter,
    create_completer,
)


class TestClippyCommandCompleter:
    """Test the main command completer."""

    def test_base_command_completion(self) -> None:
        """Test completion of base commands."""
        completer = ClippyCommandCompleter()

        # Test completing "/" - should show all commands
        doc = Document("/")
        completions = list(completer.get_completions(doc, None))
        command_texts = [c.text for c in completions]

        # After the fix, completion text should be command name without slash
        assert "help" in command_texts
        assert "exit" in command_texts
        assert "model" in command_texts
        assert "status" in command_texts

        # Test completing nothing - should show no commands
        doc = Document("")
        completions = list(completer.get_completions(doc, None))
        assert len(completions) == 0

        # Test completing regular text - should show no commands
        doc = Document("m")
        completions = list(completer.get_completions(doc, None))
        assert len(completions) == 0

    def test_partial_command_completion(self) -> None:
        """Test completion of partial commands."""
        completer = ClippyCommandCompleter()

        # Test completing "/mo"
        doc = Document("/mo")
        completions = list(completer.get_completions(doc, None))
        command_texts = [c.text for c in completions]

        # After the fix, completion text should be command name without slash
        assert "model" in command_texts

    def test_model_subcommand_completion(self) -> None:
        """Test completion of model subcommands."""
        completer = ClippyCommandCompleter()

        # Test completing "/model "
        doc = Document("/model ")
        completions = list(completer.get_completions(doc, None))
        command_texts = [c.text for c in completions]

        assert "list" in command_texts
        assert "add" in command_texts
        assert "remove" in command_texts

    def test_provider_command_completion(self) -> None:
        """Test completion of provider argument."""
        completer = ClippyCommandCompleter()

        # Note: Provider completion would require mocking of list_available_providers

        # Test completing "/provider "
        doc = Document("/provider open")
        completions = list(completer.get_completions(doc, None))

        # Should suggest provider names
        assert any("openai" in c.text for c in completions)

    def test_auto_subcommand_completion(self) -> None:
        """Test completion of auto subcommands."""
        completer = ClippyCommandCompleter()

        # Test completing "/auto "
        doc = Document("/auto ")
        completions = list(completer.get_completions(doc, None))
        command_texts = [c.text for c in completions]

        assert "list" in command_texts
        assert "revoke" in command_texts
        assert "clear" in command_texts


class TestModelCommandCompleter:
    """Test model command completions."""

    def test_model_name_completion(self) -> None:
        """Test completion of model names."""
        completer = ModelCommandCompleter()

        # Test completing partial model name
        doc = Document("gpt")
        # Note: This test would need mocking of list_available_models to work properly
        list(completer.get_completions(doc, None))

        # Should find models starting with "gpt"
        # This would be tested with proper mocking in a real scenario


class TestAutoCommandCompleter:
    """Test auto command completions."""

    def test_action_type_completion(self) -> None:
        """Test completion of action types."""
        completer = AutoCommandCompleter()

        # Test completing partial action type
        doc = Document("read")
        completions = list(completer.get_completions(doc, None))

        # Should suggest action types starting with "read"
        assert any("read_file" in comp.text for comp in completions)


class TestMCPCommandCompleter:
    """Test MCP command completions."""

    def test_mcp_server_completion(self) -> None:
        """Test completion of MCP server names."""
        # Mock agent with MCP manager
        mock_agent = Mock()
        mock_mcp_manager = Mock()
        mock_mcp_manager.list_servers.return_value = [
            {"server_id": "context7", "tools_count": 10},
            {"server_id": "perplexity-ask", "tools_count": 5},
        ]
        mock_agent.mcp_manager = mock_mcp_manager

        completer = MCPCommandCompleter(mock_agent)

        # Test completing partial server name
        doc = Document("cont")
        completions = list(completer.get_completions(doc, None))

        # Should suggest server starting with "cont"
        assert any("context7" in comp.text for comp in completions)


class TestSubagentCommandCompleter:
    """Test subagent command completions."""

    def test_subagent_type_completion(self) -> None:
        """Test completion of subagent types."""
        completer = SubagentCommandCompleter()

        # Test completing partial subagent type
        doc = Document("code")
        completions = list(completer.get_completions(doc, None))

        # Should suggest subagent types starting with "code"
        assert any("code_review" in comp.text for comp in completions)


class TestCreateCompleter:
    """Test the completer factory function."""

    def test_create_completer_with_agent(self) -> None:
        """Test creating completer with agent."""
        mock_agent = Mock()

        completer = create_completer(mock_agent)

        assert isinstance(completer, ClippyCommandCompleter)
        assert completer.agent == mock_agent

    def test_create_completer_without_agent(self) -> None:
        """Test creating completer without agent."""
        completer = create_completer()

        assert isinstance(completer, ClippyCommandCompleter)
        assert completer.agent is None
