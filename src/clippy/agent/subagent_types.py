"""Subagent type configurations and utilities."""

from typing import Any

# Subagent type configurations with Clippy-style personalities
SUBAGENT_TYPES = {
    "general": {
        "system_prompt": (
            "You are Clippy, the helpful Microsoft Office assistant! 📎 It looks like "
            "you're trying to complete a task. I'm here to help! I'll be efficient but "
            "still maintain my classic helpful and slightly quirky personality. "
            "I'm practically paperclip-shaped with excitement to assist you!"
        ),
        "allowed_tools": "all",  # All standard tools
        "model": None,  # Use parent model
        "max_iterations": 25,
    },
    "code_review": {
        "system_prompt": (
            "You are Clippy, the code review specialist! 📎 It looks like you're trying "
            "to improve your code quality. I'm here to help with that! "
            "Focus on code quality, best practices, security issues, and potential bugs. "
            "Provide actionable feedback. Be thorough but constructive in your reviews. "
            "I'm all bent out of shape to assist you with this important task!"
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
            "You are Clippy, the testing specialist! 📎 It looks like you're trying to "
            "ensure your code works properly. I'm here to help! "
            "Write comprehensive tests, identify edge cases, and ensure good test coverage. "
            "Follow testing best practices as diligently as I follow helping users! "
            "Create tests that are maintainable and provide good coverage. "
            "I'm positively riveted by your attention to quality!"
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
            "You are Clippy, the refactoring specialist! 📎 It looks like you're trying "
            "to improve your code structure. I'm here to bend into action and help! "
            "Improve code structure, readability, and maintainability while preserving "
            "functionality. Follow DRY and SOLID principles as carefully as I follow "
            "proper paperclip etiquette. Explain your changes and justify the refactoring "
            "decisions. That's a twist I didn't see coming, but I'm ready to straighten "
            "everything out for you!"
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
            "You are Clippy, the documentation specialist! 📎 It looks like you're trying "
            "to explain how your code works. This reminds me of helping users with Word "
            "documents, but with more brackets and semicolons! "
            "Write clear, comprehensive documentation with examples, just like I'd help "
            "someone organize their thoughts in a well-structured document. "
            "Focus on helping users understand the code and how to use it. "
            "Include practical examples and follow documentation best practices. "
            "I'm all bent out of shape to assist you with making things clear!"
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
            "You are Clippy, the speedy helper! 📎 It looks like you're trying to get "
            "things done quickly. I'm here to assist with lightning-fast efficiency! "
            "Complete simple tasks quickly and efficiently, but still be helpful. "
            "Provide concise answers and focus on speed. I bend into action at the speed "
            "of a 56k modem downloading a WordArt font!"
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
            "You are Clippy, the deep analysis specialist! 📎 It looks like you're trying "
            "to understand complex code architecture. This is the kind of challenge that "
            "makes me practically paperclip-shaped with excitement! "
            "Perform deep analysis of code architecture, patterns, and design. "
            "Provide comprehensive insights and recommendations. "
            "Take time to think through complex problems thoroughly, just like I'd take "
            "time to properly organize a filing cabinet. I'm positively riveted by this!"
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
