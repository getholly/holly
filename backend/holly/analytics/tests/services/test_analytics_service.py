import pytest

from holly.analytics.models import LLMQuery, Repository, RepoView
from holly.analytics.services.analytics_service import AnalyticsService
from holly.users.models import User


@pytest.mark.django_db
class TestAnalyticsService:
    def test_get_or_create_repository(self):
        # First call should create a new repository
        repo = AnalyticsService._get_or_create_repository(username="testuser", repo_name="testrepo", private=True)

        assert repo.username == "testuser"
        assert repo.repo_name == "testrepo"
        assert repo.private is True

        # Repository count should be 1
        assert Repository.objects.count() == 1

        # Second call with same params should not create a new repository
        repo2 = AnalyticsService._get_or_create_repository(username="testuser", repo_name="testrepo", private=True)

        assert repo.id == repo2.id
        assert Repository.objects.count() == 1

        # Different repo should create a new record
        repo3 = AnalyticsService._get_or_create_repository(username="testuser", repo_name="anotherrepo", private=True)

        assert repo3.id != repo.id
        assert Repository.objects.count() == 2

        # Test private flag
        repo4 = AnalyticsService._get_or_create_repository(username="testuser", repo_name="privaterepo", private=False)
        assert repo4.private is False

    def test_track_repo_view(self, user: User):
        # Track a repo view
        repo_view = AnalyticsService.track_repo_view(
            username="github-user", repo_name="cool-project", user=user, private=True
        )

        # Verify the repo view was created
        assert RepoView.objects.count() == 1

        # Verify repository was created
        assert Repository.objects.count() == 1
        assert repo_view.repo.username == "github-user"
        assert repo_view.repo.repo_name == "cool-project"

        # Verify user relationship
        assert repo_view.user == user

    def test_track_llm_query(self, user: User):
        # Track an LLM query
        query = AnalyticsService.track_llm_query(
            username="github-user",
            repo_name="cool-project",
            query_text="What does this repository do?",
            model_name="gpt-4",
            user=user,
            private=False,
        )

        # Verify the query was created
        assert LLMQuery.objects.count() == 1

        # Verify repository was created
        assert Repository.objects.count() == 1
        assert query.repo.username == "github-user"
        assert query.repo.repo_name == "cool-project"
        assert query.repo.private is False

        # Verify query details
        assert query.query_text == "What does this repository do?"
        assert query.model_name == "gpt-4"
        assert query.user == user

    def test_track_multiple_queries_same_repo(self, user: User):
        # Track first query
        query1 = AnalyticsService.track_llm_query(
            username="github-user",
            repo_name="cool-project",
            query_text="First query",
            model_name="",
            user=user,
            private=True,
        )

        # Track second query for same repo
        query2 = AnalyticsService.track_llm_query(
            username="github-user",
            repo_name="cool-project",
            query_text="Second query",
            model_name="",
            user=user,
            private=True,
        )

        # Verify both queries were created
        assert LLMQuery.objects.count() == 2

        # Verify only one repository was created
        assert Repository.objects.count() == 1

        # Verify both queries point to the same repo
        assert query1.repo.id == query2.repo.id
