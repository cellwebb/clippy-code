"""Tests for the run_parallel_subagents tool."""

from unittest.mock import MagicMock, patch

from clippy.agent.subagent import SubAgentConfig, SubAgentResult
from clippy.tools.run_parallel_subagents import (
    TOOL_SCHEMA,
    _aggregate_results,
    create_parallel_subagents_and_execute,
    get_tool_schema,
)


class TestRunParallelSubagentsTool:
    """Test run_parallel_subagents tool."""

    def test_get_tool_schema(self):
        """Test getting tool schema."""
        schema = get_tool_schema()
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema

        function_def = schema["function"]
        assert function_def["name"] == "run_parallel_subagents"
        assert "description" in function_def
        assert "parameters" in function_def

        parameters = function_def["parameters"]
        assert parameters["type"] == "object"
        assert "properties" in parameters
        assert "required" in parameters

        # Check required parameters
        required = parameters["required"]
        assert "subagents" in required

        # Check properties
        properties = parameters["properties"]
        assert "subagents" in properties
        assert "max_concurrent" in properties
        assert "fail_fast" in properties
        assert "aggregate_results" in properties

        # Check subagents property
        subagents_prop = properties["subagents"]
        assert subagents_prop["type"] == "array"
        assert "items" in subagents_prop

        # Check subagent item properties
        item_props = subagents_prop["items"]["properties"]
        assert "task" in item_props
        assert "subagent_type" in item_props
        assert "allowed_tools" in item_props
        assert "context" in item_props
        assert "timeout" in item_props
        assert "max_iterations" in item_props

    def test_tool_schema_constant(self):
        """Test TOOL_SCHEMA constant."""
        assert TOOL_SCHEMA == get_tool_schema()

    @patch("clippy.tools.run_parallel_subagents.SubAgentConfig")
    @patch("clippy.tools.run_parallel_subagents.SubAgent")
    @patch("clippy.tools.run_parallel_subagents.get_default_config")
    def test_create_parallel_subagents_success(
        self, mock_get_default_config, mock_subagent_class, mock_subagent_config_class
    ):
        """Test successful parallel subagent creation and execution."""
        # Mock dependencies
        mock_parent_agent = MagicMock()
        mock_permission_manager = MagicMock()

        # Mock default configs
        mock_default_configs = [
            {
                "system_prompt": "Test prompt 1",
                "allowed_tools": ["read_file"],
                "model": None,
                "max_iterations": 25,
                "timeout": 300,
            },
            {
                "system_prompt": "Test prompt 2",
                "allowed_tools": ["write_file"],
                "model": None,
                "max_iterations": 30,
                "timeout": 300,
            },
        ]
        mock_get_default_config.side_effect = mock_default_configs

        # Mock SubAgentConfig to return actual configs
        def create_config(**kwargs):
            return SubAgentConfig(**kwargs)

        mock_subagent_config_class.side_effect = create_config

        # Mock subagents
        mock_subagents = []
        mock_results = []
        for i in range(2):
            mock_subagent = MagicMock()
            mock_subagent.config.name = f"test_subagent_{i}_123"
            mock_result = SubAgentResult(
                success=True,
                output=f"Task {i} completed successfully",
                error=None,
                iterations_used=5 + i,
                execution_time=2.0 + i,
                metadata={"subagent_name": f"test_subagent_{i}_123"},
            )
            mock_subagent.run.return_value = mock_result
            mock_subagents.append(mock_subagent)
            mock_results.append(mock_result)

        mock_subagent_class.side_effect = mock_subagents

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.side_effect = mock_subagents
        mock_manager.run_parallel.return_value = mock_results
        mock_parent_agent.subagent_manager = mock_manager

        # Subagent configurations
        subagent_configs = [
            {
                "task": "Test task 1",
                "subagent_type": "general",
                "timeout": 600,
            },
            {
                "task": "Test task 2",
                "subagent_type": "testing",
                "max_iterations": 40,
            },
        ]

        # Execute
        success, message, result = create_parallel_subagents_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            subagents=subagent_configs,
            max_concurrent=2,
            fail_fast=False,
            aggregate_results=True,
        )

        # Verify success
        assert success is True
        assert "2 succeeded, 0 failed" in message
        assert isinstance(result, dict)

        # Verify result structure
        assert "individual_results" in result
        assert "summary" in result
        assert "total_successful" in result
        assert "total_failed" in result
        assert "total_execution_time" in result

        assert result["total_successful"] == 2
        assert result["total_failed"] == 0
        assert result["total_execution_time"] == 5.0  # 2.0 + 3.0

        # Verify individual results
        individual_results = result["individual_results"]
        assert len(individual_results) == 2
        for i, individual_result in enumerate(individual_results):
            assert individual_result["success"] is True
            assert f"Task {i} completed successfully" in individual_result["output"]

        # Verify manager calls
        assert mock_manager.create_subagent.call_count == 2
        mock_manager.run_parallel.assert_called_once_with(mock_subagents, max_concurrent=2)

    @patch("clippy.tools.run_parallel_subagents.SubAgentConfig")
    @patch("clippy.tools.run_parallel_subagents.SubAgent")
    @patch("clippy.tools.run_parallel_subagents.get_default_config")
    def test_create_parallel_subagents_mixed_results(
        self, mock_get_default_config, mock_subagent_class, mock_subagent_config_class
    ):
        """Test parallel subagents with mixed success/failure."""
        # Mock dependencies
        mock_parent_agent = MagicMock()
        mock_permission_manager = MagicMock()

        # Mock default config
        mock_default_config = {
            "system_prompt": "Test prompt",
            "allowed_tools": ["read_file"],
            "model": None,
            "max_iterations": 25,
            "timeout": 300,
        }
        mock_get_default_config.return_value = mock_default_config

        # Mock SubAgentConfig to return actual configs
        def create_config(**kwargs):
            return SubAgentConfig(**kwargs)

        mock_subagent_config_class.side_effect = create_config

        # Mock subagents with mixed results
        mock_subagents = []
        mock_results = [
            SubAgentResult(
                success=True,
                output="Task 1 completed",
                error=None,
                iterations_used=5,
                execution_time=2.0,
                metadata={},
            ),
            SubAgentResult(
                success=False,
                output="",
                error="Task 2 failed",
                iterations_used=3,
                execution_time=1.0,
                metadata={},
            ),
            SubAgentResult(
                success=True,
                output="Task 3 completed",
                error=None,
                iterations_used=7,
                execution_time=3.0,
                metadata={},
            ),
        ]

        for result in mock_results:
            mock_subagent = MagicMock()
            mock_subagent.config.name = "test_subagent"
            mock_subagent.run.return_value = result
            mock_subagents.append(mock_subagent)

        mock_subagent_class.side_effect = mock_subagents

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.side_effect = mock_subagents
        mock_manager.run_parallel.return_value = mock_results
        mock_parent_agent.subagent_manager = mock_manager

        # Execute
        success, message, result = create_parallel_subagents_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            subagents=[
                {"task": "Task 1", "subagent_type": "general"},
                {"task": "Task 2", "subagent_type": "general"},
                {"task": "Task 3", "subagent_type": "general"},
            ],
        )

        # Verify mixed results
        assert success is True  # Overall success because some succeeded
        assert "2 succeeded, 1 failed" in message
        assert result["total_successful"] == 2
        assert result["total_failed"] == 1

    @patch("clippy.tools.run_parallel_subagents.SubAgentConfig")
    @patch("clippy.tools.run_parallel_subagents.SubAgent")
    @patch("clippy.tools.run_parallel_subagents.get_default_config")
    def test_create_parallel_subagents_fail_fast(
        self, mock_get_default_config, mock_subagent_class, mock_subagent_config_class
    ):
        """Test parallel subagents with fail_fast enabled."""
        # Mock dependencies
        mock_parent_agent = MagicMock()
        mock_permission_manager = MagicMock()

        # Mock default config
        mock_default_config = {
            "system_prompt": "Test prompt",
            "allowed_tools": ["read_file"],
            "model": None,
            "max_iterations": 25,
            "timeout": 300,
        }
        mock_get_default_config.return_value = mock_default_config

        # Mock SubAgentConfig to return actual configs
        def create_config(**kwargs):
            return SubAgentConfig(**kwargs)

        mock_subagent_config_class.side_effect = create_config

        # Mock subagents with one failure
        mock_subagents = []
        mock_results = [
            SubAgentResult(
                success=True,
                output="Success",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=False,
                output="",
                error="Failed",
                iterations_used=1,
                execution_time=0.5,
            ),
        ]

        for result in mock_results:
            mock_subagent = MagicMock()
            mock_subagent.config.name = "test_subagent"
            mock_subagent.run.return_value = result
            mock_subagents.append(mock_subagent)

        mock_subagent_class.side_effect = mock_subagents

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.side_effect = mock_subagents
        mock_manager.run_parallel.return_value = mock_results
        mock_parent_agent.subagent_manager = mock_manager

        # Execute with fail_fast
        success, message, result = create_parallel_subagents_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            subagents=[
                {"task": "Task 1", "subagent_type": "general"},
                {"task": "Task 2", "subagent_type": "general"},
            ],
            fail_fast=True,
        )

        # Verify fail_fast behavior
        assert "stopped early" in message.lower()
        assert "1 succeeded, 1 failed" in message

    @patch("clippy.tools.run_parallel_subagents.SubAgentConfig")
    @patch("clippy.tools.run_parallel_subagents.SubAgent")
    @patch("clippy.tools.run_parallel_subagents.get_default_config")
    def test_create_parallel_subagents_no_aggregation(
        self, mock_get_default_config, mock_subagent_class, mock_subagent_config_class
    ):
        """Test parallel subagents without result aggregation."""
        # Mock dependencies
        mock_parent_agent = MagicMock()
        mock_permission_manager = MagicMock()

        # Mock default config
        mock_default_config = {
            "system_prompt": "Test prompt",
            "allowed_tools": ["read_file"],
            "model": None,
            "max_iterations": 25,
            "timeout": 300,
        }
        mock_get_default_config.return_value = mock_default_config

        # Mock SubAgentConfig to return actual configs
        def create_config(**kwargs):
            return SubAgentConfig(**kwargs)

        mock_subagent_config_class.side_effect = create_config

        # Mock subagents
        mock_subagents = []
        mock_results = [
            SubAgentResult(
                success=True,
                output="Result 1",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=True,
                output="Result 2",
                error=None,
                iterations_used=3,
                execution_time=1.0,
            ),
        ]

        for result in mock_results:
            mock_subagent = MagicMock()
            mock_subagent.config.name = "test_subagent"
            mock_subagent.run.return_value = result
            mock_subagents.append(mock_subagent)

        mock_subagent_class.side_effect = mock_subagents

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.side_effect = mock_subagents
        mock_manager.run_parallel.return_value = mock_results
        mock_parent_agent.subagent_manager = mock_manager

        # Execute without aggregation
        success, message, result = create_parallel_subagents_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            subagents=[
                {"task": "Task 1", "subagent_type": "general"},
                {"task": "Task 2", "subagent_type": "general"},
            ],
            aggregate_results=False,
        )

        # Verify no aggregation
        assert success is True
        assert result == mock_results  # Should return raw results list

    def test_create_parallel_subagents_empty_list(self):
        """Test parallel subagents with empty list."""
        mock_parent_agent = MagicMock()
        mock_permission_manager = MagicMock()

        # Execute with empty list
        success, message, result = create_parallel_subagents_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            subagents=[],
        )

        # Should handle gracefully
        assert success is True
        assert result == []

    @patch("clippy.tools.run_parallel_subagents.get_default_config")
    def test_create_parallel_subagents_config_exception(self, mock_get_default_config):
        """Test parallel subagents with configuration exception."""
        # Mock dependencies
        mock_parent_agent = MagicMock()
        mock_permission_manager = MagicMock()

        # Mock default config to raise exception
        mock_get_default_config.side_effect = ValueError("Invalid subagent type")

        # Execute
        success, message, result = create_parallel_subagents_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            subagents=[
                {"task": "Task 1", "subagent_type": "invalid_type"},
            ],
        )

        # Verify failure
        assert success is False
        assert "Failed to create or execute parallel subagents" in message
        assert "Invalid subagent type" in message

    def test_aggregate_results_all_success(self):
        """Test aggregating all successful results."""
        results = [
            SubAgentResult(
                success=True,
                output="Success 1",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=True,
                output="Success 2",
                error=None,
                iterations_used=3,
                execution_time=1.0,
            ),
        ]

        summary = _aggregate_results(results)

        assert "📊 Execution Summary:" in summary
        assert "Total subagents: 2" in summary
        assert "Successful: 2" in summary
        assert "Failed: 0" in summary
        assert "Total execution time: 3.00s" in summary
        assert "Total iterations: 8" in summary
        assert "✅ Successful Subagents:" in summary
        assert "Success 1" in summary
        assert "Success 2" in summary

    def test_aggregate_results_mixed_results(self):
        """Test aggregating mixed success/failure results."""
        results = [
            SubAgentResult(
                success=True,
                output="Success",
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
            SubAgentResult(
                success=False,
                output="",
                error="Failure message",
                iterations_used=1,
                execution_time=0.5,
            ),
        ]

        summary = _aggregate_results(results)

        assert "Successful: 1" in summary
        assert "Failed: 1" in summary
        assert "✅ Successful Subagents:" in summary
        assert "❌ Failed Subagents:" in summary
        assert "Success" in summary
        assert "Failure message" in summary

    def test_aggregate_results_all_failures(self):
        """Test aggregating all failed results."""
        results = [
            SubAgentResult(
                success=False,
                output="",
                error="Error 1",
                iterations_used=1,
                execution_time=0.5,
            ),
            SubAgentResult(
                success=False,
                output="",
                error="Error 2",
                iterations_used=2,
                execution_time=1.0,
            ),
        ]

        summary = _aggregate_results(results)

        assert "Successful: 0" in summary
        assert "Failed: 2" in summary
        assert "✅ Successful Subagents:" not in summary
        assert "❌ Failed Subagents:" in summary
        assert "Error 1" in summary
        assert "Error 2" in summary

    def test_aggregate_results_empty_list(self):
        """Test aggregating empty results list."""
        summary = _aggregate_results([])

        assert "Total subagents: 0" in summary
        assert "Successful: 0" in summary
        assert "Failed: 0" in summary

    def test_aggregate_results_long_output_truncation(self):
        """Test that long output is truncated in aggregation."""
        long_output = "A" * 200  # Long output
        results = [
            SubAgentResult(
                success=True,
                output=long_output,
                error=None,
                iterations_used=5,
                execution_time=2.0,
            ),
        ]

        summary = _aggregate_results(results)

        # Should be truncated with ...
        assert long_output not in summary
        assert "..." in summary

    def test_tool_schema_fallback(self):
        """Test tool schema fallback when subagent_types import fails."""
        with patch(
            "clippy.tools.run_parallel_subagents.list_subagent_types",
            side_effect=ImportError,
        ):
            schema = get_tool_schema()

            # Should still return a valid schema with fallback enum
            assert isinstance(schema, dict)
            assert schema["function"]["name"] == "run_parallel_subagents"

            enum_values = schema["function"]["parameters"]["properties"]["subagents"]["items"][
                "properties"
            ]["subagent_type"]["enum"]
            assert isinstance(enum_values, list)
            assert "general" in enum_values
            assert "code_review" in enum_values
