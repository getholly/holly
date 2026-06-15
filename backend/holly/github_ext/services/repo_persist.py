from holly.github_ext.helpers import RepositoryDetailsDTO
from holly.github_ext.models import RepositoryDetail
from holly.github_ext.utils import FileNode


class RepositoryPersistenceService:
    @staticmethod
    def get_repo_details(username: str, repo: str, commit_hash: str | None = None) -> RepositoryDetailsDTO | None:
        """
        Fetch repository details from the database.
        If commit_hash is provided, ensure data is up-to-date.
        """
        try:
            obj = RepositoryDetail.objects.get(username=username, repo=repo)
            if commit_hash and obj.commit_hash != commit_hash:
                return None

            return RepositoryDetailsDTO(
                username=obj.username,
                github_id=obj.github_id,
                repo=obj.repo,
                commit_hash=obj.commit_hash,
                description=obj.description,
                stargazers_count=obj.stargazers_count,
                watchers_count=obj.watchers_count,
                forks_count=obj.forks_count,
                open_issues_count=obj.open_issues_count,
                subscribers_count=obj.subscribers_count,
                size=obj.size,
                topics=obj.topics,
                file_tree=[FileNode.from_dict(file_node_dict) for file_node_dict in (obj.file_tree or [])],
                file_count=obj.file_count,
                languages=obj.languages,
                readme=obj.readme,
                diagram=obj.diagram,
                explanation=obj.explanation,
                private=obj.private,
            )
        except RepositoryDetail.DoesNotExist:
            return None

    @staticmethod
    def save_repo_details(  # noqa: PLR0913
        username: str,
        repo: str,
        github_id: int,
        commit_hash: str,
        description: str,
        languages: dict,
        stargazers_count: int,
        watchers_count: int,
        forks_count: int,
        open_issues_count: int,
        subscribers_count: int,
        size: int,
        topics: list[str],
        file_tree: list[FileNode],
        file_count: int,
        readme: str,
        diagram: str,
        explanation: str,
        file_token_counts: dict[str, int],
        *,  # ensure private is explictly set
        private: bool = True,
    ) -> RepositoryDetailsDTO:
        """
        Save or update repository details.
        """
        file_tree_dict = [node.to_dict() for node in file_tree]

        obj, _ = RepositoryDetail.objects.update_or_create(
            username=username,
            repo=repo,
            defaults={
                "commit_hash": commit_hash,
                "github_id": github_id,
                "description": description,
                "languages": languages,
                "stargazers_count": stargazers_count,
                "watchers_count": watchers_count,
                "forks_count": forks_count,
                "open_issues_count": open_issues_count,
                "subscribers_count": subscribers_count,
                "size": size,
                "topics": topics,
                "file_tree": file_tree_dict,
                "file_count": file_count,
                "readme": readme,
                "diagram": diagram,
                "explanation": explanation,
                "file_token_counts": file_token_counts,
                "private": private,
            },
        )

        return RepositoryDetailsDTO(
            username=obj.username,
            repo=obj.repo,
            github_id=github_id,
            commit_hash=obj.commit_hash,
            description=obj.description,
            languages=obj.languages,
            stargazers_count=obj.stargazers_count,
            watchers_count=obj.watchers_count,
            forks_count=obj.forks_count,
            open_issues_count=obj.open_issues_count,
            subscribers_count=obj.subscribers_count,
            size=obj.size,
            topics=obj.topics,
            file_tree=file_tree,
            file_count=obj.file_count,
            readme=obj.readme,
            diagram=obj.diagram,
            explanation=obj.explanation,
            private=obj.private,
        )

    @staticmethod
    def delete_repo_details(username: str, repo: str):
        """
        Delete repository details from the database.
        """
        RepositoryDetail.objects.filter(username=username, repo=repo).delete()

    @staticmethod
    def get_cached_file_tree(username: str, repo: str) -> list[FileNode] | None:
        """
        Retrieve cached file tree if available.
        """
        obj = RepositoryPersistenceService.get_repo_details(username, repo)
        return obj.file_tree if obj and obj.file_tree else None
