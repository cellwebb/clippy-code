"""Utility functions for clippy-code."""

import logging
import os

import tiktoken

logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """
    Count tokens in a text string using tiktoken.

    Args:
        text: Text to count tokens for
        model: Model name to use for tokenization (default: gpt-4)

    Returns:
        Number of tokens in the text
    """
    try:
        # Try to get the appropriate encoding for the model
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")

        return len(encoding.encode(text))
    except Exception as e:
        logger.warning(f"Error counting tokens: {e}")
        # Fallback: approximate as 4 characters per token
        return len(text) // 4


def truncate_text_to_tokens(
    text: str,
    max_tokens: int,
    model: str = "gpt-4",
    add_warning: bool = True,
    preserve_structure: bool = True,
) -> str:
    """
    Truncate text to fit within max tokens, optionally preserving structure.

    Args:
        text: Text to truncate
        max_tokens: Maximum number of tokens to keep
        model: Model name for tokenization
        add_warning: Whether to add truncation warning
        preserve_structure: Whether to try to preserve structure (code blocks, etc.)

    Returns:
        Truncated text (with optional warning)
    """
    if max_tokens <= 0:
        return "[Content truncated: max_tokens <= 0]"

    # Quick check - if already under limit, return as-is
    current_tokens = count_tokens(text, model)
    if current_tokens <= max_tokens:
        return text

    logger.info(f"Truncating text from {current_tokens:,} to {max_tokens:,} tokens")

    # Reserve some tokens for the truncation warning if needed
    warning_tokens = 20 if add_warning else 0
    usable_tokens = max_tokens - warning_tokens

    if usable_tokens <= 0:
        return "[Content truncated: max_tokens too small for warning]"

    try:
        # Try to get the appropriate encoding for the model
        try:
            encoding = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fall back to cl100k_base for unknown models
            encoding = tiktoken.get_encoding("cl100k_base")

        # Convert text to tokens
        tokens = encoding.encode(text)

        # Truncate to usable length
        truncated_tokens = tokens[:usable_tokens]
        truncated_text = encoding.decode(truncated_tokens)

        # Add warning if requested
        if add_warning:
            warning = f"\n\n[Content truncated: {current_tokens:,} → {max_tokens:,} tokens]"
            return truncated_text + warning
        else:
            return truncated_text

    except Exception as e:
        logger.error(f"Error during smart truncation: {e}")
        # Fallback: simple character-based truncation
        char_limit = usable_tokens * 4  # Rough estimate: 4 chars per token
        fallback_text = text[:char_limit] + "..." if len(text) > char_limit else text

        if add_warning:
            return fallback_text + "\n\n[Content truncated: estimated exceedance]"
        return fallback_text


def smart_truncate_tool_result(
    content: str,
    max_tokens: int,
    tool_name: str,
    model: str = "gpt-4",
) -> str:
    """
    Smart truncate tool result content based tool type and content structure.

    This function provides intelligent truncation strategies for different types
    of tool outputs, trying to preserve the most useful information while staying
    within token limits.

    Args:
        content: The tool result content to truncate
        max_tokens: Maximum tokens allowed
        tool_name: Name of the tool that generated the content
        model: Model name for tokenization

    Returns:
        Truncated content with appropriate warnings
    """
    current_tokens = count_tokens(content, model)

    if current_tokens <= max_tokens:
        return content

    logger.info(f"Smart truncating {tool_name} result: {current_tokens:,} → {max_tokens:,} tokens")

    # Reserve tokens for truncation warning
    warning_tokens = 30
    usable_tokens = max_tokens - warning_tokens

    if usable_tokens <= 0:
        return f"[{tool_name} result truncated: max_tokens too small]"

    # Different strategies for different tool types
    if tool_name in ["read_file", "read_files"]:
        return _truncate_file_content(content, usable_tokens, tool_name, model)
    elif tool_name == "grep":
        return _truncate_grep_output(content, usable_tokens, model)
    elif tool_name == "list_directory":
        return _truncate_directory_listing(content, usable_tokens, model)
    elif tool_name == "execute_command":
        return _truncate_command_output(content, usable_tokens, model)
    elif tool_name == "fetch_webpage":
        return _truncate_webpage_content(content, usable_tokens, model)
    elif tool_name == "find_replace":
        return _truncate_find_replace_output(content, usable_tokens, model)
    else:
        # Generic truncation for other tools
        return (
            truncate_text_to_tokens(
                content, usable_tokens, model, add_warning=False, preserve_structure=True
            )
            + f"\n\n[{tool_name} result truncated: {current_tokens:,} → {max_tokens:,} tokens]"
        )


def _truncate_file_content(content: str, tokens: int, tool_name: str, model: str) -> str:
    """
    Smart truncate file content, preserving structure like imports, classes, functions.
    """
    lines = content.splitlines()

    # Remove excessive empty lines first
    cleaned_lines = []
    prev_empty = False
    for line in lines:
        if line.strip() == "":
            if not prev_empty:
                cleaned_lines.append(line)
            prev_empty = True
        else:
            cleaned_lines.append(line)
            prev_empty = False

    # Try to keep the beginning (imports, class definitions) and some middle content
    if len(cleaned_lines) <= 50:
        # Small file, simple truncation
        result = "\n".join(cleaned_lines[: min(len(cleaned_lines), int(tokens * 0.75))])
    else:
        # Larger file: keep beginning and some structure from middle
        # Keep first 30% of lines (imports, setup)
        start_lines = max(30, int(len(cleaned_lines) * 0.3))
        # Keep some sample lines from the middle
        middle_start = len(cleaned_lines) // 2
        middle_end = min(middle_start + 20, len(cleaned_lines) - 10)

        selected_lines = (
            cleaned_lines[:start_lines]
            + ["\n... [middle content omitted] ..."]
            + cleaned_lines[middle_start:middle_end]
        )

        result = "\n".join(selected_lines)

    # Final token check and truncate if needed
    final_tokens = count_tokens(result, model)
    if final_tokens > tokens:
        return truncate_text_to_tokens(result, tokens, model, add_warning=False)

    current_tokens = count_tokens(content, model)
    return result + f"\n\n[File content truncated: {current_tokens:,} → {tokens + 30:,} tokens]"


def _truncate_grep_output(content: str, tokens: int, model: str) -> str:
    """
    Smart truncate grep output, keeping diverse matches.
    """
    lines = content.splitlines()

    if len(lines) <= 20:
        return truncate_text_to_tokens(content, tokens, model, add_warning=False)

    # Group by file (grep output format: "filename:line:content")
    file_matches: dict[str, list[str]] = {}
    for line in lines:
        if ":" in line:
            parts = line.split(":", 2)
            if len(parts) >= 3:
                filename = parts[0]
                if filename not in file_matches:
                    file_matches[filename] = []
                file_matches[filename].append(line)

    # Take first few matches from each file to ensure diversity
    selected_lines = []
    for filename, matches in list(file_matches.items())[:10]:  # Max 10 files
        selected_lines.extend(matches[: max(3, tokens // 100)])  # 3 matches per file average
        if count_tokens("\n".join(selected_lines), model) > tokens * 0.8:
            break

    result = "\n".join(selected_lines)

    # Final check
    if count_tokens(result, model) > tokens:
        result = truncate_text_to_tokens(result, tokens, model, add_warning=False)

    return result + f"\n\n[Grep output truncated from {len(lines)} lines]"


def _truncate_directory_listing(content: str, tokens: int, model: str) -> str:
    """
    Smart truncate directory listings, showing structure but limiting entries.
    """
    lines = content.splitlines()

    if len(lines) <= 50:
        return content

    # Keep structure (directories first, then sample files)
    dirs = []
    files = []

    for line in lines:
        if line.strip().endswith("/") or "directory" in line.lower():
            dirs.append(line)
        else:
            files.append(line)

    # Keep all directories (usually fewer) and sample of files
    selected = dirs[:50] + files[: max(50, int(tokens / 10))]
    result = "\n".join(selected)

    # Add warning about truncation
    return result + f"\n\n[Directory listing truncated: {len(lines)} → {len(selected)} entries]"


def _truncate_command_output(content: str, tokens: int, model: str) -> str:
    """
    Smart truncate command output, keeping headers, errors, and beginning/end.
    """
    lines = content.splitlines()

    if len(lines) <= 100:
        return content

    # Look for important patterns: errors, headers, summaries
    important_lines = []
    normal_lines = []

    for line in lines:
        line_lower = line.lower()
        if any(
            pattern in line_lower
            for pattern in [
                "error",
                "failed",
                "warning",
                "exception",
                "traceback",
                "summary:",
                "total:",
                "count:",
                "usage:",
                "status:",
            ]
        ):
            important_lines.append(line)
        else:
            normal_lines.append(line)

    # Keep important lines + beginning and end of normal output
    selected = (
        important_lines[:50]
        + normal_lines[: max(20, int(tokens * 0.3 / 4))]  # First portion
        + normal_lines[-max(20, int(tokens * 0.3 / 4)) :]  # Last portion
    )

    result = "\n".join(selected)

    # Final check
    if count_tokens(result, model) > tokens:
        result = truncate_text_to_tokens(result, tokens, model, add_warning=False)

    return result + f"\n\n[Command output truncated from {len(lines)} lines]"


def _truncate_webpage_content(content: str, tokens: int, model: str) -> str:
    """
    Smart truncate webpage content, focusing on main content vs structure.
    """
    # For web content, try to keep text content over HTML/structure
    try:
        # Simple heuristic: look for text content vs HTML tags
        if content.count("<") > content.count(" ") * 0.1:
            # Looks like HTML, try to extract text
            import re

            text_content = re.sub(r"<[^>]+>", " ", content)
            text_content = re.sub(r"\s+", " ", text_content).strip()
            if len(text_content) > len(content) * 0.3:
                content = text_content
    except Exception:
        pass  # Fallback to original content

    return truncate_text_to_tokens(content, tokens, model, add_warning=True)


def _truncate_find_replace_output(content: str, tokens: int, model: str) -> str:
    """
    Smart truncate find/replace output, keeping summary and sample changes.
    """
    # Look for summary line (usually at beginning or end)
    lines = content.splitlines()

    summary_lines = []
    diff_lines = []

    for line in lines:
        if "files" in line.lower() and any(
            word in line.lower()
            for word in ["changed", "modified", "processed", "found", "replaced"]
        ):
            summary_lines.append(line)
        elif line.startswith(("+", "-", " ")) and len(line.strip()) > 0:
            diff_lines.append(line)

    # Keep all summaries and sample of diffs
    result_lines = summary_lines[:]
    if len(diff_lines) > 0:
        # Take first and last diff sections
        result_lines.extend(diff_lines[: max(50, int(tokens / 5))])
        if len(diff_lines) > 100:
            result_lines.append("... [additional diffs omitted] ...")
            result_lines.extend(diff_lines[-50:])

    result = "\n".join(result_lines)

    # Final check
    if count_tokens(result, model) > tokens:
        result = truncate_text_to_tokens(result, tokens, model, add_warning=False)

    return result


def get_max_tool_result_tokens() -> int:
    """
    Get the maximum tokens allowed for tool results from environment variable.

    Returns:
        Maximum token limit for tool results (default: 10000)
    """
    try:
        max_tokens = int(os.environ.get("CLIPPY_MAX_TOOL_RESULT_TOKENS", "10000"))
        return max(1000, max_tokens)  # Minimum 1000 tokens
    except (ValueError, TypeError):
        return 10000


def format_over_size_warning(
    tool_name: str,
    original_tokens: int,
    truncated_tokens: int,
    max_allowed: int,
) -> str:
    """
    Format a warning message for oversized tool results.

    Args:
        tool_name: Name of the tool
        original_tokens: Original token count
        truncated_tokens: Final token count after truncation
        max_allowed: Maximum allowed tokens

    Returns:
        Formatted warning message
    """
    return (
        f"⚠️ Tool result from '{tool_name}' was trimmed due to size:\n"
        f"   Original: {original_tokens:,} tokens\n"
        f"   Truncated to: {truncated_tokens:,} tokens\n"
        f"   Limit: {max_allowed:,} tokens\n"
        f"   Set CLIPPY_MAX_TOOL_RESULT_TOKENS to adjust this limit."
    )
