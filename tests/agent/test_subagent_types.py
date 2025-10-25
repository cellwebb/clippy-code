"""Tests for subagent types and configurations."""

import pytest

from clippy.agent.subagent_types import (
    SUBAGENT_TYPES,
    get_default_config,
    get_subagent_config,
    list_subagent_types,
    validate_model_for_subagent_type,
    validate_subagent_config,
)


class TestSubagentTypes:
    """Test subagent type configurations."""

    def test_subagent_types_structure(self):
        """Test that SUBAGENT_TYPES has the expected structure."""
        assert isinstance(SUBAGENT_TYPES, dict)
        assert len(SUBAGENT_TYPES) > 0

        # Check required types exist
        required_types = ["general", "code_review", "testing", "refactor", "documentation"]
        for required_type in required_types:
            assert required_type in SUBAGENT_TYPES

        # Check each type has required fields
        for subagent_type, config in SUBAGENT_TYPES.items():
            assert isinstance(config, dict)
            assert "system_prompt" in config
            assert "allowed_tools" in config
            assert "max_iterations" in config
            assert isinstance(config["system_prompt"], str)
            assert isinstance(config["max_iterations"], int)
            assert config["max_iterations"] > 0

    def test_general_subagent_config(self):
        """Test general subagent configuration."""
        config = SUBAGENT_TYPES["general"]
        assert "clippy" in config["system_prompt"].lower()
        assert "helpful" in config["system_prompt"].lower()
        assert config["allowed_tools"] == "all"
        assert config["model"] is None
        assert config["max_iterations"] == 25

    def test_code_review_subagent_config(self):
        """Test code review subagent configuration."""
        config = SUBAGENT_TYPES["code_review"]
        assert "clippy" in config["system_prompt"].lower()
        assert "code review specialist" in config["system_prompt"].lower()
        assert isinstance(config["allowed_tools"], list)
        assert "read_file" in config["allowed_tools"]
        assert "write_file" not in config["allowed_tools"]  # Read-only
        assert config["max_iterations"] == 15

    def test_testing_subagent_config(self):
        """Test testing subagent configuration."""
        config = SUBAGENT_TYPES["testing"]
        assert "clippy" in config["system_prompt"].lower()
        assert "testing specialist" in config["system_prompt"].lower()
        assert isinstance(config["allowed_tools"], list)
        assert "write_file" in config["allowed_tools"]
        assert "execute_command" in config["allowed_tools"]
        assert config["max_iterations"] == 30

    def test_refactor_subagent_config(self):
        """Test refactor subagent configuration."""
        config = SUBAGENT_TYPES["refactor"]
        assert "clippy" in config["system_prompt"].lower()
        assert "refactoring specialist" in config["system_prompt"].lower()
        assert isinstance(config["allowed_tools"], list)
        assert "edit_file" in config["allowed_tools"]
        assert "write_file" in config["allowed_tools"]
        assert config["max_iterations"] == 30

    def test_documentation_subagent_config(self):
        """Test documentation subagent configuration."""
        config = SUBAGENT_TYPES["documentation"]
        assert "clippy" in config["system_prompt"].lower()
        assert "documentation specialist" in config["system_prompt"].lower()
        assert isinstance(config["allowed_tools"], list)
        assert "write_file" in config["allowed_tools"]
        assert config["max_iterations"] == 20

    def test_fast_general_subagent_config(self):
        """Test fast general subagent configuration."""
        config = SUBAGENT_TYPES["fast_general"]
        assert "clippy" in config["system_prompt"].lower()
        assert "speed" in config["system_prompt"].lower()
        assert isinstance(config["allowed_tools"], list)
        assert "write_file" not in config["allowed_tools"]  # Read-only for speed
        assert config["model"] is None  # Inherits from parent agent
        assert config["max_iterations"] == 10

    def test_power_analysis_subagent_config(self):
        """Test power analysis subagent configuration."""
        config = SUBAGENT_TYPES["power_analysis"]
        assert "clippy" in config["system_prompt"].lower()
        assert "deep analysis specialist" in config["system_prompt"].lower()
        assert config["allowed_tools"] == "all"
        assert config["model"] is None  # Inherits from parent agent
        assert config["max_iterations"] == 40


class TestSubagentTypeFunctions:
    """Test subagent type utility functions."""

    def test_get_subagent_config_valid(self):
        """Test getting configuration for valid subagent type."""
        config = get_subagent_config("general")
        assert isinstance(config, dict)
        assert "system_prompt" in config
        assert "allowed_tools" in config
        assert "max_iterations" in config

    def test_get_subagent_config_invalid(self):
        """Test getting configuration for invalid subagent type."""
        with pytest.raises(ValueError, match="Unknown subagent type"):
            get_subagent_config("invalid_type")

    def test_list_subagent_types(self):
        """Test listing subagent types."""
        types = list_subagent_types()
        assert isinstance(types, list)
        assert len(types) > 0
        assert "general" in types
        assert "code_review" in types

    def test_validate_subagent_config_valid(self):
        """Test validating valid subagent configuration."""
        config = {
            "name": "test_subagent",
            "task": "Test task",
            "subagent_type": "general",
            "timeout": 300,
            "max_iterations": 25,
        }

        is_valid, error_msg = validate_subagent_config(config)
        assert is_valid is True
        assert error_msg == ""

    def test_validate_subagent_config_missing_fields(self):
        """Test validating configuration with missing required fields."""
        config = {
            "name": "test_subagent",
            # Missing task and subagent_type
        }

        is_valid, error_msg = validate_subagent_config(config)
        assert is_valid is False
        assert "Missing required field: task" in error_msg

    def test_validate_subagent_config_invalid_type(self):
        """Test validating configuration with invalid subagent type."""
        config = {
            "name": "test_subagent",
            "task": "Test task",
            "subagent_type": "invalid_type",
        }

        is_valid, error_msg = validate_subagent_config(config)
        assert is_valid is False
        assert "Invalid subagent_type" in error_msg

    def test_validate_subagent_config_invalid_timeout(self):
        """Test validating configuration with invalid timeout."""
        config = {
            "name": "test_subagent",
            "task": "Test task",
            "subagent_type": "general",
            "timeout": -1,  # Invalid timeout
        }

        is_valid, error_msg = validate_subagent_config(config)
        assert is_valid is False
        assert "timeout must be a positive number" in error_msg

    def test_validate_subagent_config_invalid_iterations(self):
        """Test validating configuration with invalid max_iterations."""
        config = {
            "name": "test_subagent",
            "task": "Test task",
            "subagent_type": "general",
            "max_iterations": 0,  # Invalid iterations
        }

        is_valid, error_msg = validate_subagent_config(config)
        assert is_valid is False
        assert "max_iterations must be a positive integer" in error_msg

    def test_validate_subagent_config_invalid_allowed_tools(self):
        """Test validating configuration with invalid allowed_tools."""
        config = {
            "name": "test_subagent",
            "task": "Test task",
            "subagent_type": "general",
            "allowed_tools": "invalid",  # Should be "all" or a list
        }

        is_valid, error_msg = validate_subagent_config(config)
        assert is_valid is False
        assert "allowed_tools must be 'all' or a list" in error_msg

    def test_get_default_config(self):
        """Test getting default configuration."""
        config = get_default_config("general")
        assert isinstance(config, dict)
        assert config["subagent_type"] == "general"
        assert "system_prompt" in config
        assert "allowed_tools" in config
        assert config["max_iterations"] == 25
        assert config["timeout"] == 300

    def test_get_default_config_with_override(self):
        """Test getting default configuration with type-specific override."""
        config = get_default_config("code_review")
        assert config["subagent_type"] == "code_review"
        assert config["max_iterations"] == 15  # Type-specific override


class TestModelValidation:
    """Test model validation functions."""

    def test_validate_model_for_subagent_type_none(self):
        """Test validating None model (use parent model)."""
        is_valid, error_msg = validate_model_for_subagent_type("general", None)
        assert is_valid is True
        assert error_msg == ""

    def test_validate_model_for_subagent_type_valid(self):
        """Test validating valid models."""
        valid_models = [
            "gpt-4-turbo",
            "claude-3-sonnet-20240229",
            "llama-2-70b",
            "localhost:8000/v1",
        ]

        for model in valid_models:
            is_valid, error_msg = validate_model_for_subagent_type("general", model)
            assert is_valid is True
            if "Warning:" in error_msg:
                # Unknown format warnings are allowed
                pass

    def test_validate_model_for_subagent_type_invalid(self):
        """Test validating invalid models."""
        invalid_models = [
            "",
            "   ",
            None,
            123,
        ]

        for model in invalid_models:
            is_valid, error_msg = validate_model_for_subagent_type("general", model)
            if model is None:
                # None should be valid (use parent model)
                assert is_valid is True
            else:
                # Other invalid models should fail
                assert is_valid is False
                assert "non-empty string" in error_msg
