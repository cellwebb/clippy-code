"""Tests for grep flag translation functionality."""

import shlex
from pathlib import Path

from clippy.executor import ActionExecutor
from clippy.tools.grep import translate_grep_flags_to_rg


def test_grep_flag_translation_basic_flags() -> None:
    """Test translation of basic grep flags to ripgrep equivalents."""
    # Test individual flag translations
    assert "--ignore-case" == translate_grep_flags_to_rg("-i")
    assert "--invert-match" == translate_grep_flags_to_rg("-v")
    assert "--word-regexp" == translate_grep_flags_to_rg("-w")
    assert "--line-regexp" == translate_grep_flags_to_rg("-x")

    # Test line number and filename flags
    assert "--line-number" == translate_grep_flags_to_rg("-n")
    assert "--with-filename" == translate_grep_flags_to_rg("-H")
    assert "--no-filename" == translate_grep_flags_to_rg("-h")
    assert "--only-matching" == translate_grep_flags_to_rg("-o")

    # Test file recursion flags
    assert "" == translate_grep_flags_to_rg("-r")
    assert "--files-without-match" == translate_grep_flags_to_rg("-L")

    # Test long form flags remain unchanged
    assert "--ignore-case" == translate_grep_flags_to_rg("--ignore-case")
    assert "--invert-match" == translate_grep_flags_to_rg("--invert-match")
    assert "" == translate_grep_flags_to_rg("--recursive")


def test_grep_flag_translation_context_flags() -> None:
    """Test translation of context-related grep flags."""
    # Test context flag translations with arguments
    assert "--after-context 3" == translate_grep_flags_to_rg("-A 3")
    assert "--before-context 2" == translate_grep_flags_to_rg("-B 2")
    assert "--context 5" == translate_grep_flags_to_rg("-C 5")

    # Test long form context flags
    assert "--after-context 3" == translate_grep_flags_to_rg("--after-context 3")
    assert "--before-context 2" == translate_grep_flags_to_rg("--before-context 2")
    assert "--context 5" == translate_grep_flags_to_rg("--context 5")


def test_grep_flag_translation_include_exclude() -> None:
    """Test translation of --include and --exclude flags."""
    # Test include flag translation
    assert "--glob *.py" == translate_grep_flags_to_rg("--include *.py")
    assert "--glob *.txt" == translate_grep_flags_to_rg("--include *.txt")

    # Test exclude flag translation (ripgrep uses ! prefix for negation)
    assert "--glob !*.log" == translate_grep_flags_to_rg("--exclude *.log")
    assert "--glob !*.tmp" == translate_grep_flags_to_rg("--exclude *.tmp")


def test_grep_flag_translation_multiple_flags() -> None:
    """Test translation of multiple grep flags at once."""
    # Test multiple simple flags
    result = translate_grep_flags_to_rg("-i -v -w")
    expected_flags = {"--ignore-case", "--invert-match", "--word-regexp"}
    result_flags = set(shlex.split(result))
    assert result_flags == expected_flags

    # Test mix of simple and context flags
    result = translate_grep_flags_to_rg("-i -A 3 -n")
    expected_flags = {"--ignore-case", "--after-context", "3", "--line-number"}
    result_flags = set(shlex.split(result))
    assert result_flags == expected_flags

    # Test complex combination
    result = translate_grep_flags_to_rg("--ignore-case --include *.py -B 2")
    expected_flags = {"--ignore-case", "--glob", "*.py", "--before-context", "2"}
    result_flags = set(shlex.split(result))
    assert result_flags == expected_flags


def test_grep_flag_translation_unknown_flags() -> None:
    """Test that unknown flags are passed through unchanged."""
    # Test unknown flag passes through
    assert "--unknown-flag" == translate_grep_flags_to_rg("--unknown-flag")
    assert "-X" == translate_grep_flags_to_rg("-X")

    # Test mix of known and unknown flags
    result = translate_grep_flags_to_rg("-i --unknown-flag -v")
    result_flags = set(shlex.split(result))
    assert result_flags == {"--ignore-case", "--unknown-flag", "--invert-match"}


def test_grep_with_flags_translation(executor: ActionExecutor, temp_dir: str) -> None:
    """Test that grep flags are properly translated when ripgrep is used."""
    # Create a test file with content
    test_file = Path(temp_dir) / "test.txt"
    test_file.write_text("Hello, World!\nThis is a TEST file.\nHello again!")

    # Test grep with case insensitive flag
    success, message, content = executor.execute(
        "grep", {"pattern": "test", "paths": [str(test_file)], "flags": "-i"}
    )

    # Should succeed and find the match
    assert success is True
    assert "TEST file" in content
