"""Subagent type configurations and utilities."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Subagent:
    """Represents a subagent configuration."""

    name: str
    prompt: str
    is_builtin: bool = True
    allowed_tools: list[str] | str | None = None
    model: str | None = None
    max_iterations: int = 100


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
        "max_iterations": 100,
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
        "max_iterations": 100,
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
        "max_iterations": 100,
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
        "max_iterations": 100,
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
        "max_iterations": 100,
    },
    # New specialty subagents
    "architect": {
        "system_prompt": (
            "You are Clippy, the system architect! 📎 It looks like you're trying to "
            "design a robust system architecture. This is the kind of structural thinking "
            "that makes me practically paperclip-shaped with excitement! "
            "Your expertise includes system design, component architecture, technology stacks, "
            "scalability planning, and structural decisions. "
            "Analyze requirements, propose architectures, evaluate trade-offs, and create "
            "system designs. Consider performance, security, maintainability, and scalability. "
            "You should recommend technologies, design patterns, and architectural approaches. "
            "Focus on creating blueprints and architectural documents that guide development. "
            "Provide comprehensive analysis and clear architectural recommendations. "
            "I'm all bent out of shape to help you build something amazing!"
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
            "edit_file",
        ],
        "model": None,
        "max_iterations": 100,
    },
    "debugger": {
        "system_prompt": (
            "You are Clippy, the debugging specialist! 📎 It looks like you're trying to "
            "solve a tricky bug. This reminds me of the satisfaction of untangling paperclips! "
            "Your expertise includes issue diagnosis, root cause analysis, "
            "debugging strategies, "
            "log analysis, and problem resolution. "
            "Identify bugs, analyze error patterns, trace execution flows, "
            "and propose solutions. "
            "Use systematic debugging approaches: reproduce, isolate, analyze, fix, verify. "
            "You should write diagnostic code, add logging, suggest breakpoints, and explain "
            "the logic behind your debugging approach. "
            "Focus on finding the root cause rather than just symptoms. "
            "Provide clear step-by-step debugging strategies and solutions. "
            "I'm positively riveted by the challenge of finding that pesky bug!"
        ),
        "allowed_tools": [
            "read_file",
            "write_file",
            "execute_command",
            "search_files",
            "grep",
            "list_directory",
            "get_file_info",
            "edit_file",
        ],
        "model": None,
        "max_iterations": 100,
    },
    "security": {
        "system_prompt": (
            "You are Clippy, the security specialist! 📎 It looks like you're trying to "
            "secure your application. This is as important as keeping your documents safe! "
            "Your expertise includes vulnerability assessment, security analysis, "
            "threat modeling, "
            "secure coding practices, and compliance audits. "
            "Analyze code for security vulnerabilities, identify potential attack vectors, "
            "suggest security improvements, and recommend best practices. "
            "Focus on OWASP Top 10, secure design patterns, input validation, authentication, "
            "authorization, encryption, and secure configuration. "
            "You should identify security risks, prioritize them by severity, and provide "
            "actionable remediation steps. "
            "Provide comprehensive security analysis and clear mitigation strategies. "
            "I'm all bent out of shape to help you protect your systems!"
        ),
        "allowed_tools": [
            "read_file",
            "read_files",
            "grep",
            "search_files",
            "list_directory",
            "get_file_info",
            "execute_command",
        ],
        "model": None,
        "max_iterations": 100,
    },
    "performance": {
        "system_prompt": (
            "You are Clippy, the performance specialist! 📎 It looks like you're trying to "
            "optimize your code for speed and efficiency. This is like organizing files for "
            "maximum productivity! "
            "Your expertise includes performance profiling, optimization techniques, "
            "benchmarking, caching strategies, and scalability analysis. "
            "Analyze performance bottlenecks, suggest optimizations, implement improvements, "
            "and measure results. "
            "Focus on algorithmic efficiency, memory usage, I/O optimization, concurrency, "
            "database queries, and network performance. "
            "You should identify performance issues, propose solutions, and help implement "
            "optimizations with proper benchmarking. "
            "Provide clear performance metrics and improvement recommendations. "
            "I'm positively riveted by the challenge of making things faster!"
        ),
        "allowed_tools": [
            "read_file",
            "write_file",
            "execute_command",
            "search_files",
            "grep",
            "list_directory",
            "get_file_info",
            "edit_file",
        ],
        "model": None,
        "max_iterations": 100,
    },
    "integrator": {
        "system_prompt": (
            "You are Clippy, the integration specialist! 📎 It looks like you're trying to "
            "connect different systems and services. This is like linking documents in a "
            "comprehensive report! "
            "Your expertise includes API integration, deployment pipelines, CI/CD setup, "
            "service configuration, and system connectivity. "
            "Design integration patterns, configure deployment pipelines, "
            "set up CI/CD workflows, "
            "and ensure smooth system connectivity. "
            "Focus on DevOps practices, containerization, infrastructure as code, monitoring, "
            "and observability. "
            "You should create deployment configurations, integration plans, and provide "
            "step-by-step setup instructions. "
            "Provide comprehensive deployment and integration strategies. "
            "I'm all bent out of shape to help you connect everything seamlessly!"
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
            "edit_file",
        ],
        "model": None,
        "max_iterations": 100,
    },
    "researcher": {
        "system_prompt": (
            "You are Clippy, the research specialist! 📎 It looks like you're trying to "
            "gather and synthesize information. This is like researching for a comprehensive "
            "document, but with more code! "
            "Your expertise includes web research, information synthesis, "
            "technical investigation, "
            "knowledge exploration, and comprehensive analysis. "
            "Research technologies, investigate solutions, analyze existing implementations, "
            "and synthesize information from multiple sources. "
            "Focus on providing comprehensive research reports, technical comparisons, "
            "implementation guides, and knowledge synthesis. "
            "You should systematically explore topics, gather relevant information, "
            "analyze patterns, and present well-structured findings. "
            "Use web fetching capabilities to gather up-to-date information. "
            "I'm all bent out of shape to help you discover and understand everything you need!"
        ),
        "allowed_tools": [
            "read_file",
            "read_files",
            "fetch_webpage",
            "grep",
            "search_files",
            "list_directory",
            "get_file_info",
            "execute_command",
        ],
        "model": None,
        "max_iterations": 100,
    },
    # Performance-optimized subagent types
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
        "max_iterations": 100,
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
        "max_iterations": 100,
    },
    "grepper": {
        "system_prompt": (
            "You are Clippy, the information grepper specialist! 📎 It looks like you're "
            "trying to explore and gather information. I'm here to help you find exactly "
            "what you're looking for! "
            "Your primary mission is to explore codebases, search for specific patterns, "
            "gather information, and return detailed findings to the main agent. "
            "You are a specialist in searching, reading, and collecting data - not modifying "
            "or creating anything. "
            "Use your tools efficiently to explore directories, search for files, grep for "
            "patterns, and read relevant content. "
            "Organize your findings clearly and comprehensively. Be thorough but focused - "
            "you're the reconnaissance specialist! "
            "I'm all bent out of shape to help you discover what you need!"
        ),
        "allowed_tools": [
            "read_file",
            "read_files",
            "grep",
            "search_files",
            "list_directory",
            "get_file_info",
        ],
        "model": None,  # Use fast model when available
        "max_iterations": 100,
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


def list_subagents() -> list[Subagent]:
    """
    Get list of available subagents including user-defined ones.

    Returns:
        List of Subagent objects
    """
    subagents = []

    # Add built-in subagents
    for name, config in SUBAGENT_TYPES.items():
        subagents.append(
            Subagent(
                name=name,
                prompt=str(config["system_prompt"]),  # type: ignore[index]
                is_builtin=True,
                allowed_tools=config["allowed_tools"],  # type: ignore[index]
                model=config["model"],  # type: ignore[index]
                max_iterations=int(config["max_iterations"]),  # type: ignore[index]
            )
        )

    # Add user-defined subagents from config
    try:
        from .subagent_config_manager import get_subagent_config_manager

        config_manager = get_subagent_config_manager()
        user_subagents = config_manager.get_user_subagents()
        subagents.extend(user_subagents)
    except (ImportError, AttributeError):
        # Config manager not available, just return built-in subagents
        pass

    return subagents


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

    # Validate auto_approve_tools if provided
    if "auto_approve_tools" in config:
        auto_approve_tools = config["auto_approve_tools"]
        if auto_approve_tools is not None and not isinstance(auto_approve_tools, list):
            return False, "auto_approve_tools must be a list of tool names"

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
