"""Search files tool implementation."""

import os
from glob import glob
from typing import Any


def search_files(pattern: str, path: str = ".") -> tuple[bool, str, Any]:
    """Search for files matching a pattern."""
    try:
        # Use glob.glob to find files matching the pattern
        matches = glob(os.path.join(path, pattern), recursive=True)
        if matches:
            # Sort matches for consistent output
            matches.sort()
            result = "\n".join(matches)
            return True, f"Found {len(matches)} matches", result
        else:
            return True, "No matches found", ""
    except Exception as e:
        return False, f"Failed to search files: {str(e)}", None
