"""Tool catalog for merging built-in and MCP tools with enhanced categorization."""

from typing import Any

from ..mcp.manager import Manager
from ..tools import TOOLS as BUILTIN_TOOLS


def get_builtin_tools() -> list[dict[str, Any]]:
    """
    Get all built-in tools.

    Returns:
        List of built-in tool definitions in OpenAI format
    """
    return BUILTIN_TOOLS


def get_mcp_tools(mgr: Manager | None) -> list[dict[str, Any]]:
    """
    Get all MCP tools from connected servers.

    Args:
        mgr: MCP Manager instance or None

    Returns:
        List of MCP tool definitions in OpenAI format
    """
    if mgr is None:
        return []

    try:
        return mgr.get_all_tools_openai()
    except Exception:
        # Gracefully handle MCP errors
        return []


def get_all_tools(mgr: Manager | None) -> list[dict[str, Any]]:
    """
    Get all available tools (built-in + MCP).

    Args:
        mgr: MCP Manager instance or None

    Returns:
        List of all tool definitions in OpenAI format
    """
    builtin_tools = get_builtin_tools()
    mcp_tools = get_mcp_tools(mgr)

    # Combine tools, MCP tools override built-in tools with same names
    all_tools = builtin_tools.copy()

    # Create a set of built-in tool names for quick lookup
    builtin_names = {tool["function"]["name"] for tool in builtin_tools}

    # Add MCP tools, replacing any built-in tools with the same name
    for mcp_tool in mcp_tools:
        tool_name = mcp_tool["function"]["name"]
        if tool_name in builtin_names:
            # Replace the built-in tool
            for i, tool in enumerate(all_tools):
                if tool["function"]["name"] == tool_name:
                    all_tools[i] = mcp_tool
                    break
        else:
            # Add new MCP tool
            all_tools.append(mcp_tool)

    return all_tools


def is_mcp_tool(name: str) -> bool:
    """
    Check if a tool name is an MCP tool.

    Args:
        name: Tool name to check

    Returns:
        True if the tool name is an MCP tool (starts with "mcp__")
    """
    return name.startswith("mcp__")


def get_tool_categories() -> dict[str, dict[str, Any]]:
    """
    Get tool categories with descriptions and use cases.

    Returns:
        Dictionary mapping category names to category information
    """
    return {
        "file_operations": {
            "name": "File Operations",
            "description": "Core file and directory management tools",
            "use_cases": [
                "Reading/writing files",
                "Managing project structure",
                "File validation",
                "System file operations via shell commands",
            ],
            "tools": [
                "read_file",
                "write_file",
                "edit_file",
                "delete_file",
                "list_directory",
                "search_files",
                "get_file_info",
            ],
        },
        "development": {
            "name": "Development & Code",
            "description": "Code analysis, testing, and development workflow tools",
            "use_cases": ["Code review", "Testing", "Refactoring", "Project analysis"],
            "tools": [
                "grep",
                "read_files",
                "execute_command",
                "delegate_to_subagent",
                "run_parallel_subagents",
            ],
        },
        "system": {
            "name": "System & Operations",
            "description": "System operations and command execution tools",
            "use_cases": ["Running commands", "Directory operations", "System tasks"],
            "tools": ["execute_command", "create_directory"],
        },
        "collaboration": {
            "name": "Collaboration & AI Assistants",
            "description": "AI-powered tools for complex task decomposition and parallel work",
            "use_cases": ["Code review", "Parallel testing", "Documentation", "Complex analysis"],
            "tools": ["delegate_to_subagent", "run_parallel_subagents"],
        },
    }


def get_tool_recommendations(context: dict[str, Any] | None = None) -> list[str]:
    """
    Get tool recommendations based on context.

    Args:
        context: Context information (recent operations, file types, etc.)

    Returns:
        List of recommended tool names
    """
    recommendations = []

    if context is None:
        # Default recommendations for new users
        return [
            "read_file",  # Start by examining files
            "write_file",  # Create new content
            "list_directory",  # Explore project structure
            "grep",  # Search in code
        ]

    # Context-based recommendations
    recent_operations = context.get("recent_operations", [])
    context.get("current_file", "")
    file_type = context.get("file_type", "")

    # Recommend based on file type
    if file_type == "python":
        recommendations.extend(["grep", "execute_command", "delegate_to_subagent"])
    elif file_type in ["json", "yaml", "toml"]:
        recommendations.extend(["read_file", "edit_file", "validate_file"])
    elif file_type in ["md", "rst"]:
        recommendations.extend(["read_file", "edit_file", "grep"])

    # Recommend based on recent operations
    if "read_file" in recent_operations[-3:]:
        recommendations.append("edit_file")
    if "write_file" in recent_operations[-3:]:
        recommendations.append("read_file")
    if "list_directory" in recent_operations[-3:]:
        recommendations.append("search_files")

    # Remove duplicates and limit to 5 recommendations
    unique_recommendations = list(dict.fromkeys(recommendations))
    return unique_recommendations[:5]


def suggest_file_actions(file_path: str, file_type: str | None = None) -> list[dict[str, Any]]:
    """
    Suggest actions that can be performed on a specific file.

    Args:
        file_path: Path to the file
        file_type: Optional file type hint

    Returns:
        List of suggested actions with tools and descriptions
    """
    actions = []

    # Determine file type from extension if not provided
    if file_type is None:
        if "." in file_path:
            ext = file_path.split(".")[-1].lower()
            file_type = ext

    # Common actions for all files
    actions.extend(
        [
            {
                "tool": "read_file",
                "description": f"Read and examine the contents of {file_path}",
                "use_case": "code review, debugging, understanding",
            },
            {
                "tool": "get_file_info",
                "description": f"Get metadata and information about {file_path}",
                "use_case": "file analysis, size checking",
            },
        ]
    )

    # File-type specific actions
    if file_type in ["py", "js", "ts", "java", "cpp", "c"]:
        actions.extend(
            [
                {
                    "tool": "grep",
                    "description": f"Search for patterns, functions, or variables in {file_path}",
                    "use_case": "code analysis, finding definitions",
                },
                {
                    "tool": "delegate_to_subagent",
                    "description": f"Perform code review or analysis on {file_path}",
                    "use_case": "security review, quality assessment",
                },
            ]
        )

    if file_type in ["json", "yaml", "toml", "xml"]:
        actions.append(
            {
                "tool": "edit_file",
                "description": f"Modify configuration or data in {file_path}",
                "use_case": "configuration changes, data updates",
            }
        )

    if file_type in ["md", "rst", "txt"]:
        actions.append(
            {
                "tool": "edit_file",
                "description": f"Edit documentation or text content in {file_path}",
                "use_case": "documentation updates, content creation",
            }
        )

    return actions


def get_tool_by_category(category: str) -> list[dict[str, Any]]:
    """
    Get all tools in a specific category.

    Args:
        category: Category name

    Returns:
        List of tool definitions in the category
    """
    categories = get_tool_categories()

    if category not in categories:
        return []

    category_info = categories[category]
    tool_names = category_info["tools"]

    all_tools = get_builtin_tools()
    category_tools = []

    for tool in all_tools:
        tool_name = tool["function"]["name"]
        if tool_name in tool_names:
            category_tools.append(tool)

    return category_tools


def enhance_tool_descriptions(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Enhance tool descriptions with use cases and examples.

    Args:
        tools: List of tool definitions

    Returns:
        Enhanced tool definitions
    """
    enhanced_tools = []

    for tool in tools:
        enhanced_tool = tool.copy()
        function_info = enhanced_tool["function"].copy()

        name = function_info["name"]

        # Add enhanced descriptions based on tool name
        enhanced_descriptions = {
            "read_file": (
                "Read and examine file contents. Perfect for code review, debugging, "
                "and understanding existing files."
            ),
            "write_file": (
                "Create or overwrite files with automatic syntax validation for Python, JSON, "
                "YAML, XML, HTML, CSS, JS, TS, and Markdown."
            ),
            "edit_file": (
                "Modify existing files with precise pattern matching. Great for refactoring, "
                "bug fixes, and code updates."
            ),
            "list_directory": (
                "Explore directory structures and discover project files. "
                "Supports recursive listing with gitignore awareness."
            ),
            "search_files": (
                "Find files by name or pattern across your project. "
                "Essential for navigating large codebases."
            ),
            "grep": (
                "Search for patterns within files using powerful regex support. "
                "Ideal for code analysis and finding references."
            ),
            "execute_command": (
                "Run shell commands and external tools. Perfect for building, testing, "
                "system operations, and file operations like 'mv', 'cp', 'tar', 'zip', etc."
            ),
            "delegate_to_subagent": (
                "Create specialized AI assistants for complex tasks like code review, testing, "
                "documentation, and refactoring."
            ),
            "run_parallel_subagents": (
                "Execute multiple tasks concurrently with parallel AI assistants. "
                "Great for large-scale analysis and testing."
            ),
            "delete_file": (
                "Remove files and directories safely. Use with caution for cleanup and maintenance."
            ),
            "get_file_info": (
                "Inspect file metadata including size, modification time, and type. "
                "Useful for file analysis."
            ),
            "create_directory": (
                "Create directory structures for project organization. "
                "Automatically creates parent directories as needed."
            ),
            "read_files": ("Read multiple files simultaneously for batch analysis and comparison."),
        }

        if name in enhanced_descriptions:
            function_info["description"] = enhanced_descriptions[name]

        enhanced_tool["function"] = function_info
        enhanced_tools.append(enhanced_tool)

    return enhanced_tools


def get_all_tools_enhanced(mgr: Manager | None = None) -> list[dict[str, Any]]:
    """
    Get all available tools (built-in + MCP) with enhanced descriptions.

    Args:
        mgr: MCP Manager instance or None

    Returns:
        List of enhanced tool definitions
    """
    all_tools = get_all_tools(mgr)
    return enhance_tool_descriptions(all_tools)


def get_tool_help(tool_name: str) -> dict[str, Any] | None:
    """
    Get detailed help information for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Detailed tool information or None if not found
    """
    all_tools = get_all_tools_enhanced()

    for tool in all_tools:
        if tool["function"]["name"] == tool_name:
            # Find which category this tool belongs to
            categories = get_tool_categories()
            tool_category = "general"

            for category_name, category_info in categories.items():
                if tool_name in category_info["tools"]:
                    tool_category = category_info["name"]
                    break

            return {
                "name": tool_name,
                "category": tool_category,
                "description": tool["function"]["description"],
                "parameters": tool["function"].get("parameters", {}),
                "examples": get_tool_examples(tool_name),
            }

    return None


def get_tool_examples(tool_name: str) -> list[str]:
    """
    Get usage examples for a specific tool.

    Args:
        tool_name: Name of the tool

    Returns:
        List of usage examples
    """
    examples = {
        "read_file": [
            "Read a Python file to understand its structure",
            "Examine a configuration file",
            "Review documentation or README files",
        ],
        "write_file": [
            "Create a new Python script with syntax validation",
            "Write a JSON configuration file",
            "Generate documentation in Markdown format",
        ],
        "edit_file": [
            "Fix a bug in existing code",
            "Update imports or dependencies",
            "Add new functions to existing files",
        ],
        "list_directory": [
            "Explore the structure of a new project",
            "Find test files or resources",
            "Check what files exist in a directory",
        ],
        "search_files": [
            "Find all Python test files",
            "Locate configuration files",
            "Search for files with specific names",
        ],
        "grep": [
            "Find all function definitions in a codebase",
            "Search for TODO comments",
            "Locate specific variable usage across files",
        ],
        "execute_command": [
            "Run tests with pytest or unittest",
            "Build a project with make or npm",
            "Execute git commands or other system tools",
            "Create directories: 'mkdir -p path/to/directory'",
            "Copy or move files: 'cp source dest' or 'mv old new'",
            "Delete files/directories: 'rm -rf file_or_directory'",
            "Create archives: 'tar -czf archive.tar.gz files/'",
            "Download files: 'curl -O URL' or 'wget URL'",
        ],
        "delegate_to_subagent": [
            "Perform a comprehensive code review",
            "Generate unit tests for a module",
            "Create documentation for existing code",
            "Refactor code for better performance",
        ],
        "run_parallel_subagents": [
            "Test multiple modules simultaneously",
            "Review different parts of a codebase in parallel",
            "Generate documentation and tests concurrently",
        ],
    }

    return examples.get(tool_name, ["No specific examples available"])
