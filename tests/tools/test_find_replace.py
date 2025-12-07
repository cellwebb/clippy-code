"""Tests for find_replace tool."""

from pathlib import Path

from clippy.tools.find_replace import (
    TOOL_SCHEMA,
    collect_files,
    find_replace,
    prepare_pattern,
    preview_changes,
    process_file,
    should_include_file,
)


class TestFindReplace:
    """Test the main find_replace function."""

    def test_find_replace_basic_dry_run(self, tmp_path):
        """Test basic find/replace in dry run mode."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world\nHello again\nGoodbye world")

        success, message, result = find_replace(
            pattern="Hello", replacement="Hi", paths=[str(test_file)], dry_run=True
        )

        assert success
        assert "would make" in message
        assert result["dry_run"] is True
        assert result["total_replacements"] == 2
        assert result["files_with_changes"] == 1
        # File should not be modified in dry run
        assert test_file.read_text() == "Hello world\nHello again\nGoodbye world"

    def test_find_replace_basic_apply_changes(self, tmp_path):
        """Test basic find/replace actually applying changes."""
        # Create test file
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world\nHello again\nGoodbye world")

        success, message, result = find_replace(
            pattern="Hello", replacement="Hi", paths=[str(test_file)], dry_run=False
        )

        assert success
        assert "made" in message
        assert result["dry_run"] is False
        assert result["total_replacements"] == 2
        assert result["files_with_changes"] == 1
        # File should be modified
        assert test_file.read_text() == "Hi world\nHi again\nGoodbye world"

    def test_find_replace_regex_pattern(self, tmp_path):
        """Test find/replace with regex pattern."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("item1, item2, item3\nNumber: 42\nNumber: 123")

        success, message, result = find_replace(
            pattern=r"Number: (\d+)",
            replacement="Number: \\1",
            paths=[str(test_file)],
            regex=True,
            dry_run=True,
        )

        assert success
        assert result["total_replacements"] == 2

    def test_find_replace_case_sensitive(self, tmp_path):
        """Test case sensitive matching."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello hello HELLO")

        # Case insensitive (default)
        success, message, result = find_replace(
            pattern="hello",
            replacement="hi",
            paths=[str(test_file)],
            case_sensitive=False,
            dry_run=True,
        )
        assert result["total_replacements"] == 3

        # Case sensitive
        success, message, result = find_replace(
            pattern="hello",
            replacement="hi",
            paths=[str(test_file)],
            case_sensitive=True,
            dry_run=True,
        )
        assert result["total_replacements"] == 1

    def test_find_replace_with_backup(self, tmp_path):
        """Test find/replace with backup creation."""
        test_file = tmp_path / "test.txt"
        original_content = "Hello world"
        test_file.write_text(original_content)

        backup_file = tmp_path / "test.txt.bak"

        success, message, result = find_replace(
            pattern="Hello", replacement="Hi", paths=[str(test_file)], dry_run=False, backup=True
        )

        assert success
        assert backup_file.exists()
        assert backup_file.read_text() == original_content
        assert test_file.read_text() == "Hi world"

    def test_find_replace_no_files_found(self, tmp_path):
        """Test when no files match the pattern."""
        success, message, result = find_replace(
            pattern="test", replacement="replacement", paths=["nonexistent.txt"], dry_run=True
        )

        assert not success
        assert "No files found" in message
        assert result is None

    def test_find_replace_invalid_regex(self, tmp_path):
        """Test with invalid regex pattern."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test content")

        success, message, result = find_replace(
            pattern="[invalid regex",
            replacement="replacement",
            paths=[str(test_file)],
            regex=True,
            dry_run=True,
        )

        assert not success
        assert "Invalid regular expression" in message
        assert result is None

    def test_find_replace_include_patterns(self, tmp_path):
        """Test with include file patterns."""
        # Create multiple files
        py_file = tmp_path / "test.py"
        py_file.write_text("Hello world")
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("Hello world")
        js_file = tmp_path / "test.js"
        js_file.write_text("Hello world")

        success, message, result = find_replace(
            pattern="Hello",
            replacement="Hi",
            paths=[str(tmp_path)],
            include_patterns=["*.py"],
            dry_run=True,
        )

        assert success
        assert result["files_processed"] == 1
        assert result["total_replacements"] == 1

    def test_find_replace_exclude_patterns(self, tmp_path):
        """Test with exclude file patterns."""
        # Create multiple files
        py_file = tmp_path / "test.py"
        py_file.write_text("Hello world")
        test_py_file = tmp_path / "test_test.py"
        test_py_file.write_text("Hello world")

        success, message, result = find_replace(
            pattern="Hello",
            replacement="Hi",
            paths=[str(tmp_path)],
            include_patterns=["*.py"],
            exclude_patterns=["test_*.py"],
            dry_run=True,
        )

        assert success
        assert result["files_processed"] == 1
        assert result["total_replacements"] == 1

    def test_find_replace_max_file_size(self, tmp_path):
        """Test max file size filtering."""
        # Create a large file
        large_file = tmp_path / "large.txt"
        large_file.write_bytes(b"x" * 200)  # 200 bytes
        small_file = tmp_path / "small.txt"
        small_file.write_bytes(b"x" * 50)  # 50 bytes

        success, message, result = find_replace(
            pattern="x",
            replacement="y",
            paths=[str(tmp_path)],
            max_file_size=100,  # Only process files <= 100 bytes
            dry_run=True,
        )

        assert success
        assert result["files_processed"] == 1  # Only small file processed


class TestCollectFiles:
    """Test file collection functionality."""

    def test_collect_files_single_file(self, tmp_path):
        """Test collecting a single file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        files = collect_files([str(test_file)], ["*"], [], 10485760)

        assert len(files) == 1
        assert files[0] == test_file

    def test_collect_files_directory(self, tmp_path):
        """Test collecting files from directory."""
        (tmp_path / "file1.txt").write_text("content1")
        (tmp_path / "file2.py").write_text("content2")
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        files = collect_files([str(tmp_path)], ["*.txt"], [], 10485760)

        assert len(files) == 2
        file_names = [f.name for f in files]
        assert "file1.txt" in file_names
        assert "file3.txt" in file_names
        assert "file2.py" not in file_names

    def test_collect_files_glob_pattern(self, tmp_path):
        """Test collecting files with glob pattern."""
        # Change working directory for glob pattern to work
        old_cwd = Path.cwd()
        try:
            (tmp_path / "test1.txt").write_text("content1")
            (tmp_path / "test2.txt").write_text("content2")
            (tmp_path / "other.py").write_text("content3")

            # Change to tmp_path directory for relative glob patterns
            import os

            os.chdir(tmp_path)

            files = collect_files(["test*.txt"], ["*"], [], 10485760)

            assert len(files) == 2
        finally:
            os.chdir(old_cwd)

    def test_collect_files_exclude_patterns(self, tmp_path):
        """Test file exclusion patterns."""
        (tmp_path / "good.txt").write_text("content")
        (tmp_path / "bad.txt").write_text("content")
        (tmp_path / "temp.txt").write_text("content")

        files = collect_files([str(tmp_path)], ["*.txt"], ["bad.txt"], 10485760)

        file_names = [f.name for f in files]
        assert "good.txt" in file_names
        assert "temp.txt" in file_names
        assert "bad.txt" not in file_names


class TestShouldIncludeFile:
    """Test file inclusion/exclusion logic."""

    def test_should_include_file_no_exclusions(self, tmp_path):
        """Test file inclusion when no exclusion patterns."""
        test_file = tmp_path / "test.txt"

        assert should_include_file(test_file, []) is True

    def test_should_include_file_with_exclusions(self, tmp_path):
        """Test file exclusion by pattern."""
        test_file = tmp_path / "test.txt"

        assert should_include_file(test_file, ["*.txt"]) is False
        assert should_include_file(test_file, ["test.*"]) is False
        assert should_include_file(test_file, ["*.py"]) is True

    def test_should_include_file_path_contains_exclusion(self, tmp_path):
        """Test file exclusion by pattern matching."""
        test_file = tmp_path / "subdir" / "test.txt"

        # The function uses path.match() which matches the final path component
        # Will match 'subdir' directory name
        assert should_include_file(test_file, ["subdir"]) is False
        # Will match file name
        assert should_include_file(test_file, ["test.txt"]) is False
        # Won't match .txt file
        assert should_include_file(test_file, ["*.py"]) is True


class TestPreparePattern:
    """Test pattern preparation."""

    def test_prepare_pattern_regex_valid(self):
        """Test preparing valid regex pattern."""
        pattern = prepare_pattern(r"\d+", regex=True, case_sensitive=False)

        assert pattern is not None
        assert pattern.search("abc123def") is not None

    def test_prepare_pattern_regex_invalid(self):
        """Test preparing invalid regex pattern."""
        pattern = prepare_pattern("[invalid", regex=True, case_sensitive=False)

        assert pattern is None

    def test_prepare_pattern_literal(self):
        """Test preparing literal string pattern."""
        pattern = prepare_pattern("test.", regex=False, case_sensitive=False)

        assert pattern is not None
        assert pattern.search("test.") is not None
        # The dot should be escaped, so 'testx' won't match 'test.'
        assert pattern.search("testx") is None
        # But 'test.' should match
        assert pattern.search("test.") is not None

    def test_prepare_pattern_case_sensitive(self):
        """Test case sensitivity."""
        pattern_sensitive = prepare_pattern("Test", regex=False, case_sensitive=True)
        pattern_insensitive = prepare_pattern("Test", regex=False, case_sensitive=False)

        assert pattern_sensitive.search("test") is None
        assert pattern_sensitive.search("Test") is not None
        assert pattern_insensitive.search("test") is not None
        assert pattern_insensitive.search("Test") is not None


class TestProcessFile:
    """Test single file processing."""

    def test_process_file_no_changes(self, tmp_path):
        """Test processing file with no matches."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")
        pattern = prepare_pattern("xyz", regex=False, case_sensitive=False)

        result = process_file(test_file, pattern, "replacement", False, True, False)

        assert result["changes_found"] is False
        assert result["replacements_made"] == 0

    def test_process_file_with_changes_dry_run(self, tmp_path):
        """Test processing file with matches in dry run."""
        test_file = tmp_path / "test.txt"
        original_content = "Hello world\nHello again"
        test_file.write_text(original_content)
        pattern = prepare_pattern("Hello", regex=False, case_sensitive=False)

        result = process_file(test_file, pattern, "Hi", False, True, False)

        assert result["changes_found"] is True
        assert result["replacements_made"] == 2
        assert len(result["lines_changed"]) == 2
        # File should not be modified in dry run
        assert test_file.read_text() == original_content

    def test_process_file_with_changes_apply(self, tmp_path):
        """Test processing file with matches and applying changes."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world\nHello again")
        pattern = prepare_pattern("Hello", regex=False, case_sensitive=False)

        result = process_file(test_file, pattern, "Hi", False, False, False)

        assert result["changes_found"] is True
        assert result["replacements_made"] == 2
        # File should be modified
        assert test_file.read_text() == "Hi world\nHi again"

    def test_process_file_with_backup(self, tmp_path):
        """Test processing file with backup creation."""
        test_file = tmp_path / "test.txt"
        original_content = "Hello world"
        test_file.write_text(original_content)
        backup_file = tmp_path / "test.txt.bak"
        pattern = prepare_pattern("Hello", regex=False, case_sensitive=False)

        result = process_file(test_file, pattern, "Hi", False, False, True)

        assert result["changes_found"] is True
        assert result["backup_created"] is True
        assert backup_file.exists()
        assert backup_file.read_text() == original_content

    def test_process_file_unicode_error(self, tmp_path):
        """Test processing binary file (Unicode decode error)."""
        test_file = tmp_path / "binary.bin"
        # Write actual binary content that will cause Unicode decode error
        test_file.write_bytes(b"\xff\xfe\x00\x00")  # UTF-16 BOM causes issues with UTF-8 reading
        pattern = prepare_pattern("test", regex=False, case_sensitive=False)

        result = process_file(test_file, pattern, "replacement", False, True, False)

        assert result["changes_found"] is False
        # The function returns the base result structure even on decode errors
        assert "error" in result or result["changes_found"] is False

    def test_process_file_regex_replacement(self, tmp_path):
        """Test regex replacement with backreferences."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Name: John, Name: Jane")
        pattern = prepare_pattern(r"Name: (\w+)", regex=True, case_sensitive=False)

        result = process_file(test_file, pattern, r"Name: \1 Smith", True, False, False)

        assert result["changes_found"] is True
        assert result["replacements_made"] == 2
        assert test_file.read_text() == "Name: John Smith, Name: Jane Smith"

    def test_process_file_diff_generation(self, tmp_path):
        """Test diff generation in file processing."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Line 1\nLine 2\nLine 3")
        pattern = prepare_pattern("Line", regex=False, case_sensitive=False)

        result = process_file(test_file, pattern, "Row", False, True, False)

        assert result["diff"] != ""
        assert "---" in result["diff"]  # Diff header
        assert "+++" in result["diff"]  # Diff header


class TestPreviewChanges:
    """Test preview functionality."""

    def test_preview_changes_basic(self, tmp_path):
        """Test basic preview generation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world\nHello again")

        preview = preview_changes(pattern="Hello", paths=[str(test_file)])

        assert preview["files_count"] == 1
        assert len(preview["sample_matches"]) == 1
        assert preview["sample_matches"][0]["matches_count"] == 2
        assert preview["sample_matches"][0]["sample_lines"] == [1, 2]

    def test_preview_changes_no_matches(self, tmp_path):
        """Test preview when no matches found."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello world")

        preview = preview_changes(pattern="xyz", paths=[str(test_file)])

        assert preview["files_count"] == 1
        assert len(preview["sample_matches"]) == 0

    def test_preview_changes_multiple_files(self, tmp_path):
        """Test preview with multiple files."""
        (tmp_path / "file1.txt").write_text("Hello world")
        (tmp_path / "file2.txt").write_text("Hello again")

        preview = preview_changes(
            pattern="Hello", paths=[str(tmp_path)], include_patterns=["*.txt"]
        )

        assert preview["files_count"] == 2
        assert len(preview["sample_matches"]) == 2

    def test_preview_changes_error_handling(self, tmp_path):
        """Test preview error handling."""
        preview = preview_changes(pattern="test", paths=["nonexistent/file.txt"])

        # The function returns empty result for non-existent paths, not error
        assert "files_count" in preview
        assert preview["files_count"] == 0
        assert preview["sample_matches"] == []


class TestToolSchema:
    """Test the tool schema definition."""

    def test_tool_schema_structure(self):
        """Test that the tool schema has the correct structure."""
        assert TOOL_SCHEMA["type"] == "function"
        assert "function" in TOOL_SCHEMA
        assert TOOL_SCHEMA["function"]["name"] == "find_replace"
        assert "description" in TOOL_SCHEMA["function"]
        assert "parameters" in TOOL_SCHEMA["function"]

        parameters = TOOL_SCHEMA["function"]["parameters"]
        assert parameters["type"] == "object"
        assert "properties" in parameters
        assert "required" in parameters

        # Check required parameters
        required = ["pattern", "replacement", "paths"]
        assert set(parameters["required"]) == set(required)

        # Check properties
        properties = parameters["properties"]
        all_props = [
            "pattern",
            "replacement",
            "paths",
            "regex",
            "case_sensitive",
            "dry_run",
            "include_patterns",
            "exclude_patterns",
            "max_file_size",
            "backup",
        ]
        for prop in all_props:
            assert prop in properties

        # Check types
        assert properties["pattern"]["type"] == "string"
        assert properties["replacement"]["type"] == "string"
        assert properties["paths"]["type"] == "array"
        assert properties["regex"]["type"] == "boolean"

        # Check defaults
        assert properties["regex"]["default"] is False
        assert properties["dry_run"]["default"] is True
        assert properties["case_sensitive"]["default"] is False
        assert properties["max_file_size"]["default"] == 10485760
