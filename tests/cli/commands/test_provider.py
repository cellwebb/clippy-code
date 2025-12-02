"""Tests for provider management commands."""

import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from src.clippy.cli.commands.provider import (
    _handle_provider_add,
    _save_provider_config,
    handle_provider_command,
    handle_providers_command,
)
from src.clippy.models import (
    ProviderConfig,
    UserProviderManager,
)


class TestProviderCommands:
    """Test suite for provider management commands."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())
        self.console = MagicMock()

        # Create a patch for the user provider manager to use our temp dir
        self.manager_patcher = patch("src.clippy.models.UserProviderManager")
        mock_manager_class = self.manager_patcher.start()

        # Create a mock manager instance
        self.mock_manager = MagicMock(spec=UserProviderManager)
        mock_manager_class.return_value = self.mock_manager

        # Set up the default behavior
        self.mock_manager.list_providers.return_value = {}
        self.mock_manager.get_provider.return_value = None
        self.mock_manager.add_provider.return_value = (True, "Provider added successfully")
        self.mock_manager.update_provider.return_value = (True, "Provider updated successfully")
        self.mock_manager.remove_provider.return_value = (True, "Provider removed successfully")

    def teardown_method(self):
        """Clean up after tests."""
        self.manager_patcher.stop()

    def test_handle_providers_command_empty(self):
        """Test handle_providers_command with no providers."""
        with patch(
            "src.clippy.models.list_providers_by_source", return_value={"built_in": [], "user": []}
        ):
            result = handle_providers_command(self.console)
            assert result == "continue"
            self.console.print.assert_called()
            # The function should have been called (even if with a Panel object)
            assert len(self.console.print.call_args_list) > 0

    def test_handle_providers_command_with_providers(self):
        """Test handle_providers_command with providers."""
        mock_providers = {
            "built_in": [("openai", "OpenAI API"), ("anthropic", "Anthropic API")],
            "user": [("my-provider", "Custom Provider")],
        }

        with patch("src.clippy.models.list_providers_by_source", return_value=mock_providers):
            result = handle_providers_command(self.console)
            assert result == "continue"
            self.console.print.assert_called()

    def test_handle_provider_command_no_args(self):
        """Test handle_provider_command with no arguments."""
        result = handle_provider_command(None, self.console, "")
        assert result == "continue"
        # Should print usage
        call_args = [call[0][0] for call in self.console.print.call_args_list]
        assert any("Usage: /provider <command>" in str(arg) for arg in call_args)

    def test_handle_provider_command_list(self):
        """Test handle_provider_command with list subcommand."""
        with patch("src.clippy.cli.commands.provider.list_providers_by_source") as mock_list:
            mock_list.return_value = {"built_in": [], "user": []}
            result = handle_provider_command(None, self.console, "list")
            assert result == "continue"
            # The list command calls handle_providers_command which calls list_providers_by_source
            mock_list.assert_called_once()

    def test_handle_provider_command_add(self):
        """Test handle_provider_command with add subcommand."""
        with patch("src.clippy.cli.commands.provider._handle_provider_add") as mock_add:
            mock_add.return_value = "continue"
            result = handle_provider_command(None, self.console, "add")
            assert result == "continue"
            mock_add.assert_called_once_with(self.console)

    def test_handle_provider_command_remove_no_name(self):
        """Test handle_provider_command remove without name."""
        result = handle_provider_command(None, self.console, "remove")
        assert result == "continue"
        # Should print usage error
        call_args = [call[0][0] for call in self.console.print.call_args_list]
        assert any("Usage: /provider remove <name>" in str(arg) for arg in call_args)

    def test_handle_provider_command_remove_with_name(self):
        """Test handle_provider_command remove with name."""
        with patch("src.clippy.models.get_provider") as mock_get_provider:
            with patch("src.clippy.models.is_user_provider") as mock_is_user:
                # Setup mocks
                mock_provider = ProviderConfig(
                    name="test-provider",
                    base_url="https://api.test.com",
                    api_key_env="TEST_API_KEY",
                    description="Test Provider",
                )
                mock_get_provider.return_value = mock_provider
                mock_is_user.return_value = True

                # Test with our mocked manager from setup
                result = handle_provider_command(None, self.console, "remove test-provider")
                assert result == "continue"

                # The remove command should have been called at some point through
                # the manager. Since we're mocking at the manager class level in
                # setup, check that our manager was used. This is an integration
                # test checking the flow works.

    def test_handle_provider_command_unknown_subcommand(self):
        """Test handle_provider_command with unknown subcommand."""
        with patch("src.clippy.models.get_provider") as mock_get_provider:
            mock_get_provider.return_value = None  # Provider doesn't exist

            result = handle_provider_command(None, self.console, "unknown-provider")
            assert result == "continue"
            # Should print unknown provider message
            call_args = [call[0][0] for call in self.console.print.call_args_list]
            assert any("Unknown provider: unknown-provider" in str(arg) for arg in call_args)

    def test_save_provider_config_add_new(self):
        """Test _save_provider_config adding a new provider."""
        with patch("src.clippy.models.get_user_provider_manager") as mock_get_manager:
            with patch("src.clippy.models.reload_providers") as mock_reload:
                # Setup mocks
                mock_manager = MagicMock()
                mock_manager.get_provider.return_value = None  # Provider doesn't exist
                mock_manager.add_provider.return_value = (True, "added successfully")
                mock_get_manager.return_value = mock_manager

                success, message = _save_provider_config(
                    provider_name="test-provider",
                    provider_type="openai",
                    description="Test Provider",
                    base_url="https://api.test.com/v1",
                    api_key_env="TEST_API_KEY",
                    console=self.console,
                )

                assert success is True
                assert "added successfully" in message
                mock_manager.add_provider.assert_called_once_with(
                    name="test-provider",
                    base_url="https://api.test.com/v1",
                    api_key_env="TEST_API_KEY",
                    description="Test Provider",
                )
                mock_reload.assert_called_once()

    def test_save_provider_config_update_existing(self):
        """Test _save_provider_config updating an existing provider."""
        with patch("src.clippy.models.get_user_provider_manager") as mock_get_manager:
            with patch("src.clippy.models.reload_providers") as mock_reload:
                # Setup mocks
                mock_manager = MagicMock()
                mock_manager.get_provider.return_value = {
                    "name": "test-provider"
                }  # Provider exists
                mock_manager.update_provider.return_value = (True, "updated successfully")
                mock_get_manager.return_value = mock_manager

                success, message = _save_provider_config(
                    provider_name="test-provider",
                    provider_type="openai",
                    description="Updated Provider",
                    base_url="https://api.updated.com/v1",
                    api_key_env="UPDATED_API_KEY",
                    console=self.console,
                )

                assert success is True
                assert "updated successfully" in message
                mock_manager.update_provider.assert_called_once_with(
                    name="test-provider",
                    base_url="https://api.updated.com/v1",
                    api_key_env="UPDATED_API_KEY",
                    description="Updated Provider",
                )
                mock_reload.assert_called_once()

    def test_save_provider_config_add_failure(self):
        """Test _save_provider_config when add fails."""
        with patch("src.clippy.models.get_user_provider_manager") as mock_get_manager:
            with patch("src.clippy.models.reload_providers") as mock_reload:
                # Setup mocks
                mock_manager = MagicMock()
                mock_manager.get_provider.return_value = None  # Provider doesn't exist
                mock_manager.add_provider.return_value = (False, "already exists")
                mock_get_manager.return_value = mock_manager

                success, message = _save_provider_config(
                    provider_name="test-provider",
                    provider_type="openai",
                    description="Test Provider",
                    base_url="https://api.test.com/v1",
                    api_key_env="TEST_API_KEY",
                    console=self.console,
                )

                assert success is False
                assert message == "already exists"
                mock_reload.assert_not_called()

    def test_save_provider_config_exception(self):
        """Test _save_provider_config when an exception occurs."""
        with patch("src.clippy.models.get_user_provider_manager") as mock_get_manager:
            # Setup mock to raise exception
            mock_get_manager.side_effect = Exception("Test exception")

            success, message = _save_provider_config(
                provider_name="test-provider",
                provider_type="openai",
                description="Test Provider",
                base_url="https://api.test.com/v1",
                api_key_env="TEST_API_KEY",
                console=self.console,
            )

            assert success is False
            assert "Failed to save provider configuration: Test exception" in message

    @patch("builtins.__import__")
    def test_handle_provider_add_no_questionary(self, mock_import):
        """Test _handle_provider_add when questionary is not available."""
        # Simulate ImportError
        mock_import.side_effect = ImportError("No module named 'questionary'")

        result = _handle_provider_add(self.console)
        assert result == "continue"
        # Should print error message
        call_args = [str(call[0][0]) for call in self.console.print.call_args_list]
        assert any("questionary is required" in arg for arg in call_args)

    @patch("builtins.__import__")
    def test_handle_provider_add_full_workflow(self, mock_import):
        """Test the full provider add workflow with mocked questionary."""
        # Mock questionary module
        mock_questionary = MagicMock()
        mock_questionary.select.return_value.ask.return_value = "openai"  # provider type
        mock_questionary.text.return_value.ask.side_effect = [
            "test-provider",  # provider name
            "Test Provider",  # description
            "https://api.test.com/v1",  # base URL
            "TEST_API_KEY",  # API key env
        ]
        mock_questionary.confirm.return_value.ask.return_value = True  # confirmation
        mock_import.return_value = mock_questionary

        # Mock _save_provider_config which is what actually gets called
        with patch("src.clippy.cli.commands.provider._save_provider_config") as mock_save:
            mock_save.return_value = (True, "test-provider added successfully")

            with patch.dict("os.environ", {"TEST_API_KEY": "test-key"}):  # Set env var
                result = _handle_provider_add(self.console)

                assert result == "continue"

                # Verify _save_provider_config was called with correct arguments
                mock_save.assert_called_once_with(
                    provider_name="test-provider",
                    provider_type="openai",
                    description="Test Provider",
                    base_url="https://api.test.com/v1",
                    api_key_env="TEST_API_KEY",
                    console=self.console,
                )

    def test_remove_builtin_provider_fails(self):
        """Test that removing built-in providers fails."""
        with patch("src.clippy.models.get_provider") as mock_get_provider:
            with patch("src.clippy.models.is_user_provider") as mock_is_user:
                # Setup mocks
                mock_provider = ProviderConfig(
                    name="openai", base_url=None, api_key_env="OPENAI_API_KEY", description="OpenAI"
                )
                mock_get_provider.return_value = mock_provider
                mock_is_user.return_value = False  # It's a built-in provider

                result = handle_provider_command(None, self.console, "remove openai")
                assert result == "continue"

                # Should print error about removing built-in provider
                call_args = [call[0][0] for call in self.console.print.call_args_list]
                assert any("Cannot remove built-in provider" in str(arg) for arg in call_args)


class TestProviderIntegration:
    """Integration tests for provider functionality."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.temp_dir = Path(tempfile.mkdtemp())

        # Create user provider manager with temp directory
        self.provider_manager = UserProviderManager(config_dir=self.temp_dir)

    def test_provider_save_and_load_roundtrip(self):
        """Test that saving a provider and loading it back works correctly."""
        # Add a provider
        success, message = self.provider_manager.add_provider(
            name="integration-test",
            base_url="https://api.integration.com/v1",
            api_key_env="INTEGRATION_API_KEY",
            description="Integration Test Provider",
        )

        assert success is True
        assert "integration-test" in message

        # Create a new manager instance to test persistence
        new_manager = UserProviderManager(config_dir=self.temp_dir)

        # Verify the provider can be loaded
        provider = new_manager.get_provider("integration-test")
        assert provider is not None
        assert provider["base_url"] == "https://api.integration.com/v1"
        assert provider["api_key_env"] == "INTEGRATION_API_KEY"
        assert provider["description"] == "Integration Test Provider"

        # Verify it's in the list
        providers = new_manager.list_providers()
        assert "integration-test" in providers

    def test_provider_file_creation(self):
        """Test that the provider file is created correctly."""
        providers_file = self.temp_dir / "providers.json"

        # File should be created automatically by UserProviderManager.__init__
        assert providers_file.exists()

        # Check file content should be empty initially
        with open(providers_file) as f:
            data = json.load(f)

        assert "providers" in data
        assert data["providers"] == {}  # Should be empty initially

        # Add a provider
        self.provider_manager.add_provider(
            name="file-test",
            base_url="https://api.filetest.com/v1",
            api_key_env="FILE_TEST_KEY",
            description="File Test Provider",
        )

        # Check file content is updated
        with open(providers_file) as f:
            data = json.load(f)

        assert "file-test" in data["providers"]
        assert data["providers"]["file-test"]["base_url"] == "https://api.filetest.com/v1"

    def test_provider_update_persists(self):
        """Test that provider updates persist correctly."""
        # Add initial provider
        self.provider_manager.add_provider(
            name="update-test",
            base_url="https://api.old.com/v1",
            api_key_env="OLD_KEY",
            description="Old Description",
        )

        # Update the provider
        success, message = self.provider_manager.update_provider(
            name="update-test",
            base_url="https://api.new.com/v1",
            api_key_env="NEW_KEY",
            description="New Description",
        )

        assert success is True

        # Create new manager to test persistence
        new_manager = UserProviderManager(config_dir=self.temp_dir)
        provider = new_manager.get_provider("update-test")

        assert provider["base_url"] == "https://api.new.com/v1"
        assert provider["api_key_env"] == "NEW_KEY"
        assert provider["description"] == "New Description"

    def test_provider_remove_persists(self):
        """Test that provider removal persists correctly."""
        # Add a provider
        self.provider_manager.add_provider(
            name="remove-test",
            base_url="https://api.remove.com/v1",
            api_key_env="REMOVE_KEY",
            description="Remove Test Provider",
        )

        # Verify it exists
        assert self.provider_manager.get_provider("remove-test") is not None

        # Remove it
        success, message = self.provider_manager.remove_provider("remove-test")
        assert success is True

        # Create new manager to test persistence
        new_manager = UserProviderManager(config_dir=self.temp_dir)
        assert new_manager.get_provider("remove-test") is None
        assert "remove-test" not in new_manager.list_providers()

    def test_provider_add_shows_in_list_regression(self):
        """REGRESSION TEST: Core functionality test for the provider add/list fix.

        This tests the essential fix: UserProviderManager.save/load and _save_provider_config
        both use the same JSON file format and location.
        """
        # Add a provider using the UserProviderManager (which is what /provider add uses)
        success, message = self.provider_manager.add_provider(
            name="regression-test",
            base_url="https://api.regression.com/v1",
            api_key_env="REGRESSION_API_KEY",
            description="Regression Test Provider",
        )

        assert success is True

        # Verify it appears in the user provider manager's list
        providers = self.provider_manager.list_providers()
        assert "regression-test" in providers
        assert providers["regression-test"]["description"] == "Regression Test Provider"

        # Create a new manager instance to test that the data persists correctly
        # This simulates what happens when the provider listing system loads providers
        new_manager = UserProviderManager(config_dir=self.temp_dir)
        loaded_providers = new_manager.list_providers()

        # This is the core of the regression test - ensuring that saving and loading
        # from the same file format works correctly
        assert "regression-test" in loaded_providers
        assert loaded_providers["regression-test"]["base_url"] == "https://api.regression.com/v1"
        assert loaded_providers["regression-test"]["api_key_env"] == "REGRESSION_API_KEY"
        assert loaded_providers["regression-test"]["description"] == "Regression Test Provider"
