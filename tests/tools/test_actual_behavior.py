"""Test what the current implementations actually do."""

import os
import tempfile

from clippy.tools.edit_file import edit_file


def test_block_behavior():
    """Test current block behavior."""
    content = """# START
def old_function():
    print("Old implementation")
    return True
# END
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        success, message, result = edit_file(
            path=temp_path,
            operation="block_replace",
            content='def new_function():\n    print("New implementation")\n    return False',
            start_pattern="# START",
            end_pattern="# END",
        )

        print("=== Block Replace ===")
        print("Success:", success)
        print("Message:", message)
        with open(temp_path) as f:
            actual = f.read()
        print("Actual result:")
        print(repr(actual))
    finally:
        os.unlink(temp_path)


def test_block_delete_behavior():
    """Test current block delete behavior."""
    content = """Line before block
# START
def old_function():
    print("Old implementation")
    return True
# END
Line after block
"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        success, message, result = edit_file(
            path=temp_path, operation="block_delete", start_pattern="# START", end_pattern="# END"
        )

        print("\n=== Block Delete ===")
        print("Success:", success)
        print("Message:", message)
        with open(temp_path) as f:
            actual = f.read()
        print("Actual result:")
        print(repr(actual))
    finally:
        os.unlink(temp_path)


def test_regex_behavior():
    """Test current regex behavior."""
    content = """Hello world
Hello python
Hello universe"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        success, message, result = edit_file(
            path=temp_path, operation="replace", pattern="Hello", content="Hi"
        )

        print("\n=== Regex Replace ===")
        print("Success:", success)
        print("Message:", message)
        with open(temp_path) as f:
            actual = f.read()
        print("Actual result:")
        print(repr(actual))
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    test_block_behavior()
    test_block_delete_behavior()
    test_regex_behavior()
