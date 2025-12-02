"""Tests for multi-tool execution sequences."""

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest
from rich.console import Console

from clippy.agent.loop import run_agent_loop
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock LLM provider."""
    provider = MagicMock()
    return provider


@pytest.fixture
def permission_manager() -> PermissionManager:
    """Create a permission manager."""
    return PermissionManager(PermissionConfig())


@pytest.fixture
def executor(permission_manager: PermissionManager, tmp_path: Path) -> ActionExecutor:
    """Create an action executor with temp directory access."""
    import tempfile

    temp_dir = Path(tempfile.gettempdir())
    return ActionExecutor(permission_manager, allowed_write_roots=[temp_dir, tmp_path])


@pytest.fixture
def console() -> Console:
    """Create a Rich console."""
    return Console()


@pytest.fixture
def conversation_history() -> list[dict[str, Any]]:
    """Create initial conversation history."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Help me work with some files."},
    ]


class TestMultiToolSequences:
    """Tests for sequences of multiple tool executions."""

    def test_sequential_read_write_sequence(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test read followed by write in sequence."""
        # Create a source file
        source_file = tmp_path / "source.txt"
        source_file.write_text("original content", encoding="utf-8")
        dest_file = tmp_path / "dest.txt"

        responses = [
            # First: read the source file
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(source_file)}),
                        },
                    }
                ],
            },
            # Second: write to dest file
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": json.dumps(
                                {"path": str(dest_file), "content": "modified content"}
                            ),
                        },
                    }
                ],
            },
            # Final response
            {
                "role": "assistant",
                "content": "Done copying and modifying the file.",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        result = run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        assert result == "Done copying and modifying the file."
        assert dest_file.exists()
        assert dest_file.read_text() == "modified content"

        # Check conversation history has tool results
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        assert len(tool_results) == 2

    def test_multiple_reads_in_single_response(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test multiple read operations in a single response."""
        # Create test files
        file1 = tmp_path / "file1.txt"
        file2 = tmp_path / "file2.txt"
        file3 = tmp_path / "file3.txt"
        file1.write_text("content 1", encoding="utf-8")
        file2.write_text("content 2", encoding="utf-8")
        file3.write_text("content 3", encoding="utf-8")

        responses = [
            # Read all three files in one response
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(file1)}),
                        },
                    },
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(file2)}),
                        },
                    },
                    {
                        "id": "call_3",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(file3)}),
                        },
                    },
                ],
            },
            {
                "role": "assistant",
                "content": "I read all three files.",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        result = run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        assert result == "I read all three files."

        # All three tool results should be in history
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        assert len(tool_results) == 3

        # Check each tool result has the correct content
        contents = [r["content"] for r in tool_results]
        assert any("content 1" in c for c in contents)
        assert any("content 2" in c for c in contents)
        assert any("content 3" in c for c in contents)

    def test_mixed_success_and_failure_tools(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test handling of mixed success and failure in tool sequence."""
        # Create one real file, leave one missing
        existing_file = tmp_path / "exists.txt"
        existing_file.write_text("I exist!", encoding="utf-8")
        missing_file = tmp_path / "missing.txt"

        responses = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(existing_file)}),
                        },
                    },
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(missing_file)}),
                        },
                    },
                ],
            },
            {
                "role": "assistant",
                "content": "One file worked, one didn't.",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        result = run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        assert result == "One file worked, one didn't."

        # Both tool calls should have results
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        assert len(tool_results) == 2

        # One should be successful, one should be an error
        contents = [r["content"] for r in tool_results]
        assert any("I exist!" in c for c in contents)
        assert any("Error" in c or "not found" in c.lower() for c in contents)

    def test_create_directory_then_write_file(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test creating a directory then writing a file into it."""
        new_dir = tmp_path / "new_directory"
        new_file = new_dir / "new_file.txt"

        responses = [
            # Create directory
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "create_directory",
                            "arguments": json.dumps({"path": str(new_dir)}),
                        },
                    }
                ],
            },
            # Write file into the new directory
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "write_file",
                            "arguments": json.dumps(
                                {"path": str(new_file), "content": "file in new dir"}
                            ),
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "Created directory and file.",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        result = run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        assert result == "Created directory and file."
        assert new_dir.exists()
        assert new_dir.is_dir()
        assert new_file.exists()
        assert new_file.read_text() == "file in new dir"

    def test_search_then_read_workflow(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test search for files then read them workflow."""
        # Create some Python files
        (tmp_path / "module1.py").write_text("def func1(): pass", encoding="utf-8")
        (tmp_path / "module2.py").write_text("def func2(): pass", encoding="utf-8")

        responses = [
            # Search for Python files
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "search_files",
                            "arguments": json.dumps({"pattern": "*.py", "path": str(tmp_path)}),
                        },
                    }
                ],
            },
            # Read the found files
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "read_files",
                            "arguments": json.dumps(
                                {
                                    "paths": [
                                        str(tmp_path / "module1.py"),
                                        str(tmp_path / "module2.py"),
                                    ]
                                }
                            ),
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "Found and read the Python files.",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        result = run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        assert result == "Found and read the Python files."

        # Check the read_files result contains both file contents
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        read_files_result = next(
            (r for r in tool_results if "func1" in r["content"] or "func2" in r["content"]), None
        )
        assert read_files_result is not None

    def test_long_tool_chain(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test a longer chain of tool calls."""
        responses = []

        # Create 5 iterations of tool calls
        for i in range(5):
            file_path = tmp_path / f"file_{i}.txt"
            responses.append(
                {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": f"call_{i}",
                            "type": "function",
                            "function": {
                                "name": "write_file",
                                "arguments": json.dumps(
                                    {"path": str(file_path), "content": f"content {i}"}
                                ),
                            },
                        }
                    ],
                }
            )

        # Final response
        responses.append(
            {
                "role": "assistant",
                "content": "Created 5 files.",
                "finish_reason": "stop",
            }
        )

        mock_provider.create_message.side_effect = responses

        result = run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        assert result == "Created 5 files."

        # Verify all 5 files were created
        for i in range(5):
            file_path = tmp_path / f"file_{i}.txt"
            assert file_path.exists()
            assert file_path.read_text() == f"content {i}"

    def test_tool_results_have_correct_call_ids(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test that tool results are correctly associated with their call IDs."""
        file1 = tmp_path / "test1.txt"
        file2 = tmp_path / "test2.txt"
        file1.write_text("content1", encoding="utf-8")
        file2.write_text("content2", encoding="utf-8")

        responses = [
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "unique_id_alpha",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(file1)}),
                        },
                    },
                    {
                        "id": "unique_id_beta",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(file2)}),
                        },
                    },
                ],
            },
            {
                "role": "assistant",
                "content": "Done",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        # Check tool results have correct call IDs
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        call_ids = {r["tool_call_id"] for r in tool_results}

        assert "unique_id_alpha" in call_ids
        assert "unique_id_beta" in call_ids

    def test_conversation_history_order_maintained(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
        tmp_path: Path,
    ) -> None:
        """Test that conversation history maintains correct order."""
        test_file = tmp_path / "order_test.txt"
        test_file.write_text("test", encoding="utf-8")

        responses = [
            {
                "role": "assistant",
                "content": "Let me read that file.",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": json.dumps({"path": str(test_file)}),
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "Done reading.",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        run_agent_loop(
            conversation_history=conversation_history,
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )

        # Verify order: system, user, assistant (with tool_calls), tool result, assistant
        assert conversation_history[0]["role"] == "system"
        assert conversation_history[1]["role"] == "user"
        assert conversation_history[2]["role"] == "assistant"
        assert "tool_calls" in conversation_history[2]
        assert conversation_history[3]["role"] == "tool"
        assert conversation_history[4]["role"] == "assistant"
        assert conversation_history[4]["content"] == "Done reading."
