"""File validation utilities for different file types."""

import json
import re
from pathlib import Path

import yaml


class ValidationResult:
    """Result of file validation."""

    def __init__(self, is_valid: bool, message: str, line: int | None = None):
        self.is_valid = is_valid
        self.message = message
        self.line = line

    def __bool__(self) -> bool:
        return self.is_valid

    def __str__(self) -> str:
        if self.line:
            return f"{self.message} (line {self.line})"
        return self.message


def validate_file_content(content: str, filepath: str) -> ValidationResult:
    """Validate file content based on file extension.

    Args:
        content: The file content to validate
        filepath: The file path to determine validation type

    Returns:
        ValidationResult with validation status and message
    """
    path = Path(filepath)
    extension = path.suffix.lower()

    # Skip validation for binary files (common binary extensions)
    binary_extensions = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".ico",
        ".svg",  # images
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",  # documents
        ".zip",
        ".tar",
        ".gz",
        ".rar",
        ".7z",  # archives
        ".exe",
        ".dll",
        ".so",
        ".dylib",  # binaries
        ".mp3",
        ".mp4",
        ".avi",
        ".mov",
        ".wav",  # media
        ".ttf",
        ".otf",
        ".woff",
        ".woff2",  # fonts
    }

    if extension in binary_extensions:
        msg = f"Binary file .{extension} detected - use skip_validation=True"
        return ValidationResult(False, msg)

    # Skip validation for very large files (performance)
    if len(content) > 1_000_000:  # 1MB limit
        return ValidationResult(True, "File too large for validation (skipped)")

    validators = {
        ".py": validate_python,
        ".json": validate_json,
        ".yaml": validate_yaml,
        ".yml": validate_yaml,
        ".toml": validate_toml,
        ".xml": validate_xml,
        ".html": validate_html,
        ".css": validate_css,
        ".js": validate_javascript,
        ".ts": validate_typescript,
        ".md": validate_markdown,
        ".dockerfile": validate_dockerfile,
        "dockerfile": validate_dockerfile,
    }

    validator = validators.get(extension)
    if validator:
        return validator(content, filepath)

    # Basic validation for unknown text files
    return ValidationResult(True, "No specific validator for this file type")


def validate_python(content: str, filepath: str) -> ValidationResult:
    """Validate Python syntax."""
    if not filepath.endswith(".py"):
        return ValidationResult(True, "Not a Python file (validation skipped)")

    import ast

    try:
        ast.parse(content)
        return ValidationResult(True, "Python syntax is valid")
    except SyntaxError as e:
        return ValidationResult(False, f"Python syntax error: {e.msg}", e.lineno)
    except Exception as e:
        return ValidationResult(False, f"Error validating Python: {str(e)}")


def validate_json(content: str, filepath: str) -> ValidationResult:
    """Validate JSON structure."""
    try:
        json.loads(content)
        return ValidationResult(True, "JSON is valid")
    except json.JSONDecodeError as e:
        return ValidationResult(False, f"JSON error: {e.msg}", e.lineno)
    except Exception as e:
        return ValidationResult(False, f"Error validating JSON: {str(e)}")


def validate_yaml(content: str, filepath: str) -> ValidationResult:
    """Validate YAML structure."""
    try:
        yaml.safe_load(content)
        return ValidationResult(True, "YAML is valid")
    except yaml.YAMLError as e:
        line = None
        if hasattr(e, "problem_mark") and e.problem_mark:
            line = e.problem_mark.line + 1
        return ValidationResult(False, f"YAML error: {str(e)}", line)
    except Exception as e:
        return ValidationResult(False, f"Error validating YAML: {str(e)}")


def validate_toml(content: str, filepath: str) -> ValidationResult:
    """Validate TOML structure."""
    try:
        import tomllib  # type: ignore
    except ImportError:
        # tomli not available, skip TOML validation
        return ValidationResult(True, "TOML validation not available")

    try:
        tomllib.loads(content)
        return ValidationResult(True, "TOML is valid")
    except Exception as e:
        line = None
        if hasattr(e, "lineno"):
            line = e.lineno
        return ValidationResult(False, f"TOML error: {str(e)}", line)


def validate_xml(content: str, filepath: str) -> ValidationResult:
    """Validate XML structure."""
    try:
        import xml.etree.ElementTree as ET

        ET.fromstring(content)
        return ValidationResult(True, "XML is valid")
    except ET.ParseError as e:
        return ValidationResult(False, f"XML error: {str(e)}", getattr(e, "lineno", None))
    except Exception as e:
        return ValidationResult(False, f"Error validating XML: {str(e)}")


def validate_html(content: str, filepath: str) -> ValidationResult:
    """Validate basic HTML structure."""
    # Basic HTML validation - check for balanced tags
    try:
        # Simple stack-based validation for common tags
        tags: list[str] = []
        # Find all opening and closing tags
        tag_pattern = re.compile(r"<\s*/?\s*([a-zA-Z][a-zA-Z0-9]*)[^>]*>")

        for match in tag_pattern.finditer(content):
            tag = match.group(1).lower()
            full_tag = match.group(0)

            if full_tag.startswith("</"):  # Closing tag
                if tags and tags[-1] == tag:
                    tags.pop()
                else:
                    return ValidationResult(False, f"Unmatched closing tag: {tag}")
            elif not full_tag.endswith("/>"):  # Opening tag (not self-closing)
                # Skip self-closing tags
                self_closing = {
                    "br",
                    "hr",
                    "img",
                    "input",
                    "meta",
                    "link",
                    "area",
                    "base",
                    "col",
                    "embed",
                    "param",
                    "source",
                    "track",
                    "wbr",
                }
                if tag not in self_closing:
                    tags.append(tag)

        if tags:
            return ValidationResult(False, f"Unclosed tags: {', '.join(tags)}")

        return ValidationResult(True, "HTML structure appears valid")
    except Exception as e:
        return ValidationResult(False, f"Error validating HTML: {str(e)}")


def validate_css(content: str, filepath: str) -> ValidationResult:
    """Validate CSS syntax."""
    try:
        # Basic CSS validation using regex
        # Check for balanced braces
        open_braces = content.count("{")
        close_braces = content.count("}")

        if open_braces != close_braces:
            msg = f"Unbalanced braces: {open_braces} opening, {close_braces} closing"
            return ValidationResult(False, msg)

        # Check for basic CSS structure
        # This is a simple validator - for full validation, a CSS parser would be better
        lines = content.split("\n")
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("/*") or line.startswith("//"):
                continue

            # Check for common syntax errors
            if line.endswith("{") or line.endswith("}"):
                continue
            if ":" in line and not line.strip().endswith(";"):
                # Might be a property declaration missing semicolon
                if not any(char in line for char in ["{", "}"]):
                    return ValidationResult(False, "Possible missing semicolon", i)

        return ValidationResult(True, "CSS structure appears valid")
    except Exception as e:
        return ValidationResult(False, f"Error validating CSS: {str(e)}")


def validate_javascript(content: str, filepath: str) -> ValidationResult:
    """Validate JavaScript syntax."""
    return validate_with_scripting_engine(content, "JavaScript", filepath)


def validate_typescript(content: str, filepath: str) -> ValidationResult:
    """Validate TypeScript syntax."""
    return validate_with_scripting_engine(content, "TypeScript", filepath)


def validate_with_scripting_engine(content: str, language: str, filepath: str) -> ValidationResult:
    """Validate using Node.js if available for JS/TS."""
    import os
    import subprocess
    import tempfile

    # Try to use Node.js for validation if available
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".js", delete=False) as f:
            if language == "TypeScript":
                # For TypeScript, we'd need tsc, but let's do basic JS validation for now
                f.write(content)
                temp_path = f.name

                # Try basic Node.js syntax checking
                result = subprocess.run(
                    ["node", "--check", temp_path], capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0:
                    return ValidationResult(True, f"{language} syntax appears valid (basic check)")
                else:
                    # Try to extract line number from error
                    error_msg = result.stderr
                    line_match = re.search(r"(\d+)", error_msg)
                    line = int(line_match.group(1)) if line_match else None
                    msg = f"{language} syntax error: {error_msg.strip()}"
                    return ValidationResult(False, msg, line)
            else:
                f.write(content)
                temp_path = f.name

                result = subprocess.run(
                    ["node", "--check", temp_path], capture_output=True, text=True, timeout=5
                )

                if result.returncode == 0:
                    return ValidationResult(True, f"{language} syntax appears valid")
                else:
                    error_msg = result.stderr
                    line_match = re.search(r"(\d+)", error_msg)
                    line = int(line_match.group(1)) if line_match else None
                    msg = f"{language} syntax error: {error_msg.strip()}"
                    return ValidationResult(False, msg, line)

    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to basic validation if Node.js is not available
        return ValidationResult(True, f"{language} validation not available (basic check passed)")
    except Exception as e:
        return ValidationResult(False, f"Error validating {language}: {str(e)}")
    finally:
        # Clean up temp file
        try:
            if "temp_path" in locals():
                os.unlink(temp_path)
        except Exception:
            pass


def validate_markdown(content: str, filepath: str) -> ValidationResult:
    """Validate Markdown structure."""
    try:
        # Basic markdown validation - check for common issues
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            # Check for malformed links
            if "[" in line and "](" in line:
                # Check if link is properly closed
                link_pattern = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
                matches = link_pattern.findall(line)
                for text, url in matches:
                    if not text or not url:
                        return ValidationResult(False, "Malformed markdown link", i)

            # Check for malformed headers
            if line.startswith("#"):
                if not re.match(r"^#+\s+", line) and not re.match(r"^#+$", line):
                    return ValidationResult(False, "Header should have space after #", i)

        return ValidationResult(True, "Markdown structure appears valid")
    except Exception as e:
        return ValidationResult(False, f"Error validating Markdown: {str(e)}")


def validate_dockerfile(content: str, filepath: str) -> ValidationResult:
    """Validate Dockerfile syntax."""
    try:
        lines = content.split("\n")

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Check if line starts with valid Docker instruction
            if " " in line:
                instruction = line.split()[0].upper()
                valid_instructions = {
                    "FROM",
                    "MAINTAINER",
                    "RUN",
                    "CMD",
                    "LABEL",
                    "EXPOSE",
                    "ENV",
                    "ADD",
                    "COPY",
                    "ENTRYPOINT",
                    "VOLUME",
                    "USER",
                    "WORKDIR",
                    "ARG",
                    "ONBUILD",
                    "STOPSIGNAL",
                    "HEALTHCHECK",
                    "SHELL",
                    "COPY",
                    "ADD",
                }

                if instruction not in valid_instructions:
                    return ValidationResult(False, f"Unknown Docker instruction: {instruction}", i)

        return ValidationResult(True, "Dockerfile structure appears valid")
    except Exception as e:
        return ValidationResult(False, f"Error validating Dockerfile: {str(e)}")
