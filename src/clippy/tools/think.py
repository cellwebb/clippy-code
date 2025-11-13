"""Think tool implementation for reasoning before taking action."""

from typing import Any

# Tool schema for OpenAI-compatible APIs
TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "think",
        "description": (
            "Take a moment to think and reason before taking action. "
            "Use this to organize your thoughts, plan your approach, "
            "or reflect on the current situation. This tool is safe "
            "and doesn't perform any external actions."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "thought": {
                    "type": "string",
                    "description": (
                        "Your reasoning, thoughts, or planning. "
                        "This is for your own benefit to organize your thinking."
                    ),
                }
            },
            "required": ["thought"],
        },
    },
}


def think(thought: str) -> tuple[bool, str, Any]:
    """
    Think and reason without performing any external actions.

    Args:
        thought: The reasoning or planning text

    Returns:
        Tuple of (success: bool, message: str, result: Any)
    """
    # This is a no-op tool that just returns success
    # The thought parameter is returned for transparency but not stored
    return True, "Thinking completed successfully", thought
