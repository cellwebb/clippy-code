"""Write file tool implementation."""

from pathlib import Path
from typing import Any


def write_file(path: str, content: str) -> tuple[bool, str, Any]:
    """Write to a file."""
    # Use direct file I/O to avoid any event loop issues in async contexts (like document mode)
    # This is simpler and more reliable than using tempfile, which can have issues
    # when called from worker threads in an async application
    try:
        # Validate Python syntax if it's a Python file
        from ..agent.utils import validate_python_syntax

        is_valid, error_msg = validate_python_syntax(content, path)
        if not is_valid:
            return False, error_msg, None

        # Create parent directories if needed
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Write file directly
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return True, f"Successfully wrote to {path}", None
    except PermissionError:
        return False, f"Permission denied when writing: {path}", None
    except OSError as e:
        return False, f"OS error when writing {path}: {str(e)}", None
    except Exception as e:
        return False, f"Failed to write to {path}: {str(e)}", None
