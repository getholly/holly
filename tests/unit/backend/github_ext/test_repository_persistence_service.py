from pathlib import Path

import pytest

from holly.github_ext.models import RepositoryDetail
from holly.github_ext.services.repo_persist import RepositoryPersistenceService
from holly.github_ext.utils import FileNode

# Edge Cases:
# 1. get_repo_details:
#    a. Record does not exist → should return None.
#    b. Record exists and commit_hash matches → should return the object.
#    c. Record exists but commit_hash does not match → should return None.
#
# 2. save_repo_details:
#    a. update_or_create returns a tuple (object, created) → should return the object.

pytestmark = pytest.mark.django_db


@pytest.fixture
def file_tree():
    return [
        FileNode(
            name="root",
            path=Path(),
            is_dir=True,
            children=[
                FileNode(name="file1.txt", path=Path("file1.txt"), is_dir=False),
                FileNode(
                    name="dir1",
                    path=Path("dir1"),
                    is_dir=True,
                    children=[
                        FileNode(name="file2.txt", path=Path("dir1/file2.txt"), is_dir=False),
                    ],
                ),
            ],
        ),
    ]


@pytest.fixture
def file_token_counts():
    return {
        "file1.txt": 10,
        "dir1/file2.txt": 20,
    }


def test_get_repo_details_not_found():
    # Ensure no record exists.
    result = RepositoryPersistenceService.get_repo_details("testuser", "testrepo", "abc123")
    assert result is None


def test_get_repo_details_commit_match(file_tree):
    # Create a record in the DB.
    RepositoryDetail.objects.create(
        username="testuser",
        repo="testrepo",
        commit_hash="abc123",
        file_tree=[file_node.to_dict() for file_node in file_tree],
        file_count=2,
        readme="readme1",
        diagram="diagram1",
        explanation="explanation1",
    )
    # Should return the record since commit_hash matches.
    result = RepositoryPersistenceService.get_repo_details("testuser", "testrepo", "abc123")
    assert result is not None
    assert result.commit_hash == "abc123"
    assert result.file_tree == file_tree


def test_get_repo_details_commit_mismatch(file_tree):
    # Create a record with a different commit_hash.
    RepositoryDetail.objects.create(
        username="testuser",
        repo="testrepo",
        commit_hash="different",
        file_tree=[file_node.to_dict() for file_node in file_tree],
        readme="readme1",
        diagram="diagram1",
        explanation="explanation1",
    )
    # get_repo_details should return None because commit_hash does not match.
    result = RepositoryPersistenceService.get_repo_details("testuser", "testrepo", "abc123")
    assert result is None


def test_save_repo_details_creates_new_record(file_tree, file_token_counts):
    # Save a new record using the persistence service.

    RepositoryPersistenceService.save_repo_details(
        username="testuser",
        repo="testrepo",
        commit_hash="abc123",
        description="description",
        languages={
            "Python": 100,
        },
        stargazers_count=1,
        watchers_count=1,
        forks_count=1,
        open_issues_count=1,
        subscribers_count=1,
        size=1,
        topics=["test"],
        file_tree=file_tree,
        file_count=2,
        readme="readme_new",
        diagram="diagram_new",
        explanation="explanation_new",
        file_token_counts=file_token_counts,
    )
    # Retrieve the record from the DB.
    retrieved = RepositoryDetail.objects.get(username="testuser", repo="testrepo")
    assert retrieved.commit_hash == "abc123"
    assert retrieved.description == "description"
    assert retrieved.languages == {"Python": 100}
    assert retrieved.stargazers_count == 1
    assert retrieved.watchers_count == 1
    assert retrieved.forks_count == 1
    assert retrieved.open_issues_count == 1
    assert retrieved.subscribers_count == 1
    assert retrieved.size == 1
    assert retrieved.topics == ["test"]
    assert retrieved.file_tree == [file_node.to_dict() for file_node in file_tree]
    assert retrieved.file_count == 2
    assert retrieved.readme == "readme_new"
    assert retrieved.diagram == "diagram_new"
    assert retrieved.explanation == "explanation_new"
    assert retrieved.file_token_counts == file_token_counts


def test_save_repo_details_updates_existing_record(file_tree, file_token_counts):
    file_tree_new = [
        FileNode(name="root", path=Path(), is_dir=True, children=[]),
    ]

    file_token_counts_new = {}
    # First, create a record with old values.
    RepositoryDetail.objects.create(
        username="testuser",
        repo="testrepo",
        commit_hash="oldhash",
        description="old_description",
        languages={"Python": 50},
        stargazers_count=10,
        watchers_count=10,
        forks_count=10,
        open_issues_count=10,
        subscribers_count=10,
        size=10,
        topics=["old_topic"],
        file_tree=[file_node.to_dict() for file_node in file_tree],
        file_count=1,
        readme="old_readme",
        diagram="old_diagram",
        explanation="old_explanation",
        file_token_counts=file_token_counts,
    )
    # Update the record with new values.
    RepositoryPersistenceService.save_repo_details(
        username="testuser",
        repo="testrepo",
        commit_hash="newhash",
        description="new_description",
        languages={"Python": 150},
        stargazers_count=1,
        watchers_count=1,
        forks_count=1,
        open_issues_count=1,
        subscribers_count=1,
        size=1,
        topics=["new_topic"],
        file_tree=file_tree_new,
        file_count=0,
        readme="new_readme",
        diagram="new_diagram",
        explanation="new_explanation",
        file_token_counts=file_token_counts_new,
    )
    # Retrieve and verify.
    retrieved = RepositoryDetail.objects.get(username="testuser", repo="testrepo")
    assert retrieved.commit_hash == "newhash"
    assert retrieved.description == "new_description"
    assert retrieved.languages == {"Python": 150}
    assert retrieved.stargazers_count == 1
    assert retrieved.watchers_count == 1
    assert retrieved.forks_count == 1
    assert retrieved.open_issues_count == 1
    assert retrieved.subscribers_count == 1
    assert retrieved.size == 1
    assert retrieved.topics == ["new_topic"]
    assert retrieved.file_tree == [file_node.to_dict() for file_node in file_tree_new]
    assert retrieved.file_count == 0
    assert retrieved.readme == "new_readme"
    assert retrieved.diagram == "new_diagram"
    assert retrieved.explanation == "new_explanation"
    assert retrieved.file_token_counts == file_token_counts_new
