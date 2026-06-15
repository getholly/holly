import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from git import GitCommandError, InvalidGitRepositoryError

from holly.github_ext.exceptions import GitHubService403Error
from holly.github_ext.helpers import github_auth_env, remove_readonly, tokenless_github_url
from holly.github_ext.services.git_repo_mgr import GitRepositoryManager

pytestmark = pytest.mark.django_db


@pytest.fixture
def tmp_repo_base(tmp_path):
    return tmp_path / "repos"


def test_clone_new_repo(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    fake_repo = MagicMock()
    fake_repo.bare = False

    with patch("git.Repo.clone_from", return_value=fake_repo) as mock_clone_from:
        manager = GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base))
        clone_path = manager.repo_path
        repo_obj = manager.get_repo()
        # The token must NOT be embedded in the clone URL; it is supplied via the
        # GIT_ASKPASS environment instead.
        expected_url = tokenless_github_url(username, repo_name)

        mock_clone_from.assert_called_once_with(
            expected_url,
            str(clone_path),
            env=github_auth_env(token),
            multi_options=["--depth=1"],
        )
        assert token not in expected_url
        assert repo_obj is fake_repo


def test_update_existing_repo(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    clone_path = (tmp_repo_base / username / repo_name).resolve()
    clone_path.mkdir(parents=True, exist_ok=True)

    fake_repo = MagicMock()
    fake_repo.bare = False
    fake_remote = MagicMock()
    fake_repo.remotes.origin = fake_remote

    with patch("git.Repo", return_value=fake_repo):  # noqa: SIM117
        with patch("git.Repo.clone_from", return_value=fake_repo) as mock_clone_from:
            with patch.object(GitRepositoryManager, "_fetch_latest_changes") as mock_fetch:
                manager = GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base))
                repo_obj = manager.get_repo()
                mock_fetch.assert_called_once_with(fake_repo)
                mock_clone_from.assert_not_called()
                assert repo_obj is fake_repo


def test_existing_invalid_repo(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    clone_path = (tmp_repo_base / username / repo_name).resolve()
    clone_path.mkdir(parents=True, exist_ok=True)

    fake_bare_repo = MagicMock()
    fake_bare_repo.bare = True

    with patch("git.Repo", side_effect=[fake_bare_repo]), patch("shutil.rmtree") as mock_rmtree:
        fake_valid_repo = MagicMock()
        fake_valid_repo.bare = False
        with (
            patch("git.Repo.clone_from", return_value=fake_valid_repo) as mock_clone_from,
            patch(
                "holly.github_ext.helpers.error_if_bare_repo",
                side_effect=InvalidGitRepositoryError("Repository is bare or invalid."),
            ),
        ):
            manager = GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base))
            repo_obj = manager.get_repo()
            mock_rmtree.assert_called_once_with(str(clone_path), ignore_errors=True, onerror=remove_readonly)
            mock_clone_from.assert_called_once()
            assert repo_obj is fake_valid_repo


def test_clone_403_error(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    clone_path = (tmp_repo_base / username / repo_name).resolve()
    if clone_path.exists():
        shutil.rmtree(str(clone_path))

    error_403 = GitCommandError("clone", 1, stderr="403 Forbidden")
    with patch("git.Repo.clone_from", side_effect=error_403):
        with pytest.raises(GitHubService403Error) as excinfo:
            GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base)).get_repo()
        assert "Access denied" in str(excinfo.value)


def test_repo_path(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    fake_repo = MagicMock()
    fake_repo.bare = False

    expected_path = Path(tmp_repo_base) / username / repo_name
    with patch("git.Repo.clone_from", return_value=fake_repo):
        manager = GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base))
        assert manager.repo_path == expected_path


def test_get_file_count(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    fake_repo = MagicMock()
    fake_repo.git.ls_files.return_value = "file1.txt\ndir1/file2.txt\ndir1/dir2/file3.txt"

    with patch.object(GitRepositoryManager, "get_repo", return_value=fake_repo):
        manager = GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base))
        manager.get_repo()
        assert manager.get_file_count == 3


def test_delete_repo(tmp_repo_base):
    token = "dummy_token"  # noqa: S105
    username = "testuser"
    repo_name = "testrepo"

    clone_path = (tmp_repo_base / username / repo_name).resolve()
    clone_path.mkdir(parents=True, exist_ok=True)
    assert clone_path.exists()

    fake_repo = MagicMock()
    fake_repo.bare = False

    with patch("git.Repo.clone_from", return_value=fake_repo):
        manager = GitRepositoryManager(username, repo_name, token, repo_base_path=str(tmp_repo_base))
        manager.get_repo()
        manager.delete_repo()
        assert not clone_path.exists()
