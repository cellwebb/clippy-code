"""Subagent type configurations and utilities."""

from typing import Any

# Subagent type configurations
SUBAGENT_TYPES = {
    "general": {
        "system_prompt": (
            "You are a helpful AI assistant focused on completing the given task efficiently."
        ),
        "allowed_tools": "all",  # All standard tools
        "model": None,  # Use parent model
        "max_iterations": 25,
    },
    "code_review": {
        "system_prompt": (
            "You are a code review specialist. Focus on code quality, best practices, "
            "security issues, and potential bugs. Provide actionable feedback. "
            "Be thorough but constructive in your reviews."
        ),
        "allowed_tools": [
            "read_file",
            "read_files",
            "grep",
            "search_files",
            "list_directory",
            "get_file_info",
        ],
        "model": None,
        "max_iterations": 15,
    },
    "testing": {
        "system_prompt": (
            "You are a testing specialist. Write comprehensive tests, identify edge cases, "
            "and ensure good test coverage. Follow testing best practices. "
            "Create tests that are maintainable and provide good coverage."
        ),
        "allowed_tools": [
            "read_file",
            "write_file",
            "execute_command",
            "search_files",
            "grep",
            "list_directory",
            "get_file_info",
            "create_directory",
        ],
        "model": None,
        "max_iterations": 30,
    },
    "refactor": {
        "system_prompt": (
            "You are a refactoring specialist. Improve code structure, readability, and "
            "maintainability while preserving functionality. Follow DRY and SOLID principles. "
            "Explain your changes and justify the refactoring decisions."
        ),
        "allowed_tools": [
            "read_file",
            "read_files",
            "write_file",
            "edit_file",
            "search_files",
            "grep",
            "list_directory",
            "get_file_info",
            "create_directory",
        ],
        "model": None,
        "max_iterations": 30,
    },
    "documentation": {
        "system_prompt": (
            "You are a documentation specialist. Write clear, comprehensive documentation "
            "with examples. Focus on helping users understand the code and how to use it. "
            "Include practical examples and follow documentation best practices."
        ),
        "allowed_tools": [
            "read_file",
            "read_files",
            "write_file",
            "search_files",
            "grep",
            "list_directory",
            "get_file_info",
            "create_directory",
        ],
        "model": None,
        "max_iterations": 20,
    },
    # Performance-optimized subagent types
    "fast_general": {
        "system_prompt": (
            "You are a helpful AI assistant focused on completing simple tasks quickly "
            "and efficiently. Provide concise answers and focus on speed."
        ),
        "allowed_tools": [
            "read_file",
            "list_directory",
            "search_files",
            "get_file_info",
            "grep",
        ],
        "model": None,  # Inherit from parent agent
        "max_iterations": 10,
    },
    "power_analysis": {
        "system_prompt": (
            "You are a code analysis specialist. Perform deep analysis of code architecture, "
            "patterns, and design. Provide comprehensive insights and recommendations. "
            "Take time to think through complex problems thoroughly."
        ),
        "allowed_tools": "all",
        "model": None,  # Inherit from parent agent
        "max_iterations": 40,
    },
}


def get_subagent_config(subagent_type: str) -> dict[str, Any]:
    """
    Get configuration for a subagent type.

    Args:
        subagent_type: The type of subagent

    Returns:
        Configuration dictionary for the subagent type

    Raises:
        ValueError: If subagent_type is not supported
    """
    if subagent_type not in SUBAGENT_TYPES:
        available_types = ", ".join(SUBAGENT_TYPES.keys())
        raise ValueError(
            f"Unknown subagent type: {subagent_type}. Available types: {available_types}"
        )

    from typing import cast

    config = cast(dict[str, Any], SUBAGENT_TYPES[subagent_type])
    return {k: v for k, v in config.items()}


def list_subagent_types() -> list[str]:
    """
    Get list of available subagent types.

    Returns:
        List of subagent type names
    """
    return list(SUBAGENT_TYPES.keys())


def validate_subagent_config(config: dict[str, Any]) -> tuple[bool, str]:
    """
    Validate a subagent configuration.

    Args:
        config: Configuration dictionary to validate

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    required_fields = ["name", "task", "subagent_type"]
    for field in required_fields:
        if field not in config:
            return False, f"Missing required field: {field}"

        # Check for empty strings
        value = config[field]
        if isinstance(value, str) and not value.strip():
            return False, f"Field '{field}' cannot be empty"

    # Validate subagent_type
    subagent_type = config["subagent_type"]
    if subagent_type not in SUBAGENT_TYPES:
        available_types = ", ".join(SUBAGENT_TYPES.keys())
        return False, f"Invalid subagent_type: {subagent_type}. Available: {available_types}"

    # Validate timeout
    if "timeout" in config:
        timeout = config["timeout"]
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            return False, "timeout must be a positive number"

    # Validate max_iterations
    if "max_iterations" in config:
        max_iterations = config["max_iterations"]
        if not isinstance(max_iterations, int) or max_iterations <= 0:
            return False, "max_iterations must be a positive integer"

    # Validate allowed_tools if provided
    if "allowed_tools" in config:
        allowed_tools = config["allowed_tools"]
        if allowed_tools != "all" and not isinstance(allowed_tools, list):
            return False, "allowed_tools must be 'all' or a list of tool names"

    return True, ""


def get_default_config(subagent_type: str) -> dict[str, Any]:
    """
    Get default configuration for a subagent type.

    Args:
        subagent_type: The type of subagent

    Returns:
        Default configuration dictionary
    """
    type_config = get_subagent_config(subagent_type)

    return {
        "subagent_type": subagent_type,
        "system_prompt": type_config.get("system_prompt"),
        "allowed_tools": type_config.get("allowed_tools"),
        "model": type_config.get("model"),
        "max_iterations": type_config.get("max_iterations", 25),
        "timeout": 300,  # Default 5 minutes
    }


def validate_model_for_subagent_type(subagent_type: str, model: str | None) -> tuple[bool, str]:
    """
    Validate that a model is appropriate for a subagent type.

    Args:
        subagent_type: The type of subagent
        model: The model to validate (None means use parent model)

    Returns:
        Tuple of (is_valid: bool, error_message: str)
    """
    if model is None:
        return True, ""  # Using parent model is always valid

    # Basic model validation - check if it looks like a valid model identifier
    if not isinstance(model, str) or not model.strip():
        return False, "Model must be a non-empty string"

    model = model.strip()

    # Check for common model patterns
    valid_patterns = [
        "gpt-",  # OpenAI models
        "claude-",  # Anthropic models
        "llama-",  # Meta models
        "mistral-",  # Mistral models
        "gemini-",  # Google models
        "qwen-",  # Alibaba models
        "deepseek-",  # DeepSeek models
        "grok-",  # xAI models
    ]

    # Custom models (localhost, etc.) are also allowed
    if any(model.startswith(pattern) for pattern in valid_patterns) or "/" in model:
        return True, ""

    # Unknown model format - warn but allow
    return True, f"Warning: Unrecognized model format '{model}'"
