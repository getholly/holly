from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from holly.github_ext.constants import MAX_FILE_SIZE
from holly.github_ext.utils import build_file_tree


@pytest.fixture
def setup_test_directory():
    """Fixture to create a temporary test directory with various files."""
    with TemporaryDirectory() as temp_dir:
        base_path = Path(temp_dir)

        # Create subdirectories
        (base_path / "subdir").mkdir()
        (base_path / ".git").mkdir()  # Should be ignored

        # Create test files
        (base_path / "file1.txt").write_text("This is a test file with some content.", encoding="utf-8")
        (base_path / "file2.log").write_text("Log data sample.", encoding="utf-8")
        (base_path / "subdir" / "nested_file.py").write_text("print('Hello world')", encoding="utf-8")

        # Create a binary file
        (base_path / "binary.bin").write_bytes(b"\x00\xff\x10\x80")

        # Create a large file
        (base_path / "large_file.txt").write_text("X" * (MAX_FILE_SIZE + 1), encoding="utf-8")

        # Create a hidden file
        (base_path / ".hidden_file").write_text("This is hidden", encoding="utf-8")

        # Create a symlink (if supported)
        try:  # noqa: SIM105
            (base_path / "symlink").symlink_to(base_path / "file1.txt")
        except OSError:
            pass  # Symlink creation may not be supported on some OS

        yield base_path


def test_non_existent_directory():
    """Test handling of a non-existent directory."""
    path = Path("/non_existent_directory")
    with pytest.raises(FileNotFoundError):
        build_file_tree(path)


def test_empty_directory():
    """Test with an empty directory."""
    with TemporaryDirectory() as temp_dir:
        assert build_file_tree(Path(temp_dir)) == []


def test_git_directory_exclusion(setup_test_directory):
    """Ensure .git directory is excluded."""
    tree = build_file_tree(setup_test_directory)
    assert not any(node.name == ".git" for node in tree)


def test_file_type_filtering(setup_test_directory):
    """Test filtering by file type."""
    tree = build_file_tree(setup_test_directory, file_types={".txt"})
    assert len(tree) == 1
    assert tree[0].name == "file1.txt"


def test_file_type_filtering_no_match(setup_test_directory):
    """Test filtering with a non-existent file extension."""
    tree = build_file_tree(setup_test_directory, file_types={".md"})
    assert tree == []


def test_search_term_found(setup_test_directory):
    """Test searching for a term within file contents."""
    tree = build_file_tree(setup_test_directory, search_term="test file")
    assert len(tree) == 1
    assert tree[0].name == "file1.txt"


def test_search_term_case_insensitive(setup_test_directory):
    """Ensure search is case insensitive."""
    tree = build_file_tree(setup_test_directory, search_term="TEST FILE")
    assert len(tree) == 1
    assert tree[0].name == "file1.txt"


def test_binary_file_handling(setup_test_directory):
    """Ensure binary files do not cause errors."""
    tree = build_file_tree(setup_test_directory)
    assert all(node.name != "binary.bin" for node in tree)


def test_binary_file_handling_search(setup_test_directory):
    """Ensure binary files do not cause errors."""
    tree = build_file_tree(setup_test_directory, search_term="test")
    assert all(node.name != "binary.bin" for node in tree)


def test_large_file_handling(setup_test_directory):
    """Ensure large files ares skipped."""
    tree = build_file_tree(setup_test_directory, search_term="X")
    assert len(tree) == 0


def test_hidden_file_inclusion(setup_test_directory):
    """Ensure hidden files are included."""
    tree = build_file_tree(setup_test_directory)
    assert any(node.name == ".hidden_file" for node in tree)


def test_symlink_handling(setup_test_directory):
    """Ensure symlinks do not cause infinite loops."""
    tree = build_file_tree(setup_test_directory)
    assert not any(node.name == "symlink" for node in tree)


def test_nested_directory_traversal(setup_test_directory):
    """Ensure nested directories are properly traversed."""
    tree = build_file_tree(setup_test_directory)
    subdir = next((node for node in tree if node.name == "subdir"), None)
    assert subdir
    assert hasattr(subdir, "children")
    assert len(subdir.children) == 1
    assert any(child.name == "nested_file.py" for child in subdir.children)


def test_filename_matching_but_not_content(setup_test_directory):
    """Ensure files are not included just because their filename matches search term."""
    (setup_test_directory / "test_file.txt").write_text("Completely unrelated content", encoding="utf-8")
    tree = build_file_tree(setup_test_directory, search_term="test file")
    assert len(tree) == 1  # Should not include "test_file.txt"


def test_mixed_case_extension_filter(setup_test_directory):
    """Ensure file type filtering works with mixed case extensions."""
    tree = build_file_tree(setup_test_directory, file_types={".TXT"})
    assert len(tree) == 1
    assert tree[0].name == "file1.txt"
