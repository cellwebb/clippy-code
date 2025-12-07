"""Tests for auto mode functionality."""

from clippy.agent.auto_mode import (
    AutoModeConfig,
    check_auto_mode_dependencies,
    get_auto_mode_config,
)


class TestCheckAutoModeDependencies:
    """Test dependency checking for auto mode."""

    def test_check_auto_mode_dependencies_returns_list(self):
        """Test that the function returns a list."""
        result = check_auto_mode_dependencies()
        assert isinstance(result, list)

    def test_check_auto_mode_dependencies_currently_empty(self):
        """Test that currently all dependencies are available (returns empty list)."""
        result = check_auto_mode_dependencies()
        assert result == []


class TestGetAutoModeConfig:
    """Test getting auto mode configuration."""

    def test_get_auto_mode_config_returns_config(self):
        """Test that get_auto_mode_config returns an AutoModeConfig instance."""
        config = get_auto_mode_config()
        assert isinstance(config, AutoModeConfig)

    def test_get_auto_mode_config_default_enabled_false(self):
        """Test that default config has enabled=False."""
        config = get_auto_mode_config()
        assert config.enabled is False


class TestAutoModeConfig:
    """Test AutoModeConfig class."""

    def test_auto_mode_config_init_default(self):
        """Test AutoModeConfig initialization with default values."""
        config = AutoModeConfig()
        assert config.enabled is False

    def test_auto_mode_config_init_enabled_true(self):
        """Test AutoModeConfig initialization with enabled=True."""
        config = AutoModeConfig(enabled=True)
        assert config.enabled is True

    def test_auto_mode_config_init_enabled_false(self):
        """Test AutoModeConfig initialization with enabled=False."""
        config = AutoModeConfig(enabled=False)
        assert config.enabled is False

    def test_auto_mode_config_attributes(self):
        """Test that AutoModeConfig has expected attributes."""
        config = AutoModeConfig()
        assert hasattr(config, "enabled")
        assert isinstance(config.enabled, bool)

    def test_auto_mode_config_mutable(self):
        """Test that AutoModeConfig attributes can be modified."""
        config = AutoModeConfig(enabled=False)
        assert config.enabled is False

        # Modify the attribute
        config.enabled = True
        assert config.enabled is True

        # Modify back
        config.enabled = False
        assert config.enabled is False


class TestModuleExports:
    """Test that module exports are correctly defined."""

    def test_module_all_attribute(self):
        """Test __all__ attribute contains expected exports."""
        from clippy.agent import auto_mode

        expected_exports = [
            "check_auto_mode_dependencies",
            "get_auto_mode_config",
            "AutoModeConfig",
        ]

        assert hasattr(auto_mode, "__all__")
        assert set(auto_mode.__all__) == set(expected_exports)

    def test_exported_functions_are_importable(self):
        """Test that exported functions can be imported from the module."""
        from clippy.agent.auto_mode import (
            check_auto_mode_dependencies,
            get_auto_mode_config,
        )

        # Test they are callable
        assert callable(check_auto_mode_dependencies)
        assert callable(get_auto_mode_config)

    def test_exported_class_is_importable(self):
        """Test that exported class can be imported from the module."""
        from clippy.agent.auto_mode import AutoModeConfig

        # Test it's a class
        assert isinstance(AutoModeConfig, type)

        # Test it can be instantiated
        instance = AutoModeConfig()
        assert isinstance(instance, AutoModeConfig)
        assert instance.enabled is False
