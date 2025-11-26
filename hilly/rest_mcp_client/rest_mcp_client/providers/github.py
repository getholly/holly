"""GitHub provider implementation."""

import httpx
from typing import Dict, Any, List
from loguru import logger

from rest_mcp_client.providers.base import GitProvider


class GitHubProvider(GitProvider):
    """GitHub API provider implementation."""
    
    def __init__(self, auth_token: str):
        """
        Initialize GitHub provider.
        
        Args:
            auth_token: GitHub authentication token
        """
        self.auth_token = auth_token
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"Bearer {auth_token}",
            "Accept": "application/vnd.github.v3+json",
        }
    
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
        Create a GitHub pull request.
        
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
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        
        payload = {
            "title": title,
            "head": head,
            "base": base,
            "body": body,
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    headers=self.headers,
                    json=payload,
                    timeout=30.0
                )
                response.raise_for_status()
                pr_data = response.json()
                
                logger.info(f"Created PR #{pr_data.get('number')} in {owner}/{repo}")
                
                return {
                    "success": True,
                    "number": pr_data.get("number"),
                    "url": pr_data.get("html_url"),
                    "state": pr_data.get("state"),
                    "title": pr_data.get("title"),
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to create PR: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_branches(self, owner: str, repo: str) -> List[str]:
        """
        Get list of branches for a GitHub repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of branch names
        """
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                branches_data = response.json()
                
                return [branch["name"] for branch in branches_data]
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to get branches: {e}")
            return []
    
    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get GitHub repository information.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository information
        """
        url = f"{self.base_url}/repos/{owner}/{repo}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
                    headers=self.headers,
                    timeout=30.0
                )
                response.raise_for_status()
                repo_data = response.json()
                
                return {
                    "success": True,
                    "name": repo_data.get("name"),
                    "full_name": repo_data.get("full_name"),
                    "description": repo_data.get("description"),
                    "default_branch": repo_data.get("default_branch"),
                    "private": repo_data.get("private"),
                    "url": repo_data.get("html_url"),
                }
                
        except httpx.HTTPError as e:
            logger.error(f"Failed to get repository info: {e}")
            return {
                "success": False,
                "error": str(e)
            }

