"""Read file tool implementation."""

from typing import Any


def read_file(path: str) -> tuple[bool, str, Any]:
    """Read a file."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
        return True, f"Successfully read {path}", content
    except FileNotFoundError:
        return False, f"File not found: {path}", None
    except PermissionError:
        return False, f"Permission denied when reading: {path}", None
    except UnicodeDecodeError:
        return False, f"Unable to decode file (might be binary): {path}", None
    except Exception as e:
        return False, f"Failed to read {path}: {str(e)}", None
