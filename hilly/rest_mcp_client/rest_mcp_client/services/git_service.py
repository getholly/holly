import os
import subprocess
from typing import Dict, Any, Optional, List
from pathlib import Path
from loguru import logger


class GitService:
    """Service for Git operations in the container"""

    def __init__(self, base_dir: str = "/data"):
        """
        Initialize the Git service.

        Args:
            base_dir: Base directory for Git repositories
        """
        self.base_dir = Path(base_dir)
        # Ensure the base directory exists
        logger.info(f"Using {self.base_dir} as base directory")
        os.makedirs(self.base_dir, exist_ok=True)
        logger.info(f"Initialized GitService with base directory: {self.base_dir}")

    def clone_repository(
        self,
        repo_owner: str,
        repo_name: str,
        auth_token: str,
        branch: Optional[str] = "main",
        create_branch: Optional[str] = None,
        auth_type: str = "oauth",
    ) -> Dict[str, Any]:
        """
        Clone a GitHub repository with proper auth format.

        Args:
            repo_owner: GitHub repository owner/organization
            repo_name: GitHub repository name
            auth_token: GitHub auth token for authentication
            branch: Optional branch to checkout after cloning (defaults to main)
            create_branch: Optional new branch to create and checkout
            auth_type: Type of authentication ('github_app' or 'oauth')

        Returns:
            Dict with results of the operation
        """
        try:
            # Format repository path and URL
            repo_path = self.base_dir / repo_owner/ repo_name
            
            # Build correct URL based on auth type
            if auth_type == "github_app":
                repo_url = f"https://x-access-token:{auth_token}@github.com/{repo_owner}/{repo_name}.git"
                logger.info(f"Cloning {repo_owner}/{repo_name} with GitHub App token")
            else:
                repo_url = f"https://{auth_token}@github.com/{repo_owner}/{repo_name}.git"
                logger.info(f"Cloning {repo_owner}/{repo_name} with OAuth token")

            # Ensure parent directories exist
            os.makedirs(repo_path.parent, exist_ok=True)

            # Check if repository directory already exists
            if (repo_path/branch).exists():
                logger.info(f"Repository already exists at {repo_path}/{branch}, fetching latest changes")
                return self._update_existing_repo(repo_path, branch, create_branch)

            # Clone the repository
            logger.info(f"Cloning repository {repo_owner}/{repo_name} to {repo_path / branch}")
            result = subprocess.run(
                ["git", "clone", repo_url, str(repo_path / branch)],
                capture_output=True,
                text=True,
                check=False,
            )

            if result.returncode != 0:
                logger.error(f"Failed to clone repository: {result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to clone repository: {result.stderr}",
                    "path": None,
                }

            # Checkout or create branch if specified
            if create_branch:
                self.create_worktree(f"{repo_owner}/{repo_name}", create_branch, branch)

            return {
                "success": True,
                "message": f"Repository cloned successfully to {repo_path}",
                "path": str(repo_path),
                "branch": branch,
            }

        except Exception as e:
            logger.exception(f"Error cloning repository: {e}")
            return {
                "success": False,
                "message": f"Error cloning repository: {str(e)}",
                "path": None,
            }

    def _update_existing_repo(
        self,
        repo_path: Path,
        branch: Optional[str] = None,
        create_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update an existing repository with the latest changes.

        Args:
            repo_path: Path to the repository
            branch: Optional branch to checkout
            create_branch: Optional new branch to create

        Returns:
            Dict with results of the operation
        """
        try:
            # Get the current branch
            current_branch = self._get_current_branch(repo_path / branch)

            # Fetch latest changes
            fetch_result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=str(repo_path / branch),
                capture_output=True,
                text=True,
                check=False,
            )

            if fetch_result.returncode != 0:
                logger.error(f"Failed to fetch latest changes: {fetch_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to fetch latest changes: {fetch_result.stderr}",
                    "path": str(repo_path),
                    "branch": current_branch,
                }

            # Handle branch operations if needed
            if branch or create_branch:
                return self._handle_branch_operations(repo_path, branch, create_branch)

            # Otherwise, pull the latest changes for the current branch
            pull_result = subprocess.run(
                ["git", "pull", "origin", current_branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if pull_result.returncode != 0:
                logger.error(f"Failed to pull latest changes: {pull_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to pull latest changes: {pull_result.stderr}",
                    "path": str(repo_path),
                    "branch": current_branch,
                }

            return {
                "success": True,
                "message": f"Repository updated successfully at {repo_path}",
                "path": str(repo_path),
                "branch": current_branch,
            }

        except Exception as e:
            logger.exception(f"Error updating repository: {e}")
            return {
                "success": False,
                "message": f"Error updating repository: {str(e)}",
                "path": str(repo_path),
                "branch": self._get_current_branch(repo_path),
            }

    def _handle_branch_operations(
        self,
        repo_path: Path,
        branch: Optional[str] = None,
        create_branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle branch checkout and creation operations.

        Args:
            repo_path: Path to the repository
            branch: Optional branch to checkout
            create_branch: Optional new branch to create

        Returns:
            Dict with results of the operation
        """
        try:
            current_branch = self._get_current_branch(repo_path / branch)
            result_branch = current_branch

            # Checkout existing branch if specified
            if branch and not create_branch:
                logger.info(f"Checking out branch: {branch} on {repo_path}")
                checkout_result = subprocess.run(
                    ["git", "checkout", branch],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )
                logger.info(f"{checkout_result.stdout}")
                if checkout_result.returncode != 0:
                    logger.error(f"Failed to checkout branch {branch}: {checkout_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to checkout branch {branch}: {checkout_result.stderr}",
                        "path": str(repo_path),
                        "branch": current_branch,
                    }

                # Pull latest changes for this branch
                pull_result = subprocess.run(
                    ["git", "pull", "origin", branch],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if pull_result.returncode != 0:
                    logger.error(f"Failed to pull latest changes for branch {branch}: {pull_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to pull latest changes for branch {branch}: {pull_result.stderr}",
                        "path": str(repo_path),
                        "branch": branch,
                    }

                result_branch = branch

            # Create and checkout a new branch if specified
            if create_branch:
                # If branch is specified, check it out first as the base
                if branch and branch != current_branch:
                    logger.info(f"Checking out base branch: {branch}")
                    checkout_result = subprocess.run(
                        ["git", "switch", branch],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if checkout_result.returncode != 0:
                        logger.error(f"Failed to checkout base branch {branch}: {checkout_result.stderr}")
                        return {
                            "success": False,
                            "message": f"Failed to checkout base branch {branch}: {checkout_result.stderr}",
                            "path": str(repo_path),
                            "branch": current_branch,
                        }

                    # Pull latest changes for this branch
                    subprocess.run(
                        ["git", "pull", "origin", branch],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                # Create and checkout new branch
                logger.info(f"Creating and checking out new branch: {repo_path}/{create_branch}")
                create_branch_result = subprocess.run(
                    ["git", "checkout", "-b", create_branch],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if create_branch_result.returncode != 0:
                    logger.error(f"Failed to create branch {create_branch}: {create_branch_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to create branch {create_branch}: {create_branch_result.stderr}",
                        "path": str(repo_path),
                        "branch": branch if branch else current_branch,
                    }

                result_branch = create_branch

            return {
                "success": True,
                "message": f"Repository branch operations completed successfully. Current branch: {result_branch}",
                "path": str(repo_path),
                "branch": result_branch,
            }

        except Exception as e:
            logger.exception(f"Error handling branch operations: {e}")
            return {
                "success": False,
                "message": f"Error handling branch operations: {str(e)}",
                "path": str(repo_path),
                "branch": self._get_current_branch(repo_path),
            }

    def _get_current_branch(self, repo_path: Path) -> str:
        """
        Get the current branch of a repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Current branch name
        """
        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "unknown"

    def create_worktree(
        self,
        repo_name: str,
        branch: str,
        base_branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Create a new git worktree for a specific branch.

        Args:
            repo_name: Name of the repository
            branch: Branch to create worktree for
            base_branch: Base branch to use (default is main)

        Returns:
            Dict with results of the operation
        """
        try:
            # Ensure the base repository exists
            base_repo_path = self.base_dir / repo_name / base_branch
            if not base_repo_path.exists():
                results = self.create_worktree(repo_name, base_branch)
                if not results["success"]:
                    logger.error(f"Base repository does not exist at {base_repo_path}")
                    return {
                        "success": False,
                        "message": f"Base repository does not exist at {base_repo_path}. Please clone the repository first.",
                        "path": None,
                        "branch": None,
                    }

            # Determine the worktree path
            worktree_path = self.base_dir / repo_name / branch.replace("/", os.sep)

            # Check if worktree already exists
            if worktree_path.exists():
                logger.info(f"Worktree already exists at {worktree_path}")
                return {
                    "success": True,
                    "message": f"Worktree already exists at {worktree_path}",
                    "path": str(worktree_path),
                    "branch": branch,
                }

            # Ensure parent directories exist
            os.makedirs(worktree_path.parent, exist_ok=True)

            # Fetch latest changes
            fetch_result = subprocess.run(
                ["git", "fetch", "origin"],
                cwd=str(base_repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if fetch_result.returncode != 0:
                logger.error(f"Failed to fetch latest changes: {fetch_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to fetch latest changes: {fetch_result.stderr}",
                    "path": None,
                    "branch": None,
                }

            # Check if the branch already exists
            branch_exists = False
            list_branches_result = subprocess.run(
                ["git", "branch", "-a"],
                cwd=str(base_repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            # Check if branch exists locally or remotely
            branches = list_branches_result.stdout.split("\n")
            if any(b.strip().endswith(f"/{branch}") or b.strip() == branch for b in branches):
                branch_exists = True

            # Create worktree for existing branch or create a new branch
            if branch_exists:
                # Create worktree with existing branch
                worktree_result = subprocess.run(
                    ["git", "worktree", "add", str(worktree_path), branch],
                    cwd=str(base_repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )
            else:
                # Create worktree with new branch
                worktree_result = subprocess.run(
                    ["git", "worktree", "add", "-b", branch, str(worktree_path)],
                    cwd=str(base_repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )

            if worktree_result.returncode != 0:
                logger.error(f"Failed to create worktree: {worktree_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to create worktree: {worktree_result.stderr}",
                    "path": None,
                    "branch": None,
                }

            return {
                "success": True,
                "message": f"Worktree created successfully at {worktree_path}",
                "path": str(worktree_path),
                "branch": branch,
            }

        except Exception as e:
            logger.exception(f"Error creating worktree: {e}")
            return {
                "success": False,
                "message": f"Error creating worktree: {str(e)}",
                "path": None,
                "branch": None,
            }

    def commit_changes(
        self,
        repo_name: str,
        branch: str,
        commit_message: str,
        files: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Commit changes in a specific repository branch.

        Args:
            repo_name: Name of the repository
            branch: Branch to commit to
            commit_message: Commit message
            files: Optional list of specific files to commit, if None all changes will be committed

        Returns:
            Dict with results of the operation
        """
        try:
            # Determine the repository path
            repo_path = self.base_dir / repo_name / branch.replace("/", os.sep)

            # Check if repository exists
            if not repo_path.exists():
                logger.error(f"Repository branch does not exist at {repo_path}")
                return {
                    "success": False,
                    "message": f"Repository branch does not exist at {repo_path}",
                    "path": None,
                    "branch": None,
                }

            # Add files to staging
            if files:
                # Add specific files
                for file in files:
                    add_result = subprocess.run(
                        ["git", "add", file],
                        cwd=str(repo_path),
                        capture_output=True,
                        text=True,
                        check=False,
                    )

                    if add_result.returncode != 0:
                        logger.error(f"Failed to add file {file}: {add_result.stderr}")
                        return {
                            "success": False,
                            "message": f"Failed to add file {file}: {add_result.stderr}",
                            "path": str(repo_path),
                            "branch": branch,
                        }
            else:
                # Add all changes
                add_result = subprocess.run(
                    ["git", "add", "."],
                    cwd=str(repo_path),
                    capture_output=True,
                    text=True,
                    check=False,
                )

                if add_result.returncode != 0:
                    logger.error(f"Failed to add changes: {add_result.stderr}")
                    return {
                        "success": False,
                        "message": f"Failed to add changes: {add_result.stderr}",
                        "path": str(repo_path),
                        "branch": branch,
                    }

            # Check if there are any changes to commit
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if not status_result.stdout.strip():
                return {
                    "success": True,
                    "message": "No changes to commit",
                    "path": str(repo_path),
                    "branch": branch,
                }

            # Commit changes
            commit_result = subprocess.run(
                ["git", "commit", "-m", commit_message],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if commit_result.returncode != 0:
                logger.error(f"Failed to commit changes: {commit_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to commit changes: {commit_result.stderr}",
                    "path": str(repo_path),
                    "branch": branch,
                }

            return {
                "success": True,
                "message": f"Changes committed successfully: {commit_result.stdout.strip()}",
                "path": str(repo_path),
                "branch": branch,
            }

        except Exception as e:
            logger.exception(f"Error committing changes: {e}")
            return {
                "success": False,
                "message": f"Error committing changes: {str(e)}",
                "path": None,
                "branch": None,
            }

    def pull_changes(
        self,
        repo_name: str,
        branch: str,
    ) -> Dict[str, Any]:
        """
        Pull latest changes for a specific repository branch.

        Args:
            repo_name: Name of the repository
            branch: Branch to pull changes for

        Returns:
            Dict with results of the operation
        """
        try:
            # Determine the repository path
            repo_path = self.base_dir / repo_name / branch.replace("/", os.sep)

            # Check if repository exists
            if not repo_path.exists():
                logger.error(f"Repository branch does not exist at {repo_path}")
                return {
                    "success": False,
                    "message": f"Repository branch does not exist at {repo_path}",
                    "path": None,
                    "branch": None,
                }

            # Pull latest changes
            pull_result = subprocess.run(
                ["git", "pull", "origin", branch],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if pull_result.returncode != 0:
                logger.error(f"Failed to pull latest changes: {pull_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to pull latest changes: {pull_result.stderr}",
                    "path": str(repo_path),
                    "branch": branch,
                }

            return {
                "success": True,
                "message": f"Latest changes pulled successfully: {pull_result.stdout.strip()}",
                "path": str(repo_path),
                "branch": branch,
            }

        except Exception as e:
            logger.exception(f"Error pulling changes: {e}")
            return {
                "success": False,
                "message": f"Error pulling changes: {str(e)}",
                "path": None,
                "branch": None,
            }

    def push_changes(
        self,
        repo_name: str,
        branch: str,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Push local changes to remote repository.

        Args:
            repo_name: Name of the repository
            branch: Branch to push changes for
            force: Whether to force push (use with caution)

        Returns:
            Dict with results of the operation
        """
        try:
            # Determine the repository path
            repo_path = self.base_dir / repo_name / branch.replace("/", os.sep)

            # Check if repository exists
            if not repo_path.exists():
                logger.error(f"Repository branch does not exist at {repo_path}")
                return {
                    "success": False,
                    "message": f"Repository branch does not exist at {repo_path}",
                    "path": None,
                    "branch": None,
                }

            # Push changes
            push_cmd = ["git", "push", "origin", branch]
            if force:
                push_cmd.insert(2, "--force")

            push_result = subprocess.run(
                push_cmd,
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if push_result.returncode != 0:
                logger.error(f"Failed to push changes: {push_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to push changes: {push_result.stderr}",
                    "path": str(repo_path),
                    "branch": branch,
                }

            return {
                "success": True,
                "message": f"Changes pushed successfully to origin/{branch}",
                "path": str(repo_path),
                "branch": branch,
            }

        except Exception as e:
            logger.exception(f"Error pushing changes: {e}")
            return {
                "success": False,
                "message": f"Error pushing changes: {str(e)}",
                "path": None,
                "branch": None,
            }

    def get_repository_branches(
        self,
        repo_name: str,
    ) -> Dict[str, Any]:
        """
        Get a list of branches for a cloned repository.

        Args:
            repo_name: Name of the repository

        Returns:
            Dict with a list of branches and other details
        """
        try:
            # Try to find the repository directory
            # First, check if a default branch like main or master exists
            repo_path = None
            default_branches = ["main", "master", "develop"]

            for branch in default_branches:
                test_path = self.base_dir / repo_name / branch
                if test_path.exists() and test_path.is_dir():
                    repo_path = test_path
                    break

            # If default branches don't exist, look for any directory matching the repo name
            if not repo_path:
                repo_dir = self.base_dir / repo_name
                if repo_dir.exists() and repo_dir.is_dir():
                    # Find the first subdirectory that contains a .git folder or directory
                    for path in repo_dir.iterdir():
                        if path.is_dir():
                            if (path / ".git").exists() or any((path / d).is_dir() and d.startswith(".git") for d in os.listdir(path)):
                                repo_path = path
                                break

            # If still no repository found, return an error
            if not repo_path:
                logger.error(f"Repository not found: {self.base_dir}/{repo_name}")
                return {
                    "success": False,
                    "message": f"Repository not found: {repo_name}. Please clone the repository first.",
                    "branches": [],
                    "current_branch": None
                }

            # Fetch latest changes to ensure we get all remote branches
            fetch_result = subprocess.run(
                ["git", "fetch", "--all"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if fetch_result.returncode != 0:
                logger.warning(f"Failed to fetch latest branches: {fetch_result.stderr}")
                # Continue anyway since we can still get local branches

            # Get current branch
            current_branch = self._get_current_branch(repo_path)

            # Get local branches
            local_branches_result = subprocess.run(
                ["git", "branch"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if local_branches_result.returncode != 0:
                logger.error(f"Failed to get local branches: {local_branches_result.stderr}")
                return {
                    "success": False,
                    "message": f"Failed to get local branches: {local_branches_result.stderr}",
                    "branches": [],
                    "current_branch": current_branch
                }

            # Get remote branches
            remote_branches_result = subprocess.run(
                ["git", "branch", "-r"],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                check=False,
            )

            if remote_branches_result.returncode != 0:
                logger.error(f"Failed to get remote branches: {remote_branches_result.stderr}")
                # Continue anyway with local branches

            # Parse branches
            local_branches = []
            for branch in local_branches_result.stdout.split("\n"):
                branch = branch.strip()
                if branch:
                    # Remove the asterisk that indicates the current branch
                    if branch.startswith("*"):
                        branch = branch[1:].strip()
                    local_branches.append(branch)

            remote_branches = []
            if remote_branches_result.returncode == 0:
                for branch in remote_branches_result.stdout.split("\n"):
                    branch = branch.strip()
                    if branch and "->" not in branch:  # Skip HEAD -> refs
                        # Remove the remote prefix (e.g., "origin/")
                        if "/" in branch:
                            branch = branch.split("/", 1)[1]
                        remote_branches.append(branch)

            # Combine and deduplicate branches
            all_branches = list(set(local_branches + remote_branches))
            all_branches.sort()  # Sort branches alphabetically

            return {
                "success": True,
                "message": f"Found {len(all_branches)} branches for repository '{repo_name}'",
                "branches": all_branches,
                "current_branch": current_branch
            }

        except Exception as e:
            logger.exception(f"Error getting repository branches: {e}")
            return {
                "success": False,
                "message": f"Error getting repository branches: {str(e)}",
                "branches": [],
                "current_branch": None
            }
