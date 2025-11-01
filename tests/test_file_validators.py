"""Tests for file validators."""

import pytest

from clippy.file_validators import (
    ValidationResult,
    validate_css,
    validate_dockerfile,
    validate_file_content,
    validate_html,
    validate_json,
    validate_markdown,
    validate_python,
    validate_yaml,
)


class TestValidationResult:
    """Test ValidationResult class."""

    def test_valid_result(self):
        result = ValidationResult(True, "All good")
        assert result.is_valid
        assert str(result) == "All good"
        assert bool(result)

    def test_invalid_result_with_line(self):
        result = ValidationResult(False, "Syntax error", 42)
        assert not result.is_valid
        assert str(result) == "Syntax error (line 42)"
        assert not bool(result)


class TestPythonValidator:
    """Test Python validation."""

    def test_valid_python(self):
        code = "def hello():\n    print('Hello, World!')"
        result = validate_python(code, "test.py")
        assert result.is_valid
        assert "Python syntax is valid" in result.message

    def test_invalid_python_syntax(self):
        code = "def hello()\n    print('Hello, World!')"  # Missing colon
        result = validate_python(code, "test.py")
        assert not result.is_valid
        assert "Python syntax error" in result.message
        assert result.line == 1

    def test_non_python_file(self):
        code = "not python code"
        result = validate_python(code, "test.txt")
        assert result.is_valid
        assert "Not a Python file" in result.message


class TestJSONValidator:
    """Test JSON validation."""

    def test_valid_json(self):
        content = '{"name": "test", "value": 123}'
        result = validate_json(content, "test.json")
        assert result.is_valid
        assert "JSON is valid" in result.message

    def test_invalid_json(self):
        content = '{"name": "test", "value": 123'  # Missing closing brace
        result = validate_json(content, "test.json")
        assert not result.is_valid
        assert "JSON error" in result.message


class TestYAMLValidator:
    """Test YAML validation."""

    def test_valid_yaml(self):
        content = """
name: test
values:
  - item1
  - item2
        """
        result = validate_yaml(content, "test.yaml")
        assert result.is_valid
        assert "YAML is valid" in result.message

    def test_invalid_yaml_indentation(self):
        content = """
name: test
values:
-item1  # Wrong indentation
        """
        result = validate_yaml(content, "test.yaml")
        assert not result.is_valid
        assert "YAML error" in result.message


class TestHTMLValidator:
    """Test HTML validation."""

    def test_valid_html(self):
        content = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Hello</h1>
    <p>Paragraph</p>
    <img src="test.jpg" />
    <br>
</body>
</html>
        """
        result = validate_html(content, "test.html")
        assert result.is_valid
        assert "HTML structure appears valid" in result.message

    def test_unmatched_closing_tag(self):
        content = "<div><p>Hello</div></p>"  # Tags out of order
        result = validate_html(content, "test.html")
        assert not result.is_valid
        assert "Unmatched closing tag" in result.message

    def test_unclosed_tag(self):
        content = "<div><p>Hello</div>"  # Unclosed p tag
        result = validate_html(content, "test.html")
        assert not result.is_valid
        # The validation might detect this as unmatched closing tag instead
        phrases = ["Unclosed tags", "Unmatched closing tag"]
        assert any(phrase in result.message for phrase in phrases)


class TestCSSValidator:
    """Test CSS validation."""

    def test_valid_css(self):
        content = """
body {
    font-family: Arial, sans-serif;
    margin: 0;
    padding: 20px;
}

h1 {
    color: #333;
    font-size: 24px;
}
        """
        result = validate_css(content, "test.css")
        assert result.is_valid
        assert "CSS structure appears valid" in result.message

    def test_unbalanced_braces(self):
        content = "body { color: red;"  # Missing closing brace
        result = validate_css(content, "test.css")
        assert not result.is_valid
        assert "Unbalanced braces" in result.message

    def test_missing_semicolon(self):
        content = "body { color: red }"  # Missing semicolon
        result = validate_css(content, "test.css")
        # This should pass since it's not always required in CSS
        assert result.is_valid


class TestMarkdownValidator:
    """Test Markdown validation."""

    def test_valid_markdown(self):
        content = """
# Test Document

This is a paragraph with a [link](http://example.com).

## Subsection

- Item 1
- Item 2
        """
        result = validate_markdown(content, "test.md")
        assert result.is_valid
        assert "Markdown structure appears valid" in result.message

    def test_malformed_header(self):
        content = "#No space after hash"  # Missing space
        result = validate_markdown(content, "test.md")
        assert not result.is_valid
        assert "Header should have space after" in result.message

    def test_malformed_link(self):
        content = "[Empty link]()"  # Empty URL
        result = validate_markdown(content, "test.md")
        assert not result.is_valid
        assert "Malformed markdown link" in result.message


class TestDockerfileValidator:
    """Test Dockerfile validation."""

    def test_valid_dockerfile(self):
        content = """
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y python3
WORKDIR /app
COPY . .
CMD ["python3", "app.py"]
        """
        result = validate_dockerfile(content, "Dockerfile")
        assert result.is_valid
        assert "Dockerfile structure appears valid" in result.message

    def test_invalid_dockerfile_instruction(self):
        content = """
FROM ubuntu:20.04
INVALID_COMMAND echo "hello"
        """
        result = validate_dockerfile(content, "Dockerfile")
        assert not result.is_valid
        assert "Unknown Docker instruction" in result.message


class TestFileContentValidation:
    """Test the main file content validation dispatcher."""

    def test_python_file_routing(self):
        python_code = "print('Hello')"
        result = validate_file_content(python_code, "test.py")
        assert result.is_valid

    def test_json_file_routing(self):
        json_content = '{"test": true}'
        result = validate_file_content(json_content, "config.json")
        assert result.is_valid

    def test_yaml_file_routing(self):
        yaml_content = "test: true"
        result = validate_file_content(yaml_content, "config.yaml")
        assert result.is_valid

    def test_yml_file_routing(self):
        yaml_content = "test: true"
        result = validate_file_content(yaml_content, "config.yml")
        assert result.is_valid

    def test_dockerfile_without_extension(self):
        dockerfile_content = "FROM ubuntu:20.04"
        result = validate_file_content(dockerfile_content, "Dockerfile")
        assert result.is_valid

    def test_unknown_extension(self):
        content = "some content"
        result = validate_file_content(content, "test.xyz")
        assert result.is_valid
        assert "No specific validator" in result.message

    def test_large_file_skip_validation(self):
        # Create content larger than 1MB
        large_content = "x" * 1_000_001
        result = validate_file_content(large_content, "test.txt")
        assert result.is_valid
        assert "too large for validation" in result.message

    def test_binary_file_detection(self):
        """Test that binary files are rejected with helpful message."""
        result = validate_file_content("fake image data", "test.png")
        assert not result.is_valid
        assert "Binary file" in result.message
        assert "skip_validation=True" in result.message

    def test_case_insensitive_extensions(self):
        html_content = "<p>Test</p>"
        result = validate_file_content(html_content, "test.HTML")
        assert result.is_valid

        css_content = "body { color: red; }"
        result = validate_file_content(css_content, "style.CSS")
        assert result.is_valid


class TestErrorHandling:
    """Test error handling in validators."""

    def test_python_with_unicode_error(self):
        # Test with content that might cause issues
        problematic_content = "# -*- coding: utf-8 -*-\nprint('Hello \xff World')"
        result = validate_python(problematic_content, "test.py")
        # Should either validate or give clear error
        assert isinstance(result, ValidationResult)

    def test_json_with_trailing_comma(self):
        content = '{"name": "test",}'  # Trailing comma (invalid JSON)
        result = validate_json(content, "test.json")
        assert not result.is_valid
        assert "JSON error" in result.message


class TestValidationIntegration:
    """Test validation integration scenarios."""

    @pytest.mark.parametrize(
        "filename,content,should_pass",
        [
            ("valid.py", "def hello(): pass", True),
            ("invalid.py", "def hello( pass", False),
            ("valid.json", '{"key": "value"}', True),
            ("invalid.json", '{"key": "value"', False),
            ("valid.html", "<p>Hello</p>", True),
            ("invalid.html", "<p>Hello</div>", False),
            ("valid.css", "body { color: red; }", True),
            ("valid.md", "# Title\nContent", True),
            ("invalid.md", "#No Space", False),
            ("valid.yaml", "key: value", True),
            ("Dockerfile", "FROM ubuntu:20.04", True),
        ],
    )
    def test_various_file_types(self, filename, content, should_pass):
        result = validate_file_content(content, filename)
        assert result.is_valid == should_pass
