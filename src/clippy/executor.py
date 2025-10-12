"""Execute agent actions with permission checking."""

import os
import subprocess
from pathlib import Path
from typing import Any, Dict
from glob import glob
from datetime import datetime

from .permissions import ActionType, PermissionManager, PermissionLevel


class ActionExecutor:
    """Executes actions with permission checking."""

    def __init__(self, permission_manager: PermissionManager):
        self.permission_manager = permission_manager

    def execute(
        self, tool_name: str, tool_input: Dict[str, Any]
    ) -> tuple[bool, str, Any]:
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
                return self._list_directory(
                    tool_input["path"], tool_input.get("recursive", False)
                )
            elif tool_name == "create_directory":
                return self._create_directory(tool_input["path"])
            elif tool_name == "execute_command":
                return self._execute_command(
                    tool_input["command"], tool_input.get("working_dir", ".")
                )
            elif tool_name == "search_files":
                return self._search_files(
                    tool_input["pattern"], tool_input.get("path", ".")
                )
            elif tool_name == "get_file_info":
                return self._get_file_info(tool_input["path"])
            else:
                return False, f"Unimplemented tool: {tool_name}", None
        except Exception as e:
            return False, f"Error executing {tool_name}: {str(e)}", None

    def _read_file(self, path: str) -> tuple[bool, str, Any]:
        """Read a file."""
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            return True, f"Successfully read {path}", content
        except Exception as e:
            return False, f"Failed to read {path}: {str(e)}", None

    def _write_file(self, path: str, content: str) -> tuple[bool, str, Any]:
        """Write to a file."""
        try:
            # Create parent directories if needed
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return True, f"Successfully wrote to {path}", None
        except Exception as e:
            return False, f"Failed to write to {path}: {str(e)}", None

    def _delete_file(self, path: str) -> tuple[bool, str, Any]:
        """Delete a file."""
        try:
            os.remove(path)
            return True, f"Successfully deleted {path}", None
        except Exception as e:
            return False, f"Failed to delete {path}: {str(e)}", None

    def _list_directory(self, path: str, recursive: bool) -> tuple[bool, str, Any]:
        """List directory contents."""
        try:
            if recursive:
                files = []
                for root, dirs, filenames in os.walk(path):
                    for filename in filenames:
                        files.append(os.path.join(root, filename))
                    for dirname in dirs:
                        files.append(os.path.join(root, dirname) + "/")
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
        except Exception as e:
            return False, f"Failed to list {path}: {str(e)}", None

    def _create_directory(self, path: str) -> tuple[bool, str, Any]:
        """Create a directory."""
        try:
            Path(path).mkdir(parents=True, exist_ok=True)
            return True, f"Successfully created directory {path}", None
        except Exception as e:
            return False, f"Failed to create directory {path}: {str(e)}", None

    def _execute_command(
        self, command: str, working_dir: str
    ) -> tuple[bool, str, Any]:
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
                return True, f"Command executed successfully", output
            else:
                return (
                    False,
                    f"Command failed with exit code {result.returncode}",
                    output,
                )
        except subprocess.TimeoutExpired:
            return False, "Command timed out after 30 seconds", None
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
        except Exception as e:
            return False, f"Failed to get info for {path}: {str(e)}", None
