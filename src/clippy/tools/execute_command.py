"""Execute command tool implementation."""

import re
import shlex
import subprocess
from re import Pattern
from typing import Any

# Execution constants
DEFAULT_COMMAND_TIMEOUT = 300  # 5 minutes in seconds

# Dangerous command patterns - both literal strings and regex patterns
DANGEROUS_LITERAL_PATTERNS = [
    ":(){ :|:& };:",  # Fork bomb
    ":(){ :|: & };:",  # Fork bomb variant
]

# Regex patterns for dangerous commands
# These catch variations that literal matching would miss
DANGEROUS_REGEX_PATTERNS = [
    # rm -rf / or rm -fr / with various spacing and flags
    r"\brm\s+(-[rRfF]+\s+)+/\s*$",
    r"\brm\s+(-[rRfF]+\s+)+/[^/]",  # rm -rf /etc, etc.
    # mkfs commands
    r"\bmkfs\b",
    # dd writing to block devices
    r"\bdd\b.*\bof=/dev/[sh]d",
    r"\bdd\b.*\bif=/dev/(zero|random|urandom).*\bof=/",
    # Dangerous curl/wget pipes
    r"\b(curl|wget)\b.+\|\s*(sudo\s+)?(ba)?sh",
    # chmod 777 on root
    r"\bchmod\s+(-[rR]+\s+)?777\s+/\s*$",
    # Overwriting important system files
    r">\s*/etc/(passwd|shadow|sudoers)",
    r">\s*/dev/[sh]d[a-z]",
]

# Compile regex patterns for efficiency
_compiled_dangerous_patterns: list[Pattern[str]] = [re.compile(p) for p in DANGEROUS_REGEX_PATTERNS]

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
                "show_output": {
                    "type": "boolean",
                    "description": (
                        "Whether to display the command output. Defaults to false. "
                        "Can be controlled globally with CLIPPY_SHOW_COMMAND_OUTPUT "
                        "environment variable."
                    ),
                    "default": False,
                },
            },
            "required": ["command"],
        },
    },
}


def _is_dangerous_command(cmd: str) -> tuple[bool, str]:
    """Check if a command matches any dangerous patterns.

    Args:
        cmd: Command string to check

    Returns:
        Tuple of (is_dangerous, matched_pattern_description)
    """
    # Check literal patterns first (exact substring match)
    for literal in DANGEROUS_LITERAL_PATTERNS:
        if literal in cmd:
            return True, f"literal pattern: {literal}"

    # Check regex patterns
    for regex in _compiled_dangerous_patterns:
        if regex.search(cmd):
            return True, f"regex pattern: {regex.pattern}"

    return False, ""


def execute_command(
    cmd: str,
    working_dir: str = ".",
    timeout: int = DEFAULT_COMMAND_TIMEOUT,
    show_output: bool = False,
) -> tuple[bool, str, Any]:
    """Execute a shell command.

    Security notes:
    - Commands are executed with shell=True to support pipes, redirects, etc.
    - Dangerous patterns are blocked (rm -rf /, fork bombs, etc.)
    - Directory traversal in working_dir is blocked
    - Commands run with the user's permissions (no privilege escalation)

    Args:
        cmd: Command string to execute
        working_dir: Working directory for command execution
        timeout: Command timeout in seconds (0 for no timeout)
        show_output: Whether to display command output in the result

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    try:
        # Validate command syntax with shlex (catches unterminated quotes, etc.)
        try:
            shlex.split(cmd)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}", None

        # Add safety check for directory traversal
        if ".." in working_dir:
            return False, "Directory traversal not allowed in working_dir", None

        # Safety check for dangerous commands using enhanced pattern matching
        is_dangerous, matched = _is_dangerous_command(cmd)
        if is_dangerous:
            return False, f"Command blocked by security filter ({matched})", None

        # Handle timeout value
        timeout_arg = None if timeout == 0 else timeout

        # Parse command safely to avoid shell injection
        try:
            args = shlex.split(cmd)
        except ValueError as e:
            return False, f"Invalid command syntax: {e}", None

        result = subprocess.run(
            args,
            shell=False,  # SECURE: Use exec mode instead of shell
            capture_output=True,
            text=True,
            cwd=working_dir,
            timeout=timeout_arg,
        )
        output = result.stdout + result.stderr

        # Hide output if requested
        if not show_output:
            output = "[Output hidden by setting]"

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
    except (OSError, subprocess.SubprocessError) as e:
        return False, f"Failed to execute command: {str(e)}", None
