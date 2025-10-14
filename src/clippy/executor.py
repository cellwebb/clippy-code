"""Execute agent actions with permission checking."""

import os
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
            "grep": ActionType.SEARCH_FILES,  # Use same permission as search_files
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

                files = []
                skipped_dirs = []

                # Use pathspec's built-in tree walking which handles filtering properly
                if gitignore_spec:
                    # Walk the tree and collect all entries
                    for root, dirs, filenames in os.walk(path):
                        # Get relative path from base
                        rel_root = os.path.relpath(root, path)
                        if rel_root == ".":
                            rel_root = ""

                        # Check each directory to see if it should be skipped
                        dirs_to_remove = []
                        for dirname in dirs:
                            rel_dir_path = os.path.join(rel_root, dirname) if rel_root else dirname

                            # Check if this directory should be skipped
                            if gitignore_spec.match_file(rel_dir_path + "/"):
                                skipped_dirs.append(rel_dir_path + "/")
                                dirs_to_remove.append(dirname)

                        # Remove skipped directories from the walk
                        for dirname in dirs_to_remove:
                            dirs.remove(dirname)

                        # Add non-ignored directories to output
                        for dirname in dirs:
                            rel_dir_path = os.path.join(rel_root, dirname) if rel_root else dirname
                            files.append(rel_dir_path + "/")

                        # Add non-ignored files to output
                        for filename in filenames:
                            rel_file_path = (
                                os.path.join(rel_root, filename) if rel_root else filename
                            )
                            if not gitignore_spec.match_file(rel_file_path):
                                files.append(rel_file_path)
                else:
                    # No .gitignore, do normal recursive listing
                    for root, dirs, filenames in os.walk(path):
                        rel_root = os.path.relpath(root, path)
                        if rel_root == ".":
                            rel_root = ""

                        for dirname in dirs:
                            rel_dir_path = os.path.join(rel_root, dirname) if rel_root else dirname
                            files.append(rel_dir_path + "/")

                        for filename in filenames:
                            rel_file_path = (
                                os.path.join(rel_root, filename) if rel_root else filename
                            )
                            files.append(rel_file_path)

                # Add skip notes for large directories
                for skipped_dir in sorted(skipped_dirs):
                    files.append(f"[skipped {skipped_dir} due to .gitignore]")

                result = "\n".join(sorted(files))
            else:
                items = os.listdir(path)
                items_with_type = []
                for item in sorted(items):
                    full_path = os.path.join(path, item)
                    if os.path.isdir(full_path):
                        items_with_type.append(f"{item}/")
                    else:
                        items_with_type.append(item)
                result = "\n".join(items_with_type)
            return True, f"Successfully listed {path}", result
        except PermissionError:
            return False, f"Permission denied when listing: {path}", None
        except FileNotFoundError:
            return False, f"Directory not found: {path}", None
        except Exception as e:
            return False, f"Failed to list {path}: {str(e)}", None

    def _create_directory(self, path: str) -> tuple[bool, str, Any]:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True, f"Successfully created directory {path}", None
        except PermissionError:
            return False, f"Permission denied when creating directory: {path}", None
        except FileExistsError:
            return False, f"Path already exists and is not a directory: {path}", None
        except OSError as e:
            return False, f"OS error when creating directory {path}: {str(e)}", None
        except Exception as e:
            return False, f"Failed to create directory {path}: {str(e)}", None

    def _execute_command(self, command: str, working_dir: str) -> tuple[bool, str, Any]:
        """Execute a shell command."""
        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )
            output = result.stdout + result.stderr
            if result.returncode == 0:
                return True, "Command executed successfully", output
            else:
                return (
                    False,
                    f"Command failed with exit code {result.returncode}",
                    output,
                )
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 30 seconds", None
        except FileNotFoundError:
            return False, f"Working directory not found: {working_dir}", None
        except PermissionError:
            return False, f"Permission denied for working directory: {working_dir}", None
        except Exception as e:
            return False, f"Failed to execute command: {str(e)}", None

    def _search_files(self, pattern: str, path: str) -> tuple[bool, str, Any]:
        """Search for files matching a pattern."""
        try:
            search_pattern = os.path.join(path, pattern)
            matches = glob(search_pattern, recursive=True)
            result = "\n".join(sorted(matches))
            count = len(matches)
            return True, f"Found {count} matches", result
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
                "is_file": os.path.isfile(path),
                "is_dir": os.path.isdir(path),
            }
            result = "\n".join(f"{k}: {v}" for k, v in info.items())
            return True, f"Got info for {path}", result
        except FileNotFoundError:
            return False, f"File not found: {path}", None
        except PermissionError:
            return False, f"Permission denied when getting info for: {path}", None
        except Exception as e:
            return False, f"Failed to get info for {path}: {str(e)}", None

    def _grep(self, pattern: str, paths: list[str], flags: str = "") -> tuple[bool, str, Any]:
        """Search for patterns in files using grep."""
        try:
            # Use regular grep exclusively
            command = f"grep {flags} '{pattern}' {' '.join(paths)}"

            result = subprocess.run(
                command,
                shell=True,
                cwd=".",  # Explicitly set working directory
                capture_output=True,
                text=True,
                timeout=30,
            )

            output = result.stdout + result.stderr
            if result.returncode == 0:
                return True, "grep search executed successfully", output
            elif result.returncode == 1:
                # grep returns 1 when no matches found, which is not an error
                return True, "grep search completed (no matches found)", output
            else:
                return (
                    False,
                    f"grep search failed with exit code {result.returncode}",
                    output,
                )
        except subprocess.TimeoutExpired:
            return False, "Search timed out after 30 seconds", None
        except Exception as e:
            return False, f"Failed to execute grep search: {str(e)}", None
