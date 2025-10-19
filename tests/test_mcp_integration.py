"""Integration tests for MCP functionality."""

import json
import os
import tempfile

from clippy.mcp.config import Config, ServerConfig, load_config


def test_load_config_no_file() -> None:
    """Test that load_config returns None when no config file is found."""
    # Test with a path that doesn't exist
    config = load_config("/nonexistent/path/mcp.json")
    assert config is None


def test_load_config_with_env_vars() -> None:
    """Test that load_config resolves environment variables in the configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "mcp.json")

        # Create a config with environment variable placeholders
        config_data = {
            "mcp_servers": {
                "test-server": {
                    "command": "echo",
                    "args": ["${TEST_API_KEY}", "arg2"],
                    "env": {"API_KEY": "${TEST_API_KEY}"},
                }
            }
        }

        with open(config_path, "w") as f:
            json.dump(config_data, f)

        # Set environment variable
        os.environ["TEST_API_KEY"] = "test-secret"

        try:
            # Load config
            config = load_config(config_path)
            assert config is not None
            assert "test-server" in config.mcp_servers

            server_config = config.mcp_servers["test-server"]
            # Check that env vars are resolved in args
            assert "test-secret" in server_config.args
            # Check that env vars are resolved in env dict
            assert server_config.env is not None
            assert "test-secret" in server_config.env["API_KEY"]
        finally:
            # Clean up environment variable
            if "TEST_API_KEY" in os.environ:
                del os.environ["TEST_API_KEY"]


def test_config_validation() -> None:
    """Test that Config properly validates server configurations."""
    server_configs = {
        "server1": ServerConfig(
            command="echo", args=["hello"], env={"KEY": "VALUE"}, cwd="/tmp", timeout_s=30
        )
    }

    config = Config(mcp_servers=server_configs)
    assert "server1" in config.mcp_servers
    assert config.mcp_servers["server1"].command == "echo"
    assert config.mcp_servers["server1"].args == ["hello"]
    assert config.mcp_servers["server1"].env == {"KEY": "VALUE"}
    assert config.mcp_servers["server1"].cwd == "/tmp"
    assert config.mcp_servers["server1"].timeout_s == 30
