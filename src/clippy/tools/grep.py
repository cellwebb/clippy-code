"""Grep tool implementation."""

import shlex
import subprocess
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "grep",
        "description": (
            "Search for patterns in files using grep. "
            "This is a safe read-only operation that requires no approval."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "The pattern to search for in files",
                },
                "path": {
                    "type": "string",
                    "description": "A single file path or glob pattern to search in",
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Multiple file paths or glob patterns to search in",
                },
                "flags": {
                    "type": "string",
                    "description": "Optional flags for grep command (e.g., '-i', '-r', etc.)",
                },
            },
            "required": ["pattern"],
        },
    },
}


def translate_grep_flags_to_rg(flags: str) -> str:
    """
    Translate common grep flags to their ripgrep equivalents.

    Args:
        flags: String of grep flags

    Returns:
        String of translated ripgrep flags
    """
    # Mapping of grep flags to ripgrep equivalents
    # Note: ripgrep searches recursively by default, so -r/--recursive flags are ignored
    flag_mapping = {
        # Basic matching
        "-i": "--ignore-case",
        "--ignore-case": "--ignore-case",
        "-v": "--invert-match",
        "--invert-match": "--invert-match",
        "-w": "--word-regexp",
        "--word-regexp": "--word-regexp",
        "-x": "--line-regexp",
        "--line-regexp": "--line-regexp",
        # Output control
        "-n": "--line-number",
        "--line-number": "--line-number",
        "-H": "--with-filename",
        "--with-filename": "--with-filename",
        "-h": "--no-filename",
        "--no-filename": "--no-filename",
        "-o": "--only-matching",
        "--only-matching": "--only-matching",
        "-q": "--quiet",
        "--quiet": "--quiet",
        # File inclusion/exclusion
        "-r": None,  # ripgrep searches recursively by default
        "--recursive": None,  # ripgrep searches recursively by default
        "-L": "--files-without-match",
        "--files-without-match": "--files-without-match",
        "--include": "--glob",
        "--exclude": "--glob",
        # Context control
        "-A": "--after-context",
        "--after-context": "--after-context",
        "-B": "--before-context",
        "--before-context": "--before-context",
        "-C": "--context",
        "--context": "--context",
    }

    # Split flags into individual components
    flag_list = shlex.split(flags)
    translated_flags = []
    i = 0

    while i < len(flag_list):
        flag = flag_list[i]

        # Handle flags that require arguments
        if flag in ["-A", "--after-context", "-B", "--before-context", "-C", "--context"]:
            rg_flag = flag_mapping.get(flag, flag)
            # Skip None values (flags that don't apply to ripgrep)
            if rg_flag is not None:
                translated_flags.append(rg_flag)
                # Add the argument for context flags
                if i + 1 < len(flag_list):
                    translated_flags.append(flag_list[i + 1])
                    i += 2
                else:
                    i += 1
                continue

        # Handle --include and --exclude patterns
        if flag == "--include":
            if i + 1 < len(flag_list):
                translated_flags.append("--glob")
                translated_flags.append(flag_list[i + 1])
                i += 2
            else:
                i += 1
            continue
        elif flag == "--exclude":
            if i + 1 < len(flag_list):
                translated_flags.append("--glob")
                translated_flags.append(f"!{flag_list[i + 1]}")
                i += 2
            else:
                i += 1
            continue

        # Direct mapping for other flags
        if flag in flag_mapping:
            rg_flag = flag_mapping[flag]
            # Skip None values (flags that don't apply to ripgrep)
            if rg_flag is not None:
                translated_flags.append(rg_flag)
        else:
            # Keep unknown flags as-is (might be ripgrep-specific)
            translated_flags.append(flag)

        i += 1

    return " ".join(translated_flags)


def grep(pattern: str, paths: list[str], flags: str = "") -> tuple[bool, str, Any]:
    """Search for pattern in files using grep or ripgrep."""
    try:
        # Check if ripgrep is available
        use_rg = False
        try:
            subprocess.run(["rg", "--version"], capture_output=True, check=True)
            use_rg = True
        except (subprocess.CalledProcessError, FileNotFoundError):
            # ripgrep not available, fall back to grep
            pass

        if use_rg:
            # Use ripgrep with file names included
            # Add default flags to skip binary files and show line numbers and file names
            rg_flags = ["--no-heading", "--line-number", "-I", "--with-filename"]

            # Translate grep flags to ripgrep flags
            if flags:
                translated_flags = translate_grep_flags_to_rg(flags)
                rg_flags.append(translated_flags)

            # Build command - paths with glob patterns should not be quoted to allow shell expansion
            # Add -- to separate flags from pattern (prevents pattern starting with -
            # being interpreted as flag)
            cmd_parts = ["rg"] + rg_flags + ["--", shlex.quote(pattern)]
            for path in paths:
                # Check if path contains glob patterns
                if "*" in path or "?" in path or "[" in path:
                    # Don't quote glob patterns to allow shell expansion
                    cmd_parts.append(path)
                else:
                    # Quote regular paths for safety
                    cmd_parts.append(shlex.quote(path))

            cmd = " ".join(cmd_parts)

            result = subprocess.run(
                cmd,
                shell=True,  # Allow shell expansion of glob patterns
                capture_output=True,
                text=True,
                timeout=30,
            )
        else:
            # Use standard grep - it includes file names when searching multiple files
            # Always add flags to skip binary files and show line numbers
            grep_flags_list = ["-I", "-n"]
            if flags:
                # Split and rejoin to ensure proper spacing
                flag_list = shlex.split(flags)
                grep_flags_list.extend(flag_list)

            # Build command - paths with glob patterns should not be quoted to allow shell expansion
            # Add -- to separate flags from pattern (prevents pattern starting with -
            # being interpreted as flag)
            cmd_parts = ["grep"] + grep_flags_list + ["--", shlex.quote(pattern)]
            for path in paths:
                # Check if path contains glob patterns
                if "*" in path or "?" in path or "[" in path:
                    # Don't quote glob patterns to allow shell expansion
                    cmd_parts.append(path)
                else:
                    # Quote regular paths for safety
                    cmd_parts.append(shlex.quote(path))

            cmd = " ".join(cmd_parts)

            result = subprocess.run(
                cmd,
                shell=True,  # Allow shell expansion of glob patterns
                capture_output=True,
                text=True,
                timeout=30,
            )

        output = result.stdout if result.returncode == 0 or result.stdout else result.stderr

        if result.returncode == 0:  # Found matches
            return True, "grep search executed successfully", output
        elif result.returncode == 1:  # No matches found (not an error)
            return True, "grep search completed (no matches found)", ""
        else:  # Actual error occurred
            return False, f"Error in grep/rg command: {output}", None

    except subprocess.TimeoutExpired:
        return False, "Search timed out after 30 seconds", None
    except Exception as e:
        return False, f"Failed to execute grep: {str(e)}", None
