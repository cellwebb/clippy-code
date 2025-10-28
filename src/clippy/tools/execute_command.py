"""Execute command tool implementation."""

import subprocess
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_command",
        "description": "Execute a shell command. Use with caution.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell command to execute"},
                "working_dir": {
                    "type": "string",
                    "description": (
                        "The working directory for the command. Defaults to current directory."
                    ),
                },
                "timeout": {
                    "type": "integer",
                    "description": (
                        "Timeout in seconds. Defaults to 300 (5 minutes). Set to 0 for no timeout."
                    ),
                    "default": 300,
                },
            },
            "required": ["command"],
        },
    },
}


def execute_command(cmd: str, working_dir: str = ".", timeout: int = 300) -> tuple[bool, str, Any]:
    """Execute a shell command."""
    try:
        # Add safety check for directory traversal
        if ".." in working_dir:
            return False, "Directory traversal not allowed in working_dir", None

        # Handle timeout value
        timeout_arg = None if timeout == 0 else timeout

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=timeout_arg,
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return True, "Command executed successfully", output
        else:
            return False, f"Command failed with return code {result.returncode}", output
    except subprocess.TimeoutExpired:
        if timeout == 0:
            timeout_msg = "unlimited"
        else:
            timeout_msg = f"{timeout} seconds"
        return False, f"Command timed out after {timeout_msg}", None
    except Exception as e:
        return False, f"Failed to execute command: {str(e)}", None
