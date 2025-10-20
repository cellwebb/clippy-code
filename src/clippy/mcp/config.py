"""MCP configuration loading and validation."""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import BaseModel


class ServerConfig(BaseModel):
    """Configuration for an MCP server."""

    command: str
    args: list[str]
    env: dict[str, str] | None = None
    cwd: str | None = None
    timeout_s: int = 30


class Config(BaseModel):
    """MCP configuration containing server definitions."""

    mcp_servers: dict[str, ServerConfig]


def load_config(path: str | None = None) -> Config | None:
    """
    Load MCP configuration from JSON file.

    Args:
        path: Optional path to config file. If None, will search standard locations.

    Returns:
        Config object or None if no config found
    """
    config_paths = []

    # If path is specified, use that
    if path:
        config_paths.append(Path(path))
    else:
        # Search standard locations - user config takes priority over project configs
        config_paths.extend(
            [
                Path.home() / ".clippy" / "mcp.json",  # User config (priority)
                Path.cwd() / ".clippy" / "mcp.json",  # Project subdirectory
            ]
        )

    # Try each path
    for config_path in config_paths:
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)

                # Resolve environment variables in the configuration
                resolved_data = _resolve_env_variables(data)

                return Config(**resolved_data)
            except Exception:
                # If we have an explicit path and it fails, raise the error
                if path:
                    raise
                # Otherwise, continue to next path
                continue

    # No config found
    return None


def _resolve_env_variables(data: dict[str, Any]) -> dict[str, Any]:
    """
    Recursively resolve environment variable placeholders in configuration data.

    Args:
        data: Configuration data with potential env var placeholders

    Returns:
        Configuration data with resolved env vars
    """
    if isinstance(data, dict):
        return {k: _resolve_env_variables(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_resolve_env_variables(item) for item in data]
    elif isinstance(data, str):
        # Resolve ${VAR} placeholders
        import re

        pattern = r"\$\{([^}]+)\}"

        def replace_var(match):
            env_var = match.group(1)
            return os.getenv(env_var, match.group(0))  # Return original if not found

        return re.sub(pattern, replace_var, data)
    else:
        return data
