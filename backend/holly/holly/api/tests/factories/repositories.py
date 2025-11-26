import factory

from holly.github_ext.models import RepositoryDetail


class RepositoryDetailFactory(factory.django.DjangoModelFactory):
    """Factory for RepositoryDetail model."""

    class Meta:
        model = RepositoryDetail

    github_id = factory.Sequence(lambda n: n + 1)
    username = factory.Faker("user_name")
    repo = factory.Sequence(lambda n: f"repo{n}")
    branch_name = "main"
    private = False
