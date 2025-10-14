"""Execute agent actions with permission checking."""

import os
import shlex
import subprocess
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Any

import pathspec

from .permissions import ActionType, PermissionManager


class ActionExecutor:
    """Executes actions with permission checking."""

    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> tuple[bool, str, Any]:
        """
        Execute an action.

        Returns:
            Tuple of (success: bool, message: str, result: Any)
        """
        # Map tool names to action types
        action_map = {
            "read_file": ActionType.READ_FILE,
            "write_file": ActionType.WRITE_FILE,
            "delete_file": ActionType.DELETE_FILE,
            "list_directory": ActionType.LIST_DIR,
            "create_directory": ActionType.CREATE_DIR,
            "execute_command": ActionType.EXECUTE_COMMAND,
            "search_files": ActionType.SEARCH_FILES,
            "get_file_info": ActionType.GET_FILE_INFO,
            "read_files": ActionType.READ_FILE,  # Uses the same permission as read_file
            "grep": ActionType.GREP,  # Use dedicated GREP action type
            "edit_file": ActionType.EDIT_FILE,  # Add mapping for edit_file tool
        }

        action_type = action_map.get(tool_name)
        if not action_type:
            return False, f"Unknown tool: {tool_name}", None

        # Check if action is denied
        if self.permission_manager.config.is_denied(action_type):
            return False, f"Action {tool_name} is denied by policy", None

        # Execute the action
        try:
            if tool_name == "read_file":
                return self._read_file(tool_input["path"])
            elif tool_name == "write_file":
                return self._write_file(tool_input["path"], tool_input["content"])
            elif tool_name == "delete_file":
                return self._delete_file(tool_input["path"])
            elif tool_name == "list_directory":
                return self._list_directory(tool_input["path"], tool_input.get("recursive", False))
            elif tool_name == "create_directory":
                return self._create_directory(tool_input["path"])
            elif tool_name == "execute_command":
                return self._execute_command(
                    tool_input["command"], tool_input.get("working_dir", ".")
                )
            elif tool_name == "search_files":
                return self._search_files(tool_input["pattern"], tool_input.get("path", "."))
            elif tool_name == "get_file_info":
                return self._get_file_info(tool_input["path"])
            elif tool_name == "read_files":
                return self._read_files(tool_input["paths"])
            elif tool_name == "grep":
                return self._grep(
                    tool_input["pattern"], tool_input["paths"], tool_input.get("flags", "")
                )
            elif tool_name == "edit_file":
                return self._edit_file(
                    tool_input["path"],
                    tool_input["operation"],
                    tool_input.get("content", ""),
                    tool_input.get("line_number"),
                    tool_input.get("pattern", ""),
                    tool_input.get("match_pattern_line", True),
                )
            else:
                return False, f"Unimplemented tool: {tool_name}", None
        except Exception as e:
            return False, f"Error executing {tool_name}: {str(e)}", None

    def _read_file(self, path: str) -> tuple[bool, str, Any]:
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

    def _read_files(self, paths: list[str]) -> tuple[bool, str, Any]:
        """Read multiple files."""
        try:
            results = []
            for path in paths:
                try:
                    with open(path, encoding="utf-8") as f:
                        content = f.read()
                    results.append(
                        f"--- Contents of {path} ---\n{content}\n--- End of {path} ---\n"
                    )
                except Exception as e:
                    results.append(
                        f"--- Failed to read {path} ---\nError: {str(e)}\n--- End of {path} ---\n"
                    )

            combined_content = "\n".join(results)
            return True, f"Successfully read {len(paths)} files", combined_content
        except Exception as e:
            return False, f"Failed to read files: {str(e)}", None

    def _write_file(self, path: str, content: str) -> tuple[bool, str, Any]:
        """Write to a file."""
        try:
            # Create parent directories if needed
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"Successfully wrote to {path}", None
        except PermissionError:
            return False, f"Permission denied when writing to: {path}", None
        except OSError as e:
            return False, f"OS error when writing to {path}: {str(e)}", None
        except Exception as e:
            return False, f"Failed to write to {path}: {str(e)}", None

    def _delete_file(self, path: str) -> tuple[bool, str, Any]:
        """Delete a file."""
        try:
            os.remove(path)
            return True, f"Successfully deleted {path}", None
        except FileNotFoundError:
            return False, f"File not found: {path}", None
        except PermissionError:
            return False, f"Permission denied when deleting: {path}", None
        except OSError as e:
            return False, f"OS error when deleting {path}: {str(e)}", None
        except Exception as e:
            return False, f"Failed to delete {path}: {str(e)}", None

    def _load_gitignore(self, directory: str) -> pathspec.PathSpec | None:
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

    def _list_directory(self, path: str, recursive: bool) -> tuple[bool, str, Any]:
        """List directory contents."""
        try:
            if not os.path.exists(path):
                return False, f"Directory not found: {path}", None

            if not os.path.isdir(path):
                return False, f"Path is not a directory: {path}", None

            if recursive:
                # Load .gitignore patterns
                gitignore_spec = self._load_gitignore(path)

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

    def _create_directory(self, path: str) -> tuple[bool, str, Any]:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True, f"Successfully created directory {path}", None
        except PermissionError:
            return False, f"Permission denied when creating directory: {path}", None
        except OSError as e:
            return False, f"OS error when creating directory {path}: {str(e)}", None
        except Exception as e:
            return False, f"Failed to create directory {path}: {str(e)}", None

    def _execute_command(self, cmd: str, working_dir: str = ".") -> tuple[bool, str, Any]:
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

    def _search_files(self, pattern: str, path: str = ".") -> tuple[bool, str, Any]:
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

    def _get_file_info(self, path: str) -> tuple[bool, str, Any]:
        """Get file metadata."""
        try:
            stat = os.stat(path)
            info = {
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "is_directory": os.path.isdir(path),
                "is_file": os.path.isfile(path),
            }

            # Format the info as a string to match test expectations
            info_str = "\n".join([f"{key}: {value}" for key, value in info.items()])
            return True, f"Successfully retrieved file info for {path}", info_str
        except FileNotFoundError:
            return False, f"File not found: {path}", None
        except PermissionError:
            return False, f"Permission denied when getting info for: {path}", None
        except Exception as e:
            return False, f"Failed to get file info for {path}: {str(e)}", None

    def _translate_grep_flags_to_rg(self, flags: str) -> str:
        """
        Translate common grep flags to their ripgrep equivalents.

        Args:
            flags: String of grep flags

        Returns:
            String of translated ripgrep flags
        """
        # Mapping of grep flags to ripgrep equivalents
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
            "-r": "--recursive",
            "--recursive": "--recursive",
            "-L": "--files-without-match",
            "--files-without-match": "--files-without-match",
            "--include": "--glob",  # -r and --include need special handling
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
                translated_flags.append(flag_mapping.get(flag, flag))
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
                translated_flags.append(flag_mapping[flag])
            else:
                # Keep unknown flags as-is (might be ripgrep-specific)
                translated_flags.append(flag)

            i += 1

        return " ".join(translated_flags)

    def _grep(self, pattern: str, paths: list[str], flags: str = "") -> tuple[bool, str, Any]:
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
                    translated_flags = self._translate_grep_flags_to_rg(flags)
                    rg_flags.append(translated_flags)

                # Build command - paths with glob patterns should not be quoted to allow shell expansion  # noqa: E501
                cmd_parts = ["rg"] + rg_flags + [shlex.quote(pattern)]
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
                grep_flags = ["-I", "-n"]
                if flags:
                    # Split and rejoin to ensure proper spacing
                    flag_list = shlex.split(flags)
                    grep_flags.extend(flag_list)

                # Build command - paths with glob patterns should not be quoted to allow shell expansion  # noqa: E501
                cmd_parts = ["grep"] + grep_flags + [shlex.quote(pattern)]
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

    def _edit_file(
        self,
        path: str,
        operation: str,
        content: str = "",
        line_number: int | None = None,
        pattern: str = "",
        match_pattern_line: bool = True,
    ) -> tuple[bool, str, Any]:
        """Edit a file with various operations (insert, replace, delete, append)."""
        try:
            # Read current file content
            try:
                with open(path, encoding="utf-8") as f:
                    file_content = f.read()
            except FileNotFoundError:
                return False, f"File not found: {path}", None

            lines = file_content.splitlines(keepends=True)

            # Handle different operations
            if operation == "insert":
                if line_number is None:
                    return False, "Line number required for insert operation", None

                # Line numbers from user are 1-based, convert to 0-based indexing
                # For insert, line_number 1 means insert at the beginning (index 0)
                # line_number 2 means insert before the second line (index 1)
                # etc. Special case: line_number 0 means insert at the beginning
                if line_number < 0 or line_number > len(lines):
                    msg = f"Invalid line number {line_number}. File has {len(lines)} lines"
                    return False, msg, None

                # Convert 1-based line number to 0-based index
                idx = line_number - 1 if line_number > 0 else 0

                # Add newline if content doesn't end with one
                if content and not content.endswith("\n"):
                    content += "\n"

                lines.insert(idx, content)

            elif operation == "replace":
                if line_number is not None:
                    # Convert from 1-based to 0-based indexing (1-based line numbers from user)
                    idx = line_number - 1
                    if idx < 0 or idx >= len(lines):
                        msg = f"Invalid line number {line_number}. File has {len(lines)} lines"
                        return False, msg, None

                    # Add newline if content doesn't end with one
                    if content and not content.endswith("\n"):
                        content += "\n"

                    lines[idx] = content
                elif pattern:
                    # Find and replace lines matching the pattern
                    found = False
                    for i, line in enumerate(lines):
                        if match_pattern_line:
                            # Case insensitive pattern matching like the test expects
                            if pattern.lower() in line.lower():
                                # Add newline if content doesn't end with one
                                if content and not content.endswith("\n"):
                                    content += "\n"

                                lines[i] = content
                                found = True
                                break
                        else:
                            if line.strip() == pattern:
                                # Add newline if content doesn't end with one
                                if content and not content.endswith("\n"):
                                    content += "\n"

                                lines[i] = content
                                found = True
                                break

                    if not found:
                        return False, f"Pattern '{pattern}' not found in file", None
                else:
                    return (
                        False,
                        ("Either line_number or pattern is required for replace operation"),
                        None,
                    )

            elif operation == "delete":
                if line_number is not None:
                    # Convert from 1-based to 0-based indexing (1-based line numbers from user)
                    idx = line_number - 1
                    if idx < 0 or idx >= len(lines):
                        msg = f"Invalid line number {line_number}. File has {len(lines)} lines"
                        return False, msg, None

                    lines.pop(idx)
                elif pattern:
                    # Find and delete lines matching the pattern
                    # Need to iterate backwards to avoid index shifting issues
                    found = False
                    for i in range(len(lines) - 1, -1, -1):
                        line = lines[i]
                        if match_pattern_line:
                            # Case insensitive pattern matching like the test expects
                            if pattern.lower() in line.lower():
                                lines.pop(i)
                                found = True
                        else:
                            if line.strip() == pattern:
                                lines.pop(i)
                                found = True

                    if not found:
                        return False, f"Pattern '{pattern}' not found in file", None
                else:
                    return (
                        False,
                        ("Either line_number or pattern is required for delete operation"),
                        None,
                    )

            elif operation == "append":
                # If the file doesn't end with newline but we're appending, add one first
                if lines and lines[-1] and not lines[-1].endswith("\n"):
                    lines[-1] += "\n"

                # Add newline if content doesn't end with one
                if content and not content.endswith("\n"):
                    content += "\n"

                lines.append(content)
            else:
                return False, f"Unknown operation: {operation}", None

            # Write back to file
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return True, f"Successfully performed {operation} operation", None

        except PermissionError:
            return False, f"Permission denied when editing: {path}", None
        except Exception as e:
            return False, f"Failed to edit {path}: {str(e)}", None
