from typing import Optional, List

from pydantic import BaseModel


class CloneRepositoryRequest(BaseModel):
    """Request model for cloning a repository"""
    repo_owner: str
    repo_name: str
    auth_token: str
    branch: Optional[str] = "main"
    create_branch: Optional[str] = None
    auth_type: str = "oauth"


class WorktreeRequest(BaseModel):
    """Request model for creating a worktree"""
    repo_name: str
    branch: str
    base_branch: str = "main"


class CommitRequest(BaseModel):
    """Request model for committing changes"""
    repo_name: str
    branch: str
    commit_message: str
    files: Optional[List[str]] = None


class PullRequest(BaseModel):
    """Request model for pulling changes"""
    repo_name: str
    branch: str


class PushRequest(BaseModel):
    """Request model for pushing changes"""
    repo_name: str
    branch: str
    force: bool = False


class RepositoryBranchesRequest(BaseModel):
    """Request model for getting repository branches"""
    repo_name: str


class GitOperationResponse(BaseModel):
    """Response model for Git operations"""
    success: bool
    message: str
    path: Optional[str] = None
    branch: Optional[str] = None


class BranchesResponse(BaseModel):
    """Response model for repository branches"""
    success: bool
    message: str
    branches: List[str]
    current_branch: Optional[str] = None
