"""Tests for write_file validation integration."""

import tempfile
from pathlib import Path

from clippy.tools.write_file import write_file


class TestWriteFileValidation:
    """Test write_file with validation."""

    def test_valid_python_file(self):
        valid_code = """
def hello():
    print('Hello, World!')
    return True

if __name__ == '__main__':
    hello()
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            success, message, result = write_file(temp_path, valid_code)
            assert success
            assert "Successfully wrote" in message
            assert "validation" not in message
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_python_file(self):
        invalid_code = """
def hello()
    print('Hello, World!')  # Missing colon
    return True

if __name__ == '__main__':
    hello()
        """

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            success, message, result = write_file(temp_path, invalid_code)
            assert not success
            assert "File validation failed" in message
            assert "Python syntax error" in message
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_valid_json_file(self):
        valid_json = """{
    "name": "test",
    "version": "1.0.0",
    "dependencies": {
        "requests": "^2.0.0"
    }
}"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            success, message, result = write_file(temp_path, valid_json)
            assert success
            assert "Successfully wrote" in message
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_invalid_json_file(self):
        invalid_json = """{
    "name": "test",
    "version": "1.0.0",
    "dependencies": {
        "requests": "^2.0.0"
    1, invalid
}"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            temp_path = f.name

        try:
            success, message, result = write_file(temp_path, invalid_json)
            assert not success
            assert "File validation failed" in message
            assert "JSON error" in message
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_skip_validation_parameter(self):
        invalid_code = "def hello()  # Syntax error"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            # Should fail without skip_validation
            success, message, result = write_file(temp_path, invalid_code, skip_validation=False)
            assert not success

            # Should succeed with skip_validation=True
            success, message, result = write_file(temp_path, invalid_code, skip_validation=True)
            assert success
            assert "validation skipped" in message
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_file_creation_with_validation(self):
        """Test that parent directories are created and validation works."""
        valid_content = '{"test": "content"}'

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir) / "subdir" / "test.json"

            success, message, result = write_file(str(temp_path), valid_content)
            assert success
            assert temp_path.exists()

            # Verify content was written correctly
            with open(temp_path) as f:
                written_content = f.read()
            assert written_content == valid_content

    def test_unsupported_file_type(self):
        """Test that unsupported file types don't get validated but still work."""
        content = "This is just plain text content"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            temp_path = f.name

        try:
            success, message, result = write_file(temp_path, content)
            assert success
            assert "Successfully wrote" in message
        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_large_file_skip_validation(self):
        """Test that very large files skip validation."""
        # Create content larger than 1MB
        large_content = "x" * 1_000_001

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            temp_path = f.name

        try:
            success, message, result = write_file(temp_path, large_content)
            assert success
            # Should not validate due to size
        finally:
            Path(temp_path).unlink(missing_ok=True)
