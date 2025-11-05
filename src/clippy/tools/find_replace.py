"""Find and replace tool implementation."""

import difflib
import re
from pathlib import Path
from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "find_replace",
        "description": (
            "Multi-file pattern replacement with regex support, preview mode, and safety checks. "
            "Supports dry-run mode, file filtering, interactive confirmation, and generates diffs. "
            "Perfect for refactoring, updating imports, or making project-wide changes safely."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Pattern to search for (supports regex if regex=True)",
                },
                "replacement": {
                    "type": "string",
                    "description": (
                        "Replacement string (supports regex backreferences if regex=True)"
                    ),
                },
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of file paths or glob patterns to search in",
                },
                "regex": {
                    "type": "boolean",
                    "description": "Use regular expressions for pattern matching",
                    "default": False,
                },
                "case_sensitive": {
                    "type": "boolean",
                    "description": "Case sensitive matching",
                    "default": False,
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without modifying files (recommended first)",
                    "default": True,
                },
                "include_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File patterns to include (e.g., ['*.py', '*.js'])",
                    "default": ["*"],
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "File patterns to exclude (e.g., ['test_*.py', '*.min.js'])",
                    "default": [],
                },
                "max_file_size": {
                    "type": "integer",
                    "description": (
                        "Maximum file size in bytes to process (prevents processing large binaries)"
                    ),
                    "default": 10485760,  # 10MB
                },
                "backup": {
                    "type": "boolean",
                    "description": "Create backup files before modification",
                    "default": False,
                },
            },
            "required": ["pattern", "replacement", "paths"],
        },
    },
}


def find_replace(
    pattern: str,
    replacement: str,
    paths: list[str],
    regex: bool = False,
    case_sensitive: bool = False,
    dry_run: bool = True,
    include_patterns: list[str] = ["*"],
    exclude_patterns: list[str] = [],
    max_file_size: int = 10485760,
    backup: bool = False,
) -> tuple[bool, str, Any]:
    """
    Find and replace patterns in multiple files with comprehensive safety checks.

    Args:
        pattern: Pattern to search for
        replacement: Replacement string
        paths: List of file paths or glob patterns
        regex: Use regex patterns
        case_sensitive: Case sensitive matching
        dry_run: Preview without modifying files
        include_patterns: File patterns to include
        exclude_patterns: File patterns to exclude
        max_file_size: Maximum file size to process
        backup: Create backup files

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    try:
        # Collect all files to process
        files_to_process = collect_files(paths, include_patterns, exclude_patterns, max_file_size)

        if not files_to_process:
            return False, "No files found matching the specified patterns", None

        # Prepare pattern for matching
        compiled_pattern = prepare_pattern(pattern, regex, case_sensitive)

        if compiled_pattern is None:
            return False, "Invalid regular expression pattern", None

        # Process files
        results: list[dict[str, Any]] = []
        total_replacements = 0

        for file_path in files_to_process:
            file_result = process_file(
                file_path, compiled_pattern, replacement, regex, dry_run, backup
            )

            if file_result["changes_found"]:
                results.append(file_result)
                total_replacements += file_result["replacements_made"]

        # Generate summary
        summary = {
            "files_processed": len(files_to_process),
            "files_with_changes": len(results),
            "total_replacements": total_replacements,
            "dry_run": dry_run,
            "changes": results,
        }

        mode = "would make" if dry_run else "made"
        message = f"Find/replace {mode} {total_replacements} replacements in {len(results)} files"

        if dry_run and results:
            message += ". Use dry_run=False to apply changes."

        return True, message, summary

    except Exception as e:
        return False, f"Error during find/replace operation: {str(e)}", None


def collect_files(
    paths: list[str], include_patterns: list[str], exclude_patterns: list[str], max_file_size: int
) -> list[Path]:
    """Collect files to process based on paths and patterns."""
    files: list[Path] = []

    for path_pattern in paths:
        path_obj = Path(path_pattern)

        if path_obj.is_file():
            files.append(path_obj)
        elif path_obj.is_dir():
            # Search directory for matching files
            for include_pattern in include_patterns:
                for file_path in path_obj.rglob(include_pattern):
                    if file_path.is_file() and should_include_file(file_path, exclude_patterns):
                        if file_path.stat().st_size <= max_file_size:
                            files.append(file_path)
        else:
            # Treat as glob pattern
            matched_files = list(Path(".").glob(path_pattern))
            for file_path in matched_files:
                if file_path.is_file() and should_include_file(file_path, exclude_patterns):
                    if file_path.stat().st_size <= max_file_size:
                        files.append(file_path)

    # Remove duplicates
    return list(set(files))


def should_include_file(file_path: Path, exclude_patterns: list[str]) -> bool:
    """Check if file should be included based on exclude patterns."""
    file_str = str(file_path)

    for exclude_pattern in exclude_patterns:
        if file_path.match(exclude_pattern) or exclude_pattern in file_str:
            return False

    return True


def prepare_pattern(pattern: str, regex: bool, case_sensitive: bool) -> Any:
    """Prepare and compile the search pattern."""
    if regex:
        try:
            flags = 0 if case_sensitive else re.IGNORECASE
            return re.compile(pattern, flags)
        except re.error:
            return None
    else:
        # For literal string matching, we'll escape special regex chars
        escaped_pattern = re.escape(pattern)
        flags = 0 if case_sensitive else re.IGNORECASE
        return re.compile(escaped_pattern, flags)


def process_file(
    file_path: Path,
    pattern: re.Pattern[str],
    replacement: str,
    regex: bool,
    dry_run: bool,
    backup: bool,
) -> dict[str, Any]:
    """Process a single file for find/replace operations."""
    result: dict[str, Any] = {
        "file": str(file_path),
        "changes_found": False,
        "replacements_made": 0,
        "lines_changed": [],
        "backup_created": False,
        "diff": "",
    }

    try:
        # Read file content
        with open(file_path, encoding="utf-8") as f:
            original_content = f.read()

        # Check if pattern exists in file
        if not pattern.search(original_content):
            return result

        # Create backup if needed
        if not dry_run and backup:
            backup_path = file_path.with_suffix(file_path.suffix + ".bak")
            with open(backup_path, "w", encoding="utf-8") as f:
                f.write(original_content)
            result["backup_created"] = True

        # Perform replacement
        if regex:
            new_content, count = pattern.subn(replacement, original_content)
        else:
            # For literal replacement, use re.sub with escaped pattern
            new_content, count = pattern.subn(replacement, original_content)

        if count == 0:
            return result

        result["changes_found"] = True
        result["replacements_made"] = count

        # Generate line-level changes
        original_lines = original_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)

        for line_num, (orig_line, new_line) in enumerate(zip(original_lines, new_lines), 1):
            if orig_line != new_line:
                result["lines_changed"].append(
                    {
                        "line_number": line_num,
                        "original": orig_line.rstrip(),
                        "new": new_line.rstrip(),
                    }
                )

        # Generate diff
        diff = difflib.unified_diff(
            original_lines,
            new_lines,
            fromfile=f"a/{file_path.name}",
            tofile=f"b/{file_path.name}",
            lineterm="",
        )
        result["diff"] = "\n".join(diff)

        # Write file if not dry run
        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

        return result

    except UnicodeDecodeError:
        return {
            "file": str(file_path),
            "error": "Unable to decode file (likely binary)",
            "changes_found": False,
            "replacements_made": 0,
            "lines_changed": [],
            "backup_created": False,
            "diff": "",
        }
    except Exception as e:
        return {
            "file": str(file_path),
            "error": f"Error processing file: {str(e)}",
            "changes_found": False,
            "replacements_made": 0,
            "lines_changed": [],
            "backup_created": False,
            "diff": "",
        }


def preview_changes(
    pattern: str,
    paths: list[str],
    include_patterns: list[str] = ["*"],
    exclude_patterns: list[str] = [],
    max_preview_lines: int = 50,
) -> dict[str, Any]:
    """Generate a preview of potential changes without full processing."""
    try:
        files_to_process = collect_files(paths, include_patterns, exclude_patterns, 10485760)
        preview: dict[str, Any] = {"files_count": len(files_to_process), "sample_matches": []}

        # Sample first few files
        for file_path in files_to_process[:5]:
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Simple regex search for preview (no replacement)
                matches = list(re.finditer(re.escape(pattern), content, re.IGNORECASE))

                if matches:
                    line_numbers: list[int] = []
                    for match in matches[:10]:  # Limit matches per file
                        line_num = content[: match.start()].count("\n") + 1
                        line_numbers.append(line_num)

                    preview["sample_matches"].append(
                        {
                            "file": str(file_path),
                            "matches_count": len(matches),
                            "sample_lines": line_numbers[:5],
                        }
                    )

            except Exception:
                continue

        return preview

    except Exception as e:
        return {"error": f"Preview failed: {str(e)}"}
