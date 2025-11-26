from typing import TYPE_CHECKING

from django.contrib.auth import get_user_model

from holly.analytics.models import LLMQuery, Repository, RepoView

if TYPE_CHECKING:
    from holly.users.models import User
else:
    User = get_user_model()


class AnalyticsService:
    """
    Service class for handling analytics tracking operations.
    """

    @staticmethod
    def _get_or_create_repository(*, username: str, repo_name: str, private: bool) -> Repository:
        """
        Get or create a Repository instance.

        Args:
            username: GitHub repository owner username
            repo_name: GitHub repository name
            private: Whether the repository is private

        Returns:
            The Repository instance
        """
        repo, _ = Repository.objects.get_or_create(
            username=username, repo_name=repo_name, defaults={"private": private}
        )
        return repo

    @staticmethod
    def track_repo_view(
        *,
        username: str,
        repo_name: str,
        user: "User",
        private: bool,
    ) -> RepoView:
        """
        Track a repository view event.

        Args:
            username: GitHub repository owner username
            repo_name: GitHub repository name
            user: Django User model instance
            private: Whether the repository is private

        Returns:
            The created RepoView instance
        """
        repo = AnalyticsService._get_or_create_repository(username=username, repo_name=repo_name, private=private)
        return RepoView.objects.create(user=user, repo=repo)

    @staticmethod
    def track_llm_query(  # noqa: PLR0913
        *,
        username: str,
        repo_name: str,
        query_text: str,
        model_name: str,
        user: "User",
        private: bool,
    ) -> LLMQuery:
        """
        Track an LLM query event.

        Args:
            username: GitHub repository owner username
            repo_name: GitHub repository name
            query_text: The text of the query sent to the LLM
            model_name: Name of the LLM model used
            user: Django User model instance
            private: Whether the repository is private

        Returns:
            The created LLMQuery instance
        """
        repo = AnalyticsService._get_or_create_repository(username=username, repo_name=repo_name, private=private)
        return LLMQuery.objects.create(
            user=user,
            repo=repo,
            query_text=query_text,
            model_name=model_name,
        )
