"""Tests for the delegate_to_subagent tool."""

from unittest.mock import MagicMock, patch

from clippy.agent.core import ClippyAgent
from clippy.agent.subagent import SubAgentConfig, SubAgentResult
from clippy.tools.delegate_to_subagent import (
    TOOL_SCHEMA,
    create_subagent_and_execute,
    get_tool_schema,
)


class TestDelegateToSubagentTool:
    """Test delegate_to_subagent tool."""

    def test_get_tool_schema(self):
        """Test getting tool schema."""
        schema = get_tool_schema()
        assert isinstance(schema, dict)
        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema

        function_def = schema["function"]
        assert function_def["name"] == "delegate_to_subagent"
        assert "description" in function_def
        assert "parameters" in function_def

        parameters = function_def["parameters"]
        assert parameters["type"] == "object"
        assert "properties" in parameters
        assert "required" in parameters

        # Check required parameters
        required = parameters["required"]
        assert "task" in required
        assert "subagent_type" in required

        # Check properties
        properties = parameters["properties"]
        assert "task" in properties
        assert "subagent_type" in properties
        assert "allowed_tools" in properties
        assert "context" in properties
        assert "timeout" in properties
        assert "max_iterations" in properties

        # Check parameter types
        assert properties["task"]["type"] == "string"
        assert properties["subagent_type"]["type"] == "string"
        assert properties["allowed_tools"]["type"] == "array"
        assert properties["context"]["type"] == "object"
        assert properties["timeout"]["type"] == "integer"
        assert properties["max_iterations"]["type"] == "integer"

        # Check subagent_type enum
        enum_values = properties["subagent_type"]["enum"]
        assert isinstance(enum_values, list)
        assert "general" in enum_values
        assert "code_review" in enum_values
        assert "testing" in enum_values

    def test_tool_schema_constant(self):
        """Test TOOL_SCHEMA constant."""
        assert TOOL_SCHEMA == get_tool_schema()

    @patch("clippy.agent.subagent.SubAgent")
    @patch("clippy.agent.subagent_types.get_default_config")
    def test_create_subagent_and_execute_success(
        self, mock_get_default_config, mock_subagent_class
    ):
        """Test successful subagent creation and execution."""
        # Mock dependencies
        mock_parent_agent = MagicMock(spec=ClippyAgent)
        mock_permission_manager = MagicMock()

        # Mock default config
        mock_default_config = {
            "system_prompt": "Test prompt",
            "allowed_tools": ["read_file", "write_file"],
            "model": None,
            "max_iterations": 25,
            "timeout": 300,
        }
        mock_get_default_config.return_value = mock_default_config

        # Mock subagent
        mock_subagent = MagicMock()
        mock_subagent.config.name = "test_subagent_123"
        mock_result = SubAgentResult(
            success=True,
            output="Task completed successfully",
            error=None,
            iterations_used=5,
            execution_time=2.0,
            metadata={"subagent_name": "test_subagent_123"},
        )
        mock_subagent.run.return_value = mock_result
        mock_subagent_class.return_value = mock_subagent

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.return_value = mock_subagent
        mock_parent_agent.subagent_manager = mock_manager

        # Execute
        success, message, result = create_subagent_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            task="Test task description",
            subagent_type="general",
            allowed_tools=["read_file"],
            context={"project": "test"},
            timeout=600,
            max_iterations=50,
        )

        # Verify success
        assert success is True
        assert "completed successfully" in message
        assert result == mock_result

        # Verify default config was called
        mock_get_default_config.assert_called_once_with("general")

        # Verify config overrides
        assert mock_default_config["max_iterations"] == 50
        assert mock_default_config["timeout"] == 600
        assert mock_default_config["allowed_tools"] == ["read_file"]

        # Verify subagent creation
        mock_manager.create_subagent.assert_called_once()
        created_config = mock_manager.create_subagent.call_args[0][0]
        assert isinstance(created_config, SubAgentConfig)
        assert created_config.task == "Test task description"
        assert created_config.subagent_type == "general"
        assert created_config.allowed_tools == ["read_file"]
        assert created_config.context == {"project": "test"}
        assert created_config.timeout == 600
        assert created_config.max_iterations == 50

    @patch("clippy.agent.subagent.SubAgent")
    @patch("clippy.agent.subagent_types.get_default_config")
    def test_create_subagent_and_execute_failure(
        self, mock_get_default_config, mock_subagent_class
    ):
        """Test subagent creation and execution with failure."""
        # Mock dependencies
        mock_parent_agent = MagicMock(spec=ClippyAgent)
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

        # Mock subagent with failure
        mock_subagent = MagicMock()
        mock_subagent.config.name = "test_subagent_123"
        mock_result = SubAgentResult(
            success=False,
            output="",
            error="Task failed: Something went wrong",
            iterations_used=3,
            execution_time=1.0,
            metadata={"failure_reason": "task_error"},
        )
        mock_subagent.run.return_value = mock_result
        mock_subagent_class.return_value = mock_subagent

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.return_value = mock_subagent
        mock_parent_agent.subagent_manager = mock_manager

        # Execute
        success, message, result = create_subagent_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            task="Test failing task",
            subagent_type="general",
        )

        # Verify failure
        assert success is False
        assert "failed: Something went wrong" in message
        assert result == mock_result

    @patch("clippy.agent.subagent_types.get_default_config")
    def test_create_subagent_and_execute_config_exception(self, mock_get_default_config):
        """Test subagent creation with configuration exception."""
        # Mock dependencies
        mock_parent_agent = MagicMock(spec=ClippyAgent)
        mock_permission_manager = MagicMock()

        # Mock default config to raise exception
        mock_get_default_config.side_effect = ValueError("Invalid subagent type")

        # Execute
        success, message, result = create_subagent_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            task="Test task",
            subagent_type="invalid_type",
        )

        # Verify failure
        assert success is False
        assert "Failed to create or execute subagent" in message
        assert "Invalid subagent type" in message
        assert isinstance(result, SubAgentResult)
        assert result.success is False

    @patch("clippy.agent.subagent.SubAgent")
    @patch("clippy.agent.subagent_types.get_default_config")
    def test_create_subagent_and_execute_execution_exception(
        self, mock_get_default_config, mock_subagent_class
    ):
        """Test subagent execution with exception."""
        # Mock dependencies
        mock_parent_agent = MagicMock(spec=ClippyAgent)
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

        # Mock subagent that raises exception during run
        mock_subagent = MagicMock()
        mock_subagent.config.name = "test_subagent_123"
        mock_subagent.run.side_effect = RuntimeError("Execution error")
        mock_subagent_class.return_value = mock_subagent

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.return_value = mock_subagent
        mock_parent_agent.subagent_manager = mock_manager

        # Execute
        success, message, result = create_subagent_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            task="Test task",
            subagent_type="general",
        )

        # Verify failure
        assert success is False
        assert "Failed to create or execute subagent" in message
        assert "Execution error" in message
        assert isinstance(result, SubAgentResult)
        assert result.success is False

    @patch("clippy.agent.subagent.SubAgent")
    @patch("clippy.agent.subagent_types.get_default_config")
    def test_create_subagent_and_execute_with_minimal_params(
        self, mock_get_default_config, mock_subagent_class
    ):
        """Test subagent creation with minimal parameters."""
        # Mock dependencies
        mock_parent_agent = MagicMock(spec=ClippyAgent)
        mock_permission_manager = MagicMock()

        # Mock default config
        mock_default_config = {
            "system_prompt": "Test prompt",
            "allowed_tools": "all",
            "model": None,
            "max_iterations": 25,
            "timeout": 300,
        }
        mock_get_default_config.return_value = mock_default_config

        # Mock subagent
        mock_subagent = MagicMock()
        mock_subagent.config.name = "test_subagent_456"
        mock_result = SubAgentResult(
            success=True,
            output="Minimal task completed",
            error=None,
            iterations_used=2,
            execution_time=1.0,
            metadata={},
        )
        mock_subagent.run.return_value = mock_result
        mock_subagent_class.return_value = mock_subagent

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.return_value = mock_subagent
        mock_parent_agent.subagent_manager = mock_manager

        # Execute with minimal parameters
        success, message, result = create_subagent_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            task="Simple task",
            subagent_type="general",
        )

        # Verify success
        assert success is True
        assert result == mock_result

        # Verify default config wasn't modified
        assert mock_default_config["max_iterations"] == 25
        assert mock_default_config["timeout"] == 300
        assert mock_default_config["allowed_tools"] == "all"

    @patch("clippy.agent.subagent.SubAgent")
    @patch("clippy.agent.subagent_types.get_default_config")
    def test_create_subagent_and_execute_with_context(
        self, mock_get_default_config, mock_subagent_class
    ):
        """Test subagent creation with context."""
        # Mock dependencies
        mock_parent_agent = MagicMock(spec=ClippyAgent)
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

        # Mock subagent
        mock_subagent = MagicMock()
        mock_subagent.config.name = "test_subagent_789"
        mock_result = SubAgentResult(
            success=True,
            output="Context-aware task completed",
            error=None,
            iterations_used=3,
            execution_time=1.5,
            metadata={},
        )
        mock_subagent.run.return_value = mock_result
        mock_subagent_class.return_value = mock_subagent

        # Mock subagent manager
        mock_manager = MagicMock()
        mock_manager.create_subagent.return_value = mock_subagent
        mock_parent_agent.subagent_manager = mock_manager

        # Context data
        context_data = {
            "project": "my_project",
            "focus": "security",
            "files": ["src/auth.py", "src/user.py"],
        }

        # Execute with context
        success, message, result = create_subagent_and_execute(
            parent_agent=mock_parent_agent,
            permission_manager=mock_permission_manager,
            task="Review authentication code",
            subagent_type="code_review",
            context=context_data,
        )

        # Verify success
        assert success is True

        # Verify context was passed
        created_config = mock_manager.create_subagent.call_args[0][0]
        assert created_config.context == context_data

    def test_tool_schema_fallback(self):
        """Test tool schema fallback when subagent_types import fails."""
        with patch("clippy.agent.subagent_types.list_subagent_types", side_effect=ImportError):
            schema = get_tool_schema()

            # Should still return a valid schema with fallback enum
            assert isinstance(schema, dict)
            assert schema["function"]["name"] == "delegate_to_subagent"

            enum_values = schema["function"]["parameters"]["properties"]["subagent_type"]["enum"]
            assert isinstance(enum_values, list)
            assert "general" in enum_values
            assert "code_review" in enum_values
