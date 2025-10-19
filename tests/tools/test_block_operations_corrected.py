"""Test corrected block operations for edit_file tool."""

import os
import tempfile

from clippy.tools.edit_file import edit_file


def test_current_behavior():
    """Test what the current implementation actually does."""
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

        print("Success:", success)
        print("Message:", message)

        # Verify the content
        with open(temp_path) as f:
            actual = f.read()
        print("Actual result:")
        print(repr(actual))
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    test_current_behavior()
