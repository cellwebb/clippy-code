"""List directory tool implementation."""

import os
from typing import Any

import pathspec

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_directory",
        "description": "List the contents of a directory.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": (
                        "The path to the directory to list. Defaults to current directory."
                    ),
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Whether to list recursively. Defaults to false.",
                },
            },
            "required": ["path"],
        },
    },
}


def load_gitignore(directory: str) -> pathspec.PathSpec | None:
    """Load .gitignore patterns from a directory."""
    gitignore_path = os.path.join(directory, ".gitignore")
    if not os.path.exists(gitignore_path):
        return None

    try:
        with open(gitignore_path, encoding="utf-8") as f:
            patterns = f.read().splitlines()
        return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
    except Exception:
        return None


def list_directory(path: str, recursive: bool) -> tuple[bool, str, Any]:
    """List directory contents."""
    try:
        if not os.path.exists(path):
            return False, f"Directory not found: {path}", None

        if not os.path.isdir(path):
            return False, f"Path is not a directory: {path}", None

        if recursive:
            # Load .gitignore patterns
            gitignore_spec = load_gitignore(path)

            if not gitignore_spec:
                # If no .gitignore, walk normally and show all directories
                files = []
                directories = []
                for root, dirs, filenames in os.walk(path):
                    rel_root = os.path.relpath(root, path)
                    if rel_root == ".":
                        rel_root = ""

                    for filename in filenames:
                        if rel_root:
                            files.append(os.path.join(rel_root, filename))
                        else:
                            files.append(filename)

                    for dir_name in dirs:
                        dir_path = os.path.join(rel_root, dir_name) if rel_root else dir_name
                        directories.append(dir_path + "/")

                # Combine and sort all entries
                all_entries = files + directories
                all_entries.sort()
                result = "\n".join([entry for entry in all_entries if entry])
                return True, "Successfully listed directory contents (recursive)", result

            # Use pathspec's built-in tree walking which handles filtering properly
            files = []
            directories = []
            skipped_notes = []

            for root, dirs, filenames in os.walk(path):
                rel_root = os.path.relpath(root, path)
                if rel_root == ".":
                    rel_root = ""

                # Check each directory for gitignore filtering
                for dir_name in dirs:
                    dir_path = os.path.join(rel_root, dir_name) if rel_root else dir_name
                    # pathspec uses trailing slash for directory matching
                    if gitignore_spec.match_file(dir_path + "/"):
                        skipped_notes.append(f"[skipped {dir_path}/ due to .gitignore]")
                    else:
                        directories.append(dir_path + "/")

                # Check each file for gitignore filtering
                for filename in filenames:
                    file_path = os.path.join(rel_root, filename) if rel_root else filename
                    if not gitignore_spec.match_file(file_path):
                        files.append(file_path)

            # Combine all entries and sort
            all_entries = files + directories + skipped_notes
            all_entries.sort()

            # Filter out empty strings and join with newlines
            result = "\n".join([entry for entry in all_entries if entry])
            return True, "Successfully listed directory contents (recursive)", result
        else:
            entries = os.listdir(path)
            entries.sort()

            # Add trailing slash to directories
            formatted_entries = []
            for entry in entries:
                entry_path = os.path.join(path, entry)
                if os.path.isdir(entry_path):
                    formatted_entries.append(entry + "/")
                else:
                    formatted_entries.append(entry)

            result = "\n".join(formatted_entries)
            return True, "Successfully listed directory contents", result
    except PermissionError:
        return False, f"Permission denied when listing directory: {path}", None
    except Exception as e:
        return False, f"Failed to list directory {path}: {str(e)}", None
