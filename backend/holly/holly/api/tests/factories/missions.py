from uuid import uuid4

import factory

from holly.holly.models.mission import Mission

from .users import UserFactory


class MissionFactory(factory.django.DjangoModelFactory):
    """Factory for the Mission model."""

    class Meta:
        model = Mission

    owner = factory.SubFactory(UserFactory)
    title = factory.Faker("sentence")
    description = factory.Faker("text")
    branch_name = "main"
    state = Mission.State.IN_PROGRESS
    container_id = factory.LazyFunction(lambda: str(uuid4()))
    container_ip_address = factory.Faker("ipv4")
