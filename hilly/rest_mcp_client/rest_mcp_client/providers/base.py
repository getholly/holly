"""Base Git provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class GitProvider(ABC):
    """Abstract base class for Git providers."""
    
    @abstractmethod
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        head: str,
        base: str,
        title: str,
        body: str = ""
    ) -> Dict[str, Any]:
        """
        Create a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            head: Head branch (source)
            base: Base branch (target)
            title: PR title
            body: PR description
            
        Returns:
            Pull request information
        """
        pass
    
    @abstractmethod
    async def get_branches(self, owner: str, repo: str) -> List[str]:
        """
        Get list of branches for a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of branch names
        """
        pass
    
    @abstractmethod
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        pass

