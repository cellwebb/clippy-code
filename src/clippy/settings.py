"""Settings and configuration management for clippy-code."""

import os


class ClippySettings:
    """Centralized settings management for clippy-code."""

    def __init__(self) -> None:
        """Initialize settings with environment variable defaults."""
        self._show_command_output = self._get_bool_env("CLIPPY_SHOW_COMMAND_OUTPUT", False)
        self._command_timeout = self._get_int_env("CLIPPY_COMMAND_TIMEOUT", 300)
        self._max_tool_result_tokens = self._get_int_env("CLIPPY_MAX_TOOL_RESULT_TOKENS", 10000)

    def _get_bool_env(self, key: str, default: bool) -> bool:
        """Get a boolean environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Boolean value from environment
        """
        value = os.getenv(key, "").lower()
        if value in ("true", "1", "yes", "on", "enable"):
            return True
        elif value in ("false", "0", "no", "off", "disable"):
            return False
        return default

    def _get_int_env(self, key: str, default: int) -> int:
        """Get an integer environment variable.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Integer value from environment
        """
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    @property
    def show_command_output(self) -> bool:
        """Whether to show output from execute_command tool.

        Defaults to False (hides output) for a cleaner experience.
        Users can set CLIPPY_SHOW_COMMAND_OUTPUT=true to show output by default.

        Returns:
            True if command output should be displayed, False to hide it
        """
        return self._show_command_output

    @property
    def command_timeout(self) -> int:
        """Default timeout for command execution in seconds.

        Returns:
            Timeout in seconds
        """
        return self._command_timeout

    @property
    def max_tool_result_tokens(self) -> int:
        """Maximum number of tokens to allow in tool results.

        Returns:
            Maximum token count
        """
        return self._max_tool_result_tokens

    def reload(self) -> None:
        """Reload settings from environment variables.

        This is useful for settings that might change during a session.
        """
        self._show_command_output = self._get_bool_env("CLIPPY_SHOW_COMMAND_OUTPUT", True)
        self._command_timeout = self._get_int_env("CLIPPY_COMMAND_TIMEOUT", 300)
        self._max_tool_result_tokens = self._get_int_env("CLIPPY_MAX_TOOL_RESULT_TOKENS", 10000)


# Global settings instance
_global_settings: ClippySettings | None = None


def get_settings() -> ClippySettings:
    """Get the global settings instance.

    Returns:
        ClippySettings instance
    """
    global _global_settings
    if _global_settings is None:
        _global_settings = ClippySettings()
    return _global_settings


def reload_settings() -> None:
    """Reload the global settings instance.

    This creates a fresh settings instance and re-reads all environment
    variables. Use this when environment variables might have changed.
    """
    global _global_settings
    _global_settings = ClippySettings()


def reset_settings() -> None:
    """Reset the global settings instance to None.

    This is primarily useful for testing to ensure a clean state.
    """
    global _global_settings
    _global_settings = None
