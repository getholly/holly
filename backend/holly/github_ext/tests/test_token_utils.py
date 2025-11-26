"""Tests for token counting utilities."""

import tempfile
from pathlib import Path
from unittest import mock

import pytest

from holly.github_ext.models import RepositoryDetail
from holly.github_ext.token_utils import (
    build_file_token_counts,
    count_file_tokens,
)


@pytest.fixture
def temp_text_file():
    """Fixture to create a temporary text file."""
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as tmp_file:
        tmp_file.write(b"This is a sample text to count tokens")
        tmp_file.flush()
        tmp_path = Path(tmp_file.name)
    yield tmp_path
    tmp_path.unlink()  # Clean up after test


@mock.patch("githubme.github_ext.token_utils.count_tokens")
def test_count_file_tokens(mock_count_tokens, temp_text_file):
    """Test counting tokens in a text file."""
    mock_count_tokens.return_value = 42

    result = count_file_tokens(temp_text_file)

    mock_count_tokens.assert_called_once()
    assert result == 42


@pytest.fixture
def temp_directory():
    """Fixture to create a temporary directory with files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        repo_path = Path(tmp_dir)

        (repo_path / "file1.txt").touch()
        (repo_path / "file2.py").touch()
        (repo_path / "file3.js").touch()
        (repo_path / "binary_file.bin").touch()

        yield repo_path


@mock.patch("githubme.github_ext.token_utils.count_file_tokens")
def test_build_file_token_counts(mock_count_file_tokens, temp_directory):
    """Test building token counts for a directory."""
    mock_count_file_tokens.side_effect = lambda path, model=None: {
        "file1.txt": 10,
        "file2.py": 20,
        "file3.js": 30,
    }.get(path.name, 0)

    result = build_file_token_counts(temp_directory)

    assert len(result) == 3  # Only text files should be counted
    assert result["file1.txt"] == 10
    assert result["file2.py"] == 20
    assert result["file3.js"] == 30
    assert "binary_file.bin" not in result


@pytest.mark.django_db
def test_file_token_counts_field():
    """Test the file_token_counts field in RepositoryDetail model."""
    file_tree = [
        {
            "name": "root",
            "path": "",
            "is_dir": True,
            "children": [
                {"name": "file1.txt", "path": "file1.txt", "is_dir": False},
                {
                    "name": "file2.py",
                    "path": "file2.py",
                    "is_dir": False,
                },
                {
                    "name": "dir",
                    "path": "dir",
                    "is_dir": True,
                    "children": [
                        {"name": "file3.js", "path": "dir/file3.js", "is_dir": False},
                    ],
                },
            ],
        },
    ]

    repo = RepositoryDetail.objects.create(
        username="test_user",
        repo="test_repo",
        file_tree=file_tree,
        file_token_counts={
            "file1.txt": 100,
            "file2.py": 200,
            "dir/file3.js": 300,
        },
    )

    assert repo.file_token_counts["file1.txt"] == 100
    assert repo.file_token_counts["file2.py"] == 200
    assert repo.file_token_counts["dir/file3.js"] == 300
    assert repo.get_total_token_count() == 600

    repo.file_token_counts["file4.md"] = 400
    repo.save()

    repo_reloaded = RepositoryDetail.objects.get(pk=repo.pk)
    assert repo_reloaded.file_token_counts["file4.md"] == 400
    assert repo_reloaded.get_total_token_count() == 1000
