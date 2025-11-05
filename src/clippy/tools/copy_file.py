"""Copy file tool implementation."""

import hashlib
import shutil
from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "copy_file",
        "description": (
            "Copy files and directories recursively with validation and progress tracking. "
            "Preserves permissions when possible, supports checksum verification, "
            "and handles conflicts intelligently. Perfect for backups and "
            "duplicating project structures."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "source": {
                    "type": "string",
                    "description": "The source file or directory path to copy",
                },
                "destination": {
                    "type": "string",
                    "description": "The destination path where the file/directory should be copied",
                },
                "recursive": {
                    "type": "boolean",
                    "description": "Copy directories recursively (required for directories)",
                    "default": True,
                },
                "preserve_permissions": {
                    "type": "boolean",
                    "description": "Attempt to preserve file permissions and metadata",
                    "default": True,
                },
                "verify_checksum": {
                    "type": "boolean",
                    "description": (
                        "Verify copy integrity using checksum (slower but more reliable)"
                    ),
                    "default": False,
                },
                "overwrite": {
                    "type": "boolean",
                    "description": "Overwrite existing files in destination",
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


def copy_file(
    source: str,
    destination: str,
    recursive: bool = True,
    preserve_permissions: bool = True,
    verify_checksum: bool = False,
    overwrite: bool = False,
    create_parents: bool = True,
) -> tuple[bool, str, Any]:
    """
    Copy a file or directory with comprehensive validation and optional verification.

    Args:
        source: Source file or directory path
        destination: Destination path
        recursive: Copy directories recursively
        preserve_permissions: Preserve file permissions and metadata
        verify_checksum: Verify copy integrity with checksum
        overwrite: Overwrite existing destination files
        create_parents: Create parent directories if needed

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

        # Handle directory copying
        if source_path.is_dir():
            if not recursive:
                return False, "Source is a directory. Use recursive=True to copy directories.", None

            # Check if destination exists and is not a directory
            if dest_path.exists() and not dest_path.is_dir():
                return False, f"Cannot copy directory {source} to file {destination}", None

            # Copy directory
            try:
                copy_with_progress(source_path, dest_path, overwrite, preserve_permissions)
            except Exception as e:
                return False, f"Failed to copy directory: {str(e)}", None

        else:
            # Handle file copying
            if dest_path.exists() and dest_path.is_dir():
                # Copy file into directory
                dest_path = dest_path / source_path.name

            # Copy the file
            try:
                if preserve_permissions:
                    shutil.copy2(str(source_path), str(dest_path))
                else:
                    shutil.copy(str(source_path), str(dest_path))
            except Exception as e:
                return False, f"Failed to copy file: {str(e)}", None

        # Verify the copy was successful
        if not dest_path.exists():
            return False, f"Copy operation completed but destination not found: {destination}", None

        # Optional checksum verification
        if verify_checksum:
            source_checksum = calculate_checksum(source_path)
            dest_checksum = calculate_checksum(dest_path)
            if source_checksum != dest_checksum:
                return (
                    False,
                    f"Copy verification failed: checksum mismatch between {source} "
                    f"and {destination}",
                    None,
                )

        # Get information about what was copied
        copy_info = {
            "path": str(dest_path.absolute()),
            "type": "directory" if dest_path.is_dir() else "file",
            "size": get_total_size(dest_path) if dest_path.exists() else 0,
            "verified": verify_checksum if source_path.is_file() else "directories not verified",
        }

        action = "copied" if source_path.is_file() else "copied recursively"
        return True, f"Successfully {action} {source} to {destination}", copy_info

    except PermissionError:
        return False, f"Permission denied when copying {source} to {destination}", None
    except OSError as e:
        return False, f"Filesystem error copying {source} to {destination}: {str(e)}", None
    except Exception as e:
        return False, f"Unexpected error copying {source} to {destination}: {str(e)}", None


def copy_with_progress(
    source: Path, dest: Path, overwrite: bool, preserve_permissions: bool
) -> None:
    """Copy directory with progress tracking."""
    if dest.exists():
        if not overwrite:
            raise FileExistsError(f"Destination directory already exists: {dest}")
    else:
        dest.mkdir(parents=True, exist_ok=True)
        # Copy directory permissions if preservation is requested
        if preserve_permissions:
            shutil.copystat(str(source), str(dest))

    for item in source.rglob("*"):
        if item.is_file():
            relative_path = item.relative_to(source)
            dest_file = dest / relative_path

            # Create parent directories for nested files
            dest_file.parent.mkdir(parents=True, exist_ok=True)

            # Copy the file
            if preserve_permissions:
                shutil.copy2(str(item), str(dest_file))
            else:
                shutil.copy(str(item), str(dest_file))
        elif item.is_dir():
            relative_path = item.relative_to(source)
            dest_dir = dest / relative_path
            dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy final directory stats
    if preserve_permissions:
        try:
            shutil.copystat(str(source), str(dest))
        except Exception:
            pass  # Skip if stat copy fails


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    hash_sha256 = hashlib.sha256()

    if file_path.is_file():
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()
    elif file_path.is_dir():
        # For directories, calculate checksum of all files
        file_checksums = []
        for file_path in sorted(file_path.rglob("*")):
            if file_path.is_file():
                with open(file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_sha256.update(chunk)
                file_checksums.append(hash_sha256.hexdigest())

        # Combine all file checksums
        combined = hashlib.sha256("".join(sorted(file_checksums)).encode())
        return combined.hexdigest()

    return ""


def get_total_size(path: Path) -> int:
    """Get total size of a file or directory."""
    if path.is_file():
        return path.stat().st_size
    elif path.is_dir():
        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                total += item.stat().st_size
        return total
    return 0


def validate_copy_operation(source: str, destination: str) -> dict[str, Any]:
    """
    Validate a copy operation before execution.

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
    result["info"]["source_size"] = get_total_size(source_path)

    # Check if destination exists
    if dest_path.exists():
        if dest_path.is_file() and source_path.is_dir():
            result["valid"] = False
            result["errors"].append("Cannot copy directory to existing file")
        elif dest_path.is_dir() and source_path.is_file():
            result["warnings"].append(f"File will be copied into directory: {destination}")

    # Estimate disk space requirements
    source_size = get_total_size(source_path)
    if source_size > 1024 * 1024 * 100:  # 100MB
        size_mb = source_size / (1024 * 1024)
        result["warnings"].append(f"Large copy operation: {size_mb:.1f}MB")

    return result
