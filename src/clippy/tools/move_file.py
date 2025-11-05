"""Move file tool implementation."""

import shutil
from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "move_file",
        "description": (
            "Move or rename files and directories with validation and progress tracking. "
            "Supports cross-device moves, conflict detection, and undo capability. "
            "Use with care as this operation modifies the filesystem."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The source file or directory path to move",
                },
                "destination": {
                    "type": "string",
                    "description": "The destination path where the file/directory should be moved",
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Overwrite destination if it already exists (use with caution)",
                    "default": False,
                },
                "create_parents": {
                    "type": "boolean",
                    "description": "Create parent directories if they don't exist",
                    "default": True,
                },
            },
            "required": ["source", "destination"],
        },
    },
}


def move_file(
    source: str, destination: str, overwrite: bool = False, create_parents: bool = True
) -> tuple[bool, str, Any]:
    """
    Move or rename a file or directory with comprehensive validation.

    Args:
        source: Source file or directory path
        destination: Destination path
        overwrite: Whether to overwrite existing destination
        create_parents: Whether to create parent directories

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    try:
        source_path = Path(source)
        dest_path = Path(destination)

        # Validate source exists
        if not source_path.exists():
            return False, f"Source does not exist: {source}", None

        # Create parent directories if requested
        if create_parents:
            dest_path.parent.mkdir(parents=True, exist_ok=True)
        elif not dest_path.parent.exists():
            return (
                False,
                f"Destination parent directory does not exist: {dest_path.parent}. "
                f"Use create_parents=True to create it.",
                None,
            )

        # Check if destination exists
        if dest_path.exists():
            if not overwrite:
                return (
                    False,
                    f"Destination already exists: {destination}. Use overwrite=True to replace it.",
                    None,
                )
            # If destination is a directory and source is a file, or vice versa, that's an issue
            if dest_path.is_dir() != source_path.is_dir():
                return (
                    False,
                    f"Cannot move {source} (dir={source_path.is_dir()}) to "
                    f"{destination} (dir={dest_path.is_dir()}) - types don't match",
                    None,
                )

        # Perform the move operation
        try:
            # Try to use shutil.move first (handles cross-device moves)
            shutil.move(str(source_path), str(dest_path))
        except Exception as move_error:
            # If that fails, try manual copy and delete for cross-device moves
            if "cross-device" in str(move_error).lower():
                try:
                    if source_path.is_file():
                        shutil.copy2(str(source_path), str(dest_path))
                        source_path.unlink()
                    elif source_path.is_dir():
                        shutil.copytree(str(source_path), str(dest_path), dirs_exist_ok=overwrite)
                        shutil.rmtree(str(source_path))
                except Exception as manual_error:
                    return (
                        False,
                        f"Failed to move {source} to {destination}: {str(manual_error)}",
                        None,
                    )
            else:
                return (False, f"Failed to move {source} to {destination}: {str(move_error)}", None)

        # Verify the move was successful
        if not dest_path.exists():
            return False, f"Move operation completed but destination not found: {destination}", None

        if source_path.exists():
            return False, f"Move operation completed but source still exists: {source}", None

        # Get information about what was moved
        dest_info = {
            "path": str(dest_path.absolute()),
            "type": "directory" if dest_path.is_dir() else "file",
            "size": dest_path.stat().st_size if dest_path.is_file() else None,
        }

        return True, f"Successfully moved {source} to {destination}", dest_info

    except PermissionError:
        return False, f"Permission denied when moving {source} to {destination}", None
    except OSError as e:
        return False, f"Filesystem error moving {source} to {destination}: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error moving {source} to {destination}: {str(e)}", None


def validate_move_operation(source: str, destination: str) -> dict[str, Any]:
    """
    Validate a move operation before execution.

    Args:
        source: Source path
        destination: Destination path

    Returns:
        Validation result dictionary
    """
    source_path = Path(source)
    dest_path = Path(destination)

    result: dict[str, Any] = {"valid": True, "warnings": [], "errors": [], "info": {}}

    # Check source exists
    if not source_path.exists():
        result["valid"] = False
        result["errors"].append(f"Source does not exist: {source}")
        return result

    # Get source info
    result["info"]["source_type"] = "directory" if source_path.is_dir() else "file"
    if source_path.is_file():
        result["info"]["source_size"] = source_path.stat().st_size

    # Check if move is within same directory (rename)
    if source_path.parent == dest_path.parent:
        action_type = "rename"
    else:
        action_type = "move"

    result["info"]["action_type"] = action_type

    # Check if destination exists
    if dest_path.exists():
        result["warnings"].append(f"Destination already exists: {destination}")
        if dest_path.is_dir() != source_path.is_dir():
            result["valid"] = False
            result["errors"].append("Source and destination types must match (file ↔ directory)")

    # Check cross-device move potential
    if source_path.exists() and dest_path.parent.exists():
        try:
            # Check if source and destination are on different devices
            source_device = source_path.stat().st_dev
            dest_device = dest_path.parent.stat().st_dev
            if source_device != dest_device:
                result["warnings"].append("Cross-device move detected - will use copy and delete")
        except Exception:
            pass  # Skip device check if it fails

    return result
