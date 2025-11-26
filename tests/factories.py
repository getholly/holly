"""
Factory Boy factories for creating test data.

These factories provide a consistent way to generate test objects with
realistic data for all tests in the Holly application.
"""

import factory
from allauth.socialaccount.models import SocialAccount, SocialApp
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from factory.django import DjangoModelFactory
from faker import Faker

from holly.github_ext.models import GitHubAppInstallation, RepositoryDetail
from holly.holly.models.conversations import Message
from holly.holly.models.knowledge import Knowledge
from holly.holly.models.llms import LLM
from holly.holly.models.mission import Mission, MissionRepos
from holly.holly.models.mission_conversation import MissionConversation
from holly.holly.models.tools import Tools

User = get_user_model()
fake = Faker()


# User and Authentication Factories


class UserFactory(DjangoModelFactory):
    """Factory for creating test users."""

    class Meta:
        model = User
        django_get_or_create = ("email",)

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "testpass123")
    is_active = True
    is_staff = False
    is_superuser = False


class SuperUserFactory(UserFactory):
    """Factory for creating superusers."""

    is_staff = True
    is_superuser = True
    email = factory.Sequence(lambda n: f"admin{n}@example.com")



class SocialAppFactory(DjangoModelFactory):
    """Factory for creating social apps (e.g., GitHub OAuth app)."""

    class Meta:
        model = SocialApp
        django_get_or_create = ("provider", "name")

    provider = "github"
    name = "GitHub"
    client_id = factory.Faker("uuid4")
    secret = factory.Faker("uuid4")

    @factory.post_generation
    def sites(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for site in extracted:
                self.sites.add(site)
        else:
            # Add default site
            site = Site.objects.get_current()
            self.sites.add(site)


class SocialAccountFactory(DjangoModelFactory):
    """Factory for creating social accounts linked to users."""

    class Meta:
        model = SocialAccount
        django_get_or_create = ("provider", "uid")

    user = factory.SubFactory(UserFactory)
    provider = "github"
    uid = factory.Sequence(lambda n: str(100000 + n))
    extra_data = factory.LazyFunction(
        lambda: {
            "login": fake.user_name(),
            "id": fake.random_int(min=100000, max=999999),
            "avatar_url": fake.image_url(),
            "name": fake.name(),
            "email": fake.email(),
        }
    )


# GitHub Integration Factories


class GitHubAppInstallationFactory(DjangoModelFactory):
    """Factory for creating GitHub App installations."""

    class Meta:
        model = GitHubAppInstallation
        django_get_or_create = ("social_account", "installation_id")

    social_account = factory.SubFactory(SocialAccountFactory)
    installation_id = factory.Sequence(lambda n: str(50000000 + n))
    account_name = factory.LazyAttribute(lambda obj: obj.social_account.extra_data.get("login", "testuser"))
    account_type = "user"


class RepositoryDetailFactory(DjangoModelFactory):
    """Factory for creating repository details."""

    class Meta:
        model = RepositoryDetail
        django_get_or_create = ("github_id",)

    github_id = factory.Sequence(lambda n: str(800000000 + n))
    username = factory.Faker("user_name")
    repo = factory.Sequence(lambda n: f"test-repo-{n}")
    commit_hash = factory.Faker("sha1")
    description = factory.Faker("sentence", nb_words=10)
    languages = factory.LazyFunction(lambda: {"Python": 75000, "JavaScript": 25000})
    stargazers_count = factory.Faker("random_int", min=0, max=1000)
    watchers_count = factory.Faker("random_int", min=0, max=500)
    forks_count = factory.Faker("random_int", min=0, max=100)
    open_issues_count = factory.Faker("random_int", min=0, max=50)
    subscribers_count = factory.Faker("random_int", min=0, max=200)
    size = factory.Faker("random_int", min=100, max=100000)
    topics = factory.LazyFunction(lambda: ["python", "django", "api"])
    private = False
    file_tree = factory.LazyFunction(
        lambda: {
            "src": {"type": "dir", "children": {"main.py": {"type": "file"}, "utils.py": {"type": "file"}}},
            "tests": {"type": "dir", "children": {"test_main.py": {"type": "file"}}},
            "README.md": {"type": "file"},
        }
    )
    file_count = 4
    file_token_counts = factory.LazyFunction(lambda: {"src/main.py": 150, "src/utils.py": 100, "README.md": 50})
    readme = factory.Faker("text", max_nb_chars=500)


# LLM and Knowledge Factories


class LLMFactory(DjangoModelFactory):
    """Factory for creating LLM configurations."""

    class Meta:
        model = LLM
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"test-llm-{n}")
    full_name = "openai/gpt-4"
    base_url = "https://api.openai.com/v1"
    system_prompt = "You are a helpful AI assistant."
    temperature = 0.7
    max_tokens = 4096
    top_p = None
    top_k = None
    min_p = None
    is_system = False
    user = None


class SystemLLMFactory(LLMFactory):
    """Factory for creating system-wide LLM configurations."""

    is_system = True
    user = None


class UserLLMFactory(LLMFactory):
    """Factory for creating user-specific LLM configurations."""

    is_system = False
    user = factory.SubFactory(UserFactory)


class KnowledgeFactory(DjangoModelFactory):
    """Factory for creating knowledge items."""

    class Meta:
        model = Knowledge
        django_get_or_create = ("title",)

    title = factory.Sequence(lambda n: f"Knowledge Item {n}")
    content = factory.Faker("text", max_nb_chars=1000)
    source = factory.Faker("url")



class ToolsFactory(DjangoModelFactory):
    """Factory for creating tool configurations."""

    class Meta:
        model = Tools
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"tool-{n}")
    config = factory.LazyFunction(
        lambda: {
            "file_editor": {
                "description": "Edit files in the repository",
                "enabled": True,
            }
        }
    )



# Mission Factories


class MissionReposFactory(DjangoModelFactory):
    """Factory for creating MissionRepos junction objects."""

    class Meta:
        model = MissionRepos

    repository = factory.SubFactory(RepositoryDetailFactory)
    branch_name = "main"


class MissionFactory(DjangoModelFactory):
    """Factory for creating missions."""

    class Meta:
        model = Mission

    title = factory.Sequence(lambda n: f"Mission {n}")
    description = factory.Faker("sentence", nb_words=20)
    state = Mission.State.DRAFT
    owner = factory.SubFactory(UserFactory)
    branch_name = factory.Sequence(lambda n: f"holly/feature-{n}")
    llm = factory.SubFactory(LLMFactory)

    container_id = None
    container_ip_address = None
    container_status = None
    container_started_at = None
    container_stopped_at = None
    init_job_id = None
    active_jobs = []
    requirements = {}

    @factory.post_generation
    def repositories(self, create, extracted, **kwargs):
        """Add repositories to the mission after creation."""
        if not create:
            return

        if extracted:
            # A list of repositories was passed in
            for repo in extracted:
                if isinstance(repo, RepositoryDetail):
                    # Create MissionRepos junction
                    mission_repo = MissionReposFactory(
                        repository=repo, branch_name=kwargs.get("branch_name", "main")
                    )
                    self.repositories.add(mission_repo)
                elif isinstance(repo, MissionRepos):
                    self.repositories.add(repo)
        else:
            # Create a default repository
            mission_repo = MissionReposFactory()
            self.repositories.add(mission_repo)

    @factory.post_generation
    def collaborators(self, create, extracted, **kwargs):
        """Add collaborators to the mission after creation."""
        if not create:
            return

        if extracted:
            for collaborator in extracted:
                self.collaborators.add(collaborator)

    @factory.post_generation
    def knowledge_items(self, create, extracted, **kwargs):
        """Add knowledge items to the mission after creation."""
        if not create:
            return

        if extracted:
            for knowledge in extracted:
                self.knowledge_items.add(knowledge)

    @factory.post_generation
    def tools(self, create, extracted, **kwargs):
        """Add tools to the mission after creation."""
        if not create:
            return

        if extracted:
            for tool in extracted:
                self.tools.add(tool)


# Conversation Factories


class MissionConversationFactory(DjangoModelFactory):
    """Factory for creating mission conversations."""

    class Meta:
        model = MissionConversation
        django_get_or_create = ("conversation_id",)

    mission = factory.SubFactory(MissionFactory)
    conversation_id = factory.Sequence(lambda n: f"conv-{n}")
    title = factory.Faker("sentence", nb_words=5)
    status = "pending"
    is_summarized = False
    summary = ""
    remaining_tasks = []


class MessageFactory(DjangoModelFactory):
    """Factory for creating conversation messages."""

    class Meta:
        model = Message

    conversation = factory.SubFactory(MissionConversationFactory)
    role = "user"
    content = factory.Faker("sentence", nb_words=20)


# Helper Functions for Common Test Scenarios


def create_complete_mission(
    owner=None, num_repos=2, num_collaborators=0, include_knowledge=False, include_tools=False, state=Mission.State.DRAFT
):
    """
    Create a complete mission with repositories, collaborators, knowledge, and tools.

    Args:
        owner: User who owns the mission (creates one if None)
        num_repos: Number of repositories to attach (default: 2)
        num_collaborators: Number of collaborators to add (default: 0)
        include_knowledge: Whether to add knowledge items (default: False)
        include_tools: Whether to add tools (default: False)
        state: Mission state (default: DRAFT)

    Returns:
        Mission: Fully configured mission instance
    """
    if owner is None:
        owner = UserFactory()

    # Create repositories
    repos = [RepositoryDetailFactory() for _ in range(num_repos)]

    # Create collaborators
    collaborators = [UserFactory() for _ in range(num_collaborators)]

    # Create knowledge items
    knowledge = [KnowledgeFactory(owner=owner) for _ in range(2)] if include_knowledge else None

    # Create tools
    tools = [ToolsFactory(owner=owner) for _ in range(1)] if include_tools else None

    # Create mission
    mission = MissionFactory(
        owner=owner, repositories=repos, collaborators=collaborators, knowledge_items=knowledge, tools=tools, state=state
    )

    return mission


def create_mission_with_conversation(owner=None, state=Mission.State.READY):
    """
    Create a mission with a conversation ready for messaging.

    Args:
        owner: User who owns the mission (creates one if None)
        state: Mission state (default: READY)

    Returns:
        Tuple[Mission, MissionConversation]: Mission and conversation instances
    """
    mission = create_complete_mission(owner=owner, state=state)
    conversation = MissionConversationFactory(mission=mission)
    return mission, conversation


def create_github_user_with_installation(create_repos=True, num_repos=3):
    """
    Create a user with GitHub OAuth and App installation.

    Args:
        create_repos: Whether to create repository details (default: True)
        num_repos: Number of repositories to create (default: 3)

    Returns:
        Tuple[User, GitHubAppInstallation, List[RepositoryDetail]]: User, installation, and repos
    """
    user = UserFactory()
    social_account = SocialAccountFactory(user=user)
    installation = GitHubAppInstallationFactory(social_account=social_account)

    repos = []
    if create_repos:
        repos = [
            RepositoryDetailFactory(username=installation.account_name) for _ in range(num_repos)
        ]

    return user, installation, repos
