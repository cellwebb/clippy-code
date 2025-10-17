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
                    "description": "The working directory for the command. Defaults to current directory.",
                },
            },
            "required": ["command"],
        },
    },
}


def execute_command(cmd: str, working_dir: str = ".") -> tuple[bool, str, Any]:
    """Execute a shell command."""
    try:
        # Add safety check for directory traversal
        if ".." in working_dir:
            return False, "Directory traversal not allowed in working_dir", None

        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=30,
        )
        output = result.stdout + result.stderr
        if result.returncode == 0:
            return True, "Command executed successfully", output
        else:
            return False, f"Command failed with return code {result.returncode}", output
    except subprocess.TimeoutExpired:
        return False, "Command timed out after 30 seconds", None
    except Exception as e:
        return False, f"Failed to execute command: {str(e)}", None
