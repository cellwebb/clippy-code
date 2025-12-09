"""Tests for agent execution loop."""

import json
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from clippy.agent.core import InterruptedExceptionError
from clippy.agent.loop import AgentLoopConfig, run_agent_loop
from clippy.executor import ActionExecutor
from clippy.permissions import PermissionConfig, PermissionManager
from clippy.providers import LLMProvider


@pytest.fixture
def mock_provider() -> MagicMock:
    """Create a mock LLM provider."""
    provider = MagicMock(spec=LLMProvider)
    return provider


@pytest.fixture
def permission_manager() -> PermissionManager:
    """Create a permission manager."""
    return PermissionManager(PermissionConfig())


@pytest.fixture
def executor(permission_manager: PermissionManager) -> ActionExecutor:
    """Create an action executor."""
    return ActionExecutor(permission_manager)


@pytest.fixture
def console() -> Console:
    """Create a Rich console."""
    return Console()


@pytest.fixture
def conversation_history() -> list[dict[str, Any]]:
    """Create initial conversation history."""
    return [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"},
    ]


class TestRunAgentLoop:
    """Tests for run_agent_loop function."""

    def test_returns_content_without_tool_calls(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that loop returns immediately when response has no tool calls."""
        # Mock provider to return text response without tool calls
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Hello! How can I help you today?",
            "finish_reason": "stop",
        }

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == "Hello! How can I help you today?"
        # Should have added assistant message to history
        assert len(conversation_history) == 3
        assert conversation_history[-1]["role"] == "assistant"

    def test_executes_tool_calls(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that tool calls are executed properly."""
        # First response: tool call
        first_response = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": json.dumps({"file_path": "/test.txt"}),
                    },
                }
            ],
        }

        # Second response: final answer
        second_response = {
            "role": "assistant",
            "content": "Here's the file content!",
            "finish_reason": "stop",
        }

        mock_provider.create_message.side_effect = [first_response, second_response]

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,  # Auto-approve to avoid blocking
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == "Here's the file content!"
        # Provider should be called twice
        assert mock_provider.create_message.call_count == 2

    def test_handles_multiple_iterations(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that loop handles multiple tool execution iterations."""
        # Create multiple responses with tool calls, then final response
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
                            "arguments": '{"file_path": "test1.txt"}',
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_2",
                        "type": "function",
                        "function": {
                            "name": "read_file",
                            "arguments": '{"file_path": "test2.txt"}',
                        },
                    }
                ],
            },
            {
                "role": "assistant",
                "content": "Done!",
                "finish_reason": "stop",
            },
        ]

        mock_provider.create_message.side_effect = responses

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == "Done!"
        assert mock_provider.create_message.call_count == 3

    def test_stops_at_max_iterations(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that loop stops at maximum iterations."""
        # Always return tool calls (infinite loop scenario)
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"file_path": "test.txt"}'},
                }
            ],
        }

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
            max_iterations=3,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert "reached max iterations" in result.lower()
        # Should stop at the configured cap
        assert mock_provider.create_message.call_count == 3

    def test_handles_api_error(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that API errors are handled properly."""
        mock_provider.create_message.side_effect = Exception("API Error")

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        with pytest.raises(Exception, match="API Error"):
            run_agent_loop(
                conversation_history=conversation_history,
                config=config,
            )

    def test_handles_json_decode_error_in_tool_args(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test handling of invalid JSON in tool arguments."""
        # First response: tool call with invalid JSON
        first_response = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": "not valid json {{{",  # Invalid JSON
                    },
                }
            ],
        }

        # Second response: normal completion
        second_response = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        mock_provider.create_message.side_effect = [first_response, second_response]

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == "Done"
        # Should have added error result to conversation
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        assert len(tool_results) == 1
        assert "Error parsing" in tool_results[0]["content"]

    def test_respects_interrupted_flag(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that loop respects interrupted flag."""
        # Set check_interrupted to return True
        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: True,  # Always interrupted
        )
        with pytest.raises(InterruptedExceptionError):
            run_agent_loop(
                conversation_history=conversation_history,
                config=config,
            )

    def test_adds_assistant_message_to_history(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that assistant messages are added to conversation history."""
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Test response",
            "finish_reason": "stop",
        }

        initial_length = len(conversation_history)

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        # Should have added one assistant message
        assert len(conversation_history) == initial_length + 1
        assert conversation_history[-1]["role"] == "assistant"
        assert conversation_history[-1]["content"] == "Test response"

    def test_handles_tool_calls_in_message(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that tool_calls are added to assistant message."""
        tool_calls = [
            {
                "id": "call_1",
                "type": "function",
                "function": {"name": "read_file", "arguments": '{"file_path": "test.txt"}'},
            }
        ]

        first_response = {
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls,
        }

        second_response = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        mock_provider.create_message.side_effect = [first_response, second_response]

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        # Find assistant message with tool calls
        assistant_msgs = [msg for msg in conversation_history if msg.get("role") == "assistant"]
        tool_call_msg = next(msg for msg in assistant_msgs if "tool_calls" in msg)

        assert tool_call_msg["tool_calls"] == tool_calls

    def test_uses_approval_callback(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that approval callback is used when provided."""
        callback_called = {"called": False}

        def mock_callback(tool_name: str, tool_input: dict[str, Any], diff: str | None) -> bool:
            callback_called["called"] = True
            return True

        first_response = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "write_file", "arguments": '{"file_path": "test.txt"}'},
                }
            ],
        }

        second_response = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        mock_provider.create_message.side_effect = [first_response, second_response]

        # write_file requires approval by default
        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=mock_callback,
            check_interrupted=lambda: False,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert callback_called["called"] is True

    def test_stops_on_finish_reason_stop(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that loop stops when finish_reason is 'stop'."""
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Final answer",
            "finish_reason": "stop",
            "tool_calls": [],  # Empty tool calls but finish_reason is stop
        }

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == "Final answer"
        # Should only call provider once
        assert mock_provider.create_message.call_count == 1

    def test_handles_multiple_tool_calls_in_one_response(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test handling multiple tool calls in a single response."""
        first_response = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"file_path": "test1.txt"}'},
                },
                {
                    "id": "call_2",
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"file_path": "test2.txt"}'},
                },
            ],
        }

        second_response = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        mock_provider.create_message.side_effect = [first_response, second_response]

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        # Should have two tool result messages
        tool_results = [msg for msg in conversation_history if msg.get("role") == "tool"]
        assert len(tool_results) == 2

    @patch("clippy.agent.loop.tool_catalog")
    def test_gets_tools_from_catalog(
        self,
        mock_catalog: MagicMock,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that tools are fetched from catalog on each iteration."""
        mock_catalog.get_all_tools.return_value = []

        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        # Catalog should be called at least once
        assert mock_catalog.get_all_tools.called

    def test_returns_empty_string_for_none_content(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that None content is converted to empty string."""
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": None,  # No content
            "finish_reason": "stop",
        }

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == ""

    def test_stops_at_max_duration(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that loop stops when max_duration is exceeded."""
        import time

        # Mock time.time to simulate elapsed time
        start_time = time.time()

        # Create responses that keep returning tool calls
        def delayed_response(*args, **kwargs):
            return {
                "role": "assistant",
                "content": "",
                "tool_calls": [
                    {
                        "id": "call_1",
                        "type": "function",
                        "function": {"name": "read_file", "arguments": '{"file_path": "test.txt"}'},
                    }
                ],
            }

        mock_provider.create_message.side_effect = delayed_response

        # Use a very short max_duration that will be exceeded immediately
        # since we patch time.time
        call_count = [0]

        def mock_time():
            call_count[0] += 1
            if call_count[0] <= 2:
                return start_time
            # After 2 calls, return a time way past duration limit
            return start_time + 1000

        with patch("time.time", mock_time):
            config = AgentLoopConfig(
                provider=mock_provider,
                model="gpt-4",
                permission_manager=permission_manager,
                executor=executor,
                console=console,
                auto_approve_all=True,
                approval_callback=None,
                check_interrupted=lambda: False,
                max_duration=0.001,  # Very short duration
            )
            result = run_agent_loop(
                conversation_history=conversation_history,
                config=config,
            )

        assert "reached max duration" in result.lower() or "stopped" in result.lower()

    def test_filters_allowed_tools(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that allowed_tools filters the tools sent to the provider."""
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        with patch("clippy.agent.loop.tool_catalog") as mock_catalog:
            # Create mock tools
            mock_catalog.get_all_tools.return_value = [
                {"function": {"name": "read_file", "parameters": {}}},
                {"function": {"name": "write_file", "parameters": {}}},
                {"function": {"name": "delete_file", "parameters": {}}},
            ]

            config = AgentLoopConfig(
                provider=mock_provider,
                model="gpt-4",
                permission_manager=permission_manager,
                executor=executor,
                console=console,
                auto_approve_all=False,
                approval_callback=None,
                check_interrupted=lambda: False,
                allowed_tools=["read_file"],  # Only allow read_file
            )
            run_agent_loop(
                conversation_history=conversation_history,
                config=config,
            )

            # Check that provider received filtered tools
            call_args = mock_provider.create_message.call_args
            tools_sent = call_args.kwargs.get("tools", [])
            tool_names = [t["function"]["name"] for t in tools_sent]

            assert tool_names == ["read_file"]
            assert "write_file" not in tool_names
            assert "delete_file" not in tool_names

    def test_preserves_reasoning_content(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that reasoning_content from reasoner models is preserved."""
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Final answer",
            "reasoning_content": "Let me think step by step...",
            "finish_reason": "stop",
        }

        config = AgentLoopConfig(
            provider=mock_provider,
            model="o1",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        # Check that reasoning_content was preserved in history
        assistant_msg = conversation_history[-1]
        assert assistant_msg["role"] == "assistant"
        assert assistant_msg.get("reasoning_content") == "Let me think step by step..."

    def test_auto_saves_conversation_with_parent_agent(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that conversation is auto-saved when parent_agent is provided."""
        mock_provider.create_message.return_value = {
            "role": "assistant",
            "content": "Done",
            "finish_reason": "stop",
        }

        # Create mock parent agent
        mock_parent = MagicMock()
        mock_parent.save_conversation.return_value = (True, "Saved")

        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=False,
            approval_callback=None,
            check_interrupted=lambda: False,
            parent_agent=mock_parent,
        )
        run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        # save_conversation should have been called
        mock_parent.save_conversation.assert_called()

    def test_handles_tool_execution_failure_gracefully(
        self,
        mock_provider: MagicMock,
        permission_manager: PermissionManager,
        executor: ActionExecutor,
        console: Console,
        conversation_history: list[dict[str, Any]],
    ) -> None:
        """Test that tool execution failures are handled gracefully."""
        first_response = {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {
                        "name": "read_file",
                        "arguments": json.dumps({"file_path": "/nonexistent/path.txt"}),
                    },
                }
            ],
        }

        second_response = {
            "role": "assistant",
            "content": "I couldn't read the file.",
            "finish_reason": "stop",
        }

        mock_provider.create_message.side_effect = [first_response, second_response]

        # The loop should continue even when tool fails
        config = AgentLoopConfig(
            provider=mock_provider,
            model="gpt-4",
            permission_manager=permission_manager,
            executor=executor,
            console=console,
            auto_approve_all=True,
            approval_callback=None,
            check_interrupted=lambda: False,
        )
        result = run_agent_loop(
            conversation_history=conversation_history,
            config=config,
        )

        assert result == "I couldn't read the file."
        # Should have completed both iterations
        assert mock_provider.create_message.call_count == 2
