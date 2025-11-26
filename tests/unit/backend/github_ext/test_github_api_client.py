import datetime
from unittest.mock import Mock, patch

import pytest
from github import Github

from holly.github_ext.services.github_api import GithubApiClient


@pytest.fixture
def mock_repo():
    repo = Mock()

    # Default side effect for get_contents: simulate a root with a directory and a file.
    def get_contents_side_effect(path):
        if path == "":
            file1 = Mock()
            file1.type = "file"
            file1.path = "file1.txt"
            file1.size = 100
            # For files, decoded_content is a bytes-like object.
            file1.decoded_content = b"Content of file1"

            dir1 = Mock()
            dir1.type = "dir"
            dir1.path = "dir1"
            return [dir1, file1]
        if path == "dir1":
            file2 = Mock()
            file2.type = "file"
            file2.path = "dir1/file2.txt"
            file2.size = 100
            file2.decoded_content = b"Content of file2"
            return [file2]
        if path == "README.md":
            file_readme = Mock()
            file_readme.type = "file"
            file_readme.path = "README.md"
            file_readme.size = 50
            file_readme.decoded_content = b"README content"
            return [file_readme]
        msg = f"Path {path} not found"
        raise Exception(msg)  # noqa: TRY002

    repo.get_contents.side_effect = get_contents_side_effect
    return repo


@pytest.fixture
def mock_github(mock_repo):
    github = Mock(spec=Github)
    github.get_repo.return_value = mock_repo
    return github


@pytest.fixture
def api_client(mock_github):
    return GithubApiClient(mock_github, token="token")  # noqa: S106


@pytest.fixture
def mock_graphql_data():
    return {
        "data": {
            "repository": {
                "description": "Test repo",
                "isPrivate": False,
                "createdAt": "2023-01-01T00:00:00Z",
                "updatedAt": "2023-01-01T00:00:00Z",
                "stargazerCount": 42,
                "watchers": {"totalCount": 10},
                "forkCount": 5,
                "languages": {"nodes": [{"name": "Python"}, {"name": "JavaScript"}]},
                "object": {"text": "# Test README"},
            }
        }
    }


def test_get_repo_info_no_readme(api_client, mock_repo, mock_graphql_data):
    # Simulate missing README by raising an exception for "README.md".
    def get_contents_side_effect(path):
        if path == "":
            file1 = Mock()
            file1.type = "file"
            file1.path = "file1.txt"
            file1.size = 100
            file1.decoded_content = b"Content of file1"

            dir1 = Mock()
            dir1.type = "dir"
            dir1.path = "dir1"
            return [dir1, file1]
        if path == "dir1":
            file2 = Mock()
            file2.type = "file"
            file2.path = "dir1/file2.txt"
            file2.size = 100
            file2.decoded_content = b"Content of file2"
            return [file2]
        if path == "README.md":
            msg = "No README"
            raise Exception(msg)  # noqa: TRY002
        msg = f"Path {path} not found"
        raise Exception(msg)  # noqa: TRY002

    dummy_date = datetime.datetime(2023, 1, 1, 0, 0, 0, tzinfo=datetime.UTC)

    mock_repo.get_contents.side_effect = get_contents_side_effect

    mock_repo.open_issues_count = 3
    mock_repo.subscribers_count = 10
    mock_repo.size = 1024
    mock_repo.get_topics.return_value = ["topic1", "topic2"]

    with patch("holly.github_ext.services.github_api.fetch_repo_data_graphql", return_value=mock_graphql_data):
        details = api_client.get_repo_info("username", "repo")

    assert details.description == "Test repo"
    assert details.private is False
    assert details.created_at == dummy_date
    assert details.updated_at == dummy_date
    assert details.stargazers_count == 42
    assert details.watchers_count == 10
    assert details.forks_count == 5
    assert details.open_issues_count == 3
    assert details.subscribers_count == 10
    assert details.size == 1024
    assert details.languages == {"Python": 0, "JavaScript": 0}
    assert details.topics == ["topic1", "topic2"]


def test_get_repo_content(api_client, mock_repo):
    # Use the default fixture behavior.
    contents = api_client.get_repo_content("username", "repo")
    assert contents["file1.txt"] == "Content of file1"
    assert contents["dir1/file2.txt"] == "Content of file2"


def test_get_repo_content_skip_large_file(api_client, mock_repo):
    # Simulate a large file that exceeds the size threshold.
    def get_contents_side_effect(path):
        if path == "":
            large_file = Mock()
            large_file.type = "file"
            large_file.path = "large.txt"
            large_file.size = 20000000  # Above 10MB bytes threshold.
            large_file.decoded_content = b"Large content"
            return [large_file]
        return []

    mock_repo.get_contents.side_effect = get_contents_side_effect

    contents = api_client.get_repo_content("username", "repo")
    assert "large.txt" not in contents


def test_get_repo_content_decoding_error(api_client, mock_repo, caplog):
    # Simulate a file that raises a UnicodeDecodeError on decode.
    broken_file = Mock()
    broken_file.type = "file"
    broken_file.path = "broken.txt"
    broken_file.size = 100
    # Instead of a simple bytes object, provide a mock whose decode() method fails.
    broken_decoded = Mock()
    broken_decoded.decode.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "error")
    broken_file.decoded_content = broken_decoded

    def get_contents_side_effect(path):
        if path == "":
            return [broken_file]
        return []

    mock_repo.get_contents.side_effect = get_contents_side_effect

    contents = api_client.get_repo_content("username", "repo")
    assert "broken.txt" not in contents


def test_get_readme_present(api_client, mock_repo):
    # Simulate a valid README.md.
    def get_contents_side_effect(path):
        if path == "README.md":
            readme_file = Mock()
            readme_file.type = "file"
            readme_file.path = "README.md"
            readme_file.size = 50
            readme_file.decoded_content = b"README content"
            return readme_file
        if path == "":
            return []
        msg = f"Path {path} not found"
        raise Exception(msg)  # noqa: TRY002

    mock_repo.get_contents.side_effect = get_contents_side_effect

    readme = api_client._get_readme(mock_repo)
    assert readme == "README content"


def test_get_readme_missing(api_client, mock_repo):
    # Simulate missing README.md by having get_contents raise an Exception.
    def get_contents_side_effect(path):
        if path == "README.md":
            error_msg = "No README"
            raise Exception(error_msg)  # noqa: TRY002
        return []

    mock_repo.get_contents.side_effect = get_contents_side_effect

    readme = api_client._get_readme(mock_repo)
    assert readme == ""
