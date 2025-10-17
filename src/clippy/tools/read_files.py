"""Read multiple files tool implementation."""

from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "read_files",
        "description": "Read the contents of multiple files at once.",
        "parameters": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "The paths to the files to read",
                }
            },
            "required": ["paths"],
        },
    },
}


def read_files(paths: list[str]) -> tuple[bool, str, Any]:
    """Read multiple files."""
    try:
        results = []
        for path in paths:
            try:
                with open(path, encoding="utf-8") as f:
                    content = f.read()
                results.append(f"--- Contents of {path} ---\n{content}\n--- End of {path} ---\n")
            except Exception as e:
                results.append(
                    f"--- Failed to read {path} ---\nError: {str(e)}\n--- End of {path} ---\n"
                )

        combined_content = "\n".join(results)
        return True, f"Successfully read {len(paths)} files", combined_content
    except Exception as e:
        return False, f"Failed to read files: {str(e)}", None
