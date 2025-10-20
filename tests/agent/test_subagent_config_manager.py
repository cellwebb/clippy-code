"""Tests for subagent configuration manager."""

import tempfile
from pathlib import Path

import pytest

from clippy.agent.subagent_config_manager import SubagentConfigManager


class TestSubagentConfigManager:
    """Test SubagentConfigManager class."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            config_path = Path(f.name)
        yield config_path
        # Cleanup
        if config_path.exists():
            config_path.unlink()

    def test_manager_initialization(self, temp_config_file):
        """Test manager initialization."""
        manager = SubagentConfigManager(temp_config_file)
        assert manager.config_path == temp_config_file
        assert manager._model_overrides == {}

    def test_get_model_override_not_set(self, temp_config_file):
        """Test getting model override when not set."""
        manager = SubagentConfigManager(temp_config_file)
        override = manager.get_model_override("general")
        assert override is None

    def test_set_model_override(self, temp_config_file):
        """Test setting model override."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")

        override = manager.get_model_override("general")
        assert override == "gpt-4-turbo"

    def test_set_model_override_invalid_type(self, temp_config_file):
        """Test setting model override with invalid subagent type."""
        manager = SubagentConfigManager(temp_config_file)

        with pytest.raises(ValueError, match="Invalid subagent type"):
            manager.set_model_override("invalid_type", "gpt-4")

    def test_set_model_override_persistence(self, temp_config_file):
        """Test that model overrides persist across manager instances."""
        # Set override in first manager
        manager1 = SubagentConfigManager(temp_config_file)
        manager1.set_model_override("general", "gpt-4-turbo")

        # Load in second manager
        manager2 = SubagentConfigManager(temp_config_file)
        override = manager2.get_model_override("general")
        assert override == "gpt-4-turbo"

    def test_clear_model_override(self, temp_config_file):
        """Test clearing model override."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")

        cleared = manager.clear_model_override("general")
        assert cleared is True

        override = manager.get_model_override("general")
        assert override is None

    def test_clear_model_override_not_set(self, temp_config_file):
        """Test clearing model override that was not set."""
        manager = SubagentConfigManager(temp_config_file)

        cleared = manager.clear_model_override("general")
        assert cleared is False

    def test_clear_all_overrides(self, temp_config_file):
        """Test clearing all model overrides."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")
        manager.set_model_override("code_review", "claude-3-opus")
        manager.set_model_override("testing", "gpt-3.5-turbo")

        count = manager.clear_all_overrides()
        assert count == 3

        # Verify all cleared
        assert manager.get_model_override("general") is None
        assert manager.get_model_override("code_review") is None
        assert manager.get_model_override("testing") is None

    def test_list_overrides(self, temp_config_file):
        """Test listing all overrides."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")
        manager.set_model_override("code_review", "claude-3-opus")

        overrides = manager.list_overrides()
        assert overrides == {
            "general": "gpt-4-turbo",
            "code_review": "claude-3-opus",
        }

    def test_get_all_configurations(self, temp_config_file):
        """Test getting all subagent configurations."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")

        configs = manager.get_all_configurations()

        # Check that all subagent types are present
        assert "general" in configs
        assert "code_review" in configs
        assert "testing" in configs

        # Check general config has override
        general_config = configs["general"]
        assert general_config["model_override"] == "gpt-4-turbo"
        assert "max_iterations" in general_config
        assert "allowed_tools" in general_config

        # Check code_review config has no override
        code_review_config = configs["code_review"]
        assert code_review_config["model_override"] is None

    def test_set_none_clears_override(self, temp_config_file):
        """Test that setting model to None clears the override."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")

        # Set to None should clear
        manager.set_model_override("general", None)

        override = manager.get_model_override("general")
        assert override is None

    def test_multiple_overrides_independence(self, temp_config_file):
        """Test that multiple overrides are independent."""
        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")
        manager.set_model_override("code_review", "claude-3-opus")

        # Clear one shouldn't affect the other
        manager.clear_model_override("general")

        assert manager.get_model_override("general") is None
        assert manager.get_model_override("code_review") == "claude-3-opus"

    def test_load_config_handles_missing_file(self, temp_config_file):
        """Test that loading handles missing config file gracefully."""
        # Use non-existent file path
        non_existent = temp_config_file.parent / "non_existent.json"
        manager = SubagentConfigManager(non_existent)

        # Should initialize with empty overrides
        assert manager._model_overrides == {}

    def test_config_json_format(self, temp_config_file):
        """Test that config file has correct JSON format."""
        import json

        manager = SubagentConfigManager(temp_config_file)
        manager.set_model_override("general", "gpt-4-turbo")

        # Read and verify JSON structure
        with open(temp_config_file) as f:
            data = json.load(f)

        assert "model_overrides" in data
        assert data["model_overrides"]["general"] == "gpt-4-turbo"
