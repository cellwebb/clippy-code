"""Debug regex test issues."""

import os
import tempfile

from clippy.tools.edit_file import edit_file


def test_regex_basic_debug():
    """Debug basic regex test."""
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

        print("Success:", success)
        print("Message:", message)
        with open(temp_path) as f:
            actual = f.read()
        print("Actual content:")
        print(repr(actual))
        print("Actual content (visible):")
        print(actual)
    finally:
        os.unlink(temp_path)


def test_ignorecase_debug():
    """Debug ignorecase test."""
    content = """HELLO World
hello world
Hello WORLD"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        success, message, result = edit_file(
            path=temp_path,
            operation="replace",
            pattern="hello",
            content="Hi",
            regex_flags=["IGNORECASE"],
        )

        print("\n=== Ignorecase Debug ===")
        print("Success:", success)
        print("Message:", message)
        with open(temp_path) as f:
            actual = f.read()
        print("Actual content:")
        print(repr(actual))
        print("Actual content (visible):")
        print(actual)
    finally:
        os.unlink(temp_path)


def test_word_boundary_debug():
    """Debug word boundary test."""
    content = """The dog is happy
The dogs are happy
hotdog is not a dog"""

    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        success, message, result = edit_file(
            path=temp_path, operation="replace", pattern=r"\bdog\b", content="cat"
        )

        print("\n=== Word Boundary Debug ===")
        print("Success:", success)
        print("Message:", message)
        with open(temp_path) as f:
            actual = f.read()
        print("Actual content:")
        print(repr(actual))
        print("Actual content (visible):")
        print(actual)
    finally:
        os.unlink(temp_path)


if __name__ == "__main__":
    test_regex_basic_debug()
    test_ignorecase_debug()
    test_word_boundary_debug()
