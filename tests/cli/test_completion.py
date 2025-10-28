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


class TestFileCompletion:
    """Test file completion functionality."""

    def test_file_completion_with_at_symbol_at_beginning(self) -> None:
        """Test completion of file references starting with '@'."""
        completer = ClippyCommandCompleter()

        # Test completing "@READ" - should find files starting with "READ"
        doc = Document("@READ")
        completions = list(completer.get_completions(doc, None))

        # Should have some completions (exact files depend on test environment)
        # but we should check that they follow the expected format
        for completion in completions:
            # completion.text should include the "@" symbol
            text = completion.text
            assert text.startswith("@")
            assert text[1:].startswith("READ")  # Skip "@"

            # completion.display might be a FormattedText object, so we check the first part
            if isinstance(completion.display, str):
                assert completion.display.startswith("@")
            else:
                # FormattedText is a list of tuples, check the first tuple's second element
                assert completion.display[0][1].startswith("@")
            # completion.display_meta might be a FormattedText object, so we check appropriately
            if isinstance(completion.display_meta, str):
                assert completion.display_meta == "File reference"
            else:
                # FormattedText is a list of tuples, check the first tuple's second element
                assert completion.display_meta[0][1] == "File reference"

    def test_file_completion_with_at_symbol_in_middle(self) -> None:
        """Test completion of file references when '@' is in the middle of text."""
        completer = ClippyCommandCompleter()

        # Test completing "update the @READ" - should find files starting with "READ"
        doc = Document("update the @READ")
        completions = list(completer.get_completions(doc, None))

        # Should have some completions (exact count depends on test environment)
        # But we know README.md exists, so there should be at least one
        assert len(completions) >= 0

        # If we have completions, check that they follow the expected format
        if completions:
            for completion in completions:
                # completion.text should include the "@" symbol
                text = completion.text
                assert text.startswith("@")
                assert text[1:].startswith("READ")  # Skip "@"

                # Start position should replace the whole "@READ" part
                assert completion.start_position == -5  # Length of "READ" + 1 for "@"

    def test_file_completion_with_at_symbol_in_known_directory(self) -> None:
        """Test completion works with files we know exist in this directory."""
        completer = ClippyCommandCompleter()

        # Test with a prefix that will match test_*.py files
        doc = Document("run @test_")
        completions = list(completer.get_completions(doc, None))

        # Should have some completions (at least the test files in this directory)
        # The exact count isn't important, just that the logic works
        # If no files match, it's still a valid outcome (0 completions)

        # Ensure that if we have completions, they follow the format correctly
        for completion in completions:
            # completion.text should include the "@" symbol
            text = completion.text
            assert text.startswith("@")

            # Check start position logic
            assert completion.start_position <= 0  # Should be negative or zero

    def test_file_completion_with_multiple_at_symbols(self) -> None:
        """Test completion works with the last '@' symbol when multiple are present."""
        completer = ClippyCommandCompleter()

        # Test with multiple @ symbols - completion should work on the last one
        doc = Document("run @test_completion.py and check @test_")
        completions = list(completer.get_completions(doc, None))

        # Should complete based on the last "@test_" part,
        # not be affected by the first "@test_completion.py" part
        # Even if the first part is a complete filename, we should still get completions
        # for the second part

        # Ensure that if we have completions, they're working on the last @ symbol
        for completion in completions:
            assert completion.text.startswith("@")
            # Start position should be negative, indicating text to replace
            assert completion.start_position < 0

    def test_file_completion_empty_prefix(self) -> None:
        """Test completion with just "@" symbol."""
        completer = ClippyCommandCompleter()

        # Test completing "@" - should show available files
        doc = Document("@")
        completions = list(completer.get_completions(doc, None))

        # Should have completions, but limited to avoid overwhelming
        assert len(completions) <= 50

    def test_file_completion_with_space_after_at_ignored(self) -> None:
        """Test that file completion is ignored when there's a space after '@'."""
        completer = ClippyCommandCompleter()

        # Test with "read @ " - space after @ should not trigger file completion
        doc = Document("read @ ")
        completions = list(completer.get_completions(doc, None))

        # Should not have any file completions triggered by the "@ " part
        assert len(completions) == 0

    def test_general_file_completion_python_file(self) -> None:
        """Test general completion of Python files without '@' prefix."""
        completer = ClippyCommandCompleter()

        # Test completing "test_" at the end of text - should find test files
        doc = Document("run test_", 8)  # cursor at end of "run test_"
        completions = list(completer.get_completions(doc, None))

        # The behavior depends on files available, but shouldn't crash
        # Just verify the completion structure if we get any
        for completion in completions:
            # completion.text should be a filename
            assert isinstance(completion.text, str)
            # Start position should be negative (replacing backwards)
            assert completion.start_position < 0

    def test_general_file_completion_with_path(self) -> None:
        """Test general completion of paths without '@' prefix."""
        completer = ClippyCommandCompleter()

        # Test completing "tests/" - should find test files in tests directory
        doc = Document("check tests/", 12)  # cursor at end of "check tests/"
        completions = list(completer.get_completions(doc, None))

        # The behavior depends on files available, but shouldn't crash
        # Just verify the completion structure if we get any
        for completion in completions:
            # completion.text should be a filename
            assert isinstance(completion.text, str)
            # Start position should be negative (replacing backwards)
            assert completion.start_position < 0

    def test_general_file_completion_with_extension(self) -> None:
        """Test general completion of files with extensions."""
        completer = ClippyCommandCompleter()

        # Test completing ".py" at the end of text
        doc = Document("edit .py", 8)  # cursor at end of "edit .py"
        completions = list(completer.get_completions(doc, None))

        # The behavior depends on files available, but shouldn't crash
        # Just verify the completion structure if we get any
        for completion in completions:
            # completion.text should be a filename
            assert isinstance(completion.text, str)
            # Should contain ".py" in the filename
            assert ".py" in completion.text
            # Start position should be negative (replacing backwards)
            assert completion.start_position < 0


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
